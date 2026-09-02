"""Verifica que todo este instalado ANTES de abrir el simulador.

Filosofia: el alumno y el docente no tienen que configurar nada. Si falta algo,
lo instalamos; si no podemos, decimos exactamente que hacer en una linea.

Nunca dejamos que el simulador arranque a medias: es peor un simulador que abre
y falla raro a los dos minutos que uno que no abre y explica por que.
"""

from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys

# El repo oficial de Unitree. De aca salen los modelos y el bridge DDS.
REPO_OFICIAL = "https://github.com/unitreerobotics/unitree_mujoco"

def _ubicaciones_repo() -> list[str]:
    """Donde buscamos el simulador oficial, en orden de preferencia.

    Incluye rutas relativas al arbol de UadeRobotLab, porque la carpeta del
    laboratorio vive en 05LaboratoriosTPs/ y el simulador en 04Simuladores/.
    Asi el paquete se puede mover sin romper nada.
    """
    aqui = os.path.dirname(os.path.abspath(__file__))
    # PRIMERO el que viene DENTRO del paquete. Es el caso normal para un
    # profesor o un alumno: baja la carpeta de su TP y adentro esta todo lo que
    # necesita, sin git, sin internet y sin depender de donde quedo instalado
    # nada. Va primero para que el resultado no dependa de la maquina.
    rutas = [os.path.join(aqui, "unitree_mujoco")]
    # Subimos buscando el arbol de UadeRobotLab.
    d = aqui
    for _ in range(6):
        d = os.path.dirname(d)
        if not d or d == os.path.sep:
            break
        rutas.append(os.path.join(d, "04Simuladores", "UnitreeMujocoOficial",
                                  "unitree_mujoco"))
        rutas.append(os.path.join(d, "04Simuladores", "unitree_mujoco"))
    rutas += [
        os.path.expanduser("~/unitree_libs/unitree_mujoco"),
        os.path.expanduser("~/unitree_mujoco"),
        os.path.join(os.getcwd(), "unitree_mujoco"),
    ]
    return rutas


UBICACIONES_REPO = _ubicaciones_repo()

VERDE, ROJO, AMARILLO, GRIS, FIN = "\033[92m", "\033[91m", "\033[93m", "\033[90m", "\033[0m"

if os.name == "nt" or not sys.stdout.isatty():
    VERDE = ROJO = AMARILLO = GRIS = FIN = ""


class Resultado:
    def __init__(self):
        self.problemas: list[str] = []
        self.repo: str | None = None

    @property
    def todo_bien(self) -> bool:
        return not self.problemas


def _ok(texto: str, detalle: str = "") -> None:
    print(f"  {VERDE}[OK]{FIN}    {texto}" + (f" {GRIS}{detalle}{FIN}" if detalle else ""))


def _falta(texto: str, detalle: str = "") -> None:
    print(f"  {ROJO}[FALTA]{FIN} {texto}" + (f" {GRIS}{detalle}{FIN}" if detalle else ""))


def _arreglando(texto: str) -> None:
    print(f"  {AMARILLO}[...]{FIN}   {texto}")


def buscar_repo_oficial() -> str | None:
    """Devuelve la carpeta del repo oficial si tiene lo que necesitamos."""
    for base in UBICACIONES_REPO:
        modelos = os.path.join(base, "unitree_robots")
        bridge = os.path.join(base, "simulate_python", "unitree_sdk2py_bridge.py")
        if os.path.isdir(modelos) and os.path.isfile(bridge):
            return base
    return None


def _pip_install(paquete: str) -> bool:
    """Instala con pip. --trusted-host porque las redes de la facultad
    interceptan certificados SSL y rompen pip."""
    cmd = [sys.executable, "-m", "pip", "install", "--user", paquete,
           "--trusted-host", "pypi.org", "--trusted-host", "files.pythonhosted.org"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return r.returncode == 0
    except Exception:
        return False


def _tiene(modulo: str) -> bool:
    try:
        importlib.import_module(modulo)
        return True
    except Exception:
        return False


# Las tres DLL que MuJoCo necesita en Windows y que NO vienen con Python.
# Son parte del Visual C++ Redistributable de Microsoft.
_DLLS_WINDOWS = ("vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll")
_URL_VCREDIST = "https://aka.ms/vs/17/release/vc_redist.x64.exe"


def _faltan_dlls_windows() -> list[str]:
    """Cuales de las DLL de Microsoft faltan. Vacio si estan todas o no es Windows."""
    if os.name != "nt":
        return []
    import ctypes.util

    faltantes = []
    for dll in _DLLS_WINDOWS:
        if ctypes.util.find_library(dll) is None and not os.path.exists(
                os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                             "System32", dll)):
            faltantes.append(dll)
    return faltantes


