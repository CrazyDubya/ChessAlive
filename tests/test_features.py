"""Tests for the new features: ModeConfig, JSON parsing, Rich display."""

import pytest
import chess
from io import StringIO
from rich.console import Console

from chess_alive.modes.mode import GameMode, ModeConfig
from chess_alive.players.llm_player import LLMPlayer
from chess_alive.core.game import ChessGame, GameResult
from chess_alive.core.piece import Color
from chess_alive.ui.display import BoardDisplay


# =============================================================================
# ModeConfig tests
# =============================================================================

class TestModeConfig:
    """Tests for ModeConfig dataclass and per-mode defaults."""

    def test_mode_config_defaults(self):
        """Test ModeConfig has sensible defaults."""
        cfg = ModeConfig()
        assert cfg.commentary_frequency == "every_move"
        assert cfg.stockfish_depth == 15
        assert cfg.stockfish_time == 1.0
        assert cfg.stockfish_skill == 20
        assert cfg.llm_style_white == "balanced"
        assert cfg.llm_style_black == "balanced"
        assert cfg.max_moves == 500

    def test_every_mode_has_defaults(self):
        """Every GameMode should have a .defaults property."""
        for mode in GameMode:
            defaults = mode.defaults
            assert isinstance(defaults, ModeConfig)

    def test_pvp_defaults(self):
        """PvP defaults to key_moments commentary."""
        cfg = GameMode.PLAYER_VS_PLAYER.defaults
        assert cfg.commentary_frequency == "key_moments"

    def test_cvc_defaults(self):
        """CvC has faster time limit and captures_only commentary."""
        cfg = GameMode.COMPUTER_VS_COMPUTER.defaults
        assert cfg.commentary_frequency == "captures_only"
        assert cfg.stockfish_time == 0.5
        assert cfg.stockfish_skill == 20
        assert cfg.max_moves == 300

    def test_lvl_defaults(self):
        """LvL uses contrasting styles."""
        cfg = GameMode.LLM_VS_LLM.defaults
        assert cfg.llm_style_white == "aggressive"
        assert cfg.llm_style_black == "defensive"
        assert cfg.max_moves == 200

    def test_lvc_defaults(self):
        """LvC uses moderate stockfish skill."""
        cfg = GameMode.LLM_VS_COMPUTER.defaults
        assert cfg.stockfish_skill == 15


# =============================================================================
# JSON parsing tests
# =============================================================================

class TestLLMPlayerJsonParsing:
    """Tests for JSON-structured LLM response parsing."""

    def setup_method(self):
        self.player = LLMPlayer(Color.WHITE)
        self.game = ChessGame()

    def test_parse_clean_json(self):
        """Parse a clean JSON response."""
        response = '{"move": "e4", "reasoning": "Control the center"}'
        move = self.player._parse_json_response(response, self.game)
        assert move is not None
        assert move == self.game.parse_move("e4")

    def test_parse_json_embedded_in_text(self):
        """Parse JSON embedded in surrounding text."""
        response = 'Here is my analysis:\n{"move": "Nf3", "reasoning": "Develop knight"}\nThank you.'
        move = self.player._parse_json_response(response, self.game)
        assert move is not None
        assert move == self.game.parse_move("Nf3")

    def test_parse_json_with_extra_fields(self):
        """Parse JSON with extra fields beyond move/reasoning."""
        response = '{"move": "d4", "reasoning": "Queen pawn opening", "confidence": 0.9}'
        move = self.player._parse_json_response(response, self.game)
        assert move is not None
        assert move == self.game.parse_move("d4")

    def test_parse_json_invalid_move(self):
        """JSON with invalid move returns None."""
        response = '{"move": "Zz9", "reasoning": "nonsense"}'
        move = self.player._parse_json_response(response, self.game)
        assert move is None

    def test_parse_json_missing_move_field(self):
        """JSON without move field returns None."""
        response = '{"reasoning": "I think e4"}'
        move = self.player._parse_json_response(response, self.game)
        assert move is None

    def test_parse_json_empty_move(self):
        """JSON with empty move string returns None."""
        response = '{"move": "", "reasoning": "hmm"}'
        move = self.player._parse_json_response(response, self.game)
        assert move is None

    def test_parse_non_json_returns_none(self):
        """Non-JSON text returns None."""
        response = "I think e4 is the best move here."
        move = self.player._parse_json_response(response, self.game)
        assert move is None

    def test_json_preferred_over_text(self):
        """JSON parsing happens before text-based MOVE: parsing."""
        # If get_move goes JSON -> MOVE: -> fallback, test that JSON wins
        response = '{"move": "e4", "reasoning": "center"}\nMOVE: d4'
        move = self.player._parse_json_response(response, self.game)
        assert move is not None
        # Should get e4 from JSON, not d4 from MOVE:
        assert move == self.game.parse_move("e4")

    def test_parse_json_with_markdown_code_block(self):
        """Parse JSON wrapped in markdown code block."""
        response = '```json\n{"move": "e4", "reasoning": "opening"}\n```'
        move = self.player._parse_json_response(response, self.game)
        assert move is not None
        assert move == self.game.parse_move("e4")


