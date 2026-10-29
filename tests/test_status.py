import unittest
from datetime import time as dtime

from app.filler import fill_claim
from app.ui import status_of


class StatusTests(unittest.TestCase):
    def test_revisar_with_driver_and_milage_is_not_ok(self):
        row = {"driver": "200", "milage": 5.0, "flag": "revisar"}
        self.assertEqual(status_of(row), "REVISAR")

    def test_nota_with_driver_and_milage_stays_nota(self):
        row = {"driver": "200", "milage": 5.0, "flag": "nota"}
        self.assertEqual(status_of(row), "NOTA")

    def test_b_before_a_marks_revisar(self):
        rows = [
            {"row": 2, "trip": "A0A", "leg": "A", "date": "2026-10-05",
             "member": "TIME MEMBER", "driver": "200", "milage": 5.0,
             "pu": dtime(10, 0), "dropoff": dtime(10, 20),
             "license": "L", "vin": "V", "cost": "$10.00", "flag": ""},
            {"row": 3, "trip": "A0B", "leg": "B", "date": "2026-10-05",
             "member": "TIME MEMBER", "driver": "309", "milage": 5.0,
             "pu": dtime(9, 0), "dropoff": dtime(9, 20),
             "license": "L", "vin": "V", "cost": "$10.00", "flag": ""},
        ]
        drivers = {
            "table": {
                "200": {"license": "L", "vin": "V", "name": "D200", "county": "MARION"},
                "309": {"license": "L", "vin": "V", "name": "D309", "county": "MARION"},
            },
            "allowed": {"200", "309"},
        }
        fill_claim({"path": "synthetic.xlsx", "rows": rows}, {}, {}, drivers, balance=False)
        self.assertEqual(status_of(rows[1]), "REVISAR")


if __name__ == "__main__":
    unittest.main()
