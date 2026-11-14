"""Modal driver assignment dialog."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class AssignDriverDialog(QDialog):
    """Pick a driver from the engine's same-day/same-county candidate list."""

    def __init__(self, row, result, t, parent=None):
        super().__init__(parent)
        self.row = row
        self.result = result
        self.t = t
        self.action = None
        self.selected = None
        self._candidates = list(
            (result["report"].get("driver_candidates") or {}).get(
                (row.get("date"), row.get("county") or ""), []
            )
        )
        self.setWindowTitle(t("assign_title"))
        self.resize(760, 520)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self._build()
        self._populate()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        self.heading = QLabel()
        self.heading.setObjectName("PageTitle")
        layout.addWidget(self.heading)
        self.current = QLabel()
        self.current.setObjectName("Hint")
        layout.addWidget(self.current)
        self.hint = QLabel(self.t("assign_hint"))
        self.hint.setObjectName("Hint")
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)

        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(self.t("assign_search"))
        self.search.textChanged.connect(self._populate)
        filters.addWidget(self.search, 1)
        self.only_free = QCheckBox(self.t("assign_only_free"))
        self.only_free.toggled.connect(self._populate)
        filters.addWidget(self.only_free)
        layout.addLayout(filters)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            self.t("c_driver"), self.t("c_name"), self.t("c_trips"),
            self.t("c_license"), self.t("c_vin"), self.t("c_county"),
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(lambda _idx: self._accept())
        self.table.itemSelectionChanged.connect(self._selection_changed)
        layout.addWidget(self.table, 1)

        buttons = QHBoxLayout()
        self.btn_clear = QPushButton(self.t("btn_clear"))
        self.btn_clear.clicked.connect(self._clear)
        self.btn_cancel = QPushButton(self.t("btn_cancel"))
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_assign = QPushButton(self.t("btn_assign"))
        self.btn_assign.setProperty("role", "primary")
        self.btn_assign.setEnabled(False)
        self.btn_assign.setDefault(True)
        self.btn_assign.clicked.connect(self._accept)
        buttons.addWidget(self.btn_clear)
        buttons.addStretch(1)
        buttons.addWidget(self.btn_cancel)
        buttons.addWidget(self.btn_assign)
        layout.addLayout(buttons)

    def _populate(self):
        text = self.search.text().strip().casefold()
        only_free = self.only_free.isChecked()
        self.table.setRowCount(0)
        for candidate in self._candidates:
            haystack = f"{candidate.get('num', '')} {candidate.get('name', '')}".casefold()
            if text and text not in haystack:
                continue
            if only_free and candidate.get("count", 0) != 0:
                continue
            r = self.table.rowCount()
            self.table.insertRow(r)
            info = ((self.result.get("drivers") or {}).get("table", {})
                    .get(candidate.get("num"), {}))
            values = [
                candidate.get("num", ""),
                candidate.get("name", ""),
                candidate.get("count", 0),
                candidate.get("license") or info.get("license", ""),
                candidate.get("vin") or info.get("vin", ""),
                candidate.get("county") or info.get("county", ""),
            ]
            for c, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.ItemDataRole.UserRole, candidate)
                self.table.setItem(r, c, item)
        self.heading.setText(
            f"{self.row.get('member_raw') or self.row.get('member', '')} · "
            f"{self.row.get('date_text', '')} · {self.row.get('trip', '')}"
        )
        current = self.row.get("driver") or "—"
        self.current.setText(f"{self.t('assign_current')}: {current}")
        self.btn_assign.setEnabled(False)

    def _selection_changed(self):
        has = bool(self.table.selectionModel().selectedRows())
        self.btn_assign.setEnabled(has)

    def _selected_candidate(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.table.item(rows[0].row(), 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _accept(self):
        candidate = self._selected_candidate()
        if not candidate:
            return
        self.selected = candidate
        self.action = "assign"
        self.accept()

    def _clear(self):
        self.action = "clear"
        self.accept()