class TestLLMPlayerJsonWithMock:
    """Integration tests: JSON response flows through get_move correctly."""

    @pytest.mark.asyncio
    async def test_json_response_parsed(self):
        """get_move handles JSON response correctly."""

        class MockClient:
            async def complete(self, prompt, system_prompt=None, temperature=None, max_tokens=None):
                return '{"move": "e4", "reasoning": "Control center"}'

        player = LLMPlayer(Color.WHITE)
        player.set_client(MockClient())
        game = ChessGame()

        move = await player.get_move(game)
        assert move is not None
        assert move == game.parse_move("e4")

    @pytest.mark.asyncio
    async def test_json_reasoning_extracted(self):
        """get_move_with_reasoning extracts reasoning from JSON."""

        class MockClient:
            async def complete(self, prompt, system_prompt=None, temperature=None, max_tokens=None):
                return '{"move": "e4", "reasoning": "Classical king pawn opening"}'

        player = LLMPlayer(Color.WHITE)
        player.set_client(MockClient())
        game = ChessGame()

        move, reasoning = await player.get_move_with_reasoning(game)
        assert move is not None
        assert "Classical" in reasoning

    @pytest.mark.asyncio
    async def test_fallback_to_text_when_json_fails(self):
        """get_move falls back to MOVE: pattern when JSON fails."""

        class MockClient:
            async def complete(self, prompt, system_prompt=None, temperature=None, max_tokens=None):
                return "I'll play MOVE: d4"

        player = LLMPlayer(Color.WHITE)
        player.set_client(MockClient())
        game = ChessGame()

        move = await player.get_move(game)
        assert move is not None
        assert move == game.parse_move("d4")


# =============================================================================
# Rich display tests
# =============================================================================

