from __future__ import annotations

from fastapi import Header, HTTPException, Request


def obtener_servicios(request: Request):
    return request.app.state.services


def requerir_token(
    request: Request,
    x_robot_token: str | None = Header(default=None, alias="X-Robot-Token"),
) -> str:
    services = obtener_servicios(request)
    if not services.sesiones.validar_token(x_robot_token):
        raise HTTPException(status_code=401, detail="Token faltante, invalido o expirado.")
    services.sesiones.registrar_actividad()
    return x_robot_token  # type: ignore[return-value]
