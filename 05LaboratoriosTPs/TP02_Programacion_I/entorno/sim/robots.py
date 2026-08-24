"""Los dos robots reales: donde esta su modelo oficial y como se anima cada uno.

Usamos los modelos OFICIALES de Unitree (repo unitreerobotics/unitree_mujoco),
no una figura inventada: el alumno tiene que ver el robot que despues va a usar.

El movimiento es CINEMATICO: escribimos la pose y llamamos mj_forward, sin
correr fisica. Es a proposito:

  - El G1 es un humanoide y SE CAE SOLO sin un controlador de locomocion. El
    simulador oficial no trae ese controlador (vive en la PC interna del robot
    y Unitree no lo publica). Con fisica real, el robot se desploma antes de
    que el alumno pueda probar nada.
  - Un TP de programacion evalua el algoritmo, no la marcha. Si el robot se
    tropieza, el alumno recibe roja por algo que no es suyo.

La animacion de las patas es COSMETICA: el robot se desliza. Sirve para que se
vea que camina, no para simular como camina.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field

# Donde buscar los modelos oficiales, en orden.
UBICACIONES = [
    os.path.expanduser("~/unitree_libs/unitree_mujoco/unitree_robots"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "unitree_robots"),
    os.path.expanduser("~/unitree_mujoco/unitree_robots"),
    os.path.join(os.getcwd(), "unitree_mujoco", "unitree_robots"),
]


@dataclass
class Robot:
    clave: str
    nombre: str
    tipo: str
    escena: str          # ruta relativa dentro de unitree_robots/
    altura: float        # altura de la base al estar de pie, en metros
    pose_de_pie: dict = field(default_factory=dict)   # indice art -> radianes
    # Indices (dentro de qpos, contando desde la primera articulacion) que se
    # animan al caminar: (indice, amplitud, desfase)
    marcha: list = field(default_factory=list)
    saludo: dict = field(default_factory=dict)
    pose_sentado: dict = field(default_factory=dict)

    def ruta_escena(self) -> str | None:
        for base in UBICACIONES:
            ruta = os.path.join(base, self.escena)
            if os.path.exists(ruta):
                return ruta
        return None


# --- G1: humanoide de 29 grados de libertad -----------------------------
# Indices relativos (qpos real = 7 + indice)
G1_L_HIP_P, G1_L_KNEE = 0, 3
G1_R_HIP_P, G1_R_KNEE = 6, 9
G1_L_SHOULDER_P, G1_L_ELBOW = 15, 18
G1_R_SHOULDER_P, G1_R_ELBOW = 22, 25

G1 = Robot(
    clave="g1",
    nombre="Unitree G1",
    tipo="humanoide",
    escena="g1/scene_29dof.xml",   # scene.xml tiene ~100 obstaculos del terrain_tool
    altura=0.793,
    pose_de_pie={
        G1_L_SHOULDER_P: 0.20, G1_R_SHOULDER_P: 0.20,
        G1_L_ELBOW: -0.30, G1_R_ELBOW: -0.30,
    },
    marcha=[
        (G1_L_HIP_P, 0.40, 0.0),
        (G1_R_HIP_P, 0.40, math.pi),
        (G1_L_KNEE, 0.45, 1.1),
        (G1_R_KNEE, 0.45, 1.1 + math.pi),
        (G1_L_SHOULDER_P, 0.30, math.pi),
        (G1_R_SHOULDER_P, 0.30, 0.0),
    ],
    saludo={G1_R_SHOULDER_P: -2.4, G1_R_ELBOW: -1.0},
    # Agachado (FSM Sit / Damp). No es un desplome: es una postura.
    pose_sentado={G1_L_HIP_P: -1.2, G1_R_HIP_P: -1.2,
                  G1_L_KNEE: 1.8, G1_R_KNEE: 1.8},
)

# --- Go2: cuadrupedo de 12 grados de libertad ---------------------------
GO2_FL_T, GO2_FL_C = 1, 2
GO2_FR_T, GO2_FR_C = 4, 5
GO2_RL_T, GO2_RL_C = 7, 8
GO2_RR_T, GO2_RR_C = 10, 11

# Pose de perro parado. Sin esto el modelo aparece con las patas estiradas.
_GO2_MUSLO, _GO2_PANTORRILLA = 0.80, -1.55

GO2 = Robot(
    clave="go2",
    nombre="Unitree Go2",
    tipo="cuadrupedo",
    escena="go2/scene.xml",
    altura=0.33,
    pose_de_pie={
        GO2_FL_T: _GO2_MUSLO, GO2_FR_T: _GO2_MUSLO,
        GO2_RL_T: _GO2_MUSLO, GO2_RR_T: _GO2_MUSLO,
        GO2_FL_C: _GO2_PANTORRILLA, GO2_FR_C: _GO2_PANTORRILLA,
        GO2_RL_C: _GO2_PANTORRILLA, GO2_RR_C: _GO2_PANTORRILLA,
    },
    # Trote: las diagonales van juntas (FL con RR, FR con RL).
    marcha=[
        (GO2_FL_T, 0.28, 0.0), (GO2_RR_T, 0.28, 0.0),
        (GO2_FR_T, 0.28, math.pi), (GO2_RL_T, 0.28, math.pi),
        (GO2_FL_C, 0.22, 0.0), (GO2_RR_C, 0.22, 0.0),
        (GO2_FR_C, 0.22, math.pi), (GO2_RL_C, 0.22, math.pi),
    ],
    # El perro "saluda" levantando la pata delantera izquierda.
    saludo={GO2_FL_T: -0.6, GO2_FL_C: -0.9},
    pose_sentado={GO2_FL_T: 1.3, GO2_FR_T: 1.3, GO2_RL_T: 1.3, GO2_RR_T: 1.3,
                  GO2_FL_C: -2.4, GO2_FR_C: -2.4, GO2_RL_C: -2.4, GO2_RR_C: -2.4},
)

ROBOTS = {"g1": G1, "go2": GO2}


def obtener(clave: str) -> Robot:
    c = clave.lower().strip()
    if c not in ROBOTS:
        raise ValueError(f"Robot desconocido: '{clave}'. Validos: g1, go2.")
    return ROBOTS[c]


def faltan_modelos() -> str:
    """Mensaje de ayuda si no encuentra los modelos oficiales."""
    return (
        "No encuentro los modelos oficiales de Unitree.\n\n"
        "Se descargan una sola vez con:\n"
        "    git clone https://github.com/unitreerobotics/unitree_mujoco\n\n"
        "Dejalos en alguna de estas carpetas:\n"
        + "\n".join(f"    {u}" for u in UBICACIONES)
    )
