# PySide6 + QSS UI Migration — Feasibility and Implementation Analysis

**Date:** 2026-11-14
**Status:** Analysis only — no production code changed, no PySide6 install
**Scope:** UI layer only. The engine, CLI and output formats stay untouched.
**Owner decision assumed:** move to **64-bit only** with the new visual design.
**Prompt analysed:** `docs/PROMPT_PYSIDE6_UI_MIGRATION.md`

---

## 1. Executive summary

### Verdict

**Conditional GO for PySide6**, if all of these stay true:

1. 64-bit Windows 10 (1809+) / Windows 11 is acceptable. There is no 32-bit Qt 6 path.
2. The LGPLv3 obligations are acceptable and reviewed before external distribution.
3. A short packaging/visual spike passes: one-file build, acceptable startup, clean Windows VM, table at real batch size.
4. The project can afford roughly **2–4 weeks** of UI, packaging and parity work, plus parallel running.

If the only goal is “a nicer-looking UI”, or if 32-bit support must remain, **do not migrate**. The current tokens already match SelfishNet; the visual gap is mostly Tkinter’s rendering, not the palette. The cheapest 80–90 % improvement is to keep the engine and polish the existing Tk/ttk UI, or use `ttkbootstrap`/CustomTkinter (MIT-style, 32-bit-capable) and accept that `ttk.Treeview` remains the table.

### Why PySide6 is technically viable

- **PySide6 6.12.0** (latest verified) supports Python **3.10–3.15** (`<3.16`) and ships a `cp310-abi3-win_amd64` wheel. The installed **Python 3.14.6 64-bit** is supported.
- The useful package is **`PySide6-Essentials`**, not the full `PySide6` meta-package. The wheel is **78.3 MB compressed**; the meta-package pulls Addons, WebEngine and PDF modules that this app does not need.
- **Qt 6.12** supports **Windows 10 1809+ x86_64** and **Windows 11**. It is the **last Qt release that supports Windows 10**; pin 6.12 LTS and plan the Windows 10 horizon.
- PyInstaller **6.22.3** already contains PySide6 hooks; `_pyinstaller_hooks_contrib` 2026.9 is installed. Hook support exists; the 6.12 combination still needs a real build test.
- The UI is small and bounded: `app/ui.py` is **628 lines**, plus `app/strings.py` 187 and `app/uikit` 245; the engine is **1,739 lines** across eight modules. The engine boundary is clean: `run_job`, `write_output`, `generate_bulks`, `generate_driverlogs`, `report_text`.
- The engine tests (**39**) and the Excel/BULK/DOCX outputs are already stable and can be used as a parity gate.

### Cost at a glance

| Scope | One developer, no AI | With AI assistance |
|---|---:|---:|
| UI only (spike, shell, table, dialogs, wiring) | **10–15 days** | **6–10 days** |
| Packaging + QA + parallel run + cutover | **8–14 days** | **5–8 days** |
| **Total** | **18–29 days** | **11–18 days** |

Add **20–30 %** if this is the first serious PySide6/QSS desktop project. These are engineering ranges, not commitments; the spike narrows them.

### Recommended first step

Do **not** start the full rewrite. Build a **2–3 day throwaway spike** (not in `app/`, e.g. `spikes/qt_shell/`) that proves:

- PySide6 6.12 runs on Python 3.14.6 64-bit.
- The 81-row October **test** batch renders in `QTableView`.
- The dark/light QSS and status pills look right at 100/125/150/200 %.
- A one-file PyInstaller build starts on a clean Windows 10/11 64-bit VM.
- The artifact size and startup time are acceptable.

Only then approve the design and write the implementation plan.

---

## 2. Current state

### 2.1 Size and packaging facts

| Item | Current value | Source |
|---|---|---|
| App version | **2.4.0.0** | `version_info.txt`, root exe |
| Root executable | 32-bit x86 one-file, **16,595,921 bytes**, PE `0x014C` | `Facturacion MTM.exe` |
| UI code | 628 lines | `app/ui.py` |
| UI strings | 187 lines | `app/strings.py` |
| UI kit | 245 lines | `app/uikit/{tokens,theme,widgets,icons}.py` |
| Total UI layer | **1,060 lines** | `ui.py` + `strings.py` + `uikit/` modules |
| Engine | **1,739 lines** | `common`, `parsers`, `filler`, `pipeline`, `report`, `writer`, `bulk`, `driverlogs` |
| Tests | **39 unittest tests**, 731 lines | `tests/` |
| Python | 3.14.6 64-bit installed | `C:\Users\Fely\AppData\Local\Python\pythoncore-3.14-64\python.exe` |
| Runtime deps | `openpyxl==3.1.5`, `python-docx==1.2.0` | `requirements.txt` |
| Build dep | `pyinstaller==6.22.3` | `requirements-build.txt` |
| Build recipe | one-file, windowed, icon + version, `hiddenimports=['docx']`, excludes numpy/pandas/matplotlib/scipy/PIL | `Facturacion MTM.spec` |
| Build script | defaults to 32-bit portable Python, `dist32`/`build32` | `build.ps1` |
| PySide6 | **not installed** (analysis only) | checked import |

### 2.2 Screens, panels and controls in `app/ui.py`

| Area | Current implementation | Lines |
|---|---|---|
| Header | title, subtitle, theme image label, language image label | 101–119 |
| Input card | 5 path rows: claim, sources, drivers, driverlogs, days root; each has label, entry, browse button, hint | 124–134, 220–233 |
| Options | strategy radios (`first_row_B`, `pair`, `first_row_A`), Will Call spinbox (0–8, default 2), Suggest/Spread/Balance checkboxes | 136–160 |
| Actions | Help, Process (primary), Export Excel, Save CSV, Generate driverlogs, Generate BULK | 162–175 |
| Tabs | Preview table, Report text, Assign-driver tab | 177–186 |
| Preview table | `ttk.Treeview`, 9 columns: `#`, Date, Member, Trip, Driver, Milage, PU, DropOff, Status | 188–199 |
| Report | `tk.Text`, monospace, read-only by convention | 201–205 |
| Assign tab | 5-column tree + candidate combo + Assign/Clear + license/VIN label | 235–259 |
| Status bar | 9 px Canvas dot + status text; 1 px separators | 209–218, 282–283 |
| Theme | `uikit.apply_theme`, row tags, separator colors, status dot, icons | 261–295 |
| i18n | `STRINGS[self.lang]`, `t()`; retranslate all labels/headings | 297–347 |
| Browse | `filedialog.askopenfilename`, `askdirectory` | 349–378 |
| Help | `messagebox.showinfo` with long text | 380–381 |
| Process | validate, pre-scan sources, warn if no trip files, disable actions, `threading.Thread`, `run_job` | 383–443 |
| Render | status counts, table insert with tags, report text, assign list, status line | 445–492 |
| Assign | populate pending rows, candidates by `(date, county)`, assign/clear, re-render | 494–575 |
| Exports | Excel save dialog + `write_output`; CSV + `ensure_not_source`/`write_report_csv`; driverlogs; BULK | 577–665 |
| App start | DPI ctypes, `tk.Tk`, scaling 1.25, maximize | 668–684 |

### 2.3 Main user flow

1. Pick `ClaimInformation … OLD.xlsx` (Step 1).
2. Pick sources folder (Step 2); if empty, the claim folder is auto-filled.
3. Optionally pick `Informacion de Drivers.xlsx` (Step 3).
4. Optionally pick driverlog `.docx` templates (Step 4).
5. Optionally pick the days root (Step 5); if empty, sources folder is used.
6. Set leg strategy, Will Call hours, suggest/spread/balance.
7. **Process**; the UI pre-scans for trip files and asks Proceed/Cancel if none.
8. Review the colored preview (OK, NOTA, SUGERIDO, BALANCEADO, REVISAR, ELEGIR, NO FACTURAR, FACTURADO, SIN DATO).
9. Assign or clear drivers for suggested/empty rows.
10. Export Excel, save CSV, generate driverlogs, generate BULK UPLOAD.

### 2.4 State

- **`App` state:** `lang` (default `es`), `theme` (default `dark`), `result` (engine result or `None`), `_assign_map` (tree item → row), `_assign_cands`, `_imgs` (PhotoImage cache), fonts; `StringVar`/`BooleanVar` for 10 values.
- **Engine result:** `{claim: {rows, path}, report: {stats, warnings, review, needs_driver, driver_candidates, suggested, not_billed, already_billed, resumen_without_claim}, sources, claim_path, drivers}`.
- **Hidden coupling:** `_render` mutates `result["report"]["needs_driver"]` and `result["report"]["suggested"]` (lines 449–457). The Qt view model should derive these values from the claim rows instead of mutating the engine report.
- **No persistence:** there is no config file, no `QSettings`, no last-folder store, no recent-files list. Theme/language always start dark/es.
- **No keyboard shortcuts or menus:** only default Tab traversal.

### 2.5 Tk-specific behaviour and the Qt equivalent

