# Cómo funciona el dashboard (explicado desde cero)

Este documento asume que **no sabés nada** de robots, de telemetría ni de
WebSockets. Si ya sabés algo, saltá a la sección que te sirva.

1. [La idea en una frase](#1-la-idea-en-una-frase)
2. [Palabras que vas a leer](#2-palabras-que-vas-a-leer)
3. [Las piezas y cómo se conectan](#3-las-piezas-y-cómo-se-conectan)
4. [Cómo lo construimos, paso a paso](#4-cómo-lo-construimos-paso-a-paso)
5. [El viaje de un dato, del robot a tu pantalla](#5-el-viaje-de-un-dato-del-robot-a-tu-pantalla)
6. [Qué muestra cada panel y cómo leerlo](#6-qué-muestra-cada-panel-y-cómo-leerlo)
7. [Mapa del código](#7-mapa-del-código)
8. [El día del robot real](#8-el-día-del-robot-real)
9. [Si algo no anda](#9-si-algo-no-anda)
10. [Qué se podría agregar](#10-qué-se-podría-agregar)

---

## 1. La idea en una frase

El robot le cuenta a un programa (el **backend**) cómo está cada una de sus
partes, diez veces por segundo; nuestro **dashboard** es una página web que le
pregunta eso al backend y lo dibuja.

Es como el tablero de un auto: el motor no te habla a vos, le habla al tablero,
y el tablero te lo muestra con agujas y luces.

---

## 2. Palabras que vas a leer

| Palabra | Qué quiere decir, sin vueltas |
|---|---|
| **Telemetría** | *tele* = lejos, *metría* = medir. Medir algo que está lejos y mandarlo a otro lado para mirarlo. Lo que hace un auto de Fórmula 1 con los boxes. |
| **Dashboard** | Tablero. Una pantalla que junta muchos datos para leerlos de un vistazo. |
| **Backend** | El programa que está "atrás": habla con el robot y le ofrece los datos a quien los pida. Acá está hecho en Python con FastAPI. Nosotros **no** lo tocamos. |
| **Frontend** | Lo que ve la persona. Nuestro dashboard. |
| **API** | El "menú" del backend: qué se le puede pedir y qué devuelve. Está en `../API.md`. |
| **Endpoint** | Cada plato del menú. Ej: `/telemetria` devuelve todo, `/info` devuelve qué robot es. |
| **JSON** | El formato de los datos: texto con llaves y comillas, fácil de leer para personas y programas. `{"soc": 86}` = "la batería está en 86". |
| **HTTP** | La forma normal de pedir algo en la web: vos preguntás, el servidor contesta, se corta. Una pregunta, una respuesta. |
| **Polling** | Preguntar por HTTP una y otra vez: "¿cómo está?, ¿cómo está?, ¿cómo está?". Funciona, pero es insistente. |
| **WebSocket** | Una conexión que queda **abierta**. Vos te suscribís una vez y el servidor te va mandando datos solo, sin que preguntes. Como un grupo de WhatsApp contra mandar un mail cada vez. |
| **Hz** | "Veces por segundo". 10 Hz = 10 datos por segundo. |
| **Canvas** | Un rectángulo de la página donde se puede dibujar con código: líneas, círculos, texto. Así hacemos los gráficos. |
| **IMU** | El sensor que sabe hacia dónde está inclinado el robot. Da tres ángulos: **roll** (de costado, como un barco), **pitch** (de punta, como un avión que sube) y **yaw** (hacia dónde mira, como una brújula). |
| **SOC** | *State of charge*: el porcentaje de batería. |
| **Simulador cinemático** | Un simulador que mueve al robot "a mano" (le dice a cada articulación dónde estar) pero **no calcula física**: no hay peso, ni fricción, ni esfuerzo real. Por eso algunos datos se inventan de forma coherente. |
| **Derivado** | Un dato que no se midió: se calculó a partir de otros. En el simulador, el torque y la temperatura son derivados. |
| **ADR** | *Architecture Decision Record*: una ficha que cuenta una decisión importante, por qué se tomó y qué pasó después. Están en `adr/`. |

---

## 3. Las piezas y cómo se conectan

```
 ┌──────────────────────┐      ┌─────────────────────────┐       ┌───────────────────────┐
 │  SIMULADOR (MuJoCo)  │      │  BACKEND (FastAPI)      │       │  DASHBOARD (navegador)│
 │                      │      │  puerto 8001            │       │  mi_dashboard/        │
 │  mueve al robot y    │ ───▶ │                         │ ────▶ │                       │
 │  lo dibuja en 3D     │      │  GET /info              │ HTTP  │  index.html  (qué)    │
 │                      │      │  GET /telemetria        │   o   │  estilos.css (cómo)   │
 │  (el día de la       │      │  WS  /ws  ~10 por seg.  │  WS   │  app.js      (lógica) │
 │   visita: el robot   │      │                         │       │                       │
 │   de verdad)         │      │  (ya viene hecho)       │       │  (lo que hicimos)     │
 └──────────────────────┘      └─────────────────────────┘       └───────────────────────┘
```

Lo importante de este dibujo: **el dashboard sólo habla con el backend**. No
sabe si del otro lado hay un simulador o un robot de verdad. Por eso el día de
la visita alcanza con cambiar la IP.

---

## 4. Cómo lo construimos, paso a paso

Esto es lo que hicimos, en orden, incluyendo lo que salió mal. Cada decisión
importante tiene su ADR (entre corchetes).

### Paso 1 — Hacer andar el simulador

El `README` pide Python 3.10 o más nuevo; la Mac tenía **3.9**. Creamos un
entorno aparte con Python 3.13 en `~/.venvs/unitree` (el script de arranque ya
lo busca ahí) e instalamos `mujoco`, `fastapi` y `uvicorn`.

El simulador arrancó... **en modo texto**, sin ventana 3D. El log decía que en
macOS la ventana de MuJoCo sólo abre si el programa corre con `mjpython` en vez
de `python`. Con `mjpython` apareció el perro caminando. [ADR-0001]

### Paso 2 — Mirar los datos antes de escribir código

Antes de dibujar nada, le pedimos los datos al backend a mano:

```bash
curl http://localhost:8001/info
curl http://localhost:8001/telemetria
```

Así vimos **la forma real** del JSON (no la que uno se imagina). Dos
sorpresas:

- El **WebSocket no andaba**: al backend le faltaba la librería `websockets`,
  y nada la instala. Esto va a pasarle a más de uno. [ADR-0003]
- Un comentario del backend decía que los datos derivados venían marcados con
  un campo `derivado`. **No vienen.** [ADR-0007]

### Paso 3 — Elegir con qué hacerlo

HTML, CSS y JavaScript "a pelo", sin React, sin librerías de gráficos, sin
nada que instalar. Doble clic y anda, aunque no haya internet. [ADR-0002,
ADR-0004]

### Paso 4 — El esqueleto: `index.html`

Primero los "cajones" vacíos: barra de arriba con la IP, y cinco tarjetas
(batería, inclinación, patas, gráfico, tabla). Sin datos, sólo la estructura.

### Paso 5 — Conectarse: `app.js`, parte 1

1. Pedir `/info` para saber **qué robot es**. Con eso se arma la tabla con la
   cantidad justa de filas y los botones del gráfico. Nada de "12 motores"
   escrito a mano: si mañana es el G1, son 29. [ADR-0006]
2. Abrir el WebSocket. Si en 3 segundos no llegó nada, pasar al plan B:
   polling a `/telemetria`. [ADR-0003]

### Paso 6 — Dibujar: `app.js`, parte 2

Separamos **recibir** de **dibujar**. Cuando llega un dato, sólo se guarda.
Aparte, en cada refresco de pantalla (~60 veces por segundo) se dibuja lo
último que llegó. [ADR-0005]

Los tres dibujos (horizonte, patas, gráfico de líneas) están hechos con canvas.

### Paso 7 — Probar... y encontrar un bug que no era nuestro

Probando, el dashboard decía "en vivo" pero los números no se movían. El
simulador se había cerrado y **el backend seguía mandando el último dato diez
veces por segundo**, como si nada. Por fuera, todo parecía sano.

Arreglo: ahora el dashboard mira si el campo `ts` (la hora del dato) **avanza**.
Si no avanza por 2 segundos, avisa "datos congelados". Esto también va a pasar
con el robot real si se cuelga. [ADR-0008]

### Paso 8 — Probar el plan B

Forzamos que el WebSocket fallara y verificamos que el dashboard pasara solo a
polling y siguiera mostrando ~10 datos por segundo.

### Paso 9 — Probar con el otro robot

Cerramos todo y lo levantamos como **G1**. Sin tocar el código, el dashboard
mostró el nombre, las 29 filas y las dos rodillas en el gráfico. Dos
sorpresas: la guía dice que el G1 no reporta patas, pero el simulador **sí**
las manda; y el dibujo de las patas, pensado para el perro, quedaba apretado.
Le hicimos un dibujo propio al humanoide. [ADR-0006]

### Paso 10 — Retoques visuales

- La grilla dejaba una columna vacía en pantallas anchas: pasó a 3 columnas
  fijas (y 1 en pantallas chicas).
- Dos colores del gráfico eran casi iguales: se reordenó la paleta.
- El botón **Conectar** se salía de la pantalla en ventanas angostas.

---

## 5. El viaje de un dato, del robot a tu pantalla

Sigamos **un** dato: el ángulo del muslo delantero derecho (`FR_thigh`).

1. **El simulador** pone la pata en 45,8°.
2. **El backend** lo lee y arma un JSON con todo el robot:
   `{"ts": 16.24, "motores": [..., {"nombre": "FR_thigh", "angulo": 45.84, ...}], ...}`
3. **El WebSocket** se lo manda al navegador. Pasa ~10 veces por segundo.
4. **`ws.onmessage`** (en `app.js`) lo recibe y llama a **`recibir()`**, que:
   - lo guarda como "el último dato",
   - anota la hora en que llegó (para medir cuántos por segundo llegan),
   - si `ts` cambió respecto del anterior, anota que el dato **avanzó**,
   - agrega los ángulos al **historial** y tira lo que tenga más de 30 s.
5. **`cuadro()`** corre en cada refresco de pantalla. Si hay un dato nuevo:
   - escribe 45.8 en la celda de la tabla (sólo si cambió),
   - redibuja el horizonte y las patas.
   Y **siempre** redibuja el gráfico, para que se deslice suave.
6. **`dibujarGrafico()`** recorre el historial y une los puntos de `FR_thigh`
   con una línea verde.

Tiempo total, del simulador a la pantalla: unas centésimas de segundo.

---

## 6. Qué muestra cada panel y cómo leerlo

**Las marquitas de color** al lado de cada título dicen de dónde sale ese dato
en el simulador: **real** (verde), **derivado** (amarillo, calculado a partir de
cómo se mueve el robot) o **inventado** (violeta, la batería). Contra el robot
real las marquitas desaparecen, porque todo es medido.

| Panel | Qué ves | Qué mirar |
|---|---|---|
| **Batería** | barra y porcentaje | verde > 50 %, amarillo > 20 %, rojo el resto. En el simulador baja lentísimo. |
| **Inclinación** | un horizonte artificial, como el de un avión | la línea naranja es el robot; el cielo y la tierra se mueven. Si el horizonte se inclina, el robot está de costado (roll). Si sube o baja, está de punta (pitch). Las rayitas marcan cada 10°. |
| **Patas apoyadas** | el robot visto desde arriba, frente hacia arriba | verde lleno = pata en el piso, círculo vacío = pata en el aire. Caminando, se alternan **en diagonal**: delantera derecha con trasera izquierda. Parado, las cuatro verdes. Con el G1 se dibujan la cadera y los dos pies. |
| **Ángulo de motores** | una línea por motor, los últimos 30 s | Tocá los nombres para agregar o sacar motores. Por defecto: los muslos. **Vas a ver sólo dos líneas para cuatro motores**: no es un bug. El perro camina al trote, y en el trote las patas diagonales se mueven igual, así que sus líneas se tapan. |
| **Motores** | tabla con todo | La temperatura se pinta verde < 40 °C, amarilla < 50 °C, roja desde 50. Si el robot camina, sube; si frena, baja. |

---

## 7. Mapa del código

Todo lo interesante está en `app.js`, dividido en cinco secciones:

| Sección | Funciones | Qué hacen |
|---|---|---|
| **1. Conexión** | `conectar()` | pide `/info`; si falla, reintenta cada 3 s |
| | `abrirWebSocket()` | se suscribe a `/ws`; si en 3 s no llega nada, plan B |
| | `iniciarPolling()` | pide `/telemetria`; cuando contesta, espera 100 ms y vuelve a pedir |
| | `desconectar()` | limpia todo antes de una conexión nueva |
| **2. Armar la pantalla** | `armarPantalla()` | nombre del robot, aviso de simulador, marquitas |
| | `armarSelector()` | un botón por motor para el gráfico |
| | `armarTabla()` | una fila por motor, creadas una sola vez |
| **3. Recibir** | `recibir()` | guarda el dato, el historial y los tiempos |
| **4. Dibujar** | `cuadro()` | el "reloj" de la pantalla, ~60 veces por segundo |
| | `actualizarPastilla()` | decide qué dice el estado de la conexión |
| | `pintarDatos()` | batería, IMU, tabla |
| | `dibujarHorizonte()`, `dibujarPatas()`, `dibujarGrafico()` | los tres canvas |
| **5. Ayudas** | `prepararLienzo()` | ajusta el canvas a la pantalla para que no se vea borroso |
| | `pasoRedondo()` | elige marcas "lindas" para el eje: 1, 2, 5, 10, 20… |
| | `ponerTexto()` | cambia un texto sólo si es distinto (ahorra trabajo) |

Un detalle que aparece mucho: **`intento`**. Cada vez que te conectás, el número
sube. Toda respuesta que llega se fija si su `intento` sigue siendo el actual; si
no, la ignora. Sin esto, si cambiás de IP rápido, podrían mezclarse datos de dos
robots.

Los números que se pueden ajustar están todos juntos al principio de `app.js`:
cuántos segundos muestra el gráfico, cada cuánto se hace polling, a partir de
qué temperatura se pinta de rojo, etc.

---

## 8. El día del robot real

1. Conectá la compu a la misma red que el robot.
2. Pedile a la cátedra la IP del backend.
3. Escribila arriba y tocá **Conectar**.

Qué va a cambiar:

- El aviso de "estás viendo el simulador" y las marquitas desaparecen.
- Torque, temperatura, roll, pitch y batería van a ser **otros números**. Los
  umbrales de color de temperatura (40 y 50 °C) están pensados para el
  simulador; puede que haya que ajustarlos.
- Si la red es mala, vas a ver la pastilla pasar a "no llegan datos" o "datos
  congelados". Es a propósito: mejor saber que los datos están viejos que
  mirar números muertos creyendo que están vivos.

---

## 9. Si algo no anda

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| "sin conexión" | el backend no está corriendo, o la IP está mal | abrí `http://<IP>:8001/info` en el navegador. Si no aparece nada, el problema no es el dashboard. |
| "en vivo · polling" en vez de WebSocket | al backend le falta `websockets` | anda igual. Si querés WebSocket: `python -m pip install websockets` y reiniciá el backend. |
| "datos congelados" | se cerró el simulador (o la ventana 3D) | volvé a correr `INICIAR_TP05`. |
| el simulador abre sin ventana 3D en Mac | falta `mjpython` | ver ADR-0001. |
| los gráficos son líneas rectas | el robot está parado | fijate en la ventana 3D; si arrancó con `--sin-paseo`, está quieto a propósito. |
| error de CORS en la consola | casi seguro, IP o puerto equivocados | el backend acepta cualquier origen. |

---

## 10. Qué se podría agregar

- Gráficos en el tiempo de **torque y temperatura**, para ver cómo suben al
  caminar y bajan al frenar (hoy se ve en la tabla, pero sin historia).
- Alarmas: que una fila parpadee si un torque pasa cierto valor.
- Una brújula para el yaw.
- Pausar el gráfico para mirar un momento con calma.
- Exportar lo grabado a CSV.
