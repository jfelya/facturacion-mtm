# Historical notes (pre-2026-10-28)

> Preserved for reference. Current rules are in `docs/NOTES.md`.

# Facturación MTM — HANDOFF / notas completas del proyecto

> Este archivo es la fuente de verdad para continuar el proyecto en cualquier chat (los chats se compactan).
> Última actualización: 18-oct-2026. Leer completo antes de tocar código.

---

## 1. Objetivo

App local para Windows que toma el `ClaimInformation ... OLD.xlsx` descargado del portal de MTM (viajes médicos,
sin varios campos) y le rellena los huecos usando los demás archivos del negocio, exportando un Excel final
**idéntico en formato al archivo terminado de ejemplo** (el "…NEW.xlsx"). El usuario sube ese Excel al portal.

- **v1 (HECHO): SOLO el ClaimInformation relleno.**
- **v2 (HECHO, 18-oct): llenar los DRIVERLOGS de Word (.docx), uno por driver y por día** — ver **§15**.
  Incluye el **orden por driver** del claim final (§15.1).
- **v3 (HECHO, 18-oct): BULK UPLOAD** — un `BULK UPLOAD MM-DD-YYYY.xlsx` por día, en la carpeta del día,
  a partir del claim final (ver **§17**).

Usuario: Fely (escribe en inglés, archivos en español). Hablar claro y práctico.

---

## 2. Entorno

- Windows. Proyecto: `C:\Users\Fely\Documents\OpenCode\Facturacion MTM`
- **Estructura del proyecto (ver `README.md`):**
  - `app/` motor · `docs/NOTES.md` este archivo · `Facturacion MTM.exe` (raíz, único exe) ·
    `dist/`, `dist32/`, `build/` (se generan al compilar con PyInstaller).
  - ⚠️ **18-oct: se borraron `recon/` y `output/`** (proyecto limpio). Si hace falta análisis nuevo, recrearlo.
  - **`data/base/`** = datos de PRODUCCIÓN (claim OLD/NEW, `Informacion de Drivers.xlsx`, resúmenes `10-0X/`, trips `10-05.xlsx`…`10-15.xlsx`).
  - **`data/test/`** = datos de PRUEBA/referencia (claims terminados y resúmenes de septiembre, carpeta Dalia, ejemplo 09-22). Solo `.xlsx` (los PDFs de driver logs NO se copiaron, no son relevantes).
  - El proyecto es **autocontenido**: TODO se lee desde `data/`. NO usar `C:\Users\Fely\Downloads` ni sus subcarpetas. **Al llegar archivos nuevos, ponerlos en `data/base/` (producción) o `data/test/` (prueba).**
- Python 3.14: `C:\Users\Fely\AppData\Local\Python\pythoncore-3.14-64\python.exe`
  - ⚠️ `python` a veces NO está en PATH en shells nuevas → usar ruta completa del .exe.
- Paquetes instalados: `openpyxl`, `pandas`, `pyinstaller` (6.22.3).
- **Scripts de recon:** la carpeta `recon/` se **borró el 18-oct** (era solo investigación). El conocimiento queda documentado en este NOTES y en `docs/PU_TIME_FINDINGS.md`; los scripts de análisis (matching, mapeo, volcados, comparaciones, icono) ya no están.
- El terminal de PowerShell muestra acentos como `�` (codepage) — no es corrupción real de archivos.

---

## 3. Proceso de negocio (según "BULK UPLOAD Training.xlsx")

1. Descargar ClaimInformation desde CLAIMS de MTM (…OLD.xlsx).
2. Separar viajes MTM de ACCESS2CARE (**abierto**: significado exacto de este paso — preguntar).
3. Hacer Driver Logs (PDFs, no relevantes para v1).
4. Llenar BULK UPLOAD + borrar filas vacías (v2).
5. Subir el ClaimInformation/Bulk + comprimido de driver logs al portal.

---

## 4. Mapeo exacto de columnas (VERIFICADO 81/81 filas)

### Entrada: claim OLD (todas las columnas del portal)
`Claim Status | Trip Number | Appt. Date | Member Info | Driver | VIN | Claim Submit Date | Appeal Deadline |
Paid Amount | Pay By Date | Check Number | Cost | Denial Reason | Plan Code | Name (First and Last) |
Provider Cost | Special Fees`

### Salida: claim NEW (orden y nombres EXACTOS)
`Driver | License | VIN | Appt. Date | Trip Number | Member Info | PU Time | DropOff Time | Milage | Cost`
(**UNA HOJA POR DÍA**, nombre `MM-DD`). `Appt. Date` va **ANTES de `Trip Number`** (18-oct, confirmado con la
imagen del usuario; antes estaba al revés). `DropOff Time` se añadió
17-oct (lo piden los driver logs); es `h:mm` igual que PU Time. *El ejemplo terminado de septiembre era una sola hoja `ClaimInformation` (un solo día); con `write_output(..., per_day=False)` se vuelve a ese formato.*

### De dónde sale cada columna
| Columna NEW | Origen | Detalle |
|---|---|---|
| Driver | RESUMEN diario | fila MTM del miembro ese día; columna número de driver |
| License | `Informacion de Drivers.xlsx` hoja `Vehiculos` | por `NUMERO`; copiar tal cual (a veces sin guiones) |
| VIN | ídem | ídem |
| Trip Number | OLD | copiar |
| Appt. Date | OLD | copiar como TEXTO `MM/DD/YYYY` |
| Member Info | OLD `Name (First and Last)` | copiar tal cual (ya viene MAYÚSCULAS) |
| PU Time | archivo de viajes del día (tipo `10-05.xlsx`) | **ESTIMADO**: la col `Time` es la hora de la CITA (dropoff), no la recogida → `dropoff = cita − 1..5 min`; `PU = dropoff − (14 min + 1.4×millas ± 3 min)` (ver §6.4 y `docs/PU_TIME_FINDINGS.md`) |
| Milage | RESUMEN diario | `MILES` de la fila del driver elegido. **Fallback:** si no hay fila MTM, se toma `Trip Mileage` del archivo de viajes del día (cubre Dalia) |
| Cost | OLD `Provider Cost` | copiar tal cual (`$38.14` texto) |

Orden de filas del output: **por día (una hoja `MM-DD`) y, dentro de cada día, por NÚMERO DE DRIVER ascendente**
(18-oct; antes se respetaba el orden del OLD). Los que no tienen driver van al final. Tipos de celda (verificado en ejemplo terminado): Driver = número;
Appt.Date/Member/Cost/License/VIN/TripNumber = texto; Milage = número; **PU Time = valor hora real Excel con
number_format `'h:mm'`** (ej. 14:00). Cost = texto con `$` y 2 decimales.

---

## 5. Catálogo de formatos (trampas que el parser DEBE tolerar)

### 5.1 RESUMEN diario — layouts MUY cambiantes entre días (todos vistos en real)
Headers observados (todas tienen DATE/NAME/MILES en alguna forma):
- `DATE|LOS|TRIP ID|PAYER|NAME|LAST NAME|DRIVER|MILES|DRIVER` (09-16..09-22; TRIP ID presente en 09-16/17 = match exacto; a veces vacío)
- `DATE|LOS|TRIP ID|PAYER|NAME|DRIVER|MILES|DRIVER` (09-24..09-30 — NAME sola trae nombre completo)
- `DATE|LOS|PAYER TRIP ID|PROVIDER|NAME|DRIVER|MILES|DRIVER` (10-02)
- `DTE|LOS|TRIP ID|PAYER|NAME|LAST NAME|DRIVER|MILES` (10-13 — typo real "DTE")
- `DATE|LOS|RIDE ID|PAYER|NAME|LASTNAME|VEHICLE|MILEAGE` (10-05 — ¡la col VEHICLE contiene el NÚMERO de driver y hay columnas extra de datos más allá de los headers!)
- `DATE|LOS|RIDE ID|PROVIDER|NAME|LASTNAME|VEHICLE ID|MILEAGE` (09-04/09-05)
- `DATE|LOS|PAYER|NAME|LASTNAME|DRIVER|MILEAGE|DRIVER` (09-03)
- Octubre 10-06 en adelante: variantes CON `TIME` (timestamp) y/o `BILLING`.
- Alias necesarios: DATE/DTE; LAST NAME/LASTNAME; MILES/MILEAGE; PAYER/PROVIDER; TRIP ID/RIDE ID.
- Conteo de columnas ALTERADO: los headers a veces no coinciden con las columnas de datos → detectar la columna
  numérica de driver y la de miles **por contenido**, no por posición.
