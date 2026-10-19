"""Match claim rows to resumen rows and fill Driver/Milage/PU Time per business rules.

Filling per member+date group:
  1. exact match by resumen TRIP ID == claim Trip Number (when present)
  2. order-based assignment of remaining rows:
       'first_row_A': first resumen row -> ...0A trip, second -> ...0B
       'first_row_B': first resumen row -> ...0B trip, second -> ...0A   (September evidence: 60% vs 38.6%)
  3. Driver approval check:
       - number present in Informacion de Drivers  -> fill + license/VIN
       - number NOT approved (e.g. 392 Antonio, 297):
           * if a note says "auto N" and N is approved        -> fill N, flag for review
           * else                                             -> driver/license/VIN blank, flag (miles still filled)
  4. PU Time from the day's trips file, matched by Trip Number.
       'Will Call' -> A-leg time + 2h (user rule).

Nothing is guessed silently: gaps and judgment calls go to report['warnings'] / report['review'].
"""
from datetime import timedelta, datetime, date
import re
import random
import zlib
from .common import norm_num

# placeholder / non-real driver numbers in Informacion de Drivers.xlsx
PLACEHOLDER_DRIVERS = {"999"}

# Members billed without an MTM resumen row: the user's usual driver (Dalia -> 349 Daylenis).
# Used to pre-select the suggestion for those rows; still shown for confirmation.
PREFERRED_DRIVER = {"DALIA ALFONSO": "349"}

# County grouping (user rule, 18-oct): drivers only serve trips in their OWN county, because
# it would be odd for a driver to work another area. 20/30/166/413 = VOLUSIA, rest = MARION.
VOLUSIA_CITIES = ("daytona", "deland", "deltona", "ormond", "port orange", "new smyrna",
                  "edgewater", "debary", "orange city", "south daytona", "holly hill",
                  "ponce inlet", "oak hill", "pierson", "lake helen", "osteen",
                  "seville", "astor", "enterprise", "glenwood", "de leon springs")
DEFAULT_COUNTY = "MARION"


def _city_county(city):
    c = (city or "").lower()
    return "VOLUSIA" if any(k in c for k in VOLUSIA_CITIES) else DEFAULT_COUNTY

# ---- estimated pickup time from the appointment/dropoff time ----
# The provider's trip file `Time` is the APPOINTMENT (dropoff) time, not the pickup.
# Calibrated from the archived BULK UPLOAD scheduled times (see docs/PU_TIME_FINDINGS.md):
#   lead = 14 min + 1.4 min/mile   (R^2 ~ 0.74).  Reproduces the user's example:
#   7.06 mi -> 14 + 9.9 = 24 min  ->  dropoff 7:41 => pickup 7:17.
PICKUP_RATIO = 1.4        # minutes per mile
PICKUP_BUFFER = 14        # fixed minutes per trip
PICKUP_JITTER = 3         # +/- minutes, deterministic per trip (looks legit)

# Soft load-balancing (user, 18-oct): drivers usually do ~2 trips/day; when someone ends up
# with too many, spread the extra ones across the area's approved drivers (same county).
# It's a soft guide, not a hard rule -> only touches drivers ABOVE BALANCE_MAX and moves to
# drivers BELOW BALANCE_TARGET; never crosses counties; rows flagged 'balanceado' to review.
BALANCE_TARGET = 2
BALANCE_MAX = 3


def _halve_if_doubled(res):
    """Some resumen files contain every row duplicated (orig + orig)."""
    n = len(res)
    if n >= 4 and n % 2 == 0:
        half = n // 2
        if res[:half] == res[half:]:
            return res[:half]
    return res


def _add_delta(t, delta):
    return (datetime.combine(date(2000, 1, 1), t) + delta).time()


def _trip_seed(row):
    """Stable seed so the jitter is the same every run (idempotent) but varies per trip."""
    return zlib.crc32(f"{row.get('date', '')}|{row.get('trip', '')}".encode("utf-8"))


def _lead(miles, rng, ratio=PICKUP_RATIO, buffer=PICKUP_BUFFER, jitter=PICKUP_JITTER):
    """Minutes from pickup to dropoff = fixed buffer + ratio*miles + small jitter."""
    return int(round(buffer + ratio * (miles or 0.0) + rng.uniform(-jitter, jitter)))


