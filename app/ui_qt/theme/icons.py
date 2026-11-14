"""Asset lookup and QIcon helpers for the Qt UI."""
import sys
from pathlib import Path

from PySide6.QtGui import QIcon


def asset_path(*parts):
    """Resolve `assets/...` in dev and inside the PyInstaller one-file exe."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base).joinpath(*parts)
    return Path(__file__).resolve().parents[3].joinpath(*parts)


def icon(name, size=None):
    """Load an icon from `assets/ui/<name>.png` or `assets/<name>`."""
    candidates = [
        asset_path("assets", "ui", f"{name}.png"),
        asset_path("assets", f"{name}.png"),
        asset_path("assets", f"{name}.ico"),
    ]
    for path in candidates:
        if path.exists():
            return QIcon(str(path))
    return QIcon()


def app_icon():
    """Window/taskbar icon; the multi-size .ico is what Windows renders best."""
    for name in ("icon.ico", "icon.png"):
        path = asset_path("assets", name)
        if path.exists():
            return QIcon(str(path))
    return QIcon()
