# Tkinter UI Kit — Facturación MTM

Portable visual layer for our Tkinter apps, derived from
`VISUAL_DESIGN_SYSTEM.md` (SelfishNet v2, WPF) and adapted to Tk's limits.

**Rule:** this folder is the single source of truth for visuals. New screens/features must use
these tokens/styles — never hardcode colours or font sizes locally.

## Files

| File | Purpose |
|---|---|
| `tokens.py` | colours (dark/light), status tints, type scale, spacing, radii, metrics |
| `theme.py` | `make_fonts()`, `apply_theme()`, `tag_rows()`, resolved `THEMES` |
| `icons.py` | `asset_path()`, `load_icon()` (dev + one-file exe) |
| `widgets.py` | `hseparator()`, `StatusDot` |
| `__init__.py` | public exports |

## Quick start

```python
from app import uikit

fonts = uikit.make_fonts(root)          # .base .bold .title .small .mono
th = uikit.apply_theme(root, "dark", fonts)   # configures ttk; returns palette dict

label = ttk.Label(root, style="Header.TLabel")   # uses the kit styles
tree  = ttk.Treeview(root)
uikit.tag_rows(tree, "dark")            # semantic row tints

flag = uikit.load_icon(root, "ve", cache)        # assets/ui/ve.png
sep  = uikit.hseparator(root, th["border"]); sep.pack(fill="x")
dot  = uikit.widgets.StatusDot(root, bg=th["header"]); dot.set(th["success"])
```

## Palette keys (`th[...]`)

`bg, card, header, header_fg, header_sub, accent, accent_d, accent_fg, accent_dis,
accent_dis_fg, muted, txt, border, entry, tree, head, tab_bg, btn, btn_hover, sel,
success, danger, warn_bg, warn_fg` and `status{OK, NOTA, SUGERIDO, BALANCEADO, REVISAR,
ELEGIR, NO FACTURAR, SIN DATO}`.

## ttk styles provided

`TFrame`, `Card.TFrame`, `Header.TFrame`, `TLabel`, `Card.TLabel`, `Bold.TLabel`,
`Hint.TLabel`, `Header.TLabel`, `HeaderSub.TLabel`, `Status.TLabel`, `TButton`,
`Accent.TButton`, `TEntry`, `TCombobox`, `TSpinbox`, `TNotebook`/`TNotebook.Tab`,
`Treeview`/`Treeview.Heading`, `TRadiobutton`, `TCheckbutton`.

## Fidelity notes (Tk vs the WPF original)

- No rounded corners or shadows in Tk; we keep flat surfaces + 1 px borders.
- Tk has only normal/bold; the base face is **Segoe UI Semibold** to approximate *Medium*.
- Base text is **13 px**, secondary **11 px**.
- Theme switch is instant (no animation), like the original.

## Adding a new app

1. Copy `app/uikit/` into the new project (it is dependency-free: only `tkinter` + stdlib).
2. Call `make_fonts` + `apply_theme` once at startup.
3. Build screens with the provided styles/tokens; put new shared widgets in `widgets.py`.
