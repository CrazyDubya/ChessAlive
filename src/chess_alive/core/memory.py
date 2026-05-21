"""Piece memory system for tracking game events and relationships."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from collections import defaultdict
import chess

from .piece import Piece, PieceType, Color


class EventType(Enum):
    """Types of memorable events."""
    MOVE_MADE = "move"
    CAPTURED_ENEMY = "captured_enemy"
    WAS_CAPTURED = "was_captured"
    ALLY_CAPTURED = "ally_captured"
    ENEMY_CAPTURED_ALLY = "enemy_captured_ally"
    GAVE_CHECK = "gave_check"
    RECEIVED_CHECK = "received_check"
    CHECKMATE = "checkmate"
    CASTLED = "castled"
    PROMOTED = "promoted"
    GAME_STARTED = "game_started"
    GAME_WON = "game_won"
    GAME_LOST = "game_lost"
    ESCAPED_DANGER = "escaped_danger"
    DEFENDED_ALLY = "defended_ally"
    THREATENED_ENEMY = "threatened_enemy"


@dataclass
class MemoryEvent:
    """A single memorable event."""
    event_type: EventType
    move_number: int
    description: str
    involved_piece: Optional[Piece] = None  # Other piece involved
    square: Optional[chess.Square] = None
    emotional_weight: int = 1  # How memorable (1-10)

    def to_context_string(self) -> str:
        """Convert to a context string for LLM prompts."""
        parts = [f"Move {self.move_number}: {self.description}"]
        if self.involved_piece:
            parts.append(f"(involving {self.involved_piece.display_name})")
        return " ".join(parts)


@dataclass
class PieceMemory:
    """Memory bank for a single piece."""
    piece_type: PieceType
    color: Color
    events: list[MemoryEvent] = field(default_factory=list)

    # Relationship tracking (positive = friendly, negative = hostile)
    relationships: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # Grudges and alliances
    grudge_targets: list[str] = field(default_factory=list)  # Piece display names
    protected_allies: list[str] = field(default_factory=list)

    # Personal stats
    kills: int = 0
    survived_dangers: int = 0
    moves_made: int = 0

    def add_event(self, event: MemoryEvent):
        """Add an event to memory."""
        self.events.append(event)

        # Update stats based on event type
        if event.event_type == EventType.CAPTURED_ENEMY:
            self.kills += 1
            if event.involved_piece:
                self.grudge_targets.append(event.involved_piece.display_name)
        elif event.event_type == EventType.ESCAPED_DANGER:
            self.survived_dangers += 1
        elif event.event_type == EventType.DEFENDED_ALLY:
            if event.involved_piece:
                self.protected_allies.append(event.involved_piece.display_name)
        elif event.event_type == EventType.ALLY_CAPTURED:
            if event.involved_piece:
                # Grow hostile toward the piece that killed our ally
                self.relationships[event.involved_piece.display_name] -= 2

    def get_recent_memories(self, count: int = 5) -> list[MemoryEvent]:
        """Get the most recent memorable events."""
        # Prioritize emotionally weighted events
        sorted_events = sorted(
            self.events[-20:],  # Look at last 20 events
            key=lambda e: e.emotional_weight,
            reverse=True
        )
        return sorted_events[:count]

    def get_context_for_prompt(self, max_events: int = 3) -> str:
        """Build a context string for LLM prompts."""
        if not self.events:
            return ""

        parts = ["Your recent memories:"]

        # Get emotionally significant recent events
        recent = self.get_recent_memories(max_events)
        for event in recent:
            parts.append(f"  - {event.to_context_string()}")

        # Add relationship context
        if self.grudge_targets:
            unique_grudges = list(set(self.grudge_targets))[-3:]  # Last 3 unique
            parts.append(f"  - You have a grudge against: {', '.join(unique_grudges)}")

        if self.protected_allies:
            unique_allies = list(set(self.protected_allies))[-3:]
            parts.append(f"  - You have protected: {', '.join(unique_allies)}")

        # Add stats
        if self.kills > 0:
            parts.append(f"  - You have captured {self.kills} enemy piece(s)")

        return "\n".join(parts)

    def has_grudge_against(self, piece_name: str) -> bool:
        """Check if this piece has a grudge against another."""
        return piece_name in self.grudge_targets

    def has_protected(self, piece_name: str) -> bool:
        """Check if this piece has protected another."""
        return piece_name in self.protected_allies


class GameMemory:
    """Central memory manager for all pieces in a game."""

    def __init__(self):
        self._memories: dict[tuple[PieceType, Color], PieceMemory] = {}
        self._move_number = 0
        self._killed_pieces: dict[Color, list[Piece]] = {Color.WHITE: [], Color.BLACK: []}

    def get_memory(self, piece: Piece) -> PieceMemory:
        """Get or create memory for a piece."""
        key = (piece.piece_type, piece.color)
        if key not in self._memories:
            self._memories[key] = PieceMemory(piece.piece_type, piece.color)
        return self._memories[key]

    def record_move(self, move_record):
        """Record a move and update all relevant memories."""
        from .game import MoveRecord  # Avoid circular import
        self._move_number += 1

        moving_piece = move_record.piece
        moving_memory = self.get_memory(moving_piece)

        # Record the move for the moving piece
        moving_memory.add_event(MemoryEvent(
            event_type=EventType.MOVE_MADE,
            move_number=self._move_number,
            description=f"You moved to {move_record.san}",
            emotional_weight=1,
        ))
        moving_memory.moves_made += 1

        # Handle captures
        if move_record.captured_piece:
            captured = move_record.captured_piece
            captured_memory = self.get_memory(captured)

            # Moving piece remembers the kill
            moving_memory.add_event(MemoryEvent(
                event_type=EventType.CAPTURED_ENEMY,
                move_number=self._move_number,
                description=f"You captured {captured.display_name}!",
                involved_piece=captured,
                emotional_weight=8,
            ))

            # Captured piece remembers being taken
            captured_memory.add_event(MemoryEvent(
                event_type=EventType.WAS_CAPTURED,
                move_number=self._move_number,
                description=f"You were captured by {moving_piece.display_name}!",
                involved_piece=moving_piece,
                emotional_weight=10,
            ))

            # Record the kill
            self._killed_pieces[captured.color].append(captured)

            # Notify allies of the loss
            for ally_piece in self._get_allies_of(captured):
                if ally_piece.piece_type != captured.piece_type:  # Don't notify self
                    ally_memory = self.get_memory(ally_piece)
                    ally_memory.add_event(MemoryEvent(
                        event_type=EventType.ALLY_CAPTURED,
                        move_number=self._move_number,
                        description=f"Your ally {captured.display_name} was captured by {moving_piece.display_name}!",
                        involved_piece=moving_piece,
                        emotional_weight=6,
                    ))

        # Handle check
        if move_record.is_check:
            moving_memory.add_event(MemoryEvent(
                event_type=EventType.GAVE_CHECK,
                move_number=self._move_number,
                description="You put the enemy king in check!",
                emotional_weight=7,
            ))

        # Handle checkmate
        if move_record.is_checkmate:
            moving_memory.add_event(MemoryEvent(
                event_type=EventType.CHECKMATE,
                move_number=self._move_number,
                description="CHECKMATE! Victory!",
                emotional_weight=10,
            ))

        # Handle castling
        if move_record.is_castling:
            moving_memory.add_event(MemoryEvent(
                event_type=EventType.CASTLED,
                move_number=self._move_number,
                description="You castled to safety!",
                emotional_weight=4,
            ))

        # Handle promotion
        if move_record.is_promotion:
            moving_memory.add_event(MemoryEvent(
                event_type=EventType.PROMOTED,
                move_number=self._move_number,
                description="You promoted! A new beginning!",
                emotional_weight=9,
            ))

    def record_game_start(self, pieces_by_color: dict):
        """Record game start for all pieces."""
        self._move_number = 0
        self._killed_pieces = {Color.WHITE: [], Color.BLACK: []}

        for color, pieces in pieces_by_color.items():
            for piece in pieces:
                memory = self.get_memory(piece)
                memory.add_event(MemoryEvent(
                    event_type=EventType.GAME_STARTED,
                    move_number=0,
                    description="A new battle begins!",
                    emotional_weight=3,
                ))

    def record_game_end(self, winner: Optional[Color], pieces_by_color: dict):
        """Record game end for all pieces."""
        for color, pieces in pieces_by_color.items():
            for piece in pieces:
                memory = self.get_memory(piece)
                if winner is None:
                    memory.add_event(MemoryEvent(
                        event_type=EventType.GAME_WON if False else EventType.GAME_LOST,
                        move_number=self._move_number,
                        description="The game ended in a draw.",
                        emotional_weight=5,
                    ))
                elif winner == color:
                    memory.add_event(MemoryEvent(
                        event_type=EventType.GAME_WON,
                        move_number=self._move_number,
                        description="VICTORY! Your side has won!",
                        emotional_weight=10,
                    ))
                else:
                    memory.add_event(MemoryEvent(
                        event_type=EventType.GAME_LOST,
                        move_number=self._move_number,
                        description="Defeat... your side has lost.",
                        emotional_weight=10,
                    ))

    def _get_allies_of(self, piece: Piece) -> list:
        """Get allies of a piece (same color)."""
        # This will be called with game context
        return []

    def get_memorable_context(self, piece: Piece) -> str:
        """Get memorable context for a piece's commentary."""
        memory = self.get_memory(piece)
        return memory.get_context_for_prompt()

    def get_grudge_commentary_hint(self, piece: Piece, target_piece: Piece) -> Optional[str]:
        """Get a hint if piece has a grudge against target."""
        memory = self.get_memory(piece)
        if memory.has_grudge_against(target_piece.display_name):
            return f"Remember, {target_piece.display_name} has wronged you before!"
        return None
