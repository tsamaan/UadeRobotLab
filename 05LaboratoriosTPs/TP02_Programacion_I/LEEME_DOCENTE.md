# TP02 — Programación I
## Guía para el docente

---

## Qué es esto

Un laboratorio para que los alumnos construyan un **controlador de misiones**
sobre un robot Unitree (G1 humanoide o Go2 cuadrúpedo), sin necesidad de tener
el robot delante.

Usa el **simulador oficial de Unitree** (`unitree_mujoco`) y el **SDK oficial de
Python**. Cuando el alumno escribe `robot.avanzar(...)`, por debajo corre el
mismo `LocoClient` del SDK que se usa contra el robot físico. Por eso su archivo
funciona después en el robot real sin cambiarle una línea.

Todo corre en la máquina del alumno: **no necesita internet ni el robot**.

---

## Qué evalúa el TP

Diseño top-down, funciones modulares, arreglos y validación. El alumno recibe
una lista de comandos y tiene que:

1. **Validar** cada comando antes de ejecutarlo.
2. **Ejecutar** los válidos.
3. **Rechazar** los inválidos sin cortar la misión.
4. **Reportar** qué pasó con cada uno.

El archivo `mi_tp02.py` viene partido en esas cuatro funciones, cada una con su
docstring y un `# TU CODIGO ACA`. La estructura está dada; la lógica la escribe
el alumno.

---

## Paso a paso

### 1. Instalación (una vez por computadora)

Seguí **`INSTALACION.md`**. Son dos cosas: Python 3.10+ y MuJoCo. Los modelos
del robot ya vienen en la carpeta; no hace falta CycloneDDS ni el SDK de
Unitree.

Para verificar sin abrir nada:

```bash
cd entorno && python3 -m sim --solo-revisar
```

### 2. Abrir el simulador

Doble clic en `INICIAR_SIMULADOR` (`.bat` en Windows, `.sh` en Linux/macOS).
Pregunta qué robot (1 = G1, 2 = Go2), revisa el entorno y abre la ventana.

### 3. El alumno programa y ejecuta

Escribe en `mi_desarrollo/mi_tp02.py` y ejecuta con `EJECUTAR_MI_CODIGO`.

### 4. Recibir las entregas

Pediles `mi_tp02.py` renombrado con el apellido (`tp02_perez_juan.py`). Para
probarlo, lo ponés en `mi_desarrollo/` y lo ejecutás.

No hace falta que entreguen `misiones.py`: ese se los damos nosotros.

---

## El formato de misión

Todo se expresa en **velocidad y tiempo**, igual que en el TP01 y que en el
robot real:

```python
("avanzar", velocidad, tiempo)     # m/s, segundos
("girar", velocidad, tiempo)       # rad/s (+ izquierda, - derecha), segundos
("detenerse",)
("saludar",)
```

La distancia y el ángulo son **derivados**: `velocidad × tiempo`. No hay
comandos en metros ni en grados, a propósito: es como piensa el robot, y calcular
esa multiplicación es parte de lo que el alumno tiene que entender.

`misiones.py` trae cuatro misiones: `basica`, `cuadrado`, `errores` y `larga`.

### La misión con errores

`MISION_CON_ERRORES` tiene **siete comandos inválidos** deliberados, que cubren
categorías distintas de error:

| Comando | Qué está mal |
|---|---|
| `("avanzar", 0.9, 2.0)` | velocidad sobre el límite |
| `("avanzar", 0.2, 50.0)` | tiempo sobre el límite |
| `("girar", 3.0, 2.0)` | velocidad angular sobre el límite |
| `("volar", 0.2, 1.0)` | comando inexistente |
| `("avanzar", "rapido", 2.0)` | tipo incorrecto |
| `("avanzar", 0.2)` | faltan datos |
| `("avanzar", 0.2, -3.0)` | tiempo negativo |

Un alumno que sólo valide el nombre del comando va a pasar cuatro de los siete.
Sirve para ver quién validó de verdad.

---

## Los límites de esta materia

| | |
|---|---|
| Velocidad máxima | 0.20 m/s |
| Velocidad de giro máxima | 0.50 rad/s |
| Tiempo máximo por orden | 10 s |

