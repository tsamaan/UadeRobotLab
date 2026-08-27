# Contrato de la API — TP04

**Esto es contra lo que programás tu app.** Los endpoints, el JSON y los
códigos de error son **idénticos** en el simulador y en el robot real. El día
de la visita sólo cambiás la IP.

Base: `http://<IP>:8000` · Documentación viva: `http://<IP>:8000/docs`

---

## 1. Sesión — empezá siempre por acá

Un solo equipo controla el robot por vez. Sin token no te dejan mover nada.

### `POST /sesion/iniciar`

```json
{ "equipo": "Los Robotitos" }
```

Respuesta `200`:

```json
{ "ok": true, "equipo": "Los Robotitos", "token": "a1b2c3d4..." }
```

**Guardá el token.** Va en el header `X-Robot-Token` de todo lo que mueva el robot.

| Código | Qué pasó |
|---|---|
| `200` | tenés el control |
| `409` | otro equipo lo tiene. La respuesta dice cuál |

### `POST /sesion/finalizar`

```json
{ "token": "a1b2c3d4..." }
```

Liberá la sesión cuando terminás. Si no, se libera sola a los 10 minutos sin
comandos.

---

## 2. Mover el robot

### `POST /mover`

Header: `X-Robot-Token: <tu token>`

Hay **dos formas** de pedir un movimiento y las dos son válidas. Elegí una por
pedido: **mezclarlas da error**, porque sería ambiguo cuál manda.

| Forma | Cuándo se usa | Ejemplo |
|---|---|---|
| **Joystick** | control en vivo, el dedo apretado sobre un botón | `{"vx": 0.15}` |
| **Velocidad y tiempo** | una orden con principio y fin, como en los otros TPs | `{"velocidad": 0.2, "tiempo": 2.0}` |

---

#### Forma 1 — joystick

```json
{ "vx": 0.15, "vy": 0.0, "vyaw": 0.0 }
```

| Campo | Qué es | Rango |
|---|---|---|
| `vx` | adelante (+) / atrás (−) | −0.20 a 0.20 m/s |
| `vy` | costado izquierda (+) / derecha (−) | −0.20 a 0.20 m/s |
| `vyaw` | girar izquierda (+) / derecha (−) | −0.50 a 0.50 rad/s |

Las tres se aplican **al mismo tiempo**, así que podés combinarlas:

| Lo que querés | Qué mandás |
|---|---|
| Caminar hacia adelante | `{"vx": 0.2, "vy": 0, "vyaw": 0}` |
| Caminar hacia atrás | `{"vx": -0.2, "vy": 0, "vyaw": 0}` |
| **Girar sobre su eje** | `{"vx": 0, "vy": 0, "vyaw": 0.5}` |
| Desplazarse de costado | `{"vx": 0, "vy": 0.2, "vyaw": 0}` |
| **Curva**: avanzar girando | `{"vx": 0.15, "vy": 0, "vyaw": 0.4}` |
| Frenar | `{"vx": 0, "vy": 0, "vyaw": 0}` |

**Es un joystick, no un destino.** Cada `/mover` vale unos 0.4 segundos y
después el robot frena solo. Para que camine continuo, tu app tiene que mandar
`/mover` cada ~200 ms mientras el dedo esté apretado.

Eso es a propósito: si tu app se cierra, se corta el WiFi o soltás el control,
**el robot frena solo**.

> Si mandás más de lo permitido, **no falla**: se recorta al máximo y sigue.
> Un joystick que devuelve error en cada empujón sería inusable.
>
> Pero **te enterás**: cuando hubo recorte, la respuesta trae `recortado: true`
> y `pedido` con lo que habías mandado. Mostralo en tu app.

```json
{ "ok": true, "vx": 0.2, "vy": 0.0, "vyaw": 0.0,
  "recortado": true,
  "pedido": { "vx": 5.0, "vy": 0.0, "vyaw": 0.0 },
  "mensaje": "Se recorto al maximo permitido para esta materia. ..." }
```

---

#### Forma 2 — velocidad y tiempo

Es la primitiva de los otros seis TPs y la que usa el `LocoClient` del SDK.

```json
{ "velocidad": 0.2, "tiempo": 2.0 }
```

| Campo | Qué es | Rango |
|---|---|---|
| `velocidad` | adelante (+) / atrás (−) | −0.20 a 0.20 m/s |
| `velocidad_angular` | girar izquierda (+) / derecha (−) | −0.50 a 0.50 rad/s |
| `tiempo` | cuánto dura la orden | mayor que 0, hasta 2.0 s |

