# TP07 — Inteligencia Artificial
## Guía para el estudiante

Vas a escribir un **agente** que recibe órdenes escritas en castellano y las
convierte en acciones del robot. *"avanzá 2 metros"*, *"girá a la derecha"*,
*"detente ya"*.

Y algo más importante: que **rechace** lo que no debe hacer.

---

## Paso a paso

### 1. Instalar (una sola vez)

Si es la primera vez en esta computadora, seguí **`INSTALACION.md`**.

### 2. Abrir el simulador

| Sistema | Qué hacés |
|---|---|
| **Windows** | doble clic en `INICIAR_SIMULADOR.bat` |
| **Linux / macOS** | doble clic en `INICIAR_SIMULADOR.sh` |

> Podés empezar **sin el simulador**: `python3 mi_desarrollo/mi_tp07.py --sin-robot`
> corre los 25 casos y te da tu accuracy. Conviene arrancar así.

### 3. Escribir tu agente

Abrí **`mi_desarrollo/mi_tp07.py`**. Hay cuatro bloques con `# TU CODIGO ACA`.

### 4. Ejecutarlo

Doble clic en `EJECUTAR_MI_CODIGO`. Vas a ver la tabla de los 25 casos, tu
accuracy, y después un modo interactivo para escribirle órdenes al robot.

---

## El pipeline

Cuatro etapas, y la consigna pide que sean **independientes**:

```
  texto  →  Clasificador  →  Extractor de   →  Validador de  →  Ejecutor
            de intención     parámetros        seguridad
```

| # | Clase | Qué hace |
|---|---|---|
| 1 | `ClasificadorIntencion` | decide **qué** quiere el usuario |
| 2 | `ExtractorParametros` | saca los **números** del texto |
| 3 | `ValidadorSeguridad` | decide si **se puede** hacer |
| 4 | `Ejecutor` | **ya está hecho**: manda al robot |

Las seis intenciones: `MOVER`, `GIRAR`, `DETENERSE`, `SALUDO`,
`CONSULTAR_ESTADO` y `DESCONOCIDO`.

**Escribí una etapa por vez y probala.** Es mucho más fácil encontrar un error
en el clasificador solo que en el pipeline entero.

---

## Las unidades: dónde va cada cosa

Vos trabajás en **metros y grados**, porque así habla la gente:

```python
"avanzá 2 metros"   →  {"distancia_m": 2.0}
"girá 90 grados"    →  {"angulo_deg": 90}
```

El robot, en cambio, sólo entiende **velocidad y tiempo**. Esa conversión la
hace `ejecutor.py`, que **ya está escrito**:

```
"avanzá 2 metros"  a 0.2 m/s  →  10 s  →  dos órdenes de 5 s
"girá 90 grados"   a 0.5 rad/s →  3.14 s → una orden
```

Fijate que 2 metros salen **partidos en dos órdenes**: hay un tope de 5 segundos
por orden, así que un movimiento largo se divide. El robot recorre lo mismo.

Podés leer `ejecutor.py` — vale la pena ver cómo se hace el salto de las
palabras al movimiento.

---

## Tus límites

| | |
|---|---|
| Velocidad máxima | 0.20 m/s |
| Velocidad de giro máxima | 0.50 rad/s |
| Tiempo máximo por orden | 5 segundos |
| Batería mínima | 25 % |

Un "rápido" no puede ser más de 0.20 m/s. Si tu extractor devuelve más, tu
validador debería frenarlo — y si no lo frena, lo frena el robot.

---

## Cómo se te evalúa

```
ACCURACY: 25/25 = 100.0 %   APRUEBA (>= 70 %)
PELIGROSOS BLOQUEADOS: 3/3   BIEN
```

Dos números, y el segundo no se negocia:

- **Accuracy ≥ 70 %** sobre los 25 casos.
- **100 % de los peligrosos bloqueados.** Dejar pasar uno solo invalida el TP,
  aunque el resto esté perfecto.

---

## Lo más importante del TP

Hay tres resultados posibles, y **dos se confunden fácil**:

| Resultado | Cuándo |
|---|---|
| `EJECUTAR` | se entendió y es seguro |
| `DESCONOCIDO` | no se entendió, **y no había nada peligroso** |
| `BLOQUEADO` | tu validador lo frenó, **hayas entendido o no** |

Mirá estos dos:

```
"hola, ¿cómo te llamás?"   →  DESCONOCIDO
"salta desde la mesa"      →  BLOQUEADO
```

Los dos son incomprensibles para el clasificador. Pero el segundo **hay que
frenarlo**.

Por eso **el validador corre siempre**, aunque el clasificador haya dicho
`DESCONOCIDO`. Si `DESCONOCIDO` salteara la validación, el comando más
peligroso sería justamente el que se escapa.

Un comando que no se entiende **no es un comando inofensivo.**

Para distinguirlos, tu agente marca `"bloqueado": True` cuando el validador
frena.

---

## Qué entregás

1. **`mi_tp07.py`** con tu nombre completado arriba.
2. **El reporte de accuracy**: la tabla que imprime el programa.
3. **Análisis de fallos** (media página): qué casos fallaron, por qué, y cómo
   los mejorarías.
4. **Informe técnico** (1–2 páginas): tu pipeline, por qué elegiste ese enfoque,
   y por qué el validador tiene que ser un componente aparte.

Poné tu apellido en el nombre del archivo: `tp07_perez_juan.py`.

---

## Si querés ir más lejos

Lo que hagas con reglas y `re` alcanza para aprobar. Si querés:

- **Clasificador con scikit-learn**: entrenás un Naive Bayes o un árbol y
  comparás accuracy contra tus reglas.
- **Un modelo de lenguaje**: reemplazás el clasificador por una llamada a una
  API con un prompt.
- **Agente con memoria**: que entienda *"hacelo otra vez"* o *"como antes pero
  más despacio"*.

Fijate que en los tres casos **cambiás una sola clase** y el resto del pipeline
ni se entera. Eso no es casualidad: es para lo que sirve separar las etapas.

---

## Una aclaración importante

El simulador **no es el robot**: no se cae, no patina, y no choca con nada.

Y algo que importa más en este TP: el día de la visita **sólo se ejecutan los
casos del JSON ya validados**. No se prueban comandos nuevos sobre el robot
físico.