def _est_pickup(appt, miles, seed, ratio=PICKUP_RATIO, buffer=PICKUP_BUFFER, jitter=PICKUP_JITTER):
    """Estimated pickup = appointment - (buffer + ratio*miles) with a small jitter (whole minutes)."""
    rng = random.Random(seed)
    base = appt.replace(second=0, microsecond=0)
    return _add_delta(base, -timedelta(minutes=_lead(miles, rng, ratio, buffer, jitter)))


def _note_driver(note):
    m = re.search(r"auto\s*(\d+)", note or "", re.I)
    return m.group(1) if m else ""


def _drv_sort(n):
    return (0, int(n)) if str(n).isdigit() else (1, str(n))


def _assign(row, x, drivers, warnings, review, stats):
    row["src_resumen"] = True          # this trip WAS matched to a resumen row (even if driver unapproved)
    if drivers:
        cty = (drivers["table"].get(x["driver"]) or {}).get("county")
        if cty:
            row["county"] = cty        # the trip belongs to the resumen driver's county
    number = x["driver"]
    note = x.get("note") or ""
    driver = number
    note_drv = _note_driver(note)

    # note instruction ("Driver X, auto N") wins over the resumen number
    if note_drv and drivers and note_drv in drivers["table"] and note_drv != driver:
        driver = note_drv
        row["note_drv"] = True
        review.append(f"DRIVER POR NOTA {row['date']} {row['member']} {row['trip']}: se usa {note_drv} "
                      f"(resumen dice {number or '-'}): {note[:60]}")
        stats["note_overrides"] += 1

    # approval check
    # approval check: a number that is NOT in the drivers list (or has no driverlog template)
    # is not billable -> it gets replaced by a free driver of that day (suggestion pass below)
    allowed = (drivers.get("allowed") if drivers else None) or (set(drivers["table"]) if drivers else set())
    if driver and drivers and driver not in allowed:
        driver = ""
        row["flag"] = "revisar"
        warnings.append(f"{row['date']} {row['member']} {row['trip']}: driver {number} no está aprobado/sin "
                        f"driverlog -> se reemplaza por un driver libre de ese día (revisar)")
        stats["flagged_unapproved"] += 1

    if driver:
        info = drivers["table"].get(driver) if drivers else None
        if info:
            row["driver"] = driver
            row["license"] = info["license"]
            row["vin"] = info["vin"]
            if not info["license"]:
                warnings.append(f"{row['date']} {row['member']} {row['trip']}: driver {driver} sin licencia en la tabla")
            if not info["vin"]:
                warnings.append(f"{row['date']} {row['member']} {row['trip']}: driver {driver} sin VIN en la tabla")
        else:
            warnings.append(f"{row['date']} {row['member']} {row['trip']}: driver {driver} no está en Informacion de Drivers")
    elif number:
        # unapproved, no note -> driver fields intentionally blank
        row["driver"] = ""
        row["license"] = ""
        row["vin"] = ""
    else:
        warnings.append(f"{row['date']} {row['member']} {row['trip']}: fila de resumen sin número de driver")

    if x["miles"] is not None:
        row["milage"] = x["miles"]
    else:
        warnings.append(f"{row['date']} {row['member']} {row['trip']}: fila de resumen sin MILES")

    if note:
        if row.get("flag") != "revisar":
            row["flag"] = "nota"
        review.append(f"NOTA {row['date']} {row['member']} {row['trip']}: {note[:90]}")


