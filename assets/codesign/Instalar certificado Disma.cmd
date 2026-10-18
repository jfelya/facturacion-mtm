@echo off
setlocal
set "CER=%~dp0Disma-CodeSign.cer"
set "TP=76E57421C80055FF256CD4BE880B9377D5D9608F"

if not exist "%CER%" (
  echo ERROR: no encuentro Disma-CodeSign.cer junto a este archivo.
  pause
  exit /b 1
)

echo.
echo Instalando el certificado de firma de Disma Transportation...
echo Windows va a pedir confirmacion: pulsa SI / YES.
echo.

certutil -user -store Root %TP% >nul 2>&1
if errorlevel 1 (
  echo  - Instalando en Trusted Root (te va a preguntar)...
  certutil -addstore -user Root "%CER%"
) else (
  echo  - Trusted Root: ya estaba instalado.
)

certutil -user -store TrustedPublisher %TP% >nul 2>&1
if errorlevel 1 (
  echo  - Instalando en Trusted Publishers...
  certutil -addstore -user TrustedPublisher "%CER%"
) else (
  echo  - Trusted Publishers: ya estaba instalado.
)

echo.
certutil -user -store Root %TP% >nul 2>&1
if errorlevel 1 (
  echo  *** ADVERTENCIA: el certificado NO quedo en Trusted Root.
  echo      Vuelve a ejecutar este archivo y pulsa SI / YES en el aviso de Windows.
) else (
  echo  OK: certificado en Trusted Root. Ya puedes abrir "Facturacion MTM.exe";
  echo  el editor debe salir como "Disma Transportation" sin "Unknown publisher".
)
echo.
pause
endlocal
