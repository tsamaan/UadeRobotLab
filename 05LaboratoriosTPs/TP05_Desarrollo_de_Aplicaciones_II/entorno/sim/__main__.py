"""Arranque del simulador oficial de Unitree para los laboratorios UADE.

    python -m sim --robot g1 --materia tp01

Hace todo: verifica el entorno, levanta el simulador oficial con el bridge DDS,
agrega el servicio de locomocion y abre la ventana.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
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


def _publicar_activo(robot, p, domain, interfaz, grilla=None, puerto=None):
    """Deja escrito como encontrar al simulador. Lo lee `robot.py` del alumno."""
    from .local import PUERTO

    # `transporte` es lo que lee `robot.py` para saber por donde hablar. Sin
    # este dato el cliente adivinaba, y con el simulador levantado en --dds
    # se quedaba golpeando un socket que nadie abrio.
    datos = {"robot": robot.clave, "materia": p.nombre.split("-")[0],
             "transporte": "dds" if puerto is False else "local",
             "domain": domain, "interfaz": interfaz,
             "pose_archivo": ARCHIVO_POSE, "grilla": grilla,
             "puerto": PUERTO if puerto in (None, False) else puerto}
    with open(ARCHIVO_ACTIVO, "w", encoding="utf-8") as f:
        json.dump(datos, f)


# ---------------------------------------------------------------------------
#  Un simulador por vez
# ---------------------------------------------------------------------------
#
# Los siete paquetes hablan por DDS en el MISMO dominio (0) y la MISMA interfaz
# (lo). Dos simuladores abiertos a la vez publican los dos en rt/lf/lowstate, y
# el programa del alumno -- o el backend del TP04/TP05 -- se queda con el que
# llegue, que puede ser el del otro robot.
#
# El sintoma es feisimo de diagnosticar: pediste el Go2 y el dashboard te
# muestra 29 motores del G1, sin un solo error en ningun lado. Paso al probar.
#
# La sena es global (va al temp del sistema, no a la carpeta del paquete)
# justamente porque el choque es ENTRE paquetes distintos.

ARCHIVO_SENA = os.path.join(tempfile.gettempdir(), "uade_simulador_activo.json")


def _sena_viva():
    """El otro simulador anotado en la sena, si sigue vivo. Si no, None."""
    try:
        with open(ARCHIVO_SENA, encoding="utf-8") as f:
            datos = json.load(f)
        pid = int(datos["pid"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if pid == os.getpid():
        return None
    try:
        # Senal 0: no hace nada, solo pregunta si el proceso existe.
        os.kill(pid, 0)
    except OSError:
        return None      # murio mal y dejo la sena colgada: no bloquea
    return datos


def _dejar_sena(robot, materia: str) -> None:
    try:
        with open(ARCHIVO_SENA, "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "robot": robot.clave,
                       "materia": materia}, f)
    except OSError:
        pass


def _borrar_sena() -> None:
    try:
        datos = json.load(open(ARCHIVO_SENA, encoding="utf-8"))
        if int(datos.get("pid", -1)) == os.getpid():
            os.remove(ARCHIVO_SENA)
    except (OSError, ValueError, TypeError):
        pass


def _limpiar():
    _borrar_sena()
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
    ap.add_argument("--grilla", help="mapa JSON de navegacion (TP03)")
    ap.add_argument("--sin-paseo", action="store_true",
                    help="TP05: deja el robot quieto en vez de pasearlo")
    ap.add_argument("--sin-ventana", action="store_true")
    ap.add_argument("--silencioso", action="store_true")
    ap.add_argument("--dds", action="store_true",
                    help="usa DDS y el SDK real en vez del socket local "
                         "(solo Linux; para el banco de pruebas)")
    ap.add_argument("--puerto", type=int, default=None,
                    help="puerto del socket local (por defecto 8765)")
    ap.add_argument("--igualmente", action="store_true",
                    help="abre aunque parezca haber otro simulador andando")
    ap.add_argument("--solo-revisar", action="store_true",
                    help="revisa el entorno y sale")
    args = ap.parse_args(argv)

    # 1. Verificar el entorno ANTES de prometer nada.
    #    El TP04 necesita el backend; los demas no.
    # TP04 y TP05 levantan un backend HTTP; los demas no necesitan nada de esto.
    extras = ()
    if args.materia in ("tp04", "tp05"):
        que = ("de la app" if args.materia == "tp04" else "del dashboard")
        extras = (("fastapi", f"el backend {que}"),
                  ("uvicorn", "el servidor del backend"))
    r = verificar(instalar=not args.solo_revisar, extras=extras,
                  dds=args.dds)
    if not informar(r):
        return 1
    if args.solo_revisar:
        return 0

    otro = None if args.igualmente else _sena_viva()
    if otro:
        print()
        print("  ==========================================================")
        print("  YA HAY UN SIMULADOR ABIERTO")
        print("  ==========================================================")
        print()
        print(f"    Robot   : {otro.get('robot', '?')}")
        print(f"    Materia : {otro.get('materia', '?')}")
        print(f"    Proceso : {otro.get('pid', '?')}")
        print()
        print("  Los dos escuchan en el mismo puerto, asi que el segundo no")
        print("  podria abrir, o peor: tu programa terminaria hablandole al")
        print("  OTRO robot sin ningun error que te avise.")
        print()
        print("  Cerra la ventana del simulador que ya tenes abierta y volve")
        print("  a intentar. Si estas seguro de que no hay ninguno, agrega")
        print("  --igualmente al final del comando.")
        print("  ==========================================================")
        print()
        return 1

    robot = obtener(args.robot)
    p = perfil(args.materia)
    mundo = Mundo(p)

    # TP03: si hay mapa, se dibuja la grilla y el robot arranca en la celda de
    # inicio mirando en la orientacion que indica el mapa.
    mapa = None
    if args.grilla:
        from .grilla import MapaInvalido, cargar
        try:
            mapa = cargar(args.grilla)
        except MapaInvalido as exc:
            print(f"\n  ERROR EN EL MAPA: {exc}\n", file=sys.stderr)
            return 1
        x0, y0 = mapa.a_mundo(*mapa.inicio)
        mundo.situar(x0, y0, mapa.rumbo_inicial())

        # El robot tiene que entrar en la celda. El Go2 mide 0.62 m de largo:
        # en una grilla de 0.50 m sobresale por las puntas e invade las celdas
        # vecinas. En el simulador se ve como si atravesara los obstaculos; en
        # el aula, los tocaria de verdad.
        from .robots import entra_en_celda
        entra, lado = entra_en_celda(robot.clave, mapa.tamano_celda)
        if not entra:
            sugerida = round(lado * 1.15 + 0.049, 1)
            print("*" * 62)
            print(f"  ATENCION: EL {robot.nombre.upper()} NO ENTRA EN LA CELDA")
            print("*" * 62)
            print(f"  El robot mide {lado:.2f} m y la celda del mapa es "
                  f"{mapa.tamano_celda:.2f} m.")
            print()
            print("  El robot va a sobresalir hacia las celdas vecinas. En la")
            print("  ventana se va a ver como si atravesara los obstaculos, y")
            print("  con el robot real los tocaria.")
            print()
            print("  Que hacer, cualquiera de las dos:")
            print(f"    - usar el G1, que mide 0.32 m y entra")
            print(f"    - subir 'tamano_celda_metros' del mapa a {sugerida:.1f}")
            print("*" * 62)
            print()

    # El transporte por defecto es el LOCAL (socket en 127.0.0.1).
    #
    # El camino DDS necesita CycloneDDS y `unitree_sdk2py`, que no se pueden
    # instalar en macOS ni en Windows: CycloneDDS no publica wheels para
    # Python 3.11+, y el SDK llama a `timerfd_create`, que es de Linux. Como el
    # paquete se reparte, el que se reparte no puede ser ese.
    #
    # `--dds` deja el camino viejo a mano para la notebook de Teo y como banco
    # de pruebas de alta fidelidad contra el SDK de verdad.
    try:
        if args.dds:
            from .arrancar import SimuladorOficial
            sim = SimuladorOficial(mundo, robot, r.repo, args.domain,
                                   args.interfaz,
                                   verboso=not args.silencioso, mapa=mapa)
        else:
            from .simulador import SimuladorLocal
            sim = SimuladorLocal(mundo, robot, r.repo,
                                 verboso=not args.silencioso, mapa=mapa,
                                 puerto=args.puerto)
    except FileNotFoundError as exc:
        print(f"\n  ERROR: {exc}\n", file=sys.stderr)
        return 1

    _publicar_activo(robot, p, args.domain, args.interfaz, args.grilla,
                     puerto=(False if args.dds else args.puerto))
    _dejar_sena(robot, args.materia)
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
    if mapa is not None:
        print(f"  Mapa      : {mapa.nombre} ({mapa.filas}x{mapa.columnas}, "
              f"celda {mapa.tamano_celda} m)")
        print(f"  Recorrido : {tuple(mapa.inicio)} -> {tuple(mapa.destino)}, "
              f"mirando al {mapa.orientacion_inicial}")
    if args.dds:
        print(f"  Transporte: DDS, dominio {args.domain}, "
              f"interfaz {args.interfaz}")
    else:
        from .local import HOST, PUERTO
        print(f"  Transporte: local, {HOST}:{args.puerto or PUERTO}")
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

    # TP05: el robot se pasea solo para que el dashboard tenga que graficar.
    paseo = None
    if args.materia == "tp05" and not args.sin_paseo:
        from .paseo import Paseo

        paseo = Paseo(mundo, verboso=not args.silencioso)
        paseo.arrancar()

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
