"""Stockfish advisor that provides guidance for LLM move decisions."""

from dataclasses import dataclass
from typing import Optional
import chess
import chess.engine

from ..core.game import ChessGame
from ..config import EngineConfig


@dataclass
class MoveAnalysis:
    """Analysis of a single move from Stockfish."""
    san: str
    score_cp: Optional[int] = None  # Centipawns (from mover's perspective)
    is_best: bool = False
    is_blunder: bool = False  # Major mistake
    is_brilliant: bool = False  # Unexpected good move
    rank: int = 0  # Ranking among all legal moves (1 = best)
    tactical_note: str = ""  # Human-readable tactical note


@dataclass
class PositionGuidance:
    """Stockfish's guidance for the current position."""
    evaluation_cp: Optional[int] = None  # Position eval (from current player's perspective)
    best_move_san: Optional[str] = None
    top_moves: list[MoveAnalysis] = None
    threats: list[str] = None  # Tactical threats to watch
    positional_notes: list[str] = None  # Positional advice
    is_tactical: bool = False  # Sharp tactical position
    king_safety: str = "safe"  # safe, exposed, endangered

    def __post_init__(self):
        if self.top_moves is None:
            self.top_moves = []
        if self.threats is None:
            self.threats = []
        if self.positional_notes is None:
            self.positional_notes = []


