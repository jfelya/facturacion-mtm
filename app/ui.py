"""Tkinter desktop UI for the claim filler.

- DPI-aware, Segoe UI Semibold base font
- Light/Dark pastel themes (dark by default), one toggle button
- Bilingual ES (default) / EN, one flag button
- Explicit help: what files to provide and how
"""
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from .pipeline import run_job
from .report import report_text, write_report_csv
from .writer import write_output

# ---------------- themes (pastel) ----------------
THEMES = {
    "light": {
        "bg": "#eaeef3", "card": "#ffffff", "header": "#1f3a5f",
        "header_fg": "#ffffff", "header_sub": "#c7d6e6",
        "accent": "#2f6fb3", "accent_d": "#245a92", "accent_fg": "#ffffff",
        "accent_dis": "#9bb4cd", "accent_dis_fg": "#eef2f6",
        "muted": "#5b6b7c", "txt": "#1e2a36", "border": "#d3d9e0",
        "entry": "#ffffff", "tree": "#ffffff", "head": "#e9eef5", "tab_bg": "#dfe5ee",
        "btn": "#e3e9f2", "btn_hover": "#d3dce8",
        "status": {"OK": "#dcf5dc", "NOTA": "#fff3cd", "SUGERIDO": "#e6d9f7",
                   "REVISAR": "#ffe0b3", "ELEGIR": "#dbe9ff", "NO FACTURAR": "#e2e3e5",
                   "SIN DATO": "#f8d7da"},
    },
    "dark": {
        "bg": "#1b2230", "card": "#232c3d", "header": "#121826",
        "header_fg": "#eaf1fa", "header_sub": "#9fb3cc",
        "accent": "#8fb8e0", "accent_d": "#a9caea", "accent_fg": "#16202e",
        "accent_dis": "#3d4b60", "accent_dis_fg": "#7d8ba0",
        "muted": "#93a2b6", "txt": "#e8eef7", "border": "#33405a",
        "entry": "#1f2836", "tree": "#232c3d", "head": "#2b3648", "tab_bg": "#1b2230",
        "btn": "#2e394d", "btn_hover": "#3a4760",
        "status": {"OK": "#2f4d3a", "NOTA": "#4d4526", "SUGERIDO": "#3d3454",
                   "REVISAR": "#4d3f27", "ELEGIR": "#2a3d52", "NO FACTURAR": "#39414d",
                   "SIN DATO": "#4d2f34"},
    },
}

# ---------------- i18n ----------------
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
        "lbl_pairs": "Driver patas A/B:",
        "pair_pair": "Mismo en ambas (recomendado)",
        "pair_b": "1ª fila → B",
        "pair_a": "1ª fila → A",
        "lbl_willcall": "Will Call = hora pata A +",
        "hours": "h",
        "chk_suggest": "Sugerir driver (el menos ocupado)",
        "chk_spread": "Repartir drivers cuando dos viajeros comparten los mismos",
        "btn_run": "Procesar",
        "btn_export": "Exportar Excel…",
        "btn_csv": "Guardar reporte (CSV)…",
        "btn_driverlogs": "Generar driverlogs (.docx)",
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
        "st_done": ("Listo: {ok} OK, {nota} con nota, {sug} sugerido (confirmar), "
                    "{elegir} por asignar, {nofact} sin facturar, {revisar} por revisar, {sindato} sin datos."),
        "err_claim": "Elige el archivo ClaimInformation (.xlsx).",
        "err_folder": "Elige la carpeta donde están los resúmenes / viajes / drivers.",
        "err_driverlogs": "Elige la carpeta de plantillas de driverlogs (.docx).",
        "err_daysroot": "Elige la carpeta de días (donde están 10-05, 10-06…).",
        "dl_title": "Driverlogs generados",
        "dl_body": "Se generaron {n} driverlog(s) en:\n{root}\n\nSin plantilla (omitidos): {skipped}\nErrores: {errors}",
        "err_title": "Falta",
        "prev_summary": "RESUMEN VISTA PREVIA",
        "exp_title": "Guardado",
        "exp_body": "Archivo listo:\n{path}\n\n{rows} filas en {sheets} hoja(s) (una por día).\n\nSube este archivo al portal MTM.",
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
            "• El PU Time se ESTIMA desde la hora de la CITA del archivo de viajes\n"
            "   (cita − 14 min − 1.4×millas, con ±3 min de variación para que se vea natural).\n"
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
        "lbl_pairs": "A/B legs driver:",
        "pair_pair": "Same on both (recommended)",
        "pair_b": "1st row → B",
        "pair_a": "1st row → A",
        "lbl_willcall": "Will Call = A-leg time +",
        "hours": "h",
        "chk_suggest": "Suggest driver (least busy)",
        "chk_spread": "Split drivers when two members share the same ones",
        "btn_run": "Process",
        "btn_export": "Export Excel…",
        "btn_csv": "Save report (CSV)…",
        "btn_driverlogs": "Generate driverlogs (.docx)",
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
        "st_done": ("Done: {ok} OK, {nota} with note, {sug} suggested (confirm), "
                    "{elegir} to assign, {nofact} not billed, {revisar} to review, {sindato} no data."),
        "err_claim": "Pick the ClaimInformation file (.xlsx).",
        "err_folder": "Pick the folder with the resúmenes / trips / drivers.",
        "err_driverlogs": "Pick the driverlogs templates folder (.docx).",
        "err_daysroot": "Pick the days folder (where 10-05, 10-06… live).",
        "dl_title": "Driverlogs generated",
        "dl_body": "Generated {n} driverlog(s) in:\n{root}\n\nNo template (skipped): {skipped}\nErrors: {errors}",
        "err_title": "Missing",
        "prev_summary": "PREVIEW SUMMARY",
        "exp_title": "Saved",
        "exp_body": "File ready:\n{path}\n\n{rows} rows in {sheets} sheet(s) (one per day).\n\nUpload this file to the MTM portal.",
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
            "• PU Time is ESTIMATED from the trip file's APPOINTMENT time\n"
            "   (appt − 14 min − 1.4×miles, with ±3 min variation so it looks natural).\n"
            "• The output is ONE SHEET PER DAY (10-05, 10-06, …)."),
    },
}


