"""Modelo de seguridad unico para simulador y laboratorios.

Congelado en la Fase 0 del plan (ver ~/Escritorio/CONTRATO_API.md).

Separa DOS cosas que antes estaban mezcladas en un mismo validar_velocidad():

1. TECHO FISICO: que es seguro para el robot en un aula con alumnos alrededor.
   Un solo numero, innegociable, igual en todos lados. No lo toca ninguna
   materia.

2. PERFIL PEDAGOGICO: el parametro del ejercicio. TP02 ensena validacion y
   necesita un limite contra el cual validar; ese numero es didactico, no una
   afirmacion de que sea seguro. Siempre <= TECHO.

La garantia central: **el simulador nunca puede ser mas permisivo que el
robot**, porque los dos importan este mismo archivo.

RECHAZA, no recorta. Un recorte silencioso hace que el alumno calibre a ciegas:
pide 0.5 m/s, el simulador le da 0.25, el robot real le da 0.5, y la distancia
recorrida se duplica. Ver el bug del dt fijo en sim/README.md, misma familia.
"""

from __future__ import annotations

from dataclasses import dataclass

# Tolerancia para comparaciones de punto flotante. Sin esto, un alumno que pide
# exactamente el limite de su materia puede ser rechazado porque 0.2 no es
# representable en binario. Con RECHAZO en vez de recorte, esto deja de ser
# cosmetico y pasa a ser un falso rechazo.
EPSILON = 1e-9


class ErrorDeSeguridad(ValueError):
    """Un valor pedido excede lo permitido. NUNCA se recorta: se rechaza.

    Quien la captura tiene la obligacion de dejar el robot detenido antes de
    propagarla. Ver CONTRATO_API.md, seccion "Rechazar implica frenar".
    """


@dataclass(frozen=True)
class PerfilSeguridad:
    """Limites aplicables. El techo es un perfil mas; los demas van por debajo."""

    nombre: str
    velocidad_max: float      # m/s
    velocidad_angular_max: float  # rad/s
    duracion_max: float       # s, por comando individual
    bateria_min: int          # %

    def _excede(self, campo: str, otro: "PerfilSeguridad") -> bool:
        """True si este perfil es mas permisivo que 'otro' en ese campo."""
        if campo == "bateria_min":
            # Mas bajo = mas permisivo.
            return getattr(self, campo) < getattr(otro, campo) - EPSILON
        return getattr(self, campo) > getattr(otro, campo) + EPSILON


# ---------------------------------------------------------------------------
# 1. EL TECHO FISICO. No lo modifica ninguna materia.
# ---------------------------------------------------------------------------
# velocidad_max         0.25  el valor mas conservador que ya existia (TP03) y
#                             el que el gemelo viene aplicando.
# velocidad_angular_max 1.0   unico tope angular que existia (TP01) y el del
#                             gemelo. TP03 no tenia ninguno.
# duracion_max          10.0  un comando de 10 s a 0.25 m/s recorre 2.5 m. Es
#                             el maximo absoluto por comando; las materias
#                             declaran menos.
# bateria_min           25    el mas conservador que existia (TP07).
TECHO = PerfilSeguridad(
    nombre="techo-fisico",
    velocidad_max=0.25,
    velocidad_angular_max=1.0,
    duracion_max=10.0,
    bateria_min=25,
)


# ---------------------------------------------------------------------------
# 2. PERFILES PEDAGOGICOS POR MATERIA. Todos <= TECHO (se verifica al importar).
# ---------------------------------------------------------------------------
PERFILES: dict[str, PerfilSeguridad] = {
    # Fundamentos de Informatica. Programacion secuencial, primer contacto:
    # el mas lento de todos a proposito.
    "tp01": PerfilSeguridad("tp01-fundamentos", 0.20, 0.50, 5.0, 25),
    # Programacion I. Ensena validacion; su limite baja de 0.5 a 0.20 para
    # quedar bajo el techo. El ejercicio no cambia, cambia el numero.
    "tp02": PerfilSeguridad("tp02-programacion-i", 0.20, 0.50, 10.0, 25),
    # Programacion III. Navegacion en grilla; usa VELOCIDAD_NAVEGACION = 0.25,
    # que es exactamente el techo. Por eso EPSILON no es opcional aca.
    "tp03": PerfilSeguridad("tp03-programacion-iii", 0.25, 1.00, 10.0, 25),
    # Desarrollo de Aplicaciones I. App movil con joystick: movimientos cortos
    # y repetidos, no rafagas largas.
    "tp04": PerfilSeguridad("tp04-desarrollo-i", 0.20, 0.50, 2.0, 25),
    # Desarrollo de Aplicaciones II. El alumno hace un dashboard y NO mueve el
    # robot: eso lo garantiza la API, que no tiene endpoints de movimiento.
    #
    # Pero el ROBOT si se mueve: el simulador lo hace pasear solo para que el
    # dashboard tenga datos que graficar. Con velocidad 0 -- como estaba hasta
    # el 2026-08-25 -- el robot quedaba clavado y todos los graficos eran
    # lineas rectas, que es justo lo que hace inutil al TP.
    "tp05": PerfilSeguridad("tp05-desarrollo-ii", 0.20, 0.50, 5.0, 25),
    # Paradigma Orientado a Objetos. Java, sin robot por defecto.
    "tp06": PerfilSeguridad("tp06-poo", 0.20, 0.50, 5.0, 25),
    # Inteligencia Artificial. El agente traduce lenguaje natural: conviene
    # margen chico porque el alumno no escribe el numero a mano.
    "tp07": PerfilSeguridad("tp07-inteligencia-artificial", 0.20, 0.50, 5.0, 25),
}


