"""Configuration management for ChessAlive."""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

from .credentials import load_api_key, load_saved_model, load_saved_provider

load_dotenv()


def _resolve_provider() -> str:
    """Resolve LLM provider from env var, then saved credentials, then default."""
    provider = os.getenv("CHESS_LLM_PROVIDER", "")
    if provider:
        return provider.lower()
    return load_saved_provider() or "openrouter"


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
    return load_saved_model() or ""


def _resolve_base_url() -> str:
    """Resolve base URL from env var."""
    return os.getenv("CHESS_LLM_BASE_URL", "")


# Default models per provider
PROVIDER_DEFAULTS: dict[str, dict[str, str]] = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "mistralai/devstral-2512:free",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:3b",
    },
}


@dataclass
class LLMConfig:
    """Configuration for LLM integration."""

    provider: str = field(default_factory=_resolve_provider)
    api_key: str = field(default_factory=_resolve_api_key)
    base_url: str = field(default_factory=_resolve_base_url)
    model: str = field(default_factory=_resolve_model)
    temperature: float = 0.7
    max_tokens: int = 300

    def __post_init__(self):
        """Fill in provider defaults for any empty fields."""
        defaults = PROVIDER_DEFAULTS.get(self.provider, PROVIDER_DEFAULTS["openrouter"])
        if not self.base_url:
            self.base_url = defaults["base_url"]
        if not self.model:
            self.model = defaults["model"]
        # Ollama doesn't need an API key — use a placeholder
        if self.provider == "ollama" and not self.api_key:
            self.api_key = "ollama"

    @property
    def is_configured(self) -> bool:
        """Check if LLM is properly configured."""
        return bool(self.api_key)

    @property
    def is_ollama(self) -> bool:
        """Check if using Ollama backend."""
        return self.provider == "ollama"

    @property
    def provider_display(self) -> str:
        """Human-readable provider name."""
        names = {
            "openrouter": "OpenRouter",
            "ollama": "Ollama (local)",
        }
        return names.get(self.provider, self.provider)


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
