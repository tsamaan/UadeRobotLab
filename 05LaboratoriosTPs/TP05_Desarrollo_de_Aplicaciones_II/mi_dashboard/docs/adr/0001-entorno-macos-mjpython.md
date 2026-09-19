# ADR-0001 — Entorno de desarrollo en macOS: Python 3.13 aparte y `mjpython`

- **Estado:** Aceptada
- **Fecha:** 2026-09-19

## Problema

Para desarrollar el dashboard hace falta el simulador corriendo. En la Mac de
desarrollo aparecieron dos obstáculos, uno atrás del otro:

1. El Python que trae macOS es el **3.9**, y el laboratorio pide **3.10 o más
   nuevo**. Además no tenía `mujoco` instalado.
2. Resuelto eso, el simulador arrancaba **sin ventana 3D**, en un modo texto
   que dibuja el recorrido con caracteres. El motivo, en el log:
   `launch_passive requires that the Python script be run under mjpython on macOS`.
   En Mac, la ventana de MuJoCo sólo abre con un lanzador especial,
   `mjpython`, que viene con el paquete. El script `INICIAR_TP05.sh` usa
   `python` común.

## Soluciones evaluadas

| Opción | A favor | En contra |
|---|---|---|
| **A.** Instalar con `pip` sobre el Python del sistema | un paso | es 3.9, no cumple el mínimo; ensuciar el Python del sistema es mala práctica |
| **B.** Actualizar el Python del sistema | — | en macOS no se puede reemplazar sin romper cosas |
| **C.** Entorno virtual con el Python 3.13 de Homebrew, en `~/.venvs/unitree` | aislado; no toca nada más; el script de arranque **ya busca** esa ruta primero | un paso extra la primera vez |
| **D.** Usar `uv` para crear el entorno | muy rápido | otra herramienta que explicar; el script no la conoce |
| **E.** Seguir en modo texto (sin ventana 3D) | cero trabajo | el objetivo inicial era justamente ver el robot en 3D |
| **F.** Correr el simulador con `mjpython` | una palabra de diferencia; viene con `mujoco` | el script oficial no lo hace: hay que lanzarlo a mano (o modificar el script) |

## Soluciones descartadas

- **A y B** — no cumplen la versión mínima o rompen el sistema.
- **D** — funciona, pero suma una herramienta sin ganar nada que importe acá.
- **E** — el modo texto alcanza para el backend, pero no para verificar que el
  robot se mueve como dicen los datos.

## Solución elegida

**C + F.** Entorno virtual con Python 3.13 en `~/.venvs/unitree`, con `mujoco`,
`fastapi`, `uvicorn` y `websockets` (ver ADR-0003 por este último). El
simulador se lanza con:

```bash
~/.venvs/unitree/bin/mjpython -m sim --robot go2 --materia tp05
```

(desde `entorno/`), y el backend con el Python del mismo entorno.

## Resultados esperados

- Simulador con ventana 3D y backend funcionando en la Mac.
- Nada instalado por fuera del entorno: se borra la carpeta y queda todo como
  estaba.

## Resultados no esperados

- **El doble clic en `INICIAR_TP05.sh` no muestra el robot en 3D en Mac.** El
  script encuentra el entorno, pero lo corre con `python` y el simulador cae al
  modo texto. Hay que lanzarlo a mano con `mjpython`, o modificar el script.
  Seguramente les pase a otros compañeros con Mac.
- Instalar Python con Homebrew obligó antes a aceptar la licencia de Xcode
  (`sudo xcodebuild -license`); sin eso **tampoco andaba `git`**.
- Si se cierra la ventana 3D, **se cierra el simulador**, pero el backend
  sigue vivo. Eso llevó a descubrir el problema del ADR-0008.
