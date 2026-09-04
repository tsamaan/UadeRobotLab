"""Transporte LOCAL: el paquete del profesor habla por socket, no por DDS.

Por que existe este archivo
---------------------------
El paquete se reparte a profesores y alumnos con macOS y Windows. El camino DDS
(CycloneDDS + unitree_sdk2py) no se puede instalar ahi sin dolor:

  - `cyclonedds==0.10.2` solo publica wheels hasta cp310. Con Python 3.11+ pip
    intenta compilar desde el fuente y falla con "Could not locate cyclonedds".
    No hay salida por arriba: la 0.10.4 y la 0.10.5 tienen la misma cobertura.
  - El nombre de la interfaz de loopback cambia por sistema: `lo` en Linux,
    `lo0` en macOS, y en Windows no hay equivalente.
  - El bridge oficial de Unitree importa `pygame` siempre, aunque no haya
    joystick.
  - `unitree_sdk2py.utils.thread` resuelve `timerfd_create` por ctypes EN EL
    IMPORT. Es una syscall de Linux: en macOS y Windows el import explota.

Nada de eso es culpa del alumno ni tiene que ver con lo que el TP evalua.

Que se conserva
---------------
El CONTRATO de la API del alumno, que es lo unico que tiene que coincidir entre
el simulador y el robot real:

    robot.avanzar(velocidad, tiempo)
    robot.girar(velocidad, tiempo)

`ClienteLocal` expone los MISMOS nombres de metodo que el `LocoClient` y el
`SportClient` del SDK -- `Move`, `StopMove`, `WaveHand`... -- justamente para
que `robot.py` no tenga que saber por donde esta hablando. El robot que se ve
en pantalla sigue siendo el modelo OFICIAL de Unitree.

El camino DDS no se tira: sigue vivo en `arrancar.py` para la notebook de Teo,
para los laboratorios fisicos y como banco de pruebas de alta fidelidad.
"""

from __future__ import annotations

import json
import socket
import socketserver
import threading

# Loopback y un puerto alto fijo. 127.0.0.1 existe igual en Linux, macOS y
# Windows, que es justamente lo que DDS no nos daba.
HOST = "127.0.0.1"
PUERTO = 8765

# El servidor manda sobre los limites y el cliente los adopta al conectar.
# Si el cliente decidiera, un alumno declararia otra materia y se aflojaria el
# tope de velocidad.
_FIN = b"\n"


class ErrorTransporte(RuntimeError):
    pass


# ---------------------------------------------------------------------------
#  Servidor: vive dentro del proceso del simulador
# ---------------------------------------------------------------------------

