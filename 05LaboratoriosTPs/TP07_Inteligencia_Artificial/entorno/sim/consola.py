"""La vista del simulador cuando NO se puede abrir la ventana 3D.

Por que existe
--------------
En una maquina virtual sin GPU, o por escritorio remoto, MuJoCo no puede crear
la ventana: `WGL: The driver does not appear to support OpenGL`. El simulador
cae a modo consola y sigue funcionando.

Pero hasta ahora "modo consola" no mostraba **nada**: la ventana del simulador
quedaba muda para siempre mientras el robot se movia. El alumno veia su propio
programa imprimir "Avanzando..." y del otro lado, silencio. Para el TP01 --
primer contacto, la materia mas visual de todas -- eso es una pantalla negra.

Asi que se dibuja el recorrido en texto. No reemplaza a la ventana 3D, pero
alcanza para lo que el TP evalua: el alumno **ve el cuadrado que programo**.

    +----------------------------------+
    |                                  |
    |     . . . . . . . . . .          |
    |     .                 .          |
    |     .                 .          |
    |     o . . . . . . . >            |
    |                                  |
    +----------------------------------+
      x=+0.40 m   y=+0.40 m   rumbo=+90 deg   [avanzando]

`o` es donde arranco, `.` por donde paso y la flecha es hacia donde mira ahora.
"""

from __future__ import annotations

import math
import os
import shutil
import time

# Flechas por rumbo, cada 45 grados. La primera es el ESTE (yaw = 0).
_FLECHAS = (">", "/", "^", "\\", "<", "/", "v", "\\")

# Cada cuanto se redibuja. Mas rapido no aporta y llena la consola de basura en
# las terminales que no soportan borrar la pantalla.
_PERIODO = 0.25

# Cuantas posiciones se recuerdan del recorrido.
_MAX_RASTRO = 4000


def _flecha(yaw: float) -> str:
    sector = int(round((math.degrees(yaw) % 360) / 45.0)) % 8
    return _FLECHAS[sector]


