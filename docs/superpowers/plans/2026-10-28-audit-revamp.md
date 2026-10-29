# Facturación MTM Audit & Revamp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the confirmed correctness and data-loss issues, add a repeatable stdlib test suite, and remove dead/duplicated code without changing the portal Excel/Word/BULK formats.

**Architecture:** Keep the existing `parsers → pipeline → filler → writer/bulk/driverlogs` flow. Add small shared helpers in `common.py`; make balancing respect matches and preferred drivers; classify summary notes; filter already-billed rows at the output boundary; reuse the existing UI kit. No new runtime dependency.

**Tech Stack:** Python 3.14, Tkinter, openpyxl 3.1.5, python-docx 1.2.0, stdlib `unittest`, PyInstaller 6.22.3 (build only).

**Spec:** `docs/superpowers/specs/2026-10-28-audit-revamp-design.md`

## Global Constraints

- Keep the claim output at **10 columns**, one sheet per day (`MM-DD`), flat values only, sheet order by date.
- Keep the BULK UPLOAD 10-column template and the driverlog table format unchanged.
- Never modify the original claim, BULK template or driverlog templates. Outputs are new files.
- Same input → same output. The jitter seeds stay deterministic.
- No new runtime dependencies. Tests use stdlib `unittest`; `openpyxl` and `python-docx` are already runtime deps.
- `data/` stays gitignored. `docs/`, `tests/` and `selftest.py` become tracked.
- The root executable remains the 32-bit universal build.
- All user-facing strings are added in both Spanish and English.

## Review Focus

The five input classes/failure modes most likely to bite a user:

1. A summary row with `Facturado.` **and** a valid driver: must be skipped from Excel/BULK/driverlogs and listed, not merely colored.
2. A summary row with `Facturar manualmente. Driver X, auto N.`: must remain billable and use driver N; it must not be confused with `Facturado`.
3. A driver with more than 3 matched trips: balancing must leave those trips alone; the driver may exceed 3.
4. A driverlogs folder with no matching driver numbers: no driver may be accepted or suggested.
5. A B-leg with PU before its A-leg: the preview must show `REVISAR`, not `OK`.

Each of these gets a test in the owning task. Export overwrite/locked-file behavior is also tested in Task 7.

---

## File Structure

**Create**
- `tests/__init__.py`
- `tests/fixtures.py`
- `tests/test_common.py`
- `tests/test_pipeline_smoke.py`
- `tests/test_balance.py`
- `tests/test_status.py`
- `tests/test_allowed.py`
- `tests/test_notes.py`
- `tests/test_facturado.py`
- `tests/test_writer.py`
- `tests/test_pickup.py`
- `tests/test_strings.py`
- `docs/superpowers/specs/2026-10-28-audit-revamp-design.md` (already written)
- `docs/superpowers/plans/2026-10-28-audit-revamp.md` (this file)
- `requirements-build.txt`
- `build.ps1` (optional but included for reproducibility)

**Modify**
- `app/common.py` — `note_kind`, `day_name`, `add_minutes`, `numeric_key`, header-only read.
- `app/parsers.py` — classify with header-only read; add `note_kind` to resumen entries.
- `app/filler.py` — balancing guard, allowed-driver helper, Facturado flag, stats; delete `_est_pickup`.
- `app/pipeline.py` — skip billed rows in workload; optional pre-scanned sources.
- `app/writer.py` — filter Facturado, guard source path, empty-export error.
- `app/bulk.py` — filter Facturado; shared helpers; delete `sim_times`.
- `app/driverlogs.py` — filter Facturado; shared `day_name`; delete `MAX_TRIPS`.
- `app/report.py` — “already billed” section and stat.
- `app/ui.py` — statuses, strings, counts, export errors, source scan reuse; remove dead canvas fallbacks/imports.
- `app/uikit/tokens.py` — add `FACTURADO` tint; use/remove unused tokens.
- `app/uikit/theme.py` — no functional change expected; verify style keys.
- `app/uikit/widgets.py` — use existing `StatusDot`/`hseparator` in `ui.py` (or delete if unused).
- `app/uikit/README.md` — reflect final tokens/widgets.
- `README.md`, `docs/NOTES.md`, `docs/PORTABILITY.md`, `docs/PU_TIME_FINDINGS.md` — current truth.
- `.gitignore` — stop ignoring `docs/` and `selftest.py`.
- `requirements.txt` — runtime only; add pinned versions.
- `version_info.txt` — bump to 2.4.0.0 when building.

---

## Task 1: Baseline test harness

**Files:**
- Create: `tests/__init__.py`, `tests/fixtures.py`, `tests/test_common.py`, `tests/test_pipeline_smoke.py`
- No production changes.

**Interfaces:**
- `tests.fixtures.make_claim(path, rows)`, `make_resumen(path, rows)`, `make_trips(path, rows)`, `make_drivers(path, rows)`, `make_docx_template(path)`.
- Fixtures use synthetic values only. Do not read `data/`.

