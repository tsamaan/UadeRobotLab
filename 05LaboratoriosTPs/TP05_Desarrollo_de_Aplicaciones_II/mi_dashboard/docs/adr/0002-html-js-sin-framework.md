# ADR-0002 — HTML + CSS + JavaScript, sin framework ni nada que instalar

- **Estado:** Aceptada
- **Fecha:** 2026-09-19

## Problema

Hay que elegir con qué construir el dashboard. El TP deja libertad total
("HTML + JS suelto, o el framework que prefieras"). Las condiciones reales
que pesan:

- El dashboard se usa en **dos lugares**: en nuestra compu mientras
  desarrollamos, y **en el laboratorio el día de la visita**, en una red donde
  puede no haber internet y en una máquina donde quizás no podamos instalar
  nada.
- Es un TP: el docente y los compañeros tienen que poder abrirlo y **leer el
  código** sin saber un framework en particular.
- Son cinco paneles y un flujo de datos. No es una aplicación grande.

## Soluciones evaluadas

| Opción | A favor | En contra |
|---|---|---|
| **A.** React / Vue / Svelte con Vite | componentes, estado ordenado, ecosistema enorme | necesita Node y `npm install`; paso de compilación; más difícil de leer para quien no sabe el framework |
| **B.** Framework por CDN (Vue o React con `<script>`) | sin compilar | **necesita internet** para bajar el framework; sigue siendo un framework que hay que conocer |
| **C.** Dashboard en Python (Streamlit, Dash) | todo en Python, como el backend | otro servidor más que levantar; no aprovecha el WebSocket del backend de forma natural; el TP es de desarrollo web |
| **D.** Grafana u otra herramienta armada | gráficos profesionales sin programar | hay que instalarla y configurarla; no se aprende a construir nada, que es el punto del TP |
| **E.** HTML + CSS + JavaScript sin nada más | abre con doble clic; anda sin internet; cualquiera lo lee; cero instalaciones | todo se hace a mano: actualizar la pantalla, dibujar los gráficos |

## Soluciones descartadas

- **A** — el costo de instalar y compilar no se justifica para cinco paneles,
  y complica el día de la visita.
- **B** — depender de internet en el laboratorio es un riesgo innecesario.
- **C** — suma un proceso más para levantar y aleja el TP de lo web.
- **D** — resuelve el problema sin que nosotros resolvamos nada.

## Solución elegida

**E.** Tres archivos: `index.html` (estructura), `estilos.css` (aspecto),
`app.js` (lógica). Sin dependencias de ningún tipo, ni siquiera por CDN.

## Resultados esperados

- Se abre con doble clic en cualquier sistema, sin internet.
- El código se lee de arriba abajo sin conocer ninguna librería.
- Ningún "en mi máquina anda": no hay versiones de nada que puedan diferir.

## Resultados no esperados

- **Los gráficos hay que dibujarlos a mano**, lo que trajo su propia decisión
  (ADR-0004) y bastante más código del que haría falta con una librería.
- Sin un framework que "redibuje solo", **hay que cuidar a mano cuándo y qué se
  actualiza** en la pantalla. Eso llevó al ADR-0005, y a la función
  `ponerTexto()`, que sólo toca el texto si cambió.
- Abrir el archivo con doble clic (`file://`) funciona porque el backend acepta
  pedidos de cualquier origen (CORS `*`). Si la cátedra lo restringiera,
  habría que servir la carpeta con `python3 -m http.server`.
- A favor: al no haber framework, **el recorrido de un dato se puede seguir
  entero** leyendo un solo archivo. Eso hizo posible `COMO_FUNCIONA.md`.
