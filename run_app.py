"""Entry point for the app.

GUI:  python run_app.py
CLI:  python run_app.py --cli <claim.xlsx> <carpeta_fuentes> [--drivers x.xlsx]
                                          [--out salida.xlsx] [--strategy first_row_A|first_row_B]
                                          [--gen-driverlogs --driverlogs <plantillas> --days-root <raiz>]
                                          [--gen-bulk]
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
    drivers = out = driverlogs = days_root = None
    strategy = "first_row_B"
    suggest = True
    spread = True
    keep_order = False
    gen_dl = False
    gen_bulk = False
    ratio, buffer = 1.4, 14
    rest = args[2:]
    i = 0
    while i < len(rest):
        if rest[i] == "--drivers" and i + 1 < len(rest):
            drivers = rest[i + 1]; i += 2
        elif rest[i] == "--driverlogs" and i + 1 < len(rest):
            driverlogs = rest[i + 1]; i += 2
        elif rest[i] == "--days-root" and i + 1 < len(rest):
            days_root = rest[i + 1]; i += 2
        elif rest[i] == "--gen-driverlogs":
            gen_dl = True; i += 1
        elif rest[i] == "--gen-bulk":
            gen_bulk = True; i += 1
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
    if gen_dl:
        from app.driverlogs import generate_driverlogs, report_lines
        if not driverlogs:
            p("ERROR: --gen-driverlogs necesita --driverlogs <carpeta de plantillas>")
            return 2
        gen = generate_driverlogs(res["claim"]["rows"], driverlogs, days_root or folder)
        p("\n" + report_lines(gen))
    if gen_bulk:
        from app.bulk import generate_bulks, report_lines as bulk_lines
        gen = generate_bulks(res["claim"]["rows"], days_root or folder)
        p("\n" + bulk_lines(gen))
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
