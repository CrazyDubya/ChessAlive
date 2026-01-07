"""Base player interface."""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional, Callable
import chess

from ..core.game import ChessGame
from ..core.piece import Color


class PlayerType(Enum):
    """Types of players."""

    HUMAN = auto()
    COMPUTER = auto()  # Chess engine (Stockfish)
    LLM = auto()  # LLM-based player


class Player(ABC):
    """Abstract base class for all player types."""

    def __init__(self, color: Color, name: Optional[str] = None):
        self.color = color
        self.name = name or f"{self.player_type.name.title()} ({color.name_str})"

    @property
    @abstractmethod
    def player_type(self) -> PlayerType:
        """Get the type of this player."""
        pass

    @abstractmethod
    async def get_move(self, game: ChessGame) -> Optional[chess.Move]:
        """
        Get the next move from this player.

        Args:
            game: The current game state

        Returns:
            The chosen move, or None if no move is possible
        """
        pass

    async def on_game_start(self, game: ChessGame):
        """Called when a game starts. Override for setup."""
        pass

    async def on_game_end(self, game: ChessGame):
        """Called when a game ends. Override for cleanup."""
        pass

    async def on_opponent_move(self, game: ChessGame, move: chess.Move):
        """Called when opponent makes a move. Override to react."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"


class MoveCallback:
    """Callback for move input (used by human player in different UIs)."""

    def __init__(self, callback: Callable[[str], Optional[chess.Move]]):
        self._callback = callback

    def __call__(self, move_str: str) -> Optional[chess.Move]:
        return self._callback(move_str)
