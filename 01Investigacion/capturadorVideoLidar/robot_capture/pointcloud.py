from __future__ import annotations

import csv
import math
import struct
from pathlib import Path
from typing import Any

from .utils import value


ROS_DATATYPES: dict[int, tuple[str, int]] = {
    1: ("b", 1),
    2: ("B", 1),
    3: ("h", 2),
    4: ("H", 2),
    5: ("i", 4),
    6: ("I", 4),
    7: ("f", 4),
    8: ("d", 8),
}


def field_summary(msg: Any) -> list[dict[str, Any]]:
    fields = value(msg, "fields", []) or []
    summary: list[dict[str, Any]] = []
    for field in fields:
        summary.append(
            {
                "name": str(value(field, "name", "")),
                "offset": int(value(field, "offset", 0) or 0),
                "datatype": int(value(field, "datatype", 0) or 0),
                "count": int(value(field, "count", 1) or 1),
            }
        )
    return summary


def pointcloud_metadata(msg: Any) -> dict[str, Any]:
    data = bytes(value(msg, "data", b"") or b"")
    return {
        "height": int(value(msg, "height", 0) or 0),
        "width": int(value(msg, "width", 0) or 0),
        "fields": field_summary(msg),
        "is_bigendian": bool(value(msg, "is_bigendian", False)),
        "point_step": int(value(msg, "point_step", 0) or 0),
        "row_step": int(value(msg, "row_step", 0) or 0),
        "is_dense": bool(value(msg, "is_dense", False)),
        "byte_count": len(data),
    }


def parse_xyz_points(msg: Any) -> list[dict[str, float]]:
    metadata = pointcloud_metadata(msg)
    fields = {field["name"].lower(): field for field in metadata["fields"]}
    required = ("x", "y", "z")
    if any(name not in fields for name in required):
        return []

    intensity_name = next(
        (name for name in ("intensity", "reflectivity", "rgb") if name in fields),
        None,
    )
    selected = [fields[name] for name in required]
    if intensity_name:
        selected.append(fields[intensity_name])

    point_step = metadata["point_step"]
    row_step = metadata["row_step"] or point_step * metadata["width"]
    width = metadata["width"]
    height = metadata["height"] or 1
    data = bytes(value(msg, "data", b"") or b"")
    endian = ">" if metadata["is_bigendian"] else "<"

    if point_step <= 0 or width <= 0:
        return []

    points: list[dict[str, float]] = []
    for row in range(height):
        for col in range(width):
            base = row * row_step + col * point_step
            if base + point_step > len(data):
                continue
            point: dict[str, float] = {}
            for field in selected:
                parsed = _read_field(data, base, field, endian)
                if parsed is None:
                    continue
                point[field["name"].lower()] = float(parsed)
            if all(name in point for name in required):
                if all(math.isfinite(point[name]) for name in required):
                    points.append(point)
    return points


def _read_field(data: bytes, base: int, field: dict[str, Any], endian: str) -> float | int | None:
    datatype = int(field["datatype"])
    if datatype not in ROS_DATATYPES:
        return None
    fmt, size = ROS_DATATYPES[datatype]
    offset = base + int(field["offset"])
    if offset + size > len(data):
        return None
    try:
        return struct.unpack_from(endian + fmt, data, offset)[0]
    except struct.error:
        return None


def write_pcd_ascii(path: Path, points: list[dict[str, float]]) -> None:
    has_intensity = any("intensity" in point or "reflectivity" in point for point in points)
    fields = ["x", "y", "z"] + (["intensity"] if has_intensity else [])
    lines = [
        "# .PCD v0.7 - Point Cloud Data file",
        "VERSION 0.7",
        f"FIELDS {' '.join(fields)}",
        f"SIZE {' '.join(['4'] * len(fields))}",
        f"TYPE {' '.join(['F'] * len(fields))}",
        f"COUNT {' '.join(['1'] * len(fields))}",
        f"WIDTH {len(points)}",
        "HEIGHT 1",
        "VIEWPOINT 0 0 0 1 0 0 0",
        f"POINTS {len(points)}",
        "DATA ascii",
    ]
    for point in points:
        values = [point.get("x", 0.0), point.get("y", 0.0), point.get("z", 0.0)]
        if has_intensity:
            values.append(point.get("intensity", point.get("reflectivity", 0.0)))
        lines.append(" ".join(f"{float(item):.6f}" for item in values))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv_points(path: Path, points: list[dict[str, float]]) -> None:
    has_intensity = any("intensity" in point or "reflectivity" in point for point in points)
    fields = ["x", "y", "z"] + (["intensity"] if has_intensity else [])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for point in points:
            row = {name: point.get(name, "") for name in fields}
            if has_intensity:
                row["intensity"] = point.get("intensity", point.get("reflectivity", ""))
            writer.writerow(row)
