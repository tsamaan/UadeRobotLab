# Registro de decisiones (ADR)

Un **ADR** (*Architecture Decision Record*) es una ficha corta que cuenta **una**
decisión importante: qué problema había, qué opciones se miraron, cuál se
eligió y qué pasó después. Sirve para que alguien que llega dentro de seis
meses (o vos mismo) entienda **por qué** el código es como es, y no sólo
**qué** hace.

Una regla: los ADR no se borran ni se reescriben. Si una decisión cambia, se
escribe un ADR nuevo que dice "reemplaza al ADR-000X".

## Índice

| # | Decisión | En una línea |
|---|---|---|
| [0001](0001-entorno-macos-mjpython.md) | Entorno de desarrollo en macOS | Python 3.13 en un entorno aparte y `mjpython` para ver la ventana 3D |
| [0002](0002-html-js-sin-framework.md) | Con qué se construye | HTML + CSS + JavaScript, sin framework ni nada que instalar |
| [0003](0003-websocket-con-plan-b-polling.md) | Cómo llegan los datos | WebSocket, y si no anda, polling automático |
| [0004](0004-graficos-canvas-propios.md) | Cómo se dibujan los gráficos | canvas dibujado a mano, sin librerías |
| [0005](0005-separar-recibir-de-dibujar.md) | Cuándo se dibuja | recibir guarda, un "reloj" aparte dibuja |
| [0006](0006-pantalla-armada-desde-info.md) | Go2 y G1 con el mismo código | la pantalla se arma según lo que responde `/info` |
| [0007](0007-marcar-datos-derivados.md) | Honestidad con los datos | el dashboard marca qué es real, derivado o inventado |
| [0008](0008-frescura-por-ts.md) | ¿Los datos están vivos? | se mira que `ts` avance, no que lleguen mensajes |

## Formato

Todas las fichas tienen las mismas secciones:

| Sección | Pregunta que contesta |
|---|---|
| **Problema** | ¿Qué había que resolver y por qué no era obvio? |
| **Soluciones evaluadas** | ¿Qué opciones había sobre la mesa, con sus pros y contras? |
| **Soluciones descartadas** | ¿Cuáles se dejaron de lado y por qué, concretamente? |
| **Solución elegida** | ¿Qué se hizo? |
| **Resultados esperados** | ¿Qué se buscaba lograr con esta decisión? |
| **Resultados no esperados** | ¿Qué trajo la decisión que **no** se buscaba? Costos, sorpresas, efectos secundarios, buenos o malos. |

La última sección es la más honesta y la más útil: toda decisión tiene un
precio, y conviene dejarlo escrito.

Para agregar uno nuevo, copiá [`plantilla.md`](plantilla.md) con el número
siguiente.
