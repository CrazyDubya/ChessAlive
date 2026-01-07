"""Human player implementation."""

import asyncio
from typing import Optional, Callable, Awaitable
import chess

from .base import Player, PlayerType
from ..core.game import ChessGame
from ..core.piece import Color


class HumanPlayer(Player):
    """Human player that gets moves from user input."""

    def __init__(
        self,
        color: Color,
        name: Optional[str] = None,
        input_handler: Optional[Callable[[ChessGame], Awaitable[str]]] = None,
    ):
        """
        Initialize a human player.

        Args:
            color: The player's color
            name: Optional player name
            input_handler: Async function to get move input. If None, uses stdin.
        """
        super().__init__(color, name or "Human")
        self._input_handler = input_handler

    @property
    def player_type(self) -> PlayerType:
        return PlayerType.HUMAN

    async def get_move(self, game: ChessGame) -> Optional[chess.Move]:
        """Get move from human input."""
        if game.current_turn != self.color:
            return None

        while True:
            try:
                if self._input_handler:
                    move_str = await self._input_handler(game)
                else:
                    # Default: use asyncio-compatible input
                    move_str = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: input(f"{self.name}'s move: ").strip()
                    )

                if not move_str:
                    continue

                # Handle special commands
                if move_str.lower() in ("quit", "exit", "resign"):
                    return None

                if move_str.lower() == "help":
                    self._show_help(game)
                    continue

                if move_str.lower() == "moves":
                    self._show_legal_moves(game)
                    continue

                # Parse and validate move
                move = game.parse_move(move_str)
                if move and game.is_legal_move(move):
                    return move

                print(f"Invalid move: {move_str}. Type 'moves' to see legal moves.")

            except (EOFError, KeyboardInterrupt):
                return None

    def _show_help(self, game: ChessGame):
        """Show help message."""
        print("\nCommands:")
        print("  <move>  - Make a move (e.g., 'e4', 'Nf3', 'e2e4', 'O-O')")
        print("  moves   - Show all legal moves")
        print("  resign  - Resign the game")
        print("  quit    - Quit the game")

    def _show_legal_moves(self, game: ChessGame):
        """Show all legal moves."""
        moves = [game.board.san(m) for m in game.get_legal_moves()]
        print(f"\nLegal moves ({len(moves)}): {', '.join(moves)}")
