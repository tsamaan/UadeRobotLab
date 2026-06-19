from __future__ import annotations

import time
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .demo import write_demo_bmp
from .dds_dynamic import make_dynamic_reader
from .sdk import prepare_unitree_runtime
from .utils import ensure_dir, write_json


Progress = Callable[[str], None]


@dataclass
class CameraConfig:
    interface: str | None
    duration: float
    fps: float
    output_dir: Path
    sdk_path: str | None = None
    save_video: bool = True
    demo: bool = False


def capture_camera(config: CameraConfig, progress: Progress = print) -> dict:
    frames_dir = ensure_dir(config.output_dir / "camera_frames")
    if config.demo:
        return _capture_demo_camera(config, frames_dir, progress)

    try:
        return _capture_front_video_stream(config, frames_dir, progress)
    except Exception as exc:
        progress(f"[camara] Stream DDS no disponible, pruebo VideoClient. Detalle: {exc}")

    prepare_unitree_runtime(config.sdk_path)

    from unitree_sdk2py.core.channel import ChannelFactoryInitialize
    from unitree_sdk2py.go2.video.video_client import VideoClient

    ChannelFactoryInitialize(0, config.interface or None)
    client = VideoClient()
    client.SetTimeout(3.0)
    client.Init()

    cv2 = None
    np = None
    writer = None
    video_path = config.output_dir / "front_camera.avi"
    if config.save_video:
        try:
            import cv2 as _cv2
            import numpy as _np

            cv2 = _cv2
            np = _np
        except Exception as exc:
            progress(f"[camara] OpenCV no esta disponible, guardo frames JPG. Detalle: {exc}")

    start = time.time()
    frame_count = 0
    errors: list[str] = []
    target_period = 1.0 / max(config.fps, 0.1)
    next_tick = start

    progress("[camara] Capturando frames desde la camara frontal...")
    while time.time() - start < config.duration:
        loop_start = time.time()
        code, data = client.GetImageSample()
        if code != 0:
            errors.append(f"GetImageSample devolvio codigo {code}")
            time.sleep(min(0.5, target_period))
            continue

        frame_count += 1
        payload = bytes(data)
        frame_path = frames_dir / f"frame_{frame_count:06d}.jpg"
        frame_path.write_bytes(payload)

        if cv2 is not None and np is not None:
            image_data = np.frombuffer(payload, dtype=np.uint8)
            image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
            if image is not None:
                if writer is None:
                    height, width = image.shape[:2]
                    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
                    writer = cv2.VideoWriter(str(video_path), fourcc, max(config.fps, 1.0), (width, height))
                writer.write(image)

        next_tick += target_period
        sleep_for = max(0.0, next_tick - time.time())
        if sleep_for == 0:
            sleep_for = max(0.0, target_period - (time.time() - loop_start))
        time.sleep(sleep_for)

    if writer is not None:
        writer.release()

    metadata = {
        "source": "unitree_go2_front_camera",
        "duration_requested_s": config.duration,
        "fps_requested": config.fps,
        "frames_written": frame_count,
        "frames_dir": str(frames_dir),
        "video_path": str(video_path) if writer is not None else None,
        "errors": errors,
    }
    write_json(config.output_dir / "camera_metadata.json", metadata)
    progress(f"[camara] Listo: {frame_count} frames en {frames_dir}")
    return metadata


