from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from g1_student_api import RobotG1


robot = RobotG1()

robot.conectar()

print("El robot va a girar un poco.")
robot.movimiento(adelante=0.0, costado=0.0, giro=0.5, tiempo=4.0)

print("El robot va a saludar.")
robot.saludar()

print("El robot va a caminar hacia adelante.")
robot.movimiento(adelante=0.2, costado=0.0, giro=0.0, tiempo=3.0)

print("El robot va a dar un beso.")
robot.dar_beso()

print("El robot se detiene.")
robot.detenerse()

robot.desconectar()
