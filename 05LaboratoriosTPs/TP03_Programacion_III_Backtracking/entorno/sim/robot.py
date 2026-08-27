"""La API que usan los alumnos. Contrato v1.0 (ver ~/Escritorio/CONTRATO_API.md).

Tiene DOS transportes, y el codigo del alumno es el mismo en los dos:

  - **simulador** (lo que se reparte): un socket local en 127.0.0.1. No necesita
    CycloneDDS ni `unitree_sdk2py`, que no se pueden instalar en macOS ni en
    Windows -- ver la cabecera de `local.py`. Solo hace falta MuJoCo.
  - **robot real** (solo la notebook de Teo): el SDK de Unitree de verdad,
    LocoClient para el G1 y SportClient para el Go2, por DDS.

El cliente de los dos expone los MISMOS nombres de metodo (`Move`, `StopMove`,
`WaveHand`...), asi que de `conectar()` para abajo no hay una sola rama por
transporte. Lo unico que tiene que coincidir es el CONTRATO de la API, no el
cable.

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
            self.transporte = activo.get("transporte", "local")
        else:
            # Robot fisico: lo usa el laboratorio, no el alumno.
            self.modelo = modelo or destino
            self.interfaz = interfaz or ""
            self.domain = domain if domain is not None else 0
            self.perfil = obtener_perfil(materia or "tp01")
            self.transporte = "dds"      # el robot fisico habla por DDS

        self.destino = destino
        self._cliente = None

    # ---------- conexion ----------
    def conectar(self) -> EstadoRobot:
        # El SIMULADOR decide el transporte, no el cliente: el mismo paquete se
        # puede abrir en modo local (lo normal) o con --dds (el banco de pruebas
        # de la notebook de Teo), y el programa del alumno no cambia.
        if self.destino == "simulador" and self.transporte == "local":
            return self._conectar_local()
        return self._conectar_sdk()

    def _conectar_local(self) -> EstadoRobot:
        """Simulador: socket local. Es el camino que usan profesores y alumnos."""
        from .local import ClienteLocal, ErrorTransporte, PUERTO

        activo = _leer_activo()
        puerto = int(activo.get("puerto", PUERTO))
        self._cliente = ClienteLocal(puerto=puerto)
        try:
            self._cliente.Init()
        except ErrorTransporte as exc:
            self._cliente = None
            raise NoHaySimulador(
                f"{exc}\n"
                "  1. Abri INICIAR_SIMULADOR y elegi el robot\n"
                "  2. Espera a que aparezca la ventana\n"
                "  3. Volve a ejecutar este programa") from exc

        info = self._cliente.info or {}
        self.modelo = info.get("robot", self.modelo)
        nombre = ("Unitree G1 (humanoide)" if self.modelo == "g1"
                  else "Unitree Go2 (perro)")

        # EL SERVIDOR MANDA SOBRE LOS LIMITES.
        #
        # Si el cliente decidiera, alcanzaria con que el alumno declarara otra
        # materia para aflojar el tope de velocidad. El simulador sabe con que
        # perfil lo abrio el profesor, y ese es el que vale.
        limites = info.get("limites") or {}
        if limites:
            self.perfil = self.perfil.__class__(
                nombre=info.get("materia", self.perfil.nombre),
                velocidad_max=limites.get("velocidad_max",
                                          self.perfil.velocidad_max),
                velocidad_angular_max=limites.get(
                    "velocidad_angular_max", self.perfil.velocidad_angular_max),
                duracion_max=limites.get("duracion_max",
                                         self.perfil.duracion_max),
                bateria_min=limites.get("bateria_min", self.perfil.bateria_min))

        self._anunciar(nombre)
        return self.verificar_estado()

    def _conectar_sdk(self) -> EstadoRobot:
        """Robot real por DDS. Solo corre en Linux, solo en la notebook de Teo."""
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
        self._anunciar(nombre)
        return self.verificar_estado()

    def _anunciar(self, nombre: str) -> None:
        print(f"[OK] Conectado a {nombre}.")
        print(f"     Limites: {self.perfil.velocidad_max} m/s, "
              f"{self.perfil.velocidad_angular_max} rad/s, "
              f"{self.perfil.duracion_max} s por orden.")

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
        cerrar = getattr(self._cliente, "Cerrar", None)
        if cerrar is not None:
            cerrar()          # el socket local: hay que soltarlo de verdad
        self._cliente = None
        print("[OK] Desconectado.")

    # ---------- consultas ----------
    def verificar_estado(self) -> EstadoRobot:
        """Donde esta el robot.

        Con el socket se pregunta directo, que es lo mas fiel: la respuesta es
        del mismo instante. El archivo de pose queda como respaldo -- lo usa el
        camino DDS, donde la pose del G1 no viaja por ningun topico.
        """
        preguntar = getattr(self._cliente, "Estado", None)
        if preguntar is not None:
            try:
                d = preguntar()
                return EstadoRobot(
                    x=d.get("x", 0.0), y=d.get("y", 0.0), z=d.get("z", 0.0),
                    yaw=d.get("yaw", 0.0), accion=d.get("accion", "quieto"),
                    bateria=d.get("bateria", 87))
            except Exception:                                 # noqa: BLE001
                pass   # si el socket fallo, probamos con el archivo

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
        # Se refresca igual en los dos transportes: la orden VENCE. Si el
        # programa del alumno muere a mitad de un avance, el robot frena solo.
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

    def mover(self, vx: float = 0.0, vy: float = 0.0, vyaw: float = 0.0,
              tiempo: float = 1.0) -> EstadoRobot:
        """Las tres velocidades A LA VEZ, como el Move() del SDK.

        Es lo que permite una curva: avanzar y girar al mismo tiempo. Si se
        resolviera eligiendo entre avanzar() o girar(), el simulador haria una
        cosa y el robot real otra, y la app del alumno se comportaria distinto
        el dia de la visita.

            vx    adelante (+) / atras (-)      m/s
            vy    izquierda (+) / derecha (-)   m/s
            vyaw  girar izq (+) / der (-)       rad/s
        """
        vx = validar_velocidad(vx, self.perfil)
        vy = validar_velocidad(vy, self.perfil)
        vyaw = validar_velocidad_angular(vyaw, self.perfil)
        tiempo = validar_duracion(tiempo, self.perfil)
        self._sostener(vx, vy, vyaw, tiempo)
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

    def dar_la_mano(self) -> EstadoRobot:
        """Extiende la mano. Solo el G1: el Go2 no tiene manos."""
        self._exigir_conexion()
        metodo = getattr(self._cliente, "ShakeHand", None)
        if metodo is None:
            raise NotImplementedError("Este robot no puede dar la mano.")
        metodo()
        time.sleep(2.0)
        return self.verificar_estado()

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
