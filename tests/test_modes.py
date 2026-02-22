"""Tests for game modes."""

import pytest

from chess_alive.modes.mode import GameMode
from chess_alive.players.base import PlayerType


class TestGameMode:
    """Tests for GameMode enum."""

    def test_all_modes_exist(self):
        """Test all expected modes exist."""
        modes = list(GameMode)
        assert len(modes) == 7

        assert GameMode.PLAYER_VS_PLAYER in modes
        assert GameMode.PLAYER_VS_COMPUTER in modes
        assert GameMode.COMPUTER_VS_COMPUTER in modes
        assert GameMode.PLAYER_VS_LLM in modes
        assert GameMode.LLM_VS_LLM in modes
        assert GameMode.LLM_VS_COMPUTER in modes
        assert GameMode.TEACHING in modes

    def test_mode_descriptions(self):
        """Test mode descriptions."""
        assert "human" in GameMode.PLAYER_VS_PLAYER.description.lower()
        assert "stockfish" in GameMode.PLAYER_VS_COMPUTER.description.lower()
        assert "llm" in GameMode.LLM_VS_LLM.description.lower()

    def test_player_types(self):
        """Test player type properties."""
        # PvP
        assert GameMode.PLAYER_VS_PLAYER.white_player_type == PlayerType.HUMAN
        assert GameMode.PLAYER_VS_PLAYER.black_player_type == PlayerType.HUMAN

        # PvC
        assert GameMode.PLAYER_VS_COMPUTER.white_player_type == PlayerType.HUMAN
        assert GameMode.PLAYER_VS_COMPUTER.black_player_type == PlayerType.COMPUTER

        # CvC
        assert GameMode.COMPUTER_VS_COMPUTER.white_player_type == PlayerType.COMPUTER
        assert GameMode.COMPUTER_VS_COMPUTER.black_player_type == PlayerType.COMPUTER

        # PvL
        assert GameMode.PLAYER_VS_LLM.white_player_type == PlayerType.HUMAN
        assert GameMode.PLAYER_VS_LLM.black_player_type == PlayerType.LLM

        # LvL
        assert GameMode.LLM_VS_LLM.white_player_type == PlayerType.LLM
        assert GameMode.LLM_VS_LLM.black_player_type == PlayerType.LLM

        # LvC
        assert GameMode.LLM_VS_COMPUTER.white_player_type == PlayerType.LLM
        assert GameMode.LLM_VS_COMPUTER.black_player_type == PlayerType.COMPUTER

    def test_has_human(self):
        """Test has_human property."""
        assert GameMode.PLAYER_VS_PLAYER.has_human
        assert GameMode.PLAYER_VS_COMPUTER.has_human
        assert GameMode.PLAYER_VS_LLM.has_human

        assert not GameMode.COMPUTER_VS_COMPUTER.has_human
        assert not GameMode.LLM_VS_LLM.has_human
        assert not GameMode.LLM_VS_COMPUTER.has_human

    def test_has_computer(self):
        """Test has_computer property."""
        assert GameMode.PLAYER_VS_COMPUTER.has_computer
        assert GameMode.COMPUTER_VS_COMPUTER.has_computer
        assert GameMode.LLM_VS_COMPUTER.has_computer

        assert not GameMode.PLAYER_VS_PLAYER.has_computer
        assert not GameMode.PLAYER_VS_LLM.has_computer
        assert not GameMode.LLM_VS_LLM.has_computer

    def test_has_llm(self):
        """Test has_llm property."""
        assert GameMode.PLAYER_VS_LLM.has_llm
        assert GameMode.LLM_VS_LLM.has_llm
        assert GameMode.LLM_VS_COMPUTER.has_llm

        assert not GameMode.PLAYER_VS_PLAYER.has_llm
        assert not GameMode.PLAYER_VS_COMPUTER.has_llm
        assert not GameMode.COMPUTER_VS_COMPUTER.has_llm

    def test_requires_stockfish(self):
        """Test requires_stockfish property."""
        assert GameMode.PLAYER_VS_COMPUTER.requires_stockfish
        assert GameMode.COMPUTER_VS_COMPUTER.requires_stockfish
        assert GameMode.LLM_VS_COMPUTER.requires_stockfish

        assert not GameMode.PLAYER_VS_PLAYER.requires_stockfish
        assert not GameMode.PLAYER_VS_LLM.requires_stockfish
        assert not GameMode.LLM_VS_LLM.requires_stockfish

    def test_requires_openrouter(self):
        """Test requires_openrouter property."""
        assert GameMode.PLAYER_VS_LLM.requires_openrouter
        assert GameMode.LLM_VS_LLM.requires_openrouter
        assert GameMode.LLM_VS_COMPUTER.requires_openrouter

        assert not GameMode.PLAYER_VS_PLAYER.requires_openrouter
        assert not GameMode.PLAYER_VS_COMPUTER.requires_openrouter
        assert not GameMode.COMPUTER_VS_COMPUTER.requires_openrouter

    def test_from_string(self):
        """Test parsing from string."""
        assert GameMode.from_string("pvp") == GameMode.PLAYER_VS_PLAYER
        assert GameMode.from_string("PVP") == GameMode.PLAYER_VS_PLAYER
        assert GameMode.from_string("player_vs_player") == GameMode.PLAYER_VS_PLAYER

        assert GameMode.from_string("pvc") == GameMode.PLAYER_VS_COMPUTER
        assert GameMode.from_string("player-vs-computer") == GameMode.PLAYER_VS_COMPUTER

        assert GameMode.from_string("cvc") == GameMode.COMPUTER_VS_COMPUTER
        assert GameMode.from_string("lvl") == GameMode.LLM_VS_LLM
        assert GameMode.from_string("lvc") == GameMode.LLM_VS_COMPUTER

    def test_from_string_invalid(self):
        """Test parsing invalid string."""
        with pytest.raises(ValueError, match="Unknown game mode"):
            GameMode.from_string("invalid_mode")

    def test_list_all(self):
        """Test listing all modes."""
        all_modes = GameMode.list_all()

        assert len(all_modes) == 7
        assert all(isinstance(m, tuple) for m in all_modes)
        assert all(isinstance(m[0], GameMode) for m in all_modes)
        assert all(isinstance(m[1], str) for m in all_modes)
