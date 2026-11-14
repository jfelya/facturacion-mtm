"""Turn driverlog DOCX files into per-driver PDFs and one merged PDF per day.

Layout (same as the owner's reference folders):
    <days_root>\\<day>\\Docs\\<day> <NUM>.docx
    <days_root>\\<day>\\Docs\\<day> <NUM>.pdf
    <days_root>\\<day>\\<day> merged.pdf

Conversion needs Microsoft Word (COM). Merging uses pypdf and works with any
PDFs already present, even when the DOCX is gone.
"""
import os
import re
from pathlib import Path

_NUMBER = re.compile(r"(\d+)\s*$")


class DriverPdfError(Exception):
    """The PDF step could not run (no Word, locked file, ...)."""


def driver_number(path):
    """Numeric driver number from a file name like '10-07 220.docx'."""
    match = _NUMBER.search(Path(path).stem)
    return int(match.group(1)) if match else 10 ** 9


def _docs_dir(day_dir):
    return Path(day_dir) / "Docs"


def _is_lock(path):
    return Path(path).name.startswith("~$")


def _export(word, docx, pdf):
    """Export one DOCX with an already-running Word instance."""
    docx = Path(docx).resolve()
    pdf = Path(pdf).resolve()
    tmp = pdf.with_name(pdf.stem + ".tmp.pdf")
    try:
        doc = word.Documents.Open(str(docx), ReadOnly=True,
                                  AddToRecentFiles=False, ConfirmConversions=False)
        try:
            doc.ExportAsFixedFormat(str(tmp), 17)  # 17 = wdExportFormatPDF
        finally:
            doc.Close(False)
        os.replace(tmp, pdf)
    except Exception as exc:  # noqa: BLE001 - COM raises generic errors
        raise DriverPdfError(f"{type(exc).__name__}: {exc}") from exc
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


class WordConverter:
    """Reuse one Word instance for a whole batch (starting Word is the slow part)."""

    def __enter__(self):
        try:
            import pythoncom
            import win32com.client
        except ImportError as exc:  # pragma: no cover - depends on the install
            raise DriverPdfError("falta pywin32 (pip install pywin32)") from exc
        self._pythoncom = pythoncom
        pythoncom.CoInitialize()
        try:
            self.word = win32com.client.DispatchEx("Word.Application")
            self.word.Visible = False
            self.word.DisplayAlerts = 0
        except Exception as exc:  # noqa: BLE001
            pythoncom.CoUninitialize()
            raise DriverPdfError(
                f"No se pudo abrir Microsoft Word ({type(exc).__name__}: {exc})") from exc
        return self

    def __call__(self, docx, pdf):
        _export(self.word, docx, pdf)

    def __exit__(self, *exc_info):
        try:
            self.word.Quit()
        except Exception:  # noqa: BLE001
            pass
        self._pythoncom.CoUninitialize()
        return False


def convert_docx(docx, pdf):
    """Standalone single-file conversion (starts and quits Word)."""
    with WordConverter() as convert:
        convert(docx, pdf)


def convert_day(day_dir, convert=convert_docx):
    """Convert every driverlog DOCX of one day that has no up-to-date PDF."""
    docs = _docs_dir(day_dir)
    converted = skipped = 0
    errors = []
    if not docs.is_dir():
        return {"converted": 0, "skipped": 0, "errors": errors}
    for docx in sorted(docs.glob("*.docx")):
        if _is_lock(docx):
            continue
        pdf = docx.with_suffix(".pdf")
        if pdf.exists() and pdf.stat().st_mtime >= docx.stat().st_mtime:
            skipped += 1
            continue
        try:
            convert(docx, pdf)
            converted += 1
        except DriverPdfError as exc:
            errors.append({"file": docx.name, "error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            errors.append({"file": docx.name, "error": f"{type(exc).__name__}: {exc}"})
    return {"converted": converted, "skipped": skipped, "errors": errors}


def merge_day(day_dir):
    """Merge the day's driver PDFs, ordered by driver number, into '<day> merged.pdf'."""
    day_dir = Path(day_dir)
    docs = _docs_dir(day_dir)
    pdfs = sorted((p for p in docs.glob("*.pdf") if not _is_lock(p)), key=driver_number)
    if not pdfs:
        return None
    from pypdf import PdfWriter

    writer = PdfWriter()
    for pdf in pdfs:
        writer.append(str(pdf))
    out = day_dir / f"{day_dir.name} merged.pdf"
    tmp = out.with_name(out.stem + ".tmp.pdf")
    with open(tmp, "wb") as fh:
        writer.write(fh)
    os.replace(tmp, out)
    return {"path": out, "files": len(pdfs), "pages": len(writer.pages)}


def _needs_conversion(day_dir):
    for docx in _docs_dir(day_dir).glob("*.docx"):
        if _is_lock(docx):
            continue
        pdf = docx.with_suffix(".pdf")
        if not pdf.exists() or pdf.stat().st_mtime < docx.stat().st_mtime:
            return True
    return False


def process_days(days_root, convert=None):
    """Convert and merge every day folder under `days_root` that has a Docs folder."""
    root = Path(days_root)
    if not root.is_dir():
        raise DriverPdfError(f"carpeta no encontrada: {root}")
    days = sorted(p for p in root.iterdir() if p.is_dir() and _docs_dir(p).is_dir())
    if convert is not None:
        return _process_days(days, convert)
    if not any(_needs_conversion(d) for d in days):
        # every PDF is up to date (or there is no DOCX): merging needs no Word
        return _process_days(days, lambda docx, pdf: None)
    with WordConverter() as converter:
        return _process_days(days, converter)


def _process_days(days, convert):
    converted = skipped = merged = pages = 0
    merged_files = []
    errors = []
    for day_dir in days:
        day = convert_day(day_dir, convert=convert)
        converted += day["converted"]
        skipped += day["skipped"]
        errors.extend({"day": day_dir.name, **e} for e in day["errors"])
        try:
            result = merge_day(day_dir)
        except Exception as exc:  # noqa: BLE001
            errors.append({"day": day_dir.name, "file": "merge", "error": f"{type(exc).__name__}: {exc}"})
            continue
        if result:
            merged += 1
            pages += result["pages"]
            merged_files.append(result["path"])
    return {"converted": converted, "skipped": skipped, "merged": merged,
            "pages": pages, "merged_files": merged_files, "errors": errors}
