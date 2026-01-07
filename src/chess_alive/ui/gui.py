"""Tkinter-based GUI for ChessAlive with commentary display."""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import asyncio
import threading
from typing import Optional, Callable
import chess

from ..core.game import ChessGame, MoveRecord
from ..core.piece import Color, PieceType
from ..llm.client import LLMClient
from ..llm.commentary import CommentaryEngine, Commentary
from ..config import get_config


# Unicode chess pieces
PIECE_SYMBOLS = {
    (chess.KING, chess.WHITE): "♔",
    (chess.QUEEN, chess.WHITE): "♕",
    (chess.ROOK, chess.WHITE): "♖",
    (chess.BISHOP, chess.WHITE): "♗",
    (chess.KNIGHT, chess.WHITE): "♘",
    (chess.PAWN, chess.WHITE): "♙",
    (chess.KING, chess.BLACK): "♚",
    (chess.QUEEN, chess.BLACK): "♛",
    (chess.ROOK, chess.BLACK): "♜",
    (chess.BISHOP, chess.BLACK): "♝",
    (chess.KNIGHT, chess.BLACK): "♞",
    (chess.PAWN, chess.BLACK): "♟",
}

# Colors
LIGHT_SQUARE = "#F0D9B5"
DARK_SQUARE = "#B58863"
HIGHLIGHT_SQUARE = "#CDD26A"
SELECTED_SQUARE = "#829769"


class ChessBoard(tk.Frame):
    """Chess board widget."""

    def __init__(self, parent, on_move: Optional[Callable[[chess.Move], None]] = None):
        super().__init__(parent)
        self.on_move = on_move
        self.game = ChessGame()
        self.selected_square: Optional[chess.Square] = None
        self.highlighted_squares: set[chess.Square] = set()
        self.flipped = False

        self.square_size = 64
        self.squares: dict[chess.Square, tk.Label] = {}

        self._create_board()
        self._update_board()

    def _create_board(self):
        """Create the board squares."""
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                is_light = (row + col) % 2 == 0
                bg_color = LIGHT_SQUARE if is_light else DARK_SQUARE

                label = tk.Label(
                    self,
                    text="",
                    font=("Arial", 36),
                    width=2,
                    height=1,
                    bg=bg_color,
                    relief=tk.FLAT,
                )
                label.grid(row=row, column=col, sticky="nsew")
                label.bind("<Button-1>", lambda e, sq=square: self._on_square_click(sq))

                self.squares[square] = label

        # Configure grid weights
        for i in range(8):
            self.grid_rowconfigure(i, weight=1)
            self.grid_columnconfigure(i, weight=1)

    def _update_board(self):
        """Update the board display."""
        last_move = self.game.move_history[-1].move if self.game.move_history else None

        for square, label in self.squares.items():
            row = 7 - chess.square_rank(square)
            col = chess.square_file(square)
            is_light = (row + col) % 2 == 0

            # Determine background color
            if square == self.selected_square:
                bg_color = SELECTED_SQUARE
            elif square in self.highlighted_squares:
                bg_color = HIGHLIGHT_SQUARE
            elif last_move and square in (last_move.from_square, last_move.to_square):
                bg_color = HIGHLIGHT_SQUARE
            else:
                bg_color = LIGHT_SQUARE if is_light else DARK_SQUARE

            label.configure(bg=bg_color)

            # Update piece
            piece = self.game.board.piece_at(square)
            if piece:
                symbol = PIECE_SYMBOLS.get((piece.piece_type, piece.color), "?")
                label.configure(text=symbol)
            else:
                label.configure(text="")

    def _on_square_click(self, square: chess.Square):
        """Handle square click."""
        if self.selected_square is None:
            # Select a piece
            piece = self.game.board.piece_at(square)
            if piece and piece.color == self.game.board.turn:
                self.selected_square = square
                # Highlight legal moves
                self.highlighted_squares = {
                    m.to_square
                    for m in self.game.get_legal_moves_for_square(square)
                }
                self._update_board()
        else:
            # Try to make a move
            move = None
            for m in self.game.get_legal_moves_for_square(self.selected_square):
                if m.to_square == square:
                    # Handle promotion
                    if m.promotion:
                        move = chess.Move(
                            self.selected_square, square, promotion=chess.QUEEN
                        )
                    else:
                        move = m
                    break

            if move and self.game.is_legal_move(move):
                record = self.game.make_move(move)
                if record and self.on_move:
                    self.on_move(record)

            # Clear selection
            self.selected_square = None
            self.highlighted_squares.clear()
            self._update_board()

    def set_game(self, game: ChessGame):
        """Set the game to display."""
        self.game = game
        self.selected_square = None
        self.highlighted_squares.clear()
        self._update_board()

    def reset(self):
        """Reset the board."""
        self.game.reset()
        self.selected_square = None
        self.highlighted_squares.clear()
        self._update_board()


