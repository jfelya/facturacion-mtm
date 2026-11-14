"""Label + path editor + browse button + hint."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


class PathPicker(QWidget):
    changed = Signal(str)

    def __init__(self, title="", hint="", browse_text="…", on_browse=None, parent=None):
        super().__init__(parent)
        self._on_browse = on_browse
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        self.title = QLabel(title)
        self.title.setObjectName("PickerTitle")
        layout.addWidget(self.title)
        row = QHBoxLayout()
        row.setSpacing(8)
        self.edit = QLineEdit()
        self.edit.textChanged.connect(self.changed.emit)
        row.addWidget(self.edit, 1)
        self.button = QPushButton(browse_text)
        self.button.setMinimumWidth(74)
        self.button.clicked.connect(self._browse)
        row.addWidget(self.button)
        layout.addLayout(row)
        self.hint = QLabel(hint)
        self.hint.setObjectName("Hint")
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)

    def _browse(self):
        if self._on_browse:
            self._on_browse(self)

    def path(self):
        return self.edit.text().strip()

    def set_path(self, value):
        self.edit.setText(value or "")

    def set_labels(self, title, hint, browse_text):
        self.title.setText(title)
        self.hint.setText(hint)
        self.button.setText(browse_text)
