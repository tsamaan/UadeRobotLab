# ADR-0008 — Los datos están vivos si `ts` avanza, no si llegan mensajes

- **Estado:** Aceptada
- **Fecha:** 2026-09-19

## Problema

La primera versión decía "en vivo" si llegaban mensajes. Probando, la
pantalla decía **"en vivo · WebSocket — 10 datos/s"** pero los números
**no se movían**.

Qué pasaba: se había cerrado la ventana del simulador (y con ella el
simulador). El backend **siguió corriendo** y siguió mandando **el último dato
que tenía**, diez veces por segundo, idéntico. Visto desde el dashboard, la
conexión estaba perfecta.

Es el peor tipo de falla: **números muertos que parecen vivos**. Con el robot
real puede pasar lo mismo si se cuelga el programa que lee sus sensores.

## Soluciones evaluadas

| Opción | A favor | En contra |
|---|---|---|
| **A.** Mirar sólo si llegan mensajes | lo que ya teníamos | no detecta este caso |
| **B.** Comparar si el JSON entero cambió | no depende de ningún campo | con el robot quieto, algunos valores pueden repetirse legítimamente; comparar todo el JSON 10 veces por segundo es trabajo |
| **C.** Mirar si el campo `ts` avanza | un número; el backend lo genera con cada lectura nueva | depende de que `ts` signifique "hora del dato" (así se comporta) |
| **D.** Que el backend avise que perdió el simulador | la solución de fondo | no controlamos el backend |

## Soluciones descartadas

- **A** — es lo que falló.
- **B** — más caro y con falsos avisos si el robot está quieto.
- **D** — correcta, pero no está en nuestras manos (ver abajo).

## Solución elegida

**C.** En `recibir()`, si el `ts` del dato que llega es distinto al del
anterior, se anota la hora en `estado.ultimoAvance`. En
`actualizarPastilla()`, en este orden:

1. si no llega **ningún** mensaje por 2 s → **"no llegan datos"**;
2. si llegan pero `ts` no avanzó en 2 s → **"datos congelados"**;
3. si no → **"en vivo"**.

## Resultados esperados

- El dashboard distingue tres situaciones que antes parecían la misma:
  conexión caída, datos congelados y todo bien.
- Verificado: con el simulador cerrado y el backend vivo, la pastilla dice
  "datos congelados" mientras sigue mostrando "10 datos/s". Al reabrir el
  simulador, vuelve a "en vivo" sola.

## Resultados no esperados

- La medida "10 datos/s" **ya no significa "todo bien"**, y puede confundir
  junto a "datos congelados". Se dejó así a propósito: mostrar las dos cosas
  ayuda a diagnosticar (la red anda, el problema está del otro lado).
- Al reabrir el simulador, `ts` **saltó** (de ~32 a ~299). Mirando el backend
  (`entorno/api/telemetry_adapter.py`): `ts` son los segundos desde que
  arrancó **el backend** hasta que se recibió el dato. No afecta al dashboard,
  porque el gráfico usa la hora de llegada y no `ts`, pero sí a quien quiera
  usar `ts` como tiempo "del robot".
- **Hay un caso que esta solución no cubre.** Si un dato llega al backend
  *sin* hora propia, el backend le pone la hora actual, y entonces `ts` avanza
  aunque el dato esté congelado. Con los lectores actuales (simulador y robot
  real) eso no pasa, porque todos anotan la hora al recibir, pero depende de
  un detalle del backend que no controlamos.
- Vale la pena **avisarle a la cátedra**: si el backend expusiera "perdí la
  conexión con el simulador" (por ejemplo, en `/modo`), cualquier dashboard
  lo podría mostrar sin este truco.
