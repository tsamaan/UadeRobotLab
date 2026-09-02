# TP04 — Desarrollo de Aplicaciones I
## Guía para el docente

---

## Qué es esto

Un laboratorio para que los alumnos hagan una **app móvil React Native** que
controla un robot Unitree, sin tener el robot delante.

El paquete levanta **el simulador oficial de Unitree** y **el mismo backend REST**
que corre en la notebook del laboratorio el día de la visita. La app del alumno
le pega por HTTP.

**El backend es literalmente el mismo código.** Lo único que cambia es el bridge:
en el paquete habla con el simulador, en la notebook con el robot por RJ-45. Por
eso la app del alumno **no cambia nada** el día de la visita salvo la IP.

---

## Qué evalúa

Una app que sea un control remoto funcional: mover, parar, saludar, y mostrar el
estado del robot. El alumno tiene que leer una API ajena y trabajar contra ella
— que es exactamente lo que va a hacer en cualquier trabajo.

`API.md` es el contrato. Es lo más importante que se le entrega.

---

## Paso a paso

1. **Instalación** (una vez): `INSTALACION.md`. Este TP suma `fastapi` y
   `uvicorn`, que el script instala solo.
2. **Levantar**: doble clic en `INICIAR_TP04`. Elige robot, abre el simulador y
   arranca el backend. **Muestra la IP en pantalla.**
3. **El alumno** levanta su app con `npx expo start` y apunta a esa IP.

La IP es la fricción número uno: el celular no ve `localhost` de la
computadora. Por eso el script la muestra grande al arrancar.

---

## ⚠️ Lo que la API deja hacer, y lo que no

Esto es una decisión de seguridad y conviene explicarla en clase, porque los
alumnos van a preguntar.

**Permitido:**

| | |
|---|---|
| `/mover` | mover el robot |
| `/parar` | frenarlo |
| `/accion/saludo` | saludar con la mano |
| `/accion/dar_la_mano` | extender la mano (sólo G1) |

**Bloqueado, con `403`:**

| | Por qué |
|---|---|
| prender / apagar | lo hace el docente con el control oficial |
| pararse, sentarse, agacharse | cambia la postura de un robot que quizás nadie mira |
| bailar, saltar, volteretas, handstand | pueden romper el robot o lastimar a alguien |

Está implementado como **lista blanca**: lo que no está explícitamente
permitido, se rechaza. Si el SDK de Unitree agrega un método nuevo —y agrega
seguido— queda bloqueado por defecto en vez de aparecer disponible sin que nadie
lo decida.

Hay un test que **barre los métodos reales del SDK** y falla si alguno queda
permitido sin decidirlo.

---

## El joystick y el hombre muerto

`/mover` no es un destino: es una velocidad que **vence a los 0.4 segundos**.
Para que el robot camine continuo, la app tiene que repetir la llamada cada
~200 ms.

Es deliberado: si la app se cierra, se corta el WiFi o el alumno suelta el
control, **el robot frena solo**. Es la diferencia entre un robot que se detiene
y uno que sigue caminando sin nadie del otro lado.

Es el error más común: el alumno manda un `/mover`, ve que el robot se mueve un
instante y para, y cree que está roto.

---

## Límites de la materia

| | |
|---|---|
| Velocidad | 0.20 m/s |
| Giro | 0.50 rad/s |
| Batería mínima | 25 % |

Antes este laboratorio tenía 0.5 m/s —**el doble del techo común a todas las
materias**— y batería en 15 %. Corregido el 2026-08-25. Es el único laboratorio
que da control en vivo desde un celular, así que era justamente el que menos
podía tenerlo mal.

Acá se **recorta** en vez de rechazar: con un joystick a 10 comandos por segundo,
devolver error en cada uno dejaría la app inusable. Se recorta y se avisa por
consola.

---

## Sesión exclusiva

Un solo equipo controla el robot por vez, con token y timeout de 10 minutos. El
segundo equipo recibe `409` con el nombre del que tiene el control.

El día de la visita los grupos pasan de a uno: entran, prueban, cierran sesión,
y sigue el siguiente. Si un grupo se va sin cerrar, se libera solo.

---

## ⚠️ Qué NO simula

El simulador es **cinemático**: no corre física.

- El robot **se desliza**; las patas se animan pero es decorativo.
- **No se cae, no patina, no choca con nada.**
- La batería es un número fijo inventado.

Que la app funcione contra el simulador **no garantiza** que la experiencia sea
idéntica con el robot real: el robot de verdad tarda en arrancar y frenar.

---

## Problemas frecuentes

**`ERROR: could not create window` y después `Connection refused`**

Es el caso más reportado, y **no cancela nada**. Pasa cuando la máquina no
puede abrir una ventana 3D: una VM sin GPU, una sesión remota, o —muy
típico en Linux— **usar Python de Anaconda/Miniconda**, que trae su propio
`glfw` y choca con el del sistema. La pista es la palabra `EGL` en el error.

El simulador **lo detecta y sigue en modo consola**, dibujando el recorrido
del robot en texto. El backend levanta igual y la app del alumno funciona
completa: para este TP la ventana 3D no aporta nada, porque lo que se mira
es la app en el celular.

Si igual querés la ventana, probá con el Python del sistema en vez del de
conda:

```bash
conda deactivate
python3 -m pip install --user mujoco
./INICIAR_TP04.sh
```

> Si el error dice `Connection refused` pero **no** aparece antes
> `could not create window`, entonces sí es otra cosa: el simulador no llegó
> a levantar. Mirá las líneas de arriba en esa misma ventana.

**No hace falta compilar ni instalar el SDK de Unitree.** Ni `unitree_sdk2`,
ni `unitree_sdk2_python`, ni CycloneDDS, ni CMake. Este TP habla con el
simulador por un socket local: alcanza con `pip install mujoco`. Si una guía
te manda a compilar algo, es de una versión anterior.

**La app del alumno no llega al backend** — casi siempre es la red, no el
código. Que abra `http://<IP>:8000/docs` en el navegador **del celular**: si no
carga, el celular no está en la misma red.

**Todo devuelve `401`** — falta el token o venció la sesión.

**`409` al iniciar sesión** — hay otra sesión abierta. En el simulador puede ser
una vieja del mismo alumno.

**"El robot se mueve un instante y para"** — está mandando un solo `/mover`. Ver
la sección del joystick.
