"""Parsers for the four input types. Detection is by structure, never by filename.

Types:
  claim   - ClaimInformation from the MTM portal (OLD: raw 17 cols, or NEW: 9 cols)
  resumen - daily RESUMEN (driver number + miles per member)
  trips   - daily trip export (PU Time etc.), like 10-05.xlsx
  drivers - Informacion de Drivers.xlsx (license + VIN by driver number)
"""
import re
from .common import (
    s, nonempty, read_rows, norm_name, norm_num, to_iso, to_float,
    parse_time_value, fmt_mdy,
)


# ---------- classification ----------
def classify(path):
    try:
        rows, title, sheets = read_rows(path)
    except Exception:
        return None
    if not rows:
        return None
    hdr = [s(c) for c in rows[0]]
    hs = set(hdr)
    if "Vehiculos" in sheets or ({"LICENSE NUMBER", "NUMERO"} <= hs):
        return "drivers"
    if "Appt. Date" in hs or "Claim Status" in hs:
        return "claim"
    if ("DATE" in hs or "DTE" in hs) and "NAME" in hs and ({"MILES", "MILEAGE"} & hs):
        return "resumen"
    if "Appointment Date" in hs and "Trip Number" in hs:
        return "trips"
    return None


# ---------- claim ----------
def parse_claim(path):
    rows, title, sheets = read_rows(path)
    if not rows:
        return None
    hdr = [s(c) for c in rows[0]]
    if "Appt. Date" not in hdr and "Trip Number" not in hdr:
        return None

    def idx(*names):
        for n in names:
            if n in hdr:
                return hdr.index(n)
        return None

    i_trip = idx("Trip Number")
    i_date = idx("Appt. Date")
    i_mem_full = idx("Name (First and Last)")
    i_mem = idx("Member Info")
    i_member = i_mem_full if i_mem_full is not None else i_mem
    i_drv = idx("Driver")
    i_mi = idx("Milage", "Mileage")
    i_pu = idx("PU Time")
    i_lic = idx("License")
    i_vin = idx("VIN")
    i_pc = idx("Provider Cost")
    i_cost = idx("Cost")
    layout = "OLD" if "Claim Status" in hdr else "NEW"

    out = []
    for rn, r in enumerate(rows[1:], start=2):
        if all(v in (None, "") for v in r):
            continue
        trip = s(r[i_trip]) if i_trip is not None and i_trip < len(r) else ""
        if not trip:
            continue
        date_iso = to_iso(r[i_date]) if i_date is not None and i_date < len(r) else None
        member_up = norm_name(r[i_member]) if i_member is not None and i_member < len(r) else ""
        if not date_iso or not member_up:
            continue

        cost = ""
        if i_pc is not None and i_pc < len(r) and r[i_pc] not in (None, ""):
            cost = s(r[i_pc])
        elif i_cost is not None and i_cost < len(r) and r[i_cost] not in (None, ""):
            c = r[i_cost]
            cost = f"${c:,.2f}" if isinstance(c, (int, float)) else s(c)

        out.append({
            "row": rn,
            "trip": trip,
            "leg": trip[-1].upper(),
            "date": date_iso,
            "date_text": fmt_mdy(r[i_date]) if i_date is not None and i_date < len(r) else "",
            "member": member_up,
            "member_raw": s(r[i_member]) if i_member is not None and i_member < len(r) else "",
            "driver": (norm_num(r[i_drv]) if i_drv is not None and i_drv < len(r)
                       and r[i_drv] not in (None, "") else ""),
            "milage": to_float(r[i_mi]) if i_mi is not None and i_mi < len(r) else None,
            "pu": (r[i_pu] if i_pu is not None and i_pu < len(r) else None),
            "license": s(r[i_lic]) if i_lic is not None and i_lic < len(r) else "",
            "vin": s(r[i_vin]) if i_vin is not None and i_vin < len(r) else "",
            "cost": cost,
        })
    return {"path": str(path), "layout": layout, "rows": out}


