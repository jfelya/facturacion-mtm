"""Clickable status-count chips (multi-select, with a 'to review' preset)."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

STATUSES = ["OK", "NOTA", "SUGERIDO", "BALANCEADO", "REVISAR",
            "ELEGIR", "NO FACTURAR", "FACTURADO", "SIN DATO"]
REVIEW_STATUSES = {"SUGERIDO", "REVISAR", "ELEGIR"}


class SummaryStrip(QWidget):
    statuses_selected = Signal(list)

    def __init__(self, all_text="ALL", review_text="Por revisar", parent=None):
        super().__init__(parent)
        self._all_text = all_text
        self._review_text = review_text
        self._active = set()
        self._buttons = {}
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.all_button = self._add_button("ALL")
        layout.addWidget(self.all_button)
        self.review_button = self._add_button("REVIEW")
        layout.addWidget(self.review_button)
        for status in STATUSES:
            button = self._add_button(status)
            layout.addWidget(button)
        layout.addStretch(1)
        self._refresh(emit=False)
        self.set_counts({})

    def _add_button(self, key):
        button = QPushButton()
        button.setProperty("chip", True)
        button.clicked.connect(lambda: self._toggle(key))
        self._buttons[key] = button
        return button

    def _toggle(self, key):
        if key == "ALL":
            self._active = set()
        elif key == "REVIEW":
            self._active = set() if self._active == REVIEW_STATUSES else set(REVIEW_STATUSES)
        elif key in self._active:
            self._active.discard(key)
        else:
            self._active.add(key)
        self._refresh()

    def _refresh(self, emit=True):
        for key, button in self._buttons.items():
            active = (key == "ALL" and not self._active) or (key == "REVIEW" and self._active == REVIEW_STATUSES) \
                or (key in STATUSES and key in self._active)
            button.setProperty("active", active)
            button.style().unpolish(button)
            button.style().polish(button)
        if emit:
            self.statuses_selected.emit(sorted(self._active))

    def set_counts(self, counts):
        self._buttons["ALL"].setText(f"{self._all_text} {sum(counts.values())}")
        self._buttons["REVIEW"].setText(
            f"{self._review_text} {sum(counts.get(s, 0) for s in REVIEW_STATUSES)}")
        for status in STATUSES:
            self._buttons[status].setText(f"{status} {counts.get(status, 0)}")
        self._refresh(emit=False)

    def set_all_text(self, text):
        self._all_text = text
        self._buttons["ALL"].setText(text)

    def set_review_text(self, text):
        self._review_text = text
        self._buttons["REVIEW"].setText(text)

    def select_status(self, status):
        self._active = set() if not status or status == "ALL" else {status}
        self._refresh()

    def select_statuses(self, statuses):
        self._active = set(statuses or ())
        self._refresh()
