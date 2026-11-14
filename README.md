# Facturación MTM

App de escritorio (Windows) que toma el `ClaimInformation` descargado del portal de MTM,
lo rellena con los datos del negocio (RESÚMENES diarios, archivos de viajes, información de drivers)
y exporta el Excel final listo para subir al portal.

> Para el contexto completo del proyecto (reglas, formatos, decisiones, pendientes) leer
> **`docs/NOTES.md`** — es la fuente de verdad.

---

## Estructura del proyecto

```
Facturacion MTM/
├── Facturacion MTM.exe     # build 64-bit one-file (raíz, v3.0.0.0)
├── run_app.py              # entrada: GUI (PySide6) o CLI
├── selftest.py             # benchmark de precisión contra septiembre
├── build.ps1               # build PyInstaller 64-bit
├── Facturacion MTM.spec    # receta PyInstaller
├── requirements.txt        # dependencias del motor/CLI (incl. pypdf, pywin32)
├── requirements-ui.txt     # PySide6-Essentials
├── requirements-build.txt  # motor + PySide6 + PyInstaller
├── version_info.txt        # versión del build
├── assets/                 # icon.png / icon.ico (marca de MTM)
│
├── app/                    # el motor (Python) + UI
│   ├── common.py           #   normalización / fechas / horas / notas / helpers
│   ├── status.py           #   estado visual de una fila
│   ├── parsers.py          #   reconoce y lee los 4 tipos de archivo POR ESTRUCTURA
│   ├── filler.py           #   matching, notas, aprobación, sugerencias, reparto, PU/DropOff
│   ├── pipeline.py         #   orquesta: escanear carpeta → índices → rellenar
│   ├── report.py           #   reporte en pantalla + CSV
│   ├── writer.py           #   salida EXACTA (una hoja por día, 10 columnas, ordenado por driver)
│   ├── driverlogs.py       #   llena los driverlogs .docx por driver/día (python-docx)
│   ├── driverpdf.py        #   driverlogs .docx → PDF + un «<día> merged.pdf» por día
│   ├── bulk.py             #   genera el BULK UPLOAD .xlsx por día (plantilla bundleada)
│   ├── strings.py          #   textos ES/EN de la UI
│   └── ui_qt/              #   UI PySide6 (models, delegates, theme, dialogs)
│
├── tests/                  # unittest + fixtures sintéticas (no necesitan data/)
├── tests_qt/               # tests de la UI
├── data/
│   ├── base/               # DATOS DE PRODUCCIÓN (el trabajo real)
│   └── test/               # DATOS DE PRUEBA / referencia
├── docs/
│   ├── NOTES.md            # estado actual (fuente de verdad)
│   ├── HISTORY.md          # notas históricas
│   ├── PU_TIME_FINDINGS.md # calibración de PU/DropOff
│   └── PORTABILITY.md      # portabilidad / builds
│
├── dist/                   # (se genera al compilar) build 64-bit
└── build/                  # (se genera al compilar) artefactos temporales de PyInstaller
```

**Regla:** los datos de producción viven en `data/base/`; lo de prueba/referencia en `data/test/`.
Si llega un archivo nuevo, cópialo a la carpeta que corresponda dentro de `data/` para que
cualquier chat futuro tenga acceso.

---

## Cómo usarlo

### Opción A — el .exe (para el usuario final)
1. Doble clic en **`Facturacion MTM.exe`** (en la carpeta del proyecto).
2. **Claim OLD/NEW (.xlsx):** elige el `ClaimInformation ... OLD.xlsx` de `data/base/`.
3. **Carpeta de fuentes:** elige `data/base/` (detecta resúmenes, viajes y drivers por estructura, no por nombre).
4. **Informacion de Drivers.xlsx** *(opcional)*: solo si no está dentro de la carpeta de fuentes.
5. **Driverlogs (plantillas .docx)**: la carpeta con los `<NUM> <NOMBRE> DRIVERLOG VACIO.docx`
   (ej. `…\Facturacion\MTM Driverlogs`). Los drivers **sin plantilla** se reemplazan por uno libre que sí tenga.
