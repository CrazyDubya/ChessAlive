"""Main entry point for ChessAlive."""

import asyncio
import sys
from .ui.cli import CLI


def main():
    """Main entry point."""
    cli = CLI()
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
