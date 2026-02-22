"""Tests for the teaching advisor module."""

import pytest
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional

import chess
import chess.engine

from chess_alive.llm.teaching import (
    CandidateMove,
    TeachingAdvice,
    TeachingAdvisor,
)
from chess_alive.core.game import ChessGame
from chess_alive.core.piece import Color
from chess_alive.config import EngineConfig, LLMConfig
from chess_alive.llm.client import LLMClient, LLMError
from chess_alive.modes.mode import GameMode
from chess_alive.modes.match import Match, MatchConfig


class TestCandidateMove:
    """Tests for CandidateMove dataclass."""

    def test_creation(self):
        m = CandidateMove(
            san="e4",
            evaluation="+0.30",
            explanation="Controls the center.",
            likely_response="e5",
            follow_up_plan="Develop knights.",
        )
        assert m.san == "e4"
        assert m.evaluation == "+0.30"
        assert m.explanation == "Controls the center."
        assert m.likely_response == "e5"
        assert m.follow_up_plan == "Develop knights."


class TestTeachingAdvice:
    """Tests for TeachingAdvice dataclass."""

    def test_creation(self):
        moves = [
            CandidateMove("e4", "+0.30", "Center control.", "e5", "Develop pieces."),
            CandidateMove("d4", "+0.25", "Queen's pawn.", "d5", "Fight for center."),
        ]
        advice = TeachingAdvice(
            position_assessment="Opening position. Develop pieces.",
            candidate_moves=moves,
            player_color="White",
            move_number=1,
        )
        assert advice.position_assessment == "Opening position. Develop pieces."
        assert len(advice.candidate_moves) == 2
        assert advice.player_color == "White"
        assert advice.move_number == 1
        assert advice.generated_at is not None

    def test_empty_candidates(self):
        advice = TeachingAdvice(
            position_assessment="No moves available.",
            candidate_moves=[],
            player_color="Black",
            move_number=5,
        )
        assert advice.candidate_moves == []


