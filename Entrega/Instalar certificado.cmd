@echo off
title Instalar certificado Disma
setlocal
set "ROOTCER=%~dp0Disma-RootCA.cer"
set "LEAFCER=%~dp0Disma-CodeSign.cer"
set "ROOTTP=341120E0D59AB570861D867AA093E4AD19A25605"
set "LEAFTP=929CF265D50436603BEEAC22DA112CCF6CE090CD"

if not exist "%ROOTCER%" ( echo ERROR: falta Disma-RootCA.cer & pause & exit /b 1 )
if not exist "%LEAFCER%"  ( echo ERROR: falta Disma-CodeSign.cer & pause & exit /b 1 )

echo.
echo ================================================================
echo   Certificado de Disma Transportation
echo ================================================================
echo.
echo  Se va a abrir un aviso de Windows. Debes pulsar  SI / YES.
echo  (Si no lo ves, mira en la barra de tareas: a veces sale detras.)
echo.

:check_root
certutil -user -store Root %ROOTTP% >nul 2>&1
if not errorlevel 1 goto check_pub
echo  Instalando la CA raiz en "Trusted Root Certification Authorities"...
certutil -addstore -user Root "%ROOTCER%"
echo.
echo  Si el aviso se cerro sin pulsar SI, se intentara otra vez...
timeout /t 2 >nul
goto check_root

:check_pub
certutil -user -store TrustedPublisher %LEAFTP% >nul 2>&1
if errorlevel 1 (
  echo  Instalando el certificado de firma en "Trusted Publishers"...
  certutil -addstore -user TrustedPublisher "%LEAFCER%" >nul 2>&1
)

echo.
echo ================================================================
echo   LISTO. Certificado instalado para este usuario.
echo   Abre "Facturacion MTM.exe": el editor saldra como
echo   "Disma Transportation" y NO debe aparecer "Unknown publisher".
echo ================================================================
echo.
pause
endlocal
