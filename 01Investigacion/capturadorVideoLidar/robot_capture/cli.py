from __future__ import annotations

import argparse
import concurrent.futures
import sys
from pathlib import Path

from .camera import CameraConfig, capture_camera
from .lidar import LidarConfig, capture_lidar
from .utils import ensure_dir, list_network_interfaces, timestamp_slug, write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="CapturadorVideoLidar",
        description="Captura camara frontal y nubes de puntos LiDAR de Unitree Go2.",
    )
    parser.add_argument("--mode", choices=["camera", "lidar", "both"], default="both")
    parser.add_argument("--demo", action="store_true", help="Genera datos sinteticos sin robot.")
    parser.add_argument("--interface", default=None, help="Interfaz de red conectada al robot.")
    parser.add_argument("--duration", type=float, default=10.0, help="Duracion de captura en segundos.")
    parser.add_argument("--fps", type=float, default=10.0, help="FPS objetivo para la camara.")
    parser.add_argument("--output", type=Path, default=None, help="Carpeta de salida.")
    parser.add_argument("--sdk-path", default=None, help="Ruta opcional al SDK unitree_sdk2_python.")
    parser.add_argument("--no-video-file", action="store_true", help="No intenta generar AVI/MP4; conserva frames o stream crudo.")
    parser.add_argument("--lidar-topic", default="rt/utlidar/cloud", help="Topico DDS PointCloud2.")
    parser.add_argument("--lidar-state-topic", default="rt/utlidar/lidar_state", help="Topico DDS LidarState.")
    parser.add_argument("--lidar-format", choices=["all", "pcd", "csv", "raw"], default="all")
    parser.add_argument("--max-clouds", type=int, default=0, help="Maximo de nubes; 0 significa sin limite.")
    parser.add_argument("--lidar-switch", choices=["none", "on", "off"], default="none")
    parser.add_argument("--list-interfaces", action="store_true", help="Lista interfaces de red y sale.")
    parser.add_argument("--interactive", action="store_true", help="Fuerza modo asistido por preguntas.")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        args = interactive_args()
    else:
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.interactive:
            args = interactive_args(args)

    if args.list_interfaces:
        interfaces = list_network_interfaces()
        if not interfaces:
            print("No pude detectar interfaces. Se puede escribir el nombre manualmente con --interface.")
        else:
            print("Interfaces detectadas:")
            for name in interfaces:
                print(f"  - {name}")
        return 0

    try:
        run_capture(args)
        return 0
    except KeyboardInterrupt:
        print("\nCaptura cancelada por el usuario.")
        return 130
    except Exception as exc:
        print(f"\nError: {exc}")
        print("Sugerencia: verificar interfaz de red, permisos al robot y topicos LiDAR.")
        return 1