class TestTeachingAdvisor:
    """Tests for TeachingAdvisor."""

    def _make_advisor(self, api_key: str = "test-key") -> TeachingAdvisor:
        config = LLMConfig(api_key=api_key)
        client = LLMClient(config)
        engine_config = EngineConfig(path="/usr/bin/stockfish")
        return TeachingAdvisor(client, engine_config)

    def test_creation(self):
        advisor = self._make_advisor()
        assert advisor.llm_client is not None
        assert advisor.engine_config.path == "/usr/bin/stockfish"
        assert advisor._engine is None

    def test_format_score_positive(self):
        advisor = self._make_advisor()
        score = chess.engine.PovScore(chess.engine.Cp(50), chess.WHITE)
        result = advisor._format_score(score, chess.WHITE)
        assert result == "+0.50"

    def test_format_score_negative(self):
        advisor = self._make_advisor()
        score = chess.engine.PovScore(chess.engine.Cp(-75), chess.WHITE)
        result = advisor._format_score(score, chess.WHITE)
        assert result == "-0.75"

    def test_format_score_mate(self):
        advisor = self._make_advisor()
        score = chess.engine.PovScore(chess.engine.Mate(3), chess.WHITE)
        result = advisor._format_score(score, chess.WHITE)
        assert "Mate in 3" in result

    def test_format_score_opponent_mates(self):
        advisor = self._make_advisor()
        score = chess.engine.PovScore(chess.engine.Mate(-2), chess.WHITE)
        result = advisor._format_score(score, chess.WHITE)
        assert "mates in 2" in result.lower() or "opp mates" in result.lower()

    def test_format_score_black_perspective(self):
        advisor = self._make_advisor()
        # +50 from White's perspective means -0.50 from Black's perspective
        score = chess.engine.PovScore(chess.engine.Cp(50), chess.WHITE)
        result = advisor._format_score(score, chess.BLACK)
        assert result == "-0.50"

    # ------------------------------------------------------------------
    # Prompt building
    # ------------------------------------------------------------------

    def test_build_prompt_contains_fen(self):
        advisor = self._make_advisor()
        game = ChessGame()
        move_data = [("e4", "+0.30", "e5"), ("d4", "+0.25", "d5")]
        prompt = advisor._build_prompt(game, move_data, Color.WHITE)
        assert game.fen in prompt
        assert "e4" in prompt
        assert "d4" in prompt
        assert "White" in prompt

    def test_build_prompt_no_check_flag(self):
        advisor = self._make_advisor()
        game = ChessGame()
        move_data = [("e4", "+0.30", "")]
        prompt = advisor._build_prompt(game, move_data, Color.WHITE)
        assert "in check" not in prompt

    def test_build_prompt_check_flag_set(self):
        """Prompt includes 'in check' marker when the current player is in check."""
        advisor = self._make_advisor()
        # FEN: black queen on h4 gives check to white king on e1
        game = ChessGame()
        game.load_fen("rnb1kbnr/pppp1ppp/8/4p3/5PPq/8/PPPPP2P/RNBQKBNR w KQkq - 1 3")
        assert game.is_check, "Position must have white in check for this test"
        move_data = [("g3", "-3.00", "Qxg3")]
        prompt = advisor._build_prompt(game, move_data, Color.WHITE)
        assert "in check" in prompt

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def test_parse_response_structured(self):
        advisor = self._make_advisor()
        move_data = [("e4", "+0.30", "e5"), ("d4", "+0.25", "d5"), ("Nf3", "+0.20", "Nc6")]
        response = """POSITION: Strong central control available.

MOVE (e4):
- Why: Grabs the center immediately.
- Response: Black will likely reply e5 to contest center.
- Follow-up: Develop the king's knight to f3.

MOVE (d4):
- Why: Solid queen's pawn opening.
- Response: Black may play d5.
- Follow-up: Continue with c4 for Queen's Gambit.

MOVE (Nf3):
- Why: Develops a piece with tempo.
- Response: Black knight to c6.
- Follow-up: Castle kingside for safety."""

        result = advisor._parse_response(response, move_data, Color.WHITE, 1)
        assert result.position_assessment == "Strong central control available."
        assert len(result.candidate_moves) == 3
        assert result.candidate_moves[0].san == "e4"
        assert result.candidate_moves[0].evaluation == "+0.30"
        assert "center" in result.candidate_moves[0].explanation.lower()
        assert "e5" in result.candidate_moves[0].likely_response
        assert "knight" in result.candidate_moves[0].follow_up_plan.lower()

    def test_parse_response_fallback(self):
        """If the LLM returns garbled text, fallback to raw move_data."""
        advisor = self._make_advisor()
        move_data = [("e4", "+0.30", "e5")]
        response = "The position is interesting and complex."

        result = advisor._parse_response(response, move_data, Color.WHITE, 1)
        # Should still have one candidate move from fallback
        assert len(result.candidate_moves) == 1
        assert result.candidate_moves[0].san == "e4"

    def test_parse_response_player_color_and_move_number(self):
        advisor = self._make_advisor()
        move_data = [("d5", "-0.20", "c4")]
        response = "POSITION: Slightly worse for Black.\n\nMOVE (d5):\n- Why: Central pawn.\n- Response: c4.\n- Follow-up: Develop bishop."

        result = advisor._parse_response(response, move_data, Color.BLACK, 7)
        assert result.player_color == "Black"
        assert result.move_number == 7

    # ------------------------------------------------------------------
    # Fallback advice
    # ------------------------------------------------------------------

    def test_fallback_advice_normal(self):
        advisor = self._make_advisor()
        game = ChessGame()
        move_data = [("e4", "+0.30", "e5"), ("d4", "+0.25", "")]
        result = advisor._fallback_advice(game, move_data, Color.WHITE)
        assert len(result.candidate_moves) == 2
        assert result.candidate_moves[0].san == "e4"
        assert result.candidate_moves[1].san == "d4"
        assert "No immediate forced response" in result.candidate_moves[1].likely_response
        assert "center" in result.position_assessment.lower()

    def test_fallback_advice_in_check(self):
        advisor = self._make_advisor()
        # Load a check position
        game = ChessGame()
        # Use a known check position (white king in check by black queen)
        game.load_fen("4k3/8/8/8/8/8/8/4K2q w - - 0 1")
        move_data = [("Ke2", "-5.00", "Qh2")]
        result = advisor._fallback_advice(game, move_data, Color.WHITE)
        assert "check" in result.position_assessment.lower()

    # ------------------------------------------------------------------
    # Engine not configured
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_ensure_engine_no_path(self):
        config = LLMConfig(api_key="test")
        client = LLMClient(config)
        engine_config = EngineConfig(path=None)
        advisor = TeachingAdvisor(client, engine_config)
        with pytest.raises(RuntimeError, match="Stockfish path not configured"):
            await advisor._ensure_engine()

    @pytest.mark.asyncio
    async def test_close_no_engine(self):
        """close() should not raise when engine was never started."""
        advisor = self._make_advisor()
        await advisor.close()  # Should not raise

    # ------------------------------------------------------------------
    # analyze() with mocked engine + LLM
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_analyze_with_mocks(self):
        """analyze() should return TeachingAdvice when engine + LLM work."""
        config = LLMConfig(api_key="test-key")
        client = LLMClient(config)
        engine_config = EngineConfig(path="/fake/stockfish")
        advisor = TeachingAdvisor(client, engine_config)

        game = ChessGame()
        e4_move = chess.Move.from_uci("e2e4")
        d4_move = chess.Move.from_uci("d2d4")
        nf3_move = chess.Move.from_uci("g1f3")
        e5_response = chess.Move.from_uci("e7e5")

        # Build fake InfoDicts
        def make_info(move, cp):
            score = chess.engine.PovScore(chess.engine.Cp(cp), chess.WHITE)
            return {"pv": [move], "score": score}

        fake_multipv = [make_info(e4_move, 30), make_info(d4_move, 25), make_info(nf3_move, 20)]

        mock_engine = AsyncMock()
        mock_engine.analyse = AsyncMock(return_value=fake_multipv)
        mock_engine.play = AsyncMock(return_value=MagicMock(move=e5_response))
        mock_engine.quit = AsyncMock()

        advisor._engine = mock_engine

        llm_response = (
            "POSITION: Equal opening position.\n\n"
            "MOVE (e4):\n"
            "- Why: Controls the center.\n"
            "- Response: Black may play e5.\n"
            "- Follow-up: Develop your knights.\n\n"
            "MOVE (d4):\n"
            "- Why: Queen's pawn expansion.\n"
            "- Response: d5 to contest center.\n"
            "- Follow-up: Consider c4.\n\n"
            "MOVE (Nf3):\n"
            "- Why: Develops a piece.\n"
            "- Response: Nc6.\n"
            "- Follow-up: Castle kingside."
        )

        with patch.object(client, "complete", new=AsyncMock(return_value=llm_response)):
            advice = await advisor.analyze(game)

        assert isinstance(advice, TeachingAdvice)
        assert advice.position_assessment == "Equal opening position."
        assert len(advice.candidate_moves) >= 1
        assert advice.candidate_moves[0].san == "e4"
        assert advice.candidate_moves[0].evaluation == "+0.30"
        assert advice.player_color == "White"
        assert advice.move_number == 1

    @pytest.mark.asyncio
    async def test_analyze_falls_back_on_llm_error(self):
        """analyze() returns fallback advice when LLM raises LLMError."""
        config = LLMConfig(api_key="test-key")
        client = LLMClient(config)
        engine_config = EngineConfig(path="/fake/stockfish")
        advisor = TeachingAdvisor(client, engine_config)

        game = ChessGame()
        e4_move = chess.Move.from_uci("e2e4")
        e5_response = chess.Move.from_uci("e7e5")

        mock_engine = AsyncMock()
        mock_engine.analyse = AsyncMock(
            return_value=[
                {"pv": [e4_move], "score": chess.engine.PovScore(chess.engine.Cp(30), chess.WHITE)}
            ]
        )
        mock_engine.play = AsyncMock(return_value=MagicMock(move=e5_response))
        mock_engine.quit = AsyncMock()
        advisor._engine = mock_engine

        with patch.object(client, "complete", new=AsyncMock(side_effect=LLMError("API down"))):
            advice = await advisor.analyze(game)

        assert isinstance(advice, TeachingAdvice)
        assert len(advice.candidate_moves) >= 1
        # Fallback text
        assert "Stockfish" in advice.candidate_moves[0].explanation


