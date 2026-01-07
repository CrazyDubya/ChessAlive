"""Tests for match orchestration."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from chess_alive.modes.match import Match, MatchConfig, MatchEvent
from chess_alive.modes.mode import GameMode
from chess_alive.core.game import GameResult, GameState
from chess_alive.core.piece import Color
from chess_alive.players.base import PlayerType
from chess_alive.config import GameConfig


class TestMatchConfig:
    """Tests for MatchConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = MatchConfig()

        assert config.mode == GameMode.PLAYER_VS_PLAYER
        assert config.white_name == "White"
        assert config.black_name == "Black"
        assert config.enable_commentary is True
        assert config.max_moves == 500

    def test_custom_config(self):
        """Test custom configuration."""
        config = MatchConfig(
            mode=GameMode.LLM_VS_LLM,
            white_name="GPT-4",
            black_name="Claude",
            stockfish_skill=20,
        )

        assert config.mode == GameMode.LLM_VS_LLM
        assert config.white_name == "GPT-4"
        assert config.stockfish_skill == 20


class TestMatchEvent:
    """Tests for MatchEvent."""

    def test_event_creation(self):
        """Test creating match event."""
        event = MatchEvent(
            event_type="move",
            data={"move": "e4"},
        )

        assert event.event_type == "move"
        assert event.data["move"] == "e4"
        assert event.timestamp is not None


class TestMatch:
    """Tests for Match class."""

    def test_match_creation(self):
        """Test creating a match."""
        config = MatchConfig()
        match = Match(config)

        assert match.config == config
        assert match.game is not None
        assert match.white_player is None
        assert match.black_player is None

    def test_match_with_event_callback(self):
        """Test match with event callback."""
        events = []

        async def event_handler(event):
            events.append(event)

        config = MatchConfig()
        match = Match(config, on_event=event_handler)

        assert match.on_event == event_handler

    @pytest.mark.asyncio
    async def test_emit_event(self):
        """Test emitting events."""
        events = []

        async def event_handler(event):
            events.append(event)

        config = MatchConfig()
        match = Match(config, on_event=event_handler)

        await match._emit_event("test", {"value": 42})

        assert len(events) == 1
        assert events[0].event_type == "test"
        assert events[0].data["value"] == 42
        assert len(match.events) == 1

    def test_get_current_player_not_setup(self):
        """Test getting current player when not set up."""
        config = MatchConfig()
        match = Match(config)

        assert match.get_current_player() is None


class MockPlayer:
    """Mock player for testing."""

    def __init__(self, color, moves):
        self.color = color
        self.name = f"Mock {color.name_str}"
        self.player_type = PlayerType.HUMAN
        self.moves = moves
        self.move_index = 0
        self.game_started = False
        self.game_ended = False

    async def get_move(self, game):
        if game.current_turn != self.color:
            return None
        if self.move_index >= len(self.moves):
            return None
        move = game.parse_move(self.moves[self.move_index])
        self.move_index += 1
        return move

    async def on_game_start(self, game):
        self.game_started = True

    async def on_game_end(self, game):
        self.game_ended = True

    async def on_opponent_move(self, game, move):
        pass


class TestMatchGameplay:
    """Tests for match gameplay."""

    @pytest.mark.asyncio
    async def test_play_move(self):
        """Test playing a single move."""
        config = MatchConfig()
        match = Match(config)

        # Set up mock players
        match.white_player = MockPlayer(Color.WHITE, ["e4"])
        match.black_player = MockPlayer(Color.BLACK, ["e5"])

        record = await match.play_move()

        assert record is not None
        assert record.san == "e4"

    @pytest.mark.asyncio
    async def test_play_move_alternates(self):
        """Test that moves alternate between players."""
        config = MatchConfig(enable_commentary=False)
        match = Match(config)

        match.white_player = MockPlayer(Color.WHITE, ["e4", "Nf3"])
        match.black_player = MockPlayer(Color.BLACK, ["e5", "Nc6"])

        # White's move
        record1 = await match.play_move()
        assert record1.piece.color == Color.WHITE

        # Black's move
        record2 = await match.play_move()
        assert record2.piece.color == Color.BLACK

    @pytest.mark.asyncio
    async def test_short_game(self):
        """Test a short complete game (scholar's mate)."""
        config = MatchConfig(enable_commentary=False)
        match = Match(config)

        # Scholar's mate sequence
        white_moves = ["e4", "Bc4", "Qh5", "Qxf7"]
        black_moves = ["e5", "Nc6", "Nf6"]

        match.white_player = MockPlayer(Color.WHITE, white_moves)
        match.black_player = MockPlayer(Color.BLACK, black_moves)

        match.game.state = GameState.PLAYING

        # Play the game
        while not match.game.is_game_over:
            record = await match.play_move()
            if record is None:
                break

        assert match.game.is_checkmate
        assert match.game.result == GameResult.WHITE_WINS

    @pytest.mark.asyncio
    async def test_game_start_notification(self):
        """Test that players are notified of game start."""
        config = MatchConfig(enable_commentary=False)
        match = Match(config)

        match.white_player = MockPlayer(Color.WHITE, [])
        match.black_player = MockPlayer(Color.BLACK, [])

        await match.white_player.on_game_start(match.game)
        await match.black_player.on_game_start(match.game)

        assert match.white_player.game_started
        assert match.black_player.game_started


class TestMatchSetup:
    """Tests for match setup."""

    @pytest.mark.asyncio
    async def test_setup_pvp(self):
        """Test setting up PvP match."""
        config = MatchConfig(mode=GameMode.PLAYER_VS_PLAYER)
        game_config = GameConfig()
        match = Match(config, game_config)

        async def mock_input(game):
            return "e4"

        await match.setup(mock_input)

        assert match.white_player is not None
        assert match.black_player is not None
        assert match.white_player.player_type == PlayerType.HUMAN
        assert match.black_player.player_type == PlayerType.HUMAN

    @pytest.mark.asyncio
    async def test_setup_no_stockfish_error(self):
        """Test error when Stockfish not found."""
        config = MatchConfig(mode=GameMode.PLAYER_VS_COMPUTER)
        game_config = GameConfig()
        game_config.engine.path = None

        match = Match(config, game_config)

        with patch("chess_alive.players.computer.find_stockfish", return_value=None):
            with pytest.raises(RuntimeError, match="Stockfish not found"):
                await match.setup()

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup after match."""
        config = MatchConfig()
        match = Match(config)

        # Cleanup should not raise even if nothing to clean
        await match._cleanup()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using match as context manager."""
        config = MatchConfig()

        async with Match(config) as match:
            assert match is not None

        # Should be cleaned up
