import unittest

from app.filler import _balance_drivers, fill_claim


def _row(driver, member="TEST MEMBER", src_resumen=True, note_drv=False, substituted=False):
    return {"date": "2026-10-05", "member": member, "trip": "T0A",
            "driver": driver, "license": "L", "vin": "V", "flag": "",
            "src_resumen": src_resumen, "note_drv": note_drv,
            "substituted": substituted}


class BalanceTests(unittest.TestCase):
    def test_balance_moves_matched_rows_when_over_cap(self):
        claim = {"rows": [_row("200") for _ in range(4)]}
        drivers = {"table": {"200": {"county": "MARION"}, "220": {"county": "MARION"}},
                   "allowed": {"200", "220"}}
        stats, review = {}, []
        _balance_drivers(claim, drivers, stats, review)
        self.assertIn("220", [r["driver"] for r in claim["rows"]])

    def test_balance_moves_note_pinned_rows_when_over_cap(self):
        claim = {"rows": [_row("200", note_drv=True) for _ in range(4)]}
        drivers = {"table": {"200": {"county": "MARION"}, "220": {"county": "MARION"}},
                   "allowed": {"200", "220"}}
        stats, review = {}, []
        _balance_drivers(claim, drivers, stats, review)
        self.assertIn("220", [r["driver"] for r in claim["rows"]])

    def test_balance_never_crosses_county(self):
        claim = {"rows": [_row("200") for _ in range(4)]}
        drivers = {"table": {"200": {"county": "MARION"}, "20": {"county": "VOLUSIA"}},
                   "allowed": {"200", "20"}}
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

    def test_balance_can_move_substituted_rows(self):
        claim = {"rows": [_row("200", substituted=True) for _ in range(4)]}
        drivers = {"table": {"200": {"county": "MARION"}, "220": {"county": "MARION"}},
                   "allowed": {"200", "220"}}
        stats, review = {}, []
        _balance_drivers(claim, drivers, stats, review)
        self.assertIn("220", [r["driver"] for r in claim["rows"]])


def _suggestion_batch(count=4):
    """Four trips whose resumen driver (415) is not approved, with 3 free drivers in county."""
    rows = []
    resumen = {}
    for i in range(count):
        member = f"MEMBER {i}"
        rows.append({"row": i + 2, "trip": f"T{i}A", "leg": "A", "date": "2026-10-05",
                     "member": member, "driver": "", "milage": None, "pu": None,
                     "license": "", "vin": "", "cost": "$10.00", "flag": ""})
        resumen[("2026-10-05", member)] = [{
            "date": "2026-10-05", "name": member, "driver": "415", "miles": 5.0,
            "trip_id": "", "payer": "MTM", "note": "", "time": None, "src": "synthetic.xlsx",
        }]
    table = {
        "415": {"name": "UNAPPROVED", "license": "X", "vin": "X", "county": "MARION"},
        "200": {"name": "D200", "license": "L200", "vin": "V200", "county": "MARION"},
        "220": {"name": "D220", "license": "L220", "vin": "V220", "county": "MARION"},
        "309": {"name": "D309", "license": "L309", "vin": "V309", "county": "MARION"},
    }
    drivers = {"table": table, "allowed": {"200", "220", "309"}}
    return {"path": "synthetic.xlsx", "rows": rows}, resumen, drivers


class SuggestionSpreadTests(unittest.TestCase):
    def test_suggestions_do_not_pile_up_on_one_driver(self):
        claim, resumen, drivers = _suggestion_batch(4)
        fill_claim(claim, resumen, {}, drivers, driver_usage={"2026-10-05": {"count": {}}},
                   suggest_driver=True, balance=True)
        counts = {}
        for row in claim["rows"]:
            counts[row["driver"]] = counts.get(row["driver"], 0) + 1
        self.assertTrue(all(row["driver"] for row in claim["rows"]))
        self.assertLessEqual(max(counts.values()), 2)


if __name__ == "__main__":
    unittest.main()
