# =====================================================================
#  Entrenamiento del clasificador. NIVEL 2 (extension).
#
#  ESTE ARCHIVO TE LO DAMOS HECHO, pero el DATASET lo armas vos.
#
#  Corrida rapida:
#      python3 entrenar.py
#
#  Lee tu dataset.csv, entrena un clasificador y te muestra las cuatro
#  metricas: accuracy, precision, recall y F1.
#
#  Para usarlo en tu agente, en ClasificadorIntencion:
#
#      from entrenar import entrenar_desde_csv
#
#      class ClasificadorIntencion:
#          def __init__(self):
#              self.modelo = entrenar_desde_csv("dataset.csv")
#
#          def clasificar(self, texto):
#              return self.modelo.predict([texto])[0]
#
#  El resto del pipeline no se entera: extractor, validador y ejecutor
#  siguen igual. Esa es la ventaja de tener las etapas separadas.
# =====================================================================

import csv
from collections import Counter
from pathlib import Path

DATASET = Path(__file__).resolve().parent / "dataset.csv"

TIPOS = ("MOVER", "GIRAR", "DETENERSE", "SALUDO",
         "CONSULTAR_ESTADO", "DESCONOCIDO")


def hay_sklearn():
    try:
        import sklearn  # noqa: F401
        return True
    except ImportError:
        return False


def cargar_dataset(ruta=DATASET):
    """Lee el CSV. Devuelve (textos, etiquetas).

    Formato esperado, con cabecera:

        texto,intencion
        avanza dos metros,MOVER
        pará,DETENERSE
    """
    ruta = Path(ruta)
    if not ruta.is_file():
        raise FileNotFoundError(
            f"No encuentro {ruta.name}. Tenes que armar tu dataset:\n"
            f"  - una fila por ejemplo\n"
            f"  - dos columnas: texto,intencion\n"
            f"  - al menos 50 ejemplos (la consigna sugiere 80)")

    textos, etiquetas = [], []
    with open(ruta, encoding="utf-8", newline="") as f:
        for n, fila in enumerate(csv.DictReader(f), start=2):
            texto = (fila.get("texto") or "").strip()
            etiqueta = (fila.get("intencion") or "").strip().upper()
            if not texto:
                continue
            if etiqueta not in TIPOS:
                raise ValueError(
                    f"{ruta.name} linea {n}: intencion '{etiqueta}' no es valida.\n"
                    f"  Tiene que ser una de: {', '.join(TIPOS)}")
            textos.append(texto)
            etiquetas.append(etiqueta)

    if not textos:
        raise ValueError(f"{ruta.name} no tiene ejemplos.")
    return textos, etiquetas


def revisar_dataset(textos, etiquetas):
    """Avisa de los problemas tipicos ANTES de entrenar."""
    avisos = []
    cuenta = Counter(etiquetas)

    if len(textos) < 50:
        avisos.append(f"Solo {len(textos)} ejemplos. La consigna sugiere 80; "
                      f"con menos de 50 el modelo no aprende gran cosa.")

    faltan = [t for t in TIPOS if cuenta[t] == 0]
    if faltan:
        avisos.append(f"No hay ejemplos de: {', '.join(faltan)}. "
                      f"El modelo nunca va a predecir esas intenciones.")

    pocos = [f"{t} ({cuenta[t]})" for t in TIPOS if 0 < cuenta[t] < 5]
    if pocos:
        avisos.append(f"Muy pocos ejemplos de: {', '.join(pocos)}. "
                      f"Conviene al menos 5 de cada una.")

    repetidos = [t for t, c in Counter(x.lower().strip() for x in textos).items() if c > 1]
    if repetidos:
        avisos.append(f"{len(repetidos)} texto(s) repetido(s). "
                      f"Repetir no agrega informacion: cambia la redaccion.")

    return avisos


