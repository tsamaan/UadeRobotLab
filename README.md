# UadeRobotLab

Laboratorios de robótica con robots Unitree para las materias de UADE.

> ## Si sos docente o estudiante, leé solo esto
>
> **Todo lo que necesitás está en `05LaboratoriosTPs/`.** Entrá a la carpeta de
> tu materia y seguí su `INSTALACION.md`.
>
> El resto de las carpetas de este repositorio son material interno de
> investigación. **No hace falta que las abras, ni que las instales, ni que las
> entiendas.** Están acá porque este repositorio es también el archivo del
> proyecto.

---

## Instalación, en dos pasos

Se hace **una sola vez** por computadora, y funciona igual en **Windows, macOS y
Linux**.

### 1. Python

Descargalo de [python.org](https://www.python.org/downloads/) — sirve **3.10 o
más nuevo**, cualquiera.

> ⚠️ **En Windows: tildá "Add python.exe to PATH"** durante la instalación. Es
> la causa número uno de que después nada funcione.

### 2. MuJoCo

Es la ventana 3D donde se ve el robot.

```bash
# Windows
py -3 -m pip install mujoco

# macOS / Linux
python3 -m pip install mujoco
```

**Y eso es todo.** No hace falta nada más: ni CycloneDDS, ni el SDK de Unitree,
ni compilar nada, ni tener internet después de bajar tu carpeta. Los modelos 3D
del robot **ya vienen adentro**.

> Si el `pip` falla con errores de certificado — típico en las redes de la
> facultad — agregá:
> `--trusted-host pypi.org --trusted-host files.pythonhosted.org`

---

## Cómo se usa

### 1. Bajá tu carpeta

Entrá a `05LaboratoriosTPs/` y quedate con la carpeta de tu materia. **Cada una
es independiente y trae todo adentro**: no necesita a las demás ni al resto del
repositorio.

### 2. Abrí el simulador

Doble clic (o desde la terminal):

| Materia | Lanzador |
|---|---|
| TP01, TP02, TP03, TP07 | `INICIAR_SIMULADOR.bat` (Windows) · `INICIAR_SIMULADOR.sh` |
| TP04 | `INICIAR_TP04.bat` · `INICIAR_TP04.sh` |
| TP05 | `INICIAR_TP05.bat` · `INICIAR_TP05.sh` |

Pregunta qué robot querés — **1 = G1** (humanoide) o **2 = Go2** (perro) —,
revisa que esté todo instalado y abre la ventana con el robot.

Si falta algo, **no abre**: es peor un simulador que arranca a medias y después
falla raro.

### 3. Escribí tu programa

En `mi_desarrollo/mi_tpXX.py`. Es el archivo que entregás.

```python
from robot import Robot

robot = Robot()
robot.conectar()

robot.avanzar(velocidad=0.2, tiempo=2.0)     # 0.2 m/s × 2 s = 0.40 m
robot.girar(velocidad=0.5, tiempo=3.14)      # 0.5 rad/s × 3.14 s = 90°

robot.detenerse()
robot.desconectar()
```

### 4. Ejecutalo

Con el simulador **abierto**, en otra ventana:

`EJECUTAR_MI_CODIGO.bat` (Windows) · `EJECUTAR_MI_CODIGO.sh`

En TP04 y TP05 no hay `EJECUTAR_MI_CODIGO`: el alumno construye una app o un
dashboard que se conecta por HTTP, y el lanzador ya deja el backend andando.

### 5. Documentos de cada carpeta

| Archivo | Para quién |
|---|---|
| `INSTALACION.md` | de cero, paso a paso |
| `LEEME_ESTUDIANTE.md` | qué hay que hacer y cómo se entrega |
| `LEEME_DOCENTE.md` | cómo se corrige y qué esperar |
| `API.md` | solo TP04 y TP05: el contrato HTTP |

---

## Los laboratorios

| Carpeta | Materia | Qué construye el alumno |
|---|---|---|
| `TP01_Fundamentos_de_Informatica` | Fundamentos de Informática | Una rutina secuencial en Python |
| `TP02_Programacion_I` | Programación I | Un controlador de misiones con validación y reporte |
| `TP03_Programacion_III_Backtracking` | Programación III | Navegación en grilla con backtracking |
| `TP03_Programacion_III_Greedy` | Programación III | Navegación en grilla con estrategia voraz |
| `TP04_Desarrollo_de_Aplicaciones_I` | Desarrollo de Aplicaciones I | Una app móvil React Native que controla el robot |
| `TP05_Desarrollo_de_Aplicaciones_II` | Desarrollo de Aplicaciones II | Un dashboard web de telemetría en vivo |
| `TP07_Inteligencia_Artificial` | Inteligencia Artificial | Un agente que interpreta órdenes en castellano |

Falta `TP06_Paradigma_Orientado_a_Objetos`: es Java puro y su modalidad
principal no usa el robot.

### Anatomía de una carpeta

```
TPXX_Materia/
├── INSTALACION.md          de cero
├── LEEME_ESTUDIANTE.md     para el alumno
├── LEEME_DOCENTE.md        para el docente
├── INICIAR_SIMULADOR       abre el simulador  (.bat y .sh)
├── EJECUTAR_MI_CODIGO      corre tu programa  (.bat y .sh)
├── mi_desarrollo/          ← acá trabajás vos
│   ├── mi_tpXX.py              tu programa. Es lo que entregás.
│   ├── robot.py                el puente. No se toca.
│   └── LEEME.md
└── entorno/                el motor. No se toca.
    └── sim/unitree_mujoco/     modelos oficiales del G1 y el Go2
```

---

## Cómo funciona el gemelo digital

El simulador levanta el **modelo oficial de Unitree** en MuJoCo y escucha en un
socket local. Tu programa le habla por ahí:

```
  tu programa                  el simulador
  mi_tpXX.py                   (la ventana 3D)
      │                             │
      └── robot.avanzar(v, t) ──────┘
              socket local en 127.0.0.1
```

Es **local**: no sale de tu computadora, no necesita red, no necesita permisos
especiales y funciona igual en los tres sistemas operativos.

### El movimiento es cinemático

No hay física: el robot **se desliza** y la animación de las patas es cosmética.
Es a propósito, por dos motivos:

1. El controlador que hace caminar al G1 corre en la computadora interna del
   robot y Unitree no lo publica. Con física real, **el humanoide se desploma en
   dos segundos**.
2. Un TP de programación evalúa el algoritmo, no la marcha. Si el robot se
   tropieza, el alumno recibe roja por algo que no es suyo.

> **Verde en el simulador no garantiza verde en el aula.** El día de la visita
> hay un piso real, un robot de 35 kg y gente alrededor.

### Todo se expresa en velocidad y tiempo

```python
robot.avanzar(velocidad, tiempo)     # m/s, segundos
robot.girar(velocidad, tiempo)       # rad/s, segundos
```

- **distancia = velocidad × tiempo** — es derivada, nunca un dato de entrada
- **ángulo = velocidad × tiempo** — también
- En `girar`, el **signo** marca el sentido: positivo izquierda, negativo derecha

**No existen `avanzar_metros()` ni `girar_grados()`.** Es así porque es como
piensa el robot real: su orden de movimiento no es un paso, es *una velocidad
con vencimiento*. Si tu programa deja de refrescarla, el robot frena solo. Un
helper en metros mentiría sobre lo que está pasando, y hacer esa multiplicación
es parte de lo que el TP evalúa.

### Lo que puede dañar al robot está bloqueado

El robot se prende y se para **desde el control oficial, y lo hace el
operador**. Los laboratorios solo permiten mover y gestos que no cambian la
postura: nada de sentarse, pararse, bailar, saltar ni acrobacias.

Está implementado como **lista blanca** — lo que no está explícitamente
permitido se rechaza —, así que un método nuevo del SDK queda bloqueado por
defecto.

Cada materia tiene además su propio techo de velocidad, y **el simulador rechaza
lo mismo que rechazaría el robot**.

---

## El resto del repositorio

> **Nada de acá abajo hace falta para los laboratorios.** Es material de
> investigación y desarrollo del proyecto, en distintos estados de madurez.
> Si estás instalando tu TP, **saltealo**.

| Carpeta | Qué es | ¿Lo necesito? |
|---|---|---|
| `05LaboratoriosTPs/` | **Los laboratorios.** Un paquete autocontenido por materia | **Sí. Es esto** |
| `00SDK/` | Referencias a los SDKs oficiales de Unitree (C++ y Python) | No. Están vacías: son enlaces a repos de Unitree |
| `01Investigacion/` | Pruebas de captura de video y LiDAR, recuperación de datos | No |
| `02G1/` | Investigación y actividades sueltas del G1 humanoide | No |
| `03Go2/` | Investigación y actividades sueltas del Go2 cuadrúpedo | No |
| `04Simuladores/` | Experimentos previos de simulación y aprendizaje por refuerzo | No |
| `tools/` | Scripts internos para generar documentación en PDF | No |

### ⚠️ Dos avisos importantes

**No corras `04Simuladores/UnitreeMujocoOficial/setup_windows.bat`.** Es un
taller anterior, con otra arquitectura. Intenta instalar CycloneDDS y el SDK de
Unitree, que **fallan en Windows y macOS** con Python 3.11 o más nuevo, y no
tiene nada que ver con los laboratorios. Ya hubo docentes que llegaron ahí
buscando cómo instalar su TP y perdieron una tarde. Se deja por valor
histórico, no para usar.

**`00SDK/unitree_sdk2` y `00SDK/unitree_sdk2_python` están vacías.** Son enlaces
a repositorios de Unitree que no se clonan solos. **Los laboratorios no las
necesitan.**

---

## Problemas frecuentes

**`python` no se reconoce como un comando (Windows)**
Python no quedó en el PATH. Reinstalalo tildando *"Add python.exe to PATH"*.

**`Could not locate cyclonedds` o `timerfd_create: symbol not found`**
Estás siguiendo una guía vieja o corriendo algo de `04Simuladores/`. Los
laboratorios **no usan** CycloneDDS ni el SDK de Unitree. Volvé a
`05LaboratoriosTPs/` y seguí el `INSTALACION.md` de tu carpeta.

**Se abre el simulador pero sin ventana 3D**
Falta MuJoCo, o la máquina no puede abrir ventanas (drivers, escritorio remoto).
El simulador **funciona igual en modo consola**: se ve la posición del robot en
texto y el TP se puede hacer completo.

**Dice que ya hay un simulador abierto y no veo ninguno**
Quedó uno corriendo de antes, quizá minimizado o en modo consola. Cerralo con
Ctrl+C. En Linux o macOS: `pkill -f "python.*-m sim"`.

**Mi programa dice que no encuentra el simulador**
Tiene que estar abierto **antes** de ejecutar tu programa, y hay que esperar a
que la ventana aparezca del todo.

**Tengo varios Python y no encuentra MuJoCo**
El lanzador prueba cada Python disponible y elige el que tenga MuJoCo. Si aun
así falla, instalá MuJoCo en el Python que usás por defecto.

El `INSTALACION.md` de cada carpeta tiene la lista completa.

---

## Para el responsable del laboratorio

El circuito completo tiene dos mitades separadas:

```
   MÁQUINA DEL DOCENTE / ALUMNO          NOTEBOOK DEL LABORATORIO
   ┌──────────────────────────┐          ┌──────────────────────────┐
   │  05LaboratoriosTPs/      │          │  Laboratorio físico      │
   │  Gemelo digital.         │          │  RJ-45 ──────────────────┼──→ 🤖
   │  Sin robot. Se reparte.  │          │  No se reparte.          │
   └──────────────────────────┘          └──────────────────────────┘
                │                                    ▲
                │      viaja el ARCHIVO del alumno   │
                └────────────────────────────────────┘
```

Lo único que viaja entre las dos mitades es **el archivo que escribió el
alumno**. Funciona en ambas porque lo que coincide es **el contrato de la API**
—`avanzar(velocidad, tiempo)`, `girar(velocidad, tiempo)`—, no el transporte.

En este repositorio está **solo la mitad de la izquierda**. El laboratorio
físico, que se conecta al robot real, no se publica.
