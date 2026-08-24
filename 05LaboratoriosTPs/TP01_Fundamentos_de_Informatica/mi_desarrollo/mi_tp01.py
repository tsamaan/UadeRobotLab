# =====================================================================
#  TP01 - Fundamentos de Informatica
#
#  ESTE ES EL ARCHIVO DONDE ESCRIBIS TU PROGRAMA.
#
#  Antes de ejecutarlo:
#    1. Abri INICIAR_SIMULADOR (elegi G1 o Go2)
#    2. Espera a que aparezca la ventana con el robot
#    3. Recien ahi ejecuta este archivo
#
#  Nombre y apellido:  .....................................
#  Comision:           .....................................
# =====================================================================

from robot import Robot


def main():
    robot = Robot()
    robot.conectar()

    # =================================================================
    #  TU CODIGO VA ACA ABAJO
    # =================================================================
    #
    #  Ordenes disponibles:
    #
    #    robot.avanzar(velocidad=0.2, tiempo=2.0)
    #        Avanza a 0.2 metros por segundo durante 2 segundos.
    #        Distancia recorrida = velocidad x tiempo = 0.4 metros.
    #
    #    robot.girar(velocidad=0.5, tiempo=3.14)
    #        Gira a 0.5 radianes por segundo durante 3.14 segundos.
    #        Angulo girado = velocidad x tiempo = 1.57 rad = 90 grados.
    #        Positivo gira a la IZQUIERDA, negativo a la DERECHA.
    #
    #    robot.saludar()
    #    robot.detenerse()
    #    robot.verificar_estado()      devuelve donde esta el robot
    #
    # =================================================================

    pass  # <-- borra esta linea y escribi tu programa

    # =================================================================
    #  FIN DE TU CODIGO
    # =================================================================

    robot.detenerse()
    robot.desconectar()


if __name__ == "__main__":
    main()
