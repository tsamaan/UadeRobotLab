"""Levanta el simulador OFICIAL de Unitree, listo para el TP.

Que hace, en orden:

  1. Inyecta nuestra configuracion (robot, dominio, interfaz) donde el codigo
     oficial la espera. El bridge oficial hace `import config` y ramifica segun
     config.ROBOT para elegir los mensajes unitree_hg (G1) o unitree_go (Go2),
     asi que hay que dejarsela puesta ANTES de importarlo.
  2. Carga la escena oficial del robot elegido.
  3. Levanta el UnitreeSdk2Bridge OFICIAL: publica rt/lowstate y escucha
     rt/lowcmd, igual que contra el robot real.
  4. Levanta el servicio "sport", que el simulador oficial NO trae. Sin esto
     LocoClient.Move() da timeout: el controlador que hace caminar al G1 corre
     en la PC interna del robot y Unitree no lo publica.
  5. Corre el bucle y la ventana.

Sobre la fisica: el bucle usa mj_forward, no mj_step. El G1 es un humanoide y
SE CAE SOLO sin un controlador de locomocion; con fisica real se desploma antes
de que el alumno pruebe nada. La marcha de las patas es cosmetica.
"""

from __future__ import annotations

import math
import os
import sys
import time
import types


def preparar_config(robot, repo: str, domain: int, interfaz: str):
    """Deja un modulo `config` en sys.modules para el codigo oficial."""
    cfg = types.ModuleType("config")
    cfg.ROBOT = robot.clave
    cfg.ROBOT_SCENE = os.path.join(repo, "unitree_robots", robot.escena)
    cfg.DOMAIN_ID = domain
    cfg.INTERFACE = interfaz
    cfg.USE_JOYSTICK = 0            # sin joystick: nadie tiene uno en clase
    cfg.JOYSTICK_TYPE = "xbox"
    cfg.JOYSTICK_DEVICE = 0
    cfg.PRINT_SCENE_INFORMATION = False
    cfg.ENABLE_ELASTIC_BAND = False  # no hace falta: no corremos fisica
    cfg.SIMULATE_DT = 0.005
    cfg.VIEWER_DT = 0.02
    sys.modules["config"] = cfg
    return cfg