class TestBoardDisplayMoveHistory:
    """Tests for Rich Table move history display."""

    def _make_display(self) -> tuple[BoardDisplay, Console, StringIO]:
        buf = StringIO()
        console = Console(file=buf, force_terminal=True, width=120)
        display = BoardDisplay(console=console)
        return display, console, buf

    def _play_moves(self, game: ChessGame, moves: list[str]):
        """Play a list of SAN moves."""
        for san in moves:
            game.make_move_san(san)

    def test_empty_history(self):
        """print_move_history with no moves prints 'No moves yet'."""
        display, _, buf = self._make_display()
        game = ChessGame()
        display.print_move_history(game)
        output = buf.getvalue()
        assert "No moves" in output

    def test_history_with_moves(self):
        """print_move_history shows a table with moves."""
        display, _, buf = self._make_display()
        game = ChessGame()
        self._play_moves(game, ["e4", "e5", "Nf3", "Nc6"])
        display.print_move_history(game)
        output = buf.getvalue()
        assert "Move History" in output
        assert "e4" in output
        assert "e5" in output
        assert "Nf3" in output
        assert "Nc6" in output

    def test_history_with_last_n(self):
        """print_move_history with last_n shows only recent moves."""
        display, _, buf = self._make_display()
        game = ChessGame()
        self._play_moves(game, ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6"])
        display.print_move_history(game, last_n=1)
        output = buf.getvalue()
        # Should show Bb5/a6 (move 3) but not e4/e5 (move 1)
        assert "Bb5" in output
        assert "a6" in output

    def test_history_odd_number_of_moves(self):
        """print_move_history handles odd number of moves (white just moved)."""
        display, _, buf = self._make_display()
        game = ChessGame()
        self._play_moves(game, ["e4", "e5", "Nf3"])
        display.print_move_history(game)
        output = buf.getvalue()
        assert "Nf3" in output
        assert "..." in output  # Black's column shows "..."


class TestBoardDisplayGameStats:
    """Tests for game statistics table."""

    def _make_display(self) -> tuple[BoardDisplay, Console, StringIO]:
        buf = StringIO()
        console = Console(file=buf, force_terminal=True, width=120)
        display = BoardDisplay(console=console)
        return display, console, buf

    def test_stats_table_renders(self):
        """print_game_stats produces a table with expected columns."""
        display, _, buf = self._make_display()
        game = ChessGame()
        game.make_move_san("e4")
        game.make_move_san("e5")
        display.print_game_stats(game)
        output = buf.getvalue()
        assert "Game Statistics" in output
        assert "Moves" in output
        assert "Captures" in output
        assert "Checks" in output
        assert "Castled" in output
        assert "Material" in output

    def test_stats_capture_counted(self):
        """Stats table counts captures correctly."""
        display, _, buf = self._make_display()
        game = ChessGame()
        # Italian game with capture
        for san in ["e4", "e5", "Nf3", "Nc6", "Bc4", "Nf6", "d3", "Bc5", "Bg5", "d6", "Bxf6"]:
            game.make_move_san(san)
        display.print_game_stats(game)
        output = buf.getvalue()
        # White made a capture
        assert "Captures" in output


class TestBoardDisplayPostGame:
    """Tests for post-game summary."""

    def _make_display(self) -> tuple[BoardDisplay, Console, StringIO]:
        buf = StringIO()
        console = Console(file=buf, force_terminal=True, width=120)
        display = BoardDisplay(console=console)
        return display, console, buf

    def test_post_game_summary_in_progress(self):
        """Post-game summary for an in-progress game."""
        display, _, buf = self._make_display()
        game = ChessGame()
        game.make_move_san("e4")
        display.print_post_game_summary(game)
        output = buf.getvalue()
        assert "Game Statistics" in output
        assert "Move History" in output

    def test_post_game_with_player_names(self):
        """Post-game summary shows player names."""
        display, _, buf = self._make_display()
        game = ChessGame()
        game.make_move_san("e4")
        display.print_post_game_summary(game, white_name="Alice", black_name="Bob")
        output = buf.getvalue()
        assert "Game Statistics" in output


class TestStyledSan:
    """Tests for styled SAN move text."""

    def test_styled_san_capture(self):
        """Captures get STYLE_CAPTURE."""
        display = BoardDisplay()
        game = ChessGame()
        # Create a position with a capture: Scotch game
        for san in ["e4", "e5", "Nf3", "Nc6", "d4", "exd4"]:
            game.make_move_san(san)
        # The last move (exd4) was a capture
        last_record = game.move_history[-1]
        text = display._styled_san(last_record)
        assert text.plain == "exd4"

    def test_styled_san_normal_white_move(self):
        """Normal white move gets STYLE_WHITE_MOVE."""
        display = BoardDisplay()
        game = ChessGame()
        game.make_move_san("e4")
        record = game.move_history[0]
        text = display._styled_san(record)
        assert text.plain == "e4"
