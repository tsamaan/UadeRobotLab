# TP01 — Fundamentos de Informática
## Guía para el estudiante

Vas a programar un robot Unitree para que haga una rutina paso a paso. Primero
lo probás en el simulador; el día de la visita, el profesor ejecuta **tu mismo
archivo** contra el robot de verdad.

---

## Paso a paso

### 1. Instalar (una sola vez)

Si es la primera vez en esta computadora, seguí **`INSTALACION.md`**.

El script de inicio intenta instalar solo lo que falte, así que probá primero
con el paso 2. Si te dice que falta algo, ahí sí andá a `INSTALACION.md`.

### 2. Abrir el simulador

| Sistema | Qué hacés |
|---|---|
| **Windows** | doble clic en `INICIAR_SIMULADOR.bat` |
| **Linux / macOS** | doble clic en `INICIAR_SIMULADOR.sh`, o `./INICIAR_SIMULADOR.sh` |

Te va a preguntar qué robot querés:

```
   Que robot queres usar?

     1)  G1   - robot humanoide (camina en dos patas)
     2)  Go2  - robot perro     (camina en cuatro patas)

   Elegi 1 o 2 [1]:
```

Elegís, revisa que esté todo instalado, y se abre la ventana con el robot.

> **Dejá esa ventana abierta** todo el tiempo que estés programando. Si la
> cerrás, tu programa no va a encontrar el robot.

### 3. Escribir tu programa

Abrí **`mi_desarrollo/mi_tp01.py`** y escribí donde dice `TU CODIGO VA ACA`.

Completá tu nombre y comisión en la cabecera del archivo.

### 4. Ejecutarlo

| Sistema | Qué hacés |
|---|---|
| **Windows** | doble clic en `EJECUTAR_MI_CODIGO.bat` |
| **Linux / macOS** | doble clic en `EJECUTAR_MI_CODIGO.sh` |
| **Cualquiera, por terminal** | `python3 mi_desarrollo/mi_tp01.py` |

Mirá la ventana del simulador: el robot se mueve.

---

## Las órdenes que podés usar

```python
robot.conectar()
robot.verificar_estado()

robot.avanzar(velocidad=0.2, tiempo=2.0)
robot.girar(velocidad=0.5, tiempo=3.14)

robot.saludar()
robot.detenerse()
robot.desconectar()
```

### Cómo se calcula un movimiento

`avanzar` recibe **velocidad** (metros por segundo) y **tiempo** (segundos).
La distancia sale de multiplicar:

> **distancia = velocidad × tiempo**

Para recorrer 40 cm a 0.2 m/s: `0.4 m ÷ 0.2 m/s = 2 segundos`.

```python
robot.avanzar(velocidad=0.2, tiempo=2.0)   # recorre 0.40 m
```

`girar` funciona igual pero en **radianes por segundo**:

| Giro | Radianes |
|---|---|
| 90° (un cuarto de vuelta) | 1.5708 |
| 180° (media vuelta) | 3.1416 |
| 360° (una vuelta) | 6.2832 |

Para girar 90° a 0.5 rad/s: `1.5708 ÷ 0.5 = 3.14 segundos`.

```python
robot.girar(velocidad=0.5, tiempo=3.14)    # gira 90 grados a la izquierda
```

Velocidad **positiva** gira a la izquierda, **negativa** a la derecha.

---

## Tus límites en esta materia

| | |
|---|---|
| Velocidad máxima | 0.20 m/s |
| Velocidad de giro máxima | 0.50 rad/s |
| Tiempo máximo por orden | 5 segundos |

Si pedís más, **el programa se detiene y te avisa**:

```
Velocidad 0.900 m/s: el maximo de tp01-fundamentos es 0.20 m/s.
Baja la velocidad y volve a probar.
```

No se recorta en silencio a propósito. Si el robot fuera más lento sin decirte
nada, recorrería menos distancia de la que calculaste y no entenderías por qué.

Para llegar más lejos, encadená varias órdenes.

---

## Tu carpeta de trabajo

```
mi_desarrollo/
├── mi_tp01.py    ← acá escribís. Es lo que entregás.
└── robot.py      ← no lo toques
```

Podés crear más archivos ahí adentro y usarlos:

```python
from mis_funciones import recorrer_un_metro
```

Lo único que no hay que tocar es `robot.py` y la carpeta `entorno/`.

---

## Qué entregás

El archivo **`mi_tp01.py`**, con tu nombre completado arriba.

Nada más: ni la carpeta, ni el simulador. Poné tu apellido en el nombre del
archivo, por ejemplo `tp01_perez_juan.py`.

---

## Si algo no anda

**"No encuentro el simulador"**
No está abierto, o lo cerraste. Volvé al paso 2.

**"python no se reconoce como un comando" (Windows)**
Python no quedó en el PATH. Ver `INSTALACION.md`, paso 1.

**El robot no se mueve**
Fijate que la ventana del simulador siga abierta y que tu programa no haya
cortado con un error antes de llegar al movimiento.

**Se abre el simulador pero sin ventana 3D**
Funciona igual, en modo consola: vas a ver la posición del robot en texto.
Podés hacer el TP completo así.

**Dice "el simulador ya está abierto" y no veo ninguna ventana**
Quedó uno corriendo de antes. Buscá la otra ventana (puede estar minimizada) y
cerrala con Ctrl+C.

Cualquier otra cosa, avisale al profesor.

---

## Una aclaración importante

El simulador **no es el robot**. Es un modelo simplificado: el robot no se cae,
no patina, y arranca y frena al instante.

Que tu programa ande en el simulador **no garantiza** que salga igual en el
aula. Sirve para verificar que tu **lógica** es correcta, que es lo que se
evalúa en este TP.
