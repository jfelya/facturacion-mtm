"""Write the final ClaimInformation file.

Format (confirmed against the user's "GROUPED" file): ONE SHEET PER DAY,
sheet name `MM-DD`, each with the exact 9 columns and cell types of the
finished example. Rows keep the order of the claim (grouped by member).
"""
from datetime import datetime, time as dtime
from openpyxl import Workbook
from openpyxl.styles import Font

HEADERS = ["Driver", "License", "VIN", "Trip Number", "Appt. Date",
           "Member Info", "PU Time", "DropOff Time", "Milage", "Cost"]

WIDTHS = (9, 22, 20, 15, 12, 26, 9, 12, 9, 10)


def _sheet_name(date_iso):
    """'2026-10-05' -> '10-05' (Excel sheet names can't contain '/')."""
    try:
        _y, m, d = str(date_iso).split("-")
        return f"{m}-{d}"
    except Exception:
        return "Hoja1"


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
            row.get("trip") or "",
            row.get("date_text") or "",
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


def write_output(claim, path, per_day=True):
    """per_day=True -> one sheet per day (default). False -> single 'ClaimInformation' sheet."""
    wb = Workbook()
    default = wb.active
    rows = claim["rows"]

    if per_day:
        groups = {}
        for r in rows:
            groups.setdefault(r.get("date") or "", []).append(r)
        for date in sorted(groups):
            _write_sheet(wb.create_sheet(_sheet_name(date)), groups[date])
        wb.remove(default)
    else:
        default.title = "ClaimInformation"
        _write_sheet(default, rows)

    wb.save(path)
    return {"path": str(path), "rows": len(rows), "sheets": len(wb.sheetnames)}
