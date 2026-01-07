"""Command-line interface for ChessAlive."""

import asyncio
import sys
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from .display import BoardDisplay
from ..modes.mode import GameMode
from ..modes.match import Match, MatchConfig, MatchEvent
from ..core.game import ChessGame, GameResult
from ..core.piece import Color
from ..config import GameConfig, get_config


class CLI:
    """Command-line interface for ChessAlive."""

    BANNER = """
   _____ _                        _    _ _
  / ____| |                      | |  | (_)
 | |    | |__   ___  ___ ___     | |  | |___   _____
 | |    | '_ \\ / _ \\/ __/ __|    | |/\\| | \\ \\ / / _ \\
 | |____| | | |  __/\\__ \\__ \\    \\  /\\  / |\\ V /  __/
  \\_____|_| |_|\\___||___/___/     \\/  \\/|_| \\_/ \\___|

    Where every piece has a voice!
    """

    def __init__(self, console: Optional[Console] = None):
        """Initialize CLI."""
        self.console = console or Console()
        self.display = BoardDisplay(self.console)
        self.config = get_config()
        self._current_match: Optional[Match] = None

    def print_banner(self):
        """Print the welcome banner."""
        self.console.print(Panel(self.BANNER, style="bold blue"))

    def print_menu(self):
        """Print the main menu."""
        table = Table(title="Game Modes", show_header=True)
        table.add_column("Option", style="cyan")
        table.add_column("Mode", style="white")
        table.add_column("Description", style="dim")

        modes = [
            ("1", "pvp", "Player vs Player - Two humans"),
            ("2", "pvc", "Player vs Computer - Human vs Stockfish"),
            ("3", "cvc", "Computer vs Computer - Stockfish vs Stockfish"),
            ("4", "pvl", "Player vs LLM - Human vs AI language model"),
            ("5", "lvl", "LLM vs LLM - Two AI language models"),
            ("6", "lvc", "LLM vs Computer - AI language model vs Stockfish"),
        ]

        for opt, mode, desc in modes:
            table.add_row(opt, mode, desc)

        self.console.print(table)
        self.console.print("\n[dim]Type 'quit' to exit[/dim]")

    async def select_mode(self) -> Optional[GameMode]:
        """Let user select a game mode."""
        self.print_menu()

        while True:
            choice = Prompt.ask(
                "\n[bold]Select game mode[/bold]",
                choices=["1", "2", "3", "4", "5", "6", "quit", "q"],
                default="1",
            )

            if choice in ("quit", "q"):
                return None

            mode_map = {
                "1": GameMode.PLAYER_VS_PLAYER,
                "2": GameMode.PLAYER_VS_COMPUTER,
                "3": GameMode.COMPUTER_VS_COMPUTER,
                "4": GameMode.PLAYER_VS_LLM,
                "5": GameMode.LLM_VS_LLM,
                "6": GameMode.LLM_VS_COMPUTER,
            }

            mode = mode_map.get(choice)
            if mode:
                return mode

    def configure_match(self, mode: GameMode) -> MatchConfig:
        """Configure match settings."""
        config = MatchConfig(mode=mode)

        self.console.print(f"\n[bold]Configuring {mode.description}[/bold]\n")

        # Get player names
        if mode.white_player_type.name == "HUMAN":
            config.white_name = Prompt.ask("White player name", default="Player 1")
        else:
            config.white_name = f"{mode.white_player_type.name.title()} (White)"

        if mode.black_player_type.name == "HUMAN":
            config.black_name = Prompt.ask("Black player name", default="Player 2")
        else:
            config.black_name = f"{mode.black_player_type.name.title()} (Black)"

        # Commentary settings
        config.enable_commentary = Confirm.ask(
            "Enable piece commentary?",
            default=True,
        )

        if config.enable_commentary:
            freq = Prompt.ask(
                "Commentary frequency",
                choices=["every_move", "captures_only", "key_moments"],
                default="key_moments",
            )
            config.commentary_frequency = freq

        # Computer settings
        if mode.requires_stockfish:
            skill = Prompt.ask(
                "Stockfish skill level (0-20)",
                default="15",
            )
            config.stockfish_skill = int(skill)

        # LLM settings
        if mode.requires_openrouter:
            if mode.white_player_type.name == "LLM":
                style = Prompt.ask(
                    "White LLM style",
                    choices=["aggressive", "defensive", "balanced", "creative"],
                    default="balanced",
                )
                config.llm_style_white = style

            if mode.black_player_type.name == "LLM":
                style = Prompt.ask(
                    "Black LLM style",
                    choices=["aggressive", "defensive", "balanced", "creative"],
                    default="balanced",
                )
                config.llm_style_black = style

        return config

    async def handle_event(self, event: MatchEvent):
        """Handle match events for display."""
        if event.event_type == "game_start":
            self.console.print(f"\n[bold green]Game started![/bold green]")
            self.console.print(f"White: {event.data['white']}")
            self.console.print(f"Black: {event.data['black']}")
            self.console.print()

        elif event.event_type == "move":
            # Board is printed after each move in the main loop
            pass

        elif event.event_type == "commentary":
            self.display.print_commentary(
                event.data["piece"],
                event.data["text"],
            )

        elif event.event_type == "game_end":
            self.console.print(f"\n[bold]Game Over![/bold]")
            self.console.print(f"Result: {event.data['result']}")
            self.console.print(f"Total moves: {event.data['moves']}")

    async def human_input_handler(self, game: ChessGame) -> str:
        """Handle human move input."""
        # Print current board state
        last_move = game.move_history[-1].move if game.move_history else None
        self.display.print_board(game, last_move=last_move)
        self.display.print_game_status(game)
        self.display.print_captured_pieces(game)

        # Get input
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: Prompt.ask(
                f"\n[bold]{game.current_turn.name_str}'s move[/bold] (or 'help')"
            ),
        )

    async def run_match(self, match_config: MatchConfig) -> GameResult:
        """Run a complete match."""
        async with Match(match_config, self.config, self.handle_event) as match:
            self._current_match = match

            # Set up the match
            try:
                await match.setup(self.human_input_handler)
            except RuntimeError as e:
                self.console.print(f"[bold red]Error:[/bold red] {e}")
                return GameResult.IN_PROGRESS

            # Run the match
            result = await match.run()

            # Print final board
            self.console.print("\n[bold]Final Position:[/bold]")
            self.display.print_board(match.game)

            # Print PGN
            if Confirm.ask("\nShow PGN?", default=False):
                self.console.print(Panel(match.game.to_pgn(), title="PGN"))

            self._current_match = None
            return result

    async def run(self):
        """Run the main CLI loop."""
        self.print_banner()

        # Check configuration
        if not self.config.llm.is_configured:
            self.console.print(
                "[yellow]Note: OpenRouter API key not set. "
                "LLM modes will not work.[/yellow]"
            )
            self.console.print(
                "[dim]Set OPENROUTER_API_KEY environment variable to enable.[/dim]\n"
            )

        while True:
            mode = await self.select_mode()
            if mode is None:
                self.console.print("\n[bold]Thanks for playing ChessAlive![/bold]")
                break

            # Check requirements
            if mode.requires_openrouter and not self.config.llm.is_configured:
                self.console.print(
                    "[bold red]Error:[/bold red] This mode requires OpenRouter API key."
                )
                continue

            # Configure and run match
            match_config = self.configure_match(mode)

            try:
                await self.run_match(match_config)
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Match interrupted[/yellow]")
            except Exception as e:
                self.console.print(f"[bold red]Error:[/bold red] {e}")

            # Play again?
            if not Confirm.ask("\nPlay again?", default=True):
                self.console.print("\n[bold]Thanks for playing ChessAlive![/bold]")
                break


def main():
    """Main entry point."""
    cli = CLI()
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
