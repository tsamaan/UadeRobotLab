# =====================================================================
#  Evaluador. ESTE ARCHIVO TE LO DAMOS HECHO.
#
#  Corre tu agente contra los 25 casos de prueba y te dice:
#    - tu accuracy (la consigna pide >= 70 %)
#    - si tu validador bloqueo el 100 % de los casos peligrosos
#    - la tabla de fallos, que tenes que entregar
#
#  No lo modifiques: es el mismo con el que se te va a corregir.
# =====================================================================

import json
from pathlib import Path

CASOS = Path(__file__).resolve().parent / "casos_prueba.json"

# Los casos peligrosos son los que el validador NO puede dejar pasar nunca.
# Se cuentan aparte de la accuracy porque, segun la consigna, dejarlos pasar
# invalida el TP aunque el resto este bien.
PELIGROSOS = {"palabra peligrosa"}


def cargar_casos():
    with open(CASOS, encoding="utf-8") as f:
        return json.load(f)


def _resultado(respuesta):
    """Traduce lo que devolvio el agente a EJECUTAR / BLOQUEADO / DESCONOCIDO.

    Ojo con la diferencia, que es la parte fina del TP:

      DESCONOCIDO  el agente no entendio, y no habia nada peligroso
      BLOQUEADO    el validador lo freno, ENTIENDA O NO el clasificador

    "salta desde la mesa" cae en el segundo caso: ningun clasificador lo
    reconoce, y justamente por eso hay que bloquearlo. Por eso el agente
    marca `bloqueado: True` cuando el validador dice que no.
    """
    if not isinstance(respuesta, dict):
        return "ERROR", "el agente no devolvio un diccionario"
    tipo = str(respuesta.get("tipo", "")).upper()
    ejecutar = bool(respuesta.get("ejecutar", False))
    bloqueado = bool(respuesta.get("bloqueado", False))
    mensaje = respuesta.get("mensaje", "")

    if bloqueado:
        return "BLOQUEADO", mensaje
    if ejecutar:
        return "EJECUTAR", mensaje
    if tipo == "DESCONOCIDO":
        return "DESCONOCIDO", mensaje
    return "BLOQUEADO", mensaje


def evaluar(agente, mostrar=True):
    """Corre los 25 casos. Devuelve un resumen con accuracy y fallos."""
    casos = cargar_casos()
    filas, aciertos = [], 0
    peligrosos_totales = peligrosos_bloqueados = 0

    for caso in casos:
        esperado = caso["resultado_esperado"]
        es_peligroso = caso.get("motivo") in PELIGROSOS
        try:
            respuesta = agente.procesar(caso["texto"])
            obtenido, mensaje = _resultado(respuesta)
        except Exception as exc:
            obtenido, mensaje = "ERROR", f"{type(exc).__name__}: {exc}"

        correcto = obtenido == esperado
        aciertos += correcto
        if es_peligroso:
            peligrosos_totales += 1
            peligrosos_bloqueados += obtenido == "BLOQUEADO"

        filas.append({
            "id": caso["id"], "texto": caso["texto"], "esperado": esperado,
            "obtenido": obtenido, "correcto": correcto,
            "peligroso": es_peligroso, "mensaje": mensaje,
        })

    accuracy = aciertos / len(casos) if casos else 0.0
    resumen = {
        "casos": len(casos), "aciertos": aciertos, "accuracy": accuracy,
        "peligrosos_totales": peligrosos_totales,
        "peligrosos_bloqueados": peligrosos_bloqueados,
        "filas": filas,
    }
    if mostrar:
        imprimir(resumen)
    return resumen


def imprimir(r):
    print()
    print("=" * 78)
    print("  EVALUACION SOBRE LOS CASOS DE PRUEBA")
    print("=" * 78)
    print(f"  {'#':>3}  {'texto':<38} {'esperado':<12} {'obtenido':<12} ")
    print("  " + "-" * 74)
    for f in r["filas"]:
        marca = "ok " if f["correcto"] else "MAL"
        peligro = " !" if f["peligroso"] else "  "
        print(f"  {f['id']:>3}{peligro} {f['texto'][:38]:<38} {f['esperado']:<12} "
              f"{f['obtenido']:<12} {marca}")

    print("  " + "-" * 74)
    pct = r["accuracy"] * 100
    print(f"\n  ACCURACY: {r['aciertos']}/{r['casos']} = {pct:.1f} %"
          f"   {'APRUEBA (>= 70 %)' if pct >= 70 else 'NO ALCANZA (hace falta 70 %)'}")

    pt, pb = r["peligrosos_totales"], r["peligrosos_bloqueados"]
    if pt:
        estado = "BIEN" if pb == pt else "MAL: dejaste pasar un comando peligroso"
        print(f"  PELIGROSOS BLOQUEADOS: {pb}/{pt}   {estado}")

    fallos = [f for f in r["filas"] if not f["correcto"]]
    if fallos:
        print(f"\n  CASOS QUE FALLARON ({len(fallos)}) - para tu analisis de fallos:")
        for f in fallos:
            print(f"    {f['id']:>3}. \"{f['texto']}\"")
            print(f"         esperaba {f['esperado']}, dio {f['obtenido']}"
                  + (f" - {f['mensaje'][:60]}" if f["mensaje"] else ""))
    print("=" * 78)
