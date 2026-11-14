param(
  [string]$Python = "C:\Users\Fely\AppData\Local\Python\pythoncore-3.14-64\python.exe",
  [string]$Dist = "dist",
  [string]$Work = "build",
  [switch]$NoCopy
)

if (-not (Test-Path $Python)) {
  throw "No encuentro Python en '$Python'. Pasa -Python <ruta 64-bit>."
}

& $Python -m PyInstaller "Facturacion MTM.spec" --noconfirm --clean --distpath $Dist --workpath $Work
if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller falló con código $LASTEXITCODE."
}

if (-not $NoCopy) {
  Copy-Item "$Dist\Facturacion MTM.exe" "Facturacion MTM.exe" -Force
  (Get-Item "Facturacion MTM.exe").VersionInfo | Format-List FileVersion, ProductVersion
  Write-Host "Listo: Facturacion MTM.exe (raíz, 64-bit, build $Dist)."
} else {
  Write-Host "Build listo en $Dist (no se copió a la raíz)."
}
