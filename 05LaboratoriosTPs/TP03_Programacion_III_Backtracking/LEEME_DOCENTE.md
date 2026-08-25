# TP03 — Programación III
## Guía para el docente · Backtracking

---

## Qué es esto

Un laboratorio para que los alumnos implementen un planificador de rutas con
backtracking recursivo sobre un robot Unitree, sin necesidad de tener el robot delante.

Usa el **simulador oficial de Unitree** (`unitree_mujoco`) con el **SDK oficial
de Python**. La grilla se dibuja sobre la escena oficial, sin modificarla.

### Qué evalúa

Recursión y backtracking: generar candidatos, explorar en profundidad, y
**deshacer** cuando una rama no lleva a la solución.

El backtracking es **completo**: encuentra una solución siempre que exista. Eso
lo distingue del greedy, y `nivel3_bloqueo` está puesto para mostrarlo — greedy
se traba ahí, backtracking llega.

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
  "algoritmo": "backtracking",
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
| `nivel1_directo` | camino de 8 pasos |
| `nivel2_suboptimo` | camino de 8 pasos, con más obstáculos |
| `nivel3_bloqueo` | camino de 8 pasos. **Backtracking lo encuentra.** |

En `nivel3_bloqueo` una estrategia greedy queda encerrada, pero el backtracking
llega igual, porque deshace sus elecciones. Vale la pena mirar ese mapa: es la
diferencia entre los dos enfoques.

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

**"El simulador ya está abierto" y no se ve nada** — quedó un proceso.
Linux: `pkill -f "python.*-m sim"`. Windows: cerrá la consola abierta.

**Se abre sin ventana 3D** — falta MuJoCo o la máquina no abre ventanas. El TP
se hace igual en modo consola, con `mostrar_mapa()`.

**`Could not locate cyclonedds`** — ver `INSTALACION.md`, paso 3.

**pip falla con errores SSL** — agregá
`--trusted-host pypi.org --trusted-host files.pythonhosted.org`.
