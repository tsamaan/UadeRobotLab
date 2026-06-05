from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from student_sdk import Go2TrotController


def mi_programa(robot: Go2TrotController) -> None:
    robot.ready()
    robot.walk_forward(speed=0.35, duration=10.0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Trot educativo Go2 sobre LowCmd.")
    parser.add_argument("--domain", type=int, default=1)
    parser.add_argument("--interface", default="Ethernet")
    args = parser.parse_args()

    robot = Go2TrotController(domain=args.domain, interface=args.interface)
    try:
        mi_programa(robot)
    except KeyboardInterrupt:
        print("\n[STOP] Interrumpido.")
    finally:
        robot.stop()
        robot.stand_down()


if __name__ == "__main__":
    main()
