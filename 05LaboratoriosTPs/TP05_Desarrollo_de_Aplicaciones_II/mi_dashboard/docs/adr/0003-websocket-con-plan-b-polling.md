# ADR-0003 — WebSocket, y si no anda, polling automático

- **Estado:** Aceptada
- **Fecha:** 2026-09-19

## Problema

El backend ofrece los datos de dos formas:

- `WS /ws`: una conexión abierta por la que llegan ~10 datos por segundo
  sin pedirlos. Es lo que recomienda la guía.
- `GET /telemetria`: una respuesta por pedido.

Al probar el backend **tal como viene**, el WebSocket **no funcionaba**. El
servidor (`uvicorn`) necesita una librería extra, `websockets`, para
entenderlo, y ni el script de arranque ni la guía de instalación la instalan.
Sin ella, el pedido de WebSocket se rechaza.

O sea: lo recomendado puede no estar disponible en la máquina de un
compañero, en la del docente, o en el laboratorio el día de la visita. Y no
controlamos ninguna de esas máquinas.

## Soluciones evaluadas

| Opción | A favor | En contra |
|---|---|---|
| **A.** Sólo WebSocket | lo recomendado; menos tráfico; datos apenas se generan | si falta `websockets` en el backend, **el dashboard no muestra nada** |
| **B.** Sólo polling a `/telemetria` | anda siempre; más simple | 10 pedidos HTTP por segundo; un poco más de demora; no es lo que pide la guía |
| **C.** Server-Sent Events (SSE) | canal de un solo sentido, ideal para esto | el backend no lo ofrece y no lo podemos cambiar |
| **D.** Instalar `websockets` y listo | arregla la causa | arregla **nuestra** máquina, no la del laboratorio |
| **E.** WebSocket primero; si en 3 s no llegó nada, pasar solo a polling | lo mejor de A y B | dos caminos de código que probar |

## Soluciones descartadas

- **A** — un dashboard en blanco el día de la visita es el peor resultado
  posible, y depende de algo que no controlamos.
- **B** — funciona, pero desaprovecha el WebSocket cuando sí está.
- **C** — no está disponible.
- **D** — lo hicimos igual en nuestro entorno (ADR-0001), pero no alcanza como
  solución.

## Solución elegida

**E**, en `app.js`:

- `abrirWebSocket()` intenta conectarse a `/ws`.
- Si el WebSocket se cierra sin haber mandado nada, o si pasan 3 segundos
  (`ESPERA_WS_MS`) en silencio, se llama a `iniciarPolling()`.
- `iniciarPolling()` pide `/telemetria`, y **recién cuando llega la respuesta**
  programa el siguiente pedido a los 100 ms. Nunca hay dos pedidos en vuelo a
  la vez.
- Si el WebSocket **andaba y se corta** (se reinició el backend, se fue el
  wifi), se reintenta todo desde cero a los 3 segundos.
- La pastilla de estado dice por cuál camino están llegando los datos:
  "en vivo · WebSocket" o "en vivo · polling".

## Resultados esperados

- El dashboard muestra datos **con o sin** `websockets` en el backend.
  Verificado: con WebSocket llegan 10 datos/s; forzando el fallo, pasa a
  polling solo y llegan 9–10 datos/s.
- Se recupera solo si el backend se reinicia.

## Resultados no esperados

- **Cada conexión nueva tiene que invalidar a la anterior.** Al cambiar de IP,
  podía llegar tarde una respuesta de la conexión vieja y mezclar datos de dos
  robots. Se resolvió con el contador `intento`: toda respuesta de un
  `intento` que ya no es el actual se ignora. Es la parte menos obvia del
  código.
- **Hasta 3 segundos de pantalla vacía** al arrancar, si el WebSocket no
  responde ni cierra y hay que esperar el timeout para pasar al plan B.
- Esperar la respuesta antes de pedir de nuevo significa que, si la red es
  lenta, llegan **menos** de 10 datos por segundo. Es a propósito: pedir sin
  esperar apilaría pedidos y empeoraría todo.
- Descubrir que faltaba `websockets` es **útil para la cátedra**: con agregar
  esa librería a la instalación, el camino recomendado anda para todos.
