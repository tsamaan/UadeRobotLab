from __future__ import annotations

import math
import struct
from pathlib import Path


def write_demo_bmp(path: Path, width: int, height: int, frame_index: int) -> None:
    """Write a tiny animated BMP frame using only the standard library."""
    row_stride = (width * 3 + 3) & ~3
    pixel_bytes = bytearray(row_stride * height)

    for y in range(height):
        for x in range(width):
            wave = 0.5 + 0.5 * math.sin((x * 0.05) + (frame_index * 0.35))
            sweep = int((frame_index * 9) % width)
            marker = max(0, 255 - abs(x - sweep) * 12)
            r = int(30 + 180 * wave)
            g = int(50 + 120 * (y / max(1, height - 1)))
            b = marker
            out_y = height - 1 - y
            offset = out_y * row_stride + x * 3
            pixel_bytes[offset : offset + 3] = bytes((b, g, r))

    file_size = 54 + len(pixel_bytes)
    header = bytearray()
    header.extend(b"BM")
    header.extend(struct.pack("<IHHI", file_size, 0, 0, 54))
    header.extend(struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, len(pixel_bytes), 2835, 2835, 0, 0))
    path.write_bytes(bytes(header) + bytes(pixel_bytes))


def synthetic_room_points() -> list[dict[str, float]]:
    points: list[dict[str, float]] = []

    def add(x: float, y: float, z: float, intensity: float = 1.0) -> None:
        points.append({"x": x, "y": y, "z": z, "intensity": intensity})

    for i in range(120):
        t = -3.0 + 6.0 * i / 119.0
        add(t, -2.0, 0.0, 0.7)
        add(t, 2.0, 0.0, 0.7)
        add(-3.0, t * 2.0 / 3.0, 0.0, 0.8)
        add(3.0, t * 2.0 / 3.0, 0.0, 0.8)

    for i in range(72):
        angle = 2.0 * math.pi * i / 72.0
        add(0.9 * math.cos(angle), 0.9 * math.sin(angle), 0.0, 1.0)

    for i in range(40):
        z = 0.02 * i
        add(-1.2, 0.8, z, 0.9)
        add(-1.2, -0.8, z, 0.9)

    return points
