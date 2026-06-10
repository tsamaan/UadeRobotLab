# Unitree MuJoCo Oficial

Integracion del simulador oficial de Unitree:

<https://github.com/unitreerobotics/unitree_mujoco>

Este es el camino recomendado para sim-to-real con Go2, G1 y otros robots Unitree. El repo oficial trae:

- `simulate`: simulador C++ basado en `unitree_sdk2` y MuJoCo.
- `simulate_python`: simulador Python basado en `unitree_sdk2_python` y MuJoCo.
- `unitree_robots`: modelos MJCF oficiales.
- `example`: ejemplos para C++, Python y ROS 2.

Nota importante: el README oficial usa la interfaz `lo`, que es comun en Linux. En Windows esa interfaz no existe para CycloneDDS, asi que estos scripts usan `Ethernet` por defecto. Si usas otra placa, pasala con `-Interface`.

## 1. Clonar y configurar

Desde esta carpeta:

```powershell
.\run_go2_sim.ps1 -SetupOnly
```

Esto clona `unitreerobotics/unitree_mujoco` en `unitree_mujoco/` y ajusta:

- `ROBOT = "go2"`
- `DOMAIN_ID = 1`
- `INTERFACE = "Ethernet"`
- `USE_JOYSTICK = 0`
- `PRINT_SCENE_INFORMATION = False`

## 2. Abrir el simulador Go2

```powershell
.\run_go2_sim.ps1
```

Si tu interfaz no es `Ethernet`:

```powershell
.\run_go2_sim.ps1 -Interface "vEthernet (Default Switch)"
```

## 2b. Abrir el simulador G1 en Windows

### Instalacion inicial

En una PC nueva, ejecutar una sola vez:

```bat
setup_windows.bat
```

Ese script:

- clona `unitree_sdk2` y `unitree_sdk2_python` si faltan;
- crea `.venv` en esta carpeta;
- instala `requirements.txt`;
- instala `unitree_sdk2_python` en modo editable;
- corre `run_g1_sim.ps1 -SetupOnly` para verificar que el modelo G1 carga.

El instalador usa opciones `--trusted-host` para PyPI porque algunas redes institucionales interceptan certificados SSL y bloquean `pip`.

Para el taller con robot humanoide, usar el launcher de G1:

```powershell
.\run_g1_sim.ps1
```

Tambien se puede abrir con doble clic desde Windows:

```bat
abrir_g1_sim.bat
```

Requisitos en la PC del profesor:

- Python 3.10 disponible como `py -3.10`.
- Git disponible en `PATH`.
- Paquetes Python `mujoco`, `pygame` y `unitree_sdk2py` instalados.

El script verifica estos requisitos antes de abrir MuJoCo. Si falta `mujoco` o `pygame`, se pueden instalar con:

```powershell
py -3.10 -m pip install mujoco pygame
```

Si se uso `setup_windows.bat`, no hace falta instalar esto a mano: queda instalado en `.venv`.

El script configura automaticamente:

- `ROBOT = "g1"`
- `DOMAIN_ID = 1`
- una interfaz de red activa de Windows
- `USE_JOYSTICK = 0`
- `PRINT_SCENE_INFORMATION = False`
- `ENABLE_ELASTIC_BAND = False`
- `HOLD_INITIAL_POSE = True`
- API local para alumnos en `127.0.0.1:8765`

Estado actual: esta version del G1 es visual/cinematica para programacion secuencial. El launcher usa `g1_teacher_sim.py`, un runner docente que anima directamente la base y las articulaciones del G1. No usa banda elastica por defecto, asi que el humanoide no queda colgado ni sale flotando. El comando `movimiento(...)` traslada la base y activa una marcha didactica simple en las piernas; no es una politica de locomocion realista ni un controlador sim-to-real.

Mientras la ventana de MuJoCo este abierta, los alumnos pueden controlar el robot con `g1_student_api.py`.

Ejemplo:

```python
from g1_student_api import RobotG1

robot = RobotG1()
robot.conectar()
robot.saludar()
robot.movimiento(adelante=0.20, costado=0.0, giro=0.0, tiempo=2.0)
robot.movimiento(adelante=0.0, costado=0.0, giro=0.60, tiempo=1.5)
robot.dar_beso()
robot.detenerse()
robot.desconectar()
```

