#!/usr/bin/env python3
"""Test script for ChessAlive features."""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set stockfish path
os.environ["STOCKFISH_PATH"] = "/usr/games/stockfish"

from chess_alive.modes.mode import GameMode
from chess_alive.modes.match import Match, MatchConfig, MatchEvent
from chess_alive.config import GameConfig
from chess_alive.llm.client import LLMClient
from chess_alive.core.piece import DEFAULT_PERSONALITIES, PieceType, Color


def print_separator(title: str):
    """Print a separator with title."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


async def on_event(event: MatchEvent):
    """Event handler for match events."""
    if event.event_type == "game_start":
        print(f"Game started: {event.data['white']} vs {event.data['black']}")
    elif event.event_type == "move":
        move_info = f"Move: {event.data['move']} by {event.data['piece']}"
        if event.data.get('captured'):
            move_info += f" (captured {event.data['captured']})"
        if event.data.get('is_check'):
            move_info += " - CHECK!"
        if event.data.get('is_checkmate'):
            move_info += " - CHECKMATE!"
        print(move_info)
    elif event.event_type == "commentary":
        print(f"  [{event.data['piece']}]: \"{event.data['text']}\"")
    elif event.event_type == "game_end":
        print(f"\nGame ended: {event.data['result']} in {event.data['moves']} moves")


async def test_personas():
    """Test the different piece personas."""
    print_separator("Testing Piece Personas")

    print("Available piece personalities:\n")

    for (piece_type, color), personality in DEFAULT_PERSONALITIES.items():
        print(f"{color.name_str} {piece_type.name_str}:")
        print(f"  Name: {personality.name}")
        print(f"  Archetype: {personality.archetype}")
        print(f"  Speaking Style: {personality.speaking_style}")
        print(f"  Traits: Aggression={personality.aggression}, Caution={personality.caution}, Humor={personality.humor}, Eloquence={personality.eloquence}")
        print()

    return True


async def test_llm_connection():
    """Test LLM connectivity."""
    print_separator("Testing LLM Connection")

    config = GameConfig()
    if not config.llm.is_configured:
        print("ERROR: OpenRouter API key not configured!")
        return False

    print(f"API configured: {config.llm.is_configured}")
    print(f"Model: {config.llm.model}")

    # Test a simple completion
    async with LLMClient(config.llm) as client:
        try:
            response = await client.complete(
                "Say 'Hello from ChessAlive!' in character as a medieval knight.",
                system_prompt="You are a chivalrous knight piece on a chess board.",
                max_tokens=50
            )
            print(f"LLM Response: {response}")
            return True
        except Exception as e:
            print(f"LLM Error: {e}")
            return False


async def test_cvc_game(max_moves: int = 6):
    """Test Computer vs Computer game with commentary."""
    print_separator(f"Testing CvC Game (max {max_moves} moves)")

    config = MatchConfig(
        mode=GameMode.COMPUTER_VS_COMPUTER,
        white_name="King Aldric's Army",
        black_name="King Malachar's Forces",
        enable_commentary=True,
        commentary_frequency="every_move",
        stockfish_skill=5,  # Lower skill for faster games
        stockfish_depth=8,
        max_moves=max_moves,
    )

    game_config = GameConfig()

    async with Match(config, game_config, on_event) as match:
        await match.setup()
        result = await match.run()

        print(f"\nFinal Result: {result.name}")
        print(f"PGN:\n{match.game.to_pgn()}")

    return True


async def test_lvl_game(max_moves: int = 4):
    """Test LLM vs LLM game with different styles."""
    print_separator(f"Testing LLM vs LLM Game (max {max_moves} moves)")

    config = MatchConfig(
        mode=GameMode.LLM_VS_LLM,
        white_name="Aggressive LLM (White)",
        black_name="Defensive LLM (Black)",
        enable_commentary=True,
        commentary_frequency="every_move",
        llm_style_white="aggressive",
        llm_style_black="defensive",
        max_moves=max_moves,
    )

    game_config = GameConfig()

    async with Match(config, game_config, on_event) as match:
        await match.setup()
        result = await match.run()

        print(f"\nFinal Result: {result.name}")
        print(f"PGN:\n{match.game.to_pgn()}")

    return True


async def test_lvc_game(max_moves: int = 4):
    """Test LLM vs Computer game."""
    print_separator(f"Testing LLM vs Computer Game (max {max_moves} moves)")

    config = MatchConfig(
        mode=GameMode.LLM_VS_COMPUTER,
        white_name="Creative LLM",
        black_name="Stockfish",
        enable_commentary=True,
        commentary_frequency="key_moments",
        llm_style_white="creative",
        stockfish_skill=5,
        stockfish_depth=8,
        max_moves=max_moves,
    )

    game_config = GameConfig()

    async with Match(config, game_config, on_event) as match:
        await match.setup()
        result = await match.run()

        print(f"\nFinal Result: {result.name}")
        print(f"PGN:\n{match.game.to_pgn()}")

    return True


async def main():
    """Run all tests."""
    print_separator("ChessAlive Feature Tests")
    print("Testing recently added features...")

    results = {}

    # Test 1: Personas
    try:
        results["Personas"] = await test_personas()
    except Exception as e:
        print(f"Personas test failed: {e}")
        results["Personas"] = False

    # Test 2: LLM Connection
    try:
        results["LLM Connection"] = await test_llm_connection()
    except Exception as e:
        print(f"LLM Connection test failed: {e}")
        results["LLM Connection"] = False

    # Test 3: CvC Game
    try:
        results["CvC Game"] = await test_cvc_game(max_moves=6)
    except Exception as e:
        print(f"CvC Game test failed: {e}")
        import traceback
        traceback.print_exc()
        results["CvC Game"] = False

    # Test 4: LvL Game (if LLM works)
    if results.get("LLM Connection"):
        try:
            results["LvL Game"] = await test_lvl_game(max_moves=4)
        except Exception as e:
            print(f"LvL Game test failed: {e}")
            import traceback
            traceback.print_exc()
            results["LvL Game"] = False

    # Test 5: LvC Game (if LLM works)
    if results.get("LLM Connection"):
        try:
            results["LvC Game"] = await test_lvc_game(max_moves=4)
        except Exception as e:
            print(f"LvC Game test failed: {e}")
            import traceback
            traceback.print_exc()
            results["LvC Game"] = False

    # Summary
    print_separator("Test Summary")
    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {test_name}: {status}")

    return all(results.values())


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