| Tk today | Why it exists | Qt equivalent / care |
|---|---|---|
| `ttk.Treeview` + tags | fast table, row background per status | `QTableView` + `QAbstractTableModel`; `BackgroundRole` and/or delegate |
| `root.after(0, ...)` | marshal worker result to UI thread | Qt signals across threads; never touch widgets from the worker |
| `threading.Thread` | keep UI responsive during `run_job` | `QThread` + worker object, or `QThreadPool`/`QRunnable` |
| `tk.PhotoImage` | PNG icons in labels | `QIcon`/`QPixmap`; multi-size/2x or SVG |
| `_init_dpi` ctypes | Tk DPI awareness | Qt 6 high-DPI is automatic; optional title-bar DWM only |
| `root.state("zoomed")` | maximize on start | `showMaximized()` |
| `_MEIPASS` path lookup | one-file assets | same `sys._MEIPASS` check with `QIcon`/`QFile` |
| `ttk.Style` in `uikit/theme.py` | theme engine | generated QSS + `QPalette`; no per-widget style objects |
| `StringVar` / `BooleanVar` | form state | plain dataclass/`AppState` + Qt signals; no business logic |
| `tk.Text` | report | `QPlainTextEdit` (read-only, monospace, copyable) |
| `messagebox` / `filedialog` | dialogs | `QMessageBox` wrappers / `QFileDialog` |
| `ttk.Treeview` assign tab | pending assignments | `AssignDriverDialog` with a candidate table |
| `Canvas` status dot / separators | custom drawing | small `QWidget` with `paintEvent`, or `QFrame` HLine |
| `ttk.Treeview` tags are not per-cell | status is row-wide | model row tint + delegate status pill in the Status column |

### 2.6 Current visual tokens (source of truth)

- `app/uikit/tokens.py` already ports SelfishNet’s dark/light palette and status tints.
- `app/uikit/theme.py` maps tokens to `bg`, `card`, `header`, `accent`, `muted`, `txt`, `border`, `tree`, `head`, `btn`, `sel`, `success`, `danger`, `warn_bg`, `warn_fg`, `status`.
- Current font: `Segoe UI Semibold` fallback stack, base 13 px, small 11 px, title 17 px, mono Consolas 12 px.
- Current metrics: window 1180×790, min 1020×640, row height 30, card padding 16, status dot 9.
- Current cards have **no radius**; Tk cannot do rounded corners without custom drawing.
- The visual gap is therefore **rendering capability**, not a different design language.

---

## 3. Visual reference extraction

### 3.1 Colour tokens: SelfishNet → Monmusu → current Facturación → proposed Qt

SelfishNet and Facturación have both dark and light palettes. Monmusu is dark-only in the reference.

| Role | SelfishNet dark | SelfishNet light | Monmusu dark | Current Facturación dark | Current light | Proposed Qt token |
|---|---|---|---|---|---|---|
| App background | `#14171B` | `#F3F5F7` | `#0F1115` | `#14171B` | `#F3F5F7` | `bg` |
| Surface / cards / toolbar | `#1C2128` | `#FFFFFF` | `#1C222C` | `#1C2128` | `#FFFFFF` | `surface` |
| Surface alt / hover / header | `#262C35` | `#ECEFF3` | `#232B38` | `#262C35` | `#ECEFF3` | `surface_alt` |
| Border / separator | `#333B47` | `#D2D9E0` | `#2D3747` | `#333B47` | `#D2D9E0` | `border` |
| Primary text | `#E6EDF3` | `#1F2328` | `#E8EDF5` | `#E6EDF3` | `#1F2328` | `text` |
| Secondary text | `#9AA7B4` | `#5A6572` | `#9AA6B6` | `#9AA7B4` | `#5A6572` | `text_dim` |
| Faint labels | — | — | `#6F7C8F` | — | — | `text_faint` (from Monmusu; optional) |
| Accent | `#4C8DFF` | `#0969DA` | `#5B8DEF` | `#4C8DFF` | `#0969DA` | `accent` |
| Accent hover | `#6FA3FF` | `#2F7FE0` | `#76A3FF` | `#6FA3FF` | `#2F7FE0` | `accent_hover` |
| Accent pressed | — | — | `#4477D6` | — | — | `accent_pressed` (Monmusu; derive light pressed from accent) |
| On accent | white | white | `#0B1020` | white | white | `on_accent` (accessibility decision; see §7.6) |
| Success | `#3FB950` | `#1A7F37` | `#4CC38A` | `#3FB950` | `#1A7F37` | `success` |
| Danger | `#F85149` | `#CF222E` | `#F06A6A` | `#F85149` | `#CF222E` | `danger` |
| Warning background | `#3D2E12` | `#FFF3CD` | `#D9A441` (warning fg) | `#3D2E12` | `#FFF3CD` | `warning_bg` |
| Warning text | `#F0B429` | `#8A5A00` | `#D9A441` | `#F0B429` | `#8A5A00` | `warning_fg` |
| Selection | accent 28 % | accent 18 % | `#2A3B57` | `#25344A` | `#D6E6FA` | `selection` |
| Modal overlay | `#0B0D10` 72 % | white 75 % | — | none | none | `overlay` |
| Chart series | `#58A6FF` / `#3FB950` | `#0969DA` / `#1A7F37` | — | none | none | not used |

**Conclusion:** keep the current Facturación palette as the source of truth. Use Monmusu only for pressed-accent/faint-label values if needed. Do not introduce a second brand palette.

**Alias note:** the current `app/uikit/theme.py` keys are aliases, not extra colors:
`header=surface`, `card=surface`, `entry=surface`, `tree=surface`, `head=surface_alt`, `tab_bg=background`,
`btn=surface`, `btn_hover=surface_alt`, `sel=selection`, `muted=text_dim`, `txt=text`,
`warn_bg=warning_bg`, `warn_fg=warning_fg`. The Qt token module should keep the same aliases or resolve them at
build time; never hardcode a second value.

### 3.2 Typography and metrics

| Role | SelfishNet | Monmusu | Current Facturación | Proposed Qt |
|---|---|---|---|---|
| Window design size | 1280×780 | 1550×830 | 1180×790 | **1280×800** |
| Window minimum | 880×470 | 1000×600 | 1020×640 | **1000×620** |
| Base font | Segoe UI Variable Text → Segoe UI, 13, Medium | Segoe UI, 13 | Segoe UI Semibold, 13 | **Segoe UI Variable Text → Segoe UI, 13, Medium (500)** |
| Page title | — | 20, SemiBold | 17, bold | **20, SemiBold (600)** |
| Section title | 12, SemiBold | 12, SemiBold | 13, bold | **12, SemiBold** |
| Field label / hint | 11 | 11, faint | 11 | **11, text_faint/text_dim** |
| Mono / technical | Consolas 13 | Consolas | Consolas 12 | **Consolas 12–13** |
| Main table row | 34 (dialog 38) | 28 | 30 | **34 main; 28 compact dialogs** |
| Table header | 10,8 padding | 32 height, 8,0 padding | 10,8 | **32 height; 10,8 padding** |
| Table cell | 10,4 | 8,0 | — | **10,4** |
| Card radius | 10 | 8 | 0 | **8** |
| Button radius | 6 | 6 | 0 | **6** |
| Input radius | 5 | 6 | 0 | **5** |
| Checkbox radius | 4 | 4 | — | **4** |
| Card padding | 10–24 | 14 | 16 | **14** |
| Toolbar padding | 12,9 | — | 16,10 | **12,9** |
| Status padding | 14,8 | — | 16,6 | **14,8** |
| Outer content margin | 12 | 16 | 14 | **12–16** |
| Button padding | 14,7 (primary 16,7) | 12,7 | 14,7 / 16,7 | **14,7 / 16,7** |
| Status dot | 9 | — | 9 | **9** |
| Scrollbar width | 10 | — | ttk default | **10** |

**Call:** use **1280×800** as the design size and **1000×620** minimum. It is close to the current 1180×790 and SelfishNet’s 1280×780, and leaves room for a 300 px source sidebar plus a 900 px table on a 1280-wide window. Maximize on start; keep the layout responsive.

### 3.3 Status colours

Use the current `STATUS_TINTS` exactly; do not invent new statuses or new hues.

| Status | Dark background | Light background | Proposed text/icon |
|---|---|---|---|
| OK | `#183A22` | `#DDF4E0` | success / dark green |
| NOTA | `#3D2E12` | `#FFF3CD` | warning_fg / brown |
| SUGERIDO | `#2C2640` | `#E7DDF7` | text on violet tint |
| BALANCEADO | `#14333B` | `#D7EEF5` | text on teal tint |
| REVISAR | `#3B2E17` | `#FDE7C7` | warning_fg / brown |
| ELEGIR | `#1B2C44` | `#D9E7FB` | accent / blue |
| NO FACTURAR | `#2A2F36` | `#E7E9EC` | text_dim / gray |
| FACTURADO | `#2A2F36` | `#E7E9EC` | text_dim / gray |
| SIN DATO | `#3B1F22` | `#FBDDDD` | danger / red |

