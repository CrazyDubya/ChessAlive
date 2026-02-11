"""Secure credential storage for ChessAlive API keys."""

import base64
import getpass
import hashlib
import json
import os
import platform
import stat
from pathlib import Path
from typing import Optional


def _get_config_dir() -> Path:
    """Get the platform-appropriate config directory."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        base = Path(xdg)
    elif platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif platform.system() == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    return base / "chess-alive"


def _get_credentials_path() -> Path:
    """Get the path to the credentials file."""
    return _get_config_dir() / "credentials.json"


def _derive_key() -> bytes:
    """Derive a machine-local key for obfuscating stored credentials.

    This is NOT cryptographic security — it prevents the API key from
    being stored as plaintext so it won't show up in casual file browsing
    or grep. The real security comes from file permissions (chmod 600).
    """
    parts = [
        getpass.getuser(),
        platform.node(),
        str(Path.home()),
    ]
    return hashlib.sha256("|".join(parts).encode()).digest()


def _obfuscate(plaintext: str) -> str:
    """XOR-obfuscate a string with the machine key, return base64."""
    key = _derive_key()
    data = plaintext.encode("utf-8")
    obfuscated = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.b64encode(obfuscated).decode("ascii")


def _deobfuscate(encoded: str) -> str:
    """Reverse the obfuscation."""
    key = _derive_key()
    data = base64.b64decode(encoded)
    plaintext = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return plaintext.decode("utf-8")


def _secure_file(path: Path) -> None:
    """Set file permissions to owner-only (chmod 600)."""
    if platform.system() != "Windows":
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def save_api_key(
    api_key: str,
    model: Optional[str] = None,
    provider: Optional[str] = None,
) -> Path:
    """Save an API key and provider config securely.

    The key is obfuscated and stored in a file with restricted permissions.

    Args:
        api_key: The API key to save (empty string for Ollama).
        model: Optional model name to save alongside the key.
        provider: LLM provider ("openrouter" or "ollama").

    Returns:
        Path to the credentials file.
    """
    config_dir = _get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    cred_path = _get_credentials_path()

    data: dict[str, str] = {}
    if api_key:
        data["openrouter_api_key"] = _obfuscate(api_key)
    if model:
        data["model"] = model
    if provider:
        data["provider"] = provider

    cred_path.write_text(json.dumps(data, indent=2))
    _secure_file(cred_path)

    return cred_path


def load_api_key() -> Optional[str]:
    """Load a saved OpenRouter API key.

    Returns:
        The API key string, or None if not saved.
    """
    cred_path = _get_credentials_path()
    if not cred_path.exists():
        return None

    try:
        data = json.loads(cred_path.read_text())
        encoded = data.get("openrouter_api_key")
        if not encoded:
            return None
        return _deobfuscate(encoded)
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def load_saved_model() -> Optional[str]:
    """Load a saved model name.

    Returns:
        The model string, or None if not saved.
    """
    cred_path = _get_credentials_path()
    if not cred_path.exists():
        return None

    try:
        data = json.loads(cred_path.read_text())
        model: Optional[str] = data.get("model")
        return model
    except (json.JSONDecodeError, KeyError):
        return None


def load_saved_provider() -> Optional[str]:
    """Load a saved provider name.

    Returns:
        The provider string, or None if not saved.
    """
    cred_path = _get_credentials_path()
    if not cred_path.exists():
        return None

    try:
        data = json.loads(cred_path.read_text())
        provider: Optional[str] = data.get("provider")
        return provider
    except (json.JSONDecodeError, KeyError):
        return None


def clear_api_key() -> bool:
    """Remove saved API key.

    Returns:
        True if a key was removed, False if none existed.
    """
    cred_path = _get_credentials_path()
    if cred_path.exists():
        cred_path.unlink()
        return True
    return False


def has_saved_key() -> bool:
    """Check if there is a saved API key."""
    return load_api_key() is not None


def mask_key(key: str) -> str:
    """Mask an API key for safe display (show first 4 and last 4 chars)."""
    if len(key) <= 12:
        return key[:2] + "*" * (len(key) - 2)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]
