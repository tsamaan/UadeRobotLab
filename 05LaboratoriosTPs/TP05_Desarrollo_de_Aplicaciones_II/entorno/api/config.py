"""Configuracion del backend TP05 en el paquete del simulador.

Es el mismo backend que corre en el laboratorio fisico. La diferencia esta
aca: el paquete NO lleva IPs ni credenciales del robot, porque no las
necesita y son un pasivo.
"""

from __future__ import annotations

import socket
import struct
from pathlib import Path
from typing import Optional

try:
    import fcntl
except ImportError:  # pragma: no cover - el laboratorio se ejecuta en Linux
    fcntl = None


ROBOTS = {
    "go2": {
        "nombre": "Unitree Go2 EDU",
        "tipo": "cuadrupedo",
        "n_motores": 12,
        "topic_lowstate": "rt/lf/lowstate",
        "msg_type": "unitree_go",
        "patas": ["FR", "FL", "RR", "RL"],
        "motores_nombres": [
            "FR_hip", "FR_thigh", "FR_calf",
            "FL_hip", "FL_thigh", "FL_calf",
            "RR_hip", "RR_thigh", "RR_calf",
            "RL_hip", "RL_thigh", "RL_calf",
        ],
    },
    "g1": {
        "nombre": "Unitree G1 EDU",
        "tipo": "humanoide",
        "n_motores": 29,
        "topic_lowstate": "rt/lf/lowstate",
        "msg_type": "unitree_hg",
        "patas": ["R_foot", "L_foot"],
        "motores_nombres": [
            "L_hip_yaw", "L_hip_roll", "L_hip_pitch",
            "L_knee", "L_ankle_pitch", "L_ankle_roll",
            "R_hip_yaw", "R_hip_roll", "R_hip_pitch",
            "R_knee", "R_ankle_pitch", "R_ankle_roll",
            "torso_yaw", "torso_roll", "torso_pitch",
            "L_shoulder_pitch", "L_shoulder_roll", "L_shoulder_yaw",
            "L_elbow", "L_wrist_roll", "L_wrist_pitch", "L_wrist_yaw",
            "R_shoulder_pitch", "R_shoulder_roll", "R_shoulder_yaw",
            "R_elbow", "R_wrist_roll", "R_wrist_pitch", "R_wrist_yaw",
        ],
    },
}

ROBOT_ACTIVO = "go2"
NETWORK_INTERFACE = None
API_HOST = "0.0.0.0"
API_PORT = 8001
API_CORS_ORIGINS = ["*"]
TELEMETRY_RATE_HZ = 10
WEBSOCKET_RATE_HZ = 10


def _ipv4_interfaz(nombre: str) -> Optional[str]:
    if fcntl is None:
        return None
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = fcntl.ioctl(
            sock.fileno(), 0x8915, struct.pack("256s", nombre[:15].encode())
        )
        return socket.inet_ntoa(data[20:24])
    except (OSError, PermissionError):
        return None
    finally:
        if sock is not None:
            sock.close()


def interfaces_ipv4() -> dict[str, str]:
    """Devuelve las interfaces activas que tienen una direccion IPv4."""
    base = Path("/sys/class/net")
    nombres = [p.name for p in base.iterdir()] if base.exists() else []
    return {
        nombre: ip
        for nombre in nombres
        if nombre != "lo" and (ip := _ipv4_interfaz(nombre))
    }


def detectar_interfaz_red(*_a, **_k) -> str:
    """En el paquete siempre es 'lo': el simulador corre en esta maquina.

    La deteccion de la interfaz del robot vive en el laboratorio fisico, que es
    el unico que se conecta por RJ-45.
    """
    return "lo"