class CommentaryPanel(tk.Frame):
    """Panel displaying piece commentary."""

    def __init__(self, parent):
        super().__init__(parent, bg="#2b2b2b")
        self._create_widgets()

    def _create_widgets(self):
        """Create panel widgets."""
        # Title
        title = tk.Label(
            self,
            text="Piece Commentary",
            font=("Arial", 14, "bold"),
            bg="#2b2b2b",
            fg="white",
        )
        title.pack(pady=10)

        # Commentary text area
        self.text_area = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            width=40,
            height=20,
            font=("Arial", 11),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            state=tk.DISABLED,
        )
        self.text_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Configure tags for styling
        self.text_area.tag_configure("piece_name", foreground="#4fc3f7", font=("Arial", 11, "bold"))
        self.text_area.tag_configure("white_piece", foreground="#ffffff")
        self.text_area.tag_configure("black_piece", foreground="#b0b0b0")
        self.text_area.tag_configure("move", foreground="#81c784")
        self.text_area.tag_configure("capture", foreground="#ef5350")
        self.text_area.tag_configure("check", foreground="#ffb74d")

    def add_commentary(self, piece_name: str, text: str, color: Color = Color.WHITE):
        """Add a commentary entry."""
        self.text_area.configure(state=tk.NORMAL)

        # Add separator if not first entry
        if self.text_area.get("1.0", tk.END).strip():
            self.text_area.insert(tk.END, "\n" + "─" * 35 + "\n")

        # Add piece name
        tag = "white_piece" if color == Color.WHITE else "black_piece"
        self.text_area.insert(tk.END, f"[{piece_name}]\n", ("piece_name", tag))

        # Add commentary text
        self.text_area.insert(tk.END, f'"{text}"\n')

        # Scroll to bottom
        self.text_area.see(tk.END)
        self.text_area.configure(state=tk.DISABLED)

    def add_move_info(self, move_record: MoveRecord):
        """Add move information."""
        self.text_area.configure(state=tk.NORMAL)

        # Move notation
        move_text = f"Move: {move_record.san}"
        if move_record.captured_piece:
            move_text += f" (captures {move_record.captured_piece.piece_type.name_str})"

        tag = "move"
        if move_record.captured_piece:
            tag = "capture"
        if move_record.is_check:
            move_text += " CHECK!"
            tag = "check"
        if move_record.is_checkmate:
            move_text = f"Move: {move_record.san} CHECKMATE!"

        self.text_area.insert(tk.END, f"\n{move_text}\n", tag)
        self.text_area.configure(state=tk.DISABLED)

    def clear(self):
        """Clear all commentary."""
        self.text_area.configure(state=tk.NORMAL)
        self.text_area.delete("1.0", tk.END)
        self.text_area.configure(state=tk.DISABLED)


class StatusBar(tk.Frame):
    """Status bar showing game state."""

    def __init__(self, parent):
        super().__init__(parent, bg="#333333")
        self._create_widgets()

    def _create_widgets(self):
        """Create status widgets."""
        self.turn_label = tk.Label(
            self,
            text="White to move",
            font=("Arial", 12),
            bg="#333333",
            fg="white",
            padx=10,
        )
        self.turn_label.pack(side=tk.LEFT)

        self.move_label = tk.Label(
            self,
            text="Move: 1",
            font=("Arial", 12),
            bg="#333333",
            fg="white",
            padx=10,
        )
        self.move_label.pack(side=tk.LEFT)

        self.status_label = tk.Label(
            self,
            text="",
            font=("Arial", 12, "bold"),
            bg="#333333",
            fg="#ffb74d",
            padx=10,
        )
        self.status_label.pack(side=tk.RIGHT)

    def update(self, game: ChessGame):
        """Update status from game state."""
        turn = "White" if game.current_turn == Color.WHITE else "Black"
        self.turn_label.configure(text=f"{turn} to move")
        self.move_label.configure(text=f"Move: {game.fullmove_number}")

        if game.is_checkmate:
            winner = "Black" if game.current_turn == Color.WHITE else "White"
            self.status_label.configure(text=f"Checkmate! {winner} wins!", fg="#ef5350")
        elif game.is_stalemate:
            self.status_label.configure(text="Stalemate - Draw", fg="#ffb74d")
        elif game.is_check:
            self.status_label.configure(text="Check!", fg="#ffb74d")
        else:
            self.status_label.configure(text="")


