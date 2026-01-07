"""Game mode definitions."""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Type

from ..players.base import Player, PlayerType


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
        }
        return descriptions.get(self, "Unknown mode")

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
        return self.has_computer

    @property
    def requires_openrouter(self) -> bool:
        """Check if this mode requires OpenRouter API."""
        return self.has_llm

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
        }
        key = s.lower().strip().replace("-", "_").replace(" ", "_")
        if key not in mapping:
            raise ValueError(f"Unknown game mode: {s}")
        return mapping[key]

    @classmethod
    def list_all(cls) -> list[tuple["GameMode", str]]:
        """List all modes with descriptions."""
        return [(mode, mode.description) for mode in cls]
