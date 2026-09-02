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
| **Visual C++ Redistributable** | sólo Windows: MuJoCo no carga sin él | descarga aparte |
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

Ese comando es el que importa: **`pip install` puede terminar bien y aun así
`import mujoco` fallar.** Si imprime un número de versión, está listo.

---

## Paso 2.b — Windows: el Visual C++ Redistributable

> **Este paso es sólo para Windows, y es el que más problemas dio.**

MuJoCo está escrito en C++ y necesita tres librerías del sistema que **no vienen
con Windows ni con Python ni con MuJoCo**. Sin ellas, `pip install mujoco`
termina **sin ningún error** y después `import mujoco` falla con:

```
ImportError: DLL load failed while importing _mujoco:
No se puede encontrar el módulo especificado.
```

Y `INICIAR_SIMULADOR.bat` dice que MuJoCo no está instalado, cuando en realidad
sí lo está. Es confuso a propósito de lo mal que informa Windows este caso.

### Verificar si ya lo tenés

En **PowerShell**:

```powershell
Test-Path "C:\Windows\System32\vcruntime140.dll"
Test-Path "C:\Windows\System32\vcruntime140_1.dll"
Test-Path "C:\Windows\System32\msvcp140.dll"
```

Los tres tienen que dar **`True`**.

### Si alguno da False

Descargá e instalá el **Microsoft Visual C++ Redistributable (x64)**:

<https://aka.ms/vs/17/release/vc_redist.x64.exe>

*(página oficial: [learn.microsoft.com](https://learn.microsoft.com/es-es/cpp/windows/latest-supported-vc-redist))*

**Cerrá y volvé a abrir la consola** después de instalarlo, y probá otra vez
`python -c "import mujoco; print(mujoco.__version__)"`.

> Muchas computadoras ya lo tienen, porque lo instalan juegos y otros
> programas. Por eso a algunos les funciona a la primera y a otros no.

---

## Paso 2.c — La ventana 3D y la placa de video

MuJoCo dibuja con **OpenGL 3.3**. Que `import mujoco` funcione **no garantiza**
que se pueda abrir la ventana.

| Dónde | ¿Abre la ventana 3D? |
|---|---|
| Notebook o PC con placa **integrada** (Intel/AMD) | **Sí**, con los drivers de video al día |
| PC con placa **dedicada** (NVIDIA/AMD) | Sí |
| **Máquina virtual** sin GPU configurada | **No** |
| Sesión por **escritorio remoto** | Normalmente no |

**No hace falta una placa dedicada.** Una integrada moderna con sus drivers
alcanza. Lo que falla es una VM sin aceleración gráfica, que no tiene ningún
driver de OpenGL.

Si no se puede abrir, vas a ver algo así:

```
GLFWError: (65542) b'WGL: The driver does not appear to support OpenGL'
```

### Eso NO cancela la clase

El simulador **lo detecta y sigue funcionando en modo consola**: el programa del
alumno corre igual, el robot se mueve igual, y **el recorrido se dibuja en la
terminal**:

```
+--------------------------------------------------+
|          .................................       |
|          .                               .       |
|          .                               .       |
|          o................................       |
|          >                                       |
+--------------------------------------------------+
  x=+0.00 m   y=-0.00 m   rumbo=-0 deg   [quieto]   bateria 87%
  recorrido: 1.59 m      (sin ventana 3D: se dibuja en texto)
```

`o` es donde arrancó, `.` por dónde pasó y la flecha es hacia dónde mira ahora.
Ese dibujo es un cuadrado de 0.40 m de lado hecho con `avanzar` y `girar`.

**El TP se puede hacer completo sin ver el robot en 3D.**

Si querés forzar ese modo directamente:

```bash
cd entorno && python3 -m sim --sin-ventana
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

**Instalé MuJoCo pero dice que falta (Windows)**
Falta el **Visual C++ Redistributable**. `pip` termina bien pero la librería no
carga. Ver el **paso 2.b**. Es el problema más común en Windows.

**`DLL load failed while importing _mujoco`**
Lo mismo: paso 2.b.

**`WGL: The driver does not appear to support OpenGL`**
No hay soporte gráfico: casi siempre una máquina virtual sin GPU o una sesión
remota. **El simulador sigue funcionando en modo consola** y el TP se puede
hacer completo. Ver el paso 2.c.

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
py -3 -c "import mujoco; print(mujoco.__version__)"
cd 05LaboratoriosTPs\TP01_Fundamentos_de_Informatica && INICIAR_SIMULADOR.bat
```

Si el segundo comando falla, instalá el **Visual C++ Redistributable**
(<https://aka.ms/vs/17/release/vc_redist.x64.exe>), cerrá la consola y volvé a
probar. Ver el paso 2.b.