def _capture_front_video_stream(config: CameraConfig, frames_dir: Path, progress: Progress) -> dict:
    cv2 = None
    np = None
    writer = None
    video_path = config.output_dir / "front_camera.avi"
    h264_path = config.output_dir / "front_camera.h264"
    mp4_path = config.output_dir / "front_camera.mp4"
    h264_file = None
    if config.save_video:
        try:
            import cv2 as _cv2
            import numpy as _np

            cv2 = _cv2
            np = _np
        except Exception as exc:
            progress(f"[camara] OpenCV no esta disponible, guardo frames JPG. Detalle: {exc}")

    progress("[camara] Descubriendo stream DDS rt/frontvideostream...")
    _participant, reader, _datatype = make_dynamic_reader(config.interface, "rt/frontvideostream", runtime_s=6.0)

    start = time.time()
    frame_count = 0
    read_count = 0
    h264_packet_count = 0
    h264_skipped_packets = 0
    h264_nal_counts: dict[int, int] = {}
    h264_pending: list[tuple[bytes, list[int]]] = []
    h264_ready = False
    h264_seen_sps = False
    h264_seen_pps = False
    errors: list[str] = []
    target_period = 1.0 / max(config.fps, 0.1)
    next_save = start
    last_resolution = None
    stream_kind = "unknown"

    progress("[camara] Capturando stream frontal DDS...")
    while time.time() - start < config.duration:
        try:
            samples = reader.take(N=10)
        except Exception as exc:
            errors.append(str(exc))
            time.sleep(0.05)
            continue

        if not samples:
            time.sleep(0.02)
            continue

        for msg in samples:
            read_count += 1

            payload = bytes(getattr(msg, "data", b"") or b"")
            if not payload:
                continue

            last_resolution = getattr(msg, "resolution", None)

            if _is_jpeg(payload):
                stream_kind = "jpeg"
                now = time.time()
                if now < next_save:
                    continue
                next_save = now + target_period

                frame_count += 1
                frame_path = frames_dir / f"frame_{frame_count:06d}.jpg"
                frame_path.write_bytes(payload)

                if cv2 is not None and np is not None:
                    image_data = np.frombuffer(payload, dtype=np.uint8)
                    image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
                    if image is not None:
                        if writer is None:
                            height, width = image.shape[:2]
                            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
                            writer = cv2.VideoWriter(str(video_path), fourcc, max(config.fps, 1.0), (width, height))
                        writer.write(image)
                continue

            if _looks_like_h264(payload):
                stream_kind = "h264_annex_b"
                nal_types = _h264_nal_types(payload)

                if not h264_ready:
                    has_sps_or_pps = 7 in nal_types or 8 in nal_types
                    if has_sps_or_pps or h264_pending:
                        h264_pending.append((payload, nal_types))
                        h264_seen_sps = h264_seen_sps or 7 in nal_types
                        h264_seen_pps = h264_seen_pps or 8 in nal_types
                    else:
                        h264_skipped_packets += 1
                        continue

                    if not (h264_seen_sps and h264_seen_pps and 5 in nal_types):
                        continue

                    h264_ready = True
                    if h264_file is None:
                        h264_file = h264_path.open("wb")
                    for pending_payload, pending_nal_types in h264_pending:
                        h264_file.write(pending_payload)
                        h264_packet_count += 1
                        _add_h264_nal_counts(h264_nal_counts, pending_nal_types)
                    h264_pending.clear()
                    continue

                if h264_file is None:
                    h264_file = h264_path.open("wb")
                h264_file.write(payload)
                h264_packet_count += 1
                _add_h264_nal_counts(h264_nal_counts, nal_types)
                continue

            stream_kind = "binary"
            now = time.time()
            if now < next_save:
                continue
            next_save = now + target_period
            frame_count += 1
            (frames_dir / f"frame_{frame_count:06d}.bin").write_bytes(payload)

    if writer is not None:
        writer.release()
    if h264_file is not None:
        h264_file.close()

    mp4_written = False
    if config.save_video and h264_path.exists() and h264_path.stat().st_size > 0:
        mp4_written = _convert_h264_to_mp4(h264_path, mp4_path, config.fps, errors)

    metadata = {
        "source": "unitree_go2_frontvideostream",
        "duration_requested_s": config.duration,
        "fps_requested": config.fps,
        "frames_read": read_count,
        "frames_written": frame_count,
        "frames_dir": str(frames_dir),
        "video_path": str(video_path) if writer is not None else None,
        "h264_path": str(h264_path) if h264_path.exists() else None,
        "mp4_path": str(mp4_path) if mp4_written else None,
        "h264_packets_written": h264_packet_count,
        "h264_packets_skipped_before_keyframe": h264_skipped_packets,
        "h264_nal_counts": {str(key): value for key, value in sorted(h264_nal_counts.items())},
        "stream_kind": stream_kind,
        "last_resolution": last_resolution,
        "capture_backend": "cyclonedds_dynamic",
        "errors": errors,
    }
    write_json(config.output_dir / "camera_metadata.json", metadata)
    if h264_packet_count:
        if mp4_written:
            progress(f"[camara] Listo: {h264_packet_count} paquetes H264 y MP4 en {mp4_path}")
        else:
            progress(f"[camara] Listo: {h264_packet_count} paquetes H264 en {h264_path}")
    else:
        progress(f"[camara] Listo: {frame_count} frames en {frames_dir}")
    return metadata


