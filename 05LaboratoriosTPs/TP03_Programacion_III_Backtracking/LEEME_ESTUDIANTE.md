# TP03 — Programación III
## Guía para el estudiante · Backtracking

Vas a implementar un planificador con **backtracking**: una busqueda que
prueba caminos y, cuando uno no lleva a ningun lado, **deshace** y prueba otro.

Primero lo probás en el simulador; el día de la visita, el profesor ejecuta **tu
ruta** contra el robot de verdad.

---

## Paso a paso

### 1. Instalar (una sola vez)

Si es la primera vez en esta computadora, seguí **`INSTALACION.md`**.

### 2. Abrir el simulador

| Sistema | Qué hacés |
|---|---|
| **Windows** | doble clic en `INICIAR_SIMULADOR.bat` |
| **Linux / macOS** | doble clic en `INICIAR_SIMULADOR.sh` |

Elegís el robot (1 = G1 humanoide, 2 = Go2 perro) y se abre la ventana **con la
grilla dibujada en el piso**.

> Dejá esa ventana abierta mientras programás.

### 3. Escribir tu algoritmo

Abrí **`mi_desarrollo/mi_tp03.py`**. Completá tu nombre arriba, elegí el mapa, y
escribí donde dice `# TU CODIGO ACA`.

### 4. Ejecutarlo

Doble clic en `EJECUTAR_MI_CODIGO`, o `python3 mi_desarrollo/mi_tp03.py`.

Vas a ver el mapa en la consola, tu ruta, y el robot recorriéndola en 3D.

---

## Qué tenés que escribir

Una sola función: **`planificar_ruta(mapa)`**, que devuelve **dos cosas**:

```python
return ruta, estado
```

- `ruta`: lista de celdas, `[[0,0], [0,1], [1,1], ...]`, empezando en el inicio
- `estado`: uno de estos

| Estado | Cuándo |
|---|---|
| `DESTINO_ALCANZADO` | Encontraste un camino |
| `SIN_SOLUCION` | No existe ningún camino |
| `LIMITE_DE_PASOS` | Te pasaste de `mapa.maximo_pasos` |

### La idea del algoritmo

1. Marcá la celda actual como visitada y agregala a la ruta.
2. Si es el destino, terminaste.
3. Si no, probá cada vecino: arriba, derecha, abajo, izquierda.
4. Si un vecino lleva a la solución, listo.
5. Si **ninguno** funciona, **deshacé**: sacala de la ruta, desmarcala, y
   devolvé el control a quien te llamó.

El paso 5 es el corazón del backtracking. Es lo que le permite encontrar una
solución **siempre que exista**.

### Qué tenés disponible

```python
mapa.filas, mapa.columnas
mapa.inicio                  # tupla (fila, columna)
mapa.destino                 # tupla (fila, columna)
mapa.maximo_pasos
mapa.es_transitable(f, c)    # True si la celda existe y está libre
mapa.celda(f, c)             # 0 libre · 1 obstáculo · 2 zona prohibida
```

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

Para cambiar de mapa, editá la línea `MAPA = "..."` arriba de `mi_tp03.py`.

### Ver un mapa sin abrir el simulador

```python
from recorrido import cargar_mapa, mostrar_mapa
mostrar_mapa(cargar_mapa("nivel1_directo"))
```

---

## Cómo se mueve el robot

Vos trabajás en **celdas**. El robot se mueve en **velocidad y tiempo**.

La traducción la hace `recorrido.py`, que ya está hecho. Con una celda de 0.50 m:

| Movimiento en la grilla | Orden que sale al robot |
|---|---|
| Avanzar una celda | `avanzar(0.25, 2.00)` |
| Girar a la derecha | `girar(-1.00, 1.57)` |
| Girar a la izquierda | `girar(+1.00, 1.57)` |

> **distancia = velocidad × tiempo**  ·  **ángulo = velocidad × tiempo**

Al robot **nunca** le llegan celdas ni grados. El signo de la velocidad de giro
marca el sentido: positivo izquierda, negativo derecha.

### Tus límites

| | |
|---|---|
| Velocidad máxima | 0.25 m/s |
| Velocidad de giro máxima | 1.00 rad/s |
| Tiempo máximo por orden | 10 segundos |

Si algo se pasa, el programa **se detiene y te avisa**. No se recorta en
silencio.

---

## Los colores de la grilla

| Color | Qué es |
|---|---|
| Verde | inicio |
| Azul | destino |
| Rojo (caja alta) | obstáculo |
| Amarillo (baldosa) | zona prohibida |
| Esferas naranjas | tu ruta |

---

## Qué entregás

Al ejecutar tu programa se genera solo:

```
mi_desarrollo/entrega/ruta_apellido_nombre.json
```

**Ese archivo es lo que entregás.** Un solo JSON, no el programa.

Poné tu nombre en `ALUMNO` arriba de `mi_tp03.py`, así el archivo sale con tu
apellido.

---

## Si algo no anda

**"No encuentro el simulador"** — no está abierto. Volvé al paso 2.

**"LA RUTA NO SE PUEDE EJECUTAR"** — tu ruta tiene un problema: un salto entre
celdas no adyacentes, pasa por un obstáculo, o repite una celda. El mensaje dice
cuál.

**El robot no se mueve** — si el estado no es `DESTINO_ALCANZADO`, el programa
no mueve el robot a propósito.

---

## Una aclaración importante

El simulador **no es el robot**: no se cae, no patina, arranca y frena al
instante, y no choca con los obstáculos —los atraviesa si tu ruta se lo pide.

Por eso tu ruta se **valida** antes de ejecutarse. Que ande en el simulador
verifica que tu **algoritmo** es correcto, que es lo que se evalúa.
