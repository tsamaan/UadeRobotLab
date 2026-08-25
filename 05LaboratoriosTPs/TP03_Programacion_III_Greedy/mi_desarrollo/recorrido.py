# =====================================================================
#  Ejecutor del recorrido. ESTE ARCHIVO TE LO DAMOS HECHO.
#
#  No hace falta que lo modifiques, pero conviene que lo leas: es la
#  parte que conecta TU algoritmo con el robot.
#
#  Se encarga de:
#    - cargar el mapa desde el JSON
#    - validar que tu ruta sea fisicamente ejecutable
#    - traducirla a ordenes de VELOCIDAD y TIEMPO
#    - mandarlas al robot
#    - exportar tu entrega
# =====================================================================

import json
import sys
from datetime import datetime
from pathlib import Path

_ENTORNO = Path(__file__).resolve().parent.parent / "entorno"
if str(_ENTORNO) not in sys.path:
    sys.path.insert(0, str(_ENTORNO))

from sim.grilla import MapaInvalido, cargar, validar_ruta   # noqa: E402
from sim.navegacion import describir, ejecutar, traducir     # noqa: E402

CARPETA_MAPAS = Path(__file__).resolve().parent / "mapas"
CARPETA_ENTREGA = Path(__file__).resolve().parent / "entrega"

# Estados con los que puede terminar tu planificador.
DESTINO_ALCANZADO = "DESTINO_ALCANZADO"
BLOQUEADO = "BLOQUEADO"
LIMITE_DE_PASOS = "LIMITE_DE_PASOS"
SIN_SOLUCION = "SIN_SOLUCION"


def cargar_mapa(nombre):
    """Carga un mapa de la carpeta mapas/. Ejemplo: cargar_mapa('nivel1_directo')."""
    ruta = CARPETA_MAPAS / (nombre if nombre.endswith(".json") else nombre + ".json")
    mapa = cargar(str(ruta))
    # Guardamos el nombre del archivo: el laboratorio fisico lo necesita para
    # encontrar el mismo mapa al ejecutar la entrega contra el robot.
    mapa.archivo = ruta.name
    return mapa


def mapas_disponibles():
    return sorted(p.stem for p in CARPETA_MAPAS.glob("*.json"))


def mostrar_mapa(mapa, ruta=None):
    """Dibuja el mapa en la consola. Util para depurar sin abrir el simulador."""
    paso = {tuple(p): i for i, p in enumerate(ruta or [])}
    print(f"\n  {mapa.nombre}   ({mapa.filas}x{mapa.columnas})")
    print(f"  inicio {tuple(mapa.inicio)}  destino {tuple(mapa.destino)}  "
          f"mirando al {mapa.orientacion_inicial}\n")
    for f in range(mapa.filas):
        fila = []
        for c in range(mapa.columnas):
            v = mapa.celda(f, c)
            if v == 1:
                fila.append(" ## ")
            elif v == 2:
                fila.append(" // ")
            elif (f, c) == tuple(mapa.inicio):
                fila.append("  I ")
            elif (f, c) == tuple(mapa.destino):
                fila.append("  D ")
            elif (f, c) in paso:
                fila.append(f"{paso[(f, c)]:>3} ")
            else:
                fila.append("  . ")
        print("   " + "".join(fila))
    print("\n   I=inicio  D=destino  ##=obstaculo  //=zona prohibida  "
          "numeros=orden de tu ruta\n")


def recorrer(robot, mapa, ruta, mostrar=True):
    """Valida la ruta y la ejecuta en el robot. Devuelve cuantas ordenes salieron."""
    problemas = validar_ruta(mapa, ruta)
    if problemas:
        print("\n  LA RUTA NO SE PUEDE EJECUTAR:")
        for p in problemas:
            print(f"    - {p}")
        print("\n  No se movio el robot.")
        return 0

    ordenes = traducir(mapa, ruta,
                       velocidad=robot.perfil.velocidad_max,
                       velocidad_giro=robot.perfil.velocidad_angular_max)
    if mostrar:
        print(f"\n  {len(ordenes)} ordenes, todas en velocidad y tiempo:")
        print(describir(ordenes))
        print()
    return ejecutar(robot, ordenes, mostrar=mostrar)


def exportar_entrega(mapa, ruta, estado, alumno, algoritmo, nodos_explorados=0):
    """Genera el archivo que hay que entregar."""
    CARPETA_ENTREGA.mkdir(exist_ok=True)
    seguro = "".join(ch if ch.isalnum() else "_" for ch in alumno.lower()).strip("_")
    archivo = CARPETA_ENTREGA / f"ruta_{seguro or 'sin_nombre'}.json"

    datos = {
        "alumno": alumno,
        "algoritmo": algoritmo,
        "mapa": mapa.nombre,
        "grilla_usada": getattr(mapa, "archivo", ""),
        "inicio": list(mapa.inicio),
        "destino": list(mapa.destino),
        "tamano_celda_metros": mapa.tamano_celda,
        "orientacion_inicial": mapa.orientacion_inicial,
        "ruta": [list(p) for p in ruta],
        "pasos": max(0, len(ruta) - 1),
        "estado": estado,
        "nodos_explorados": nodos_explorados,
        "generado": datetime.now().isoformat(timespec="seconds"),
    }
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

    print(f"\n  Entrega generada: {archivo.name}")
    print(f"  Esta en la carpeta mi_desarrollo/entrega/")
    print(f"  ESE es el archivo que tenes que entregar.")
    return archivo
