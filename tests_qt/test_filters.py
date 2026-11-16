import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui_qt.models.claim_filter_proxy import ClaimFilterProxy
from app.ui_qt.models.claim_table_model import ClaimTableModel
from app.ui_qt.widgets.summary_strip import REVIEW_STATUSES, SummaryStrip


def _row(member, trip, date, driver="200", milage=5.0, flag="",
         license="L200", vin="V200", county="MARION"):
    return {"member": member, "member_raw": member, "trip": trip, "date": date,
            "driver": driver, "milage": milage, "flag": flag, "license": license,
            "vin": vin, "county": county}


ROWS = [
    _row("ANA LOPEZ", "T001", "2026-10-05"),
    _row("LUIS DIAZ", "T002", "2026-10-05", driver="220", flag="nota"),
    _row("EVA RUIZ", "T003", "2026-10-06", driver="309", flag="sugerido",
         license="B221-544-80-591-0", vin="4T1G11AKXLU985689"),
    _row("MARCO POLO", "T004", "2026-10-09", driver="", milage=5.0, flag="revisar",
         license="", vin="", county="VOLUSIA"),
    _row("SARA GIL", "T005", "2026-10-09", driver="", milage=5.0, flag="",
         license="", vin="", county="VOLUSIA"),
    _row("NO BILL", "T006", "2026-10-12", driver="", milage=None, flag="nofacturar",
         license="", vin="", county="MARION"),
]


class FilterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.model = ClaimTableModel(ROWS)
        self.proxy = ClaimFilterProxy()
        self.proxy.setSourceModel(self.model)

    def test_multi_status_filter(self):
        self.proxy.set_statuses({"OK", "NOTA"})
        self.assertEqual(self.proxy.rowCount(), 2)

    def test_review_preset_groups_three_statuses(self):
        self.proxy.set_statuses({"SUGERIDO", "REVISAR", "ELEGIR"})
        self.assertEqual(self.proxy.rowCount(), 3)

    def _visible_trips(self):
        trips = []
        for i in range(self.proxy.rowCount()):
            source = self.proxy.mapToSource(self.proxy.index(i, 0))
            trips.append(self.model.row_at(source.row())["trip"])
        return trips

    def test_search_matches_license_vin_date_and_county(self):
        for text, expected in (("B221", "T003"), ("4T1G11", "T003"),
                               ("10-09", "T004"), ("VOLUSIA", "T004")):
            self.proxy.set_search(text)
            self.assertIn(expected, self._visible_trips(), text)

    def test_search_field_shortcuts(self):
        for text, expected in (("driver:309", 1), ("trip:T003", 1), ("date:10-09", 2)):
            self.proxy.set_search(text)
            self.assertEqual(self.proxy.rowCount(), expected, text)

    def test_blank_status_means_all(self):
        self.proxy.set_statuses({"OK"})
        self.proxy.set_statuses(set())
        self.assertEqual(self.proxy.rowCount(), len(ROWS))


class SummaryStripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.strip = SummaryStrip()
        self.emitted = []
        self.strip.statuses_selected.connect(self.emitted.append)

    def test_review_chip_selects_three_statuses(self):
        self.strip._buttons["REVIEW"].click()
        self.assertEqual(set(self.emitted[-1]), REVIEW_STATUSES)

    def test_status_chips_combine(self):
        self.strip._buttons["OK"].click()
        self.strip._buttons["NOTA"].click()
        self.assertEqual(set(self.emitted[-1]), {"OK", "NOTA"})
        self.strip._buttons["OK"].click()
        self.assertEqual(set(self.emitted[-1]), {"NOTA"})

    def test_all_clears_selection(self):
        self.strip._buttons["OK"].click()
        self.strip._buttons["ALL"].click()
        self.assertEqual(self.emitted[-1], [])

    def test_review_count_sums_its_statuses(self):
        counts = {"OK": 4, "SUGERIDO": 2, "REVISAR": 3, "ELEGIR": 1}
        self.strip.set_counts(counts)
        text = self.strip._buttons["REVIEW"].text()
        self.assertIn("6", text)


if __name__ == "__main__":
    unittest.main()
