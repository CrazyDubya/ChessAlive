"""Tests for LLM client and commentary."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from chess_alive.llm.client import LLMClient, LLMResponse, LLMError
from chess_alive.llm.commentary import (
    CommentaryEngine,
    PieceVoice,
    Commentary,
)
from chess_alive.core.game import ChessGame
from chess_alive.core.piece import Piece, PieceType, Color, PiecePersonality
from chess_alive.config import LLMConfig


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = LLMConfig()

        assert config.base_url == "https://openrouter.ai/api/v1"
        assert config.temperature == 0.7
        assert config.max_tokens == 300

    def test_is_configured(self):
        """Test is_configured property."""
        config = LLMConfig(api_key="")
        assert not config.is_configured

        config = LLMConfig(api_key="test-key")
        assert config.is_configured


class TestLLMResponse:
    """Tests for LLMResponse."""

    def test_response_creation(self):
        """Test creating response."""
        response = LLMResponse(
            content="Hello",
            model="gpt-4",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        )

        assert response.content == "Hello"
        assert response.model == "gpt-4"
        assert response.total_tokens == 15


class TestLLMClient:
    """Tests for LLMClient."""

    def test_client_creation(self):
        """Test client creation."""
        config = LLMConfig(api_key="test-key")
        client = LLMClient(config)

        assert client.config == config

    @pytest.mark.asyncio
    async def test_complete_no_api_key(self):
        """Test complete raises error without API key."""
        config = LLMConfig(api_key="")
        client = LLMClient(config)

        with pytest.raises(RuntimeError, match="LLM not configured"):
            await client.complete("test prompt")

    @pytest.mark.asyncio
    async def test_complete_with_mock(self):
        """Test complete with mocked HTTP client."""
        config = LLMConfig(api_key="test-key")
        client = LLMClient(config)

        mock_response = {
            "choices": [{"message": {"content": "Test response"}}],
            "model": "gpt-4",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        }

        with patch.object(httpx.AsyncClient, "post") as mock_post:
            mock_post.return_value = MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            )

            response = await client.complete("Hello")

            assert response == "Test response"

    @pytest.mark.asyncio
    async def test_complete_full_with_mock(self):
        """Test complete_full with mocked HTTP client."""
        config = LLMConfig(api_key="test-key")
        client = LLMClient(config)

        mock_response = {
            "choices": [{"message": {"content": "Test response"}}],
            "model": "gpt-4",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        }

        with patch.object(httpx.AsyncClient, "post") as mock_post:
            mock_post.return_value = MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            )

            response = await client.complete_full("Hello")

            assert isinstance(response, LLMResponse)
            assert response.content == "Test response"
            assert response.total_tokens == 15

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the client."""
        config = LLMConfig(api_key="test-key")
        client = LLMClient(config)

        # Should not raise even if no client created
        await client.close()


class TestPieceVoice:
    """Tests for PieceVoice."""

    def test_piece_voice_creation(self):
        """Test creating piece voice."""
        piece = Piece(PieceType.KNIGHT, Color.WHITE)
        mock_client = MagicMock()

        voice = PieceVoice(piece, mock_client)

        assert voice.piece == piece
        assert voice.client == mock_client

    def test_get_system_prompt(self):
        """Test system prompt generation."""
        personality = PiecePersonality(
            name="Sir Galahad",
            archetype="brave knight",
        )
        piece = Piece(PieceType.KNIGHT, Color.WHITE, personality=personality)
        mock_client = MagicMock()

        voice = PieceVoice(piece, mock_client)
        prompt = voice._get_system_prompt()

        assert "knight" in prompt.lower()
        assert "white" in prompt.lower()
        assert "Sir Galahad" in prompt

    def test_fallback_commentary_capture(self):
        """Test fallback commentary for captures."""
        personality = PiecePersonality(aggression=8)
        piece = Piece(PieceType.ROOK, Color.WHITE, personality=personality)
        mock_client = MagicMock()

        voice = PieceVoice(piece, mock_client)

        game = ChessGame()
        game.make_move_san("e4")
        game.make_move_san("d5")
        record = game.make_move_san("exd5")

        commentary = voice._fallback_commentary(record, is_own_move=True)
        assert len(commentary) > 0

    def test_fallback_commentary_normal_move(self):
        """Test fallback commentary for normal moves."""
        piece = Piece(PieceType.PAWN, Color.WHITE)
        mock_client = MagicMock()

        voice = PieceVoice(piece, mock_client)

        game = ChessGame()
        record = game.make_move_san("e4")

        commentary = voice._fallback_commentary(record, is_own_move=True)
        assert len(commentary) > 0


class TestCommentaryEngine:
    """Tests for CommentaryEngine."""

    def test_engine_creation(self):
        """Test creating commentary engine."""
        mock_client = MagicMock()
        engine = CommentaryEngine(mock_client)

        assert engine.client == mock_client
        assert engine.frequency == "every_move"

    def test_should_generate_every_move(self):
        """Test commentary frequency: every_move."""
        mock_client = MagicMock()
        engine = CommentaryEngine(mock_client, "every_move")

        game = ChessGame()
        record = game.make_move_san("e4")

        assert engine.should_generate_commentary(record)

    def test_should_generate_captures_only(self):
        """Test commentary frequency: captures_only."""
        mock_client = MagicMock()
        engine = CommentaryEngine(mock_client, "captures_only")

        game = ChessGame()
        record = game.make_move_san("e4")
        assert not engine.should_generate_commentary(record)

        game.make_move_san("d5")
        record = game.make_move_san("exd5")
        assert engine.should_generate_commentary(record)

    def test_should_generate_key_moments(self):
        """Test commentary frequency: key_moments."""
        mock_client = MagicMock()
        engine = CommentaryEngine(mock_client, "key_moments")

        game = ChessGame()

        # Normal move - no commentary
        record = game.make_move_san("e4")
        assert not engine.should_generate_commentary(record)

        # Capture - yes commentary
        game.make_move_san("d5")
        record = game.make_move_san("exd5")
        assert engine.should_generate_commentary(record)


class TestCommentary:
    """Tests for Commentary dataclass."""

    def test_commentary_creation(self):
        """Test creating commentary."""
        piece = Piece(PieceType.QUEEN, Color.WHITE)
        commentary = Commentary(
            piece=piece,
            text="For the kingdom!",
            commentary_type="move",
        )

        assert commentary.piece == piece
        assert commentary.text == "For the kingdom!"
        assert commentary.commentary_type == "move"
        assert commentary.move_context is None
