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
