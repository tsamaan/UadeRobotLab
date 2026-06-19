from __future__ import annotations

import argparse
import math
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QObject, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from .camera import _convert_h264_to_mp4, _find_ffmpeg, _is_jpeg, _looks_like_h264
from .dds_dynamic import make_dynamic_reader
from .demo import synthetic_room_points
from .pointcloud import (
    parse_xyz_points,
    pointcloud_metadata,
    write_csv_points,
    write_pcd_ascii,
)
from .utils import ensure_dir, list_network_interfaces, timestamp_slug, value, write_json


FRONT_VIDEO_TOPIC = "rt/frontvideostream"
DEFAULT_LIDAR_TOPIC = "rt/utlidar/cloud"


def default_output_dir() -> Path:
    documents = Path.home() / "Documents"
    if documents.exists():
        return documents / "CapturadorVideoLidar"
    return Path.home() / "CapturadorVideoLidar"


class H264PreviewDecoder:
    def __init__(self, on_frame: Callable[[QImage], None], on_status: Callable[[str], None]) -> None:
        self._on_frame = on_frame
        self._on_status = on_status
        self._process: subprocess.Popen[bytes] | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._stop = threading.Event()

    def start(self) -> bool:
        ffmpeg = _find_ffmpeg()
        if not ffmpeg:
            self._on_status("No encontre ffmpeg.exe para mostrar H264 en vivo.")
            return False

        command = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-fflags",
            "nobuffer",
            "-flags",
            "low_delay",
            "-f",
            "h264",
            "-i",
            "pipe:0",
            "-an",
            "-f",
            "image2pipe",
            "-vcodec",
            "ppm",
            "pipe:1",
        ]
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
        self._process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        self._thread = threading.Thread(target=self._read_loop, name="h264-preview-decoder", daemon=True)
        self._thread.start()
        return True

    def write(self, payload: bytes) -> None:
        with self._lock:
            process = self._process
            if process is None or process.poll() is not None or process.stdin is None:
                return
            try:
                process.stdin.write(payload)
                process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass

    def stop(self) -> None:
        self._stop.set()
        with self._lock:
            process = self._process
            if process is not None:
                try:
                    if process.stdin is not None:
                        process.stdin.close()
                except OSError:
                    pass
                try:
                    process.terminate()
                except OSError:
                    pass
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def _read_loop(self) -> None:
        process = self._process
        if process is None or process.stdout is None:
            return

        stream = process.stdout
        while not self._stop.is_set():
            magic = self._read_token(stream)
            if magic is None:
                break
            if magic != b"P6":
                continue

            width_token = self._read_token(stream)
            height_token = self._read_token(stream)
            max_token = self._read_token(stream)
            if width_token is None or height_token is None or max_token is None:
                break

            try:
                width = int(width_token)
                height = int(height_token)
                max_value = int(max_token)
            except ValueError:
                continue

            if width <= 0 or height <= 0 or max_value != 255:
                continue

            byte_count = width * height * 3
            frame = stream.read(byte_count)
            if len(frame) != byte_count:
                break

            image = QImage(frame, width, height, width * 3, QImage.Format.Format_RGB888).copy()
            self._on_frame(image)

    @staticmethod
    def _read_token(stream: Any) -> bytes | None:
        token = bytearray()
        while True:
            char = stream.read(1)
            if not char:
                return None
            if char == b"#":
                stream.readline()
                continue
            if char.isspace():
                continue
            token.extend(char)
            break

        while True:
            char = stream.read(1)
            if not char or char.isspace():
                break
            if char == b"#":
                stream.readline()
                break
            token.extend(char)
        return bytes(token)


