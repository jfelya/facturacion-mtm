"""UI state and derived values; no Qt widgets and no engine logic."""
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from ..status import status_of
from ..strings import STRINGS


@dataclass
class AppState:
    claim_path: str = ""
    sources_folder: str = ""
    drivers_path: str = ""
    driverlogs_folder: str = ""
    days_root: str = ""
    strategy: str = "first_row_B"
    willcall_hours: float = 2.0
    suggest: bool = True
    spread: bool = True
    balance: bool = True
    lang: str = "es"
    theme: str = "dark"
    result: dict | None = None
    selected_key: tuple | None = None
    sources: dict | None = field(default=None, repr=False)

    def t(self, key, **kw):
        text = STRINGS.get(self.lang, STRINGS["es"]).get(key, key)
        return text.format(**kw) if kw else text


def counts(rows):
    return dict(Counter(status_of(row) for row in rows))


def row_key(row):
    return (row.get("date") or "", row.get("trip") or "")


def pending_rows(rows):
    return [r for r in rows if not r.get("driver") and r.get("flag") not in ("nofacturar", "facturado")]


def default_export_name(result):
    src = Path(result["claim_path"])
    return src.with_name(src.stem + " FILLED.xlsx")


def default_csv_name(result):
    src = Path(result["claim_path"])
    return src.with_name(src.stem + " REPORT.csv")
