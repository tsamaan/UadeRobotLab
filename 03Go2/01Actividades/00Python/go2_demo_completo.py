"""
=============================================================
  Unitree Go2 - Script de Demostración Completo
  Para actividad universitaria con alumnos de secundaria
=============================================================
"""

import sys
import time
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient

NETWORK_INTERFACE = "enp0s31f6"
SLEEP_AFTER_CMD  = 1.5

def conectar_robot(interfaz):
    print(f"[INFO] Conectando al Go2 vía '{interfaz}'...")
    ChannelFactoryInitialize(0, interfaz)
    client = SportClient()
    client.SetTimeout(10.0)
    client.Init()
    print("[OK]  Conexión establecida.\n")
    return client

def esperar(segundos=SLEEP_AFTER_CMD, msg=""):
    if msg:
        print(f"       → {msg}")
    time.sleep(segundos)

def rutina_arranque(c):
    print("▶  Rutina 1: ARRANQUE")
    c.StandUp()
    esperar(2, "De pie...")
    c.BalanceStand()
    esperar(1.5, "Modo balance activado.")

def rutina_movimiento(c):
    print("\n▶  Rutina 2: MOVIMIENTO")
    print("   ↑ Avanzando...")
    inicio = time.time()
    while time.time() - inicio < 2.0:
        c.Move(0.3, 0, 0)
        time.sleep(0.05)
    c.StopMove()
    esperar(0.8)

    print("   ↓ Retrocediendo...")
    inicio = time.time()
    while time.time() - inicio < 1.5:
        c.Move(-0.3, 0, 0)
        time.sleep(0.05)
    c.StopMove()
    esperar(0.8)

    print("   ↻ Girando...")
    inicio = time.time()
    while time.time() - inicio < 2.0:
        c.Move(0, 0, 0.6)
        time.sleep(0.05)
    c.StopMove()
    esperar(0.8)

def rutina_gestos(c):
    print("\n▶  Rutina 3: GESTOS")
    print("   👋 Saludando...")
    c.Hello()
    esperar(3)
    print("   🤸 Estirándose...")
    c.Stretch()
    esperar(3)
    print("   ❤️  Corazón...")
    c.Heart()
    esperar(3)

def rutina_baile(c):
    print("\n▶  Rutina 4: BAILE")
    print("   🕺 Dance 1...")
    c.Dance1()
    esperar(5)
    print("   💃 Dance 2...")
    c.Dance2()
    esperar(5)

def rutina_sentar(c):
    print("\n▶  Rutina 5: SENTARSE / PARARSE")
    c.Sit()
    esperar(2, "Sentado.")
    c.RiseSit()
    esperar(2, "De pie nuevamente.")

def rutina_fin(c):
    print("\n▶  Fin de la demo")
    c.StandDown()
    esperar(1.5)
    c.Damp()
    print("[OK]  Robot en reposo. ¡Gracias!")

def main():
    interfaz = sys.argv[1] if len(sys.argv) > 1 else NETWORK_INTERFACE
    print("=" * 55)
    print("  Unitree Go2 — Demostración para Secundarios")
    print("=" * 55)
    client = conectar_robot(interfaz)
    try:
        rutina_arranque(client)
        rutina_movimiento(client)
        rutina_gestos(client)
        rutina_baile(client)
        rutina_sentar(client)
    except KeyboardInterrupt:
        print("\n[STOP] Interrumpido por el usuario.")
    finally:
        rutina_fin(client)

if __name__ == "__main__":
    main()
