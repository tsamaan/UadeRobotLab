@echo off
setlocal
powershell -ExecutionPolicy Bypass -File "%~dp0build_windows_exe.ps1"
echo.
pause
