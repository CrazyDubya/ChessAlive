"""FastAPI WebSocket server for 3D frontend integration."""

from __future__ import annotations

import asyncio
import json
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from ..core.game import ChessGame
from ..core.piece import PieceType, Color as CoreColor, DEFAULT_PERSONALITIES
from ..llm.commentary import CommentaryEngine
from ..llm.client import LLMClient
from ..config import get_config
from .schemas import (
    GameStateResponse,
    MoveRequest,
    MoveResponse,
    PieceInfoResponse,
    PieceSchema,
    PiecePersonalitySchema,
    CapturedPiece,
    CommentaryMessage,
    WebSocketMessage,
    WSMessageType,
    WSMoveResult,
    WSError,
)


class GameManager:
    """Manages active game instances and their connections."""

    def __init__(self):
        self._game: Optional[ChessGame] = None
        self._commentary_engine: Optional[CommentaryEngine] = None
        self._llm_client: Optional[LLMClient] = None
        self._commentary_enabled: bool = True
        self._connections: list[WebSocket] = []

    def create_game(
        self,
        white_name: str = "Player 1",
        black_name: str = "Player 2",
        commentary_enabled: bool = True,
        commentary_frequency: str = "key_moments",
    ) -> ChessGame:
        """Create a new game with optional commentary."""
        self._game = ChessGame()
        self._commentary_enabled = commentary_enabled

        # Set player names
        self._game.white_name = white_name
        self._game.black_name = black_name

        # Initialize commentary engine if enabled
        if commentary_enabled:
            config = get_config()
            if config.llm.is_configured:
                self._llm_client = LLMClient(config.llm)
                self._commentary_engine = CommentaryEngine(
                    self._llm_client,
                    commentary_frequency=commentary_frequency,
                )

        return self._game

    @property
    def game(self) -> ChessGame:
        """Get current game, creating one if needed."""
        if self._game is None:
            self.create_game()
        return self._game

    async def make_move(self, move_str: str) -> MoveResponse:
        """Make a move and return response with commentary."""
        game = self.game

        # Try to parse the move
        move = game.parse_move(move_str)
        if move is None or not game.is_legal_move(move):
            return MoveResponse(
                success=False,
                fen=game.fen,
                san="",
                legal_moves=[game.board.san(m) for m in game.get_legal_moves()],
            )

        # Get the SAN before making the move
        san = game.board.san(move)

        # Track captured piece
        captured_piece = None
        if game.board.is_capture(move):
            captured = game.board.piece_at(move.to_square)
            if captured:
                piece_type = PieceType(captured.piece_type)
                color = CoreColor(captured.color)
                personality = DEFAULT_PERSONALITIES.get((piece_type, color))
                captured_piece = CapturedPiece(
                    type=piece_type,
                    color=color,
                    name=personality.name if personality else f"{color.name_str} {piece_type.name_str}",
                )

        # Make the move
        move_record = game.make_move(move)

        # Get commentary if enabled (with timeout to avoid blocking)
        commentary = []
        print(f"DEBUG: Commentary enabled={self._commentary_enabled}, move_record={move_record}")

        if self._commentary_enabled and move_record:
            # Add basic instant commentary (no LLM needed)
            piece = move_record.piece
            piece_name = piece.display_name

            # Generate simple commentary based on move type
            comments = []

            if move_record.is_check:
                comments.append(f"{piece_name} delivers a check!")
            elif move_record.captured_piece:
                comments.append(f"{piece_name} captures {move_record.captured_piece.display_name}!")
            elif move_record.is_castling:
                comments.append(f"{piece_name} castles - smart move!")
            else:
                comments.append(f"{piece_name} moves to {move_record.san}")

            # Add instant commentary
            commentary.append(CommentaryMessage(
                piece=PieceSchema(
                    type=piece.piece_type.name_str.upper(),
                    color=piece.color.name_str.upper(),
                    name=piece_name,
                    square=piece.square_name,
                ),
                text=comments[0],
                commentary_type="move_description",
            ))

            print(f"DEBUG: Generated commentary: {comments[0]}")

            # Try to get LLM commentary in background (non-blocking)
            if self._commentary_engine:
                try:
                    # Try quick LLM commentary with short timeout
                    llm_commentaries = await asyncio.wait_for(
                        self._commentary_engine.generate_move_commentary(game, move_record),
                        timeout=2.0
                    )
                    for c in llm_commentaries:
                        commentary.append(CommentaryMessage(
                            piece=PieceSchema(
                                type=c.piece.piece_type,
                                color=c.piece.color,
                                name=c.piece.display_name,
                                square=c.piece.square_name,
                            ),
                            text=c.text,
                            commentary_type=c.commentary_type,
                        ))
                except (asyncio.TimeoutError, Exception):
                    # LLM commentary failed - we already have basic commentary
                    pass
        else:
            print(f"DEBUG: Commentary not generated (enabled={self._commentary_enabled}, has_record={move_record is not None})")

        return MoveResponse(
            success=True,
            fen=game.fen,
            san=san,
            captured_piece=captured_piece,
            is_check=game.is_check,
            is_checkmate=game.is_checkmate,
            is_game_over=game.is_game_over,
            result=game.result.name if game.is_game_over else None,
            commentary=commentary,
            legal_moves=[game.board.san(m) for m in game.get_legal_moves()],
        )

    def get_game_state(self) -> GameStateResponse:
        """Get current game state."""
        game = self.game
        # Extract fullmove_number and halfmove_clock from the board
        board = game.board
        fullmove_number = board.fullmove_number
        halfmove_clock = board.halfmove_clock

        return GameStateResponse(
            fen=game.fen,
            turn='WHITE' if game.current_turn == CoreColor.WHITE else 'BLACK',
            legal_moves=[game.board.san(m) for m in game.get_legal_moves()],
            is_check=game.is_check,
            is_checkmate=game.is_checkmate,
            is_stalemate=game.is_stalemate,
            is_game_over=game.is_game_over,
            result=game.result.name if game.is_game_over else None,
            fullmove_number=fullmove_number,
            halfmove_clock=halfmove_clock,
            white_name=game.white_name,
            black_name=game.black_name,
        )

    def get_piece_at_square(self, square: str) -> Optional[PieceSchema]:
        """Get piece info at a specific square."""
        import chess
        game = self.game

        try:
            sq = chess.parse_square(square)
            piece = game.board.piece_at(sq)
            if piece:
                piece_type = PieceType(piece.piece_type)
                color = CoreColor(piece.color)
                personality = DEFAULT_PERSONALITIES.get((piece_type, color))

                return PieceSchema(
                    type=piece_type,
                    color=color,
                    name=personality.name if personality else f"{color.name_str} {piece_type.name_str}",
                    square=square,
                    personality=PiecePersonalitySchema(
                        name=personality.name,
                        archetype=personality.archetype,
                        speaking_style=personality.speaking_style,
                        backstory=personality.backstory,
                        aggression=personality.aggression,
                        caution=personality.caution,
                        humor=personality.humor,
                        eloquence=personality.eloquence,
                    ) if personality else None,
                )
        except ValueError:
            pass

        return None

    async def broadcast(self, message: dict):
        """Broadcast message to all connected WebSocket clients."""
        for connection in self._connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    def add_connection(self, ws: WebSocket):
        """Add a WebSocket connection."""
        self._connections.append(ws)

    def remove_connection(self, ws: WebSocket):
        """Remove a WebSocket connection."""
        if ws in self._connections:
            self._connections.remove(ws)


