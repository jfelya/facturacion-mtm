"""Run the existing engine in a QThread; the worker touches no widgets."""
from PySide6.QtCore import QObject, Signal

from ...pipeline import run_job


class JobWorker(QObject):
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, options):
        super().__init__()
        self._options = dict(options)

    def run(self):
        try:
            result = run_job(**self._options)
        except Exception as exc:  # noqa: BLE001 - reported to the UI
            self.failed.emit(f"{type(exc).__name__}: {exc}")
            return
        self.finished.emit(result)
