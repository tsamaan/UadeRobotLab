"""Que le puede pedir una app al robot. LISTA BLANCA, no lista negra.

Congelado 2026-08-25 por decision explicita del operador.

    EL ROBOT SE PRENDE Y SE PARA DESDE EL CONTROL OFICIAL, Y LO HACE EL
    OPERADOR. Ningun endpoint puede apagarlo, sentarlo, desenergizarlo ni
    ponerlo en una postura de riesgo.

Los alumnos controlan el robot desde una app, sin verlo necesariamente, y a
veces desde otra habitacion. Por eso la lista es BLANCA: lo que no esta
explicitamente permitido, se rechaza. Si manana el SDK agrega un metodo nuevo
-- y el de Unitree agrega bastante -- queda bloqueado por defecto en vez de
aparecer disponible sin que nadie lo decida.

Lo permitido es lo minimo util: moverse y gestos que no cambian la postura.
"""

from __future__ import annotations

# Gestos permitidos, por robot. nombre publico -> (metodo del bridge, descripcion)
PERMITIDAS: dict[str, dict[str, tuple[str, str]]] = {
    "g1": {
        "saludo": ("saludar", "Saluda con la mano"),
        "dar_la_mano": ("dar_la_mano", "Extiende la mano para saludar"),
    },
    "go2": {
        "saludo": ("saludar", "Saluda"),
    },
}

# Movimiento: lo unico que mueve la base.
MOVIMIENTO = ("mover", "detenerse")

# Consultas, sin efecto sobre el robot.
CONSULTAS = ("verificar_estado",)


# ---------------------------------------------------------------------------
# Lo prohibido, con el motivo. No se usa para decidir -- para eso esta la lista
# blanca -- pero documenta el porque y lo verifica un test.
# ---------------------------------------------------------------------------
PROHIBIDAS: dict[str, str] = {
    # Desenergizan: el G1 se desploma.
    "Damp": "desenergiza los motores; el G1 se desploma",
    "ZeroTorque": "desenergiza los motores; el G1 se desploma",
    # Cambian la postura sin nadie mirando el robot.
    "Sit": "sienta al robot; solo con un humano al lado",
    "StandDown": "baja al robot; solo con un humano al lado",
    "StandUp": "levantar el robot lo hace el operador con el control oficial",
    "RiseSit": "cambia la postura",
    "Squat2StandUp": "cambia la postura",
    "StandUp2Squat": "cambia la postura",
    "Lie2StandUp": "levanta al robot desde el piso",
    "RecoveryStand": "recuperacion tras una caida; la hace el operador",
    "LowStand": "cambia la altura de la postura",
    "HighStand": "cambia la altura de la postura",
    "SetStandHeight": "cambia la altura de la postura",
    # Acrobacias: rompen el robot o lastiman a alguien.
    "BackFlip": "acrobacia; puede destruir el robot o lastimar a alguien",
    "FrontFlip": "acrobacia; puede destruir el robot o lastimar a alguien",
    "LeftFlip": "acrobacia; puede destruir el robot o lastimar a alguien",
    "HandStand": "acrobacia; el robot queda invertido y se cae",
    "FrontJump": "salto; impacto y perdida de equilibrio",
    "FrontPounce": "salto hacia adelante; puede embestir a una persona",
    "Dance1": "rutina de baile; movimientos bruscos e impredecibles",
    "Dance2": "rutina de baile; movimientos bruscos e impredecibles",
    "Scrape": "rutina acrobatica",
    "Heart": "rutina que cambia la postura",
    "Stretch": "cambia la postura",
    "Pose": "cambia la postura",
    "WalkUpright": "camina en dos patas; el Go2 pierde estabilidad",
    "CrossStep": "marcha inestable",
    "FreeJump": "salto",
    "FreeBound": "salto",
    "FreeAvoid": "movimiento autonomo, sin control del operador",
    "TrotRun": "carrera; velocidad fuera de lo permitido en un aula",
    # Controles del sistema.
    "SwitchJoystick": "puede quitarle el mando al control remoto del operador",
    "SwitchToUserCtrl": "cambia el modo de control",
    "SwitchToInternalCtrl": "cambia el modo de control",
    "SetFsmId": "cambia el estado interno del robot",
    "AutoRecoverySet": "cambia el comportamiento ante caidas",
}


class AccionProhibida(PermissionError):
    """Se pidio algo que no esta en la lista blanca."""


def acciones_de(robot: str) -> dict[str, tuple[str, str]]:
    return PERMITIDAS.get(robot.lower(), {})


def esta_permitida(nombre: str, robot: str) -> bool:
    return nombre.lower() in acciones_de(robot)


def exigir_permitida(nombre: str, robot: str) -> tuple[str, str]:
    """Devuelve (metodo, descripcion) o levanta AccionProhibida."""
    accion = acciones_de(robot).get(nombre.lower())
    if accion is None:
        motivo = PROHIBIDAS.get(nombre) or PROHIBIDAS.get(nombre.capitalize())
        detalle = f": {motivo}" if motivo else ""
        raise AccionProhibida(
            f"'{nombre}' no esta permitida para el {robot.upper()}{detalle}. "
            f"Permitidas: {', '.join(sorted(acciones_de(robot))) or 'ninguna'}.")
    return accion
