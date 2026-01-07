"""Tests for player implementations."""

import pytest
import asyncio
import chess

from chess_alive.core.game import ChessGame
from chess_alive.core.piece import Color
from chess_alive.players.base import Player, PlayerType
from chess_alive.players.human import HumanPlayer
from chess_alive.players.llm_player import LLMPlayer


class TestPlayerBase:
    """Tests for base Player class."""

    def test_player_type_enum(self):
        """Test PlayerType enum values."""
        assert PlayerType.HUMAN.value == 1
        assert PlayerType.COMPUTER.value == 2
        assert PlayerType.LLM.value == 3


class TestHumanPlayer:
    """Tests for HumanPlayer."""

    def test_human_player_creation(self):
        """Test creating a human player."""
        player = HumanPlayer(Color.WHITE, "Alice")

        assert player.color == Color.WHITE
        assert player.name == "Alice"
        assert player.player_type == PlayerType.HUMAN

    def test_human_player_default_name(self):
        """Test default name for human player."""
        player = HumanPlayer(Color.BLACK)

        assert player.name == "Human"

    @pytest.mark.asyncio
    async def test_human_player_with_custom_handler(self):
        """Test human player with custom input handler."""
        game = ChessGame()

        async def mock_handler(g):
            return "e4"

        player = HumanPlayer(Color.WHITE, input_handler=mock_handler)
        move = await player.get_move(game)

        assert move is not None
        assert move.from_square == chess.E2
        assert move.to_square == chess.E4

    @pytest.mark.asyncio
    async def test_human_player_wrong_turn(self):
        """Test human player returns None when not their turn."""
        game = ChessGame()

        async def mock_handler(g):
            return "e5"

        player = HumanPlayer(Color.BLACK, input_handler=mock_handler)
        move = await player.get_move(game)

        # Black's turn is not first, so should return None without calling handler
        assert move is None


class TestLLMPlayer:
    """Tests for LLMPlayer."""

    def test_llm_player_creation(self):
        """Test creating an LLM player."""
        player = LLMPlayer(Color.WHITE, "GPT-4")

        assert player.color == Color.WHITE
        assert player.name == "GPT-4"
        assert player.player_type == PlayerType.LLM
        assert player.style == "balanced"

    def test_llm_player_styles(self):
        """Test different LLM player styles."""
        aggressive = LLMPlayer(Color.WHITE, style="aggressive")
        defensive = LLMPlayer(Color.BLACK, style="defensive")
        creative = LLMPlayer(Color.WHITE, style="creative")

        assert aggressive.style == "aggressive"
        assert defensive.style == "defensive"
        assert creative.style == "creative"

    def test_llm_player_parse_move_from_response(self):
        """Test parsing move from LLM response."""
        player = LLMPlayer(Color.WHITE)
        game = ChessGame()

        # Test with proper MOVE: format
        response = "Looking at the position, I think the best move is MOVE: e4"
        move = player._parse_move_from_response(response, game)
        assert move is not None

    def test_llm_player_parse_move_case_insensitive(self):
        """Test parsing move is case insensitive."""
        player = LLMPlayer(Color.WHITE)
        game = ChessGame()

        response = "move: Nf3"
        move = player._parse_move_from_response(response, game)
        assert move is not None

    def test_llm_player_fallback_extraction(self):
        """Test fallback move extraction."""
        player = LLMPlayer(Color.WHITE)
        game = ChessGame()

        # Response without MOVE: but contains valid move
        response = "I recommend playing e4 to control the center."
        move = player._fallback_move_extraction(response, game)
        assert move is not None

    def test_llm_player_fallback_uci(self):
        """Test fallback extraction with UCI format."""
        player = LLMPlayer(Color.WHITE)
        game = ChessGame()

        response = "The move e2e4 seems strong here."
        move = player._fallback_move_extraction(response, game)
        assert move is not None

    @pytest.mark.asyncio
    async def test_llm_player_no_client_error(self):
        """Test LLM player raises error without client."""
        player = LLMPlayer(Color.WHITE)
        game = ChessGame()

        with pytest.raises(RuntimeError, match="LLM client not configured"):
            await player.get_move(game)


class MockLLMClient:
    """Mock LLM client for testing."""

    def __init__(self, response: str):
        self.response = response
        self.calls = []

    async def complete(self, prompt, system_prompt=None, temperature=None, max_tokens=None):
        self.calls.append({
            "prompt": prompt,
            "system_prompt": system_prompt,
            "temperature": temperature,
        })
        return self.response


class TestLLMPlayerWithMock:
    """Tests for LLMPlayer with mock client."""

    @pytest.mark.asyncio
    async def test_llm_player_get_move_with_mock(self):
        """Test getting move with mock client."""
        player = LLMPlayer(Color.WHITE)
        game = ChessGame()

        mock_client = MockLLMClient("MOVE: e4")
        player.set_client(mock_client)

        move = await player.get_move(game)

        assert move is not None
        assert len(mock_client.calls) == 1

    @pytest.mark.asyncio
    async def test_llm_player_random_fallback(self):
        """Test random fallback when no valid move parsed."""
        player = LLMPlayer(Color.WHITE)
        game = ChessGame()

        mock_client = MockLLMClient("I don't know what to play...")
        player.set_client(mock_client)

        move = await player.get_move(game)

        # Should still return a valid move (random fallback)
        assert move is not None
        assert game.is_legal_move(move)

    @pytest.mark.asyncio
    async def test_llm_player_get_move_with_reasoning(self):
        """Test getting move with reasoning."""
        player = LLMPlayer(Color.WHITE)
        game = ChessGame()

        mock_client = MockLLMClient("REASONING: Control the center\nMOVE: e4")
        player.set_client(mock_client)

        move, reasoning = await player.get_move_with_reasoning(game)

        assert move is not None
        assert "center" in reasoning.lower()
