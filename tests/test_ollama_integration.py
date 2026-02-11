"""Integration tests for Ollama backend support.

Spins up a lightweight mock OpenAI-compatible server to simulate Ollama,
then runs LLM-vs-LLM games through it.
"""

import asyncio
import json
import pytest
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from unittest.mock import patch

from chess_alive.config import LLMConfig, GameConfig, PROVIDER_DEFAULTS
from chess_alive.llm.client import LLMClient, LLMError
from chess_alive.players.llm_player import LLMPlayer
from chess_alive.core.game import ChessGame
from chess_alive.core.piece import Color
from chess_alive.credentials import save_api_key, load_saved_provider


# ---------------------------------------------------------------------------
# Mock Ollama server (OpenAI-compatible /v1/chat/completions)
# ---------------------------------------------------------------------------

class _MockOllamaHandler(BaseHTTPRequestHandler):
    """Minimal handler that returns a chess move in JSON."""

    move_counter = 0

    # Scripted moves for a short game (Scholar's Mate attempt)
    SCRIPTED_MOVES = [
        "e4", "e5",       # 1. e4 e5
        "Bc4", "Nc6",     # 2. Bc4 Nc6
        "Qh5", "Nf6",     # 3. Qh5 Nf6
        "Qxf7",           # 4. Qxf7# — checkmate
    ]

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        data = json.loads(body)

        # Pick the next scripted move
        idx = _MockOllamaHandler.move_counter % len(self.SCRIPTED_MOVES)
        move = self.SCRIPTED_MOVES[idx]
        _MockOllamaHandler.move_counter += 1

        response = {
            "id": "mock-001",
            "object": "chat.completion",
            "model": data.get("model", "mock-model"),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps({"move": move, "reasoning": f"Playing {move}"}),
                },
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 20,
                "total_tokens": 70,
            },
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        pass  # Suppress request logs


@pytest.fixture(autouse=True)
def reset_move_counter():
    """Reset move counter between tests."""
    _MockOllamaHandler.move_counter = 0
    yield


@pytest.fixture
def mock_ollama_server():
    """Spin up a mock Ollama HTTP server on a random port."""
    server = HTTPServer(("127.0.0.1", 0), _MockOllamaHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}/v1"
    server.shutdown()


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------

class TestOllamaConfig:
    """Test Ollama-specific configuration."""

    def test_ollama_provider_defaults(self):
        """Ollama provider defaults are correct."""
        defaults = PROVIDER_DEFAULTS["ollama"]
        assert defaults["base_url"] == "http://localhost:11434/v1"
        assert defaults["model"] == "qwen2.5:3b"

    def test_ollama_config_no_api_key_needed(self):
        """Ollama config auto-fills api_key='ollama' when empty."""
        config = LLMConfig(provider="ollama", api_key="", base_url="", model="")
        assert config.api_key == "ollama"
        assert config.is_configured
        assert config.is_ollama

    def test_ollama_config_fills_defaults(self):
        """Ollama config fills in default base_url and model."""
        config = LLMConfig(provider="ollama", api_key="", base_url="", model="")
        assert "11434" in config.base_url
        assert config.model == "qwen2.5:3b"

    def test_openrouter_config_unchanged(self):
        """OpenRouter config still works as before."""
        config = LLMConfig(
            provider="openrouter",
            api_key="sk-test-123",
            base_url="",
            model="",
        )
        assert config.base_url == "https://openrouter.ai/api/v1"
        assert config.model == "mistralai/devstral-2512:free"
        assert not config.is_ollama

    def test_provider_display_names(self):
        """Display names are correct."""
        ollama = LLMConfig(provider="ollama")
        assert ollama.provider_display == "Ollama (local)"

        openrouter = LLMConfig(provider="openrouter", api_key="test")
        assert openrouter.provider_display == "OpenRouter"

    def test_custom_base_url_preserved(self):
        """A custom base_url is not overwritten."""
        config = LLMConfig(
            provider="ollama",
            base_url="http://remote-host:11434/v1",
            model="llama3.2:1b",
        )
        assert config.base_url == "http://remote-host:11434/v1"
        assert config.model == "llama3.2:1b"


# ---------------------------------------------------------------------------
# Credentials tests
# ---------------------------------------------------------------------------

class TestOllamaCredentials:
    """Test saving/loading Ollama config via credentials."""

    def test_save_and_load_ollama_provider(self, tmp_path):
        """Save Ollama provider config and load it back."""
        with patch("chess_alive.credentials._get_config_dir", return_value=tmp_path / "chess-alive"):
            with patch(
                "chess_alive.credentials._get_credentials_path",
                return_value=tmp_path / "chess-alive" / "credentials.json",
            ):
                save_api_key(api_key="", model="llama3.2:1b", provider="ollama")
                assert load_saved_provider() == "ollama"