def _verificar_perfiles() -> None:
    """Ningun perfil puede superar el techo. Falla al importar, no en el aula.

    Este es el mecanismo que hace cumplir la Opcion C. Si alguien sube un numero
    de una materia por encima del techo, el import explota en el arranque del
    simulador o del laboratorio, no cuando el robot ya se esta moviendo.
    """
    campos = ("velocidad_max", "velocidad_angular_max", "duracion_max", "bateria_min")
    for clave, perfil in PERFILES.items():
        for campo in campos:
            if perfil._excede(campo, TECHO):
                raise ErrorDeSeguridad(
                    f"El perfil '{clave}' declara {campo}={getattr(perfil, campo)}, "
                    f"que supera el techo fisico ({getattr(TECHO, campo)}). "
                    f"Ninguna materia puede ir por encima del techo."
                )


_verificar_perfiles()


def perfil(materia: str) -> PerfilSeguridad:
    """Devuelve el perfil de una materia ('tp01'...'tp07')."""
    clave = materia.lower().strip()
    if clave not in PERFILES:
        raise ErrorDeSeguridad(
            f"Materia desconocida: '{materia}'. "
            f"Validas: {', '.join(sorted(PERFILES))}."
        )
    return PERFILES[clave]


# ---------------------------------------------------------------------------
# 3. VALIDADORES. Rechazan con ErrorDeSeguridad; nunca recortan.
# ---------------------------------------------------------------------------
def _numero(valor: object, nombre: str) -> float:
    try:
        numero = float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise ErrorDeSeguridad(
            f"{nombre} tiene que ser un numero, no {type(valor).__name__}."
        ) from None
    if numero != numero or numero in (float("inf"), float("-inf")):
        raise ErrorDeSeguridad(f"{nombre} no puede ser NaN ni infinito.")
    return numero


def validar_velocidad(velocidad: object, p: PerfilSeguridad) -> float:
    v = _numero(velocidad, "La velocidad")
    if abs(v) > p.velocidad_max + EPSILON:
        raise ErrorDeSeguridad(
            f"Velocidad {v:.3f} m/s: el maximo de {p.nombre} es "
            f"{p.velocidad_max:.2f} m/s. Baja la velocidad y volve a probar."
        )
    return v


def validar_velocidad_angular(velocidad: object, p: PerfilSeguridad) -> float:
    v = _numero(velocidad, "La velocidad de giro")
    if abs(v) > p.velocidad_angular_max + EPSILON:
        raise ErrorDeSeguridad(
            f"Velocidad de giro {v:.3f} rad/s: el maximo de {p.nombre} es "
            f"{p.velocidad_angular_max:.2f} rad/s."
        )
    return v


def validar_duracion(duracion: object, p: PerfilSeguridad) -> float:
    t = _numero(duracion, "El tiempo")
    if t < 0.0:
        raise ErrorDeSeguridad(f"El tiempo no puede ser negativo (pediste {t:.2f} s).")
    if t > p.duracion_max + EPSILON:
        raise ErrorDeSeguridad(
            f"Tiempo {t:.2f} s: el maximo por comando en {p.nombre} es "
            f"{p.duracion_max:.1f} s. Parti el movimiento en varios pasos."
        )
    return t


def validar_bateria(nivel: object, p: PerfilSeguridad) -> int:
    """Fail-closed: bateria desconocida (None) NO es bateria segura."""
    if nivel is None:
        raise ErrorDeSeguridad(
            "Bateria desconocida. Telemetria desconocida no es telemetria "
            "segura: el movimiento queda bloqueado."
        )
    n = int(_numero(nivel, "La bateria"))
    if n < p.bateria_min:
        raise ErrorDeSeguridad(
            f"Bateria {n}%: el minimo de {p.nombre} es {p.bateria_min}%. "
            f"Carga el robot antes de continuar."
        )
    return n
