"""Levanta el backend de telemetria del TP05 leyendo del simulador.

Lo llama INICIAR_TP05. No hace falta ejecutarlo a mano.

Es EXACTAMENTE el mismo backend que corre en la notebook del laboratorio
contra el robot fisico. Lo unico que cambia es de donde lee: aca del
simulador por DDS local, alla del robot por RJ-45.
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
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Backend de telemetria TP05")
    ap.add_argument("--robot", default="go2", choices=("g1", "go2"))
    ap.add_argument("--puerto", type=int, default=8001)
    ap.add_argument("--demo", action="store_true",
                    help="datos inventados, sin simulador")
    args = ap.parse_args(argv)

    import uvicorn
    from api.telemetry_server import app, configurar
    from api.telemetry_reader import DemoReader, TelemetryReader

    if args.demo:
        lector, modo = DemoReader(args.robot), "demo"
    else:
        # 'lo' y dominio 0: la misma configuracion que usa el simulador.
        lector = TelemetryReader(args.robot, network_interface="lo")
        if not lector.esperar_primer_dato(timeout=8.0):
            print("\n  No llegan datos del simulador.")
            print("  Fijate que la ventana del simulador siga abierta.")
            print("  Para probar el backend sin simulador: --demo\n")
            return 1
        modo = "simulador"

    configurar(lector, args.robot, modo)
    ip = ip_de_la_maquina()

    print()
    print("=" * 66)
    print("  BACKEND DE TELEMETRIA TP05 LISTO")
    print("=" * 66)
    print(f"  Robot : {args.robot}   Modo: {modo}")
    print()
    print("  TU DASHBOARD tiene que pegarle a:")
    print()
    print(f"        http://{ip}:{args.puerto}")
    print()
    print("  Endpoints:")
    for e in ("/telemetria", "/motores", "/imu", "/bms", "/fuerzas", "/info"):
        print(f"        GET  {e}")
    print(f"        WS   ws://{ip}:{args.puerto}/ws     (tiempo real)")
    print()
    print(f"  Documentacion: http://{ip}:{args.puerto}/docs")
    print("=" * 66)
    print()

    uvicorn.run(app, host="0.0.0.0", port=args.puerto, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
