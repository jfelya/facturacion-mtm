"""Orchestrate the full job: scan sources -> parse -> fill -> result for UI/CLI."""
import re
from pathlib import Path
from datetime import timedelta

from .parsers import classify, parse_claim, parse_resumen, parse_trips, parse_drivers
from .filler import fill_claim


def _iter_xlsx(folder):
    for f in sorted(Path(folder).glob("*.xlsx")):
        if f.name.startswith("~$"):
            continue
        yield f
    for f in sorted(Path(folder).glob("*/*.xlsx")):
        if f.name.startswith("~$"):
            continue
        yield f
    # deeper levels (skip temp files)
    for f in sorted(Path(folder).glob("*/*/*.xlsx")):
        if f.name.startswith("~$"):
            continue
        yield f


def scan_driverlogs(folder):
    """Set of driver numbers that HAVE a driverlog template in `folder`.

    Template names look like `200 JORGE NINO DRIVERLOG VACIO.docx` (leading number).
    Files without a leading number (e.g. `MARINES PENA ...`) are ignored.
    """
    nums = set()
    if not folder:
        return nums
    for f in Path(folder).glob("*.docx"):
        if f.name.startswith("~$"):
            continue
        m = re.match(r"\s*(\d+)\b", f.stem)
        if m:
            nums.add(m.group(1))
    return nums


def _numsort(n):
    return (0, int(n)) if str(n).isdigit() else (1, str(n))


def scan_sources(folder, drivers_path=None):
    """Classify every xlsx under `folder` (up to 3 levels). Never fails on bad files."""
    folder = Path(folder)
    out = {"resumen": [], "trips": [], "drivers": [], "claim": []}
    for f in _iter_xlsx(folder):
        try:
            kind = classify(f)
        except Exception:
            kind = None
        if kind in ("resumen", "trips", "drivers", "claim"):
            out[kind].append(f)

    drivers = None
    if drivers_path and Path(drivers_path).exists():
        drivers = Path(drivers_path)
    elif out["drivers"]:
        drivers = out["drivers"][0]
    else:
        # common layout: sources folder is a subfolder and the drivers file sits in its parent
        parent = folder.parent
        for cand in sorted(parent.glob("*.xlsx")):
            if cand.name.startswith("~$"):
                continue
            try:
                if classify(cand) == "drivers":
                    drivers = cand
                    break
            except Exception:
                pass
    out["drivers_file"] = drivers
    return out


def build_resumen_index(files, warnings, usage=None):
    """One file per date wins (path order); conflicting copies are reported.

    If `usage` is given, it is filled with {date: {'mtm': set(), 'any': set()}}
    of every driver number seen that day (any payer / MTM only).
    """
    index = {}
    owner = {}
    seen_pairs = set()
    for f in files:
        if "original" in f.name.lower():
            continue
        try:
            parsed = parse_resumen(f)
        except Exception as e:
            warnings.append(f"No pude leer {f.name}: {type(e).__name__}")
            continue
        if not parsed:
            continue
        if usage is not None:
            for e in parsed:
                if not e["date"] or not e["driver"]:
                    continue
                if e.get("note_kind") == "billed":
                    continue
                # Dalia's SafeRide/Alivi rows are NOT our billing: ignore them entirely
                # (she is billed from the provider claim, and her driver is chosen by hand)
                if "DALIA" in e["name"].upper() and e["payer"].strip().upper() != "MTM":
                    continue
                u = usage.setdefault(e["date"], {"mtm": set(), "count": {}})
                u["count"][e["driver"]] = u["count"].get(e["driver"], 0) + 1
                if e["payer"].strip().upper() == "MTM":
                    u["mtm"].add(e["driver"])
        mtm = [e for e in parsed if e["payer"].strip().upper() == "MTM"]
        if not mtm:
            continue
        new_dates = {e["date"] for e in mtm} - set(owner)
        for e in mtm:
            key = (e["date"], e["name"])
            if e["date"] in new_dates:
                index.setdefault(key, []).append(e)
            else:
                other = index.get(key)
                if other and any(
                    o["driver"] != e["driver"] or o["miles"] != e["miles"]
                    or o["trip_id"] != e["trip_id"] for o in other
                ):
                    pair = (e["date"], owner.get(e["date"], "?"), str(f))
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        warnings.append(
                            f"OJO {e['date']}: hay más de un resumen con datos distintos "
                            f"({Path(owner.get(e['date'], '?')).name} y {f.name}); se usó el primero")
        for d in new_dates:
            owner[d] = str(f)
    return index