class CameraWorker(QObject):
    frame = Signal(QImage)
    status = Signal(str)
    stats = Signal(dict)
    recording_finished = Signal(str)

    def __init__(self, interface: str | None, session_dir: Path, fps: float, demo: bool = False) -> None:
        super().__init__()
        self.interface = interface
        self.session_dir = session_dir
        self.fps = fps
        self.demo = demo
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._recording = False
        self._finish_requested = False
        self._record_lock = threading.Lock()
        self._h264_file: Any | None = None
        self._h264_path: Path | None = None
        self._h264_packets = 0
        self._jpeg_frames = 0

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="camera-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._finish_recording()

    def set_recording(self, enabled: bool) -> None:
        with self._record_lock:
            self._recording = enabled
            if not enabled:
                self._finish_requested = True

    def _run(self) -> None:
        try:
            if self.demo:
                self._run_demo()
            else:
                self._run_robot()
        except Exception as exc:
            self.status.emit(f"Camara detenida: {exc}")
        finally:
            self._finish_recording()

    def _run_robot(self) -> None:
        self.status.emit("Descubriendo camara DDS...")
        _participant, reader, _datatype = make_dynamic_reader(self.interface, FRONT_VIDEO_TOPIC, runtime_s=6.0)
        decoder = H264PreviewDecoder(self.frame.emit, self.status.emit)
        decoder.start()
        frames_read = 0
        self.status.emit("Camara conectada.")

        try:
            while not self._stop.is_set():
                try:
                    samples = reader.take(N=10)
                except Exception as exc:
                    self.status.emit(f"Camara: {exc}")
                    time.sleep(0.05)
                    continue

                if not samples:
                    self._finish_recording_if_requested()
                    time.sleep(0.02)
                    continue

                for msg in samples:
                    self._finish_recording_if_requested()
                    frames_read += 1
                    payload = bytes(getattr(msg, "data", b"") or b"")
                    if not payload:
                        continue

                    if _is_jpeg(payload):
                        image = QImage.fromData(payload, "JPG")
                        if not image.isNull():
                            self.frame.emit(image)
                        self._record_jpeg(payload)
                    elif _looks_like_h264(payload):
                        decoder.write(payload)
                        self._record_h264(payload)

                    self.stats.emit(
                        {
                            "frames_read": frames_read,
                            "h264_packets": self._h264_packets,
                            "jpeg_frames": self._jpeg_frames,
                        }
                    )
        finally:
            decoder.stop()

    def _run_demo(self) -> None:
        index = 0
        period = 1.0 / max(self.fps, 1.0)
        self.status.emit("Camara demo activa.")
        while not self._stop.is_set():
            index += 1
            image = QImage(960, 540, QImage.Format.Format_RGB32)
            image.fill(QColor("#15191c"))
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            hue = (index * 4) % 360
            painter.fillRect(0, 360, 960, 180, QColor("#2f3937"))
            painter.setPen(QPen(QColor.fromHsv(hue, 150, 230), 8))
            painter.drawEllipse(360 + (index * 8) % 220, 165, 140, 140)
            painter.setPen(QColor("#e8f0ee"))
            painter.drawText(28, 48, "Camara demo")
            painter.drawText(28, 84, f"Frame {index}")
            painter.end()
            self.frame.emit(image)
            self.stats.emit({"frames_read": index, "h264_packets": 0, "jpeg_frames": 0})
            time.sleep(period)

    def _recording_enabled(self) -> bool:
        with self._record_lock:
            return self._recording

    def _finish_recording_if_requested(self) -> None:
        with self._record_lock:
            finish_requested = self._finish_requested
            self._finish_requested = False
        if finish_requested:
            self._finish_recording()

    def _record_h264(self, payload: bytes) -> None:
        if not self._recording_enabled():
            return
        if self._h264_file is None:
            video_dir = ensure_dir(self.session_dir / "video")
            self._h264_path = video_dir / f"front_camera_{timestamp_slug()}.h264"
            self._h264_file = self._h264_path.open("wb")
            self._h264_packets = 0
            self.status.emit(f"Grabando video: {self._h264_path.name}")
        self._h264_file.write(payload)
        self._h264_packets += 1

    def _record_jpeg(self, payload: bytes) -> None:
        if not self._recording_enabled():
            return
        frames_dir = ensure_dir(self.session_dir / "video" / "jpeg_frames")
        self._jpeg_frames += 1
        (frames_dir / f"frame_{self._jpeg_frames:06d}.jpg").write_bytes(payload)

    def _finish_recording(self) -> None:
        h264_path = self._h264_path
        h264_packets = self._h264_packets
        if self._h264_file is not None:
            try:
                self._h264_file.close()
            except OSError:
                pass
            self._h264_file = None

        if h264_path is None or not h264_path.exists() or h264_packets <= 0:
            return

        errors: list[str] = []
        mp4_path = h264_path.with_suffix(".mp4")
        mp4_ok = _convert_h264_to_mp4(h264_path, mp4_path, self.fps, errors)
        metadata = {
            "source": "unitree_go2_frontvideostream_gui",
            "h264_path": str(h264_path),
            "mp4_path": str(mp4_path) if mp4_ok else None,
            "h264_packets_written": h264_packets,
            "jpeg_frames_written": self._jpeg_frames,
            "errors": errors,
        }
        write_json(h264_path.with_name(h264_path.stem + "_metadata.json"), metadata)
        final_path = mp4_path if mp4_ok else h264_path
        self.recording_finished.emit(str(final_path))
        self.status.emit(f"Video guardado: {final_path.name}")
        self._h264_path = None
        self._h264_packets = 0


