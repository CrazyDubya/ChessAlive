"""User interface components."""

from .display import BoardDisplay
from .cli import CLI

# GUI import is optional (requires tkinter)
try:
    from .gui import ChessAliveGUI
    __all__ = ["BoardDisplay", "CLI", "ChessAliveGUI"]
except ImportError:
    __all__ = ["BoardDisplay", "CLI"]
