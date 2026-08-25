"""Hace que el robot se pasee solo, para que el dashboard tenga que graficar.

EL PROBLEMA. En el TP05 el alumno hace un dashboard de solo lectura: no mueve
el robot. Si el robot esta quieto, todos los graficos son lineas rectas y no
hay nada que visualizar ni que analizar.

QUE HACE. Un recorrido simple y repetitivo -- avanzar, girar, avanzar -- para
que la telemetria varie de forma coherente: al caminar suben la velocidad de
las articulaciones, el torque y la temperatura; al frenar bajan.

Se puede apagar con --sin-paseo si se prefiere el robot quieto.
"""

from __future__ import annotations

import threading
import time

# Recorrido: (vx, vy, vyaw, segundos).
#
# Tramos CORTOS y variados a proposito. Con tramos largos, el alumno mira el
# grafico de yaw y lo ve plano diez segundos seguidos, y cree que esta roto.
# Asi todos los graficos se mueven seguido: avanza, gira, curva, pausa.
RECORRIDO = [
    (0.20, 0.0, 0.00, 2.5),    # adelante
    (0.00, 0.0, 0.50, 1.6),    # gira a la izquierda
    (0.15, 0.0, 0.30, 2.0),    # curva
    (0.00, 0.0, 0.00, 1.2),    # pausa: se ve enfriar y apoyar las 4 patas
    (0.18, 0.0, -0.35, 2.0),   # curva al otro lado
    (0.00, 0.0, -0.50, 1.6),   # gira a la derecha
    (-0.15, 0.0, 0.00, 1.8),   # marcha atras
    (0.00, 0.0, 0.00, 1.2),    # pausa
]


class Paseo:
    """Mueve el mundo directamente, sin pasar por DDS.

    No usa el servicio de locomocion a proposito: el paseo es del simulador, no
    de un cliente. Asi el alumno ve datos aunque no haya nadie mas conectado.
    """

    def __init__(self, mundo, verboso: bool = True):
        self.mundo = mundo
        self.verboso = verboso
        self._parar = threading.Event()
        self._hilo: threading.Thread | None = None

    def arrancar(self) -> None:
        self._hilo = threading.Thread(target=self._bucle, daemon=True)
        self._hilo.start()

    def detener(self) -> None:
        self._parar.set()

    def _bucle(self) -> None:
        if self.verboso:
            print("  [PASEO] El robot se pasea solo para que tengas datos.")
            print("          Para dejarlo quieto: --sin-paseo")
        while not self._parar.is_set():
            for vx, vy, vyaw, segundos in RECORRIDO:
                if self._parar.is_set():
                    return
                # set_velocidad recorta al perfil y no levanta excepciones:
                # es el mismo camino que usa el servicio de locomocion.
                self.mundo.set_velocidad(vx, vy, vyaw, segundos)
                fin = time.monotonic() + segundos
                while time.monotonic() < fin and not self._parar.is_set():
                    time.sleep(0.1)
            self.mundo.detener()
