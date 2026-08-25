# =====================================================================
#  TP07 - Inteligencia Artificial
#  Agente que interpreta comandos en lenguaje natural
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

from ejecutor import Ejecutor
from evaluar import evaluar

# Pone tu nombre: aparece en el reporte que entregas.
ALUMNO = "Apellido, Nombre"


# =====================================================================
#  ETAPA 1 - CLASIFICADOR DE INTENCION
# =====================================================================
class ClasificadorIntencion:
    """Decide QUE quiere el usuario, sin mirar los numeros todavia."""

    TIPOS = ("MOVER", "GIRAR", "DETENERSE", "SALUDO",
             "CONSULTAR_ESTADO", "DESCONOCIDO")

    def __init__(self):
        self.modelo = None

        # -------------------------------------------------------------
        #  NIVEL 2 (extension): entrenar un modelo con TU dataset.
        #
        #  Armas dataset.csv con tus propios ejemplos (texto,intencion),
        #  descomentas estas dos lineas, y listo. El extractor, el
        #  validador y el ejecutor NO se enteran: solo cambia como
        #  clasificas.
        #
        #  Antes de esto, corre `python3 entrenar.py` para ver tus
        #  metricas y que te avise si al dataset le falta algo.
        # -------------------------------------------------------------
        # from entrenar import entrenar_desde_csv
        # self.modelo = entrenar_desde_csv()

    def clasificar(self, texto):
        """Devuelve uno de los seis tipos de TIPOS.

        Tiene que aguantar variantes del espanol rioplatense:

            avanza / avanza / movete / adelante / camina  ->  MOVER
            gira / rota / dale una vuelta                 ->  GIRAR
            detente / para / frena / quieto               ->  DETENERSE
            saluda / hola / hace un saludo                ->  SALUDO
            cuanta bateria / como estas / estado          ->  CONSULTAR_ESTADO

        Todo lo que no reconozcas: DESCONOCIDO. Es una respuesta valida y
        correcta, no una derrota.

        El modulo `re` alcanza para esto. Si despues queres probar con
        scikit-learn o con un modelo de lenguaje, cambias SOLO esta clase:
        el resto del pipeline no se entera. Esa es la gracia de que las
        etapas sean independientes.

        Si entrenaste un modelo (nivel 2), aca lo usas:

            if self.modelo is not None:
                return self.modelo.predict([texto])[0]

        Conviene dejar las reglas como respaldo: si el dataset no esta o
        scikit-learn no esta instalado, el agente sigue funcionando.
        """
        # TU CODIGO ACA
        return "DESCONOCIDO"


# =====================================================================
#  ETAPA 2 - EXTRACTOR DE PARAMETROS
# =====================================================================
class ExtractorParametros:
    """Saca los numeros del texto. Sigue en unidades humanas."""

    def extraer(self, texto, tipo):
        """Devuelve un diccionario con lo que encuentres. Todo es opcional.

            {"distancia_m": 2.0}                  de "2 metros"
            {"angulo_deg": 90}                    de "90 grados" o "90 grados"
            {"velocidad_ms": 0.2}                 de "a 0.2 m/s"
            {"direccion": "derecha"}              de "a la derecha"
            {"direccion": "atras"}                de "retrocede"

        Ojo con los adverbios, que no traen numero:

            "despacio", "lento"  ->  velocidad baja
            "rapido", "veloz"    ->  la maxima que permita tu materia
            "un poco"            ->  distancia corta
            "media vuelta"       ->  180 grados

        IMPORTANTE: aca seguis en metros y grados, porque asi habla la
        gente. La conversion a velocidad y tiempo la hace el Ejecutor, que
        ya esta escrito. Vos no la haces.
        """
        # TU CODIGO ACA
        return {}


# =====================================================================
#  ETAPA 3 - VALIDADOR DE SEGURIDAD
# =====================================================================
class ValidadorSeguridad:
    """La ultima barrera antes del robot.

    Este es el corazon del TP. Tiene que ser un componente SEPARADO del
    clasificador, no unas reglas mas metidas adentro.

    El motivo: tu clasificador se va a equivocar. Todos se equivocan. Si la
    seguridad viviera adentro del clasificador, un error de clasificacion
    seria tambien un error de seguridad. Separandolos, un error de
    clasificacion sigue siendo bloqueado.
    """

    # Palabras que describen acciones que el robot no debe intentar nunca.
    PALABRAS_PELIGROSAS = ("salta", "salto", "corre", "corré", "sprint",
                           "empuja", "empujá", "golpea", "rompe", "tira",
                           "cae", "fuerza")

    def __init__(self, perfil):
        # perfil trae los limites de tu materia:
        #   perfil.velocidad_max          m/s
        #   perfil.velocidad_angular_max  rad/s
        #   perfil.duracion_max           segundos por orden
        #   perfil.bateria_min            porcentaje
        self.perfil = perfil

    def validar(self, texto, tipo, parametros):
        """Devuelve (True, "") si se puede ejecutar, o (False, motivo).

        Que conviene revisar:

          1. Palabras peligrosas en el TEXTO ORIGINAL. Va en los dos
             sentidos: aunque el clasificador haya dicho MOVER, si el texto
             dice "salta" no va; y aunque haya dicho DESCONOCIDO, tampoco.
             Por eso mirás el texto y no solo la intencion.
          2. Velocidad pedida por encima de perfil.velocidad_max.
          3. Distancia que no tenga sentido (100 metros en un aula, no).
          4. Angulo mayor a 180 grados.
          5. Cualquier cosa que no puedas justificar como segura.

        Cuando bloquees, devolve un motivo entendible: va al reporte.
        """
        # TU CODIGO ACA
        return True, ""