- Dos columnas "DRIVER": una numérica (número) y otra con nombre. Clasificar por contenido (>60% numérico).
- Filas DUPLICADAS (ej. 09-08 todo x2) → deduplicar por (fecha, nombre, drv, miles, tripid).
- Columnas/notas extra con INSTRUCCIONES: `DUPLICADO. FACTURAR VEHICULO 2..`, `VEHICULO 309 PERFIL MARIELKIS`,
  `FACTURAR PERFIL DAYLENIS`, `Facturación manual. Driver Marielkis, auto 309`, `Facturar manualmente.`, `Facturado.`
  → parsear `auto\s*(\d+)` para driver; mostrar estas notas en el reporte.
- `PAYER` mezcla: Alivi / SafeRide / ModivCare / **MTM** → SOLO MTM va al portal (regla del usuario).
- `LOS`: AMB / WCH (no afecta el claim).

### 5.2 Claim (portal)
- `Appt. Date` puede ser TEXTO `10/15/2026` o fecha real de Excel (ambos vistos). Normalizar para joins.
- Claim files antiguos (09-01/02/04/10) tienen OTRO header (sin Driver/Milage) → en tests solo se usan los que tienen el header NEW/OLD estándar.

### 5.3 Archivos de viajes (tipo `10-05.xlsx`) — PU Time
- Nombre arbitrario — detectar por estructura: header con `Trip Number`, `Appointment Date`, `Time`, `Trip Mileage`, `Trip Cost`, `Member's First Name`, `Member's Last Name`, `Medicaid Number` (41 columnas en total).
- `Time` puede ser hora (`07:45 AM`, formato AM/PM) o el TEXTO `Will Call`.
- Match al claim por `Trip Number` exacto (+ validar nombre del miembro).

### 5.4 Informacion de Drivers.xlsx
- Hoja `Vehiculos`: `DRIVER|COUNTY|LICENSE NUMBER|VIN Number|CURRENT VEHICLE|VEHICLE PLATE|NUMERO`.
  `NUMERO` = número de driver del portal. Filas duplicadas con NUMERO 999 y placeholders `-` (sin vehículo) → elegir fila con licencia/VIN real. Hay más hojas (Direcciones/Correos) — ignorar.
- Números de driver conocidos: 10 Monica, 20 Dixon, 30 Juan, 166 Andrew, 200 Jorge, 220 Jeimy, 281 Felix, 309 Marielkis, 349 Daylenis, 392 Antonio, 394 Maritza/Wilber, 413 Carmen N, 415 Mairen, 999 varios.

### 5.5 Nombres de archivo (trampa clave)
- Acentos en NFC **y** NFD (ej. `FACTURACIÓN` con Ó compuesta o decompuesta). NUNCA escribir rutas con acentos a mano — descubrir por glob (`RESUMEN*.xlsx`) o por estructura.
- Variantes de nombre: `RESUMEN FACTURACION`, `RESUMEN FACTURACIÓN`, `... DE ...`, `... MTM`, `(1)`, `Original`.

### 5.6 BULK UPLOAD (v3, ver §17)
- Hoja `Export Trip`: `TripNumber|Driver(=License)|Vehicle(=VIN)|ScheduledPickupTime|ReportedPickupArriveTime|ReportedPickupPerformTime|ScheduledDropoffTime|ReportedDropoffArriveTime|ReportedDropoffPerformTime|TripLogSignature(=Y)`.
- El **Training** (`RESPALDOS\BULK UPLOAD Training.xlsx`) documenta cada columna en la fila 2 (¡fuente de verdad!):
  Driver = **licencia** del driver · Vehicle = **VIN** · ScheduledDropoffTime = **hora de la cita médica en MTM**.
- Filled examples (sept/oct) en `C:\Users\Fely\Downloads\Facturacion\RESPALDOS\Trips\Listos\...\BULK UPLOAD*.xlsx`;
  plantillas vacías (con fórmulas) en `...\1. PARA FACTURAR\10-0X\BULK UPLOAD.xlsx` (idénticas).

---

## 6. Reglas de matching y relleno

1. **Driver + Milage ← RESUMEN MTM del día del claim, match por (nombre completo, fecha).**
   - Nombre = `NAME + " " + LAST NAME` (o NAME sola) en MAYÚSCULAS, espacios normalizados.
2. **Si el RESUMEN trae TRIP ID poblado** → match EXACTO por Trip Number (verificado 23/23). Prioridad máxima.
3. **Pares 0A/0B (día con 2 filas resumen):** estrategias (`strategy` en el código):
   - **`first_row_B` (DEFAULT desde 18-oct):** **un driver por pata**, cada uno tomado de su fila del resumen
     (1ª fila → 0B, 2ª fila → 0A). Es lo que el usuario pidió: "normalmente un miembro puede tener un driver por
     pata"; así se reparten mejor los viajes y no se repite el mismo driver en ambas patas del cliente.
   - **`pair` (OPCIÓN, ya no default):** el **MISMO driver en ambas patas**, tomado de la 1ª fila del resumen.
     Se elige en la UI ("Mismo driver en ambas") o con `--strategy pair`.
   - **`first_row_A`:** igual que `first_row_B` pero invertido (1ª fila → 0A). `--strategy first_row_A`.
   - **`spread`:** solo aplica con `pair`: si DOS o más miembros comparten los mismos candidatos, se reparte.
     Desactivar con `--no-spread` o la casilla.
   - Si hay una nota **"auto N"** en una fila, N es el driver de **ESA pata** (antes, con `pair`, era el de AMBAS).
   - **Milage por pata: SIEMPRE `first_row_B`** (2ª fila del resumen → 0A). Verificado contra el doc del usuario
     **13/15 pares** (EVELYN 10-06 fue una suposición suya; el usuario confirmó que la pata no es una regla fija).
     El archivo de viajes trae `Trip Mileage` exacto por Trip Number, pero con valores DISTINTOS (es el recorrido
     real, no el facturado) → **NO se usa**; el orden del resumen es el mejor estimador.
   - **Self-test sept:** `first_row_B` 65.7% vs `pair` 57.1% → por eso `first_row_B` es el default.
4. **PU Time ← archivo de viajes del día por Trip Number — pero ES UN CÁLCULO, no un copiar.**
   - **OJO (17-oct):** la col `Time` del archivo de viajes es la hora de **CITA / DROPOFF**, NO la recogida.
   - **Fórmula real (verificada en `tests/test_pickup.py`):** `dropoff = cita − 1..5 min` y
     `PU = dropoff − (14 min + 1.4 × millas ± 3 min)`. Es el mismo ajuste calibrado con un margen
     pequeño para que el DropOff quede antes de la cita; el PU sale 1–5 min antes de la fórmula de
     una sola línea. Ejemplo fijado: 5.67 mi y cita 10:00 → DropOff 09:56, PU 09:34.
   - Parámetros: `pickup_ratio=1.4`, `pickup_buffer=14`, `pickup_jitter=3` (CLI `--ratio`, `--buffer`).
   - **Will Call** (= pata B): `PU = cita de la pata A + 2 h − (1..3 min)`. (No traen hora de cita propia.)
   - Si no aparece el archivo de viajes o el trip → dejar PU Time VACÍO y listarlo en el reporte.
