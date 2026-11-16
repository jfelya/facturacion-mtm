"""Filtering/sorting proxy for the claim table."""
from PySide6.QtCore import QSortFilterProxyModel, Qt

from ...status import status_of
from .roles import SORT_ROLE, STATUS_ROLE

# fields searched by a free-text term, and by `field:value` shortcuts
SEARCH_FIELDS = ("member", "member_raw", "trip", "driver", "license", "vin", "date", "county")
SHORTCUTS = {
    "member": ("member", "member_raw"),
    "name": ("member", "member_raw"),
    "trip": ("trip",),
    "driver": ("driver",),
    "date": ("date",),
    "license": ("license",),
    "lic": ("license",),
    "vin": ("vin",),
    "county": ("county",),
}


class ClaimFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._terms = []          # [(fields, text)] — every term must match
        self._statuses = set()
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def _invalidate(self):
        self.beginFilterChange()
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def set_search(self, text):
        self._terms = []
        for part in (text or "").split():
            key, sep, value = part.partition(":")
            if sep and key.casefold() in SHORTCUTS and value:
                self._terms.append((SHORTCUTS[key.casefold()], value.casefold()))
            else:
                self._terms.append((SEARCH_FIELDS, part.casefold()))
        self._invalidate()

    def set_statuses(self, statuses):
        self._statuses = set(statuses or ())
        self._invalidate()

    def set_status_filter(self, status):
        self.set_statuses({status} if status else set())

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        if model is None:
            return True
        row = model.row_at(source_row)
        if row is None:
            return False
        if self._statuses and status_of(row) not in self._statuses:
            return False
        for fields, term in self._terms:
            if not any(term in str(row.get(key) or "").casefold() for key in fields):
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
