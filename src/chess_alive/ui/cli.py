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
from ..config import get_config
from ..credentials import save_api_key, load_api_key, clear_api_key, mask_key, has_saved_key


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

    def _print_key_status(self):
        """Print the current API key status."""
        if self.config.llm.is_configured:
            masked = mask_key(self.config.llm.api_key)
            self.console.print(f"[green]API Key:[/green] {masked}")
            self.console.print(f"[green]Model:[/green]   {self.config.llm.model}")
        else:
            self.console.print("[yellow]API Key: not configured[/yellow]")

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
        self.console.print(
            "\n[dim]Type 'key' to manage API key, or 'quit' to exit[/dim]"
        )

    async def select_mode(self) -> Optional[GameMode]:
        """Let user select a game mode. Returns None to quit."""
        self.print_menu()

        while True:
            choice = Prompt.ask(
                "\n[bold]Select game mode[/bold]",
                choices=["1", "2", "3", "4", "5", "6", "key", "quit", "q"],
                default="1",
            )

            if choice in ("quit", "q"):
                return None

            if choice == "key":
                self._manage_api_key()
                self.print_menu()
                continue

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

    def _manage_api_key(self):
        """Interactive API key management."""
        self.console.print("\n[bold]API Key Management[/bold]")
        self._print_key_status()
        self.console.print()

        action = Prompt.ask(
            "Action",
            choices=["set", "show", "clear", "back"],
            default="back",
        )

        if action == "set":
            self._set_api_key()
        elif action == "show":
            self._show_api_key()
        elif action == "clear":
            self._clear_api_key()

    def _set_api_key(self):
        """Prompt user to enter and save an API key."""
        self.console.print(
            "\n[dim]Get a free key at https://openrouter.ai/keys[/dim]"
        )
        key = Prompt.ask("[bold]Enter your OpenRouter API key[/bold]")

        if not key or not key.strip():
            self.console.print("[red]No key entered.[/red]")
            return

        key = key.strip()

        # Optionally set model
        model = Prompt.ask(
            "LLM model",
            default=self.config.llm.model,
        )

        path = save_api_key(key, model if model != self.config.llm.model else None)
        self.console.print(f"[green]Key saved to {path}[/green]")
        self.console.print(
            "[dim]File permissions restricted to owner only.[/dim]"
        )

        # Reload config to pick up the new key
        self.config = get_config()
        self._print_key_status()

    def _show_api_key(self):
        """Show the currently configured API key (masked)."""
        key = load_api_key()
        if key:
            self.console.print(f"\nSaved key: {mask_key(key)}")
        else:
            self.console.print("\n[yellow]No saved key found.[/yellow]")

        if self.config.llm.api_key:
            self.console.print(f"Active key: {mask_key(self.config.llm.api_key)}")
            if has_saved_key():
                source = "saved credentials"
            else:
                source = "environment variable"
            self.console.print(f"[dim]Source: {source}[/dim]")
        else:
            self.console.print("[yellow]No active key configured.[/yellow]")

    def _clear_api_key(self):
        """Clear the saved API key."""
        if not has_saved_key():
            self.console.print("[yellow]No saved key to clear.[/yellow]")
            return

        if Confirm.ask("Remove saved API key?", default=False):
            clear_api_key()
            self.console.print("[green]Saved key removed.[/green]")
            self.config = get_config()

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
            self.console.print("\n[bold green]Game started![/bold green]")
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
            self.console.print("\n[bold]Game Over![/bold]")
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
            result: GameResult = await match.run()

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
                "[dim]Type 'key' at the menu to set up your API key.[/dim]\n"
            )

        while True:
            mode = await self.select_mode()
            if mode is None:
                self.console.print("\n[bold]Thanks for playing ChessAlive![/bold]")
                break

            # Check requirements
            if mode.requires_openrouter and not self.config.llm.is_configured:
                self.console.print(
                    "[bold red]Error:[/bold red] This mode requires an OpenRouter API key."
                )
                self.console.print(
                    "[dim]Type 'key' to set up your API key.[/dim]"
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