6. **Carpeta de días** *(opcional)*: donde están las carpetas `10-05`, `10-06`… (ej. `…\1. PARA FACTURAR`).
   Si la dejas vacía, se usa la **carpeta de fuentes**.
7. Pulsa **Procesar**.
8. Revisa los colores:
   - 🟢 **OK** — driver + milage listos
   - 🟡 **NOTA** — tiene una anotación tuya (se respetó)
   - 🟣 **SUGERIDO** — el app puso el driver menos ocupado de ese día; confírmalo o cámbialo en *Asignar driver*
   - 🔵 **ELEGIR** — viene del portal pero no hay fila MTM ni forma de sugerir: elige el driver a mano
   - ⬜ **NO FACTURAR** — viene del claim pero no está en el resumen (y no es Dalia): no se factura
   - 🔴 **SIN DATO** — no hay información para ese viaje
9. **Exportar Excel** → guarda el archivo terminado. La salida tiene **UNA HOJA POR DÍA** (`10-05`, `10-06`, …),
   cada una **ordenada por número de driver**, con las columnas exactas (`Driver, License, VIN, Appt. Date,
   Trip Number, Member Info, PU Time, DropOff Time, Milage, Cost`).
10. **Generar driverlogs (.docx)** → escribe un driverlog por driver y día en
    **`<día>\Docs\<día> <NUM>.docx`** (ej. `10-05 200.docx`). **No toca las plantillas**.
11. **Generar BULK UPLOAD** → escribe **`<día>\BULK UPLOAD MM-DD-YYYY.xlsx`** (uno por día) listo para subir al
    portal, con el mismo formato de la plantilla. Ver `docs/NOTES.md`.
12. **Generar PDFs (merged)** → convierte cada driverlog a PDF (`<día>\Docs\<día> <NUM>.pdf`) y crea
    **`<día>\<día> merged.pdf`** con todos los drivers del día, en orden de número (10, 20, 220…).
    Necesita **Microsoft Word** instalado; si los PDF ya existen, solo combina.

> **Idioma y tema:** arriba a la derecha hay dos botones — uno de **idioma** (bandera 🇻🇪/🇺🇸, español por defecto)
> y uno de **tema** (sol/luna, **modo oscuro por defecto**). Un clic en cada uno y listo.
>
> **PU Time / DropOff Time:** el archivo de viajes trae la hora de la **cita** (dropoff), no la recogida. El app
> fija el **DropOff** 1–5 min antes de la cita y estima el pickup con `DropOff − (14 min + 1.4×millas ± 3 min)`,
> calibrado con los datos históricos (ver `docs/PU_TIME_FINDINGS.md` y `tests/test_pickup.py`).
>
> **Drivers:** por defecto el app asigna **un driver por pata** según el resumen (opción **"Uno por pata"**). Si quieres
> el **mismo driver en ambas** patas, elige esa opción en la UI o usa `--strategy pair`. Dalia prefiere 349 salvo que
> el resumen traiga una nota `auto N` (por ejemplo, 309 en 10-14/10-15).

### Opción B — Python (para desarrollo)
```
python run_app.py                 # GUI
python run_app.py --cli "<claim.xlsx>" "data\base" --out "output\salida.xlsx"
python run_app.py --cli "<claim.xlsx>" "data\base" --driverlogs "<carpeta MTM Driverlogs>"
python run_app.py --cli "<claim.xlsx>" "data\base" --no-suggest   # dejar drivers en blanco
python run_app.py --cli "<claim.xlsx>" "data\base" --keep-order   # respetar el orden del claim
python run_app.py --cli "<claim.xlsx>" "data\base" --gen-bulk --days-root "…\1. PARA FACTURAR"
python selftest.py                # mide precisión contra septiembre
```

