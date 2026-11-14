"""Read-only table model over the engine's claim row dictionaries."""
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from ...status import status_of
from ...strings import STRINGS
from ..theme.tokens import STATUS_ORDER, STATUS_TINTS
from .roles import RAW_ROW_ROLE, SORT_ROLE, STATUS_ROLE

COLUMNS = [
    ("c_fila", "row", Qt.AlignmentFlag.AlignCenter),
    ("c_fecha", "date", Qt.AlignmentFlag.AlignLeft),
    ("c_miembro", "member", Qt.AlignmentFlag.AlignLeft),
    ("c_trip", "trip", Qt.AlignmentFlag.AlignLeft),
    ("c_driver", "driver", Qt.AlignmentFlag.AlignCenter),
    ("c_milage", "milage", Qt.AlignmentFlag.AlignRight),
    ("c_pu", "pu", Qt.AlignmentFlag.AlignCenter),
    ("c_dropoff", "dropoff", Qt.AlignmentFlag.AlignCenter),
    ("c_estado", "status", Qt.AlignmentFlag.AlignCenter),
]


def _miles(v):
    if v is None:
        return ""
    try:
        return f"{float(v):.2f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(v)


def _hhmm(v):
    return v.strftime("%H:%M") if hasattr(v, "strftime") else ""


class ClaimTableModel(QAbstractTableModel):
    def __init__(self, rows=None, lang="es", theme="dark", parent=None):
        super().__init__(parent)
        self._rows = list(rows or [])
        self._lang = lang
        self._theme = theme

    # ------------------------------------------------------------------ data
    @property
    def rows(self):
        return self._rows

    def row_at(self, row_index):
        if 0 <= row_index < len(self._rows):
            return self._rows[row_index]
        return None

    def set_rows(self, rows):
        self.beginResetModel()
        self._rows = list(rows or [])
        self.endResetModel()

    def set_language(self, lang):
        self._lang = lang
        if self._rows:
            self.headerDataChanged.emit(Qt.Orientation.Horizontal, 0, len(COLUMNS) - 1)

    def set_theme(self, theme):
        self._theme = theme
        if self._rows:
            top = self.index(0, 0)
            bottom = self.index(len(self._rows) - 1, len(COLUMNS) - 1)
            self.dataChanged.emit(top, bottom, [Qt.ItemDataRole.BackgroundRole])

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation != Qt.Orientation.Horizontal or role != Qt.ItemDataRole.DisplayRole:
            return None
        key = COLUMNS[section][0]
        return STRINGS.get(self._lang, STRINGS["es"]).get(key, key)

    def _status(self, row):
        return status_of(row)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._rows)):
            return None
        row = self._rows[index.row()]
        col = index.column()
        status = self._status(row)

        if role == Qt.ItemDataRole.DisplayRole:
            values = (
                row.get("row", ""),
                row.get("date_text", ""),
                row.get("member_raw") or row.get("member", ""),
                row.get("trip", ""),
                row.get("driver") or "",
                _miles(row.get("milage")),
                _hhmm(row.get("pu")),
                _hhmm(row.get("dropoff")),
                status,
            )
            return values[col]
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return COLUMNS[col][2] | Qt.AlignmentFlag.AlignVCenter
        if role == Qt.ItemDataRole.BackgroundRole:
            tint = STATUS_TINTS.get(self._theme, STATUS_TINTS["dark"]).get(status)
            return QColor(tint) if tint else None
        if role == Qt.ItemDataRole.ToolTipRole:
            return f"{row.get('member_raw') or row.get('member', '')}\n{row.get('trip', '')}\n{status}"
        if role == STATUS_ROLE:
            return status
        if role == RAW_ROW_ROLE:
            return row
        if role == SORT_ROLE:
            if col == 0:
                return int(row.get("row") or 0)
            if col == 4:
                try:
                    return (0, int(row.get("driver") or 0))
                except (TypeError, ValueError):
                    return (1, str(row.get("driver") or ""))
            if col == 5:
                return float(row.get("milage") or 0)
            if col in (6, 7):
                v = row.get("pu") if col == 6 else row.get("dropoff")
                return (v.hour * 60 + v.minute) if hasattr(v, "hour") else 10 ** 9
            if col == 8:
                return STATUS_ORDER.get(status, 99)
            return str(self.data(index, Qt.ItemDataRole.DisplayRole) or "").casefold()
        if role == Qt.ItemDataRole.UserRole:
            return row
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
