"""Configuration management for ChessAlive."""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

from .credentials import load_api_key, load_saved_model

load_dotenv()


def _resolve_api_key() -> str:
    """Resolve API key from env var, then saved credentials."""
    key = os.getenv("OPENROUTER_API_KEY", "")
    if key:
        return key
    return load_api_key() or ""


def _resolve_model() -> str:
    """Resolve model from env var, then saved credentials, then default."""
    model = os.getenv("CHESS_LLM_MODEL", "")
    if model:
        return model
    return load_saved_model() or "mistralai/devstral-2512:free"


@dataclass
class LLMConfig:
    """Configuration for LLM integration via OpenRouter."""

    api_key: str = field(default_factory=_resolve_api_key)
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = field(default_factory=_resolve_model)
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
