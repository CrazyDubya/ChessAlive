"""Board display utilities using Rich library."""

from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.style import Style
import chess

from ..core.game import ChessGame, MoveRecord, GameResult
from ..core.piece import Color, PieceType


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

    # Styles
    STYLE_WHITE_MOVE = Style(color="white", bold=True)
    STYLE_BLACK_MOVE = Style(color="bright_black", bold=True)
    STYLE_CAPTURE = Style(color="red")
    STYLE_CHECK = Style(color="red", bold=True)
    STYLE_CHECKMATE = Style(color="bright_red", bold=True, underline=True)
    STYLE_CASTLING = Style(color="cyan")
    STYLE_PROMOTION = Style(color="magenta", bold=True)
    STYLE_HEADER = Style(color="bright_blue", bold=True)
    STYLE_DIM = Style(dim=True)

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

    def _styled_san(self, record: MoveRecord) -> Text:
        """Create a styled Text object for a move in SAN notation."""
        text = Text(record.san)

        if record.is_checkmate:
            text.stylize(self.STYLE_CHECKMATE)
        elif record.is_check:
            text.stylize(self.STYLE_CHECK)
        elif record.is_promotion:
            text.stylize(self.STYLE_PROMOTION)
        elif record.is_castling:
            text.stylize(self.STYLE_CASTLING)
        elif record.captured_piece:
            text.stylize(self.STYLE_CAPTURE)
        elif record.piece.color == Color.WHITE:
            text.stylize(self.STYLE_WHITE_MOVE)
        else:
            text.stylize(self.STYLE_BLACK_MOVE)

        return text

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

    def print_move_history(self, game: ChessGame, last_n: Optional[int] = None):
        """Print move history as a styled Rich Table.

        Args:
            game: The game whose history to display.
            last_n: If set, only show the last N full moves.
        """
        history = game.move_history
        if not history:
            self.console.print(Text("No moves yet.", style=self.STYLE_DIM))
            return

        table = Table(
            title="Move History",
            show_header=True,
            header_style=self.STYLE_HEADER,
            border_style="dim",
            pad_edge=False,
            collapse_padding=True,
        )
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("White", min_width=8)
        table.add_column("Black", min_width=8)
        table.add_column("Notes", style="dim", max_width=30)

        # Pair moves into (white, black) rows
        pairs: list[tuple[MoveRecord, Optional[MoveRecord]]] = []
        for i in range(0, len(history), 2):
            white = history[i]
            black = history[i + 1] if i + 1 < len(history) else None
            pairs.append((white, black))

        if last_n is not None:
            pairs = pairs[-last_n:]

        for idx, (white, black) in enumerate(pairs):
            move_num = (len(pairs) - len(pairs) + idx + 1) if last_n else (idx + 1)
            # Adjust move number when slicing
            if last_n is not None:
                move_num = len(game.move_history) // 2 - len(pairs) + idx + 1

            white_text = self._styled_san(white)
            black_text = self._styled_san(black) if black else Text("...", style=self.STYLE_DIM)

            notes = self._move_notes(white, black)

            table.add_row(str(move_num), white_text, black_text, notes)

        self.console.print(table)

    def _move_notes(
        self, white: MoveRecord, black: Optional[MoveRecord]
    ) -> Text:
        """Build a notes column for a move pair."""
        parts: list[str] = []

        for record in [white, black]:
            if record is None:
                continue
            if record.captured_piece:
                sym = self.get_piece_symbol(
                    chess.Piece(record.captured_piece.piece_type.value,
                                record.captured_piece.color.value)
                )
                parts.append(f"x{sym}")
            if record.is_castling:
                parts.append("castle")
            if record.is_promotion:
                parts.append("promo")

        return Text(" ".join(parts), style=self.STYLE_DIM) if parts else Text("")

    def print_game_stats(self, game: ChessGame):
        """Print a statistics table for the game."""
        table = Table(
            title="Game Statistics",
            show_header=True,
            header_style=self.STYLE_HEADER,
            border_style="dim",
        )
        table.add_column("Stat", style="bold")
        table.add_column("White", justify="center")
        table.add_column("Black", justify="center")

        white_moves = [r for r in game.move_history if r.piece.color == Color.WHITE]
        black_moves = [r for r in game.move_history if r.piece.color == Color.BLACK]

        table.add_row(
            "Moves",
            str(len(white_moves)),
            str(len(black_moves)),
        )
        table.add_row(
            "Captures",
            str(sum(1 for r in white_moves if r.captured_piece)),
            str(sum(1 for r in black_moves if r.captured_piece)),
        )
        table.add_row(
            "Checks",
            str(sum(1 for r in white_moves if r.is_check)),
            str(sum(1 for r in black_moves if r.is_check)),
        )
        table.add_row(
            "Castled",
            "Yes" if any(r.is_castling for r in white_moves) else "No",
            "Yes" if any(r.is_castling for r in black_moves) else "No",
        )
        table.add_row(
            "Promotions",
            str(sum(1 for r in white_moves if r.is_promotion)),
            str(sum(1 for r in black_moves if r.is_promotion)),
        )

        # Material remaining
        white_pieces = game.get_pieces_by_color(Color.WHITE)
        black_pieces = game.get_pieces_by_color(Color.BLACK)

        white_mat = self._material_string(white_pieces)
        black_mat = self._material_string(black_pieces)

        table.add_row("Material", white_mat, black_mat)
        table.add_row(
            "Pieces left",
            str(len(white_pieces)),
            str(len(black_pieces)),
        )

        self.console.print(table)

    def _material_string(self, pieces: list) -> str:
        """Build a compact string showing remaining material."""
        symbols = []
        for pt in [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP,
                    PieceType.KNIGHT, PieceType.PAWN]:
            count = sum(1 for p in pieces if p.piece_type == pt)
            if count > 0:
                sym = self.get_piece_symbol(
                    chess.Piece(pt.value, pieces[0].color.value)
                )
                symbols.append(f"{sym}{count}" if count > 1 else sym)
        return " ".join(symbols)

    def print_post_game_summary(
        self,
        game: ChessGame,
        white_name: str = "White",
        black_name: str = "Black",
    ):
        """Print a full post-game summary panel with stats + move list."""
        result = game.result
        if result == GameResult.WHITE_WINS:
            result_text = Text(f"{white_name} wins!", style=Style(color="bright_green", bold=True))
        elif result == GameResult.BLACK_WINS:
            result_text = Text(f"{black_name} wins!", style=Style(color="bright_green", bold=True))
        elif result == GameResult.DRAW:
            result_text = Text("Draw", style=Style(color="yellow", bold=True))
        else:
            result_text = Text("Game in progress", style=self.STYLE_DIM)

        header = Text.assemble(
            ("Result: ", self.STYLE_HEADER),
            result_text,
            ("  |  ", self.STYLE_DIM),
            (f"Moves: {len(game.move_history)}", self.STYLE_DIM),
        )
        self.console.print(Panel(header, border_style="bright_blue"))

        self.print_game_stats(game)
        self.print_move_history(game)

    def print_teaching_advice(self, advice: "TeachingAdvice"):  # type: ignore[name-defined]
        """Print structured teaching advice from the coaching advisor.

        Args:
            advice: :class:`~chess_alive.llm.teaching.TeachingAdvice` returned
                by :class:`~chess_alive.llm.teaching.TeachingAdvisor`.
        """
        from ..llm.teaching import TeachingAdvice  # local import to avoid circular

        assert isinstance(advice, TeachingAdvice)

        self.console.print(
            Panel(
                f"[bold]{advice.position_assessment}[/bold]",
                title=f"[bold cyan]Teaching Coach — Move {advice.move_number} "
                f"({advice.player_color} to move)[/bold cyan]",
                border_style="cyan",
            )
        )

        if not advice.candidate_moves:
            return

        table = Table(
            title="Candidate Moves",
            show_header=True,
            header_style=Style(color="bright_cyan", bold=True),
            border_style="dim",
        )
        table.add_column("#", style="dim", width=3, justify="right")
        table.add_column("Move", style="bold cyan", min_width=6)
        table.add_column("Eval", style="yellow", min_width=8)
        table.add_column("Why this move", style="white", min_width=20)
        table.add_column("Likely opponent reply", style="red", min_width=20)
        table.add_column("Your follow-up goal", style="green", min_width=20)

        for i, candidate in enumerate(advice.candidate_moves, 1):
            table.add_row(
                str(i),
                candidate.san,
                candidate.evaluation,
                candidate.explanation,
                candidate.likely_response,
                candidate.follow_up_plan,
            )

        self.console.print(table)

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
            self.console.print(
                f"Captured: White: {white_captured or 'none'} | "
                f"Black: {black_captured or 'none'}"
            )

    def print_legal_moves(self, game: ChessGame):
        """Print all legal moves."""
        moves = [game.board.san(m) for m in game.get_legal_moves()]
        self.console.print(f"Legal moves ({len(moves)}): {', '.join(moves)}")

    def print_result(self, game: ChessGame):
        """Print the game result."""
        result = game.result

        if result == GameResult.WHITE_WINS:
            self.console.print("[bold]Result: White wins![/bold]")
        elif result == GameResult.BLACK_WINS:
            self.console.print("[bold]Result: Black wins![/bold]")
        elif result == GameResult.DRAW:
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
