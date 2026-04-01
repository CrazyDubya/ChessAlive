"""Position analysis with piece commentary."""

import asyncio
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from enum import Enum
import chess
import chess.engine

from ..llm.client import LLMClient
from ..core.game import ChessGame, MoveRecord
from ..core.piece import DEFAULT_PERSONALITIES, PieceType, Color


class InsightType(Enum):
    """Types of positional insights."""
    BLUNDER = "blunder"           # Major mistake (-2.0+ pawns)
    MISTAKE = "mistake"           # Minor mistake (-1.0 to -2.0)
    INACCURACY = "inaccuracy"     # Small error (-0.5 to -1.0)
    GOOD_MOVE = "good"            # Solid move
    EXCELLENT = "excellent"       # Strong move (+0.5 to +1.0)
    BRILLIANT = "brilliant"       # Exceptional (+1.0+ unexpected)
    TURNING_POINT = "turning"     # Eval crosses threshold
    MISSED_WIN = "missed_win"     # Had winning position, lost it


INSIGHT_THRESHOLDS = {
    InsightType.BLUNDER: -2.0,
    InsightType.MISTAKE: -1.0,
    InsightType.INACCURACY: -0.5,
    InsightType.EXCELLENT: 0.5,
    InsightType.BRILLIANT: 1.0,
}


@dataclass
class PositionInsight:
    """Analysis of a key moment from piece perspective."""
    move_number: int
    move_san: str
    insight_type: InsightType

    # Evaluation data
    eval_before: float
    eval_after: float
    eval_delta: float
    best_move: Optional[str] = None
    best_eval: Optional[float] = None

    # Piece commentary
    piece_name: str = ""
    piece_quote: str = ""

    # Secondary perspective
    secondary_piece: Optional[str] = None
    secondary_quote: Optional[str] = None

    # Position info
    fen_before: str = ""
    fen_after: str = ""


@dataclass
class GameAnalysis:
    """Complete analysis of a game."""
    insights: List[PositionInsight]
    total_moves: int
    blunders: int
    mistakes: int
    inaccuracies: int
    brilliancies: int
    average_eval_loss: float
    summary: str = ""


