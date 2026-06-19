from __future__ import annotations

import importlib.util
import platform
import sys
import tempfile
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


def prepare_unitree_runtime(explicit_path: str | None = None) -> None:
    require_unitree_sdk(explicit_path)
    patch_best_effort_qos()
    if platform.system().lower() == "windows":
        patch_windows_cyclonedds_log_path()


def patch_windows_cyclonedds_log_path() -> None:
    """Avoid the Linux-only /tmp/cdds.LOG path from Unitree's SDK config."""
    try:
        import unitree_sdk2py.core.channel as channel
    except Exception:
        return

    log_path = (Path(tempfile.gettempdir()) / "unitree_cdds.LOG").as_posix()
    for name in ("ChannelConfigHasInterface", "ChannelConfigAutoDetermine"):
        config = getattr(channel, name, None)
        if isinstance(config, str):
            setattr(channel, name, config.replace("/tmp/cdds.LOG", log_path))


def patch_best_effort_qos() -> None:
    """Match Unitree Go2 topics/services that advertise BestEffort QoS."""
    try:
        import unitree_sdk2py.core.channel as channel
        from cyclonedds.qos import Policy, Qos
    except Exception:
        return

    if getattr(channel, "_uade_best_effort_qos_patch", False):
        return

    best_effort = Qos(
        Policy.DataRepresentation(use_cdrv0_representation=True, use_xcdrv2_representation=True),
        Policy.Reliability.BestEffort,
        Policy.TypeConsistency.DisallowTypeCoercion(force_type_validation=False),
    )
    original_reader = channel.DataReader
    original_writer = channel.DataWriter

    def data_reader(participant, topic, qos=None, *args, **kwargs):
        return original_reader(participant, topic, best_effort if qos is None else qos, *args, **kwargs)

    def data_writer(participant, topic, qos=None, *args, **kwargs):
        return original_writer(participant, topic, best_effort if qos is None else qos, *args, **kwargs)

    channel.DataReader = data_reader
    channel.DataWriter = data_writer
    channel._uade_best_effort_qos_patch = True


def cyclonedds_config(interface: str | None = None) -> str:
    log_path = (Path(tempfile.gettempdir()) / "unitree_cdds.LOG").as_posix()
    if interface:
        interface_xml = f"<NetworkInterface name='{interface}' priority='default' multicast='default'/>"
    else:
        interface_xml = "<NetworkInterface autodetermine='true' priority='default' multicast='default'/>"
    return (
        "<CycloneDDS><Domain Id='any'><General><Interfaces>"
        f"{interface_xml}"
        "</Interfaces></General><Tracing><Verbosity>warning</Verbosity>"
        f"<OutputFile>{log_path}</OutputFile>"
        "</Tracing></Domain></CycloneDDS>"
    )
