# Firma el .exe con el certificado propio de Disma Transportation.
# El certificado (con clave privada) debe estar en Cert:\CurrentUser\My.
# Uso:  powershell -ExecutionPolicy Bypass -File sign_exe.ps1
#       powershell ... -File sign_exe.ps1 -Exe "..\..\dist32\Facturacion MTM.exe"

param(
    [string]$Exe = "..\..\Facturacion MTM.exe",
    [string]$Timestamp = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"
$thumb = "76E57421C80055FF256CD4BE880B9377D5D9608F"

$cert = Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Thumbprint -eq $thumb }
if (-not $cert) {
    throw "No encuentro el certificado $thumb en Cert:\CurrentUser\My. Importa Disma-CodeSign.pfx primero."
}

$path = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot $Exe))
if (-not (Test-Path $path)) { throw "No existe: $path" }

$r = Set-AuthenticodeSignature -FilePath $path -Certificate $cert -TimestampServer $Timestamp
Write-Host "Firma: $($r.Status) -> $path"
Get-AuthenticodeSignature $path |
    Format-List Status, StatusMessage, @{n = 'Signer'; e = { $_.SignerCertificate.Subject } }
