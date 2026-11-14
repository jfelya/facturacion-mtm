"""Main PySide6 window for Facturación MTM."""
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QThread
from PySide6.QtGui import QFont, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QStatusBar,
    QTabWidget,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..bulk import generate_bulks, report_lines as bulk_lines
from ..driverlogs import generate_driverlogs, report_lines as driverlog_lines
from ..driverpdf import DriverPdfError, process_days
from ..pipeline import run_job, scan_sources
from ..report import report_text, write_report_csv
from ..status import status_of
from ..writer import ensure_not_source, write_output
from .dialogs.assign_driver import AssignDriverDialog
from .dialogs.help_dialog import HelpDialog
from .dialogs import messages
from .models.claim_filter_proxy import ClaimFilterProxy
from .models.claim_table_model import ClaimTableModel
from .delegates.row_delegate import RowDelegate
from .delegates.status_delegate import StatusDelegate
from .theme import icons
from .theme.qss import apply_theme
from .theme.window import set_dark_title_bar
from .theme.tokens import METRICS
from .view_model import (
    AppState,
    counts,
    default_csv_name,
    default_export_name,
    pending_rows,
    row_key,
)
from .widgets.detail_drawer import DetailDrawer
from .widgets.path_picker import PathPicker
from .widgets.status_dot import StatusDot
from .widgets.summary_strip import SummaryStrip
from .workers.job_worker import JobWorker


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.state = AppState()
        self._thread = None
        self._worker = None
        self._selected_row = None
        self._shortcuts = []

        self.resize(*METRICS["window"])
        self.setMinimumSize(*METRICS["window_min"])
        self._build()
        self._apply_theme()
        self._retranslate()
        self._set_busy(False)

    # ------------------------------------------------------------------ build
    def _build(self):
        central = QWidget()
        central.setObjectName("Root")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_topbar())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(12, 12, 12, 8)
        body_layout.setSpacing(12)
        body_layout.addWidget(self._build_sidebar(), 0)
        body_layout.addWidget(self._build_center(), 1)
        root.addWidget(body, 1)

        self.setStatusBar(self._build_statusbar())
        self._shortcuts = [
            self._shortcut("Ctrl+R", self.run),
            self._shortcut("Ctrl+E", self.export_excel),
            self._shortcut("Ctrl+Shift+E", self.save_csv),
            self._shortcut("Ctrl+D", self.generate_driverlogs),
            self._shortcut("Ctrl+B", self.generate_bulk),
            self._shortcut("F1", self.show_help),
        ]

    def _shortcut(self, key, slot):
        shortcut = QShortcut(QKeySequence(key), self)
        shortcut.activated.connect(slot)
        return shortcut

    def _build_topbar(self):
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(METRICS["topbar_height"])
        row = QHBoxLayout(bar)
        row.setContentsMargins(16, 8, 16, 8)
        row.setSpacing(10)

        self.logo = QLabel()
        pix = icons.icon("icon").pixmap(QSize(32, 32))
        if not pix.isNull():
            self.logo.setPixmap(pix)
        row.addWidget(self.logo)

        titles = QVBoxLayout()
        titles.setSpacing(0)
        self.lbl_title = QLabel("Facturación MTM")
        self.lbl_title.setObjectName("PageTitle")
        self.lbl_sub = QLabel()
        self.lbl_sub.setObjectName("Subtitle")
        titles.addWidget(self.lbl_title)
        titles.addWidget(self.lbl_sub)
        row.addLayout(titles)
        row.addStretch(1)

        self.btn_theme = QToolButton()
        self.btn_theme.setIconSize(QSize(20, 20))
        self.btn_theme.clicked.connect(self.toggle_theme)
        row.addWidget(self.btn_theme)
        self.btn_lang = QToolButton()
        self.btn_lang.setIconSize(QSize(26, 13))
        self.btn_lang.clicked.connect(self.toggle_lang)
        row.addWidget(self.btn_lang)
        self.btn_help = QPushButton()
        self.btn_help.setProperty("role", "ghost")
        self.btn_help.clicked.connect(self.show_help)
        row.addWidget(self.btn_help)
        return bar

    def _build_sidebar(self):
        side = QFrame()
        side.setObjectName("Sidebar")
        side.setFixedWidth(METRICS["sidebar_width"])
        outer = QVBoxLayout(side)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setObjectName("SidebarScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("SidebarContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 14, 14, 12)
        layout.setSpacing(10)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.lbl_sources = QLabel()
        self.lbl_sources.setObjectName("SectionTitle")
        layout.addWidget(self.lbl_sources)

        self.pick_claim = self._picker("claim_path", self.browse_claim)
        self.pick_folder = self._picker("sources_folder", self.browse_folder)
        self.pick_drivers = self._picker("drivers_path", self.browse_drivers)
        self.pick_driverlogs = self._picker("driverlogs_folder", self.browse_driverlogs)
        self.pick_days = self._picker("days_root", self.browse_daysroot)
        for picker in (self.pick_claim, self.pick_folder, self.pick_drivers,
                       self.pick_driverlogs, self.pick_days):
            layout.addWidget(picker)

        line = QFrame()
        line.setObjectName("HLine")
        layout.addWidget(line)
        self.lbl_options = QLabel()
        self.lbl_options.setObjectName("SectionTitle")
        layout.addWidget(self.lbl_options)

        self.lbl_pairs = QLabel()
        self.lbl_pairs.setObjectName("FieldLabel")
        layout.addWidget(self.lbl_pairs)
        self.radio_group = QButtonGroup(self)
        self.rb_b = QRadioButton()
        self.rb_pair = QRadioButton()
        self.rb_a = QRadioButton()
        for rb, value in ((self.rb_b, "first_row_B"), (self.rb_pair, "pair"),
                          (self.rb_a, "first_row_A")):
            self.radio_group.addButton(rb)
            rb.toggled.connect(
                lambda checked, v=value: checked and setattr(self.state, "strategy", v)
            )
            layout.addWidget(rb)
        self.rb_b.setChecked(True)

        will = QHBoxLayout()
        self.lbl_willcall = QLabel()
        self.lbl_willcall.setObjectName("FieldLabel")
        will.addWidget(self.lbl_willcall)
        self.spin_willcall = QSpinBox()
        self.spin_willcall.setRange(0, 8)
        self.spin_willcall.setValue(2)
        self.spin_willcall.setFixedWidth(58)
        self.spin_willcall.valueChanged.connect(
            lambda value: setattr(self.state, "willcall_hours", float(value))
        )
        will.addWidget(self.spin_willcall)
        self.lbl_hours = QLabel()
        self.lbl_hours.setObjectName("Hint")
        will.addWidget(self.lbl_hours)
        will.addStretch(1)
        layout.addLayout(will)

        self.chk_suggest = QCheckBox()
        self.chk_suggest.setChecked(True)
        self.chk_suggest.toggled.connect(lambda v: setattr(self.state, "suggest", v))
        self.chk_spread = QCheckBox()
        self.chk_spread.setChecked(True)
        self.chk_spread.toggled.connect(lambda v: setattr(self.state, "spread", v))
        self.chk_balance = QCheckBox()
        self.chk_balance.setChecked(True)
        self.chk_balance.toggled.connect(lambda v: setattr(self.state, "balance", v))
        layout.addWidget(self.chk_suggest)
        layout.addWidget(self.chk_spread)
        layout.addWidget(self.chk_balance)
        layout.addStretch(1)

        self.btn_run = QPushButton()
        self.btn_run.setProperty("role", "primary")
        self.btn_run.setMinimumHeight(36)
        self.btn_run.clicked.connect(self.run)
        bottom = QFrame()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(14, 8, 14, 12)
        bottom_layout.addWidget(self.btn_run)
        outer.addWidget(bottom)
        return side

    def _picker(self, attr, browse):
        picker = PathPicker(on_browse=browse)
        picker.changed.connect(lambda value, a=attr: setattr(self.state, a, value))
        setattr(self, f"_pick_{attr}", picker)
        return picker

    def _build_center(self):
        center = QWidget()
        layout = QVBoxLayout(center)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.summary = SummaryStrip()
        self.summary.status_selected.connect(self._summary_selected)
        layout.addWidget(self.summary)

        actions = QHBoxLayout()
        actions.setSpacing(6)
        self.btn_export = QPushButton()
        self.btn_csv = QPushButton()
        self.btn_driverlogs = QPushButton()
        self.btn_pdfs = QPushButton()
        self.btn_bulk = QPushButton()
        for button, slot in ((self.btn_export, self.export_excel), (self.btn_csv, self.save_csv),
                             (self.btn_driverlogs, self.generate_driverlogs),
                             (self.btn_pdfs, self.generate_pdfs),
                             (self.btn_bulk, self.generate_bulk)):
            button.clicked.connect(slot)
            actions.addWidget(button)
        actions.addStretch(1)
        self.search = QLineEdit()
        self.search.setFixedWidth(260)
        self.search.textChanged.connect(self._search_changed)
        actions.addWidget(self.search)
        self.btn_clear_filters = QPushButton()
        self.btn_clear_filters.setProperty("role", "ghost")
        self.btn_clear_filters.clicked.connect(self._clear_filters)
        actions.addWidget(self.btn_clear_filters)
        layout.addLayout(actions)

        self.tabs = QTabWidget()
        self.preview_page = QWidget()
        preview_layout = QVBoxLayout(self.preview_page)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_stack = QStackedWidget()
        self.empty_page = self._build_empty()
        self.table_page = QWidget()
        table_layout = QVBoxLayout(self.table_page)
        table_layout.setContentsMargins(0, 0, 0, 0)
        self.table = QTableView()
        self.model = ClaimTableModel(lang=self.state.lang, theme=self.state.theme)
        self.proxy = ClaimFilterProxy(self)
        self.proxy.setSourceModel(self.model)
        self.table.setModel(self.proxy)
        self.row_delegate = RowDelegate(self.table)
        self.table.setItemDelegate(self.row_delegate)
        self.delegate = StatusDelegate(self.state.theme, self.table)
        self.table.setItemDelegateForColumn(8, self.delegate)
        self._configure_table()
        table_layout.addWidget(self.table)
        self.preview_stack.addWidget(self.empty_page)
        self.preview_stack.addWidget(self.table_page)
        preview_layout.addWidget(self.preview_stack)
        self.tabs.addTab(self.preview_page, "")

        self.report = QPlainTextEdit()
        self.report.setReadOnly(True)
        mono = QFont("Consolas")
        mono.setPixelSize(12)
        self.report.setFont(mono)
        self.tabs.addTab(self.report, "")
        layout.addWidget(self.tabs, 1)

        self.detail = DetailDrawer(self.state.t)
        self.detail.assign_requested.connect(self.assign_selected)
        self.detail.clear_requested.connect(self.clear_selected)
        layout.addWidget(self.detail)
        return center

    def _configure_table(self):
        table = self.table
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setShowGrid(False)
        table.setAlternatingRowColors(False)
        table.setWordWrap(False)
        table.setTextElideMode(Qt.TextElideMode.ElideRight)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(METRICS["row_height"])
        table.setSortingEnabled(False)
        header = table.horizontalHeader()
        header.setFixedHeight(METRICS["header_height"])
        header.setMinimumSectionSize(48)
        widths = (48, 100, 220, 130, 64, 70, 64, 78, 120)
        for index, width in enumerate(widths):
            header.setSectionResizeMode(
                index,
                QHeaderView.ResizeMode.Stretch if index in (2, 3)
                else QHeaderView.ResizeMode.Interactive,
            )
            table.setColumnWidth(index, width)
        table.selectionModel().currentRowChanged.connect(self._current_changed)
        table.doubleClicked.connect(self._double_clicked)

    def _build_empty(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addStretch(1)
        self.empty_title = QLabel()
        self.empty_title.setObjectName("PageTitle")
        self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_hint = QLabel()
        self.empty_hint.setObjectName("Hint")
        self.empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_hint.setWordWrap(True)
        layout.addWidget(self.empty_title)
        layout.addWidget(self.empty_hint)
        layout.addStretch(1)
        return page

    def _build_statusbar(self):
        bar = QStatusBar()
        bar.setSizeGripEnabled(False)
        self.status_dot = StatusDot(METRICS["status_dot"])
        bar.addWidget(self.status_dot)
        self.status_label = QLabel()
        bar.addWidget(self.status_label, 1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setFixedWidth(120)
        self.progress.hide()
        bar.addPermanentWidget(self.progress)
        self.version_label = QLabel("v3.0.0 · 64-bit")
        self.version_label.setObjectName("Version")
        bar.addPermanentWidget(self.version_label)
        return bar

    # ------------------------------------------------------------------ i18n/theme
    def _apply_theme(self):
        apply_theme(self.app, self.state.theme)
        set_dark_title_bar(self, self.state.theme == "dark")
        if hasattr(self, "model"):
            self.model.set_theme(self.state.theme)
            self.delegate.set_theme(self.state.theme)
        if hasattr(self, "btn_theme"):
            icon = "moon" if self.state.theme == "dark" else "sun"
            self.btn_theme.setIcon(icons.icon(icon))
        if hasattr(self, "btn_lang"):
            self.btn_lang.setIcon(icons.icon("ve" if self.state.lang == "es" else "us"))
        if hasattr(self, "status_dot"):
            if self.state.result:
                self.status_dot.set_color("#3FB950")
            else:
                self.status_dot.set_color("#9AA7B4")

    def _retranslate(self):
        t = self.state.t
        self.setWindowTitle(t("title"))
        self.lbl_sub.setText(t("subtitle"))
        self.lbl_sources.setText(t("sec_sources"))
        for picker, key in (
            (self.pick_claim, "claim"), (self.pick_folder, "folder"),
            (self.pick_drivers, "drivers"), (self.pick_driverlogs, "driverlogs"),
            (self.pick_days, "daysroot"),
        ):
            picker.set_labels(t(f"lbl_{key}"), t(f"hint_{key}"), t("browse"))
        self.lbl_options.setText(t("sec_options"))
        self.lbl_pairs.setText(t("lbl_pairs"))
        self.rb_b.setText(t("pair_b"))
        self.rb_pair.setText(t("pair_pair"))
        self.rb_a.setText(t("pair_a"))
        self.lbl_willcall.setText(t("lbl_willcall"))
        self.lbl_hours.setText(t("hours"))
        self.chk_suggest.setText(t("chk_suggest"))
        self.chk_spread.setText(t("chk_spread"))
        self.chk_balance.setText(t("chk_balance"))
        self.btn_run.setText(t("btn_run"))
        self.btn_export.setText(t("btn_export"))
        self.btn_csv.setText(t("btn_csv"))
        self.btn_driverlogs.setText(t("btn_driverlogs"))
        self.btn_pdfs.setText(t("btn_pdfs"))
        self.btn_bulk.setText(t("btn_bulk"))
        self.btn_help.setText(t("btn_help"))
        self.btn_clear_filters.setText(t("filter_clear"))
        self.search.setPlaceholderText(t("filter_search"))
        self.tabs.setTabText(0, t("tab_preview"))
        self.tabs.setTabText(1, t("tab_report"))
        self.summary.set_all_text(t("all"))
        self.empty_title.setText(t("empty_title"))
        self.empty_hint.setText(t("empty_hint"))
        self.detail.set_labels(t)
        self.btn_theme.setToolTip(t("theme_tooltip"))
        self.btn_lang.setToolTip(t("lang_tooltip"))
        self.btn_lang.setIcon(icons.icon("ve" if self.state.lang == "es" else "us"))
        self.btn_theme.setIcon(icons.icon("moon" if self.state.theme == "dark" else "sun"))
        self.model.set_language(self.state.lang)
        self.detail.set_row(self._selected_row)
        if not self.state.result:
            self.status_label.setText(t("st_idle"))

    def toggle_theme(self):
        self.state.theme = "light" if self.state.theme == "dark" else "dark"
        self._apply_theme()

    def toggle_lang(self):
        self.state.lang = "en" if self.state.lang == "es" else "es"
        self._retranslate()
        if self.state.result:
            self._render(preserve=True)

    # ------------------------------------------------------------------ run/worker
    def run(self):
        if self._thread is not None:
            return
        claim = self.state.claim_path.strip()
        folder = self.state.sources_folder.strip()
        if not claim or not Path(claim).exists():
            messages.error(self, self.state.t("err_title"), self.state.t("err_claim"))
            return
        if not folder or not Path(folder).exists():
            messages.error(self, self.state.t("err_title"), self.state.t("err_folder"))
            return
        drivers = self.state.drivers_path.strip() or None
        sources = None
        try:
            sources = scan_sources(folder, drivers)
            if not sources.get("trips"):
                if not messages.confirm(self, self.state.t("notrips_title"),
                                        self.state.t("notrips_body")):
                    return
        except Exception:
            sources = None

        options = dict(
            claim_path=claim,
            sources_folder=folder,
            drivers_path=drivers,
            strategy=self.state.strategy,
            willcall_hours=float(self.state.willcall_hours),
            suggest_driver=self.state.suggest,
            sort_by_date=True,
            spread=self.state.spread,
            balance=self.state.balance,
            driverlogs_folder=self.state.driverlogs_folder.strip() or None,
            sources=sources,
        )
        self.state.sources = sources
        self._set_busy(True)
        self.status_label.setText(self.state.t("st_working"))
        self.status_dot.set_color("#4C8DFF")

        thread = QThread(self)
        worker = JobWorker(options)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_finished)
        worker.failed.connect(self._on_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._thread_finished)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _on_finished(self, result):
        self._set_busy(False)
        if result.get("error"):
            self._show_error(result["error"])
            return
        self.state.result = result
        self._render(preserve=False)
        self.status_dot.set_color("#3FB950")

    def _on_failed(self, message):
        self._set_busy(False)
        self._show_error(message)

    def _show_error(self, message):
        self.status_label.setText(self.state.t("st_error"))
        self.status_dot.set_color("#F85149")
        messages.error(self, self.state.t("st_error"), message)

    def _thread_finished(self):
        self._thread = None
        self._worker = None

    def _set_busy(self, busy):
        self._busy = busy
        self.progress.setVisible(busy)
        for widget in (self.pick_claim, self.pick_folder, self.pick_drivers,
                       self.pick_driverlogs, self.pick_days, self.rb_b, self.rb_pair,
                       self.rb_a, self.spin_willcall, self.chk_suggest, self.chk_spread,
                       self.chk_balance, self.search):
            widget.setEnabled(not busy)
        self.btn_run.setEnabled(not busy)
        if busy:
            self.detail.btn_assign.setEnabled(False)
            self.detail.btn_clear.setEnabled(False)
        elif self._selected_row is not None:
            self.detail.set_row(self._selected_row)
        self._update_actions()

    def _update_actions(self):
        enabled = bool(self.state.result) and not getattr(self, "_busy", False)
        for button in (self.btn_export, self.btn_csv, self.btn_driverlogs,
                       self.btn_pdfs, self.btn_bulk):
            button.setEnabled(enabled)

    # ------------------------------------------------------------------ render
    def _render(self, preserve=True):
        result = self.state.result
        if not result:
            return
        key = self.state.selected_key if preserve else None
        rows = result["claim"]["rows"]
        self.model.set_rows(rows)
        self.model.set_language(self.state.lang)
        if hasattr(self.proxy, "beginFilterChange"):
            self.proxy.beginFilterChange()
            self.proxy.endFilterChange(self.proxy.Direction.Rows)
        else:
            self.proxy.invalidate()
        status_counts = counts(rows)
        self.summary.set_counts(status_counts)
        text = report_text(result, self.state.lang)
        text += "\n\n" + self.state.t("prev_summary") + "\n  "
        text += " | ".join(f"{k} {v}" for k, v in status_counts.items()) + "\n"
        self.report.setPlainText(text)
        self.preview_stack.setCurrentIndex(1)
        self.status_label.setText(self.state.t(
            "st_done", ok=status_counts.get("OK", 0), nota=status_counts.get("NOTA", 0),
            sug=status_counts.get("SUGERIDO", 0), bal=status_counts.get("BALANCEADO", 0),
            elegir=status_counts.get("ELEGIR", 0), nofact=status_counts.get("NO FACTURAR", 0),
            facturado=status_counts.get("FACTURADO", 0), revisar=status_counts.get("REVISAR", 0),
            sindato=status_counts.get("SIN DATO", 0),
        ))
        self.status_dot.set_color("#3FB950")
        self.detail.set_row(None)
        self._selected_row = None
        self.state.selected_key = None
        self._update_actions()
        if key:
            self._select_key(key)

    def _select_key(self, key):
        for row in range(self.proxy.rowCount()):
            index = self.proxy.index(row, 0)
            source = self.proxy.mapToSource(index)
            data = self.model.row_at(source.row())
            if data and row_key(data) == key:
                self.table.selectRow(row)
                self.table.scrollTo(index)
                self.table.setCurrentIndex(index)
                return

    def _current_changed(self, current, _previous):
        row = self.proxy.row_for_source_index(current)
        self._selected_row = row
        self.state.selected_key = row_key(row) if row else None
        self.detail.set_row(row)
        self._update_actions()

    def _double_clicked(self, index):
        row = self.proxy.row_for_source_index(index)
        if row and status_of(row) in ("ELEGIR", "SUGERIDO", "REVISAR"):
            self.assign_selected()

    def _summary_selected(self, status):
        self.proxy.set_status_filter(None if status == "ALL" else status)

    def _search_changed(self, text):
        self.proxy.set_search(text)

    def _clear_filters(self):
        self.search.clear()
        self.summary.select_status("ALL")
        self.proxy.set_status_filter(None)

    # ------------------------------------------------------------------ assign
    def assign_selected(self):
        row = self._selected_row
        if not row or not self.state.result:
            return
        dialog = AssignDriverDialog(row, self.state.result, self.state.t, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if dialog.action == "clear":
            row["driver"] = row["license"] = row["vin"] = ""
            row["flag"] = "elegir"
        elif dialog.action == "assign" and dialog.selected:
            candidate = dialog.selected
            number = candidate["num"]
            info = ((self.state.result.get("drivers") or {}).get("table", {})
                    .get(number, {}))
            row["driver"] = number
            row["license"] = info.get("license", candidate.get("license", ""))
            row["vin"] = info.get("vin", candidate.get("vin", ""))
            row["flag"] = ""
        self.state.selected_key = row_key(row)
        self._render(preserve=True)

    def clear_selected(self):
        row = self._selected_row
        if not row:
            return
        row["driver"] = row["license"] = row["vin"] = ""
        row["flag"] = "elegir"
        self.state.selected_key = row_key(row)
        self._render(preserve=True)

    # ------------------------------------------------------------------ browse
    def _initial(self, value, fallback=True):
        if value and Path(value).exists():
            return value
        return str(Path.home()) if fallback else ""

    def browse_claim(self, _picker=None):
        path, _ = QFileDialog.getOpenFileName(
            self, "ClaimInformation", self._initial(self.state.claim_path), "Excel (*.xlsx)")
        if not path:
            return
        self.pick_claim.set_path(path)
        self.state.claim_path = path
        if not self.state.sources_folder.strip():
            folder = str(Path(path).parent)
            self.pick_folder.set_path(folder)
            self.state.sources_folder = folder

    def browse_folder(self, _picker=None):
        path = QFileDialog.getExistingDirectory(
            self, self.state.t("lbl_folder"), self._initial(self.state.sources_folder))
        if not path:
            return
        self.pick_folder.set_path(path)
        self.state.sources_folder = path
        if not self.state.days_root.strip():
            self.pick_days.set_path(path)
            self.state.days_root = path

    def browse_drivers(self, _picker=None):
        path, _ = QFileDialog.getOpenFileName(
            self, "Informacion de Drivers.xlsx", self._initial(self.state.drivers_path),
            "Excel (*.xlsx)")
        if path:
            self.pick_drivers.set_path(path)
            self.state.drivers_path = path

    def browse_driverlogs(self, _picker=None):
        path = QFileDialog.getExistingDirectory(
            self, self.state.t("lbl_driverlogs"), self._initial(self.state.driverlogs_folder))
        if path:
            self.pick_driverlogs.set_path(path)
            self.state.driverlogs_folder = path

    def browse_daysroot(self, _picker=None):
        path = QFileDialog.getExistingDirectory(
            self, self.state.t("lbl_daysroot"), self._initial(self.state.days_root))
        if path:
            self.pick_days.set_path(path)
            self.state.days_root = path

    # ------------------------------------------------------------------ exports
    def export_excel(self):
        if not self.state.result:
            return
        pending = pending_rows(self.state.result["claim"]["rows"])
        if pending and not messages.yes_no(
                self, self.state.t("pend_title"), self.state.t("pend_body", n=len(pending))):
            return
        default = default_export_name(self.state.result)
        path, _ = QFileDialog.getSaveFileName(
            self, self.state.t("btn_export"), str(default), "Excel (*.xlsx)")
        if not path:
            return
        try:
            info = write_output(self.state.result["claim"], path)
        except (ValueError, OSError) as exc:
            messages.error(self, self.state.t("st_error"), str(exc))
            return
        messages.info(self, self.state.t("exp_title"), self.state.t(
            "exp_body", path=path, rows=info["rows"], sheets=info["sheets"]))

    def save_csv(self):
        if not self.state.result:
            return
        default = default_csv_name(self.state.result)
        path, _ = QFileDialog.getSaveFileName(
            self, self.state.t("btn_csv"), str(default), "CSV (*.csv)")
        if not path:
            return
        try:
            ensure_not_source(path, self.state.result["claim_path"])
            write_report_csv(path, self.state.result)
        except (ValueError, OSError) as exc:
            messages.error(self, self.state.t("st_error"), str(exc))
            return
        messages.info(self, self.state.t("csv_title"), self.state.t("csv_body", path=path))

    def generate_driverlogs(self):
        if not self.state.result:
            return
        templates = self.state.driverlogs_folder.strip()
        if not templates or not Path(templates).is_dir():
            messages.error(self, self.state.t("err_title"), self.state.t("err_driverlogs"))
            return
        root = self.state.days_root.strip() or self.state.sources_folder.strip()
        if not root or not Path(root).is_dir():
            messages.error(self, self.state.t("err_title"), self.state.t("err_daysroot"))
            return
        try:
            result = generate_driverlogs(self.state.result["claim"]["rows"], templates, root)
        except Exception as exc:  # noqa: BLE001
            messages.error(self, self.state.t("st_error"), f"{type(exc).__name__}: {exc}")
            return
        self.state.result["driverlogs"] = result
        self.report.appendPlainText("\n\n" + driverlog_lines(result, self.state.lang))
        messages.info(self, self.state.t("dl_title"), self.state.t(
            "dl_body", n=len(result["created"]), root=root,
            skipped=len(result["skipped"]), errors=len(result["errors"])))

    def generate_pdfs(self):
        root = self.state.days_root.strip() or self.state.sources_folder.strip()
        if not root or not Path(root).is_dir():
            messages.error(self, self.state.t("err_title"), self.state.t("err_daysroot"))
            return
        try:
            result = process_days(root)
        except DriverPdfError as exc:
            messages.error(self, self.state.t("err_title"), str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            messages.error(self, self.state.t("err_title"), f"{type(exc).__name__}: {exc}")
            return
        self.report.appendPlainText("\n\n" + self.state.t(
            "pdf_report", converted=result["converted"], merged=result["merged"],
            pages=result["pages"], errors=len(result["errors"])))
        messages.info(self, self.state.t("pdf_title"), self.state.t(
            "pdf_body", converted=result["converted"], merged=result["merged"],
            pages=result["pages"], errors=len(result["errors"]), root=root))

    def generate_bulk(self):
        if not self.state.result:
            return
        root = self.state.days_root.strip() or self.state.sources_folder.strip()
        if not root or not Path(root).is_dir():
            messages.error(self, self.state.t("err_title"), self.state.t("err_daysroot"))
            return
        try:
            result = generate_bulks(self.state.result["claim"]["rows"], root)
        except Exception as exc:  # noqa: BLE001
            messages.error(self, self.state.t("st_error"), f"{type(exc).__name__}: {exc}")
            return
        self.state.result["bulk"] = result
        self.report.appendPlainText("\n\n" + bulk_lines(result, self.state.lang))
        messages.info(self, self.state.t("bulk_title"), self.state.t(
            "bulk_body", n=len(result["created"]), root=root,
            excluded=len(result.get("excluded", [])), errors=len(result.get("errors", []))))

    def show_help(self):
        HelpDialog(self.state.t("help_title"), self.state.t("help_body"), self).exec()

    def showEvent(self, event):
        super().showEvent(event)
        set_dark_title_bar(self, self.state.theme == "dark")

    # ------------------------------------------------------------------ close
    def closeEvent(self, event):
        if self._thread is not None and self._thread.isRunning():
            messages.info(self, self.state.t("busy_close_title"),
                          self.state.t("busy_close_body"))
            event.ignore()
            return
        event.accept()
