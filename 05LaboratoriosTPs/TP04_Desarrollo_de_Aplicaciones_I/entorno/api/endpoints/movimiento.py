"""El endpoint /mover del TP04, en sus dos formas.

Este archivo es COMPARTIDO: el mismo corre en el laboratorio fisico contra el
robot y dentro del paquete del simulador que recibe cada profesor. Si divergen,
la app del alumno se comporta distinto el dia de la visita.

Hay dos maneras de pedir un movimiento y las dos son validas:

  1. JOYSTICK      {"vx": 0.2, "vy": 0, "vyaw": 0}
     Sin duracion. Vale ~0.4 s y despues el robot frena solo, asi que la app
     tiene que repetirlo cada ~200 ms mientras el dedo este apretado. Es lo que
     hace que soltar el dedo, cerrar la app o perder el WiFi frenen al robot.

  2. VELOCIDAD Y TIEMPO   {"velocidad": 0.2, "tiempo": 2.0}
     La primitiva de los otros seis TPs. El pedido BLOQUEA hasta terminar y el
     robot frena al final. Distancia = velocidad x tiempo.

Se aceptan las dos a proposito: el joystick es lo que necesita una app de
control en vivo, y velocidad-y-tiempo es como piensan el resto de los labs y el
`LocoClient` del SDK. Lo que NO se acepta es mezclarlas en un mismo pedido:
seria ambiguo cual manda.
"""

import math

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, root_validator, validator

from endpoints.dependencies import obtener_servicios, requerir_token
from utils.safety import clamp_velocidad

router = APIRouter(tags=["Movimiento"])

_JOYSTICK = ("vx", "vy", "vyaw")
_TEMPORIZADO = ("velocidad", "velocidad_angular", "tiempo")


class Movimiento(BaseModel):
    # Forma 1: joystick. Sin duracion.
    vx: float | None = None
    vy: float | None = None
    vyaw: float | None = None
    # Forma 2: velocidad y tiempo, como el resto de los TPs.
    velocidad: float | None = None
    velocidad_angular: float | None = None
    tiempo: float | None = None

    class Config:
        # Un campo que no reconocemos es un ERROR, no algo para ignorar.
        #
        # Sin esto los campos quedaban en su default 0.0 y la respuesta era
        # {"ok": true, "vx": 0.0, ...}: la app recibia exito y el robot no se
        # movia, sin una sola pista de por que.
        extra = "forbid"

    @validator("vx", "vy", "vyaw", "velocidad", "velocidad_angular", "tiempo")
    def numero_finito(cls, valor):
        if valor is not None and not math.isfinite(valor):
            raise ValueError("El valor debe ser un numero finito")
        return valor

    @validator("tiempo")
    def tiempo_positivo(cls, valor):
        if valor is not None and valor <= 0:
            raise ValueError("'tiempo' tiene que ser mayor que cero")
        return valor

    @root_validator(skip_on_failure=True)
    def una_sola_forma(cls, valores):
        usa_joystick = any(valores.get(c) is not None for c in _JOYSTICK)
        usa_tiempo = any(valores.get(c) is not None for c in _TEMPORIZADO)

        if usa_joystick and usa_tiempo:
            raise ValueError(
                "No se pueden mezclar las dos formas en un mismo pedido. "
                "O mandas {vx, vy, vyaw} (joystick, sin duracion), "
                "o mandas {velocidad, tiempo} (velocidad y tiempo).")

        # El olvido mas probable: mandar velocidad sin decir por cuanto tiempo.
        # Es justo lo que la regla de los labs quiere que el alumno piense.
        if usa_tiempo and valores.get("tiempo") is None:
            raise ValueError(
                "Falta 'tiempo'. La distancia se deriva: velocidad x tiempo. "
                "Ejemplo: {\"velocidad\": 0.2, \"tiempo\": 2.0} avanza 0.4 m.")

        if valores.get("tiempo") is not None and not usa_joystick:
            if (valores.get("velocidad") is None
                    and valores.get("velocidad_angular") is None):
                raise ValueError(
                    "Mandaste 'tiempo' pero ninguna velocidad. Agrega "
                    "'velocidad' (m/s) o 'velocidad_angular' (rad/s).")
        return valores

    @property
    def es_temporizado(self) -> bool:
        return self.tiempo is not None

    def velocidades(self) -> tuple[float, float, float]:
        """Las tres velocidades del SDK, venga por la forma que venga."""
        if self.es_temporizado:
            return (self.velocidad or 0.0, 0.0, self.velocidad_angular or 0.0)
        return (self.vx or 0.0, self.vy or 0.0, self.vyaw or 0.0)


@router.post("/mover")
async def mover(
    comando: Movimiento,
    request: Request,
    _: str = Depends(requerir_token),
) -> dict:
    services = obtener_servicios(request)
    pedido_vx, pedido_vy, pedido_vyaw = comando.velocidades()
    vx, vy, vyaw = clamp_velocidad(pedido_vx, pedido_vy, pedido_vyaw)

    # Recortamos, no rechazamos: un joystick que devuelve error en cada empujon
    # seria inusable. Pero el recorte VIAJA EN LA RESPUESTA, para que la app
    # pueda mostrarlo. Antes solo se avisaba por la consola del servidor, que
    # el alumno no ve nunca.
    recortado = (vx, vy, vyaw) != (pedido_vx, pedido_vy, pedido_vyaw)

    params = {"vx": vx, "vy": vy, "vyaw": vyaw}
    if comando.es_temporizado:
        params["tiempo"] = comando.tiempo
        ok = await services.ejecutar_bridge(
            "mover_durante", vx, vy, vyaw, comando.tiempo)
    else:
        ok = await services.ejecutar_bridge("mover", vx, vy, vyaw)

    equipo = services.sesiones.equipo_activo or "desconocido"
    services.logger.registrar(equipo, "/mover", params, "ok" if ok else "error")
    if not ok:
        raise HTTPException(status_code=503,
                            detail="El robot no pudo ejecutar el movimiento.")

    if comando.es_temporizado:
        # mover_durante ya frena al terminar.
        services.robot_en_movimiento = False
    else:
        services.marcar_movimiento()

    respuesta = {"ok": True, **params}
    if recortado:
        respuesta["recortado"] = True
        respuesta["pedido"] = {"vx": pedido_vx, "vy": pedido_vy,
                               "vyaw": pedido_vyaw}
        respuesta["mensaje"] = (
            "Se recorto al maximo permitido para esta materia. "
            "El robot se movio, pero mas lento de lo que pediste.")
    return respuesta
