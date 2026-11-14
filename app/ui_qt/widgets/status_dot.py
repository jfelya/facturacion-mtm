"""Small painted status dot."""
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class StatusDot(QWidget):
    def __init__(self, size=9, parent=None):
        super().__init__(parent)
        self._size = size
        self._color = QColor("#9AA7B4")
        self.setFixedSize(QSize(size + 2, size + 2))

    def set_color(self, color):
        self._color = QColor(color)
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color)
        painter.drawEllipse(1, 1, self._size, self._size)
        painter.end()
