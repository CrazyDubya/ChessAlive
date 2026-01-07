"""Configuration management for ChessAlive."""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMConfig:
    """Configuration for LLM integration via OpenRouter."""

    api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = field(default_factory=lambda: os.getenv("CHESS_LLM_MODEL", "mistralai/devstral-2512:free"))
    temperature: float = 0.7
    max_tokens: int = 300

    @property
    def is_configured(self) -> bool:
        """Check if LLM is properly configured."""
        return bool(self.api_key)


@dataclass
class EngineConfig:
    """Configuration for chess engine (Stockfish)."""

    path: Optional[str] = field(default_factory=lambda: os.getenv("STOCKFISH_PATH"))
    depth: int = 15
    time_limit: float = 1.0  # seconds per move
    skill_level: int = 20  # 0-20, 20 is strongest
    threads: int = 1
    hash_size: int = 128  # MB

    @property
    def is_configured(self) -> bool:
        """Check if engine path is set."""
        return self.path is not None


@dataclass
class GameConfig:
    """Overall game configuration."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    engine: EngineConfig = field(default_factory=EngineConfig)

    # Commentary settings
    commentary_enabled: bool = True
    commentary_frequency: str = "every_move"  # "every_move", "captures_only", "key_moments"

    # Display settings
    show_evaluation: bool = True
    show_legal_moves: bool = False
    unicode_pieces: bool = True


def get_config() -> GameConfig:
    """Get the default game configuration."""
    return GameConfig()
