"""Paint the status column as a tinted pill."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QStyle, QStyledItemDelegate

from ..theme.tokens import THEMES
from ..models.roles import STATUS_ROLE


class StatusDelegate(QStyledItemDelegate):
    def __init__(self, theme="dark", parent=None):
        super().__init__(parent)
        self._theme = theme

    def set_theme(self, theme):
        self._theme = theme

    def paint(self, painter, option, index):
        status = index.data(STATUS_ROLE) or ""
        tint = THEMES.get(self._theme, THEMES["dark"])["status"].get(status)
        if not tint:
            return super().paint(painter, option, index)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        if selected:
            painter.fillRect(option.rect, option.palette.highlight())
        elif option.backgroundBrush.style() != Qt.BrushStyle.NoBrush:
            painter.fillRect(option.rect, option.backgroundBrush)

        rect = QRectF(option.rect).adjusted(10, 5, -10, -5)
        painter.setBrush(QColor(tint))
        painter.setPen(QPen(QColor(THEMES[self._theme]["border"]), 1))
        painter.drawRoundedRect(rect, 9, 9)

        font = option.font
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(THEMES[self._theme]["text"]))
        text = QFontMetrics(font).elidedText(status, Qt.TextElideMode.ElideRight, int(rect.width()) - 8)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()