def entrenar(textos, etiquetas):
    """Entrena un Naive Bayes sobre bolsa de palabras."""
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import make_pipeline

    modelo = make_pipeline(
        # analyzer="char_wb" con n-gramas aguanta mejor las variantes del
        # espanol: "avanza", "avanza", "avanzar" comparten letras.
        CountVectorizer(analyzer="char_wb", ngram_range=(3, 5)),
        MultinomialNB(),
    )
    modelo.fit(textos, etiquetas)
    return modelo


def entrenar_desde_csv(ruta=DATASET):
    """Lo que llamas desde tu agente. Devuelve el modelo listo para predecir."""
    textos, etiquetas = cargar_dataset(ruta)
    return entrenar(textos, etiquetas)


def metricas(modelo, textos, etiquetas):
    """Las cuatro que pide la consigna."""
    from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                                 recall_score)
    pred = modelo.predict(textos)
    return {
        "accuracy": accuracy_score(etiquetas, pred),
        "precision": precision_score(etiquetas, pred, average="macro", zero_division=0),
        "recall": recall_score(etiquetas, pred, average="macro", zero_division=0),
        "f1": f1_score(etiquetas, pred, average="macro", zero_division=0),
    }


def main():
    print("\n  ENTRENAMIENTO DEL CLASIFICADOR (nivel 2)")
    print("  " + "=" * 56)

    try:
        textos, etiquetas = cargar_dataset()
    except (FileNotFoundError, ValueError) as exc:
        print(f"\n  {exc}\n")
        return 1

    cuenta = Counter(etiquetas)
    print(f"\n  Dataset: {len(textos)} ejemplos")
    for t in TIPOS:
        if cuenta[t]:
            print(f"    {t:<20} {cuenta[t]:>3}")

    for aviso in revisar_dataset(textos, etiquetas):
        print(f"\n  [AVISO] {aviso}")

    if not hay_sklearn():
        print("\n  scikit-learn no esta instalado, asi que no se puede entrenar.")
        print("    pip install --user scikit-learn")
        print("\n  El TP se puede hacer igual con reglas: esto es la extension.\n")
        return 1

    from sklearn.model_selection import train_test_split

    print("\n  Entrenando...")
    # Se separa una parte para medir. Medir sobre los mismos ejemplos con los
    # que entrenaste no dice nada: el modelo ya los vio.
    separado = len(textos) >= 20 and min(cuenta.values()) >= 2
    if separado:
        x_tr, x_te, y_tr, y_te = train_test_split(
            textos, etiquetas, test_size=0.25, random_state=0, stratify=etiquetas)
    else:
        print("  [AVISO] Muy pocos ejemplos para separar en entrenamiento y")
        print("          prueba, asi que se mide sobre los MISMOS con los que")
        print("          se entreno. Ese numero no significa nada: el modelo")
        print("          ya los vio. Agranda el dataset.")
        x_tr, x_te, y_tr, y_te = textos, textos, etiquetas, etiquetas

    modelo = entrenar(x_tr, y_tr)
    m = metricas(modelo, x_te, y_te)

    donde = ("ejemplos que el modelo NO vio al entrenar" if separado
             else "los MISMOS ejemplos del entrenamiento (no sirve para evaluar)")
    print(f"\n  Sobre {len(x_te)} {donde}:")
    print(f"    accuracy   {m['accuracy'] * 100:>5.1f} %")
    print(f"    precision  {m['precision'] * 100:>5.1f} %")
    print(f"    recall     {m['recall'] * 100:>5.1f} %")
    print(f"    F1         {m['f1'] * 100:>5.1f} %")

    print("\n  Para usarlo en tu agente:")
    print("    from entrenar import entrenar_desde_csv")
    print("    self.modelo = entrenar_desde_csv()")
    print("    ... self.modelo.predict([texto])[0]")
    print("\n  Despues compara estas metricas con las de tu clasificador de")
    print("  reglas: esa comparacion es parte del informe.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
