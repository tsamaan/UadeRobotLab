# =====================================================================
#  TP03 - Programacion III
#  Planificador de rutas con BACKTRACKING
#
#  ESTE ES EL ARCHIVO DONDE ESCRIBIS TU PROGRAMA.
#
#  Antes de ejecutarlo:
#    1. Abri INICIAR_SIMULADOR (elegi G1 o Go2)
#    2. Espera a que aparezca la ventana con la grilla dibujada
#    3. Recien ahi ejecuta este archivo
#
#  Nombre y apellido:  .....................................
#  Comision:           .....................................
# =====================================================================

from robot import Robot

from recorrido import (
    BLOQUEADO,
    DESTINO_ALCANZADO,
    LIMITE_DE_PASOS,
    SIN_SOLUCION,
    cargar_mapa,
    exportar_entrega,
    mostrar_mapa,
    recorrer,
)

# Poné acá tu nombre: con eso se arma el archivo de entrega.
ALUMNO = "Apellido, Nombre"

# Cambiá esto para probar los distintos mapas:
#   practica_simple  ·  nivel1_directo  ·  nivel2_suboptimo  ·  nivel3_bloqueo
MAPA = "practica_simple"


# =====================================================================
#  TU ALGORITMO
# =====================================================================
def planificar_ruta(mapa):
    """Busca un camino del inicio al destino usando BACKTRACKING.

    Devolve DOS cosas:  (ruta, estado)

        ruta   : lista de celdas [ [fila,columna], [fila,columna], ... ]
                 Empieza en mapa.inicio. Si no hay solucion, devolve [].
        estado : DESTINO_ALCANZADO  si llegaste
                 SIN_SOLUCION       si no existe camino
                 LIMITE_DE_PASOS    si te pasaste de mapa.maximo_pasos

    Que tenes disponible:

        mapa.filas, mapa.columnas
        mapa.inicio                  tupla (fila, columna)
        mapa.destino                 tupla (fila, columna)
        mapa.maximo_pasos
        mapa.es_transitable(f, c)    True si la celda existe y esta libre
        mapa.celda(f, c)             0 libre · 1 obstaculo · 2 prohibida

    La idea del backtracking:

        1. Marca la celda actual como visitada y agregala a la ruta.
        2. Si es el destino, terminaste.
        3. Si no, proba cada vecino (arriba, derecha, abajo, izquierda).
        4. Si un vecino lleva a la solucion, listo.
        5. Si NINGUNO funciona, DESHACE: sacala de la ruta, desmarcala,
           y devolve el control a quien te llamo.

        El paso 5 es el corazon del backtracking, y es lo que lo
        diferencia del greedy: el greedy nunca deshace una eleccion.

    Consejo: escribi una funcion auxiliar recursiva y llamala desde aca.
    """
    # TU CODIGO ACA
    return [], SIN_SOLUCION


# =====================================================================
#  PROGRAMA PRINCIPAL - no hace falta que lo toques
# =====================================================================
def main():
    mapa = cargar_mapa(MAPA)

    ruta, estado = planificar_ruta(mapa)
    mapa.ruta = ruta

    mostrar_mapa(mapa, ruta)
    print(f"  Estado: {estado}   ({max(0, len(ruta) - 1)} pasos)")

    if estado != DESTINO_ALCANZADO:
        print("\n  No se llego al destino, asi que no se mueve el robot.")
        print("  Eso puede ser el resultado correcto: fijate el enunciado.")
    else:
        robot = Robot()
        robot.conectar()
        try:
            recorrer(robot, mapa, ruta)
        finally:
            robot.detenerse()
            robot.desconectar()

    exportar_entrega(mapa, ruta, estado, ALUMNO, "backtracking")


if __name__ == "__main__":
    main()
