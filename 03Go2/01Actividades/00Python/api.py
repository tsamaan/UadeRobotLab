"""
=============================================================
  Unitree Go2 — API Flask
  Controlá el robot por HTTP desde cualquier dispositivo
  en la misma red.
=============================================================
  Uso:
    python3 api.py [interfaz_de_red]
    python3 api.py enp0s31f6

  Endpoints disponibles:
    POST /connect              → Conectar al robot
    POST /disconnect           → Llevar a reposo y desconectar

    -- Postura --
    POST /stand_up             → Pararse
    POST /stand_down           → Acostarse
    POST /sit                  → Sentarse
    POST /rise_sit             → Levantarse desde sentado
    POST /balance_stand        → Modo balance
    POST /damp                 → Amortiguación (reposo)
    POST /recovery             → Recuperar postura
    POST /hand_stand           → Pararse en manos (body: {"enable": true/false})

    -- Movimiento --
    POST /move                 → Mover (body: {"x":0.3,"y":0,"yaw":0})
    POST /stop                 → Frenar
    POST /move_timed           → Mover por N segundos
                                 (body: {"x":0.3,"y":0,"yaw":0,"duration":2.0})

    -- Gestos --
    POST /hello                → Saludo
    POST /stretch              → Estirarse
    POST /heart                → Corazón
    POST /wallow               → Revolcarse

    -- Baile / Acrobacias --
    POST /dance1               → Baile 1
    POST /dance2               → Baile 2
    POST /front_jump           → Salto frontal
    POST /left_flip            → Voltereta izquierda
    POST /back_flip            → Voltereta atrás

    -- Modos especiales --
    POST /free_walk            → Modo caminata libre
    POST /free_bound           → Modo salto libre (body: {"enable": true/false})
    POST /free_avoid           → Modo evasión libre (body: {"enable": true/false})
    POST /walk_upright         → Caminar erguido  (body: {"enable": true/false})
    POST /cross_step           → Paso cruzado     (body: {"enable": true/false})
    POST /free_jump            → Salto libre      (body: {"enable": true/false})

    -- Rutinas completas --
    POST /rutina/arranque      → StandUp + BalanceStand
    POST /rutina/movimiento    → Avanzar, retroceder, girar
    POST /rutina/gestos        → Hello, Stretch, Heart
    POST /rutina/baile         → Dance1 + Dance2
    POST /rutina/demo_completo → Toda la demo

    -- Estado --
    GET  /status               → Estado actual del robot
    GET  /comandos             → Lista todos los endpoints
=============================================================
"""

import sys
import time
import threading
from flask import Flask, jsonify, request

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient

# ── Configuración ─────────────────────────────────────────
DEFAULT_INTERFACE = "enp0s31f6"
API_PORT          = 5000

app = Flask(__name__)

# ── Estado global ─────────────────────────────────────────
robot: SportClient | None = None
robot_lock   = threading.Lock()
estado_robot = {
    "conectado": False,
    "interfaz":  None,
    "ultimo_comando": None,
}


# ── Helpers ───────────────────────────────────────────────

def ok(msg: str, **extra):
    payload = {"ok": True, "mensaje": msg}
    payload.update(extra)
    return jsonify(payload), 200


def err(msg: str, code: int = 400):
    return jsonify({"ok": False, "error": msg}), code


def robot_requerido():
    """Devuelve None si el robot está conectado, o una respuesta de error."""
    if robot is None or not estado_robot["conectado"]:
        return err("Robot no conectado. Llamá primero a POST /connect.", 503)
    return None


def mover_por_tiempo(x: float, y: float, yaw: float, duracion: float):
    """Envía comandos Move en un loop durante `duracion` segundos."""
    inicio = time.time()
    while time.time() - inicio < duracion:
        robot.Move(x, y, yaw)
        time.sleep(0.05)
    robot.StopMove()


# ── Conexión ──────────────────────────────────────────────

@app.route("/connect", methods=["POST"])
def connect():
    global robot
    data      = request.get_json(silent=True) or {}
    interfaz  = data.get("interfaz", estado_robot["interfaz"] or DEFAULT_INTERFACE)

    with robot_lock:
        if estado_robot["conectado"]:
            return ok("Robot ya estaba conectado.", interfaz=interfaz)

        result = {"error": None}

        def _init():
            try:
                ChannelFactoryInitialize(0, interfaz)
                r = SportClient()
                r.SetTimeout(10.0)
                r.Init()
                result["client"] = r
            except Exception as e:
                result["error"] = str(e)

        t = threading.Thread(target=_init, daemon=True)
        t.start()
        t.join(timeout=12)

        if t.is_alive():
            return err("Timeout al conectar. Verificá que el robot esté encendido y en la red.", 504)
        if result.get("error"):
            return err(f"Error al conectar: {result['error']}", 500)

        robot = result["client"]
        estado_robot["conectado"] = True
        estado_robot["interfaz"]  = interfaz

    return ok("Robot conectado.", interfaz=interfaz)


