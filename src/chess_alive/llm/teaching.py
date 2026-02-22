"""LLM + Stockfish teaching advisor for chess coaching."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import chess
import chess.engine

from .client import LLMClient, LLMError
from ..core.game import ChessGame
from ..core.piece import Color
from ..config import EngineConfig


@dataclass
class CandidateMove:
    """A candidate move with coaching analysis."""

    san: str
    evaluation: str  # e.g. "+0.50", "Mate in 3"
    explanation: str  # Why this move is good
    likely_response: str  # Opponent's expected reply
    follow_up_plan: str  # Strategic follow-up goal


@dataclass
class TeachingAdvice:
    """Complete teaching advice for a position."""

    position_assessment: str
    candidate_moves: list[CandidateMove]
    player_color: str
    move_number: int
    generated_at: datetime = field(default_factory=datetime.now)


class TeachingAdvisor:
    """Combines Stockfish multi-line analysis with LLM explanation for coaching.

    For each of the player's top candidate moves (per Stockfish) the advisor:
    1. Evaluates the move with Stockfish (centipawn / mate score).
    2. Simulates the opponent's best response using Stockfish.
    3. Asks the LLM to explain the move, the likely response, and the
       follow-up plan in natural language.

    This produces a structured :class:`TeachingAdvice` that is emitted
    before each human move in Teaching mode.
    """

    NUM_CANDIDATES = 3
    ANALYSIS_DEPTH = 15
    RESPONSE_DEPTH = 10
    MAX_FALLBACK_TEXT_LENGTH = 200

    def __init__(self, llm_client: LLMClient, engine_config: EngineConfig):
        """
        Initialize the teaching advisor.

        Args:
            llm_client: LLM client for generating explanations.
            engine_config: Stockfish engine configuration.
        """
        self.llm_client = llm_client
        self.engine_config = engine_config
        self._engine: Optional[chess.engine.Protocol] = None
        self._transport = None

    # ------------------------------------------------------------------
    # Engine management
    # ------------------------------------------------------------------

    async def _ensure_engine(self):
        """Ensure Stockfish engine is running."""
        if self._engine is not None:
            return
        if not self.engine_config.path:
            raise RuntimeError(
                "Stockfish path not configured. Set STOCKFISH_PATH environment variable."
            )
        try:
            self._transport, self._engine = await chess.engine.popen_uci(
                self.engine_config.path
            )
            await self._engine.configure({
                "Threads": self.engine_config.threads,
                "Hash": self.engine_config.hash_size,
            })
        except Exception as e:
            raise RuntimeError(f"Failed to start Stockfish: {e}") from e

    async def close(self):
        """Shut down the Stockfish engine."""
        if self._engine:
            await self._engine.quit()
            self._engine = None
            self._transport = None

    # ------------------------------------------------------------------
    # Stockfish helpers
    # ------------------------------------------------------------------

    def _format_score(
        self, score: chess.engine.PovScore, player_color: chess.Color
    ) -> str:
        """Format a PovScore relative to the player's perspective."""
        pov = score.pov(player_color)
        if pov.is_mate():
            m = pov.mate()
            if m is not None:
                return f"Mate in {abs(m)}" if m > 0 else f"Opp mates in {abs(m)}"
        cp = pov.score()
        if cp is None:
            return "0.00"
        val = cp / 100.0
        return f"+{val:.2f}" if val >= 0 else f"{val:.2f}"

    async def _get_candidate_moves(
        self, game: ChessGame
    ) -> list[tuple[chess.Move, str]]:
        """Return top N candidate moves with Stockfish evaluation strings."""
        await self._ensure_engine()
        assert self._engine is not None

        depth = max(self.ANALYSIS_DEPTH, self.engine_config.depth)
        analysis = await self._engine.analyse(
            game.board,
            chess.engine.Limit(depth=depth),
            multipv=self.NUM_CANDIDATES,
        )

        player_color = game.board.turn
        candidates: list[tuple[chess.Move, str]] = []
        for info in analysis:
            pv = info.get("pv")
            if not pv:
                continue
            move = pv[0]
            score = info.get("score")
            eval_str = self._format_score(score, player_color) if score else "?"
            candidates.append((move, eval_str))
        return candidates

    async def _get_opponent_response(
        self, game: ChessGame, candidate_move: chess.Move
    ) -> Optional[str]:
        """Get opponent's best SAN reply after *candidate_move* is played."""
        await self._ensure_engine()
        assert self._engine is not None

        temp_board = game.board.copy()
        temp_board.push(candidate_move)
        if temp_board.is_game_over():
            return None

        result = await self._engine.play(
            temp_board,
            chess.engine.Limit(depth=self.RESPONSE_DEPTH),
        )
        if result.move is None:
            return None
        return temp_board.san(result.move)

    # ------------------------------------------------------------------
    # Main public API
    # ------------------------------------------------------------------

    async def analyze(self, game: ChessGame) -> TeachingAdvice:
        """Analyze the current position and return coaching advice.

        Args:
            game: The current game state.

        Returns:
            :class:`TeachingAdvice` with position assessment and up to
            :attr:`NUM_CANDIDATES` candidate moves.
        """
        player_color = game.current_turn

        # Step 1: Stockfish multi-line analysis
        candidates = await self._get_candidate_moves(game)

        # Step 2: Opponent response for each candidate
        move_data: list[tuple[str, str, str]] = []
        for move, eval_str in candidates:
            san = game.board.san(move)
            opp_san = await self._get_opponent_response(game, move) or ""
            move_data.append((san, eval_str, opp_san))

        # Step 3: LLM explanations
        try:
            advice = await self._generate_llm_advice(game, move_data, player_color)
        except (LLMError, RuntimeError):
            advice = self._fallback_advice(game, move_data, player_color)

        return advice

    # ------------------------------------------------------------------
    # LLM prompt / parsing
    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        game: ChessGame,
        move_data: list[tuple[str, str, str]],
        player_color: Color,
    ) -> str:
        """Build the LLM coaching prompt."""
        moves_lines = []
        for i, (san, ev, opp) in enumerate(move_data, 1):
            opp_part = f", opponent may respond: {opp}" if opp else ""
            moves_lines.append(f"{i}. {san} (eval: {ev}{opp_part})")
        moves_text = "\n".join(moves_lines)

        in_check = " — currently in check" if game.is_check else ""

        # Build the MOVE sections dynamically so there's no stray placeholder text
        move_sections = []
        for san, _ev, _opp in move_data:
            move_sections.append(
                f"MOVE ({san}):\n"
                "- Why: [1 sentence tactical/strategic reason]\n"
                "- Response: [opponent's likely reply and why]\n"
                "- Follow-up: [player's next strategic goal]"
            )
        moves_format = "\n\n".join(move_sections)

        return (
            "You are a chess coach giving concise guidance to a student.\n\n"
            f"Position (FEN): {game.fen}\n"
            f"Player's color: {player_color.name_str}\n"
            f"Move number: {game.fullmove_number}{in_check}\n\n"
            f"Stockfish's top candidate moves:\n{moves_text}\n\n"
            "Provide coaching advice in exactly this format "
            "(keep each section to 1-2 sentences):\n\n"
            "POSITION: [Brief assessment of the position]\n\n"
            f"{moves_format}"
        )

    async def _generate_llm_advice(
        self,
        game: ChessGame,
        move_data: list[tuple[str, str, str]],
        player_color: Color,
    ) -> TeachingAdvice:
        """Call the LLM and parse its response into :class:`TeachingAdvice`."""
        system = (
            "You are a patient, knowledgeable chess coach. "
            "Give clear, educational explanations to help players understand "
            "tactical and strategic reasons behind moves. Be concise."
        )
        prompt = self._build_prompt(game, move_data, player_color)
        response = await self.llm_client.complete(
            prompt,
            system_prompt=system,
            temperature=0.3,
            max_tokens=600,
        )
        return self._parse_response(response, move_data, player_color, game.fullmove_number)

    def _parse_response(
        self,
        response: str,
        move_data: list[tuple[str, str, str]],
        player_color: Color,
        move_number: int,
    ) -> TeachingAdvice:
        """Parse the LLM text response into structured :class:`TeachingAdvice`."""
        position_assessment = ""
        candidate_moves: list[CandidateMove] = []

        # Collect current move fields while scanning
        cur_san = ""
        cur_eval = ""
        cur_why = ""
        cur_response = ""
        cur_followup = ""

        def _flush():
            nonlocal cur_san, cur_eval, cur_why, cur_response, cur_followup
            if cur_san:
                candidate_moves.append(
                    CandidateMove(
                        san=cur_san,
                        evaluation=cur_eval,
                        explanation=cur_why,
                        likely_response=cur_response,
                        follow_up_plan=cur_followup,
                    )
                )
            cur_san = cur_eval = cur_why = cur_response = cur_followup = ""

        for raw_line in response.splitlines():
            line = raw_line.strip()
            if line.upper().startswith("POSITION:"):
                position_assessment = line[len("POSITION:"):].strip()
            elif line.upper().startswith("MOVE"):
                _flush()
                # Extract SAN from "MOVE (e4):" or "MOVE 1 (e4):"
                m = re.search(r"\(([^)]+)\)", line)
                if m:
                    cur_san = m.group(1)
                    # Find matching eval from move_data
                    cur_eval = next(
                        (ev for san, ev, _ in move_data if san == cur_san), "?"
                    )
            elif line.startswith("- Why:"):
                cur_why = line[len("- Why:"):].strip()
            elif line.startswith("- Response:"):
                cur_response = line[len("- Response:"):].strip()
            elif line.startswith("- Follow-up:"):
                cur_followup = line[len("- Follow-up:"):].strip()

        _flush()  # save last move

        # Fallback: if parsing yielded nothing useful, use raw data
        if not candidate_moves:
            for san, ev, _ in move_data:
                candidate_moves.append(
                    CandidateMove(
                        san=san,
                        evaluation=ev,
                        explanation=response.strip()[:self.MAX_FALLBACK_TEXT_LENGTH] if not candidate_moves else "",
                        likely_response="",
                        follow_up_plan="",
                    )
                )
        if not position_assessment:
            position_assessment = response.strip().splitlines()[0][:self.MAX_FALLBACK_TEXT_LENGTH]

        return TeachingAdvice(
            position_assessment=position_assessment,
            candidate_moves=candidate_moves,
            player_color=player_color.name_str,
            move_number=move_number,
        )

    # ------------------------------------------------------------------
    # Fallback (no LLM)
    # ------------------------------------------------------------------

    def _fallback_advice(
        self,
        game: ChessGame,
        move_data: list[tuple[str, str, str]],
        player_color: Color,
    ) -> TeachingAdvice:
        """Generate basic advice without LLM (Stockfish data only)."""
        candidate_moves = [
            CandidateMove(
                san=san,
                evaluation=ev,
                explanation="Stockfish's recommended move.",
                likely_response=(
                    f"Opponent may play {opp}." if opp else "No immediate forced response."
                ),
                follow_up_plan="Continue developing pieces and controlling the center.",
            )
            for san, ev, opp in move_data
        ]
        return TeachingAdvice(
            position_assessment=(
                "You are in check — prioritize escaping." if game.is_check
                else "Develop your pieces and contest the center."
            ),
            candidate_moves=candidate_moves,
            player_color=player_color.name_str,
            move_number=game.fullmove_number,
        )
