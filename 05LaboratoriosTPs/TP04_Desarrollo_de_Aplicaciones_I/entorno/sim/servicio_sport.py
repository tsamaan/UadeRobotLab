"""Servicio 'sport' simulado: el LocoClient real del SDK le habla sin saberlo.

El alumno escribe LocoClient().Move(vx, vy, vyaw) y funciona igual contra el
simulador que contra el G1. La unica diferencia son domain_id/interface.

En el simulador esto desliza la base en MuJoCo. En el robot real, el mismo
llamado pega contra el servicio propietario de Unitree y camina de verdad.
"""

from __future__ import annotations

import json

from unitree_sdk2py.rpc.server import Server
from unitree_sdk2py.g1.loco.g1_loco_api import (
    LOCO_SERVICE_NAME,
    LOCO_API_VERSION,
    ROBOT_API_ID_LOCO_GET_FSM_ID,
    ROBOT_API_ID_LOCO_GET_FSM_MODE,
    ROBOT_API_ID_LOCO_GET_BALANCE_MODE,
    ROBOT_API_ID_LOCO_GET_SWING_HEIGHT,
    ROBOT_API_ID_LOCO_GET_STAND_HEIGHT,
    ROBOT_API_ID_LOCO_SET_FSM_ID,
    ROBOT_API_ID_LOCO_SET_BALANCE_MODE,
    ROBOT_API_ID_LOCO_SET_SWING_HEIGHT,
    ROBOT_API_ID_LOCO_SET_STAND_HEIGHT,
    ROBOT_API_ID_LOCO_SET_VELOCITY,
    ROBOT_API_ID_LOCO_SET_ARM_TASK,
    ROBOT_API_ID_LOCO_SET_SPEED_MODE,
    ROBOT_API_ID_LOCO_SWITCH_TO_USER_CTRL,
    ROBOT_API_ID_LOCO_SWITCH_TO_INTERNAL_CTRL,
)

# FSM ids que usa LocoClient (ver g1_loco_client.py)
FSM = {
    0: "ZeroTorque", 1: "Damp", 3: "Sit",
    500: "Start", 702: "Lie2StandUp", 706: "Squat<->StandUp",
    4: "Caminar",
}
# Estados en los que el robot NO acepta moverse.
FSM_SIN_MOVIMIENTO = {0, 1, 3}

UINT32_MAX = (1 << 32) - 1


class ServicioSportSimulado(Server):
    def __init__(self, mundo, verboso: bool = True):
        super().__init__(LOCO_SERVICE_NAME)
        self.mundo = mundo
        self.verboso = verboso
        self.fsm_id = 4
        self.balance_mode = 0
        self.swing_height = 0.08
        self.llamadas = 0
        self._ultima_firma = None

        self.Init()
        self._SetApiVersion(LOCO_API_VERSION)

        rutas = {
            ROBOT_API_ID_LOCO_SET_VELOCITY: self._set_velocity,
            ROBOT_API_ID_LOCO_SET_FSM_ID: self._set_fsm_id,
            ROBOT_API_ID_LOCO_SET_STAND_HEIGHT: self._set_stand_height,
            ROBOT_API_ID_LOCO_SET_BALANCE_MODE: self._set_balance_mode,
            ROBOT_API_ID_LOCO_SET_SWING_HEIGHT: self._set_swing_height,
            ROBOT_API_ID_LOCO_SET_ARM_TASK: self._ok,
            ROBOT_API_ID_LOCO_SET_SPEED_MODE: self._ok,
            ROBOT_API_ID_LOCO_SWITCH_TO_USER_CTRL: self._ok,
            ROBOT_API_ID_LOCO_SWITCH_TO_INTERNAL_CTRL: self._ok,
            ROBOT_API_ID_LOCO_GET_FSM_ID: lambda p: (0, json.dumps({"data": self.fsm_id})),
            ROBOT_API_ID_LOCO_GET_FSM_MODE: lambda p: (0, json.dumps({"data": 0})),
            ROBOT_API_ID_LOCO_GET_BALANCE_MODE: lambda p: (0, json.dumps({"data": self.balance_mode})),
            ROBOT_API_ID_LOCO_GET_SWING_HEIGHT: lambda p: (0, json.dumps({"data": self.swing_height})),
            ROBOT_API_ID_LOCO_GET_STAND_HEIGHT: lambda p: (0, json.dumps({"data": 0.78 + self.mundo.leer()["altura"]})),
        }
        for api_id, fn in rutas.items():
            self._RegistHandler(api_id, self._envolver(api_id, fn), False)

        self.Start()

    def _envolver(self, api_id, fn):
        """Parsea el JSON, cuenta la llamada y evita que una excepcion del
        handler se convierta en un 3202 opaco para el alumno."""
        def handler(parameter: str):
            self.llamadas += 1
            try:
                p = json.loads(parameter) if parameter else {}
            except json.JSONDecodeError:
                return 3204, ""  # RPC_ERR_SERVER_API_PARAMETER
            try:
                return fn(p)
            except Exception as exc:  # noqa: BLE001
                print(f"[sim-sport] error en api {api_id}: {exc!r}")
                return 3202, ""
        return handler

    def _log(self, texto):
        if self.verboso:
            print(f"[sim-sport] {texto}")

    # ---------- handlers ----------
    def _ok(self, p):
        return 0, "{}"

    def _set_velocity(self, p):
        vx, vy, vyaw = p.get("velocity", [0.0, 0.0, 0.0])
        dur = float(p.get("duration", 1.0))

        if self.fsm_id in FSM_SIN_MOVIMIENTO:
            self._log(f"Move rechazado: el robot esta en {FSM[self.fsm_id]}. "
                      f"Llama a Start() antes de moverte.")
            return 0, "{}"   # el robot real tampoco falla: simplemente no se mueve

        self.mundo.set_velocidad(vx, vy, vyaw, dur)

        # Los labs refrescan Move() cada 100 ms mientras dura el movimiento, asi
        # que loguear cada llamada tapa la consola. Solo avisamos los cambios.
        firma = (round(vx, 3), round(vy, 3), round(vyaw, 3))
        if firma != self._ultima_firma:
            self._ultima_firma = firma
            if firma == (0.0, 0.0, 0.0):
                self._log("Move -> detenido")
            else:
                continuo = " (continuo)" if dur > 1000 else ""
                self._log(f"Move vx={vx:+.2f} vy={vy:+.2f} vyaw={vyaw:+.2f}{continuo}")
        for aviso in self.mundo.avisos:
            self._log(f"  LIMITE: {aviso}")
        self.mundo.avisos.clear()
        return 0, "{}"

    def _set_fsm_id(self, p):
        self.fsm_id = int(p.get("data", 0))
        self._log(f"FSM -> {self.fsm_id} ({FSM.get(self.fsm_id, 'desconocido')})")
        self.mundo.set_de_pie(self.fsm_id not in FSM_SIN_MOVIMIENTO)
        return 0, "{}"

    def _set_stand_height(self, p):
        valor = float(p.get("data", 0.0))
        # HighStand/LowStand mandan UINT32_MAX / 0 como centinelas.
        if valor == UINT32_MAX:
            self.mundo.set_altura(0.0)
        elif valor == 0:
            self.mundo.set_altura(-0.2)
        else:
            self.mundo.set_altura(valor)
        self._log(f"altura de pie -> {self.mundo.leer()['altura']:.2f} m")
        return 0, "{}"

    def _set_balance_mode(self, p):
        self.balance_mode = int(p.get("data", 0))
        return 0, "{}"

    def _set_swing_height(self, p):
        self.swing_height = float(p.get("data", 0.08))
        return 0, "{}"
