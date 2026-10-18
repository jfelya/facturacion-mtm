@echo off
setlocal
set "CER=%~dp0Disma-CodeSign.cer"
set "TP=A8E8C2FAB0CA8D237D7CE54BE6888EE6143DC3B4"

if not exist "%CER%" (
  echo ERROR: no encuentro Disma-CodeSign.cer junto a este archivo.
  pause
  exit /b 1
)

echo.
echo Instalando el certificado de firma de Disma Transportation...
echo Windows puede pedir confirmacion: pulsa SI / YES.
echo.

certutil -user -store Root %TP% >nul 2>&1
if errorlevel 1 (
  certutil -addstore -user Root "%CER%"
) else (
  echo  - Trusted Root: ya estaba instalado.
)

certutil -user -store TrustedPublisher %TP% >nul 2>&1
if errorlevel 1 (
  certutil -addstore -user TrustedPublisher "%CER%"
) else (
  echo  - Trusted Publishers: ya estaba instalado.
)

echo.
echo Listo. Ahora "Facturacion MTM.exe" se muestra como "Disma Transportation"
echo y no debe salir el aviso "Unknown publisher".
echo.
pause
endlocal
