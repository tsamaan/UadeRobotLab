# Politicas RL para Go2

Este carril es para locomocion realista en simulacion.

Estado actual:

- `unitree_mujoco` oficial no incluye el controlador `SportClient` del Go2 fisico.
- Para caminar bien en MuJoCo hay que cargar un controlador entrenado o entrenar uno.
- La integracion esperada es: observacion del simulador -> politica RL -> accion de 12 motores -> `LowCmd`.

Primer candidato externo para investigar:

- `cagataydev/sac-unitree-go2-mujoco` en Hugging Face: politica SAC para Unitree Go2 en MuJoCo, reportada con accion continua de 12 torques y observacion de 37 dimensiones.

Advertencia:

Una politica preentrenada solo sirve directamente si su entorno, orden de joints, escalas de observacion y accion coinciden con nuestro `unitree_mujoco`. Si no coinciden, hay que escribir un adaptador o reentrenar.

Proximo archivo a crear en este carril:

```text
rl_policy_runner.py
```

Ese runner deberia:

1. Suscribirse a `LowState` y `SportModeState`.
2. Construir la observacion esperada por la politica.
3. Ejecutar inferencia con `stable-baselines3`, `torch` u `onnxruntime`.
4. Convertir la accion en torques o posiciones.
5. Publicar `LowCmd`.

## Verificar dependencias

Desde `04Simuladores/UnitreeMujocoOficial`:

```powershell
py -3.10 -m pip install -r .\policies\requirements_rl.txt
.\policies\download_candidate_policy.ps1
.\run_rl_policy.ps1 -Check
```

Hoy el runner solo valida dependencias/modelo y documenta el punto de integracion pendiente. Para caminar con RL falta adaptar la observacion y accion de la politica elegida al simulador oficial.

El candidato descargado desde Hugging Face puede requerir compatibilidad de versiones: su `system_info.txt` indica Python 3.13, Stable-Baselines3 2.7.1 y NumPy 2.2.6. Si en esta maquina falla al cargar, la salida de `run_rl_policy.ps1 -Check` va a indicarlo.
