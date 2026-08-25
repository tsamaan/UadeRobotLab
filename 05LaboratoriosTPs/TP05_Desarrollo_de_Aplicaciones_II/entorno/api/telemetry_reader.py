"""Lectores de telemetria real DDS y simulada."""

from __future__ import annotations

import copy
import math
import threading
import time
from typing import Any

from config import ROBOTS


def _valor(obj: Any, nombre: str, default=None):
    """Lee campos IDL que, segun la version del SDK, son metodo o atributo."""
    try:
        valor = getattr(obj, nombre)
        return valor() if callable(valor) else valor
    except (AttributeError, TypeError):
        return default


def _lista(valor: Any, default=None) -> list:
    if isinstance(valor, (int, float)):
        return [valor]
    try:
        return list(valor)
    except (TypeError, ValueError):
        return list(default or [])


class TelemetryReader:
    """Suscriptor de solo lectura al LowState de un robot Unitree."""

    def __init__(self, modelo: str, network_interface: str | None = None):
        if modelo not in ROBOTS:
            raise ValueError(f"Modelo desconocido: {modelo}")
        self.modelo = modelo
        self.config = ROBOTS[modelo]
        self._lock = threading.Lock()
        self._snapshot = None
        self._mensajes = 0
        self._subscriber = None

        try:
            from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
            if modelo == "go2":
                from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowState_
            else:
                from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_
        except ImportError as exc:
            raise RuntimeError(
                "No se encontro unitree_sdk2py. Instale requirements.txt o use --demo."
            ) from exc

        ChannelFactoryInitialize(0, network_interface)
        self._subscriber = ChannelSubscriber(self.config["topic_lowstate"], LowState_)
        self._subscriber.Init(self._on_low_state, 10)

    def _on_low_state(self, msg):
        motores_raw = _lista(_valor(msg, "motor_state", []))
        motores = []
        for indice, motor in enumerate(motores_raw[: self.config["n_motores"]]):
            motores.append({
                "id": indice,
                "q": float(_valor(motor, "q", 0.0) or 0.0),
                "dq": float(_valor(motor, "dq", 0.0) or 0.0),
                "tau_est": float(_valor(motor, "tau_est", 0.0) or 0.0),
                "temperature": int(_valor(motor, "temperature", 0) or 0),
            })

        imu = _valor(msg, "imu_state")
        bms = _valor(msg, "bms_state")
        temperaturas = _lista(_valor(bms, "temperature", [])) if bms else []
        if not temperaturas and bms:
            temperaturas = _lista(_valor(bms, "temp", []))
        snapshot = {
            "timestamp": time.time(),
            "motor_state": motores,
            "imu": {
                "quaternion": _lista(_valor(imu, "quaternion", [1, 0, 0, 0])),
                "accelerometer": _lista(_valor(imu, "accelerometer", [0, 0, 0])),
                "gyroscope": _lista(_valor(imu, "gyroscope", [0, 0, 0])),
            },
            "bms": {
                "soc": int(_valor(bms, "soc", 0) or 0),
                "current": int(_valor(bms, "current", 0) or 0),
                "cell_vol": _lista(_valor(bms, "cell_vol", [])),
                "temperature": max(temperaturas) if temperaturas else 0,
            },
            "foot_force": _lista(_valor(msg, "foot_force", [])),
        }
        with self._lock:
            self._snapshot = snapshot
            self._mensajes += 1

    def obtener_snapshot(self) -> dict | None:
        with self._lock:
            return copy.deepcopy(self._snapshot)

    def esperar_primer_dato(self, timeout: float = 5.0) -> bool:
        limite = time.monotonic() + timeout
        while time.monotonic() < limite:
            if self.obtener_snapshot() is not None:
                return True
            time.sleep(0.05)
        return False

    @property
    def mensajes_leidos(self) -> int:
        with self._lock:
            return self._mensajes

    def cerrar(self):
        sub, self._subscriber = self._subscriber, None
        if sub is not None:
            for metodo in ("Close", "close"):
                fn = getattr(sub, metodo, None)
                if callable(fn):
                    fn()
                    break


class DemoReader:
    """Genera telemetria deterministica y animada para usar sin robot."""

    def __init__(self, modelo: str = "go2"):
        if modelo not in ROBOTS:
            raise ValueError(f"Modelo desconocido: {modelo}")
        self.modelo = modelo
        self.config = ROBOTS[modelo]
        self._inicio = time.time()
        self._mensajes = 0

    def _simular_motor(self, indice: int, t: float) -> dict:
        fase = indice * 0.45
        return {
            "id": indice,
            "q": math.radians(28 * math.sin(t * 0.8 + fase)),
            "dq": 2.2 * math.cos(t * 0.8 + fase),
            "tau_est": 5 + 4 * math.sin(t * 1.1 + fase),
            "temperature": 34 + int(9 * (1 + math.sin(t * 0.08 + fase)) / 2),
        }

    def obtener_snapshot(self) -> dict:
        t = time.time() - self._inicio
        n = self.config["n_motores"]
        n_patas = len(self.config["patas"])
        angulo = 0.04 * math.sin(t * 0.5)
        self._mensajes += 1
        return {
            "timestamp": time.time(),
            "motor_state": [self._simular_motor(i, t) for i in range(n)],
            "imu": {
                "quaternion": [math.cos(angulo / 2), 0.0, math.sin(angulo / 2), 0.0],
                "accelerometer": [0.15 * math.sin(t), 0.1 * math.cos(t), 9.81],
                "gyroscope": [0.02 * math.cos(t), 0.01, 0.03 * math.sin(t)],
            },
            "bms": {
                "soc": max(0, 92 - int(t / 180)),
                "current": int(1100 + 350 * math.sin(t * 0.3)),
                "temperature": round(31 + 2 * math.sin(t * 0.05), 1),
                "cell_vol": [int(3710 + 15 * math.sin(t * 0.1 + i)) for i in range(8)],
            },
            "foot_force": [80 if math.sin(t * 2 + i * 1.7) > -0.5 else 0 for i in range(n_patas)],
        }

    def esperar_primer_dato(self, timeout: float = 0) -> bool:
        return True

    @property
    def mensajes_leidos(self) -> int:
        return self._mensajes

    def cerrar(self):
        pass