- [ ] **Step 1: Write `tests/fixtures.py`**

Use openpyxl and python-docx. Each helper creates a workbook/document at the given path with these headers:

```python
CLAIM_HEADERS = ["Claim Status", "Trip Number", "Appt. Date", "Member Info",
                 "Driver", "VIN", "Provider Cost", "Name (First and Last)"]
RESUMEN_HEADERS = ["DATE", "LOS", "TRIP ID", "PAYER", "NAME", "LAST NAME",
                   "DRIVER", "MILES", "NOTES"]
TRIPS_HEADERS = ["Trip Number", "Appointment Date", "Time", "Trip Mileage",
                 "Trip Cost", "Member's First Name", "Member's Last Name", "Pickup City"]
DRIVERS_HEADERS = ["DRIVER", "COUNTY", "LICENSE NUMBER", "VIN Number",
                   "CURRENT VEHICLE", "VEHICLE PLATE", "NUMERO"]
```

`make_docx_template(path)` creates one table with a header row and 14 empty data rows, 8 columns.

- [ ] **Step 2: Write `tests/test_common.py`**

```python
class CommonTests(unittest.TestCase):
    def test_norm_num(self):
        self.assertEqual(norm_num(200.0), "200")
        self.assertEqual(norm_num("200-1"), "200")
    def test_to_iso(self):
        self.assertEqual(to_iso("10/05/2026"), "2026-10-05")
    def test_parse_time_value(self):
        self.assertEqual(parse_time_value("7:45 AM"), ("time", dtime(7, 45)))
        self.assertEqual(parse_time_value("Will Call"), ("willcall", None))
```

- [ ] **Step 3: Write `tests/test_pipeline_smoke.py`**

Create a temp folder with one claim row (`LISA HALSEY`, trip `M4F32EG2N0A`, date `10/05/2026`, cost `$15.00`), one resumen row (`2026-10-05`, `LISA HALSEY`, driver `200`, miles `5.67`), one trip row (`M4F32EG2N0A`, `2026-10-05`, `10:00 AM`, `5.67`), and one driver (`200`, `MARION`, license `L1`, VIN `V1`). Run `run_job(...)`; assert:

```python
row = res["claim"]["rows"][0]
self.assertEqual(row["driver"], "200")
self.assertEqual(row["license"], "L1")
self.assertEqual(row["vin"], "V1")
self.assertEqual(row["milage"], 5.67)
self.assertIsNotNone(row["pu"])
self.assertIsNotNone(row["dropoff"])
self.assertLess(row["pu"], row["dropoff"])
```

Write the output to a temp `.xlsx`, reopen it, assert sheet name `10-05` and the 10 headers from `writer.HEADERS`.

- [ ] **Step 4: Run the baseline tests**

Run: `& "C:\Users\Fely\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m unittest discover -s tests -v`
Expected: all tests PASS on the current code. If they fail, fix the fixture, not production code.

- [ ] **Step 5: Record the current baseline (outside the repo)**

Run `selftest.py` and save the output. Current expected: `first_row_B 41/70 exact (58.6%)` with balancing on; `46/70 (65.7%)` with balancing off. Run the October CLI to `$env:TEMP\mtm_baseline.xlsx` and record `Get-FileHash`. This is a reference, not a committed file.

- [ ] **Step 6: Commit**

```bash
git add tests
git commit -m "test: add baseline fixtures and smoke tests"
```

---

## Task 2: Balancing must respect matches and preferred drivers

**Files:**
- Modify: `app/filler.py`
- Test: `tests/test_balance.py`

**Interfaces:**
- `_can_balance(row) -> bool` (internal).
- `fill_claim(..., balance=True)` keeps the same signature.
- Rows that may move: `src_resumen` false, `note_drv` false, member not in `PREFERRED_DRIVER`, flag not `nofacturar`/`facturado`.

- [ ] **Step 1: Write the failing tests**

```python
def _row(driver, member="TEST MEMBER", src_resumen=True, note_drv=False):
    return {"date": "2026-10-05", "member": member, "trip": "T0A",
            "driver": driver, "license": "L", "vin": "V", "flag": "",
            "src_resumen": src_resumen, "note_drv": note_drv}

def test_balance_does_not_move_matched_rows(self):
    claim = {"rows": [_row("200") for _ in range(4)]}
    drivers = {"table": {"200": {"county": "MARION"}, "220": {"county": "MARION"}},
               "allowed": {"200", "220"}}
    stats, review = {}, []
    _balance_drivers(claim, drivers, stats, review)
    self.assertTrue(all(r["driver"] == "200" for r in claim["rows"]))

def test_balance_does_not_move_preferred_driver(self):
    claim = {"rows": [_row("349", "DALIA ALFONSO", src_resumen=False) for _ in range(4)]}
    drivers = {"table": {"349": {"county": "MARION"}, "10": {"county": "MARION"}},
               "allowed": {"349", "10"}}
    stats, review = {}, []
    _balance_drivers(claim, drivers, stats, review)
    self.assertTrue(all(r["driver"] == "349" for r in claim["rows"]))

def test_balance_can_move_unmatched_rows(self):
    claim = {"rows": [_row("200", src_resumen=False) for _ in range(4)]}
    drivers = {"table": {"200": {"county": "MARION"}, "220": {"county": "MARION"}},
               "allowed": {"200", "220"}}
    stats, review = {}, []
    _balance_drivers(claim, drivers, stats, review)
    self.assertIn("220", [r["driver"] for r in claim["rows"]])
```

