import copy
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.pipeline import run_job
from app.ui_qt.dialogs.assign_driver import AssignDriverDialog
from app.ui_qt.main_window import MainWindow
from tests.fixtures import make_claim, make_docx_template, make_drivers, make_resumen, make_trips


def _batch(root):
    sources = root / "sources"
    sources.mkdir()
    claim = make_claim(
        root / "claim.xlsx",
        [{"Claim Status": "Open", "Trip Number": "T0A", "Appt. Date": "10/05/2026",
          "Member Info": "TEST MEMBER", "Driver": "", "VIN": "", "Provider Cost": "$10.00",
          "Name (First and Last)": "TEST MEMBER"}],
    )
    make_resumen(
        sources / "RESUMEN.xlsx",
        [{"DATE": "10/05/2026", "LOS": "AMB", "TRIP ID": "", "PAYER": "MTM",
          "NAME": "TEST", "LAST NAME": "MEMBER", "DRIVER": 200, "MILES": 5.0, "NOTES": ""}],
    )
    make_trips(
        sources / "10-05.xlsx",
        [{"Trip Number": "T0A", "Appointment Date": "10/05/2026", "Time": "10:00 AM",
          "Trip Mileage": 5.0, "Trip Cost": 10.0, "Member's First Name": "TEST",
          "Member's Last Name": "MEMBER", "Pickup City": "OCALA"}],
    )
    make_drivers(
        sources / "Informacion de Drivers.xlsx",
        [{"DRIVER": "TEST DRIVER", "COUNTY": "MARION", "LICENSE NUMBER": "L",
          "VIN Number": "V", "CURRENT VEHICLE": "", "VEHICLE PLATE": "", "NUMERO": 200}],
    )
    return claim, sources


class UiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.win = MainWindow(self.app)
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        claim, sources = _batch(self.root)
        self.result = run_job(claim, sources)
        self.assertNotIn("error", self.result)
        self.win.state.result = self.result
        self.win._render()
        self.app.processEvents()

    def tearDown(self):
        self.win.close()
        self.win.deleteLater()
        self.app.processEvents()
        self.tmp.cleanup()

    def test_table_and_empty_state(self):
        self.assertEqual(self.win.model.columnCount(), 9)
        self.assertEqual(self.win.proxy.rowCount(), 1)
        self.assertEqual(self.win.preview_stack.currentIndex(), 1)
        self.assertEqual(self.win.summary._buttons["OK"].text(), "OK 1")

    def test_selection_updates_detail(self):
        self.win.table.selectRow(0)
        self.app.processEvents()
        self.assertEqual(self.win.detail.values["c_driver"].text(), "200")
        self.assertEqual(self.win.detail.values["c_license"].text(), "L")

    def test_search_and_status_filter(self):
        self.win.search.setText("TEST")
        self.app.processEvents()
        self.assertEqual(self.win.proxy.rowCount(), 1)
        self.win.search.setText("no-match")
        self.app.processEvents()
        self.assertEqual(self.win.proxy.rowCount(), 0)
        self.win.search.clear()
        self.win.summary.select_status("OK")
        self.app.processEvents()
        self.assertEqual(self.win.proxy.rowCount(), 1)
        self.win.summary.select_status("SIN DATO")
        self.app.processEvents()
        self.assertEqual(self.win.proxy.rowCount(), 0)

    def test_theme_and_language_preserve_state(self):
        self.win.state.claim_path = "C:/keep.xlsx"
        self.win.toggle_theme()
        self.assertEqual(self.win.state.theme, "light")
        self.win.toggle_lang()
        self.assertEqual(self.win.state.lang, "en")
        self.assertEqual(self.win.state.claim_path, "C:/keep.xlsx")
        self.assertEqual(self.win.tabs.tabText(0), "Preview")

    def test_assign_dialog_candidate(self):
        row = copy.deepcopy(self.result["claim"]["rows"][0])
        row["driver"] = row["license"] = row["vin"] = ""
        row["flag"] = "elegir"
        row["county"] = "MARION"
        result = copy.deepcopy(self.result)
        result["report"]["driver_candidates"] = {
            (row["date"], "MARION"): [{
                "num": "200", "name": "TEST DRIVER", "count": 0,
                "license": "L", "vin": "V", "county": "MARION",
            }]
        }
        dialog = AssignDriverDialog(row, result, self.win.state.t, self.win)
        self.assertEqual(dialog.table.rowCount(), 1)
        dialog.table.selectRow(0)
        dialog._accept()
        self.assertEqual(dialog.action, "assign")
        self.assertEqual(dialog.selected["num"], "200")
        dialog.deleteLater()

    def test_window_has_app_icon(self):
        self.assertFalse(self.win.windowIcon().isNull())

    def test_generate_pdfs_reports_merge(self):
        days = self.root / "days"
        days.mkdir()
        self.win.state.days_root = str(days)
        fake = {"converted": 2, "skipped": 0, "merged": 1, "pages": 2,
                "merged_files": [], "errors": []}
        with patch("app.ui_qt.main_window.process_days", return_value=fake), \
                patch("app.ui_qt.main_window.messages.info") as info:
            self.win.generate_pdfs()
        self.assertTrue(info.called)
        self.assertIn("PDFs generados", info.call_args.args[1])

    def test_output_actions_write_engine_files(self):
        days = self.root / "days"
        templates = self.root / "templates"
        days.mkdir()
        make_docx_template(templates / "200 TEST DRIVERLOG VACIO.docx")
        self.win.state.days_root = str(days)
        self.win.state.driverlogs_folder = str(templates)
        out = self.root / "out.xlsx"
        csv = self.root / "out.csv"
        with patch("app.ui_qt.main_window.QFileDialog.getSaveFileName",
                   side_effect=[(str(out), ""), (str(csv), "")]), \
                patch("app.ui_qt.main_window.messages.info"):
            self.win.export_excel()
            self.win.save_csv()
            self.win.generate_driverlogs()
            self.win.generate_bulk()
        self.assertTrue(out.exists())
        self.assertTrue(csv.exists())
        self.assertTrue((days / "10-05" / "Docs" / "10-05 200.docx").exists())
        self.assertTrue((days / "10-05" / "BULK UPLOAD 10-05-2026.xlsx").exists())

