"""
=============================================================
  Unitree Go2 — TALLER de Programación
=============================================================
  COMANDOS DISPONIBLES:
    robot.StandUp()      → Se para
    robot.StandDown()    → Se acuesta
    robot.Sit()          → Se sienta
    robot.RiseSit()      → Se levanta
    robot.BalanceStand() → Modo balance
    robot.StopMove()     → Frena
    robot.Hello()        → Saluda
    robot.Stretch()      → Se estira
    robot.Heart()        → Corazon
    robot.Dance1()       → Baile 1
    robot.Dance2()       → Baile 2
    robot.FrontJump()    → Salto
    mover(robot, adelante, costado, giro, duracion)
    esperar(segundos)
=============================================================
"""

import sys
import time
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient

def mover(robot, adelante=0.0, costado=0.0, giro=0.0, duracion=1.0):
    inicio = time.time()
    while time.time() - inicio < duracion:
        robot.Move(adelante, costado, giro)
        time.sleep(0.05)
    robot.StopMove()

def esperar(segundos):
    time.sleep(segundos)

# ══════════════════════════════════════════════
#   -----------------------------------------------------------------------------------------------------------
# ══════════════════════════════════════════════

def mi_programa(robot):
    """robot.StandUp()
    esperar(2)
    robot.BalanceStand()
    mover(robot, giro=-0.5, duracion=5)
    mover(robot, adelante=0.5, duracion=3)
    esperar(4)
    robot.Hello()"""

    robot.StandUp()
    esperar(2)
    robot.BalanceStand()
    robot.Stretch()
    esperar(7)
    mover(robot, adelante=0.2, duracion=2)
    esperar(5)

# ══════════════════════════════════════════════
#   -----------------------------------------------------------------------------------------------------------
# ══════════════════════════════════════════════

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
