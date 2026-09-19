# Dashboard de telemetría — TP05

Muestra en vivo lo que le pasa a un robot Unitree (Go2 o G1): batería,
inclinación, patas apoyadas, ángulo de cada motor en el tiempo, y una tabla con
ángulo, velocidad, torque y temperatura de todos los motores.

Son tres archivos y **no hay que instalar nada**:

| Archivo | Qué tiene |
|---|---|
| `index.html` | la estructura de la pantalla: qué paneles hay |
| `estilos.css` | cómo se ve: colores, tamaños, grilla |
| `app.js` | la lógica: conectarse, recibir datos, dibujar |

## Cómo abrirlo

1. Levantá el simulador y el backend con `INICIAR_TP05` (ver `../LEEME_ESTUDIANTE.md`).
2. Abrí `index.html` con doble clic. Se conecta solo a `localhost`.
3. Si el backend está en otra máquina, escribí su IP arriba y tocá **Conectar**.
   También se puede abrir con `index.html?ip=10.0.0.5`.

Si el navegador se pone quisquilloso con archivos locales, servilo:

```bash
python3 -m http.server 8080 --directory mi_dashboard
```

y entrá a <http://localhost:8080>.

## Cómo leer la pastilla de estado (arriba a la derecha)

| Dice | Significa |
|---|---|
| **en vivo · WebSocket** | todo bien, datos en tiempo real |
| **en vivo · polling** | todo bien, pero por el plan B (el backend no tiene WebSocket) |
| **datos congelados** | llegan mensajes pero siempre el mismo dato: se cerró el simulador o el robot dejó de publicar |
| **no llegan datos** | la conexión está abierta pero no llega nada |
| **sin conexión** | no responde el backend; reintenta cada 3 s |

## Documentación

- **[docs/COMO_FUNCIONA.md](docs/COMO_FUNCIONA.md)** — explicación desde cero:
  cómo lo construimos, cómo viaja un dato del robot a la pantalla, qué hace
  cada parte del código.
- **[docs/adr/](docs/adr/README.md)** — las decisiones importantes, una por
  archivo, con el problema, lo que se evaluó, lo que se descartó y qué salió
  (lo esperado y lo no esperado).