Rules:
- Status is **text plus tint plus pill**, never colour alone.
- Row tint can use the status background; the Status column gets a rounded pill with the status label.
- Selected rows must remain readable; do not let the selection colour erase the status label.

### 3.4 WPF effects that cannot/should not be copied exactly

| WPF effect | Qt reality | Qt-appropriate substitute |
|---|---|---|
| DWM immersive dark title bar | Qt does not expose it; Windows 10 1809+ has `DwmSetWindowAttribute` | Optional ctypes helper for attributes 20/19; fallback to native light chrome. Do not build a custom frame. |
| Rounded window corners | Window corners are OS-managed | Rounded cards/buttons via QSS; Windows 11 rounds the window; Windows 10 stays square |
| Drop shadows / glows | Not part of SelfishNet; Qt QSS has no box-shadow | None; use 1 px borders and surface tints |
| WPF storyboards (progress/chart) | Different animation model | `QProgressBar` indeterminate; no decorative animations; theme switch instant |
| Native WPF popup shadows | Qt popups are native/Qt-drawn and vary by style | QSS for `QComboBox` popup and `QToolTip`; accept OS shadow differences |
| ClearType/WPF text metrics | Qt font rasterisation differs | `Segoe UI Variable Text`/`Segoe UI`; test at 100–200 %; use layouts, not fixed widths |
| Path-based WPF icons | Qt uses QIcon/QPainter/SVG | SVG icons or 1×/2× PNGs; no mixed icon family |
| DWM Mica/acrylic | Not used by SelfishNet; Windows 11 only | Do not add |

---

## 4. Proposed architecture

### 4.1 File tree

```
Facturacion MTM/
├── run_app.py                    # unchanged: CLI + current Tk GUI (rollback)
├── run_app_qt.py                 # new: Qt GUI entry point only
├── app/
│   ├── ...                       # engine unchanged
│   ├── status.py                 # new shared status_of mapping (no Tk/Qt imports)
│   └── ui_qt/
│       ├── __init__.py
│       ├── application.py        # QApplication, fonts, icons, theme manager, main()
│       ├── main_window.py        # QMainWindow shell, actions, signals
│       ├── view_model.py         # AppState, derived rows/counts, no widgets
│       ├── models/
│       │   ├── roles.py          # RawRowRole, StatusRole, SortRole
│       │   ├── claim_table_model.py
│       │   └── claim_filter_proxy.py
│       ├── delegates/
│       │   └── status_delegate.py
│       ├── dialogs/
│       │   ├── assign_driver.py
│       │   ├── help_dialog.py
│       │   └── messages.py       # QMessageBox wrappers with translation
│       ├── workers/
│       │   └── job_worker.py     # QThread worker around run_job
│       ├── theme/
│       │   ├── tokens.py         # Qt token source (copy of current uikit values)
│       │   └── qss.py            # build_qss(theme) + apply_theme()
│       ├── widgets/
│       │   ├── path_picker.py    # label + line edit + browse + hint
│       │   ├── summary_strip.py  # clickable status count chips
│       │   ├── detail_drawer.py  # selected row + Assign/Clear
│       │   └── status_dot.py     # 9 px painted dot
│       └── resources/            # optional Qt resource/icon helpers
├── requirements-ui.txt           # PySide6-Essentials==6.12.0
├── requirements-ui-build.txt     # -r requirements-ui.txt + pyinstaller
├── Facturacion MTM Qt.spec       # new one-file recipe
├── build_qt.ps1                  # 64-bit Qt build, copies Facturacion MTM Qt.exe
├── tests_qt/                     # pytest-qt UI tests, synthetic fixtures
└── docs/                         # this analysis + future design/plan
```

### 4.2 Responsibilities

| File / class | Responsibility | Must not do |
|---|---|---|
| `app/ui_qt/application.py` | Create `QApplication`, set app id/version/icon, high-DPI policy, font, theme, show `MainWindow` | Business logic |
| `MainWindow` | Shell layout, actions, state binding, wiring engine calls | Parse or fill claims |
| `AppState`/`view_model` | Form paths/options, `result`, selected row key, derived counts, assign/clear user edits | Touch widgets; reimplement matching |
| `ClaimTableModel` | Map `claim["rows"]` to columns/roles; stable sort keys; status mapping | Call engine; mutate rows except user assignment |
| `ClaimFilterProxyModel` | Status/search filter; numeric sort; stable selection | Recompute business statuses |
| `StatusDelegate` | Draw status pill; preserve row tint/selection | Decide status semantics |
| `AssignDriverDialog` | Candidate list for one row; assign/clear; license/VIN preview | Choose candidates itself |
| `JobWorker` | Run `run_job` in a `QThread`; emit result/error | Touch widgets |
| `theme/tokens.py` | Single Qt token source | Duplicate colors in widgets |
| `theme/qss.py` | Generate/apply complete QSS; theme switching; QPalette | Per-widget hardcoded colors |
| `status.py` | `status_of(row)` shared by Tk and Qt | Import Tk/Qt |
| `run_app_qt.py` | GUI-only entry; imports Qt | Import engine in CLI path |

### 4.3 Engine boundary

The Qt UI may call only these existing functions:

- `app.pipeline.scan_sources` for the pre-run no-trip check.
- `app.pipeline.run_job` for the full job.
- `app.writer.write_output` / `app.writer.ensure_not_source`.
- `app.report.write_report_csv` / `app.report.report_text`.
- `app.bulk.generate_bulks` / `app.bulk.report_lines`.
- `app.driverlogs.generate_driverlogs` / `app.driverlogs.report_lines`.

No parser, filler, writer logic is moved into widgets. The UI may update the claim row's `driver`, `license`, `vin`, `flag` after a user assignment, exactly as the Tk UI does today; that is a UI edit, not business logic.

### 4.4 Transition strategy

- Keep `run_app.py` and `app/ui.py` frozen for rollback. Do not add new features to Tk.
- Add `run_app_qt.py` and `app/ui_qt/` beside the current UI.
- Keep the current 32-bit exe as `Facturacion MTM.exe` until the Qt build passes parity; build the new one as `Facturacion MTM Qt.exe` (or `dist_qt/`).
- At cutover, decide whether to rename `run_app_qt.py` to the default GUI entry and remove `app/ui.py`/`app/uikit`. Do not maintain both indefinitely.
- The CLI remains `run_app.py --cli …` and must not import PySide6.

### 4.5 Versioning

- Four-part app version for the Qt release: **3.0.0.0** (UI/platform breaking change).
- Keep engine versioned with the app; no separate engine version is needed.
- `version_info.txt` should reflect 3.0.0.0 for the Qt build; the Tk rollback stays 2.4.0.0.

---

## 5. Screen blueprints

### 5.1 Main window (1280×800, maximized)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  [MTM icon]  Facturación MTM                          [ES/EN] [☾/☀] [Help]  │ 56
│              Fill the portal ClaimInformation…                              │
├───────────────────────┬──────────────────────────────────────────────────────┤
│  INPUTS               │  [OK 12] [NOTA 3] [SUGERIDO 2] [REVISAR 1] [ELEGIR 4]│ 44
│                       │  [Export Excel] [CSV] [Driverlogs] [BULK]            │ 40
│ 1 Claim       [……][…]│  ┌ Preview ┬ Report ┐                               │
│   hint                │  │ # │ Date │ Member │ Trip │ Driver │ Mil │ PU …  │
│ 2 Sources     [……][…]│  │ 2 │ 10/05│ LISA…  │ M4…  │ 200    │ 5.67│ 10:49 │
│   hint                │  │ 3 │ 10/05│ ELENA… │ M4…  │ 309    │ 11.27│ 9:42 │
│ 3 Drivers     [……][…]│  │ … │      │        │      │        │     │       │
│   hint                │  │   │      │        │      │        │     │       │
│ 4 Templates   [……][…]│  └──────────────────────────────────────────────────┘ │
│   hint                │  ┌ Selected row ────────────────────────────────────┐ │
│ 5 Days root   [……][…]│  │ LISA HALSEY · M4F32EG2N0A · 10/05/2026           │ │
│   hint                │  │ Driver 200 · License … · VIN … · Cost $15.00     │ │
│                       │  │ [Assign driver] [Clear]         [Copy row]       │ │
│ Options               │  └───────────────────────────────────────────────────┘ │
│  Driver per leg       │                                                      │
│  (•) One per leg      │                                                      │
│  ( ) Same both legs   │                                                      │
│  ( ) Reversed         │                                                      │
│  Will Call = A + [2]h │                                                      │
│  [x] Suggest driver   │                                                      │
│  [x] Split drivers    │                                                      │
│  [x] Balance trips    │                                                      │
│                       │                                                      │
│  [        Process        ]                                                   │
├───────────────────────┴──────────────────────────────────────────────────────┤
│  ● Ready · 81 rows · 14 to assign                        2.4.0.0 · 64-bit    │ 32
└──────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Layout rationale

