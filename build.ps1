param(
  [string]$Python = "$env:TEMP\opencode\py32\python\python.exe",
  [string]$Dist = "dist32",
  [string]$Work = "build32",
  [switch]$NoCopy
)

if (-not (Test-Path $Python)) {
  throw "No encuentro Python en '$Python'. Pasa -Python <ruta> (32-bit para el exe universal)."
}

& $Python -m PyInstaller "Facturacion MTM.spec" --noconfirm --clean --distpath $Dist --workpath $Work
if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller falló con código $LASTEXITCODE."
}

if (-not $NoCopy) {
  Copy-Item "$Dist\Facturacion MTM.exe" "Facturacion MTM.exe" -Force
  (Get-Item "Facturacion MTM.exe").VersionInfo | Format-List FileVersion, ProductVersion
  Write-Host "Listo: Facturacion MTM.exe (raíz, build $Dist)."
} else {
  Write-Host "Build listo en $Dist (no se copió a la raíz)."
}
