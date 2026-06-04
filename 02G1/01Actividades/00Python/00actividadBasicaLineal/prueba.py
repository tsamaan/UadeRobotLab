import time

import sys

from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize

from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient

from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient
 
def patron_bandera_argentina(audio_client):

    print("Mostrando bandera Argentina... 🇦🇷")

    audio_client.LedControl(117, 170, 219)

    time.sleep(2)

    audio_client.LedControl(255, 255, 255)

    time.sleep(2)

    audio_client.LedControl(252, 191, 73)

    time.sleep(2)

    audio_client.LedControl(255, 255, 255)

    time.sleep(2)

    audio_client.LedControl(117, 170, 219)

    time.sleep(2)
 
if __name__ == "__main__":

    interfaz = sys.argv[1] if len(sys.argv) > 1 else "enp0s31f6"

    print(f"[INFO] Conectando vía '{interfaz}'...")

    ChannelFactoryInitialize(0, interfaz)
 
    audio_client = AudioClient()  

    audio_client.SetTimeout(10.0)

    audio_client.Init()
 
    sport_client = LocoClient()  

    sport_client.SetTimeout(10.0)

    sport_client.Init()
 
    audio_client.SetVolume(100)

    time.sleep(1)
 
    sport_client.WaveHand()

    time.sleep(1)
 
    print("Frase")

    estrofa = (

        "Hola Pole ¿Cómo estás?"

    )

    audio_client.SetVolume(100)

    audio_client.TtsMaker(estrofa, 1)

    time.sleep(5)

    patron_bandera_argentina(audio_client)
 
    time.sleep(2)
 
    audio_client.LedControl(0, 0, 0)
 