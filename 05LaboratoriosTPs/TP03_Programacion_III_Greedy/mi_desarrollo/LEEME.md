# Tu carpeta de trabajo — TP03

| Archivo | Para qué |
|---|---|
| `mi_tp03.py` | Acá escribís tu planificador. **Es lo que trabajás.** |
| `mapas/` | Los mapas de la cátedra. Dados hechos. |
| `recorrido.py` | Dado hecho. Valida tu ruta, la traduce y la ejecuta. |
| `robot.py` | No lo toques. |
| `entrega/` | Se crea sola. **Acá aparece el archivo que entregás.** |

## Cómo lo ejecutás

1. Abrí `INICIAR_SIMULADOR` (carpeta de arriba) y elegí el robot.
2. Esperá la ventana: vas a ver la grilla dibujada en el piso.
3. Doble clic en `EJECUTAR_MI_CODIGO`, o `python3 mi_desarrollo/mi_tp03.py`.

## Los colores de la grilla

| Color | Qué es |
|---|---|
| Verde | celda de inicio |
| Azul | celda de destino |
| Rojo (caja alta) | obstáculo |
| Amarillo (baldosa) | zona prohibida |
| Gris | celda libre |
| Esferas naranjas | tu ruta |

## Ver el mapa sin abrir el simulador

```python
from recorrido import cargar_mapa, mostrar_mapa
mapa = cargar_mapa("nivel1_directo")
mostrar_mapa(mapa)
```
