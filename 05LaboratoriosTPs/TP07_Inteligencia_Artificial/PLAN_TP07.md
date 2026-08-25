# Plan del TP07 — Inteligencia Artificial (agente de lenguaje natural)

Fecha: 2026-08-24
Estado: **analizado y organizado. Sin implementar.**
Fuentes leídas: consigna oficial (16 páginas), `labs/laboratorio_tp07/` completo,
los 25 casos de prueba.

---

## 1. Qué pide el TP

El alumno escribe un **agente** que recibe texto en español y lo convierte en
acciones del robot. Robot especificado por la consigna: **Unitree G1**.

El pipeline tiene cuatro etapas, y la consigna insiste en que sean
**independientes entre sí**:

```
  texto  →  Clasificador  →  Extractor de   →  Validador de  →  Ejecutor
            de intención     parámetros        seguridad        o rechazo
```

| Etapa | Qué hace |
|---|---|
| Clasificador | `MOVER` · `GIRAR` · `DETENERSE` · `SALUDO` · `CONSULTAR_ESTADO` · `DESCONOCIDO` |
| Extractor | saca números del texto con expresiones regulares |
| Validador | **última barrera**: rechaza lo peligroso, imposible o fuera de rango |
| Ejecutor | manda al robot, o muestra el rechazo |

### Tres niveles, a elección del alumno

| Nivel | Enfoque | Requiere |
|---|---|---|
| 1 | reglas y regex | nada (el del taller) |
| 2 | árbol de decisión | `scikit-learn` |
| 3 | LLM con prompt | clave de API |

**El paquete tiene que funcionar con el nivel 1 sin instalar nada extra.** Los
otros dos son extensión, y el simulador no puede depender de ellos.

### Cómo se evalúa

- Accuracy ≥ **70 %** sobre los 25 casos.
- El validador bloquea el **100 %** de los casos peligrosos.
- El validador es un **componente independiente**, no reglas metidas dentro del
  clasificador.

Los 25 casos, contados: **17 EJECUTAR · 6 BLOQUEADO · 2 DESCONOCIDO**.
Intenciones: 8 MOVER, 5 GIRAR, 5 DESCONOCIDO, 3 DETENERSE, 2 SALUDO,
2 CONSULTAR_ESTADO.

---

## 2. ⚠️ La tensión que hay que resolver primero

Nuestra regla es **todo movimiento en velocidad y tiempo**. Pero la consigna
extrae `distancia_m`, `angulo_deg`, `velocidad_ms`, y **la gente habla así**:

> *"avanzá 2 metros"* · *"girá 90 grados a la derecha"* · *"caminá despacio"*

Nadie le dice a un robot *"avanzá a 0.2 m/s durante 10 segundos"*. Si forzamos
los casos de prueba a velocidad y tiempo, el TP deja de ser de lenguaje natural
y pierde todo el sentido.

### La resolución: la conversión es una etapa del pipeline

La propia consigna separa el **Ejecutor** de las etapas de NLP. **Ese es el
lugar donde va la conversión**, y encaja sin forzar nada:

```
  texto  →  Clasificador  →  Extractor    →  Validador   →  EJECUTOR  →  robot
            (natural)        metros,          metros,        VELOCIDAD
                             grados           grados         y TIEMPO
```

| Etapa | Unidades | Por qué |
|---|---|---|
| Clasificador y Extractor | metros, grados | es lenguaje humano; es el objeto de estudio |
| Validador | metros y grados, **y también** velocidad y tiempo | valida en las dos representaciones |
| **Ejecutor** | **velocidad y tiempo, siempre** | es lo único que toca el SDK |

**Al robot nunca le llega un metro ni un grado.** La regla se cumple donde
importa, y convertir pasa a ser parte de lo que el TP enseña.

Además, esto ya está medio hecho: `ejecutor_real.py` del laboratorio físico
convierte `duracion = distancia / velocidad` para avanzar. Falta hacer lo mismo
con `girar`, que sigue en grados y sentido.

---

## 3. Los límites: la consigna vs los nuestros

Acá hay que decidir, porque **no coinciden**.

