import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from student_sdk import Go2LowLevelClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Go2 low-level stand demo para unitree_mujoco.")
    parser.add_argument("--domain", type=int, default=1, help="DDS domain id del simulador.")
    parser.add_argument("--interface", default="Ethernet", help="Interfaz DDS. En Linux suele ser lo.")
    parser.add_argument("--hold", type=float, default=1.5, help="Segundos de espera parado.")
    parser.add_argument("--dt", type=float, default=0.002, help="Periodo de publicacion.")
    args = parser.parse_args()

    robot = Go2LowLevelClient(domain=args.domain, interface=args.interface, dt=args.dt)

    print("[INFO] Stand up...")
    robot.stand_up(duration=1.2)
    robot.hold(duration=args.hold)

    print("[INFO] Stand down...")
    robot.stand_down(duration=1.2)
    robot.damp()
    print("[OK] Comando finalizado.")


if __name__ == "__main__":
    main()
