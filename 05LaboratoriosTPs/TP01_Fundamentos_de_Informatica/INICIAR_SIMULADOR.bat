@echo off
REM ============================================================
REM   Fundamentos de Informatica - TP01
REM   Levanta el simulador oficial de Unitree listo para el TP.
REM ============================================================
cd /d "%~dp0"

echo ============================================================
echo    Fundamentos de Informatica
echo    Simulador de robots Unitree
echo ============================================================
echo.
echo    Que robot queres usar?
echo.
echo      1)  G1   - robot humanoide (camina en dos patas)
echo      2)  Go2  - robot perro     (camina en cuatro patas)
echo.
set OPCION=1
set /p OPCION="   Elegi 1 o 2 [1]: "

set ROBOT=g1
if "%OPCION%"=="2" set ROBOT=go2
echo.

REM Preferimos un Python que ademas pueda abrir la ventana 3D.
set PYTHON=
py -3 -c "import mujoco" >nul 2>&1 && set PYTHON=py -3
if not defined PYTHON python -c "import mujoco" >nul 2>&1 && set PYTHON=python
if not defined PYTHON where py >nul 2>&1 && set PYTHON=py -3
if not defined PYTHON where python >nul 2>&1 && set PYTHON=python

if not defined PYTHON (
  echo    ERROR: no encuentro Python. Instalalo desde https://python.org
  echo    Acordate de tildar "Add Python to PATH".
  pause & exit /b 1
)

cd entorno
%PYTHON% -m sim --robot %ROBOT% --materia tp01

echo.
pause