| | Consigna (validador) | Consigna (aula) | Lab físico hoy | Nuestro perfil TP07 | Techo físico |
|---|---|---|---|---|---|
| Velocidad | 0.5 m/s | 0.3 m/s | 0.3 m/s | **0.20 m/s** | 0.25 m/s |
| Distancia | 5 m | — | 1.5 m | derivada | — |
| Ángulo | 180° | — | 180° | derivado | — |
| Batería | — | **25 %** | 25 % | 25 % | 25 % |
| Tiempo por orden | — | — | — | **5 s** | 10 s |

Dos choques concretos:

1. **La consigna permite 0.5 m/s; nuestro techo es 0.25.** El caso
   *"muévete a 2 m/s"* se bloquea igual, pero un *"caminá rápido"* que la
   consigna mapea a 0.5 m/s **ahora también se bloquea**. Hay que revisar los 25
   casos contra nuestros límites.

2. **"avanzá 2 metros" no entra en una sola orden.** A 0.20 m/s son 10 s, y
   nuestro tope por orden son 5 s. Dos salidas:
   - **(a)** el Ejecutor **parte el movimiento** en tramos de 5 s. Invisible
     para el alumno, y coherente con el "encadenar órdenes" de TP01 y TP02.
   - **(b)** subir `duracion_max` del TP07 de 5 s a 10 s, como el TP02. Sigue
     por debajo del techo.

   **DECIDIDO (2026-08-24): opcion (a), partir en tramos.** El perfil del TP07
   queda conservador (5 s por orden) y el alumno no toca nada: el Ejecutor
   divide `2 m a 0.20 m/s` en dos ordenes de 5 s. Es coherente con el
   "encadenar ordenes" que ya ensenan TP01 y TP02.

La consigna, además, es más estricta que nosotros en un punto y hay que
respetarlo: **"los alumnos no deben probar comandos creativos sobre el robot
físico; sólo los casos del JSON validados previamente en simulación."**

---

## 4. El circuito

```
  ESTUDIANTE (su máquina)                       TEO (notebook + robot G1)
  ┌──────────────────────────────┐             ┌────────────────────────────┐
  │ 1. INICIAR_SIMULADOR         │             │                            │
  │ 2. escribe su pipeline en    │             │                            │
  │    mi_desarrollo/mi_tp07.py  │             │                            │
  │ 3. EJECUTAR_MI_CODIGO        │             │                            │
  │    → corre los 25 casos      │             │                            │
  │    → ve el robot actuar      │             │                            │
  │    → obtiene su accuracy     │             │                            │
  │ 4. modo interactivo: escribe │             │                            │
  │    sus propias frases        │             │                            │
  └───────────┬──────────────────┘             └────────────────────────────┘
              │                                              ▲
              │  entrega mi_tp07.py + reporte de accuracy    │
              └──────────────────────────────────────────────┘
                                                             │
                    ┌────────────────────────────────────────┘
                    │  5. Teo lo pone en agentes_alumno/
                    │  6. valida en seco: --solo-clasificar
                    │  7. ejecuta SOLO los casos del JSON → 🤖
                    ▼
```

**Diferencia con TP03:** acá viaja **código**, no un JSON. Eso obliga a
sandbox — ver §6, punto 5.

---

## 5. Qué hay hoy

### En `labs/laboratorio_tp07/` (laboratorio físico)

Está bastante armado, mejor que TP02 y TP03:

| Archivo | Qué hace |
|---|---|
| `validador_lab.py` | validador propio del laboratorio, independiente del alumno |
| `ejecutor_real.py` | traduce la intención a comandos del bridge |
| `cargar_agente.py` | carga el agente del alumno |
| `casos_prueba.json` | los 25 casos |
| `ejecutar_casos.py` | corre los casos, con `--solo-clasificar` |
| `agente_demo.py` | agente de referencia |
| `agentes_alumno/ejemplo_agente.py` | el contrato mínimo |

**Ya tiene doble validación** (la del alumno y la del laboratorio), que es
justo lo que pide la consigna.

### Lo que ya está bien y no hay que tocar

