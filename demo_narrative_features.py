#!/usr/bin/env python3
"""
Demo script for ChessAlive Narrative Features.

This demonstrates the three new narrative features:
1. AI Game Stories - Generate stories/tweets from games
2. Narrative Puzzles - Story-wrapped chess puzzles
3. Position Analysis - Engine analysis with piece commentary
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

os.environ["STOCKFISH_PATH"] = "/usr/games/stockfish"

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich import box
import chess

from chess_alive.llm.client import LLMClient
from chess_alive.config import GameConfig, LLMConfig
from chess_alive.core.game import ChessGame
from chess_alive.narrative.stories import StoryGenerator, NarratorStyle, StoryFormat, PieceQuote
from chess_alive.narrative.puzzles import PuzzleEngine, PuzzleFlavor, PuzzleTheme
from chess_alive.narrative.analysis import PositionAnalyzer, InsightType

console = Console()


def print_header(title: str, subtitle: str = ""):
    """Print a styled header."""
    content = f"[bold cyan]{title}[/bold cyan]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"
    console.print(Panel(content, box=box.DOUBLE, padding=(1, 2)))
    console.print()


def print_section(title: str):
    """Print a section divider."""
    console.print(f"\n[bold yellow]{'─' * 60}[/bold yellow]")
    console.print(f"[bold yellow]  {title}[/bold yellow]")
    console.print(f"[bold yellow]{'─' * 60}[/bold yellow]\n")


async def demo_story_generation():
    """Demonstrate AI Game Story generation."""
    print_header("Feature 1: AI Game Stories", "Transform chess games into narrative stories")

    config = LLMConfig()
    if not config.is_configured:
        console.print("[red]Error: OpenRouter API key not configured[/red]")
        return

    # Create a sample game with some moves
    game = ChessGame()
    moves = ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4", "Nf6", "O-O", "Be7",
             "Re1", "b5", "Bb3", "d6", "c3", "O-O", "h3", "Nb8"]

    for move in moves:
        game.make_move_san(move)

    # Create some piece quotes
    quotes = [
        PieceQuote(1, "Footsoldier", "pawn", "white", "The journey of a thousand squares begins with a single step!", "move"),
        PieceQuote(3, "Sir Galahad", "knight", "white", "For honor and glory, I ride forth!", "move"),
        PieceQuote(5, "Bishop Luminos", "bishop", "white", "The diagonal path reveals hidden truths...", "move"),
        PieceQuote(9, "King Aldric", "king", "white", "To the fortress we go! Castling is complete.", "castling"),
    ]

    async with LLMClient(config) as client:
        generator = StoryGenerator(client)

        # Demo 1: Tweet Generation
        print_section("Tweet Generation (280 chars)")

        for style in [NarratorStyle.CHRONICLER, NarratorStyle.GUMSHOE, NarratorStyle.PLAY_BY_PLAY]:
            console.print(f"[bold]Narrator: {style.value.replace('_', ' ').title()}[/bold]")
            story = await generator.generate_tweet(game, quotes, style)
            console.print(Panel(
                story.content,
                title=f"[cyan]{len(story.content)} characters[/cyan]",
                border_style="green"
            ))
            console.print()

        # Demo 2: Short Story Generation
        print_section("Short Story Generation")

        for style in [NarratorStyle.CHRONICLER, NarratorStyle.NATURE]:
            console.print(f"[bold magenta]Narrator: {style.value.replace('_', ' ').title()}[/bold magenta]\n")
            story = await generator.generate_short_story(game, quotes, style)

            if story.title:
                console.print(f"[bold underline]{story.title}[/bold underline]\n")

            # Print story with nice formatting
            paragraphs = story.content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    console.print(f"  {para.strip()}\n")

            console.print("[dim]" + "─" * 50 + "[/dim]\n")


async def demo_narrative_puzzles():
    """Demonstrate Narrative Puzzles."""
    print_header("Feature 2: Narrative Puzzles", "Chess puzzles wrapped in story")

    engine = PuzzleEngine()

    console.print(f"[bold]Total puzzles available: {engine.get_puzzle_count()}[/bold]\n")

    # Demo puzzles in different flavors
    flavors = [
        (PuzzleFlavor.KINGDOM_SIEGE, "Epic Fantasy"),
        (PuzzleFlavor.CASE_FILES, "Noir Detective"),
        (PuzzleFlavor.CHAMPIONSHIP, "Sports Drama"),
        (PuzzleFlavor.HAUNTED_BOARD, "Gothic Horror"),
        (PuzzleFlavor.NATURE_DOC, "Nature Documentary"),
    ]

    for flavor, genre_name in flavors[:3]:  # Show 3 flavors
        print_section(f"{genre_name} Flavor")

        puzzle = engine.get_random_puzzle(flavor)

        # Display puzzle info
        table = Table(box=box.ROUNDED, show_header=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value")

        table.add_row("Title", f"[bold]{puzzle.title}[/bold]")
        table.add_row("Theme", puzzle.theme.value)
        table.add_row("Difficulty", f"{puzzle.difficulty} ({engine.get_difficulty_label(puzzle.difficulty)})")
        table.add_row("Flavor", puzzle.flavor.value.replace('_', ' ').title())

        console.print(table)
        console.print()

        # Display the narrative setup
        console.print(Panel(
            puzzle.setup_text,
            title="[yellow]The Scene[/yellow]",
            border_style="yellow"
        ))

        # Display the board
        board = chess.Board(puzzle.fen)
        console.print(f"\n[bold]Position (White to move):[/bold]")
        console.print(f"```\n{board}\n```")

        # Simulate solving
        console.print(f"\n[bold green]Solution:[/bold green] {' '.join(puzzle.solution)}")
        console.print(f"[italic green]{puzzle.narrator_piece}: \"{puzzle.success_text}\"[/italic green]")

        console.print()


async def demo_position_analysis():
    """Demonstrate Position Analysis."""
    print_header("Feature 3: Position Analysis", "Engine analysis with piece commentary")

    stockfish_path = os.environ.get("STOCKFISH_PATH", "/usr/games/stockfish")
    if not os.path.exists(stockfish_path):
        console.print("[red]Error: Stockfish not found[/red]")
        return

    config = LLMConfig()
    llm_client = LLMClient(config) if config.is_configured else None

    # Create a game with some tactical moments
    game = ChessGame()
    # Play a game with a blunder
    tactical_game = [
        "e4", "e5",      # 1
        "Nf3", "Nc6",    # 2
        "Bc4", "Bc5",    # 3
        "c3", "Nf6",     # 4
        "d4", "exd4",    # 5
        "cxd4", "Bb4+",  # 6
        "Nc3", "Nxe4",   # 7 - tactical moment
        "O-O", "Nxc3",   # 8
        "bxc3", "Bxc3",  # 9
        "Qb3", "Bxa1",   # 10
    ]

    for move in tactical_game:
        try:
            game.make_move_san(move)
        except:
            break

    async with PositionAnalyzer(stockfish_path, llm_client, depth=12) as analyzer:
        print_section("Game Analysis")

        console.print("[bold]Analyzing game...[/bold] (this may take a moment)\n")

        analysis = await analyzer.analyze_game(game, include_all_moves=False)

        # Summary table
        summary_table = Table(title="Analysis Summary", box=box.ROUNDED)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", justify="right")

        summary_table.add_row("Total Moves", str(analysis.total_moves))
        summary_table.add_row("Blunders", f"[red]{analysis.blunders}[/red]" if analysis.blunders else "0")
        summary_table.add_row("Mistakes", f"[yellow]{analysis.mistakes}[/yellow]" if analysis.mistakes else "0")
        summary_table.add_row("Inaccuracies", str(analysis.inaccuracies))
        summary_table.add_row("Brilliancies", f"[green]{analysis.brilliancies}[/green]" if analysis.brilliancies else "0")
        summary_table.add_row("Avg Eval Loss", f"{analysis.average_eval_loss:.2f}")

        console.print(summary_table)
        console.print()

        # Key moments
        print_section("Key Moments")

        insight_styles = {
            InsightType.BLUNDER: ("red", "??"),
            InsightType.MISTAKE: ("yellow", "?"),
            InsightType.INACCURACY: ("dim", "?!"),
            InsightType.BRILLIANT: ("green", "!!"),
            InsightType.EXCELLENT: ("cyan", "!"),
            InsightType.TURNING_POINT: ("magenta", "⟳"),
            InsightType.MISSED_WIN: ("red", "○"),
            InsightType.GOOD_MOVE: ("white", ""),
        }

        for insight in analysis.insights[:5]:  # Show top 5 insights
            style, symbol = insight_styles.get(insight.insight_type, ("white", ""))

            console.print(Panel(
                f"[bold]Move {insight.move_number}: {insight.move_san} {symbol}[/bold]\n"
                f"Type: [{style}]{insight.insight_type.value.upper()}[/{style}]\n"
                f"Eval: {insight.eval_before:+.2f} → {insight.eval_after:+.2f} "
                f"([{'green' if insight.eval_delta > 0 else 'red'}]{insight.eval_delta:+.2f}[/])\n"
                f"{f'Best was: {insight.best_move}' if insight.best_move and insight.best_move != insight.move_san else ''}\n\n"
                f"[italic]{insight.piece_name}:[/italic]\n"
                f'"{insight.piece_quote}"',
                title=f"[{style}]{insight.insight_type.value.title()}[/{style}]",
                border_style=style
            ))
            console.print()

        # Single position analysis demo
        print_section("Single Position Analysis")

        test_position = "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4"
        console.print(f"[bold]Position:[/bold] Scholar's Mate threat\n")

        board = chess.Board(test_position)
        console.print(f"```\n{board}\n```\n")

        pos_analysis = await analyzer.analyze_position(test_position)

        pos_table = Table(box=box.SIMPLE)
        pos_table.add_column("Metric", style="cyan")
        pos_table.add_column("Value")

        pos_table.add_row("Evaluation", f"{pos_analysis['evaluation']:+.2f}")
        pos_table.add_row("Best Move", f"[bold green]{pos_analysis['best_move']}[/bold green]")
        pos_table.add_row("After Best", f"{pos_analysis['best_eval']:+.2f}")
        pos_table.add_row("Is Check", "Yes" if pos_analysis['is_check'] else "No")
        pos_table.add_row("Legal Moves", str(len(pos_analysis['legal_moves'])))

        console.print(pos_table)

    if llm_client:
        await llm_client.close()


async def main():
    """Run all demos."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold magenta]ChessAlive Narrative Features Demo[/bold magenta]\n\n"
        "Demonstrating the three new narrative features:\n"
        "1. [cyan]AI Game Stories[/cyan] - Generate stories/tweets from games\n"
        "2. [yellow]Narrative Puzzles[/yellow] - Story-wrapped chess puzzles\n"
        "3. [green]Position Analysis[/green] - Engine analysis with piece commentary",
        box=box.DOUBLE_EDGE,
        padding=(1, 4)
    ))

    console.print("\n")

    # Run demos
    try:
        await demo_story_generation()
    except Exception as e:
        console.print(f"[red]Story generation error: {e}[/red]")
        import traceback
        traceback.print_exc()

    try:
        await demo_narrative_puzzles()
    except Exception as e:
        console.print(f"[red]Puzzle demo error: {e}[/red]")
        import traceback
        traceback.print_exc()

    try:
        await demo_position_analysis()
    except Exception as e:
        console.print(f"[red]Analysis error: {e}[/red]")
        import traceback
        traceback.print_exc()

    # Final summary
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]Demo Complete![/bold green]\n\n"
        "All three narrative features are now implemented:\n"
        "• [cyan]StoryGenerator[/cyan] - in narrative/stories.py\n"
        "• [yellow]PuzzleEngine[/yellow] - in narrative/puzzles.py\n"
        "• [green]PositionAnalyzer[/green] - in narrative/analysis.py",
        box=box.DOUBLE_EDGE,
        padding=(1, 4)
    ))


if __name__ == "__main__":
    asyncio.run(main())