class SimuladorOficial:
    def __init__(self, mundo, robot, repo: str, domain: int = 0,
                 interfaz: str = "lo", verboso: bool = True, mapa=None):
        self.mundo = mundo
        self.robot = robot
        self.mapa = mapa
        self.repo = repo
        self.verboso = verboso

        self.cfg = preparar_config(robot, repo, domain, interfaz)
        if not os.path.exists(self.cfg.ROBOT_SCENE):
            raise FileNotFoundError(
                f"No encuentro la escena oficial:\n  {self.cfg.ROBOT_SCENE}")

        # El bridge oficial vive en el repo de Unitree.
        ruta_oficial = os.path.join(repo, "simulate_python")
        if ruta_oficial not in sys.path:
            sys.path.insert(0, ruta_oficial)

        import mujoco

        self.mj = mujoco
        self.model = mujoco.MjModel.from_xml_path(self.cfg.ROBOT_SCENE)
        self.data = mujoco.MjData(self.model)
        self.model.opt.timestep = self.cfg.SIMULATE_DT
        self.model.opt.gravity[:] = 0.0   # sin fisica, el robot no se cae

        self.bridge = None
        self.servicio = None

        # Telemetria para el TP05. Sin esto, el dashboard del alumno grafica
        # lineas planas: la cinematica no produce torque ni temperatura.
        from .telemetria import Telemetria

        self.telemetria = Telemetria(self.model.nu)
        self._qpos_previo = None

    # ---------- DDS ----------
    def iniciar_dds(self):
        from unitree_sdk2py.core.channel import ChannelFactoryInitialize

        ChannelFactoryInitialize(self.cfg.DOMAIN_ID, self.cfg.INTERFACE)

        # Bridge OFICIAL: rt/lowstate, rt/lowcmd, rt/sportmodestate
        from unitree_sdk2py_bridge import UnitreeSdk2Bridge

        self.bridge = UnitreeSdk2Bridge(self.model, self.data)
        if self.verboso:
            print("  [DDS] Bridge oficial activo: rt/lowstate, rt/lowcmd")

        # El bridge oficial publica SOLO en rt/lowstate. El robot real publica
        # ademas en rt/lf/lowstate, y varios laboratorios escuchan ahi -- el
        # TP05 entre ellos. Sin este espejo, el dashboard del alumno no recibe
        # nada contra el simulador y si contra el robot: la diferencia
        # aparecería recien el dia de la visita.
        self._espejo_lowstate()

        # Servicio de locomocion, que el oficial NO trae.
        if self.robot.clave == "g1":
            from .servicio_sport import ServicioSportSimulado

            self.servicio = ServicioSportSimulado(self.mundo, verboso=self.verboso)
            if self.verboso:
                print("  [DDS] Servicio de locomocion activo: LocoClient responde")
        else:
            from .servicio_sport_go2 import ServicioSportGo2

            self.servicio = ServicioSportGo2(self.mundo, verboso=self.verboso)
            if self.verboso:
                print("  [DDS] Servicio de locomocion activo: SportClient responde")

    def _espejo_lowstate(self) -> None:
        """Republica el LowState en rt/lf/lowstate, como hace el robot real."""
        import threading

        from unitree_sdk2py.core.channel import ChannelPublisher

        if self.robot.clave == "g1":
            from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_
        else:
            from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowState_

        pub = ChannelPublisher("rt/lf/lowstate", LowState_)
        pub.Init()
        self._pub_espejo = pub

        def bucle():
            while True:
                low = getattr(self.bridge, "low_state", None)
                if low is not None:
                    # La inclinacion se aplica ACA, justo antes de publicar: el
                    # bridge oficial reescribe el cuaternion desde sensordata en
                    # su propio hilo, asi que el ultimo en escribir tiene que
                    # ser el espejo. El adaptador del TP05 calcula roll y pitch
                    # a partir del cuaternion, no de rpy.
                    roll, pitch = getattr(self, "_inclinacion", (0.0, 0.0))
                    yaw = getattr(self, "_yaw", 0.0)
                    cr, sr = math.cos(roll / 2), math.sin(roll / 2)
                    cp, sp = math.cos(pitch / 2), math.sin(pitch / 2)
                    cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
                    try:
                        q = low.imu_state.quaternion
                        q[0] = cr * cp * cy + sr * sp * sy
                        q[1] = sr * cp * cy - cr * sp * sy
                        q[2] = cr * sp * cy + sr * cp * sy
                        q[3] = cr * cp * sy - sr * sp * cy
                        low.imu_state.rpy[0] = roll
                        low.imu_state.rpy[1] = pitch
                        low.imu_state.rpy[2] = yaw
                        pub.Write(low)
                    except Exception:
                        pass
                time.sleep(0.02)   # 50 Hz, como el bridge oficial

        threading.Thread(target=bucle, daemon=True).start()
        if self.verboso:
            print("  [DDS] Espejo activo: rt/lf/lowstate (lo usa el TP05)")

    # ---------- pose ----------
    def _escribir_pose(self):
        e = self.mundo.leer()
        q = self.data.qpos

        q[0] = e["x"]
        q[1] = e["y"]
        q[2] = self.robot.altura + e.get("altura", 0.0)
        media = e["yaw"] / 2.0
        q[3], q[4], q[5], q[6] = math.cos(media), 0.0, 0.0, math.sin(media)

        art = q[7:]
        art[:] = 0.0
        for idx, valor in self.robot.pose_de_pie.items():
            if idx < len(art):
                art[idx] = valor

        if not e.get("de_pie", True):
            for idx, valor in self.robot.pose_sentado.items():
                if idx < len(art):
                    art[idx] = valor
        elif e["accion"] in ("saludando", "besando"):
            for idx, valor in self.robot.saludo.items():
                if idx < len(art):
                    art[idx] = valor
        elif e["moviendose"]:
            f = e["fase"]
            for idx, amplitud, desfase in self.robot.marcha:
                if idx < len(art):
                    art[idx] += amplitud * math.sin(f + desfase)

        # Velocidad de las articulaciones por diferencia finita. Es REAL: las
        # articulaciones se estan moviendo de verdad, aunque no haya fisica.
        # De aca salen tambien el gyro y la velocidad de motor que publica el
        # bridge oficial.
        ahora = time.perf_counter()
        if self._qpos_previo is not None:
            dt = ahora - self._qpos_previo[0]
            if dt > 1e-6:
                self.data.qvel[6:] = (q[7:] - self._qpos_previo[1]) / dt
                self.data.qvel[:6] = 0.0
            else:
                self.data.qvel[:] = 0.0
        else:
            self.data.qvel[:] = 0.0
        self._qpos_previo = (ahora, q[7:].copy())

        self.mj.mj_forward(self.model, self.data)
        self._completar_telemetria(e)

    # ---------- bucles ----------
    def correr_con_ventana(self):
        import mujoco.viewer

        with mujoco.viewer.launch_passive(
            self.model, self.data, show_left_ui=False, show_right_ui=False
        ) as v:
            v.cam.distance = 3.5 if self.robot.tipo == "humanoide" else 2.6
            v.cam.elevation = -20
            if self.mapa is not None:
                from .dibujo import dibujar
                # Se dibuja sobre la escena OFICIAL, sin modificarla.
                dibujar(v.user_scn, self.mapa)
                v.cam.distance = max(
                    3.0, 1.6 * max(self.mapa.filas, self.mapa.columnas)
                    * self.mapa.tamano_celda)
                cx = (self.mapa.columnas - 1) / 2 * self.mapa.tamano_celda
                cy = -(self.mapa.filas - 1) / 2 * self.mapa.tamano_celda
                v.cam.lookat[:] = [cx, cy, 0.0]
            self.iniciar_dds()
            periodo = self.cfg.VIEWER_DT
            while v.is_running():
                inicio = time.perf_counter()
                self.mundo.avanzar()
                self._escribir_pose()
                self._volcar_avisos()
                if self.mapa is not None and self._ruta_cambio():
                    from .dibujo import dibujar
                    dibujar(v.user_scn, self.mapa)
                v.sync()
                resto = periodo - (time.perf_counter() - inicio)
                if resto > 0:
                    time.sleep(resto)

    def correr_sin_ventana(self):
        self.iniciar_dds()
        while True:
            self.mundo.avanzar()
            self._escribir_pose()
            self._volcar_avisos()
            time.sleep(self.cfg.VIEWER_DT)

    def _completar_telemetria(self, estado) -> None:
        """Rellena lo que la cinematica no produce. Ver telemetria.py."""
        import numpy as np

        nu = self.model.nu
        moviendose = bool(estado.get("moviendose"))
        fase = float(estado.get("fase", 0.0))

        # Esfuerzo por motor: cuanto se esta moviendo cada articulacion.
        vel = np.abs(self.data.qvel[6:6 + nu])
        esfuerzos = np.clip(vel / 2.0, 0.0, 1.0).tolist()

        # Las piernas cargan mas peso que los brazos.
        cargas = [1.0 if i < nu // 2 else 0.45 for i in range(nu)]

        self.telemetria.actualizar(esfuerzos, moviendose)
        torques = self.telemetria.torque(esfuerzos, cargas)

        # El bridge oficial lee el torque de sensordata (mjSENS_JOINTACTFRC),
        # que sin fisica queda en cero. Se escribe ahi para no tocar el bridge
        # ni el laboratorio: la ruta de la telemetria queda igual.
        base_torque = 2 * nu
        for i, t in enumerate(torques):
            if base_torque + i < len(self.data.sensordata):
                self.data.sensordata[base_torque + i] = t

        # Temperatura, bateria y fuerzas NO las publica el bridge oficial: se
        # escriben directo en el mensaje que esta por salir.
        low = getattr(self.bridge, "low_state", None)
        if low is None:
            return
        temps = self.telemetria.temperaturas
        for i in range(min(nu, len(low.motor_state))):
            m = low.motor_state[i]
            try:
                if hasattr(m.temperature, "__len__"):
                    m.temperature[0] = int(temps[i])
                    if len(m.temperature) > 1:
                        m.temperature[1] = int(temps[i])
                else:
                    m.temperature = int(temps[i])
            except (TypeError, ValueError, IndexError):
                pass

        # La inclinacion se guarda y la aplica el espejo al publicar. No se
        # escribe aca porque el bridge oficial reescribe el cuaternion desde
        # sensordata en su propio hilo, DESPUES de esto, y se perderia.
        self._inclinacion = self.telemetria.inclinacion(fase, moviendose)
        self._yaw = float(estado.get("yaw", 0.0))

        if hasattr(low, "foot_force"):
            for i, f in enumerate(self.telemetria.fuerzas_de_pata(fase, 4, moviendose)):
                if i < len(low.foot_force):
                    low.foot_force[i] = f
        if hasattr(low, "bms_state"):
            try:
                low.bms_state.soc = int(self.telemetria.bateria)
            except (TypeError, ValueError):
                pass
        if hasattr(low, "power_v"):
            try:
                low.power_v = 28.0 + (self.telemetria.bateria / 100.0) * 4.0
            except (TypeError, ValueError):
                pass

    _ultima_ruta = None

    def _ruta_cambio(self) -> bool:
        actual = len(self.mapa.ruta) if self.mapa.ruta else 0
        if actual != self._ultima_ruta:
            self._ultima_ruta = actual
            return True
        return False

    def _volcar_avisos(self):
        if self.mundo.avisos and self.verboso:
            for aviso in self.mundo.avisos:
                print(f"  [LIMITE] {aviso}")
            self.mundo.avisos.clear()