class TestTeachingMode:
    """Tests for TEACHING GameMode."""

    def test_teaching_mode_exists(self):
        assert GameMode.TEACHING in list(GameMode)

    def test_teaching_mode_player_types(self):
        from chess_alive.players.base import PlayerType

        assert GameMode.TEACHING.white_player_type == PlayerType.HUMAN
        assert GameMode.TEACHING.black_player_type == PlayerType.COMPUTER

    def test_teaching_mode_has_human(self):
        assert GameMode.TEACHING.has_human

    def test_teaching_mode_has_computer(self):
        assert GameMode.TEACHING.has_computer

    def test_teaching_mode_requires_stockfish(self):
        assert GameMode.TEACHING.requires_stockfish

    def test_teaching_mode_requires_openrouter(self):
        assert GameMode.TEACHING.requires_openrouter

    def test_teaching_mode_description(self):
        assert "teaching" in GameMode.TEACHING.description.lower()

    def test_teaching_mode_from_string(self):
        assert GameMode.from_string("teaching") == GameMode.TEACHING
        assert GameMode.from_string("teach") == GameMode.TEACHING
        assert GameMode.from_string("TEACHING") == GameMode.TEACHING

    def test_teaching_mode_defaults(self):
        defaults = GameMode.TEACHING.defaults
        assert defaults.stockfish_skill == 15
        assert defaults.max_moves == 500

    def test_list_all_includes_teaching(self):
        all_modes = GameMode.list_all()
        mode_names = [m.name for m, _ in all_modes]
        assert "TEACHING" in mode_names