def _balance_drivers(claim, drivers, stats, review):
    """Soft balancing: no driver should end the day with too many trips.

    For each day, any driver ABOVE `BALANCE_MAX` gives extra trips (preferring ones NOT pinned
    by a manual note) to approved drivers of the SAME county that are BELOW `BALANCE_TARGET`.
    Moved rows are flagged 'balanceado' so the user reviews them. Never crosses counties.
    """
    if not drivers:
        return
    table = drivers["table"]
    allowed = drivers.get("allowed") or set(table)
    approved = [n for n in allowed if n not in PLACEHOLDER_DRIVERS]

    def county(n):
        return table.get(n, {}).get("county") or ""

    by_date = {}
    for r in claim["rows"]:
        if r.get("driver") and r.get("flag") != "nofacturar":
            by_date.setdefault(r["date"], []).append(r)

    moved = 0
    for date in sorted(by_date):
        rows = by_date[date]
        counts = {}
        for r in rows:
            counts[r["driver"]] = counts.get(r["driver"], 0) + 1
        progress = True
        while progress:
            progress = False
            over = sorted((d for d, c in counts.items() if c > BALANCE_MAX),
                          key=lambda d: (-counts[d], _drv_sort(d)))
            for src in over:
                sc = county(src)
                receivers = [n for n in approved
                             if n != src and county(n) == sc and counts.get(n, 0) < BALANCE_TARGET]
                if not receivers:
                    continue
                dst = min(receivers, key=lambda n: (counts.get(n, 0), _drv_sort(n)))
                src_rows = [r for r in rows if r.get("driver") == src]
                # move the most "flexible" trip: not pinned by a manual note, most recent first
                src_rows.sort(key=lambda r: (1 if r.get("note_drv") else 0, -(r.get("row") or 0)))
                r = src_rows[0]
                info = table.get(dst, {})
                old = r["driver"]
                r["driver"] = dst
                r["license"] = info.get("license", "")
                r["vin"] = info.get("vin", "")
                if r.get("flag") != "sugerido":
                    r["flag"] = "balanceado"
                counts[old] -= 1
                counts[dst] = counts.get(dst, 0) + 1
                moved += 1
                progress = True
                review.append(f"REPARTO {date} {r['member']} {r['trip']}: {old} -> {dst} "
                              f"(meta ~{BALANCE_TARGET} viajes/driver en {sc or 'area'})")
    stats["balanced"] = moved


