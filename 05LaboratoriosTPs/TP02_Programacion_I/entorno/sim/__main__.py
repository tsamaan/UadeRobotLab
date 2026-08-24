"""Arranque del simulador oficial de Unitree para los laboratorios UADE.

    python -m sim --robot g1 --materia tp01

Hace todo: verifica el entorno, levanta el simulador oficial con el bridge DDS,
agrega el servicio de locomocion y abre la ventana.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import threading
import time

from .mundo import Mundo
from .robots import ROBOTS, obtener
from .safety import PERFILES, perfil
from .verificar import buscar_repo_oficial, informar, verificar

ARCHIVO_ACTIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              ".simulador_activo.json")
ARCHIVO_POSE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            ".pose_actual.json")


def _publicar_activo(robot, p, domain, interfaz):
    with open(ARCHIVO_ACTIVO, "w", encoding="utf-8") as f:
        json.dump({"robot": robot.clave, "materia": p.nombre.split("-")[0],
                   "domain": domain, "interfaz": interfaz,
                   "pose_archivo": ARCHIVO_POSE}, f)


def _limpiar():
    for f in (ARCHIVO_ACTIVO, ARCHIVO_POSE):
        try:
            os.remove(f)
        except OSError:
            pass


def _publicar_pose(mundo, detener):
    """El programa del alumno lee la pose de aca.

    Va por archivo y no por DDS porque el simulador oficial publica la pose del
    Go2 en rt/sportmodestate, pero la del G1 no: el G1 usa mensajes unitree_hg,
    que no traen ese topico. Un archivo funciona igual para los dos.
    """
    while not detener.is_set():
        try:
            with open(ARCHIVO_POSE, "w", encoding="utf-8") as f:
                json.dump(mundo.leer(), f)
        except OSError:
            pass
        time.sleep(0.1)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="sim", description="Simulador oficial Unitree - Laboratorios UADE")
    ap.add_argument("--robot", default="g1", choices=sorted(ROBOTS))
    ap.add_argument("--materia", default="tp01", choices=sorted(PERFILES))
    ap.add_argument("--domain", type=int, default=0)
    ap.add_argument("--interfaz", default="lo")
    ap.add_argument("--sin-ventana", action="store_true")
    ap.add_argument("--silencioso", action="store_true")
    ap.add_argument("--solo-revisar", action="store_true",
                    help="revisa el entorno y sale")
    args = ap.parse_args(argv)

    # 1. Verificar el entorno ANTES de prometer nada.
    r = verificar(instalar=not args.solo_revisar)
    if not informar(r):
        return 1
    if args.solo_revisar:
        return 0

    robot = obtener(args.robot)
    p = perfil(args.materia)
    mundo = Mundo(p)

    from .arrancar import SimuladorOficial

    try:
        sim = SimuladorOficial(mundo, robot, r.repo, args.domain, args.interfaz,
                               verboso=not args.silencioso)
    except FileNotFoundError as exc:
        print(f"\n  ERROR: {exc}\n", file=sys.stderr)
        return 1

    _publicar_activo(robot, p, args.domain, args.interfaz)
    detener = threading.Event()
    threading.Thread(target=_publicar_pose, args=(mundo, detener),
                     daemon=True).start()

    print("=" * 62)
    print("  SIMULADOR OFICIAL UNITREE - Laboratorios UADE")
    print("=" * 62)
    print(f"  Robot     : {robot.nombre} ({robot.tipo})")
    print(f"  Escena    : {robot.escena}")
    print(f"  Materia   : {p.nombre}")
    print(f"  Limites   : {p.velocidad_max} m/s | {p.velocidad_angular_max} rad/s"
          f" | {p.duracion_max} s por orden")
    print(f"  DDS       : dominio {args.domain}, interfaz {args.interfaz}")
    print("=" * 62)
    print()
    print("  Deja esta ventana abierta y ejecuta tu programa aparte.")
    print("  Para cerrar: Ctrl+C")
    print()

    # Ctrl+C tiene que cerrar SIEMPRE. Con la ventana abierta el hilo principal
    # queda bloqueado adentro del visor de MuJoCo y Python no llega a procesar
    # el KeyboardInterrupt: el simulador se quedaria vivo ocupando el puerto.
    def _cerrar(signum, frame):
        detener.set()
        _limpiar()
        print("\n[SIM] Simulador cerrado.")
        sys.stdout.flush()
        os._exit(0)

    signal.signal(signal.SIGINT, _cerrar)
    signal.signal(signal.SIGTERM, _cerrar)

    from .visor import mujoco_disponible

    hay_ventana, motivo = mujoco_disponible()
    try:
        if args.sin_ventana or not hay_ventana:
            if not args.sin_ventana:
                print("*" * 62)
                print("  ATENCION: NO SE VA A ABRIR LA VENTANA 3D")
                print(f"  Motivo: {motivo.splitlines()[0]}")
                print("  EL SIMULADOR FUNCIONA IGUAL, en modo consola.")
                print("*" * 62)
                print()
            sim.correr_sin_ventana()
        else:
            sim.correr_con_ventana()
    except KeyboardInterrupt:
        pass
    finally:
        detener.set()
        _limpiar()
        print("\n[SIM] Simulador cerrado.")
        sys.stdout.flush()

    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