class TestMatchConfigTeaching:
    """Tests for MatchConfig with teaching enabled."""

    def test_default_enable_teaching_false(self):
        config = MatchConfig()
        assert config.enable_teaching is False

    def test_enable_teaching_true(self):
        config = MatchConfig(mode=GameMode.TEACHING, enable_teaching=True)
        assert config.enable_teaching is True

    @pytest.mark.asyncio
    async def test_match_setup_teaching_no_stockfish(self):
        """Match setup for TEACHING fails cleanly if Stockfish is not found."""
        from chess_alive.config import GameConfig
        from unittest.mock import patch

        config = MatchConfig(mode=GameMode.TEACHING)
        game_config = GameConfig()
        game_config.engine.path = None

        match = Match(config, game_config)

        with patch("chess_alive.players.computer.find_stockfish", return_value=None):
            with pytest.raises(RuntimeError, match="Stockfish not found"):
                await match.setup()

    @pytest.mark.asyncio
    async def test_match_teaching_advisor_created_when_llm_available(self):
        """TeachingAdvisor is created when LLM is configured and mode is TEACHING."""
        from chess_alive.config import GameConfig
        from unittest.mock import patch, AsyncMock

        config = MatchConfig(mode=GameMode.TEACHING)
        game_config = GameConfig()
        game_config.llm = LLMConfig(api_key="test-key")
        game_config.engine.path = "/fake/stockfish"

        match = Match(config, game_config)

        with patch("chess_alive.players.computer.find_stockfish", return_value="/fake/stockfish"):
            with patch("chess.engine.popen_uci", new=AsyncMock(
                return_value=(MagicMock(), MagicMock(configure=AsyncMock()))
            )):
                await match.setup()

        assert match.teaching_advisor is not None

    @pytest.mark.asyncio
    async def test_match_cleanup_closes_teaching_advisor(self):
        """_cleanup() calls close() on the teaching advisor."""
        config = MatchConfig()
        match = Match(config)

        mock_advisor = AsyncMock()
        mock_advisor.close = AsyncMock()
        match.teaching_advisor = mock_advisor

        await match._cleanup()

        mock_advisor.close.assert_called_once()
        assert match.teaching_advisor is None