Plantilla lista para probar:

```powershell
.\.venv\Scripts\python.exe .\examples\ejemplo_g1_simple.py
```

La plantilla hace:

- conecta con el simulador;
- gira durante unos segundos;
- saluda;
- camina hacia adelante;
- da un beso;
- se detiene y desconecta.

Tambien hay una plantilla editable para alumnos:

```powershell
py -3.10 .\examples\alumnos_g1_api.py
```

Para verificar dependencias y configuracion sin abrir MuJoCo:

```powershell
.\run_g1_sim.ps1 -SetupOnly
```

Si Windows elige mal la placa de red, pasarla manualmente:

```powershell
.\run_g1_sim.ps1 -Interface "Ethernet"
.\run_g1_sim.ps1 -Interface "Wi-Fi"
.\run_g1_sim.ps1 -Interface "vEthernet (Default Switch)"
```

Si el puerto local `8765` estuviera ocupado:

```powershell
.\run_g1_sim.ps1 -ApiPort 8766
```

## 3. Enviar un comando low-level al simulador

Con el simulador abierto, en otra terminal:

```powershell
py -3.10 .\examples\go2_lowcmd_stand.py --interface Ethernet
```

Ese ejemplo usa `unitree_sdk2py` y publica `LowCmd` en el dominio DDS `1`, igual que el simulador.

## Actividades para alumnos

Alto nivel en simulador: el alumno programa acciones simples del robot. Esta capa es didactica y experimental; no equivale al `SportClient.Move()` del Go2 fisico porque el simulador oficial de Unitree no incluye el controlador interno de locomocion.

```powershell
.\run_alto_nivel.ps1
```

El archivo para editar es:

```text
examples/alumnos_alto_nivel.py
```

Ejemplo:

```python
robot.StandUp()
robot.Move(x=0.25, y=0.0, yaw=0.0, duration=2.0)
robot.Hello()
robot.StandDown()
```

Para movimiento de alto nivel realista, usar el robot fisico con `unitree_sdk2py.go2.sport.SportClient`. Ese controlador vive dentro del robot real, no dentro de `unitree_mujoco`.

Bajo nivel: el alumno programa posiciones de articulaciones y publica `LowCmd`.

```powershell
.\run_bajo_nivel.ps1
```

El archivo para editar es:

```text
examples/alumnos_bajo_nivel.py
```

Ejemplo:

```python
pose = robot.pose()
pose = robot.set_joint(pose, "FR_thigh", 0.25)
pose = robot.set_joint(pose, "FR_calf", -0.80)
robot.interpolate_to(pose, duration=0.8)
```

Trot educativo: el alumno usa una marcha mas explicable que convierte trayectoria de pies a articulaciones con IK.

```powershell
.\run_trot_educativo.ps1
```

El archivo para editar es:

```text
examples/alumnos_trot_educativo.py
```

Ejemplo:

```python
robot.ready()
robot.walk_forward(speed=0.22, duration=3.0)
robot.turn_left(yaw=0.30, duration=2.0)
```

## Diferencia entre niveles

El simulador oficial actualmente apunta principalmente a control low-level. El README oficial indica que la version actual soporta principalmente desarrollo low-level para verificar controladores sim-to-real:

- `LowCmd`: comandos de motor.
- `LowState`: estado de motores.
- `SportModeState`: pose y velocidad.

La carpeta `student_sdk` agrega una capa de alto nivel didactica encima de `LowCmd`. Sirve para introducir la idea de acciones como `StandUp`, `Move` y `Hello`, pero una caminata parecida a la del robot fisico requiere un controlador de locomocion de verdad, por ejemplo MPC o una politica RL entrenada.

## Carriles de locomocion

1. Controlador educativo propio:

   - Archivo: `student_sdk/go2_trot_controller.py`
   - Ejemplo: `examples/alumnos_trot_educativo.py`
   - Objetivo: que los alumnos entiendan fases de marcha, trayectorias de pie, IK y `LowCmd`.

2. Politica RL/preentrenada:

   - Carpeta: `policies/`
   - Objetivo: lograr una caminata mas realista en MuJoCo.
   - Estado: pendiente de adaptar una politica al modelo oficial y al orden de observaciones/acciones.
   - Chequeo inicial: `.\run_rl_policy.ps1 -Check`
