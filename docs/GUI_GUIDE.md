# ChessAlive GUI Guide

## Overview

ChessAlive includes a graphical user interface built with Tkinter that displays both the chess board and piece commentary in real-time.

## Installation

```bash
# Install with GUI dependencies
pip install -e ".[gui]"

# Run the GUI
chess-alive-gui
# Or
python -m chess_alive.ui.gui
```

## Features

### Interactive Chess Board
- Click-to-move interface
- Legal move highlighting
- Last move highlighting
- Unicode chess pieces

### Commentary Panel
- Real-time LLM-generated commentary
- Color-coded by piece color (white/black)
- Move annotations with captures and checks
- Scrollable history

### Status Bar
- Current turn indicator
- Move number
- Check/Checkmate/Stalemate alerts

## GUI Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ChessAlive - Where Every Piece Has a Voice                          [─][□][×]│
├─────────────────────────────────────────────────────────────────────────────┤
│  Game  Help                                                                  │
├────────────────────────────┬────────────────────────────────────────────────┤
│                            │  Piece Commentary                              │
│  ┌─────────────────────┐   │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│  │ ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜ │   │                                                │
│  │ ♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟ │   │  Move: e4                                      │
│  │ · · · · · · · · │   │  ───────────────────────────────────────       │
│  │ · · · · · · · · │   │  [Footsoldier]                                  │
│  │ · · · · ♙ · · · │   │  "Onward! I march forth to claim the center    │
│  │ · · · · · · · · │   │   for our king! The battle begins!"            │
│  │ ♙ ♙ ♙ ♙ · ♙ ♙ ♙ │   │                                                │
│  │ ♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖ │   │  ───────────────────────────────────────       │
│  └─────────────────────┘   │  [King Aldric]                               │
│    a b c d e f g h         │  "A wise opening. The center must be         │
│                            │   controlled for victory."                    │
│                            │                                                │
│                            │  ───────────────────────────────────────       │
│                            │  Move: e5                                      │
│                            │  [Dark Infantry]                               │
│                            │  "We shall not cede ground so easily!         │
│                            │   The center is contested!"                   │
│                            │                                                │
├────────────────────────────┴────────────────────────────────────────────────┤
│  White to move │ Move: 2 │                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## How to Play

### Making Moves
1. **Click** on a piece to select it
2. Legal move squares are **highlighted in green**
3. **Click** on a highlighted square to make the move
4. Commentary appears automatically in the right panel

### Special Moves
- **Castling**: Click the king, then click the castling square (g1/c1 for white, g8/c8 for black)
- **En Passant**: Click the capturing pawn, then click the en passant square
- **Promotion**: Automatically promotes to Queen (future: selection dialog)

### Menu Options
- **Game → New Game**: Start a fresh game
- **Game → Exit**: Close the application
- **Help → About**: Show version information

## Commentary Types

| Event | Commentary |
|-------|-----------|
| Regular Move | Piece comments on the move |
| Capture | Both capturing and captured pieces comment |
| Check | King reacts to the threat |
| Checkmate | Victory/defeat commentary from kings |

## Configuration

The GUI uses the same configuration as the CLI:

```bash
# Required for LLM commentary
export OPENROUTER_API_KEY="your-key-here"

# Optional: Change LLM model
export CHESS_LLM_MODEL="openai/gpt-4o-mini"
```

Without an API key, the GUI falls back to pre-written commentary templates.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Ctrl+N | New Game |
| Ctrl+Q | Quit |
| F1 | About |

## Troubleshooting

### "No module named 'tkinter'"
Install tkinter for your Python version:
```bash
# Ubuntu/Debian
sudo apt install python3-tk

# macOS (usually included)
# Windows (usually included)
```

### GUI is slow
- LLM commentary generation takes 1-3 seconds
- Commentary runs in background thread
- Game moves are instant, commentary follows

### No commentary appearing
- Check that `OPENROUTER_API_KEY` is set
- Check internet connectivity
- Fallback commentary will appear on API errors

## Screenshots

### Initial Board
```
 ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜
 ♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟
 · · · · · · · ·
 · · · · · · · ·
 · · · · · · · ·
 · · · · · · · ·
 ♙ ♙ ♙ ♙ ♙ ♙ ♙ ♙
 ♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖
```

### After 1. e4 e5 2. Nf3 (with highlights)
```
 ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜
 ♟ ♟ ♟ ♟ · ♟ ♟ ♟
 · · · · · · · ·
 · · · · ♟ · · ·
 · · · · ♙ · · ·
 · · · · · ♘ · ·    ← Knight just moved
 ♙ ♙ ♙ ♙ · ♙ ♙ ♙
 ♖ ♘ ♗ ♕ ♔ ♗ · ♖
```

## API Usage

```python
from chess_alive.ui.gui import ChessAliveGUI

# Create and run GUI
app = ChessAliveGUI()
app.run()
```

Or use individual components:

```python
import tkinter as tk
from chess_alive.ui.gui import ChessBoard, CommentaryPanel
from chess_alive.core.game import ChessGame

root = tk.Tk()
game = ChessGame()

# Create board
board = ChessBoard(root, on_move=handle_move)
board.set_game(game)

# Create commentary panel
panel = CommentaryPanel(root)
panel.add_commentary("King Aldric", "The game begins!")
```