### Opción C — tests y build
```powershell
$py = "C:\Users\Fely\AppData\Local\Python\pythoncore-3.14-64\python.exe"
& $py -m unittest discover -s tests -v   # 47 tests, fixtures sintéticas (no necesita data/)
$env:QT_QPA_PLATFORM="offscreen"
& $py -m unittest discover -s tests_qt -v  # 6 tests de la UI
& $py selftest.py                        # benchmark de septiembre
.\build.ps1                              # PyInstaller 64-bit + copia el exe a la raíz
```

`tests/` usa solo la librería estándar. El build usa el **Python 3.14 64-bit**
(`C:\Users\Fely\AppData\Local\Python\pythoncore-3.14-64\python.exe`); si está en otra ruta, pasa
`-Python <ruta>`. El exe de la raíz es **64-bit one-file**.

### Opción D — dependencias de la UI
```powershell
pip install -r requirements-ui.txt       # PySide6-Essentials 6.12 (64-bit)
```

La app es **64-bit-only** (Windows 10 64-bit 1809+ / Windows 11). No hay build de 32 bits.

---

## Estado

- **v1 (HECHO)**: ClaimInformation relleno, una hoja por día, ordenado por driver. Probado y empaquetado.
- **v2 (HECHO)**: **driverlogs de Word** (.docx) — uno por driver y día, en `<día>\Docs\<día> <NUM>.docx`.
  Botón "Generar driverlogs (.docx)" en la app; ver `docs/NOTES.md`.
- **v2.1 (HECHO)**: regla de **condado** (Volusia/Marion), Dalia prefiere un driver libre ese día, aviso si faltan
  trip files (Proceed/Cancel), chequeo de **tiempos A/B** (B no puede empezar antes que A) y apertura maximizada.
- **v3 (HECHO)**: **BULK UPLOAD** por día — `<día>\BULK UPLOAD MM-DD-YYYY.xlsx` con el formato exacto de la plantilla
  (usado por el portal). Botón "Generar BULK UPLOAD" / CLI `--gen-bulk`. Ver `docs/NOTES.md`.
- **v3.1 (RETIRADO)**: existió un build **32-bit universal**; desde v5 la app es **64-bit-only**.
- **v4 (HECHO, 28-oct-2026)**: auditoría/revamp. El reparto ya **no mueve filas con match/nota/preferencia**
  (solo sugeridas), las filas con nota `Facturado.` se **omiten** del Excel/BULK/driverlogs y salen en el reporte,
  se protegió la exportación contra sobreescribir el claim, se corrigió el estado `REVISAR`, se añadieron **39 tests**
  (`python -m unittest discover -s tests -v`) y se limpió código muerto. Ver `docs/NOTES.md`.
- **v5 (HECHO, 14-nov-2026)**: UI **PySide6 + QSS** en `app/ui_qt/`, **64-bit-only**, build único
  `Facturacion MTM.exe` (v3.0.0.0, 45 MB). La UI Tk y el build de 32 bits **fueron retirados**. Ver
  `docs/PYSIDE6_UI_MIGRATION_ANALYSIS.md`.

## Portabilidad

El `.exe` de la **raíz** es **standalone / one-file y 64-bit (x64)**: cópialo a cualquier PC con **Windows 10 64-bit
(1809+) o Windows 11** y funciona sin instalar Python ni dependencias. La build `dist\` se regenera al compilar con
PyInstaller. Ver `docs/PORTABILITY.md`.

**Firma digital:** por ahora el `.exe` va **sin firmar**. Windows puede mostrar "Unknown publisher" la primera vez →
*Más información → Ejecutar de todas formas*. La firma de código queda **pendiente** (ver `docs/HISTORY.md`).

> **Importante:** el exe de la raíz se recompiló el **14-nov-2026** como **64-bit · v3.0.0.0** y se verificó:
> arranca maximizado y sus salidas (Excel, CSV, BULK y driverlogs) son idénticas a las del motor. Si cambias código,
> vuelve a ejecutar `.\build.ps1`.

La app abre **maximizada**. Si no hay archivos de viajes en la carpeta de fuentes, avisa antes de procesar
(las horas y la milla de Dalia saldrían vacías) y deja elegir **Proceed / Cancel**.
