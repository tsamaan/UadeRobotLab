"""Lector de telemetria del TP05 para el PAQUETE: lee por socket, no por DDS.

El laboratorio fisico lee el `LowState_` del robot por DDS. Eso no se puede
reproducir en la maquina de un profesor con macOS o Windows: CycloneDDS no
tiene wheels para Python 3.11+, y `unitree_sdk2py` llama a `timerfd_create`,
que es una syscall de Linux. Ver `entorno/sim/local.py`.

Asi que aca se le pregunta al simulador por el mismo socket local que usa el
programa del alumno. **La forma del snapshot es identica** a la que devolvia el
lector DDS -- `motor_state`, `imu`, `bms`, `foot_force` -- para que
`telemetry_adapter.py` y el dashboard no se enteren de la diferencia.

El `DemoReader` (modo `--demo`, datos inventados sin simulador) se reusa tal
cual del lector del laboratorio, que viaja al paquete como
`telemetry_reader_dds.py`: no depende del transporte.
"""

from __future__ import annotations

import json
import socket
import threading
import time

from config import ROBOTS

# Tiene que coincidir con `entorno/sim/local.py`.
HOST = "127.0.0.1"
PUERTO = 8765


def _puerto_del_simulador() -> int:
    """El simulador deja anotado en que puerto quedo escuchando."""
    import os
    from pathlib import Path

    marca = (Path(__file__).resolve().parent.parent / "sim"
             / ".simulador_activo.json")
    try:
        with open(marca, encoding="utf-8") as f:
            return int(json.load(f).get("puerto", PUERTO))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return PUERTO


class TelemetryReader:
    """Sondea al simulador por el socket local y guarda la ultima foto."""

    # 20 Hz. El dashboard grafica a esta velocidad; mas rapido no aporta nada
    # y solo carga la maquina del profesor, que ademas esta corriendo MuJoCo.
    PERIODO = 0.05

    def __init__(self, modelo: str, network_interface: str | None = None):
        # network_interface se acepta y se ignora a proposito: mantiene la
        # misma firma que el lector DDS del laboratorio, asi `arrancar_api.py`
        # es el mismo archivo en los dos lados.
        if modelo not in ROBOTS:
            raise ValueError(f"Modelo desconocido: {modelo}")
        self.modelo = modelo
        self.config = ROBOTS[modelo]
        self._lock = threading.Lock()
        self._snapshot = None
        self._mensajes = 0
        self._cortar = threading.Event()
        self._aviso_dado = False
        self._hilo = threading.Thread(target=self._bucle, daemon=True)
        self._hilo.start()

    # ---------- el hilo que sondea ----------
    def _bucle(self) -> None:
        while not self._cortar.is_set():
            try:
                self._sesion()
            except Exception as exc:                          # noqa: BLE001
                # Nunca dejar morir el hilo: si el simulador se cierra y se
                # vuelve a abrir, esto tiene que reengancharse solo. El lector
                # DDS moria para siempre ante la primera excepcion y el
                # dashboard se quedaba mudo sin decir por que.
                if not self._aviso_dado:
                    self._aviso_dado = True
                    print(f"[TELEMETRIA] Sin conexion con el simulador "
                          f"({type(exc).__name__}: {exc}). Reintentando...")
            self._cortar.wait(1.0)

    def _sesion(self) -> None:
        with socket.create_connection((HOST, _puerto_del_simulador()),
                                      timeout=3.0) as sock:
            sock.settimeout(3.0)
            with sock.makefile("rwb") as canal:
                self._aviso_dado = False
                while not self._cortar.is_set():
                    canal.write(b'{"orden": "telemetria"}\n')
                    canal.flush()
                    linea = canal.readline()
                    if not linea:
                        return          # el simulador cerro: se reintenta
                    datos = json.loads(linea.decode("utf-8"))
                    tele = datos.get("telemetria") or {}
                    if tele:
                        self._guardar(tele)
                    time.sleep(self.PERIODO)

    def _guardar(self, tele: dict) -> None:
        n = self.config["n_motores"]
        snapshot = {
            "timestamp": time.time(),
            "motor_state": tele.get("motor_state", [])[:n],
            "imu": tele.get("imu", {}),
            "bms": tele.get("bms", {}),
            "foot_force": tele.get("foot_force", []),
        }
        with self._lock:
            self._snapshot = snapshot
            self._mensajes += 1

    # ---------- la misma interfaz que el lector DDS ----------
    def obtener_snapshot(self) -> dict | None:
        import copy

        with self._lock:
            return copy.deepcopy(self._snapshot)

    def esperar_primer_dato(self, timeout: float = 5.0) -> bool:
        limite = time.monotonic() + timeout
        while time.monotonic() < limite:
            with self._lock:
                if self._snapshot is not None:
                    return True
            time.sleep(0.1)
        return False

    @property
    def mensajes_leidos(self) -> int:
        with self._lock:
            return self._mensajes

    def cerrar(self) -> None:
        self._cortar.set()


# El modo --demo no depende del transporte: se reusa el del laboratorio.
try:
    from telemetry_reader_dds import DemoReader          # noqa: F401
except ImportError:                                      # pragma: no cover
    DemoReader = None