class PositionAnalyzer:
    """Analyzes chess positions using Stockfish and LLM commentary."""

    def __init__(
        self,
        stockfish_path: str,
        llm_client: Optional[LLMClient] = None,
        depth: int = 18,
    ):
        """Initialize the analyzer."""
        self.stockfish_path = stockfish_path
        self.llm_client = llm_client
        self.depth = depth
        self._engine: Optional[chess.engine.SimpleEngine] = None

    async def _get_engine(self) -> chess.engine.SimpleEngine:
        """Get or create the engine."""
        if self._engine is None:
            self._engine = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            )
        return self._engine

    async def close(self):
        """Close the engine."""
        if self._engine:
            self._engine.quit()
            self._engine = None

    async def evaluate_position(self, board: chess.Board) -> float:
        """Get centipawn evaluation for a position."""
        engine = await self._get_engine()

        info = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: engine.analyse(board, chess.engine.Limit(depth=self.depth))
        )

        score = info["score"].relative
        if score.is_mate():
            mate_in = score.mate()
            return 100.0 if mate_in > 0 else -100.0
        return score.score() / 100.0  # Convert to pawns

    async def get_best_move(self, board: chess.Board) -> Tuple[str, float]:
        """Get the best move and its evaluation."""
        engine = await self._get_engine()

        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: engine.play(board, chess.engine.Limit(depth=self.depth))
        )

        best_move = board.san(result.move)

        # Get eval after best move
        board_copy = board.copy()
        board_copy.push(result.move)
        best_eval = await self.evaluate_position(board_copy)

        return best_move, best_eval

    def _classify_insight(
        self,
        eval_before: float,
        eval_after: float,
        is_white_move: bool,
    ) -> InsightType:
        """Classify the significance of an eval change."""
        # Adjust for perspective (white wants positive, black wants negative)
        delta = eval_after - eval_before
        if not is_white_move:
            delta = -delta  # From black's perspective

        # Check for turning points
        if (eval_before > 0.5 and eval_after < -0.5) or (eval_before < -0.5 and eval_after > 0.5):
            return InsightType.TURNING_POINT

        # Check for missed wins
        if abs(eval_before) > 3.0 and abs(eval_after) < 1.0:
            return InsightType.MISSED_WIN

        # Classify by magnitude
        if delta <= INSIGHT_THRESHOLDS[InsightType.BLUNDER]:
            return InsightType.BLUNDER
        elif delta <= INSIGHT_THRESHOLDS[InsightType.MISTAKE]:
            return InsightType.MISTAKE
        elif delta <= INSIGHT_THRESHOLDS[InsightType.INACCURACY]:
            return InsightType.INACCURACY
        elif delta >= INSIGHT_THRESHOLDS[InsightType.BRILLIANT]:
            return InsightType.BRILLIANT
        elif delta >= INSIGHT_THRESHOLDS[InsightType.EXCELLENT]:
            return InsightType.EXCELLENT
        else:
            return InsightType.GOOD_MOVE

    def _get_piece_from_move(self, board: chess.Board, move_san: str) -> Tuple[str, Color]:
        """Get the piece type and color from a move."""
        # Parse the move
        if move_san.startswith("O-O"):
            return "King", Color.WHITE if board.turn else Color.BLACK

        piece_char = move_san[0] if move_san[0].isupper() else "P"
        piece_map = {
            "K": "King", "Q": "Queen", "R": "Rook",
            "B": "Bishop", "N": "Knight", "P": "Pawn"
        }
        piece_type = piece_map.get(piece_char, "Pawn")
        color = Color.WHITE if board.turn else Color.BLACK

        return piece_type, color

    def _get_piece_personality_name(self, piece_type: str, color: Color) -> str:
        """Get the personality name for a piece."""
        type_map = {
            "King": PieceType.KING,
            "Queen": PieceType.QUEEN,
            "Rook": PieceType.ROOK,
            "Bishop": PieceType.BISHOP,
            "Knight": PieceType.KNIGHT,
            "Pawn": PieceType.PAWN,
        }
        ptype = type_map.get(piece_type, PieceType.PAWN)
        personality = DEFAULT_PERSONALITIES.get((ptype, color))
        if personality:
            return personality.name
        return f"{color.name_str} {piece_type}"

    async def _generate_piece_commentary(
        self,
        insight: PositionInsight,
        move_san: str,
        piece_name: str,
        insight_type: InsightType,
    ) -> str:
        """Generate commentary from the piece's perspective."""
        if not self.llm_client:
            return self._fallback_commentary(insight_type, piece_name)

        personality = None
        for (ptype, color), p in DEFAULT_PERSONALITIES.items():
            if p.name == piece_name:
                personality = p
                break

        if not personality:
            return self._fallback_commentary(insight_type, piece_name)

        insight_context = {
            InsightType.BLUNDER: "This was a terrible blunder that lost significant material or position.",
            InsightType.MISTAKE: "This was a mistake that weakened our position.",
            InsightType.INACCURACY: "This was a small inaccuracy.",
            InsightType.GOOD_MOVE: "This was a solid, good move.",
            InsightType.EXCELLENT: "This was an excellent move that improved our position significantly.",
            InsightType.BRILLIANT: "This was a brilliant, unexpected move!",
            InsightType.TURNING_POINT: "This move changed the course of the game entirely.",
            InsightType.MISSED_WIN: "We had a winning position but let it slip away.",
        }

        prompt = f"""You are {piece_name}, a chess piece.

Your personality: {personality.archetype}, speaks in a {personality.speaking_style} manner.
{personality.backstory}

The move {move_san} was played. {insight_context.get(insight_type, 'Analyze this moment.')}

Evaluation changed from {insight.eval_before:.1f} to {insight.eval_after:.1f} ({"improved" if insight.eval_delta > 0 else "worsened"} by {abs(insight.eval_delta):.1f}).
{f"The best move was {insight.best_move}." if insight.best_move and insight.best_move != move_san else ""}

Give a brief (1-2 sentences) in-character reaction to this moment. Show emotion appropriate to the situation."""

        try:
            return await self.llm_client.complete(
                prompt,
                temperature=0.8,
                max_tokens=100,
            )
        except Exception:
            return self._fallback_commentary(insight_type, piece_name)

    def _fallback_commentary(self, insight_type: InsightType, piece_name: str) -> str:
        """Generate fallback commentary without LLM."""
        templates = {
            InsightType.BLUNDER: [
                "What have I done?! This is a disaster!",
                "No... no, this cannot be!",
                "A grievous error. The consequences will be dire.",
            ],
            InsightType.MISTAKE: [
                "That was not my finest moment.",
                "I should have seen that coming.",
                "A misstep. We must recover.",
            ],
            InsightType.INACCURACY: [
                "Not optimal, but we continue.",
                "There may have been a better path.",
                "Hmm, perhaps I could have done better.",
            ],
            InsightType.GOOD_MOVE: [
                "A solid move. The plan unfolds.",
                "Onward we march.",
                "Position secured.",
            ],
            InsightType.EXCELLENT: [
                "Yes! This is the way!",
                "The initiative is ours!",
                "They will feel the pressure now.",
            ],
            InsightType.BRILLIANT: [
                "Behold! A stroke of genius!",
                "They never saw it coming!",
                "This is what victory looks like!",
            ],
            InsightType.TURNING_POINT: [
                "The tide has turned!",
                "Everything changes now.",
                "This moment will be remembered.",
            ],
            InsightType.MISSED_WIN: [
                "We had them... and let them slip away.",
                "Victory was within grasp.",
                "If only we had seen the winning path.",
            ],
        }
        import random
        options = templates.get(insight_type, ["The game continues..."])
        return random.choice(options)

    async def analyze_game(
        self,
        game: ChessGame,
        include_all_moves: bool = False,
    ) -> GameAnalysis:
        """Analyze a complete game."""
        insights = []
        board = chess.Board()

        blunders = 0
        mistakes = 0
        inaccuracies = 0
        brilliancies = 0
        total_eval_loss = 0.0

        eval_before = await self.evaluate_position(board)

        for i, record in enumerate(game.move_history):
            move_san = record.san
            is_white = (i % 2) == 0

            # Make the move
            try:
                move = board.parse_san(move_san)
                fen_before = board.fen()
                board.push(move)
                fen_after = board.fen()
            except ValueError:
                continue

            eval_after = await self.evaluate_position(board)
            eval_delta = eval_after - eval_before

            # Get best move for comparison
            board_copy = chess.Board(fen_before)
            try:
                best_move, best_eval = await self.get_best_move(board_copy)
            except Exception:
                best_move, best_eval = None, None

            # Classify the move
            insight_type = self._classify_insight(eval_before, eval_after, is_white)

            # Count by type
            if insight_type == InsightType.BLUNDER:
                blunders += 1
            elif insight_type == InsightType.MISTAKE:
                mistakes += 1
            elif insight_type == InsightType.INACCURACY:
                inaccuracies += 1
            elif insight_type == InsightType.BRILLIANT:
                brilliancies += 1

            # Calculate eval loss
            if best_eval is not None:
                loss = abs(best_eval - eval_after)
                total_eval_loss += loss

            # Only include significant moments unless include_all_moves
            if include_all_moves or insight_type not in [InsightType.GOOD_MOVE]:
                piece_type, color = self._get_piece_from_move(chess.Board(fen_before), move_san)
                piece_name = self._get_piece_personality_name(piece_type, color)

                insight = PositionInsight(
                    move_number=(i // 2) + 1,
                    move_san=move_san,
                    insight_type=insight_type,
                    eval_before=eval_before,
                    eval_after=eval_after,
                    eval_delta=eval_delta,
                    best_move=best_move,
                    best_eval=best_eval,
                    piece_name=piece_name,
                    fen_before=fen_before,
                    fen_after=fen_after,
                )

                # Generate commentary
                insight.piece_quote = await self._generate_piece_commentary(
                    insight, move_san, piece_name, insight_type
                )

                insights.append(insight)

            eval_before = eval_after

        # Calculate average eval loss
        avg_loss = total_eval_loss / len(game.move_history) if game.move_history else 0

        return GameAnalysis(
            insights=insights,
            total_moves=len(game.move_history),
            blunders=blunders,
            mistakes=mistakes,
            inaccuracies=inaccuracies,
            brilliancies=brilliancies,
            average_eval_loss=avg_loss,
        )

    async def analyze_position(self, fen: str) -> dict:
        """Analyze a single position."""
        board = chess.Board(fen)
        evaluation = await self.evaluate_position(board)
        best_move, best_eval = await self.get_best_move(board)

        return {
            "fen": fen,
            "evaluation": evaluation,
            "best_move": best_move,
            "best_eval": best_eval,
            "is_check": board.is_check(),
            "is_checkmate": board.is_checkmate(),
            "is_stalemate": board.is_stalemate(),
            "legal_moves": [board.san(m) for m in board.legal_moves],
        }

    async def __aenter__(self):
        await self._get_engine()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
