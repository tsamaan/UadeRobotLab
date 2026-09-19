# ADR-0005 — Separar "recibir" de "dibujar"

- **Estado:** Aceptada
- **Fecha:** 2026-09-19

## Problema

Los datos llegan ~10 veces por segundo, pero no parejos: a veces dos juntos,
a veces con un hueco. La pantalla se refresca ~60 veces por segundo. Si
dibujamos **cada vez que llega un dato**:

- el gráfico avanza "a saltos", 10 veces por segundo, en vez de deslizarse;
- si llegan datos más rápido de lo que se puede dibujar, se hace trabajo que
  nunca se llega a ver;
- con la pestaña en segundo plano, se sigue dibujando para nadie.

Además, la tabla tiene 12 filas (Go2) o 29 (G1) con 4 números cada una.
Rehacerla entera en cada dato es mucho trabajo tirado.

## Soluciones evaluadas

| Opción | A favor | En contra |
|---|---|---|
| **A.** Dibujar todo dentro de `ws.onmessage` | lo más directo; lo que muestra el ejemplo de la guía | gráfico a saltos; trabajo innecesario; sigue en segundo plano |
| **B.** Dibujar con un `setInterval` fijo | ritmo parejo | no está sincronizado con la pantalla (puede dar tirones); sigue en segundo plano |
| **C.** Recibir sólo guarda; `requestAnimationFrame` dibuja | sincronizado con la pantalla; el navegador lo pausa solo en segundo plano; se dibuja una vez por cuadro aunque lleguen varios datos | dos partes que entender en vez de una |
| **D.** Rehacer la tabla con `innerHTML` en cada dato | una línea de código | se tira y se recrea todo el DOM de la tabla 10 veces por segundo |
| **E.** Crear las filas una vez y sólo cambiar el texto | mínimo trabajo | hay que guardar referencias a cada celda |

## Soluciones descartadas

- **A** — es el ejemplo de la guía y está bien para empezar, pero el gráfico
  a saltos se nota.
- **B** — igual de simple que C pero peor en todo.
- **D** — funciona, pero es el tipo de derroche que hace que un dashboard se
  ponga lento con el tiempo.

## Solución elegida

**C + E.**

- `recibir()` sólo guarda: el último dato, el historial para el gráfico y los
  tiempos de llegada. Marca `hayNuevo = true`.
- `cuadro()` corre con `requestAnimationFrame`. Si `hayNuevo`, actualiza
  tabla, batería, horizonte y patas. El gráfico lo redibuja **siempre**, porque
  el eje del tiempo avanza aunque no lleguen datos.
- `armarTabla()` crea las filas **una sola vez** y guarda las celdas en
  `estado.celdas`. Después, `ponerTexto()` sólo cambia un texto si es distinto
  al que ya había.

## Resultados esperados

- El gráfico se desliza suave, no a saltos.
- Nada se dibuja dos veces por cuadro, y nada se dibuja con la pestaña oculta.
- La tabla no se reconstruye nunca, sólo cambian números.

## Resultados no esperados

- **Si llegan dos datos en el mismo cuadro, el primero no se ve** en la tabla
  ni en el horizonte (sí queda en el historial del gráfico). Para mirar, está
  bien. Para **registrar** datos no serviría: habría que guardar cada uno.
- **Con la pestaña oculta, la pantalla se congela a propósito.** Al volver
  queda al día al instante, porque el historial se siguió llenando. Pero
  confunde al principio si uno no lo sabe. En las herramientas de captura de
  pantalla también se ve: la animación de la barra de batería puede
  aparecer "a medio llenar".
- La medida "datos/s" de la pastilla se calcula en el dibujo, pero cuenta las
  llegadas registradas en `recibir()`: es precisa aunque la pantalla vaya
  más lenta.
