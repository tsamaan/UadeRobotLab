#!/usr/bin/env bash
if [ -z "${BASH_VERSION:-}" ]; then
    exec bash "$0" "$@"
fi

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPO_DIR="$SCRIPT_DIR/unitree_mujoco"
REPO_URL="https://github.com/unitreerobotics/unitree_mujoco.git"
SDK_DIR="$ROOT_DIR/00SDK"
SDK_CPP="$SDK_DIR/unitree_sdk2"
SDK_PY="$SDK_DIR/unitree_sdk2_python"
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
CYCLONEDDS_PREFIX="$SCRIPT_DIR/.cyclonedds"
PYENV_VERSION_REQUIRED="3.10.14"
PYENV_BIN="${PYENV_ROOT:-$HOME/.pyenv}/bin/pyenv"
PYENV_CMD=""

INTERFACE="lo"
DOMAIN_ID="1"
USE_JOYSTICK="0"
ELASTIC_BAND="False"
POSE_HOLD="True"
API_PORT="8765"
SETUP_ONLY="0"

usage() {
    cat <<'EOF'
Uso:
  ./run_g1_sim.sh [opciones]

Opciones:
  --interface NOMBRE       Interfaz DDS. En Linux local suele ser lo. Default: lo
  --domain-id ID           Domain ID DDS. Default: 1
  --use-joystick           Activa joystick
  --use-elastic-band       Activa banda elastica
  --no-elastic-band        Desactiva banda elastica
  --no-pose-hold           Desactiva estabilizacion inicial de pose
  --api-port PUERTO        Puerto API alumnos. Default: 8765
  --setup-only             Verifica modelo/estabilidad sin abrir MuJoCo
  -h, --help               Muestra esta ayuda

Ejemplos:
  ./run_g1_sim.sh
  ./run_g1_sim.sh --setup-only
  ./run_g1_sim.sh --interface lo --api-port 8766
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --interface)
            INTERFACE="${2:?Falta el nombre de interfaz}"
            shift 2
            ;;
        --domain-id)
            DOMAIN_ID="${2:?Falta el Domain ID}"
            shift 2
            ;;
        --use-joystick)
            USE_JOYSTICK="1"
            shift
            ;;
        --use-elastic-band)
            ELASTIC_BAND="True"
            shift
            ;;
        --no-elastic-band)
            ELASTIC_BAND="False"
            shift
            ;;
        --no-pose-hold)
            POSE_HOLD="False"
            shift
            ;;
        --api-port)
            API_PORT="${2:?Falta el puerto}"
            shift 2
            ;;
        --setup-only)
            SETUP_ONLY="1"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "[ERROR] Opcion no reconocida: $1" >&2
            usage
            exit 1
            ;;
    esac
done

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "[ERROR] No se encontro '$1' en PATH." >&2
        exit 1
    fi
}

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
    echo "        Instala pyenv y Python $PYENV_VERSION_REQUIRED antes de correr este launcher." >&2
    exit 1
}