- **Left source rail (300 px)** matches the sequential “Step 1…5” workflow and keeps the table wide. It is closer to Monmusu’s left files panel than to the current full-width input card.
- **Top bar + toolbar** follows SelfishNet’s anchored toolbar: identity on the left, utility toggles on the right; output actions stay near the result.
- **Summary strip** turns the current status-bar counts into clickable filters; it is the fast way to review only `ELEGIR`/`SUGERIDO`/`REVISAR`.
- **Bottom detail drawer** preserves horizontal space for 9 columns and replaces the current third tab. It appears when a row is selected, shows License/VIN/Cost and the row’s notes, and hosts Assign/Clear.
- **Preview/Report tabs** keep the current mental model; Report is read-only and copyable.
- **Empty state:** before processing, the center shows a welcome card (`QStackedWidget` page) with “Select claim / sources / Process”; the table is not a blank grid.

### 5.3 Assign-driver dialog (modal, 760×520, centered on owner)

```
┌─ Assign driver ────────────────────────────────────────────────────────────┐
│ LISA HALSEY · 10/05/2026 · M4F32EG2N0A                                    │
│ Current: 200 - JORGE NINO · 2 trips                                       │
│ Search: [………………]  [x] Only free today        County: MARION             │
│ ┌───┬────────┬──────────────────────┬───────┬───────────┬───────────────┐ │
│ │ # │ Driver │ Name                 │ Trips │ License   │ VIN           │ │
│ ├───┼────────┼──────────────────────┼───────┼───────────┼───────────────┤ │
│ │200│ 200    │ JORGE NINO           │ 2     │ N242-…    │ 2C4RD…        │ │
│ │220│ 220    │ JEIMY DELGADO        │ 0     │ D239-…    │ 5XY…          │ │
│ │309│ 309    │ MARIELKIS …          │ 3     │ M618-…    │ JTD…          │ │
│ └───┴────────┴──────────────────────┴───────┴───────────┴───────────────┘ │
│ [Clear]                                             [Cancel] [Assign]     │
└────────────────────────────────────────────────────────────────────────────┘
```

- Double-click a row or press Enter = Assign.
- Assign is disabled until a candidate is selected.
- Clear sets `driver/license/vin=""`, `flag="elegir"`, and closes.
- The dialog uses `report["driver_candidates"][(date, county)]`; no new candidate logic.
- A suggested row can be confirmed by assigning the suggested candidate, or cleared.

### 5.4 Help dialog (720×560)

```
┌─ What files do I need? ────────────────────────────────────────────────┐
│ 1) PORTAL CLAIM …                                                      │
│ 2) SOURCES FOLDER …                                                    │
│ 3) DRIVERS …                                                           │
│ IMPORTANT …                                                            │
│                                                                        │
│                                                    [Close]              │
└────────────────────────────────────────────────────────────────────────┘
```

- `QTextBrowser` with `setOpenExternalLinks(False)`; render the existing `help_body` text with escaped text/`<pre>`; no new Markdown dependency.
- Resizable; remembers nothing (no settings yet).

### 5.5 Error / confirmation dialogs

- `messages.py` wrappers around `QMessageBox`:
  - `show_error(title, text)` → `QMessageBox.critical`.
  - `show_info(title, text)` → `QMessageBox.information`.
  - `confirm(title, text, ok_text, cancel_text)` → `QMessageBox.question` with custom buttons.
  - `no_trip_files()` → `Ok/Cancel`, same wording as today.
  - `pending_drivers(n)` → `Yes/No`.
- Use translated strings from `app/strings.py`; no hardcoded English.
- Native `QFileDialog` for file/folder selection; start from the claim folder; auto-fill sources/days root exactly as today.

### 5.6 Theme/language controls

- Two `QToolButton`s in the top-right: language flag (`ve`/`us`) and theme (`moon`/`sun`), 20–24 px icons, tooltips, accessible names.
- One click toggles; no menu.
- On language change: call `retranslate()` on main window and any open dialogs; table headers, tab labels, status text, summary chips, combo labels, and report re-render; values and selection stay.
- On theme change: apply tokens/QSS/palette/icons; repaint table model; no restart; if a busy job is running, disable toggles.

---

## 6. Component mapping

| Current (Tkinter) | Proposed (PySide6) | Notes |
|---|---|---|
| `tk.Tk` root | `QApplication` + `MainWindow(QMainWindow)` | `showMaximized`; `setWindowIcon`; no custom frame |
| Header `ttk.Frame` | `QFrame#TopBar` inside `QVBoxLayout` | 1 px bottom border via QSS; 56 px height |
| Title `ttk.Label` (`Header.TLabel`) | `QLabel#PageTitle` | 20 px SemiBold; object name/role |
| Subtitle `ttk.Label` | `QLabel#Subtitle` | 11–12 px text_dim |
| Theme/language image `tk.Label` | `QToolButton` with `QIcon` | 20–24 px; tooltip; accessible name |
| `ttk.Frame` card | `QFrame#Card` | 1 px border, 8 px radius, 14 px padding |
| Input row frame | `PathPicker(QWidget)` | `QLabel`, `QLineEdit`, `QToolButton`, hint `QLabel` |
| `ttk.Entry` | `QLineEdit` | editable; file path; `clearButtonEnabled` optional |
| Browse `ttk.Button` | `QPushButton` / `QToolButton` | opens `QFileDialog` |
| `ttk.Radiobutton` ×3 | `QRadioButton` + `QButtonGroup` | same three strategy IDs; no logic change |
| `ttk.Spinbox` | `QSpinBox` | 0–8, default 2, suffix “h” |
| `ttk.Checkbutton` ×3 | `QCheckBox` | suggest/spread/balance; same defaults |
| Primary `ttk.Button` | `QPushButton[role="primary"]` | min width 112; disabled while running |
| Secondary action buttons | `QPushButton[role="secondary"]` | export/CSV/driverlogs/BULK; disabled until result |
| Help button | `QPushButton[role="ghost"]` or `QToolButton` | opens `HelpDialog` |
| `ttk.Notebook` | `QTabWidget` | Preview / Report only; assign moves to dialog |
| `ttk.Treeview` main | `QTableView` + `ClaimTableModel` + `ClaimFilterProxyModel` | 9 columns; status tint/pill; virtualised |
| Treeview tags | `BackgroundRole` + `StatusDelegate` | row tint; status pill; selection readable |
| `tk.Text` report | `QPlainTextEdit` | read-only, Consolas 12, copyable, no rich text |
| Assign tree + combo | `AssignDriverDialog` (`QTableView`/`QListView` + `QComboBox`) | modal; candidates from report |
| `ttk.Combobox` | `QComboBox` | inside dialog; read-only |
| Status dot Canvas | `StatusDot(QWidget)` | 9 px `paintEvent`; idle/running/success/error |
| Separators `tk.Frame` | `QFrame` HLine / QSS border | 1 px |
| `tk.StringVar`/`BooleanVar` | `AppState` dataclass | no widget-bound logic; one source of truth |
| `filedialog` | `QFileDialog` | native by default; same filters/titles |
| `messagebox` | `messages.py` wrappers | translate; no hardcoded titles |
| Help `messagebox.showinfo` | `HelpDialog` | `QTextBrowser`; source `help_body` |
| `after(0, ...)` | Qt signals | worker → main thread |
| `threading.Thread` | `QThread` + `JobWorker` | no widgets in worker |
| `PhotoImage` | `QIcon`/`QPixmap` | multi-size/2x; app icon `.ico` |
| `_MEIPASS` | same `sys._MEIPASS` | use `QIcon`/`QFile`; test one-file |
| DPI ctypes | Qt high-DPI | no manual DPI calls; test 100–200 % |
| ttk theme engine | `theme/qss.py` + `QPalette` | generated QSS; runtime switch |
| `status_of` in `ui.py` | `app/status.py` | shared by Tk and Qt; no Tk import |

---

## 7. QSS plan

### 7.1 Static `.qss` vs generated QSS

**Recommendation: generate QSS from Python tokens.** Qt style sheets have no variables, and two complete palettes would duplicate every selector and value in static files. A generated stylesheet keeps `theme/tokens.py` as the single source, lets the theme switch at runtime, and can be tested for unresolved tokens. Use a small `build_qss(theme) -> str` function in `theme/qss.py`; optionally store the static structure in a `.qss` template with `{{token}}` placeholders, but keep the values in Python.

- `theme/tokens.py`: `PALETTES`, `STATUS_TINTS`, `METRICS`, `FONTS`, `THEMES`.
- `theme/qss.py`: `build_qss(theme)` → one complete stylesheet; `ThemeManager.apply(name)`.
- `tests_qt/test_theme.py`: assert both themes produce no `{{…}}` placeholders and include every required selector.

### 7.2 Selector map

