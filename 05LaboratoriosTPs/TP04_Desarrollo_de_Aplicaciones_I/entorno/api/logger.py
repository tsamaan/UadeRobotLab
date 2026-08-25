"""Registro en memoria y consola de los comandos recibidos."""

from __future__ import annotations

from datetime import datetime
from threading import RLock
from typing import Any


class CommandLogger:
    def __init__(self) -> None:
        self._historial: list[dict[str, Any]] = []
        self._lock = RLock()

    def registrar(
        self,
        equipo: str,
        endpoint: str,
        params: dict[str, Any] | None,
        resultado: str,
        detalle: str = "",
    ) -> None:
        entrada = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "equipo": equipo,
            "endpoint": endpoint,
            "params": params or {},
            "resultado": resultado,
            "detalle": detalle,
        }
        with self._lock:
            self._historial.append(entrada)
        hora = datetime.now().strftime("%H:%M:%S")
        parametros = f" {entrada['params']}" if entrada["params"] else ""
        sufijo = f" ({detalle})" if detalle else ""
        print(f"[{hora}] {equipo} -> {endpoint}{parametros} -> {resultado.upper()}{sufijo}")

    def obtener_historial(self, equipo: str | None = None, ultimos: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            items = self._historial
            if equipo is not None:
                items = [item for item in items if item["equipo"] == equipo]
            return [dict(item) for item in items[-max(0, ultimos) :]]

    def limpiar(self) -> None:
        with self._lock:
            self._historial.clear()

    @property
    def cantidad(self) -> int:
        with self._lock:
            return len(self._historial)
