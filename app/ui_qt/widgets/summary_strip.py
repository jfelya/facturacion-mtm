"""Clickable status-count chips."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

STATUSES = ["OK", "NOTA", "SUGERIDO", "BALANCEADO", "REVISAR",
            "ELEGIR", "NO FACTURAR", "FACTURADO", "SIN DATO"]


class SummaryStrip(QWidget):
    status_selected = Signal(str)

    def __init__(self, all_text="ALL", parent=None):
        super().__init__(parent)
        self._all_text = all_text
        self._buttons = {}
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.all_button = self._add_button("ALL", "ALL")
        layout.addWidget(self.all_button)
        for status in STATUSES:
            button = self._add_button(status, status)
            layout.addWidget(button)
        layout.addStretch(1)

    def _add_button(self, key, status):
        button = QPushButton()
        button.setProperty("chip", True)
        button.setProperty("active", key == "ALL")
        button.clicked.connect(lambda: self._select(status))
        self._buttons[key] = button
        return button

    def _select(self, status):
        for key, button in self._buttons.items():
            button.setProperty("active", key == ("ALL" if status == "ALL" else status))
            button.style().unpolish(button)
            button.style().polish(button)
        self.status_selected.emit(status)

    def set_counts(self, counts):
        self._buttons["ALL"].setText(f"{self._all_text} {sum(counts.values())}")
        for status in STATUSES:
            self._buttons[status].setText(f"{status} {counts.get(status, 0)}")
        self._buttons["ALL"].style().unpolish(self._buttons["ALL"])
        self._buttons["ALL"].style().polish(self._buttons["ALL"])

    def set_all_text(self, text):
        self._all_text = text
        self._buttons["ALL"].setText(text)

    def select_status(self, status):
        self._select(status)