class LidarWorker(QObject):
    cloud = Signal(object, object)
    status = Signal(str)
    stats = Signal(dict)
    recording_finished = Signal(str)

    def __init__(self, interface: str | None, topic: str, session_dir: Path, demo: bool = False) -> None:
        super().__init__()
        self.interface = interface
        self.topic = topic
        self.session_dir = session_dir
        self.demo = demo
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._recording = False
        self._record_lock = threading.Lock()
        self._save_lock = threading.Lock()
        self._cloud_count = 0
        self._saved_cloud_count = 0
        self._snapshot_count = 0
        self._last_cloud: tuple[list[dict[str, float]], dict[str, Any], bytes] | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="lidar-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._write_lidar_metadata()

    def set_recording(self, enabled: bool) -> None:
        with self._record_lock:
            self._recording = enabled
        if not enabled:
            self._write_lidar_metadata()

    def save_snapshot(self) -> None:
        with self._save_lock:
            last_cloud = self._last_cloud
        if last_cloud is None:
            self.status.emit("Todavia no hay nube LiDAR para guardar.")
            return
        points, metadata, raw_data = last_cloud
        path = self._save_cloud(points, metadata, raw_data, snapshot=True)
        self.recording_finished.emit(str(path))
        self.status.emit(f"Nube guardada: {path.name}")

    def _run(self) -> None:
        try:
            if self.demo:
                self._run_demo()
            else:
                self._run_robot()
        except Exception as exc:
            self.status.emit(f"LiDAR detenido: {exc}")
        finally:
            self._write_lidar_metadata()

    def _run_robot(self) -> None:
        self.status.emit(f"Descubriendo LiDAR DDS en {self.topic}...")
        _participant, reader, _datatype = make_dynamic_reader(self.interface, self.topic, runtime_s=6.0)
        self.status.emit("LiDAR conectado.")
        while not self._stop.is_set():
            try:
                samples = reader.take(N=5)
            except Exception as exc:
                self.status.emit(f"LiDAR: {exc}")
                time.sleep(0.05)
                continue

            if not samples:
                time.sleep(0.02)
                continue

            for msg in samples:
                self._publish_cloud(msg)

    def _run_demo(self) -> None:
        base_points = synthetic_room_points()
        tick = 0
        self.status.emit("LiDAR demo activo.")
        while not self._stop.is_set():
            tick += 1
            angle = tick * 0.05
            points: list[dict[str, float]] = []
            for point in base_points:
                x = point["x"]
                y = point["y"]
                points.append(
                    {
                        "x": x * math.cos(angle) - y * math.sin(angle),
                        "y": x * math.sin(angle) + y * math.cos(angle),
                        "z": point["z"],
                        "intensity": point.get("intensity", 0.0),
                    }
                )
            metadata = {
                "source": "demo",
                "topic": "demo",
                "parsed_points": len(points),
                "received_at": time.time(),
            }
            raw_data = b""
            self._update_cloud(points, metadata, raw_data)
            time.sleep(0.35)

    def _publish_cloud(self, msg: object) -> None:
        metadata = pointcloud_metadata(msg)
        metadata["received_at"] = time.time()
        metadata["topic"] = self.topic
        metadata["capture_backend"] = "cyclonedds_dynamic_gui"
        raw_data = bytes(value(msg, "data", b"") or b"")
        points = parse_xyz_points(msg)
        metadata["parsed_points"] = len(points)
        self._update_cloud(points, metadata, raw_data)

    def _update_cloud(self, points: list[dict[str, float]], metadata: dict[str, Any], raw_data: bytes) -> None:
        self._cloud_count += 1
        with self._save_lock:
            self._last_cloud = (points, metadata, raw_data)
        self.cloud.emit(points, metadata)
        self.stats.emit(
            {
                "clouds": self._cloud_count,
                "points": len(points),
                "saved_clouds": self._saved_cloud_count + self._snapshot_count,
            }
        )
        if self._recording_enabled():
            self._save_cloud(points, metadata, raw_data, snapshot=False)

    def _recording_enabled(self) -> bool:
        with self._record_lock:
            return self._recording

    def _save_cloud(
        self,
        points: list[dict[str, float]],
        metadata: dict[str, Any],
        raw_data: bytes,
        snapshot: bool,
    ) -> Path:
        with self._save_lock:
            lidar_dir = ensure_dir(self.session_dir / "lidar")
            if snapshot:
                self._snapshot_count += 1
                stem = f"snapshot_{timestamp_slug()}"
            else:
                self._saved_cloud_count += 1
                stem = f"cloud_{self._saved_cloud_count:06d}"

            if raw_data:
                (lidar_dir / f"{stem}.bin").write_bytes(raw_data)
            if points:
                write_pcd_ascii(lidar_dir / f"{stem}.pcd", points)
                write_csv_points(lidar_dir / f"{stem}.csv", points)

            saved_metadata = dict(metadata)
            saved_metadata["parsed_points"] = len(points)
            saved_metadata["raw_byte_count"] = len(raw_data)
            saved_metadata["saved_at"] = time.time()
            saved_metadata["snapshot"] = snapshot
            json_path = lidar_dir / f"{stem}.json"
            write_json(json_path, saved_metadata)
            return json_path

    def _write_lidar_metadata(self) -> None:
        if self._saved_cloud_count <= 0 and self._snapshot_count <= 0:
            return
        metadata = {
            "source": "unitree_go2_utlidar_gui",
            "topic": self.topic,
            "clouds_seen": self._cloud_count,
            "clouds_written": self._saved_cloud_count,
            "snapshots_written": self._snapshot_count,
            "files_written": self._saved_cloud_count + self._snapshot_count,
            "lidar_dir": str(self.session_dir / "lidar"),
            "errors": [],
        }
        write_json(self.session_dir / "lidar_metadata.json", metadata)


