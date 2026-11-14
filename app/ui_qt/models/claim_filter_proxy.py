"""Filtering/sorting proxy for the claim table."""
from PySide6.QtCore import QSortFilterProxyModel, Qt

from ...status import status_of
from .roles import SORT_ROLE, STATUS_ROLE


class ClaimFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._search = ""
        self._status = None
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def _invalidate(self):
        self.beginFilterChange()
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def set_search(self, text):
        self._search = (text or "").strip().casefold()
        self._invalidate()

    def set_status_filter(self, status):
        self._status = status or None
        self._invalidate()

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        if model is None:
            return True
        row = model.row_at(source_row)
        if row is None:
            return False
        if self._status and status_of(row) != self._status:
            return False
        if self._search:
            haystack = " ".join(
                str(row.get(k) or "") for k in ("member", "member_raw", "trip", "driver")
            ).casefold()
            if self._search not in haystack:
                return False
        return True

    def lessThan(self, left, right):
        model = self.sourceModel()
        lv = model.data(left, SORT_ROLE)
        rv = model.data(right, SORT_ROLE)
        try:
            return lv < rv
        except TypeError:
            return str(lv) < str(rv)

    def status_counts(self):
        counts = {}
        model = self.sourceModel()
        if model is None:
            return counts
        for row in model.rows:
            status = status_of(row)
            counts[status] = counts.get(status, 0) + 1
        return counts

    def row_for_source_index(self, proxy_index):
        if not proxy_index.isValid():
            return None
        source = self.mapToSource(proxy_index)
        model = self.sourceModel()
        return model.row_at(source.row()) if model else None
