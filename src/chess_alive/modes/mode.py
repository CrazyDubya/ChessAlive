"""Game mode definitions."""

from dataclasses import dataclass
from enum import Enum, auto

from ..players.base import PlayerType


@dataclass
class ModeConfig:
    """Per-mode default configuration.

    Each GameMode carries sensible defaults for commentary, engine, and LLM
    settings so the UI only has to override what the user explicitly changes.
    """

    commentary_frequency: str = "every_move"
    stockfish_depth: int = 15
    stockfish_time: float = 1.0
    stockfish_skill: int = 20
    llm_style_white: str = "balanced"
    llm_style_black: str = "balanced"
    max_moves: int = 500


# Tuned defaults per mode
_MODE_DEFAULTS: dict[str, ModeConfig] = {
    "PLAYER_VS_PLAYER": ModeConfig(
        commentary_frequency="key_moments",
        max_moves=500,
    ),
    "PLAYER_VS_COMPUTER": ModeConfig(
        commentary_frequency="key_moments",
        stockfish_skill=15,
        stockfish_depth=15,
    ),
    "COMPUTER_VS_COMPUTER": ModeConfig(
        commentary_frequency="captures_only",
        stockfish_skill=20,
        stockfish_depth=20,
        stockfish_time=0.5,
        max_moves=300,
    ),
    "PLAYER_VS_LLM": ModeConfig(
        commentary_frequency="every_move",
        llm_style_black="balanced",
    ),
    "LLM_VS_LLM": ModeConfig(
        commentary_frequency="key_moments",
        llm_style_white="aggressive",
        llm_style_black="defensive",
        max_moves=200,
    ),
    "LLM_VS_COMPUTER": ModeConfig(
        commentary_frequency="key_moments",
        llm_style_white="balanced",
        stockfish_skill=15,
    ),
    "TEACHING": ModeConfig(
        commentary_frequency="key_moments",
        stockfish_skill=15,
        stockfish_depth=15,
        max_moves=500,
    ),
}


class GameMode(Enum):
    """Available game modes."""

    # Player vs Player - Two humans
    PLAYER_VS_PLAYER = auto()

    # Player vs Computer - Human vs Stockfish
    PLAYER_VS_COMPUTER = auto()

    # Computer vs Computer - Stockfish vs Stockfish
    COMPUTER_VS_COMPUTER = auto()

    # Player vs LLM - Human vs LLM-controlled player
    PLAYER_VS_LLM = auto()

    # LLM vs LLM - Two LLMs playing against each other
    LLM_VS_LLM = auto()

    # LLM vs Computer - LLM vs Stockfish
    LLM_VS_COMPUTER = auto()

    # Teaching - Human plays vs Stockfish with LLM coaching before each move
    TEACHING = auto()

    @property
    def description(self) -> str:
        """Get a human-readable description."""
        descriptions = {
            GameMode.PLAYER_VS_PLAYER: "Two human players",
            GameMode.PLAYER_VS_COMPUTER: "Human vs Stockfish chess engine",
            GameMode.COMPUTER_VS_COMPUTER: "Stockfish vs Stockfish",
            GameMode.PLAYER_VS_LLM: "Human vs LLM-controlled player",
            GameMode.LLM_VS_LLM: "LLM vs LLM",
            GameMode.LLM_VS_COMPUTER: "LLM vs Stockfish chess engine",
            GameMode.TEACHING: "Teaching mode — Human vs Stockfish with LLM coaching",
        }
        return descriptions.get(self, "Unknown mode")

    @property
    def defaults(self) -> ModeConfig:
        """Get sensible default configuration for this mode."""
        return _MODE_DEFAULTS.get(self.name, ModeConfig())

    @property
    def white_player_type(self) -> PlayerType:
        """Get the type of the white player."""
        mapping = {
            GameMode.PLAYER_VS_PLAYER: PlayerType.HUMAN,
            GameMode.PLAYER_VS_COMPUTER: PlayerType.HUMAN,
            GameMode.COMPUTER_VS_COMPUTER: PlayerType.COMPUTER,
            GameMode.PLAYER_VS_LLM: PlayerType.HUMAN,
            GameMode.LLM_VS_LLM: PlayerType.LLM,
            GameMode.LLM_VS_COMPUTER: PlayerType.LLM,
            GameMode.TEACHING: PlayerType.HUMAN,
        }
        return mapping[self]

    @property
    def black_player_type(self) -> PlayerType:
        """Get the type of the black player."""
        mapping = {
            GameMode.PLAYER_VS_PLAYER: PlayerType.HUMAN,
            GameMode.PLAYER_VS_COMPUTER: PlayerType.COMPUTER,
            GameMode.COMPUTER_VS_COMPUTER: PlayerType.COMPUTER,
            GameMode.PLAYER_VS_LLM: PlayerType.LLM,
            GameMode.LLM_VS_LLM: PlayerType.LLM,
            GameMode.LLM_VS_COMPUTER: PlayerType.COMPUTER,
            GameMode.TEACHING: PlayerType.COMPUTER,
        }
        return mapping[self]

    @property
    def has_human(self) -> bool:
        """Check if this mode includes a human player."""
        return (
            self.white_player_type == PlayerType.HUMAN
            or self.black_player_type == PlayerType.HUMAN
        )

    @property
    def has_computer(self) -> bool:
        """Check if this mode includes a computer player."""
        return (
            self.white_player_type == PlayerType.COMPUTER
            or self.black_player_type == PlayerType.COMPUTER
        )

    @property
    def has_llm(self) -> bool:
        """Check if this mode includes an LLM player."""
        return (
            self.white_player_type == PlayerType.LLM
            or self.black_player_type == PlayerType.LLM
        )

    @property
    def requires_stockfish(self) -> bool:
        """Check if this mode requires Stockfish."""
        return self.has_computer or self == GameMode.TEACHING

    @property
    def requires_openrouter(self) -> bool:
        """Check if this mode requires OpenRouter API."""
        return self.has_llm or self == GameMode.TEACHING

    @classmethod
    def from_string(cls, s: str) -> "GameMode":
        """Parse game mode from string."""
        mapping = {
            "pvp": cls.PLAYER_VS_PLAYER,
            "player_vs_player": cls.PLAYER_VS_PLAYER,
            "pvc": cls.PLAYER_VS_COMPUTER,
            "player_vs_computer": cls.PLAYER_VS_COMPUTER,
            "player_vs_comp": cls.PLAYER_VS_COMPUTER,
            "cvc": cls.COMPUTER_VS_COMPUTER,
            "computer_vs_computer": cls.COMPUTER_VS_COMPUTER,
            "comp_vs_comp": cls.COMPUTER_VS_COMPUTER,
            "pvl": cls.PLAYER_VS_LLM,
            "player_vs_llm": cls.PLAYER_VS_LLM,
            "lvl": cls.LLM_VS_LLM,
            "llm_vs_llm": cls.LLM_VS_LLM,
            "lvc": cls.LLM_VS_COMPUTER,
            "llm_vs_computer": cls.LLM_VS_COMPUTER,
            "llm_vs_comp": cls.LLM_VS_COMPUTER,
            "teaching": cls.TEACHING,
            "teach": cls.TEACHING,
        }
        key = s.lower().strip().replace("-", "_").replace(" ", "_")
        if key not in mapping:
            raise ValueError(f"Unknown game mode: {s}")
        return mapping[key]

    @classmethod
    def list_all(cls) -> list[tuple["GameMode", str]]:
        """List all modes with descriptions."""
        return [(mode, mode.description) for mode in cls]
