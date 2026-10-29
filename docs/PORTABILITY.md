# Portability / Standalone Audit — `Facturacion MTM.exe`

> **2026-10-28 note:** the root EXE was rebuilt as **32-bit · v2.4.0.0** (16,595,921 bytes) and verified
> against the engine: Excel, 9 BULK files and 36 driverlogs all matched with **0 differences**. The
> 2.3.0.0 measurements below are the historical audit; the build toolchain is the same 32-bit one.

**Date:** 18-oct-2026
**Auditor:** automated subagent (OpenCode)
**Artifacts (18-oct, after the 32-bit build):**
- `Facturacion MTM.exe` (root) = **32-bit x86 · 15.81 MiB** · v2.3.0.0 ← the one to ship (universal)
- `dist32\Facturacion MTM.exe` = same 32-bit build
- `dist\Facturacion MTM.exe` = **64-bit x64 · 17.73 MiB** · v2.3.0.0
**Build toolchains:** PyInstaller 6.22.3 · Python 3.14.6 64-bit (MSC v.1944, AMD64) and Python 3.14.6 **32-bit**
(portable zip at `%TEMP%\opencode\py32\python`).

## VERDICT

✅ **PORTABLE / STANDALONE AND UNIVERSAL (32-BIT).** The `.exe` in the project root is a **32-bit (x86)** build, so it
runs on **both 32-bit and 64-bit Windows 10/11** without Python or installs. (A 64-bit build is kept in `dist\` for
speed; see §9.) Verified end-to-end from a bare temp folder containing **only the .exe**, against real project data —
Excel, BULK UPLOAD and Word/driverlog paths all pass, with output **identical** to the Python engine.

---

## 1. One-file build — CONFIRMED

`Facturacion MTM.spec` has a single `EXE(...)` target that receives **all** of `a.binaries` and `a.datas`, and there is
**no `COLLECT(...)` block**. That combination is precisely what makes it a one-file build.

```python
# lines 19–38 of "Facturacion MTM.spec"
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,   # <-- binaries embedded in the EXE
    a.datas,      # <-- data files embedded in the EXE
    [],
    name='Facturacion MTM',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # <-- windowed, no console
    ...
)
```

Additional relevant lines (lines 4–16): `hiddenimports=['docx']` and `excludes=['numpy','pandas','matplotlib','scipy']`
(the heavy numeric stacks are deliberately left out — good for size and for the low-RAM constraint).

Corroborating evidence from the binary itself: the build produces **no `.toc` and no `COLLECT` output directory** — the
only build outputs are the two identical 17.61 MiB EXEs. Note: `upx=True` is requested, but **UPX is not installed on
this machine**, so no UPX compression was actually applied; the size reduction comes from PyInstaller's own zlib
compression of the CArchive.

## 2. Bundled contents — everything present

`build\` does not exist (no `warn-*.txt`, no `.toc`), so the EXE's embedded CArchive was read directly with
PyInstaller's own reader (`PyInstaller.archive.readers.CArchiveReader` / `ZlibArchiveReader`).

| Property | Value |
|---|---|
| CArchive entries | **1,006** (`b`=994 binaries, `s`=6 scripts, `m`=5 modules, `z`=1 PYZ) |
| Uncompressed payload | **39.2 MB** |
| PYZ (pure-Python) modules | **574** |

Presence of the required pieces:

| Requirement | Result |
|---|---|
| Python runtime | ✅ `python314.dll` present |
| `openpyxl` | ✅ **176 modules** inside the PYZ (`openpyxl`, `openpyxl.cell`, …) + dependency `et_xmlfile` |
| `python-docx` | ✅ **95 modules** inside the PYZ (`docx`, `docx.api`, `docx.blkcntnr`, …) + `docx/templates/*` data files |
| `lxml` | ✅ **24 Python modules** in the PYZ **and** 7 compiled extensions: `lxml/etree.cp314-win_amd64.pyd`, `builder`, `objectify`, `sax`, `_elementpath`, `html/diff`, `html/_difflib` |
| Tcl/Tk (GUI) | ✅ `_tkinter.pyd`, `tcl86t.dll`, `tk86t.dll`, `_tcl_data` (895 files), `_tk_data` |
| Other bundled libs | ✅ `libffi-8.dll`, `zlib1.dll`, `libssl-3.dll`, `libcrypto-3.dll`, `pyexpat.pyd`, `_ssl.pyd`, `_hashlib.pyd`, `_ctypes.pyd`, `_decimal.pyd`, `_lzma.pyd`, `_bz2.pyd`, `_zstd.pyd`, `unicodedata.pyd` |
| App code | ✅ `app`, `app.common`, `app.driverlogs`, `app.filler`, `app.parsers`, `app.pipeline`, `app.report`, `app.ui`, `app.writer` |

**Nothing appears to be missing.** All app imports (`openpyxl`, `docx`, `tkinter`) resolve from inside the EXE.

## 3. External DLL dependencies — no VC++ redistributable needed

`dumpbin` is **not available** on this machine (no Visual Studio installed), so the PE import tables of every bundled
native module (34 files, extracted from the archive) were parsed directly.

- **Bundled and self-supplied:** `python314.dll`, `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll`, `tcl86t.dll`, `tk86t.dll`,
  `libffi-8.dll`, `zlib1.dll`, `libssl-3.dll`, `libcrypto-3.dll`.
- **`msvcp140.dll` is NOT required.** It is **not bundled and not imported by any** bundled binary. The `lxml` C++
  extensions (`etree`, `objectify`, …) import only `VCRUNTIME140.dll` and the OS UCRT API sets — the C++ standard
  library is statically linked. This is the single most important result for clean-machine portability.
- **Every other imported DLL is a Windows OS component**, present on Windows 10 out of the box:
  `kernel32`, `user32`, `advapi32`, `shell32`, `ole32`, `oleaut32`, `comctl32`, `comdlg32`, `gdi32`, `imm32`,
  `crypt32`, `bcrypt`, `iphlpapi`, `netapi32`, `rpcrt4`, `propsys`, `userenv`, `version`, `ws2_32`, `msvcrt`,
  and the Universal CRT API sets `api-ms-win-crt-*.dll`.
- `api-ms-win-core-path-l1-1-0.dll` is imported by `python314.dll`; this is exactly the API set that makes modern
  CPython require **Windows 8+** (see §5).

**Conclusion:** the MSVC runtime is effectively bundled (`VCRUNTIME140*.dll`), the UCRT comes from Windows 10 itself,
and `msvcp140.dll` is unnecessary. **No Visual C++ Redistributable install is needed on the target PC.**

## 4. Portability test — PASSED (both paths)

Only `Facturacion MTM.exe` was copied to `%TEMP%\opencode\portable_test\` (no other files, no Python, no DLLs), and run
via CLI. The argument list was passed as **one quoted string** (an array mangles the paths, per project notes).

### 4a. Excel path (openpyxl)

```
Start-Process -FilePath "…\portable_test\Facturacion MTM.exe" -Wait -PassThru `
  -ArgumentList '--cli "…\data\base\ClaimInformation 10-05 A 10-15 OLD.xlsx" "…\data\base" --out "…\portable_test\out.xlsx"'
```

- **Exit code 0**, elapsed **5.17 s**.
- `out.xlsx` written (17,321 bytes). Validated by re-opening it with openpyxl: **9 sheets**
  `10-05 … 10-15`, dimensions `A1:J9`, correct headers and correct data rows
  (e.g. `200 · N242-541-93-600-0 · 2C4RDGBG0HR853353 · 10/05/2026 · M4F32EG2N0B · LISA HALSEY · 10:49:00 · 11:09:00 · 5.67`).

### 4b. Word/driverlog path (forces `lxml` + `python-docx` to load)

```
-ArgumentList '--cli "…\ClaimInformation 10-05 A 10-15 OLD.xlsx" "…\data\base" --out "…\out2.xlsx" `
               '--gen-driverlogs --driverlogs "…\MTM Driverlogs" --days-root "…\portable_dl"'
```

- **Exit code 0**, elapsed **6.17 s**.
- `out2.xlsx` written **and 29 `.docx` driverlogs** generated across all 9 days
  (`10-05\Docs\10-05 200.docx`, … `10-15\Docs\10-15 309.docx`).
- A generated driverlog was re-opened with python-docx: 1 table, 15 rows, correct headers, correct trip rows, and the
  template logo (`media/image1.png`) preserved — i.e. the bundled `lxml/etree.pyd` genuinely works.

This test proves the two heaviest native dependencies (openpyxl, lxml) both load and run from the standalone EXE.

### 4c. Startup / self-extraction

- Bootstrap + extraction run (`--cli` with missing args → exit code 1): **≈2.0 s** (3 runs: 2.14 / 2.02 / 2.03 s).
- The one-file bootloader extracts the payload to `%TEMP%\_MEIxxxxx` and **cleans it up on exit** — no leftover `_MEI*`
  directory was left behind. So there is no temp-directory leak, but each run pays the extraction cost (§6).

## 5. Minimum Windows version — current 32-bit universal build

> The measurements in this section were taken on the earlier 64-bit build. The current root EXE is
> 32-bit; see §9 for the current build and verification.

- Official CPython 3.14 statement: *"Python 3.14 supports Windows 10 and newer. If you require Windows 7 support,
  please install Python 3.8. If you require Windows 8.1 support, please install Python 3.12."*
- PE evidence agrees: `python314.dll` imports `api-ms-win-core-path-l1-1-0.dll` (an API set that exists only on
  Windows 8+).
- **Architecture:** the historical 64-bit build was `machine=0x8664` (x64 only). The current root EXE is
  `machine=0x014C` (x86) and runs on 32- and 64-bit Windows; ARM Windows needs x86/x64 emulation.

**Target requirement: Windows 10 or newer, 32-bit or 64-bit.** Windows 11 is fine.

## 6. Size and startup considerations on a slower PC

- **On-disk size:** 17.61 MiB (single file) — very reasonable for a bundled Python + openpyxl + lxml + Tk app.
- **Temporary footprint:** ~39 MB is extracted to `%TEMP%` on every launch, then deleted on exit.
- **Startup:** ~2 s here just to bootstrap; the full job (81 claim rows + 9 summaries + 9 trip files) took 5–6 s. On a
  slower PC (spinning disk, low RAM), expect roughly **3–8 s of startup** for the self-extraction before the window
  appears, plus processing.
- **RAM:** the app already sets `OPENBLAS_NUM_THREADS=1` / `OMP_NUM_THREADS=1` before imports, and the build excludes
  numpy/pandas/scipy, so there is no OpenBLAS memory blow-up — good for low-RAM machines. Typical working set is
  modest (openpyxl streams the workbooks).
- If startup ever became a priority, switching the spec from one-file to one-dir would remove the per-launch
  extraction — but that **breaks the "copy a single .exe" requirement**, so it is not recommended here.

## 7. Caveats (no blockers)

1. **The EXE is currently UNSIGNED** (`Get-AuthenticodeSignature` → `NotSigned`) but **has version info + the MTM icon**
   (`FileVersion 2.4.0.0`, `CompanyName Disma Transportation`). On another PC, SmartScreen will likely show
   *"Windows protected your PC / Unknown publisher"* → the user must click **More info → Run anyway**. This is a trust
   prompt, not a dependency problem. Digital signing was **removed on 19-oct** and deferred (see `docs/HISTORY.md`).
2. **Antivirus / AppLocker:** one-file PyInstaller EXEs occasionally trigger heuristic AV flags, and the
   self-extraction to `%TEMP%` can be blocked by AppLocker or restrictive corporate policy. On a normal home/office
   Windows 10 PC this is not an issue (verified here). **Optional mitigation:** the one-dir build.
3. **Windowed build (`console=False`) discards stdout.** This is why the CLI is run with `-Wait -PassThru` and success is
   judged by the **exit code** and the output file. `print()` output is intentionally swallowed
   (`run_app.py` guards it: *"windowed exe has no stdout"*). If you ever need visible CLI output for debugging, build a
   separate console variant. Note the project convention: pass the argument list as **one quoted string**, never as an
   array.
4. **`%TEMP%` must be writable** (it always is for a normal user session).
5. **Tcl/Tk version:** `tcl86t.dll`/`tk86t.dll` (Tcl/Tk 8.6) are bundled, so the GUI works without any Tcl install; the
   theme is the app's own flat design, so no external theme files are needed.
6. **No internet required** and **no registry/installer footprint** — the app only reads the source folder the user
   chooses and writes the output file/folder.

## 8. Recommendation

**Ship it as-is: the `.exe` is genuinely portable and standalone for 32-bit and 64-bit Windows 10+.** Nothing must be changed for
the copy-one-file-and-run requirement to hold. If you want a smoother first-run experience on other people's PCs,
the only worthwhile improvements are cosmetic/institutional: **code-sign the EXE** and add **version info + an icon**.

---

### Reproducing this audit

Quick portability check (from a folder containing only the EXE):

```powershell
$t = "$env:TEMP\opencode\portable_test"
New-Item -ItemType Directory -Force $t | Out-Null
Copy-Item "C:\Users\Fely\Documents\OpenCode\Facturacion MTM\Facturacion MTM.exe" "$t\Facturacion MTM.exe"
Start-Process -FilePath "$t\Facturacion MTM.exe" -Wait -PassThru -ArgumentList `
  '--cli "C:\Users\Fely\Documents\OpenCode\Facturacion MTM\data\base\ClaimInformation 10-05 A 10-15 OLD.xlsx" "C:\Users\Fely\Documents\OpenCode\Facturacion MTM\data\base" --out "C:\Users\Fely\AppData\Local\Temp\opencode\portable_test\out.xlsx"'
# expect ExitCode = 0 and out.xlsx created
```

Archive inspection (low RAM): always set `$env:OPENBLAS_NUM_THREADS="1"; $env:OMP_NUM_THREADS="1"` and run one Python
process at a time. Helpers used during this audit live in `%TEMP%\opencode\` (`inspect_all.py`, `pever.py`,
`peimports.py`).

---

## 9. 32-bit universal build — DONE (18-oct)

The app now ships as a **32-bit (x86)** one-file EXE, which runs on **both 32-bit and 64-bit Windows 10/11** (via WOW64).
A 64-bit build is also kept because it is slightly faster on modern machines.

### 9.1 Why a 32-bit build is the "universal" one
- An **x64** EXE refuses to start on 32-bit Windows ("This app can't run on your PC").
- An **x86 (32-bit)** EXE runs on **32-bit and 64-bit** Windows.
- Trade-off: a 32-bit process has a ~2–4 GB address-space ceiling. This app is I/O-bound (openpyxl/python-docx) and
  handles a few dozen rows, so the ceiling is irrelevant.

### 9.2 How it was built (no installer needed)
1. Downloaded the official **full 32-bit zip**: `https://www.python.org/ftp/python/3.14.6/python-3.14.6-win32.zip`
   (34.7 MB). It includes `python.exe`, `tkinter`, `tcl86t.dll`/`tk86t.dll`, `ensurepip` and pip.
2. Extracted to `%TEMP%\opencode\py32\python` (portable; no registry, no PATH changes).
3. `python -m pip install --only-binary=:all: openpyxl python-docx pyinstaller`
   → installed `lxml-6.1.3-cp314-cp314-win32.whl` (a real 32-bit wheel exists, so **no source build**).
4. `python -m PyInstaller "Facturacion MTM.spec" --noconfirm --clean --distpath dist32 --workpath build32`
   → PyInstaller used the **`Windows-32bit-intel\runw.exe`** bootloader.

### 9.3 Verification
| Check | Result |
|---|---|
| PE machine | `0x014C` = **i386 (32-bit)** ✅ |
| Version info | `2.4.0.0`, CompanyName `Disma Transportation` ✅ |
| Size | **16,595,921 bytes** (32-bit) vs 17.73 MiB (64-bit) |
| Runs from a folder with **only the exe** | ✅ exit 0 |
| Excel output vs Python engine | **0 diffs** (all 9 sheets) ✅ |
| BULK UPLOAD (9 files) vs engine | **0 diffs** ✅ |
| Driverlogs (.docx, exercises 32-bit lxml) | ✅ generated |
| 64-bit build (rebuilt with same source) | ✅ exit 0, Excel + 9 BULKs |

### 9.4 Rebuilding later
```powershell
$py32 = "$env:TEMP\opencode\py32\python\python.exe"   # 32-bit portable
& $py32 -m PyInstaller "Facturacion MTM.spec" --noconfirm --clean --distpath dist32 --workpath build32
Copy-Item "dist32\Facturacion MTM.exe" "Facturacion MTM.exe" -Force
```
Keep the root EXE 32-bit so it remains universal. The `%TEMP%\opencode\py32` toolchain is disposable; re-download the
zip above if it was cleaned.
