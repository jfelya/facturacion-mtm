import unittest

from app.filler import _balance_drivers


def _row(driver, member="TEST MEMBER", src_resumen=True, note_drv=False):
    return {"date": "2026-10-05", "member": member, "trip": "T0A",
            "driver": driver, "license": "L", "vin": "V", "flag": "",
            "src_resumen": src_resumen, "note_drv": note_drv}


class BalanceTests(unittest.TestCase):
    def test_balance_does_not_move_matched_rows(self):
        claim = {"rows": [_row("200") for _ in range(4)]}
        drivers = {"table": {"200": {"county": "MARION"}, "220": {"county": "MARION"}},
                   "allowed": {"200", "220"}}
        stats, review = {}, []
        _balance_drivers(claim, drivers, stats, review)
        self.assertTrue(all(r["driver"] == "200" for r in claim["rows"]))

    def test_balance_does_not_move_preferred_driver(self):
        claim = {"rows": [_row("349", "DALIA ALFONSO", src_resumen=False) for _ in range(4)]}
        drivers = {"table": {"349": {"county": "MARION"}, "10": {"county": "MARION"}},
                   "allowed": {"349", "10"}}
        stats, review = {}, []
        _balance_drivers(claim, drivers, stats, review)
        self.assertTrue(all(r["driver"] == "349" for r in claim["rows"]))

    def test_balance_can_move_unmatched_rows(self):
        claim = {"rows": [_row("200", src_resumen=False) for _ in range(4)]}
        drivers = {"table": {"200": {"county": "MARION"}, "220": {"county": "MARION"}},
                   "allowed": {"200", "220"}}
        stats, review = {}, []
        _balance_drivers(claim, drivers, stats, review)
        self.assertIn("220", [r["driver"] for r in claim["rows"]])


if __name__ == "__main__":
    unittest.main()
