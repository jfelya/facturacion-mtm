"""Tkinter desktop UI for the claim filler.

- DPI-aware, Segoe UI Semibold base font
- Light/Dark pastel themes (dark by default), one toggle button
- Bilingual ES (default) / EN, one flag button
- Explicit help: what files to provide and how
"""
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from .pipeline import run_job
from .report import report_text, write_report_csv
from .writer import write_output
from . import uikit
from .uikit import THEMES
from .strings import STRINGS

def status_of(row):
    flag = row.get("flag") or ""
    if flag == "facturado":
        return "FACTURADO"
    if flag == "revisar":
        return "REVISAR"
    if row.get("driver") and row.get("milage") is not None:
        if flag == "sugerido":
            return "SUGERIDO"
        if flag == "balanceado":
            return "BALANCEADO"
        return "NOTA" if flag == "nota" else "OK"
    if flag == "nofacturar":
        return "NO FACTURAR"
    if not row.get("driver"):
        return "ELEGIR" if row.get("milage") is not None else "SIN DATO"
    return "REVISAR"


def _init_dpi():
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def _set_window_icon(root):
    """Window/taskbar icon from assets/icon.png (works both in dev and inside the onefile exe)."""
    try:
        import sys
        base = getattr(sys, "_MEIPASS", None)
        p = (Path(base) / "assets" / "icon.png") if base else (
            Path(__file__).resolve().parents[1] / "assets" / "icon.png")
        if p.exists():
            root.iconphoto(True, tk.PhotoImage(file=str(p)))
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
        self._imgs = {}

        root.title("Facturación MTM")
        win_w, win_h = uikit.tokens.METRICS["window"]
        root.geometry(f"{win_w}x{win_h}")
        min_w, min_h = uikit.tokens.METRICS["window_min"]
        root.minsize(min_w, min_h)

        self.fonts = uikit.make_fonts(root)
        self.font = self.fonts.base
        self.font_small = self.fonts.small
        self.font_mono = self.fonts.mono

        self.claim_var = tk.StringVar()
        self.folder_var = tk.StringVar()
        self.drivers_var = tk.StringVar()
        self.driverlogs_var = tk.StringVar()
        self.daysroot_var = tk.StringVar()
        self.strategy_var = tk.StringVar(value="first_row_B")
        self.willcall_var = tk.StringVar(value="2")
        self.suggest_var = tk.BooleanVar(value=True)
        self.spread_var = tk.BooleanVar(value=True)
        self.balance_var = tk.BooleanVar(value=True)

        self._build()
        self._apply_theme()
        self._retranslate()

    # ---------------- layout ----------------
    def _build(self):
        head = ttk.Frame(self.root, style="Header.TFrame", padding=(16, 10))
        head.pack(fill="x")
        self.hline = uikit.widgets.hseparator(self.root, THEMES[self.theme]["border"])
        self.hline.pack(fill="x")
        left = ttk.Frame(head, style="Header.TFrame")
        left.pack(side="left")
        self.lbl_title = ttk.Label(left, style="Header.TLabel")
        self.lbl_title.pack(anchor="w")
        self.lbl_sub = ttk.Label(left, style="HeaderSub.TLabel")
        self.lbl_sub.pack(anchor="w", pady=(2, 0))

        ctrl = ttk.Frame(head, style="Header.TFrame")
        ctrl.pack(side="right")
        self.theme_lbl = tk.Label(ctrl, bd=0, highlightthickness=0, cursor="hand2")
        self.theme_lbl.pack(side="right", padx=(10, 0))
        self.theme_lbl.bind("<Button-1>", lambda e: self._toggle_theme())
        self.lang_lbl = tk.Label(ctrl, bd=0, highlightthickness=0, cursor="hand2")
        self.lang_lbl.pack(side="right")
        self.lang_lbl.bind("<Button-1>", lambda e: self._toggle_lang())

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
        self.rb_b = ttk.Radiobutton(opt, text="", variable=self.strategy_var, value="first_row_B")
        self.rb_b.pack(side="left", padx=(6, 0))
        self.rb_pair = ttk.Radiobutton(opt, text="", variable=self.strategy_var, value="pair")
        self.rb_pair.pack(side="left", padx=(10, 0))
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
        self.chk_balance = ttk.Checkbutton(opt2, text="", variable=self.balance_var)
        self.chk_balance.pack(side="left", padx=(18, 0))

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
        self.btn_bulk = ttk.Button(act, command=self.generate_bulk, state="disabled")
        self.btn_bulk.pack(side="left")

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

        self.sline = uikit.widgets.hseparator(self.root, THEMES[self.theme]["border"])
        self.sline.pack(fill="x", side="bottom")
        self.statusbar = ttk.Frame(self.root, style="Header.TFrame")
        self.statusbar.pack(fill="x", side="bottom")
        self.status_dot = uikit.widgets.StatusDot(
            self.statusbar, size=uikit.tokens.METRICS["status_dot"],
            bg=THEMES[self.theme]["header"])
        self.status_dot.pack(side="left", padx=(16, 8), pady=9)
        self.status = ttk.Label(self.statusbar, style="Status.TLabel", anchor="w")
        self.status.pack(side="left", fill="x", expand=True, padx=(0, 14), pady=6)

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
        th = uikit.apply_theme(self.root, self.theme, self.fonts)
        self.txt.configure(bg=th["tree"], fg=th["txt"], insertbackground=th["txt"])
        uikit.tag_rows(self.tree, self.theme)
        # 1-px separators (toolbar bottom / status top)
        if hasattr(self, "hline"):
            self.hline.configure(bg=th["border"])
        if hasattr(self, "sline"):
            self.sline.configure(bg=th["border"])
        if hasattr(self, "status_dot"):
            self.status_dot.configure(bg=th["header"])
            self._dot(th["muted"])
        self._draw_controls()

    def _dot(self, color):
        self.status_dot.set(color)

    def _draw_controls(self):
        th = THEMES[self.theme]
        flag = self._img("ve" if self.lang == "es" else "us")
        if flag is not None:
            self.lang_lbl.configure(image=flag, bg=th["header"])
        icon = self._img("moon" if self.theme == "dark" else "sun")
        if icon is not None:
            self.theme_lbl.configure(image=icon, bg=th["header"])

    def _img(self, name):
        return uikit.load_icon(self.root, name, self._imgs)

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
        self.chk_balance.config(text=self.t("chk_balance"))
        self.btn_run.config(text=self.t("btn_run"))
        self.btn_export.config(text=self.t("btn_export"))
        self.btn_csv.config(text=self.t("btn_csv"))
        self.btn_driverlogs.config(text=self.t("btn_driverlogs"))
        self.btn_bulk.config(text=self.t("btn_bulk"))
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
            self._dot(THEMES[self.theme]["muted"])

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
        # warn if the sources folder has no trip files (PU/DropOff/Dalia-Milage would be empty)
        sources = None
        try:
            from .pipeline import scan_sources
            sources = scan_sources(folder, drivers)
            if not sources.get("trips"):
                if not messagebox.askokcancel(self.t("notrips_title"), self.t("notrips_body")):
                    return
        except Exception:
            sources = None
        try:
            delta = float(self.willcall_var.get())
        except ValueError:
            delta = 2.0
        self.btn_run.config(state="disabled")
        self.btn_export.config(state="disabled")
        self.btn_csv.config(state="disabled")
        self.btn_driverlogs.config(state="disabled")
        self.btn_bulk.config(state="disabled")
        self.status.config(text=self.t("st_working"), foreground=THEMES[self.theme]["muted"])
        self._dot(THEMES[self.theme]["accent"])
        self.txt.delete("1.0", "end")
        args = (claim, folder, drivers, self.driverlogs_var.get().strip() or None,
                self.strategy_var.get(), delta, self.suggest_var.get(), self.spread_var.get(),
                self.balance_var.get(), sources)
        threading.Thread(target=self._work, args=args, daemon=True).start()

    def _work(self, claim, folder, drivers, driverlogs, strategy, delta, suggest, spread, balance,
              sources=None):
        try:
            res = run_job(claim, folder, drivers_path=drivers, strategy=strategy,
                          willcall_hours=delta, suggest_driver=suggest, spread=spread, balance=balance,
                          driverlogs_folder=driverlogs, sources=sources)
        except Exception as e:  # pragma: no cover
            res = {"error": f"{type(e).__name__}: {e}"}
        self.root.after(0, lambda: self._finish(res))

    def _finish(self, res):
        self.btn_run.config(state="normal")
        if res.get("error"):
            self.status.config(text=self.t("st_error"), foreground=THEMES[self.theme]["danger"])
            self._dot(THEMES[self.theme]["danger"])
            messagebox.showerror(self.t("st_error"), res["error"])
            return
        self.result = res
        self.btn_export.config(state="normal")
        self.btn_csv.config(state="normal")
        self.btn_driverlogs.config(state="normal")
        self.btn_bulk.config(state="normal")
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
                  "NO FACTURAR": 0, "FACTURADO": 0, "SIN DATO": 0, "BALANCEADO": 0}
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
                                       sug=counts["SUGERIDO"], bal=counts["BALANCEADO"],
                                       elegir=counts["ELEGIR"],
                                       nofact=counts["NO FACTURAR"],
                                       facturado=counts["FACTURADO"],
                                       revisar=counts["REVISAR"],
                                       sindato=counts["SIN DATO"]),
                           foreground=THEMES[self.theme]["accent"])
        self._dot(THEMES[self.theme]["success"])

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
            if row.get("flag") in ("nofacturar", "facturado"):
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
                if not r.get("driver") and r.get("flag") not in ("nofacturar", "facturado")]
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
        try:
            info = write_output(self.result["claim"], path)
        except (ValueError, OSError) as e:
            messagebox.showerror(self.t("st_error"), str(e))
            return
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
        try:
            write_report_csv(path, self.result)
        except OSError as e:
            messagebox.showerror(self.t("st_error"), str(e))
            return
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

    # ---------------- BULK UPLOAD ----------------
    def generate_bulk(self):
        if not self.result:
            return
        root = self.daysroot_var.get().strip() or self.folder_var.get().strip()
        if not root or not Path(root).is_dir():
            messagebox.showerror(self.t("err_title"), self.t("err_daysroot"))
            return
        from .bulk import generate_bulks, report_lines
        try:
            gen = generate_bulks(self.result["claim"]["rows"], root)
        except Exception as e:                          # pragma: no cover
            messagebox.showerror(self.t("st_error"), f"{type(e).__name__}: {e}")
            return
        self.result["bulk"] = gen
        self.txt.insert("end", "\n\n" + report_lines(gen, self.lang) + "\n")
        self.txt.see("end")
        messagebox.showinfo(
            self.t("bulk_title"),
            self.t("bulk_body", n=len(gen["created"]), root=root,
                   excluded=len(gen.get("excluded", [])), errors=len(gen.get("errors", []))))


def main():
    _init_dpi()
    root = tk.Tk()
    try:
        root.call("tk", "scaling", 1.25)
    except Exception:
        pass
    App(root)
    _set_window_icon(root)
    try:
        root.state("zoomed")          # abrir maximizado (pantalla completa) en Windows
    except Exception:
        try:
            root.attributes("-zoomed", True)
        except Exception:
            pass
    root.mainloop()
