"""
=============================================================
  Unitree G1 — TALLER de Programación
=============================================================

  El G1 es un robot humanoide bípedo. A diferencia del Go2
  (que es cuadrúpedo), el G1 camina erguido sobre dos piernas
  y tiene brazos con los que puede interactuar.

  COMANDOS DISPONIBLES:
  ┌─ Postura ──────────────────────────────────────────────┐
  │  robot.HighStand()       → Se para bien erguido (alto) │
  │  robot.LowStand()        → Postura más baja            │
  ├─ Movimiento ───────────────────────────────────────────┤
  │  mover(robot, adelante, costado, giro, duracion)       │
  │    adelante : +avanza / -retrocede  (recomendado ≤ 0.4)│
  │    costado  : +izquierda / -derecha (recomendado ≤ 0.3)│
  │    giro     : +gira izq / -gira der (recomendado ≤ 0.5)│
  │    duracion : segundos que dura el movimiento          │
  │  robot.StopMove()        → Frena inmediatamente        │
  ├─ Brazos / Gestos ──────────────────────────────────────┤
  │  robot.WaveHand()        → Saluda con la mano          │
  │  robot.WaveHand(True)    → Saluda girando el cuerpo    │
  │  robot.ShakeHand()       → Estrecha la mano            │
  ├─ Balance ──────────────────────────────────────────────┤
  │  robot.BalanceStand(0)   → Balance normal              │
  │  robot.BalanceStand(1)   → Balance avanzado            │
  └────────────────────────────────────────────────────────┘
  UTILIDADES:
    esperar(segundos)         → Pausa el programa

  SECUENCIA SEGURA DE INICIO:
    1. ... tu código ...  ← el robot ya está parado
    2. Al final: robot.StopMove() para que quede quieto

=============================================================
  USO:
    python3 g1_taller_alumnos.py [interfaz_de_red]
    python3 g1_taller_alumnos.py eth0
=============================================================
"""

import sys
import time
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient


# ── Funciones auxiliares ──────────────────────────────────

def mover(robot, adelante=0.0, costado=0.0, giro=0.0, duracion=1.0):
    """Mueve el robot durante 'duracion' segundos y luego frena."""
    inicio = time.time()
    while time.time() - inicio < duracion:
        robot.Move(adelante, costado, giro)
        time.sleep(0.05)
    robot.StopMove()


def esperar(segundos):
    """Pausa la ejecución del programa."""
    time.sleep(segundos)
 
def mi_programa(robot):
    mover (robot, giro = 0.5, duracion = 2)
    print ("Gira hacia el costado")
    time.sleep(1)
    mover (robot, adelante = 0.5, duracion = 3)
    print("Camina hacia adelante")
    time.sleep(1)
    mover (robot, giro = 0.5, duracion = 10)
    print("Gira para el otro lado")
    time.sleep(1)

def main():
    interfaz = sys.argv[1] if len(sys.argv) > 1 else "enp0s31f6"
    print("=" * 50)
    print("  Unitree G1 — Taller de Programación")
    print("=" * 50)
    print(f"[INFO] Conectando vía '{interfaz}'...")

    ChannelFactoryInitialize(0, interfaz)
    robot = LocoClient()
    robot.SetTimeout(10.0)
    robot.Init()

    print("[OK]  Conectado. Iniciando en 3 segundos...\n")
    time.sleep(3)

    try:
        mi_programa(robot)
    except KeyboardInterrupt:
        print("\n[STOP] Programa interrumpido.")
    finally:
        print("\n[FIN]  Frenando...")
        robot.StopMove()
        print("[OK]   Listo!")


if __name__ == "__main__":
    main()
