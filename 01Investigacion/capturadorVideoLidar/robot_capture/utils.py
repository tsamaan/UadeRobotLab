from __future__ import annotations

import json
import platform
import subprocess
import time
from pathlib import Path
from typing import Any


def timestamp_slug() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")


def value(obj: Any, name: str, default: Any = None) -> Any:
    try:
        attr = getattr(obj, name)
    except Exception:
        return default
    try:
        return attr() if callable(attr) else attr
    except Exception:
        return default


def list_network_interfaces() -> list[str]:
    system = platform.system().lower()
    if system == "windows":
        return _list_windows_interfaces()
    return _list_posix_interfaces()


def _list_windows_interfaces() -> list[str]:
    try:
        raw = subprocess.check_output(
            ["netsh", "interface", "show", "interface"],
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except Exception:
        return []

    names: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        lowered = stripped.lower()
        if (
            not stripped
            or stripped.startswith("-")
            or lowered.startswith("admin")
            or "nombre interfaz" in lowered
            or "interface name" in lowered
        ):
            continue
        # netsh uses aligned columns; the interface name is the last column.
        parts = [part for part in stripped.split("  ") if part.strip()]
        if len(parts) >= 4:
            names.append(parts[-1].strip())
    return names


def _list_posix_interfaces() -> list[str]:
    for command in (["ip", "-o", "link", "show"], ["ifconfig", "-a"]):
        try:
            raw = subprocess.check_output(command, text=True, errors="replace")
            break
        except Exception:
            raw = ""
    else:
        return []

    names: list[str] = []
    if raw and raw.lstrip().startswith("1:"):
        for line in raw.splitlines():
            parts = line.split(":", 2)
            if len(parts) >= 2:
                name = parts[1].strip().split("@", 1)[0]
                if name:
                    names.append(name)
        return names

    for line in raw.splitlines():
        if line and not line.startswith((" ", "\t")) and ":" in line:
            names.append(line.split(":", 1)[0])
    return names