def diagnosticar_mujoco() -> tuple[bool, str]:
    """Dice si MuJoCo se puede importar y, si no, POR QUE.

    Existe porque `_tiene()` se traga la excepcion, y eso hacia un diagnostico
    directamente falso: en Windows sin el Visual C++ Redistributable, `pip
    install mujoco` termina **bien** pero `import mujoco` falla al cargar la
    DLL. El chequeo decia "falta MuJoCo", intentaba instalarlo de nuevo -- pip
    contestaba que ya estaba --, y volvia a decir que faltaba. Un profesor
    perdio una tarde con eso.
    """
    try:
        importlib.import_module("mujoco")
        return True, ""
    except ImportError as exc:
        texto = str(exc)
        faltan = _faltan_dlls_windows()
        # "DLL load failed" es el sintoma clasico del redistribuible ausente.
        if faltan or "DLL load failed" in texto:
            detalle = ", ".join(faltan) if faltan else "las DLL de Microsoft"
            return False, (
                f"MuJoCo ESTA instalado, pero no puede cargarse: falta el\n"
                f"      Microsoft Visual C++ Redistributable ({detalle}).\n"
                f"      No viene con Python ni con MuJoCo; se instala aparte:\n"
                f"        {_URL_VCREDIST}\n"
                f"      Despues de instalarlo, cerra y volve a abrir la consola.")
        return False, f"No se pudo importar MuJoCo: {texto}"
    except Exception as exc:                                   # noqa: BLE001
        return False, f"No se pudo importar MuJoCo: {exc}"


