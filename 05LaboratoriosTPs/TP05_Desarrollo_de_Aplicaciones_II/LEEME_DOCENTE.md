# TP05 — Desarrollo de Aplicaciones II
## Guía para el docente

---

## Qué es esto

Un laboratorio para que los alumnos hagan un **dashboard web de telemetría** de
un robot Unitree, sin tener el robot delante.

El paquete levanta **el simulador oficial de Unitree** y **el mismo backend de
telemetría** que corre en la notebook del laboratorio el día de la visita. El
dashboard del alumno le pega por HTTP o WebSocket.

**Es sólo lectura.** No hay ningún endpoint que mueva el robot: eso lo garantiza
la API, que no tiene ninguno.

---

## Qué evalúa

Consumo de una API ajena y visualización de datos en tiempo real. El alumno
tiene que leer un contrato, elegir qué mostrar y cómo, y manejar un WebSocket.

`API.md` es ese contrato. Es lo más importante que se le entrega.

---

## Paso a paso

1. **Instalación** (una vez): `INSTALACION.md`. Suma `fastapi` y `uvicorn`.
2. **Levantar**: doble clic en `INICIAR_TP05`. Elige robot, abre el simulador,
   arranca el backend y **muestra la dirección en pantalla**.
3. **El alumno** apunta su dashboard a esa dirección.

Para verificar que todo anda sin abrir nada del alumno: abrir
`http://<IP>:8001/telemetria` en el navegador. Si aparece el JSON, está listo.

---

## El robot se pasea solo

En el simulador el robot **camina un recorrido por su cuenta**: avanza, gira,
hace curvas y para.

Sin eso, el robot quedaría quieto y **todos los gráficos serían líneas rectas**:
un dashboard de un robot inmóvil no se puede evaluar. Con el paseo, el alumno ve
subir el torque y las temperaturas al caminar, y bajar al frenar.

El recorrido es corto y variado a propósito. Con tramos largos, el alumno mira
el gráfico de yaw plano diez segundos y cree que está roto.

Se puede apagar con `--sin-paseo` si hace falta el robot quieto.

---

## ⚠️ Qué es real y qué está derivado

Esto conviene explicarlo en clase, porque es una limitación honesta del
simulador y los alumnos van a preguntar.

El simulador es **cinemático**: mueve el robot pero no calcula física. El bridge
oficial de Unitree publica lo que sale de los sensores de MuJoCo, así que sin
física llegaba casi todo en cero.

| Dato | En el simulador |
|---|---|
| Ángulo de motor | **real** |
| Velocidad de motor | **real** (derivada del movimiento de la articulación) |
| Yaw | **real** |
| Torque | **derivado** del esfuerzo de cada articulación |
| Temperatura | **derivada**: sube con el uso, baja al frenar |
| Roll / pitch | **derivados**: oscilación al caminar |
| Fuerzas de pata | **derivadas** de la fase de la marcha |
| Batería | **inventada** (87 %, baja lentísimo) |

Los derivados **son coherentes con lo que el robot hace**, no ruido decorativo.
Pero no son mediciones: contra el robot real esos números van a ser otros.

Está documentado en `API.md`, en la guía del alumno, y marcado en la respuesta
de la API. Un alumno no debería creer que ve el torque medido de un motor.

---

## Cómo llega al robot real

El backend es el mismo. En la notebook del laboratorio lee del robot por RJ-45
en vez del simulador; los endpoints y el JSON no cambian.

El alumno **cambia sólo la dirección** a la que apunta su dashboard.

A diferencia del TP04, acá **pueden conectarse todos los grupos a la vez**: es
sólo lectura y no hay sesión exclusiva. No hay riesgo de que dos equipos se
peleen por el control, porque nadie controla nada.

---

## Diferencias entre los dos robots

| | Go2 | G1 |
|---|---|---|
| Motores | 12 | 29 |
| Patas reportadas | 4 | — |

El alumno debería consultar `/info` en vez de asumir. Es un buen detalle para
señalar al corregir.

---

## Problemas frecuentes

**`ERROR: could not create window` y después `Connection refused`**

Es el caso más reportado, y **no cancela nada**. Pasa cuando la máquina no
puede abrir una ventana 3D: una VM sin GPU, una sesión remota, o —muy
típico en Linux— **usar Python de Anaconda/Miniconda**, que trae su propio
`glfw` y choca con el del sistema. La pista es la palabra `EGL` en el error.

El simulador **lo detecta y sigue en modo consola**, dibujando el recorrido
del robot en texto. El backend levanta igual y el dashboard del alumno
recibe todos los datos: para este TP la ventana 3D no aporta nada, porque
lo que se mira es el dashboard.

Si igual querés la ventana, probá con el Python del sistema en vez del de
conda:

```bash
conda deactivate
python3 -m pip install --user mujoco
./INICIAR_TP05.sh
```

> Si el error dice `Connection refused` pero **no** aparece antes
> `could not create window`, entonces sí es otra cosa: el simulador no llegó
> a levantar. Mirá las líneas de arriba en esa misma ventana.

**No hace falta compilar ni instalar el SDK de Unitree.** Ni `unitree_sdk2`,
ni `unitree_sdk2_python`, ni CycloneDDS, ni CMake. Este TP habla con el
simulador por un socket local: alcanza con `pip install mujoco`. Si una guía
te manda a compilar algo, es de una versión anterior.

**No llega nada al dashboard** — que abra `http://<IP>:8001/telemetria` en el
navegador. Si el JSON aparece, el problema es del código del alumno.

**Todos los gráficos planos** — el robot está quieto. Ver si arrancó con
`--sin-paseo`, o si el simulador se cerró.

**El WebSocket se corta** — normal si el backend se reinicia. El dashboard
debería reconectar solo; es parte de lo que se evalúa.

**Error de CORS** — el backend permite cualquier origen, así que casi siempre es
que el alumno apunta a la dirección equivocada.