- [ ] **Step 2: Run and see the first two fail**

Run: `& "<python>" -m unittest tests.test_balance -v`
Expected: matched and preferred tests FAIL (rows moved to 220/10); unmatched test PASSES.

- [ ] **Step 3: Implement the guard**

In `app/filler.py`:

```python
def _can_balance(row):
    member = (row.get("member") or "").upper()
    return (row.get("driver")
            and row.get("flag") not in ("nofacturar", "facturado")
            and not row.get("src_resumen")
            and not row.get("note_drv")
            and member not in PREFERRED_DRIVER)
```

In `_balance_drivers`, keep all billable rows in `by_date` for counting, excluding `nofacturar` and `facturado`, but select movable rows:

```python
src_rows = [r for r in rows if r.get("driver") == src and _can_balance(r)]
if not src_rows:
    continue
```

Do not change the receiver rules (same county, below `BALANCE_TARGET`). If a driver is over `BALANCE_MAX` but has no movable rows, add one review line:

```python
review.append(f"REPARTO BLOQUEADO {date} {src}: {counts[src]} viajes, "
              f"todos con match/nota/preferencia (no se mueven)")
```

- [ ] **Step 4: Run the tests and the benchmark**

Run: `& "<python>" -m unittest tests.test_balance -v` → PASS.
Run: `& "<python>" selftest.py` → expect `first_row_B 46/70 (65.7%)` with default settings, matching the balance-off result. If it is still 41/70, stop: some matched row is still movable.

- [ ] **Step 5: Verify October behavior**

Run the October batch to a temp output. Expected: Dalia’s 10-14/10-15 rows keep their note-pinned driver (`309`), never `10`/`200`/`220`; on days without a note they stay on `349`. The number of `balanceado` rows drops; any `REPARTO BLOQUEADO` lines are listed in REVIEW.

- [ ] **Step 6: Commit**

```bash
git add app/filler.py tests/test_balance.py
git commit -m "fix: never balance matched or preferred drivers"
```

---

## Task 3: Show `revisar` rows as REVISAR

**Files:**
- Modify: `app/ui.py`
- Test: `tests/test_status.py`

- [ ] **Step 1: Write the failing test**

```python
def test_revisar_with_driver_and_milage_is_not_ok(self):
    row = {"driver": "200", "milage": 5.0, "flag": "revisar"}
    self.assertEqual(status_of(row), "REVISAR")
```

- [ ] **Step 2: Run and see it fail**

Expected: current `status_of` returns `OK`.

- [ ] **Step 3: Fix the precedence**

At the start of `status_of`, before the driver/mileage branch:

```python
if flag == "revisar":
    return "REVISAR"
```

Keep `facturado`/`nofacturar` checks in the same early block (Task 6 adds `facturado`).

- [ ] **Step 4: Run the test**

Expected: PASS. Add a case for a row with driver+milage+`nota` still returning `NOTA`.

- [ ] **Step 5: Commit**

```bash
git add app/ui.py tests/test_status.py
git commit -m "fix: show revisar rows as REVISAR"
```

---

## Task 4: Empty allowed set must mean no drivers

**Files:**
- Modify: `app/filler.py`
- Test: `tests/test_allowed.py`

**Interfaces:**
- `_allowed_drivers(drivers) -> set[str]` (internal): `set()` when drivers is falsy; `set(drivers["table"])` only when `drivers.get("allowed") is None`; otherwise return `set(drivers["allowed"])`.

- [ ] **Step 1: Write the failing tests**

```python
def test_empty_allowed_helper_is_empty(self):
    drivers = {"table": {"200": {}}, "allowed": set()}
    self.assertEqual(_allowed_drivers(drivers), set())

def test_empty_allowed_does_not_accept_summary_driver(self):
    # one claim row, one resumen row with driver 200, drivers table has 200,
    # but drivers["allowed"] is empty (no matching template)
    report = fill_claim(claim, resumen_index, {}, drivers, suggest_driver=True)
    row = claim["rows"][0]
    self.assertEqual(row["driver"], "")
    self.assertIn(row["flag"], ("revisar", "elegir"))
```

- [ ] **Step 2: Run and see them fail**

Expected: current code falls back to the table and assigns 200.