5. **License/VIN ← drivers por número de driver** (cuidado con NaN / placeholders). Verificado 46/46 = 100% en self-test.
   - **Regla de aprobación (ACTUALIZADA 18-oct):** un número del resumen que NO existe en `Informacion de Drivers.xlsx`
     (ej. 392 "Antonio", 297 — **fueron removidos del listado recientemente**) se **REEMPLAZA por un driver libre de
     ese día** (el menos ocupado, vía el flujo de sugerencia) y la fila queda `sugerido` (lila) para confirmar.
     Ya NO se deja en blanco. Verificado con prueba: 392 → 10 (libre ese día) + License/VIN + flag `sugerido`.
     - **✅ IMPLEMENTADO (18-oct):** con la **carpeta de driverlogs** (`--driverlogs` / caja "Paso 4" en la UI), un driver
       de la lista pero **SIN plantilla** (`<NUM> ...DRIVERLOG VACIO.docx`) también es no facturable → se reemplaza por
       un driver libre que SÍ tenga plantilla. `drivers["allowed"]` = lista ∩ plantillas. Verificado: 413/415/999 quedan
       fuera; en el batch solo se usan `10, 20, 166, 200, 220, 309, 349, 394`.
   - **Nota "auto N"** (ej. "Driver Daylenis, auto 349."): si N está aprobado, se USA N en vez del número del resumen
     (+ se lista en el reporte). En oct 2026 los resúmenes traen "Facturar manualmente. Driver X, auto N." → el app
     los respeta (18 filas así en el batch 10-05..10-15).
6. **Dalia / viajes que vienen del portal pero SIN fila MTM en el resumen — REGLAS FINALES (17-oct):**
   - **Solo se factura lo que viene en el CLAIM del portal.** Si Dalia NO aparece en el claim ese día, no se factura
     aunque esté en el resumen (con o sin SafeRide). El app ya procesa sólo las filas del claim.
   - **Las filas SafeRide/Alivi de Dalia se IGNORAN por completo** — no son fuente de driver, no cuentan como
     viajes de ningún driver. (Regla del usuario.)
   - **Milage y PU Time:** salen del **archivo de viajes del día** (`Trip Mileage`/`Time`), por Trip Number exacto
     (0A = 7.06, 0B = 7.05). NO del resumen. Confirmado contra los claims terminados de sept y los trip files de oct.
   - **Driver: el app SUGIERE y el usuario confirma.** Sugiere el **driver menos ocupado de ese día** (menor número
     de viajes en el resumen del día, contando cualquier payer pero ignorando las filas SafeRide de Dalia; los 999
     placeholder quedan fuera). Se rellena Driver+License+VIN y la fila queda marcada **`sugerido`** (lila) para que
     el usuario la confirme o cambie en la pestaña **"Asignar driver"**. Si no hay resumen de ese día, NO se sugiere.
     - Opción `--no-suggest` (CLI) o desmarcar la casilla en la UI → deja las filas en blanco para elegir a mano.
     - **Excepción Dalia:** se prefiere SIEMPRE el driver **349** (Daylenis) — es lo que usa el usuario en 10-05/06/07.
       Configurable en `PREFERRED_DRIVER` (`app/filler.py`).
   - Los días 10-14/10-15 el resumen SÍ trae filas MTM de Dalia con nota "auto 309" → se respeta la nota (309), no
     entra en el flujo de sugerencia.
   - **Reglas de "no facturar" (17-oct):**
     - Claim row **sin fila MTM en el resumen y que NO es Dalia** → **NO se factura**. Se marca `nofacturar`
       (gris) y sale en el reporte. Sólo **Dalia Alfonso** es la excepción (se factura aunque no esté en el resumen).
     - Fila **MTM en el resumen que NO está en el claim** → **NO se factura**; se lista como aviso
       ("está en el resumen pero no en el claim").
     - `Cost` = OLD `Provider Cost` (texto con `$`). `Milage` = resumen del día (`MILES`/`MILEAGE`); si no hay fila
       MTM, del archivo de viajes. Encabezado tal cual: `Milage`.
   - Ejemplo oct: sugeridos → 10-05: 349 (libre) · 10-06: 349 (2 viajes) · 10-07: 349 (5) · 10-08: 349 (2) ·
     10-09: 349 (4) · 10-12: 394 (libre) · 10-13: 394 (libre). Mateo 10-13 (claim sin resumen, no es Dalia) → NO FACTURAR.
     - **Regla del usuario (18-oct):** para Dalia se prefiere un driver **SIN viajes ese día**; si 349 (su habitual)
       también está libre, gana 349. Implementado en el ranking `(libre?, es_349?, nº viajes, número)`.
7. **Regla de CONDADO (county) — 18-oct.** Los drivers SOLO hacen viajes de su condado (sería raro que un driver
   trabaje en otra área). En `Informacion de Drivers.xlsx` col `COUNTY`:
   **VOLUSIA = {20 Dixon, 30 Juan, 166 Andrew, 413 Carmen N}**; el resto = **MARION** (10, 200, 220, 281, 309, 349,
   394, 415, 999). Los de Volusia comparten viajes **entre ellos** pero nunca con los de Marion.
   - El condado del viaje = el condado del **driver del resumen** de esa fila; si no hay (Dalia), el de la **otra pata**
     del mismo miembro; si no, el de la **ciudad del pickup** del archivo de viajes (`DELAND`/`DAYTONA`… → VOLUSIA,
     resto → MARION).
   - Afecta a los **reemplazos/sugerencias**: 392/297 (removidos) o sin plantilla → se busca un libre DEL MISMO CONDADO.
   - `app/filler.py`: `VOLUSIA_CITIES`, `_city_county()`, `row["county"]`; `parse_drivers` ahora guarda `county`,
     `parse_trips` guarda `city`. `driver_candidates` está indexado por `(fecha, condado)`.

---

## 7. Job actual del usuario (batch `ClaimInformation 10-05 A 10-15`)

- 81 filas de claim; fuentes en **`data/base/`** (subcarpetas `10-05`…`10-15` con su RESUMEN; trips files
  `10-05.xlsx`…`10-15.xlsx`; `Informacion de Drivers.xlsx`).
- Cobertura (al 17-oct, con 9 resúmenes + 2 trip files): 66 filas con datos de resumen (18 vía nota "auto N"),
  **15 filas "sin driver → elegir"** (14 Dalia 10-05..10-13 + Mateo 10-13). Dalia 10-05/10-06 ya reciben Milage+PU
  del trip file. 10-09 quedó lleno (nota auto 309) al incluirse su resumen.
- PU Time: 24 llenas (5 Will Call) con 10-05/10-06; el resto vacío hasta tener sus trip files.
- ⚠️ **OJO 18-oct — FALTAN LOS TRIP FILES EN SU CARPETA (causa de "sin horas"):** el usuario movió los
  `10-XX.xlsx` fuera de `1. PARA FACTURAR`; en `Downloads\Facturacion` **ya no hay trip files** (solo quedan en
  `data/base/`). Al correr el app contra una carpeta sin trip files, el claim sale **sin PU/DropOff** y **Dalia sin
  Milage**; los driverlogs copian eso. **No es bug del generador.** → Los trip files DEBEN estar en la carpeta de
  fuentes. (El usuario tiene una carpeta `1. PRUEBA` con la estructura de días + los .docx generados, sin trip files.)
- Fechas batch: 10-05 a 10-15 (sin fines de semana).

---

## 8. Especificación de construcción (v1 del app)

- **UI:** app de escritorio Tkinter, empaquetada con PyInstaller en un solo `.exe` (windowed, sin consola). Confirmado por el usuario.
  Flujo: [1] elegir claim OLD (.xlsx) → [2] elegir carpeta(s) con los demás archivos (detección automática por ESTRUCTURA, no por nombre) → [3] botón `Procesar` → [4] tabla de vista previa (verde=rellenado, ámbar=ambiguo/dudoso, rojo=vacío/error) + listado de advertencias → [5] botón `Exportar Excel` (escribe el archivo final) + botón `Guardar reporte` (CSV).
  Idioma de la UI: simple, español o inglés neutro corto (decidir al construir; el usuario usa ambos).