| Selector | Purpose |
|---|---|
| `QMainWindow`, `QWidget#Root` | base background/text/font |
| `QFrame#TopBar`, `QFrame#Sidebar`, `QFrame#Card`, `QFrame#DetailDrawer` | surfaces and 1 px borders |
| `QLabel#PageTitle`, `QLabel#Subtitle`, `QLabel#SectionTitle`, `QLabel#Hint` | type scale |
| `QPushButton` / `QPushButton[role="primary"]` / `[role="secondary"]` / `[role="danger"]` | button roles, hover/pressed/focus/disabled |
| `QToolButton` | icon buttons |
| `QLineEdit`, `QComboBox`, `QSpinBox` | inputs, focus ring, disabled |
| `QCheckBox::indicator`, `QRadioButton::indicator` | 18/17 px boxes, checked state |
| `QTableView` | background, border, selection, alternate rows |
| `QHeaderView::section` | header surface-alt, 10,8 padding, bottom border |
| `QTableView::item` | padding/selection; row tint is model-driven |
| `QTabWidget::pane`, `QTabBar::tab` | tabs, selected accent, hover |
| `QScrollBar:vertical` / `:horizontal` | 10 px slim scrollbars |
| `QStatusBar`, `QStatusBar::item` | status bar surface + top border |
| `QToolTip` | surface-alt, border, 10,6 padding |
| `QDialog`, `QMessageBox` | dialog surface, 18 px margin, buttons |
| `QProgressBar` | 6 px, accent, indeterminate |
| `QSplitter::handle` | 1 px border/6 px hit area |

### 7.3 States

| State | QSS treatment |
|---|---|
| Normal | surface / text / 1 px border |
| Hover | surface_alt background; accent border on buttons; no transition |
| Pressed | selection tint or accent_pressed |
| Focus | 1–2 px accent border; visible focus ring; never remove focus |
| Disabled | 45 % opacity or muted foreground; no hover |
| Checked | accent fill, white/dark check mark |
| Selected row | selection background; text remains text colour; status pill remains visible |
| Invalid/error | danger border + error text; only for validation, not status rows |

### 7.4 Dynamic properties

Use Qt dynamic properties rather than per-widget style sheets:

- `role="primary"|"secondary"|"danger"|"ghost"`
- `state="idle"|"working"|"done"|"error"`
- `density="main"|"compact"`
- `status="OK"|...` only if a widget needs it; the table uses model roles/delegate.

After changing a property, call `style().unpolish(widget)` and `style().polish(widget)` so QSS re-evaluates. This is especially relevant for status chips and buttons.

### 7.5 Runtime theme switch

`ThemeManager.apply(name)`:

1. Resolve tokens for `dark`/`light`.
2. Build QSS and call `QApplication.setStyleSheet(qss)`.
3. Update `QPalette` for native controls, tooltips, menus, scrollbars.
4. Update icons (moon/sun, status dot).
5. Call `dataChanged` on the table model so row tints/pills repaint.
6. Update DWM title bar best-effort.
7. If a QSettings store exists, save the theme; otherwise keep session-only.

Apply the saved theme **before** `MainWindow.show()` to avoid a dark-first flash (the WPF reference explicitly warns about this).

### 7.6 Fonts and status styling

- `QFont("Segoe UI Variable Text", 10)` with fallback `Segoe UI`, `Arial`; check `QFontDatabase.families()`.
- Base 13 px / Medium; page title 20 / SemiBold; section 12 / SemiBold; hint 11; mono Consolas 12.
- Use `QFont` for weights (Medium/SemiBold) where QSS `font-weight` numeric support is inconsistent; use QSS for sizes/families.
- Status pill: `StatusDelegate` paints a 20–22 px-high rounded rect with the status tint, 1 px border, text centered; row background is model-driven. Do not try to style per-row statuses in QSS.
- Contrast decision: SelfishNet’s white-on-`#4C8DFF` is about **3.2:1**, below 4.5:1 for normal text. Proposed Qt uses `on_accent=#0B1020` on dark accent (Monmusu’s value) and white on light `#0969DA` if contrast passes; verify with a contrast checker. This is an intentional accessibility improvement, not a palette change.

### 7.7 QSS limitations to accept

- No CSS variables; generated QSS solves it.
- No box-shadow/glow; flat design already says no shadows.
- Per-row styling is not QSS; use model roles/delegate.
- Native `QFileDialog` does not follow app QSS; accept OS theme or use non-native dialogs (worse UX).
- `QComboBox` popup and `QToolTip` need explicit sub-control styling.
- Style sheets can be expensive if re-applied per widget; apply once per theme.
- High-DPI font metrics can differ from WPF; use layouts and elide text.

### 7.8 Accessibility

- Visible focus ring for every focusable control, including table and buttons.
- Keyboard navigation: Tab order left→right/top→bottom; arrow keys in table; Enter opens Assign dialog; Escape closes dialogs.
- Suggested shortcuts: `Ctrl+O` claim, `Ctrl+Shift+O` sources, `Ctrl+R` process, `Ctrl+E` export, `Ctrl+Shift+E` CSV, `Ctrl+D` driverlogs, `Ctrl+B` BULK, `F1` help. Current app has none.
- Status is text + colour; tooltips explain `REVISAR`, `SUGERIDO`, etc.
- Minimum contrast: fix primary accent text; status pills use `text`/semantic colours; test with Windows High Contrast? Not required, but do not break.
- `setAccessibleName`/`setAccessibleDescription` on icon-only theme/language buttons and status dot.
- Table headers and rows should expose text; screen-reader smoke test with Narrator.

---

## 8. Table and delegate plan

### 8.1 Model

`ClaimTableModel(QAbstractTableModel)` wraps `list[dict]` from `result["claim"]["rows"]`.

Columns:

| Index | Header | Width | Alignment | Display |
|---:|---|---:|---|---|
| 0 | # | 48 | center | `row` |
| 1 | Date | 100 | left | `date_text` |
| 2 | Member | 220 (stretch, min 160) | left | `member_raw` or `member` |
| 3 | Trip | 130 (stretch, min 110) | left | `trip` |
| 4 | Driver | 64 | center | `driver` |
| 5 | Milage | 70 | right | number, 2 decimals max |
| 6 | PU | 64 | center | `HH:MM` |
| 7 | DropOff | 78 | center | `HH:MM` |
| 8 | Status | 120 | center | status pill |

Required roles:
- `DisplayRole`: formatted text.
- `TextAlignmentRole`: left/center/right.
- `BackgroundRole`: status tint (theme-aware); selected state handled by the view.
- `ForegroundRole`: default text; status pill paints its own.
- `ToolTipRole`: full member/trip/status explanation.
- `RawRowRole`: the row dict.
- `StatusRole`: `status_of(row)`.
- `SortRole`: numeric for Driver/Milage/row; text for Date/Member/Trip; status order by severity (e.g. ELEGIR, REVISAR, SUGERIDO, …).

### 8.2 Filter proxy

`ClaimFilterProxyModel(QSortFilterProxyModel)`:

- `setSourceModel(model)`.
- `filterAcceptsRow`: match search text against Member, Trip, Driver; match status filter (one of 9 or “all”).
- `lessThan`: numeric comparison for driver/milage/row; case-insensitive text; stable original row index as tiebreaker.
- `setSortRole`/custom `SortRole`.
- Expose `status_counts` for summary chips.

UI:
- Search `QLineEdit` with placeholder “Search member, trip, driver…”.
- Status filter `QComboBox` or clickable summary chips. Recommend both: chips set the combo; combo is the explicit filter.
- “Clear filters” action.

### 8.3 Delegate

`StatusDelegate(QStyledItemDelegate)` for column 8:

- Paint background from `BackgroundRole` (or transparent), then a pill:
  - rect with 8–10 px radius;
  - status tint fill; 1 px border; `text`/semantic foreground;
  - centered label; elide if needed.
- Respect selection: if selected, use selection background and keep pill readable.
- Do not create a widget per row; paint only.

Optional `TimeDelegate` not needed; format times in the model. Numeric alignment via `TextAlignmentRole`; no editor.

### 8.4 View settings

- `setSelectionBehavior(SelectRows)`, `setSelectionMode(SingleSelection)`.
- `setEditTriggers(NoEditTriggers)`; assign through dialog.
- `verticalHeader().setVisible(False)`.
- `verticalHeader().setDefaultSectionSize(34)`; header height 32.
- `setShowGrid(False)`; draw 1 px bottom separator in delegate/model or use horizontal grid with palette; choose delegate bottom border for theme control.
- `setAlternatingRowColors(False)`; status tint is the semantic background. (If status tints are too strong for whole rows, use a subtle tint + pill; keep one system.)
- `setWordWrap(False)`, `setTextElideMode(Qt.ElideRight)`.
- `horizontalHeader().setStretchLastSection(False)`; Member/Trip stretch; others Fixed/Interactive.
- No frozen columns; 9 columns fit at 1280 with the bottom-drawer layout; horizontal scroll at minimum width.
- Sorting enabled; default sort from engine (`date`, driver, row); preserve stable order.