- [ ] **Step 3: Implement and use the helper**

Replace both `(drivers.get("allowed") if drivers else None) or set(drivers["table"])` patterns in `_assign` and the suggestion pass with `_allowed_drivers(drivers)`. In `_balance_drivers`, use it too.

- [ ] **Step 4: Run the tests**

Expected: PASS. Confirm no driver is suggested and the row stays unfilled/reviewable.

- [ ] **Step 5: Commit**

```bash
git add app/filler.py tests/test_allowed.py
git commit -m "fix: treat an empty allowed set as empty"
```

---

## Task 5: Classify notes and flag already-billed rows

**Files:**
- Modify: `app/common.py`, `app/parsers.py`, `app/filler.py`, `app/pipeline.py`
- Test: `tests/test_notes.py`

**Interfaces:**
- `note_kind(note: str) -> str` returns `"billed"`, `"actionable"`, `"info"` or `""`.
  - `"billed"`: starts with `Facturado` or `Ya facturado` (case-insensitive).
  - `"actionable"`: not billed and contains `auto N`, `duplicad`, `perfil`, `vehiculo` or `will call`.
  - `"info"`: any other non-empty note (for example `Facturación manual.`).
- `parse_resumen` entries gain `"note_kind"`.
- `fill_claim` stats gain `"already_billed": 0`; the report gains `"already_billed": [...]`.

- [ ] **Step 1: Write the failing tests**

```python
class NoteKindTests(unittest.TestCase):
    def test_billed(self):
        self.assertEqual(note_kind("Facturado."), "billed")
        self.assertEqual(note_kind("Facturado manualmente. Auto 20, driver Dixon."), "billed")
        self.assertEqual(note_kind("Ya facturado."), "billed")
    def test_actionable(self):
        self.assertEqual(note_kind("Facturar manualmente. Driver Marielkis, auto 309."), "actionable")
        self.assertEqual(note_kind("Facturación manual. Driver X, auto 309."), "actionable")
    def test_info_and_empty(self):
        self.assertEqual(note_kind("Facturación manual."), "info")
        self.assertEqual(note_kind(""), "")
```

Add a `fill_claim` test with a resumen row whose `NOTES` cell is `Facturado.`:

```python
self.assertEqual(row["flag"], "facturado")
self.assertEqual(report["stats"]["already_billed"], 1)
```

Add a second row with `Facturar manualmente. Driver Marielkis, auto 309.`:

```python
self.assertEqual(row["driver"], "309")
self.assertEqual(row["flag"], "nota")
self.assertNotEqual(row["flag"], "facturado")
```

- [ ] **Step 2: Run and see them fail**

Expected: `note_kind` is missing; the billed row is marked `nota`, not `facturado`.

- [ ] **Step 3: Implement `note_kind` and parser field**

Use `re` and the existing `s()` helper. Add `"note_kind": note_kind(note)` to each `parse_resumen` entry. Do not add a new dependency.

- [ ] **Step 4: Implement the filler behavior**

Add a `billed` list parameter to `_assign` and `fill_claim` (and pass it at every `_assign` call). After the driver/mileage work and before the old `if note:` block:

```python
kind = x.get("note_kind") or note_kind(note)
if kind == "billed":
    row["flag"] = "facturado"
    stats["already_billed"] += 1
    billed.append({"date": row["date"], "trip": row["trip"], "member": row["member"]})
    review.append(f"YA FACTURADO {row['date']} {row['member']} {row['trip']}: "
                  f"{note[:90]}")
elif note:
    if row.get("flag") != "revisar":
        row["flag"] = "nota"
    review.append(f"NOTA {row['date']} {row['member']} {row['trip']}: {note[:90]}")
```

Return `"already_billed": billed` in the `fill_claim` result. Do not append the old `NOTA` line for billed rows.

- [ ] **Step 5: Exclude billed rows from workload and suggestions**

In `build_resumen_index` (`app/pipeline.py`), skip billed rows when filling `usage`:

```python
if e.get("note_kind") == "billed":
    continue
```

In `fill_claim`, exclude `facturado` from `needs` and from `_balance_drivers`; `_balance_drivers` must not count or move facturado rows. The `_can_balance` guard from Task 2 covers moving; also exclude them from the `by_date` count.

- [ ] **Step 6: Run the tests**

Expected: PASS. Verify a billed row remains in `claim["rows"]` with `flag == "facturado"` and is not in `needs_driver`/`suggested`.

- [ ] **Step 7: Commit**

```bash
git add app/common.py app/parsers.py app/filler.py app/pipeline.py tests/test_notes.py
git commit -m "feat: classify notes and flag already-billed rows"
```

---

## Task 6: Skip already-billed rows in every output and report them

**Files:**
- Modify: `app/writer.py`, `app/bulk.py`, `app/driverlogs.py`, `app/report.py`, `app/ui.py`, `app/uikit/tokens.py`
- Test: `tests/test_facturado.py`

