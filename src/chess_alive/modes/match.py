"""Match orchestration - runs a complete chess game."""

from dataclasses import dataclass, field
from typing import Optional, Callable, Awaitable
from datetime import datetime

from .mode import GameMode
from ..core.game import ChessGame, GameState, GameResult, MoveRecord
from ..core.piece import Color
from ..players.base import Player, PlayerType
from ..players.human import HumanPlayer
from ..players.computer import ComputerPlayer
from ..players.llm_player import LLMPlayer
from ..llm.client import LLMClient
from ..llm.commentary import CommentaryEngine
from ..llm.teaching import TeachingAdvisor
from ..config import GameConfig


@dataclass
class MatchConfig:
    """Configuration for a match."""

    mode: GameMode = GameMode.PLAYER_VS_PLAYER
    white_name: str = "White"
    black_name: str = "Black"
    enable_commentary: bool = True
    commentary_frequency: str = "every_move"
    stockfish_depth: int = 15
    stockfish_time: float = 1.0
    stockfish_skill: int = 20
    llm_style_white: str = "balanced"
    llm_style_black: str = "balanced"
    max_moves: int = 500  # Prevent infinite games
    enable_teaching: bool = False  # LLM + Stockfish coaching before each human move


@dataclass
class MatchEvent:
    """An event that occurred during the match."""

    event_type: str  # "move", "commentary", "game_start", "game_end", "error"
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class Match:
    """Orchestrates a complete chess match between two players."""

    def __init__(
        self,
        config: MatchConfig,
        game_config: Optional[GameConfig] = None,
        on_event: Optional[Callable[[MatchEvent], Awaitable[None]]] = None,
    ):
        """
        Initialize a match.

        Args:
            config: Match configuration
            game_config: Overall game configuration
            on_event: Async callback for match events
        """
        self.config = config
        self.game_config = game_config or GameConfig()
        self.on_event = on_event

        self.game = ChessGame()
        self.white_player: Optional[Player] = None
        self.black_player: Optional[Player] = None
        self.commentary_engine: Optional[CommentaryEngine] = None
        self.teaching_advisor: Optional[TeachingAdvisor] = None
        self.events: list[MatchEvent] = []

        self._llm_client: Optional[LLMClient] = None
        self._running = False

    async def _emit_event(self, event_type: str, data: Optional[dict] = None):  # type: ignore[type-arg]
        """Emit an event."""
        event = MatchEvent(event_type=event_type, data=data or {})
        self.events.append(event)
        if self.on_event:
            await self.on_event(event)

    async def setup(
        self,
        human_input_handler: Optional[Callable[[ChessGame], Awaitable[str]]] = None,
    ):
        """
        Set up the match with appropriate players.

        Args:
            human_input_handler: Custom input handler for human players
        """
        mode = self.config.mode

        # Create LLM client if needed
        if mode.requires_openrouter:
            self._llm_client = LLMClient(self.game_config.llm)

        # Create white player
        self.white_player = await self._create_player(
            mode.white_player_type,
            Color.WHITE,
            self.config.white_name,
            human_input_handler,
            self.config.llm_style_white,
        )

        # Create black player
        self.black_player = await self._create_player(
            mode.black_player_type,
            Color.BLACK,
            self.config.black_name,
            human_input_handler,
            self.config.llm_style_black,
        )

        # Set up commentary engine if enabled
        if self.config.enable_commentary and self._llm_client:
            self.commentary_engine = CommentaryEngine(
                self._llm_client,
                self.config.commentary_frequency,
            )

        # Set up teaching advisor if enabled
        if (self.config.enable_teaching or self.config.mode == GameMode.TEACHING) and self._llm_client:
            self.teaching_advisor = TeachingAdvisor(
                self._llm_client,
                self.game_config.engine,
            )

    async def _create_player(
        self,
        player_type: PlayerType,
        color: Color,
        name: str,
        human_input_handler: Optional[Callable],
        llm_style: str,
    ) -> Player:
        """Create a player of the specified type."""
        if player_type == PlayerType.HUMAN:
            return HumanPlayer(color, name, human_input_handler)

        elif player_type == PlayerType.COMPUTER:
            from ..players.computer import find_stockfish

            engine_config = self.game_config.engine

            # Try to find Stockfish if path not configured
            if not engine_config.path:
                found_path = await find_stockfish()
                if found_path:
                    engine_config.path = found_path

            if not engine_config.path:
                raise RuntimeError(
                    "Stockfish not found. Please install Stockfish and set STOCKFISH_PATH."
                )

            engine_config.depth = self.config.stockfish_depth
            engine_config.time_limit = self.config.stockfish_time
            engine_config.skill_level = self.config.stockfish_skill

            return ComputerPlayer(color, name, engine_config)

        elif player_type == PlayerType.LLM:
            if not self._llm_client:
                raise RuntimeError("LLM client not available")

            player = LLMPlayer(color, name, self._llm_client, llm_style)
            return player

        raise ValueError(f"Unknown player type: {player_type}")

    def get_current_player(self) -> Optional[Player]:
        """Get the player whose turn it is."""
        if self.game.current_turn == Color.WHITE:
            return self.white_player
        return self.black_player

    async def play_move(self) -> Optional[MoveRecord]:
        """Play a single move from the current player."""
        if self.game.is_game_over:
            return None

        current_player = self.get_current_player()
        if not current_player:
            return None

        # Get move from player
        move = await current_player.get_move(self.game)
        if move is None:
            # Player resigned or error
            return None

        # Make the move
        record = self.game.make_move(move)
        if record is None:
            return None

        # Emit move event
        await self._emit_event("move", {
            "move": record.san,
            "piece": record.piece.display_name,
            "captured": record.captured_piece.display_name if record.captured_piece else None,
            "is_check": record.is_check,
            "is_checkmate": record.is_checkmate,
        })

        # Generate commentary
        if self.commentary_engine and self.config.enable_commentary:
            commentaries = await self.commentary_engine.generate_move_commentary(
                self.game, record
            )
            for commentary in commentaries:
                record.commentary = commentary.text  # Store on record
                await self._emit_event("commentary", {
                    "piece": commentary.piece.display_name,
                    "text": commentary.text,
                    "type": commentary.commentary_type,
                })

        # Notify opponent
        other_player = (
            self.black_player
            if current_player == self.white_player
            else self.white_player
        )
        if other_player:
            await other_player.on_opponent_move(self.game, move)

        return record

    async def run(self) -> GameResult:
        """
        Run the complete match until game over.

        Returns:
            The game result
        """
        if not self.white_player or not self.black_player:
            raise RuntimeError("Match not set up. Call setup() first.")

        self._running = True
        self.game.state = GameState.PLAYING

        # Notify players of game start
        await self.white_player.on_game_start(self.game)
        await self.black_player.on_game_start(self.game)

        await self._emit_event("game_start", {
            "mode": self.config.mode.name,
            "white": self.white_player.name,
            "black": self.black_player.name,
        })

        # Generate opening commentary
        if self.commentary_engine and self.config.enable_commentary:
            commentaries = await self.commentary_engine.generate_game_start_commentary(
                self.game
            )
            for commentary in commentaries:
                await self._emit_event("commentary", {
                    "piece": commentary.piece.display_name,
                    "text": commentary.text,
                    "type": "game_start",
                })

        # Main game loop
        move_count = 0
        while self._running and not self.game.is_game_over:
            if move_count >= self.config.max_moves:
                # Force draw after too many moves
                break

            record = await self.play_move()
            if record is None:
                # Player resigned or error
                break

            move_count += 1

        # Game over
        self.game.state = GameState.FINISHED
        result = self.game.result

        await self._emit_event("game_end", {
            "result": result.name,
            "moves": move_count,
            "pgn": self.game.to_pgn(),
        })

        # Generate ending commentary
        if self.commentary_engine and self.config.enable_commentary:
            commentaries = await self.commentary_engine.generate_game_end_commentary(
                self.game
            )
            for commentary in commentaries:
                await self._emit_event("commentary", {
                    "piece": commentary.piece.display_name,
                    "text": commentary.text,
                    "type": "game_end",
                })

        # Notify players
        await self.white_player.on_game_end(self.game)
        await self.black_player.on_game_end(self.game)

        # Cleanup
        await self._cleanup()

        return result

    def stop(self):
        """Stop the match."""
        self._running = False

    async def _cleanup(self):
        """Clean up resources."""
        if self.teaching_advisor:
            await self.teaching_advisor.close()
            self.teaching_advisor = None
        if self._llm_client:
            await self._llm_client.close()
            self._llm_client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._cleanup()
