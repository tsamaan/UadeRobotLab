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
| **Python 3.10+** | ejecuta todo | del sistema |
| **MuJoCo** | la ventana 3D donde ves el robot | `pip` |
| **Modelos del G1 y el Go2** | el robot que ves en pantalla | **ya viene en el paquete** |
| **Carpeta del laboratorio** | el TP en sí | `05LaboratoriosTPs/` |

**Eso es todo.** Un `pip install mujoco` y listo. No hace falta CycloneDDS, ni
el SDK de Unitree, ni compilar nada, ni tener internet después de bajar la
carpeta.

> **Si venís de una versión anterior de este documento:** antes acá pedíamos
> CycloneDDS y `unitree_sdk2_python`. Ya **no hacen falta** y se sacaron a
> propósito:
>
> - `cyclonedds==0.10.2` solo publica paquetes precompilados hasta Python 3.10.
>   Con 3.11 o más nuevo, `pip` intenta compilarlo desde el código fuente y
>   falla con *"Could not locate cyclonedds"*.
> - El SDK de Unitree llama a `timerfd_create`, que existe **solo en Linux**.
>   En macOS y en Windows el import explota con *"symbol not found"*.
>
> El simulador ahora se comunica por un socket local en `127.0.0.1`, que
> funciona igual en Windows, macOS y Linux. **El código que escribe el alumno
> no cambia ni una línea**: sigue siendo `robot.avanzar(velocidad, tiempo)`, y
> el robot que se ve en pantalla sigue siendo el modelo oficial de Unitree.

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

## Paso 3 — Los modelos del robot (ya están)

**Ya viene adentro del paquete. No hay que descargar nada.**

Los modelos 3D del G1 y del Go2 viajan dentro de tu carpeta, en
`entorno/sim/unitree_mujoco/`. Son unos 46 MB.

Antes había que hacer un `git clone` la primera vez, y eso pedía git, internet
y que la red de la facultad no rompiera la descarga. Ahora la carpeta del TP se
abre sola, sin conexión.

Verificar que estén (opcional):

```bash
ls entorno/sim/unitree_mujoco/unitree_robots/
# tiene que aparecer: g1  go2
```

> Son los modelos **oficiales** de Unitree, redistribuidos bajo licencia
> BSD 3-Clause. El texto de la licencia va en
> `entorno/sim/unitree_mujoco/LICENSE`.
>
> Del repo oficial se recortó lo que no se usa: vienen sólo el G1 y el Go2 (no
> los otros ocho robots) y de cada uno sólo las mallas que el modelo referencia.
> El repo completo son 299 MB.

Si tenés el repo oficial clonado aparte, se sigue usando el del paquete: va
primero a propósito, para que el resultado no dependa de cada máquina.

---

## Paso 4 — Probar que todo funciona

Desde la carpeta del laboratorio:

```bash
cd 05LaboratoriosTPs/TP01_Fundamentos_de_Informatica
cd entorno && python3 -m sim --solo-revisar
```

Tiene que dar:

```
  [OK]    Python 3.12.3
  [OK]    MuJoCo v3.11.0
  [OK]    Modelos oficiales de Unitree /ruta/a/tu/carpeta/entorno/sim/unitree_mujoco

  Todo listo.
```

Tres líneas. Si tenés una guía que espera cinco y menciona CycloneDDS o el SDK
de Unitree, es de la versión anterior.

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

**`Could not locate cyclonedds`**
Estás siguiendo una guía vieja. **CycloneDDS ya no hace falta.** Si aparece, es
porque alguien está corriendo el simulador con `--dds`, que es un modo de
prueba interno que solo funciona en Linux con Python 3.10.

**`timerfd_create: symbol not found` (macOS)**
Lo mismo: es el SDK de Unitree, que **ya no se usa** en el paquete. Bajá la
versión nueva de la carpeta del TP.

**`selected interface "lo" is not multicast-capable`**
Tampoco aparece más: era un aviso de CycloneDDS y ya no hay CycloneDDS.

**`Address already in use` / el puerto 8765 está ocupado**
Quedó otro simulador abierto. Cerralo y volvé a intentar. Si estás seguro de
que no hay ninguno, alguna otra aplicación está usando ese puerto: podés
elegir otro con `--puerto 8766`.

**Se abre el simulador pero sin ventana 3D**
Falta MuJoCo, o la máquina no puede abrir ventanas (drivers, escritorio
remoto). El simulador **funciona igual** en modo consola: se ve la posición del
robot en texto y el TP se puede hacer completo.

**Dice "el simulador ya está abierto" y no veo ninguna ventana**
Quedó un simulador corriendo de antes. Buscá la otra ventana (puede estar
minimizada o en modo consola) y cerrala con Ctrl+C. En Linux:
`pkill -f "python.*-m sim"`. Si igual no arranca, borrá el
archivo `uade_simulador_activo.json` de la carpeta temporal del sistema.

**Tengo varios Python instalados y no encuentra MuJoCo**
El script prueba cada Python disponible y elige el que tenga MuJoCo. Si aun así
falla, instalá MuJoCo en el Python que usás por defecto.

---

## Resumen para copiar y pegar

### Linux / macOS

```bash
python3 -m pip install --user mujoco
cd 05LaboratoriosTPs/TP01_Fundamentos_de_Informatica && ./INICIAR_SIMULADOR.sh
```

### Windows

```bat
py -3 -m pip install --user mujoco
cd 05LaboratoriosTPs\TP01_Fundamentos_de_Informatica && INICIAR_SIMULADOR.bat
```
