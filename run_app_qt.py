"""Qt GUI entry point; the engine/CLI entry in run_app.py is unchanged."""
import sys

from app.ui_qt.application import main


if __name__ == "__main__":
    sys.exit(main())
