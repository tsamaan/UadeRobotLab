import time

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient


def mover(robot, adelante=0.0, costado=0.0, giro=0.0, duracion=1.0):
    inicio = time.time()
    while time.time() - inicio < duracion:
        robot.Move(adelante, costado, giro)
        time.sleep(0.05)
    robot.StopMove()


def main():
    ChannelFactoryInitialize(0, "modo-prueba")

    robot = SportClient()
    robot.SetTimeout(10.0)
    robot.Init()

    robot.StandUp()
    time.sleep(1)
    robot.BalanceStand()
    mover(robot, adelante=0.3, duracion=2)
    mover(robot, giro=0.5, duracion=1)
    robot.Hello()
    time.sleep(1)
    robot.StandDown()
    robot.Damp()


if __name__ == "__main__":
    main()