def status_of(row):
    flag = row.get("flag") or ""
    if row.get("driver") and row.get("milage") is not None:
        if flag == "sugerido":
            return "SUGERIDO"
        return "NOTA" if flag == "nota" else "OK"
    if flag == "nofacturar":
        return "NO FACTURAR"
    if not row.get("driver"):
        return "ELEGIR" if row.get("milage") is not None else "SIN DATO"
    return "REVISAR"


def _draw_flag(canvas, country, bg):
    canvas.configure(bg=bg)
    canvas.delete("all")
    w, h = int(canvas["width"]), int(canvas["height"])
    if country == "es":          # Venezuela
        canvas.create_rectangle(0, 0, w, h / 3, fill="#f7d417", outline="")
        canvas.create_rectangle(0, h / 3, w, 2 * h / 3, fill="#0033a0", outline="")
        canvas.create_rectangle(0, 2 * h / 3, w, h, fill="#cf142b", outline="")
        for i in range(5):
            x = 5 + i * (w - 10) / 4
            canvas.create_oval(x, h / 3 + 2, x + 2.2, h / 3 + 4.2, fill="white", outline="")
    else:                        # USA
        stripe = h / 13
        for i in range(13):
            col = "#b22234" if i % 2 == 0 else "#ffffff"
            canvas.create_rectangle(0, i * stripe, w, (i + 1) * stripe, fill=col, outline="")
        canvas.create_rectangle(0, 0, w * 0.44, stripe * 7, fill="#3c3b6e", outline="")
        for r in range(3):
            for c in range(3):
                x = 3 + c * (w * 0.44 - 6) / 2
                y = 2.2 + r * (stripe * 7 - 4.4) / 2
                canvas.create_oval(x, y, x + 1.8, y + 1.8, fill="white", outline="")
    canvas.create_rectangle(0, 0, w - 1, h - 1, outline="#8b98a8")


def _draw_theme_icon(canvas, theme, bg):
    canvas.configure(bg=bg)
    canvas.delete("all")
    w, h = int(canvas["width"]), int(canvas["height"])
    cx, cy, r = w / 2, h / 2, min(w, h) / 2 - 3
    if theme == "dark":          # moon = dark active
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#dbe4f0", outline="")
        canvas.create_oval(cx - r + 3.5, cy - r - 1.5, cx + r + 5, cy + r - 2.5, fill=bg, outline="")
    else:                        # sun = light active
        for a in range(0, 360, 45):
            import math
            x1 = cx + (r + 1) * math.cos(math.radians(a))
            y1 = cy + (r + 1) * math.sin(math.radians(a))
            x2 = cx + (r + 4) * math.cos(math.radians(a))
            y2 = cy + (r + 4) * math.sin(math.radians(a))
            canvas.create_line(x1, y1, x2, y2, fill="#f2c14e", width=2)
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#f2c14e", outline="")


def _pick_family(cands, available):
    for c in cands:
        if c in available:
            return c
    return "TkDefaultFont"


