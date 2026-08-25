"""Levanta el backend del TP04 apuntando al simulador.

Lo llama INICIAR_TP04. No hace falta ejecutarlo a mano.
"""

from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
for sub in (BASE, BASE / "api"):
    if str(sub) not in sys.path:
        sys.path.insert(0, str(sub))


def ip_de_la_maquina() -> str:
    """La IP que el celular tiene que usar. No sirve 127.0.0.1 desde el telefono."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))   # no manda nada, solo elige la ruta
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Backend TP04 contra el simulador")
    ap.add_argument("--robot", default="g1", choices=("g1", "go2"))
    ap.add_argument("--puerto", type=int, default=8000)
    ap.add_argument("--mock", action="store_true",
                    help="sin simulador, para probar la API sola")
    args = ap.parse_args(argv)

    import uvicorn
    from api.api_server import app, configurar_runtime
    from unitree_bridge import MockBridge, RobotBridge

    bridge = MockBridge(args.robot) if args.mock else RobotBridge(args.robot)
    if not bridge.conectar():
        print("\n  No pude conectar con el simulador.")
        print("  Fijate que la ventana del simulador siga abierta.\n")
        return 1
    configurar_runtime(bridge, args.robot)

    ip = ip_de_la_maquina()
    print()
    print("=" * 64)
    print("  BACKEND TP04 LISTO")
    print("=" * 64)
    print(f"  Robot     : {args.robot}" + ("  (modo mock)" if args.mock else ""))
    print()
    print("  DESDE TU CELULAR, la app tiene que apuntar a:")
    print()
    print(f"        http://{ip}:{args.puerto}")
    print()
    print("  El celular y esta computadora tienen que estar en la MISMA red.")
    print(f"  Desde esta misma maquina (emulador) tambien sirve:")
    print(f"        http://localhost:{args.puerto}")
    print()
    print(f"  Documentacion de los endpoints: http://{ip}:{args.puerto}/docs")
    print("=" * 64)
    print()

    uvicorn.run(app, host="0.0.0.0", port=args.puerto, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
