"""
Mapeo de índices de motor a nombre y grupo corporal.
Go2: 12 motores (índices 0-11) — MotorState[20], solo se usan 12
G1:  29 motores (índices 0-28) — MotorState[35], solo se usan 29
"""

GO2_JOINT_MAP = {
    # --- Pata Frontal Derecha (FR) ---
    0:  {"name": "FR_Hip",   "group": "Pata Frontal Derecha"},
    1:  {"name": "FR_Thigh", "group": "Pata Frontal Derecha"},
    2:  {"name": "FR_Calf",  "group": "Pata Frontal Derecha"},
    # --- Pata Frontal Izquierda (FL) ---
    3:  {"name": "FL_Hip",   "group": "Pata Frontal Izquierda"},
    4:  {"name": "FL_Thigh", "group": "Pata Frontal Izquierda"},
    5:  {"name": "FL_Calf",  "group": "Pata Frontal Izquierda"},
    # --- Pata Trasera Derecha (RR) ---
    6:  {"name": "RR_Hip",   "group": "Pata Trasera Derecha"},
    7:  {"name": "RR_Thigh", "group": "Pata Trasera Derecha"},
    8:  {"name": "RR_Calf",  "group": "Pata Trasera Derecha"},
    # --- Pata Trasera Izquierda (RL) ---
    9:  {"name": "RL_Hip",   "group": "Pata Trasera Izquierda"},
    10: {"name": "RL_Thigh", "group": "Pata Trasera Izquierda"},
    11: {"name": "RL_Calf",  "group": "Pata Trasera Izquierda"},
}

G1_JOINT_MAP = {
    # --- Pierna Izquierda ---
    0:  {"name": "L_Hip_Pitch",       "group": "Pierna Izquierda"},
    1:  {"name": "L_Hip_Roll",        "group": "Pierna Izquierda"},
    2:  {"name": "L_Hip_Yaw",         "group": "Pierna Izquierda"},
    3:  {"name": "L_Knee",            "group": "Pierna Izquierda"},
    4:  {"name": "L_Ankle_Pitch",     "group": "Pierna Izquierda"},
    5:  {"name": "L_Ankle_Roll",      "group": "Pierna Izquierda"},
    # --- Pierna Derecha ---
    6:  {"name": "R_Hip_Pitch",       "group": "Pierna Derecha"},
    7:  {"name": "R_Hip_Roll",        "group": "Pierna Derecha"},
    8:  {"name": "R_Hip_Yaw",         "group": "Pierna Derecha"},
    9:  {"name": "R_Knee",            "group": "Pierna Derecha"},
    10: {"name": "R_Ankle_Pitch",     "group": "Pierna Derecha"},
    11: {"name": "R_Ankle_Roll",      "group": "Pierna Derecha"},
    # --- Cintura ---
    12: {"name": "Waist_Yaw",         "group": "Cintura"},
    13: {"name": "Waist_Roll",        "group": "Cintura"},
    14: {"name": "Waist_Pitch",       "group": "Cintura"},
    # --- Brazo Izquierdo ---
    15: {"name": "L_Shoulder_Pitch",  "group": "Brazo Izquierdo"},
    16: {"name": "L_Shoulder_Roll",   "group": "Brazo Izquierdo"},
    17: {"name": "L_Shoulder_Yaw",    "group": "Brazo Izquierdo"},
    18: {"name": "L_Elbow",           "group": "Brazo Izquierdo"},
    # --- Muñeca/Mano Izquierda ---
    19: {"name": "L_Wrist_Roll",      "group": "Mano Izquierda"},
    20: {"name": "L_Wrist_Pitch",     "group": "Mano Izquierda"},
    21: {"name": "L_Wrist_Yaw",       "group": "Mano Izquierda"},
    # --- Brazo Derecho ---
    22: {"name": "R_Shoulder_Pitch",  "group": "Brazo Derecho"},
    23: {"name": "R_Shoulder_Roll",   "group": "Brazo Derecho"},
    24: {"name": "R_Shoulder_Yaw",    "group": "Brazo Derecho"},
    25: {"name": "R_Elbow",           "group": "Brazo Derecho"},
    # --- Muñeca/Mano Derecha ---
    26: {"name": "R_Wrist_Roll",      "group": "Mano Derecha"},
    27: {"name": "R_Wrist_Pitch",     "group": "Mano Derecha"},
    28: {"name": "R_Wrist_Yaw",       "group": "Mano Derecha"},
}


def get_joint_map(robot_type: str) -> dict:
    """Devuelve el mapa de joints según el tipo de robot."""
    if robot_type.lower() == "go2":
        return GO2_JOINT_MAP
    elif robot_type.lower() == "g1":
        return G1_JOINT_MAP
    else:
        raise ValueError(f"Robot no soportado: {robot_type}")


def get_num_motors(robot_type: str) -> int:
    """Cantidad de motores activos según el robot."""
    return 12 if robot_type.lower() == "go2" else 29