- El contrato del agente: clase con `procesar(texto) -> dict` con
  `tipo`, `parametros`, `ejecutar`, `confianza`, `mensaje`.
- `LAB_BATERIA_MIN = 25` — **el único lab que ya cumple el mínimo.**
- Los 25 casos, que vienen de la consigna.

---

## 6. Qué hay que hacer

### A. Decidir primero (§3)

1. ~~Cómo se resuelve "avanzá 2 metros"~~ — **DECIDIDO: partir en tramos** (§3).
2. Revisar los **25 casos** contra nuestros límites y ajustar los esperados.
   **Pendiente.**

### B. Paquete del simulador (`materiales/tp07/`)

3. `mi_tp07.py` — **la estructura del pipeline**, con las cuatro clases vacías:
   `ClasificadorIntencion`, `ExtractorParametros`, `ValidadorSeguridad`, y el
   `AgenteRobot` que las une. Cada una con su docstring y `# TU CODIGO ACA`.
4. `casos_prueba.json` — los 25 casos.
5. `evaluar.py` (dado hecho) — corre los 25 casos, calcula **accuracy**, arma la
   tabla `texto | esperado | obtenido | correcto` que pide la consigna, y marca
   aparte si el validador bloqueó el 100 % de los peligrosos.
6. `ejecutor.py` (dado hecho) — **acá vive la conversión a velocidad y tiempo**.
7. Modo interactivo: que el alumno escriba frases y vea al robot reaccionar.
   Es lo que hace que el TP se sienta vivo.
8. `LEEME_ESTUDIANTE.md`, `LEEME_DOCENTE.md`, `LEEME.md`, `PLAN_TP07.md`.

### C. Laboratorio físico (`labs/laboratorio_tp07/`)

Los siete puntos de la receta (`REPORTE_ESTADO.md` §9):

9. **`utils/safety.py` y `config.py`** → delegar en `unitree_lab_core.safety`.
   Hoy `LAB_VEL_MAX_MS = 0.3`, **por encima del techo de 0.25**.
10. **`ejecutor_real.py`** → `girar` en velocidad y tiempo (avanzar ya convierte).
11. **`unitree_bridge.py`** → `girar(velocidad, duracion)`, como TP02.
12. **Sandbox**: hoy `cargar_agente.py` importa el código del alumno **con los
    permisos del operador**. Como acá viaja código y no un JSON, esto **sí es
    urgente**. Migrar a bwrap, que ya existe.
13. **`validar_entrega.py --tp`** → extender de `(1,2)` a incluir el 7.
14. Log con **timestamp de cada comando enviado al robot**, que la consigna pide
    explícitamente para auditoría.
15. **Parada de emergencia con prioridad** sobre cualquier acción en cola.

### D. Verificación

16. Agente de referencia que alcance **≥ 70 % de accuracy** y **bloquee el
    100 % de los peligrosos**. Sin eso no sabemos si el TP es resoluble.
17. Probar con G1 y Go2, ventana 3D, Ctrl+C limpio.
18. Las tres suites en verde.

---

## 7. Lo que hace distinto a este TP

Vale la pena tenerlo presente al armarlo:

- **No hay una única solución correcta.** La consigna lo dice: el alumno elige
  el enfoque y lo defiende. El material tiene que dejar espacio, no encajonar.
- **El validador es el corazón pedagógico**, no un accesorio. La consigna cierra
  con eso: *"la responsabilidad no puede delegarse completamente a una caja
  negra"*. El material tiene que hacerlo evidente.
- **Es el único TP donde el alumno entrega código que va a correr en la máquina
  del operador.** De ahí que el sandbox pase de deseable a obligatorio.
- Es de **nivel avanzado** y el único marcado así.

---

## 8. Orden sugerido

1. Resolver las dos decisiones de §A.
2. Laboratorio físico (C), empezando por el **sandbox** (punto 12), que es el
   riesgo real.
3. Paquete del simulador (B).
4. Agente de referencia y verificación (D).

Los puntos 9, 10 y 11 no dependen de nada y se pueden hacer ya.
