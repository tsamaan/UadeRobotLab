"""Aplicacion FastAPI del laboratorio TP04."""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator

from config import API_CORS_ORIGINS, COMANDO_TIMEOUT_MS, ROBOTS, SESION_TIMEOUT_MINUTOS
from endpoints import acciones, control, estado, movimiento
from endpoints.dependencies import obtener_servicios, requerir_token
from logger import CommandLogger
from sesion_manager import SesionManager, SesionOcupadaError
from unitree_bridge import MockBridge


@dataclass
class RuntimeServices:
    bridge: Any
    tipo_robot: str
    sesiones: SesionManager = field(default_factory=SesionManager)
    logger: CommandLogger = field(default_factory=CommandLogger)
    robot_en_movimiento: bool = False
    ultimo_movimiento: float | None = None
    bridge_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def ejecutar_bridge(self, metodo: str, *args: Any) -> Any:
        async with self.bridge_lock:
            return await asyncio.to_thread(getattr(self.bridge, metodo), *args)

    def marcar_movimiento(self) -> None:
        self.ultimo_movimiento = time.monotonic()
        self.robot_en_movimiento = True


_bridge_inicial = MockBridge("go2")
services = RuntimeServices(_bridge_inicial, "go2")


def configurar_runtime(bridge: Any, tipo_robot: str) -> RuntimeServices:
    """Inyecta el unico bridge creado por iniciar_lab.py."""
    global services
    services = RuntimeServices(bridge=bridge, tipo_robot=tipo_robot)
    app.state.services = services
    return services


async def watchdog_movimiento(app_: FastAPI) -> None:
    intervalo = min(0.1, COMANDO_TIMEOUT_MS / 2000)
    while True:
        await asyncio.sleep(intervalo)
        runtime: RuntimeServices = app_.state.services
        sesion_vencida = runtime.sesiones.verificar_timeout()
        vencio_joystick = bool(
            runtime.ultimo_movimiento is not None
            and (time.monotonic() - runtime.ultimo_movimiento) * 1000 >= COMANDO_TIMEOUT_MS
        )
        if runtime.robot_en_movimiento and (vencio_joystick or sesion_vencida):
            ok = await runtime.ejecutar_bridge("detenerse")
            runtime.robot_en_movimiento = False
            runtime.logger.registrar(
                "SISTEMA",
                "/watchdog",
                {},
                "ok" if ok else "error",
                "Timeout de joystick" if vencio_joystick else "Sesion expirada",
            )


@asynccontextmanager
async def lifespan(app_: FastAPI):
    tarea = asyncio.create_task(watchdog_movimiento(app_))
    try:
        yield
    finally:
        tarea.cancel()
        try:
            await tarea
        except asyncio.CancelledError:
            pass
        runtime: RuntimeServices = app_.state.services
        if runtime.robot_en_movimiento:
            await runtime.ejecutar_bridge("detenerse")
        runtime.sesiones.finalizar_forzada()
        await asyncio.to_thread(runtime.bridge.desconectar)


app = FastAPI(
    title="API Robot Unitree - Lab TP04",
    description="API REST para controlar Unitree Go2/G1 desde una app React Native",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.services = services
app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(estado.router)
app.include_router(movimiento.router)
app.include_router(control.router)
app.include_router(acciones.router)


class NuevaSesion(BaseModel):
    equipo: str

    @validator("equipo")
    def equipo_valido(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El equipo no puede estar vacio")
        if len(valor) > 80:
            raise ValueError("El equipo no puede superar 80 caracteres")
        return valor


@app.get("/", include_in_schema=False)
async def raiz() -> dict:
    return {"ok": True, "nombre": app.title, "docs": "/docs"}


@app.post("/sesion/iniciar", tags=["Sesion"])
async def iniciar_sesion(datos: NuevaSesion, request: Request) -> dict:
    runtime = obtener_servicios(request)
    try:
        resultado = runtime.sesiones.iniciar_sesion(datos.equipo)
    except SesionOcupadaError:
        estado_sesion = runtime.sesiones.estado_sesion()
        raise HTTPException(
            status_code=409,
            detail={
                "ok": False,
                "mensaje": f"Robot ocupado por '{estado_sesion['equipo_activo']}'.",
                "equipo_activo": estado_sesion["equipo_activo"],
                "tiempo_restante_min": estado_sesion["tiempo_restante_min"],
            },
        )
    runtime.logger.limpiar()
    runtime.logger.registrar(resultado["equipo"], "/sesion/iniciar", {}, "ok")
    return {
        "ok": True,
        **resultado,
        "mensaje": "Sesion iniciada. Usar este token en el header X-Robot-Token para todos los comandos.",
        "timeout_minutos": SESION_TIMEOUT_MINUTOS,
    }


@app.post("/sesion/finalizar", tags=["Sesion"])
async def finalizar_sesion(
    request: Request,
    token: str = Depends(requerir_token),
) -> dict:
    runtime = obtener_servicios(request)
    equipo = runtime.sesiones.equipo_activo or "desconocido"
    # Frenar antes de invalidar el token evita dejar al robot caminando.
    ok_stop = await runtime.ejecutar_bridge("detenerse")
    runtime.robot_en_movimiento = False
    runtime.logger.registrar(equipo, "/sesion/finalizar", {}, "ok" if ok_stop else "error")
    runtime.sesiones.finalizar_sesion(token)
    return {"ok": True, "mensaje": "Sesion finalizada. Robot disponible."}


@app.get("/historial", tags=["Historial"])
async def historial(
    request: Request,
    ultimos: int = Query(default=50, ge=1, le=500),
) -> dict:
    runtime = obtener_servicios(request)
    return {
        "equipo": runtime.sesiones.equipo_activo,
        "comandos": runtime.logger.obtener_historial(ultimos=ultimos),
    }
