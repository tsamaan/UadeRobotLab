# ADR-0007 — El dashboard marca qué dato es real, derivado o inventado

- **Estado:** Aceptada
- **Fecha:** 2026-09-19

## Problema

El simulador no calcula física (ver `../../../API.md`). De lo que muestra el
dashboard:

| Dato | En el simulador |
|---|---|
| ángulo, velocidad, yaw | **real** |
| torque, temperatura, roll, pitch, patas | **derivado** (calculado a partir de cómo se mueve) |
| batería | **inventado** (arranca en 87 % y baja lentísimo) |

Un gráfico de temperatura que sube cuando el robot camina **parece** una
medición. Si alguien pone una alarma a 50 °C basándose en el simulador, el
día del robot real puede fallar, porque ahí los números van a ser otros.

El comentario del backend (`entorno/sim/telemetria.py`) dice que lo derivado
viene marcado en la respuesta con un campo `derivado`. **Al mirar el JSON
real, ese campo no existe.**

## Soluciones evaluadas

| Opción | A favor | En contra |
|---|---|---|
| **A.** No marcar nada | cero trabajo | el dashboard presenta como mediciones cosas que no lo son |
| **B.** Leer el campo `derivado` del JSON | lo que dice el comentario del backend | **no existe**; el código no haría nada |
| **C.** Pedirle a la cátedra que agregue el campo | la solución correcta a largo plazo | no depende de nosotros ni llega a tiempo |
| **D.** Una tabla en el dashboard con el origen de cada dato, aplicada sólo si `/info.modo` es `"simulador"` | funciona hoy; desaparece sola con el robot real | si el simulador cambia, la tabla queda desactualizada |
| **E.** Una nota fija al pie del dashboard | simple | nadie lee las notas al pie; no dice cuál dato es cuál |

## Soluciones descartadas

- **A** — es justamente lo que la guía advierte que no hay que hacer.
- **B** — no hay nada que leer.
- **C** — vale la pena comentarlo (ver abajo), pero no resuelve el TP.
- **E** — no alcanza: el valor está en marcar **cada** dato, al lado del dato.

## Solución elegida

**D.** En `app.js`, la constante `ORIGEN_EN_SIMULADOR` copia la tabla de
`API.md`. En el HTML, cada título o columna lleva `data-origen="..."`, y
`armarPantalla()` le pone una marca de color:

- verde **real**, amarillo **derivado**, violeta **inventado**.

Arriba de todo, un aviso explica qué significan. Si `/info.modo` **no** es
`"simulador"`, no se muestra ni el aviso ni ninguna marca.

## Resultados esperados

- Nadie confunde un número derivado con una medición.
- Con el robot real, las marcas desaparecen solas.

## Resultados no esperados

- **La verdad sobre qué es real vive ahora en dos lugares**: en el backend y
  en nuestro dashboard. Si la cátedra cambia el simulador (por ejemplo,
  empieza a medir el torque), nuestras marcas mienten hasta que alguien
  actualice la tabla.
- Se encontró una **discrepancia entre la documentación y el código de la
  cátedra**: el campo `derivado` que promete el comentario no está. Conviene
  avisarles; si lo agregan, esta decisión se reemplaza por leer el campo
  (opción B).
- Pequeña diferencia entre documentos de la cátedra: `API.md` dice que la
  batería es "inventada" y `LEEME_ESTUDIANTE.md` la pone con los
  "derivados". Seguimos a `API.md`, que es el contrato.
