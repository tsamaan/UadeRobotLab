import math

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, validator

from endpoints.dependencies import obtener_servicios, requerir_token
from utils.safety import clamp_velocidad

router = APIRouter(tags=["Movimiento"])


class Movimiento(BaseModel):
    vx: float = 0.0
    vy: float = 0.0
    vyaw: float = 0.0

    @validator("vx", "vy", "vyaw")
    def numero_finito(cls, valor: float) -> float:
        if not math.isfinite(valor):
            raise ValueError("La velocidad debe ser un numero finito")
        return valor


@router.post("/mover")
async def mover(
    comando: Movimiento,
    request: Request,
    _: str = Depends(requerir_token),
) -> dict:
    services = obtener_servicios(request)
    vx, vy, vyaw = clamp_velocidad(comando.vx, comando.vy, comando.vyaw)
    params = {"vx": vx, "vy": vy, "vyaw": vyaw}
    ok = await services.ejecutar_bridge("mover", vx, vy, vyaw)
    equipo = services.sesiones.equipo_activo or "desconocido"
    services.logger.registrar(equipo, "/mover", params, "ok" if ok else "error")
    if not ok:
        raise HTTPException(status_code=503, detail="El robot no pudo ejecutar el movimiento.")
    services.marcar_movimiento()
    return {"ok": True, **params}
