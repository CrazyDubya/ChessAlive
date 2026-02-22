"""Command-line interface for ChessAlive."""

import asyncio
import sys
from typing import Optional, Callable, Awaitable
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table

from .display import BoardDisplay
from ..modes.mode import GameMode
from ..modes.match import Match, MatchConfig, MatchEvent
from ..core.game import ChessGame, GameResult
from ..config import get_config, PROVIDER_DEFAULTS
from ..credentials import (
    save_api_key,
    clear_api_key,
    mask_key,
    has_saved_key,
)


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
        # Callback set to TeachingAdvisor.analyze during teaching mode matches
        self._pre_move_advisor: Optional[Callable[[ChessGame], Awaitable]] = None

    def print_banner(self):
        """Print the welcome banner."""
        self.console.print(Panel(self.BANNER, style="bold blue"))

    def _print_provider_status(self):
        """Print the current LLM provider status."""
        llm = self.config.llm
        self.console.print(f"[green]Provider:[/green] {llm.provider_display}")
        self.console.print(f"[green]Model:[/green]    {llm.model}")
        if llm.is_ollama:
            self.console.print(f"[green]Endpoint:[/green] {llm.base_url}")
        elif llm.api_key and llm.api_key != "ollama":
            self.console.print(f"[green]API Key:[/green]  {mask_key(llm.api_key)}")
        else:
            self.console.print("[yellow]API Key:  not configured[/yellow]")

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
            ("7", "teaching", "Teaching mode - Human vs Stockfish with LLM coaching"),
        ]

        for opt, mode, desc in modes:
            table.add_row(opt, mode, desc)

        self.console.print(table)

        llm = self.config.llm
        status = f"[dim]{llm.provider_display}: {llm.model}[/dim]"
        self.console.print(f"\n{status}")
        self.console.print(
            "[dim]Type 'setup' to configure LLM provider, or 'quit' to exit[/dim]"
        )

    async def select_mode(self) -> Optional[GameMode]:
        """Let user select a game mode. Returns None to quit."""
        self.print_menu()

        while True:
            choice = Prompt.ask(
                "\n[bold]Select game mode[/bold]",
                choices=["1", "2", "3", "4", "5", "6", "7", "setup", "quit", "q"],
                default="1",
            )

            if choice in ("quit", "q"):
                return None

            if choice == "setup":
                self._setup_llm()
                self.print_menu()
                continue

            mode_map = {
                "1": GameMode.PLAYER_VS_PLAYER,
                "2": GameMode.PLAYER_VS_COMPUTER,
                "3": GameMode.COMPUTER_VS_COMPUTER,
                "4": GameMode.PLAYER_VS_LLM,
                "5": GameMode.LLM_VS_LLM,
                "6": GameMode.LLM_VS_COMPUTER,
                "7": GameMode.TEACHING,
            }

            mode = mode_map.get(choice)
            if mode:
                return mode

    def _setup_llm(self):
        """Interactive LLM provider setup."""
        self.console.print("\n[bold]LLM Provider Setup[/bold]")
        self._print_provider_status()
        self.console.print()

        action = Prompt.ask(
            "Action",
            choices=["ollama", "openrouter", "show", "clear", "back"],
            default="back",
        )

        if action == "ollama":
            self._setup_ollama()
        elif action == "openrouter":
            self._setup_openrouter()
        elif action == "show":
            self._print_provider_status()
        elif action == "clear":
            self._clear_config()

    def _setup_ollama(self):
        """Configure Ollama as the LLM provider."""
        self.console.print("\n[bold]Ollama Setup[/bold]")
        self.console.print(
            "[dim]Ollama runs LLMs locally. Install: https://ollama.com[/dim]"
        )
        self.console.print(
            "[dim]Then run: ollama pull qwen2.5:3b[/dim]\n"
        )

        default_model = PROVIDER_DEFAULTS["ollama"]["model"]
        model = Prompt.ask("Ollama model", default=default_model)

        path = save_api_key(api_key="", model=model, provider="ollama")
        self.console.print(f"[green]Ollama config saved to {path}[/green]")

        # Reload
        self.config = get_config()
        self._print_provider_status()

    def _setup_openrouter(self):
        """Configure OpenRouter as the LLM provider."""
        self.console.print("\n[bold]OpenRouter Setup[/bold]")
        self.console.print(
            "[dim]Get a free key at https://openrouter.ai/keys[/dim]"
        )
        key = Prompt.ask("[bold]Enter your OpenRouter API key[/bold]")

        if not key or not key.strip():
            self.console.print("[red]No key entered.[/red]")
            return

        key = key.strip()

        default_model = PROVIDER_DEFAULTS["openrouter"]["model"]
        model = Prompt.ask("Model", default=default_model)

        path = save_api_key(api_key=key, model=model, provider="openrouter")
        self.console.print(f"[green]Config saved to {path}[/green]")
        self.console.print(
            "[dim]File permissions restricted to owner only.[/dim]"
        )

        # Reload
        self.config = get_config()
        self._print_provider_status()

    def _clear_config(self):
        """Clear saved LLM configuration."""
        if not has_saved_key():
            self.console.print("[yellow]No saved config to clear.[/yellow]")
            return

        if Confirm.ask("Remove saved LLM config?", default=False):
            clear_api_key()
            self.console.print("[green]Saved config removed.[/green]")
            self.config = get_config()

    def configure_match(self, mode: GameMode) -> MatchConfig:
        """Configure match settings, pre-populated from mode defaults."""
        defaults = mode.defaults
        config = MatchConfig(
            mode=mode,
            commentary_frequency=defaults.commentary_frequency,
            stockfish_depth=defaults.stockfish_depth,
            stockfish_time=defaults.stockfish_time,
            stockfish_skill=defaults.stockfish_skill,
            llm_style_white=defaults.llm_style_white,
            llm_style_black=defaults.llm_style_black,
            max_moves=defaults.max_moves,
        )

        self.console.print(f"\n[bold]Configuring {mode.description}[/bold]\n")

        # Teaching mode - enable coaching and skip irrelevant options
        if mode == GameMode.TEACHING:
            config.enable_teaching = True
            config.white_name = Prompt.ask("Your name (White)", default="Student")
            config.black_name = "Stockfish (Black)"
            config.enable_commentary = False

            skill = Prompt.ask(
                "Stockfish opponent skill level (0-20, lower = easier)",
                default="10",
            )
            config.stockfish_skill = int(skill)
            return config

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

        # Show teaching advice when in teaching mode
        if self._pre_move_advisor is not None:
            try:
                advice = await self._pre_move_advisor(game)
                self.display.print_teaching_advice(advice)
            except Exception as e:
                self.console.print(
                    f"[yellow]Teaching analysis unavailable: {e}[/yellow]"
                )

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
            self._pre_move_advisor = None

            # Set up the match
            try:
                await match.setup(self.human_input_handler)
            except RuntimeError as e:
                self.console.print(f"[bold red]Error:[/bold red] {e}")
                return GameResult.IN_PROGRESS

            # Wire up teaching advisor (analysis runs before each human move)
            if match.teaching_advisor is not None:
                self._pre_move_advisor = match.teaching_advisor.analyze
                self.console.print(
                    "[bold cyan]Teaching mode active![/bold cyan] "
                    "[dim]LLM + Stockfish coaching will appear before each of your moves.[/dim]"
                )

            # Run the match
            result: GameResult = await match.run()

            # Print final board and post-game summary
            self.console.print("\n[bold]Final Position:[/bold]")
            self.display.print_board(match.game)
            self.display.print_post_game_summary(
                match.game,
                white_name=match_config.white_name,
                black_name=match_config.black_name,
            )

            # Print PGN
            if Confirm.ask("\nShow PGN?", default=False):
                self.console.print(Panel(match.game.to_pgn(), title="PGN"))

            self._current_match = None
            self._pre_move_advisor = None
            return result

    async def run(self):
        """Run the main CLI loop."""
        self.print_banner()

        # Check configuration
        if not self.config.llm.is_configured:
            self.console.print(
                "[yellow]Note: No LLM provider configured. "
                "LLM modes will not work.[/yellow]"
            )
            self.console.print(
                "[dim]Type 'setup' at the menu to configure "
                "Ollama (local) or OpenRouter.[/dim]\n"
            )

        while True:
            mode = await self.select_mode()
            if mode is None:
                self.console.print("\n[bold]Thanks for playing ChessAlive![/bold]")
                break

            # Check requirements
            if mode.requires_openrouter and not self.config.llm.is_configured:
                self.console.print(
                    "[bold red]Error:[/bold red] This mode requires an LLM provider."
                )
                self.console.print(
                    "[dim]Type 'setup' to configure Ollama or OpenRouter.[/dim]"
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
