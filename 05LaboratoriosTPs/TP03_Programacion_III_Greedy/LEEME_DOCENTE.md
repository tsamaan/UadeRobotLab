# TP03 — Programación III
## Guía para el docente · Greedy

---

## Qué es esto

Un laboratorio para que los alumnos implementen un planificador de rutas con
estrategia greedy (voraz) sobre un robot Unitree, sin necesidad de tener el robot delante.

Usa el **simulador oficial de Unitree** (`unitree_mujoco`) con el **SDK oficial
de Python**. La grilla se dibuja sobre la escena oficial, sin modificarla.

### Qué evalúa

Estrategias voraces: conjunto de candidatos, criterio de factibilidad, función
de selección y condición de finalización. Y sobre todo, **la diferencia entre
una decisión localmente óptima y una solución globalmente óptima**.

Los tres mapas están construidos y verificados para mostrar exactamente eso:

| Mapa | Óptimo (BFS) | Greedy | Resultado |
|---|---|---|---|
| `nivel1_directo` | 8 pasos | 8 pasos | óptimo |
| `nivel2_suboptimo` | 8 pasos | 12 pasos | **subóptimo** |
| `nivel3_bloqueo` | 8 pasos | se traba a los 12 | **falla** |

En el nivel 3, lo que condena al algoritmo es un **empate** resuelto por una
regla arbitraria. Es un buen disparador para la conclusión del TP.

---

## Paso a paso

1. **Instalación** (una vez por máquina): seguí `INSTALACION.md`.
   Para verificar sin abrir nada: `cd entorno && python3 -m sim --solo-revisar`
2. **Abrir el simulador**: doble clic en `INICIAR_SIMULADOR`. Pregunta el robot
   (1 = G1, 2 = Go2) y abre la ventana con la grilla.
3. **El alumno programa** en `mi_desarrollo/mi_tp03.py` y ejecuta con
   `EJECUTAR_MI_CODIGO`.
4. **Recibís** el archivo `entrega/ruta_apellido.json`.

---

## Qué te entregan

Un **JSON**, no un programa:

```json
{{
  "alumno": "Perez, Juan",
  "algoritmo": "greedy",
  "mapa": "Nivel 1 - Solucion directa",
  "inicio": [0, 0], "destino": [4, 4],
  "tamano_celda_metros": 0.5,
  "orientacion_inicial": "ESTE",
  "ruta": [[0,0], [0,1], ...],
  "pasos": 8,
  "estado": "DESTINO_ALCANZADO"
}}
```

Que sea un JSON y no código tiene una ventaja concreta: **no puede ejecutar nada
en tu máquina**. Se valida y se traduce, no se importa.

---

## Los mapas

| Mapa | Qué esperar |
|---|---|
| `practica_simple` | 3×3, para arrancar |
| `nivel1_directo` | greedy **llega**, y por el camino más corto (8 pasos) |
| `nivel2_suboptimo` | greedy **llega**, pero en 12 pasos cuando el mejor es 8 |
| `nivel3_bloqueo` | greedy **queda bloqueado**, aunque existe un camino de 8 pasos |

**El nivel 3 no es un error tuyo.** Existe un camino, pero llegar exige alejarse
temporalmente del destino, y el greedy nunca hace eso. El punto de quiebre es un
empate: desde la celda (2,3), la de la derecha y la de abajo están a la misma
distancia; elegir la de la derecha lleva a un callejón.

**Informar el bloqueo ES el resultado correcto.** No cambies el algoritmo para
forzar la solución: lo que se evalúa es que entiendas por qué falla.

Los mapas viven en `mi_desarrollo/mapas/`. Podés agregar los tuyos: mismo
formato, y el simulador los valida al cargarlos.

---

## Cómo se mueve el robot

El alumno razona en celdas; al robot le llegan **velocidad y tiempo**. Con celda
de 0.50 m, velocidad 0.25 m/s y giro 1.0 rad/s:

| Movimiento | Orden |
|---|---|
| Avanzar una celda | `avanzar(0.25, 2.00)` |
| Girar un cuarto de vuelta | `girar(±1.00, 1.57)` |

No hay grados ni metros en ninguna orden. La traducción está en
`entorno/sim/navegacion.py` y el alumno puede leerla.

### Límites de la materia

| | |
|---|---|
| Velocidad máxima | 0.25 m/s |
| Velocidad de giro | 1.00 rad/s |
| Tiempo por orden | 10 s |

Coinciden con la recomendación de la consigna (0,25 m/s). **Rechaza, no
recorta.**

---

## La validación de la ruta

Antes de mover nada, se verifica que la ruta:

- empiece en la celda de inicio
- no se salga de la grilla
- no pase por obstáculos ni zonas prohibidas
- no salte entre celdas no adyacentes
- no repita celdas
- no supere `maximo_pasos`

Si algo falla, **no se mueve el robot** y se listan los problemas. Esto corre
igual en el simulador y en el laboratorio físico.

---

## ⚠️ Qué NO simula

El simulador es **cinemático**: no corre física.

- El robot **se desliza**; las patas se animan pero es decorativo.
- **No se cae, no patina, no tiene inercia.**
- **No choca con los obstáculos**: los atraviesa si la ruta se lo pide. Por eso
  la validación previa no es opcional.
- La batería es un número fijo inventado.

Que un programa funcione en el simulador **no garantiza** que funcione en el
robot. Valida la **lógica**, que es lo que evalúa el TP.

El simulador oficial de Unitree no incluye el controlador de locomoción —corre
en la PC interna del robot y Unitree no lo publica—, así que este laboratorio lo
agrega y mueve el robot de forma cinemática.

---

## Cómo llega al robot real

El responsable del robot pone el JSON en `labs/laboratorio_tp03/rutas_alumno/`,
lo valida en `--dry-run` sin mover nada, y recién después lo ejecuta.

Antes de cualquier movimiento se verifica red, batería y estado del robot, y se
**bloquea** la ejecución si no se pueden confirmar.

---

## Problemas frecuentes

**`ERROR: could not create window` / se abre sin ventana 3D**

No cancela nada. Pasa en una VM sin GPU, por escritorio remoto, o —típico en
Linux— usando Python de Anaconda/Miniconda, que trae su propio `glfw` (la
pista es `EGL` en el error). El simulador **lo detecta y sigue en modo
consola, dibujando el recorrido del robot en texto**, y el TP se hace
completo. Si querés la ventana: `conda deactivate` y usar el Python del
sistema.

**No hace falta compilar ni instalar el SDK de Unitree**, ni CycloneDDS, ni
CMake. Alcanza con `pip install mujoco`.

**"El simulador ya está abierto" y no se ve nada** — quedó un proceso.
Linux: `pkill -f "python.*-m sim"`. Windows: cerrá la consola abierta.

**Se abre sin ventana 3D** — falta MuJoCo o la máquina no abre ventanas. El TP
se hace igual en modo consola, con `mostrar_mapa()`.

**`Could not locate cyclonedds`** — no debería aparecer más: CycloneDDS
ya no se usa. Si sale, estás con una carpeta vieja.

**pip falla con errores SSL** — agregá
`--trusted-host pypi.org --trusted-host files.pythonhosted.org`.
