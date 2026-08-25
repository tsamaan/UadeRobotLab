"""Traduce una ruta de grilla a movimientos del robot.

ACA ES DONDE LA GRILLA SE CONVIERTE EN VELOCIDAD Y TIEMPO.

El algoritmo del alumno piensa en celdas y en puntos cardinales: eso esta bien,
es su algoritmo. Pero al robot NUNCA le llegan celdas ni grados. Le llegan:

    avanzar(velocidad, tiempo)    tiempo = distancia / velocidad
    girar(velocidad, tiempo)      tiempo = angulo_rad / velocidad
                                  el SIGNO de la velocidad marca el sentido

Ejemplo con celda de 0.50 m, velocidad 0.25 m/s y giro 1.0 rad/s:

    avanzar una celda      ->  avanzar(0.25, 2.00)
    girar a la derecha     ->  girar(-1.0, 1.5708)
    girar a la izquierda   ->  girar(+1.0, 1.5708)
    media vuelta           ->  girar(+1.0, 3.1416)

El alumno no escribe este archivo, pero puede leerlo: es la parte que conecta
su algoritmo con el robot.
"""

from __future__ import annotations

import math

from .grilla import DELTAS, RUMBOS

# Vuelta completa, para normalizar angulos.
DOS_PI = 2 * math.pi


def _direccion(desde: tuple[int, int], hasta: tuple[int, int]) -> str:
    delta = (hasta[0] - desde[0], hasta[1] - desde[1])
    for nombre, d in DELTAS.items():
        if d == delta:
            return nombre
    raise ValueError(
        f"Movimiento invalido de {desde} a {hasta}: solo se permite avanzar "
        f"a una celda adyacente en las cuatro direcciones.")


def _giro_mas_corto(rumbo_actual: float, rumbo_destino: float) -> float:
    """Diferencia de rumbo en [-pi, pi]. Positivo = a la izquierda."""
    d = (rumbo_destino - rumbo_actual + math.pi) % DOS_PI - math.pi
    # -pi y +pi son la misma media vuelta; elegimos +pi para no depender del
    # redondeo y que el robot siempre gire para el mismo lado.
    return math.pi if math.isclose(d, -math.pi, abs_tol=1e-9) else d


def traducir(mapa, ruta, velocidad: float = 0.25,
             velocidad_giro: float = 1.0) -> list[dict]:
    """Convierte una ruta de celdas en ordenes de velocidad y tiempo."""
    if not ruta or len(ruta) < 2:
        return []
    if velocidad <= 0 or velocidad_giro <= 0:
        raise ValueError("Las velocidades tienen que ser mayores que cero.")

    pasos = [tuple(int(v) for v in p) for p in ruta]
    rumbo = mapa.rumbo_inicial()
    ordenes: list[dict] = []

    for i in range(1, len(pasos)):
        direccion = _direccion(pasos[i - 1], pasos[i])
        giro = _giro_mas_corto(rumbo, RUMBOS[direccion])

        if abs(giro) > 1e-9:
            ordenes.append({
                "tipo": "girar",
                "velocidad": math.copysign(velocidad_giro, giro),
                "tiempo": abs(giro) / velocidad_giro,
                # Solo para que el alumno lea el log; NO se le manda al robot.
                "detalle": f"hacia el {direccion}",
            })
            rumbo = RUMBOS[direccion]

        ordenes.append({
            "tipo": "avanzar",
            "velocidad": velocidad,
            "tiempo": mapa.tamano_celda / velocidad,
            "detalle": f"a la celda {pasos[i]}",
        })

    return ordenes


def describir(ordenes: list[dict]) -> str:
    lineas = []
    for i, o in enumerate(ordenes, 1):
        lineas.append(
            f"  {i:>3}. {o['tipo']:<8} velocidad={o['velocidad']:+.2f} "
            f"tiempo={o['tiempo']:.2f} s   {o['detalle']}")
    return "\n".join(lineas)


def ejecutar(robot, ordenes: list[dict], mostrar: bool = True) -> int:
    """Manda las ordenes al robot. Devuelve cuantas se ejecutaron.

    Si una es rechazada por seguridad, se detiene: seguir moviendo el robot
    despues de un rechazo es exactamente lo que no queremos.
    """
    from .safety import ErrorDeSeguridad

    hechas = 0
    for i, o in enumerate(ordenes, 1):
        if mostrar:
            print(f"  [{i}/{len(ordenes)}] {o['tipo']} "
                  f"velocidad={o['velocidad']:+.2f} tiempo={o['tiempo']:.2f} s "
                  f"({o['detalle']})")
        try:
            if o["tipo"] == "avanzar":
                robot.avanzar(velocidad=o["velocidad"], tiempo=o["tiempo"])
            else:
                robot.girar(velocidad=o["velocidad"], tiempo=o["tiempo"])
            hechas += 1
        except ErrorDeSeguridad as exc:
            print(f"\n  RECHAZADO en la orden {i}: {exc}")
            print("  Se detiene el recorrido.")
            robot.detenerse()
            break
    return hechas