def _init_dpi():
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


class App:
    def __init__(self, root):
        self.root = root
        self.lang = "es"
        self.theme = "dark"
        self.result = None
        self._assign_map = {}
        self._assign_cands = []

        root.title("Facturación MTM")
        root.geometry("1180x790")
        root.minsize(1020, 640)

        fams = set(tkfont.families())
        self.fam = _pick_family(["Segoe UI Semibold", "Segoe UI", "Arial"], fams)
        fam_r = _pick_family(["Segoe UI", "Arial"], fams)
        self.font = (self.fam, 11)
        self.font_bold = (self.fam, 11, "bold")
        self.font_title = (self.fam, 17, "bold")
        self.font_small = (fam_r, 9)
        self.font_mono = ("Consolas", 10)

        self.claim_var = tk.StringVar()
        self.folder_var = tk.StringVar()
        self.drivers_var = tk.StringVar()
        self.driverlogs_var = tk.StringVar()
        self.daysroot_var = tk.StringVar()
        self.strategy_var = tk.StringVar(value="pair")
        self.willcall_var = tk.StringVar(value="2")
        self.suggest_var = tk.BooleanVar(value=True)
        self.spread_var = tk.BooleanVar(value=True)

        self._build()
        self._apply_theme()
        self._retranslate()

    # ---------------- layout ----------------
    def _build(self):
        head = ttk.Frame(self.root, style="Header.TFrame", padding=(18, 12))
        head.pack(fill="x")
        left = ttk.Frame(head, style="Header.TFrame")
        left.pack(side="left")
        self.lbl_title = ttk.Label(left, style="Header.TLabel")
        self.lbl_title.pack(anchor="w")
        self.lbl_sub = ttk.Label(left, style="HeaderSub.TLabel")
        self.lbl_sub.pack(anchor="w", pady=(2, 0))

        ctrl = ttk.Frame(head, style="Header.TFrame")
        ctrl.pack(side="right")
        self.theme_canvas = tk.Canvas(ctrl, width=40, height=30, highlightthickness=0,
                                      bd=0, cursor="hand2")
        self.theme_canvas.pack(side="right", padx=(10, 0))
        self.theme_canvas.bind("<Button-1>", lambda e: self._toggle_theme())
        self.lang_canvas = tk.Canvas(ctrl, width=64, height=30, highlightthickness=0,
                                     bd=0, cursor="hand2")
        self.lang_canvas.pack(side="right")
        self.lang_canvas.bind("<Button-1>", lambda e: self._toggle_lang())

        body = ttk.Frame(self.root, padding=(14, 12, 14, 10))
        body.pack(fill="both", expand=True)

        card = ttk.Frame(body, style="Card.TFrame", padding=16)
        card.pack(fill="x")
        self.lbl_sources = ttk.Label(card, style="Bold.TLabel")
        self.lbl_sources.pack(anchor="w", pady=(0, 8))
        self.lbl_claim = self._file_row(card, "claim", self.claim_var, self.browse_claim)
        self.lbl_folder = self._file_row(card, "folder", self.folder_var, self.browse_folder)
        self.lbl_drivers = self._file_row(card, "drivers", self.drivers_var, self.browse_drivers)
        self.lbl_driverlogs = self._file_row(card, "driverlogs", self.driverlogs_var,
                                             self.browse_driverlogs)
        self.lbl_daysroot = self._file_row(card, "daysroot", self.daysroot_var,
                                           self.browse_daysroot)

        opt = ttk.Frame(body, padding=(4, 12, 4, 6))
        opt.pack(fill="x")
        self.lbl_pairs = ttk.Label(opt)
        self.lbl_pairs.pack(side="left")
        self.rb_pair = ttk.Radiobutton(opt, text="", variable=self.strategy_var, value="pair")
        self.rb_pair.pack(side="left", padx=(6, 0))
        self.rb_b = ttk.Radiobutton(opt, text="", variable=self.strategy_var, value="first_row_B")
        self.rb_b.pack(side="left", padx=(10, 0))
        self.rb_a = ttk.Radiobutton(opt, text="", variable=self.strategy_var, value="first_row_A")
        self.rb_a.pack(side="left", padx=(10, 0))
        self.lbl_willcall = ttk.Label(opt)
        self.lbl_willcall.pack(side="left", padx=(18, 4))
        ttk.Spinbox(opt, from_=0, to=8, width=3, textvariable=self.willcall_var,
                    font=self.font).pack(side="left")
        self.lbl_hours = ttk.Label(opt)
        self.lbl_hours.pack(side="left", padx=(3, 0))

        opt2 = ttk.Frame(body, padding=(4, 0, 4, 6))
        opt2.pack(fill="x")
        self.chk_suggest = ttk.Checkbutton(opt2, text="", variable=self.suggest_var)
        self.chk_suggest.pack(side="left")
        self.chk_spread = ttk.Checkbutton(opt2, text="", variable=self.spread_var)
        self.chk_spread.pack(side="left", padx=(18, 0))

        act = ttk.Frame(body, padding=(4, 2, 4, 8))
        act.pack(fill="x")
        self.btn_help = ttk.Button(act, command=self.show_help)
        self.btn_help.pack(side="right")
        self.btn_run = ttk.Button(act, style="Accent.TButton", command=self.run)
        self.btn_run.pack(side="left")
        self.btn_export = ttk.Button(act, command=self.export, state="disabled")
        self.btn_export.pack(side="left", padx=6)
        self.btn_csv = ttk.Button(act, command=self.save_csv, state="disabled")
        self.btn_csv.pack(side="left")
        self.btn_driverlogs = ttk.Button(act, command=self.generate_driverlogs, state="disabled")
        self.btn_driverlogs.pack(side="left", padx=6)

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=14, pady=(0, 6))
        self.nb = nb
        tab1 = ttk.Frame(nb, style="Card.TFrame")
        tab2 = ttk.Frame(nb, style="Card.TFrame")
        tab3 = ttk.Frame(nb, style="Card.TFrame")
        nb.add(tab1, text="")
        nb.add(tab2, text="")
        nb.add(tab3, text="")
        self.tabs = (tab1, tab2, tab3)

        cols = ("fila", "fecha", "miembro", "trip", "driver", "milage", "pu", "dropoff", "estado")
        self.cols = cols
        widths = {"fila": 46, "fecha": 100, "miembro": 240, "trip": 130, "driver": 66,
                  "milage": 66, "pu": 64, "dropoff": 78, "estado": 110}
        self.tree = ttk.Treeview(tab1, columns=cols, show="headings")
        for c in cols:
            self.tree.column(c, width=widths[c],
                             anchor="w" if c in ("fecha", "miembro", "trip") else "center")
        self.tree.pack(fill="both", expand=True, side="left")
        vsb = ttk.Scrollbar(tab1, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        self.txt = tk.Text(tab2, wrap="word", font=self.font_mono, relief="flat", padx=10, pady=8)
        self.txt.pack(fill="both", expand=True, side="left")
        vsb2 = ttk.Scrollbar(tab2, orient="vertical", command=self.txt.yview)
        self.txt.configure(yscrollcommand=vsb2.set)
        vsb2.pack(side="right", fill="y")

        self._build_assign_tab(tab3)

        self.status = ttk.Label(self.root, style="Status.TLabel", anchor="w", padding=(16, 6))
        self.status.pack(fill="x", side="bottom")

    def _file_row(self, parent, key, var, browse):
        row = ttk.Frame(parent, style="Card.TFrame")
        row.pack(fill="x", pady=(0, 8))
        top = ttk.Frame(row, style="Card.TFrame")
        top.pack(fill="x")
        lbl = ttk.Label(top, style="Bold.TLabel")
        lbl.pack(side="left")
        btn = ttk.Button(top, text="", width=9, command=browse)
        btn.pack(side="right", padx=(8, 0))
        ttk.Entry(top, textvariable=var).pack(side="left", fill="x", expand=True, padx=(10, 0))
        hint = ttk.Label(row, style="Hint.TLabel")
        hint.pack(anchor="w", padx=(0, 2))
        row._lbl, row._hint, row._btn = lbl, hint, btn
        return row

    def _build_assign_tab(self, parent):
        self.lbl_assign_hint = ttk.Label(parent, style="Card.TLabel", wraplength=1080, padding=(8, 8))
        self.lbl_assign_hint.pack(anchor="w")
        cols = ("fecha", "miembro", "trip", "milage", "driver")
        self.acols = cols
        widths = {"fecha": 100, "miembro": 240, "trip": 130, "milage": 70, "driver": 140}
        self.assign_tree = ttk.Treeview(parent, columns=cols, show="headings", height=10)
        for c in cols:
            self.assign_tree.column(c, width=widths[c],
                                    anchor="w" if c in ("fecha", "miembro", "trip") else "center")
        self.assign_tree.pack(fill="both", expand=True, padx=8)
        self.assign_tree.bind("<<TreeviewSelect>>", self._on_assign_select)
        bot = ttk.Frame(parent, style="Card.TFrame", padding=8)
        bot.pack(fill="x")
        self.lbl_assign = ttk.Label(bot, style="Card.TLabel")
        self.lbl_assign.pack(side="left")
        self.assign_combo = ttk.Combobox(bot, width=42, state="readonly", font=self.font_small)
        self.assign_combo.pack(side="left", padx=8)
        self.assign_combo.bind("<<ComboboxSelected>>", lambda e: self._show_cand_info())
        self.btn_assign = ttk.Button(bot, command=self.assign_driver)
        self.btn_assign.pack(side="left")
        self.btn_clear = ttk.Button(bot, command=self.clear_driver)
        self.btn_clear.pack(side="left", padx=6)
        self.assign_info = ttk.Label(bot, style="Hint.TLabel")
        self.assign_info.pack(side="left", padx=10)

    # ---------------- theme ----------------
    def _toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self._apply_theme()
        if self.result:
            self._render()

    def _apply_theme(self):
        th = THEMES[self.theme]
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        self.root.configure(bg=th["bg"])
        self.root.option_add("*Font", self.font)
        style.configure(".", background=th["bg"], foreground=th["txt"], font=self.font)
        style.configure("TFrame", background=th["bg"])
        style.configure("Card.TFrame", background=th["card"])
        style.configure("Header.TFrame", background=th["header"])
        style.configure("TLabel", background=th["bg"], foreground=th["txt"], font=self.font)
        style.configure("Card.TLabel", background=th["card"], foreground=th["txt"], font=self.font)
        style.configure("Bold.TLabel", background=th["card"], foreground=th["txt"], font=self.font_bold)
        style.configure("Hint.TLabel", background=th["card"], foreground=th["muted"], font=self.font_small)
        style.configure("Header.TLabel", background=th["header"], foreground=th["header_fg"],
                        font=self.font_title)
        style.configure("HeaderSub.TLabel", background=th["header"], foreground=th["header_sub"],
                        font=self.font_small)
        style.configure("Status.TLabel", background=th["bg"], foreground=th["muted"], font=self.font_small)
        style.configure("TButton", font=self.font, padding=(12, 6),
                        background=th["btn"], foreground=th["txt"],
                        bordercolor=th["border"], focuscolor=th["card"])
        style.map("TButton",
                  background=[("active", th["btn_hover"]), ("pressed", th["btn_hover"])],
                  foreground=[("disabled", th["muted"])])
        style.configure("Accent.TButton", font=self.font_bold, padding=(16, 8),
                        background=th["accent"], foreground=th["accent_fg"], borderwidth=0)
        style.map("Accent.TButton",
                  background=[("active", th["accent_d"]), ("disabled", th["accent_dis"])],
                  foreground=[("disabled", th["accent_dis_fg"])])
        style.configure("TEntry", padding=6, fieldbackground=th["entry"], foreground=th["txt"],
                        insertcolor=th["txt"], bordercolor=th["border"])
        style.configure("TCombobox", fieldbackground=th["entry"], background=th["entry"],
                        foreground=th["txt"], arrowcolor=th["txt"])
        style.map("TCombobox", fieldbackground=[("readonly", th["entry"])],
                  foreground=[("readonly", th["txt"])])
        style.configure("TSpinbox", fieldbackground=th["entry"], foreground=th["txt"],
                        arrowcolor=th["txt"], insertcolor=th["txt"])
        style.configure("TNotebook", background=th["bg"], borderwidth=0, tabmargins=(6, 6, 6, 0))
        style.configure("TNotebook.Tab", font=self.font, padding=(18, 9),
                        background=th["tab_bg"], foreground=th["muted"])
        style.map("TNotebook.Tab", background=[("selected", th["card"])],
                  foreground=[("selected", th["accent"])])
        style.configure("Treeview", font=self.font_small, rowheight=27,
                        background=th["tree"], fieldbackground=th["tree"], foreground=th["txt"])
        style.configure("Treeview.Heading", font=self.font_bold, background=th["head"],
                        foreground=th["txt"], relief="flat")
        style.map("Treeview", background=[("selected", th["accent"])],
                  foreground=[("selected", th["accent_fg"])])
        style.configure("TRadiobutton", background=th["card"], foreground=th["txt"], font=self.font)
        style.map("TRadiobutton", background=[("active", th["card"])])
        style.configure("TCheckbutton", background=th["card"], foreground=th["txt"], font=self.font)
        style.map("TCheckbutton", background=[("active", th["card"])])

        self.txt.configure(bg=th["tree"], fg=th["txt"], insertbackground=th["txt"])
        for name, col in th["status"].items():
            self.tree.tag_configure(name, background=col, foreground=th["txt"])
        self._draw_controls()

    def _draw_controls(self):
        th = THEMES[self.theme]
        _draw_flag(self.lang_canvas, self.lang, th["header"])
        # small language code next to the flag
        self.lang_canvas.create_text(56, 15, text=self.lang.upper(), fill=th["header_fg"],
                                     font=self.font_bold, anchor="e")
        _draw_theme_icon(self.theme_canvas, self.theme, th["header"])

    # ---------------- i18n ----------------
    def t(self, key, **kw):
        s = STRINGS[self.lang].get(key, key)
        return s.format(**kw) if kw else s

    def _toggle_lang(self):
        self.lang = "en" if self.lang == "es" else "es"
        self._retranslate()
        if self.result:
            self._render()

    def _retranslate(self):
        self.lbl_title.config(text=self.t("title"))
        self.lbl_sub.config(text=self.t("subtitle"))
        self.lbl_sources.config(text=self.t("sec_sources"))
        for row, key in ((self.lbl_claim, "claim"), (self.lbl_folder, "folder"),
                         (self.lbl_drivers, "drivers"), (self.lbl_driverlogs, "driverlogs"),
                         (self.lbl_daysroot, "daysroot")):
            row._lbl.config(text=self.t(f"lbl_{key}"))
            row._hint.config(text=self.t(f"hint_{key}"))
            row._btn.config(text=self.t("browse"))
        self.lbl_pairs.config(text=self.t("lbl_pairs"))
        self.rb_pair.config(text=self.t("pair_pair"))
        self.rb_b.config(text=self.t("pair_b"))
        self.rb_a.config(text=self.t("pair_a"))
        self.lbl_willcall.config(text=self.t("lbl_willcall"))
        self.lbl_hours.config(text=self.t("hours"))
        self.chk_suggest.config(text=self.t("chk_suggest"))
        self.chk_spread.config(text=self.t("chk_spread"))
        self.btn_run.config(text=self.t("btn_run"))
        self.btn_export.config(text=self.t("btn_export"))
        self.btn_csv.config(text=self.t("btn_csv"))
        self.btn_driverlogs.config(text=self.t("btn_driverlogs"))
        self.btn_help.config(text=self.t("btn_help"))
        self.nb.tab(self.tabs[0], text=self.t("tab_preview"))
        self.nb.tab(self.tabs[1], text=self.t("tab_report"))
        self.nb.tab(self.tabs[2], text=self.t("tab_assign"))
        for c in self.cols:
            self.tree.heading(c, text=self.t(f"c_{c}"))
        for c in self.acols:
            self.assign_tree.heading(c, text=self.t(f"c_{c}"))
        self.lbl_assign_hint.config(text=self.t("assign_hint"))
        self.lbl_assign.config(text=self.t("assign_lbl"))
        self.btn_assign.config(text=self.t("btn_assign"))
        self.btn_clear.config(text=self.t("btn_clear"))
        self._draw_controls()
        if not self.result:
            self.status.config(text=self.t("st_idle"))

    # ---------------- browse ----------------
    def browse_claim(self):
        p = filedialog.askopenfilename(title="ClaimInformation", filetypes=[("Excel", "*.xlsx")])
        if p:
            self.claim_var.set(p)
            if not self.folder_var.get().strip():
                self.folder_var.set(str(Path(p).parent))

    def browse_folder(self):
        p = filedialog.askdirectory(title=self.t("lbl_folder"))
        if p:
            self.folder_var.set(p)
            if not self.daysroot_var.get().strip():
                self.daysroot_var.set(p)

    def browse_drivers(self):
        p = filedialog.askopenfilename(title="Informacion de Drivers.xlsx",
                                       filetypes=[("Excel", "*.xlsx")])
        if p:
            self.drivers_var.set(p)

    def browse_driverlogs(self):
        p = filedialog.askdirectory(title=self.t("lbl_driverlogs"))
        if p:
            self.driverlogs_var.set(p)

    def browse_daysroot(self):
        p = filedialog.askdirectory(title=self.t("lbl_daysroot"))
        if p:
            self.daysroot_var.set(p)

    def show_help(self):
        messagebox.showinfo(self.t("help_title"), self.t("help_body"))

    # ---------------- run ----------------
    def run(self):
        claim = self.claim_var.get().strip()
        folder = self.folder_var.get().strip()
        if not claim or not Path(claim).exists():
            messagebox.showerror(self.t("err_title"), self.t("err_claim"))
            return
        if not folder or not Path(folder).exists():
            messagebox.showerror(self.t("err_title"), self.t("err_folder"))
            return
        drivers = self.drivers_var.get().strip() or None
        try:
            delta = float(self.willcall_var.get())
        except ValueError:
            delta = 2.0
        self.btn_run.config(state="disabled")
        self.btn_export.config(state="disabled")
        self.btn_csv.config(state="disabled")
        self.btn_driverlogs.config(state="disabled")
        self.status.config(text=self.t("st_working"), foreground=THEMES[self.theme]["muted"])
        self.txt.delete("1.0", "end")
        args = (claim, folder, drivers, self.driverlogs_var.get().strip() or None,
                self.strategy_var.get(), delta, self.suggest_var.get(), self.spread_var.get())
        threading.Thread(target=self._work, args=args, daemon=True).start()

    def _work(self, claim, folder, drivers, driverlogs, strategy, delta, suggest, spread):
        try:
            res = run_job(claim, folder, drivers_path=drivers, strategy=strategy,
                          willcall_hours=delta, suggest_driver=suggest, spread=spread,
                          driverlogs_folder=driverlogs)
        except Exception as e:  # pragma: no cover
            res = {"error": f"{type(e).__name__}: {e}"}
        self.root.after(0, lambda: self._finish(res))

    def _finish(self, res):
        self.btn_run.config(state="normal")
        if res.get("error"):
            self.status.config(text=self.t("st_error"), foreground="#e06c75")
            messagebox.showerror(self.t("st_error"), res["error"])
            return
        self.result = res
        self.btn_export.config(state="normal")
        self.btn_csv.config(state="normal")
        self.btn_driverlogs.config(state="normal")
        self._render()

    def _render(self):
        res = self.result
        if not res:
            return
        res["report"]["needs_driver"] = [
            {"date": r["date"], "trip": r["trip"], "member": r["member"], "milage": r.get("milage"),
             "county": r.get("county") or ""}
            for r in res["claim"]["rows"] if not r.get("driver") and r.get("flag") != "nofacturar"
        ]
        active = {r["trip"] for r in res["claim"]["rows"]
                  if r.get("flag") == "sugerido" and r.get("driver")}
        res["report"]["suggested"] = [s for s in (res["report"].get("suggested") or [])
                                      if s["trip"] in active]
        self.tree.delete(*self.tree.get_children())
        counts = {"OK": 0, "NOTA": 0, "SUGERIDO": 0, "REVISAR": 0, "ELEGIR": 0,
                  "NO FACTURAR": 0, "SIN DATO": 0}
        for row in res["claim"]["rows"]:
            stt = status_of(row)
            pu = row.get("pu")
            put = pu.strftime("%H:%M") if hasattr(pu, "strftime") else ""
            do = row.get("dropoff")
            dot = do.strftime("%H:%M") if hasattr(do, "strftime") else ""
            self.tree.insert("", "end", tags=(stt,), values=(
                row.get("row", ""),
                row.get("date_text", ""),
                row.get("member_raw") or row.get("member", ""),
                row.get("trip", ""),
                row.get("driver") or "",
                row.get("milage") if row.get("milage") is not None else "",
                put,
                dot,
                stt,
            ))
            counts[stt] += 1
        self.txt.delete("1.0", "end")
        self.txt.insert("end", report_text(res, self.lang))
        self.txt.insert("end", f"\n\n{self.t('prev_summary')}\n  "
                               + " | ".join(f"{k} {v}" for k, v in counts.items()) + "\n")
        self._populate_assign()
        self.status.config(text=self.t("st_done", ok=counts["OK"], nota=counts["NOTA"],
                                       sug=counts["SUGERIDO"], elegir=counts["ELEGIR"],
                                       nofact=counts["NO FACTURAR"], revisar=counts["REVISAR"],
                                       sindato=counts["SIN DATO"]),
                           foreground=THEMES[self.theme]["accent"])

    # ---------------- assign tab ----------------
    def _populate_assign(self):
        self.assign_tree.delete(*self.assign_tree.get_children())
        self.assign_combo.set("")
        self.assign_combo["values"] = ()
        self.assign_info.config(text="")
        self._assign_map = {}
        if not self.result:
            return
        for row in self.result["claim"]["rows"]:
            if row.get("flag") == "nofacturar":
                continue
            suggested = row.get("flag") == "sugerido"
            if row.get("driver") and not suggested:
                continue
            mi = row.get("milage")
            item = self.assign_tree.insert("", "end", values=(
                row.get("date_text", ""),
                row.get("member_raw") or row.get("member", ""),
                row.get("trip", ""),
                "" if mi is None else mi,
                row.get("driver") or "",
            ))
            self._assign_map[item] = row

    def _on_assign_select(self, _evt=None):
        sel = self.assign_tree.selection()
        if not sel:
            return
        row = self._assign_map.get(sel[0])
        if not row:
            return
        cands = (self.result["report"].get("driver_candidates") or {}).get(
            (row.get("date"), row.get("county") or ""), [])
        vals = []
        cur = 0
        for i, c in enumerate(cands):
            tag = self.t("sugg_free") if c["count"] == 0 else f"{c['count']} {self.t('sugg_trips')}"
            vals.append(f"{c['num']} - {c['name']}  ({tag})")
            if row.get("driver") and c["num"] == row["driver"]:
                cur = i
        self._assign_cands = cands
        self.assign_combo["values"] = vals
        self.assign_combo.current(cur if vals else -1)
        self._show_cand_info()

    def _show_cand_info(self):
        idx = self.assign_combo.current()
        cands = self._assign_cands
        if idx < 0 or idx >= len(cands):
            self.assign_info.config(text="")
            return
        info = (self.result.get("drivers") or {}).get("table", {}).get(cands[idx]["num"], {})
        self.assign_info.config(
            text=f"License: {info.get('license') or '-'}   VIN: {info.get('vin') or '-'}")

    def assign_driver(self):
        sel = self.assign_tree.selection()
        if not sel:
            return
        row = self._assign_map.get(sel[0])
        idx = self.assign_combo.current()
        cands = self._assign_cands
        if not row or idx < 0 or idx >= len(cands):
            return
        num = cands[idx]["num"]
        info = (self.result.get("drivers") or {}).get("table", {}).get(num, {})
        row["driver"] = num
        row["license"] = info.get("license", "")
        row["vin"] = info.get("vin", "")
        row["flag"] = ""
        self._render()

    def clear_driver(self):
        sel = self.assign_tree.selection()
        if not sel:
            return
        row = self._assign_map.get(sel[0])
        if row:
            row["driver"] = row["license"] = row["vin"] = ""
            row["flag"] = "elegir"
            self._render()

    # ---------------- exports ----------------
    def export(self):
        if not self.result:
            return
        pend = [r for r in self.result["claim"]["rows"]
                if not r.get("driver") and r.get("flag") != "nofacturar"]
        if pend and not messagebox.askyesno(self.t("pend_title"), self.t("pend_body", n=len(pend))):
            return
        src = Path(self.result["claim_path"])
        default = src.with_name(src.stem + " FILLED.xlsx")
        path = filedialog.asksaveasfilename(
            title=self.t("btn_export"), defaultextension=".xlsx",
            initialdir=str(default.parent), initialfile=default.name,
            filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        info = write_output(self.result["claim"], path)
        messagebox.showinfo(self.t("exp_title"),
                            self.t("exp_body", path=path, rows=info["rows"], sheets=info["sheets"]))

    def save_csv(self):
        if not self.result:
            return
        src = Path(self.result["claim_path"])
        path = filedialog.asksaveasfilename(
            title=self.t("btn_csv"), defaultextension=".csv",
            initialdir=str(src.parent), initialfile=src.stem + " REPORT.csv",
            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        write_report_csv(path, self.result)
        messagebox.showinfo(self.t("csv_title"), self.t("csv_body", path=path))

    # ---------------- driverlogs ----------------
    def generate_driverlogs(self):
        if not self.result:
            return
        templates = self.driverlogs_var.get().strip()
        if not templates or not Path(templates).is_dir():
            messagebox.showerror(self.t("err_title"), self.t("err_driverlogs"))
            return
        root = self.daysroot_var.get().strip() or self.folder_var.get().strip()
        if not root or not Path(root).is_dir():
            messagebox.showerror(self.t("err_title"), self.t("err_daysroot"))
            return
        from .driverlogs import generate_driverlogs, report_lines
        try:
            gen = generate_driverlogs(self.result["claim"]["rows"], templates, root)
        except Exception as e:                          # pragma: no cover
            messagebox.showerror(self.t("st_error"), f"{type(e).__name__}: {e}")
            return
        self.result["driverlogs"] = gen
        self.txt.insert("end", "\n\n" + report_lines(gen, self.lang) + "\n")
        self.txt.see("end")
        messagebox.showinfo(
            self.t("dl_title"),
            self.t("dl_body", n=len(gen["created"]), root=root,
                   skipped=len(gen["skipped"]), errors=len(gen["errors"])))


def main():
    _init_dpi()
    root = tk.Tk()
    try:
        root.call("tk", "scaling", 1.25)
    except Exception:
        pass
    App(root)
    root.mainloop()
