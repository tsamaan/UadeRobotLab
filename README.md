# UadeRobotLab

Laboratorio UADE para robots fisicos, simuladores, SDKs, actividades y proyectos.

## SDKs

- `00SDK/unitree_sdk2`: SDK oficial C++ de Unitree.
- `00SDK/unitree_sdk2_python`: SDK oficial Python de Unitree.

## Simuladores

- `04Simuladores/UnitreeMujocoOficial`: integracion recomendada con el simulador oficial `unitreerobotics/unitree_mujoco`.
- `04Simuladores/EntrenamientoRLGo2`: entorno Gymnasium + Stable-Baselines3 para entrenar caminata del Go2 con aprendizaje por refuerzo.

## Taller G1 visual

Para abrir el simulador docente del humanoide G1 en Windows:

```powershell
cd 04Simuladores\UnitreeMujocoOficial
.\setup_windows.bat
```

Despues de instalar una vez:

```powershell
cd 04Simuladores\UnitreeMujocoOficial
.\run_g1_sim.ps1
```

Con MuJoCo abierto, probar la API simple para alumnos:

```powershell
.\.venv\Scripts\python.exe .\examples\ejemplo_g1_simple.py
```

### Linux

En Linux se recomienda usar `pyenv` con Python `3.10.14` y un entorno virtual local `.venv` dentro de `04Simuladores/UnitreeMujocoOficial`.

En una PC nueva con Ubuntu/Debian, instalar dependencias del sistema:

```bash
sudo apt update
sudo apt install -y \
  build-essential curl git cmake pkg-config \
  libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
  libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
  libffi-dev liblzma-dev \
  cyclonedds-dev
```

Si `pyenv` no esta instalado:

```bash
curl https://pyenv.run | bash
```

Agregar `pyenv` al shell. Para Bash:

```bash
cat <<'EOF' >> ~/.bashrc
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
EOF
exec "$SHELL"
```

Luego instalar Python `3.10.14`:

```bash
pyenv install 3.10.14
```

Instalacion inicial del simulador:

```bash
cd 04Simuladores/UnitreeMujocoOficial
chmod +x setup_linux.sh run_g1_sim.sh abrir_g1_sim.sh
./setup_linux.sh
```

El setup clona los SDKs de Unitree si faltan, crea `.venv` con Python `3.10.14`, instala `requirements.txt`, instala `unitree_sdk2_python` y verifica el modelo G1 sin abrir MuJoCo.

Despues de instalar una vez:

```bash
cd 04Simuladores/UnitreeMujocoOficial
./run_g1_sim.sh
```

Con MuJoCo abierto, probar la API simple para alumnos:

```bash
./.venv/bin/python examples/ejemplo_g1_simple.py
```

Comandos utiles:

```bash
./run_g1_sim.sh --setup-only
./run_g1_sim.sh --interface lo
./run_g1_sim.sh --api-port 8766
./abrir_g1_sim.sh
```

Si `.venv` fue creado con otra version de Python:

```bash
rm -rf .venv
./setup_linux.sh
```

Esta version es visual/cinematica para programacion secuencial: mueve la base y anima articulaciones para que los alumnos vean consecuencias claras de cada instruccion. No es una locomocion fisica realista ni sim-to-real.
