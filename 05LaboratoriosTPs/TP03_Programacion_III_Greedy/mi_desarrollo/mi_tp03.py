# =====================================================================
#  TP03 - Programacion III
#  Planificador de rutas con estrategia GREEDY
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
#  FUNCION DE SELECCION
# =====================================================================
def distancia_manhattan(posicion, destino):
    """Cuantos pasos harian falta si no hubiera obstaculos.

        distancia = |fila - fila_destino| + |columna - columna_destino|
    """
    # TU CODIGO ACA
    return 0


# =====================================================================
#  TU ALGORITMO
# =====================================================================
def planificar_ruta(mapa):
    """Busca un camino del inicio al destino con una estrategia GREEDY.

    Devolve DOS cosas:  (ruta, estado)

        ruta   : lista de celdas [ [fila,columna], [fila,columna], ... ]
                 Empieza en mapa.inicio.
        estado : DESTINO_ALCANZADO  si llegaste
                 BLOQUEADO          si te quedaste sin candidatos
                 LIMITE_DE_PASOS    si te pasaste de mapa.maximo_pasos

    Que tenes disponible:

        mapa.filas, mapa.columnas
        mapa.inicio                  tupla (fila, columna)
        mapa.destino                 tupla (fila, columna)
        mapa.maximo_pasos
        mapa.es_transitable(f, c)    True si la celda existe y esta libre
        mapa.celda(f, c)             0 libre · 1 obstaculo · 2 prohibida

    La idea del greedy:

        1. Desde la celda actual, genera los cuatro vecinos.
        2. Descarta los que se salen, los bloqueados y los ya visitados.
        3. Si no queda ninguno, termina con BLOQUEADO.
        4. Calcula la distancia Manhattan de cada candidato al destino.
        5. Eleg el de MENOR distancia. Si hay empate, usa siempre el mismo
           orden: arriba, derecha, abajo, izquierda.
        6. Repeti hasta llegar al destino o superar mapa.maximo_pasos.

        El greedy NUNCA deshace una eleccion. Esa es su fuerza (es rapido
        y simple) y su debilidad: en el mapa nivel3 vas a ver que se
        queda encerrado aunque exista un camino.

        Si eso pasa, NO cambies el algoritmo para forzar la solucion:
        informar el bloqueo ES el resultado correcto.

    Orden de desempate sugerido:

        PRIORIDAD = [(-1, 0), (0, 1), (1, 0), (0, -1)]
                    #  arriba, derecha, abajo, izquierda
    """
    # TU CODIGO ACA
    return [], BLOQUEADO


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

    exportar_entrega(mapa, ruta, estado, ALUMNO, "greedy")


if __name__ == "__main__":
    main()
