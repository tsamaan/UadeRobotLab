# Tu carpeta de trabajo — TP07

| Archivo | Para qué |
|---|---|
| `mi_tp07.py` | Acá escribís tu agente. **Es lo que entregás.** |
| `casos_prueba.json` | Los 25 casos de la cátedra. Dados hechos. |
| `evaluar.py` | Dado hecho. Calcula tu accuracy y la tabla de fallos. |
| `ejecutor.py` | Dado hecho. Convierte a velocidad y tiempo, y manda al robot. |
| `robot.py` | No lo toques. |
| `dataset.csv` | **Extensión**: 5 ejemplos para que veas el formato. Completalo vos. |
| `entrenar.py` | Dado hecho. Entrena con tu dataset y te da las métricas. |

## Cómo lo ejecutás

**Con robot** (para ver al G1 hacerte caso):

1. Abrí `INICIAR_SIMULADOR` y elegí el robot.
2. Doble clic en `EJECUTAR_MI_CODIGO`, o `python3 mi_desarrollo/mi_tp07.py`.

**Sin robot** (para trabajar el clasificador tranquilo):

```
python3 mi_desarrollo/mi_tp07.py --sin-robot
```

Corre los 25 casos y te da la accuracy, sin abrir nada.

## Modo interactivo

Con el robot conectado, después de la evaluación podés escribirle órdenes:

```
  > avanzá 2 metros
  > girá 90 grados a la derecha
  > salta desde la mesa
```

Es la mejor forma de encontrar los casos que tu agente no cubre.

## Extensión: entrenar un modelo (nivel 2)

Con reglas alcanza para aprobar. Si querés ir más lejos:

**1. Armá tu dataset.** `dataset.csv` trae 5 ejemplos para que veas el formato:

```
texto,intencion
dale para adelante,MOVER
frená ahí,DETENERSE
```

Completalo hasta unos 80. Las intenciones válidas son `MOVER`, `GIRAR`,
`DETENERSE`, `SALUDO`, `CONSULTAR_ESTADO` y `DESCONOCIDO`.

**2. Entrená y mirá tus métricas:**

```
python3 mi_desarrollo/entrenar.py
```

Te avisa si al dataset le falta algo: pocas filas, una intención sin ejemplos,
textos repetidos.

**3. Usalo en tu agente.** En `ClasificadorIntencion.__init__` hay dos líneas
comentadas:

```python
from entrenar import entrenar_desde_csv
self.modelo = entrenar_desde_csv()
```

Y en `clasificar()`:

```python
if self.modelo is not None:
    return self.modelo.predict([texto])[0]
```

Dejá las reglas de respaldo: si el dataset no está, el agente sigue andando.

**El extractor, el validador y el ejecutor no se enteran.** Cambiás una sola
clase.

**4. Compará.** ¿El modelo le gana a tus reglas? ¿En qué casos pierde? Esa
comparación es parte del informe.

> Necesitás `scikit-learn`: `pip install --user scikit-learn`.
> Sin él, el TP se hace igual con reglas.

## Qué entregás si hiciste la extensión

Una **carpeta** con los dos archivos:

```
tp07_apellido/
├── mi_tp07.py
└── dataset.csv
```

No hace falta que entregues el modelo entrenado: se entrena solo al arrancar,
en milisegundos. Y así el profesor puede **leer** tu dataset.
