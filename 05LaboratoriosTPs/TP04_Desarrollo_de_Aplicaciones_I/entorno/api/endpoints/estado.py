from fastapi import APIRouter, Request

from config import ROBOTS
from endpoints.dependencies import obtener_servicios

router = APIRouter(tags=["Estado"])


@router.get("/estado")
async def estado(request: Request) -> dict:
    services = obtener_servicios(request)
    estado_robot = await services.ejecutar_bridge("verificar_estado")
    sesion = services.sesiones.estado_sesion()
    robot = ROBOTS[services.tipo_robot]
    return {
        "conectado": estado_robot.get("conectado", False),
        "bateria": estado_robot.get("bateria"),
        "tipo_robot": services.tipo_robot,
        "nombre_robot": robot["nombre"],
        "sesion_activa": sesion["sesion_activa"],
        "equipo_activo": sesion["equipo_activo"],
    }
