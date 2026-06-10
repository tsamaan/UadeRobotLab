from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from g1_student_api import RobotG1


def mi_programa(robot: RobotG1) -> None:
    robot.saludar()
    robot.movimiento(adelante=0.20, costado=0.0, giro=0.0, tiempo=2.0)
    robot.movimiento(adelante=0.0, costado=0.0, giro=0.60, tiempo=1.5)
    robot.dar_beso()
    robot.detenerse()


def main() -> None:
    robot = RobotG1()
    robot.conectar()
    try:
        mi_programa(robot)
    finally:
        robot.detenerse()
        robot.desconectar()


if __name__ == "__main__":
    main()
