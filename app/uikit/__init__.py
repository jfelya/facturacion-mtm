"""Facturación MTM — Tkinter UI kit.

A small, dependency-free visual layer shared by our apps. It provides:
- design tokens (colours, type, spacing, metrics)  -> `tokens.py`
- theme engine (ttk styles for dark/light)          -> `theme.apply_theme`
- font resolution                                   -> `theme.make_fonts`
- icon loading (bundled PNGs)                       -> `icons.load_icon`
- tiny widgets (separators, status dot)             -> `widgets`

Usage:
    from app import uikit
    fonts = uikit.make_fonts(root)
    th = uikit.apply_theme(root, "dark", fonts)      # returns the palette dict
    ...
    uikit.tag_rows(tree, "dark")
    flag = uikit.load_icon(root, "ve", cache)
"""
from . import icons, tokens, widgets
from .theme import THEMES, apply_theme, make_fonts, tag_rows

load_icon = icons.load_icon
asset_path = icons.asset_path

__all__ = [
    "THEMES", "apply_theme", "make_fonts", "tag_rows",
    "load_icon", "asset_path", "tokens", "widgets", "icons",
]