A 0.20 m/s, 10 segundos son 2 metros: suficiente para un aula, y obliga a
encadenar órdenes en vez de resolver todo con un comando largo.

**El simulador rechaza, no recorta.** Si el alumno pide 0.9 m/s, salta un
`ErrorDeSeguridad` con un mensaje claro. Es deliberado: un recorte silencioso
haría que la distancia recorrida no fuera la calculada, y el alumno ajustaría
números a ciegas.

Eso además es parte del ejercicio: aunque su validación deje pasar algo, el
robot avisa, y el alumno puede atraparlo con `try/except` y registrarlo en el
reporte. **Hay dos capas de validación y las dos importan.**

Los límites viven en `entorno/sim/safety.py`. Hay un **techo físico** (0.25 m/s)
que ninguna materia puede superar, y por debajo el límite pedagógico de cada TP.

---

## ⚠️ Qué NO simula — leer antes de prometer nada

El simulador es **cinemático**: no corre física.

- El robot **se desliza**. El movimiento de las patas es decorativo.
- **No se cae, no patina, no tiene inercia.** Arranca y frena al instante.
- No hay obstáculos ni colisiones.
- La batería es un número fijo inventado.

**Que un programa funcione en el simulador no garantiza que funcione en el
robot.** Valida la **lógica** del alumno —que es lo que evalúa el TP—, no la
ejecución física.

### Por qué es así

El simulador oficial de Unitree **no incluye el controlador de locomoción**: el
que hace caminar al G1 corre en la PC interna del robot y Unitree no lo publica.
Con física real, el humanoide se desploma en dos segundos.

Este laboratorio agrega el servicio de locomoción que falta y mueve el robot de
forma cinemática. Es la única manera de que las órdenes de alto nivel funcionen
hoy contra el simulador oficial.

---

## Cómo llega esto al robot real

El alumno entrega `mi_tp02.py`. El día de la visita, el responsable del robot
copia ese archivo al laboratorio físico y lo ejecuta **sin modificarlo**.

Funciona porque lo que coincide es **el contrato de la API** —
`avanzar(velocidad, tiempo)`, `girar(velocidad, tiempo)`—, no el cable. En el
simulador esas órdenes viajan por un socket local; contra el robot, por DDS con
el SDK oficial de Unitree. El archivo del alumno es el mismo.

Antes de cualquier movimiento real, el laboratorio verifica red, batería y
estado del robot, y **bloquea la ejecución si no puede confirmarlos**.

---

## Detalles técnicos

| Componente | Qué hace |
|---|---|
| `unitree_mujoco` (oficial) | modelos 3D y escenas de los robots |
| `local.py` | el socket que une el programa del alumno con el simulador |
| `simulador.py` | el simulador que se reparte: MuJoCo + socket, sin DDS |
| `arrancar.py` | el camino DDS con el SDK real (solo Linux, `--dds`) |
| `mundo.py` | pose del robot e integración del movimiento |
| `safety.py` | límites: techo físico + perfil por materia |
| `robot.py` | la API que usa el alumno |

El simulador escucha en **127.0.0.1:8765**. Es un socket local: no sale
de la máquina y funciona igual en Windows, macOS y Linux.

```bash
cd entorno
python3 -m sim --solo-revisar      # revisa el entorno y sale
python3 -m sim --robot go2         # elegir robot sin el menú
python3 -m sim --sin-ventana       # sin 3D (máquinas sin drivers)
```

---

## Problemas frecuentes

**"El simulador ya está abierto" y no se ve ninguna ventana**
Quedó un proceso corriendo. Linux: `pkill -f "python.*-m sim"`. Windows: cerrá
la consola que quedó abierta.

**Se abre sin ventana 3D**
Falta MuJoCo o la máquina no puede abrir ventanas. **El TP se hace igual** en
modo consola.

**`Could not locate cyclonedds`**
Ya no debería aparecer: **CycloneDDS no se usa más**. Si aparece, estás
siguiendo una guía vieja o corriendo el simulador con `--dds`.

**pip falla con errores SSL en la facultad**
La red intercepta certificados. Agregá
`--trusted-host pypi.org --trusted-host files.pythonhosted.org`.
