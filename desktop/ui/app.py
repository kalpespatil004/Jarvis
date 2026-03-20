"""Compatibility entrypoint.

Allows running:
    python -m desktop.ui.app

while the main implementation lives in `ui.desktop.app`.
"""

from ui.desktop.app import run


if __name__ == "__main__":
    raise SystemExit(run())
