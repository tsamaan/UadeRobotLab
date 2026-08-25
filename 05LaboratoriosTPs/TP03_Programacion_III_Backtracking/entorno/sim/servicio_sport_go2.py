"""Servicio 'sport' del Go2: el SportClient real del SDK le habla sin saberlo.

Mismo nombre de servicio que el G1 ("sport"), pero otros api ids. El alumno
escribe SportClient().Move(vx, vy, vyaw) y funciona igual contra el simulador
que contra el Go2 fisico.
"""

from __future__ import annotations

import json

from unitree_sdk2py.go2.sport.sport_api import (
    SPORT_SERVICE_NAME,
    SPORT_API_VERSION,
    SPORT_API_ID_BALANCESTAND,
    SPORT_API_ID_DAMP,
    SPORT_API_ID_HELLO,
    SPORT_API_ID_MOVE,
    SPORT_API_ID_RISESIT,
    SPORT_API_ID_SIT,
    SPORT_API_ID_STANDDOWN,
    SPORT_API_ID_STANDUP,
    SPORT_API_ID_STOPMOVE,
)
from unitree_sdk2py.rpc.server import Server


class ServicioSportGo2(Server):
    def __init__(self, mundo, verboso: bool = True):
        super().__init__(SPORT_SERVICE_NAME)
        self.mundo = mundo
        self.verboso = verboso
        self.Init()
        # Sin esto el servidor rechaza todo por version: el SportClient declara
        # SPORT_API_VERSION al inicializarse y las dos puntas tienen que coincidir.
        self._SetApiVersion(SPORT_API_VERSION)

        rutas = {
            SPORT_API_ID_MOVE: self._move,
            SPORT_API_ID_STOPMOVE: self._stop,
            SPORT_API_ID_STANDUP: lambda p: self._postura(True, "de pie"),
            SPORT_API_ID_BALANCESTAND: lambda p: self._postura(True, "equilibrio"),
            SPORT_API_ID_RISESIT: lambda p: self._postura(True, "se levanta"),
            SPORT_API_ID_STANDDOWN: lambda p: self._postura(False, "se agacha"),
            SPORT_API_ID_SIT: lambda p: self._postura(False, "se sienta"),
            SPORT_API_ID_DAMP: lambda p: self._postura(False, "damp"),
            SPORT_API_ID_HELLO: self._hello,
        }
        for api_id, fn in rutas.items():
            self._RegistHandler(api_id, self._envolver(fn), False)

        # Sin Start() el servidor queda registrado pero nunca escucha, y el
        # SportClient da timeout sin decir por que.
        self.Start()

    def _envolver(self, fn):
        def handler(parameter: str):
            try:
                return fn(parameter)
            except Exception as exc:      # nunca tirar el servicio
                self._log(f"error: {exc}")
                return (0, "")
        return handler

    def _log(self, texto: str) -> None:
        if self.verboso:
            print(f"  [GO2] {texto}")

    def _move(self, parameter: str):
        p = json.loads(parameter) if parameter else {}
        vx = float(p.get("x", 0.0))
        vy = float(p.get("y", 0.0))
        vyaw = float(p.get("z", 0.0))
        # duracion corta a proposito: Move() del SDK es una velocidad con
        # vencimiento. Si el programa muere, el robot frena solo.
        self.mundo.set_velocidad(vx, vy, vyaw, 1.0)
        return (0, "")

    def _stop(self, parameter: str):
        self.mundo.detener()
        return (0, "")

    def _postura(self, de_pie: bool, nombre: str):
        self.mundo.set_de_pie(de_pie)
        self._log(nombre)
        return (0, "")

    def _hello(self, parameter: str):
        self.mundo.gesto("saludando")
        self._log("saluda")
        return (0, "")
