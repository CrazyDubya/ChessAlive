# ChessAlive Help Guide

## Quick Start

```bash
# Install
pip install -e .

# Run the game
chess-alive
# Or
python -m chess_alive.main
```

## Configuration

### OpenRouter API Key (Required for LLM modes)

Set your OpenRouter API key:

```bash
# Option 1: Environment variable
export OPENROUTER_API_KEY="your-key-here"

# Option 2: Create .env file
cp .env.example .env
# Edit .env and add your key
```

Get your API key at: https://openrouter.ai

### Stockfish (Required for Computer modes)

Install Stockfish chess engine:

```bash
# Ubuntu/Debian
sudo apt install stockfish

# macOS
brew install stockfish

# Or set custom path
export STOCKFISH_PATH="/path/to/stockfish"
```

## Game Modes

| Mode | Command | Description |
|------|---------|-------------|
| PvP  | 1       | Player vs Player - Two humans |
| PvC  | 2       | Player vs Computer (Stockfish) |
| CvC  | 3       | Computer vs Computer |
| PvL  | 4       | Player vs LLM |
| LvL  | 5       | LLM vs LLM |
| LvC  | 6       | LLM vs Computer |

## In-Game Commands

During your turn, you can enter:

| Command | Description |
|---------|-------------|
| `e4`, `Nf3`, `O-O` | Standard chess notation (SAN) |
| `e2e4`, `g1f3` | UCI notation |
| `help` | Show available commands |
| `moves` | List all legal moves |
| `resign` | Resign the game |
| `quit` | Exit the game |

## Piece Personalities

Each piece has a unique personality that influences their commentary:

### White Pieces
| Piece | Name | Archetype |
|-------|------|-----------|
| King | King Aldric | Wise ruler |
| Queen | Queen Seraphina | Fierce warrior queen |
| Rook | Tower Guard | Stalwart defender |
| Bishop | Bishop Luminos | Cunning advisor |
| Knight | Sir Galahad | Chivalrous knight |
| Pawn | Footsoldier | Humble soldier |

### Black Pieces
| Piece | Name | Archetype |
|-------|------|-----------|
| King | King Malachar | Cunning strategist |
| Queen | Queen Nyx | Shadow assassin |
| Rook | Dark Tower | Silent sentinel |
| Bishop | Bishop Umbra | Dark oracle |
| Knight | The Black Rider | Fearsome raider |
| Pawn | Dark Infantry | Devoted servant |

## Commentary Settings

When starting a game, you can configure commentary:

- **every_move**: Commentary on every move
- **captures_only**: Only when pieces are captured
- **key_moments**: Captures, checks, promotions, castling

## Example Game Session

```
╭──────────────────────────────────────────────────────────────────╮
│                                                                  │
│    _____ _                        _    _ _                       │
│   / ____| |                      | |  | (_)                      │
│  | |    | |__   ___  ___ ___     | |  | |___   _____             │
│  | |____| | | |  __/\__ \__ \    \  /\  / |\ V /  __/            │
│   \_____|_| |_|\___||___/___/     \/  \/|_| \_/ \___|            │
│                                                                  │
│     Where every piece has a voice!                               │
│                                                                  │
╰──────────────────────────────────────────────────────────────────╯

                         Game Modes
┏━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Option ┃ Mode ┃ Description                              ┃
┡━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1      │ pvp  │ Player vs Player - Two humans            │
│ 2      │ pvc  │ Player vs Computer - Stockfish           │
│ 3      │ cvc  │ Computer vs Computer                     │
│ 4      │ pvl  │ Player vs LLM                            │
│ 5      │ lvl  │ LLM vs LLM                               │
│ 6      │ lvc  │ LLM vs Computer                          │
└────────┴──────┴──────────────────────────────────────────┘

Select game mode [1]: 1

Configuring Player vs Player - Two humans

White player name [Player 1]: Alice
Black player name [Player 2]: Bob
Enable piece commentary? [Y/n]: y
Commentary frequency [every_move/captures_only/key_moments]: key_moments

Game started!
White: Alice
Black: Bob

  +-----------------+
8 | ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜ |
7 | ♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟ |
6 | . . . . . . . . |
5 | . . . . . . . . |
4 | . . . . . . . . |
3 | . . . . . . . . |
2 | ♙ ♙ ♙ ♙ ♙ ♙ ♙ ♙ |
1 | ♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖ |
  +-----------------+
    a b c d e f g h

Move: 1 | Turn: White

White's move (or 'help'): e4

1. e4

╭─ Footsoldier ────────────────────────────────────────────────────╮
│ "Onward! I march forth to claim the center for our king!"        │
╰──────────────────────────────────────────────────────────────────╯
```

## Troubleshooting

### "OpenRouter API key not configured"
Set the `OPENROUTER_API_KEY` environment variable or create a `.env` file.

### "Stockfish not found"
Install Stockfish or set `STOCKFISH_PATH` to the executable location.

### API returns 503 error
The LLM service is temporarily unavailable. The game will use fallback commentary.

### Move not recognized
Use standard algebraic notation (e4, Nf3, O-O) or UCI format (e2e4).

## API Usage

You can also use ChessAlive programmatically:

```python
import asyncio
from chess_alive.core.game import ChessGame
from chess_alive.llm.client import LLMClient
from chess_alive.llm.commentary import CommentaryEngine
from chess_alive.config import get_config

async def main():
    config = get_config()
    game = ChessGame()
    client = LLMClient(config.llm)
    engine = CommentaryEngine(client)

    # Make a move
    record = game.make_move_san("e4")

    # Get commentary
    commentaries = await engine.generate_move_commentary(game, record)
    for c in commentaries:
        print(f"{c.piece.display_name}: {c.text}")

    await client.close()

asyncio.run(main())
```

## Support

For issues and feature requests, visit:
https://github.com/yourusername/ChessAlive/issues
