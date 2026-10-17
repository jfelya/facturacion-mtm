# Facturacion MTM app package
import os

# openpyxl optionally imports numpy; OpenBLAS can die on low-RAM machines unless
# we cap its thread pool BEFORE numpy gets imported anywhere.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