def _is_jpeg(payload: bytes) -> bool:
    return len(payload) >= 2 and payload[0] == 0xFF and payload[1] == 0xD8


def _looks_like_h264(payload: bytes) -> bool:
    return payload.startswith(b"\x00\x00\x00\x01") or payload.startswith(b"\x00\x00\x01")


def _h264_nal_types(payload: bytes) -> list[int]:
    positions: list[int] = []
    index = 0
    while True:
        pos4 = payload.find(b"\x00\x00\x00\x01", index)
        pos3 = payload.find(b"\x00\x00\x01", index)
        candidates = [pos for pos in (pos4, pos3) if pos >= 0]
        if not candidates:
            break
        pos = min(candidates)
        start_len = 4 if payload[pos : pos + 4] == b"\x00\x00\x00\x01" else 3
        nal_pos = pos + start_len
        if nal_pos < len(payload):
            positions.append(payload[nal_pos] & 0x1F)
        index = nal_pos + 1
    return positions


def _add_h264_nal_counts(counts: dict[int, int], nal_types: list[int]) -> None:
    for nal_type in nal_types:
        counts[nal_type] = counts.get(nal_type, 0) + 1


def _convert_h264_to_mp4(h264_path: Path, mp4_path: Path, fps: float, errors: list[str]) -> bool:
    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        errors.append("ffmpeg no disponible; se guardo solo H264 crudo.")
        return False

    command = [
        ffmpeg,
        "-y",
        "-f",
        "h264",
        "-r",
        str(max(fps, 1.0)),
        "-i",
        str(h264_path),
        "-c:v",
        "copy",
        str(mp4_path),
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        errors.append("ffmpeg no pudo convertir H264 a MP4: " + completed.stderr[-800:])
        return False
    return mp4_path.exists() and mp4_path.stat().st_size > 0


def _find_ffmpeg() -> str | None:
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "ffmpeg.exe")
        candidates.append(Path(sys.executable).resolve().parent / "_internal" / "ffmpeg.exe")

    local_exe = Path(__file__).resolve().parent / "ffmpeg.exe"
    candidates.append(local_exe)

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return shutil.which("ffmpeg")


def _capture_demo_camera(config: CameraConfig, frames_dir: Path, progress: Progress) -> dict:
    start = time.time()
    frame_count = 0
    target_period = 1.0 / max(config.fps, 0.1)
    progress("[camara-demo] Generando frames BMP de prueba...")

    while time.time() - start < config.duration:
        frame_count += 1
        write_demo_bmp(frames_dir / f"frame_{frame_count:06d}.bmp", 640, 360, frame_count)
        time.sleep(target_period)

    metadata = {
        "source": "demo",
        "duration_requested_s": config.duration,
        "fps_requested": config.fps,
        "frames_written": frame_count,
        "frames_dir": str(frames_dir),
        "video_path": None,
        "errors": [],
    }
    write_json(config.output_dir / "camera_metadata.json", metadata)
    progress(f"[camara-demo] Listo: {frame_count} frames en {frames_dir}")
    return metadata
