import tempfile
import unittest
from pathlib import Path

from app.writer import ensure_not_source, write_output


def _row(flag=""):
    return {
        "date": "2026-10-05", "date_text": "10/05/2026", "trip": "T0A",
        "member_raw": "TEST MEMBER", "driver": "200", "license": "L",
        "vin": "V", "pu": None, "dropoff": None, "milage": 1.0,
        "cost": "$1.00", "flag": flag,
    }


class WriterGuardTests(unittest.TestCase):
    def test_write_output_refuses_source_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "claim.xlsx"
            source.write_bytes(b"ORIGINAL")
            before = source.read_bytes()
            claim = {"path": str(source), "rows": [_row()]}
            with self.assertRaises(ValueError):
                write_output(claim, source)
            self.assertEqual(source.read_bytes(), before)

    def test_write_output_to_new_path_still_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "claim.xlsx"
            source.write_bytes(b"ORIGINAL")
            out = Path(tmp) / "out.xlsx"
            info = write_output({"path": str(source), "rows": [_row()]}, out)
            self.assertTrue(out.exists())
            self.assertEqual(info["rows"], 1)

    def test_write_output_refuses_when_all_rows_are_billed(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.xlsx"
            with self.assertRaises(ValueError):
                write_output({"rows": [_row("facturado")]}, out)

    def test_ensure_not_source_rejects_the_source_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "claim.xlsx"
            source.write_bytes(b"ORIGINAL")
            with self.assertRaises(ValueError):
                ensure_not_source(source, source)
            ensure_not_source(Path(tmp) / "other.csv", source)


if __name__ == "__main__":
    unittest.main()
