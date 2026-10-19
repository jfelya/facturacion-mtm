"""Asset lookup + image loading for the UI kit (works in dev and inside the one-file exe)."""
import sys
from pathlib import Path

import tkinter as tk


def asset_path(*parts):
    """Resolve a bundled asset: `<root>/assets/...` in dev, `<MEIPASS>/assets/...` in the exe."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base).joinpath(*parts)
    return Path(__file__).resolve().parents[2].joinpath(*parts)


def load_icon(root, name, cache):
    """Load+cache a PNG from `assets/ui/<name>.png`. Returns a PhotoImage or None."""
    if name in cache:
        return cache[name]
    p = asset_path("assets", "ui", f"{name}.png")
    try:
        cache[name] = tk.PhotoImage(master=root, file=str(p))
    except Exception:
        cache[name] = None
    return cache[name]
