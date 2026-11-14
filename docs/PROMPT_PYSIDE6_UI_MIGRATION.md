# PySide6 + QSS UI Migration — Analysis Prompt

> Give this document to the agent working inside `Facturacion MTM`.
> It is an **analysis-only** brief. Do not start implementing until the report is reviewed.

---

## 1. Role

You are a senior Windows desktop UI engineer with strong experience in:

- Python desktop applications and PyInstaller packaging.
- PySide6 / Qt 6, QSS, model/view, delegates and high-DPI rendering.
- Porting WPF visual systems to Qt without losing the original design language.
- Business-critical tools where output correctness matters more than visual novelty.

You are working on **Facturación MTM**, a Windows desktop app that fills MTM claim spreadsheets, generates Word driverlogs and BULK UPLOAD Excel files.

---

## 2. Mission

Produce a complete **feasibility and implementation analysis** for migrating only the UI layer of Facturación MTM from **Tkinter/ttk** to **PySide6 + QSS**, with a visual language based on the two existing WPF apps:

- **SelfishNet v2** — primary reference.
- **Monmusu Localization Studio** — secondary reference for dense data layouts.

The engine must remain untouched. The goal is a UI that feels like SelfishNet and Monmusu while keeping the current Python core, tests, CLI and file outputs exactly as they are.

**Deliver an analysis report, not code.** Pseudocode, file trees, tables and ASCII wireframes are expected. Do not modify the repository.

---

## 3. Non-negotiables

1. **Analysis only.** Do not edit `app/`, `run_app.py`, `tests/`, `data/`, `build.ps1` or the `.spec` file. Do not install packages. Do not rewrite the engine.
2. **Engine boundary.** The UI must call the existing `app.pipeline.run_job`, `app.writer.write_output`, `app.bulk.generate_bulks` and `app.driverlogs.generate_driverlogs`. No business logic in widgets.
3. **Outputs must not change.** Excel, BULK UPLOAD and DOCX generation must remain produced by the same Python modules.
4. **Preserve current behavior.** Spanish default, English switch, dark default, light switch, all status colors, assignment dialog, report/CSV, error messages and CLI.
5. **32-bit gate.** The current `.exe` is 32-bit universal on purpose. **PySide6 / Qt 6 is 64-bit only.** Treat this as an explicit decision gate: if 32-bit Windows support is a hard requirement, say so and recommend alternatives. Never silently drop it.
6. **Licensing.** PySide6 is LGPL. Do **not** propose PyQt6 (GPL/commercial) or `qfluentwidgets` (GPLv3) unless the owner explicitly approves the license. Prefer hand-written QSS and standard Qt widgets.
7. **No web UI.** Do not propose Electron, Tauri, Flet, NiceGUI or a local web server. The target is a native PySide6 desktop app.
8. **Do not touch production data.** Use `data/test/` or synthetic fixtures for any experiment. Never read, copy or commit `data/base/`.
9. **Windows 10/11, DPI-aware.** The UI must stay usable at 100%, 125%, 150% and 200% scaling.

---

## 4. Project context

Read these first, in this order:

1. `README.md`
2. `docs/NOTES.md` — source of truth for rules and behavior.
3. `app/ui.py` — current Tkinter UI (~628 lines).
4. `app/uikit/tokens.py` — design tokens (~72 lines).
5. `app/uikit/theme.py` — ttk theme engine (~138 lines).
6. `app/uikit/widgets.py`, `app/uikit/icons.py`.
7. `app/strings.py` — ES/EN strings.
8. `run_app.py` — GUI/CLI entry point.
9. `app/pipeline.py`, `app/report.py` — the UI-facing engine boundary.
10. `tests/` — especially `test_pipeline_smoke.py` and `test_writer.py`.

Current shape:

| Area | Current implementation |
|---|---|
| UI | Tkinter + ttk, custom `uikit` |
| Engine | Python 3.x, `openpyxl` + `python-docx` |
| Packaging | PyInstaller, 32-bit one-file, ~15.8 MB |
| UI size | ~873 lines including theme and widgets |
| Engine size | ~1,739 lines |
| Tests | 39 unittest tests |

Important: `app/uikit/tokens.py` says it was **ported from SelfishNet v2's `VISUAL_DESIGN_SYSTEM.md`**. The current palette is already very close to SelfishNet. The visual gap is mostly Tkinter's rendering limits, not the color choices.

---

## 5. Visual references

### 5.1 Primary: SelfishNet v2

Repository path: `..\SelfishNet v2` (relative to `Facturacion MTM`).

Read:

