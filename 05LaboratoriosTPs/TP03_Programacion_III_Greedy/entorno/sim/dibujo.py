"""Dibuja la grilla del TP03 en la ventana 3D.

Usa `viewer.user_scn`, que permite agregar geometrias en vivo SIN tocar la
escena oficial de Unitree. Nada de generar XML ni de modificar el modelo:
la escena oficial se carga tal cual y la grilla se superpone.

Sin esto el alumno ve al robot moverse sobre un piso vacio y no puede saber si
esquivo el obstaculo o lo atraveso.
"""

from __future__ import annotations

import numpy as np

# Colores (RGBA). Pensados para que se distingan tambien en captura de pantalla.
COLOR_LIBRE = np.array([0.86, 0.88, 0.91, 0.35], dtype=np.float32)
COLOR_OBSTACULO = np.array([0.72, 0.18, 0.18, 0.90], dtype=np.float32)
COLOR_PROHIBIDA = np.array([0.85, 0.65, 0.10, 0.70], dtype=np.float32)
COLOR_INICIO = np.array([0.20, 0.65, 0.32, 0.75], dtype=np.float32)
COLOR_DESTINO = np.array([0.15, 0.45, 0.85, 0.75], dtype=np.float32)
COLOR_RUTA = np.array([0.95, 0.75, 0.10, 0.95], dtype=np.float32)

ALTURA_PISO = 0.005      # las baldosas, casi al ras
ALTURA_OBSTACULO = 0.35  # los obstaculos, visibles pero sin tapar al robot
IDENTIDAD = np.eye(3).flatten()


def dibujar(user_scn, mapa, mostrar_ruta: bool = True) -> int:
    """Vuelca la grilla en la escena del visor. Devuelve cuantos geoms uso."""
    import mujoco

    n = 0
    media = mapa.tamano_celda / 2.0

    def _geom(tipo, tamano, pos, color):
        nonlocal n
        if n >= user_scn.maxgeom:
            return
        mujoco.mjv_initGeom(
            user_scn.geoms[n], tipo,
            np.array(tamano, dtype=np.float64),
            np.array(pos, dtype=np.float64),
            IDENTIDAD, color)
        n += 1

    for fila in range(mapa.filas):
        for columna in range(mapa.columnas):
            x, y = mapa.a_mundo(fila, columna)
            valor = mapa.celda(fila, columna)

            if valor == 1:      # obstaculo: caja alta
                _geom(mujoco.mjtGeom.mjGEOM_BOX,
                      [media * 0.92, media * 0.92, ALTURA_OBSTACULO / 2],
                      [x, y, ALTURA_OBSTACULO / 2], COLOR_OBSTACULO)
                continue

            if valor == 2:      # zona prohibida: baldosa marcada, sin volumen
                color = COLOR_PROHIBIDA
            elif (fila, columna) == mapa.inicio:
                color = COLOR_INICIO
            elif (fila, columna) == mapa.destino:
                color = COLOR_DESTINO
            else:
                color = COLOR_LIBRE

            _geom(mujoco.mjtGeom.mjGEOM_BOX,
                  [media * 0.92, media * 0.92, ALTURA_PISO],
                  [x, y, ALTURA_PISO], color)

    # La ruta calculada, como esferas encadenadas sobre el piso.
    if mostrar_ruta and mapa.ruta:
        for fila, columna in mapa.ruta:
            x, y = mapa.a_mundo(int(fila), int(columna))
            _geom(mujoco.mjtGeom.mjGEOM_SPHERE,
                  [mapa.tamano_celda * 0.10] * 3, [x, y, 0.05], COLOR_RUTA)

    user_scn.ngeom = n
    return n
