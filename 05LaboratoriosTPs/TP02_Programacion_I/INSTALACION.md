# Instalación completa — de cero a simulador andando

Esta guía instala **todo lo necesario** para correr los laboratorios de robots
Unitree. Se hace **una sola vez** por computadora.

Si ya tenés todo instalado, andá directo a `LEEME_DOCENTE.md` o `LEEME_ESTUDIANTE.md`.

> **Atajo:** el script `INICIAR_SIMULADOR` intenta instalar solo lo que falte.
> Probá primero con él. Esta guía es para cuando algo falla o querés entender
> qué está pasando.

---

## Qué se instala y para qué

| Pieza | Para qué sirve | Dónde vive |
|---|---|---|
| **Python 3.8+** | ejecuta todo | del sistema |
| **MuJoCo** | la ventana 3D donde ves el robot | `pip` |
| **CycloneDDS 0.10.2** | el protocolo con el que se habla al robot | `pip` |
| **unitree_sdk2_python** | el SDK oficial de Unitree | `00SDK/` |
| **unitree_mujoco** | el simulador oficial (modelos 3D + puente DDS) | `04Simuladores/` |
| **Carpeta del laboratorio** | el TP en sí | `05LaboratoriosTPs/` |

El orden importa: **CycloneDDS antes que el SDK**, porque el SDK se compila
contra él.

---

## Paso 1 — Python

### Windows