def build_trips(files, claim, warnings):
    claim_years = sorted({r["date"][:4] for r in claim["rows"] if r.get("date")})
    claim_dates = {r["date"] for r in claim["rows"] if r.get("date")}
    by_date = {}
    for f in files:
        try:
            parsed = parse_trips(f)
        except Exception as e:
            warnings.append(f"No pude leer el archivo de viajes {f.name}: {type(e).__name__}")
            continue
        if not parsed:
            continue
        # filename date fallback: "10-05.xlsx"
        fdate = None
        m = re.search(r"(\d{2})-(\d{2})", f.stem)
        if m:
            for y in claim_years:
                cand = f"{y}-{m.group(1)}-{m.group(2)}"
                if not claim_dates or cand in claim_dates:
                    fdate = cand
                    break
        got = 0
        for e in parsed:
            d = e["date"]
            if not d:
                d = fdate
            if d:
                by_date.setdefault(d, []).append(e)
                got += 1
        if got == 0:
            warnings.append(f"{f.name}: no pude determinar la fecha de sus viajes -> ignorado")
    return by_date


def run_job(claim_path, sources_folder, drivers_path=None, strategy="first_row_B",
            willcall_hours=2.0, suggest_driver=True, sort_by_date=True, spread=True, balance=True,
            pickup_ratio=1.4, pickup_buffer=14, pickup_jitter=3, driverlogs_folder=None):
    """Full pipeline. Returns {'claim', 'report', 'sources', 'claim_path'} or {'error'}."""
    claim_path = Path(claim_path)
    try:
        claim = parse_claim(claim_path)
    except Exception as e:
        return {"error": f"No pude leer el claim ({claim_path.name}): {type(e).__name__}: {e}"}
    if not claim or not claim["rows"]:
        return {"error": f"El archivo no parece un ClaimInformation con filas: {claim_path.name}"}

    warnings = []
    src = scan_sources(sources_folder, drivers_path)
    driver_usage = {}
    resumen_index = build_resumen_index(src["resumen"], warnings, driver_usage)
    trips_by_date = build_trips(src["trips"], claim, warnings)

    drivers = None
    if src["drivers_file"]:
        try:
            drivers = parse_drivers(src["drivers_file"])
        except Exception as e:
            warnings.append(f"No pude leer drivers ({Path(src['drivers_file']).name}): {type(e).__name__}")
    if not drivers:
        warnings.append("NO se encontró Informacion de Drivers.xlsx -> License/VIN quedarán en blanco")
    else:
        # a driver must be in the list AND (if a driverlogs folder was given) have a template
        allowed = set(drivers["table"])
        if driverlogs_folder:
            tpl = scan_driverlogs(driverlogs_folder)
            if tpl:
                missing = sorted(allowed - tpl, key=_numsort)
                if missing:
                    warnings.append("Drivers en la lista pero SIN plantilla de driverlog "
                                    "(se reemplazarán por uno libre que sí tenga): "
                                    + ", ".join(missing))
                allowed &= tpl
        drivers["allowed"] = allowed

    report = fill_claim(
        claim, resumen_index, trips_by_date, drivers,
        strategy=strategy, willcall_delta=timedelta(hours=willcall_hours),
        driver_usage=driver_usage, suggest_driver=suggest_driver, spread=spread, balance=balance,
        pickup_ratio=pickup_ratio, pickup_buffer=pickup_buffer, pickup_jitter=pickup_jitter,
    )
    report["warnings"] = warnings + report["warnings"]
    st = report["stats"]
    st["resumen_files"] = len(src["resumen"])
    st["trips_files"] = len(src["trips"])
    st["drivers_file"] = str(src["drivers_file"] or "")

    # group the output by day (chronological) and, inside each day, sort by DRIVER number
    # (rows with no driver go last). Keeps the claim order for ties.
    if sort_by_date:
        def _sort_key(r):
            d = str(r.get("driver") or "")
            try:
                dn = int(d)
            except (TypeError, ValueError):
                dn = 10 ** 9
            return (r.get("date") or "", dn, r.get("row") or 0)
        claim["rows"].sort(key=_sort_key)

    return {"claim": claim, "report": report, "sources": src, "claim_path": str(claim_path),
            "drivers": drivers}