**La distancia y el ángulo son derivados**, nunca datos de entrada:

```
distancia = velocidad x tiempo        0.2 m/s x 2.0 s = 0.40 m
angulo    = velocidad_angular x tiempo   0.4 rad/s x 1.5 s = 0.60 rad
```

A diferencia del joystick, **este pedido no vuelve hasta que el movimiento
terminó**, y el robot frena solo al final. No hay que repetirlo.

Podés mandar `velocidad` y `velocidad_angular` juntas para hacer una curva.

##### Errores que vas a ver seguido

| Qué mandaste | Qué pasa |
|---|---|
| `{"velocidad": 0.2}` | **422** — falta `tiempo`. La distancia se deriva de los dos. |
| `{"vx": 0.2, "tiempo": 1}` | **422** — estás mezclando las dos formas. |
| `{"velocidad_x": 0.2}` | **422** — ese campo no existe. Antes esto devolvía `ok` y el robot no se movía. |
| `{"velocidad": 0.2, "tiempo": -1}` | **422** — el tiempo tiene que ser mayor que cero. |

### `POST /parar`

Header: `X-Robot-Token: <tu token>`. Sin body.

Frena el robot. Poné esto en el `onPressOut` de tus botones.

---

## 3. Acciones

### `GET /acciones`

Te dice qué puede hacer el robot conectado. **Consultalo al arrancar** en vez de
asumir: el G1 y el Go2 no tienen las mismas.

```json
{
  "tipo_robot": "g1",
  "acciones": [
    { "nombre": "saludo", "descripcion": "Saluda con la mano" },
    { "nombre": "dar_la_mano", "descripcion": "Extiende la mano para saludar" }
  ]
}
```

### `POST /accion/{nombre}`

Header: `X-Robot-Token: <tu token>`. Sin body.

```
POST /accion/saludo
POST /accion/dar_la_mano
```

| Código | Qué pasó |
|---|---|
| `200` | hecho |
| `403` | esa acción **no está permitida**. La respuesta explica por qué |
| `401` | te falta el token |

---

## 4. Estado

### `GET /estado`

No necesita token. Podés consultarlo siempre, incluso sin sesión.

```json
{
  "conectado": true,
  "bateria": 87,
  "tipo_robot": "g1",
  "nombre_robot": "Unitree G1 EDU",
  "sesion_activa": true,
  "equipo_activo": "Los Robotitos"
}
```

Útil para la pantalla de inicio: mostrar la batería y si alguien más está
usando el robot.

### `GET /historial`

Todo lo que se le pidió al robot. Sirve para depurar tu app.

---

## 5. ⚠️ Lo que la API NO hace, y no es un error

Hay cosas que **el robot puede hacer y la API no te deja pedir**:

| No disponible | Por qué |
|---|---|
| Prender o apagar el robot | lo hace el docente con el control oficial |
| Pararse, sentarse, agacharse | cambia la postura de un robot que quizás nadie está mirando |
| Bailar, saltar, dar volteretas | pueden romper el robot o lastimar a alguien |

Si pedís alguna, recibís **`403`** con el motivo. **No lo reportes como bug:**
es una decisión de seguridad.

Tu app se centra en **mover el robot y saludar**. Con eso alcanza y sobra para
un buen control remoto.

---

## 6. Resumen de códigos

| Código | Significa |
|---|---|
| `200` | salió bien |
| `401` | falta el token, es inválido, o venció la sesión |
| `403` | la acción no está permitida por seguridad |
| `404` | ese endpoint no existe |
| `409` | otro equipo tiene el control |
| `503` | el robot no pudo ejecutarlo |

---

## 7. Un flujo completo

```js
const API = "http://10.0.0.5:8000";   // la IP que muestra el script

// 1. tomar el control
const r = await fetch(`${API}/sesion/iniciar`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ equipo: "Los Robotitos" }),
});
const { token } = await r.json();

// 2. mover mientras el dedo esté apretado
const mover = (vx, vyaw) => fetch(`${API}/mover`, {
  method: "POST",
  headers: { "Content-Type": "application/json", "X-Robot-Token": token },
  body: JSON.stringify({ vx, vy: 0, vyaw }),
});

// 3. frenar al soltar
const parar = () => fetch(`${API}/parar`, {
  method: "POST",
  headers: { "X-Robot-Token": token },
});

// 4. saludar
const saludar = () => fetch(`${API}/accion/saludo`, {
  method: "POST",
  headers: { "X-Robot-Token": token },
});
```