@app.route("/disconnect", methods=["POST"])
def disconnect():
    global robot
    e = robot_requerido()
    if e:
        return e
    try:
        robot.StandDown()
        time.sleep(1.0)
        robot.Damp()
    except Exception:
        pass
    with robot_lock:
        robot = None
        estado_robot["conectado"]     = False
        estado_robot["ultimo_comando"] = "disconnect"
    return ok("Robot en reposo. Conexión cerrada.")


# ── Estado ────────────────────────────────────────────────

@app.route("/status", methods=["GET"])
def status():
    return jsonify(estado_robot), 200


@app.route("/comandos", methods=["GET"])
def comandos():
    rutas = [
        {"metodo": r.methods - {"HEAD", "OPTIONS"}, "ruta": r.rule}
        for r in app.url_map.iter_rules()
        if r.rule != "/static/<path:filename>"
    ]
    rutas.sort(key=lambda r: r["ruta"])
    return jsonify([{"ruta": r["ruta"], "metodos": list(r["metodo"])} for r in rutas]), 200


# ── Postura ───────────────────────────────────────────────

@app.route("/stand_up", methods=["POST"])
def stand_up():
    e = robot_requerido()
    if e: return e
    robot.StandUp()
    estado_robot["ultimo_comando"] = "stand_up"
    return ok("Parándose.")


@app.route("/stand_down", methods=["POST"])
def stand_down():
    e = robot_requerido()
    if e: return e
    robot.StandDown()
    estado_robot["ultimo_comando"] = "stand_down"
    return ok("Acostándose.")


@app.route("/sit", methods=["POST"])
def sit():
    e = robot_requerido()
    if e: return e
    robot.Sit()
    estado_robot["ultimo_comando"] = "sit"
    return ok("Sentándose.")


@app.route("/rise_sit", methods=["POST"])
def rise_sit():
    e = robot_requerido()
    if e: return e
    robot.RiseSit()
    estado_robot["ultimo_comando"] = "rise_sit"
    return ok("Levantándose desde sentado.")


@app.route("/balance_stand", methods=["POST"])
def balance_stand():
    e = robot_requerido()
    if e: return e
    robot.BalanceStand()
    estado_robot["ultimo_comando"] = "balance_stand"
    return ok("Modo balance activado.")


@app.route("/damp", methods=["POST"])
def damp():
    e = robot_requerido()
    if e: return e
    robot.Damp()
    estado_robot["ultimo_comando"] = "damp"
    return ok("Amortiguación activada (reposo).")


@app.route("/recovery", methods=["POST"])
def recovery():
    e = robot_requerido()
    if e: return e
    robot.RecoveryStand()
    estado_robot["ultimo_comando"] = "recovery"
    return ok("Recuperando postura.")


@app.route("/hand_stand", methods=["POST"])
def hand_stand():
    e = robot_requerido()
    if e: return e
    data   = request.get_json(silent=True) or {}
    enable = bool(data.get("enable", True))
    robot.HandStand(enable)
    if enable:
        time.sleep(4)
        robot.HandStand(False)
    estado_robot["ultimo_comando"] = f"hand_stand(enable={enable})"
    return ok(f"HandStand {'activado y desactivado' if enable else 'desactivado'}.")


# ── Movimiento ────────────────────────────────────────────

@app.route("/move", methods=["POST"])
def move():
    e = robot_requerido()
    if e: return e
    data = request.get_json(silent=True) or {}
    x    = float(data.get("x",   0.0))
    y    = float(data.get("y",   0.0))
    yaw  = float(data.get("yaw", 0.0))
    ret  = robot.Move(x, y, yaw)
    estado_robot["ultimo_comando"] = f"move(x={x}, y={y}, yaw={yaw})"
    return ok(f"Moviendo: x={x}, y={y}, yaw={yaw}.", ret=ret)


@app.route("/stop", methods=["POST"])
def stop():
    e = robot_requerido()
    if e: return e
    robot.StopMove()
    estado_robot["ultimo_comando"] = "stop"
    return ok("Detenido.")