- `VISUAL_DESIGN_SYSTEM.md` — full design system, spacing scale, component specs, porting guidance.
- `src/SelfishNetV2.App/Themes/Dark.xaml`
- `src/SelfishNetV2.App/Themes/Light.xaml`
- `src/SelfishNetV2.App/Themes/Controls.xaml`
- `src/SelfishNetV2.App/MainWindow.xaml`
- `src/SelfishNetV2.App/Views/AdapterWindow.xaml`

Why primary: Facturación's current tokens are already derived from this system.

### 5.2 Secondary: Monmusu Localization Studio

Repository path: `..\monmusu-paradox-3-translation`.

Read:

- `src/MonmusuLocalizationStudio.App/Resources/Themes/Dark.xaml`
- `src/MonmusuLocalizationStudio.App/Resources/Themes/Styles.xaml`
- `src/MonmusuLocalizationStudio.App/MainWindow.xaml`

Why secondary: it is a denser, data-heavy WPF app with a compact grid, side panels and workflow dialogs — closer to Facturación's real usage than SelfishNet's dashboard.

### 5.3 Fidelity target

Aim for **the same visual language**, not pixel-identical WPF:

- Flat, dense, dark-first.
- 1 px borders, 6–8 px corner radii, no heavy shadows.
- Segoe UI family, 13 px base, 20 px page title, 11–12 px labels.
- 34 px table rows in the main grid (28 px is acceptable for compact secondary grids).
- Semantic colors for status, never hardcoded per screen.
- One accent color, one danger color, one success color.
- Consistent 4/8/12/16 spacing rhythm.
- Icons from a single family; no mixed styles.

State clearly in the report which WPF effects **cannot or should not** be reproduced exactly in Qt (DWM dark title bar, certain animations, native popup behavior) and what the Qt-appropriate substitute is.

---

## 6. Required analysis

Produce the following sections. Every recommendation must name concrete files, classes and Qt widgets.

### 6.1 Current UI inventory

- List every screen, panel, dialog, menu, button, input, table, status indicator and keyboard shortcut in `app/ui.py`.
- Describe the main user flow: select claim → select sources → optional drivers → optional driverlogs → optional days root → process → review rows → assign drivers → export Excel → generate driverlogs → generate BULK.
- Identify state kept in the `App` class and state returned by the engine.
- Find any Tk-specific behavior that has no direct Qt equivalent (e.g. `ttk.Treeview` tags, `after`, `PhotoImage`, DPI calls, `_MEIPASS`).

### 6.2 Screen-by-screen Qt blueprint

For each screen, provide an ASCII wireframe and a component tree:

- Main window: top bar, file/source selection card, action buttons, summary strip, results table, detail/assignment panel, status bar.
- Assign-driver dialog.
- Help window.
- Error/confirmation dialogs.
- Theme and language controls.

Recommend the final layout. Consider whether a left sidebar, a top toolbar or a cards layout fits Facturación better. Justify the choice using the two reference apps.

### 6.3 Component mapping table

Map every current element to Qt:

| Current (Tkinter) | Proposed (PySide6) | Notes |
|---|---|---|
| `ttk.Treeview` | `QTableView` + model | Must support status tints and per-column alignment |
| `ttk.Button` | `QPushButton` | Primary/secondary/danger roles |
| `tk.Frame` card | `QFrame` with `role=card` | QSS border/radius |
| `tk.StringVar` / form state | Dataclass / view-model | No logic in widgets |
| `messagebox` | `QMessageBox` or custom dialog | Match tone and language |
| `filedialog` | `QFileDialog` | Remember last folder |

### 6.4 Design system and QSS plan

- Consolidate tokens into one Python module (`ui_qt/theme/tokens.py` or reuse `app/uikit/tokens.py`).
- Decide between static `.qss` files and QSS generated from Python tokens. Recommend one and justify it.
- Define selectors and dynamic properties (`role="primary"`, `role="danger"`, `state="selected"`, `status="OK"`).
- Cover: `QMainWindow`, `QWidget`, `QFrame#Card`, `QPushButton`, `QLineEdit`, `QComboBox`, `QCheckBox`, `QTableView`, `QHeaderView`, `QScrollBar`, `QStatusBar`, `QToolTip`, `QDialog`, `QTabWidget`, `QSplitter`.
- Specify hover, pressed, focus, disabled and selected states.
- Explain how dark/light switching works at runtime without restarting.
- Define font stack: `Segoe UI Variable Text`, `Segoe UI`, fallback; `Consolas` for numeric/technical cells if needed.
- Map the current 9 status colors (`OK`, `NOTA`, `SUGERIDO`, `BALANCEADO`, `REVISAR`, `ELEGIR`, `NO FACTURAR`, `FACTURADO`, `SIN DATO`) to row backgrounds and status pills.
- Define accessibility: focus rings, keyboard navigation, minimum contrast, no color-only meaning.