# ---------- resumen ----------
def parse_resumen(path):
    rows, title, sheets = read_rows(path)
    if not rows:
        return None

    hdr_i = None
    for i, r in enumerate(rows[:5]):
        cells = [s(c).upper() for c in r]
        if (("DATE" in cells or "DTE" in cells) and "NAME" in cells
                and ({"MILES", "MILEAGE"} & set(cells))):
            hdr_i = i
            break
    if hdr_i is None:
        return None

    hdr = [s(c).upper() for c in rows[hdr_i]]
    data = nonempty(rows[hdr_i + 1:])

    def find(*names):
        for n in names:
            if n in hdr:
                return hdr.index(n)
        return None

    i_date = find("DATE", "DTE")
    i_name = find("NAME")
    i_last = find("LAST NAME", "LASTNAME")
    i_miles = find("MILES", "MILEAGE")
    i_trip = find("TRIP ID", "RIDE ID")
    i_payer = find("PAYER", "PROVIDER")
    i_time = find("TIME")

    # driver-number column: header candidates, classified by CONTENT
    candidates = [i for i, h in enumerate(hdr) if h.startswith("DRIVER")]
    candidates += [i for i, h in enumerate(hdr) if h in ("VEHICLE", "VEHICLE ID")]
    numcol = None
    for i in candidates:
        vals = [r[i] for r in data if i < len(r) and r[i] not in (None, "")]
        if vals and sum(1 for v in vals if re.fullmatch(r"\d+(-\d+)?", s(v))) / len(vals) > 0.6:
            numcol = i
            break

    out = []
    for r in data:
        date_iso = to_iso(r[i_date]) if i_date is not None and i_date < len(r) else None
        if not date_iso:
            continue
        name = norm_name(
            r[i_name] if i_name is not None and i_name < len(r) else "",
            r[i_last] if i_last is not None and i_last < len(r) else "",
        )
        if not name:
            continue
        payer = s(r[i_payer]).upper() if i_payer is not None and i_payer < len(r) else "MTM"
        miles = to_float(r[i_miles]) if i_miles is not None and i_miles < len(r) else None
        trip_id = s(r[i_trip]) if i_trip is not None and i_trip < len(r) else ""
        drv = norm_num(r[numcol]) if numcol is not None and numcol < len(r) else ""

        # whole-row scan: driver hints in notes ("... auto 309") + note text
        note = ""
        if not drv:
            for v in r:
                m = re.search(r"auto\s*(\d+)", s(v), re.I)
                if m:
                    drv = m.group(1)
                    break
        for v in r:
            t = s(v)
            if len(t) > 6 and re.search(r"(factur|duplicad|perfil|vehiculo|will call|driver)", t, re.I):
                note = t
                break

        out.append({
            "date": date_iso, "name": name, "driver": drv, "miles": miles,
            "trip_id": trip_id, "payer": payer, "note": note,
            "time": r[i_time] if i_time is not None and i_time < len(r) else None,
            "src": str(path),
        })
    return out


# ---------- trips (PU Time source) ----------
def parse_trips(path):
    rows, title, sheets = read_rows(path)
    if not rows:
        return None

    hdr_i = None
    for i, r in enumerate(rows[:5]):
        cells = [s(c) for c in r]
        if "Trip Number" in cells and ("Time" in cells or "Appointment Date" in cells):
            hdr_i = i
            break
    if hdr_i is None:
        return None

    hdr = [s(c) for c in rows[hdr_i]]

    def idx(*names):
        for n in names:
            if n in hdr:
                return hdr.index(n)
        return None

    i_trip = idx("Trip Number")
    i_time = idx("Time", "Appointment Time")
    i_first = idx("Member's First Name", "Member First Name")
    i_last = idx("Member's Last Name", "Member Last Name")
    i_miles = idx("Trip Mileage")
    i_cost = idx("Trip Cost")
    i_date = idx("Appointment Date")

    out = []
    for r in nonempty(rows[hdr_i + 1:]):
        trip = s(r[i_trip]) if i_trip is not None and i_trip < len(r) else ""
        if not trip:
            continue
        if i_time is not None and i_time < len(r):
            kind, tv = parse_time_value(r[i_time])
        else:
            kind, tv = (None, None)
        out.append({
            "trip": trip,
            "time_kind": kind,
            "time": tv,
            "first": s(r[i_first]) if i_first is not None and i_first < len(r) else "",
            "last": s(r[i_last]) if i_last is not None and i_last < len(r) else "",
            "miles": to_float(r[i_miles]) if i_miles is not None and i_miles < len(r) else None,
            "cost": r[i_cost] if i_cost is not None and i_cost < len(r) else None,
            "date": to_iso(r[i_date]) if i_date is not None and i_date < len(r) else None,
            "src": str(path),
        })
    return out


# ---------- drivers ----------
def parse_drivers(path):
    rows, title, sheets = read_rows(path, "Vehiculos")
    if "Vehiculos" not in sheets:
        rows, title, sheets = read_rows(path)
    if not rows:
        return None

    hdr_i = None
    for i, r in enumerate(rows[:5]):
        cells = [s(c) for c in r]
        if "NUMERO" in cells and "DRIVER" in cells:
            hdr_i = i
            break
    if hdr_i is None:
        return None

    hdr = [s(c) for c in rows[hdr_i]]
    i_name, i_lic = hdr.index("DRIVER"), hdr.index("LICENSE NUMBER")
    i_vin, i_num = hdr.index("VIN Number"), hdr.index("NUMERO")

    table = {}
    names = {}
    for r in nonempty(rows[hdr_i + 1:]):
        if max(i_name, i_lic, i_vin, i_num) >= len(r):
            continue
        num = norm_num(r[i_num])
        if not num:
            continue
        lic, vin = s(r[i_lic]), s(r[i_vin])
        if lic in ("-", "N/A"):
            lic = ""
        if vin in ("-", "N/A"):
            vin = ""
        cur = table.get(num)
        if cur is None or (not cur["vin"] and vin):
            table[num] = {
                "license": lic or (cur or {}).get("license", ""),
                "vin": vin or (cur or {}).get("vin", ""),
                "name": norm_name(r[i_name]),
            }
        nm = norm_name(r[i_name])
        if nm:
            names.setdefault(nm, num)
            names.setdefault(nm.split()[0], num)
    return {"table": table, "names": names}
