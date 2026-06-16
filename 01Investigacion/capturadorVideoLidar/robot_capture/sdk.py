from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def repo_root_from_project() -> Path:
    return Path(__file__).resolve().parents[3]


def bootstrap_unitree_sdk(explicit_path: str | None = None) -> Path | None:
    """Make the local Unitree SDK importable when it is not installed."""
    if importlib.util.find_spec("unitree_sdk2py") is not None:
        return None

    candidates: list[Path] = []
    if explicit_path:
        candidates.append(Path(explicit_path).expanduser())

    candidates.append(repo_root_from_project() / "00SDK" / "unitree_sdk2_python")

    for candidate in candidates:
        if candidate.exists() and (candidate / "unitree_sdk2py").exists():
            sys.path.insert(0, str(candidate))
            if importlib.util.find_spec("unitree_sdk2py") is not None:
                return candidate

    return None


def require_unitree_sdk(explicit_path: str | None = None) -> None:
    bootstrap_unitree_sdk(explicit_path)
    if importlib.util.find_spec("unitree_sdk2py") is None:
        raise RuntimeError(
            "No se encontro unitree_sdk2py. Instalar el SDK o ejecutar desde el repo "
            "con 00SDK/unitree_sdk2_python disponible."
        )
