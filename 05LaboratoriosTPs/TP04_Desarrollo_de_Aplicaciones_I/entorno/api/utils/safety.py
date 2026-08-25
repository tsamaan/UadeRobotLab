"""Limites del TP04, tomados del nucleo del simulador.

Mismos numeros que en el laboratorio fisico: los dos salen del mismo perfil.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ENTORNO = Path(__file__).resolve().parent.parent.parent
if str(_ENTORNO) not in sys.path:
    sys.path.insert(0, str(_ENTORNO))

from sim.safety import ErrorDeSeguridad, perfil, validar_bateria as _validar_bateria

PERFIL = perfil("tp04")

VELOCIDAD_MAX_LINEAL = PERFIL.velocidad_max
VELOCIDAD_MAX_ANGULAR = PERFIL.velocidad_angular_max
BATERIA_MIN = PERFIL.bateria_min

_aviso_dado = False


def log_seguridad(mensaje: str) -> None:
    print(f"[SEGURIDAD] {mensaje}")


def clamp_velocidades(vx: float, vy: float, vyaw: float):
    global _aviso_dado
    nvx = max(-VELOCIDAD_MAX_LINEAL, min(VELOCIDAD_MAX_LINEAL, float(vx)))
    nvy = max(-VELOCIDAD_MAX_LINEAL, min(VELOCIDAD_MAX_LINEAL, float(vy)))
    nvyaw = max(-VELOCIDAD_MAX_ANGULAR, min(VELOCIDAD_MAX_ANGULAR, float(vyaw)))
    if not _aviso_dado and (nvx, nvy, nvyaw) != (float(vx), float(vy), float(vyaw)):
        _aviso_dado = True
        log_seguridad(
            f"la app pidio ({vx:.2f}, {vy:.2f}, {vyaw:.2f}) y se recorto a "
            f"({nvx:.2f}, {nvy:.2f}, {nvyaw:.2f}). "
            f"Maximos: {VELOCIDAD_MAX_LINEAL} m/s y {VELOCIDAD_MAX_ANGULAR} rad/s.")
    return nvx, nvy, nvyaw


clamp_velocidad = clamp_velocidades


def validar_bateria(nivel) -> bool:
    try:
        _validar_bateria(nivel, PERFIL)
        return True
    except ErrorDeSeguridad as exc:
        log_seguridad(str(exc))
        return False
