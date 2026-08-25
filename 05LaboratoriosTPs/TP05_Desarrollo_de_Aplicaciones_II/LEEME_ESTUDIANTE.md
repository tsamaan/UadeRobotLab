# TP05 — Desarrollo de Aplicaciones II
## Guía para el estudiante

Vas a hacer un **dashboard web** que muestra en vivo lo que le pasa a un robot
Unitree: ángulos de sus motores, temperatura, inclinación, batería.

Mientras desarrollás, el robot es simulado. El día de la visita, tu mismo
dashboard muestra datos del robot de verdad: sólo cambiás la IP.

---

## Paso a paso

### 1. Instalar (una sola vez)

Seguí **`INSTALACION.md`**. Este TP suma `fastapi` y `uvicorn`, que el script
instala solo.

### 2. Levantar el simulador y el backend

| Sistema | Qué hacés |
|---|---|
| **Windows** | doble clic en `INICIAR_TP05.bat` |
| **Linux / macOS** | doble clic en `INICIAR_TP05.sh` |

Elegís el robot (1 = G1, 2 = Go2). Se abre la ventana con el robot, arranca el
backend, y te muestra la dirección:

```
  TU DASHBOARD tiene que pegarle a:

        http://10.0.0.5:8001
```

> **Dejá esa ventana abierta** mientras desarrollás.

### 3. Tu dashboard

Ponelo en `mi_dashboard/`. Puede ser HTML + JS suelto, o el framework que
prefieras. Apuntá a la dirección que te mostró el script.

Probá primero desde el navegador: abrí `http://<IP>:8001/telemetria` y fijate
que llegue el JSON. Si eso anda, tu dashboard va a andar.

---

## Qué tenés que construir

Un dashboard que muestre en vivo:

- **Ángulos de los motores** — el dato más rico: 12 motores en el Go2, 29 en el G1
- **Temperatura** de cada motor
- **Inclinación** del robot (roll, pitch, yaw)
- **Batería**
- **Qué patas están apoyadas** (sólo Go2)

**Todo lo que necesitás está en `API.md`.** Leelo antes de escribir código.

---

## El robot se pasea solo

En el simulador el robot **camina por su cuenta**: avanza, gira, hace curvas y
para. Es a propósito: si estuviera quieto, todos tus gráficos serían líneas
rectas.

Vas a ver que cuando camina sube el torque y suben las temperaturas, y cuando
para bajan y las cuatro patas quedan apoyadas. **Tu dashboard tiene que dejar
ver eso.**

---

## Tiempo real: usá el WebSocket

Podés consultar `/telemetria` en un bucle, pero para gráficos en vivo es mejor:

```js
const ws = new WebSocket("ws://10.0.0.5:8001/ws");
ws.onmessage = (e) => actualizarGraficos(JSON.parse(e.data));
```

Llega ~10 veces por segundo, solo.

---

## ⚠️ Algo importante sobre los datos

El simulador **mueve el robot pero no calcula física**. Algunos valores son
reales y otros están **derivados**:

| Real | Derivado |
|---|---|
| ángulo de motor | torque |
| velocidad de motor | temperatura |
| yaw | roll y pitch |
| | fuerzas de pata |
| | batería |

Los derivados **son coherentes**: reaccionan a lo que el robot hace. Pero no son
mediciones. Contra el robot real esos números van a ser otros — tenelo en cuenta
si ponés umbrales o alarmas.

`API.md` tiene la tabla completa.

---

## Si algo no anda

**No llega nada** — abrí `http://<IP>:8001/telemetria` en el navegador. Si el
JSON aparece, el problema está en tu código; si no, el backend o el simulador se
cerraron.

**Todos los gráficos planos** — fijate que el robot se esté paseando en la
ventana del simulador. Si arrancaste con `--sin-paseo`, está quieto a propósito.

**El WebSocket se corta** — reconectá en el `onclose`. Es lo que haría cualquier
dashboard de producción.

**CORS** — el backend ya lo permite desde cualquier origen. Si tenés un error de
CORS, casi seguro estás apuntando a la dirección equivocada.