- **Arquitectura REAL construida (paquete `app/`):**
  - `app/common.py` — helpers (normalización de nombres/números/fechas/horas).
  - `app/parsers.py` — `classify()` (reconoce por ESTRUCTURA) + parse_claim / parse_resumen / parse_trips / parse_drivers.
  - `app/filler.py` — reglas de la sección 6 (estrategia de pares, delta Will Call, aprobación de drivers, notas).
  - `app/pipeline.py` — orquesta todo: scan de carpeta → índices → fill → resultado.
  - `app/report.py` — texto de reporte + CSV.
  - `app/writer.py` — salida EXACTA: **una hoja por día** (`MM-DD`), orden de columnas del NEW, tipos de celda y formatos (sección 4).
  - `app/driverlogs.py` — **v2**: llena los driverlogs `.docx` (python-docx) y los guarda en `<día>\Docs\` (§15).
  - `app/ui.py` — Tkinter (vista previa coloreada + reporte + exportar).
  - `run_app.py` — entrada: GUI sin args; CLI con `--cli <claim> <carpeta> [--out x.xlsx] [--strategy ...]`.
  - `selftest.py` — test contra claims terminados (sección 9).
- **Formato de salida obligatorio:** ver sección 4 (tipos de celda incluidos). Cost = texto `$x.xx`; PU Time = hora real `h:mm`; Driver numérico.
- **Reporte (siempre, en pantalla y exportable):** filas sin resumen; pares ambiguos con lo asignado; Will Call calculados; notas detectadas; días sin archivo de viajes; trip numbers no encontrados; filas duplicadas ignoradas; número de drivers balance check NO (no existe regla dura).
- **NO tocar nunca los archivos originales.** Salida = archivo nuevo, nunca sobreescribir el OLD.
- **Idempotente:** correr 2 veces el mismo batch produce el mismo output (sin duplicar).

---

## 9. Self-test contra datos terminados — HECHO ✅

Corrido con `selftest.py` (raíz del proyecto) sobre 7 claims terminados de sept (70 filas evaluables):

| estrategia | exacto | sobre asignables | revisar | sin_dato | driver_mal | miles_mal | ambos_mal |
|---|---|---|---|---|---|---|---|
| first_row_A | 27 (38.6%) | 48.2% | 8 | 6 | 2 | 10 | 17 |
| **first_row_B** | **46 (65.7%)** | **82.1%** | 8 | 6 | 1 | 3 | 6 |

- **License/VIN: 46/46 = 100%** en filas con driver acertado.
- fill: id_matched=24, por orden=40, flagged=8, note_overrides=9.
- Los desaciertos restantes son TODOS decisiones humanas: pares invertidos según el día (Eric 09-21, Laura 09-22, Lisa 09-24),
  reasignaciones 392/394→10/281 (Elena, Margaret, Brenda, Juan) — todos salen en el reporte para revisión.
- PU Time no testeable en sept (no hay trip files de sept). Probado manualmente en el batch de octubre (sección 12).
- **Conclusión: default `first_row_B`**; opción `first_row_A` disponible en la UI.

## 10. Pendientes / preguntas abiertas
1. ✅ **DALIA resuelto (17-oct)** — ver sección 6.6. El app **sugiere** el driver menos ocupado (lila) y el usuario lo
   **confirma o cambia** en "Asignar driver" (14 viajes 10-05..10-13 + Mateo 10-13). Milage+PU ya se llenan solos.
2. Significado exacto de "Separar viajes de MTM (Z) con ACCESS2CARE (M)" (paso 2 del training).
3. ✅ Archivos de viajes por día: al 17-oct llegaron **todos** (`10-05.xlsx`…`10-15.xlsx`) en `data/base/`.
   PU Time quedó **81/81**. El app los detecta por estructura aunque cambie el nombre.
4. ✅ Resuelto: default 0A/0B = first_row_B (evidencia self-test). Avisar al usuario — si prefiere A, se cambia con un clic.
5. Preguntar: cuando el resumen trae un número no aprobado (392/297), ¿alguna regla de reasignación preferida?
   (v1: sugiere el menos ocupado + reporte).
6. **Mateo 10-09 / 10-13 y Vicente 10-09**: aparecen en el claim sin fila MTM. 10-09 se llenó (nota auto 309);
   Mateo 10-13 recibe driver sugerido. Confirmar con el usuario si Mateo se trata igual que Dalia.
7. **Distribución de sugerencias**: hoy se sugiere el MISMO driver para todas las filas sin MTM de un día
   (p. ej. Dalia y Mateo 10-13 → ambos 394). Confirmar si se prefiere repartir entre los menos ocupados.
8. **Milage por pata (A/B)**: el resumen no trae Trip Number → la asignación de millas a cada pata es una
   suposición. El archivo de viajes SÍ trae `Trip Mileage` exacto por Trip Number (pero con valores algo
   distintos a los del resumen; el resumen es el que se factura). Pendiente decidir si usar el archivo de viajes
   para *decidir cuál fila del resumen va a A y cuál a B* (por rango de millas). Preguntar al usuario.

## 11. Inventario de datos de referencia rápida (rutas del PROYECTO)
- Claim terminado ejemplo: `data/test/reference/ClaimInformation 09-22 FINISHED EXAMPLE.xlsx` (8 viajes) — = copia del de `data/test/Trips/Listos/09-22-2026/`.
- RESUMENes: `data/base/10-0X/` (oct) y `data/test/Trips/Resumenes/` + carpetas Listos (sep).
- Oct OLD/NEW: `data/base/ClaimInformation 10-05 A 10-15 OLD.xlsx` y `... NEW.xlsx`.
- **"MANUALLY MADE"**: `data/base/ClaimInformation 10-05 a 10-15 MANUALLY MADE.xlsx` — plantilla del usuario (a 17-oct aún SIN rellenar; se comparará con `recon/compare_key.py` cuando la llene).
- Trip file ejemplo: `data/base/10-05.xlsx` y `10-06.xlsx` (estructura de 41 columnas, `Trip Mileage`, `Time`).
- Drivers: `data/base/Informacion de Drivers.xlsx`.
- Driverlog PDFs (no relevantes v1) en `Docs\` de cada día (NO copiados al proyecto).

## 12. Estado de construcción (v1 — HECHO y probado)
- Código completo en `app/` + entradas `run_app.py` (GUI) / `run_app.py --cli ...` + `selftest.py`.
- **Novedades 17-oct (v1.2) — caso Dalia + sugerencia de driver:**
  - `app/filler.py`: **fallback de Milage** desde el archivo de viajes (`Trip Mileage`) cuando el resumen no trae
    fila MTM; **sugerencia de driver** = el **menos ocupado del día** (menor nº de viajes en el resumen, ignorando
    SafeRide de Dalia, excluyendo 999). Parámetro `suggest_driver` (default True); sin resumen de ese día NO sugiere.
  - `app/pipeline.py`: `driver_usage` por día con **conteo** de viajes por driver (cualquier payer, menos SafeRide de Dalia).
  - `app/report.py`: sección **"DRIVER SUGERIDO - CONFIRMAR"** + "SIN DRIVER - ELEGIR UNO" con opciones y su nº de viajes.
  - `app/ui.py`: pestaña **"Asignar driver"** (lista los sugeridos y los vacíos; combobox con el nº de viajes de cada
    opción; confirma → quita el flag). Estados **SUGERIDO** (lila) y **ELEGIR** (azul); casilla "Sugerir driver".
  - CLI: `--no-suggest` para dejar los drivers en blanco.
  - Verificado: `recon/test_ui.py` confirma una sugerencia, rellena License/VIN, la quita de la lista y exporta OK.
- **Dry-run del batch 10-05..10-15 (81 filas, 9 resúmenes + 9 trip files):** salida
  `output\ClaimInformation 10-05 a 10-15 FILLED.xlsx` + reporte `output\dryrun_october.txt`.
  - 66 filas con datos de resumen (18 vía nota "auto N"); **14 con driver SUGERIDO** (Dalia 10-05..10-13) y
    **1 marcada NO FACTURAR** (Mateo 10-13: claim sin resumen y no es Dalia). Aviso "resumen sin claim": ninguno en este batch.
  - Milage desde archivo de viajes: 15 filas (toda la Dalia sin MTM + Mateo 10-13). **PU Time: 81/81 (18 Will Call).**
  - Auditoría de tipos: **0 problemas** (Driver int, PU `h:mm`, Milage numérico, Cost `$x.xx`, resto texto). 9 columnas.
- **Self-test sept re-corrido: sin cambios** → first_row_B 46/70 exacto (65.7%), 82.1% sobre asignables,
  License/VIN 46/46. (ver `output\selftest_v2.txt`).
- **¡OJO en esta máquina!** Poca RAM libre y `import openpyxl` carga numpy → OpenBLAS revienta con
  "Memory allocation failed". Solución aplicada en `app/__init__.py` y `run_app.py`: `OPENBLAS_NUM_THREADS=1` y
  `OMP_NUM_THREADS=1` ANTES de los imports. **No correr varios scripts Python en paralelo** (provoca MemoryError).
- **PU Time ESTIMADO (17-oct)**: la hora del archivo de viajes es la CITA/dropoff; el PU se calcula
  `cita − (14 + 1.4×millas) ± 3 min` (ver §6.4). Calibración en `docs/PU_TIME_FINDINGS.md`.
- UI Tkinter: cabecera con título + **un botón de idioma** (bandera VE/USA) y **un botón de tema** (sol/luna)
  a la derecha. **Modo oscuro por defecto**; paletas pastel claro/oscuro. Fuentes Segoe UI Semibold 11,
  DPI-aware (nítido en escalado de Windows). Pestañas Vista previa, Reporte, Asignar driver; botón
  "¿Qué archivos necesito?". Español por defecto.
- **Salida = UNA HOJA POR DÍA** (`10-05`, `10-06`, …), nombre de hoja `MM-DD`, con las 9 columnas exactas.
  Confirmado contra el archivo del usuario "MANUALLY MADE GROUPED BUT NOT FILLED YET". Dentro de cada día se respeta
  el orden del claim. `--keep-order` en CLI desactiva el orden por día; `write_output(..., per_day=False)` da una
  sola hoja `ClaimInformation`.
- **UI bilingüe** (17-oct): español por defecto, toggle con banderas VE/USA arriba a la derecha (dibujadas en Canvas,
  sin imágenes). DPI-aware + fuentes Segoe UI. Botón "¿Qué archivos necesito?" con instrucciones explícitas.
- **.exe (v1.3)**: copia lista para usar en la **raíz** → `Facturacion MTM.exe` (el build queda en `dist\`).
  Verificado contra el motor Python: **0 diferencias celda a celda**.
  Nota: al lanzar el exe por CLI desde PowerShell usar `Start-Process -Wait` con las rutas entre comillas
  (un `-ArgumentList` con array rompe las rutas con espacios → sale con código 2).
- **Pendiente:** que el usuario **revise/confirme los drivers sugeridos** y, cuando llene su
  `ClaimInformation 10-05 a 10-15 MANUALLY MADE *.xlsx` (separado por día), comparar con `recon/compare_key.py`.

### 12.1 Novedades 18-oct (v2.1)
- La app abre **MAXIMIZADA** (`root.state("zoomed")` en `app/ui.py → main()`), no en ventana.
- **Aviso "sin archivos de viajes"** con **Proceed/Cancel** antes de procesar: si la carpeta de fuentes no tiene
  trip files (`10-XX.xlsx`), avisa que PU/DropOff/Milage de Dalia quedarán vacíos. (Sin trip files no hay horas.)
- **Chequeo de tiempos A/B:** para cada miembro/día, si la pata **B** tiene PU o DropOff **antes** que la **A**, se
  agrega un warning al reporte (`Aviso de tiempos`) y la fila B queda en `revisar`. (En el batch de octubre: 0 avisos.)
- **Portabilidad VERIFICADA** → `docs/PORTABILITY.md`. El `.exe` es **one-file, standalone, Windows 10+ x64**, sin
  Python ni DLLs que instalar; incluye `python314.dll`, openpyxl, python-docx, lxml (+`.pyd`) y `VCRUNTIME140`.
  Se probó copiando SOLO el exe a una carpeta temporal: Excel + 29 driverlogs OK (exit 0).
  Caveats: sin firma → SmartScreen "Unknown publisher"; sin icono/version info; build windowed → no imprime stdout.
- **Datos sincronizados:** el usuario actualizó los **RESÚMENES** (8 de 9 días distintos a los copiados); se
  copiaron los actuales a `data/base/` (junto con los trip files). Comparación 10-05..10-07 sigue **26 OK / 8 DIFF**
  (solo las diferencias aceptadas: milla de Dalia y el swap de EVELYN).

## 13. Repositorio Git

- Remote: `https://github.com/jfelya/facturacion-mtm.git` (rama `main`). Ya inicializado y **pusheado**.
- **Solo se versiona lo necesario para correr el app**: `app/`, `run_app.py`, `Facturacion MTM.spec`, `README.md`,
  `requirements.txt`, `.gitignore`.