class _Manejador(socketserver.StreamRequestHandler):
    """Una linea JSON por pedido, una linea JSON por respuesta."""

    def handle(self) -> None:
        while True:
            try:
                linea = self.rfile.readline()
            except (BrokenPipeError, ConnectionResetError, OSError):
                return   # el alumno cerro su programa: no es un error del simulador
            if not linea:
                return
            try:
                pedido = json.loads(linea.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._responder({"ok": False, "error": "pedido ilegible"})
                continue
            try:
                respuesta = self.server.despachar(pedido)
            except Exception as exc:                          # noqa: BLE001
                respuesta = {"ok": False,
                             "error": f"{type(exc).__name__}: {exc}"}
            self._responder(respuesta)

    def _responder(self, datos: dict) -> None:
        try:
            self.wfile.write(json.dumps(datos).encode("utf-8") + _FIN)
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass   # el alumno cerro su programa: no es un error del simulador


class ServidorLocal(socketserver.ThreadingTCPServer):
    """Atiende las ordenes del programa del alumno y las aplica al mundo."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, mundo, robot, perfil, telemetria=None, verboso=True,
                 puerto: int = PUERTO):
        self.mundo = mundo
        self.robot = robot
        self.perfil = perfil
        self.telemetria = telemetria
        self.verboso = verboso
        try:
            super().__init__((HOST, puerto), _Manejador)
        except OSError as exc:
            raise ErrorTransporte(
                f"No pude abrir el puerto {puerto}.\n"
                f"  Casi siempre es otro simulador que quedo abierto.\n"
                f"  Cerralo y volve a intentar.  ({exc})") from exc
        self.puerto = self.server_address[1]

    def arrancar_en_hilo(self) -> None:
        threading.Thread(target=self.serve_forever, daemon=True).start()
        if self.verboso:
            print(f"  [LOCAL] Escuchando en {HOST}:{self.puerto}")

    # ---------- ordenes ----------
    def despachar(self, pedido: dict) -> dict:
        orden = pedido.get("orden")
        metodo = getattr(self, f"_orden_{orden}", None)
        if metodo is None:
            return {"ok": False, "error": f"orden desconocida: {orden!r}"}
        return metodo(pedido)

    def _orden_hola(self, _pedido: dict) -> dict:
        """Saludo inicial. El cliente adopta de aca el robot y los limites."""
        p = self.perfil
        return {"ok": True,
                "robot": self.robot.clave,
                "nombre": self.robot.nombre,
                "materia": p.nombre,
                "limites": {"velocidad_max": p.velocidad_max,
                            "velocidad_angular_max": p.velocidad_angular_max,
                            "duracion_max": p.duracion_max,
                            "bateria_min": p.bateria_min}}

    def _orden_mover(self, pedido: dict) -> dict:
        # set_velocidad RECORTA en vez de rechazar, igual que por DDS: la
        # validacion que el alumno ve vive en robot.py, antes de mandar.
        self.mundo.set_velocidad(float(pedido.get("vx", 0.0)),
                                 float(pedido.get("vy", 0.0)),
                                 float(pedido.get("vyaw", 0.0)),
                                 float(pedido.get("duracion", 1.0)))
        return {"ok": True}

    def _orden_detener(self, _pedido: dict) -> dict:
        # Frenar es velocidad cero. NUNCA desenergizar ni cambiar la postura.
        self.mundo.detener()
        return {"ok": True}

    def _orden_gesto(self, pedido: dict) -> dict:
        nombre = pedido.get("nombre", "")
        from .acciones import exigir_permitida

        try:
            exigir_permitida(nombre, self.robot.clave)
        except Exception as exc:                              # noqa: BLE001
            # La lista blanca vive en acciones.py y es la MISMA que usa el
            # laboratorio fisico. Nada que cambie la postura pasa por aca.
            return {"ok": False, "error": str(exc)}
        self.mundo.gesto(nombre, float(pedido.get("duracion", 2.0)))
        return {"ok": True}

    def _orden_estado(self, _pedido: dict) -> dict:
        return {"ok": True, "estado": self.mundo.leer()}

    def _orden_telemetria(self, _pedido: dict) -> dict:
        """Lo usa el dashboard del TP05. Por DDS esto venia del LowState."""
        if self.telemetria is None:
            return {"ok": False, "error": "este simulador no publica telemetria"}
        return {"ok": True, "telemetria": self.telemetria()}


# ---------------------------------------------------------------------------
#  Cliente: vive en el proceso del alumno
# ---------------------------------------------------------------------------

class ClienteLocal:
    """Habla como el LocoClient/SportClient del SDK, pero por socket.

    Los nombres de los metodos son los del SDK a proposito. `robot.py` llama a
    `self._cliente.Move(...)` sin saber si abajo hay DDS o un socket, asi que
    el codigo del alumno y el del laboratorio fisico son el mismo.
    """

    def __init__(self, host: str = HOST, puerto: int = PUERTO,
                 timeout: float = 5.0):
        self.host, self.puerto = host, puerto
        self._timeout = timeout
        self._sock = None
        self._archivo = None
        self._lock = threading.Lock()
        self.info: dict = {}

    # ---------- conexion ----------
    def Init(self) -> None:
        try:
            self._sock = socket.create_connection((self.host, self.puerto),
                                                  timeout=self._timeout)
        except OSError as exc:
            raise ErrorTransporte(
                f"No pude conectarme al simulador en {self.host}:{self.puerto}.\n"
                f"  ({exc})") from exc
        self._sock.settimeout(self._timeout)
        self._archivo = self._sock.makefile("rwb")
        self.info = self._pedir({"orden": "hola"})

    def SetTimeout(self, segundos: float) -> None:
        self._timeout = float(segundos)
        if self._sock is not None:
            self._sock.settimeout(self._timeout)

    def Cerrar(self) -> None:
        for recurso in (self._archivo, self._sock):
            try:
                if recurso is not None:
                    recurso.close()
            except OSError:
                pass
        self._archivo = self._sock = None

    # ---------- ida y vuelta ----------
    def _pedir(self, pedido: dict) -> dict:
        if self._archivo is None:
            raise ErrorTransporte("El cliente no esta conectado.")
        with self._lock:
            try:
                self._archivo.write(json.dumps(pedido).encode("utf-8") + _FIN)
                self._archivo.flush()
                linea = self._archivo.readline()
            except OSError as exc:
                raise ErrorTransporte(
                    f"Se corto la conexion con el simulador ({exc}). "
                    f"Fijate que la ventana siga abierta.") from exc
        if not linea:
            raise ErrorTransporte(
                "El simulador cerro la conexion. Fijate que la ventana siga "
                "abierta y volve a ejecutar tu programa.")
        try:
            return json.loads(linea.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ErrorTransporte(f"Respuesta ilegible del simulador: {exc}")

    def _codigo(self, respuesta: dict) -> int:
        """0 si salio bien, distinto de 0 si no. Como los codigos del SDK."""
        return 0 if respuesta.get("ok") else 1

    # ---------- metodos con forma de SDK ----------
    def Move(self, vx: float, vy: float, vyaw: float, duracion: float = 1.0) -> int:
        return self._codigo(self._pedir({"orden": "mover", "vx": vx, "vy": vy,
                                         "vyaw": vyaw, "duracion": duracion}))

    def StopMove(self) -> int:
        return self._codigo(self._pedir({"orden": "detener"}))

    def WaveHand(self) -> int:
        return self._codigo(self._pedir({"orden": "gesto", "nombre": "saludo"}))

    def ShakeHand(self) -> int:
        return self._codigo(self._pedir({"orden": "gesto",
                                         "nombre": "dar_la_mano"}))

    def Estado(self) -> dict:
        return self._pedir({"orden": "estado"}).get("estado", {})

    def Telemetria(self) -> dict:
        return self._pedir({"orden": "telemetria"}).get("telemetria", {})

    # El chequeo de "el servicio responde de verdad" que hace robot.py. Con
    # DDS habia que usar GetFsmId/StandUp porque Move() descarta el codigo;
    # aca alcanza con el saludo, que si devuelve respuesta.
    def GetFsmId(self):
        return self._codigo(self._pedir({"orden": "hola"})), 0

    def StandUp(self) -> int:
        return self._codigo(self._pedir({"orden": "hola"}))