ensure_pyenv_python() {
    local pyenv_root
    local version_python
    local actual_version

    PYENV_CMD="$(find_pyenv)"
    pyenv_root="$("$PYENV_CMD" root)"
    version_python="$pyenv_root/versions/$PYENV_VERSION_REQUIRED/bin/python"

    if [[ ! -x "$version_python" ]]; then
        echo "[ERROR] pyenv no tiene instalada la version $PYENV_VERSION_REQUIRED." >&2
        echo "        Ejecuta: pyenv install $PYENV_VERSION_REQUIRED" >&2
        exit 1
    fi

    export PYENV_VERSION="$PYENV_VERSION_REQUIRED"
    actual_version="$("$PYENV_CMD" exec python -c 'import platform; print(platform.python_version())')"
    if [[ "$actual_version" != "$PYENV_VERSION_REQUIRED" ]]; then
        echo "[ERROR] pyenv encontro Python $actual_version, pero este proyecto requiere $PYENV_VERSION_REQUIRED." >&2
        echo "        Revisa: $version_python" >&2
        exit 1
    fi

    if [[ ! -f "$SCRIPT_DIR/.python-version" ]] || [[ "$(<"$SCRIPT_DIR/.python-version")" != "$PYENV_VERSION_REQUIRED" ]]; then
        echo "[INFO] Configurando pyenv local $PYENV_VERSION_REQUIRED..."
        (cd "$SCRIPT_DIR" && "$PYENV_CMD" local "$PYENV_VERSION_REQUIRED")
    else
        echo "[OK] pyenv local $PYENV_VERSION_REQUIRED configurado."
    fi
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

python_import_ok() {
    "$VENV_PYTHON" -c "import $1" >/dev/null 2>&1
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

ensure_venv() {
    ensure_pyenv_python

    if [[ ! -x "$VENV_PYTHON" ]]; then
        echo "[INFO] Creando entorno virtual .venv..."
        "$PYENV_CMD" exec python -m venv "$VENV_DIR"
    else
        echo "[OK] Entorno virtual existente."
    fi
    ensure_venv_python_version

    echo "[INFO] Actualizando pip..."
    "$VENV_PYTHON" -m pip install --upgrade pip
}

ensure_python_deps() {
    echo "[INFO] Instalando/verificando dependencias Python..."
    "$VENV_PYTHON" -m pip install -r "$SCRIPT_DIR/requirements.txt"

    if ! python_import_ok unitree_sdk2py; then
        require_command git
        mkdir -p "$SDK_DIR"

        if [[ ! -d "$SDK_CPP/.git" && ! -f "$SDK_CPP/README.md" ]]; then
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

        echo "[INFO] Instalando SDK Python de Unitree..."
        ensure_cyclonedds_native
        "$VENV_PYTHON" -m pip install -e "$SDK_PY"
    fi

    python_import_ok mujoco || {
        echo "[ERROR] Falta el paquete Python 'mujoco'." >&2
        echo "        Ejecuta: $VENV_PYTHON -m pip install -r requirements.txt" >&2
        exit 1
    }
    python_import_ok pygame || {
        echo "[ERROR] Falta el paquete Python 'pygame'." >&2
        echo "        Ejecuta: $VENV_PYTHON -m pip install -r requirements.txt" >&2
        exit 1
    }
    python_import_ok unitree_sdk2py || {
        echo "[ERROR] Falta 'unitree_sdk2py'." >&2
        echo "        Revisa la instalacion de $SDK_PY" >&2
        exit 1
    }
}

ensure_unitree_mujoco() {
    require_command git

    if [[ ! -d "$REPO_DIR" ]]; then
        echo "[INFO] Clonando unitree_mujoco oficial..."
        git clone --depth 1 "$REPO_URL" "$REPO_DIR"
    else
        echo "[INFO] unitree_mujoco ya existe. No se vuelve a clonar."
    fi
}

configure_simulator() {
    local config_path="$REPO_DIR/simulate_python/config.py"
    local bridge_path="$REPO_DIR/simulate_python/unitree_sdk2py_bridge.py"

    if [[ ! -f "$config_path" ]]; then
        echo "[ERROR] No se encontro config.py en $config_path" >&2
        exit 1
    fi

    "$VENV_PYTHON" - "$config_path" "$INTERFACE" "$DOMAIN_ID" "$USE_JOYSTICK" "$ELASTIC_BAND" "$POSE_HOLD" "$API_PORT" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
interface = sys.argv[2]
domain_id = sys.argv[3]
use_joystick = sys.argv[4]
elastic_band = sys.argv[5]
pose_hold = sys.argv[6]
api_port = sys.argv[7]

content = path.read_text(encoding="utf-8")


def set_assignment(text: str, name: str, value: str) -> str:
    pattern = rf"(?m)^{re.escape(name)}\s*=.*$"
    line = f"{name} = {value}"
    if re.search(pattern, text):
        return re.sub(pattern, line, text)
    return text.rstrip() + "\n" + line + "\n"


content = set_assignment(content, "ROBOT", '"g1"')
content = set_assignment(content, "DOMAIN_ID", domain_id)
content = set_assignment(content, "INTERFACE", repr(interface))
content = set_assignment(content, "USE_JOYSTICK", use_joystick)
content = set_assignment(content, "PRINT_SCENE_INFORMATION", "False")
content = set_assignment(content, "ENABLE_ELASTIC_BAND", elastic_band)
content = set_assignment(content, "HOLD_INITIAL_POSE", pose_hold)
content = set_assignment(content, "POSE_HOLD_KP", "100.0")
content = set_assignment(content, "POSE_HOLD_KD", "10.0")
content = set_assignment(content, "ELASTIC_BAND_POINT", "[0.0, 0.0, 1.4]")
content = set_assignment(content, "ELASTIC_BAND_STIFFNESS", "600.0")
content = set_assignment(content, "ELASTIC_BAND_DAMPING", "100.0")
content = set_assignment(content, "ELASTIC_BAND_LENGTH", "0.0")
content = set_assignment(content, "ELASTIC_BAND_ENABLE_AT_START", "True")
content = set_assignment(content, "STUDENT_API_HOST", '"127.0.0.1"')
content = set_assignment(content, "STUDENT_API_PORT", api_port)

path.write_text(content, encoding="utf-8")
PY

    if [[ -f "$bridge_path" ]]; then
        "$VENV_PYTHON" - "$bridge_path" <<'PY'
from __future__ import annotations

from pathlib import Path
import sys

path = Path(sys.argv[1])
content = path.read_text(encoding="utf-8")
old = "from unitree_sdk2py.utils.thread import RecurrentThread"
new = '''try:
    from unitree_sdk2py.utils.thread import RecurrentThread
except Exception:
    import threading
    import time

    class RecurrentThread:
        def __init__(self, interval, target, name=""):
            self.interval = interval
            self.target = target
            self.name = name
            self._running = False
            self._thread = None

        def Start(self):
            self._running = True
            self._thread = threading.Thread(target=self._run, name=self.name, daemon=True)
            self._thread.start()

        def Stop(self):
            self._running = False

        def _run(self):
            while self._running:
                start = time.perf_counter()
                self.target()
                sleep_time = self.interval - (time.perf_counter() - start)
                if sleep_time > 0:
                    time.sleep(sleep_time)
'''

if old in content and "class RecurrentThread:" not in content:
    path.write_text(content.replace(old, new), encoding="utf-8")
    print("[OK] Fallback RecurrentThread aplicado a unitree_sdk2py_bridge.py")
PY
    fi
}

print_config() {
    echo "[OK] Configuracion lista:"
    echo "     Robot        : g1"
    echo "     Domain ID    : $DOMAIN_ID"
    echo "     Interface    : $INTERFACE"
    echo "     Joystick     : $USE_JOYSTICK"
    echo "     Elastic band : $ELASTIC_BAND"
    echo "     Pose hold    : $POSE_HOLD"
    echo "     API          : 127.0.0.1:$API_PORT"
    echo "     Python       : .venv"
}

ensure_venv
ensure_python_deps
ensure_unitree_mujoco
configure_simulator
print_config

cd "$SCRIPT_DIR"

if [[ "$SETUP_ONLY" == "1" ]]; then
    "$VENV_PYTHON" "$SCRIPT_DIR/g1_teacher_sim.py" --check-model
    "$VENV_PYTHON" "$SCRIPT_DIR/g1_teacher_sim.py" --check-stability
    echo "[OK] SetupOnly finalizado. No se abre la ventana de MuJoCo."
    exit 0
fi

echo "[INFO] Abriendo MuJoCo con G1. Cerrar la ventana corta el simulador."
echo "[INFO] El robot queda estabilizado por motores/base docente, sin banda elastica."
echo "[INFO] Los alumnos pueden usar g1_student_api.py mientras esta ventana este abierta."
"$VENV_PYTHON" "$SCRIPT_DIR/g1_teacher_sim.py"
