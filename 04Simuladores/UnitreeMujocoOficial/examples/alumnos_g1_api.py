# =============================================================================
# MÉTODOS DISPONIBLES EN RobotG1
# =============================================================================
#
# robot.conectar()
#   Conecta al simulador y devuelve el estado inicial del robot.
#
# robot.desconectar()
#   Desconecta del simulador.
#
# robot.verificar_estado() -> EstadoRobot
#   Devuelve la posición y acción actual del robot (x, y, z, yaw, accion).
#
# robot.movimiento(adelante, costado, giro, tiempo)
#   Mueve el robot:
#     adelante : velocidad hacia adelante/atrás  (m/s, puede ser negativo)
#     costado  : desplazamiento lateral           (m/s, puede ser negativo)
#     giro     : velocidad de rotación            (rad/s, puede ser negativo)
#     tiempo   : duración del movimiento          (segundos)
#
# robot.saludar()
#   El robot ejecuta una animación de saludo.
#
# robot.dar_beso()
#   El robot ejecuta una animación de beso.
#
# robot.detenerse()
#   Detiene al robot y cancela cualquier movimiento en curso.
#
# =============================================================================

from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from g1_student_api import RobotG1

def mi_programa(robot: RobotG1) -> None:
    robot.movimiento(adelante=0.0, costado=0.0,giro=0.5,tiempo=8.5)
    robot.movimiento(adelante=0.80, costado=0.0,giro=0.0,tiempo=30.0)
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
