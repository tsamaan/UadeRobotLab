"""Mapas de navegacion para el TP03: carga, validacion y coordenadas.

El mapa es un JSON con el formato de la catedra:

    {
      "nombre": "Mapa nivel 1",
      "grilla": [[0,0,0,1,0], [1,1,0,1,0], ...],
      "inicio": [0, 0],
      "destino": [4, 4],
      "tamano_celda_metros": 0.50,
      "orientacion_inicial": "ESTE",
      "maximo_pasos": 30
    }

Valores de celda:  0 libre  ·  1 obstaculo  ·  2 zona prohibida

CONVENCION DE COORDENADAS. La grilla se indexa (fila, columna) y el mundo en
metros (x, y):

        x =  columna * celda        ESTE  = +x
        y = -fila    * celda        NORTE = +y

Con yaw = 0 el robot mira al ESTE (+x), que es la orientacion inicial por
defecto de la catedra. Girar a la izquierda (yaw positivo) lo lleva al NORTE.
Asi el signo de la velocidad angular coincide con la intuicion del mapa.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

LIBRE, OBSTACULO, PROHIBIDA = 0, 1, 2

# fila, columna. Coinciden con la prioridad de desempate de la catedra:
# arriba, derecha, abajo, izquierda.
DELTAS = {"NORTE": (-1, 0), "ESTE": (0, 1), "SUR": (1, 0), "OESTE": (0, -1)}
ORIENTACIONES = list(DELTAS)

# Rumbo en radianes de cada orientacion, con ESTE = 0.
RUMBOS = {"ESTE": 0.0, "NORTE": math.pi / 2, "OESTE": math.pi, "SUR": -math.pi / 2}


class MapaInvalido(ValueError):
    """El JSON del mapa no se puede usar."""


@dataclass
class Mapa:
    nombre: str
    grilla: list[list[int]]
    inicio: tuple[int, int]
    destino: tuple[int, int]
    tamano_celda: float
    orientacion_inicial: str
    maximo_pasos: int
    ruta: list = field(default_factory=list)   # se completa al planificar

    @property
    def filas(self) -> int:
        return len(self.grilla)

    @property
    def columnas(self) -> int:
        return len(self.grilla[0])

    def celda(self, fila: int, columna: int) -> int:
        return self.grilla[fila][columna]

    def es_transitable(self, fila: int, columna: int) -> bool:
        if not (0 <= fila < self.filas and 0 <= columna < self.columnas):
            return False
        return self.celda(fila, columna) == LIBRE

    def a_mundo(self, fila: int, columna: int) -> tuple[float, float]:
        """Centro de una celda, en metros."""
        return (columna * self.tamano_celda, -fila * self.tamano_celda)

    def rumbo_inicial(self) -> float:
        return RUMBOS[self.orientacion_inicial]


def _exigir(condicion: bool, mensaje: str) -> None:
    if not condicion:
        raise MapaInvalido(mensaje)


def cargar(ruta_archivo: str) -> Mapa:
    """Lee y valida un mapa. Falla con un mensaje que dice que arreglar."""
    try:
        with open(ruta_archivo, encoding="utf-8") as f:
            datos = json.load(f)
    except FileNotFoundError:
        raise MapaInvalido(f"No encuentro el mapa: {ruta_archivo}") from None
    except json.JSONDecodeError as exc:
        raise MapaInvalido(
            f"El mapa {ruta_archivo} no es un JSON valido: {exc}") from None
    return desde_dict(datos, origen=ruta_archivo)


def desde_dict(datos: dict, origen: str = "") -> Mapa:
    d = f" ({origen})" if origen else ""

    grilla = datos.get("grilla")
    _exigir(isinstance(grilla, list) and grilla, f"El mapa{d} no tiene 'grilla'.")
    _exigir(all(isinstance(f, list) and f for f in grilla),
            f"Las filas del mapa{d} tienen que ser listas no vacias.")
    ancho = len(grilla[0])
    _exigir(all(len(f) == ancho for f in grilla),
            f"Todas las filas del mapa{d} tienen que medir lo mismo.")
    validos = {LIBRE, OBSTACULO, PROHIBIDA}
    for i, fila in enumerate(grilla):
        for j, v in enumerate(fila):
            _exigir(v in validos,
                    f"Celda ({i},{j}) del mapa{d} vale {v!r}; "
                    f"solo se permiten 0 (libre), 1 (obstaculo) y 2 (prohibida).")

    def _posicion(clave: str) -> tuple[int, int]:
        p = datos.get(clave)
        _exigir(isinstance(p, (list, tuple)) and len(p) == 2,
                f"El mapa{d} necesita '{clave}' como [fila, columna].")
        f, c = int(p[0]), int(p[1])
        _exigir(0 <= f < len(grilla) and 0 <= c < ancho,
                f"'{clave}' ({f},{c}) del mapa{d} cae fuera de la grilla.")
        _exigir(grilla[f][c] == LIBRE,
                f"'{clave}' ({f},{c}) del mapa{d} cae sobre una celda no libre.")
        return (f, c)

    inicio, destino = _posicion("inicio"), _posicion("destino")

    celda = float(datos.get("tamano_celda_metros", 0.5))
    _exigir(0.1 <= celda <= 1.0,
            f"'tamano_celda_metros' del mapa{d} es {celda}; "
            f"tiene que estar entre 0.1 y 1.0 m.")

    orientacion = str(datos.get("orientacion_inicial", "ESTE")).upper().strip()
    _exigir(orientacion in ORIENTACIONES,
            f"'orientacion_inicial' del mapa{d} es {orientacion!r}; "
            f"tiene que ser una de {', '.join(ORIENTACIONES)}.")

    pasos = int(datos.get("maximo_pasos", 30))
    _exigir(pasos > 0, f"'maximo_pasos' del mapa{d} tiene que ser positivo.")

    return Mapa(
        nombre=str(datos.get("nombre", "sin nombre")),
        grilla=[[int(v) for v in fila] for fila in grilla],
        inicio=inicio, destino=destino, tamano_celda=celda,
        orientacion_inicial=orientacion, maximo_pasos=pasos,
    )


def validar_ruta(mapa: Mapa, ruta: list) -> list[str]:
    """Revisa que una ruta sea fisicamente ejecutable. Devuelve los problemas.

    Esto corre ANTES de mover el robot, en el simulador y en el laboratorio
    fisico. Una ruta con un salto entre celdas no adyacentes haria que el robot
    atraviese una pared.
    """
    problemas: list[str] = []
    if not ruta:
        return ["La ruta esta vacia."]

    pasos = [tuple(p) for p in ruta]
    if pasos[0] != mapa.inicio:
        problemas.append(f"La ruta empieza en {pasos[0]}, no en el inicio {mapa.inicio}.")

    for i, (f, c) in enumerate(pasos):
        if not (0 <= f < mapa.filas and 0 <= c < mapa.columnas):
            problemas.append(f"Paso {i}: la celda ({f},{c}) cae fuera de la grilla.")
        elif mapa.celda(f, c) != LIBRE:
            que = "un obstaculo" if mapa.celda(f, c) == OBSTACULO else "una zona prohibida"
            problemas.append(f"Paso {i}: la celda ({f},{c}) es {que}.")

    for i in range(1, len(pasos)):
        (f0, c0), (f1, c1) = pasos[i - 1], pasos[i]
        if abs(f1 - f0) + abs(c1 - c0) != 1:
            problemas.append(
                f"Paso {i}: salto de ({f0},{c0}) a ({f1},{c1}). "
                f"Solo se permiten movimientos a una celda adyacente.")

    if len(set(pasos)) != len(pasos):
        problemas.append("La ruta pasa dos veces por la misma celda.")

    if len(pasos) - 1 > mapa.maximo_pasos:
        problemas.append(
            f"La ruta usa {len(pasos) - 1} pasos; el maximo es {mapa.maximo_pasos}.")

    return problemas
