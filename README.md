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
├── Facturacion MTM.exe     # ← EL PROGRAMA (doble clic para abrir la app)
├── run_app.py              # entrada por Python: GUI (doble clic) o CLI
├── selftest.py             # test contra los claims terminados de septiembre
├── Facturacion MTM.spec    # receta de PyInstaller
│
├── app/                    # el motor (Python)
│   ├── common.py           #   normalización de nombres / números / fechas / horas
│   ├── parsers.py          #   reconoce y lee los 4 tipos de archivo POR ESTRUCTURA
│   ├── filler.py           #   reglas de matching y relleno (ver NOTES.md §6)
│   ├── pipeline.py         #   orquesta: escanear carpeta → índices → rellenar
│   ├── report.py           #   reporte en pantalla + CSV
│   ├── writer.py           #   salida EXACTA (una hoja por día, 10 columnas, ordenado por driver)
│   ├── driverlogs.py       #   llena los driverlogs .docx por driver/día (python-docx)
│   └── ui.py               #   interfaz Tkinter
│
├── data/
│   ├── base/               # DATOS DE PRODUCCIÓN (el trabajo real)
│   │   ├── ClaimInformation 10-05 A 10-15 OLD.xlsx   # lo que baja del portal
│   │   ├── ClaimInformation 10-05 a 10-15 NEW.xlsx   # layout objetivo
│   │   ├── Informacion de Drivers.xlsx               # License/VIN por número de driver
│   │   ├── 10-05/ … 10-15/                           # RESÚMENES diarios
│   │   └── 10-05.xlsx, 10-06.xlsx                    # archivos de viajes (PU Time / Milage)
│   └── test/               # DATOS DE PRUEBA / referencia (no se usan al procesar)
│       ├── reference/      #   ejemplo de salida terminada (09-22)
│       └── Trips/          #   claims terminados + resúmenes de septiembre, carpeta Dalia, etc.
│
├── docs/
│   └── NOTES.md            # handoff completo del proyecto
│
├── output/                 # archivos generados (ClaimInformation relleno + reportes)
├── recon/                  # scripts de análisis usados para descifrar formatos (referencia)
├── dist/                   # copia de build del .exe (el que se usa está en la raíz)
└── build/                  # artefactos temporales de PyInstaller (se borra)
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

> **Idioma y tema:** arriba a la derecha hay dos botones — uno de **idioma** (bandera 🇻🇪/🇺🇸, español por defecto)
> y uno de **tema** (sol/luna, **modo oscuro por defecto**). Un clic en cada uno y listo.
>
> **PU Time / DropOff Time:** el archivo de viajes trae la hora de la **cita** (dropoff), no la recogida. El app
> **estima** el pickup con `cita − (14 min + 1.4×millas) ± 3 min` y el **DropOff** unos minutos antes de la cita,
> calibrado con los datos históricos (ver `docs/PU_TIME_FINDINGS.md`).
>
> **Drivers:** por defecto el app **empareja las patas A y B con el mismo driver** y, si dos viajeros del día
> comparten los mismos candidatos, los **reparte** (opción "Repartir…" para desactivarlo). Dalia siempre prefiere 349.

### Opción B — Python (para desarrollo)
```
python run_app.py                 # GUI
python run_app.py --cli "<claim.xlsx>" "data\base" --out "output\salida.xlsx"
python run_app.py --cli "<claim.xlsx>" "data\base" --driverlogs "<carpeta MTM Driverlogs>"
python run_app.py --cli "<claim.xlsx>" "data\base" --no-suggest   # dejar drivers en blanco
python run_app.py --cli "<claim.xlsx>" "data\base" --keep-order   # respetar el orden del claim
python selftest.py                # mide precisión contra septiembre
```

---

## Estado

- **v1 (HECHO)**: ClaimInformation relleno, una hoja por día, ordenado por driver. Probado y empaquetado.
- **v2 (HECHO)**: **driverlogs de Word** (.docx) — uno por driver y día, en `<día>\Docs\<día> <NUM>.docx`.
  Botón "Generar driverlogs (.docx)" en la app; ver `docs/NOTES.md` §15.
- El **BULK UPLOAD no es parte de esta app**: el usuario lo llena a mano después.
