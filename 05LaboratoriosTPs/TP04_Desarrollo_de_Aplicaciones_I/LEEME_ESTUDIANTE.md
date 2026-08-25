# TP04 — Desarrollo de Aplicaciones I
## Guía para el estudiante

Vas a hacer una **app móvil en React Native** que controla un robot Unitree como
si fuera un control remoto — pero hecho por vos.

Mientras desarrollás, el robot es **simulado**. El día de la visita, tu misma
app controla el robot de verdad: sólo cambiás la IP.

---

## Paso a paso

### 1. Instalar (una sola vez)

Seguí **`INSTALACION.md`**. Para este TP hacen falta además `fastapi` y
`uvicorn`, que el script instala solo la primera vez.

### 2. Levantar el simulador y el backend

| Sistema | Qué hacés |
|---|---|
| **Windows** | doble clic en `INICIAR_TP04.bat` |
| **Linux / macOS** | doble clic en `INICIAR_TP04.sh` |

Elegís el robot (1 = G1, 2 = Go2). Se abre la ventana con el robot y arranca el
backend. Al final te muestra esto:

```
  DESDE TU CELULAR, la app tiene que apuntar a:

        http://10.0.0.5:8000
```

**Anotá esa dirección.** Es la que va en tu app.

> **Dejá esa ventana abierta** mientras desarrollás.

### 3. Levantar tu app

```bash
cd mi_app
npx expo start
```

Escaneás el QR con Expo Go, o abrís el emulador.

### 4. Conectar

En tu app, apuntá a la dirección que te mostró el script.

| Dónde corre tu app | A qué apuntás |
|---|---|
| Celular con Expo Go | `http://<la-IP-que-te-mostró>:8000` |
| Emulador en la misma máquina | `http://localhost:8000` |

**El celular y la computadora tienen que estar en la misma red WiFi.**

---

## Qué tenés que construir

Una app que sea un control remoto:

- Botones o joystick para mover el robot: adelante, atrás, **girar sobre su
  eje**, de costado, y curvas (avanzar girando a la vez)
- Un botón de **parar**
- Un botón de **saludar**
- Mostrar el estado: batería, robot conectado, quién tiene el control

**Todo lo que necesitás saber está en `API.md`.** Leelo antes de escribir código.

---

## Lo que más se malentiende

**`/mover` es un joystick, no un destino.** Cada llamada vale unos 0.4 segundos
y después el robot frena solo. Para que camine continuo, tu app tiene que
mandar `/mover` cada ~200 ms mientras el dedo esté apretado.

Es a propósito: si tu app se cierra o se corta el WiFi, el robot frena solo en
vez de seguir caminando.

**Necesitás un token.** Primero `POST /sesion/iniciar`, y ese token va en el
header `X-Robot-Token` de todo lo que mueva el robot. Un solo equipo controla el
robot por vez.

---

## Los límites

| | |
|---|---|
| Velocidad | ±0.20 m/s |
| Giro | ±0.50 rad/s |

Si pedís más, **no falla**: se recorta y sigue. Un joystick que devuelve error
en cada empujón sería inusable.

---

## ⚠️ Lo que la API no te deja hacer

Hay cosas que el robot puede hacer y la API **no**: prenderlo o apagarlo,
pararlo, sentarlo, bailar, saltar, dar volteretas.

Si las pedís, recibís `403` con el motivo. **No es un bug**: es una decisión de
seguridad. Un robot de 35 kg controlado desde un celular, por alguien que quizás
no lo está mirando, no puede cambiar de postura ni hacer acrobacias.

Tu app se centra en **mover y saludar**. Con eso hacés un control remoto
completo.

---

## El día de la visita

El profesor levanta el backend en su notebook, con el robot conectado por cable.
Te va a dar:

- una **red WiFi** para conectar tu celular
- una **dirección** para apuntar tu app

**Cambiás sólo esa dirección en tu app.** Nada más: los endpoints, el JSON y los
errores son idénticos.

Los grupos pasan de a uno: mientras otro equipo tiene la sesión, tu
`/sesion/iniciar` va a devolver `409`. Cuando terminan, te toca.

---

## Si algo no anda

**La app no llega al backend** — el celular y la computadora tienen que estar en
la misma red. Probá abrir `http://<IP>:8000/docs` desde el navegador **del
celular**: si no carga, es la red, no tu código.

**`401` en todo** — te falta el token, o venció la sesión (10 minutos sin
comandos).

**`409` al iniciar sesión** — hay otra sesión abierta. En el simulador, puede
ser una tuya de antes: esperá el timeout o reiniciá el backend.

**El robot no se mueve pero recibo `200`** — probablemente mandás un solo
`/mover`. Acordate: hay que repetirlo mientras el dedo esté apretado.

**El simulador no abre la ventana 3D** — funciona igual en modo consola. El
backend y tu app andan lo mismo.
