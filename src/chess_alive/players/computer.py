"""Computer player using Stockfish chess engine."""

import asyncio
from typing import Optional
import chess
import chess.engine

from .base import Player, PlayerType
from ..core.game import ChessGame
from ..core.piece import Color
from ..config import EngineConfig


class ComputerPlayer(Player):
    """Computer player powered by Stockfish chess engine."""

    def __init__(
        self,
        color: Color,
        name: Optional[str] = None,
        config: Optional[EngineConfig] = None,
    ):
        """
        Initialize a computer player.

        Args:
            color: The player's color
            name: Optional player name
            config: Engine configuration
        """
        super().__init__(color, name or "Stockfish")
        self.config = config or EngineConfig()
        self._engine: Optional[chess.engine.SimpleEngine] = None
        self._transport: Optional[chess.engine.Protocol] = None

    @property
    def player_type(self) -> PlayerType:
        return PlayerType.COMPUTER

    async def _ensure_engine(self):
        """Ensure the engine is running."""
        if self._engine is not None:
            return

        if not self.config.path:
            raise RuntimeError(
                "Stockfish path not configured. Set STOCKFISH_PATH environment variable "
                "or provide path in EngineConfig."
            )

        try:
            self._transport, self._engine = await chess.engine.popen_uci(
                self.config.path
            )

            # Configure engine
            await self._engine.configure({
                "Threads": self.config.threads,
                "Hash": self.config.hash_size,
                "Skill Level": self.config.skill_level,
            })
        except Exception as e:
            raise RuntimeError(f"Failed to start Stockfish: {e}")

    async def get_move(self, game: ChessGame) -> Optional[chess.Move]:
        """Get move from Stockfish."""
        if game.current_turn != self.color:
            return None

        await self._ensure_engine()

        try:
            # Get best move with time limit
            result = await self._engine.play(
                game.board,
                chess.engine.Limit(
                    time=self.config.time_limit,
                    depth=self.config.depth,
                ),
            )
            return result.move
        except chess.engine.EngineTerminatedError:
            self._engine = None
            return None

    async def analyze_position(
        self, game: ChessGame, depth: Optional[int] = None
    ) -> Optional[chess.engine.InfoDict]:
        """
        Analyze the current position.

        Returns evaluation info from the engine.
        """
        await self._ensure_engine()

        try:
            info = await self._engine.analyse(
                game.board,
                chess.engine.Limit(depth=depth or self.config.depth),
            )
            return info
        except chess.engine.EngineTerminatedError:
            self._engine = None
            return None

    async def get_evaluation(self, game: ChessGame) -> Optional[float]:
        """
        Get position evaluation in centipawns from White's perspective.

        Returns:
            Evaluation in centipawns (positive favors White)
        """
        info = await self.analyze_position(game)
        if info and "score" in info:
            score = info["score"].white()
            if score.is_mate():
                # Return large value for mate
                mate_in = score.mate()
                return 10000 if mate_in > 0 else -10000
            return score.score() / 100  # Convert centipawns to pawns

        return None

    async def on_game_start(self, game: ChessGame):
        """Start the engine when game begins."""
        await self._ensure_engine()

    async def on_game_end(self, game: ChessGame):
        """Clean up engine when game ends."""
        await self._cleanup()

    async def _cleanup(self):
        """Clean up engine resources."""
        if self._engine:
            await self._engine.quit()
            self._engine = None
            self._transport = None

    def set_skill_level(self, level: int):
        """Set engine skill level (0-20)."""
        self.config.skill_level = max(0, min(20, level))

    def set_time_limit(self, seconds: float):
        """Set time limit per move in seconds."""
        self.config.time_limit = max(0.1, seconds)

    def set_depth(self, depth: int):
        """Set search depth."""
        self.config.depth = max(1, min(30, depth))


class StockfishNotFoundError(Exception):
    """Raised when Stockfish executable is not found."""

    pass


async def find_stockfish() -> Optional[str]:
    """Try to find Stockfish executable on the system."""
    import shutil

    # Common names for stockfish executable
    names = ["stockfish", "stockfish.exe", "stockfish-ubuntu-x86-64", "stockfish_15"]

    for name in names:
        path = shutil.which(name)
        if path:
            return path

    # Common installation paths
    common_paths = [
        "/usr/bin/stockfish",
        "/usr/local/bin/stockfish",
        "/usr/games/stockfish",
        "/opt/stockfish/stockfish",
        "C:\\Program Files\\Stockfish\\stockfish.exe",
        "C:\\stockfish\\stockfish.exe",
    ]

    import os

    for path in common_paths:
        if os.path.isfile(path):
            return path

    return None
