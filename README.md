# ChessAlive

A chess game where every piece has a voice! Each chess piece is connected to an LLM and provides commentary during the game.

## Features

- **Full Chess Implementation**: Complete chess rules with all special moves (castling, en passant, promotion)
- **LLM-Powered Commentary**: Each piece has its own personality and provides in-character commentary
- **Multiple Game Modes**:
  - Player vs Player (PvP) - Two humans
  - Player vs Computer (PvC) - Human vs Stockfish
  - Computer vs Computer (CvC) - Stockfish vs Stockfish
  - Player vs LLM (PvL) - Human vs AI language model
  - LLM vs LLM (LvL) - Two AI language models
  - LLM vs Computer (LvC) - AI language model vs Stockfish

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ChessAlive.git
cd ChessAlive

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Required for LLM modes:
- `OPENROUTER_API_KEY`: Your OpenRouter API key (get one at https://openrouter.ai)

### Optional:
- `CHESS_LLM_MODEL`: LLM model to use (default: `openai/gpt-4o-mini`)
- `STOCKFISH_PATH`: Path to Stockfish executable (auto-detected if installed)

### Installing Stockfish

For computer opponent modes, you need Stockfish installed:

**Ubuntu/Debian:**
```bash
sudo apt install stockfish
```

**macOS:**
```bash
brew install stockfish
```

**Windows:**
Download from https://stockfishchess.org/download/

## Usage

```bash
# Run the game
chess-alive

# Or run directly
python -m chess_alive.main
```

### Game Controls

During a human player's turn:
- Enter moves in standard notation (e.g., `e4`, `Nf3`, `O-O`)
- Or use UCI notation (e.g., `e2e4`, `g1f3`)
- Type `help` for available commands
- Type `moves` to see all legal moves
- Type `resign` to resign the game

## Architecture

```
src/chess_alive/
├── core/           # Chess game logic
│   ├── game.py     # Game state management
│   └── piece.py    # Piece representation & personalities
├── players/        # Player implementations
│   ├── human.py    # Human player (CLI input)
│   ├── computer.py # Stockfish-based AI
│   └── llm_player.py # LLM-based player
├── llm/            # LLM integration
│   ├── client.py   # OpenRouter API client
│   └── commentary.py # Piece commentary system
├── modes/          # Game modes
│   ├── mode.py     # Game mode definitions
│   └── match.py    # Match orchestration
└── ui/             # User interface
    ├── cli.py      # Command-line interface
    └── display.py  # Board display utilities
```

## Piece Personalities

Each piece has a unique personality that influences its commentary:

### White Pieces
- **King Aldric**: Wise ruler, measured speech
- **Queen Seraphina**: Fierce warrior queen
- **Sir Galahad** (Knight): Chivalrous and brave
- **Bishop Luminos**: Cunning advisor
- **Tower Guard** (Rook): Stalwart defender
- **Footsoldier** (Pawn): Humble but determined

### Black Pieces
- **King Malachar**: Cunning strategist
- **Queen Nyx**: Shadow assassin
- **The Black Rider** (Knight): Fearsome raider
- **Bishop Umbra**: Dark oracle
- **Dark Tower** (Rook): Silent sentinel
- **Dark Infantry** (Pawn): Devoted servant

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=chess_alive

# Run specific test file
pytest tests/test_game.py -v
```

## API Reference

### OpenRouter Integration

ChessAlive uses [OpenRouter](https://openrouter.ai) for LLM access, which provides:
- Access to 100+ AI models through one API
- Automatic fallbacks and routing
- No markup on inference costs

### Supported Models

Any model available on OpenRouter can be used. Recommended:
- `openai/gpt-4o-mini` (default, good balance)
- `openai/gpt-4o` (stronger reasoning)
- `anthropic/claude-3-haiku` (fast, economical)
- `anthropic/claude-3-sonnet` (strong analysis)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.
