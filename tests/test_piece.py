"""Tests for piece module."""

import pytest
import chess

from chess_alive.core.piece import (
    Piece,
    PieceType,
    Color,
    PiecePersonality,
    DEFAULT_PERSONALITIES,
)


class TestPieceType:
    """Tests for PieceType enum."""

    def test_piece_type_values(self):
        """Test piece type values match python-chess."""
        assert PieceType.PAWN.value == chess.PAWN
        assert PieceType.KNIGHT.value == chess.KNIGHT
        assert PieceType.BISHOP.value == chess.BISHOP
        assert PieceType.ROOK.value == chess.ROOK
        assert PieceType.QUEEN.value == chess.QUEEN
        assert PieceType.KING.value == chess.KING

    def test_piece_type_symbol(self):
        """Test piece type symbols."""
        assert PieceType.KING.symbol == "K"
        assert PieceType.QUEEN.symbol == "Q"
        assert PieceType.PAWN.symbol == "P"

    def test_piece_type_name_str(self):
        """Test piece type name strings."""
        assert PieceType.KING.name_str == "King"
        assert PieceType.KNIGHT.name_str == "Knight"
        assert PieceType.PAWN.name_str == "Pawn"


class TestColor:
    """Tests for Color enum."""

    def test_color_values(self):
        """Test color values match python-chess."""
        assert Color.WHITE.value == chess.WHITE
        assert Color.BLACK.value == chess.BLACK

    def test_color_name_str(self):
        """Test color name strings."""
        assert Color.WHITE.name_str == "White"
        assert Color.BLACK.name_str == "Black"

    def test_color_opposite(self):
        """Test opposite color."""
        assert Color.WHITE.opposite == Color.BLACK
        assert Color.BLACK.opposite == Color.WHITE


class TestPiecePersonality:
    """Tests for PiecePersonality."""

    def test_default_personality(self):
        """Test default personality values."""
        personality = PiecePersonality()
        assert personality.name == ""
        assert personality.aggression == 5
        assert personality.caution == 5

    def test_custom_personality(self):
        """Test custom personality."""
        personality = PiecePersonality(
            name="Test Knight",
            archetype="brave warrior",
            speaking_style="bold",
            aggression=8,
            caution=2,
        )
        assert personality.name == "Test Knight"
        assert personality.aggression == 8

    def test_personality_to_prompt_context(self):
        """Test personality prompt context generation."""
        personality = PiecePersonality(
            name="Sir Test",
            archetype="tester",
            aggression=8,
            humor=8,
        )
        context = personality.to_prompt_context()
        assert "Sir Test" in context
        assert "tester" in context
        assert "aggressive" in context
        assert "jokes" in context

    def test_default_personalities_exist(self):
        """Test that default personalities are defined for all pieces."""
        for piece_type in PieceType:
            for color in Color:
                key = (piece_type, color)
                assert key in DEFAULT_PERSONALITIES


class TestPiece:
    """Tests for Piece class."""

    def test_piece_creation(self):
        """Test basic piece creation."""
        piece = Piece(
            piece_type=PieceType.KNIGHT,
            color=Color.WHITE,
            square=chess.E4,
        )
        assert piece.piece_type == PieceType.KNIGHT
        assert piece.color == Color.WHITE
        assert piece.square == chess.E4
        assert not piece.is_captured

    def test_piece_from_chess_piece(self):
        """Test creating piece from python-chess piece."""
        chess_piece = chess.Piece(chess.QUEEN, chess.BLACK)
        piece = Piece.from_chess_piece(chess_piece, chess.D8)

        assert piece.piece_type == PieceType.QUEEN
        assert piece.color == Color.BLACK
        assert piece.square == chess.D8
        # Should have default personality
        assert piece.personality.name != ""

    def test_piece_square_name(self):
        """Test square name property."""
        piece = Piece(PieceType.ROOK, Color.WHITE, chess.A1)
        assert piece.square_name == "a1"

        piece.square = chess.H8
        assert piece.square_name == "h8"

        piece.square = None
        assert piece.square_name == "captured"

    def test_piece_display_name(self):
        """Test display name uses personality name."""
        piece = Piece(
            PieceType.KING,
            Color.WHITE,
            personality=PiecePersonality(name="King Arthur"),
        )
        assert piece.display_name == "King Arthur"

    def test_piece_display_name_fallback(self):
        """Test display name fallback to piece type."""
        piece = Piece(
            PieceType.PAWN,
            Color.BLACK,
            personality=PiecePersonality(),  # No name
        )
        assert piece.display_name == "Black Pawn"

    def test_piece_unicode_symbol(self):
        """Test Unicode symbols."""
        white_king = Piece(PieceType.KING, Color.WHITE)
        black_queen = Piece(PieceType.QUEEN, Color.BLACK)

        assert white_king.symbol == ""
        assert black_queen.symbol == ""

    def test_piece_moves_tracking(self):
        """Test moves and captures tracking."""
        piece = Piece(PieceType.ROOK, Color.WHITE)
        assert piece.moves_made == 0
        assert piece.captures_made == 0

        piece.moves_made += 1
        piece.captures_made += 1

        assert piece.moves_made == 1
        assert piece.captures_made == 1