# Global game manager
game_manager = GameManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("ChessAlive API server starting...")
    yield
    # Shutdown
    print("ChessAlive API server shutting down...")


app = FastAPI(
    title="ChessAlive API",
    description="API for ChessAlive 3D frontend",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# REST API Endpoints

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "ChessAlive API", "version": "0.1.0"}


@app.get("/game/state", response_model=GameStateResponse)
async def get_game_state():
    """Get current game state."""
    return game_manager.get_game_state()


@app.post("/game/move", response_model=MoveResponse)
async def make_move(request: MoveRequest):
    """Make a move."""
    result = await game_manager.make_move(request.move)
    return result


@app.post("/game/new")
async def new_game(
    white_name: str = "Player 1",
    black_name: str = "Player 2",
    commentary_enabled: bool = True,
    commentary_frequency: str = "key_moments",
):
    """Start a new game."""
    game_manager.create_game(
        white_name=white_name,
        black_name=black_name,
        commentary_enabled=commentary_enabled,
        commentary_frequency=commentary_frequency,
    )
    return {"message": "New game started", "state": game_manager.get_game_state()}


@app.get("/pieces/{square}", response_model=PieceInfoResponse)
async def get_piece_info(square: str):
    """Get information about the piece at a square."""
    piece = game_manager.get_piece_at_square(square)
    if piece is None:
        raise HTTPException(status_code=404, detail=f"No piece at square {square}")
    return PieceInfoResponse(piece=piece)


# WebSocket Endpoint

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time game updates."""
    await websocket.accept()
    game_manager.add_connection(websocket)

    try:
        # Send initial game state
        state = game_manager.get_game_state()
        await websocket.send_json({
            "type": WSMessageType.STATE_UPDATE.value,
            "data": state.model_dump(),
        })

        while True:
            # Receive and parse message
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                msg_data = message.get("data", {})
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": WSMessageType.ERROR.value,
                    "error": "Invalid JSON",
                })
                continue

            # Handle message types
            if msg_type == WSMessageType.MOVE.value:
                move_str = msg_data.get("move", "")
                result = await game_manager.make_move(move_str)

                response = {
                    "type": WSMessageType.MOVE_RESULT.value,
                    "data": result.model_dump(),
                }
                await websocket.send_json(response)

                # Broadcast to all connections
                await game_manager.broadcast(response)

            elif msg_type == WSMessageType.GET_STATE.value:
                state = game_manager.get_game_state()
                await websocket.send_json({
                    "type": WSMessageType.STATE_UPDATE.value,
                    "data": state.model_dump(),
                })

            elif msg_type == WSMessageType.NEW_GAME.value:
                game_manager.create_game(
                    white_name=msg_data.get("white_name", "Player 1"),
                    black_name=msg_data.get("black_name", "Player 2"),
                    commentary_enabled=msg_data.get("commentary_enabled", True),
                    commentary_frequency=msg_data.get("commentary_frequency", "key_moments"),
                )
                state = game_manager.get_game_state()
                await game_manager.broadcast({
                    "type": WSMessageType.STATE_UPDATE.value,
                    "data": state.model_dump(),
                })

            elif msg_type == WSMessageType.GET_PIECE.value:
                square = msg_data.get("square", "")
                piece = game_manager.get_piece_at_square(square)
                await websocket.send_json({
                    "type": "piece_info",
                    "data": piece.model_dump() if piece else None,
                })

            else:
                await websocket.send_json({
                    "type": WSMessageType.ERROR.value,
                    "error": f"Unknown message type: {msg_type}",
                })

    except WebSocketDisconnect:
        game_manager.remove_connection(websocket)
    except Exception as e:
        game_manager.remove_connection(websocket)
        raise


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the FastAPI server."""
    uvicorn.run(
        "chess_alive.api.server:app",
        host=host,
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    run_server()