# ---------------------------------------------------------------------------
# LLM Client tests with mock server
# ---------------------------------------------------------------------------

class TestOllamaClient:
    """Test LLMClient connecting to mock Ollama server."""

    @pytest.mark.asyncio
    async def test_complete_via_ollama(self, mock_ollama_server):
        """Basic completion through Ollama endpoint."""
        config = LLMConfig(
            provider="ollama",
            api_key="ollama",
            base_url=mock_ollama_server,
            model="mock-model",
        )
        async with LLMClient(config) as client:
            response = await client.complete("What is the best move?")
            # Should get JSON with first scripted move
            assert "e4" in response

    @pytest.mark.asyncio
    async def test_complete_full_via_ollama(self, mock_ollama_server):
        """Full completion with metadata."""
        config = LLMConfig(
            provider="ollama",
            api_key="ollama",
            base_url=mock_ollama_server,
            model="mock-model",
        )
        async with LLMClient(config) as client:
            response = await client.complete_full("test")
            assert response.model == "mock-model"
            assert response.total_tokens == 70

    @pytest.mark.asyncio
    async def test_no_auth_header_for_ollama(self, mock_ollama_server):
        """Ollama client should NOT send Authorization header."""
        config = LLMConfig(
            provider="ollama",
            api_key="ollama",
            base_url=mock_ollama_server,
            model="mock-model",
        )
        client = LLMClient(config)
        http = await client._get_client()
        assert "Authorization" not in http.headers
        await client.close()

    @pytest.mark.asyncio
    async def test_auth_header_for_openrouter(self):
        """OpenRouter client DOES send Authorization header."""
        config = LLMConfig(
            provider="openrouter",
            api_key="sk-test-key",
        )
        client = LLMClient(config)
        http = await client._get_client()
        assert "Authorization" in http.headers
        assert http.headers["Authorization"] == "Bearer sk-test-key"
        await client.close()

    @pytest.mark.asyncio
    async def test_connection_error_message(self):
        """Ollama connection error gives a helpful message."""
        config = LLMConfig(
            provider="ollama",
            api_key="ollama",
            base_url="http://127.0.0.1:1/v1",  # nothing listening
            model="test",
        )
        async with LLMClient(config) as client:
            with pytest.raises(LLMError, match="Cannot connect to Ollama"):
                await client.complete("test")


# ---------------------------------------------------------------------------
# LLM Player with mock Ollama
# ---------------------------------------------------------------------------

class TestLLMPlayerWithOllama:
    """Test LLMPlayer using mock Ollama backend."""

    @pytest.mark.asyncio
    async def test_player_gets_move_from_ollama(self, mock_ollama_server):
        """LLMPlayer can get a chess move via Ollama."""
        config = LLMConfig(
            provider="ollama",
            api_key="ollama",
            base_url=mock_ollama_server,
            model="mock-model",
        )
        async with LLMClient(config) as client:
            player = LLMPlayer(Color.WHITE, "Ollama-White")
            player.set_client(client)

            game = ChessGame()
            move = await player.get_move(game)

            assert move is not None
            assert game.is_legal_move(move)

    @pytest.mark.asyncio
    async def test_json_parsing_from_ollama(self, mock_ollama_server):
        """The mock returns JSON and the player's JSON parser handles it."""
        config = LLMConfig(
            provider="ollama",
            api_key="ollama",
            base_url=mock_ollama_server,
            model="mock-model",
        )
        async with LLMClient(config) as client:
            player = LLMPlayer(Color.WHITE, "Ollama-White")
            player.set_client(client)

            game = ChessGame()
            move, reasoning = await player.get_move_with_reasoning(game)

            assert move is not None
            assert "Playing" in reasoning

    @pytest.mark.asyncio
    async def test_multi_move_sequence(self, mock_ollama_server):
        """Play multiple moves against the mock server."""
        config = LLMConfig(
            provider="ollama",
            api_key="ollama",
            base_url=mock_ollama_server,
            model="mock-model",
        )
        async with LLMClient(config) as client:
            white = LLMPlayer(Color.WHITE, "Ollama-W")
            black = LLMPlayer(Color.BLACK, "Ollama-B")
            white.set_client(client)
            black.set_client(client)

            game = ChessGame()

            # Play 4 half-moves (2 full moves)
            for i in range(4):
                current = white if game.current_turn == Color.WHITE else black
                move = await current.get_move(game)
                assert move is not None, f"Move {i} returned None"
                record = game.make_move(move)
                assert record is not None, f"Move {i} was illegal"

            assert len(game.move_history) == 4