Descargar de [python.org](https://www.python.org/downloads/) e instalar.

> ⚠️ **Tildá "Add Python to PATH"** durante la instalación. Es la causa número
> uno de que después nada funcione.

Verificar:

```bat
py -3 --version
```

### Linux

```bash
sudo apt install python3 python3-pip python3-venv git
python3 --version
```

### macOS

```bash
brew install python git
python3 --version
```

---

## Paso 2 — MuJoCo (la ventana 3D)

```bash
python3 -m pip install --user mujoco
```

En Windows: `py -3 -m pip install --user mujoco`

**Si estás en la red de la universidad** y pip falla con errores de
certificado SSL, agregá:

```bash
python3 -m pip install --user mujoco ^
  --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

Verificar:

```bash
python3 -c "import mujoco; print(mujoco.__version__)"
```

---

## Paso 3 — CycloneDDS

**Tiene que ir antes del SDK.** La versión es exacta: el SDK de Unitree pide
`0.10.2`.

```bash
python3 -m pip install --user cyclonedds==0.10.2
```

Verificar:

```bash
python3 -c "import cyclonedds; print('ok')"
```

### Si falla con "Could not locate cyclonedds"

Pasa cuando pip no encuentra una versión precompilada para tu sistema. Hay que
compilarla y decirle al SDK dónde quedó:

```bash
git clone -b releases/0.10.x https://github.com/eclipse-cyclonedds/cyclonedds
cd cyclonedds && mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install -DBUILD_IDLC=ON
cmake --build . --target install
cd ../..
export CYCLONEDDS_HOME="$(pwd)/cyclonedds/install"
```

Esa variable `CYCLONEDDS_HOME` tiene que estar definida **en el paso 4**, cuando
instalás el SDK.

---

## Paso 4 — SDK de Unitree para Python

El SDK vive en `00SDK/unitree_sdk2_python`.

> ⚠️ **Esa carpeta puede estar vacía.** En el repositorio figura como
> referencia, pero el contenido no siempre viene clonado. Si `ls 00SDK/unitree_sdk2_python`
> no muestra nada, cloná el repo primero.

```bash
cd 00SDK
git clone https://github.com/unitreerobotics/unitree_sdk2_python
python3 -m pip install --user -e unitree_sdk2_python
```

Si tuviste que compilar CycloneDDS a mano en el paso 3, la instalación va así:

```bash
CYCLONEDDS_HOME=/ruta/a/cyclonedds/install \
  python3 -m pip install --user -e unitree_sdk2_python
```

Verificar:

```bash
python3 -c "import unitree_sdk2py; print('ok')"
```

### El SDK de C++ (opcional)

`00SDK/unitree_sdk2` es el SDK de C++. **No hace falta para los laboratorios**,
que son todos en Python. Sólo se usa para proyectos en C++.

---

## Paso 5 — El simulador oficial de Unitree

Son los modelos 3D de los robots y el puente DDS que los conecta con el SDK.

```bash
cd 04Simuladores
git clone https://github.com/unitreerobotics/unitree_mujoco
```

El script del laboratorio lo busca solo, en este orden:

1. `04Simuladores/UnitreeMujocoOficial/unitree_mujoco/`
2. `04Simuladores/unitree_mujoco/`
3. `~/unitree_libs/unitree_mujoco/`
4. `~/unitree_mujoco/`

Cualquiera de esas sirve. Si no lo encuentra en ninguna, lo descarga solo.

Verificar que estén los modelos:

```bash
ls 04Simuladores/unitree_mujoco/unitree_robots/
# tiene que aparecer: g1  go2  h1  b2 ...
```

---

## Paso 6 — Probar que todo funciona

Desde la carpeta del laboratorio:

```bash
cd 05LaboratoriosTPs/TP01_Fundamentos_de_Informatica
cd entorno && python3 -m sim --solo-revisar
```

Tiene que dar:

```
  [OK]    Python 3.12.3
  [OK]    MuJoCo v3.11.0
  [OK]    CycloneDDS
  [OK]    SDK de Unitree (unitree_sdk2py)
  [OK]    Simulador oficial de Unitree /ruta/al/repo

  Todo listo.
```

Si alguna línea dice `[FALTA]`, el mensaje indica qué hacer.

Ahora sí:

```bash
cd ..
./INICIAR_SIMULADOR.sh      # Linux / macOS
INICIAR_SIMULADOR.bat       # Windows
```

---

## Problemas frecuentes

**`python no se reconoce como un comando` (Windows)**
Python no quedó en el PATH. Reinstalalo tildando "Add Python to PATH".

**`pip` falla con errores de certificado SSL**
Estás en una red que intercepta certificados (típico en universidades). Agregá
`--trusted-host pypi.org --trusted-host files.pythonhosted.org`, o instalá
desde otra red.

**`Could not locate cyclonedds` al instalar el SDK**
Ver paso 3: hay que compilar CycloneDDS y exportar `CYCLONEDDS_HOME`.

**`selected interface "lo" is not multicast-capable`**
No es un error. Es un aviso normal de CycloneDDS en simulación local.

**Se abre el simulador pero sin ventana 3D**
Falta MuJoCo, o la máquina no puede abrir ventanas (drivers, escritorio
remoto). El simulador **funciona igual** en modo consola: se ve la posición del
robot en texto y el TP se puede hacer completo.

**Dice "el simulador ya está abierto" y no veo ninguna ventana**
Quedó un simulador corriendo de antes. Buscá la otra ventana (puede estar
minimizada o en modo consola) y cerrala con Ctrl+C. En Linux:
`pkill -f "python.*-m sim"`.

**Tengo varios Python instalados y no encuentra MuJoCo**
El script prueba cada Python disponible y elige el que tenga MuJoCo. Si aun así
falla, instalá MuJoCo en el Python que usás por defecto.

---

## Resumen para copiar y pegar

### Linux / macOS

```bash
python3 -m pip install --user mujoco cyclonedds==0.10.2
cd 00SDK && git clone https://github.com/unitreerobotics/unitree_sdk2_python
python3 -m pip install --user -e unitree_sdk2_python && cd ..
cd 04Simuladores && git clone https://github.com/unitreerobotics/unitree_mujoco && cd ..
cd 05LaboratoriosTPs/TP01_Fundamentos_de_Informatica && ./INICIAR_SIMULADOR.sh
```

### Windows

```bat
py -3 -m pip install --user mujoco cyclonedds==0.10.2
cd 00SDK && git clone https://github.com/unitreerobotics/unitree_sdk2_python
py -3 -m pip install --user -e unitree_sdk2_python && cd ..
cd 04Simuladores && git clone https://github.com/unitreerobotics/unitree_mujoco && cd ..
cd 05LaboratoriosTPs\TP01_Fundamentos_de_Informatica && INICIAR_SIMULADOR.bat
```
