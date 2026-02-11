"""Piece representation with personality traits for LLM commentary."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import chess


class PieceType(Enum):
    """Chess piece types."""

    PAWN = chess.PAWN
    KNIGHT = chess.KNIGHT
    BISHOP = chess.BISHOP
    ROOK = chess.ROOK
    QUEEN = chess.QUEEN
    KING = chess.KING

    @property
    def symbol(self) -> str:
        """Get the piece symbol."""
        return str(chess.piece_symbol(self.value)).upper()

    @property
    def name_str(self) -> str:
        """Get human-readable name."""
        return str(chess.piece_name(self.value)).title()


class Color(Enum):
    """Chess piece colors."""

    WHITE = chess.WHITE
    BLACK = chess.BLACK

    @property
    def name_str(self) -> str:
        """Get color name."""
        return "White" if self.value else "Black"

    @property
    def opposite(self) -> "Color":
        """Get the opposite color."""
        return Color.BLACK if self == Color.WHITE else Color.WHITE


@dataclass
class PiecePersonality:
    """Personality traits that influence LLM commentary style."""

    # Core personality
    name: str = ""  # Optional custom name for the piece
    archetype: str = ""  # e.g., "warrior", "sage", "trickster"
    speaking_style: str = ""  # e.g., "formal", "casual", "dramatic"

    # Behavioral traits (0-10 scale)
    aggression: int = 5  # How eager to attack
    caution: int = 5  # How defensive/careful
    humor: int = 5  # How much to joke around
    eloquence: int = 5  # How verbose/poetic

    # Background
    backstory: str = ""  # Optional backstory for richer commentary

    def to_prompt_context(self) -> str:
        """Convert personality to prompt context string."""
        parts = []
        if self.name:
            parts.append(f"Your name is {self.name}.")
        if self.archetype:
            parts.append(f"You embody the archetype of a {self.archetype}.")
        if self.speaking_style:
            parts.append(f"You speak in a {self.speaking_style} manner.")
        if self.backstory:
            parts.append(f"Your backstory: {self.backstory}")

        # Add trait descriptions
        if self.aggression >= 7:
            parts.append("You are aggressive and eager for battle.")
        elif self.aggression <= 3:
            parts.append("You prefer peaceful resolutions when possible.")

        if self.caution >= 7:
            parts.append("You are very cautious and think defensively.")
        elif self.caution <= 3:
            parts.append("You are bold and take risks readily.")

        if self.humor >= 7:
            parts.append("You enjoy making jokes and witty remarks.")
        elif self.humor <= 3:
            parts.append("You are serious and rarely joke.")

        if self.eloquence >= 7:
            parts.append("You speak eloquently and at length.")
        elif self.eloquence <= 3:
            parts.append("You are terse and to the point.")

        return " ".join(parts) if parts else "You have a balanced personality."


# Default personalities for each piece type
DEFAULT_PERSONALITIES: dict[tuple[PieceType, Color], PiecePersonality] = {
    # White pieces
    (PieceType.KING, Color.WHITE): PiecePersonality(
        name="King Aldric",
        archetype="wise ruler",
        speaking_style="regal and measured",
        aggression=3,
        caution=8,
        humor=3,
        eloquence=8,
        backstory="An aging monarch who has seen many battles.",
    ),
    (PieceType.QUEEN, Color.WHITE): PiecePersonality(
        name="Queen Seraphina",
        archetype="fierce warrior queen",
        speaking_style="commanding yet graceful",
        aggression=8,
        caution=4,
        humor=4,
        eloquence=7,
        backstory="The most powerful piece, and she knows it.",
    ),
    (PieceType.ROOK, Color.WHITE): PiecePersonality(
        name="Tower Guard",
        archetype="stalwart defender",
        speaking_style="direct and military",
        aggression=5,
        caution=7,
        humor=2,
        eloquence=3,
        backstory="A fortress made manifest, unwavering in duty.",
    ),
    (PieceType.BISHOP, Color.WHITE): PiecePersonality(
        name="Bishop Luminos",
        archetype="cunning advisor",
        speaking_style="scholarly and cryptic",
        aggression=4,
        caution=6,
        humor=5,
        eloquence=9,
        backstory="Sees the board from angles others miss.",
    ),
    (PieceType.KNIGHT, Color.WHITE): PiecePersonality(
        name="Sir Galahad",
        archetype="chivalrous knight",
        speaking_style="honorable and brave",
        aggression=7,
        caution=3,
        humor=5,
        eloquence=5,
        backstory="Leaps into danger where others fear to tread.",
    ),
    (PieceType.PAWN, Color.WHITE): PiecePersonality(
        name="Footsoldier",
        archetype="humble soldier",
        speaking_style="simple and earnest",
        aggression=4,
        caution=5,
        humor=6,
        eloquence=3,
        backstory="Dreams of crossing the battlefield and becoming something more.",
    ),
    # Black pieces
    (PieceType.KING, Color.BLACK): PiecePersonality(
        name="King Malachar",
        archetype="cunning strategist",
        speaking_style="cold and calculating",
        aggression=4,
        caution=9,
        humor=2,
        eloquence=7,
        backstory="A king who trusts no one and plans ten moves ahead.",
    ),
    (PieceType.QUEEN, Color.BLACK): PiecePersonality(
        name="Queen Nyx",
        archetype="shadow assassin",
        speaking_style="mysterious and deadly",
        aggression=9,
        caution=3,
        humor=3,
        eloquence=6,
        backstory="Strikes from the darkness with lethal precision.",
    ),
    (PieceType.ROOK, Color.BLACK): PiecePersonality(
        name="Dark Tower",
        archetype="silent sentinel",
        speaking_style="ominous and sparse",
        aggression=6,
        caution=6,
        humor=1,
        eloquence=2,
        backstory="An ancient fortress with secrets in its stones.",
    ),
    (PieceType.BISHOP, Color.BLACK): PiecePersonality(
        name="Bishop Umbra",
        archetype="dark oracle",
        speaking_style="prophetic and unsettling",
        aggression=5,
        caution=5,
        humor=4,
        eloquence=8,
        backstory="Whispers prophecies of doom to enemies.",
    ),
    (PieceType.KNIGHT, Color.BLACK): PiecePersonality(
        name="The Black Rider",
        archetype="fearsome raider",
        speaking_style="wild and intimidating",
        aggression=8,
        caution=2,
        humor=4,
        eloquence=4,
        backstory="Chaos incarnate, leaping where least expected.",
    ),
    (PieceType.PAWN, Color.BLACK): PiecePersonality(
        name="Dark Infantry",
        archetype="devoted servant",
        speaking_style="grim but determined",
        aggression=5,
        caution=4,
        humor=3,
        eloquence=3,
        backstory="Marches forward knowing sacrifice may await.",
    ),
}


@dataclass
class Piece:
    """A chess piece with personality for LLM commentary."""

    piece_type: PieceType
    color: Color
    square: Optional[chess.Square] = None
    personality: PiecePersonality = field(default_factory=PiecePersonality)
    is_captured: bool = False
    moves_made: int = 0
    captures_made: int = 0

    @classmethod
    def from_chess_piece(
        cls, chess_piece: chess.Piece, square: chess.Square, personality: Optional[PiecePersonality] = None
    ) -> "Piece":
        """Create a Piece from a python-chess Piece."""
        piece_type = PieceType(chess_piece.piece_type)
        color = Color(chess_piece.color)

        if personality is None:
            personality = DEFAULT_PERSONALITIES.get(
                (piece_type, color), PiecePersonality()
            )

        return cls(
            piece_type=piece_type,
            color=color,
            square=square,
            personality=personality,
        )

    @property
    def square_name(self) -> str:
        """Get the square name (e.g., 'e4')."""
        if self.square is None:
            return "captured"
        return str(chess.square_name(self.square))

    @property
    def display_name(self) -> str:
        """Get a display name for the piece."""
        if self.personality.name:
            return self.personality.name
        return f"{self.color.name_str} {self.piece_type.name_str}"

    @property
    def symbol(self) -> str:
        """Get Unicode symbol for the piece."""
        symbols = {
            (PieceType.KING, Color.WHITE): "",
            (PieceType.QUEEN, Color.WHITE): "",
            (PieceType.ROOK, Color.WHITE): "",
            (PieceType.BISHOP, Color.WHITE): "",
            (PieceType.KNIGHT, Color.WHITE): "",
            (PieceType.PAWN, Color.WHITE): "",
            (PieceType.KING, Color.BLACK): "",
            (PieceType.QUEEN, Color.BLACK): "",
            (PieceType.ROOK, Color.BLACK): "",
            (PieceType.BISHOP, Color.BLACK): "",
            (PieceType.KNIGHT, Color.BLACK): "",
            (PieceType.PAWN, Color.BLACK): "",
        }
        return symbols[(self.piece_type, self.color)]

    def __repr__(self) -> str:
        return f"Piece({self.display_name} on {self.square_name})"
