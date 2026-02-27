"""
main.py - Application Entry Point

Run this file to launch the Fiction Novel Generator:

    python main.py

This module:
  1. Checks that the required packages are installed (gives a helpful message if not)
  2. Creates and starts the Tkinter main window
"""

from __future__ import annotations

import sys


def _check_dependencies() -> None:
    """
    Verifies that third-party dependencies are available.
    Prints a helpful error and exits if any are missing.
    """
    missing: list[str] = []

    try:
        import google.generativeai  # noqa: F401
    except ImportError:
        missing.append("google-generativeai")

    try:
        import dotenv  # noqa: F401
    except ImportError:
        missing.append("python-dotenv")

    if missing:
        print("=" * 60)
        print("Missing required packages!")
        print("Please run the following command:")
        print()
        print(f"    pip install {' '.join(missing)}")
        print()
        print("Or run setup_and_run.bat to install everything automatically.")
        print("=" * 60)
        sys.exit(1)


def main() -> None:
    """Launches the Fiction Novel Generator desktop application."""
    _check_dependencies()

    # Import gui after dependency check so we get a nice error message
    # instead of a raw ImportError stack trace.
    from gui import NovelGeneratorApp

    app = NovelGeneratorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
