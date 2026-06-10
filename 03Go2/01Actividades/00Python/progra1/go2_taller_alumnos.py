import sys
import time
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient

def mi_programa(robot):
    """Aquí va tu programa. Puedes usar los siguientes comandos:
    robot.StandUp()      # Poner al robot de pie
    robot.StandDown()    # Poner al robot en reposo
    robot.BalanceStand() # Mantener equilibrio
    robot.StopMove()     # Frenar
    robot.Damp()         # Amortiguar movimientos
    robot.Move(x, y, z)  # Mover: x=adelante, y=costado, z=giro
    """
    pass

def main():
    interfaz = sys.argv[1] if len(sys.argv) > 1 else "enp0s31f6"
    print("=" * 50)
    print("  Unitree Go2 — Taller de Programación")
    print("=" * 50)
    print(f"[INFO] Conectando vía '{interfaz}'...")
    ChannelFactoryInitialize(0, interfaz)
    robot = SportClient()
    robot.SetTimeout(10.0)
    robot.Init()
    print("[OK]  Conectado. Iniciando en 2 segundos...\n")
    time.sleep(2)
    try:
        mi_programa(robot)
    except KeyboardInterrupt:
        print("\n[STOP] Programa interrumpido.")
    finally:
        print("\n[FIN]  Llevando al robot a reposo...")
        robot.StandDown()
        time.sleep(1)
        robot.Damp()
        print("[OK]   Listo!")

if __name__ == "__main__":
    main()
