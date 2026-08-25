# =====================================================================
#  Ejecutor. ESTE ARCHIVO TE LO DAMOS HECHO.
#
#  Es la ultima etapa del pipeline: recibe la intencion ya clasificada y
#  validada, y la manda al robot.
#
#  ACA ES DONDE SE CONVIERTE A VELOCIDAD Y TIEMPO.
#
#  Tu clasificador y tu extractor trabajan en las unidades en que habla
#  la gente: metros y grados. Esta bien, eso es lenguaje natural. Pero al
#  robot NUNCA le llega un metro ni un grado: le llegan velocidad y
#  tiempo, que es como piensa el SDK.
#
#      "avanza 2 metros"  a 0.2 m/s  ->  avanzar(0.2, 10 s)
#      "gira 90 grados"   a 0.5 rad/s ->  girar(0.5, 3.14 s)
#
#  Y como hay un tope de tiempo por orden, un movimiento largo se PARTE
#  en tramos. "avanza 2 metros" con tope de 5 s sale como dos ordenes de
#  5 s, no como una de 10. El robot recorre lo mismo; simplemente ninguna
#  orden individual supera el limite.
# =====================================================================

import math
import sys
from pathlib import Path

_ENTORNO = Path(__file__).resolve().parent.parent / "entorno"
if str(_ENTORNO) not in sys.path:
    sys.path.insert(0, str(_ENTORNO))

try:
    from sim.safety import ErrorDeSeguridad
except ImportError:      # permite leer y probar este archivo suelto
    class ErrorDeSeguridad(ValueError):
        pass


def partir_en_tramos(tiempo_total, tope):
    """Divide un tiempo largo en tramos que no superen el tope.

    Devuelve una lista de duraciones que suman exactamente tiempo_total.
    """
    if tiempo_total <= tope:
        return [tiempo_total]
    tramos = []
    restante = float(tiempo_total)
    while restante > tope + 1e-9:
        tramos.append(tope)
        restante -= tope
    if restante > 1e-9:
        tramos.append(restante)
    return tramos


class Ejecutor:
    """Traduce intenciones a movimientos del robot."""

    def __init__(self, robot, mostrar=True):
        self.robot = robot
        self.mostrar = mostrar
        self.perfil = robot.perfil

    # ---------- lo que usa el agente ----------
    def ejecutar(self, tipo, parametros):
        """Manda la intencion al robot. Devuelve un texto con lo que paso."""
        parametros = parametros or {}
        try:
            if tipo == "MOVER":
                return self._mover(parametros)
            if tipo == "GIRAR":
                return self._girar(parametros)
            if tipo == "DETENERSE":
                self.robot.detenerse()
                return "detenido"
            if tipo == "SALUDO":
                self.robot.saludar()
                return "saludo"
            if tipo == "CONSULTAR_ESTADO":
                e = self.robot.verificar_estado()
                return f"estado: {e}"
        except ErrorDeSeguridad as exc:
            # Ultima red: si algo llego hasta aca fuera de limite, el robot lo
            # rechaza igual. Que pase significa que el validador dejo pasar
            # algo que no debia.
            return f"RECHAZADO POR EL ROBOT: {exc}"
        return f"no se como ejecutar {tipo}"

    # ---------- conversion a velocidad y tiempo ----------
    def _mover(self, p):
        # La gente habla en metros; el robot entiende velocidad y tiempo.
        distancia = float(p.get("distancia_m", 0.5))
        velocidad = float(p.get("velocidad_ms", self.perfil.velocidad_max))
        velocidad = min(abs(velocidad), self.perfil.velocidad_max)
        if velocidad <= 0:
            return "velocidad cero: no hay nada que ejecutar"

        signo = -1.0 if p.get("direccion") == "atras" else 1.0
        tiempo_total = abs(distancia) / velocidad
        tramos = partir_en_tramos(tiempo_total, self.perfil.duracion_max)

        self._log(f"{distancia:g} m a {velocidad:g} m/s = {tiempo_total:.2f} s"
                  + (f", partido en {len(tramos)} tramos" if len(tramos) > 1 else ""))
        for i, t in enumerate(tramos, 1):
            self._log(f"  tramo {i}/{len(tramos)}: avanzar({signo * velocidad:+.2f}, {t:.2f})")
            self.robot.avanzar(velocidad=signo * velocidad, tiempo=t)
        return f"avanzo {distancia:g} m en {len(tramos)} orden(es)"

    def _girar(self, p):
        # La gente habla en grados; el robot entiende velocidad y tiempo.
        grados = float(p.get("angulo_deg", 90))
        velocidad = float(p.get("velocidad_giro", self.perfil.velocidad_angular_max))
        velocidad = min(abs(velocidad), self.perfil.velocidad_angular_max)
        if velocidad <= 0:
            return "velocidad de giro cero"

        # El SIGNO marca el sentido: positivo izquierda, negativo derecha.
        signo = -1.0 if p.get("direccion") == "derecha" else 1.0
        radianes = math.radians(abs(grados))
        tiempo_total = radianes / velocidad
        tramos = partir_en_tramos(tiempo_total, self.perfil.duracion_max)

        lado = "derecha" if signo < 0 else "izquierda"
        self._log(f"{grados:g} grados = {radianes:.4f} rad a la {lado}, "
                  f"a {velocidad:g} rad/s = {tiempo_total:.2f} s"
                  + (f", partido en {len(tramos)} tramos" if len(tramos) > 1 else ""))
        for i, t in enumerate(tramos, 1):
            self._log(f"  tramo {i}/{len(tramos)}: girar({signo * velocidad:+.2f}, {t:.2f})")
            self.robot.girar(velocidad=signo * velocidad, tiempo=t)
        return f"giro {grados:g} grados a la {lado} en {len(tramos)} orden(es)"

    def _log(self, texto):
        if self.mostrar:
            print(f"      [EJECUTOR] {texto}")
