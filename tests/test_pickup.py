import tempfile
import unittest
from datetime import time as dtime
from pathlib import Path

from app.pipeline import run_job
from tests.fixtures import make_claim, make_drivers, make_resumen, make_trips


def _mins(t):
    return t.hour * 60 + t.minute


def _normal_row(tmp):
    root = Path(tmp)
    sources = root / "sources"
    sources.mkdir()
    claim = make_claim(
        root / "claim.xlsx",
        [{"Claim Status": "Open", "Trip Number": "M4F32EG2N0A",
          "Appt. Date": "10/05/2026", "Member Info": "LISA HALSEY",
          "Driver": "", "VIN": "", "Provider Cost": "$15.00",
          "Name (First and Last)": "LISA HALSEY"}],
    )
    make_resumen(
        sources / "RESUMEN.xlsx",
        [{"DATE": "10/05/2026", "LOS": "AMB", "TRIP ID": "", "PAYER": "MTM",
          "NAME": "LISA", "LAST NAME": "HALSEY", "DRIVER": 200,
          "MILES": 5.67, "NOTES": ""}],
    )
    make_trips(
        sources / "10-05.xlsx",
        [{"Trip Number": "M4F32EG2N0A", "Appointment Date": "10/05/2026",
          "Time": "10:00 AM", "Trip Mileage": 5.67, "Trip Cost": 15.00,
          "Member's First Name": "LISA", "Member's Last Name": "HALSEY",
          "Pickup City": "OCALA"}],
    )
    make_drivers(
        sources / "Informacion de Drivers.xlsx",
        [{"DRIVER": "LISA DRIVER", "COUNTY": "MARION", "LICENSE NUMBER": "L1",
          "VIN Number": "V1", "CURRENT VEHICLE": "", "VEHICLE PLATE": "",
          "NUMERO": 200}],
    )
    res = run_job(claim, sources)
    return res["claim"]["rows"][0]


class PickupTimingTests(unittest.TestCase):
    def test_normal_trip_keeps_current_dropoff_and_pickup(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = _normal_row(tmp)
        self.assertEqual(row["pu_appt"], dtime(10, 0))
        self.assertEqual(row["dropoff"], dtime(9, 56))
        self.assertEqual(row["pu"], dtime(9, 34))
        self.assertLess(row["pu"], row["dropoff"])
        self.assertLess(row["dropoff"], row["pu_appt"])

    def test_normal_trip_dropoff_is_one_to_five_minutes_early(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = _normal_row(tmp)
        gap = _mins(row["pu_appt"]) - _mins(row["dropoff"])
        self.assertTrue(0 < gap <= 5, gap)

    def test_will_call_pickup_is_one_to_three_minutes_after_the_call_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = root / "sources"
            sources.mkdir()
            claim = make_claim(
                root / "claim.xlsx",
                [{"Claim Status": "Open", "Trip Number": "W0B",
                  "Appt. Date": "10/05/2026", "Member Info": "WC MEMBER",
                  "Driver": "", "VIN": "", "Provider Cost": "$15.00",
                  "Name (First and Last)": "WC MEMBER"}],
            )
            make_resumen(
                sources / "RESUMEN.xlsx",
                [{"DATE": "10/05/2026", "LOS": "AMB", "TRIP ID": "", "PAYER": "MTM",
                  "NAME": "WC", "LAST NAME": "MEMBER", "DRIVER": 200,
                  "MILES": 7.0, "NOTES": ""}],
            )
            make_trips(
                sources / "10-05.xlsx",
                [
                    {"Trip Number": "W0A", "Appointment Date": "10/05/2026",
                     "Time": "3:00 PM", "Trip Mileage": 7.0, "Trip Cost": 15.00,
                     "Member's First Name": "WC", "Member's Last Name": "MEMBER",
                     "Pickup City": "OCALA"},
                    {"Trip Number": "W0B", "Appointment Date": "10/05/2026",
                     "Time": "Will Call", "Trip Mileage": 7.0, "Trip Cost": 15.00,
                     "Member's First Name": "WC", "Member's Last Name": "MEMBER",
                     "Pickup City": "OCALA"},
                ],
            )
            make_drivers(
                sources / "Informacion de Drivers.xlsx",
                [{"DRIVER": "WC DRIVER", "COUNTY": "MARION", "LICENSE NUMBER": "L1",
                  "VIN Number": "V1", "CURRENT VEHICLE": "", "VEHICLE PLATE": "",
                  "NUMERO": 200}],
            )
            res = run_job(claim, sources)
            row = res["claim"]["rows"][0]

        self.assertIsNotNone(row["pu_appt"])
        self.assertIsNotNone(row["pu"])
        self.assertTrue(0 < _mins(row["pu_appt"]) - _mins(row["pu"]) <= 3)
        self.assertLess(row["pu"], row["dropoff"])


if __name__ == "__main__":
    unittest.main()
