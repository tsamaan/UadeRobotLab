from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .demo import write_demo_bmp
from .sdk import require_unitree_sdk
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

    require_unitree_sdk(config.sdk_path)

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
