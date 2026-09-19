# ADR-0006 — La pantalla se arma según lo que responde `/info`

- **Estado:** Aceptada
- **Fecha:** 2026-09-19

## Problema

Hay dos robots y son bastante distintos:

| | Go2 (perro) | G1 (humanoide) |
|---|---|---|
| Motores | 12 | 29 |
| Nombres | `FR_hip`, `FR_thigh`… | `L_hip_yaw`, `L_knee`… |
| Patas apoyadas | 4 (`FR`, `FL`, `RR`, `RL`) | según `API.md`, **no reporta** |

Desarrollamos con el Go2. El día de la visita puede tocar cualquiera de los
dos. La API dice explícitamente: *"Consultá `/info` en vez de asumir"*.

Encontramos además una inconsistencia: `API.md` dice que el G1 no reporta
patas, pero `/info` del G1 lista `R_foot` y `L_foot`, y al probarlo el
simulador **sí manda las dos, alternando al caminar**.

## Soluciones evaluadas

| Opción | A favor | En contra |
|---|---|---|
| **A.** Escribir el Go2 en el código (12 filas, 4 patas) | lo más rápido de hacer | con el G1 se rompe o muestra 12 de 29 motores |
| **B.** Dos versiones del dashboard, una por robot | cada una a medida | todo duplicado; cada arreglo, dos veces |
| **C.** Armar la pantalla con lo que dice `/info` | un solo código para los dos; si aparece un tercer robot, anda | un paso más antes de mostrar datos |
| **D.** Armarla con el primer dato que llega, sin `/info` | un pedido menos | el JSON de telemetría no trae el nombre ni el tipo del robot |

## Soluciones descartadas

- **A** — es justo lo que la API pide no hacer.
- **B** — el doble de mantenimiento para el mismo resultado.
- **D** — falta información (nombre, tipo, si es simulador o robot real).

## Solución elegida

**C.** `conectar()` pide `/info` primero, y `armarPantalla()` usa:

- `nombre`, `tipo`, `n_motores` → el título y la línea de detalle;
- `motores_nombres` → una fila de la tabla y un botón del gráfico por motor;
- `modo` → si es `"simulador"`, muestra el aviso y las marcas de ADR-0007.

Los motores elegidos por defecto para el gráfico son los que **más se mueven
al caminar**: los que tienen `thigh` (muslo, Go2) o `knee` (rodilla, G1) en el
nombre. Si no hay ninguno, los primeros cuatro.

Para las **patas**, no se confía en `/info.patas` ni en `API.md` sino en lo
que realmente llega en `fuerzas` en cada dato: se dibuja cada pata que llega
y tiene una posición conocida. El perro se dibuja con un lomo largo y cuatro
patas; el humanoide, con la cadera y dos pies. Si no llega ninguna, el panel
dice "Este robot no reporta qué patas están apoyadas" en vez de quedar vacío.

## Resultados esperados

- El mismo dashboard sirve para el Go2 y el G1 sin tocar una línea.
  Verificado con los dos: con el G1 aparecen el nombre, 29 filas, las dos
  rodillas en el gráfico y los dos pies alternando.

## Resultados no esperados

- **Con el G1, la tabla tiene 29 filas** y el selector 29 botones. Entra, pero
  la pantalla queda larga. No se resolvió porque no fue un problema al
  probar con el Go2.
- La **posición de cada pata en el dibujo** sí está escrita en el código
  (`POSICION_PATAS`), porque `/info` sólo da nombres, no dónde está cada una.
  Un robot nuevo con otros nombres de patas no se dibujaría.
- Los colores del gráfico se asignan por número de motor. Hubo que
  **reordenar la paleta** para que los elegidos por defecto de los dos robots
  (1, 4, 7, 10 y 3, 9) no cayeran en colores parecidos.
- **Riesgo con el G1 real.** El backend **siempre** manda las patas que lista
  `/info`: si el robot no publica ese dato, las rellena con 0. Si `API.md`
  tiene razón y el G1 real no lo reporta, el panel va a mostrar los dos pies
  "en el aire" todo el tiempo, y el dashboard no tiene forma de distinguir
  eso de un dato real. Hay que mirarlo el día de la visita; si pasa, lo
  honesto es ocultar el panel para el G1.
- Probar con el G1 mostró que el dibujo pensado para el perro quedaba
  apretado con dos pies (el texto "frente" se encimaba). Se hizo un dibujo
  aparte para el humanoide.
