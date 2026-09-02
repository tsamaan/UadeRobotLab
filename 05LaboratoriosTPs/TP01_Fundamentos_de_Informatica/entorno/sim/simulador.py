"""El simulador que va en el paquete: MuJoCo + socket local, SIN DDS.

Es el mismo simulador de siempre -- el modelo OFICIAL de Unitree, la misma
cinematica, el mismo visor, la misma telemetria y la misma grilla -- con el
transporte cambiado. Hereda de `SimuladorOficial` y solo reemplaza dos cosas:

    iniciar_transporte()      levanta el socket en vez del bridge DDS
    _publicar_telemetria()    arma un diccionario en vez de un LowState_

Todo lo demas se reusa tal cual, que es justamente lo que hace barato tener los
dos caminos vivos: si se arregla la marcha o la integracion, se arregla en los
dos a la vez.

Por que sin DDS: ver la cabecera de `local.py`. En dos lineas -- CycloneDDS no
tiene wheels para Python 3.11+, y el SDK de Unitree solo corre en Linux. El
paquete se reparte a gente con macOS y Windows.
"""

from __future__ import annotations

from .arrancar import SimuladorOficial
from .local import ServidorLocal


class SimuladorLocal(SimuladorOficial):
    """El simulador del paquete. No importa nada de `unitree_sdk2py`."""

    def __init__(self, mundo, robot, repo: str, verboso: bool = True,
                 mapa=None, puerto: int | None = None):
        # domain e interfaz no se usan en este modo, pero el padre arma con
        # ellos su `cfg` (que ademas trae SIMULATE_DT y VIEWER_DT). Se le pasan
        # valores neutros: aca no hay red que configurar.
        super().__init__(mundo, robot, repo, domain=0, interfaz="",
                         verboso=verboso, mapa=mapa)
        self.puerto = puerto
        self.servidor = None
        self._ultima_telemetria: dict = {}

    # ---------- transporte ----------
    def iniciar_transporte(self):
        """Levanta el socket. Es IDEMPOTENTE a proposito.

        Si la ventana 3D se cae a mitad de camino, el simulador vuelve al modo
        consola y ese camino llama de nuevo aca. Sin esta guarda, el segundo
        intento chocaria con el puerto ya abierto y el simulador moriria por un
        problema que ya habia sobrevivido.
        """
        if self.servidor is not None:
            return

        from .local import PUERTO

        self.servidor = ServidorLocal(
            self.mundo, self.robot, self.mundo.perfil,
            telemetria=lambda: self._ultima_telemetria,
            verboso=self.verboso,
            puerto=self.puerto if self.puerto is not None else PUERTO)
        self.servidor.arrancar_en_hilo()

    def cerrar(self) -> None:
        if self.servidor is not None:
            try:
                self.servidor.shutdown()
                self.servidor.server_close()
            except Exception:                                 # noqa: BLE001
                pass
            self.servidor = None

    # ---------- telemetria ----------
    def _publicar_telemetria(self, estado, nu, fase, moviendose) -> None:
        """Deja lista la foto que sirve el socket.

        Tiene la MISMA forma que lo que el TP05 leia del `LowState_` por DDS,
        para que el adaptador del dashboard no cambie: `motor_state`, `imu`,
        `bms` y `foot_force`.
        """
        import math

        temps = self.telemetria.temperaturas
        qpos = self.data.qpos[7:]
        qvel = self.data.qvel[6:]
        base_torque = 2 * nu
        sensores = self.data.sensordata

        motores = []
        for i in range(nu):
            torque = (float(sensores[base_torque + i])
                      if base_torque + i < len(sensores) else 0.0)
            motores.append({
                "id": i,
                "q": float(qpos[i]) if i < len(qpos) else 0.0,
                "dq": float(qvel[i]) if i < len(qvel) else 0.0,
                "tau_est": torque,
                "temperature": int(temps[i]) if i < len(temps) else 0,
            })

        roll, pitch = self._inclinacion
        yaw = self._yaw
        cr, sr = math.cos(roll / 2), math.sin(roll / 2)
        cp, sp = math.cos(pitch / 2), math.sin(pitch / 2)
        cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)

        soc = int(self.telemetria.bateria)
        self._ultima_telemetria = {
            "motor_state": motores,
            "imu": {
                "quaternion": [cr * cp * cy + sr * sp * sy,
                               sr * cp * cy - cr * sp * sy,
                               cr * sp * cy + sr * cp * sy,
                               cr * cp * sy - sr * sp * cy],
                "rpy": [roll, pitch, yaw],
                # Sin fisica no hay acelerometro real: se publica la gravedad
                # proyectada, que es lo que mide un IMU quieto e inclinado.
                "accelerometer": [-9.81 * math.sin(pitch),
                                  9.81 * math.sin(roll),
                                  9.81 * math.cos(roll) * math.cos(pitch)],
                "gyroscope": [0.0, 0.0, float(getattr(self.mundo, "vyaw", 0.0))],
            },
            "bms": {
                "soc": soc,
                # Negativo = descarga, como reporta el robot real.
                "current": -1200 if moviendose else -300,
                "cell_vol": [3700 + (soc - 50) * 4] * 10,
                "temperature": 30,
            },
            "foot_force": [int(f) for f in
                           self.telemetria.fuerzas_de_pata(fase, 4, moviendose)],
        }