def interactive_args(previous: argparse.Namespace | None = None) -> argparse.Namespace:
    print("")
    print("Capturador Video/LiDAR Unitree Go2")
    print("Dejar una respuesta vacia usa el valor sugerido.")
    print("")

    interfaces = list_network_interfaces()
    if interfaces:
        print("Interfaces detectadas:")
        for index, name in enumerate(interfaces, start=1):
            print(f"  {index}. {name}")
        raw_interface = input("Interfaz del robot (numero o nombre, vacio=auto): ").strip()
        interface = _select_interface(raw_interface, interfaces)
    else:
        interface = input("Interfaz del robot (vacio=auto): ").strip() or None

    mode = _ask_choice("Modo [both/camera/lidar]", "both", {"both", "camera", "lidar"})
    demo = _ask_yes_no("Usar modo demo sin robot", False)
    duration = _ask_float("Duracion en segundos", 10.0)
    fps = _ask_float("FPS objetivo camara", 10.0)
    output_raw = input("Carpeta de salida (vacio=captures/<fecha>): ").strip()
    output = Path(output_raw) if output_raw else None

    lidar_topic = "rt/utlidar/cloud"
    lidar_state_topic = "rt/utlidar/lidar_state"
    lidar_format = "all"
    lidar_switch = "none"
    if mode in {"both", "lidar"}:
        lidar_topic = input(f"Topico nube LiDAR [{lidar_topic}]: ").strip() or lidar_topic
        lidar_state_topic = input(f"Topico estado LiDAR [{lidar_state_topic}]: ").strip() or lidar_state_topic
        lidar_format = _ask_choice("Formato LiDAR [all/pcd/csv/raw]", "all", {"all", "pcd", "csv", "raw"})
        lidar_switch = _ask_choice("Enviar switch LiDAR [none/on/off]", "none", {"none", "on", "off"})

    namespace = argparse.Namespace()
    namespace.mode = mode
    namespace.demo = demo
    namespace.interface = interface
    namespace.duration = duration
    namespace.fps = fps
    namespace.output = output
    namespace.sdk_path = getattr(previous, "sdk_path", None)
    namespace.no_video_file = not _ask_yes_no("Intentar generar video MP4/AVI cuando sea posible", True)
    namespace.lidar_topic = lidar_topic
    namespace.lidar_state_topic = lidar_state_topic
    namespace.lidar_format = lidar_format
    namespace.max_clouds = 0
    namespace.lidar_switch = lidar_switch
    namespace.list_interfaces = False
    namespace.interactive = False
    return namespace


def run_capture(args: argparse.Namespace) -> dict:
    output_dir = ensure_dir(args.output or Path("captures") / timestamp_slug())
    print(f"Salida: {output_dir.resolve()}")

    session = {
        "mode": args.mode,
        "demo": bool(args.demo),
        "interface": args.interface,
        "duration_s": args.duration,
        "output_dir": str(output_dir.resolve()),
        "camera": None,
        "lidar": None,
    }

    tasks: dict[str, object] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        if args.mode in {"camera", "both"}:
            camera_config = CameraConfig(
                interface=args.interface,
                duration=args.duration,
                fps=args.fps,
                output_dir=output_dir,
                sdk_path=args.sdk_path,
                save_video=not args.no_video_file,
                demo=args.demo,
            )
            tasks["camera"] = executor.submit(capture_camera, camera_config)

        if args.mode in {"lidar", "both"}:
            lidar_config = LidarConfig(
                interface=args.interface,
                duration=args.duration,
                output_dir=output_dir,
                sdk_path=args.sdk_path,
                topic=args.lidar_topic,
                state_topic=args.lidar_state_topic,
                export_format=args.lidar_format,
                max_clouds=args.max_clouds,
                switch=args.lidar_switch,
                demo=args.demo,
            )
            tasks["lidar"] = executor.submit(capture_lidar, lidar_config)

        for name, future in tasks.items():
            session[name] = future.result()

    write_json(output_dir / "session_metadata.json", session)
    print("Captura finalizada.")
    return session


def _select_interface(raw: str, interfaces: list[str]) -> str | None:
    if not raw:
        return None
    if raw.isdigit():
        index = int(raw)
        if 1 <= index <= len(interfaces):
            return interfaces[index - 1]
    return raw


def _ask_choice(prompt: str, default: str, choices: set[str]) -> str:
    while True:
        raw = input(f"{prompt} [{default}]: ").strip().lower()
        answer = raw or default
        if answer in choices:
            return answer
        print(f"Opciones validas: {', '.join(sorted(choices))}")


def _ask_yes_no(prompt: str, default: bool) -> bool:
    suffix = "S/n" if default else "s/N"
    while True:
        raw = input(f"{prompt} [{suffix}]: ").strip().lower()
        if not raw:
            return default
        if raw in {"s", "si", "y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Responder s o n.")


def _ask_float(prompt: str, default: float) -> float:
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        if not raw:
            return default
        try:
            value = float(raw)
        except ValueError:
            print("Ingresar un numero.")
            continue
        if value > 0:
            return value
        print("El valor debe ser mayor a cero.")
