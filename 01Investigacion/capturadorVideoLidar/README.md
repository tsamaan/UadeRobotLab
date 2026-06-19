# Capturador Video/LiDAR Unitree Go2

Herramienta para tomar una ventana corta de datos del robot y dejar archivos listos para procesar con algoritmos externos o IA.

## Que captura

- Camara frontal Go2: en el robot real escucha `rt/frontvideostream` y guarda `front_camera.h264`; si `ffmpeg` esta disponible tambien arma `front_camera.mp4`.
- Radar/LiDAR UTLiDAR: escucha un topico DDS `PointCloud2` y exporta `.pcd`, `.csv`, `.bin` y metadatos `.json`.
- Modo demo: genera datos sinteticos sin robot para probar el flujo.

## Red del robot

Para el Go2 conectado por RJ45 suele funcionar dejar la placa Ethernet de Windows en una IP fija de la red del robot, por ejemplo:

```text
IP:      192.168.123.222
Mascara: 255.255.255.0
```

En las pruebas de laboratorio el robot respondio en `192.168.123.18` y `192.168.123.161`, usando la interfaz de Windows llamada `Ethernet`.

## Uso desde codigo fuente

La interfaz grafica se abre sin parametros:

```powershell
cd 01Investigacion\capturadorVideoLidar
python main.py
```

Desde la ventana se puede conectar al robot, ver la camara frontal, ver la nube LiDAR en planta y guardar video/LiDAR en la carpeta de salida.

El modo consola sigue disponible con `--console`:

```powershell
cd 01Investigacion\capturadorVideoLidar
python main.py --console --mode both --interface Ethernet --duration 10 --fps 10
```

Modo consola interactivo:

```powershell
python main.py --console
```

Para ver interfaces de red:

```powershell
python main.py --list-interfaces
```

Prueba sin robot:

```powershell
python main.py --console --demo --mode both --duration 3 --fps 3
```

Prueba grafica sin robot:

```powershell
python main.py --gui --demo
```

## Archivos de salida

Por defecto se crea:

```text
captures/<fecha>/
  camera_frames/
    frame_000001.jpg        # solo si el stream entrega imagenes JPEG
  front_camera.h264         # stream real del Go2
  front_camera.mp4          # si ffmpeg esta disponible
  lidar/
    cloud_000001.pcd
    cloud_000001.csv
    cloud_000001.bin
    cloud_000001.json
  camera_metadata.json
  lidar_metadata.json
  session_metadata.json
```

## Topicos LiDAR

El topico por defecto es:

```text
rt/utlidar/cloud
```

Si en el robot aparece con otro nombre, usar:

```powershell
python main.py --mode lidar --lidar-topic rt/otro/topico
```

Tambien se puede enviar el switch del UTLiDAR:

```powershell
python main.py --mode lidar --lidar-switch on
```

## Generar un paquete con .exe para Windows

En la PC de build hace falta Python solo una vez. El docente que recibe el zip no necesita instalar Python ni dependencias.

La app usa `cyclonedds>=11`, que en Windows se instala por wheel y permite descubrir dinamicamente los tipos DDS publicados por el robot. El SDK local de Unitree queda incluido como respaldo, sin forzar sus dependencias antiguas. Si `ffmpeg.exe` esta en el `PATH` de la PC de build, tambien se copia al zip para poder generar MP4 en otra PC sin instalar nada.

```powershell
cd 01Investigacion\capturadorVideoLidar
.\generar_exe_windows.bat
```

La salida queda en:

```text
dist\CapturadorVideoLidar-win64.zip
```

Enviar ese zip. La otra persona lo descomprime y ejecuta:

```text
CapturadorVideoLidar.exe
```

El programa abre una ventana grafica. Para usar el modo consola desde el `.exe`, ejecutar:

```powershell
CapturadorVideoLidar.exe --console
```

## Prueba real realizada

Con el robot conectado por RJ45 y la placa `Ethernet` en `192.168.123.222`, se verifico:

- Descubrimiento DDS del robot.
- Captura LiDAR desde `rt/utlidar/cloud`: nubes de 1440 puntos exportadas a `.pcd`, `.csv`, `.bin` y `.json`.
- Captura de camara desde `rt/frontvideostream`: stream H.264 1280x720 convertido a `.mp4` cuando `ffmpeg` esta disponible.

## Nota sobre ESP32CAM

Esta herramienta cubre camara frontal del Go2 y UTLiDAR. Para ESP32CAM por USB puede hacer falta el driver CH341 en Windows. Si la ESP32CAM se usa por Ethernet/WiFi con stream HTTP/MJPEG, se puede agregar como una tercera fuente sin depender del CH341.
