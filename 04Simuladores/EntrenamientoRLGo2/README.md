# Entrenamiento RL Go2

Entrenamiento por refuerzo para que el Go2 aprenda a caminar en MuJoCo.

Este laboratorio usa el modelo oficial de Unitree, pero entrena sobre una escena plana generada desde:

```text
../UnitreeMujocoOficial/unitree_mujoco/unitree_robots/go2/flat_scene.xml
```

Ese `flat_scene.xml` se crea automaticamente si no existe. Incluye el `go2.xml` oficial y solo agrega piso, luz y camara. No usa los obstaculos/escaleras del `scene.xml` oficial.

La diferencia con `UnitreeMujocoOficial` es que aca no usamos DDS ni viewer durante entrenamiento. Entrenar requiere muchisimos pasos, asi que el entorno corre directo sobre MuJoCo y Stable-Baselines3.

## Idea

- Observacion: orientacion, velocidades, joints, velocidades de joints, ultima accion y velocidad objetivo.
- Accion: 12 offsets de posicion articular.
- Control interno: PD convierte esos objetivos en torques.
- Recompensa: avanzar a una velocidad objetivo, mantenerse derecho, no caerse, gastar poca energia y evitar que las patas traseras queden inactivas.

## Smoke test

```powershell
cd "C:\Users\tbond\OneDrive - Fundación UADE\Escritorio\UadeRobotLab\04Simuladores\EntrenamientoRLGo2"
py -3.10 .\scripts\smoke_test.py
```

## Entrenar

Prueba corta:

```powershell
.\train.ps1 -Timesteps 5000 -RunName prueba_corta
```

Prueba tecnica minima, solo para validar que todo corre:

```powershell
.\train.ps1 -Timesteps 1024 -RunName smoke_test
.\eval.ps1 -RunDir "runs\smoke_test" -Seconds 3
```

Entrenamiento mas serio:

```powershell
.\train.ps1 -Timesteps 1000000 -RunName ppo_go2_flat_v1
```

## Continuar entrenamiento

Si ya hay una politica aprendida y queres seguir entrenandola sin empezar desde cero:

```powershell
.\continue.ps1 -SourceRun "runs\ppo_go2_flat_v1" -Timesteps 1000000 -RunName ppo_go2_flat_v2
```

Esto carga:

- `runs\ppo_go2_flat_v1\model.zip`
- `runs\ppo_go2_flat_v1\vecnormalize.pkl`

Y guarda el resultado nuevo en:

```text
runs\ppo_go2_flat_v2
```

Para validar que puede cargar el modelo sin entrenar:

```powershell
.\continue.ps1 -SourceRun "runs\ppo_go2_flat_v1" -RunName ppo_go2_flat_v2 -CheckOnly
```

Si una politica aprende a avanzar usando casi solo las patas delanteras, conviene continuar con una nueva corrida para que se adapte a la recompensa actual:

```powershell
.\continue.ps1 -SourceRun "runs\ppo_go2_flat_v2" -Timesteps 1000000 -RunName ppo_go2_flat_v3_rear_legs
```

Si el run todavia no termino pero ya tiene checkpoints, se puede continuar desde el ultimo checkpoint completo:

```powershell
.\continue.ps1 -SourceRun "runs\ppo_go2_flat_v2" -SourceCheckpoint latest -Timesteps 1000000 -RunName ppo_go2_flat_v3_rear_legs
```

La observacion no cambia, asi que se puede continuar desde modelos anteriores. Lo que cambia es la recompensa: ahora penaliza saltos, inclinacion, cambios bruscos, poca actividad relativa de las patas traseras y poco levantamiento de los pies traseros.

Para medirlo sin abrir viewer:

```powershell
.\score.ps1 -RunDir "runs\ppo_go2_flat_v3_rear_fix_test" -Checkpoint latest -Deterministic
```

Senales utiles:

- `rear_ratio`: actividad de joints traseros comparada contra delanteros.
- `rear_clearance`: cuanto varian verticalmente los pies traseros en una ventana corta.
- `rear_clear_pen`: penalizacion aplicada por poco levantamiento de pies traseros.

## Evaluar

```powershell
.\eval.ps1 -RunDir "runs\ppo_go2_flat_v1" -Seconds 30
```

## Ver como aprende mientras entrena

El entrenamiento guarda checkpoints cada 25.000 pasos. Para ver el ultimo checkpoint sin cortar el entrenamiento:

```powershell
.\watch.ps1 -RunDir "runs\ppo_go2_flat_v1" -Once -Seconds 12
```

Para dejar un visor que espera checkpoints nuevos y los muestra automaticamente:

```powershell
.\watch.ps1 -RunDir "runs\ppo_go2_flat_v1" -Seconds 12 -Poll 60
```

Esto abre una evaluacion aparte. No modifica ni detiene el entrenamiento, pero puede consumir CPU mientras muestra el viewer.

## Escaleras y curriculum

El `scene.xml` oficial de Go2 trae obstaculos y escalones adelante del robot. Para una politica inicial de caminata eso es demasiado dificil: el agente todavia no sabe caminar, y ademas tiene que resolver impactos, altura de patas y recuperacion.

La ruta recomendada es:

- Piso plano: aprender equilibrio, direccion y velocidad.
- Piso con pequenas irregularidades: aprender robustez.
- Obstaculos bajos: aprender a levantar mas las patas.
- Escaleras: entrenar otra politica o continuar desde una politica plana ya buena.

## Nota honesta

Que el robot aprenda a caminar puede tardar bastante. Una politica util suele requerir cientos de miles o millones de pasos. Esta carpeta deja listo el pipeline para entrenar y evaluar; no promete una marcha buena en 30 segundos.
