"""Design tokens for the Tkinter UI kit.

Ported from `VISUAL_DESIGN_SYSTEM.md` (SelfishNet v2, WPF) and adapted to what Tk can do.
This file is the SINGLE SOURCE OF TRUTH for colours, type, spacing and metrics. New screens
should read from here (or from the ttk styles produced by `theme.apply_theme`), never hardcode
colours locally.
"""

# --------------------------------------------------------------------------- scales
# Spacing scale used across the app (px).
SPACE = (2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24)

# Corner radii from the design. Tk has no rounded corners; kept for documentation / canvas work.
RADIUS = {"card": 10, "button": 6, "input": 5, "check": 4, "progress": 3}

# Component metrics.
METRICS = {
    "window": (1180, 790),
    "window_min": (1020, 640),
    "row_height": 30,
    "status_dot": 9,
    "toolbar_pad": (16, 10),
    "status_pad": (16, 6),
    "card_pad": 16,
}

# --------------------------------------------------------------------------- colours
# Raw tokens (semantic names). Two complete palettes, swapped at runtime.
PALETTES = {
    "dark": {
        "background": "#14171B",
        "surface": "#1C2128",
        "surface_alt": "#262C35",
        "border": "#333B47",
        "text": "#E6EDF3",
        "text_dim": "#9AA7B4",
        "accent": "#4C8DFF",
        "accent_hover": "#6FA3FF",
        "accent_fg": "#FFFFFF",
        "success": "#3FB950",
        "danger": "#F85149",
        "selection": "#25344A",
        "warning_bg": "#3D2E12",
        "warning_fg": "#F0B429",
    },
    "light": {
        "background": "#F3F5F7",
        "surface": "#FFFFFF",
        "surface_alt": "#ECEFF3",
        "border": "#D2D9E0",
        "text": "#1F2328",
        "text_dim": "#5A6572",
        "accent": "#0969DA",
        "accent_hover": "#2F7FE0",
        "accent_fg": "#FFFFFF",
        "success": "#1A7F37",
        "danger": "#CF222E",
        "selection": "#D6E6FA",
        "warning_bg": "#FFF3CD",
        "warning_fg": "#8A5A00",
    },
}

# Preview-row tints (semantic, low alpha-looking surfaces; text stays `text`).
STATUS_TINTS = {
    "dark": {
        "OK": "#183A22", "NOTA": "#3D2E12", "SUGERIDO": "#2C2640", "BALANCEADO": "#14333B",
        "REVISAR": "#3B2E17", "ELEGIR": "#1B2C44", "NO FACTURAR": "#2A2F36", "SIN DATO": "#3B1F22",
    },
    "light": {
        "OK": "#DDF4E0", "NOTA": "#FFF3CD", "SUGERIDO": "#E7DDF7", "BALANCEADO": "#D7EEF5",
        "REVISAR": "#FDE7C7", "ELEGIR": "#D9E7FB", "NO FACTURAR": "#E7E9EC", "SIN DATO": "#FBDDDD",
    },
}

# --------------------------------------------------------------------------- typography
# Tk only has normal/bold, so the base face is "Segoe UI Semibold" to approximate the
# design's Medium weight. Sizes are in px (negative numbers in Tk font tuples).
FONT_FAMILY = ("Segoe UI Semibold", "Segoe UI Variable Text", "Segoe UI", "Arial")
FONT_MONO = "Consolas"
FONT_SIZE = {"base": -13, "small": -11, "title": -17, "mono": -12}
