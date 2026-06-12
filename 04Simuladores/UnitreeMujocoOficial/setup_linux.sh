#!/usr/bin/env bash
if [ -z "${BASH_VERSION:-}" ]; then
    exec bash "$0" "$@"
fi

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
SDK_DIR="$ROOT_DIR/00SDK"
SDK_CPP="$SDK_DIR/unitree_sdk2"
SDK_PY="$SDK_DIR/unitree_sdk2_python"
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
CYCLONEDDS_PREFIX="$SCRIPT_DIR/.cyclonedds"
PYENV_VERSION_REQUIRED="3.10.14"
PYENV_BIN="${PYENV_ROOT:-$HOME/.pyenv}/bin/pyenv"
PYENV_CMD=""

echo "============================================================"
echo " Setup Linux - Unitree MuJoCo G1 docente"
echo "============================================================"
echo

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "[ERROR] No se encontro '$1' en PATH." >&2
        exit 1
    fi
}

require_command git

mkdir -p "$SDK_DIR"

find_pyenv() {
    if command -v pyenv >/dev/null 2>&1; then
        command -v pyenv
        return
    fi

    if [[ -x "$PYENV_BIN" ]]; then
        echo "$PYENV_BIN"
        return
    fi

    echo "[ERROR] No se encontro pyenv." >&2
    echo "        Instala pyenv y Python $PYENV_VERSION_REQUIRED antes de correr este setup." >&2
    exit 1
}

ensure_pyenv_python() {
    PYENV_CMD="$(find_pyenv)"

    if ! "$PYENV_CMD" versions --bare | grep -qx "$PYENV_VERSION_REQUIRED"; then
        echo "[ERROR] pyenv no tiene instalada la version $PYENV_VERSION_REQUIRED." >&2
        echo "        Ejecuta: pyenv install $PYENV_VERSION_REQUIRED" >&2
        exit 1
    fi

    export PYENV_VERSION="$PYENV_VERSION_REQUIRED"
    echo "[OK] Usando Python $("${PYENV_CMD}" exec python --version) via pyenv."
}

ensure_venv_python_version() {
    local current_version
    current_version="$("$VENV_PYTHON" -c 'import platform; print(platform.python_version())')"
    if [[ "$current_version" != "$PYENV_VERSION_REQUIRED" ]]; then
        echo "[ERROR] .venv usa Python $current_version, pero este proyecto requiere $PYENV_VERSION_REQUIRED." >&2
        echo "        Recrealo con:" >&2
        echo "        rm -rf .venv" >&2
        echo "        ./setup_linux.sh" >&2
        exit 1
    fi
}

ensure_cyclonedds_native() {
    if [[ -n "${CYCLONEDDS_HOME:-}" && -f "$CYCLONEDDS_HOME/include/dds/dds.h" && -e "$CYCLONEDDS_HOME/lib/libddsc.so" ]]; then
        return
    fi

    if command -v dpkg-query >/dev/null 2>&1 &&
        ! dpkg-query -W -f='${Status}' cyclonedds-dev 2>/dev/null | grep -q "install ok installed"; then
        echo "[ERROR] Falta la libreria nativa de CycloneDDS." >&2
        echo "        Instalala y volve a correr este script:" >&2
        echo "        sudo apt update" >&2
        echo "        sudo apt install cmake cyclonedds-dev" >&2
        echo >&2
        echo "        Alternativa avanzada: compilar CycloneDDS y exportar CYCLONEDDS_HOME." >&2
        exit 1
    fi

    if [[ -f /usr/include/dds/dds.h && -e /usr/lib/x86_64-linux-gnu/libddsc.so ]]; then
        mkdir -p "$CYCLONEDDS_PREFIX"
        ln -sfn /usr/include "$CYCLONEDDS_PREFIX/include"
        ln -sfn /usr/lib/x86_64-linux-gnu "$CYCLONEDDS_PREFIX/lib"
        export CYCLONEDDS_HOME="$CYCLONEDDS_PREFIX"
        export CMAKE_PREFIX_PATH="$CYCLONEDDS_PREFIX:/usr${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
    fi
}

if [[ ! -f "$SDK_CPP/README.md" ]]; then
    echo "[INFO] Clonando unitree_sdk2..."
    git clone --depth 1 https://github.com/unitreerobotics/unitree_sdk2.git "$SDK_CPP"
else
    echo "[OK] unitree_sdk2 ya esta disponible."
fi

if [[ ! -f "$SDK_PY/setup.py" ]]; then
    echo "[INFO] Clonando unitree_sdk2_python..."
    git clone --depth 1 https://github.com/unitreerobotics/unitree_sdk2_python.git "$SDK_PY"
else
    echo "[OK] unitree_sdk2_python ya esta disponible."
fi

ensure_pyenv_python

if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "[INFO] Creando entorno virtual .venv..."
    "$PYENV_CMD" exec python -m venv "$VENV_DIR" || {
        echo "[ERROR] No se pudo crear el entorno virtual." >&2
        echo "        Verifica pyenv y Python $PYENV_VERSION_REQUIRED." >&2
        exit 1
    }
else
    echo "[OK] Entorno virtual existente."
fi
ensure_venv_python_version

echo "[INFO] Actualizando pip..."
"$VENV_PYTHON" -m pip install --upgrade pip

echo "[INFO] Instalando dependencias MuJoCo/Pygame..."
"$VENV_PYTHON" -m pip install -r "$SCRIPT_DIR/requirements.txt"

echo "[INFO] Instalando SDK Python de Unitree..."
ensure_cyclonedds_native
"$VENV_PYTHON" -m pip install -e "$SDK_PY"

echo "[INFO] Verificando simulador G1..."
"$SCRIPT_DIR/run_g1_sim.sh" --setup-only

echo
echo "============================================================"
echo " Setup terminado."
echo "============================================================"
echo "Para abrir el simulador:"
echo "  cd \"$SCRIPT_DIR\""
echo "  ./run_g1_sim.sh"
echo
echo "Para probar la API de alumnos con el simulador abierto:"
echo "  ./.venv/bin/python examples/ejemplo_g1_simple.py"
echo
