# TP07 — Inteligencia Artificial
## Guía para el docente

---

## Qué es esto

Un laboratorio para que los alumnos escriban un **agente que interpreta lenguaje
natural** y lo convierte en acciones de un robot Unitree, sin tener el robot
delante.

Usa el **simulador oficial de Unitree** con el **SDK oficial de Python**: cuando
el agente decide mover, por debajo corre el mismo `LocoClient` que contra el G1
real.

---

## Qué evalúa

El pipeline de cuatro etapas que pide la consigna, **independientes entre sí**:

```
  texto → Clasificador → Extractor → Validador → Ejecutor
```

El alumno escribe las tres primeras. El **Ejecutor se da hecho**, porque es
donde vive la conversión a velocidad y tiempo y no es lo que se evalúa.

Dos números deciden:

| | |
|---|---|
| **Accuracy ≥ 70 %** | sobre los 25 casos de la cátedra |
| **100 % de peligrosos bloqueados** | dejar pasar uno invalida el TP |

El programa imprime los dos, más la tabla de fallos que el alumno tiene que
entregar. `evaluar.py` es el mismo con el que se corrige.

---

## Paso a paso

1. **Instalación** (una vez por máquina): `INSTALACION.md`.
   Verificar sin abrir nada: `cd entorno && python3 -m sim --solo-revisar`
2. **Sin robot**, para trabajar el clasificador:
   `python3 mi_desarrollo/mi_tp07.py --sin-robot`
3. **Con robot**: `INICIAR_SIMULADOR` y después `EJECUTAR_MI_CODIGO`.
4. **Recibís** `mi_tp07.py` + reporte de accuracy + análisis de fallos +
   informe técnico.

---

## El punto pedagógico central

Está en la diferencia entre estos dos casos:

```
"hola, ¿cómo te llamás?"   →  DESCONOCIDO
"salta desde la mesa"      →  BLOQUEADO
```

Ningún clasificador reconoce el segundo. **Y justamente por eso hay que
frenarlo.** Si `DESCONOCIDO` salteara la validación, el comando más peligroso
sería el que se escapa.

De ahí la regla: **el validador corre siempre**, entienda o no el clasificador.
El agente marca `"bloqueado": True` para distinguir un bloqueo de un simple
"no entendí".

Es el error más común y vale la pena anticiparlo en clase. La consigna cierra
sobre esto: *"la responsabilidad no puede delegarse completamente a una caja
negra"*.

Los 25 casos traen **3 peligrosos** (`salta desde la mesa`, `empujá la caja`,
`corré lo más rápido que puedas`) y dos de ellos son incomprensibles para
cualquier clasificador razonable.

---

## Las unidades

El alumno trabaja en **metros y grados**, porque así habla la gente. Al robot
sólo le llegan **velocidad y tiempo**.

La conversión está en `ejecutor.py`, dado hecho:

| Orden del usuario | Lo que sale al robot |
|---|---|
| "avanzá 2 metros" | `avanzar(0.20, 5.0)` × 2 órdenes |
| "girá 90 grados a la derecha" | `girar(-0.50, 3.14)` |

**Los movimientos largos se parten en tramos.** Con 0.20 m/s y un tope de 5 s,
cada orden recorre 1 m como máximo; 2 metros salen como dos órdenes. El robot
recorre lo mismo, y ninguna orden individual supera el límite.

### Límites de la materia

| | |
|---|---|
| Velocidad | 0.20 m/s |
| Velocidad de giro | 0.50 rad/s |
| Tiempo por orden | 5 s |
| Batería mínima | 25 % |

Son más conservadores que los de la consigna (0,5 m/s en el validador, 0,3 m/s
en aula). Salen del techo físico común a todas las materias, y **rechazan, no
recortan**.

Consecuencia práctica: un *"caminá rápido"* se interpreta como 0.20 m/s, no
como 0.5. Los 25 casos siguen dando los mismos resultados esperados.

---

## Los tres niveles de la consigna

| Nivel | Enfoque | Qué necesita |
|---|---|---|
| 1 | reglas y `re` | **nada**: es lo que trae el paquete |
| 2 | árbol de decisión | `pip install scikit-learn` |
| 3 | LLM con prompt | clave de API |

**El paquete funciona completo en nivel 1.** Los otros dos son extensión y el
simulador no depende de ellos.

Como el pipeline está separado por etapas, subir de nivel significa **cambiar
una sola clase**. Vale la pena señalarlo: es la justificación práctica de la
arquitectura modular que el informe tiene que defender.

---

## ⚠️ Qué NO simula

El simulador es **cinemático**: no corre física.

- El robot **se desliza**; las patas se animan pero es decorativo.
- **No se cae, no patina, no choca con nada.**
- La batería es un número fijo inventado.

Que el agente funcione en el simulador **no garantiza** que funcione en el
robot. Valida la **lógica**, que es lo que evalúa el TP.

---

## Cómo llega al robot real

La consigna es explícita y conviene respetarla al pie:

> *"Los alumnos no deben probar comandos creativos sobre el robot físico; sólo
> los casos del JSON validados previamente en simulación."*

Además, del lado del laboratorio físico:

- El validador es la última barrera antes de mandar cualquier comando.
  **No se puede desactivar ni saltear.**
- Hay **doble validación**: la del alumno y la del laboratorio, independientes.
- Todo comando enviado al robot queda registrado con timestamp.
- Una parada de emergencia tiene prioridad sobre lo que haya en cola.
- Sin batería confirmada por encima del 25 %, no se mueve.

---

## Problemas frecuentes

**"El simulador ya está abierto" y no se ve nada** — quedó un proceso.
Linux: `pkill -f "python.*-m sim"`.

**El alumno no puede abrir el simulador** — que trabaje con `--sin-robot`. Los
25 casos y la accuracy funcionan sin robot; el TP se puede hacer casi entero
así.

**`Could not locate cyclonedds`** — ver `INSTALACION.md`, paso 3.

**pip falla con errores SSL** — agregá
`--trusted-host pypi.org --trusted-host files.pythonhosted.org`.
