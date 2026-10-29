import tempfile
import unittest
from pathlib import Path

from app.filler import _allowed_drivers, fill_claim
from app.pipeline import run_job
from tests.fixtures import make_claim, make_drivers, make_resumen, make_trips


def _claim():
    return {
        "path": "synthetic.xlsx",
        "rows": [{
            "row": 2,
            "trip": "T0A",
            "leg": "A",
            "date": "2026-10-05",
            "member": "TEST MEMBER",
            "driver": "",
            "milage": None,
            "pu": None,
            "license": "",
            "vin": "",
            "cost": "$10.00",
            "flag": "",
        }],
    }


def _resumen():
    return {
        ("2026-10-05", "TEST MEMBER"): [{
            "date": "2026-10-05",
            "name": "TEST MEMBER",
            "driver": "200",
            "miles": 5.0,
            "trip_id": "",
            "payer": "MTM",
            "note": "",
            "time": None,
            "src": "synthetic.xlsx",
        }],
    }


class AllowedTests(unittest.TestCase):
    def test_empty_allowed_helper_is_empty(self):
        drivers = {"table": {"200": {}}, "allowed": set()}
        self.assertEqual(_allowed_drivers(drivers), set())

    def test_empty_allowed_does_not_accept_summary_driver(self):
        claim = _claim()
        drivers = {
            "table": {"200": {"license": "L", "vin": "V", "name": "D", "county": "MARION"}},
            "allowed": set(),
        }
        fill_claim(claim, _resumen(), {}, drivers, suggest_driver=True)
        row = claim["rows"][0]
        self.assertEqual(row["driver"], "")
        self.assertIn(row["flag"], ("revisar", "elegir"))

    def test_empty_driverlogs_folder_rejects_every_driver(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = root / "sources"
            sources.mkdir()
            templates = root / "templates"
            templates.mkdir()
            claim = make_claim(
                root / "claim.xlsx",
                [{"Claim Status": "Open", "Trip Number": "T0A",
                  "Appt. Date": "10/05/2026", "Member Info": "TEST MEMBER",
                  "Driver": "", "VIN": "", "Provider Cost": "$10.00",
                  "Name (First and Last)": "TEST MEMBER"}],
            )
            make_resumen(
                sources / "RESUMEN.xlsx",
                [{"DATE": "10/05/2026", "LOS": "AMB", "TRIP ID": "", "PAYER": "MTM",
                  "NAME": "TEST", "LAST NAME": "MEMBER", "DRIVER": 200,
                  "MILES": 5.0, "NOTES": ""}],
            )
            make_trips(
                sources / "10-05.xlsx",
                [{"Trip Number": "T0A", "Appointment Date": "10/05/2026",
                  "Time": "10:00 AM", "Trip Mileage": 5.0, "Trip Cost": 10.00,
                  "Member's First Name": "TEST", "Member's Last Name": "MEMBER",
                  "Pickup City": "OCALA"}],
            )
            make_drivers(
                sources / "Informacion de Drivers.xlsx",
                [{"DRIVER": "TEST DRIVER", "COUNTY": "MARION", "LICENSE NUMBER": "L",
                  "VIN Number": "V", "CURRENT VEHICLE": "", "VEHICLE PLATE": "",
                  "NUMERO": 200}],
            )
            res = run_job(claim, sources, driverlogs_folder=templates)
            row = res["claim"]["rows"][0]
        self.assertEqual(row["driver"], "")
        self.assertIn(row["flag"], ("revisar", "elegir"))


if __name__ == "__main__":
    unittest.main()
