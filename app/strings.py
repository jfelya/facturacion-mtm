"""Bilingual UI strings for the Tkinter app."""

STRINGS = {
    "es": {
        "title": "Facturación MTM — Llenar ClaimInformation",
        "subtitle": "Rellena el ClaimInformation del portal con los datos de cada día.",
        "sec_sources": "Archivos de entrada",
        "lbl_claim": "Paso 1 · Claim del portal (…OLD.xlsx)",
        "hint_claim": "El archivo que bajas de MTM con las columnas del portal (Claim Status, Trip Number, …).",
        "lbl_folder": "Paso 2 · Carpeta de fuentes",
        "hint_folder": "Aquí van los RESUMEN FACTURACION de cada día, los archivos de viajes (10-05.xlsx…) y los drivers.",
        "lbl_drivers": "Paso 3 · Informacion de Drivers.xlsx",
        "hint_drivers": "Solo si no está dentro de la carpeta de fuentes (se busca solo si lo dejas vacío).",
        "lbl_driverlogs": "Paso 4 · Driverlogs (plantillas .docx)",
        "hint_driverlogs": "Carpeta con «<NUM> <NOMBRE> DRIVERLOG VACIO.docx». Los drivers sin plantilla se reemplazan por uno libre.",
        "lbl_daysroot": "Paso 5 · Carpeta de días (salida .docx)",
        "hint_daysroot": "Dónde están las carpetas 10-05, 10-06… (ej. «1. PARA FACTURAR»). Vacío → usa la carpeta de fuentes.",
        "browse": "Elegir…",
        "sec_options": "Opciones",
        "lbl_pairs": "Driver por pata:",
        "pair_pair": "Mismo driver en ambas",
        "pair_b": "Uno por pata (recomendado)",
        "pair_a": "Uno por pata (invertido)",
        "lbl_willcall": "Will Call = hora pata A +",
        "hours": "h",
        "chk_suggest": "Sugerir driver (el menos ocupado)",
        "chk_spread": "Repartir drivers cuando dos viajeros comparten los mismos",
        "chk_balance": "Repartir viajes (≈2 por driver)",
        "btn_run": "Procesar",
        "btn_export": "Exportar Excel…",
        "btn_csv": "Guardar reporte (CSV)…",
        "btn_driverlogs": "Generar driverlogs (.docx)",
        "btn_bulk": "Generar BULK UPLOAD",
        "btn_help": "¿Qué archivos necesito?",
        "tab_preview": "Vista previa",
        "tab_report": "Reporte",
        "tab_assign": "Asignar driver",
        "assign_hint": ("Viajes que vienen del portal y no tienen fila MTM en el resumen. "
                        "Elige un driver libre y se rellenan Driver + License + VIN."),
        "assign_lbl": "Driver para la fila seleccionada:",
        "btn_assign": "Asignar",
        "btn_clear": "Quitar",
        "sugg_free": "libre ese día",
        "sugg_trips": "viaje(s) ese día",
        "c_fila": "#", "c_fecha": "Fecha", "c_miembro": "Miembro", "c_trip": "Trip",
        "c_driver": "Driver", "c_milage": "Milage", "c_pu": "PU", "c_estado": "Estado",
        "c_dropoff": "DropOff",
        "st_idle": "Elige el claim y la carpeta de fuentes, luego Procesar.",
        "st_working": "Procesando…",
        "st_error": "Error",
        "st_done": ("Listo: {ok} OK, {nota} con nota, {sug} sugerido (confirmar), {bal} reasignado (reparto), "
                    "{elegir} por asignar, {nofact} sin facturar, {facturado} ya facturado, "
                    "{revisar} por revisar, {sindato} sin datos."),
        "err_claim": "Elige el archivo ClaimInformation (.xlsx).",
        "err_folder": "Elige la carpeta donde están los resúmenes / viajes / drivers.",
        "err_driverlogs": "Elige la carpeta de plantillas de driverlogs (.docx).",
        "err_daysroot": "Elige la carpeta de días (donde están 10-05, 10-06…).",
        "notrips_title": "Sin archivos de viajes",
        "notrips_body": ("No encontré archivos de viajes (tipo 10-05.xlsx) en la carpeta de fuentes.\n\n"
                         "Sin ellos, el PU Time, el DropOff Time y la Milage de Dalia quedarán VACÍOS.\n\n"
                         "¿Continuar de todas formas? (Proceed) o Cancelar para agregarlos."),
        "dl_title": "Driverlogs generados",
        "dl_body": "Se generaron {n} driverlog(s) en:\n{root}\n\nSin plantilla (omitidos): {skipped}\nErrores: {errors}",
        "bulk_title": "BULK UPLOAD generados",
        "bulk_body": ("Se generaron {n} archivo(s) «BULK UPLOAD <fecha>.xlsx» en:\n{root}\n\n"
                      "Filas omitidas (sin driver / no facturar): {excluded}\nErrores: {errors}"),
        "err_title": "Falta",
        "prev_summary": "RESUMEN VISTA PREVIA",
        "exp_title": "Guardado",
        "exp_body": "Archivo guardado:\n{path}\n\n{rows} filas en {sheets} hoja(s) (una por día).",
        "csv_title": "Guardado",
        "csv_body": "Reporte guardado:\n{path}",
        "pend_title": "Faltan drivers",
        "pend_body": ("{n} viaje(s) siguen SIN driver asignado.\n\n"
                      "Puedes asignarlos en la pestaña 'Asignar driver' o exportar igual y completarlos a mano.\n\n"
                      "¿Exportar de todas formas?"),
        "help_title": "¿Qué archivos necesito?",
        "help_body": (
            "1) CLAIM DEL PORTAL (Paso 1)\n"
            "   El archivo 'ClaimInformation … OLD.xlsx' que descargas de MTM.\n\n"
            "2) CARPETA DE FUENTES (Paso 2)\n"
            "   Una carpeta que contenga:\n"
            "   • los 'RESUMEN FACTURACION' de cada día (pueden traer SafeRide/Alivi/etc.; el app filtra MTM),\n"
            "   • los archivos de viajes del día (tipo 10-05.xlsx) — de aquí salen PU Time y Milage,\n"
            "   • 'Informacion de Drivers.xlsx' (License/VIN).\n\n"
            "3) DRIVERS (Paso 3)\n"
            "   Solo si el archivo de drivers no está dentro de la carpeta de fuentes.\n\n"
            "IMPORTANTE:\n"
            "• El app detecta cada archivo por su ESTRUCTURA, no por el nombre: puedes renombrarlos.\n"
            "• Nunca modifica los originales: siempre escribe un archivo nuevo.\n"
            "• Al llegar archivos nuevos, ponlos en la carpeta del proyecto (data/base).\n"
            "• El DropOff queda 1–5 min antes de la CITA del archivo de viajes; el PU Time se estima\n"
            "   (DropOff − 14 min − 1.4×millas, con ±3 min de variación para que se vea natural).\n"
            "• La salida queda en UNA HOJA POR DÍA (10-05, 10-06, …)."),
    },
    "en": {
        "title": "MTM Billing — Fill ClaimInformation",
        "subtitle": "Fill the portal's ClaimInformation with each day's data.",
        "sec_sources": "Input files",
        "lbl_claim": "Step 1 · Portal claim (…OLD.xlsx)",
        "hint_claim": "The file you download from MTM with the portal columns (Claim Status, Trip Number, …).",
        "lbl_folder": "Step 2 · Sources folder",
        "hint_folder": "Holds each day's RESUMEN FACTURACION, the trip files (10-05.xlsx…) and the drivers.",
        "lbl_drivers": "Step 3 · Informacion de Drivers.xlsx",
        "hint_drivers": "Only if it is not inside the sources folder (it's auto-found when left empty).",
        "lbl_driverlogs": "Step 4 · Driverlogs (.docx templates)",
        "hint_driverlogs": "Folder with «<NUM> <NAME> DRIVERLOG VACIO.docx». Drivers without a template get replaced.",
        "lbl_daysroot": "Step 5 · Days folder (.docx output)",
        "hint_daysroot": "Where the 10-05, 10-06… folders live (e.g. «1. PARA FACTURAR»). Empty → uses the sources folder.",
        "browse": "Browse…",
        "sec_options": "Options",
        "lbl_pairs": "Driver per leg:",
        "pair_pair": "Same driver both legs",
        "pair_b": "One driver per leg (recommended)",
        "pair_a": "One driver per leg (reversed)",
        "lbl_willcall": "Will Call = A-leg time +",
        "hours": "h",
        "chk_suggest": "Suggest driver (least busy)",
        "chk_spread": "Split drivers when two members share the same ones",
        "chk_balance": "Balance trips (~2 per driver)",
        "btn_run": "Process",
        "btn_export": "Export Excel…",
        "btn_csv": "Save report (CSV)…",
        "btn_driverlogs": "Generate driverlogs (.docx)",
        "btn_bulk": "Generate BULK UPLOAD",
        "btn_help": "What files do I need?",
        "tab_preview": "Preview",
        "tab_report": "Report",
        "tab_assign": "Assign driver",
        "assign_hint": ("Trips that come from the portal and have no MTM row in the resumen. "
                        "Pick a free driver and Driver + License + VIN get filled."),
        "assign_lbl": "Driver for the selected row:",
        "btn_assign": "Assign",
        "btn_clear": "Clear",
        "sugg_free": "free that day",
        "sugg_trips": "trip(s) that day",
        "c_fila": "#", "c_fecha": "Date", "c_miembro": "Member", "c_trip": "Trip",
        "c_driver": "Driver", "c_milage": "Milage", "c_pu": "PU", "c_estado": "Status",
        "c_dropoff": "DropOff",
        "st_idle": "Pick the claim and the sources folder, then Process.",
        "st_working": "Processing…",
        "st_error": "Error",
        "st_done": ("Done: {ok} OK, {nota} with note, {sug} suggested (confirm), {bal} rebalanced, "
                    "{elegir} to assign, {nofact} not billed, {facturado} already billed, "
                    "{revisar} to review, {sindato} no data."),
        "err_claim": "Pick the ClaimInformation file (.xlsx).",
        "err_folder": "Pick the folder with the resúmenes / trips / drivers.",
        "err_driverlogs": "Pick the driverlogs templates folder (.docx).",
        "err_daysroot": "Pick the days folder (where 10-05, 10-06… live).",
        "notrips_title": "No trip files",
        "notrips_body": ("I found no trip files (like 10-05.xlsx) in the sources folder.\n\n"
                         "Without them, PU Time, DropOff Time and Dalia's Milage will be EMPTY.\n\n"
                         "Proceed anyway? (or Cancel to add them)"),
        "dl_title": "Driverlogs generated",
        "dl_body": "Generated {n} driverlog(s) in:\n{root}\n\nNo template (skipped): {skipped}\nErrors: {errors}",
        "bulk_title": "BULK UPLOAD generated",
        "bulk_body": ("Generated {n} «BULK UPLOAD <date>.xlsx» file(s) in:\n{root}\n\n"
                      "Rows skipped (no driver / not billed): {excluded}\nErrors: {errors}"),
        "err_title": "Missing",
        "prev_summary": "PREVIEW SUMMARY",
        "exp_title": "Saved",
        "exp_body": "File saved:\n{path}\n\n{rows} rows in {sheets} sheet(s) (one per day).",
        "csv_title": "Saved",
        "csv_body": "Report saved:\n{path}",
        "pend_title": "Missing drivers",
        "pend_body": ("{n} trip(s) still have NO driver assigned.\n\n"
                      "You can assign them in the 'Assign driver' tab or export anyway and finish them by hand.\n\n"
                      "Export anyway?"),
        "help_title": "What files do I need?",
        "help_body": (
            "1) PORTAL CLAIM (Step 1)\n"
            "   The 'ClaimInformation … OLD.xlsx' file you download from MTM.\n\n"
            "2) SOURCES FOLDER (Step 2)\n"
            "   A folder containing:\n"
            "   • each day's 'RESUMEN FACTURACION' (may include SafeRide/Alivi/etc.; the app filters MTM),\n"
            "   • the day's trip files (like 10-05.xlsx) — PU Time and Milage come from here,\n"
            "   • 'Informacion de Drivers.xlsx' (License/VIN).\n\n"
            "3) DRIVERS (Step 3)\n"
            "   Only if the drivers file is not inside the sources folder.\n\n"
            "IMPORTANT:\n"
            "• The app detects each file by its STRUCTURE, not its name: you can rename them.\n"
            "• It never modifies the originals: it always writes a new file.\n"
            "• When new files arrive, put them in the project folder (data/base).\n"
            "• DropOff lands 1–5 min before the trip file's APPOINTMENT; PU Time is estimated\n"
            "   (DropOff − 14 min − 1.4×miles, with ±3 min variation so it looks natural).\n"
            "• The output is ONE SHEET PER DAY (10-05, 10-06, …)."),
    },
}
