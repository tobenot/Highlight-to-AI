@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
set "EXITCODE=%ERRORLEVEL%"

endlocal & exit /b %EXITCODE%
