"""Lista blanca de acciones, tomada del nucleo del simulador.

Es el MISMO archivo que usa el laboratorio fisico: si divergieran, la app del
alumno podria pedir el dia de la visita algo que en el simulador no existia.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ENTORNO = Path(__file__).resolve().parent.parent.parent
if str(_ENTORNO) not in sys.path:
    sys.path.insert(0, str(_ENTORNO))

from sim.acciones import (  # noqa: E402,F401
    AccionProhibida,
    MOVIMIENTO,
    PERMITIDAS,
    PROHIBIDAS,
    acciones_de,
    esta_permitida,
    exigir_permitida,
)
