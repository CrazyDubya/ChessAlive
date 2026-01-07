"""Core chess game logic wrapping python-chess."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Iterator
import chess
import chess.pgn
from datetime import datetime

from .piece import Piece, PieceType, Color, PiecePersonality, DEFAULT_PERSONALITIES


class GameResult(Enum):
    """Possible game outcomes."""

    IN_PROGRESS = auto()
    WHITE_WINS = auto()
    BLACK_WINS = auto()
    DRAW = auto()

    @property
    def is_finished(self) -> bool:
        return self != GameResult.IN_PROGRESS


class GameState(Enum):
    """Current state of the game."""

    WAITING = auto()  # Waiting to start
    PLAYING = auto()  # Game in progress
    PAUSED = auto()  # Game paused
    FINISHED = auto()  # Game over


@dataclass
class MoveRecord:
    """Record of a single move with metadata."""

    move: chess.Move
    san: str  # Standard Algebraic Notation
    piece: Piece
    captured_piece: Optional[Piece] = None
    is_check: bool = False
    is_checkmate: bool = False
    is_castling: bool = False
    is_en_passant: bool = False
    is_promotion: bool = False
    commentary: str = ""  # LLM-generated commentary
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ChessGame:
    """Main chess game class wrapping python-chess board."""

    board: chess.Board = field(default_factory=chess.Board)
    pieces: dict[chess.Square, Piece] = field(default_factory=dict)
    captured_white: list[Piece] = field(default_factory=list)
    captured_black: list[Piece] = field(default_factory=list)
    move_history: list[MoveRecord] = field(default_factory=list)
    state: GameState = GameState.WAITING
    _custom_personalities: dict[tuple[PieceType, Color], PiecePersonality] = field(
        default_factory=dict
    )

    def __post_init__(self):
        """Initialize pieces from the board."""
        if not self.pieces:
            self._init_pieces()

    def _init_pieces(self):
        """Initialize piece objects from current board state."""
        self.pieces.clear()
        for square in chess.SQUARES:
            chess_piece = self.board.piece_at(square)
            if chess_piece:
                piece_type = PieceType(chess_piece.piece_type)
                color = Color(chess_piece.color)
                personality = self._custom_personalities.get(
                    (piece_type, color),
                    DEFAULT_PERSONALITIES.get((piece_type, color), PiecePersonality()),
                )
                self.pieces[square] = Piece(
                    piece_type=piece_type,
                    color=color,
                    square=square,
                    personality=personality,
                )

    def set_personality(
        self, piece_type: PieceType, color: Color, personality: PiecePersonality
    ):
        """Set a custom personality for a piece type."""
        self._custom_personalities[(piece_type, color)] = personality
        # Update existing pieces
        for piece in self.pieces.values():
            if piece.piece_type == piece_type and piece.color == color:
                piece.personality = personality

    @property
    def current_turn(self) -> Color:
        """Get whose turn it is."""
        return Color.WHITE if self.board.turn else Color.BLACK

    @property
    def result(self) -> GameResult:
        """Get the current game result."""
        if not self.board.is_game_over():
            return GameResult.IN_PROGRESS

        outcome = self.board.outcome()
        if outcome is None:
            return GameResult.IN_PROGRESS

        if outcome.winner is None:
            return GameResult.DRAW
        elif outcome.winner:
            return GameResult.WHITE_WINS
        else:
            return GameResult.BLACK_WINS

    @property
    def is_check(self) -> bool:
        """Check if current player is in check."""
        return self.board.is_check()

    @property
    def is_checkmate(self) -> bool:
        """Check if current player is in checkmate."""
        return self.board.is_checkmate()

    @property
    def is_stalemate(self) -> bool:
        """Check if game is in stalemate."""
        return self.board.is_stalemate()

    @property
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.board.is_game_over()

    @property
    def fen(self) -> str:
        """Get the FEN string of current position."""
        return self.board.fen()

    @property
    def fullmove_number(self) -> int:
        """Get the current full move number."""
        return self.board.fullmove_number

    def get_legal_moves(self) -> list[chess.Move]:
        """Get all legal moves for the current player."""
        return list(self.board.legal_moves)

    def get_legal_moves_for_square(self, square: chess.Square) -> list[chess.Move]:
        """Get legal moves for a piece on a specific square."""
        return [m for m in self.board.legal_moves if m.from_square == square]

    def is_legal_move(self, move: chess.Move) -> bool:
        """Check if a move is legal."""
        return move in self.board.legal_moves

    def parse_move(self, move_str: str) -> Optional[chess.Move]:
        """Parse a move string (SAN or UCI) to a Move object."""
        try:
            # Try SAN first (e.g., "e4", "Nf3", "O-O")
            return self.board.parse_san(move_str)
        except ValueError:
            pass

        try:
            # Try UCI (e.g., "e2e4", "g1f3")
            return chess.Move.from_uci(move_str)
        except ValueError:
            pass

        return None

    def get_piece_at(self, square: chess.Square) -> Optional[Piece]:
        """Get the piece at a square."""
        return self.pieces.get(square)

    def get_piece_by_square_name(self, square_name: str) -> Optional[Piece]:
        """Get piece by square name (e.g., 'e4')."""
        try:
            square = chess.parse_square(square_name)
            return self.get_piece_at(square)
        except ValueError:
            return None

    def get_pieces_by_color(self, color: Color) -> list[Piece]:
        """Get all pieces of a given color."""
        return [p for p in self.pieces.values() if p.color == color]

    def get_pieces_by_type(self, piece_type: PieceType) -> list[Piece]:
        """Get all pieces of a given type."""
        return [p for p in self.pieces.values() if p.piece_type == piece_type]

    def make_move(self, move: chess.Move) -> Optional[MoveRecord]:
        """Make a move and return the move record."""
        if not self.is_legal_move(move):
            return None

        # Get the moving piece
        from_square = move.from_square
        to_square = move.to_square
        moving_piece = self.pieces.get(from_square)

        if moving_piece is None:
            return None

        # Check for capture
        captured_piece = self.pieces.get(to_square)

        # Check special moves before making the move
        is_en_passant_move = self.board.is_en_passant(move)
        is_castling_move = self.board.is_castling(move)

        # Handle en passant capture
        if is_en_passant_move:
            # The captured pawn is on a different square
            ep_square = to_square + (-8 if self.board.turn else 8)
            captured_piece = self.pieces.get(ep_square)
            if captured_piece:
                del self.pieces[ep_square]

        # Get SAN before making the move
        san = self.board.san(move)

        # Make the move on the board
        self.board.push(move)

        # Update piece tracking
        del self.pieces[from_square]
        moving_piece.square = to_square
        moving_piece.moves_made += 1

        # Handle promotion
        if move.promotion:
            moving_piece.piece_type = PieceType(move.promotion)

        # Handle castling - move the rook
        if is_castling_move:
            # Determine rook squares based on castling type
            if chess.square_file(to_square) == 6:  # Kingside
                rook_from = chess.square(7, chess.square_rank(from_square))
                rook_to = chess.square(5, chess.square_rank(from_square))
            else:  # Queenside
                rook_from = chess.square(0, chess.square_rank(from_square))
                rook_to = chess.square(3, chess.square_rank(from_square))

            if rook_from in self.pieces:
                rook = self.pieces[rook_from]
                del self.pieces[rook_from]
                rook.square = rook_to
                self.pieces[rook_to] = rook

        self.pieces[to_square] = moving_piece

        # Handle captured piece
        if captured_piece:
            captured_piece.is_captured = True
            captured_piece.square = None
            moving_piece.captures_made += 1
            if captured_piece.color == Color.WHITE:
                self.captured_white.append(captured_piece)
            else:
                self.captured_black.append(captured_piece)

        # Create move record
        record = MoveRecord(
            move=move,
            san=san,
            piece=moving_piece,
            captured_piece=captured_piece,
            is_check=self.board.is_check(),
            is_checkmate=self.board.is_checkmate(),
            is_castling=is_castling_move,
            is_en_passant=is_en_passant_move,
            is_promotion=move.promotion is not None,
        )

        self.move_history.append(record)
        return record

    def make_move_san(self, san: str) -> Optional[MoveRecord]:
        """Make a move from SAN notation."""
        move = self.parse_move(san)
        if move:
            return self.make_move(move)
        return None

    def make_move_uci(self, uci: str) -> Optional[MoveRecord]:
        """Make a move from UCI notation."""
        try:
            move = chess.Move.from_uci(uci)
            return self.make_move(move)
        except ValueError:
            return None

    def undo_move(self) -> Optional[MoveRecord]:
        """Undo the last move."""
        if not self.move_history:
            return None

        record = self.move_history.pop()
        self.board.pop()

        # Restore piece positions
        self._init_pieces()

        # Restore captured pieces lists
        if record.captured_piece:
            if record.captured_piece.color == Color.WHITE:
                if self.captured_white and self.captured_white[-1] == record.captured_piece:
                    self.captured_white.pop()
            else:
                if self.captured_black and self.captured_black[-1] == record.captured_piece:
                    self.captured_black.pop()

        return record

    def reset(self):
        """Reset the game to initial position."""
        self.board.reset()
        self._init_pieces()
        self.captured_white.clear()
        self.captured_black.clear()
        self.move_history.clear()
        self.state = GameState.WAITING

    def load_fen(self, fen: str) -> bool:
        """Load a position from FEN string."""
        try:
            self.board.set_fen(fen)
            self._init_pieces()
            self.captured_white.clear()
            self.captured_black.clear()
            self.move_history.clear()
            return True
        except ValueError:
            return False

    def to_pgn(self) -> str:
        """Export game to PGN format."""
        game = chess.pgn.Game()
        game.headers["Event"] = "ChessAlive Game"
        game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        game.headers["Result"] = self.board.result()

        node = game
        temp_board = chess.Board()
        for record in self.move_history:
            node = node.add_variation(record.move)
            if record.commentary:
                node.comment = record.commentary
            temp_board.push(record.move)

        return str(game)

    def get_active_pieces(self) -> Iterator[Piece]:
        """Iterate over all active (non-captured) pieces."""
        return iter(self.pieces.values())

    def get_pieces_that_can_move(self) -> list[Piece]:
        """Get pieces that have at least one legal move."""
        pieces = []
        for move in self.board.legal_moves:
            piece = self.pieces.get(move.from_square)
            if piece and piece not in pieces:
                pieces.append(piece)
        return pieces

    def get_attacked_squares(self, color: Color) -> set[chess.Square]:
        """Get all squares attacked by pieces of a color."""
        attacked = set()
        for square in chess.SQUARES:
            if self.board.is_attacked_by(color.value, square):
                attacked.add(square)
        return attacked

    def __repr__(self) -> str:
        return f"ChessGame(turn={self.current_turn.name_str}, move={self.fullmove_number})"
