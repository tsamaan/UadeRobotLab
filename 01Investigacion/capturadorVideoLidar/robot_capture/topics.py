from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping


AUTO_TOPIC = "Auto"
TopicKind = Literal["camera", "lidar"]


@dataclass(frozen=True)
class RobotPreset:
    key: str
    label: str
    camera_topics: tuple[str, ...]
    lidar_topics: tuple[str, ...]


ROBOT_PRESETS: dict[str, RobotPreset] = {
    "go2": RobotPreset(
        key="go2",
        label="Go2",
        camera_topics=("rt/frontvideostream",),
        lidar_topics=("rt/utlidar/cloud", "rt/utlidar/cloud_livox_mid360"),
    ),
    "g1": RobotPreset(
        key="g1",
        label="G1 EDU",
        camera_topics=("rt/frontvideostream",),
        lidar_topics=(
            "rt/utlidar/cloud_livox_mid360",
            "rt/utlidar/cloud",
            "rt/ele_clouds",
            "rt/no_warning_clouds",
            "rt/safe_clouds",
            "rt/pre_safe_clouds",
            "rt/grid_clouds",
            "rt/collision_clouds",
        ),
    ),
    "auto": RobotPreset(
        key="auto",
        label="Auto",
        camera_topics=("rt/frontvideostream",),
        lidar_topics=(
            "rt/utlidar/cloud",
            "rt/utlidar/cloud_livox_mid360",
            "rt/ele_clouds",
            "rt/no_warning_clouds",
            "rt/safe_clouds",
            "rt/pre_safe_clouds",
            "rt/grid_clouds",
            "rt/collision_clouds",
        ),
    ),
}


def normalize_robot_key(raw: str | None) -> str:
    text = (raw or "").strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    if text in {"g1", "g1edu", "unitreeg1", "unitreeg1edu"}:
        return "g1"
    if text in {"go2", "unitreego2"}:
        return "go2"
    return "auto"


def is_auto_topic(raw: str | None) -> bool:
    text = (raw or "").strip().lower()
    return text in {"", "auto", "automatico", "autodetectar"}


def suggested_topic_text(robot_key: str, kind: TopicKind) -> str:
    key = normalize_robot_key(robot_key)
    if key == "go2":
        return fallback_topic_for(key, kind) or AUTO_TOPIC
    return AUTO_TOPIC


def fallback_topic_for(robot_key: str, kind: TopicKind) -> str | None:
    preset = ROBOT_PRESETS.get(normalize_robot_key(robot_key), ROBOT_PRESETS["auto"])
    topics = preset.camera_topics if kind == "camera" else preset.lidar_topics
    return topics[0] if topics else None


def choose_topic(
    publications: list[Mapping[str, object]],
    robot_key: str,
    kind: TopicKind,
) -> str | None:
    preset = ROBOT_PRESETS.get(normalize_robot_key(robot_key), ROBOT_PRESETS["auto"])
    candidates = preset.camera_topics if kind == "camera" else preset.lidar_topics
    published_by_name = {_topic_name(item): item for item in publications}

    for candidate in candidates:
        item = published_by_name.get(candidate)
        if item is not None and _score_topic(kind, item) >= 0:
            return candidate

    scored = [
        (_score_topic(kind, item), _topic_name(item))
        for item in publications
        if _topic_name(item)
    ]
    scored = [(score, name) for score, name in scored if score > 0]
    if not scored:
        return None
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[0][1]


def summarize_publications(publications: list[Mapping[str, object]], limit: int = 12) -> str:
    names = [_topic_name(item) for item in publications if _topic_name(item)]
    if not names:
        return "sin topicos"
    visible = names[:limit]
    suffix = "" if len(names) <= limit else f", +{len(names) - limit} mas"
    return ", ".join(visible) + suffix


def _topic_name(item: Mapping[str, object]) -> str:
    return str(item.get("topic_name", "") or "")


def _type_name(item: Mapping[str, object]) -> str:
    return str(item.get("type_name", "") or "")


def _score_topic(kind: TopicKind, item: Mapping[str, object]) -> int:
    name = _topic_name(item).lower()
    type_name = _type_name(item).lower()
    if any(blocked in name for blocked in ("/request", "/response", "reply")):
        return -100
    if kind == "camera":
        return _score_camera(name, type_name)
    return _score_lidar(name, type_name)


def _score_camera(name: str, type_name: str) -> int:
    score = 0
    if "frontvideostream" in name:
        score += 200
    if "videodata" in type_name or "compressedimage" in type_name:
        score += 120
    if "image" in type_name and "pointcloud" not in type_name:
        score += 80
    if "videostream" in name:
        score += 40
    if "camera" in name:
        score += 25
    if "videohub" in name and "string" in type_name:
        score -= 80
    return score


def _score_lidar(name: str, type_name: str) -> int:
    score = 0
    if "pointcloud2" in type_name:
        score += 120
    if "utlidar" in name:
        score += 90
    if "livox" in name:
        score += 80
    if "cloud" in name:
        score += 35
    if "lidar" in name or "pointcloud" in name:
        score += 30
    if "imu" in name or "state" in name:
        score -= 80
    if "gridmap" in name or "planner_map" in name or "global_map" in name:
        score -= 40
    return score
