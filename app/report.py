"""Human-readable report + CSV export.

Bilingual chrome (es/en) for the section titles and stat labels; the itemized
details (member names, notes, trips) keep the original data text.
"""
import csv
from pathlib import Path

L = {
    "es": {
        "sources": "FUENTES", "claim": "Claim", "resumenes": "Resúmenes",
        "trips": "Archivos viajes", "drivers": "Drivers", "not_found": "NO ENCONTRADO",
        "stats": "ESTADÍSTICAS", "rows": "Filas", "with_resumen": "Con datos de resumen",
        "by_id": "por Trip ID", "by_order": "por orden",
        "driver_pick": "Driver por elegir", "unapproved": "número no aprobado",
        "auto_note": "override por nota", "no_mtm": "Sin datos MTM",
        "pu": "PU Time", "filled": "lleno", "empty": "vacío",
        "pu_est": "PU Time estimado (cita - 14min - 1.4×millas)",
        "time_warn": "Avisos de tiempos",
        "milage_trips": "Milage de archivo viajes", "resumen_missing": "(resumen no lo traía)",
        "balanced": "Reparto de drivers (soft ~2)",
        "suggested": "Driver sugerido", "suggest_note": "(el menos ocupado; confirmar)",
        "not_billed": "Claim sin resumen", "not_billed_note": "(NO facturar salvo Dalia)",
        "billed": "Ya facturado", "billed_note": "(no se vuelve a facturar)",
        "billed_title": "YA FACTURADO - NO SE VUELVE A FACTURAR",
        "billed_hint": "Vienen del claim con nota «Facturado.»; ya se facturaron.",
        "no_driver": "Sin driver", "pick_manual": "(elegir manual)",
        "warnings": "ADVERTENCIAS", "review": "REVISAR",
        "sugg_title": "DRIVER SUGERIDO - CONFIRMAR",
        "sugg_hint": "El app puso el driver MENOS ocupado de ese día. Confírmalo o cámbialo",
        "sugg_hint2": "en la pestaña 'Asignar driver' (o bórralo para dejarlo vacío).",
        "sugg_free": "libre ese día", "sugg_trips": "viaje(s) ese día",
        "needs_title": "SIN DRIVER - ELEGIR UNO",
        "needs_hint": "Estos viajes vienen del portal pero no tienen fila MTM en el resumen.",
        "option": "opción", "miles": "miles",
        "nb_title": "NO FACTURAR - CLAIM SIN RESUMEN",
        "nb_hint": "Vienen del claim pero no están en el resumen y NO son Dalia.",
        "rwc_title": "NO FACTURAR - EN RESUMEN PERO NO EN EL CLAIM",
    },
    "en": {
        "sources": "SOURCES", "claim": "Claim", "resumenes": "Resúmenes",
        "trips": "Trip files", "drivers": "Drivers", "not_found": "NOT FOUND",
        "stats": "STATS", "rows": "Rows", "with_resumen": "With resumen data",
        "by_id": "by Trip ID", "by_order": "by order",
        "driver_pick": "Driver to pick", "unapproved": "unapproved number",
        "auto_note": "note override", "no_mtm": "No MTM data",
        "pu": "PU Time", "filled": "filled", "empty": "empty",
        "pu_est": "Estimated PU Time (appt - 14min - 1.4×miles)",
        "time_warn": "Time warnings",
        "milage_trips": "Milage from trip file", "resumen_missing": "(resumen didn't have it)",
        "balanced": "Driver rebalancing (soft ~2)",
        "suggested": "Suggested driver", "suggest_note": "(least busy; confirm)",
        "not_billed": "Claim w/o resumen", "not_billed_note": "(do NOT bill unless Dalia)",
        "billed": "Already billed", "billed_note": "(not billed again)",
        "billed_title": "ALREADY BILLED - NOT BILLED AGAIN",
        "billed_hint": "They come from the claim with a 'Facturado.' note; already billed.",
        "no_driver": "No driver", "pick_manual": "(pick manually)",
        "warnings": "WARNINGS", "review": "REVIEW",
        "sugg_title": "SUGGESTED DRIVER - CONFIRM",
        "sugg_hint": "The app picked the LEAST busy driver of that day. Confirm or change it",
        "sugg_hint2": "in the 'Assign driver' tab (or clear it to leave it blank).",
        "sugg_free": "free that day", "sugg_trips": "trip(s) that day",
        "needs_title": "NO DRIVER - PICK ONE",
        "needs_hint": "These trips come from the portal but have no MTM row in the resumen.",
        "option": "option", "miles": "miles",
        "nb_title": "DO NOT BILL - CLAIM WITHOUT RESUMEN",
        "nb_hint": "They come from the claim but are not in the resumen and are NOT Dalia.",
        "rwc_title": "DO NOT BILL - IN RESUMEN BUT NOT IN CLAIM",
    },
}


