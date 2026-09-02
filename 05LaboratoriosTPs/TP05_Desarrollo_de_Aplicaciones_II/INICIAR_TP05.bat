@echo off
REM ============================================================
REM   Desarrollo de Aplicaciones II
REM   Levanta el simulador y el backend para tu app.
REM ============================================================
cd /d "%~dp0"

echo ============================================================
echo    Desarrollo de Aplicaciones II
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


echo    Abriendo el simulador...
REM `start /d` en vez de `cmd /c "cd ... ^&^& ..."`: las comillas anidadas
REM del segundo rompen cuando la ruta de Python tiene espacios, que es el
REM caso de C:\Program Files\Python312\python.exe.
start "Simulador" /d entorno "%PYTHON%" %PYARGS% -m sim --robot %ROBOT% --materia tp05
timeout /t 8 >nul

"%PYTHON%" %PYARGS% entorno\arrancar_api.py --robot %ROBOT%
echo.
pause
