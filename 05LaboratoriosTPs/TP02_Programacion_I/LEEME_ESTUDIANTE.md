# TP02 — Programación I
## Guía para el estudiante

Vas a construir un **controlador de misiones**: un programa que recibe una lista
de órdenes, las valida una por una, ejecuta las que están bien, rechaza las que
están mal, y al final muestra un reporte.

Primero lo probás en el simulador; el día de la visita, el profesor ejecuta **tu
mismo archivo** contra el robot de verdad.

---

## Paso a paso

### 1. Instalar (una sola vez)

Si es la primera vez en esta computadora, seguí **`INSTALACION.md`**.

El script de inicio intenta instalar solo lo que falte, así que probá primero
con el paso 2.

### 2. Abrir el simulador

| Sistema | Qué hacés |
|---|---|
| **Windows** | doble clic en `INICIAR_SIMULADOR.bat` |
| **Linux / macOS** | doble clic en `INICIAR_SIMULADOR.sh` |

Te pregunta qué robot querés (1 = G1 humanoide, 2 = Go2 perro) y abre la ventana.

> **Dejá esa ventana abierta** mientras programás.

### 3. Escribir tu programa

Abrí **`mi_desarrollo/mi_tp02.py`**. Está dividido en cuatro partes, y cada una
tiene un `# TU CODIGO ACA`.

### 4. Ejecutarlo

Doble clic en `EJECUTAR_MI_CODIGO`, o `python3 mi_desarrollo/mi_tp02.py`.

---

## Qué es una misión

Una **misión** es una lista de **comandos**. Cada comando es una tupla, donde el
primer elemento dice qué hacer:

```python
("avanzar", 0.2, 2.0)        # avanzar a 0.2 m/s durante 2 segundos
("girar", -0.5, 3.14)        # girar a -0.5 rad/s durante 3.14 segundos
("detenerse",)               # frenar
("saludar",)                 # saludar
```

Todo se expresa en **velocidad y tiempo**. Lo que el robot recorre sale de
multiplicar:

> **distancia = velocidad × tiempo**  ·  **ángulo = velocidad × tiempo**

`("avanzar", 0.2, 2.0)` recorre `0.2 × 2.0 = 0.4 metros`.

En los giros, la velocidad **positiva** gira a la izquierda y la **negativa** a
la derecha. `("girar", -0.5, 3.14)` gira `0.5 × 3.14 = 1.57 rad`, o sea 90
grados, hacia la derecha.

| Ángulo | Radianes |
|---|---|
| 90° | 1.5708 |
| 180° | 3.1416 |
| 360° | 6.2832 |

Te damos las misiones hechas en `misiones.py`. Vos escribís el controlador que
las procesa.

---

## Las cuatro partes del TP

| Parte | Función | Qué tiene que hacer |
|---|---|---|
| 1 | `comando_es_valido(comando)` | decir si un comando se puede ejecutar |
| 2 | `ejecutar_comando(robot, comando)` | ejecutar **un** comando |
| 3 | `ejecutar_mision(robot, mision, historial)` | recorrer la lista entera |
| 4 | `generar_reporte(historial)` | mostrar el resumen final |

**El orden importa.** Empezá por la 1, probala, y recién ahí seguí con la 2.
Es más fácil encontrar un error en 10 líneas que en 100.

### Cómo probar cada parte

Empezá con `MISION_BASICA`, que no tiene errores. Cuando eso funcione, cambiá a
`MISION_CON_ERRORES`.

Esa misión **tiene comandos inválidos a propósito**:

```python
("avanzar", 10.0, 0.2)      # 10 metros tardan 50 segundos: demasiado
("girar", 45, "arriba")     # "arriba" no es un sentido
("volar", 3)                # ese comando no existe
("avanzar", "mucho", 0.2)   # la distancia no es un numero
("avanzar", 0.3, 5.0)       # 5 m/s supera lo permitido
```

Tu controlador tiene que detectarlos, **no ejecutarlos**, y **seguir con el
resto**. Un comando malo no puede cortar la misión.

---

## Las órdenes del robot

```python
robot.conectar()
robot.verificar_estado()

robot.avanzar(velocidad=0.2, tiempo=2.0)     # m/s y segundos
robot.girar(velocidad=0.5, tiempo=3.14)      # rad/s y segundos

robot.saludar()
robot.detenerse()
robot.desconectar()
```

Los comandos de la misión tienen **exactamente esos dos datos**, en ese orden,
así que pasarlos al robot es directo.

---

## Tus límites en esta materia

| | |
|---|---|
| Velocidad máxima | 0.20 m/s |
| Velocidad de giro máxima | 0.50 rad/s |
| Tiempo máximo por orden | 10 segundos |

A 0.20 m/s, 10 segundos son **2 metros**. Por eso el comando de 50 segundos de
`MISION_CON_ERRORES` se rechaza.

Si pedís de más, el robot **lanza un error** en vez de recortar en silencio:

```
Velocidad 0.900 m/s: el maximo de tp02-programacion-i es 0.20 m/s.
Baja la velocidad y volve a probar.
```

Ese error se llama `ErrorDeSeguridad` y **lo podés atrapar**:

```python
try:
    robot.avanzar(velocidad=0.9, tiempo=2.0)
except ErrorDeSeguridad as error:
    print("Rechazado:", error)
```

Eso te sirve para la parte 2: aunque tu validación deje pasar algo, el robot te
avisa y tu programa puede seguir.

---

## Qué entregás

El archivo **`mi_tp02.py`**, con tu nombre completado arriba.

Poné tu apellido en el nombre, por ejemplo `tp02_perez_juan.py`.

No hace falta que entregues `misiones.py`: ese te lo dimos nosotros.

---

## Si algo no anda

**"No encuentro el simulador"** — no está abierto. Volvé al paso 2.

**El robot ejecuta el comando inválido igual** — tu `comando_es_valido()` está
devolviendo `True` cuando no debería. Probala sola, con un `print`, antes de
conectarla al resto.

**El robot gira para el lado equivocado** — el signo de la velocidad. Positiva
es izquierda, negativa es derecha.

**El programa corta en el primer comando malo** — te falta el `try/except` en la
parte 3, o estás cortando el bucle con un `return`.

**`python no se reconoce como un comando` (Windows)** — ver `INSTALACION.md`.

Cualquier otra cosa, avisale al profesor.

---

## Una aclaración importante

El simulador **no es el robot**: no se cae, no patina, arranca y frena al
instante.

Que tu programa ande en el simulador **no garantiza** que salga igual en el
aula. Sirve para verificar que tu **lógica** es correcta, que es lo que se
evalúa.
