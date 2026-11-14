"""Selected-row detail strip and assignment actions."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from ...status import status_of


class DetailDrawer(QFrame):
    assign_requested = Signal()
    clear_requested = Signal()

    def __init__(self, t, parent=None):
        super().__init__(parent)
        self.setObjectName("DetailDrawer")
        self.setFixedHeight(128)
        self._t = t
        self._row = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(4)
        self.title = QLabel(t("detail_select"))
        self.title.setObjectName("SectionTitle")
        left.addWidget(self.title)
        self.sub = QLabel("")
        self.sub.setObjectName("FieldValue")
        left.addWidget(self.sub)
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(2)
        self.values = {}
        self.labels = {}
        for i, key in enumerate(("c_driver", "c_license", "c_vin", "c_milage", "c_cost", "c_estado")):
            label = QLabel(t(key))
            label.setObjectName("FieldLabel")
            value = QLabel("—")
            value.setObjectName("FieldValue")
            grid.addWidget(label, 0 if i < 3 else 1, (i % 3) * 2)
            grid.addWidget(value, 0 if i < 3 else 1, (i % 3) * 2 + 1)
            self.values[key] = value
            self.labels[key] = label
        left.addLayout(grid)
        layout.addLayout(left, 1)

        actions = QVBoxLayout()
        actions.setSpacing(6)
        self.btn_assign = QPushButton(t("btn_assign"))
        self.btn_assign.setProperty("role", "primary")
        self.btn_assign.clicked.connect(self.assign_requested)
        self.btn_clear = QPushButton(t("btn_clear"))
        self.btn_clear.clicked.connect(self.clear_requested)
        actions.addWidget(self.btn_assign)
        actions.addWidget(self.btn_clear)
        actions.addStretch(1)
        layout.addLayout(actions)

    def set_labels(self, t):
        self._t = t
        self.title.setText(t("detail_select") if self._row is None else t("detail_title"))
        self.btn_assign.setText(t("btn_assign"))
        self.btn_clear.setText(t("btn_clear"))
        for key, label in self.labels.items():
            label.setText(t(key))
        if self._row is not None:
            self.set_row(self._row)

    def set_row(self, row):
        self._row = row
        if row is None:
            self.title.setText(self._t("detail_select"))
            self.sub.setText("")
            for value in self.values.values():
                value.setText("—")
            self.btn_assign.setEnabled(False)
            self.btn_clear.setEnabled(False)
            return
        self.title.setText(self._t("detail_title"))
        self.sub.setText(
            f"{row.get('member_raw') or row.get('member', '')} · "
            f"{row.get('date_text', '')} · {row.get('trip', '')}"
        )
        status = status_of(row)
        values = {
            "c_driver": row.get("driver") or "—",
            "c_license": row.get("license") or "—",
            "c_vin": row.get("vin") or "—",
            "c_milage": "" if row.get("milage") is None else row.get("milage"),
            "c_cost": row.get("cost") or "—",
            "c_estado": status,
        }
        for key, value in values.items():
            self.values[key].setText(str(value))
        self.btn_assign.setEnabled(status in ("ELEGIR", "SUGERIDO", "REVISAR"))
        self.btn_clear.setEnabled(bool(row.get("driver")))
