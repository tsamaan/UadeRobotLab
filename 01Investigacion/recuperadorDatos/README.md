# Unitree Motor Monitor — Go2 / G1 EDU

App de escritorio para monitorear en tiempo real los motores y sensores de los robots Unitree Go2 y G1 (versión EDU). Pensada para docentes y alumnos de Ingeniería Electrónica y Electromecánica.

## Datos que muestra

**Por cada motor** (12 en Go2, 29 en G1):
- Ángulo (grados)
- Velocidad angular (rad/s)
- Torque estimado (N·m)
- Temperatura (°C) con indicador de color

**Energía general:**
- Voltaje (V), Corriente (A), Potencia (W)

**Batería (BMS):**
- Carga (%), Corriente (mA), Temperatura NTC, Ciclos, Voltaje por celda (mV)

**IMU:**
- Roll, Pitch, Yaw (grados)
- Acelerómetro (x, y, z en m/s²)
- Giroscopio (x, y, z en rad/s)

**Fuerza en patas:**
- Fuerza de contacto por pata (FR, FL, RR, RL)

**Exportar:**
- Capturar mediciones puntuales y exportar todo a CSV

## Estructura del proyecto

```
electroSim/
├── main.py                      # Punto de entrada
├── unitree_monitor/
│   ├── __init__.py
│   ├── joint_maps.py            # Mapeo de motores por robot
│   ├── dds_reader.py            # Hilo DDS que lee datos del robot
│   └── ui_main.py               # Interfaz gráfica (PyQt6)
├── requirements.txt             # Dependencias Python
├── generar_exe_windows.bat      # Script para generar .exe en Windows
├── ejecutar.bat                 # Lanzador rápido Windows
├── ejecutar.sh                  # Lanzador rápido Linux
└── README.md
```

## Opción 1: Usar el ejecutable (sin instalar nada)

Si alguien ya generó el ejecutable para tu sistema operativo:

- **Linux:** descargar `UnitreeMotorMonitor`, darle permisos (`chmod +x UnitreeMotorMonitor`) y doble click
- **Windows:** descargar `UnitreeMotorMonitor.exe` y doble click

## Opción 2: Instalar desde código fuente

### Linux / Mac

```bash
# 1. Clonar el proyecto
git clone https://github.com/tomasbondUade/electroSim.git
cd electroSim

# 2. Crear entorno virtual
python3 -m venv env
source env/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Instalar el SDK de Unitree
git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
pip install -e unitree_sdk2_python

# 5. En Ubuntu, instalar esta dependencia del sistema
sudo apt install libxcb-cursor0

# 6. Ejecutar
python3 main.py
```

Para las siguientes veces, solo hace falta:
```bash
cd electroSim
source env/bin/activate
python3 main.py
```

O usar el lanzador:
```bash
chmod +x ejecutar.sh
./ejecutar.sh
```

### Windows

**Requisitos previos (instalar una sola vez):**

1. **Python 3.12+** desde https://www.python.org/downloads/ — al instalar, tildar "Add python.exe to PATH"
2. **Git** desde https://git-scm.com/download/win — instalar con opciones por defecto

**Instalación:**

Abrir PowerShell y ejecutar:
```powershell
git clone https://github.com/tomasbondUade/electroSim.git
cd electroSim
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
pip install -e unitree_sdk2_python
python main.py
```

Para las siguientes veces, usar `ejecutar.bat` (doble click).

## Generar ejecutable

### Linux
```bash
source env/bin/activate
pip install pyinstaller
pyinstaller --onefile --windowed --name "UnitreeMotorMonitor" \
  --collect-all unitree_sdk2py --collect-all cyclonedds main.py
```
El ejecutable queda en `dist/UnitreeMotorMonitor`.

### Windows
Doble click en `generar_exe_windows.bat` y esperar. El ejecutable queda en `dist\UnitreeMotorMonitor.exe`.

O manualmente en PowerShell:
```powershell
env\Scripts\activate
pip install pyinstaller
pyinstaller --onefile --windowed --name "UnitreeMotorMonitor" --collect-all unitree_sdk2py --collect-all cyclonedds main.py
```

## Uso de la app

1. Conectar la PC al robot por cable Ethernet o WiFi AP del robot
2. Abrir la app
3. Seleccionar el robot: **Go2** o **G1**
4. Seleccionar la interfaz de red del desplegable (la que conecta al robot)
5. Presionar **Conectar**
6. Los datos se actualizan en tiempo real
7. Usar **Capturar dato actual** para guardar una medición
8. Usar **Exportar CSV** para descargar todas las capturas

## Motores por robot

### Go2 (12 motores)
| Índice | Motor | Grupo |
|--------|-------|-------|
| 0-2 | FR_Hip, FR_Thigh, FR_Calf | Pata Frontal Derecha |
| 3-5 | FL_Hip, FL_Thigh, FL_Calf | Pata Frontal Izquierda |
| 6-8 | RR_Hip, RR_Thigh, RR_Calf | Pata Trasera Derecha |
| 9-11 | RL_Hip, RL_Thigh, RL_Calf | Pata Trasera Izquierda |

### G1 (29 motores)
| Índice | Grupo |
|--------|-------|
| 0-5 | Pierna Izquierda |
| 6-11 | Pierna Derecha |
| 12-14 | Cintura |
| 15-18 | Brazo Izquierdo |
| 19-21 | Mano Izquierda |
| 22-25 | Brazo Derecho |
| 26-28 | Mano Derecha |

## Solución de problemas

**"No module named unitree_sdk2py":** El SDK no está instalado. Seguir el paso 4 de la instalación.

**"does not match an available interface":** La interfaz de red seleccionada no está conectada al robot. Verificar la conexión y seleccionar la interfaz correcta.

**La app se tilda:** Si los datos llegan muy rápido, verificar que el archivo `dds_reader.py` tenga el limitador de frecuencia (máximo 10 updates por segundo).

**Temperatura siempre en amarillo/rojo:** Es normal si el robot estuvo en uso. Verde < 40°C, Amarillo 40-60°C, Rojo > 60°C.
