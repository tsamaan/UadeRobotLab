"""Telemetria del simulador para el TP05.

EL PROBLEMA. El simulador es CINEMATICO: escribe poses y no corre fisica. El
bridge oficial de Unitree publica lo que sale de los sensores de MuJoCo, asi
que sin fisica llegan asi:

    angulo de motor   REAL      (lo escribimos nosotros)
    yaw de la IMU     REAL
    velocidad         0
    torque            0
    temperatura       0         (el bridge ni siquiera la publica)
    roll / pitch      0
    fuerzas de pata   0
    bateria           0

Un dashboard donde la mitad de los graficos son lineas planas no sirve para
que el alumno haga el TP.

QUE SE HACE. Se completan esos campos a partir del estado real del simulador,
no con ruido suelto. Si el robot camina, sube el torque y suben las
temperaturas; si frena, bajan. El dashboard reacciona a lo que el robot hace.

    velocidad     REAL: derivada de cuanto se movio cada articulacion
    gyro          REAL: derivado del giro de la base
    torque        DERIVADO del esfuerzo de cada articulacion
    temperatura   DERIVADA: sube con el uso, baja al frenar
    roll / pitch  DERIVADOS: pequena oscilacion al caminar
    fuerzas       DERIVADAS de la fase de la marcha
    bateria       INVENTADA (87 %) y baja lentisimo

HONESTIDAD. Todo lo derivado va marcado como tal en la respuesta de la API,
con el campo `derivado`. Un alumno no puede creer que esta viendo el torque
medido de un motor real: no lo es, y en el robot fisico esos numeros van a ser
otros.
"""

from __future__ import annotations

import math
import time

TEMPERATURA_REPOSO = 28.0    # grados, robot quieto
TEMPERATURA_MAXIMA = 55.0    # a la que tiende con uso sostenido
CALENTAMIENTO = 0.9          # grados por segundo de esfuerzo pleno
ENFRIAMIENTO = 0.25          # grados por segundo en reposo

BATERIA_INICIAL = 87.0
CONSUMO_POR_SEGUNDO = 0.004  # muy lento: una clase no la agota


class Telemetria:
    """Completa los campos que la cinematica no produce."""

    def __init__(self, n_motores: int):
        self.n = n_motores
        self.temperaturas = [TEMPERATURA_REPOSO] * n_motores
        self.bateria = BATERIA_INICIAL
        self._ultimo = time.monotonic()

    def actualizar(self, esfuerzos: list[float], moviendose: bool) -> None:
        """Avanza temperaturas y bateria segun cuanto trabajo se esta haciendo.

        `esfuerzos` es un valor 0..1 por motor: cuanto se esta moviendo.
        """
        ahora = time.monotonic()
        dt = min(max(ahora - self._ultimo, 0.0), 1.0)
        self._ultimo = ahora
        if dt <= 0:
            return

        for i in range(min(self.n, len(esfuerzos))):
            e = max(0.0, min(1.0, esfuerzos[i]))
            objetivo = TEMPERATURA_REPOSO + e * (TEMPERATURA_MAXIMA - TEMPERATURA_REPOSO)
            actual = self.temperaturas[i]
            ritmo = CALENTAMIENTO if objetivo > actual else ENFRIAMIENTO
            paso = ritmo * dt
            if abs(objetivo - actual) <= paso:
                self.temperaturas[i] = objetivo
            else:
                self.temperaturas[i] = actual + math.copysign(paso, objetivo - actual)

        consumo = CONSUMO_POR_SEGUNDO * dt * (2.5 if moviendose else 1.0)
        self.bateria = max(5.0, self.bateria - consumo)

    def torque(self, esfuerzos: list[float], cargas: list[float]) -> list[float]:
        """Torque estimado por motor, en Nm.

        No es una medicion: es una estimacion a partir de cuanto se mueve cada
        articulacion y cuanto peso carga. Las piernas cargan mas que los brazos.
        """
        return [round(e * c * 12.0, 2)
                for e, c in zip(esfuerzos, cargas)]

    def inclinacion(self, fase: float, moviendose: bool) -> tuple[float, float]:
        """Roll y pitch en radianes.

        El robot cinematico no se inclina nunca. Al caminar, uno real oscila un
        poco: se reproduce esa oscilacion para que el grafico no sea una linea
        recta. Quieto, queda en cero.
        """
        if not moviendose:
            return 0.0, 0.0
        return (0.035 * math.sin(fase), 0.025 * math.sin(fase * 2.0 + 0.7))

    def fuerzas_de_pata(self, fase: float, patas: int, moviendose: bool) -> list[int]:
        """Que patas estan apoyadas, segun la fase de la marcha.

        Quieto, todas apoyan. Caminando, alternan como en la animacion.
        """
        if not moviendose:
            return [180] * patas
        fuerzas = []
        for i in range(patas):
            # Las diagonales van juntas, igual que la marcha del visor.
            desfase = math.pi if i in (1, 2) else 0.0
            apoyada = math.sin(fase + desfase) < 0.3
            fuerzas.append(180 if apoyada else 0)
        return fuerzas