- **Gitignored (contexto/investigación/datos):** `data/`, `docs/`, `recon/`, `selftest.py`, `output/`, `build/`,
  `dist/`, `*.exe`, `__pycache__/`.
- Para subir cambios: `git add -A && git commit -m "..." && git push`.

## 14. Comparación contra el doc del usuario (10-05..10-07) — 17-oct

El usuario llenó `data/base/ClaimInformation 10-05 a 10-15 MANUALLY MADE.xlsx` para 10-05, 10-06 y 10-07
(Driver + Milage + Cost; PU Time y License/VIN los pone el app). Comparado con `recon/compare_filled.py`:

- **Driver: 28/28 filas** iguales (estrategia `pair` + `spread` + preferencia Dalia→349). El "balance" LINDA/JANET
  ya se automatizó con `spread` (LINDA→394, JANET→220).
- **Milage: 13/15 pares** con la pata correcta (`first_row_B`). Única diferencia: **EVELYN 10-06** (usuario A=5.03/B=4.85,
  app A=4.85/B=5.03) — el usuario confirmó que la pata A/B "no es una regla fija, a veces adivino".
- **Dalia:** el usuario usa **driver 349** siempre (implementado como preferencia) y la milla = 7, pero **confirmó
  que se quede el valor del trip file (7.05/7.06)**. Los 6 "diffs" de Dalia son solo por eso.
- **PU/DropOff:** el usuario NO los llena a mano (los deja al app). No comparables todavía.
- **Cost:** coincide 100% (viene del `Provider Cost` del claim).

---

## 15. FEATURE v2: llenar los DRIVERLOGS de Word — ✅ CONSTRUIDO (18-oct)

> Estado: **CONSTRUIDO y verificado**. Código en `app/driverlogs.py` (usa `python-docx`).
> UI: botón "Generar driverlogs (.docx)". CLI: `--gen-driverlogs --driverlogs <plantillas> --days-root <raíz>`.
> Verificación: los 4 driverlogs de `10-05` (200/220/309/349) salen **idénticos (0 diffs)** a los que hizo el usuario
> a mano; 27 driverlogs en los 9 días; el `.exe` (17.6 MB) hace lo mismo que el motor.
> Detalles en §15.1–§15.7; decisiones del usuario en §15.8.

### 15.1 LO ÚNICO YA HECHO (18-oct): orden por driver en el claim final
- Cada hoja (día) del ClaimInformation exportado ahora se ordena **por NÚMERO de driver ascendente**.
  Implementado en `app/pipeline.py` (`_sort_key`): clave `(fecha, int(driver), fila_OLD)`; sin driver → al final.
- Verificado: 10-05 → `[200,200,220,220,309,309,349,349]`; el `.exe` = motor (**0 diffs**). El `.exe` fue reconstruido.

### 15.2 Objetivo
Tras exportar el ClaimInformation final, **rellenar los driverlogs de Word** (uno por driver que trabajó ese día)
con los viajes de ese driver, y guardarlos en la carpeta `Docs` de cada día.

### 15.3 Entradas necesarias
1. **El claim final** (filas ya rellenadas). Ya están en memoria en `claim["rows"]` con:
   `date` (ISO), `date_text` (MM/DD/YYYY), `driver`, `trip`, `member`, `pu`, `dropoff`, `milage`, `cost`.
