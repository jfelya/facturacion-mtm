"""Write the final ClaimInformation file.

Format (confirmed against the user's "GROUPED" file): ONE SHEET PER DAY,
sheet name `MM-DD`, each with the exact 9 columns and cell types of the
finished example. Rows keep the order of the claim (grouped by member).
"""
from datetime import datetime, time as dtime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

from .common import day_name

HEADERS = ["Driver", "License", "VIN", "Appt. Date", "Trip Number", "Member Info",
           "PU Time", "DropOff Time", "Milage", "Cost"]

WIDTHS = (9, 22, 20, 15, 12, 26, 9, 12, 9, 10)


def _write_sheet(ws, rows):
    ws.append(HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for row in rows:
        drv = row.get("driver") or ""
        try:
            drv = int(drv)
        except (TypeError, ValueError):
            pass

        pu = row.get("pu")
        if isinstance(pu, datetime):
            pu = pu.time()
        do = row.get("dropoff")
        if isinstance(do, datetime):
            do = do.time()

        member = row.get("member_raw") or row.get("member") or ""
        ws.append([
            drv,
            row.get("license") or "",
            row.get("vin") or "",
            row.get("date_text") or "",     # Appt. Date
            row.get("trip") or "",           # Trip Number
            member,
            pu,
            do,
            row.get("milage"),
            row.get("cost") or "",
        ])
        if isinstance(pu, dtime):
            ws.cell(row=ws.max_row, column=7).number_format = "h:mm"
        if isinstance(do, dtime):
            ws.cell(row=ws.max_row, column=8).number_format = "h:mm"

    ws.freeze_panes = "A2"
    for col, w in zip("ABCDEFGHIJ", WIDTHS):
        ws.column_dimensions[col].width = w

    # the portal wants flat values: make sure nothing is left as a formula
    for row in ws.iter_rows():
        for c in row:
            if c.data_type == "f":
                c.value = None


def ensure_not_source(path, source):
    """Refuse writing an output over the original claim."""
    if source and Path(path).resolve() == Path(source).resolve():
        raise ValueError("La salida no puede ser el archivo original del claim.")


def write_output(claim, path, per_day=True):
    """per_day=True -> one sheet per day (default). False -> single 'ClaimInformation' sheet."""
    ensure_not_source(path, claim.get("path"))
    all_rows = claim["rows"]
    rows = [r for r in all_rows if r.get("flag") != "facturado"]
    skipped = len(all_rows) - len(rows)
    if not rows:
        raise ValueError("No hay filas facturables para exportar")
    wb = Workbook()
    default = wb.active

    if per_day:
        groups = {}
        for r in rows:
            groups.setdefault(r.get("date") or "", []).append(r)
        for date in sorted(groups):
            _write_sheet(wb.create_sheet(day_name(date)), groups[date])
        wb.remove(default)
    else:
        default.title = "ClaimInformation"
        _write_sheet(default, rows)

    wb.save(path)
    return {"path": str(path), "rows": len(rows), "sheets": len(wb.sheetnames),
            "skipped": skipped}
