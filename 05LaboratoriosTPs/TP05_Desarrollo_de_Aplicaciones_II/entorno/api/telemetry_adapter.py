"""Normalizacion del LowState al contrato JSON del TP05."""

from __future__ import annotations

import math
import time

from config import ROBOTS
from utils.imu_utils import quaternion_a_euler

_INICIO = time.time()


def _completar(valores, cantidad, default=0.0):
    valores = list(valores or [])[:cantidad]
    return valores + [default] * (cantidad - len(valores))


def adaptar_telemetria(snapshot: dict | None, modelo: str) -> dict:
    if modelo not in ROBOTS:
        raise ValueError(f"Modelo desconocido: {modelo}")
    cfg = ROBOTS[modelo]
    snapshot = snapshot or {}
    motores_raw = snapshot.get("motor_state") or []
    motores = []
    for i in range(cfg["n_motores"]):
        motor = motores_raw[i] if i < len(motores_raw) else {}
        motores.append({
            "id": i,
            "nombre": cfg["motores_nombres"][i],
            "angulo": round(math.degrees(float(motor.get("q", 0.0))), 2),
            "velocidad": round(float(motor.get("dq", 0.0)), 3),
            "torque": round(float(motor.get("tau_est", 0.0)), 2),
            "temperatura": round(float(motor.get("temperature", 0.0)), 1),
        })

    imu_raw = snapshot.get("imu") or {}
    q = _completar(imu_raw.get("quaternion"), 4)
    if q == [0.0, 0.0, 0.0, 0.0]:
        q[0] = 1.0
    roll, pitch, yaw = quaternion_a_euler(*q)
    acc = _completar(imu_raw.get("accelerometer"), 3)
    bms_raw = snapshot.get("bms") or {}
    fuerzas_raw = _completar(snapshot.get("foot_force"), len(cfg["patas"]), 0)

    timestamp = snapshot.get("timestamp")
    ts = max(0.0, float(timestamp) - _INICIO) if timestamp else time.time() - _INICIO
    return {
        "modelo": modelo,
        "ts": round(ts, 2),
        "motores": motores,
        "imu": {
            "roll": roll, "pitch": pitch, "yaw": yaw,
            "ax": round(float(acc[0]), 3),
            "ay": round(float(acc[1]), 3),
            "az": round(float(acc[2]), 3),
        },
        "bms": {
            "soc": int(bms_raw.get("soc", 0)),
            "corriente": int(bms_raw.get("current", 0)),
            "temperatura": round(float(bms_raw.get("temperature", 0.0)), 1),
            "celdas": [round(float(v) / 1000.0, 3) for v in bms_raw.get("cell_vol", [])],
        },
        "fuerzas": {
            nombre: 1 if float(fuerza) > 10 else 0
            for nombre, fuerza in zip(cfg["patas"], fuerzas_raw)
        },
    }
