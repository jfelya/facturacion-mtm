"""Tkinter theme engine for the UI kit.

`apply_theme(root, name, fonts)` configures every ttk style from the tokens and returns the
palette dict. `THEMES` exposes the resolved palettes (app key names) so screens can read colours
without touching ttk internals.

App keys (kept stable for existing code):
    bg, card, header, header_fg, header_sub, accent, accent_d, accent_fg, accent_dis,
    accent_dis_fg, muted, txt, border, entry, tree, head, tab_bg, btn, btn_hover, sel,
    success, danger, warn_bg, warn_fg, status{...}
"""
from types import SimpleNamespace
import tkinter.font as tkfont
from tkinter import ttk

from .tokens import PALETTES, STATUS_TINTS, FONT_FAMILY, FONT_MONO, FONT_SIZE, METRICS


def _resolve(tokens, theme):
    tints = STATUS_TINTS[theme]
    return {
        "bg": tokens["background"],
        "card": tokens["surface"],
        "header": tokens["surface"],
        "header_fg": tokens["text"],
        "header_sub": tokens["text_dim"],
        "accent": tokens["accent"],
        "accent_d": tokens["accent_hover"],
        "accent_fg": tokens["accent_fg"],
        "accent_dis": tokens["border"],
        "accent_dis_fg": tokens["text_dim"],
        "muted": tokens["text_dim"],
        "txt": tokens["text"],
        "border": tokens["border"],
        "entry": tokens["surface"],
        "tree": tokens["surface"],
        "head": tokens["surface_alt"],
        "tab_bg": tokens["background"],
        "btn": tokens["surface"],
        "btn_hover": tokens["surface_alt"],
        "sel": tokens["selection"],
        "success": tokens["success"],
        "danger": tokens["danger"],
        "warn_bg": tokens["warning_bg"],
        "warn_fg": tokens["warning_fg"],
        "status": dict(tints),
    }


THEMES = {name: _resolve(tokens, name) for name, tokens in PALETTES.items()}


# --------------------------------------------------------------------------- fonts
def _pick(cands, available):
    for c in cands:
        if c in available:
            return c
    return "TkDefaultFont"


def make_fonts(root):
    """Resolve the font stack for this machine. Returns a SimpleNamespace of tuples."""
    fams = set(tkfont.families(root))
    fam = _pick(FONT_FAMILY, fams)
    return SimpleNamespace(
        family=fam,
        base=(fam, FONT_SIZE["base"]),
        bold=(fam, FONT_SIZE["base"], "bold"),
        title=(fam, FONT_SIZE["title"], "bold"),
        small=(fam, FONT_SIZE["small"]),
        mono=(FONT_MONO, FONT_SIZE["mono"]),
    )


# --------------------------------------------------------------------------- engine
def apply_theme(root, theme="dark", fonts=None):
    """Configure the root + every ttk style for `theme`. Returns the palette dict."""
    theme = theme if theme in THEMES else "dark"
    th = THEMES[theme]
    fonts = fonts or make_fonts(root)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    root.configure(bg=th["bg"])
    root.option_add("*Font", fonts.base)

    style.configure(".", background=th["bg"], foreground=th["txt"], font=fonts.base,
                    bordercolor=th["border"], focuscolor=th["accent"], borderwidth=0)
    style.configure("TFrame", background=th["bg"], borderwidth=0)
    style.configure("Card.TFrame", background=th["card"], borderwidth=1, relief="solid",
                    bordercolor=th["border"])
    style.configure("Header.TFrame", background=th["header"], borderwidth=0)
    style.configure("TLabel", background=th["bg"], foreground=th["txt"], font=fonts.base)
    style.configure("Card.TLabel", background=th["card"], foreground=th["txt"], font=fonts.base)
    style.configure("Bold.TLabel", background=th["card"], foreground=th["txt"], font=fonts.bold)
    style.configure("Hint.TLabel", background=th["card"], foreground=th["muted"], font=fonts.small)
    style.configure("Header.TLabel", background=th["header"], foreground=th["header_fg"],
                    font=fonts.title)
    style.configure("HeaderSub.TLabel", background=th["header"], foreground=th["header_sub"],
                    font=fonts.small)
    style.configure("Status.TLabel", background=th["header"], foreground=th["muted"], font=fonts.small)

    # buttons: base = surface + 1px border; hover = surface-alt + accent border
    style.configure("TButton", font=fonts.base, padding=(14, 7), background=th["btn"],
                    foreground=th["txt"], bordercolor=th["border"], borderwidth=1,
                    relief="flat", focuscolor=th["card"])
    style.map("TButton",
              background=[("active", th["btn_hover"]), ("pressed", th["sel"])],
              bordercolor=[("active", th["accent"])],
              foreground=[("disabled", th["muted"])])
    style.configure("Accent.TButton", font=fonts.bold, padding=(16, 7),
                    background=th["accent"], foreground=th["accent_fg"],
                    bordercolor=th["accent"], borderwidth=1, relief="flat")
    style.map("Accent.TButton",
              background=[("active", th["accent_d"]), ("pressed", th["accent"]),
                          ("disabled", th["accent_dis"])],
              bordercolor=[("disabled", th["accent_dis"])],
              foreground=[("disabled", th["accent_dis_fg"])])

    style.configure("TEntry", padding=(6, 3), fieldbackground=th["entry"], foreground=th["txt"],
                    insertcolor=th["txt"], bordercolor=th["border"], borderwidth=1)
    style.map("TEntry", bordercolor=[("focus", th["accent"])])
    style.configure("TCombobox", fieldbackground=th["entry"], background=th["entry"],
                    foreground=th["txt"], arrowcolor=th["muted"], bordercolor=th["border"],
                    borderwidth=1, padding=(6, 3))
    style.map("TCombobox", fieldbackground=[("readonly", th["entry"])],
              foreground=[("readonly", th["txt"])])
    style.configure("TSpinbox", fieldbackground=th["entry"], foreground=th["txt"],
                    arrowcolor=th["muted"], insertcolor=th["txt"], bordercolor=th["border"])

    style.configure("TNotebook", background=th["bg"], borderwidth=0, tabmargins=(6, 6, 6, 0))
    style.configure("TNotebook.Tab", font=fonts.base, padding=(14, 8),
                    background=th["tab_bg"], foreground=th["muted"])
    style.map("TNotebook.Tab", background=[("selected", th["card"])],
              foreground=[("selected", th["accent"])])

    style.configure("Treeview", font=fonts.small, rowheight=METRICS["row_height"],
                    background=th["tree"], fieldbackground=th["tree"], foreground=th["txt"],
                    bordercolor=th["border"], borderwidth=1, relief="flat")
    style.configure("Treeview.Heading", font=fonts.bold, background=th["head"],
                    foreground=th["muted"], relief="flat", padding=(10, 8))
    style.map("Treeview", background=[("selected", th["sel"])],
              foreground=[("selected", th["txt"])])
    style.map("Treeview.Heading", background=[("active", th["head"])])

    style.configure("TRadiobutton", background=th["card"], foreground=th["txt"], font=fonts.base)
    style.map("TRadiobutton", background=[("active", th["card"])])
    style.configure("TCheckbutton", background=th["card"], foreground=th["txt"], font=fonts.base)
    style.map("TCheckbutton", background=[("active", th["card"])])
    return th


def tag_rows(tree, theme):
    """Apply the semantic preview-row tints to a Treeview."""
    th = THEMES[theme]
    for name, col in th["status"].items():
        tree.tag_configure(name, background=col, foreground=th["txt"])
