"""Tests for secure credential storage."""

import json
import os
import stat
import platform
from pathlib import Path
from unittest.mock import patch

import pytest

from chess_alive.credentials import (
    save_api_key,
    load_api_key,
    load_saved_model,
    clear_api_key,
    has_saved_key,
    mask_key,
    _obfuscate,
    _deobfuscate,
    _get_config_dir,
    _get_credentials_path,
)


@pytest.fixture
def tmp_config_dir(tmp_path):
    """Use a temporary directory for credential storage during tests."""
    config_dir = tmp_path / "chess-alive"
    with patch("chess_alive.credentials._get_config_dir", return_value=config_dir):
        with patch(
            "chess_alive.credentials._get_credentials_path",
            return_value=config_dir / "credentials.json",
        ):
            yield config_dir


class TestObfuscation:
    """Test the obfuscation/deobfuscation round-trip."""

    def test_round_trip(self):
        """Obfuscate and deobfuscate returns original string."""
        original = "sk-or-v1-abc123def456"
        encoded = _obfuscate(original)
        decoded = _deobfuscate(encoded)
        assert decoded == original

    def test_not_plaintext(self):
        """Obfuscated value should not contain the original key."""
        original = "sk-or-v1-abc123def456"
        encoded = _obfuscate(original)
        assert original not in encoded

    def test_empty_string(self):
        """Round-trip on empty string works."""
        assert _deobfuscate(_obfuscate("")) == ""

    def test_unicode_key(self):
        """Round-trip with unicode characters."""
        original = "key-with-special-chars-!@#$%"
        assert _deobfuscate(_obfuscate(original)) == original


class TestSaveAndLoad:
    """Test saving and loading API keys."""

    def test_save_and_load(self, tmp_config_dir):
        """Save a key and load it back."""
        save_api_key("test-key-12345")
        assert load_api_key() == "test-key-12345"

    def test_save_with_model(self, tmp_config_dir):
        """Save a key with a model and load both."""
        save_api_key("test-key-12345", model="openai/gpt-4o-mini")
        assert load_api_key() == "test-key-12345"
        assert load_saved_model() == "openai/gpt-4o-mini"

    def test_save_without_model(self, tmp_config_dir):
        """Save a key without model returns None for model."""
        save_api_key("test-key-12345")
        assert load_saved_model() is None

    def test_load_nonexistent(self, tmp_config_dir):
        """Loading when no file exists returns None."""
        assert load_api_key() is None

    def test_load_model_nonexistent(self, tmp_config_dir):
        """Loading model when no file exists returns None."""
        assert load_saved_model() is None

    def test_save_creates_directory(self, tmp_config_dir):
        """Save creates the config directory if missing."""
        assert not tmp_config_dir.exists()
        save_api_key("test-key")
        assert tmp_config_dir.exists()

    def test_save_returns_path(self, tmp_config_dir):
        """Save returns the path to the credentials file."""
        path = save_api_key("test-key")
        assert path.exists()
        assert path.name == "credentials.json"

    def test_file_not_plaintext(self, tmp_config_dir):
        """The stored file should not contain the plaintext key."""
        save_api_key("my-secret-api-key-value")
        content = (tmp_config_dir / "credentials.json").read_text()
        assert "my-secret-api-key-value" not in content

    def test_file_is_valid_json(self, tmp_config_dir):
        """The stored file should be valid JSON."""
        save_api_key("test-key")
        content = (tmp_config_dir / "credentials.json").read_text()
        data = json.loads(content)
        assert "openrouter_api_key" in data

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix permissions only")
    def test_file_permissions(self, tmp_config_dir):
        """File should be chmod 600 on Unix."""
        path = save_api_key("test-key")
        mode = os.stat(path).st_mode
        assert mode & stat.S_IRWXG == 0  # No group permissions
        assert mode & stat.S_IRWXO == 0  # No other permissions
        assert mode & stat.S_IRUSR  # Owner can read
        assert mode & stat.S_IWUSR  # Owner can write

    def test_overwrite_key(self, tmp_config_dir):
        """Saving a new key overwrites the old one."""
        save_api_key("old-key")
        save_api_key("new-key")
        assert load_api_key() == "new-key"

    def test_corrupt_file(self, tmp_config_dir):
        """Loading from a corrupt file returns None gracefully."""
        tmp_config_dir.mkdir(parents=True, exist_ok=True)
        (tmp_config_dir / "credentials.json").write_text("not valid json{{{")
        assert load_api_key() is None


class TestClearKey:
    """Test clearing saved keys."""

    def test_clear_existing(self, tmp_config_dir):
        """Clearing an existing key removes it."""
        save_api_key("test-key")
        assert has_saved_key()
        assert clear_api_key() is True
        assert not has_saved_key()
        assert load_api_key() is None

    def test_clear_nonexistent(self, tmp_config_dir):
        """Clearing when no key exists returns False."""
        assert clear_api_key() is False


class TestHasSavedKey:
    """Test has_saved_key."""

    def test_no_key(self, tmp_config_dir):
        assert has_saved_key() is False

    def test_with_key(self, tmp_config_dir):
        save_api_key("test-key")
        assert has_saved_key() is True


class TestMaskKey:
    """Test key masking for display."""

    def test_long_key(self):
        """Long keys show first 4 and last 4 chars."""
        assert mask_key("sk-or-v1-abc123def456") == "sk-o*************f456"

    def test_short_key(self):
        """Short keys show first 2 chars and mask the rest."""
        assert mask_key("short") == "sh***"

    def test_minimum_key(self):
        """Very short keys still get masked."""
        assert mask_key("ab") == "ab"


class TestConfigDir:
    """Test config directory resolution."""

    def test_xdg_config_home(self):
        """XDG_CONFIG_HOME is respected."""
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/tmp/test-xdg"}):
            d = _get_config_dir()
            assert str(d) == "/tmp/test-xdg/chess-alive"

    def test_default_config(self):
        """Default falls back to ~/.config on Linux."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("chess_alive.credentials.platform.system", return_value="Linux"):
                d = _get_config_dir()
                assert d == Path.home() / ".config" / "chess-alive"
