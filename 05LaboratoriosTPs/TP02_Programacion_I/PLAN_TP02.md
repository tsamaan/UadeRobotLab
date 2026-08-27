# Plan del laboratorio TP02 — Programación I

Fecha: 2026-08-24
Estado: **paquete del simulador terminado y verificado. Laboratorio físico pendiente.**

---

## 1. La regla que gobierna todo

> ## TODO se expresa en VELOCIDAD y TIEMPO.

Sin excepciones, en toda la cadena: la API, los datos de las misiones, los
enunciados y la documentación.

```python
avanzar(velocidad, tiempo)    # m/s, segundos
girar(velocidad, tiempo)      # rad/s (signo = sentido), segundos
```

- La **distancia es derivada**: `velocidad × tiempo`
- El **ángulo es derivado**: `velocidad × tiempo`
- En `girar`, el **signo** marca el sentido: positivo izquierda, negativo derecha

**No existen `avanzar_metros()` ni `girar_grados()`**, ni siquiera como azúcar
encima de la primitiva. Se probaron y se borraron el 2026-08-24.

**Por qué:** es como piensan el `LocoClient` del SDK y el robot real. `Move()`
no es un paso, es una velocidad con vencimiento. Un helper en metros mentiría
sobre lo que el robot hace. Y calcular esa multiplicación es parte de lo que el
alumno de Programación I tiene que entender.

**Consecuencia práctica:** el TP02 original de la cátedra traía las misiones en
metros y grados (`("avanzar", 0.5, 0.3)` = distancia + velocidad). **Se
reescribieron los datos**, no se adaptó la API.

---

## 2. Los dos productos, y cuál está hecho

| | Producto A — Simulador | Producto B — Laboratorio físico |
|---|---|---|
| Dónde corre | máquina de cada alumno y docente | **sólo** la notebook de Teo |
| Se reparte | sí | no |
| Robot | no toca hardware | RJ-45 al G1 / Go2 |
| Estado | ✅ **terminado y verificado** | ⬜ pendiente |

Lo único que viaja entre los dos es **el archivo del alumno**, `mi_tp02.py`.
Funciona en ambos porque lo que coincide es **el contrato de la API** —
`avanzar(velocidad, tiempo)`, `girar(velocidad, tiempo)`—, no el transporte. En
el paquete esas órdenes van por un socket local; contra el robot, por DDS con el
SDK oficial.

---

## 3. De dónde sale cada pieza

```
UadeRobotLab/
├── 00SDK/
│   └── unitree_sdk2_python/     ← SDK oficial Python  ⚠️ ESTÁ VACÍA, hay que clonarla
├── 04Simuladores/
│   └── unitree_mujoco/          ← simulador oficial: modelos 3D + bridge DDS
└── 05LaboratoriosTPs/
    └── TP02_Programacion_I/     ← este laboratorio
```

| Pieza | Origen | Qué aporta |
|---|---|---|
| **Modelos 3D** (`g1/scene_29dof.xml`, `go2/scene.xml`) | `unitree_mujoco` oficial | los robots que se ven |
| **`UnitreeSdk2Bridge`** | `unitree_mujoco/simulate_python` | publica `rt/lowstate`, escucha `rt/lowcmd` |
| **`LocoClient` / `SportClient`** | `unitree_sdk2_python` | lo que usa el alumno, idéntico al robot real |
| **Servicio de locomoción** | **nuestro** (`servicio_sport.py`) | el oficial **no lo trae**; sin él `Move()` da timeout |
| **Límites de seguridad** | **nuestro** (`safety.py`) | techo físico + perfil de la materia |
| **Consigna del TP** | `labs/laboratorio_tp02/` + el ZIP de la cátedra | qué se evalúa |

### El cruce clave

El simulador oficial de Unitree **no incluye el controlador de locomoción**: el
que hace caminar al G1 corre en la PC interna del robot y Unitree no lo publica.
Verificado leyendo su fuente — el bridge oficial sólo implementa `rt/lowcmd`,
`rt/lowstate`, `rt/sportmodestate` y `rt/wirelesscontroller`.

Por eso este laboratorio **le agrega el servicio `sport` que falta**. Con eso, el
`LocoClient` real del SDK funciona contra el simulador oficial sin modificarlo.

---

## 4. Qué evalúa el TP02

Diseño top-down, funciones modulares, arreglos y validación.

El alumno recibe una lista de comandos y escribe cuatro funciones:

| # | Función | Qué hace |
|---|---|---|
| 1 | `comando_es_valido(comando)` | decide si se puede ejecutar |
| 2 | `ejecutar_comando(robot, comando)` | ejecuta **uno** |
| 3 | `ejecutar_mision(robot, mision, historial)` | recorre la lista entera |
| 4 | `generar_reporte(historial)` | muestra el resumen |

`mi_tp02.py` viene con las cuatro funciones vacías, cada una con su docstring y
un `# TU CODIGO ACA`. **La estructura está dada, la lógica la escribe el alumno.**

### La validación en dos capas

Es el corazón del TP y conviene no romperlo:

1. **La del alumno** (`comando_es_valido`) — atrapa comandos mal formados:
   nombre inexistente, faltan datos, tipos incorrectos, tiempo negativo.
2. **La del robot** (`ErrorDeSeguridad`) — atrapa valores fuera de límite:
   velocidad, tiempo o giro por encima de lo permitido.

`MISION_CON_ERRORES` tiene **7 inválidos deliberados**, repartidos a propósito
entre las dos capas: 4 los caza el alumno, 3 los caza el robot.

Un alumno que sólo valide el nombre del comando pasa 4 de 7 y lo nota en el
reporte. Un alumno que no ponga `try/except` se lleva un choque contra la
segunda capa.

---

## 5. Los límites de la materia

| | |
|---|---|
| Velocidad máxima | 0.20 m/s |
| Velocidad de giro máxima | 0.50 rad/s |
| Tiempo máximo por orden | 10 s |

A 0.20 m/s, 10 segundos son 2 metros.

Vienen del modelo de seguridad acordado: un **techo físico** de 0.25 m/s que
ninguna materia puede superar, y por debajo el perfil pedagógico de cada TP.
`_verificar_perfiles()` corre al importar y explota si alguien sube un número
por encima del techo.

**Rechaza, no recorta.** Un recorte silencioso haría que la distancia recorrida
no fuera `velocidad × tiempo`, y el alumno ajustaría números a ciegas.

La validación que el alumno **ve** vive en `robot.py`, del lado del cliente,
antes de tocar DDS. Es necesario: `Move()` del SDK **descarta el código de
retorno**, así que un rechazo que viniera del simulador sería invisible.

---

## 6. Estructura del paquete

```
TP02_Programacion_I/
├── INSTALACION.md              guía de cero (compartida entre las 7 materias)
├── LEEME_ESTUDIANTE.md         para el alumno
├── LEEME_DOCENTE.md            para el profesor
├── PLAN_TP02.md                este archivo
├── INICIAR_SIMULADOR.sh/.bat   verifica el entorno, pregunta el robot, levanta
├── EJECUTAR_MI_CODIGO.sh/.bat  corre el programa del alumno
├── mi_desarrollo/              ← donde trabaja el alumno
│   ├── mi_tp02.py              4 funciones vacías. Es lo que entrega.
│   ├── misiones.py             dado hecho: 4 misiones de prueba
│   ├── robot.py                puente, no se toca
│   └── LEEME.md
└── entorno/sim/                el motor, no se toca
```

Se regenera con `python3 ~/Escritorio/armar_paquetes.py tp02`. Lo propio de la
materia vive en `~/Escritorio/materiales/tp02/`; lo común, en
`~/Escritorio/materiales/comun/`. **Nunca editar el paquete a mano:** se
sobrescribe al regenerar.

---

## 7. Estado verificado

Corrido el 2026-08-24 desde la carpeta final:

| Prueba | Resultado |
|---|---|
| Verificación del entorno | 5/5 OK |
| Levanta con ventana 3D (G1) | ✅ |
| Levanta con ventana 3D (Go2) | ✅ |
| Bridge oficial DDS | `rt/lowstate`, `rt/lowcmd` activos |
| Servicio de locomoción | `LocoClient` y `SportClient` responden |
| `MISION_BASICA` | 4/4 ejecutados |
| `MISION_CON_ERRORES` | 4 ejecutados, 7 rechazados (correcto) |
| `MISION_CUADRADO` con Go2 | vuelve al origen (x=-0.00, y=-0.01) |
| Ctrl+C | cierra limpio, libera el puerto |

Se escribió una **solución de referencia** para confirmar que el esqueleto es
resoluble y que los 7 errores se detectan donde corresponde. No se distribuye.

---

## 8. Lo que falta

### Laboratorio físico (Producto B)

`~/Escritorio/labs/laboratorio_tp02/` existe pero **todavía no está alineado**
con este paquete:

- Sus misiones siguen en el formato viejo (distancia + velocidad, grados +
  sentido). **Hay que reescribirlas a velocidad y tiempo.**
- Su `utils/safety.py` tiene los números viejos (`VELOCIDAD_MAX = 0.5`), que
  están por **encima del techo físico de 0.25**. Se reemplaza por
  `unitree_lab_core/safety.py`.
- Su `unitree_bridge.py` es una de las 5 copias divergentes; se unifica.

### Antes de la primera visita con robot

- Entorno Python 3.10 para control real (el actual es 3.12.3 y el preflight lo
  rechaza).
- Preflight real con el robot conectado.
- Ensayo completo: una entrega real recorriendo simulador → sandbox → robot.

### Prueba que no puedo hacer yo

Que alguien que no sepa nada siga `INSTALACION.md` en una máquina limpia. Es la
única forma de saber si la documentación sirve.

---

## 9. Documentos relacionados

| Documento | Qué tiene |
|---|---|
| `~/Escritorio/CONTRATO_API.md` | contrato congelado de la API (v1.0) |
| `~/Escritorio/PLAN_LABS_SIMULADOR.md` | plan general de las 7 materias |
| `INSTALACION.md` | instalación del SDK y del simulador oficial |
| `LEEME_DOCENTE.md` | operación en clase |