def verificar(instalar: bool = True, extras: tuple[str, ...] = (),
              dds: bool = False) -> Resultado:
    """Revisa el entorno. `extras` son librerias que pide una materia puntual.

    El TP04 necesita FastAPI y uvicorn para levantar su backend; los demas TPs
    no. Se piden solo donde hacen falta, para no engordar la instalacion de
    todos por una materia.

    `dds=True` pide ademas CycloneDDS y el SDK de Unitree. Va apagado por
    defecto y a proposito: son las dos piezas que NO se pueden instalar en
    macOS ni en Windows, y el paquete que se reparte no las usa. Ver la
    cabecera de `local.py`.
    """
    r = Resultado()
    print()
    print("  Revisando que este todo listo...")
    print()

    # 1. Python
    v = sys.version_info
    if v >= (3, 8):
        _ok(f"Python {v.major}.{v.minor}.{v.micro}")
    else:
        _falta(f"Python {v.major}.{v.minor}", "hace falta 3.8 o mas nuevo")
        r.problemas.append(
            "Tu Python es muy viejo. Instala uno nuevo desde https://python.org")

    # 2. MuJoCo (la ventana 3D)
    ok_mujoco, porque = diagnosticar_mujoco()
    if ok_mujoco:
        import mujoco
        _ok("MuJoCo", f"v{mujoco.__version__}")
    elif "Visual C++" in porque:
        # Reinstalar no arregla nada: el paquete ya esta. Lo que falta es una
        # dependencia del sistema operativo.
        _falta("MuJoCo", "instalado pero no carga")
        r.problemas.append(porque)
    elif instalar:
        _arreglando("Instalando MuJoCo (la ventana 3D)... puede tardar un minuto")
        _pip_install("mujoco")
        ok_mujoco, porque = diagnosticar_mujoco()
        if ok_mujoco:
            _ok("MuJoCo instalado")
        else:
            _falta("MuJoCo")
            r.problemas.append(
                porque if "Visual C++" in porque else
                f"No pude instalar MuJoCo. Proba a mano:\n"
                f"      {sys.executable} -m pip install --user mujoco")
    else:
        _falta("MuJoCo")
        r.problemas.append(porque or "Falta MuJoCo.")

    # 3 y 4. CycloneDDS y el SDK de Unitree: SOLO en modo --dds.
    #
    # El paquete normal no los usa, y es deliberado: CycloneDDS 0.10.2 solo
    # publica wheels hasta cp310 (con 3.11+ pip intenta compilar y falla), y
    # `unitree_sdk2py` resuelve `timerfd_create` por ctypes al importar, que es
    # una syscall de Linux. En macOS y Windows no hay forma. Pedirlos a todo el
    # mundo era regalarle a cada profesor una tarde de pelea con pip.
    if dds:
        if _tiene("cyclonedds"):
            _ok("CycloneDDS")
        elif instalar and v < (3, 11):
            _arreglando("Instalando CycloneDDS (modo --dds)...")
            if _pip_install("cyclonedds==0.10.2") and _tiene("cyclonedds"):
                _ok("CycloneDDS instalado")
            else:
                _falta("CycloneDDS")
                r.problemas.append(
                    "No pude instalar CycloneDDS 0.10.2.\n"
                    f"      Proba: {sys.executable} -m pip install --user "
                    f"cyclonedds==0.10.2")
        else:
            _falta("CycloneDDS")
            r.problemas.append(
                "Falta CycloneDDS y no se puede instalar en este Python.\n"
                f"      Tenes {v.major}.{v.minor} y la 0.10.2 solo tiene wheels\n"
                "      hasta 3.10. El modo --dds necesita Python 3.10 y Linux.\n"
                "      Sin --dds, el simulador anda igual y no hace falta nada "
                "de esto.")

        if _tiene("unitree_sdk2py"):
            _ok("SDK de Unitree (unitree_sdk2py)")
        else:
            _falta("SDK de Unitree")
            r.problemas.append(
                "Falta el SDK de Unitree. Se instala con:\n"
                "      git clone https://github.com/unitreerobotics/"
                "unitree_sdk2_python\n"
                f"      {sys.executable} -m pip install --user -e "
                f"unitree_sdk2_python")

        # El bridge oficial importa pygame incondicionalmente, aunque no haya
        # joystick. Sin esto el import explota y el error no dice por que.
        if _tiene("pygame"):
            _ok("pygame", "lo pide el bridge oficial de Unitree")
        elif instalar:
            _arreglando("Instalando pygame (lo pide el bridge oficial)...")
            if _pip_install("pygame") and _tiene("pygame"):
                _ok("pygame instalado")
            else:
                _falta("pygame")
                r.problemas.append(
                    f"Falta pygame. Proba: {sys.executable} -m pip install "
                    f"--user pygame")
        else:
            _falta("pygame", "lo pide el bridge oficial de Unitree")
            r.problemas.append("Falta pygame.")

    # 4b. Librerias que pide la materia (TP04: el backend)
    for paquete, para_que in extras:
        modulo = paquete.split("==")[0].replace("-", "_")
        if _tiene(modulo):
            _ok(f"{paquete.split('==')[0]}", para_que)
        elif instalar:
            _arreglando(f"Instalando {paquete.split('==')[0]} ({para_que})...")
            if _pip_install(paquete) and _tiene(modulo):
                _ok(f"{paquete.split('==')[0]} instalado")
            else:
                _falta(paquete.split("==")[0])
                r.problemas.append(
                    f"No pude instalar {paquete}. Proba a mano:\n"
                    f"      {sys.executable} -m pip install --user {paquete}")
        else:
            _falta(paquete.split("==")[0], para_que)
            r.problemas.append(f"Falta {paquete} ({para_que}).")

    # 5. Los modelos oficiales. Vienen DENTRO del paquete: normalmente esto no
    # hace nada. El git clone queda como red de seguridad por si alguien corre
    # el nucleo fuera de un paquete armado.
    repo = buscar_repo_oficial()
    if repo:
        _ok("Modelos oficiales de Unitree", repo)
        r.repo = repo
    elif instalar and shutil.which("git"):
        destino = UBICACIONES_REPO[0]
        _arreglando(f"Descargando el simulador oficial en {destino}...")
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        try:
            p = subprocess.run(["git", "clone", "--depth", "1", REPO_OFICIAL, destino],
                               capture_output=True, text=True, timeout=900)
            repo = buscar_repo_oficial()
            if repo:
                _ok("Simulador oficial descargado", repo)
                r.repo = repo
            else:
                _falta("Simulador oficial", p.stderr.strip().splitlines()[-1:] and
                       p.stderr.strip().splitlines()[-1] or "")
                r.problemas.append(
                    f"No pude descargar el simulador oficial. Proba a mano:\n"
                    f"      git clone {REPO_OFICIAL} {destino}")
        except Exception as exc:
            _falta("Simulador oficial", str(exc))
            r.problemas.append(f"git clone {REPO_OFICIAL} {destino}")
    else:
        _falta("Simulador oficial de Unitree")
        r.problemas.append(
            f"Falta el simulador oficial. Descargalo con:\n"
            f"      git clone {REPO_OFICIAL} {UBICACIONES_REPO[0]}"
            + ("" if shutil.which("git") else
               "\n      (primero instala git: https://git-scm.com)"))

    return r


def informar(r: Resultado) -> bool:
    print()
    if r.todo_bien:
        print(f"  {VERDE}Todo listo.{FIN}")
        print()
        return True

    print("  " + "=" * 58)
    print(f"  {ROJO}FALTAN COSAS PARA PODER ABRIR EL SIMULADOR{FIN}")
    print("  " + "=" * 58)
    print()
    for i, p in enumerate(r.problemas, 1):
        print(f"  {i}. {p}")
        print()
    print("  Si no podes resolverlo, avisale al profesor.")
    print("  " + "=" * 58)
    print()
    return False


if __name__ == "__main__":
    sin_instalar = "--solo-revisar" in sys.argv
    raise SystemExit(0 if informar(verificar(instalar=not sin_instalar)) else 1)