**Interfaces:**
- `write_output` filters `flag == "facturado"`; returns `{"path", "rows", "sheets", "skipped"}`; raises `ValueError("No hay filas facturables para exportar")` if none remain.
- `generate_bulks` excludes facturado and includes it in `excluded`.
- `generate_driverlogs` excludes facturado and returns `"billed_skipped": N`.
- `report_text` adds a `YA FACTURADO`/`ALREADY BILLED` section.
- `status_of` returns `"FACTURADO"` for flag `facturado`.

- [ ] **Step 1: Write the failing output tests**

Use a claim with two rows: one normal (driver 200, flag `""`) and one facturado (driver 220, flag `facturado`).

```python
def test_writer_excludes_facturado(self):
    info = write_output(claim, out)
    wb = load_workbook(out, read_only=True)
    values = list(wb["10-05"].iter_rows(values_only=True))
    self.assertEqual(len(values), 2)          # header + one normal row
    self.assertEqual(values[1][0], 200)
    self.assertEqual(info["skipped"], 1)

def test_bulk_excludes_facturado(self):
    res = generate_bulks(claim["rows"], temp_dir)
    self.assertEqual(len(res["created"]), 1)
    self.assertEqual(len(res["excluded"]), 1)

def test_driverlogs_exclude_facturado(self):
    res = generate_driverlogs(claim["rows"], templates, temp_dir)
    self.assertTrue(all("220" not in path for path in res["created"]))
    self.assertEqual(res["billed_skipped"], 1)

def test_report_lists_billed(self):
    text = report_text({"report": report, "claim_path": "x.xlsx"}, "es")
    self.assertIn("YA FACTURADO", text)
```

Also test `status_of({"driver": "220", "milage": 1.0, "flag": "facturado"}) == "FACTURADO"`.

- [ ] **Step 2: Run and see them fail**

Expected: facturado rows still appear in Excel/BULK/driverlogs; status is OK.

- [ ] **Step 3: Implement the writer filter**

At the start of `write_output`:

```python
rows = [r for r in claim["rows"] if r.get("flag") != "facturado"]
skipped = len(claim["rows"]) - len(rows)
if not rows:
    raise ValueError("No hay filas facturables para exportar")
```

Use `rows` for grouping. Add `"skipped": skipped` to the return dict.

- [ ] **Step 4: Implement BULK and driverlog filters**

BULK: `selected = [r for r in rows if r.get("driver") and r.get("flag") not in ("nofacturar", "facturado") and r.get("date")]`.

Driverlogs: filter `flag != "facturado"` before `by_day`; count `billed_skipped` and include it in the return/report.

- [ ] **Step 5: Add the report section and UI status**

`report.py`:
- `stats` line: `Ya facturado: {n} (no se vuelve a facturar)` / `Already billed: {n} (not billed again)`.
- Section `billed_title` / `billed_hint`, listing date, member, trip.

`ui.py`:
- `status_of`: return `FACTURADO` for flag `facturado` before the other branches.
- `STRINGS["es"/"en"]["st_done"]`: add `{facturado}`; add a label for the status? The status text itself is `FACTURADO`.
- `_render` counts include `"FACTURADO": 0`.
- `_populate_assign` skips `facturado`.
- `export` pending count skips `facturado`.
- `STATUS_TINTS` adds `FACTURADO` (use the same gray as `NO FACTURAR` if you do not want a new color).
- `bulk_body`/`dl_body` may mention skipped billed rows.

- [ ] **Step 6: Run the tests**

Expected: PASS. Verify the BULK template file is unchanged and no facturado driverlog is written.

- [ ] **Step 7: Commit**

```bash
git add app/writer.py app/bulk.py app/driverlogs.py app/report.py app/ui.py app/uikit/tokens.py tests/test_facturado.py
git commit -m "feat: skip already-billed rows in outputs and report them"
```

---

## Task 7: Export guard and friendly file errors

**Files:**
- Modify: `app/writer.py`, `app/ui.py`, `run_app.py`
- Test: `tests/test_writer.py`

**Interfaces:**
- `write_output` raises `ValueError` when `Path(path).resolve() == Path(claim.get("path", "")).resolve()`.
- UI export/CSV catch `ValueError`/`OSError` and show a message.
- CLI catches the same errors and returns exit code 2.

- [ ] **Step 1: Write the failing guard test**

```python
def test_write_output_refuses_source_path(self):
    claim = {"path": str(claim_path), "rows": [{"date": "2026-10-05", ...}]}
    before = claim_path.read_bytes()
    with self.assertRaises(ValueError):
        write_output(claim, claim_path)
    self.assertEqual(claim_path.read_bytes(), before)
```

- [ ] **Step 2: Run and see it fail**

Expected: current code overwrites the source file.

- [ ] **Step 3: Implement the guard**

At the start of `write_output`, before filtering:

