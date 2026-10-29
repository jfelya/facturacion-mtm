# Facturación MTM — Current Project Notes

> **Last updated:** 2026-10-28. This is the current source of truth.
> History and old decisions: `docs/HISTORY.md`. Time calibration: `docs/PU_TIME_FINDINGS.md`.
> Portability/build details: `docs/PORTABILITY.md`.

## 1. Purpose

Windows desktop app that takes the MTM `ClaimInformation` downloaded from the portal, fills it with
the business's daily summaries, trip files and driver data, and exports:

- the finished **ClaimInformation Excel** (one sheet per day),
- one **BULK UPLOAD** Excel per day,
- the **Word driverlogs** per driver/day.

The user reviews the preview, confirms suggested drivers, and uploads the outputs to MTM.

## 2. Current status (2026-10-28)

- v4 audit/revamp: matching accuracy restored, already-billed rows skipped, export overwrite guarded,
  review flags visible, empty allowed-driver set fixed, dead code removed, tests added.
- 39 stdlib `unittest` tests pass.
- September benchmark: `first_row_B` **46/70 exact (65.7%)** with the current default settings.
- October batch: 81 claim rows, 9 summaries, 9 trip files; no matched row currently carries a
  `Facturado.` note, so the skip rule is exercised by synthetic tests and is ready for future batches.

## 3. Environment

