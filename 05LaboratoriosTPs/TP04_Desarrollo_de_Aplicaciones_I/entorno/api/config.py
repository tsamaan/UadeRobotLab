"""Configuracion del backend TP04 en el paquete del simulador.

Es el mismo backend que corre en el laboratorio fisico. La diferencia esta en
este archivo y en unitree_bridge.py: aca NO hay IPs ni credenciales del robot,
porque el paquete no las necesita y son un pasivo.
"""

from __future__ import annotations

# Escuchar en todas las interfaces para que el celular pueda llegar.
# El script muestra la IP en pantalla al arrancar.
API_HOST = "0.0.0.0"
API_PORT = 8000
API_CORS_ORIGINS = ["*"]

# Un solo equipo controla el robot por vez. En el simulador no hace falta, pero
# se mantiene para que la app del alumno se desarrolle contra el mismo flujo que
# va a encontrar el dia de la visita.
SESION_TIMEOUT_MINUTOS = 10
COMANDO_TIMEOUT_MS = 500

ROBOT_ACTIVO = "g1"
ROBOTS = {
    "g1": {"nombre": "Unitree G1 EDU", "tipo": "humanoide"},
    "go2": {"nombre": "Unitree Go2 EDU", "tipo": "cuadrupedo"},
}
