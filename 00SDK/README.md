# SDKs Unitree

Esta carpeta contiene los SDKs oficiales usados por los ejemplos, simuladores y actividades del laboratorio.

## Repositorios

- `unitree_sdk2`: SDK oficial C++.
  - Origen: <https://github.com/unitreerobotics/unitree_sdk2>
- `unitree_sdk2_python`: SDK oficial Python.
  - Origen: <https://github.com/unitreerobotics/unitree_sdk2_python>

## Uso esperado

- `unitree_sdk2` se usa para ejemplos y proyectos C++.
- `unitree_sdk2_python` se usa para scripts Python, simulacion MuJoCo y wrappers docentes.

En Windows, para las actividades actuales con G1 visual, los profesores normalmente no tienen que tocar esta carpeta directamente. El launcher del simulador esta en:

```powershell
..\04Simuladores\UnitreeMujocoOficial\run_g1_sim.ps1
```

## Nota de versionado

Estas carpetas son repos Git clonados desde Unitree. Si se actualizan con `git pull`, el repo principal puede mostrar cambios en los gitlinks/submodulos.
