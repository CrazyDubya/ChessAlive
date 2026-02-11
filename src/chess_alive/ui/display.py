"""Board display utilities using Rich library."""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
import chess

from ..core.game import ChessGame, MoveRecord
from ..core.piece import Color


class BoardDisplay:
    """Display chess board and game state using Rich."""

    # Unicode chess pieces
    UNICODE_PIECES = {
        (chess.KING, chess.WHITE): "",
        (chess.QUEEN, chess.WHITE): "",
        (chess.ROOK, chess.WHITE): "",
        (chess.BISHOP, chess.WHITE): "",
        (chess.KNIGHT, chess.WHITE): "",
        (chess.PAWN, chess.WHITE): "",
        (chess.KING, chess.BLACK): "",
        (chess.QUEEN, chess.BLACK): "",
        (chess.ROOK, chess.BLACK): "",
        (chess.BISHOP, chess.BLACK): "",
        (chess.KNIGHT, chess.BLACK): "",
        (chess.PAWN, chess.BLACK): "",
    }

    # ASCII pieces (fallback)
    ASCII_PIECES = {
        (chess.KING, chess.WHITE): "K",
        (chess.QUEEN, chess.WHITE): "Q",
        (chess.ROOK, chess.WHITE): "R",
        (chess.BISHOP, chess.WHITE): "B",
        (chess.KNIGHT, chess.WHITE): "N",
        (chess.PAWN, chess.WHITE): "P",
        (chess.KING, chess.BLACK): "k",
        (chess.QUEEN, chess.BLACK): "q",
        (chess.ROOK, chess.BLACK): "r",
        (chess.BISHOP, chess.BLACK): "b",
        (chess.KNIGHT, chess.BLACK): "n",
        (chess.PAWN, chess.BLACK): "p",
    }

    def __init__(
        self,
        console: Optional[Console] = None,
        use_unicode: bool = True,
        light_square: str = "#F0D9B5",
        dark_square: str = "#B58863",
    ):
        """
        Initialize board display.

        Args:
            console: Rich console to use
            use_unicode: Whether to use Unicode chess pieces
            light_square: Color for light squares
            dark_square: Color for dark squares
        """
        self.console = console or Console()
        self.use_unicode = use_unicode
        self.light_square = light_square
        self.dark_square = dark_square
        self.pieces = self.UNICODE_PIECES if use_unicode else self.ASCII_PIECES

    def get_piece_symbol(self, piece: Optional[chess.Piece]) -> str:
        """Get the display symbol for a piece."""
        if piece is None:
            return " "
        return self.pieces.get((piece.piece_type, piece.color), "?")

    def render_board(
        self,
        game: ChessGame,
        flip: bool = False,
        highlight_squares: Optional[set[chess.Square]] = None,
        last_move: Optional[chess.Move] = None,
    ) -> str:
        """
        Render the board as a string.

        Args:
            game: The game to render
            flip: Whether to flip the board (black's perspective)
            highlight_squares: Squares to highlight
            last_move: Last move to highlight

        Returns:
            String representation of the board
        """
        highlight_squares = highlight_squares or set()

        # Add last move squares to highlights
        if last_move:
            highlight_squares.add(last_move.from_square)
            highlight_squares.add(last_move.to_square)

        lines = []
        ranks = range(7, -1, -1) if not flip else range(8)
        files = range(8) if not flip else range(7, -1, -1)

        # Top border
        lines.append("  +" + "-" * 17 + "+")

        for rank in ranks:
            line_parts = [f"{rank + 1} |"]
            for file in files:
                square = chess.square(file, rank)
                piece = game.board.piece_at(square)
                symbol = self.get_piece_symbol(piece)

                # Add highlighting marker
                if square in highlight_squares:
                    line_parts.append(f"[{symbol}]")
                else:
                    line_parts.append(f" {symbol} ")

            line_parts.append("|")
            lines.append("".join(line_parts))

        # Bottom border
        lines.append("  +" + "-" * 17 + "+")

        # File labels
        file_labels = "    a  b  c  d  e  f  g  h" if not flip else "    h  g  f  e  d  c  b  a"
        lines.append(file_labels)

        return "\n".join(lines)

    def print_board(
        self,
        game: ChessGame,
        flip: bool = False,
        highlight_squares: Optional[set[chess.Square]] = None,
        last_move: Optional[chess.Move] = None,
        title: Optional[str] = None,
    ):
        """Print the board to the console."""
        board_str = self.render_board(game, flip, highlight_squares, last_move)

        if title:
            self.console.print(Panel(board_str, title=title))
        else:
            self.console.print(board_str)

    def print_game_status(self, game: ChessGame):
        """Print current game status."""
        status_parts = []

        status_parts.append(f"Move: {game.fullmove_number}")
        status_parts.append(f"Turn: {game.current_turn.name_str}")

        if game.is_check:
            status_parts.append("[bold red]CHECK![/bold red]")
        if game.is_checkmate:
            status_parts.append("[bold red]CHECKMATE![/bold red]")
        if game.is_stalemate:
            status_parts.append("[bold yellow]STALEMATE[/bold yellow]")

        self.console.print(" | ".join(status_parts))

    def print_move(self, record: MoveRecord, move_number: int):
        """Print a move record."""
        color = "white" if record.piece.color == Color.WHITE else "black"
        prefix = f"{move_number}." if record.piece.color == Color.WHITE else f"{move_number}..."

        parts = [f"[bold]{prefix}[/bold]"]
        parts.append(f"[{color}]{record.san}[/{color}]")

        if record.captured_piece:
            parts.append(f"(captures {record.captured_piece.display_name})")

        if record.is_checkmate:
            parts.append("[bold red]CHECKMATE![/bold red]")
        elif record.is_check:
            parts.append("[red]CHECK![/red]")

        self.console.print(" ".join(parts))

    def print_commentary(self, piece_name: str, text: str):
        """Print piece commentary."""
        self.console.print(
            Panel(
                text,
                title=f"[bold]{piece_name}[/bold]",
                border_style="dim",
            )
        )

    def print_captured_pieces(self, game: ChessGame):
        """Print captured pieces for both sides."""
        white_captured = " ".join(
            self.get_piece_symbol(
                chess.Piece(p.piece_type.value, chess.WHITE)
            )
            for p in game.captured_white
        )
        black_captured = " ".join(
            self.get_piece_symbol(
                chess.Piece(p.piece_type.value, chess.BLACK)
            )
            for p in game.captured_black
        )

        if white_captured or black_captured:
            self.console.print(f"Captured: White: {white_captured or 'none'} | Black: {black_captured or 'none'}")

    def print_legal_moves(self, game: ChessGame):
        """Print all legal moves."""
        moves = [game.board.san(m) for m in game.get_legal_moves()]
        self.console.print(f"Legal moves ({len(moves)}): {', '.join(moves)}")

    def print_result(self, game: ChessGame):
        """Print the game result."""
        result = game.result

        if result == result.WHITE_WINS:
            self.console.print("[bold]Result: White wins![/bold]")
        elif result == result.BLACK_WINS:
            self.console.print("[bold]Result: Black wins![/bold]")
        elif result == result.DRAW:
            self.console.print("[bold]Result: Draw[/bold]")
        else:
            self.console.print("[dim]Game in progress[/dim]")


def create_simple_board_string(board: chess.Board, use_unicode: bool = True) -> str:
    """Create a simple board string without Rich formatting."""
    pieces = BoardDisplay.UNICODE_PIECES if use_unicode else BoardDisplay.ASCII_PIECES

    lines = []
    for rank in range(7, -1, -1):
        row = []
        for file in range(8):
            piece = board.piece_at(chess.square(file, rank))
            if piece:
                symbol = pieces.get((piece.piece_type, piece.color), "?")
            else:
                symbol = "."
            row.append(symbol)
        lines.append(f"{rank + 1} " + " ".join(row))

    lines.append("  a b c d e f g h")
    return "\n".join(lines)