### 8.5 Selection and reprocessing

- Store the selected key `(date, trip)`.
- On new `result`, rebuild model, restore selection if the key still exists; otherwise clear.
- `QItemSelectionModel` updates the detail drawer.
- While a job runs, disable the table; do not clear the old result until success (or show busy overlay).

### 8.6 Assignment flow

- Double-click an `ELEGIR`/`SUGERIDO` row, or press `Assign driver` in the drawer → `AssignDriverDialog`.
- Dialog candidates from `report["driver_candidates"][(date, county)]`.
- `QTableView` columns: #, Name, Trips, License, VIN, County; sorting by trips/name.
- Search/filter; “only free today” checkbox.
- Assign sets `driver/license/vin`, `flag=""`; Clear sets blank and `elegir`.
- Dialog returns accepted; main window updates model row and derived counts; no engine recompute.
- If the user assigns a candidate from another county, the dialog should show only same-county candidates by default; the current engine candidate map already does.
- Inline editing rejected: the table is read-only, avoids accidental edits, and reuses the existing candidate data.

### 8.7 Performance

- Expected batch: 81 rows (current), maybe a few hundred. `QTableView` virtualization is more than enough; 5,000 rows should remain responsive.
- Avoid `setIndexWidget`; use delegate painting.
- Avoid `ResizeToContents` with many rows; fixed/stretch widths.
- Status counts computed once per result; proxy filtering is cheap.
- Test with 1,000 and 5,000 synthetic rows; measure sort/filter time.

---

## 9. Threading and responsiveness

### 9.1 Current behaviour

- `ui.run` validates, pre-scans sources on the main thread, disables action buttons, starts `threading.Thread(target=self._work)`.
- `_work` calls `run_job` and posts `_finish` via `root.after(0, ...)`.
- `run_job` has no progress or cancellation callback; it returns one result dict.

### 9.2 Proposed Qt model

**Use a single `QThread` + `JobWorker(QObject)`** rather than a thread pool; the app runs one job at a time, and lifecycle/cleanup is simpler.

```
MainWindow.run()
  validate paths
  optional scan_sources pre-check (fast, main thread)
  if pending job: return
  disable inputs/actions; show busy overlay/progress
  thread = QThread(self)
  worker = JobWorker(args)
  worker.moveToThread(thread)
  thread.started.connect(worker.run)
  worker.finished.connect(self.on_finished)
  worker.failed.connect(self.on_failed)
  worker.finished.connect(thread.quit)
  worker.failed.connect(thread.quit)
  thread.finished.connect(worker.deleteLater)
  thread.finished.connect(thread.deleteLater)
  thread.start()
```

Signals:
- `finished(dict)` — engine result (including `{"error": ...}` semantics).
- `failed(str)` — unexpected exception; UI shows error.
- `started()` / `finished()` — enable/disable, status dot.
- No `progress` signal until the engine exposes progress; use indeterminate progress.

### 9.3 Cancellation

There is **no safe cancellation point inside `run_job`** today. It is a synchronous sequence of scan/parse/fill; it does not check a cancel flag. Therefore:

- Do not call `QThread.terminate()`; it can corrupt Python state, openpyxl/docx objects and output files.
- Do not offer a “Cancel” button during processing. Offer “Process” disabled and a busy overlay; the user waits.
- `closeEvent`: if a job is running, show “A job is running; wait for it to finish before closing.” and ignore the close (or hide the window and close when finished; choose ignore for simplicity).
- If cancellation becomes a requirement, add an optional `cancel_event`/progress callback to `run_job` in a separate engine task (out of scope; must not break CLI/tests).
- Double-start guard: `self._thread is not None`; disable Process and all input fields.

### 9.4 Pre-scan

The current `scan_sources` no-trip warning is fast (header-only classification). Keep it on the main thread before launching the worker, to preserve the exact Proceed/Cancel flow. If it becomes slow, move it into the worker and add a `needs_confirmation` signal; that is a later optimization, not required for 81 rows.

### 9.5 Thread-safety rules

- Worker only calls pure engine functions; no QWidget/QPixmap/QFileDialog access.
- Worker returns a plain dict/list; the main thread owns models/widgets.
- Do not share `claim["rows"]` with the worker while the UI edits it; the UI is disabled during the job.
- Use `Qt.QueuedConnection` implicitly for cross-thread signals.
- Catch all exceptions in the worker and emit a string; never let a thread die silently.

---

## 10. Packaging and distribution

### 10.1 Verified platform facts

| Fact | Value | Source |
|---|---|---|
| PySide6 version | 6.12.0 (latest verified) | PyPI |
| Python requirement | `>=3.10,<3.16`; Python 3.14 supported | PyPI classifiers/metadata |
| Windows wheel | `cp310-abi3-win_amd64`, **78.3 MB** compressed | PyPI |
| Qt Windows target | Windows 10 1809+ x86_64, Windows 11 | Qt 6.12 docs |
| Windows 10 horizon | Qt 6.12 is the **last** Qt release supporting Windows 10 | Qt docs |
| PyInstaller | 6.22.3 with PySide6 hooks; hooks-contrib 2026.9 | local installation |
| Current app exe | 32-bit, 16,595,921 bytes, 2.4.0.0 | local build |
| Current startup/size | ~15.8 MB, ~2 s bootstrap one-file | current docs/measurements |

### 10.2 Dependencies

- New UI runtime: **`PySide6-Essentials==6.12.0`** (pulls `shiboken6`). Do **not** use the `PySide6` meta-package; it also pulls Addons, WebEngine and PDF.
- New UI build: `requirements-ui-build.txt` = `-r requirements-ui.txt` + `pyinstaller==6.22.3`.
- Keep `requirements.txt` for the engine/CLI; the CLI must not import PySide6.
- No `qfluentwidgets` (GPLv3) and no PyQt6 (GPL/commercial). Hand-written QSS + standard widgets only.

**Licensing position:** PySide6 6.12 metadata declares `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`. Use it under
**LGPLv3**. Keep Qt/PySide6 dynamically linked (the PyInstaller one-file still extracts DLLs), include the LGPL license
text/notices, do not statically link Qt, and do not modify Qt itself. If the app is distributed outside the owner’s
organization, get a legal review and document how users can replace the LGPL libraries. This is a distribution
obligation, not a reason to choose PyQt6 or a GPL-only widget pack.

### 10.3 PyInstaller spec

Fork the current spec; do not overwrite it:

`Facturacion MTM Qt.spec`:
- `Analysis(['run_app_qt.py'], ...)`
- datas: `assets/icon.png`, `assets/icon.ico`, `assets/ui`, `app/assets/bulk_template.xlsx`, and any new SVG/2x icons.
- `hiddenimports=['docx']`; PySide6 hooks handle Qt modules.
- `excludes`: keep `numpy`, `pandas`, `matplotlib`, `scipy`, `PIL`, `Pillow`; add unused Qt modules:
  - `PySide6.QtWebEngine*`, `PySide6.QtWebChannel`, `PySide6.QtWebSockets`
  - `PySide6.QtQml`, `PySide6.QtQuick*`
  - `PySide6.QtMultimedia*`, `PySide6.Qt3D*`, `PySide6.QtCharts`, `PySide6.QtDataVisualization`
  - `PySide6.QtPdf*`, `PySide6.QtSql`, `PySide6.QtHelp`, `PySide6.QtDesigner`, `PySide6.QtUiTools`
  - `PySide6.QtTest` in runtime; keep `QtCore`, `QtGui`, `QtWidgets`, and `QtSvg` only if SVG icons are used.
  - Do not exclude modules before the spike proves the UI does not import them.
- `EXE(...)`: `name='Facturacion MTM Qt'`, `icon='assets/icon.ico'`, `version='version_info.txt'`, `console=False`, `upx=False` (UPX can break Qt DLLs), one-file.
- Qt plugins: let PyInstaller collect `platforms/qwindows.dll`, `styles/qmodernwindowsstyle.dll`, image/icon plugins; remove qml/quick plugins through excludes and verify.
- `QT_QPA_PLATFORM_PLUGIN_PATH` is handled by PyInstaller; do not hardcode `_MEIPASS` paths.
- Test on a clean Windows 10 1809+ 64-bit VM and Windows 11; no Python installed.

### 10.4 One-file vs one-folder

| Criterion | One-file | One-folder |
|---|---|---|
| Distribution | single `.exe`, matches current habit | copy a folder / zip |
| Size | likely **70–120 MB** after excludes | likely **180–300 MB** uncompressed |
| Startup | extracts Qt DLL/plugins to `%TEMP%`; likely **3–6 s** | likely **1–2 s** |
| AV/SmartScreen | higher heuristic risk; unsigned | lower extraction risk, still unsigned |
| Debugging | harder; temp extraction | easier |
| Update | replace one file | replace folder |
| Recommendation | **first attempt**, preserve single-exe requirement | fallback if startup >5 s or size >120 MB |

