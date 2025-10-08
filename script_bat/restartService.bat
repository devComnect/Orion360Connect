@echo off
setlocal

:: Nome do serviço
set SERVICE=FlaskApp

echo [%DATE% %TIME%] Reiniciando o serviço %SERVICE%...
net stop %SERVICE%
timeout /t 5 /nobreak >nul
net start %SERVICE%
echo [%DATE% %TIME%] Serviço %SERVICE% reiniciado com sucesso.

endlocal
