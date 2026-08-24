@echo off
REM Ejecuta tu programa contra el simulador que ya tenes abierto.
cd /d "%~dp0"

set ARCHIVO=%1
if "%ARCHIVO%"=="" set ARCHIVO=mi_desarrollo\mi_tp01.py

set PYTHON=
where py >nul 2>&1 && set PYTHON=py -3
if not defined PYTHON where python >nul 2>&1 && set PYTHON=python

%PYTHON% "%ARCHIVO%"
echo.
pause