```python
source = claim.get("path")
if source and Path(path).resolve() == Path(source).resolve():
    raise ValueError("La salida no puede ser el archivo original del claim.")
```

- [ ] **Step 4: Handle errors in the UI and CLI**

`ui.export` and `ui.save_csv` wrap the write in `try/except (ValueError, OSError) as e` and call `messagebox.showerror(self.t("st_error"), str(e))`.

In `run_app.main_cli`, wrap `write_output` in the same `try/except`, print `ERROR: ...`, and `return 2`.

- [ ] **Step 5: Run the tests**

Expected: PASS. Manual checks: choose the source claim as output → friendly error; open the target in Excel → friendly error; different path → saved normally.

- [ ] **Step 6: Commit**

```bash
git add app/writer.py app/ui.py run_app.py tests/test_writer.py
git commit -m "fix: refuse source overwrite and handle locked outputs"
```

---

## Task 8: Pin the current PU/DropOff behavior and correct the docs

**Files:**
- Create: `tests/test_pickup.py`
- Modify: `docs/PU_TIME_FINDINGS.md`, `docs/NOTES.md`, `README.md`, `app/ui.py` help strings

**Interfaces:**
- No production logic change. The pinned sequence is: `dropoff = appointment − 1..5 min`; `PU = dropoff − (14 + 1.4×miles ± 3)` for normal trips; Will Call keeps the A-leg + 2 h rule.

- [ ] **Step 1: Write the characterization test**

Use the synthetic pipeline with date `2026-10-05`, trip `M4F32EG2N0A`, member `LISA HALSEY`, miles `5.67`, appointment `10:00 AM`, driver `200`. Assert the current values:

```python
self.assertEqual(row["pu_appt"], dtime(10, 0))
self.assertEqual(row["dropoff"], dtime(9, 56))
self.assertEqual(row["pu"], dtime(9, 34))
self.assertLess(row["pu"], row["dropoff"])
self.assertLess(row["dropoff"], row["pu_appt"])
```

If the seed or fixture changes the exact minutes, use the values produced by the deterministic run and record them in the test; do not change production logic. Add an invariant test for a normal row (`0 < appointment − dropoff <= 5`) and a Will Call row (`0 < pu_appt − pu <= 3`).

- [ ] **Step 2: Run the test**

Expected: PASS on current code. This locks the behavior before cleanup.

- [ ] **Step 3: Update the docs**

- `docs/PU_TIME_FINDINGS.md` §7: replace the single-line formula with the actual two-step sequence and state the 1–5 minute dropoff margin.
- `docs/NOTES.md` §6.4/§4: same.
- `README.md` lines 91–93: same.
- `app/ui.py` `help_body` (Spanish and English): same, so the in-app help does not contradict behavior.

- [ ] **Step 4: Run the tests and compile**

Run: `& "<python>" -m unittest tests.test_pickup -v` → PASS.
Run: `& "<python>" -m compileall -q app run_app.py` → no errors.

- [ ] **Step 5: Commit**

```bash
git add tests/test_pickup.py docs/PU_TIME_FINDINGS.md docs/NOTES.md README.md app/ui.py
git commit -m "docs: align PU timing documentation and pin behavior"
```

---

## Task 9: Lean cleanup and shared helpers

**Files:**
- Modify: `app/common.py`, `app/bulk.py`, `app/driverlogs.py`, `app/writer.py`, `app/filler.py`, `app/pipeline.py`, `app/ui.py`, `app/uikit/tokens.py`, `app/uikit/widgets.py`, `app/uikit/README.md`, `run_app.py`
- Create: `app/strings.py`, `tests/test_strings.py`
- Test: all existing tests.

**Interfaces:**
- `common.day_name(iso) -> "MM-DD"`.
- `common.add_minutes(t, minutes) -> time`.
- `common.numeric_key(value) -> tuple` (numeric values first, text last).
- `common.read_header(path) -> (header_row, sheetnames)` for classification.
- `app/strings.py` exports `STRINGS` (the current `ui.py` dictionary).

- [ ] **Step 1: Add helper tests**

```python
def test_day_name(self):
    self.assertEqual(day_name("2026-10-05"), "10-05")
def test_add_minutes(self):
    self.assertEqual(add_minutes(dtime(23, 55), 10), dtime(0, 5))
def test_numeric_key(self):
    self.assertEqual(numeric_key("200"), (0, 200))
    self.assertEqual(numeric_key("A"), (1, "A"))
```

- [ ] **Step 2: Implement the helpers and replace duplicates**

- Replace `bulk.day_name`, `driverlogs.day_name` and `writer._sheet_name` with `common.day_name`.
- Replace `filler._add_delta` and `bulk._add` with `common.add_minutes`.
- Replace `filler._drv_sort`, `pipeline._numsort` and the driverlog sort with `common.numeric_key`.
- Add `read_header` and use it in `parsers.classify` (Task 10 does the performance switch; the helper can land here).