### 6.5 Table strategy

Facturación's main screen is a data grid. Analyze:

- `QAbstractTableModel` over the existing list of row dicts.
- `QSortFilterProxyModel` for status filters and search.
- `QStyledItemDelegate` for status pills, time formatting and right-aligned mileage/cost.
- Column sizing, resizing, freezing, row height and alternating rows.
- Expected row counts per batch and whether virtualization is sufficient.
- Selection behavior: single row, multi-row or cell selection.
- Inline editing vs the assign-driver dialog. Recommend one.
- How to keep sorting stable and how to preserve selection after reprocessing.

### 6.6 Threading and responsiveness

- Current UI uses `threading`; Qt requires UI updates on the main thread.
- Propose `QThreadPool` + `QRunnable` or `QThread` + worker object.
- Define signals for progress, log lines, completion, error and cancellation.
- Identify safe cancellation points in `run_job` without changing the engine. If cancellation is not feasible, say so.
- Prevent double-start, closing during a running job, and cross-thread widget access.

### 6.7 Dialogs, i18n and persistence

- Inventory ES/EN strings and decide whether to keep `app/strings.py` or introduce Qt translation files. Recommend the lower-risk option.
- Language switch must be instant and must not lose form state.
- Theme and language persistence: reuse the current config file, do not create a second settings store.
- File dialogs, last-used folders and recent files.
- Help window content source.
- High-DPI icon strategy: SVG via `QIcon` or PNG at multiple sizes. Note that the current icons are generated PNGs.

### 6.8 Packaging and distribution

- Compare one-file vs one-folder PyInstaller builds for PySide6.
- Required Qt plugins and excludes; how to keep the artifact as small as practical.
- Expected size and startup time versus the current 15.8 MB Tkinter exe.
- 64-bit-only consequence and the exact user-facing impact.
- Icon, version info, `--windowed`, console suppression.
- Code signing status and SmartScreen implications.
- Whether the existing `build.ps1` and `.spec` can be reused or must be forked.
- Rollback plan: keep the Tkinter build available until the Qt UI is validated.

### 6.9 Testing and parity

- Engine tests must keep passing unchanged.
- Propose UI tests with `pytest-qt` (or an equivalent): window opens, process with fixtures, table populates, filters work, theme/language switch, assignment dialog, export wiring.
- Propose one end-to-end smoke test using `tests/fixtures.py` and `test_pipeline_smoke.py` patterns.
- Verify that the Qt UI produces the same Excel/DOCX/BULK outputs as the Tkinter UI because it calls the same engine.
- Manual visual checklist: dark/light, ES/EN, 100/125/150/200% DPI, empty state, error state, long text, many rows, narrow window.

### 6.10 Risks

Provide a risk table with likelihood, impact and mitigation:

- 32-bit support loss.
- Visual fidelity gap versus WPF.
- Qt licensing/distribution.
- Table performance and delegate complexity.
- Threading bugs and frozen UI.
- Packaging size/startup.
- Regression in a billing-critical workflow.
- Maintenance burden of two UI implementations during transition.
- Python/PySide6 version compatibility.

### 6.11 Phased plan and estimate

Propose phases with exit criteria and effort in days:

1. Visual prototype (main window only, fake data).
2. Design system + shell.
3. Results table + filters + status rendering.
4. Assignment dialog + detail panel.
5. Real engine wiring + threading.
6. Packaging + visual QA.
7. Parallel run + cutover.

Give a realistic total for one developer, with and without AI assistance. Separate "UI only" from "UI + packaging + QA".

### 6.12 Go / no-go recommendation

End with a clear recommendation:

- Is the migration worth it if the only goal is a better-looking UI?
- What is the cheapest path to 80–90% of the visual result?
- Under which conditions should the owner choose PySide6, CustomTkinter, or a full C#/WPF port instead?
- What should be done first, regardless of the decision?

---

## 7. Output format

Write a Markdown report with:

1. **Executive summary** — one page maximum.
2. **Current state** — what exists today, with file references and line counts.
3. **Visual reference extraction** — side-by-side token table: SelfishNet → Monmusu → current Facturación → proposed Qt.
4. **Proposed architecture** — file tree and responsibilities.
5. **Screen blueprints** — ASCII wireframes.
6. **Component mapping table**.
7. **QSS plan** — selectors, states, theme switching.
8. **Table/delegate plan**.
9. **Threading plan**.
10. **Packaging plan**.
11. **Test plan**.
12. **Risk table**.
13. **Phased plan with estimates**.
14. **Go/no-go and open questions**.

Use short sentences and tables. Name exact files. Do not write production code. Do not modify anything.

---

## 8. Acceptance criteria

The analysis is complete only when:

- Every widget and flow in `app/ui.py` is mapped to a Qt equivalent.
- Every color, font size, spacing value and radius has a source and a target value.
- The 32-bit trade-off is explicitly decided or escalated.
- The licensing position is explicit (PySide6 LGPL; no GPL-only dependencies).
- The main table strategy is justified, including delegates and filtering.
- Threading and cancellation are addressed.
- Packaging size/startup and rollback are covered.
- The estimate includes verification and parallel running, not just coding.
- The recommendation is concrete and does not hedge.

---

## Appendix A — Reference tokens

### A.1 SelfishNet v2 dark palette

```text
background      #14171B
surface         #1C2128
surface_alt     #262C35
border          #333B47
text            #E6EDF3
text_dim        #9AA7B4
accent          #4C8DFF
accent_hover    #6FA3FF
success         #3FB950
danger          #F85149
selection       accent @ 28% opacity
warning_bg      #3D2E12
warning_fg      #F0B429
```

### A.2 SelfishNet v2 light palette

```text
background      #F3F5F7
surface         #FFFFFF
surface_alt     #ECEFF3
border          #D2D9E0
text            #1F2328
text_dim        #5A6572
accent          #0969DA
accent_hover    #2F7FE0
success         #1A7F37
danger          #CF222E
selection       accent @ 18% opacity
warning_bg      #FFF3CD
warning_fg      #8A5A00
```

### A.3 Monmusu dark palette

```text
app background  #0F1115
panel           #151922
surface         #1C222C
surface_alt     #232B38
border          #2D3747
text            #E8EDF5
muted           #9AA6B6
faint           #6F7C8F
accent          #5B8DEF
accent_hover    #76A3FF
accent_pressed  #4477D6
selection       #2A3B57
error           #F06A6A
warning         #D9A441
success         #4CC38A
on_accent       #0B1020
```

### A.4 Typography and metrics

```text
Base font       Segoe UI Variable Text → Segoe UI → Arial
Base size       13 px
Page title      20 px SemiBold
Section title   12 px SemiBold
Field label     11 px
Mono            Consolas

Card radius     6–8 px
Button radius   6 px
Input radius    5–6 px
DataGrid row    34 px (SelfishNet) / 28 px (Monmusu)
Grid header     10,8 padding
Grid cell       10,4 padding
Toolbar         12,9 padding
Status bar      14,8 padding
```

### A.5 Current Facturación status tints

Use the existing values in `app/uikit/tokens.py` (`STATUS_TINTS`) as the source of truth. Do not invent new status colors.

---

## Appendix B — Files to inspect

```text
README.md
docs/NOTES.md
docs/PORTABILITY.md
app/ui.py
app/uikit/tokens.py
app/uikit/theme.py
app/uikit/widgets.py
app/uikit/icons.py
app/strings.py
app/pipeline.py
app/report.py
app/writer.py
app/bulk.py
app/driverlogs.py
run_app.py
tests/test_pipeline_smoke.py
tests/fixtures.py

..\SelfishNet v2\VISUAL_DESIGN_SYSTEM.md
..\SelfishNet v2\src\SelfishNetV2.App\Themes\Dark.xaml
..\SelfishNet v2\src\SelfishNetV2.App\Themes\Light.xaml
..\SelfishNet v2\src\SelfishNetV2.App\Themes\Controls.xaml
..\SelfishNet v2\src\SelfishNetV2.App\MainWindow.xaml

..\monmusu-paradox-3-translation\src\MonmusuLocalizationStudio.App\Resources\Themes\Dark.xaml
..\monmusu-paradox-3-translation\src\MonmusuLocalizationStudio.App\Resources\Themes\Styles.xaml
..\monmusu-paradox-3-translation\src\MonmusuLocalizationStudio.App\MainWindow.xaml
```

---

## Appendix C — Read-only commands

```powershell
# Run the current app (GUI)
python run_app.py

# Run the engine tests (must remain green)
python -m unittest discover -s tests -v

# Inspect the current UI size
(Get-Content app\ui.py | Measure-Object -Line).Lines
```

Do not rebuild the exe, do not modify `data/base/`, and do not install PySide6 as part of this analysis.

---

## Appendix D — Open questions for the owner

Include answers or explicit assumptions for:

1. Is 32-bit Windows still required? If yes, PySide6 is out unless that requirement is dropped.
2. Is the app distributed only internally, or to external customers? This affects LGPL compliance and code signing.
3. Which is more important: visual polish or minimal risk/time?
4. Should the Qt UI live beside the Tkinter UI (`ui_qt/`) during the transition, or replace it in one cutover?
5. Are new features planned soon (auto-update, Outlook, API, signing) that would change the UI requirements?
