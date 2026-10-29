# Facturación MTM — Audit & Revamp Design

**Date:** 2026-10-28
**Status:** Proposed — awaiting approval
**Scope:** fix confirmed correctness and data-loss bugs, keep portal output formats, add a repeatable test suite, then do behavior-preserving cleanup.

## Intent

The app works on the current October batch, but the newest balancing rule measurably lowers driver accuracy, the export path can overwrite the source claim, and the “Facturado.” notes are not handled as a billing rule. The revamp fixes those issues without redesigning the matching engine or changing the portal file formats.

## Goals

- Balancing may move only unmatched/suggested rows. It must never override a summary match, a note-pinned driver, or Dalia’s preferred driver.
- Rows whose summary note says “Facturado” (already billed) are excluded from the claim Excel, BULK UPLOAD and generated driverlogs, and listed in the report.
- “Facturar manualmente … auto N” remains billable and keeps using driver N.
- PU/DropOff keeps the current physical sequence: dropoff 1–5 minutes before the appointment, PU earlier by the calibrated travel time. Docs and tests are corrected to match.
- Export refuses to overwrite the source claim and shows a friendly error when a target file is locked.
- `revisar` rows are visible as REVISAR, never as OK.
- An empty allowed-driver set never falls back to “all drivers”.
- A small stdlib `unittest` suite covers the matching, notes, balancing, time rules, output filtering and export guard. No new runtime dependency.
- Dead code and duplicated helpers are removed. Docs describe the current behavior, not stale history.

## Non-goals

- No rewrite of the parser or matching engine.
- No new GUI framework, database, server or cloud service.
- No change to the 10-column claim format, one-sheet-per-day layout, flat-value rule, BULK template or driverlog template.
- No automatic handling of “Facturado” rows beyond skipping and reporting them.
- No change to the 32-bit one-file executable strategy.

## Decisions from the user

1. **Revamp scope:** fix bugs and keep formats. Refactor and add tests, but preserve the portal Excel/Word/BULK formats and correct business rules.
2. **Balancing:** matches win. Only unmatched or suggested rows may be moved; summary/ID/order matches, note-pinned drivers and preferred drivers are locked.
3. **“Facturado.”:** already billed. Exclude those rows from the claim export and BULK UPLOAD, and report them. This design also excludes them from newly generated driverlogs; if driverlogs must be retained for already-billed trips, that is a one-line change.
4. **PU timing:** keep the current 1–5 minute dropoff margin; update the docs and pin the behavior with tests.

## Approaches considered

- **A — Cleanup only:** delete dead code and add tests, change no behavior. Rejected: leaves the accuracy regression, the export overwrite risk and the “Facturado” ambiguity in place.
- **B — Fix confirmed bugs, keep formats:** targeted correctness fixes, tests, then behavior-preserving cleanup. **Chosen.**
- **C — Free redesign:** restructure the engine and UI freely. Rejected: high risk for a working billing tool with no automated test net.

## Behavior changes

| Area | Before | After |
|---|---|---|
| Balancing | Can move any matched row | Moves only unmatched/suggested rows; never preferred drivers |
| “Facturado.” note | Row is billed and marked NOTA | Row is marked FACTURADO, excluded from Excel/BULK/driverlogs, reported |
| “Facturar manualmente … auto N” | Billed with N | Unchanged |
| PU/DropOff | Dropoff 1–5 min before appointment; PU earlier by travel time | Unchanged; docs/tests corrected |
| Review flag | A row with driver+miles can show OK | Shows REVISAR |
| Allowed drivers | Empty set falls back to all drivers | Empty set means no allowed drivers |
| Export | Can write over the source claim | Refuses the source path; friendly error for locked files |

## Constraints

- Python 3.14; `openpyxl` 3.1.5; `python-docx` 1.2.0; PyInstaller 6.22.3 only for builds.
- Tests use the standard library `unittest`; no new runtime package.
- Never modify originals. Outputs are new files; the BULK template and driverlog templates are read-only.
- Same input must produce the same output (deterministic jitter, sorted days/drivers).
- `data/` stays out of git. `docs/`, `tests/` and `selftest.py` become tracked.
- The root `.exe` remains the 32-bit universal build.

## Risks

- **False “Facturado” match:** a note that means something else could be skipped. Mitigation: match only notes beginning with “Facturado”/“Ya facturado”, report every skipped row, and test both “Facturado” and “Facturar manualmente”.
- **Weaker balancing:** drivers can exceed 3 trips when all their rows are matched. This is accepted; a warning lists blocked overloads.
- **Output changes:** rows previously billed with a “Facturado” note disappear from the exports. This is intentional and visible in the report.
- **Test fixtures must be synthetic:** no production data in `tests/`.

## Approval

This design is approved when the user approves the plan at
`docs/superpowers/plans/2026-10-28-audit-revamp.md`. No production code is changed before that approval.
