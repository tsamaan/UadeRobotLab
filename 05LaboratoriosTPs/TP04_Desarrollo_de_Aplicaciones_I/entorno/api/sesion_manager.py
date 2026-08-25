"""Sesion exclusiva para que un solo equipo controle el robot."""

from __future__ import annotations

from datetime import datetime, timedelta
from threading import RLock
from uuid import uuid4

from config import SESION_TIMEOUT_MINUTOS


class SesionOcupadaError(RuntimeError):
    pass


class SesionManager:
    def __init__(self, timeout_minutos: float = SESION_TIMEOUT_MINUTOS) -> None:
        self.timeout = timedelta(minutes=timeout_minutos)
        self.equipo_activo: str | None = None
        self.token: str | None = None
        self.inicio_sesion: datetime | None = None
        self.ultimo_comando: datetime | None = None
        self.historial_sesion: list[dict] = []
        self.total_grupos = 0
        self._lock = RLock()

    def _liberar(self) -> None:
        self.equipo_activo = None
        self.token = None
        self.inicio_sesion = None
        self.ultimo_comando = None
        self.historial_sesion = []

    def verificar_timeout(self) -> bool:
        """Libera una sesion vencida y devuelve True si acaba de vencer."""
        with self._lock:
            if self.token and self.ultimo_comando and datetime.now() - self.ultimo_comando >= self.timeout:
                self._liberar()
                return True
            return False

    def iniciar_sesion(self, nombre_equipo: str) -> dict[str, str]:
        nombre = nombre_equipo.strip()
        if not nombre:
            raise ValueError("El nombre del equipo no puede estar vacio.")
        with self._lock:
            self.verificar_timeout()
            if self.token:
                raise SesionOcupadaError(self.equipo_activo or "otro equipo")
            ahora = datetime.now()
            self.equipo_activo = nombre
            self.token = str(uuid4())
            self.inicio_sesion = ahora
            self.ultimo_comando = ahora
            self.historial_sesion = []
            self.total_grupos += 1
            return {"token": self.token, "equipo": nombre}

    def validar_token(self, token: str | None) -> bool:
        with self._lock:
            self.verificar_timeout()
            return bool(token and self.token and token == self.token)

    def registrar_actividad(self) -> None:
        with self._lock:
            if self.token:
                self.ultimo_comando = datetime.now()

    def finalizar_sesion(self, token: str) -> bool:
        with self._lock:
            if not self.validar_token(token):
                return False
            self._liberar()
            return True

    def finalizar_forzada(self) -> None:
        with self._lock:
            self._liberar()

    def hay_sesion_activa(self) -> bool:
        with self._lock:
            self.verificar_timeout()
            return self.token is not None

    def estado_sesion(self) -> dict:
        with self._lock:
            self.verificar_timeout()
            activa = self.token is not None
            transcurridos = (
                (datetime.now() - self.inicio_sesion).total_seconds() / 60
                if activa and self.inicio_sesion
                else 0
            )
            restante = (
                max(0, (self.timeout.total_seconds() - (datetime.now() - self.ultimo_comando).total_seconds()) / 60)
                if activa and self.ultimo_comando
                else 0
            )
            return {
                "sesion_activa": activa,
                "equipo_activo": self.equipo_activo,
                "tiempo_transcurrido_min": round(transcurridos, 1),
                "tiempo_restante_min": max(0, int(restante + 0.999)),
            }