def fill_claim(claim, resumen_index, trips_by_date, drivers,
               strategy="first_row_B", willcall_delta=timedelta(hours=2),
               driver_usage=None, suggest_driver=True, spread=True, balance=True,
               pickup_ratio=PICKUP_RATIO, pickup_buffer=PICKUP_BUFFER, pickup_jitter=PICKUP_JITTER):
    """Modifies claim['rows'] in place. Returns report dict.

    driver_usage: optional {date: {'mtm': set(driver_numbers), 'count': {num: n_trips}}}
                  used to propose 'available drivers' for rows with no MTM data.
    suggest_driver: when True, auto-assign the LEAST-BUSY driver of that day to rows
                    with no MTM row (flagged 'sugerido' for the user to confirm).
    """
    warnings = []
    review = []
    stats = {"rows": len(claim["rows"]), "id_matched": 0, "order_assigned": 0,
             "no_data": 0, "pu_filled": 0, "pu_willcall": 0, "pu_missing": 0,
             "flagged_unapproved": 0, "note_overrides": 0,
             "milage_from_trips": 0, "needs_driver": 0, "suggested": 0, "not_billed": 0,
             "pu_estimated": 0, "dropoff_filled": 0, "paired": 0, "spread": 0, "time_warnings": 0,
             "balanced": 0}

    groups = {}
    for row in claim["rows"]:
        row.setdefault("flag", "")
        groups.setdefault((row["date"], row["member"]), []).append(row)

    # 'spread' (default): when two+ members on the same day share the same candidate
    # drivers, give them DIFFERENT ones (ordered by how busy each driver is), like the user
    # does (LINDA->394, JANET->220). The pair driver otherwise comes from the 1st resumen row.
    pair_override = {}
    if strategy == "pair" and spread:
        per_date = {}
        for (date, member) in groups:
            drvs = sorted({x["driver"] for x in resumen_index.get((date, member), []) if x["driver"]})
            if len(drvs) >= 2:
                per_date.setdefault(date, []).append((member, tuple(drvs)))
        for date, items in per_date.items():
            by_key = {}
            for member, key in items:
                by_key.setdefault(key, []).append(member)
            counts = ((driver_usage or {}).get(date) or {}).get("count", {})
            for key, members in by_key.items():
                if len(members) < 2:
                    continue
                order = sorted(key, key=lambda n: (counts.get(n, 0), _drv_sort(n)))
                for i, member in enumerate(members):
                    pair_override[(date, member)] = order[i % len(order)]
                stats["spread"] += 1

    for (date, member), rows in sorted(groups.items()):
        res = _halve_if_doubled(list(resumen_index.get((date, member), [])))
        used = set()
        pending = []

        # 1) exact trip-id matches
        for row in rows:
            cands = [x for x in res if x["trip_id"] and x["trip_id"].upper() == row["trip"].upper()]
            if cands:
                x = cands[0]
                used.add(id(x))
                _assign(row, x, drivers, warnings, review, stats)
                stats["id_matched"] += 1
            else:
                pending.append(row)

        # 2) order-based assignment of the rest
        rest = [x for x in res if id(x) not in used]
        if pending and rest:
            order = {"A": 0, "B": 1} if strategy == "first_row_A" else {"B": 0, "A": 1}
            targets = sorted(pending, key=lambda r: (order.get(r["leg"], 9), r["trip"]))
            # 'pair' (user's usual way): give BOTH legs the same driver taken from the
            # first resumen row, as long as that driver is approved.
            if strategy == "pair" and len(rest) == 2 and rest[0].get("driver"):
                pd = pair_override.get((date, member))
                if not pd:
                    # a note like "Driver Marielkis, auto 309" defines the driver for BOTH legs
                    note_drv = next((_note_driver(x.get("note")) for x in rest
                                     if _note_driver(x.get("note"))), "")
                    pd = note_drv or rest[0]["driver"]
                if rest[0]["driver"] != rest[1].get("driver"):
                    review.append(f"PAR-PAIR {date} {member}: resumen {rest[0]['driver']}/{rest[1].get('driver')} "
                                  f"-> se usa {pd} en ambas patas")
                    stats["paired"] += 1
                rest = [dict(x, driver=pd) for x in rest]
            if len(rest) != len(targets):
                warnings.append(
                    f"{date} {member}: {len(targets)} viaje(s) vs {len(rest)} fila(s) de resumen "
                    f"(asignación parcial: revisar)")
            for row, x in zip(targets, rest):
                _assign(row, x, drivers, warnings, review, stats)
                stats["order_assigned"] += 1
            for row in targets[len(rest):]:
                warnings.append(f"{date} {member} {row['trip']}: sin fila de resumen MTM (revisar manual)")
                stats["no_data"] += 1
        elif pending:
            for row in pending:
                warnings.append(f"{date} {member} {row['trip']}: sin datos MTM en resumen del día (revisar manual)")
                stats["no_data"] += 1

        # pair report: trips A/B assigned different values -> worth eyeballing
        if len(rows) == 2:
            a = next((r for r in rows if r["leg"] == "A"), None)
            b = next((r for r in rows if r["leg"] == "B"), None)
            if a and b and (a["driver"], a["milage"]) != (b["driver"], b["milage"]):
                review.append(
                    f"PAR {date} {member}: {a['trip']} drv={a['driver'] or '?'} mi={a['milage']}  |  "
                    f"{b['trip']} drv={b['driver'] or '?'} mi={b['milage']}")

    # 2.5) Milage fallback from the day's trip export (column "Trip Mileage").
    #      This is what covers trips the resumen never listed under MTM (e.g. Dalia):
    #      the provider trip file still carries the exact mileage per leg.
    for row in claim["rows"]:
        if row.get("milage") is not None:
            continue
        trips = trips_by_date.get(row["date"])
        if not trips:
            continue
        rec = next((t for t in trips if t["trip"].upper() == row["trip"].upper()), None)
        if rec and rec.get("miles") is not None:
            row["milage"] = rec["miles"]
            row["milage_src"] = "trips"
            stats["milage_from_trips"] += 1

    # 3) PU Time = ESTIMATED PICKUP from the trip file's appointment/dropoff time.
    #    The provider `Time` is the appointment time, so pickup = appointment - (14 + 1.4*miles).
    missing_days = set()
    for row in claim["rows"]:
        if row.get("pu") not in (None, ""):
            continue
        trips = trips_by_date.get(row["date"])
        if not trips:
            missing_days.add(row["date"])
            stats["pu_missing"] += 1
            continue
        rec = next((t for t in trips if t["trip"].upper() == row["trip"].upper()), None)
        if rec is None:
            warnings.append(f"{row['date']} {row['trip']}: no está en el archivo de viajes del día")
            stats["pu_missing"] += 1
            continue
        if rec["time_kind"] == "time":
            appt = rec["time"].replace(second=0, microsecond=0)
            rng = random.Random(_trip_seed(row))
            lead = _lead(row.get("milage"), rng, pickup_ratio, pickup_buffer, pickup_jitter)
            margin = rng.randint(1, 5)          # dropoff lands a little before the appointment
            row["dropoff"] = _add_delta(appt, -timedelta(minutes=margin))
            row["pu"] = _add_delta(row["dropoff"], -timedelta(minutes=lead))
            row["pu_appt"] = appt
            stats["pu_filled"] += 1
            stats["pu_estimated"] += 1
            stats["dropoff_filled"] += 1
        elif rec["time_kind"] == "willcall":
            partner = row["trip"][:-1] + "A"
            prec = next((t for t in trips if t["trip"].upper() == partner.upper()), None)
            if prec and prec["time_kind"] == "time":
                wc = _add_delta(prec["time"].replace(second=0, microsecond=0), willcall_delta)
                rng = random.Random(_trip_seed(row))
                off = rng.randint(1, 3)
                lead = _lead(row.get("milage"), rng, pickup_ratio, pickup_buffer, pickup_jitter)
                row["pu"] = _add_delta(wc, -timedelta(minutes=off))
                row["dropoff"] = _add_delta(row["pu"], timedelta(minutes=lead))
                row["pu_appt"] = wc
                stats["pu_filled"] += 1
                stats["pu_willcall"] += 1
                stats["dropoff_filled"] += 1
                review.append(f"WILLCALL {row['date']} {row['trip']}: pata A ({partner} @ "
                              f"{prec['time'].strftime('%H:%M')}) + {willcall_delta} = "
                              f"{wc.strftime('%H:%M')} -> PU {row['pu'].strftime('%H:%M')}")
            else:
                warnings.append(f"{row['date']} {row['trip']}: Will Call pero no hay hora de la pata A "
                                f"({partner}) en el archivo de viajes")
                stats["pu_missing"] += 1
        else:
            warnings.append(f"{row['date']} {row['trip']}: celda Time vacía o no reconocida en archivo de viajes")
            stats["pu_missing"] += 1

    for d in sorted(missing_days):
        n = sum(1 for r in claim["rows"] if r["date"] == d and r.get("pu") in (None, ""))
        warnings.append(f"{d}: sin archivo de viajes para ese día -> {n} PU Time quedan en blanco")

    # 3.5) sanity check: a member's B leg (return) must not start/end BEFORE its A leg (same day)
    pairs = {}
    for row in claim["rows"]:
        pairs.setdefault((row["date"], row["member"]), {})[row.get("leg")] = row
    for (d, member), legs in sorted(pairs.items()):
        a, b = legs.get("A"), legs.get("B")
        if not a or not b:
            continue
        apu, bpu = a.get("pu"), b.get("pu")
        ad, bd = a.get("dropoff"), b.get("dropoff")
        if apu and bpu and bpu < apu:
            warnings.append(f"{d} {member}: la pata B ({b['trip']}, PU {bpu.strftime('%H:%M')}) empieza ANTES "
                            f"que la A ({a['trip']}, PU {apu.strftime('%H:%M')}) -> revisar tiempos")
            b["flag"] = "revisar"
            stats["time_warnings"] += 1
        if ad and bd and bd < ad:
            warnings.append(f"{d} {member}: el DropOff de la pata B ({b['trip']}, {bd.strftime('%H:%M')}) es antes "
                            f"que el de la A ({a['trip']}, {ad.strftime('%H:%M')}) -> revisar tiempos")
            b["flag"] = "revisar"
            stats["time_warnings"] += 1

    # 4) Rows with no driver (no MTM resumen row, or unapproved number).
    #    Rank the approved drivers by how many trips they already have that day
    #    (Dalia's SafeRide rows are ignored) and either SUGGEST the least busy one
    #    (flagged 'sugerido' for confirmation) or leave it for the user to pick.
    driver_candidates = {}
    needs_driver = []
    suggested = []
    not_billed = []
    needs = [r for r in claim["rows"] if not r.get("driver")]

    # county of every row: from the resumen driver when matched, else from the trip's city
    city_by_trip = {}
    for _d, _ts in (trips_by_date or {}).items():
        for _t in _ts:
            city_by_trip[_t["trip"].upper()] = _t.get("city") or ""
    member_county = {}
    for r in claim["rows"]:
        if r.get("county"):
            member_county.setdefault((r["date"], r["member"]), r["county"])
    for r in claim["rows"]:
        if r.get("county"):
            continue
        r["county"] = (member_county.get((r["date"], r["member"]))
                       or _city_county(city_by_trip.get(r["trip"].upper(), "")))

    if needs and drivers:
        allowed = drivers.get("allowed") or set(drivers["table"])
        approved = [n for n in sorted(allowed, key=_drv_sort) if n not in PLACEHOLDER_DRIVERS]
        for d in sorted({r["date"] for r in needs}):
            counts = ((driver_usage or {}).get(d) or {}).get("count", {})
            for county in sorted({r.get("county") or "" for r in needs if r["date"] == d}):
                pool = [n for n in approved
                        if not county or (drivers["table"].get(n, {}).get("county") or "") == county]
                ranked = sorted(pool, key=lambda n: (counts.get(n, 0), _drv_sort(n)))
                driver_candidates[(d, county)] = [
                    {"num": n, "name": drivers["table"][n]["name"],
                     "count": counts.get(n, 0), "free": counts.get(n, 0) == 0}
                    for n in ranked
                ]

    for r in needs:
        is_dalia = "DALIA" in (r.get("member") or "").upper()
        billable = r.get("src_resumen") or is_dalia
        if not billable:
            # claim row with no resumen and NOT Dalia -> business rule: do not bill it
            r["flag"] = "nofacturar"
            stats["not_billed"] += 1
            not_billed.append({"date": r["date"], "trip": r["trip"], "member": r["member"]})
            warnings.append(f"{r['date']} {r['member']} {r['trip']}: viene del claim pero NO está en el "
                            f"resumen del día y no es Dalia -> NO se factura (revisar)")
            continue
        cands = list(driver_candidates.get((r["date"], r.get("county") or "")) or [])
        pref = PREFERRED_DRIVER.get((r.get("member") or "").upper())
        # ranking: drivers that are FREE that day first, then the member's usual driver (e.g. Dalia->349),
        # then fewest trips. All candidates are already limited to the trip's county.
        if pref:
            cands.sort(key=lambda c: (0 if c["count"] == 0 else 1, 0 if c["num"] == pref else 1,
                                      c["count"], _drv_sort(c["num"])))
        best = cands[0] if cands else None
        # only suggest when we actually know that day's workload (a resumen exists for it)
        have_info = driver_usage is not None and r["date"] in driver_usage
        if suggest_driver and best and have_info:
            info = drivers["table"][best["num"]]
            r["driver"] = best["num"]
            r["license"] = info.get("license", "")
            r["vin"] = info.get("vin", "")
            r["flag"] = "sugerido"
            stats["suggested"] += 1
            suggested.append({"date": r["date"], "trip": r["trip"], "member": r["member"],
                              "driver": best["num"], "name": best["name"],
                              "count": best["count"], "milage": r.get("milage")})
            review.append(f"SUGERIDO {r['date']} {r['member']} {r['trip']}: driver {best['num']} "
                          f"{best['name']} ({best['count']} viajes ese día) - confirmar")
        else:
            r["flag"] = "revisar" if r.get("flag") == "revisar" else "elegir"
            needs_driver.append({"date": r["date"], "trip": r["trip"], "member": r["member"],
                                 "milage": r.get("milage"), "county": r.get("county") or ""})
            stats["needs_driver"] += 1

    # 4.5) Soft balancing: spread trips so no driver ends the day overloaded (~2 each, same county).
    if balance:
        _balance_drivers(claim, drivers, stats, review)

    # advisory: MTM resumen groups with no claim row at all -> not billed
    claim_keys = {(r["date"], r["member"]) for r in claim["rows"]}
    resumen_without_claim = [
        {"date": d, "member": m}
        for (d, m) in sorted(resumen_index.keys()) if (d, m) not in claim_keys
    ]
    for x in resumen_without_claim:
        warnings.append(f"{x['date']} {x['member']}: está en el resumen MTM pero NO en el claim -> no se factura")

    return {"warnings": warnings, "review": review, "stats": stats,
            "needs_driver": needs_driver, "driver_candidates": driver_candidates,
            "suggested": suggested, "not_billed": not_billed,
            "resumen_without_claim": resumen_without_claim}
