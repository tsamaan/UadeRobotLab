# Contrato de la API — TP05

**Esto es contra lo que programás tu dashboard.** Los endpoints y el JSON son
**idénticos** en el simulador y en el robot real. El día de la visita sólo
cambiás la IP.

Base: `http://<IP>:8001` · Documentación viva: `http://<IP>:8001/docs`

**Es sólo lectura.** No hay ningún endpoint que mueva el robot: este TP es de
visualización.

---

## Los endpoints

| Endpoint | Qué devuelve |
|---|---|
| `GET /telemetria` | **todo junto**: motores, IMU, batería, patas |
| `GET /motores` | sólo los motores |
| `GET /imu` | sólo la inclinación |
| `GET /bms` | sólo la batería |
| `GET /fuerzas` | qué patas están apoyadas |
| `GET /info` | nombre y tipo del robot, cantidad de motores |
| `WS /ws` | **tiempo real**, ~10 veces por segundo |

---

## `GET /telemetria`

```json
{
  "modelo": "go2",
  "ts": 16.24,
  "motores": [
    { "id": 0, "nombre": "FR_hip", "angulo": 45.84,
      "velocidad": -0.218, "torque": 1.31, "temperatura": 30.0 }
  ],
  "imu":     { "roll": -1.39, "pitch": -1.06, "yaw": 78.2,
               "ax": -0.043, "ay": -0.012, "az": 9.79 },
  "bms":     { "soc": 86, "corriente": 0, "temperatura": 0.0, "celdas": [] },
  "fuerzas": { "FR": 1, "FL": 0, "RR": 0, "RL": 1 }
}
```

| Campo | Unidad |
|---|---|
| `angulo` | grados |
| `velocidad` | rad/s |
| `torque` | Nm |
| `temperatura` | °C |
| `roll` `pitch` `yaw` | grados |
| `soc` | % de batería |
| `fuerzas` | 1 = apoyada, 0 = en el aire |

El Go2 tiene 12 motores y 4 patas; el G1 tiene 29 motores y no reporta patas.
**Consultá `/info` en vez de asumir.**

---

## Tiempo real con WebSocket

```js
const ws = new WebSocket("ws://10.0.0.5:8001/ws");
ws.onmessage = (e) => {
  const t = JSON.parse(e.data);   // el mismo JSON que /telemetria
  actualizarGraficos(t);
};
```

Llega ~10 veces por segundo. Para gráficos en vivo es mejor que consultar
`/telemetria` en un bucle.

---

## ⚠️ Qué es real y qué está derivado

El simulador es **cinemático**: mueve el robot pero no calcula física. Así que
algunos valores son medidos y otros **derivados del estado del robot**:

| Dato | En el simulador |
|---|---|
| Ángulo de motor | **real** |
| Velocidad de motor | **real** (derivada del movimiento) |
| Yaw | **real** |
| Torque | **derivado** del esfuerzo de cada articulación |
| Temperatura | **derivada**: sube con el uso, baja al frenar |
| Roll / pitch | **derivados**: oscilación al caminar |
| Fuerzas de pata | **derivadas** de la fase de la marcha |
| Batería | **inventada** (arranca en 87 % y baja lentísimo) |

**Los derivados son coherentes, no ruido.** Si el robot camina, sube el torque y
suben las temperaturas; si frena, bajan y las cuatro patas quedan apoyadas. Tu
dashboard va a reaccionar a lo que el robot hace.

Pero **no son mediciones**: contra el robot real esos números van a ser otros.
Conviene que lo tengas en cuenta si tu dashboard pone umbrales o alarmas.

---

## El robot se pasea solo

En el simulador el robot **camina un recorrido por su cuenta**: avanza, gira,
hace curvas y para. Es a propósito: si estuviera quieto, todos tus gráficos
serían líneas rectas y no habría nada que visualizar.

Si preferís el robot quieto para probar algo puntual, el simulador acepta
`--sin-paseo`.

---

## Ideas para el dashboard

- Un gráfico de líneas con el ángulo de varios motores en el tiempo
- Temperatura por motor, con color según qué tan caliente está
- Un indicador de batería
- Las patas apoyadas, como un diagrama del robot visto desde arriba
- Roll y pitch como un horizonte artificial
- Alarma cuando un torque pasa cierto umbral