@app.route("/move_timed", methods=["POST"])
def move_timed():
    e = robot_requerido()
    if e: return e
    data     = request.get_json(silent=True) or {}
    x        = float(data.get("x",        0.0))
    y        = float(data.get("y",        0.0))
    yaw      = float(data.get("yaw",      0.0))
    duration = float(data.get("duration", 1.0))
    if duration <= 0 or duration > 30:
        return err("'duration' debe ser un número entre 0 y 30 segundos.")
    mover_por_tiempo(x, y, yaw, duration)
    estado_robot["ultimo_comando"] = f"move_timed(x={x}, y={y}, yaw={yaw}, dur={duration})"
    return ok(f"Movido durante {duration}s: x={x}, y={y}, yaw={yaw}.")


# ── Gestos ────────────────────────────────────────────────

@app.route("/hello", methods=["POST"])
def hello():
    e = robot_requerido()
    if e: return e
    robot.Hello()
    estado_robot["ultimo_comando"] = "hello"
    return ok("Saludando.")


@app.route("/stretch", methods=["POST"])
def stretch():
    e = robot_requerido()
    if e: return e
    robot.Stretch()
    estado_robot["ultimo_comando"] = "stretch"
    return ok("Estirándose.")


@app.route("/heart", methods=["POST"])
def heart():
    e = robot_requerido()
    if e: return e
    robot.Heart()
    estado_robot["ultimo_comando"] = "heart"
    return ok("Haciendo corazón.")


@app.route("/wallow", methods=["POST"])
def wallow():
    e = robot_requerido()
    if e: return e
    robot.Wallow()
    estado_robot["ultimo_comando"] = "wallow"
    return ok("Revolcándose.")


# ── Baile / Acrobacias ────────────────────────────────────

@app.route("/dance1", methods=["POST"])
def dance1():
    e = robot_requerido()
    if e: return e
    robot.Dance1()
    estado_robot["ultimo_comando"] = "dance1"
    return ok("Baile 1.")


@app.route("/dance2", methods=["POST"])
def dance2():
    e = robot_requerido()
    if e: return e
    robot.Dance2()
    estado_robot["ultimo_comando"] = "dance2"
    return ok("Baile 2.")


@app.route("/front_jump", methods=["POST"])
def front_jump():
    e = robot_requerido()
    if e: return e
    robot.FrontJump()
    estado_robot["ultimo_comando"] = "front_jump"
    return ok("Salto frontal.")


@app.route("/left_flip", methods=["POST"])
def left_flip():
    e = robot_requerido()
    if e: return e
    ret = robot.LeftFlip()
    estado_robot["ultimo_comando"] = "left_flip"
    return ok("Voltereta izquierda.", ret=ret)


@app.route("/back_flip", methods=["POST"])
def back_flip():
    e = robot_requerido()
    if e: return e
    ret = robot.BackFlip()
    estado_robot["ultimo_comando"] = "back_flip"
    return ok("Voltereta atrás.", ret=ret)


# ── Modos especiales ──────────────────────────────────────

@app.route("/free_walk", methods=["POST"])
def free_walk():
    e = robot_requerido()
    if e: return e
    ret = robot.FreeWalk()
    estado_robot["ultimo_comando"] = "free_walk"
    return ok("Modo caminata libre.", ret=ret)


@app.route("/free_bound", methods=["POST"])
def free_bound():
    e = robot_requerido()
    if e: return e
    data   = request.get_json(silent=True) or {}
    enable = bool(data.get("enable", True))
    ret    = robot.FreeBound(enable)
    estado_robot["ultimo_comando"] = f"free_bound(enable={enable})"
    return ok(f"FreeBound {'activado' if enable else 'desactivado'}.", ret=ret)


@app.route("/free_avoid", methods=["POST"])
def free_avoid():
    e = robot_requerido()
    if e: return e
    data   = request.get_json(silent=True) or {}
    enable = bool(data.get("enable", True))
    ret    = robot.FreeAvoid(enable)
    estado_robot["ultimo_comando"] = f"free_avoid(enable={enable})"
    return ok(f"FreeAvoid {'activado' if enable else 'desactivado'}.", ret=ret)


@app.route("/walk_upright", methods=["POST"])
def walk_upright():
    e = robot_requerido()
    if e: return e
    data   = request.get_json(silent=True) or {}
    enable = bool(data.get("enable", True))
    ret    = robot.WalkUpright(enable)
    estado_robot["ultimo_comando"] = f"walk_upright(enable={enable})"
    return ok(f"WalkUpright {'activado' if enable else 'desactivado'}.", ret=ret)


