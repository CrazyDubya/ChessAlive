"""Tests for game module."""

import pytest
import chess

from chess_alive.core.game import (
    ChessGame,
    GameState,
    GameResult,
    MoveRecord,
)
from chess_alive.core.piece import PieceType, Color, PiecePersonality


class TestGameResult:
    """Tests for GameResult enum."""

    def test_is_finished(self):
        """Test is_finished property."""
        assert not GameResult.IN_PROGRESS.is_finished
        assert GameResult.WHITE_WINS.is_finished
        assert GameResult.BLACK_WINS.is_finished
        assert GameResult.DRAW.is_finished


class TestChessGame:
    """Tests for ChessGame class."""

    def test_initial_state(self):
        """Test initial game state."""
        game = ChessGame()

        assert game.current_turn == Color.WHITE
        assert game.fullmove_number == 1
        assert not game.is_check
        assert not game.is_checkmate
        assert not game.is_game_over
        assert game.result == GameResult.IN_PROGRESS
        assert game.state == GameState.WAITING

    def test_pieces_initialized(self):
        """Test that pieces are properly initialized."""
        game = ChessGame()

        # Should have 32 pieces
        assert len(game.pieces) == 32

        # Check specific pieces
        white_king = game.get_piece_by_square_name("e1")
        assert white_king is not None
        assert white_king.piece_type == PieceType.KING
        assert white_king.color == Color.WHITE

        black_queen = game.get_piece_by_square_name("d8")
        assert black_queen is not None
        assert black_queen.piece_type == PieceType.QUEEN
        assert black_queen.color == Color.BLACK

    def test_get_legal_moves(self):
        """Test getting legal moves."""
        game = ChessGame()
        moves = game.get_legal_moves()

        # Initial position has 20 legal moves
        assert len(moves) == 20

    def test_get_legal_moves_for_square(self):
        """Test getting legal moves for a specific square."""
        game = ChessGame()

        # e2 pawn can move to e3 or e4
        moves = game.get_legal_moves_for_square(chess.E2)
        assert len(moves) == 2

        # King has no moves initially
        moves = game.get_legal_moves_for_square(chess.E1)
        assert len(moves) == 0

    def test_parse_move_san(self):
        """Test parsing SAN moves."""
        game = ChessGame()

        move = game.parse_move("e4")
        assert move is not None
        assert move.from_square == chess.E2
        assert move.to_square == chess.E4

        move = game.parse_move("Nf3")
        assert move is not None
        assert move.from_square == chess.G1
        assert move.to_square == chess.F3

    def test_parse_move_uci(self):
        """Test parsing UCI moves."""
        game = ChessGame()

        move = game.parse_move("e2e4")
        assert move is not None
        assert move.from_square == chess.E2
        assert move.to_square == chess.E4

    def test_parse_invalid_move(self):
        """Test parsing invalid moves."""
        game = ChessGame()

        move = game.parse_move("xyz")
        assert move is None

        move = game.parse_move("e5")  # Illegal from starting position
        assert move is None

    def test_is_legal_move(self):
        """Test move legality checking."""
        game = ChessGame()

        legal_move = chess.Move.from_uci("e2e4")
        assert game.is_legal_move(legal_move)

        illegal_move = chess.Move.from_uci("e2e5")
        assert not game.is_legal_move(illegal_move)

    def test_make_move(self):
        """Test making a move."""
        game = ChessGame()

        move = chess.Move.from_uci("e2e4")
        record = game.make_move(move)

        assert record is not None
        assert record.san == "e4"
        assert record.piece.piece_type == PieceType.PAWN
        assert game.current_turn == Color.BLACK
        assert len(game.move_history) == 1

    def test_make_move_san(self):
        """Test making a move from SAN."""
        game = ChessGame()

        record = game.make_move_san("e4")
        assert record is not None
        assert record.san == "e4"

    def test_make_move_capture(self):
        """Test capture move."""
        game = ChessGame()

        # Set up a capture scenario
        game.make_move_san("e4")
        game.make_move_san("d5")
        record = game.make_move_san("exd5")

        assert record is not None
        assert record.captured_piece is not None
        assert record.captured_piece.piece_type == PieceType.PAWN
        assert record.captured_piece.color == Color.BLACK
        assert len(game.captured_black) == 1

    def test_make_illegal_move(self):
        """Test making an illegal move returns None."""
        game = ChessGame()

        illegal_move = chess.Move.from_uci("e2e5")
        record = game.make_move(illegal_move)
        assert record is None

    def test_undo_move(self):
        """Test undoing a move."""
        game = ChessGame()

        game.make_move_san("e4")
        assert game.current_turn == Color.BLACK

        record = game.undo_move()
        assert record is not None
        assert game.current_turn == Color.WHITE
        assert len(game.move_history) == 0

    def test_reset(self):
        """Test resetting the game."""
        game = ChessGame()

        game.make_move_san("e4")
        game.make_move_san("e5")
        game.reset()

        assert game.current_turn == Color.WHITE
        assert game.fullmove_number == 1
        assert len(game.move_history) == 0
        assert len(game.captured_white) == 0
        assert len(game.captured_black) == 0

    def test_load_fen(self):
        """Test loading a position from FEN."""
        game = ChessGame()

        # Position after 1. e4
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        result = game.load_fen(fen)

        assert result is True
        assert game.current_turn == Color.BLACK
        assert game.get_piece_by_square_name("e4") is not None

    def test_load_invalid_fen(self):
        """Test loading invalid FEN."""
        game = ChessGame()

        result = game.load_fen("invalid fen string")
        assert result is False

    def test_fen_property(self):
        """Test FEN property."""
        game = ChessGame()
        starting_fen = game.fen
        assert "rnbqkbnr" in starting_fen

    def test_check_detection(self):
        """Test check detection."""
        game = ChessGame()

        # Scholar's mate setup (not complete)
        game.make_move_san("e4")
        game.make_move_san("e5")
        game.make_move_san("Bc4")
        game.make_move_san("Nc6")
        game.make_move_san("Qh5")
        game.make_move_san("Nf6")
        game.make_move_san("Qxf7")

        assert game.is_checkmate
        assert game.is_game_over
        assert game.result == GameResult.WHITE_WINS

    def test_get_pieces_by_color(self):
        """Test getting pieces by color."""
        game = ChessGame()

        white_pieces = game.get_pieces_by_color(Color.WHITE)
        black_pieces = game.get_pieces_by_color(Color.BLACK)

        assert len(white_pieces) == 16
        assert len(black_pieces) == 16

    def test_get_pieces_by_type(self):
        """Test getting pieces by type."""
        game = ChessGame()

        pawns = game.get_pieces_by_type(PieceType.PAWN)
        knights = game.get_pieces_by_type(PieceType.KNIGHT)
        kings = game.get_pieces_by_type(PieceType.KING)

        assert len(pawns) == 16
        assert len(knights) == 4
        assert len(kings) == 2

    def test_set_personality(self):
        """Test setting custom personality."""
        game = ChessGame()

        custom_personality = PiecePersonality(
            name="Custom King",
            aggression=10,
        )
        game.set_personality(PieceType.KING, Color.WHITE, custom_personality)

        king = game.get_piece_by_square_name("e1")
        assert king.personality.name == "Custom King"
        assert king.personality.aggression == 10

    def test_to_pgn(self):
        """Test PGN export."""
        game = ChessGame()

        game.make_move_san("e4")
        game.make_move_san("e5")
        game.make_move_san("Nf3")

        pgn = game.to_pgn()
        assert "1. e4 e5 2. Nf3" in pgn

    def test_castling(self):
        """Test castling moves."""
        game = ChessGame()

        # Set up for kingside castling
        game.make_move_san("e4")
        game.make_move_san("e5")
        game.make_move_san("Nf3")
        game.make_move_san("Nc6")
        game.make_move_san("Bc4")
        game.make_move_san("Bc5")
        game.make_move_san("O-O")

        # King should be on g1
        king = game.get_piece_by_square_name("g1")
        assert king is not None
        assert king.piece_type == PieceType.KING

        # Rook should be on f1
        rook = game.get_piece_by_square_name("f1")
        assert rook is not None
        assert rook.piece_type == PieceType.ROOK

    def test_en_passant(self):
        """Test en passant capture."""
        game = ChessGame()

        # Set up en passant
        game.make_move_san("e4")
        game.make_move_san("a6")
        game.make_move_san("e5")
        game.make_move_san("d5")  # Pawn advances two squares
        record = game.make_move_san("exd6")  # En passant

        assert record is not None
        assert record.captured_piece is not None
        assert record.captured_piece.piece_type == PieceType.PAWN

    def test_promotion(self):
        """Test pawn promotion."""
        game = ChessGame()

        # Set up promotion scenario
        fen = "8/P7/8/8/8/8/8/4K2k w - - 0 1"
        game.load_fen(fen)

        record = game.make_move_san("a8=Q")
        assert record is not None
        assert record.is_promotion

        # Check the promoted piece
        queen = game.get_piece_by_square_name("a8")
        assert queen is not None
        assert queen.piece_type == PieceType.QUEEN


class TestMoveRecord:
    """Tests for MoveRecord class."""

    def test_move_record_creation(self):
        """Test creating a move record."""
        game = ChessGame()
        record = game.make_move_san("e4")

        assert record.san == "e4"
        assert record.piece.piece_type == PieceType.PAWN
        assert record.captured_piece is None
        assert not record.is_check
        assert not record.is_checkmate
        assert record.commentary == ""