- [ ] **Step 3: Delete dead code**

After `grep` confirms no references:
- `filler._est_pickup` (the old formula; PU is now documented as current).
- `bulk.sim_times`.
- `driverlogs.MAX_TRIPS`.
- `parse_claim`’s unused `layout` field (and update any test that reads it; none should).
- `ui._draw_flag`, `ui._draw_theme_icon`, unused `tkfont` import.
- Unused `norm_num` import in `filler.py`, unused `Path` import in `run_app.py`.
- Unused `SPACE`/`RADIUS` tokens; use `METRICS` for the window size, row height and status-dot size in `ui.py`.
- Replace the raw status dot/separators with `uikit.widgets.StatusDot`/`hseparator`, or delete the unused widget module if using them is not worth the churn. Prefer using them.

- [ ] **Step 4: Move the UI strings**

Create `app/strings.py` with the current `STRINGS` dict; `ui.py` imports it. Add `tests/test_strings.py`:

```python
def test_languages_have_the_same_keys(self):
    self.assertEqual(set(STRINGS["es"]), set(STRINGS["en"]))
```

- [ ] **Step 5: Run tests and prove the output is unchanged**

Run all tests. Generate the October Excel/BULK before and after this task (use the post-M1 behavior as the new baseline) and compare cell values with a small openpyxl script; expect **0 differences**. Compare one driverlog’s table cell text; expect 0 differences. Do not compare zip bytes (timestamps/metadata differ).

- [ ] **Step 6: Commit**

```bash
git add app tests
git commit -m "refactor: centralize helpers and remove dead code"
```

---

## Task 10: Reuse the source scan and read only headers for classification

**Files:**
- Modify: `app/common.py`, `app/parsers.py`, `app/pipeline.py`, `app/ui.py`
- Test: `tests/test_pipeline_smoke.py` (add a scan-reuse case)

**Interfaces:**
- `run_job(..., sources=None)`; when `sources` is provided, use it instead of calling `scan_sources` again.
- `common.read_header(path) -> (header, sheetnames)` uses `load_workbook(read_only=True)` and reads row 1 only.

- [ ] **Step 1: Add the scan-reuse test**

```python
src = scan_sources(sources_dir, drivers_file)
res1 = run_job(claim, sources_dir, drivers_path=drivers_file)
res2 = run_job(claim, sources_dir, drivers_path=drivers_file, sources=src)
self.assertEqual(res1["report"]["stats"], res2["report"]["stats"])
self.assertEqual([r["trip"] for r in res1["claim"]["rows"]],
                 [r["trip"] for r in res2["claim"]["rows"]])
```

- [ ] **Step 2: Implement `run_job(..., sources=None)`**

If `sources` is not provided, call `scan_sources(sources_folder, drivers_path)` as today. If it is provided, use it directly.

- [ ] **Step 3: Pass the scan from the UI**

In `ui.run`, keep the existing `scan_sources` check for the no-trip warning, then pass the result to `_work` and `run_job`. This removes the second full scan.

- [ ] **Step 4: Use header-only classification**

Replace `read_rows(path)` in `parsers.classify` with `read_header(path)`; keep the full parse functions unchanged. Test classification with the existing fixtures.

- [ ] **Step 5: Measure and verify**

Run the October CLI before/after and record elapsed time. Expected: no behavior change; the duplicate scan is gone and classification is cheaper. If the time improvement is negligible, keep the change anyway only if it is clearly simpler; otherwise skip `read_header` and keep only the scan reuse.

- [ ] **Step 6: Commit**

```bash
git add app/common.py app/parsers.py app/pipeline.py app/ui.py tests/test_pipeline_smoke.py
git commit -m "perf: avoid duplicate source scans and full reads for classification"
```

---

## Task 11: Current docs, repo hygiene, requirements and build

**Files:**
- Modify: `README.md`, `docs/NOTES.md`, `docs/PORTABILITY.md`, `docs/PU_TIME_FINDINGS.md`, `app/uikit/README.md`, `.gitignore`, `requirements.txt`, `version_info.txt`
- Create: `requirements-build.txt`, `build.ps1`

- [ ] **Step 1: Rewrite `docs/NOTES.md` as current truth**

Keep it short: purpose, environment, input/output map, current matching rules, current balancing rule, Facturado rule, PU/DropOff sequence, UI/exports, tests/build commands. Move historical notes to an appendix titled “History” or a separate `docs/HISTORY.md` if it grows. Remove references to deleted `recon/` scripts and external `Downloads` paths that no longer apply.

- [ ] **Step 2: Fix README and portability contradictions**

- 10 columns, one sheet per day, current default `first_row_B`, balancing only moves unmatched rows, Facturado rows are skipped.
- The root exe is 32-bit universal; the 64-bit build is optional.
- Current test command and build command.
- Ensure `docs/PORTABILITY.md` does not still claim “64-bit only” where the app is 32-bit universal.