class VistaConsola:
    """Dibuja el recorrido del robot en la terminal."""

    def __init__(self, ancho: int | None = None, alto: int | None = None,
                 verboso: bool = True):
        medida = shutil.get_terminal_size((80, 24))
        self.ancho = ancho or max(32, min(72, medida.columns - 8))
        self.alto = alto or max(9, min(20, medida.lines - 10))
        self.verboso = verboso
        self.rastro: list[tuple[float, float]] = []
        self._ultimo_dibujo = 0.0
        self._ultima_clave = None
        # No todas las consolas entienden los codigos para borrar la pantalla.
        # En Windows los soporta desde Windows 10; si algo falla, se degrada a
        # imprimir una linea por vez, que es feo pero nunca deja basura.
        self._puede_borrar = os.environ.get("TERM") != "dumb"

    # ---------- API ----------
    def actualizar(self, estado: dict) -> None:
        """Lo llama el bucle del simulador en cada paso."""
        x, y = float(estado.get("x", 0.0)), float(estado.get("y", 0.0))
        if not self.rastro or _lejos(self.rastro[-1], (x, y)):
            self.rastro.append((x, y))
            if len(self.rastro) > _MAX_RASTRO:
                # Se descarta uno de cada dos: el recorrido se sigue viendo
                # igual y la memoria no crece sin limite en una clase larga.
                self.rastro = self.rastro[::2]

        ahora = time.monotonic()
        if ahora - self._ultimo_dibujo < _PERIODO:
            return

        clave = (round(x, 2), round(y, 2), round(estado.get("yaw", 0.0), 2),
                 estado.get("accion"))
        if clave == self._ultima_clave:
            return          # nada cambio: no se redibuja

        self._ultimo_dibujo = ahora
        self._ultima_clave = clave
        self.dibujar(estado)

    def dibujar(self, estado: dict) -> None:
        lienzo = self._pintar(estado)
        if self._puede_borrar:
            print("\033[2J\033[H", end="")
        print("\n".join(lienzo))

    # ---------- dibujo ----------
    def _limites(self) -> tuple[float, float, float, float]:
        """La ventana del mundo que se muestra, siempre cuadrada.

        Si no fuera cuadrada, un cuadrado de 0.40 m de lado se veria como un
        rectangulo y el alumno pensaria que su programa esta mal.
        """
        xs = [p[0] for p in self.rastro] or [0.0]
        ys = [p[1] for p in self.rastro] or [0.0]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        lado = max(max(xs) - min(xs), max(ys) - min(ys), 0.6) * 1.25
        mitad = lado / 2
        return cx - mitad, cx + mitad, cy - mitad, cy + mitad

    def _celda(self, x: float, y: float, lim) -> tuple[int, int] | None:
        x0, x1, y0, y1 = lim
        if x1 - x0 <= 0 or y1 - y0 <= 0:
            return None
        # La Y del mundo crece hacia arriba y la fila de la consola hacia
        # abajo: por eso se invierte.
        col = int((x - x0) / (x1 - x0) * (self.ancho - 1))
        fila = int((y1 - y) / (y1 - y0) * (self.alto - 1))
        if 0 <= col < self.ancho and 0 <= fila < self.alto:
            return fila, col
        return None

    def _pintar(self, estado: dict) -> list[str]:
        lim = self._limites()
        grilla = [[" "] * self.ancho for _ in range(self.alto)]

        for punto in self.rastro:
            celda = self._celda(punto[0], punto[1], lim)
            if celda:
                grilla[celda[0]][celda[1]] = "."

        if self.rastro:
            inicio = self._celda(self.rastro[0][0], self.rastro[0][1], lim)
            if inicio:
                grilla[inicio[0]][inicio[1]] = "o"

        x, y = float(estado.get("x", 0.0)), float(estado.get("y", 0.0))
        actual = self._celda(x, y, lim)
        if actual:
            grilla[actual[0]][actual[1]] = _flecha(float(estado.get("yaw", 0.0)))

        borde = "+" + "-" * self.ancho + "+"
        lineas = [borde]
        lineas += ["|" + "".join(fila) + "|" for fila in grilla]
        lineas.append(borde)

        grados = math.degrees(float(estado.get("yaw", 0.0)))
        bateria = estado.get("bateria")

        # El pie se arma por partes y se acomoda al ancho del marco. Si se
        # imprimiera de una, en una consola angosta lo parte la terminal por
        # donde quiere y el dibujo queda desalineado.
        datos = [f"x={x:+.2f} m", f"y={y:+.2f} m", f"rumbo={grados:+.0f} deg",
                 f"[{estado.get('accion', 'quieto')}]"]
        if bateria is not None:
            datos.append(f"bateria {bateria}%")
        datos.append(f"recorrido {self._distancia():.2f} m")
        lineas += _acomodar(datos, len(borde))
        lineas.append("  (sin ventana 3D: el recorrido se dibuja en texto)"
                      [:len(borde)])
        return lineas

    def _distancia(self) -> float:
        return sum(math.dist(a, b)
                   for a, b in zip(self.rastro, self.rastro[1:]))


def _acomodar(datos: list[str], ancho: int) -> list[str]:
    """Reparte los datos en las lineas que hagan falta, sin pasarse del marco."""
    lineas: list[str] = []
    actual = " "
    for dato in datos:
        candidato = f"{actual}  {dato}" if actual.strip() else f"  {dato}"
        if len(candidato) > ancho and actual.strip():
            lineas.append(actual)
            actual = f"  {dato}"
        else:
            actual = candidato
    if actual.strip():
        lineas.append(actual)
    return lineas


def _lejos(a: tuple[float, float], b: tuple[float, float]) -> bool:
    """Solo se guarda un punto si el robot se movio de verdad.

    Sin esto el rastro guarda miles de puntos identicos mientras el robot esta
    quieto, y el recorrido calculado se llena de ruido.
    """
    return math.dist(a, b) > 0.005