Measure both in the spike; do not promise a size before measurement. The current 15.8 MB → expected 5–8× increase is a user-visible change.

### 10.5 64-bit-only consequences

- New Qt build runs on **Windows 10 64-bit 1809+ / Windows 11**. It will not run on 32-bit Windows 10.
- Keep the current 2.4.0.0 **32-bit** exe as the rollback for 32-bit users; label it clearly and freeze it.
- Do not overwrite the current root exe until the Qt build passes parity. Build `Facturacion MTM Qt.exe` (or `dist_qt/`) separately.
- Communication: “This version requires 64-bit Windows 10/11; 32-bit users must stay on 2.4.0.0 or upgrade Windows.”
- Qt 6.12 is the last Windows 10 release; if Windows 10 support must outlive Qt 6.12, plan a Windows 11-only future or a different UI stack.

### 10.6 Build script and CLI

- `build_qt.ps1` uses the **64-bit** Python 3.14.6, `requirements-ui-build.txt`, `Facturacion MTM Qt.spec`, `dist_qt`/`build_qt`; accepts `-Python`, `-Dist`, `-Work`, `-NoCopy` like the current script.
- Keep `build.ps1` and `Facturacion MTM.spec` for the 32-bit Tk rollback.
- `run_app.py --cli` remains unchanged and must not import PySide6; test it in the Qt build environment.
- `run_app_qt.py` is GUI-only; it imports `QApplication` and the Qt shell, then `run_app.main`/engine only when needed.

### 10.7 Signing, icon, version

- Icon: use `assets/icon.ico` for the executable/window; `QApplication.setWindowIcon(QIcon(...))`; keep `assets/icon.png` for in-app branding.
- Version: bump to **3.0.0.0** for the Qt release; keep 2.4.0.0 for the Tk rollback.
- `--windowed`/`console=False`; no stdout in the windowed build.
- Code signing remains deferred; SmartScreen “Unknown publisher” is expected. A one-file Qt build may also trigger AV heuristics because it extracts Qt DLLs to `%TEMP%`; test and document. If external distribution, budget OV/EV/Azure Trusted Signing.
- No auto-update in this scope.

### 10.8 Rollback

- Keep the 32-bit `Facturacion MTM.exe` and the Tk source/build until the Qt build is accepted.
- Run both UIs in parallel on the same test data for at least one full batch; compare Excel/BULK/driverlog outputs and reports.
- Cut over by renaming the Qt exe; keep the old build in a labeled `rollback/` folder for one release cycle.
- Remove the Tk UI only after the owner signs off and no 32-bit users remain.

---

## 11. Testing and parity

### 11.1 Engine tests

The existing **39** `unittest` tests must pass unchanged. They are the real business gate:

- `test_pipeline_smoke`, `test_writer`, `test_notes`, `test_facturado`, `test_allowed`, `test_balance`, `test_pickup`, `test_status`, `test_strings`.
- No engine file is edited for the UI migration.
- `selftest.py` remains the September accuracy benchmark (`first_row_B` 46/70 at the time of this analysis).

### 11.2 UI tests

Use **`pytest-qt`** (dev-only) with `pytest`; keep it in `requirements-dev.txt`, not runtime. Run with `QT_QPA_PLATFORM=offscreen` for CI where possible; use a Windows runner for native file dialogs/DPI.

| Test | What it proves |
|---|---|
| `test_window_opens` | `MainWindow` constructs, QSS applies, no missing plugin |
| `test_process_populates_table` | `run_job` wiring + model rows/columns/status |
| `test_search_filters` | proxy search across member/trip/driver |
| `test_status_filter` | each status chip/combo filters correctly |
| `test_theme_switch` | dark/light QSS changes without restart, state preserved |
| `test_language_switch` | labels/headers/status/report switch, values preserved |
| `test_assign_dialog` | candidates, assign, clear, double-click, validation |
| `test_export_wiring` | save dialog path → `write_output`; file exists; source guard |
| `test_csv_wiring` | `write_report_csv`; source guard |
| `test_driverlogs_bulk_wiring` | engine calls, result/report lines |
| `test_error_paths` | missing files, invalid claim, engine error, locked output |
| `test_double_start_and_close` | no concurrent jobs; close while running |
| `test_selection_preserved` | selection restored after reprocess |
| `test_many_rows` | 1,000/5,000 rows sort/filter performance |
| `test_engine_boundary` | UI calls only the allowed engine functions; no parser/filler imports in widgets |

### 11.3 Output parity

- Use `tests/fixtures.py` and the existing `test_pipeline_smoke` pattern.
- Run the engine once; load the Qt shell with the result; export via the Qt action to a temp file; compare cell values with a direct `write_output` run.
- BULK and driverlogs: call the Qt action, compare generated files/cell text to the engine baseline.
- Do not use `data/base/`; use synthetic fixtures or `data/test/`.
- The engine already has the golden behavior; the UI must not alter rows except explicit user assignments.

### 11.4 Manual visual checklist

| Condition | Check |
|---|---|
| Themes | dark/light; no hardcoded color; status tints/pills correct |
| Languages | ES/EN; no clipped labels; table headers swap |
| DPI | 100 %, 125 %, 150 %, 200 %; text crisp; no overlap |
| Window sizes | 1280×800, 1000×620 minimum, maximized, narrow |
| Empty state | before processing; no blank table |
| Error state | missing claim/sources, engine error, locked file |
| Long text | long member/trip names elide with tooltip |
| Many rows | 81, 1,000; scroll/sort/filter smooth |
| Keyboard | Tab order, focus rings, Enter/Escape, shortcuts |
| Screen reader | Narrator reads labels/status/table headers |
| High contrast | OS high-contrast mode does not make text invisible |

### 11.5 No screenshot tests initially

`QWidget.grab()` screenshot tests are fragile across DPI/themes. Start with behavior tests and the manual matrix; add visual regression only if the design stabilizes and a stable Windows runner exists.

---

## 12. Risk table

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **32-bit loss** | Certain (owner decision) | High for 32-bit users | Freeze 2.4.0.0; communicate Windows 10/11 64-bit requirement; keep rollback |
| **Qt 6.12 is last Windows 10** | Certain | Medium/long-term | Pin 6.12 LTS; plan Windows 11-only future; document |
| **Package size/startup** | High | Medium | Essentials only; excludes; one-file spike; one-folder fallback; measure |
| **Qt plugin missing on clean VM** | Medium | High | PyInstaller hooks; clean VM test; explicit plugin smoke |
| **LGPL compliance** | Low likelihood / high impact | High if external | Legal review; LGPLv3 notices; dynamic linking; no GPL-only deps; no PyQt6/qfluentwidgets |
| **Visual fidelity gap** | Medium | Medium | QSS/delegate prototype; accept Qt popup/text differences; no custom title frame |
| **Table/delegate complexity** | Medium | Medium | Model/view, one status delegate, 9 columns; no per-row widgets |
| **Threading bugs/frozen UI** | Medium | High | QThread worker, signals only, no widget access; disable close/start; no terminate |
| **Billing regression** | Medium | High | Engine untouched; 39 tests; output parity; parallel run |
| **Dual UI maintenance** | High | Medium | Time-box transition; freeze Tk; cutover date; no feature work in Tk |
| **Python/PySide6 compatibility** | Low now | High | Pin 3.14.6 + 6.12.0; spike; lockfile/requirements |
| **Accessibility/contrast** | Medium | Medium | Focus rings; contrast-safe accent text; text statuses; Narrator smoke |
| **SmartScreen/AV** | Medium | Medium | Test unsigned; document; code signing later; one-folder fallback |
| **Settings/persistence** | Low | Low | No config today; either keep session defaults or one QSettings store, never two |
| **Icon/DPI assets** | Low | Low | SVG or 1x/2x PNG; QIcon; test 200 % |

---

## 13. Phased plan and estimate

**Assumption:** one developer familiar with Python and desktop UI; PySide6/QSS is new or lightly used. Add 20–30 % if it is the first Qt project. Days are engineering days, not calendar days.

