@echo off
title Instalar certificado Disma
setlocal
set "CER=%~dp0Disma-CodeSign.cer"
set "TP=76E57421C80055FF256CD4BE880B9377D5D9608F"

if not exist "%CER%" (
  echo ERROR: falta el archivo Disma-CodeSign.cer en esta misma carpeta.
  pause
  exit /b 1
)

echo.
echo ================================================================
echo   Certificado de firma de Disma Transportation
echo ================================================================
echo.
echo  Se va a abrir un aviso de Windows. Debes pulsar  SI / YES.
echo  (Si no lo ves, mira en la barra de tareas: a veces sale detras.)
echo.

:check
certutil -user -store Root %TP% >nul 2>&1
if not errorlevel 1 goto trusted

echo  Instalando en "Trusted Root Certification Authorities"...
certutil -addstore -user Root "%CER%"
echo.
echo  Si el aviso se cerro sin pulsar SI, se intentara otra vez.
timeout /t 2 >nul
goto check

:trusted
certutil -user -store TrustedPublisher %TP% >nul 2>&1
if errorlevel 1 (
  echo  Instalando en "Trusted Publishers"...
  certutil -addstore -user TrustedPublisher "%CER%" >nul 2>&1
)

echo.
echo ================================================================
echo   LISTO. Certificado instalado para este usuario.
echo   Ya puedes abrir "Facturacion MTM.exe":
echo   el editor saldra como "Disma Transportation"
echo   y NO debe aparecer "Unknown publisher".
echo ================================================================
echo.
pause
endlocal
