"""La API que usan los alumnos. Contrato v1.0 (ver ~/Escritorio/CONTRATO_API.md).

Por debajo usa el SDK REAL de Unitree: LocoClient para el G1, SportClient para
el Go2. Los mismos objetos que se usan contra el robot fisico. Lo unico que
cambia entre simulador y robot real son el dominio DDS y la interfaz de red.

    from robot import Robot

    robot = Robot()
    robot.conectar()
    robot.avanzar(velocidad=0.2, tiempo=2.0)
    robot.girar(velocidad=0.5, tiempo=3.14)
    robot.saludar()
    robot.detenerse()
    robot.desconectar()
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass

from .safety import (
    ErrorDeSeguridad,
    PerfilSeguridad,
    perfil as obtener_perfil,
    validar_duracion,
    validar_velocidad,
    validar_velocidad_angular,
)

# El simulador deja aca que robot y que materia levanto.
ARCHIVO_ACTIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              ".simulador_activo.json")

# Refresco de Move(): es una velocidad con vencimiento, no un paso. Si el
# programa muere, el robot frena solo en ~1 s. Ver frenado en el CONTRATO.
PASO_REFRESCO = 0.1

_DDS_INICIADO = {"hecho": False}


@dataclass
class EstadoRobot:
    x: float
    y: float
    z: float
    yaw: float
    accion: str
    bateria: int = 87

    def __str__(self) -> str:
        return (f"x={self.x:+.2f} m  y={self.y:+.2f} m  "
                f"rumbo={math.degrees(self.yaw):+.1f} deg  [{self.accion}]")


class NoHaySimulador(RuntimeError):
    pass


def _leer_activo() -> dict:
    try:
        with open(ARCHIVO_ACTIVO, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


class Robot:
    """El robot. Por defecto se conecta al simulador que tenes abierto."""

    def __init__(self, materia: str | None = None, destino: str = "simulador",
                 modelo: str | None = None, interfaz: str | None = None,
                 domain: int | None = None):
        activo = _leer_activo()

        if destino == "simulador":
            if not activo:
                raise NoHaySimulador(
                    "No encuentro el simulador.\n"
                    "  1. Abri INICIAR_SIMULADOR y elegi el robot\n"
                    "  2. Espera a que aparezca la ventana\n"
                    "  3. Volve a ejecutar este programa")
            self.modelo = modelo or activo.get("robot", "g1")
            self.interfaz = interfaz or activo.get("interfaz", "lo")
            self.domain = domain if domain is not None else activo.get("domain", 0)
            self.perfil = obtener_perfil(materia or activo.get("materia", "tp01"))
        else:
            # Robot fisico: lo usa el laboratorio, no el alumno.
            self.modelo = modelo or destino
            self.interfaz = interfaz or ""
            self.domain = domain if domain is not None else 0
            self.perfil = obtener_perfil(materia or "tp01")

        self.destino = destino
        self._cliente = None

    # ---------- conexion ----------
    def conectar(self) -> EstadoRobot:
        from unitree_sdk2py.core.channel import ChannelFactoryInitialize

        if not _DDS_INICIADO["hecho"]:
            ChannelFactoryInitialize(self.domain, self.interfaz)
            _DDS_INICIADO["hecho"] = True

        if self.modelo == "g1":
            from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient

            self._cliente = LocoClient()
            self._cliente.SetTimeout(5.0)
            self._cliente.Init()
            # Sin Start() el robot ignora los Move: queda en un estado que no
            # acepta movimiento.
            self._cliente.Start()
            nombre = "Unitree G1 (humanoide)"
        else:
            from unitree_sdk2py.go2.sport.sport_client import SportClient

            self._cliente = SportClient()
            self._cliente.SetTimeout(5.0)
            self._cliente.Init()
            self._cliente.StandUp()
            nombre = "Unitree Go2 (perro)"

        # VERIFICAR QUE EL SERVICIO RESPONDE DE VERDAD.
        #
        # Move() del SDK descarta el codigo de retorno. Si el servicio de
        # locomocion todavia no esta arriba -- por ejemplo si el programa
        # arranca un segundo antes que el simulador -- las ordenes se pierden
        # en silencio: el alumno ve "11 ordenes ejecutadas" y un robot que no
        # se movio ni un centimetro.
        #
        # Por eso hacemos un ida y vuelta con una llamada que SI devuelve
        # codigo, y reintentamos unos segundos por si el simulador esta
        # terminando de levantar.
        self._verificar_servicio()

        print(f"[OK] Conectado a {nombre}.")
        print(f"     Limites: {self.perfil.velocidad_max} m/s, "
              f"{self.perfil.velocidad_angular_max} rad/s, "
              f"{self.perfil.duracion_max} s por orden.")
        return self.verificar_estado()

    def _verificar_servicio(self, intentos: int = 12, espera: float = 0.5) -> None:
        ultimo = None
        for _ in range(intentos):
            try:
                if self.modelo == "g1":
                    codigo, _dato = self._cliente.GetFsmId()
                else:
                    codigo = self._cliente.StandUp()
                if codigo == 0:
                    return
                ultimo = f"codigo {codigo}"
            except Exception as exc:
                ultimo = str(exc)
            time.sleep(espera)

        raise NoHaySimulador(
            "Me conecte al robot pero NO responde a las ordenes"
            + (f" ({ultimo})" if ultimo else "") + ".\n\n"
            "  Casi siempre es una de estas dos:\n"
            "    1. El simulador todavia estaba abriendo. Espera a que la\n"
            "       ventana aparezca del todo y volve a ejecutar.\n"
            "    2. El simulador no esta abierto. Abri INICIAR_SIMULADOR.\n\n"
            "  (Se corta aca a proposito: si siguieramos, las ordenes se\n"
            "   perderian en silencio y pareceria que tu programa anda.)")

    def desconectar(self) -> None:
        try:
            self.detenerse()
        except Exception:
            pass
        self._cliente = None
        print("[OK] Desconectado.")

    # ---------- consultas ----------
    def verificar_estado(self) -> EstadoRobot:
        """Lee la pose desde el simulador. Contra el robot real vendria del DDS."""
        a = _leer_activo()
        pose = a.get("pose_archivo")
        datos = {}
        if pose and os.path.exists(pose):
            try:
                with open(pose, encoding="utf-8") as f:
                    datos = json.load(f)
            except Exception:
                datos = {}
        return EstadoRobot(
            x=datos.get("x", 0.0), y=datos.get("y", 0.0),
            z=datos.get("z", 0.0), yaw=datos.get("yaw", 0.0),
            accion=datos.get("accion", "quieto"),
            bateria=datos.get("bateria", 87))

    # ---------- movimiento ----------
    def _sostener(self, vx: float, vy: float, vyaw: float, tiempo: float) -> None:
        """Refresca Move() en un loop. NUNCA usa continous_move.

        Move() vence en ~1 s: si el programa muere, el robot frena solo y queda
        parado. continous_move=True lleva la duracion a 10 dias y elimina esa
        red de seguridad.
        """
        self._exigir_conexion()
        fin = time.monotonic() + tiempo
        while time.monotonic() < fin:
            self._cliente.Move(vx, vy, vyaw)
            time.sleep(min(PASO_REFRESCO, max(0.0, fin - time.monotonic())))
        self._cliente.StopMove()
        time.sleep(0.15)

    def avanzar(self, velocidad: float = 0.2, tiempo: float = 1.0) -> EstadoRobot:
        """Avanza a 'velocidad' m/s durante 'tiempo' s. Distancia = v x t.

        Validamos ACA, antes de tocar DDS. Es a proposito: el Move() del SDK
        descarta el codigo de retorno, asi que si dejaramos que el rechazo
        viniera del simulador el alumno no se enteraria nunca -- veria el robot
        quieto y ningun mensaje.
        """
        velocidad = validar_velocidad(velocidad, self.perfil)
        tiempo = validar_duracion(tiempo, self.perfil)
        self._sostener(velocidad, 0.0, 0.0, tiempo)
        return self.verificar_estado()

    def girar(self, velocidad: float = 0.5, tiempo: float = 1.0) -> EstadoRobot:
        """Gira a 'velocidad' rad/s durante 'tiempo' s. Positivo = izquierda."""
        velocidad = validar_velocidad_angular(velocidad, self.perfil)
        tiempo = validar_duracion(tiempo, self.perfil)
        self._sostener(0.0, 0.0, velocidad, tiempo)
        return self.verificar_estado()

    def detenerse(self) -> EstadoRobot:
        """Velocidad a cero. NO apaga el robot ni lo sienta ni lo desenergiza."""
        self._exigir_conexion()
        self._cliente.StopMove()
        time.sleep(0.15)
        return self.verificar_estado()

    def saludar(self) -> EstadoRobot:
        self._exigir_conexion()
        for nombre in ("WaveHand", "Hello"):
            metodo = getattr(self._cliente, nombre, None)
            if metodo is not None:
                metodo()
                time.sleep(2.0)
                return self.verificar_estado()
        raise NotImplementedError("Este robot no tiene un gesto de saludo.")

    # ---------- alias tolerantes a errores de tipeo ----------
    def movmineto(self, *a, **k):
        return self.avanzar(*a, **k)

    def detener(self):
        return self.detenerse()

    def parar(self):
        return self.detenerse()

    def _exigir_conexion(self) -> None:
        if self._cliente is None:
            raise NoHaySimulador(
                "El robot no esta conectado. Llama a robot.conectar() primero.")