def report_text(result, lang="es"):
    t = L.get(lang, L["es"])
    r = result["report"]
    st = r["stats"]
    lines = []
    lines.append(t["sources"])
    lines.append(f"  {t['claim']}:            {Path(result['claim_path']).name}")
    lines.append(f"  {t['resumenes']}:        {st.get('resumen_files', 0)}")
    lines.append(f"  {t['trips']}:  {st.get('trips_files', 0)}")
    lines.append(f"  {t['drivers']}:          {st.get('drivers_file') or t['not_found']}")
    lines.append("")
    lines.append(t["stats"])
    assigned = st["id_matched"] + st["order_assigned"]
    lines.append(f"  {t['rows']}:                 {st['rows']}")
    lines.append(f"  {t['with_resumen']}:  {assigned}  ({t['by_id']}: {st['id_matched']}, "
                 f"{t['by_order']}: {st['order_assigned']})")
    lines.append(f"  {t['driver_pick']}:     {st['flagged_unapproved']}  "
                 f"({t['unapproved']}; {t['auto_note']}: {st['note_overrides']})")
    lines.append(f"  {t['no_mtm']}:         {st['no_data']}")
    lines.append(f"  {t['pu']}:               {t['filled']} {st['pu_filled']} "
                 f"(Will Call {st['pu_willcall']}) | {t['empty']} {st['pu_missing']}")
    if st.get("pu_estimated"):
        lines.append(f"  {t['pu_est']}: {st['pu_estimated']}")
    if st.get("time_warnings"):
        lines.append(f"  {t['time_warn']}: {st['time_warnings']}  "
                     + ("(pata B antes que la A)" if lang == "es" else "(B leg before A)"))
    if st.get("milage_from_trips"):
        lines.append(f"  {t['milage_trips']}: {st['milage_from_trips']}  {t['resumen_missing']}")
    if st.get("balanced"):
        lines.append(f"  {t['balanced']}: {st['balanced']}")
    if st.get("suggested"):
        lines.append(f"  {t['suggested']}:       {st['suggested']}  {t['suggest_note']}")
    if st.get("not_billed"):
        lines.append(f"  {t['not_billed']}:     {st['not_billed']}  {t['not_billed_note']}")
    if st.get("already_billed"):
        lines.append(f"  {t['billed']}:     {st['already_billed']}  {t['billed_note']}")
    if st.get("needs_driver"):
        lines.append(f"  {t['no_driver']}:            {st['needs_driver']}  {t['pick_manual']}")
    lines.append("")
    warn = r["warnings"]
    rev = r["review"]
    lines.append(f"{t['warnings']} ({len(warn)})")
    for w in warn:
        lines.append("  - " + w)
    lines.append("")
    lines.append(f"{t['review']} ({len(rev)})")
    for w in rev:
        lines.append("  * " + w)

    sugg = r.get("suggested") or []
    if sugg:
        lines.append("")
        lines.append(f"{t['sugg_title']} ({len(sugg)})")
        lines.append("  " + t["sugg_hint"])
        lines.append("  " + t["sugg_hint2"])
        for s in sugg:
            tag = t["sugg_free"] if s["count"] == 0 else f"{s['count']} {t['sugg_trips']}"
            lines.append(f"  - {s['date']} {s['member']} {s['trip']}: "
                         f"{s['driver']} {s['name']} ({tag})")

    needs = r.get("needs_driver") or []
    if needs:
        cand = r.get("driver_candidates") or {}
        lines.append("")
        lines.append(f"{t['needs_title']} ({len(needs)})")
        lines.append("  " + t["needs_hint"])
        for d in sorted({(x["date"], x.get("county") or "") for x in needs}):
            date, county = d
            lines.append(f"  {date}" + (f" [{county}]" if county else "") + ":")
            for c in cand.get(d, []):
                tag = t["sugg_free"] if c["free"] else f"{c['count']} {t['sugg_trips']}"
                lines.append(f"      {t['option']}: {c['num']} {c['name']}  ({tag})")
            for x in needs:
                if x["date"] == date and (x.get("county") or "") == county:
                    mi = x["milage"] if x["milage"] is not None else "-"
                    lines.append(f"      -> {x['member']} {x['trip']} ({t['miles']} {mi})")

    nb = r.get("not_billed") or []
    if nb:
        lines.append("")
        lines.append(f"{t['nb_title']} ({len(nb)})")
        lines.append("  " + t["nb_hint"])
        for x in nb:
            lines.append(f"  - {x['date']} {x['member']} {x['trip']}")

    rwc = r.get("resumen_without_claim") or []
    if rwc:
        lines.append("")
        lines.append(f"{t['rwc_title']} ({len(rwc)})")
        for x in rwc:
            lines.append(f"  - {x['date']} {x['member']}")

    billed = r.get("already_billed") or []
    if billed:
        lines.append("")
        lines.append(f"{t['billed_title']} ({len(billed)})")
        lines.append("  " + t["billed_hint"])
        for x in billed:
            lines.append(f"  - {x['date']} {x['member']} {x['trip']}")

    return "\n".join(lines)


def write_report_csv(path, result):
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["tipo", "detalle"])
        for x in result["report"]["warnings"]:
            w.writerow(["ADVERTENCIA", x])
        for x in result["report"]["review"]:
            w.writerow(["REVISAR", x])
