from __future__ import annotations

import json
import queue
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .demo import synthetic_room_points
from .pointcloud import (
    parse_xyz_points,
    pointcloud_metadata,
    write_csv_points,
    write_pcd_ascii,
)
from .sdk import require_unitree_sdk
from .utils import ensure_dir, value, write_json


Progress = Callable[[str], None]


@dataclass
class LidarConfig:
    interface: str | None
    duration: float
    output_dir: Path
    sdk_path: str | None = None
    topic: str = "rt/utlidar/cloud"
    state_topic: str = "rt/utlidar/lidar_state"
    export_format: str = "all"
    max_clouds: int = 0
    switch: str = "none"
    demo: bool = False


def capture_lidar(config: LidarConfig, progress: Progress = print) -> dict:
    lidar_dir = ensure_dir(config.output_dir / "lidar")
    if config.demo:
        return _capture_demo_lidar(config, lidar_dir, progress)

    require_unitree_sdk(config.sdk_path)

    from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher, ChannelSubscriber
    from unitree_sdk2py.idl.sensor_msgs.msg.dds_ import PointCloud2_
    from unitree_sdk2py.idl.std_msgs.msg.dds_ import String_
    from unitree_sdk2py.idl.unitree_go.msg.dds_ import LidarState_

    ChannelFactoryInitialize(0, config.interface or None)

    if config.switch.lower() in {"on", "off"}:
        publisher = ChannelPublisher("rt/utlidar/switch", String_)
        publisher.Init()
        publisher.Write(String_(config.switch.upper()))
        progress(f"[lidar] Switch UTLiDAR enviado: {config.switch.upper()}")

    cloud_queue: queue.Queue[tuple[float, object]] = queue.Queue(maxsize=20)
    state_rows: list[dict] = []

    def cloud_handler(msg: object) -> None:
        try:
            cloud_queue.put_nowait((time.time(), msg))
        except queue.Full:
            try:
                cloud_queue.get_nowait()
            except queue.Empty:
                pass
            cloud_queue.put_nowait((time.time(), msg))

    def state_handler(msg: object) -> None:
        state_rows.append(
            {
                "timestamp": time.time(),
                "stamp": value(msg, "stamp"),
                "cloud_frequency": value(msg, "cloud_frequency"),
                "cloud_packet_loss_rate": value(msg, "cloud_packet_loss_rate"),
                "cloud_size": value(msg, "cloud_size"),
                "cloud_scan_num": value(msg, "cloud_scan_num"),
                "imu_rpy": list(value(msg, "imu_rpy", []) or []),
                "error_state": value(msg, "error_state"),
            }
        )

    cloud_sub = ChannelSubscriber(config.topic, PointCloud2_)
    cloud_sub.Init(cloud_handler, 10)

    state_sub = None
    if config.state_topic:
        try:
            state_sub = ChannelSubscriber(config.state_topic, LidarState_)
            state_sub.Init(state_handler, 10)
        except Exception as exc:
            progress(f"[lidar] No pude suscribirme a estado LiDAR ({config.state_topic}): {exc}")

    progress(f"[lidar] Escuchando nube de puntos en {config.topic}...")
    start = time.time()
    cloud_count = 0
    parsed_points_total = 0
    raw_only_count = 0
    errors: list[str] = []

    while time.time() - start < config.duration:
        if config.max_clouds and cloud_count >= config.max_clouds:
            break
        try:
            received_at, msg = cloud_queue.get(timeout=0.25)
        except queue.Empty:
            continue

        cloud_count += 1
        stem = f"cloud_{cloud_count:06d}"
        metadata = pointcloud_metadata(msg)
        metadata["received_at"] = received_at
        metadata["topic"] = config.topic

        raw_data = bytes(value(msg, "data", b"") or b"")
        if config.export_format in {"all", "raw"}:
            (lidar_dir / f"{stem}.bin").write_bytes(raw_data)

        points = parse_xyz_points(msg)
        metadata["parsed_points"] = len(points)
        parsed_points_total += len(points)
        if not points:
            raw_only_count += 1
        else:
            if config.export_format in {"all", "pcd"}:
                write_pcd_ascii(lidar_dir / f"{stem}.pcd", points)
            if config.export_format in {"all", "csv"}:
                write_csv_points(lidar_dir / f"{stem}.csv", points)

        write_json(lidar_dir / f"{stem}.json", metadata)

    try:
        cloud_sub.Close()
    except Exception:
        pass
    if state_sub is not None:
        try:
            state_sub.Close()
        except Exception:
            pass

    if state_rows:
        with (lidar_dir / "lidar_state.jsonl").open("w", encoding="utf-8") as handle:
            for row in state_rows:
                handle.write(json.dumps(row, ensure_ascii=True) + "\n")

    metadata = {
        "source": "unitree_go2_utlidar",
        "duration_requested_s": config.duration,
        "topic": config.topic,
        "state_topic": config.state_topic,
        "clouds_written": cloud_count,
        "parsed_points_total": parsed_points_total,
        "raw_only_clouds": raw_only_count,
        "lidar_dir": str(lidar_dir),
        "errors": errors,
    }
    write_json(config.output_dir / "lidar_metadata.json", metadata)
    progress(f"[lidar] Listo: {cloud_count} nubes en {lidar_dir}")
    return metadata


def _capture_demo_lidar(config: LidarConfig, lidar_dir: Path, progress: Progress) -> dict:
    progress("[lidar-demo] Generando nube PCD/CSV de prueba...")
    points = synthetic_room_points()
    if config.export_format in {"all", "pcd"}:
        write_pcd_ascii(lidar_dir / "cloud_000001.pcd", points)
    if config.export_format in {"all", "csv"}:
        write_csv_points(lidar_dir / "cloud_000001.csv", points)
    metadata = {
        "source": "demo",
        "duration_requested_s": config.duration,
        "topic": "demo",
        "clouds_written": 1,
        "parsed_points_total": len(points),
        "raw_only_clouds": 0,
        "lidar_dir": str(lidar_dir),
        "errors": [],
    }
    write_json(config.output_dir / "lidar_metadata.json", metadata)
    progress(f"[lidar-demo] Listo: {len(points)} puntos en {lidar_dir}")
    return metadata
