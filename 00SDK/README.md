> # ⛔ ESTO NO ES PARA LOS LABORATORIOS DE LOS TPs
>
> **Si estás acá buscando cómo instalar tu TP, te equivocaste de carpeta.**
>
> Andá a **[`05LaboratoriosTPs/`](../05LaboratoriosTPs/)**, entrá a la carpeta
> de tu materia y seguí su `INSTALACION.md`.
>
> **Los laboratorios NO necesitan el SDK de Unitree.** Se instalan con un solo
> `pip install mujoco`. El SDK solo hace falta para conectarse al robot físico,
> y de eso se ocupa el responsable del laboratorio, no vos.
>
> Las carpetas de acá abajo además **están vacías**: son enlaces a repositorios
> de Unitree que no se descargan solos.
>
> ⚠️ **El launcher que se menciona más abajo (`run_g1_sim.ps1`) es de un taller
> anterior y no sirve para los TPs.** Instala CycloneDDS y el SDK, que fallan en
> Windows y macOS con Python 3.11 o más nuevo.
>
> **Se conserva por valor histórico. No se borra nada, pero no lo uses para dar
> clase.**

---

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
