"""Paint the model's status tint on every column, then let the default delegate draw text."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QStyle, QStyledItemDelegate


class RowDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if not (option.state & QStyle.StateFlag.State_Selected):
            color = index.data(Qt.ItemDataRole.BackgroundRole)
            if color:
                painter.fillRect(option.rect, QColor(color))
        super().paint(painter, option, index)
