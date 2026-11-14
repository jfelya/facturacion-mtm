import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.driverpdf import driver_number, merge_day, process_days


def _blank(path, height):
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=height)
    with open(path, "wb") as fh:
        writer.write(fh)


class DriverPdfTests(unittest.TestCase):
    def test_driver_number_is_numeric_not_textual(self):
        self.assertEqual(driver_number(Path("10-07 10.pdf")), 10)
        self.assertEqual(driver_number(Path("10-07 220.pdf")), 220)
        self.assertEqual(driver_number(Path("09-01-2026 200.pdf")), 200)

    def test_merge_day_orders_by_driver_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            day = Path(tmp) / "10-07"
            docs = day / "Docs"
            docs.mkdir(parents=True)
            _blank(docs / "10-07 220.pdf", 220)
            _blank(docs / "10-07 10.pdf", 10)
            _blank(docs / "10-07 30.pdf", 30)
            result = merge_day(day)
            self.assertTrue(result["path"].exists())
            self.assertEqual(result["path"].name, "10-07 merged.pdf")
            pages = PdfReader(result["path"]).pages
            self.assertEqual([round(float(p.mediabox.height)) for p in pages], [10, 30, 220])

    def test_merge_day_without_pdfs_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            day = Path(tmp) / "10-07"
            (day / "Docs").mkdir(parents=True)
            self.assertIsNone(merge_day(day))

    def test_process_days_converts_and_merges(self):
        def fake_convert(docx, pdf):
            _blank(pdf, driver_number(docx))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "10-07" / "Docs"
            docs.mkdir(parents=True)
            (docs / "10-07 30.docx").write_bytes(b"x")
            (docs / "10-07 10.docx").write_bytes(b"x")
            (docs / "~$10-07 220.docx").write_bytes(b"lock")
            result = process_days(root, convert=fake_convert)
            self.assertEqual(result["converted"], 2)
            self.assertTrue((root / "10-07" / "10-07 merged.pdf").exists())
            self.assertEqual(result["errors"], [])


if __name__ == "__main__":
    unittest.main()