| Phase | Deliverable | Exit criteria | No AI | With AI |
|---|---|---|---:|---:|
| 0. Spike | Throwaway `spikes/qt_shell` with shell + 81-row table + dark QSS + one-file build | PySide6 runs on 3.14.6 64-bit; clean VM starts; size/startup measured; table readable at 100–200 % | 2–3 | 1–2 |
| 1. Design system + shell | `ui_qt/theme`, `MainWindow`, top bar, sidebar, status bar, theme/lang | Tokens/QSS complete; dark/light switch; no hardcoded colors; 100–200 % DPI | 3–4 | 2–3 |
| 2. Results table | `ClaimTableModel`, proxy, delegate, summary chips, search/status filter | 81 rows correct; status pills; sort/filter; 1,000-row test | 3–5 | 2–3 |
| 3. Dialogs + detail | `AssignDriverDialog`, help, messages, detail drawer | Assign/clear parity; help text; error/confirm paths | 2–3 | 1–2 |
| 4. Engine wiring + threading | `JobWorker`, process, export/CSV/driverlogs/BULK actions | Full flow with fixtures; no UI freeze; no cross-thread access; errors handled | 2–3 | 1–2 |
| 5. Packaging | `requirements-ui*`, `Facturacion MTM Qt.spec`, `build_qt.ps1` | One-file/folder measured; clean VM; version/icon/windowed; CLI unaffected | 2–4 | 1–2 |
| 6. QA + parallel run | `pytest-qt` suite, output parity, visual matrix, 32-bit rollback | 39 engine tests + UI tests green; Excel/BULK/DOCX identical; DPI/language/themes checked | 4–6 | 2–4 |
| 7. Cutover | Release notes, new exe name, old exe preserved | Owner sign-off; rollback documented; 64-bit communication | 1–2 | 1 |
| **Total** | | | **19–30** | **11–19** |

Separate view:

- **UI only** (phases 1–4): **10–15 days** no AI; **6–10 days** with AI.
- **UI + packaging + QA + cutover** (all): **18–29 days** no AI; **11–18 days** with AI.

The spike is the gate; if it fails on size/startup/clean VM, stop before phases 1–7.

---

## 14. Go/no-go and open questions

### 14.1 Recommendation

**Conditional GO for PySide6.** The technical path is viable and the UI is small, but the decision is only justified because the owner has accepted **64-bit-only** and wants a materially better visual/data-grid experience. The engine is not the risk; packaging, 64-bit user impact, LGPL, dual maintenance, and visual parity are.

**No-go** if any of these is true:

- 32-bit Windows support is a hard requirement.
- External distribution cannot accept LGPLv3 or legal review.
- The budget is under ~2 weeks and the visual gain is not important.
- The only goal is slightly nicer colors/rounding; the current tokens already match SelfishNet, and Tk/ttk polish is cheaper.

### 14.2 Cheapest path to 80–90 % of the visual result

1. **Keep Tkinter** and improve `app/uikit` + `ttk` (stronger status pills via images, better spacing, focus states, custom Canvas card borders). Lowest risk; 32-bit remains; no new runtime package.
2. **`ttkbootstrap` or CustomTkinter** (MIT-style) for chrome/theme; still uses `ttk.Treeview` for the table, so the data grid remains the visual ceiling. Verify 32-bit/Pillow support and license.
3. **PySide6** only when the table, high-DPI rendering, rounded surfaces, and native desktop feel are worth the 64-bit/packaging/LGPL cost.

### 14.3 When to choose each option

| Option | Choose when |
|---|---|
| **Keep Tkinter / polish uikit** | 32-bit required; minimal risk/time; current workflow is acceptable |
| **ttkbootstrap / CustomTkinter** | 32-bit required; want better chrome without a full rewrite; table can stay ttk |
| **PySide6** | 64-bit-only accepted; table/visual quality matters; can afford 2–4 weeks + QA + LGPL review |
| **C#/WPF** | The app is becoming a long-lived Windows-only product with a C# team, native integrations, and a willingness to rewrite the engine/UI boundary; overkill for one form |

### 14.4 What to do first, regardless

1. Freeze the engine and capture golden Excel/BULK/DOCX outputs from the current 2.4.0.0 build (they already exist; keep them).
2. Run the **2–3 day PySide6 spike** on Python 3.14.6 64-bit with test data only.
3. Measure one-file size, startup, clean-VM launch, 100/125/150/200 % DPI, and 81/1,000/5,000 rows.
4. Resolve LGPL/distribution and 64-bit user communication before writing the shell.
5. Only then approve the design and write the implementation plan.

### 14.5 Open questions for the owner

| # | Question | Default assumption / impact |
|---:|---|---|
| 1 | Is 32-bit Windows truly no longer required? | Owner says 64-bit-only. If any user has 32-bit Windows 10, they cannot run the Qt build. |
| 2 | Is the app internal-only or distributed externally? | Affects LGPL notices, legal review, code signing, support. |
| 3 | One-file or one-folder? | One-file first for parity; one-folder if startup/size fails. |
| 4 | Pin Python 3.14.6 or use 3.13 for Qt? | PySide6 6.12 supports 3.14; pin 3.14.6 unless the spike finds a packaging issue. |
| 5 | Parallel `app/ui_qt` or immediate replacement? | Parallel with `run_app_qt.py`; keep Tk rollback; cut over after parity. |
| 6 | Persist theme/language/last folders? | No config today; smallest is session-only. If added, use one `QSettings` store, not two. |
| 7 | Assignment dialog or inline editor? | Dialog; table read-only; safer and simpler. |
| 8 | Keep Report as a tab or a lower panel? | Tab is lower risk; bottom panel is possible but more layout work. |
| 9 | Dark native title bar via DWM? | Best effort with ctypes; otherwise native light title bar. |
| 10 | Keep PNG icons or move to SVG? | SVG or 1×/2× PNG; decide icon licensing/source. |
| 11 | Windows 10 horizon? | Qt 6.12 is the last Windows 10 release; pin LTS; plan Windows 11-only future. |
| 12 | New features soon (auto-update, Outlook, API, signing)? | They may change navigation/settings and should be considered before the shell is frozen. |

### 14.6 Acceptance criteria for the next design/plan

- Every widget/flow in `app/ui.py` maps to a Qt class (this document does).
- Every palette/font/spacing/radius has a source and target (this document does).
- 64-bit-only impact is explicitly accepted (owner).
- LGPL position is explicit: PySide6 LGPLv3; no PyQt6/qfluentwidgets; notices/legal review for external distribution.
- Table model/delegate/filter strategy is chosen (this document).
- Threading/cancellation is explicit: no safe in-job cancellation; no `terminate`.
- Packaging size/startup and rollback are covered.
- Estimate includes testing, parity and parallel running.
- Recommendation is concrete (conditional GO).

---

## Appendix A — Evidence and verification performed

- Read `README.md`, `docs/NOTES.md`, `docs/PORTABILITY.md`, `app/ui.py`, `app/strings.py`, `app/uikit/*`, `app/pipeline.py`, `app/report.py`, `app/writer.py`, `app/bulk.py`, `app/driverlogs.py`, `run_app.py`, `build.ps1`, `Facturacion MTM.spec`, `requirements.txt`, and the 39-test suite.
- Read `SelfishNet v2/VISUAL_DESIGN_SYSTEM.md`, its Dark/Light/Controls/MainWindow/AdapterWindow XAML.
- Read `monmusu-paradox-3-translation` Dark/Styles/MainWindow XAML.
- Queried PyPI for `PySide6` and `PySide6-Essentials`: 6.12.0, Python `<3.16,>=3.10`, `cp310-abi3-win_amd64` wheel 78.3 MB, LGPL-3.0/GPL-2.0/GPL-3.0.
- Read Qt 6.12 Windows platform docs: Windows 10 1809+ x86_64 and Windows 11; last Qt release supporting Windows 10.
- Confirmed PyInstaller 6.22.3 PySide6 hooks exist locally; hooks-contrib 2026.9.
- Did **not** install PySide6; did **not** edit app/engine/tests; did **not** touch `data/base/`.

## Appendix B — Source references

| Reference | Why it matters |
|---|---|
| `app/ui.py:63-97` | `App` state and initialization |
| `app/ui.py:100-218` | shell, inputs, options, actions, tabs, status |
| `app/ui.py:220-259` | file rows and assign tab |
| `app/ui.py:261-347` | theme, icons, i18n, retranslate |
| `app/ui.py:383-443` | run/thread/finish |
| `app/ui.py:445-575` | render, assign, clear |
| `app/ui.py:577-665` | export/CSV/driverlogs/BULK |
| `app/strings.py:1-188` | all ES/EN text |
| `app/uikit/tokens.py:9-77` | current palette, status tints, metrics, fonts |
| `app/uikit/theme.py:76-160` | ttk styles and status tags |
| `app/pipeline.py:170-239` | `run_job` result shape and allowed inputs |
| `app/report.py` | report text/CSV |
| `tests/` | 39 tests and synthetic fixtures |
| `..\SelfishNet v2\VISUAL_DESIGN_SYSTEM.md:183-314` | tokens, type, radii, spacing, metrics, motion |
| `..\SelfishNet v2\...\Controls.xaml:5-316` | button/input/grid/scrollbar/tooltip styles |
| `..\SelfishNet v2\...\MainWindow.xaml:25-250` | five-row shell, toolbar/status/overlay |
| `..\SelfishNet v2\...\AdapterWindow.xaml:1-65` | modal dialog pattern |
| `..\monmusu...\Styles.xaml:3-407` | dense cards, buttons, combo, 28 px grid |
| `..\monmusu...\MainWindow.xaml:33-280` | 3-column dense layout, summary strip, search/filter |
