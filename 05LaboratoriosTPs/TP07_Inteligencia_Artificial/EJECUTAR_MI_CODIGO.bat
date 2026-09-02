@echo off
REM Ejecuta tu programa contra el simulador que ya tenes abierto.
cd /d "%~dp0"

set ARCHIVO=%1
if "%ARCHIVO%"=="" set ARCHIVO=mi_desarrollo\mi_tp07.py

REM ============================================================
REM   Buscar Python
REM ============================================================
REM Se busca en tres lugares, en este orden, y cada uno tiene su motivo:
REM
REM   1. El lanzador `py`. Se instala en C:\Windows, asi que funciona
REM      AUNQUE no se haya tildado "Add python.exe to PATH". Es el caso
REM      que salva a la mayoria.
REM   2. `python` del PATH, SALTEANDO el stub de la Microsoft Store.
REM   3. Las carpetas donde el instalador deja Python cuando no toca el
REM      PATH.
REM
REM El stub de la Store es la trampa peor: en Windows 10 y 11 existe un
REM python.exe en WindowsApps AUNQUE Python no este instalado. `where
REM python` lo encuentra, y ejecutarlo ABRE LA TIENDA en vez de correr
REM nada. Sin saltearlo, el script parece funcionar y no hace nada.
REM
REM Todo esto va PLANO, con etiquetas en vez de parentesis anidados: cmd
REM se porta mal cuando hay bloques dentro de bloques con && adentro.

set "PYTHON="
set "PYARGS="
set "HAY_STORE="

REM 1. El lanzador. Se prefiere uno que ademas tenga MuJoCo.
py -3 -c "import mujoco" >nul 2>&1 && set "PYTHON=py"
if not defined PYTHON py -3 -c "import sys" >nul 2>&1 && set "PYTHON=py"
if defined PYTHON set "PYARGS=-3"

REM 2. El PATH, sin el stub de la Store.
if not defined PYTHON for /f "delims=" %%P in ('where python 2^>nul') do call :probar_python "%%P"

REM 3. Instalado pero fuera del PATH.
if not defined PYTHON for %%V in (313 312 311 310) do call :probar_ruta "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
if not defined PYTHON for %%V in (313 312 311 310) do call :probar_ruta "%ProgramFiles%\Python%%V\python.exe"
if not defined PYTHON for %%V in (313 312 311 310) do call :probar_ruta "C:\Python%%V\python.exe"

if defined PYTHON goto :python_encontrado

echo.
echo    ============================================================
echo    NO ENCUENTRO PYTHON
echo    ============================================================
echo.
if defined HAY_STORE echo    OJO: el unico "python" que hay es el atajo de la Microsoft
if defined HAY_STORE echo    Store. Ese NO sirve: abre la tienda en vez de ejecutar nada.
if defined HAY_STORE echo.
echo    Instalalo desde https://www.python.org/downloads/
echo.
echo    Durante la instalacion, TILDA las dos casillas:
echo      [x] Add python.exe to PATH
echo      [x] py launcher
echo.
echo    Si ya lo instalaste, cerra esta ventana, abri una nueva y
echo    volve a intentar.
echo    ============================================================
echo.
pause
exit /b 1

:probar_python
REM %1 es una ruta a python.exe que encontro `where`.
if defined PYTHON goto :eof
echo %~1| find /i "WindowsApps" >nul
if not errorlevel 1 set "HAY_STORE=1"
if not errorlevel 1 goto :eof
"%~1" -c "import sys" >nul 2>&1 && set "PYTHON=%~1"
goto :eof

:probar_ruta
if defined PYTHON goto :eof
if not exist "%~1" goto :eof
"%~1" -c "import sys" >nul 2>&1 && set "PYTHON=%~1"
goto :eof

:python_encontrado


if not exist "%ARCHIVO%" (
  echo    No encuentro "%ARCHIVO%".
  echo    Fijate que estes ejecutando esto desde la carpeta del TP.
  pause
  exit /b 1
)

"%PYTHON%" %PYARGS% "%ARCHIVO%"
echo.
pause