2. **Carpeta de PLANTILLAS de driverlogs** (nueva caja en la UI, la elige el usuario).
   En su máquina: `C:\Users\Fely\Downloads\Facturacion\MTM Driverlogs\`
   - Un archivo por driver: **`<NUM> <NOMBRE> DRIVERLOG VACIO.docx`** (ej. `200 JORGE NINO DRIVERLOG VACIO.docx`,
     `220 JEIMY DELGADO RIVERLOG VACIO.docx`). Hay ~13 plantillas (10, 20, 30, 166, 200, 220, 281, 297, 309, 349, 392, 394, + MARINES PENA).
   - La plantilla YA trae pre-rellenados **DRIVER'S NAME** y **VEHICLE NUMBER (VIN)** del driver.
   - ⚠️ Las plantillas "VACIO" traen **1 fila de datos con basura de un uso anterior**
     (ej. 200 → `09/11/2026 · M4BLTJ4ON0A · LISA HALSEY · 8:25`; 10 → `09/16/2026 · M4CR92OT80A · AGUSTIN GUASTAVINO · 5:10`).
     → El app debe **limpiar las filas de datos** antes de rellenar.
3. **Carpeta raíz de los días** (donde viven `10-05`, `10-06`, …): `...\1. PARA FACTURAR\`
   (nueva caja, o derivada de la carpeta de fuentes que ya se elige).

### 15.4 Salida y carpetas
- Ruta: **`<raíz>\<día>\Docs\<MM-DD-YYYY> <NUM>.docx`**
  (ej. `...\1. PARA FACTURAR\10-05\Docs\10-05-2026 200.docx`).
  - Evidencia real: `RESPALDOS\Trips\Listos\FACTURACION 09-02-2026\Docs\09-02-2026 200.docx` (y `... 10/220/281/297/30/392/394.docx`).
  - ✅ **Nombre CONFIRMADO (18-oct) con los archivos reales del usuario:** en `...\1. PARA FACTURAR\10-05\Docs\`
    hay **`10-05 200.docx`, `10-05 220.docx`, `10-05 309.docx`, `10-05 349.docx`** → patrón **`<día> <NUM>.docx`**
    (el día de la carpeta + número de driver). Usar ese formato (los de septiembre usaban `09-02-2026 <NUM>.docx`).
- **Crear** la carpeta del día y su `Docs` si no existen (`<día>` + `Docs`). Los `Docs` de `10-05`…`10-15` YA existen y están **vacíos**.
- Días a generar = los días del claim final (las hojas del export).
- **Un driverlog por cada número de driver distinto** de ese día.

### 15.5 Estructura del .docx (1 tabla, 15 filas: 1 cabecera + 14 datos)
- Encabezado (NO tocar): `DISMA TRANSPORTATION` / `PROVIDER'S NAME` / `WEEK ENDING` / `DRIVER'S NAME` / `VEHICLE NUMBER` / `DRIVER SIGNATURE`.
- Columnas: `Date of Service | Trip number | Recipient's Name | PickUp Time | DropOff Time | Milleage | Per Trip Bill Amount | Recipient's Signature`
- Cada fila de datos = un viaje del driver ese día (tomado del claim final):

  | Celda del driverlog | Campo del claim |
  |---|---|
  | Date of Service | `Appt. Date` (MM/DD/YYYY) |
  | Trip number | `Trip Number` |
  | Recipient's Name | `Member Info` |
  | PickUp Time | `PU Time` (texto `h:mm` sin cero a la izquierda: `7:58`) |
  | DropOff Time | `DropOff Time` |
  | Milleage | `Milage` |
  | Per Trip Bill Amount | `Cost` (`$15.00`) |
  | Recipient's Signature | vacío |

- **"El resto del driverlog debe quedar intacto"** → sólo se escriben las celdas de datos; nada más (ni estilos ni cabecera).
- Ejemplo real con varias filas: `...\FACTURACION 09-02-2026\Docs\09-02-2026 394.docx` (Brenda ×3 + Lisa).
- **✅ EJEMPLO REAL DEL USUARIO (18-oct):** `...\1. PARA FACTURAR\10-05\Docs\10-05 200.docx` (JORGE NINO) y
  `10-05 349.docx` (DAYLENIS MARRERO). Se verificó que los valores y el orden **coinciden exactamente** con la salida
  del app (ej. 200: `10/05/2026 · M4F32EG2N0B · LISA HALSEY · 10:49 · 11:09 · 5.67 · $15.00`). El usuario tomó los
  datos del FILLED. → El driverlog se llena **en el orden del claim (driver-sorted)**; los ejemplos viejos no seguían orden.

### 15.6 Implementación (HECHO)
- `app/driverlogs.py`: `scan_templates()` (número desde `<NUM> …docx`), `fill_doc()`, `generate_driverlogs()`, `report_lines()`.
- **`python-docx` 1.2.0** instalado; añadido a `requirements.txt` y al spec (`hiddenimports=['docx']`).
  El `.exe` pasó de 12.4 a **~17.6 MB** (por `lxml`).
- `fill_doc()`: abre la plantilla, **limpia las celdas 0..7 de cada fila de datos**, escribe los viajes y devuelve el
  Document; `generate_driverlogs()` guarda una **COPIA** en `<días>\<día>\Docs\<día> <NUM>.docx` (la plantilla NO se toca).
  Crea `<día>\Docs` si no existe. Si un driver no tiene plantilla → se omite (`skipped`).
- Verificado que el .docx generado **conserva** el logo (`word/media/image1.png`), estilos, tema y el encabezado
  (DISMA TRANSPORTATION / DRIVER'S NAME / VEHICLE NUMBER / DRIVER SIGNATURE). Solo cambian las filas de la tabla.
- UI: botón **"Generar driverlogs (.docx)"** (se habilita tras Procesar) + caja **"Paso 5 · Carpeta de días"**
  (si se deja vacía, usa la carpeta de fuentes). La 4ª caja (Paso 4) es la de plantillas.
- Verificación: **27 driverlogs en 9 días** (`10-05`…`10-15`); `10-05` (200/220/309/349) **0 diffs** vs el usuario.

### 15.7 UI (nueva parte)
- **Nueva caja**: "Carpeta de plantillas de driverlogs (.docx)" + botón *Elegir…* (bilingüe ES/EN).
- **Nueva caja** (o derivar de la carpeta de fuentes): "Carpeta raíz de días (1. PARA FACTURAR)".
- **Nuevo botón**: "Generar driverlogs" (habilitado después de Procesar; no requiere exportar el Excel).
- Reportar: driverlogs generados por día, **drivers sin plantilla**, días sin carpeta, etc.

### 15.8 RESPUESTAS DEL USUARIO (18-oct) — decisiones ya tomadas
1. **Nombre de salida:** `<día> <NUM>.docx`, ej. **`10-05-2026 200.docx`** (día del viaje/carpeta + número de driver).
   **Recipient's Signature queda vacía.**
2. **Orden de las filas:** no importa; **por hora de PU** está bien.
3. **Drivers no válidos:** los que no están en `Informacion de Drivers.xlsx` (o sin driverlog) se **reemplazan por un
   driver libre de ese día** — **YA HECHO** en el claim (flujo de sugerencia; ver §6.5). Probado: 392 → 10.
4. **Borrar las filas de las plantillas:** OK, siempre que no se toque nada más.
5. **>14 viajes/día:** imposible (2-6 viajes por driver). No hace falta añadir filas.
6. **Driver sin plantilla (ej. Marines):** **IGNORARLO** (no generarle driverlog).
7. **No sobreescribir las plantillas**; se exporta una **COPIA** rellenada a `<día>\Docs\`. Sí se puede sobreescribir
   lo que ya haya en `Docs` (normalmente vacío).
8. **El usuario llenará `10-05` a mano** como referencia en la próxima iteración, **antes** de construir.

### 15.9 Referencias reales (rutas fuera del proyecto — NO se copiaron)
- Plantillas: `C:\Users\Fely\Downloads\Facturacion\MTM Driverlogs\*.docx`
- Ejemplos llenos: `C:\Users\Fely\Downloads\Facturacion\RESPALDOS\Trips\Listos\FACTURACION 09-XX-2026\Docs\09-XX-2026 <num>.docx`
- Formato maestro: `C:\Users\Fely\Downloads\Facturacion\RESPALDOS\Copia de Copia de DRIVER LOG FORMAT 7.27.26  .docx` (tabla de 13 filas).
- Días de octubre con `Docs` vacío: `...\1. PARA FACTURAR\10-0X\Docs\`.
- El usuario **ofreció llenar un driverlog a mano** como referencia → **pedírselo**.

### 15.10 Fuera de alcance
- ~~**NO tocar el BULK UPLOAD**~~ → **ya NO está fuera de alcance** desde 18-oct: ver **§17** (el usuario pidió automatizarlo).

---

## 16. Empaquetado: icono, versión, firma y 32-bit

- **Icono (18-oct):** se usa la **marca de MTM** (los triángulos de colores). Fuente:
  `https://idp-ua.mtmlink.net/images/icon/favicon.png` (63×64, la marca sola) y
  `https://idp-ua.mtmlink.net/images/mtm_link.svg` (wordmark vectorial "MTM LINK").
  - `assets/icon.png` (1024×1024, transparente, centrado) y `assets/icon.ico` (16/24/32/48/64/128/256) ya están hechos;
    el spec usa `icon='assets/icon.ico'`. Origen: la marca se extrajo del SVG y se renderizó con Chrome headless.
  - Guardados también los originales: `assets/mtm_logo.svg` y `assets/mtm_favicon.png`.
  - Para reemplazar el icono: poner un PNG **cuadrado** en `assets/icon.png`, generar el `.ico` y reconstruir con
    PyInstaller. ⚠️ El script `recon/make_icon.py` se **borró** el 18-oct; si se cambia el icono, hay que regenerar el
    `.ico` (p.ej. con Pillow) o pedirlo.
