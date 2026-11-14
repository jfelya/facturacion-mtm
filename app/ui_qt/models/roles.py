"""Item roles shared by the Qt table model, proxy and delegate."""
from PySide6.QtCore import Qt

STATUS_ROLE = Qt.ItemDataRole.UserRole + 1
SORT_ROLE = Qt.ItemDataRole.UserRole + 2
RAW_ROW_ROLE = Qt.ItemDataRole.UserRole + 3
