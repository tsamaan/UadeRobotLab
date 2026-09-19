# ADR-0004 — Gráficos dibujados a mano en canvas, sin librerías

- **Estado:** Aceptada
- **Fecha:** 2026-09-19

## Problema

Hacen falta tres dibujos que cambian ~10 veces por segundo:

- un **gráfico de líneas** con el ángulo de varios motores en los últimos
  30 segundos, que se desplace suave;
- un **horizonte artificial** para roll y pitch;
- un **esquema del robot visto desde arriba** con las patas apoyadas.

Sólo el primero es un "gráfico" tradicional. Los otros dos son dibujos a
medida que ninguna librería de gráficos trae hechos. Y por el ADR-0002 no
queremos depender de internet.

## Soluciones evaluadas

| Opción | A favor | En contra |
|---|---|---|
| **A.** Chart.js | conocida; ejes, leyendas y tooltips hechos | por CDN necesita internet; copiarla al proyecto son ~200 KB ajenos; no hace horizonte ni patas; con datos en vivo hay que desactivar sus animaciones |
| **B.** uPlot | muy rápida para series de tiempo | mismo problema de dependencia; sólo resuelve el gráfico de líneas |
| **C.** Plotly | muy completa | pesada (MB); mucho más de lo que hace falta |
| **D.** SVG armado con JavaScript | cada línea es un elemento; se inspecciona fácil | recrear cientos de puntos 60 veces por segundo en el DOM es caro |
| **E.** `<canvas>` dibujado a mano | cero dependencias; un solo enfoque para los tres dibujos; rápido | hay que hacer a mano ejes, escala, grilla y nitidez en pantallas retina |

## Soluciones descartadas

- **A, B y C** — suman una dependencia y resuelven sólo uno de los tres
  dibujos. Igual habría que aprender canvas para los otros dos.
- **D** — funcionaría, pero es más lento para redibujar todo en cada cuadro, y
  el gráfico se redibuja siempre (ADR-0005).

## Solución elegida

**E.** Tres funciones en `app.js`: `dibujarGrafico()`, `dibujarHorizonte()` y
`dibujarPatas()`, más dos ayudas compartidas:

- `prepararLienzo()` ajusta la resolución interna del canvas a la densidad de
  la pantalla (`devicePixelRatio`) para que no se vea borroso en pantallas
  retina, y lo deja limpio para dibujar.
- `pasoRedondo()` elige las marcas del eje Y en pasos "humanos" (1, 2, 5, 10,
  20…) en vez de números como 7,3.

El eje Y del gráfico se adapta a los motores elegidos, con un rango mínimo de
10° para que un motor casi quieto no parezca un terremoto.

## Resultados esperados

- Los tres dibujos, sin ninguna dependencia.
- El gráfico se desliza suave (se redibuja en cada refresco de pantalla).

## Resultados no esperados

- **Hubo que resolver cosas que una librería trae gratis:** nitidez en retina,
  escala automática, marcas del eje, recorte de líneas fuera del área.
- **No hay tooltips ni zoom.** Pasar el mouse por el gráfico no muestra el
  valor. Para ver números exactos está la tabla.
- **El canvas es invisible para lectores de pantalla**: para una persona
  ciega el gráfico no existe. Es otra razón para que todos los números
  también estén en la tabla, que sí es texto.
- El dibujo reveló algo del robot que no esperábamos: con los cuatro muslos
  elegidos se ven **sólo dos líneas**. No es un bug. El Go2 camina al trote,
  donde las patas diagonales se mueven igual (delantera derecha con trasera
  izquierda), y sus líneas se tapan. Se confirma con el panel de patas.
