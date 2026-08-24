"""Estado del robot simulado: donde esta y como se mueve.

Es CINEMATICO a proposito: no hay fisica, no hay caidas, no hay patinaje.
Un TP de navegacion evalua si el algoritmo llega a la celda destino, no si el
tobillo compenso bien. Que sea determinista es una feature: la misma ruta da
siempre el mismo resultado, y eso hace que corregir sea justo.

Lo que NO modela (y el robot real si tiene): inercia, deslizamiento, tiempo de
arranque y frenado, y la posibilidad de tropezar.

RECHAZA, NO RECORTA. Ver CONTRATO_API.md seccion 4: recortar en silencio hace
que el alumno calibre a ciegas, y como la distancia es velocidad x tiempo, un
recorte de velocidad corrompe la distancia recorrida.
"""

from __future__ import annotations

import math
import threading
import time

from .safety import (
    ErrorDeSeguridad,
    PerfilSeguridad,
    validar_duracion,
    validar_velocidad,
    validar_velocidad_angular,
)

ALTURA_BASE = 0.78  # altura del torso de pie, en metros
BATERIA_SIMULADA = 87  # inventada; ver CONTRATO_API.md seccion 6


class Mundo:
    """Pose del robot (x, y, yaw) + fase de la animacion de piernas."""

    def __init__(self, perfil: PerfilSeguridad):
        self._lock = threading.RLock()
        self.perfil = perfil
        self.reiniciar()

    def reiniciar(self) -> None:
        with self._lock:
            self.x = 0.0
            self.y = 0.0
            self.yaw = 0.0
            self.vx = 0.0
            self.vy = 0.0
            self.vyaw = 0.0
            self.fase = 0.0
            self.accion = "quieto"
            self._vence_en = 0.0
            self._gesto_hasta = 0.0
            self._ultimo_avance = time.monotonic()
            self.de_pie = True
            self.altura = 0.0        # offset sobre la altura normal, en metros
            self.avisos = []

    # ---------- ordenes ----------
    def mover(self, vx: float, vy: float, vyaw: float, tiempo: float) -> None:
        """Fija la velocidad por 'tiempo' segundos. RECHAZA si excede el perfil.

        El robot real hace exactamente esto: Move() no es un paso, es una
        velocidad con vencimiento. Si no la refrescas, se detiene.
        """
        vx = validar_velocidad(vx, self.perfil)
        vy = validar_velocidad(vy, self.perfil)
        vyaw = validar_velocidad_angular(vyaw, self.perfil)
        tiempo = validar_duracion(tiempo, self.perfil)

        with self._lock:
            self.vx, self.vy, self.vyaw = vx, vy, vyaw
            self._vence_en = tiempo
            if abs(vyaw) > abs(vx) + abs(vy):
                self.accion = "girando"
            elif vx or vy:
                self.accion = "avanzando"
            else:
                self.accion = "quieto"

    # --- API que usa el servicio sport (el LocoClient real habla con el) ---
    def set_velocidad(self, vx: float, vy: float, vyaw: float,
                      duracion: float = 1.0) -> None:
        """Como mover(), pero RECORTA en vez de rechazar.

        Es la unica excepcion a la regla de rechazar, y tiene motivo: aca la
        orden llega por DDS desde el LocoClient del SDK, que DESCARTA el codigo
        de retorno de SetVelocity. Si rechazaramos, el alumno no se enteraria
        nunca: veria el robot quieto y ningun mensaje.

        Por eso la validacion que el alumno SI ve vive en robot.py, antes de
        tocar DDS. Esto de aca es la ultima defensa: recorta, avisa por consola
        del simulador, y nunca deja pasar un valor fuera del techo.
        """
        lim = []
        for valor, tope, nombre in ((vx, self.perfil.velocidad_max, "vx"),
                                    (vy, self.perfil.velocidad_max, "vy"),
                                    (vyaw, self.perfil.velocidad_angular_max, "vyaw")):
            if abs(valor) > tope + 1e-9:
                self.avisos.append(f"{nombre}={valor:.2f} recortado a {tope:.2f}")
                valor = math.copysign(tope, valor)
            lim.append(float(valor))

        with self._lock:
            if not self.de_pie:
                self.avisos.append("el robot no esta de pie: ignoro el movimiento")
                return
            self.vx, self.vy, self.vyaw = lim
            self._vence_en = max(0.0, float(duracion))
            if abs(self.vyaw) > abs(self.vx) + abs(self.vy):
                self.accion = "girando"
            elif self.vx or self.vy:
                self.accion = "avanzando"
            else:
                self.accion = "quieto"

    def set_de_pie(self, de_pie: bool) -> None:
        with self._lock:
            self.de_pie = de_pie
            if not de_pie:
                self.vx = self.vy = self.vyaw = 0.0
                self._vence_en = 0.0
                self.accion = "quieto"

    def set_altura(self, altura: float) -> None:
        with self._lock:
            self.altura = max(-0.25, min(0.0, float(altura)))

    def detener(self) -> None:
        """Velocidad a cero. No apaga nada: el robot queda parado."""
        with self._lock:
            self.vx = self.vy = self.vyaw = 0.0
            self._vence_en = 0.0
            self.accion = "quieto"

    def gesto(self, nombre: str, duracion: float = 2.0) -> None:
        with self._lock:
            self.vx = self.vy = self.vyaw = 0.0
            self._vence_en = 0.0
            self.accion = nombre
            self._gesto_hasta = time.monotonic() + duracion

    # ---------- lo llama el bucle del simulador ----------
    # Paso maximo de integracion. Con velocidades de 0.25 m/s, 20 ms son 5 mm:
    # de sobra para que el arco de un giro salga bien.
    SUBPASO = 0.02

    def avanzar(self, dt: float | None = None) -> None:
        """Integra el tiempo transcurrido. NUNCA descarta tiempo.

        Usa el reloj real medido, no un dt nominal: con dt nominal fijo el mundo
        avanza ~8% mas lento que el reloj y TODA ruta queda corta, desalineando
        la grilla del TP03. Ese bug ya se corrigio una vez; no reintroducirlo.

        Si la ventana se congela y llegan 300 ms de golpe, se integran los 300 ms
        en sub-pasos. Recortarlos volveria a acortar la ruta, en silencio y de
        forma distinta en cada maquina: el alumno con la notebook mas lenta
        recibiria peor nota por el hardware, no por su algoritmo.
        """
        ahora = time.monotonic()
        with self._lock:
            if dt is None:
                dt = ahora - self._ultimo_avance
            self._ultimo_avance = ahora
            if dt <= 0.0:
                return

            if self._gesto_hasta and ahora >= self._gesto_hasta:
                self._gesto_hasta = 0.0
                self.accion = "quieto"

            restante = dt
            while restante > 1e-9:
                paso = min(self.SUBPASO, restante)
                restante -= paso
                self._integrar(paso)

    def _integrar(self, dt: float) -> None:
        """Un sub-paso. Se llama con el lock tomado."""
        if self._vence_en <= 0.0:
            if self.vx or self.vy or self.vyaw:
                self.vx = self.vy = self.vyaw = 0.0
                self.accion = "quieto"
            return

        # El comando puede vencer en la mitad de este sub-paso: se integra solo
        # la fraccion que corresponde, para que el total sea exactamente v x t.
        efectivo = min(dt, self._vence_en)
        self._vence_en -= dt

        # vx/vy vienen en el marco del ROBOT; el mundo esta rotado por yaw.
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        self.x += (self.vx * c - self.vy * s) * efectivo
        self.y += (self.vx * s + self.vy * c) * efectivo
        self.yaw = (self.yaw + self.vyaw * efectivo + math.pi) % (2 * math.pi) - math.pi

        rapidez = math.hypot(self.vx, self.vy) + 0.3 * abs(self.vyaw)
        self.fase += rapidez * 6.0 * efectivo

    def leer(self) -> dict:
        with self._lock:
            return {
                "x": round(self.x, 4),
                "y": round(self.y, 4),
                "z": ALTURA_BASE,
                "yaw": round(self.yaw, 4),
                "accion": self.accion,
                "altura": self.altura,
                "de_pie": self.de_pie,
                "bateria": BATERIA_SIMULADA,
                "moviendose": abs(self.vx) + abs(self.vy) + abs(self.vyaw) > 1e-6,
                "fase": self.fase,
            }
