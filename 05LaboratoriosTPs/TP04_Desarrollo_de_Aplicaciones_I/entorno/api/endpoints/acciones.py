from fastapi import APIRouter, Depends, HTTPException, Request

from endpoints.dependencies import obtener_servicios, requerir_token
from utils.acciones import AccionProhibida, acciones_de, exigir_permitida

router = APIRouter(tags=["Acciones"])

# La lista de acciones ya NO vive aca: viene de la LISTA BLANCA compartida en
# unitree_lab_core/acciones.py.
#
# Antes este archivo habilitaba "sentarse", "pararse" y "estirar" desde la app.
# El robot se prende y se para desde el control oficial, y lo hace el operador:
# ningun endpoint puede cambiarle la postura a un robot que nadie esta mirando.
ACCIONES = {robot: acciones_de(robot) for robot in ("g1", "go2")}


@router.get("/acciones")
async def listar_acciones(request: Request) -> dict:
    services = obtener_servicios(request)
    return {
        "tipo_robot": services.tipo_robot,
        "acciones": [
            {"nombre": nombre, "descripcion": datos[1]}
            for nombre, datos in ACCIONES[services.tipo_robot].items()
        ],
    }


@router.post("/accion/{nombre}")
async def ejecutar_accion(
    nombre: str,
    request: Request,
    _: str = Depends(requerir_token),
) -> dict:
    services = obtener_servicios(request)
    equipo = services.sesiones.equipo_activo or "desconocido"
    try:
        accion = exigir_permitida(nombre, services.tipo_robot)
    except AccionProhibida as exc:
        services.logger.registrar(equipo, f"/accion/{nombre}", {}, "rechazado", str(exc))
        raise HTTPException(status_code=403, detail=str(exc))
    ok = await services.ejecutar_bridge(accion[0])
    services.logger.registrar(equipo, f"/accion/{nombre}", {}, "ok" if ok else "error")
    if not ok:
        raise HTTPException(status_code=503, detail=f"No se pudo ejecutar la accion '{nombre}'.")
    return {"ok": True, "accion": nombre, "mensaje": f"Accion '{nombre}' ejecutada correctamente."}