# =====================================================================
#  EL AGENTE - une las tres etapas y llama al ejecutor
# =====================================================================
class AgenteRobot:
    def __init__(self, robot=None):
        self.robot = robot
        self.clasificador = ClasificadorIntencion()
        self.extractor = ExtractorParametros()
        self.validador = ValidadorSeguridad(
            robot.perfil if robot else _perfil_por_defecto())
        self.ejecutor = Ejecutor(robot) if robot else None
        self.historial = []

    def procesar(self, texto):
        """El pipeline completo. ESTA ES LA FUNCION QUE SE TE EVALUA.

        Tiene que devolver un diccionario con esta forma:

            {
              "tipo": "MOVER",          uno de los seis tipos
              "parametros": {...},      lo que extrajiste
              "ejecutar": True,         si se ejecuto o no
              "bloqueado": False,       True si tu validador lo freno
              "confianza": 0.9,
              "texto_original": texto,
              "mensaje": "...",         que paso, en castellano
            }

        Sobre `bloqueado`: sirve para distinguir dos cosas que NO son lo
        mismo, y es donde se juega buena parte de la nota.

            DESCONOCIDO   no entendiste, y no habia nada peligroso
                          ("hola, como estas?")
            BLOQUEADO     tu validador lo freno, hayas entendido o no
                          ("salta desde la mesa")

        Si marcaras "salta desde la mesa" como DESCONOCIDO a secas, estarias
        diciendo que es un comando inofensivo que no supiste interpretar. Y
        es al reves: es el que MAS importa frenar.
        """
        # TU CODIGO ACA
        #
        # El orden es: clasificar -> extraer -> validar -> ejecutar.
        #
        # Acordate:
        #   - el validador corre SIEMPRE, aunque el tipo sea DESCONOCIDO.
        #     "salta desde la mesa" no lo entiende ningun clasificador, y
        #     justamente por eso hay que bloquearlo: si DESCONOCIDO salteara
        #     la validacion, el comando mas peligroso seria el que se escapa.
        #     Un comando que no se entiende NO es un comando inofensivo.
        #   - si el validador bloquea, NO se ejecuta
        #   - solo se llama a self.ejecutor.ejecutar(...) si paso todo
        #   - si self.ejecutor es None, estas sin robot: clasifica igual
        return {
            "tipo": "DESCONOCIDO",
            "parametros": {},
            "ejecutar": False,
            "confianza": 0.0,
            "texto_original": texto,
            "mensaje": "todavia no implementado",
        }


def _perfil_por_defecto():
    """Permite evaluar el agente sin abrir el simulador."""
    import sys
    from pathlib import Path
    entorno = Path(__file__).resolve().parent.parent / "entorno"
    if str(entorno) not in sys.path:
        sys.path.insert(0, str(entorno))
    from sim.safety import perfil
    return perfil("tp07")


# =====================================================================
#  PROGRAMA PRINCIPAL - no hace falta que lo toques
# =====================================================================
def main():
    import sys

    # Modo sin robot: solo evalua los 25 casos. Sirve para trabajar el
    # clasificador sin tener el simulador abierto.
    sin_robot = "--sin-robot" in sys.argv

    robot = None
    if not sin_robot:
        robot = Robot()
        robot.conectar()

    try:
        agente = AgenteRobot(robot)
        evaluar(agente)

        if robot is not None:
            print("\n  Escribi ordenes para el robot. Enter vacio para salir.")
            while True:
                try:
                    texto = input("\n  > ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                if not texto:
                    break
                r = agente.procesar(texto)
                print(f"    {r['tipo']}  {r.get('mensaje', '')}")
    finally:
        if robot is not None:
            robot.detenerse()
            robot.desconectar()


if __name__ == "__main__":
    main()