@app.route("/cross_step", methods=["POST"])
def cross_step():
    e = robot_requerido()
    if e: return e
    data   = request.get_json(silent=True) or {}
    enable = bool(data.get("enable", True))
    ret    = robot.CrossStep(enable)
    estado_robot["ultimo_comando"] = f"cross_step(enable={enable})"
    return ok(f"CrossStep {'activado' if enable else 'desactivado'}.", ret=ret)


@app.route("/free_jump", methods=["POST"])
def free_jump():
    e = robot_requerido()
    if e: return e
    data   = request.get_json(silent=True) or {}
    enable = bool(data.get("enable", True))
    ret    = robot.FreeJump(enable)
    estado_robot["ultimo_comando"] = f"free_jump(enable={enable})"
    return ok(f"FreeJump {'activado' if enable else 'desactivado'}.", ret=ret)


# ── Rutinas ───────────────────────────────────────────────

@app.route("/rutina/arranque", methods=["POST"])
def rutina_arranque():
    e = robot_requerido()
    if e: return e
    robot.StandUp()
    time.sleep(2)
    robot.BalanceStand()
    time.sleep(1.5)
    estado_robot["ultimo_comando"] = "rutina_arranque"
    return ok("Rutina arranque completada: StandUp + BalanceStand.")


@app.route("/rutina/movimiento", methods=["POST"])
def rutina_movimiento():
    e = robot_requerido()
    if e: return e
    # Avanzar
    mover_por_tiempo(0.3, 0, 0, 2.0)
    time.sleep(0.8)
    # Retroceder
    mover_por_tiempo(-0.3, 0, 0, 1.5)
    time.sleep(0.8)
    # Girar
    mover_por_tiempo(0, 0, 0.6, 2.0)
    time.sleep(0.8)
    estado_robot["ultimo_comando"] = "rutina_movimiento"
    return ok("Rutina movimiento completada: avanzar, retroceder, girar.")


@app.route("/rutina/gestos", methods=["POST"])
def rutina_gestos():
    e = robot_requerido()
    if e: return e
    robot.Hello()
    time.sleep(3)
    robot.Stretch()
    time.sleep(3)
    robot.Heart()
    time.sleep(3)
    estado_robot["ultimo_comando"] = "rutina_gestos"
    return ok("Rutina gestos completada: Hello, Stretch, Heart.")


@app.route("/rutina/baile", methods=["POST"])
def rutina_baile():
    e = robot_requerido()
    if e: return e
    robot.Dance1()
    time.sleep(5)
    robot.Dance2()
    time.sleep(5)
    estado_robot["ultimo_comando"] = "rutina_baile"
    return ok("Rutina baile completada: Dance1 + Dance2.")


@app.route("/rutina/demo_completo", methods=["POST"])
def rutina_demo_completo():
    e = robot_requerido()
    if e: return e

    # Arranque
    robot.StandUp();      time.sleep(2)
    robot.BalanceStand(); time.sleep(1.5)

    # Movimiento
    mover_por_tiempo(0.3,  0,   0,   2.0); time.sleep(0.8)
    mover_por_tiempo(-0.3, 0,   0,   1.5); time.sleep(0.8)
    mover_por_tiempo(0,    0,   0.6, 2.0); time.sleep(0.8)

    # Gestos
    robot.Hello();   time.sleep(3)
    robot.Stretch(); time.sleep(3)
    robot.Heart();   time.sleep(3)

    # Baile
    robot.Dance1(); time.sleep(5)
    robot.Dance2(); time.sleep(5)

    # Sentarse/levantarse
    robot.Sit();     time.sleep(2)
    robot.RiseSit(); time.sleep(2)

    # Fin
    robot.StandDown(); time.sleep(1.5)
    robot.Damp()
    estado_robot["ultimo_comando"] = "rutina_demo_completo"
    return ok("Demo completa finalizada.")


# ── Main ───────────────────────────────────────────────────

if __name__ == "__main__":
    interfaz = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INTERFACE
    estado_robot["interfaz"] = interfaz

    print("=" * 55)
    print("  Unitree Go2 — API Flask")
    print("=" * 55)
    print(f"  Interfaz de red : {interfaz}")
    print(f"  Puerto          : {API_PORT}")
    print()
    print("  Conectá el robot con:  POST /connect")
    print(f"  API corriendo en:      http://0.0.0.0:{API_PORT}")
    print("=" * 55)

    app.run(host="0.0.0.0", port=API_PORT, debug=False)
