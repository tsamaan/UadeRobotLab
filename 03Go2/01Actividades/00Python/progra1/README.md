# SDK de prueba para Unitree Go2

Esta carpeta trae un paquete local `unitree_sdk2py` que imita una parte del SDK real de Unitree.
Sirve para que los alumnos prueben su logica en cualquier PC sin conectarse al robot.

## Como usarlo

Ejecutar desde esta carpeta:

```bash
python go2_taller_alumnos.py
```

Los imports son los mismos que en el robot real:

```python
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient
```

El SDK de prueba imprime cada comando y devuelve `0` cuando el comando seria exitoso, igual que el SDK real en los metodos basicos.

## Para pasar al robot real

El alumno solo debe entregar su archivo `.py`.
En la PC del robot, usar el SDK real de `00SDK/unitree_sdk2_python` y no copiar la carpeta local `unitree_sdk2py` de este taller.

## Comandos principales

- `robot.StandUp()`
- `robot.StandDown()`
- `robot.BalanceStand()`
- `robot.StopMove()`
- `robot.Damp()`
- `robot.Move(x, y, yaw)`
- `robot.Sit()`
- `robot.RiseSit()`
- `robot.Hello()`
- `robot.Stretch()`
- `robot.Dance1()`
- `robot.Dance2()`
- `robot.FrontJump()`
- `robot.LeftFlip()`
- `robot.BackFlip()`
- `robot.FreeWalk()`
- `robot.FreeAvoid(True/False)`
