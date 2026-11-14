param(
  [string]$Python = "C:\Users\Fely\AppData\Local\Python\pythoncore-3.14-64\python.exe",
  [string]$Dist = "dist_qt",
  [string]$Work = "build_qt",
  [switch]$NoCopy
)

if (-not (Test-Path $Python)) {
  throw "No encuentro Python en '$Python'. Pasa -Python <ruta 64-bit>."
}

& $Python -m PyInstaller "Facturacion MTM Qt.spec" --noconfirm --clean --distpath $Dist --workpath $Work
if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller falló con código $LASTEXITCODE."
}

if (-not $NoCopy) {
  Copy-Item "$Dist\Facturacion MTM Qt.exe" "Facturacion MTM Qt.exe" -Force
  (Get-Item "Facturacion MTM Qt.exe").VersionInfo | Format-List FileVersion, ProductVersion
  Write-Host "Listo: Facturacion MTM Qt.exe (raíz, build $Dist)."
} else {
  Write-Host "Build listo en $Dist (no se copió a la raíz)."
}