- **Versión:** `version_info.txt` (2.3.0.0, CompanyName `Disma Transportation`, etc.). El spec lo embebe
  (`version='version_info.txt'`). Verificado con `(Get-Item exe).VersionInfo`.
- **Icono de la ventana:** `app/ui.py → _set_window_icon()` usa `assets/icon.png` (bundleado vía `datas` en el spec).
- **Tamaño:** **32-bit 15.8 MB** / **64-bit 17.7 MB**. Se **excluyó `PIL`/`Pillow`** del build (openpyxl la arrastraba opcionalmente; no se usa).
- **Firma (SmartScreen "Unknown publisher") — PENDIENTE / DESCARTADA por ahora (19-oct):** el `.exe` va **sin firmar**.
  - Se había probado un certificado autofirmado (Root CA + leaf, `CN=Disma Transportation`) e instaladores por PC, pero
    **el usuario decidió quitarlo y retomarlo "algún día"**. Se borraron `assets/codesign/` y los `.cer`/instaladores;
    los exes se **reconstruyeron sin firma** (`Get-AuthenticodeSignature` → `NotSigned`).
  - Lección por si se retoma: meter una CA en **Trusted Root** exige un "Sí" de Windows (no hay forma silenciosa:
    `Import-Certificate` falla con *"UI is not allowed"*; `CertAddEncodedCertificateToStore` también bloquea;
    `certutil -f` sigue preguntando). Un self-signed con EKU tiende a clasificarse en *Intermediate* y no valida;
    para uso interno haría falta **CA raíz (CA=TRUE, sin EKU) + leaf (EKU Code Signing)** y un instalador por usuario.
  - No existe certificado gratuito reconocido mundialmente para firmar código (público = **OV/EV** o
    **Azure Trusted Signing** ~US$10/mes). SmartScreen (reputación) puede salir igual en PCs nuevos.
  - Mientras tanto: *Más información → Ejecutar de todas formas* una vez por PC.
- **32-bit (HECHO, 18-oct):** el exe de la **raíz** es ahora **x86 (32-bit)** y corre en **Windows 10/11 de 32 y 64 bits**
  (build "universal"). Se construyó con **Python 3.14.6 32-bit portable** (zip oficial `python-3.14.6-win32.zip`,
  sin instalador) en `%TEMP%\opencode\py32\python`; `pip install --only-binary=:all: openpyxl python-docx pyinstaller`
  (lxml trae wheel `cp314-win32`); `python -m PyInstaller "Facturacion MTM.spec" --distpath dist32 --workpath build32`.
  - `Facturacion MTM.exe` (raíz) = **32-bit · 15.81 MB** · v2.3.0.0 (universal).
  - `dist32\Facturacion MTM.exe` = 32-bit (igual). `dist\Facturacion MTM.exe` = **64-bit · 17.73 MB** (reconstruido
    también con el código actual).
  - **Verificado:** copiando **solo** el exe a una carpeta temporal → exit 0, Excel + 9 BULK + driverlogs. Salidas
    **idénticas** al motor (Excel **0 diffs**, 9 BULK **0 diffs**). El techo de RAM de 32 bits (~2-4 GB) sobra para esta app.

## 17. FEATURE v3: BULK UPLOAD — ✅ CONSTRUIDO (18-oct)

> Estado: **CONSTRUIDO y verificado**. Código en `app/bulk.py`.
> UI: botón **"Generar BULK UPLOAD"** (se habilita tras Procesar). CLI: `--gen-bulk` (usa `--days-root` o la carpeta de fuentes).
> Salida: **`<días>\<MM-DD>\BULK UPLOAD <MM-DD-YYYY>.xlsx`** (un archivo por día).
> Verificación: la estructura (headers, relleno azul `FF0070C0`, anchos, `h:mm`, alineaciones, nº de filas) sale **idéntica a la plantilla**;
> las columnas A/B/C/D/J coinciden 100% con el `BULK UPLOAD 09-16-2026` del usuario (comparadas por TripNumber).

### 17.1 Mapeo de columnas (de `BULK UPLOAD Training.xlsx`, fila 2 — fuente de verdad)
| Col BULK | = Campo del claim final |
|---|---|
| `TripNumber` | `Trip Number` |
| `Driver` | **`License`** (¡no el número!) |
| `Vehicle` | **`VIN`** |
| `ScheduledPickupTime` | `PU Time` |
| `ScheduledDropoffTime` | **`pu_appt`** = `Time` del archivo de viajes (la cita, marcas de 15 min). En **Will Call** (no hay cita) = el **DropOff calculado** del claim (retorno). |
| `TripLogSignature` | `Y` (siempre) |
| `ReportedPickupArriveTime` | **simulado** (no está en el claim) |
| `ReportedPickupPerformTime` | **simulado** = arrive + 1 min |
| `ReportedDropoffArriveTime` | **simulado** |
| `ReportedDropoffPerformTime` | **simulado** = arrive (misma hora) |

### 17.2 Tiempos "Reported" (simulados, decisión del usuario 18-oct)
No existen en el ClaimInformation → el app los **inventa con jitter determinista** (misma clave `fecha|trip` → mismos
valores en cada corrida, así el output es **idempotente**):
`arrive_pu = PU − 1..5 min` (pata A) / `PU − 1..3 min` (pata **B**) · `perform_pu = arrive + 1 min` ·
`arrive_drop = ScheduledDrop − 1..3 min` (el dropoff programado es la **hora máxima**; se llega un par de minutos antes) ·
`perform_drop = arrive`.
**Reglas de seguridad:** (1) el dropoff nunca ocurre antes del pickup; (2) **una pata B nunca llega antes de que la pata A
haya dejado al miembro** (si choca, se empuja la llegada de B justo después del dropoff de A). Verificado: **0 choques**
en el batch 10-05..10-15.
`app/bulk.py → day_sims()` / `sim_times()`; `scheduled_dropoff()` detecta el Will Call porque `pu_appt` queda 1..3 min
después de `pu` (en un viaje normal queda ≥ ~12 min después).

### 17.3 Reglas de generación
- **Un archivo por día** con los viajes **facturables** de ese día (con driver y sin flag `nofacturar`); los demás se omiten y se cuentan.
- **Orden dentro del día** = el mismo del claim exportado (ordenado por **número de driver**).
- El formato se clona de la **plantilla bundleada** `app/assets/bulk_template.xlsx` (copia idéntica a la del usuario:
  `BULK UPLOAD.xlsx`, SHA256 `7762AF4A…741B`). Se **borran las filas sobrantes** ("borrar espacios en blanco") y
  se sobrescriben las fórmulas `F=E+1/1440` / `I=H` por **valores** (como el archivo real subido). La plantilla original NUNCA se toca.
  Añadida al `.spec` como `('app/assets/bulk_template.xlsx', 'app/assets')`.
