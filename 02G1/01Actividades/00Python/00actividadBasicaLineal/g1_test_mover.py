"""
Test mínimo: mover el G1 hacia adelante y frenar.

Si falla con "ModuleNotFoundError: unitree_sdk2py", instalá el SDK:
    pip install -e ~/unitree_sdk2_python

Uso:
    python3 g1_test_mover.py [interfaz_de_red]
    python3 g1_test_mover.py enp0s31f6
"""

import sys
import time
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient

interfaz = sys.argv[1] if len(sys.argv) > 1 else "enp0s31f6"

print(f"[INFO] Conectando vía '{interfaz}'...")
ChannelFactoryInitialize(0, interfaz)

robot = LocoClient()
robot.SetTimeout(10.0)
robot.Init()
print("[OK]  Conectado.\n")

time.sleep(1)

# Avanzar
print("Avanzando...")
inicio = time.time()
while time.time() - inicio < 5.0:
    robot.Move(0.3, 0.0, 0.0)
    time.sleep(0.05)
robot.StopMove()
print("[OK]  Frenado.")