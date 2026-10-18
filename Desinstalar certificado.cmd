@echo off
title Desinstalar certificado Disma
setlocal
set "TP=76E57421C80055FF256CD4BE880B9377D5D9608F"
echo Quitando el certificado de Disma Transportation de este usuario...
certutil -delstore -user Root %TP%
certutil -delstore -user TrustedPublisher %TP%
echo.
echo Listo.
pause
endlocal