- Windows 10/11. The root `Facturacion MTM.exe` is a **32-bit one-file** build (runs on 32- and
  64-bit Windows), version **2.4.0.0** (rebuilt 2026-10-28). A 64-bit build is optional and kept in
  `dist\` when built.
- Python 3.14.6 on this machine:
  `C:\Users\Fely\AppData\Local\Python\pythoncore-3.14-64\python.exe`.
- Runtime: `openpyxl==3.1.5`, `python-docx==1.2.0`, Tkinter (stdlib).
- Build: `pyinstaller==6.22.3` (`requirements-build.txt`).
- Icon generation (`assets/ui/make_icons.py`) needs Pillow, dev-only. Pillow is not a runtime dep.

## 4. Project map

```
Facturacion MTM/
├── Facturacion MTM.exe       # current 32-bit universal build (root)
├── run_app.py                # GUI or --cli entry point
├── selftest.py               # September accuracy benchmark (not a unit test)
├── build.ps1                 # PyInstaller build + copy root exe
├── requirements.txt          # runtime
├── requirements-build.txt    # runtime + PyInstaller
├── app/
│   ├── common.py             # normalization, dates/times, notes, shared helpers
│   ├── parsers.py            # claim/resumen/trips/drivers detection + parsing
│   ├── filler.py             # matching, approvals, notes, suggestions, balancing, PU/DropOff
│   ├── pipeline.py           # scan -> indexes -> fill -> result
│   ├── writer.py             # final ClaimInformation Excel
│   ├── bulk.py               # BULK UPLOAD Excel
│   ├── driverlogs.py         # Word driverlogs
│   ├── report.py             # text/CSV report
│   ├── strings.py            # ES/EN UI text
│   ├── uikit/                # Tkinter design tokens/widgets
│   └── ui.py                 # Tkinter UI
├── tests/                    # stdlib unittest + synthetic fixtures
├── docs/                     # NOTES, HISTORY, calibration, portability
├── assets/                   # app icon + UI PNGs
└── data/                     # production/test data (gitignored)
```

## 5. Inputs

Detection is by **structure**, never by filename. Renaming a file is safe.

| Type | What it is |
|---|---|
| Claim | `ClaimInformation … OLD.xlsx` (17 portal columns) or NEW layout. Required: Trip Number, Appt. Date, member name, provider cost. |
| Resumen | Daily `RESUMEN FACTURACION` summary: date, member name, payer, driver number, miles, optional Trip ID/notes. Layout varies by day; the parser tolerates aliases and duplicate rows. |
| Trips | Daily provider export (`10-05.xlsx` style): Trip Number, Appointment Date, Time, Trip Mileage, Trip Cost, member names, pickup city. |
| Drivers | `Informacion de Drivers.xlsx`, sheet `Vehiculos`: NUMERO, DRIVER, COUNTY, LICENSE NUMBER, VIN Number. |

Only **MTM** rows from a resumen feed billing. SafeRide/Alivi rows for Dalia are ignored. Other payers
can count toward a driver's workload but do not become claim rows.

## 6. Outputs

### ClaimInformation Excel
- One sheet per day, named `MM-DD`, chronological.
- Rows ordered by driver number inside each day; rows without a driver go last.
- Exactly 10 columns:
  `Driver | License | VIN | Appt. Date | Trip Number | Member Info | PU Time | DropOff Time | Milage | Cost`.
- Driver = number; Milage = number; PU/DropOff = real Excel time with `h:mm`; Cost = text `$x.xx`.
- Flat values only; no formulas.
- `NO FACTURAR` rows stay in the Excel with a blank driver for traceability. `FACTURADO` rows are
  excluded completely (see §7.4).

### BULK UPLOAD
- One `BULK UPLOAD MM-DD-YYYY.xlsx` per day in `<days_root>\<MM-DD>\`.
- `Export Trip` sheet, 10 columns, cloned from `app/assets/bulk_template.xlsx`.
- Driver = License, Vehicle = VIN, ScheduledPickup = PU, ScheduledDropoff = appointment (or the
  computed return dropoff for Will Call), TripLogSignature = `Y`.
- Reported times are simulated with deterministic jitter; B never arrives before A drops off.
- Only billable rows (driver present, not `NO FACTURAR`, not `FACTURADO`).

### Driverlogs
- One filled copy per driver/day in `<days_root>\<MM-DD>\Docs\<MM-DD> <NUM>.docx`.
- Templates are never modified; only the data rows are written.
- `FACTURADO` rows and drivers without a template are skipped.

### Report
- Screen report + optional CSV: sources, stats, warnings, review items, suggested drivers,
  manual choices, no-bill rows, and already-billed rows.

## 7. Matching and filling rules

1. **Only claim rows are billed.** A resumen row without a claim row is listed as a warning; it does
   not create a new claim row.
2. **Match by member name + date.** If the resumen has a populated Trip ID, an exact Trip Number
   match wins.
3. **Legs A/B.** Default `first_row_B`: first resumen row → B leg, second → A leg (one driver per leg).
   `pair` uses the same driver on both legs; `first_row_A` reverses the order. Milage follows the
   resumen order (the pair strategy still uses the `first_row_B` milage pairing).
4. **Notes.**
   - `Facturado.` / `Ya facturado.` → row is **already billed**: flag `FACTURADO`, excluded from the
     claim Excel, BULK and new driverlogs; listed in the report. It also does not count as workload
     for driver suggestions.
   - Only an **exact Trip ID** match auto-marks a claim row as `FACTURADO`. If a member/day group has
     both billed and normal resumen rows without Trip IDs, the billed rows are excluded from the
     order-based pairing, the group is flagged `REVISAR`, and every billed resumen row is listed.
     The app never silently skips a new trip by pairing it with an already-billed row.
   - A B-leg time warning (`B` before `A`) never clears the `FACTURADO` flag.
   - `Facturar manualmente. Driver X, auto N.` → still billable; driver N wins if approved.
   - Other notes (`Facturación manual.`, etc.) → normal note; row stays billable and appears as `NOTA`
     for review.
5. **Approved drivers.** A driver must be in `Informacion de Drivers.xlsx`. When a driverlogs folder
   is provided, the driver must also have a template (`<NUM> … DRIVERLOG VACIO.docx`).
   `allowed = driver list ∩ templates`. An **empty** driverlogs folder means **no driver is approved,
   accepted or suggested** (not “fall back to all”). `999` is a placeholder: excluded from
   suggestions/balancing; no 999 appears in current summaries.
6. **Dalia.** If the claim has a Dalia row without an MTM resumen, it is billable and the app suggests
   the least-busy approved driver of that day/county, preferring `349`. A resumen note `auto 309`
   overrides the preference (as on 10-14/10-15).
7. **No resumen / no bill.** A non-Dalia claim row with no MTM resumen row is flagged `NO FACTURAR`.
   It stays in the Excel with a blank driver but is not included in BULK or driverlogs.
8. **County.** Drivers only serve their own county (VOLUSIA or MARION). County comes from the resumen
   driver, else the other leg, else the trip's pickup city.
9. **Soft balancing.** Only **unmatched/suggested** rows may move: never a row matched by Trip ID,
   order, or note, and never a preferred driver. If a driver is over 3 trips but every row is locked,
   the report says `REPARTO BLOQUEADO`. Drivers may exceed 3 when matches win.
10. **Milage fallback.** If the resumen has no miles, use the trip file's `Trip Mileage` for that Trip
    Number (covers Dalia).
11. **PU/DropOff.** The trip file `Time` is the appointment, not the pickup:
    - `DropOff = appointment − 1..5 min` (deterministic jitter).
    - `PU = DropOff − (14 min + 1.4 × miles ± 3 min)`.
    - Will Call: `PU = A-leg appointment + 2 h − 1..3 min`; dropoff = PU + travel time.
    See `docs/PU_TIME_FINDINGS.md` and `tests/test_pickup.py`.

## 8. UI and CLI

GUI: `python run_app.py` (or double-click the exe).

Steps: claim → sources folder → optional drivers file → optional driverlog templates → optional days
root → **Procesar**. Review the colored preview, use **Asignar driver** for suggested/empty rows, then
**Exportar Excel**, **Generar driverlogs**, **Generar BULK UPLOAD**.

Status colors: OK, NOTA, SUGERIDO, BALANCEADO, REVISAR, ELEGIR, NO FACTURAR, FACTURADO, SIN DATO.
Language (ES/EN) and dark/light theme are toggles in the header.

CLI examples:

```
python run_app.py --cli "<claim.xlsx>" "data\base" --out "output\salida.xlsx"
python run_app.py --cli "<claim.xlsx>" "data\base" --strategy pair
python run_app.py --cli "<claim.xlsx>" "data\base" --gen-bulk --days-root "…\1. PARA FACTURAR"
python run_app.py --cli "<claim.xlsx>" "data\base" --gen-driverlogs --driverlogs "<plantillas>" --days-root "<raíz>"
```

Excel and CSV export refuse to write over the source claim. A locked target file shows an error instead
of crashing.

## 9. Tests and build

```powershell
$py = "C:\Users\Fely\AppData\Local\Python\pythoncore-3.14-64\python.exe"
& $py -m unittest discover -s tests -v   # 39 tests, synthetic fixtures, no data/ needed
& $py selftest.py                        # September accuracy benchmark
.\build.ps1                              # PyInstaller + copy root exe (32-bit Python path by default)
```

`tests/` uses stdlib `unittest` only. `selftest.py` is a benchmark, not a pass/fail gate; its current
`first_row_B` result is 46/70 exact.

The build script defaults to the portable 32-bit Python at `%TEMP%\opencode\py32\python\python.exe`.
If that path does not exist, pass `-Python <path>` or build a 64-bit exe for a smoke test; the root exe
remains the 32-bit universal build.

## 10. Data and git

- `data/` is **gitignored** and contains production/test business data. Never commit it.
- `docs/`, `tests/` and `selftest.py` are tracked.
- Never modify the input claim, the BULK template or the driverlog templates. Outputs are new files.
- Same input → same output: the jitter is deterministic and days/drivers are sorted.
- `git status` should not show generated `output/`, `build*/`, `dist*/` or `*.exe`.

## 11. Known limitations / open questions

- The exact meaning of “separar viajes MTM de ACCESS2CARE” (training step 2) is still open.
- Balancing intentionally does less now: matched drivers can exceed 3 trips; the report lists them.
- The `Facturado.` skip applies only when the matched resumen row carries that note. The current
  October batch has no such matched row.
- A future resumen that uses driver `999` directly could still be accepted if 999 is in the drivers
  list and no template restriction is active; it is excluded from suggestions/balancing only.
- The Excel output includes `NO FACTURAR` rows with a blank driver; BULK/driverlogs exclude them.
- Windows + Excel are the target; no server, database or multi-user mode.
