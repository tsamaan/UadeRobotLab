from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from student_sdk import Go2LowLevelClient, JOINT_NAMES


def mi_programa(robot: Go2LowLevelClient) -> None:
    robot.stand_up()
    robot.hold(duration=0.8)

    pose = robot.pose()
    pose = robot.set_joint(pose, "FR_thigh", 0.25)
    pose = robot.set_joint(pose, "FR_calf", -0.80)
    robot.interpolate_to(pose, duration=0.8)
    robot.hold(duration=0.5)

    robot.stand_up()
    robot.hold(duration=0.5)


def main() -> None:
    parser = argparse.ArgumentParser(description="Actividad Go2 en bajo nivel.")
    parser.add_argument("--domain", type=int, default=1)
    parser.add_argument("--interface", default="Ethernet")
    args = parser.parse_args()

    print("Joints disponibles:")
    print(", ".join(JOINT_NAMES))

    robot = Go2LowLevelClient(domain=args.domain, interface=args.interface)
    try:
        mi_programa(robot)
    except KeyboardInterrupt:
        print("\n[STOP] Interrumpido.")
    finally:
        robot.stand_down()
        robot.damp()


if __name__ == "__main__":
    main()
