"""LLM-powered commentary system for chess pieces."""

import asyncio
from dataclasses import dataclass, field
from typing import Optional
import random

from .client import LLMClient, LLMError
from ..core.game import ChessGame, MoveRecord
from ..core.piece import Piece, PieceType, Color


@dataclass
class Commentary:
    """A piece of commentary from a chess piece."""

    piece: Piece
    text: str
    move_context: Optional[MoveRecord] = None
    commentary_type: str = "move"  # "move", "capture", "check", "promotion", "reaction"


class PieceVoice:
    """Generates commentary in a piece's voice using LLM."""

    def __init__(self, piece: Piece, client: LLMClient):
        """
        Initialize piece voice.

        Args:
            piece: The chess piece
            client: LLM client for API calls
        """
        self.piece = piece
        self.client = client
        self._recent_commentary: list[str] = []

    def _get_system_prompt(self) -> str:
        """Get the system prompt for this piece's voice."""
        personality = self.piece.personality.to_prompt_context()

        return f"""You are a {self.piece.piece_type.name_str.lower()} chess piece on the {self.piece.color.name_str.lower()} side.
{personality}

You provide brief, in-character commentary during a chess game. Your commentary should:
1. Stay in character based on your personality
2. Be brief (1-2 sentences max)
3. Reference the game situation appropriately
4. Never break character or mention you're an AI
5. Show personality through word choice and tone

Remember: You ARE this chess piece, speaking about the game from your perspective on the board."""

    async def comment_on_move(
        self,
        game: ChessGame,
        move_record: MoveRecord,
        is_own_move: bool,
    ) -> str:
        """
        Generate commentary for a move.

        Args:
            game: Current game state
            move_record: The move that was made
            is_own_move: Whether this piece made the move

        Returns:
            Commentary text
        """
        context_parts = []

        if is_own_move:
            context_parts.append(
                f"You just moved from {move_record.move.from_square} to {move_record.move.to_square} ({move_record.san})."
            )
            if move_record.captured_piece:
                context_parts.append(
                    f"You captured the enemy {move_record.captured_piece.piece_type.name_str}!"
                )
            if move_record.is_check:
                context_parts.append("Your move puts the enemy king in check!")
            if move_record.is_checkmate:
                context_parts.append("CHECKMATE! You've won the game!")
        else:
            context_parts.append(
                f"The {move_record.piece.color.name_str} {move_record.piece.piece_type.name_str} "
                f"moved {move_record.san}."
            )
            if move_record.captured_piece == self.piece:
                context_parts.append("You have been captured!")
            if move_record.is_check and self.piece.piece_type == PieceType.KING:
                context_parts.append("You are in check!")

        context = " ".join(context_parts)

        prompt = f"""Game situation: {context}

The board position shows {'an intense' if game.is_check else 'a developing'} game.
Move number: {game.fullmove_number}

Give a brief, in-character reaction (1-2 sentences). Don't explain the move technically - react emotionally/dramatically as your character would."""

        try:
            return await self.client.complete(
                prompt,
                system_prompt=self._get_system_prompt(),
                temperature=0.8,
                max_tokens=100,
            )
        except LLMError:
            # Fallback to template-based commentary
            return self._fallback_commentary(move_record, is_own_move)

    async def comment_on_situation(self, game: ChessGame, situation: str) -> str:
        """
        Generate commentary for a general situation.

        Args:
            game: Current game state
            situation: Description of the situation

        Returns:
            Commentary text
        """
        prompt = f"""Current situation: {situation}

You are at square {self.piece.square_name}. The game is at move {game.fullmove_number}.

Give a brief, in-character comment about this situation (1-2 sentences)."""

        try:
            return await self.client.complete(
                prompt,
                system_prompt=self._get_system_prompt(),
                temperature=0.8,
                max_tokens=100,
            )
        except LLMError:
            return self._generic_fallback(situation)

    def _fallback_commentary(self, move_record: MoveRecord, is_own_move: bool) -> str:
        """Generate fallback commentary without LLM."""
        personality = self.piece.personality

        if is_own_move:
            if move_record.captured_piece:
                if personality.aggression >= 7:
                    return random.choice([
                        "Victory! Another enemy falls!",
                        "That's what happens when you stand in my way!",
                        "One less foe to worry about!",
                    ])
                else:
                    return random.choice([
                        "A necessary sacrifice on their part.",
                        "The position demanded this exchange.",
                        "Sometimes pieces must fall.",
                    ])
            elif move_record.is_check:
                return random.choice([
                    "Check! The king trembles!",
                    "Your majesty should watch their back!",
                    "The hunt is on!",
                ])
            else:
                return random.choice([
                    "Onward!",
                    "A solid move.",
                    "The plan unfolds.",
                    "Position secured.",
                ])
        else:
            if move_record.is_check:
                if self.piece.piece_type == PieceType.KING:
                    return random.choice([
                        "They dare threaten me?!",
                        "A temporary inconvenience...",
                        "We must address this threat.",
                    ])
                return "Our king is threatened!"
            return random.choice([
                "Interesting...",
                "Let's see where this leads.",
                "They make their move.",
            ])

    def _generic_fallback(self, situation: str) -> str:
        """Generic fallback for situation commentary."""
        return f"The game continues..."


