"""Self-test: run the filler against FINISHED September claims and measure accuracy.

Metrics per strategy:
  exacto     - driver + milage match what you filled by hand
  revisar    - engine deliberately left driver blank (unapproved number) -> your manual pick
  sin_dato   - no MTM resumen data for that member/day
  *_mal      - filled but differs from your hand-filled value
Also verifies License/VIN reproduction (should be ~100% whenever driver matches).
"""
import sys
import copy
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from app.parsers import parse_claim, parse_resumen, parse_drivers
from app.common import norm_num, s
from app.filler import fill_claim

DATA = ROOT / "data"
BASE = DATA / "base"                      # working data (current job)
LISTOS = DATA / "test" / "Trips" / "Listos"     # finished September claims (test)
RESDIR = DATA / "test" / "Trips" / "Resumenes"  # September resúmenes (test)

STRATEGIES = ("first_row_A", "first_row_B", "pair")


def main():
    drivers = parse_drivers(BASE / "Informacion de Drivers.xlsx")
    print(f"drivers parsed: {len(drivers['table'])}")

    resumen_index = {}
    covered = set()
    for f in sorted(LISTOS.glob("*/RESUMEN*.xlsx")) + sorted(RESDIR.glob("RESUMEN*.xlsx")):
        if "original" in f.name.lower():
            continue
        parsed = parse_resumen(f)
        if not parsed:
            continue
        dates = {e["date"] for e in parsed}
        new_dates = dates - covered
        if not new_dates:
            continue
        for e in parsed:
            if e["date"] in new_dates and e["payer"].strip().upper() == "MTM":
                resumen_index.setdefault((e["date"], e["name"]), []).append(e)
        covered |= new_dates
    print(f"resumen dates covered: {len(covered)}")

    claim_files = (sorted(LISTOS.glob("09-*/ClaimInformation*.xlsx"))
                   + sorted(LISTOS.glob("ClaimInformation*.xlsx")))

    totals = {st: Counter() for st in STRATEGIES}
    per_day = {st: defaultdict(Counter) for st in STRATEGIES}
    samples = {st: [] for st in STRATEGIES}
    fill_stats = {st: Counter() for st in STRATEGIES}
    lic = Counter()
    diff_rows = 0

    for f in claim_files:
        claim = parse_claim(f)
        if not claim or not claim["rows"]:
            print("  skip claim:", f.name)
            continue
        expected = []
        for r in claim["rows"]:
            edrv, emi = norm_num(r["driver"]), r["milage"]
            if edrv and emi is not None:
                expected.append((r["trip"], edrv, emi, r["date"], r["license"], r["vin"]))
        if not expected:
            print(f"  no evaluable rows: {f.name}")
            continue
        print(f"\nclaim: {f.parent.name}/{f.name} | rows={len(claim['rows'])} evaluable={len(expected)}")

        results = {}
        for st in STRATEGIES:
            c = copy.deepcopy(claim)
            for r in c["rows"]:
                r["driver"], r["milage"] = "", None
                r["license"] = r["vin"] = ""
                r["pu"] = None
                r["flag"] = ""
            report = fill_claim(c, resumen_index, {}, drivers, strategy=st)
            by_trip = {r["trip"]: r for r in c["rows"]}
            results[st] = by_trip
            for k, v in report["stats"].items():
                fill_stats[st][k] += v

            for trip, edrv, emi, date, elic, evin in expected:
                r = by_trip[trip]
                gdrv = norm_num(r["driver"]) if r["driver"] else ""
                gmi = r["milage"]
                if not gdrv and not gmi:
                    cat = "revisar" if r.get("flag") == "revisar" else "sin_dato"
                elif not gdrv or gmi is None:
                    cat = "revisar" if r.get("flag") == "revisar" else "parcial_mal"
                else:
                    dok = gdrv == edrv
                    mok = abs(gmi - emi) < 1e-6
                    cat = "exacto" if (dok and mok) else ("driver_mal" if mok else ("miles_mal" if dok else "ambos_mal"))
                totals[st][cat] += 1
                per_day[st][date][cat] += 1
                if cat in ("driver_mal", "miles_mal", "ambos_mal", "parcial_mal") and len(samples[st]) < 12:
                    samples[st].append(
                        f"  {date} {trip} {r['member'][:24]}: esperado {edrv}/{emi} -> "
                        f"obtenido {gdrv or '-'}/{gmi if gmi is not None else '-'} [{cat}]")
                if cat == "exacto" and st == STRATEGIES[-1]:
                    lic["rows"] += 1
                    if s(elic) and s(r["license"]) == s(elic):
                        lic["license_ok"] += 1
                    elif s(elic):
                        lic["license_bad"] += 1
                    if s(evin) and s(r["vin"]) == s(evin):
                        lic["vin_ok"] += 1
                    elif s(evin):
                        lic["vin_bad"] += 1

        for trip, _, _, _, _, _ in expected:
            a, b = results["first_row_A"][trip], results["first_row_B"][trip]
            if (norm_num(a["driver"]), a["milage"]) != (norm_num(b["driver"]), b["milage"]):
                diff_rows += 1

    print("\n" + "=" * 90)
    for st in STRATEGIES:
        t = totals[st]
        total = sum(t.values())
        exact = t["exacto"]
        revisar = t["revisar"]
        pct = 100 * exact / total if total else 0
        pct2 = 100 * exact / (total - revisar - t["sin_dato"]) if (total - revisar - t["sin_dato"]) else 0
        print(f"\n### {st}: {total} filas | exacto {exact} ({pct:.1f}%) | "
              f"sobre asignables {exact}/{total - revisar - t['sin_dato']} ({pct2:.1f}%)")
        print(f"    revisar {revisar} | sin_dato {t['sin_dato']} | driver_mal {t['driver_mal']} | "
              f"miles_mal {t['miles_mal']} | ambos_mal {t['ambos_mal']} | parcial_mal {t['parcial_mal']}")
        fs = fill_stats[st]
        print(f"    fill: id_matched={fs['id_matched']} order={fs['order_assigned']} no_data={fs['no_data']} "
              f"flagged={fs['flagged_unapproved']} note_override={fs['note_overrides']}")
        for line in samples[st]:
            print(line)

    print(f"\nlicense/VIN check on exacto rows: {dict(lic)}")
    print(f"rows where strategies differ: {diff_rows}")

    print("\nper-day (A = first_row_A, B = first_row_B):")
    dates = sorted(set(per_day["first_row_A"]) | set(per_day["first_row_B"]))
    for d in dates:
        a = dict(per_day["first_row_A"][d])
        b = dict(per_day["first_row_B"][d])
        print(f"  {d}:  A {a}   B {b}")


if __name__ == "__main__":
    main()
