from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Any


@dataclass
class EstadoRobot:
    x: float
    y: float
    z: float
    yaw: float
    accion: str


class RobotG1:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765, timeout: float = 30.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.conectado = False

    def conectar(self) -> EstadoRobot:
        estado = self.verificar_estado()
        self.conectado = True
        print("[OK] Conectado al simulador G1.")
        return estado

    def verificar_estado(self) -> EstadoRobot:
        response = self._request({"command": "estado"})
        return self._estado_from_response(response)

    def movimiento(
        self,
        adelante: float = 0.0,
        costado: float = 0.0,
        giro: float = 0.0,
        tiempo: float = 1.0,
    ) -> EstadoRobot:
        response = self._request(
            {
                "command": "movimiento",
                "adelante": adelante,
                "costado": costado,
                "giro": giro,
                "tiempo": tiempo,
            }
        )
        return self._estado_from_response(response)

    def movmineto(
        self,
        adelante: float = 0.0,
        costado: float = 0.0,
        giro: float = 0.0,
        tiempo: float = 1.0,
    ) -> EstadoRobot:
        return self.movimiento(adelante, costado, giro, tiempo)

    def saludar(self) -> EstadoRobot:
        response = self._request({"command": "saludar"})
        return self._estado_from_response(response)

    def dar_beso(self) -> EstadoRobot:
        response = self._request({"command": "dar_beso"})
        return self._estado_from_response(response)

    def dar_un_beso(self) -> EstadoRobot:
        return self.dar_beso()

    def detenerse(self) -> EstadoRobot:
        response = self._request({"command": "detenerse"})
        return self._estado_from_response(response)

    def desconectar(self) -> None:
        self.conectado = False
        print("[OK] Desconectado del simulador G1.")

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        message = json.dumps(payload).encode("utf-8") + b"\n"
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as client:
                client.sendall(message)
                data = b""
                while not data.endswith(b"\n"):
                    chunk = client.recv(4096)
                    if not chunk:
                        break
                    data += chunk
        except OSError as exc:
            raise RuntimeError(
                "No se pudo conectar al simulador G1. "
                "Primero abri run_g1_sim.ps1 y deja la ventana de MuJoCo abierta."
            ) from exc

        if not data:
            raise RuntimeError("El simulador no respondio.")

        response = json.loads(data.decode("utf-8"))
        if not response.get("ok"):
            raise RuntimeError(response.get("error", "Comando rechazado por el simulador."))
        return response

    @staticmethod
    def _estado_from_response(response: dict[str, Any]) -> EstadoRobot:
        estado = response["estado"]
        return EstadoRobot(
            x=float(estado["x"]),
            y=float(estado["y"]),
            z=float(estado["z"]),
            yaw=float(estado["yaw"]),
            accion=str(estado["accion"]),
        )
