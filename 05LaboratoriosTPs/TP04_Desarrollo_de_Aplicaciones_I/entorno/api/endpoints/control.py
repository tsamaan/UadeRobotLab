from fastapi import APIRouter, Depends, HTTPException, Request

from endpoints.dependencies import obtener_servicios, requerir_token

router = APIRouter(tags=["Control"])


async def _control(nombre: str, metodo: str, request: Request) -> dict:
    services = obtener_servicios(request)
    equipo = services.sesiones.equipo_activo or "desconocido"
    ok = await services.ejecutar_bridge(metodo)
    services.logger.registrar(equipo, f"/{nombre}", {}, "ok" if ok else "error")
    if not ok:
        raise HTTPException(status_code=503, detail=f"No se pudo ejecutar '{nombre}'.")
    if nombre == "parar":
        services.robot_en_movimiento = False
    return {"ok": True, "mensaje": "Robot detenido."}


@router.post("/parar")
async def parar(request: Request, _: str = Depends(requerir_token)) -> dict:
    return await _control("parar", "detenerse", request)


# /pararse y /sentarse SE QUITARON el 2026-08-25.
#
# Levantar o sentar al robot cambia su postura, y eso solo se hace con alguien
# mirandolo. El robot se prende y se para desde el control oficial, y lo hace el
# operador. La app solo mueve y hace gestos.
