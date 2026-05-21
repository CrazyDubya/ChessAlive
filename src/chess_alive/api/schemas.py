"""Pydantic schemas for the ChessAlive API."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PieceType(str, Enum):
    """Chess piece types."""
    PAWN = "PAWN"
    KNIGHT = "KNIGHT"
    BISHOP = "BISHOP"
    ROOK = "ROOK"
    QUEEN = "QUEEN"
    KING = "KING"


class Color(str, Enum):
    """Chess piece colors."""
    WHITE = "WHITE"
    BLACK = "BLACK"


class PiecePersonalitySchema(BaseModel):
    """Personality information for a piece."""
    name: str = Field(..., description="Piece's name (e.g., 'King Aldric')")
    archetype: str = Field(..., description="Character archetype")
    speaking_style: str = Field(..., description="How the piece speaks")
    backstory: Optional[str] = Field(None, description="Piece's background story")
    aggression: int = Field(5, ge=0, le=10, description="Aggression level (0-10)")
    caution: int = Field(5, ge=0, le=10, description="Caution level (0-10)")
    humor: int = Field(5, ge=0, le=10, description="Humor level (0-10)")
    eloquence: int = Field(5, ge=0, le=10, description="Eloquence level (0-10)")


class PieceSchema(BaseModel):
    """Information about a chess piece."""
    piece_type: PieceType = Field(..., alias="type")
    color: Color
    name: str = Field(..., description="Display name (e.g., 'King Aldric')")
    square: str = Field(..., description="Current square (e.g., 'e1')")
    is_captured: bool = Field(False, description="Whether piece has been captured")
    personality: Optional[PiecePersonalitySchema] = None

    class Config:
        populate_by_name = True


class PieceInfoResponse(BaseModel):
    """Response for piece info endpoint."""
    piece: PieceSchema


class CommentaryMessage(BaseModel):
    """A single piece of commentary from a piece."""
    piece: PieceSchema
    text: str = Field(..., description="The commentary text")
    commentary_type: str = Field(
        "move",
        description="Type: move, capture, check, reaction, game_start, game_end"
    )


class GameStateResponse(BaseModel):
    """Current game state."""
    fen: str = Field(..., description="FEN notation of current position")
    turn: Color = Field(..., description="Whose turn it is")
    legal_moves: list[str] = Field(..., description="List of legal moves in SAN")
    is_check: bool = Field(False, description="Whether current player is in check")
    is_checkmate: bool = Field(False, description="Whether game is checkmate")
    is_stalemate: bool = Field(False, description="Whether game is stalemate")
    is_game_over: bool = Field(False, description="Whether game has ended")
    result: Optional[str] = Field(None, description="Game result if over")
    fullmove_number: int = Field(1, description="Current move number")
    halfmove_clock: int = Field(0, description="Halfmove clock for 50-move rule")
    white_name: str = Field("Player 1", description="White player name")
    black_name: str = Field("Player 2", description="Black player name")


class MoveRequest(BaseModel):
    """Request to make a move."""
    move: str = Field(..., description="Move in SAN (e4) or UCI (e2e4) format")


class CapturedPiece(BaseModel):
    """Information about a captured piece."""
    piece_type: PieceType = Field(..., alias="type")
    color: Color
    name: str

    class Config:
        populate_by_name = True


class MoveResponse(BaseModel):
    """Response after making a move."""
    success: bool = Field(..., description="Whether move was legal and executed")
    fen: str = Field(..., description="New FEN after move")
    san: str = Field(..., description="Move in SAN format")
    captured_piece: Optional[CapturedPiece] = Field(None, description="Captured piece if any")
    is_check: bool = Field(False)
    is_checkmate: bool = Field(False)
    is_game_over: bool = Field(False)
    result: Optional[str] = None
    commentary: list[CommentaryMessage] = Field(
        default_factory=list,
        description="Commentary from pieces about this move"
    )
    legal_moves: list[str] = Field(..., description="Legal moves for next player")


class NewGameRequest(BaseModel):
    """Request to start a new game."""
    white_name: Optional[str] = Field("Player 1", description="White player name")
    black_name: Optional[str] = Field("Player 2", description="Black player name")
    white_style: Optional[str] = Field("balanced", description="White LLM style")
    black_style: Optional[str] = Field("balanced", description="Black LLM style")
    commentary_enabled: bool = Field(True, description="Enable piece commentary")
    commentary_frequency: str = Field(
        "key_moments",
        description="Commentary frequency: every_move, captures_only, key_moments"
    )


# WebSocket message types
class WSMessageType(str, Enum):
    """WebSocket message types."""
    # Client -> Server
    MOVE = "move"
    GET_STATE = "get_state"
    NEW_GAME = "new_game"
    GET_PIECE = "get_piece"

    # Server -> Client
    STATE_UPDATE = "state_update"
    MOVE_RESULT = "move_result"
    COMMENTARY = "commentary"
    ERROR = "error"
    GAME_OVER = "game_over"


class WebSocketMessage(BaseModel):
    """Generic WebSocket message wrapper."""
    type: WSMessageType
    data: Optional[dict] = None
    error: Optional[str] = None


class WSMoveRequest(BaseModel):
    """WebSocket move request."""
    move: str


class WSNewGameRequest(BaseModel):
    """WebSocket new game request."""
    white_name: Optional[str] = "Player 1"
    black_name: Optional[str] = "Player 2"
    white_style: Optional[str] = "balanced"
    black_style: Optional[str] = "balanced"
    commentary_enabled: bool = True
    commentary_frequency: str = "key_moments"


class WSMoveResult(BaseModel):
    """WebSocket move result."""
    fen: str
    san: str
    captured_piece: Optional[CapturedPiece] = None
    is_check: bool = False
    is_checkmate: bool = False
    is_game_over: bool = False
    result: Optional[str] = None
    commentary: list[CommentaryMessage] = []
    legal_moves: list[str] = []
    turn: Color = Color.WHITE


class WSError(BaseModel):
    """WebSocket error message."""
    message: str
    code: Optional[str] = None
