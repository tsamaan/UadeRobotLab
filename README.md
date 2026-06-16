# UadeRobotLab

Laboratorio UADE para robots fisicos, simuladores, SDKs, actividades y proyectos.

## SDKs

- `00SDK/unitree_sdk2`: SDK oficial C++ de Unitree.
- `00SDK/unitree_sdk2_python`: SDK oficial Python de Unitree.

## Investigacion

- `01Investigacion/capturadorVideoLidar`: capturador de camara frontal y LiDAR del Go2, con modo demo y script para generar un paquete `.exe` portable en Windows.

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

Esta version es visual/cinematica para programacion secuencial: mueve la base y anima articulaciones para que los alumnos vean consecuencias claras de cada instruccion. No es una locomocion fisica realista ni sim-to-real.
