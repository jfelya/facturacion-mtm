import tempfile
import unittest
from pathlib import Path

from app.common import note_kind
from app.filler import fill_claim
from app.parsers import parse_resumen
from app.pipeline import build_resumen_index
from tests.fixtures import make_resumen


def _claim():
    return {
        "path": "synthetic.xlsx",
        "rows": [
            {"row": 2, "trip": "B0A", "leg": "A", "date": "2026-10-05",
             "member": "BILLED MEMBER", "driver": "", "milage": None, "pu": None,
             "license": "", "vin": "", "cost": "$10.00", "flag": ""},
            {"row": 3, "trip": "M0A", "leg": "A", "date": "2026-10-05",
             "member": "MANUAL MEMBER", "driver": "", "milage": None, "pu": None,
             "license": "", "vin": "", "cost": "$11.00", "flag": ""},
        ],
    }


def _resumen_entry(name, note, driver, miles):
    return {"date": "2026-10-05", "name": name, "driver": driver, "miles": miles,
            "trip_id": "", "payer": "MTM", "note": note, "time": None, "src": "x.xlsx"}


def _drivers():
    table = {
        "200": {"license": "L200", "vin": "V200", "name": "DRIVER 200", "county": "MARION"},
        "309": {"license": "L309", "vin": "V309", "name": "DRIVER 309", "county": "MARION"},
    }
    return {"table": table, "allowed": set(table)}


class NoteKindTests(unittest.TestCase):
    def test_billed(self):
        self.assertEqual(note_kind("Facturado."), "billed")
        self.assertEqual(note_kind("Facturado manualmente. Auto 20, driver Dixon."), "billed")
        self.assertEqual(note_kind("Ya facturado."), "billed")

    def test_actionable(self):
        self.assertEqual(note_kind("Facturar manualmente. Driver Marielkis, auto 309."), "actionable")
        self.assertEqual(note_kind("Facturación manual. Driver X, auto 309."), "actionable")

    def test_info_and_empty(self):
        self.assertEqual(note_kind("Facturación manual."), "info")
        self.assertEqual(note_kind(""), "")


class NoteFillerTests(unittest.TestCase):
    def test_billed_row_is_flagged_and_manual_row_stays_billable(self):
        claim = _claim()
        resumen_index = {
            ("2026-10-05", "BILLED MEMBER"): [
                _resumen_entry("BILLED MEMBER", "Facturado.", "200", 5.0)
            ],
            ("2026-10-05", "MANUAL MEMBER"): [
                _resumen_entry("MANUAL MEMBER",
                               "Facturar manualmente. Driver Marielkis, auto 309.",
                               "200", 6.0)
            ],
        }
        report = fill_claim(claim, resumen_index, {}, _drivers(), suggest_driver=True)
        billed, manual = claim["rows"]

        self.assertEqual(billed["driver"], "200")
        self.assertEqual(billed["flag"], "facturado")
        self.assertEqual(report["stats"]["already_billed"], 1)
        self.assertEqual(len(report["already_billed"]), 1)
        self.assertNotIn(billed["trip"],
                         [x["trip"] for x in report["needs_driver"]])

        self.assertEqual(manual["driver"], "309")
        self.assertEqual(manual["flag"], "nota")
        self.assertNotEqual(manual["flag"], "facturado")

    def test_resumen_entry_has_note_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = make_resumen(
                Path(tmp) / "RESUMEN.xlsx",
                [{"DATE": "10/05/2026", "LOS": "AMB", "TRIP ID": "", "PAYER": "MTM",
                  "NAME": "BILLED", "LAST NAME": "MEMBER", "DRIVER": 200,
                  "MILES": 5.0, "NOTES": "Facturado."}],
            )
            parsed = parse_resumen(path)
        self.assertEqual(parsed[0]["note_kind"], "billed")

    def test_billed_rows_do_not_count_as_workload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = make_resumen(
                Path(tmp) / "RESUMEN.xlsx",
                [
                    {"DATE": "10/05/2026", "LOS": "AMB", "TRIP ID": "", "PAYER": "MTM",
                     "NAME": "BILLED", "LAST NAME": "MEMBER", "DRIVER": 200,
                     "MILES": 5.0, "NOTES": "Facturado."},
                    {"DATE": "10/05/2026", "LOS": "AMB", "TRIP ID": "", "PAYER": "MTM",
                     "NAME": "NORMAL", "LAST NAME": "MEMBER", "DRIVER": 220,
                     "MILES": 6.0, "NOTES": ""},
                ],
            )
            usage, warnings = {}, []
            build_resumen_index([path], warnings, usage)
        self.assertEqual(usage["2026-10-05"]["count"].get("200", 0), 0)
        self.assertEqual(usage["2026-10-05"]["count"].get("220", 0), 1)


if __name__ == "__main__":
    unittest.main()
