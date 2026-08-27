"""Bridge del backend TP04 contra el SIMULADOR.

El backend (api_server.py, endpoints/, sesion_manager.py) es EXACTAMENTE el
mismo que corre en la notebook del laboratorio contra el robot fisico. Lo unico
que cambia es este archivo: alla habla con el robot por RJ-45, aca con el
simulador.

Por eso la app del alumno no necesita cambiar nada el dia de la visita: los
endpoints, el JSON y los errores son identicos. Solo cambia la IP a la que
apunta.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_ENTORNO = Path(__file__).resolve().parent.parent
if str(_ENTORNO) not in sys.path:
    sys.path.insert(0, str(_ENTORNO))

from sim.robot import Robot  # noqa: E402
from sim.safety import ErrorDeSeguridad  # noqa: E402

# Cada comando del joystick dura esto y despues vence. Es corto a proposito:
# si la app deja de mandar -- se cierra, se corta el WiFi, el alumno suelta el
# control -- el robot frena solo. Es el hombre muerto.
DURACION_COMANDO = 0.4


class RobotBridge:
    """Lo que el backend le pide al robot. Mismos metodos que el bridge fisico."""

    def __init__(self, robot: str = "g1", **_ignorado):
        self.tipo_robot = robot
        self.conectado = False
        self._robot: Robot | None = None

    def conectar(self) -> bool:
        try:
            self._robot = Robot(materia="tp04")
            self._robot.conectar()
            self.conectado = True
            return True
        except Exception as exc:
            print(f"[BRIDGE] No se pudo conectar al simulador: {exc}")
            self._robot = None
            return False

    def desconectar(self) -> None:
        if self._robot is not None:
            try:
                self._robot.desconectar()
            except Exception:
                pass
        self._robot = None
        self.conectado = False

    # ---------- movimiento ----------
    def mover(self, vx: float, vy: float, vyaw: float) -> bool:
        """Una pulsacion del joystick: las tres velocidades por un rato corto.

        Se mandan LAS TRES JUNTAS, igual que el Move() del SDK contra el robot
        real. Asi una curva -- avanzar y girar a la vez -- se comporta igual en
        el simulador que en el aula.
        """
        if self._robot is None:
            return False
        try:
            if not (vx or vy or vyaw):
                self._robot.detenerse()
            else:
                self._robot.mover(vx=vx, vy=vy, vyaw=vyaw,
                                  tiempo=DURACION_COMANDO)
            return True
        except ErrorDeSeguridad as exc:
            print(f"[BRIDGE] {exc}")
            return False
        except Exception as exc:
            print(f"[BRIDGE] Fallo el movimiento: {exc}")
            return False

    def mover_durante(self, vx: float, vy: float, vyaw: float,
                      tiempo: float) -> bool:
        """Sostiene las tres velocidades 'tiempo' segundos y despues frena.

        Es la forma "velocidad y tiempo", la misma primitiva que usan los otros
        seis TPs. El simulador ya sostiene y frena solo, asi que aca alcanza con
        pasarle la duracion; en el laboratorio fisico el bridge tiene que
        refrescar el Move() cada 100 ms porque el del SDK vence al segundo.
        """
        if self._robot is None:
            return False
        try:
            if not (vx or vy or vyaw):
                self._robot.detenerse()
            else:
                self._robot.mover(vx=vx, vy=vy, vyaw=vyaw, tiempo=tiempo)
                self._robot.detenerse()
            return True
        except ErrorDeSeguridad as exc:
            print(f"[BRIDGE] {exc}")
            return False
        except Exception as exc:
            print(f"[BRIDGE] Fallo el movimiento: {exc}")
            return False

    def avanzar(self, velocidad: float = 0.2, duracion: float = 1.0) -> bool:
        return self._intentar("avanzar", velocidad=velocidad, tiempo=duracion)

    def girar(self, velocidad: float = 0.5, duracion: float = 1.0) -> bool:
        return self._intentar("girar", velocidad=velocidad, tiempo=duracion)

    def detenerse(self) -> bool:
        """Velocidad cero. NO apaga el robot ni lo desenergiza."""
        return self._intentar("detenerse")

    # ---------- gestos permitidos ----------
    #
    # Lista blanca: solo movimiento y gestos que NO cambian la postura. Ver
    # sim/acciones.py. El robot se prende y se para desde el control oficial, y
    # eso lo hace el operador.
    def saludar(self) -> bool:
        return self._intentar("saludar")

    def dar_la_mano(self) -> bool:
        return self._intentar("dar_la_mano")

    # ---------- bloqueados a proposito ----------
    def pararse(self) -> bool:
        return self._bloqueado(
            "pararse", "levantar el robot lo hace el operador con el control oficial")

    def sentarse(self) -> bool:
        return self._bloqueado(
            "sentarse", "sentar al robot cambia su postura; solo con alguien al lado")

    def estirar(self) -> bool:
        return self._bloqueado("estirar", "cambia la postura del robot")

    @staticmethod
    def _bloqueado(nombre: str, motivo: str) -> bool:
        print(f"[BRIDGE] '{nombre}' esta bloqueado: {motivo}.")
        return False

    # ---------- estado ----------
    def verificar_estado(self) -> dict[str, Any]:
        if self._robot is None:
            return {"conectado": False, "bateria": None, "modelo": self.tipo_robot}
        try:
            e = self._robot.verificar_estado()
            return {
                "conectado": True,
                "modelo": self.tipo_robot,
                "bateria": e.bateria,
                "x": e.x, "y": e.y, "yaw": e.yaw,
                "accion": e.accion,
                "simulado": True,
            }
        except Exception as exc:
            print(f"[BRIDGE] No se pudo leer el estado: {exc}")
            return {"conectado": False, "bateria": None, "modelo": self.tipo_robot}

    # ---------- interno ----------
    def _intentar(self, metodo: str, **kwargs) -> bool:
        if self._robot is None:
            return False
        try:
            getattr(self._robot, metodo)(**kwargs)
            return True
        except ErrorDeSeguridad as exc:
            print(f"[BRIDGE] {exc}")
            return False
        except Exception as exc:
            print(f"[BRIDGE] Fallo {metodo}: {exc}")
            return False


class MockBridge(RobotBridge):
    """Sin simulador ni robot. Solo para probar la API a mano."""

    def conectar(self) -> bool:
        self.conectado = True
        return True

    def mover(self, vx, vy, vyaw):
        return True

    def mover_durante(self, vx, vy, vyaw, tiempo):
        return True

    def verificar_estado(self):
        return {"conectado": True, "modelo": self.tipo_robot, "bateria": 87,
                "x": 0.0, "y": 0.0, "yaw": 0.0, "accion": "quieto", "mock": True}

    def _intentar(self, metodo, **kwargs):
        return True
