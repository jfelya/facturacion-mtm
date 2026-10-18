@echo off
setlocal
set "TP=A8E8C2FAB0CA8D237D7CE54BE6888EE6143DC3B4"
echo Quitando el certificado de Disma Transportation de este usuario...
certutil -delstore -user Root %TP%
certutil -delstore -user TrustedPublisher %TP%
echo.
echo Listo.
pause
endlocal
