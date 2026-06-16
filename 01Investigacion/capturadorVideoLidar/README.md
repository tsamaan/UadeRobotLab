# Capturador Video/LiDAR Unitree Go2

Herramienta para tomar una ventana corta de datos del robot y dejar archivos listos para procesar con algoritmos externos o IA.

## Que captura

- Camara frontal Go2: guarda frames JPG. Si OpenCV esta disponible tambien arma `front_camera.avi`.
- Radar/LiDAR UTLiDAR: escucha un topico DDS `PointCloud2` y exporta `.pcd`, `.csv`, `.bin` y metadatos `.json`.
- Modo demo: genera datos sinteticos sin robot para probar el flujo.

## Uso desde codigo fuente

```powershell
cd 01Investigacion\capturadorVideoLidar
python main.py --mode both --interface Ethernet --duration 10 --fps 10
```

Si se abre sin parametros, el programa pregunta los datos necesarios:

```powershell
python main.py
```

Para ver interfaces de red:

```powershell
python main.py --list-interfaces
```

Prueba sin robot:

```powershell
python main.py --demo --mode both --duration 3 --fps 3
```

## Archivos de salida

Por defecto se crea:

```text
captures/<fecha>/
  camera_frames/
    frame_000001.jpg
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

Importante: para capturar LiDAR real, el SDK de Unitree usa CycloneDDS. En Windows, la PC que genera el `.exe` puede necesitar CycloneDDS nativo y las variables `CYCLONEDDS_HOME` o `CMAKE_PREFIX_PATH`. Si `pip` muestra `Could not locate cyclonedds`, falta ese runtime de build. Una vez empaquetado correctamente, las DLL quedan dentro del zip.

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

El programa abre una consola interactiva para elegir interfaz, duracion, camara/LiDAR y carpeta de salida.

## Nota sobre ESP32CAM

Esta herramienta cubre camara frontal del Go2 y UTLiDAR. Para ESP32CAM por USB puede hacer falta el driver CH341 en Windows. Si la ESP32CAM se usa por Ethernet/WiFi con stream HTTP/MJPEG, se puede agregar como una tercera fuente sin depender del CH341.