- [ ] **Step 3: Track docs/tests, keep data ignored**

`.gitignore`:
- Remove `docs/` and `selftest.py`.
- Keep `data/`, `output/`, `build/`, `build32/`, `dist/`, `dist32/`, `*.exe`.

Then `git add docs tests selftest.py`.

- [ ] **Step 4: Split requirements and pin versions**

`requirements.txt`:

```
openpyxl==3.1.5
python-docx==1.2.0
```

`requirements-build.txt`:

```
-r requirements.txt
pyinstaller==6.22.3
```

Document that `assets/ui/make_icons.py` needs Pillow (dev-only); do not add it to runtime.

- [ ] **Step 5: Add the build script and bump the version**

`build.ps1` (accept a Python path parameter; default to the documented 32-bit portable path if it exists):

```powershell
param(
  [string]$Python = "$env:TEMP\opencode\py32\python\python.exe",
  [string]$Dist = "dist32",
  [string]$Work = "build32"
)
& $Python -m PyInstaller "Facturacion MTM.spec" --noconfirm --clean --distpath $Dist --workpath $Work
Copy-Item "$Dist\Facturacion MTM.exe" "Facturacion MTM.exe" -Force
(Get-Item "Facturacion MTM.exe").VersionInfo | Format-List FileVersion, ProductVersion
```

Bump `version_info.txt` to `2.4.0.0` (all four version fields). Update the documented size after the build if it changes.

- [ ] **Step 6: Verify a fresh checkout**

After committing, clone the repo to a temp directory, install runtime requirements, and run the tests. The tests must pass without `data/` because fixtures are synthetic. Then run the build script if the 32-bit Python path exists; otherwise build 64-bit for the smoke test and record that the 32-bit root exe was not rebuilt on this machine.

- [ ] **Step 7: Commit**

```bash
git add README.md docs app/uikit/README.md .gitignore requirements.txt requirements-build.txt version_info.txt build.ps1
git commit -m "docs: refresh project notes and add reproducible build"
```

---

## Task 12: Final verification and sign-off

**Files:** none (verification only).

- [ ] **Step 1: Run the full test suite**

`& "C:\Users\Fely\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m unittest discover -s tests -v`
Expected: all PASS.

- [ ] **Step 2: Run the accuracy benchmark**

`& "<python>" selftest.py`
Expected: `first_row_B` **46/70 exact (65.7%)** with default settings; pair/no-balance remains 26/34 on the manual 10-05…10-07 sample. If the Facturado rule affects the benchmark, record the new number and explain it; do not hide a regression.

- [ ] **Step 3: Run the October batch**

Generate the Excel, BULK and driverlogs to a temp folder. Verify:
- Excel has one sheet per day, 10 columns, no formulas, flat values.
- BULK files have 10 columns and the template formatting; no formulas.
- Driverlogs exist for billable drivers only; no facturado driverlogs.
- Facturado rows (if any) are listed in the report and absent from Excel/BULK/driverlogs. The current October claim has no matched row whose detected note starts with `Facturado.`; the rule is exercised by the synthetic tests and is ready for the next batch.
- Dalia 10-14/10-15 keep their note-pinned driver (309); days without a note stay on 349.
- The output is idempotent: run twice and compare cell values; expect 0 differences.

- [ ] **Step 4: Manual UI checklist**

Run `python run_app.py` and check:
- Process with the October data.
- Status colors show `REVISAR`, `FACTURADO`, `SUGERIDO`, `BALANCEADO`.
- Language toggle and theme toggle still work.
- Assign/clear driver still works.
- Export to a new path works.
- Export to the source claim shows an error, no overwrite.
- Open the target in Excel and export → friendly error.
- Driverlogs/BULK buttons work and report skipped billed rows.

- [ ] **Step 5: Smoke-test the executable**

If the 32-bit toolchain is available, build and run the root exe from a temp folder with only the exe; run the October CLI and compare outputs with the engine. If not, build the 64-bit exe for the smoke test and record that the 32-bit root exe still needs a rebuild on a machine with the portable 32-bit toolchain.

- [ ] **Step 6: Update the plan and report**

Mark completed tasks, record the exact commands and results, and list any residual risks. Do not claim completion without the test/benchmark/output evidence.

---

## Self-Review

- **Spec coverage:** balancing (Task 2), Facturado (Tasks 5–6), PU docs (Task 8), review status (Task 3), empty allowed (Task 4), export safety (Task 7), tests (Task 1 + each task), cleanup (Task 9), docs/repo/build (Task 11), final verification (Task 12).
- **Type consistency:** `note_kind` returns strings; `already_billed` is an int stat and a list in the report; `billed_skipped` is an int in driverlogs; `write_output` returns `skipped`.
- **Review focus:** each of the five failure modes has an owning test (Tasks 2–7).
- **Proportion:** the plan is longer than the diff because it covers a full audit; each task is independently reviewable and ends with a test/verification and commit.
