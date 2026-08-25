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

## Laboratorios de los TPs

`05LaboratoriosTPs/` contiene un laboratorio autocontenido por materia, listo
para repartir a docentes y estudiantes. **No necesitan robot, ni internet, ni
red especial.**

| Laboratorio | Materia | Tema |
|---|---|---|
| `TP01_Fundamentos_de_Informatica` | Fundamentos de Informatica | Programacion secuencial |
| `TP02_Programacion_I` | Programacion I | Controlador de misiones: validacion y reporte |
| `TP03_Programacion_III_Backtracking` | Programacion III | Navegacion en grilla con backtracking |
| `TP03_Programacion_III_Greedy` | Programacion III | Navegacion en grilla con estrategia voraz |
| `TP07_Inteligencia_Artificial` | Inteligencia Artificial | Agente que interpreta lenguaje natural |

Cada carpeta trae un `INICIAR_SIMULADOR` (`.bat` para Windows, `.sh` para
Linux/macOS) que verifica el entorno, instala lo que falte, pregunta si se
quiere el **G1 humanoide** o el **Go2 cuadrupedo**, y levanta el simulador
oficial con los parametros de esa materia.

Usan el simulador oficial `unitree_mujoco` y el SDK oficial de Python: el
alumno escribe `robot.avanzar(...)` y por debajo corre el mismo `LocoClient`
(G1) o `SportClient` (Go2) que contra el robot fisico. Por eso su archivo
funciona despues en el robot real sin cambiarle una linea.

Empezar por `INSTALACION.md`, y despues `LEEME_ESTUDIANTE.md` o
`LEEME_DOCENTE.md` segun corresponda.

**Convencion importante:** todo movimiento se expresa en **velocidad y tiempo**.
La distancia y el angulo son derivados (`velocidad x tiempo`). En `girar`, el
signo de la velocidad marca el sentido.

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