class StockfishAdvisor:
    """Provides chess guidance from Stockfish for LLM decision-making."""

    # Score thresholds for categorizing moves
    BRILLIANT_THRESHOLD = 50  # cp above second-best
    BLUNDER_THRESHOLD = -150  # cp loss
    GOOD_MOVE_THRESHOLD = 30  # Within this of best is "good"

    def __init__(self, config: Optional[EngineConfig] = None):
        """Initialize the advisor."""
        self.config = config or EngineConfig()
        self._engine: Optional[chess.engine.SimpleEngine] = None
        self._transport = None

    async def _ensure_engine(self):
        """Ensure Stockfish is running."""
        if self._engine is not None:
            return

        if not self.config.path:
            raise RuntimeError("Stockfish path not configured for advisor")

        try:
            self._transport, self._engine = await chess.engine.popen_uci(
                self.config.path
            )
            await self._engine.configure({
                "Threads": self.config.threads,
                "Hash": self.config.hash_size,
            })
        except Exception as e:
            raise RuntimeError(f"Failed to start Stockfish advisor: {e}")

    async def analyze_position(
        self,
        game: ChessGame,
        depth: Optional[int] = None,
        top_n: int = 5,
    ) -> PositionGuidance:
        """
        Analyze the current position and provide guidance.

        Args:
            game: Current game state
            depth: Analysis depth (default from config)
            top_n: Number of top moves to analyze

        Returns:
            PositionGuidance with analysis and recommendations
        """
        await self._ensure_engine()
        assert self._engine is not None

        try:
            # Get overall position evaluation
            info = await self._engine.analyse(
                game.board,
                chess.engine.Limit(depth=depth or self.config.depth),
            )

            # Extract evaluation
            eval_cp = None
            if "score" in info:
                score = info["score"].relative
                if score.is_mate():
                    mate_in = score.mate()
                    eval_cp = 10000 if mate_in > 0 else -10000
                else:
                    eval_cp = score.score()

            # Analyze all legal moves
            legal_moves = list(game.get_legal_moves())
            move_analyses = []

            for move in legal_moves:
                analysis = await self._analyze_move(game, move, depth or 15)
                move_analyses.append(analysis)

            # Sort by score (best first)
            move_analyses.sort(key=lambda m: m.score_cp or -9999, reverse=True)

            # Assign rankings and flags
            if move_analyses:
                best_score = move_analyses[0].score_cp or 0
                for i, analysis in enumerate(move_analyses):
                    analysis.rank = i + 1
                    analysis.is_best = (i == 0)

                    # Check for brilliant/blunder
                    if analysis.score_cp is not None:
                        if i > 0 and best_score - analysis.score_cp > self.BLUNDER_THRESHOLD:
                            analysis.is_blunder = True
                        elif i == 0 and len(move_analyses) > 1:
                            second_best = move_analyses[1].score_cp or 0
                            if best_score - second_best > self.BRILLIANT_THRESHOLD:
                                analysis.is_brilliant = True

            # Get top moves
            top_moves = move_analyses[:top_n]

            # Identify tactical situation
            is_tactical = False
            if eval_cp is not None and abs(eval_cp) > 200:
                is_tactical = True

            # Check for immediate threats
            threats = await self._identify_threats(game)
            if threats:
                is_tactical = True

            # King safety assessment
            king_safety = await self._assess_king_safety(game)

            # Generate positional notes
            positional_notes = self._generate_positional_notes(game, move_analyses)

            return PositionGuidance(
                evaluation_cp=eval_cp,
                best_move_san=top_moves[0].san if top_moves else None,
                top_moves=top_moves,
                threats=threats,
                positional_notes=positional_notes,
                is_tactical=is_tactical,
                king_safety=king_safety,
            )

        except chess.engine.EngineTerminatedError:
            self._engine = None
            return PositionGuidance()

    async def _analyze_move(
        self,
        game: ChessGame,
        move: chess.Move,
        depth: int,
    ) -> MoveAnalysis:
        """Analyze a single move."""
        assert self._engine is not None

        san = game.board.san(move)

        # Make the move on a copy
        board_copy = game.board.copy()
        board_copy.push(move)

        try:
            # Evaluate resulting position (from opponent's perspective)
            info = await self._engine.analyse(
                board_copy,
                chess.engine.Limit(depth=depth),
            )

            score_cp = None
            if "score" in info:
                score = info["score"].relative
                if score.is_mate():
                    mate_in = score.mate()
                    # From mover's perspective, opponent getting mated is good
                    score_cp = -10000 if mate_in > 0 else 10000
                else:
                    # Negate because it's from opponent's perspective
                    score_cp = -(score.score() or 0)

            # Generate tactical note
            tactical_note = self._generate_tactical_note(game, move, board_copy)

            return MoveAnalysis(
                san=san,
                score_cp=score_cp,
                tactical_note=tactical_note,
            )

        except Exception:
            return MoveAnalysis(san=san)

    def _generate_tactical_note(
        self,
        game: ChessGame,
        move: chess.Move,
        resulting_board: chess.Board,
    ) -> str:
        """Generate a human-readable note about the move."""
        notes = []

        # Check for captures
        if game.board.is_capture(move):
            captured = game.board.piece_at(move.to_square)
            if captured:
                notes.append(f"captures {chess.piece_name(captured.piece_type)}")

        # Check for check
        if resulting_board.is_check():
            notes.append("gives check")

        # Check for castling
        if game.board.is_castling(move):
            notes.append("castles")

        # Check for promotion
        if move.promotion:
            notes.append(f"promotes to {chess.piece_name(move.promotion)}")

        return ", ".join(notes) if notes else ""

    async def _identify_threats(self, game: ChessGame) -> list[str]:
        """Identify tactical threats in the position."""
        threats = []

        # Check if we're in check
        if game.is_check:
            threats.append("You are in CHECK - must respond!")

        # Look for hanging pieces
        board = game.board
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == game.current_turn.value:
                # Check if this piece is attacked
                attackers = board.attackers(not piece.color, square)
                if attackers:
                    defenders = board.attackers(piece.color, square)
                    if len(attackers) > len(defenders):
                        piece_name = chess.piece_name(piece.piece_type)
                        threats.append(
                            f"Your {piece_name} on {chess.square_name(square)} is under attack!"
                        )

        return threats

    async def _assess_king_safety(self, game: ChessGame) -> str:
        """Assess king safety for the current player."""
        board = game.board
        king_square = board.king(game.current_turn.value)

        if king_square is None:
            return "endangered"

        # Count attackers around king
        king_zone = chess.BB_KING_ATTACKS[king_square]
        enemy_attacks = 0

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color != game.current_turn.value:
                if board.attacks(square) & king_zone:
                    enemy_attacks += 1

        if enemy_attacks >= 3:
            return "endangered"
        elif enemy_attacks >= 1:
            return "exposed"
        else:
            return "safe"

    def _generate_positional_notes(
        self,
        game: ChessGame,
        move_analyses: list[MoveAnalysis],
    ) -> list[str]:
        """Generate positional advice."""
        notes = []
        board = game.board

        # Check development
        if game.fullmove_number <= 10:
            developed_pieces = 0
            # Rough count of developed minor pieces
            back_rank = 0 if game.current_turn == chess.WHITE else 7
            for square in chess.SQUARES:
                piece = board.piece_at(square)
                if piece and piece.color == game.current_turn.value:
                    if piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                        if chess.square_rank(square) != back_rank:
                            developed_pieces += 1

            if developed_pieces < 2:
                notes.append("Consider developing your pieces")

        # Check center control
        center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
        center_control = sum(1 for sq in center_squares if board.is_attacked_by(game.current_turn.value, sq))
        if center_control < 2:
            notes.append("Controlling the center is important")

        # Check for good capturing opportunities
        for analysis in move_analyses[:3]:
            if "captures" in analysis.tactical_note and analysis.is_best:
                notes.append(f"A capture looks promising: {analysis.san}")
                break

        return notes

    def format_guidance_for_llm(self, guidance: PositionGuidance) -> str:
        """Format guidance as a prompt section for the LLM."""
        parts = ["<position_analysis>"]

        # Position evaluation
        if guidance.evaluation_cp is not None:
            if guidance.evaluation_cp > 500:
                parts.append("Position: You have a winning advantage!")
            elif guidance.evaluation_cp > 200:
                parts.append("Position: You have a clear advantage.")
            elif guidance.evaluation_cp > 50:
                parts.append("Position: You are slightly better.")
            elif guidance.evaluation_cp > -50:
                parts.append("Position: The position is roughly equal.")
            elif guidance.evaluation_cp > -200:
                parts.append("Position: Your opponent is slightly better.")
            else:
                parts.append("Position: You are under pressure - be careful!")

        # King safety
        if guidance.king_safety == "endangered":
            parts.append("WARNING: Your king is in danger!")
        elif guidance.king_safety == "exposed":
            parts.append("Note: Your king could be safer.")

        # Threats
        if guidance.threats:
            parts.append("Threats to address:")
            for threat in guidance.threats:
                parts.append(f"  - {threat}")

        # Top moves with notes
        if guidance.top_moves:
            parts.append("\nStockfish's top move suggestions:")
            for i, move in enumerate(guidance.top_moves[:5]):
                flag = ""
                if move.is_brilliant:
                    flag = " [BRILLIANT!]"
                elif move.is_best:
                    flag = " [BEST]"
                elif move.is_blunder:
                    flag = " [AVOID]"

                note = f" - {move.tactical_note}" if move.tactical_note else ""
                parts.append(f"  {i+1}. {move.san}{flag}{note}")

        # Positional notes
        if guidance.positional_notes:
            parts.append("\nPositional advice:")
            for note in guidance.positional_notes:
                parts.append(f"  - {note}")

        # Tactical warning
        if guidance.is_tactical:
            parts.append("\nThis is a TACTICAL position - look for tactics!")

        parts.append("</position_analysis>")
        parts.append("\nYou may follow Stockfish's suggestions or choose your own move. The final decision is YOURS.")

        return "\n".join(parts)

    async def cleanup(self):
        """Clean up engine resources."""
        if self._engine:
            await self._engine.quit()
            self._engine = None
            self._transport = None
