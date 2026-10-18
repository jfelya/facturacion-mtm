@echo off
title Desinstalar certificado Disma
setlocal
echo Quitando el certificado de Disma Transportation de este usuario...
certutil -delstore -user Root 341120E0D59AB570861D867AA093E4AD19A25605
certutil -delstore -user TrustedPublisher 929CF265D50436603BEEAC22DA112CCF6CE090CD
echo.
echo Listo.
pause
endlocal