class CommentaryEngine:
    """Manages commentary from all pieces during a game."""

    def __init__(
        self,
        client: LLMClient,
        commentary_frequency: str = "every_move",
    ):
        """
        Initialize commentary engine.

        Args:
            client: LLM client for API calls
            commentary_frequency: When to generate commentary
                - "every_move": Commentary on every move
                - "captures_only": Only on captures
                - "key_moments": Captures, checks, promotions
        """
        self.client = client
        self.frequency = commentary_frequency
        self._voices: dict[tuple[PieceType, Color], PieceVoice] = {}

    def _get_voice(self, piece: Piece) -> PieceVoice:
        """Get or create a voice for a piece."""
        key = (piece.piece_type, piece.color)
        if key not in self._voices:
            self._voices[key] = PieceVoice(piece, self.client)
        voice = self._voices[key]
        voice.piece = piece  # Update with current piece state
        return voice

    def should_generate_commentary(self, move_record: MoveRecord) -> bool:
        """Check if commentary should be generated for this move."""
        if self.frequency == "every_move":
            return True
        elif self.frequency == "captures_only":
            return move_record.captured_piece is not None
        elif self.frequency == "key_moments":
            return (
                move_record.captured_piece is not None
                or move_record.is_check
                or move_record.is_checkmate
                or move_record.is_promotion
                or move_record.is_castling
            )
        return False

    async def generate_move_commentary(
        self,
        game: ChessGame,
        move_record: MoveRecord,
        include_reactions: bool = True,
    ) -> list[Commentary]:
        """
        Generate commentary for a move.

        Args:
            game: Current game state
            move_record: The move that was made
            include_reactions: Whether to include reactions from other pieces

        Returns:
            List of Commentary objects
        """
        if not self.should_generate_commentary(move_record):
            return []

        commentaries = []

        # Commentary from the moving piece
        moving_piece = move_record.piece
        voice = self._get_voice(moving_piece)
        text = await voice.comment_on_move(game, move_record, is_own_move=True)
        commentaries.append(
            Commentary(
                piece=moving_piece,
                text=text,
                move_context=move_record,
                commentary_type="move",
            )
        )

        # Commentary from captured piece (if any)
        if move_record.captured_piece:
            captured_voice = self._get_voice(move_record.captured_piece)
            captured_text = await captured_voice.comment_on_move(
                game, move_record, is_own_move=False
            )
            commentaries.append(
                Commentary(
                    piece=move_record.captured_piece,
                    text=captured_text,
                    move_context=move_record,
                    commentary_type="capture",
                )
            )

        # Reactions from other pieces (optional, limited)
        if include_reactions and (move_record.is_check or move_record.is_checkmate):
            # Get the king that's in check
            opposite_color = move_record.piece.color.opposite
            for piece in game.get_pieces_by_color(opposite_color):
                if piece.piece_type == PieceType.KING:
                    king_voice = self._get_voice(piece)
                    king_text = await king_voice.comment_on_move(
                        game, move_record, is_own_move=False
                    )
                    commentaries.append(
                        Commentary(
                            piece=piece,
                            text=king_text,
                            move_context=move_record,
                            commentary_type="reaction",
                        )
                    )
                    break

        return commentaries

    async def generate_game_start_commentary(
        self, game: ChessGame
    ) -> list[Commentary]:
        """Generate opening commentary from key pieces."""
        commentaries = []

        # Let kings make opening statements
        for color in [Color.WHITE, Color.BLACK]:
            for piece in game.get_pieces_by_color(color):
                if piece.piece_type == PieceType.KING:
                    voice = self._get_voice(piece)
                    text = await voice.comment_on_situation(
                        game, "The game is about to begin!"
                    )
                    commentaries.append(
                        Commentary(
                            piece=piece,
                            text=text,
                            commentary_type="game_start",
                        )
                    )
                    break

        return commentaries

    async def generate_game_end_commentary(
        self, game: ChessGame
    ) -> list[Commentary]:
        """Generate ending commentary."""
        commentaries = []

        result = game.result
        if result == game.result.IN_PROGRESS:
            return commentaries

        # Let kings react to the result
        situation = {
            game.result.WHITE_WINS: "White has won the game!",
            game.result.BLACK_WINS: "Black has won the game!",
            game.result.DRAW: "The game is a draw!",
        }.get(result, "The game has ended.")

        for color in [Color.WHITE, Color.BLACK]:
            for piece in game.get_pieces_by_color(color):
                if piece.piece_type == PieceType.KING:
                    voice = self._get_voice(piece)
                    text = await voice.comment_on_situation(game, situation)
                    commentaries.append(
                        Commentary(
                            piece=piece,
                            text=text,
                            commentary_type="game_end",
                        )
                    )
                    break

        return commentaries
