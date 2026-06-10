@echo off
setlocal

cd /d "%~dp0"

set "SIM_DIR=%~dp0"
for %%I in ("%SIM_DIR%\..\..") do set "ROOT_DIR=%%~fI"
set "SDK_DIR=%ROOT_DIR%\00SDK"
set "SDK_CPP=%SDK_DIR%\unitree_sdk2"
set "SDK_PY=%SDK_DIR%\unitree_sdk2_python"
set "VENV_DIR=%SIM_DIR%.venv"
set "PIP_FLAGS=--trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org"

echo ============================================================
echo  Setup Windows - Unitree MuJoCo G1 docente
echo ============================================================
echo.

where git >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encontro git en PATH.
    echo         Instalar Git para Windows y volver a ejecutar.
    exit /b 1
)

where py >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encontro el launcher py de Python.
    echo         Instalar Python 3.10 y marcar "Add python.exe to PATH".
    exit /b 1
)

if not exist "%SDK_DIR%" mkdir "%SDK_DIR%"

if not exist "%SDK_CPP%\README.md" (
    echo [INFO] Clonando unitree_sdk2...
    git clone --depth 1 https://github.com/unitreerobotics/unitree_sdk2.git "%SDK_CPP%"
    if errorlevel 1 exit /b 1
) else (
    echo [OK] unitree_sdk2 ya esta disponible.
)

if not exist "%SDK_PY%\setup.py" (
    echo [INFO] Clonando unitree_sdk2_python...
    git clone --depth 1 https://github.com/unitreerobotics/unitree_sdk2_python.git "%SDK_PY%"
    if errorlevel 1 exit /b 1
) else (
    echo [OK] unitree_sdk2_python ya esta disponible.
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [INFO] Creando entorno virtual .venv...
    py -3.10 -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno con Python 3.10.
        echo         Verificar que Python 3.10 este instalado: py -3.10 --version
        exit /b 1
    )
) else (
    echo [OK] Entorno virtual existente.
)

call "%VENV_DIR%\Scripts\activate.bat"

echo [INFO] Actualizando pip...
python -m pip install %PIP_FLAGS% --upgrade pip
if errorlevel 1 exit /b 1

echo [INFO] Instalando dependencias MuJoCo/Pygame...
python -m pip install %PIP_FLAGS% -r "%SIM_DIR%requirements.txt"
if errorlevel 1 exit /b 1

echo [INFO] Instalando SDK Python de Unitree...
python -m pip install %PIP_FLAGS% -e "%SDK_PY%"
if errorlevel 1 exit /b 1

echo [INFO] Verificando simulador G1...
powershell -NoProfile -ExecutionPolicy Bypass -File "%SIM_DIR%run_g1_sim.ps1" -SetupOnly
if errorlevel 1 exit /b 1

echo.
echo ============================================================
echo  Setup terminado.
echo ============================================================
echo Para abrir el simulador:
echo   cd /d "%SIM_DIR%"
echo   run_g1_sim.ps1
echo.
echo Para probar la API de alumnos con el simulador abierto:
echo   .venv\Scripts\python.exe examples\ejemplo_g1_simple.py
echo.

endlocal
