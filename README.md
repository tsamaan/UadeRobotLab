# UadeRobotLab

Laboratorio UADE para robots fisicos, simuladores, SDKs, actividades y proyectos.

## SDKs

- `00SDK/unitree_sdk2`: SDK oficial C++ de Unitree.
- `00SDK/unitree_sdk2_python`: SDK oficial Python de Unitree.

> Estas carpetas pueden estar **vacias**: son repos de Unitree que hay que
> clonar. El paso a paso esta en el `INSTALACION.md` de cualquier laboratorio.

## Investigacion

- `01Investigacion/capturadorVideoLidar`: capturador de camara frontal y LiDAR del Go2, con modo demo y script para generar un paquete `.exe` portable en Windows.

## Simuladores

- `04Simuladores/UnitreeMujocoOficial`: integracion recomendada con el simulador oficial `unitreerobotics/unitree_mujoco`.
- `04Simuladores/EntrenamientoRLGo2`: entorno Gymnasium + Stable-Baselines3 para entrenar caminata del Go2 con aprendizaje por refuerzo.

## Laboratorios de los TPs

`05LaboratoriosTPs/` contiene un laboratorio autocontenido por materia, listo
para repartir a docentes y estudiantes. **No necesitan robot, ni internet, ni
red especial**: todo corre en la maquina del alumno.

| Laboratorio | Materia | Que construye el alumno |
|---|---|---|
| `TP01_Fundamentos_de_Informatica` | Fundamentos de Informatica | Una rutina secuencial en Python |
| `TP02_Programacion_I` | Programacion I | Un controlador de misiones con validacion y reporte |
| `TP03_Programacion_III_Backtracking` | Programacion III | Navegacion en grilla con backtracking |
| `TP03_Programacion_III_Greedy` | Programacion III | Navegacion en grilla con estrategia voraz |
| `TP04_Desarrollo_de_Aplicaciones_I` | Desarrollo de Aplicaciones I | Una app movil React Native que controla el robot |
| `TP05_Desarrollo_de_Aplicaciones_II` | Desarrollo de Aplicaciones II | Un dashboard web de telemetria en vivo |
| `TP07_Inteligencia_Artificial` | Inteligencia Artificial | Un agente que interpreta ordenes en castellano |

Falta `TP06_Paradigma_Orientado_a_Objetos`: es Java puro y su modalidad
principal no usa el robot.

### Como se arranca

Cada carpeta trae un lanzador, `.bat` para Windows y `.sh` para Linux/macOS:

| Lanzador | En que materias |
|---|---|
| `INICIAR_SIMULADOR` | TP01, TP02, TP03 |
| `INICIAR_TP04` | TP04 (levanta ademas el backend REST) |
| `INICIAR_TP05` | TP05 (levanta ademas el backend de telemetria) |

Verifica el entorno, instala lo que falte, pregunta si se quiere el **G1
humanoide** o el **Go2 cuadrupedo**, y levanta el simulador con los parametros
de esa materia. Si algo falta, **no abre**: es peor un simulador que arranca a
medias y falla raro despues.

Empezar por `INSTALACION.md`, y despues `LEEME_ESTUDIANTE.md` o
`LEEME_DOCENTE.md` segun corresponda. TP04 y TP05 traen ademas un `API.md`, que
es el contrato contra el que el alumno programa.

### Como funciona

Usan el simulador oficial `unitree_mujoco` y el **SDK oficial de Python**: el
alumno escribe `robot.avanzar(...)` y por debajo corre el mismo `LocoClient`
(G1) o `SportClient` (Go2) que contra el robot fisico.

```
  codigo del alumno
     └─ LocoClient / SportClient      SDK oficial, igual que en el robot real
          └─ DDS
               ├─ UnitreeSdk2Bridge   oficial: rt/lowstate, rt/lowcmd
               └─ servicio "sport"    propio: el oficial no lo trae
                    └─ MuJoCo         modelos oficiales del G1 y el Go2
```

El simulador oficial **no incluye el controlador de locomocion** -- corre en la
PC interna del robot y Unitree no lo publica --, asi que estos laboratorios lo
agregan. El movimiento es **cinematico**: sin el, el G1 se desploma en dos
segundos.

En TP04 y TP05 el contrato no es un archivo de Python sino **la API HTTP**. El
backend es el mismo que corre en la notebook del laboratorio: lo unico que
cambia es de donde lee. Por eso la app del alumno solo cambia la IP el dia de la
visita.

### Dos convenciones que atraviesan todo

**Todo movimiento se expresa en velocidad y tiempo**, el giro tambien. La
distancia y el angulo son derivados (`velocidad x tiempo`). En `girar`, el signo
de la velocidad marca el sentido: positivo izquierda, negativo derecha.

**Lo que puede danar al robot esta bloqueado.** El robot se prende y se para
desde el control oficial, y lo hace el operador. Los laboratorios solo permiten
mover y gestos que no cambian la postura: nada de sentarse, pararse, bailar,
saltar ni acrobacias. Esta implementado como **lista blanca** -- lo que no esta
explicitamente permitido se rechaza --, asi que un metodo nuevo del SDK queda
bloqueado por defecto.

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
