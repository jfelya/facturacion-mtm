"""Qt design tokens.

Values are the same semantic palette as the Tk uikit until the Tk UI is removed.
The Qt module deliberately does not import `app.uikit` (which imports tkinter), so
the Qt build does not pull Tcl/Tk into the executable.
"""

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
        "accent_pressed": "#4477D6",
        "accent_fg": "#0B1020",
        "success": "#3FB950",
        "danger": "#F85149",
        "selection": "#25344A",
        "warning_bg": "#3D2E12",
        "warning_fg": "#F0B429",
        "overlay": "rgba(11, 13, 16, 0.72)",
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
        "accent_pressed": "#0757B8",
        "accent_fg": "#FFFFFF",
        "success": "#1A7F37",
        "danger": "#CF222E",
        "selection": "#D6E6FA",
        "warning_bg": "#FFF3CD",
        "warning_fg": "#8A5A00",
        "overlay": "rgba(255, 255, 255, 0.75)",
    },
}

STATUS_TINTS = {
    "dark": {
        "OK": "#183A22", "NOTA": "#3D2E12", "SUGERIDO": "#2C2640",
        "BALANCEADO": "#14333B", "REVISAR": "#3B2E17", "ELEGIR": "#1B2C44",
        "NO FACTURAR": "#2A2F36", "FACTURADO": "#2A2F36", "SIN DATO": "#3B1F22",
    },
    "light": {
        "OK": "#DDF4E0", "NOTA": "#FFF3CD", "SUGERIDO": "#E7DDF7",
        "BALANCEADO": "#D7EEF5", "REVISAR": "#FDE7C7", "ELEGIR": "#D9E7FB",
        "NO FACTURAR": "#E7E9EC", "FACTURADO": "#E7E9EC", "SIN DATO": "#FBDDDD",
    },
}

METRICS = {
    "window": (1280, 800),
    "window_min": (1000, 620),
    "topbar_height": 56,
    "toolbar_height": 40,
    "summary_height": 40,
    "sidebar_width": 310,
    "detail_height": 128,
    "row_height": 34,
    "header_height": 32,
    "status_dot": 9,
    "card_pad": 14,
    "card_radius": 8,
    "button_radius": 6,
    "input_radius": 5,
    "icon_size": 20,
}

FONT_FAMILY = ("Segoe UI Variable Text", "Segoe UI", "Arial")
FONT_MONO = "Consolas"
FONT_SIZE = {"base": 13, "small": 11, "title": 20, "section": 12, "mono": 12}

STATUS_ORDER = {
    "ELEGIR": 0, "REVISAR": 1, "SUGERIDO": 2, "BALANCEADO": 3, "NOTA": 4,
    "OK": 5, "SIN DATO": 6, "NO FACTURAR": 7, "FACTURADO": 8,
}


def resolve(theme):
    base = dict(PALETTES.get(theme, PALETTES["dark"]))
    base["status"] = dict(STATUS_TINTS.get(theme, STATUS_TINTS["dark"]))
    return base


THEMES = {name: resolve(name) for name in PALETTES}