- **Salida SOLO con valores planos: sin fórmulas.** Tanto el ClaimInformation (`writer.py`) como el BULK
  (`bulk.py → _flatten()`) barren cualquier fórmula; el BULK sobrescribe las `F=E+1/1440` / `I=H` de la plantilla con valores.
  Verificado: 39 archivos generados → **0 fórmulas**.
- Sale **carpeta del día** (`<días>\10-05\`) si no existe; el archivo nuevo NO reemplaza al `BULK UPLOAD.xlsx` vacío (queda al lado).

### 17.4 Qué falta / notas
- Si un día no tiene `PU`/`DropOff` (p.ej. sin archivo de viajes), esas celdas salen **vacías** (el app ya avisa antes de procesar).
- **Will Call (decisión 18-oct):** el `ScheduledDropoffTime` usa el **DropOff calculado** del claim (retorno), porque el
  `A+2h` del trip file es la **recogida** del regreso, no una cita; así los tiempos reportados quedan realistas.
- **Resúmenes en carpeta plana + formatos distintos:** VERIFICADO (9 resúmenes en `data/base/` sin subcarpetas, 7 layouts
  distintos → todos parseados, 0 errores; `PU 81/81`). El match por Trip ID solo aplica si la fila **MTM** trae el número
  del portal; si no, cae a nombre/fecha/orden. No requiere cambios.
- El usuario **aún no ha subido** un BULK de octubre para comparar 1:1 los tiempos simulados; ajustar el jitter si lo pide.
- Ejemplos llenos de referencia: `…\RESPALDOS\Trips\Listos\<MM-DD-YYYY>\BULK UPLOAD <MM-DD-YYYY>.xlsx`;
  plantillas vacías: `…\1. PARA FACTURAR\<MM-DD>\BULK UPLOAD.xlsx` (todas idénticas).
- **32-bit:** ver §16 (el exe de la raíz ya es 32-bit universal).

## 18. Notas sueltas (18-oct)

- **Los RESÚMENES del usuario cambian** (se actualizaron 8/9 días). Eso NO es un problema: la app usa los archivos que
  haya en la carpeta que se elija; `data/base/` es solo espejo para pruebas. Ya se sincronizaron.
- La comparación 10-05..10-07 (contra el doc del usuario) sigue **26 OK / 8 DIFF**, y las 8 son las aceptadas:
  milla de Dalia (7 vs 7.05/7.06) y el swap de EVELYN.
- El usuario **regresó los trip files** a `1. PARA FACTURAR` (los había movido a `1. PRUEBA`), así que las horas vuelven a salir.

## 19. Firma digital — DESCARTADA por ahora (19-oct)

- El usuario decidió **quitar todo lo del certificado** y retomarlo "algún día". Se borraron `assets/codesign/` y los
  `.cer`/instaladores; los exes se **reconstruyeron sin firma** (`NotSigned`).
- En este PC quedó **un registro inerte** del cert viejo en `Cert:\CurrentUser\CA` (Windows no deja borrarlo desde el
  proveedor de PowerShell; no afecta nada). No hay nada instalado en Root/TrustedPublisher.
- Para retomarlo: ver la lección en §16 (CA raíz + leaf + instalador por usuario; Root exige un "Sí" de Windows).

## 20. Ajustes 18-oct (v3.2) — pedidos tras la aprobación

- **Driver por pata por defecto:** el default pasó de `pair` a **`first_row_B`** (un driver por pata según el resumen).
  Motivo: el usuario notó "demasiados viajes en un mismo driver" y "mismo miembro en ambas patas". `pair` sigue como
  opción ("Mismo driver en ambas" en la UI / `--strategy pair`). Ver §6.3.
- **Textos de la UI:** se quitó lo de "Sube este archivo al portal MTM" del aviso al exportar (ahora solo dice
  "Archivo guardado…"). Revisar otros textos si aparecen raros.
- **Iconos de la UI:** las banderas VE/USA y sol/luna ahora son **PNG nítidos** (`assets/ui/ve.png`, `us.png`, `sun.png`,
  `moon.png`) generados con **Pillow** (supersampling + LANCZOS) por `assets/ui/make_icons.py`. Se cargan con
  `tk.PhotoImage` (con las formas de Canvas como fallback). Bundleados en el spec (`assets/ui`). Se quitó el texto
  "ES/EN" del botón de idioma (ahora solo la bandera).
- **Reparto suave (balancing):** `_balance_drivers()` en `filler.py`. Por día y **condado**, si un driver pasa de
  **`BALANCE_MAX = 3`** se mueven viajes (prefiriendo los **NO** fijados por nota) a drivers aprobados del **mismo
  condado** con menos de **`BALANCE_TARGET = 2`**. Las filas movidas quedan flag **`balanceado`** (color verde-agua) y
  salen en REVIEW como "REPARTO …". Regla **suave** (guía, no ley). UI: casilla **"Repartir viajes (≈2 por driver)"**;
  CLI `--no-balance`. Verificado: máximo **3 viajes/driver** (antes 5-6) y 14 filas reasignadas en el batch de octubre.

## 21. Sistema visual (19-oct) — portado de SelfishNet v2

- Fuente: `C:\Users\Fely\Documents\OpenCode\SelfishNet v2\VISUAL_DESIGN_SYSTEM.md` (WPF). Se portó **solo la parte
  visual** a Tkinter: paleta dark-first estilo GitHub, superficies planas, bordes de 1 px, acento azul, tipografía densa.
- **Tokens** (en `app/ui.py → THEMES`): `#14171B/#F3F5F7` fondo, `#1C2128/#FFFFFF` superficie, `#262C35/#ECEFF3`
  superficie alt, `#333B47/#D2D9E0` borde, `#E6EDF3/#1F2328` texto, `#9AA7B4/#5A6572` texto dim, `#4C8DFF/#0969DA`
  acento, `#3FB950/#1A7F37` éxito, `#F85149/#CF222E` peligro.
- **Tipografía:** base **13 px**; se usa la cara **"Segoe UI Semibold"** como base (Tk solo tiene normal/bold; imita el
  *Medium* del diseño y da el look "un poco más grueso"); énfasis en **bold**; `Consolas` para identificadores.
- **Componentes:** botón base = superficie + borde 1 px (hover acento), primario = relleno acento, tablas
  (`Treeview`) con encabezado `surface-alt` dim y filas de 30 px, selección = tinte (`sel`), barra de estado con
  **punto de estado** (gris/accento/verde/rojo), separadores de 1 px en toolbar y status.
- **Aproximación Tk:** no hay esquinas redondeadas ni sombras (el diseño usa radio 10/6/5 y sin sombras); se mantiene
  plano con bordes de 1 px. Los iconos de bandera/sol/luna ahora son `tk.Label(image=...)` (los `Canvas` con imagen no
  componían bien sobre el header ttk), PNGs en `assets/ui/`.
- **UI KIT (framework propio):** la capa visual vive en **`app/uikit/`** (fuente única de verdad):
  `tokens.py` (colores/status/tipografía/espaciado/métricas), `theme.py` (`make_fonts`, `apply_theme`, `tag_rows`,
  `THEMES`), `icons.py` (`asset_path`, `load_icon`), `widgets.py` (`hseparator`, `StatusDot`) y `README.md` con el
  contrato. `app/ui.py` ya solo consume el kit. Para apps nuevas: copiar `app/uikit/` y llamar
  `make_fonts()` + `apply_theme(root, "dark", fonts)` al inicio. Ver `app/uikit/README.md`.
- **Limpieza (19-oct):** se borraron `build/`, `build32/`, `dist/`, `dist32/` y todos los `__pycache__` (se regeneran
  al compilar). El proyecto pasó de ~116 MB a **~20 MB**. Se mantiene **un solo exe en la raíz** (se eliminó `Entrega/`).
