@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_g1_sim.ps1" %*
if errorlevel 1 pause
