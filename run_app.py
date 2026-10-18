"""Entry point for the app.

GUI:  python run_app.py
CLI:  python run_app.py --cli <claim.xlsx> <carpeta_fuentes> [--drivers x.xlsx]
                                          [--out salida.xlsx] [--strategy first_row_A|first_row_B]
"""
import os
# must be set BEFORE anything imports numpy/openpyxl (low-RAM machines crash in OpenBLAS)
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import sys
from pathlib import Path


def main_cli(args):
    from app.pipeline import run_job
    from app.report import report_text
    from app.writer import write_output

    def p(*a):
        try:
            print(*a)
        except Exception:
            pass  # windowed exe has no stdout

    claim, folder = args[0], args[1]
    drivers = out = driverlogs = None
    strategy = "pair"
    suggest = True
    spread = True
    keep_order = False
    ratio, buffer = 1.4, 14
    rest = args[2:]
    i = 0
    while i < len(rest):
        if rest[i] == "--drivers" and i + 1 < len(rest):
            drivers = rest[i + 1]; i += 2
        elif rest[i] == "--driverlogs" and i + 1 < len(rest):
            driverlogs = rest[i + 1]; i += 2
        elif rest[i] == "--out" and i + 1 < len(rest):
            out = rest[i + 1]; i += 2
        elif rest[i] == "--strategy" and i + 1 < len(rest):
            strategy = rest[i + 1]; i += 2
        elif rest[i] == "--ratio" and i + 1 < len(rest):
            ratio = float(rest[i + 1]); i += 2
        elif rest[i] == "--buffer" and i + 1 < len(rest):
            buffer = float(rest[i + 1]); i += 2
        elif rest[i] == "--no-suggest":
            suggest = False; i += 1
        elif rest[i] == "--no-spread":
            spread = False; i += 1
        elif rest[i] == "--keep-order":
            keep_order = True; i += 1
        else:
            i += 1

    res = run_job(claim, folder, drivers_path=drivers, strategy=strategy,
                  suggest_driver=suggest, sort_by_date=not keep_order, spread=spread,
                  pickup_ratio=ratio, pickup_buffer=buffer, driverlogs_folder=driverlogs)
    if res.get("error"):
        p("ERROR:", res["error"])
        return 2
    p(report_text(res))
    if out:
        info = write_output(res["claim"], out)
        p(f"\nGuardado: {out} ({info['rows']} filas)")
    return 0


def main():
    args = sys.argv[1:]
    if args and args[0] == "--cli":
        if len(args) < 3:
            print(__doc__)
            return 1
        return main_cli(args[1:])
    from app.ui import main as gui_main
    gui_main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
