import unittest

from app.filler import _allowed_drivers, fill_claim


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


if __name__ == "__main__":
    unittest.main()