class VideoView(QLabel):
    def __init__(self) -> None:
        super().__init__("Sin video")
        self._image: QImage | None = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(480, 270)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background:#101417; color:#8b9794; border:1px solid #29312f;")

    def set_image(self, image: QImage) -> None:
        self._image = image
        self._refresh()

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        self._refresh()

    def _refresh(self) -> None:
        if self._image is None or self._image.isNull():
            self.setText("Sin video")
            return
        pixmap = QPixmap.fromImage(self._image)
        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setText("")
        self.setPixmap(scaled)


class LidarView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._points: list[dict[str, float]] = []
        self.setMinimumSize(460, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_points(self, points: list[dict[str, float]]) -> None:
        self._points = points[-5000:]
        self.update()

    def paintEvent(self, event: Any) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        rect = self.rect()
        painter.fillRect(rect, QColor("#101417"))

        width = max(1, rect.width())
        height = max(1, rect.height())
        center_x = width * 0.5
        center_y = height * 0.53
        radius = min(width, height) * 0.44

        usable_points = [
            point
            for point in self._points
            if math.isfinite(float(point.get("x", 0.0))) and math.isfinite(float(point.get("y", 0.0)))
        ]
        max_abs = 3.0
        if usable_points:
            max_abs = max(
                1.5,
                min(
                    12.0,
                    max(max(abs(float(point["x"])), abs(float(point["y"]))) for point in usable_points) * 1.15,
                ),
            )
        scale = radius / max_abs

        grid_pen = QPen(QColor("#26302e"), 1)
        painter.setPen(grid_pen)
        for meters in range(1, int(math.ceil(max_abs)) + 1):
            r = meters * scale
            painter.drawEllipse(int(center_x - r), int(center_y - r), int(r * 2), int(r * 2))
        painter.drawLine(int(center_x - radius), int(center_y), int(center_x + radius), int(center_y))
        painter.drawLine(int(center_x), int(center_y - radius), int(center_x), int(center_y + radius))

        painter.setPen(QPen(QColor("#d7dedb"), 2))
        robot_w = 16
        robot_h = 24
        painter.drawLine(int(center_x), int(center_y - robot_h), int(center_x - robot_w), int(center_y + robot_h))
        painter.drawLine(int(center_x), int(center_y - robot_h), int(center_x + robot_w), int(center_y + robot_h))
        painter.drawLine(int(center_x - robot_w), int(center_y + robot_h), int(center_x + robot_w), int(center_y + robot_h))

        if not usable_points:
            painter.setPen(QColor("#8b9794"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Sin LiDAR")
            painter.end()
            return

        for point in usable_points:
            x = float(point["x"])
            y = float(point["y"])
            z = float(point.get("z", 0.0))
            px = int(center_x + y * scale)
            py = int(center_y - x * scale)
            if px < 0 or py < 0 or px >= width or py >= height:
                continue
            color = QColor("#73e2a7") if z < 0.35 else QColor("#f2b35d")
            painter.setPen(color)
            painter.drawPoint(px, py)

        painter.setPen(QColor("#b8c4c0"))
        painter.drawText(12, 22, f"{len(usable_points)} puntos")
        painter.drawText(12, 44, f"Radio {max_abs:.1f} m")
        painter.end()


class MainWindow(QMainWindow):
    def __init__(
        self,
        initial_interface: str | None = None,
        output_dir: Path | None = None,
        demo: bool = False,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Capturador Video/LiDAR Go2")
        self.resize(1280, 760)
        self.camera_worker: CameraWorker | None = None
        self.lidar_worker: LidarWorker | None = None
        self.session_dir: Path | None = None
        self.demo_default = demo
        self._build_ui(initial_interface, output_dir or default_output_dir())
        self._apply_style()

    def _build_ui(self, initial_interface: str | None, output_dir: Path) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 10)
        layout.setSpacing(10)

        toolbar = QFrame()
        toolbar.setObjectName("toolbar")
        grid = QGridLayout(toolbar)
        grid.setContentsMargins(12, 10, 12, 10)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        self.interface_combo = QComboBox()
        self._refresh_interfaces(initial_interface)
        refresh_button = QPushButton("Actualizar")
        refresh_button.clicked.connect(lambda: self._refresh_interfaces(self.interface_combo.currentText()))

        self.topic_edit = QLineEdit(DEFAULT_LIDAR_TOPIC)
        self.output_edit = QLineEdit(str(output_dir))
        browse_button = QPushButton("Carpeta")
        browse_button.clicked.connect(self._choose_output_dir)
        open_output_button = QPushButton("Abrir salida")
        open_output_button.clicked.connect(self._open_output_dir)

        self.demo_check = QCheckBox("Demo")
        self.demo_check.setChecked(self.demo_default)

        self.start_button = QPushButton("Conectar")
        self.start_button.clicked.connect(self.start_capture)
        self.stop_button = QPushButton("Detener")
        self.stop_button.clicked.connect(self.stop_capture)
        self.stop_button.setEnabled(False)

        self.video_record_button = QPushButton("Grabar video")
        self.video_record_button.setCheckable(True)
        self.video_record_button.setEnabled(False)
        self.video_record_button.toggled.connect(self._toggle_video_recording)

        self.lidar_record_button = QPushButton("Guardar LiDAR")
        self.lidar_record_button.setCheckable(True)
        self.lidar_record_button.setEnabled(False)
        self.lidar_record_button.toggled.connect(self._toggle_lidar_recording)

        self.snapshot_button = QPushButton("Nube actual")
        self.snapshot_button.setEnabled(False)
        self.snapshot_button.clicked.connect(self._save_lidar_snapshot)

        grid.addWidget(QLabel("Interfaz"), 0, 0)
        grid.addWidget(self.interface_combo, 0, 1)
        grid.addWidget(refresh_button, 0, 2)
        grid.addWidget(QLabel("Topico LiDAR"), 0, 3)
        grid.addWidget(self.topic_edit, 0, 4)
        grid.addWidget(self.demo_check, 0, 5)
        grid.addWidget(QLabel("Salida"), 1, 0)
        grid.addWidget(self.output_edit, 1, 1, 1, 3)
        grid.addWidget(browse_button, 1, 4)
        grid.addWidget(open_output_button, 1, 5)

        button_row = QHBoxLayout()
        for button in (
            self.start_button,
            self.stop_button,
            self.video_record_button,
            self.lidar_record_button,
            self.snapshot_button,
        ):
            button.setMinimumHeight(34)
            button_row.addWidget(button)
        button_row.addStretch(1)
        grid.addLayout(button_row, 2, 0, 1, 6)
        grid.setColumnStretch(4, 1)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = self._make_panel("Camara frontal")
        self.video_view = VideoView()
        left.layout().addWidget(self.video_view)
        self.camera_stats = QLabel("Frames: 0")
        left.layout().addWidget(self.camera_stats)

        right = self._make_panel("LiDAR")
        self.lidar_view = LidarView()
        right.layout().addWidget(self.lidar_view)
        self.lidar_stats = QLabel("Nubes: 0 | Puntos: 0")
        right.layout().addWidget(self.lidar_stats)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([680, 560])

        layout.addWidget(toolbar)
        layout.addWidget(splitter, 1)
        self.setCentralWidget(root)

        status = QStatusBar()
        self.setStatusBar(status)
        self.statusBar().showMessage("Listo.")

    def _make_panel(self, title: str) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        label = QLabel(title)
        label.setObjectName("panelTitle")
        layout.addWidget(label)
        return panel

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #1a1f21;
                color: #e6ece9;
                font-family: Segoe UI, Arial, sans-serif;
                font-size: 10pt;
            }
            #toolbar, #panel {
                background: #202729;
                border: 1px solid #34403d;
                border-radius: 6px;
            }
            #panelTitle {
                color: #f1f5f3;
                font-size: 12pt;
                font-weight: 600;
            }
            QLineEdit, QComboBox {
                background: #111618;
                border: 1px solid #3a4643;
                border-radius: 4px;
                padding: 6px;
                color: #edf3f0;
            }
            QPushButton {
                background: #2f3a3b;
                border: 1px solid #465553;
                border-radius: 4px;
                padding: 6px 12px;
                color: #f4f7f6;
            }
            QPushButton:hover {
                background: #3a4747;
            }
            QPushButton:checked {
                background: #2f6f55;
                border-color: #65b88c;
            }
            QPushButton:disabled {
                color: #73807c;
                background: #252b2d;
                border-color: #30383a;
            }
            QStatusBar {
                background: #161b1d;
                color: #c8d2ce;
            }
            """
        )

    def _refresh_interfaces(self, preferred: str | None = None) -> None:
        interfaces = list_network_interfaces()
        self.interface_combo.clear()
        self.interface_combo.addItem("Auto")
        for name in interfaces:
            self.interface_combo.addItem(name)
        target = preferred or ("Ethernet" if "Ethernet" in interfaces else None)
        if target:
            index = self.interface_combo.findText(target)
            if index >= 0:
                self.interface_combo.setCurrentIndex(index)

    def _choose_output_dir(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Carpeta de salida", self.output_edit.text())
        if selected:
            self.output_edit.setText(selected)

    def _open_output_dir(self) -> None:
        target = self.session_dir or Path(self.output_edit.text().strip() or default_output_dir())
        ensure_dir(target)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target.resolve())))

    def start_capture(self) -> None:
        if self.camera_worker is not None or self.lidar_worker is not None:
            return

        interface_text = self.interface_combo.currentText().strip()
        interface = None if not interface_text or interface_text == "Auto" else interface_text
        output_base = Path(self.output_edit.text().strip() or "captures")
        self.session_dir = ensure_dir(output_base / f"gui_{timestamp_slug()}")
        topic = self.topic_edit.text().strip() or DEFAULT_LIDAR_TOPIC
        demo = self.demo_check.isChecked()

        self.camera_worker = CameraWorker(interface, self.session_dir, fps=15.0, demo=demo)
        self.lidar_worker = LidarWorker(interface, topic, self.session_dir, demo=demo)

        self.camera_worker.frame.connect(self.video_view.set_image)
        self.camera_worker.status.connect(self._show_status)
        self.camera_worker.stats.connect(self._update_camera_stats)
        self.camera_worker.recording_finished.connect(self._show_saved)

        self.lidar_worker.cloud.connect(self._update_lidar_cloud)
        self.lidar_worker.status.connect(self._show_status)
        self.lidar_worker.stats.connect(self._update_lidar_stats)
        self.lidar_worker.recording_finished.connect(self._show_saved)

        self.camera_worker.start()
        self.lidar_worker.start()
        self._set_running(True)
        self._show_status(f"Sesion: {self.session_dir}")

    def stop_capture(self) -> None:
        if self.video_record_button.isChecked():
            self.video_record_button.setChecked(False)
        if self.lidar_record_button.isChecked():
            self.lidar_record_button.setChecked(False)

        if self.camera_worker is not None:
            self.camera_worker.stop()
            self.camera_worker = None
        if self.lidar_worker is not None:
            self.lidar_worker.stop()
            self.lidar_worker = None
        self._set_running(False)
        self._show_status("Captura detenida.")

    def _set_running(self, running: bool) -> None:
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        self.video_record_button.setEnabled(running)
        self.lidar_record_button.setEnabled(running)
        self.snapshot_button.setEnabled(running)
        self.interface_combo.setEnabled(not running)
        self.topic_edit.setEnabled(not running)
        self.demo_check.setEnabled(not running)

    def _toggle_video_recording(self, enabled: bool) -> None:
        self.video_record_button.setText("Detener video" if enabled else "Grabar video")
        if self.camera_worker is not None:
            self.camera_worker.set_recording(enabled)

    def _toggle_lidar_recording(self, enabled: bool) -> None:
        self.lidar_record_button.setText("Detener LiDAR" if enabled else "Guardar LiDAR")
        if self.lidar_worker is not None:
            self.lidar_worker.set_recording(enabled)
        if not enabled and self.session_dir is not None:
            self._save_lidar_map_png("mapa_lidar_final")

    def _save_lidar_snapshot(self) -> None:
        if self.lidar_worker is not None:
            self.lidar_worker.save_snapshot()
        self._save_lidar_map_png("mapa_lidar_actual")

    def _save_lidar_map_png(self, prefix: str) -> None:
        if self.session_dir is None:
            return
        lidar_dir = ensure_dir(self.session_dir / "lidar")
        png_path = lidar_dir / f"{prefix}_{timestamp_slug()}.png"
        if self.lidar_view.grab().save(str(png_path), "PNG"):
            self.statusBar().showMessage(f"Mapa guardado: {png_path}")

    def _update_camera_stats(self, stats: dict[str, Any]) -> None:
        self.camera_stats.setText(
            "Frames: {frames_read} | H264: {h264_packets} | JPG: {jpeg_frames}".format(
                frames_read=stats.get("frames_read", 0),
                h264_packets=stats.get("h264_packets", 0),
                jpeg_frames=stats.get("jpeg_frames", 0),
            )
        )

    def _update_lidar_cloud(self, points: object, metadata: object) -> None:
        if isinstance(points, list):
            self.lidar_view.set_points(points)

    def _update_lidar_stats(self, stats: dict[str, Any]) -> None:
        self.lidar_stats.setText(
            "Nubes: {clouds} | Puntos: {points} | Guardadas: {saved_clouds}".format(
                clouds=stats.get("clouds", 0),
                points=stats.get("points", 0),
                saved_clouds=stats.get("saved_clouds", 0),
            )
        )

    def _show_status(self, text: str) -> None:
        self.statusBar().showMessage(text)

    def _show_saved(self, path: str) -> None:
        self.statusBar().showMessage(f"Guardado: {path}")

    def closeEvent(self, event: Any) -> None:
        self.stop_capture()
        super().closeEvent(event)

    def sizeHint(self) -> QSize:
        return QSize(1280, 760)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="CapturadorVideoLidar --gui")
    parser.add_argument("--interface", default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--smoke-test", action="store_true", help="Abre la GUI en demo y sale automaticamente.")
    parser.add_argument("--smoke-record", action="store_true", help="Activa grabacion durante la prueba automatica.")
    args = parser.parse_args(argv)

    app = QApplication(sys.argv[:1])
    window = MainWindow(initial_interface=args.interface, output_dir=args.output, demo=args.demo)
    window.show()

    if args.smoke_test:
        QTimer.singleShot(200, window.start_capture)
        if args.smoke_record:
            record_start_ms = 600 if args.demo else 7600
            record_stop_ms = 1400 if args.demo else 12000
            QTimer.singleShot(record_start_ms, lambda: window.video_record_button.setChecked(True))
            QTimer.singleShot(record_start_ms, lambda: window.lidar_record_button.setChecked(True))
            QTimer.singleShot(record_stop_ms, lambda: window.video_record_button.setChecked(False))
            QTimer.singleShot(record_stop_ms, lambda: window.lidar_record_button.setChecked(False))
            QTimer.singleShot(record_stop_ms + 200, window._save_lidar_snapshot)
        close_after_ms = 2200 if args.demo else 15000
        QTimer.singleShot(close_after_ms, window.close)

    return app.exec()
