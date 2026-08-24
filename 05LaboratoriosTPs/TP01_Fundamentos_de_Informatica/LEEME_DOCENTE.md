# TP01 — Fundamentos de Informática
## Guía para el docente

---

## Qué es esto

Un laboratorio para que los alumnos programen un robot Unitree (G1 humanoide o
Go2 cuadrúpedo) sin necesidad de tener el robot delante.

Usa el **simulador oficial de Unitree** (`unitree_mujoco`) y el **SDK oficial
de Python**. Cuando el alumno escribe `robot.avanzar(...)`, por debajo corre el
mismo `LocoClient` del SDK que se usa contra el robot físico. Por eso su
archivo funciona después en el robot real sin cambiarle una línea.

Todo corre en la máquina del alumno: **no necesita internet ni el robot**.

---

## Qué evalúa el TP

Programación secuencial: una rutina de pasos ordenados. El alumno entrega
`mi_tp01.py`, y ahí se ve si entendió el orden de las operaciones y el cálculo
`distancia = velocidad × tiempo`.

---

## Paso a paso

### 1. Instalación (una vez por computadora)

Seguí **`INSTALACION.md`**. Instala, en este orden:

1. Python 3.8+
2. MuJoCo (ventana 3D)
3. CycloneDDS 0.10.2
4. SDK de Unitree (`00SDK/unitree_sdk2_python`)
5. Simulador oficial (`04Simuladores/unitree_mujoco`)

> El script de inicio intenta instalar solo lo que falte. `INSTALACION.md` es
> para cuando algo falla o querés entender el detalle.

Para verificar sin abrir nada:

```bash
cd entorno && python3 -m sim --solo-revisar
```

### 2. Abrir el simulador

Doble clic en `INICIAR_SIMULADOR` (`.bat` en Windows, `.sh` en Linux/macOS).

Pregunta qué robot querés (1 = G1, 2 = Go2), revisa el entorno, y abre la
ventana. Esa ventana queda abierta durante toda la clase.

### 3. El alumno programa y ejecuta

Escribe en `mi_desarrollo/mi_tp01.py` y ejecuta con `EJECUTAR_MI_CODIGO`.

### 4. Recibir las entregas

Pediles el archivo `mi_tp01.py` renombrado con el apellido
(`tp01_perez_juan.py`). Para probarlo, lo ponés en `mi_desarrollo/` y lo
ejecutás.

---

## Estructura de la carpeta

```
TP01_Fundamentos_de_Informatica/
├── INSTALACION.md              ← instalación completa, de cero
├── LEEME_ESTUDIANTE.md         ← para pasarle a los alumnos
├── LEEME_DOCENTE.md            ← este archivo
├── INICIAR_SIMULADOR.sh/.bat   ← abre el simulador, pregunta el robot
├── EJECUTAR_MI_CODIGO.sh/.bat  ← corre el programa del alumno
├── mi_desarrollo/              ← donde trabaja el alumno
│   ├── mi_tp01.py              ← lo que edita y entrega
│   └── robot.py                ← puente, no se toca
└── entorno/                    ← el motor, no se toca
    └── sim/
```

---

## Los límites de esta materia

| | |
|---|---|
| Velocidad máxima | 0.20 m/s |
| Velocidad de giro máxima | 0.50 rad/s |
| Tiempo máximo por orden | 5 s |

Están puestos por dos motivos: son seguros para el robot real, y obligan al
alumno a encadenar órdenes en vez de resolver todo con un comando largo.

**El simulador rechaza, no recorta.** Si el alumno pide 0.9 m/s, el programa se
detiene con un mensaje claro. Es deliberado: un recorte silencioso haría que la
distancia recorrida no fuera la calculada, y el alumno ajustaría números a
ciegas hasta que "le dé", sin entender nada.

Los límites viven en `entorno/sim/safety.py`. Hay un **techo físico**
(0.25 m/s) que ninguna materia puede superar, y por debajo el límite pedagógico
de cada TP.

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

El simulador oficial de Unitree **no incluye el controlador de locomoción**. El
que hace caminar al G1 corre en la PC interna del robot y Unitree no lo
publica. Con física real, el humanoide se desploma en dos segundos y el alumno
no puede probar nada.

Este laboratorio agrega el servicio de locomoción que falta, y mueve el robot
de forma cinemática. Es la única manera de que las órdenes de alto nivel
funcionen hoy contra el simulador oficial.

Es a propósito, además: si el robot se tropezara, el alumno recibiría una mala
nota por algo que no depende de él. La marcha real la aporta el robot el día de
la visita.

---

## Cómo llega esto al robot real

El alumno entrega `mi_tp01.py`. El día de la visita, el responsable del robot
copia ese archivo al laboratorio físico y lo ejecuta **sin modificarlo**.

Funciona porque el alumno ya está usando el SDK real: lo único que cambia entre
simulador y robot es el dominio DDS y la interfaz de red.

Antes de cualquier movimiento real, el laboratorio verifica red, batería y
estado del robot, y **bloquea la ejecución si no puede confirmarlos**.

---

## Detalles técnicos

Por si necesitás explicar qué está pasando, o depurar.

| Componente | Qué hace |
|---|---|
| `unitree_mujoco` (oficial) | modelos 3D y escenas de los robots |
| `UnitreeSdk2Bridge` (oficial) | publica `rt/lowstate`, escucha `rt/lowcmd` |
| `servicio_sport.py` | servicio de locomoción del G1 (`LocoClient`) |
| `servicio_sport_go2.py` | servicio de locomoción del Go2 (`SportClient`) |
| `mundo.py` | pose del robot e integración del movimiento |
| `safety.py` | límites: techo físico + perfil por materia |
| `robot.py` | la API que usa el alumno |

DDS corre en **dominio 0, interfaz `lo`** (loopback). El aviso
`selected interface "lo" is not multicast-capable` es normal.

Opciones útiles:

```bash
cd entorno
python3 -m sim --solo-revisar          # revisa el entorno y sale
python3 -m sim --robot go2             # elegir robot sin el menú
python3 -m sim --sin-ventana           # sin 3D (máquinas sin drivers)
python3 -m sim --silencioso            # sin log de comandos
```

---

## Problemas frecuentes

**"El simulador ya está abierto" y no se ve ninguna ventana**
Quedó un proceso corriendo. En Linux: `pkill -f "python.*-m sim"`. En Windows,
cerrá la ventana de consola que quedó abierta.

**Se abre sin ventana 3D**
Falta MuJoCo o la máquina no puede abrir ventanas. **El TP se puede hacer
igual** en modo consola.

**Una PC tiene varios Python y no encuentra MuJoCo**
El script prueba cada uno y elige el que tenga MuJoCo instalado. Si aun así
falla, instalá MuJoCo en el Python por defecto.

**`Could not locate cyclonedds` al instalar el SDK**
Ver `INSTALACION.md`, paso 3: hay que compilar CycloneDDS y exportar
`CYCLONEDDS_HOME`.

**pip falla con errores SSL en la facultad**
La red intercepta certificados. Agregá
`--trusted-host pypi.org --trusted-host files.pythonhosted.org`.
