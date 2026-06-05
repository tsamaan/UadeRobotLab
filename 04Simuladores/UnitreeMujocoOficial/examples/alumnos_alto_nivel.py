from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from student_sdk import Go2HighLevelClient


def mi_programa(robot: Go2HighLevelClient) -> None:
    # Esta capa es didactica. El simulador oficial de Unitree no trae el
    # controlador interno SportClient del Go2 fisico, asi que Move no va a
    # caminar igual que el robot real.
    robot.StandUp()
    robot.BalanceStand()

    robot.Move(x=0.25, y=0.0, yaw=0.0, duration=2.0)
    robot.Move(x=0.0, y=0.0, yaw=0.45, duration=1.5)
    robot.Hello()

    robot.Sit()
    time.sleep(1.0)
    robot.RiseSit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Actividad Go2 en alto nivel.")
    parser.add_argument("--domain", type=int, default=1)
    parser.add_argument("--interface", default="Ethernet")
    args = parser.parse_args()

    robot = Go2HighLevelClient(domain=args.domain, interface=args.interface)
    try:
        mi_programa(robot)
    except KeyboardInterrupt:
        print("\n[STOP] Interrumpido.")
    finally:
        robot.StopMove()
        robot.StandDown()


if __name__ == "__main__":
    main()
