import sys
import os as _os

# Evita que el mock local de unitree_sdk2py (usado por ejemplo_alumno.py) interfiera
# con el SDK real instalado, que es el que necesitamos para conectar al robot físico.
_here = _os.path.dirname(_os.path.abspath(__file__))
if _here in sys.path:
    sys.path.remove(_here)
del _here, _os

import time
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient
from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient
 
 
def mi_programa(loco, arm, audio):
    """Aquí va tu programa. Puedes usar:
    loco.Start()          # Poner al robot listo/de pie
    loco.Damp()            # Amortiguar (reposo seguro)
    loco.Move(x, y, yaw)   # Caminar: x=adelante, y=costado, yaw=giro
    loco.StopMove()        # Frenar
    loco.WaveHand()        # Saludar con la mano
    arm.ExecuteActionByName("nombre")  # Gesto predefinido (ver lista abajo)
    audio.TtsMaker("texto", 0)         # El robot HABLA por sus parlantes
 
    Gestos disponibles en arm.action_map:
    release arm, shake hand, high five, hug, high wave, face wave,
    clap, hands up, right hand up, heart, right heart, left kiss,
    right kiss, two-hand kiss, reject, x-ray
    """
    # --- Secuencia "celebración" con voz real del robot ---
    loco.Start()
    time.sleep(2)
 
    arm.ExecuteActionByName("hands up")   # levanta las dos manos
    time.sleep(2)
 
    audio.TtsMaker("Están todos aprobados con 10", 0)
    time.sleep(3)
 
    arm.ExecuteActionByName("clap")        # aplaude de festejo
    time.sleep(2)
 
    arm.ExecuteActionByName("release arm")  # vuelve los brazos a posición normal
    time.sleep(1)
 
 
def main():
    interfaz = sys.argv[1] if len(sys.argv) > 1 else "enp0s31f6"
    print("=" * 50)
    print("  Unitree G1 — Taller de Programación")
    print("=" * 50)
    print(f"[INFO] Conectando vía '{interfaz}'...")
    ChannelFactoryInitialize(0, interfaz)
 
    loco = LocoClient()
    loco.SetTimeout(10.0)
    loco.Init()
 
    arm = G1ArmActionClient()
    arm.SetTimeout(10.0)
    arm.Init()
 
    audio = AudioClient()
    audio.SetTimeout(10.0)
    audio.Init()
 
    print("[OK]  Conectado. Iniciando en 2 segundos...\n")
    time.sleep(2)
    try:
        mi_programa(loco, arm, audio)
    except KeyboardInterrupt:
        print("\n[STOP] Programa interrumpido.")
    finally:
        print("\n[FIN]  Llevando al robot a reposo...")
        arm.ExecuteActionByName("release arm")
        time.sleep(1)
        print("[OK]   Listo!")
 
 
if __name__ == "__main__":
    main()