class ChessAliveGUI:
    """Main GUI application for ChessAlive."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ChessAlive - Where Every Piece Has a Voice")
        self.root.configure(bg="#1e1e1e")

        self.config = get_config()
        self.game = ChessGame()
        self.llm_client: Optional[LLMClient] = None
        self.commentary_engine: Optional[CommentaryEngine] = None

        # Initialize LLM if configured
        if self.config.llm.is_configured:
            self.llm_client = LLMClient(self.config.llm)
            self.commentary_engine = CommentaryEngine(self.llm_client, "every_move")

        self._create_ui()
        self._setup_menu()

    def _create_ui(self):
        """Create the main UI layout."""
        # Main container
        main_frame = tk.Frame(self.root, bg="#1e1e1e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left side - Board
        left_frame = tk.Frame(main_frame, bg="#1e1e1e")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH)

        self.board = ChessBoard(left_frame, on_move=self._on_move)
        self.board.pack(padx=10, pady=10)

        # Right side - Commentary
        right_frame = tk.Frame(main_frame, bg="#1e1e1e")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        self.commentary_panel = CommentaryPanel(right_frame)
        self.commentary_panel.pack(fill=tk.BOTH, expand=True)

        # Bottom - Status bar
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_bar.update(self.game)

    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Game menu
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Game", menu=game_menu)
        game_menu.add_command(label="New Game", command=self._new_game)
        game_menu.add_separator()
        game_menu.add_command(label="Exit", command=self.root.quit)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _on_move(self, record: MoveRecord):
        """Handle a move being made."""
        self.status_bar.update(self.game)
        self.commentary_panel.add_move_info(record)

        # Generate commentary asynchronously
        if self.commentary_engine:
            thread = threading.Thread(
                target=self._generate_commentary_thread,
                args=(record,),
                daemon=True,
            )
            thread.start()
        else:
            # Use fallback commentary
            self._add_fallback_commentary(record)

    def _generate_commentary_thread(self, record: MoveRecord):
        """Generate commentary in a background thread."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            commentaries = loop.run_until_complete(
                self.commentary_engine.generate_move_commentary(self.game, record)
            )
            loop.close()

            # Update UI from main thread
            for c in commentaries:
                self.root.after(0, lambda c=c: self.commentary_panel.add_commentary(
                    c.piece.display_name,
                    c.text,
                    c.piece.color,
                ))
        except Exception as e:
            # Use fallback on error
            self.root.after(0, lambda: self._add_fallback_commentary(record))

    def _add_fallback_commentary(self, record: MoveRecord):
        """Add fallback commentary without LLM."""
        piece = record.piece
        if record.captured_piece:
            text = "Victory! Another enemy falls!"
        elif record.is_check:
            text = "Check! The king trembles!"
        else:
            text = "Onward! The battle continues."

        self.commentary_panel.add_commentary(
            piece.display_name,
            text,
            piece.color,
        )

    def _new_game(self):
        """Start a new game."""
        self.game.reset()
        self.board.set_game(self.game)
        self.status_bar.update(self.game)
        self.commentary_panel.clear()

        # Opening commentary
        self.commentary_panel.add_commentary(
            "King Aldric",
            "Let the battle commence! May wisdom guide our moves.",
            Color.WHITE,
        )
        self.commentary_panel.add_commentary(
            "King Malachar",
            "So it begins. We shall see who commands the board this day.",
            Color.BLACK,
        )

    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About ChessAlive",
            "ChessAlive - Where Every Piece Has a Voice!\n\n"
            "A chess game where each piece provides\n"
            "LLM-powered commentary during gameplay.\n\n"
            "Version 0.1.0"
        )

    def run(self):
        """Run the GUI application."""
        # Add opening commentary
        self.commentary_panel.add_commentary(
            "King Aldric",
            "Greetings, noble player. The board awaits your command.",
            Color.WHITE,
        )

        self.root.mainloop()

        # Cleanup
        if self.llm_client:
            asyncio.run(self.llm_client.close())


def main():
    """Main entry point for GUI."""
    app = ChessAliveGUI()
    app.run()


if __name__ == "__main__":
    main()
