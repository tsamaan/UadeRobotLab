from __future__ import annotations

import os
import time
from typing import Any

from .sdk import cyclonedds_config


def discover_topic_publications(interface: str | None, runtime_s: float = 4.0) -> list[dict[str, Any]]:
    from cyclonedds.builtin import BuiltinDataReader, BuiltinTopicDcpsPublication
    from cyclonedds.core import InstanceState, ReadCondition, SampleState, ViewState
    from cyclonedds.domain import DomainParticipant

    os.environ["CYCLONEDDS_URI"] = cyclonedds_config(interface)
    participant = DomainParticipant(0)
    publication_reader = BuiltinDataReader(participant, BuiltinTopicDcpsPublication)
    publication_condition = ReadCondition(
        publication_reader,
        SampleState.NotRead | ViewState.Any | InstanceState.Alive,
    )

    found: dict[str, dict[str, Any]] = {}
    deadline = time.time() + runtime_s
    while time.time() < deadline:
        for publication in publication_reader.take(N=100, condition=publication_condition):
            topic_name = str(getattr(publication, "topic_name", "") or "")
            if not topic_name:
                continue
            found[topic_name] = {
                "topic_name": topic_name,
                "type_name": str(getattr(publication, "type_name", "") or ""),
                "has_type_id": getattr(publication, "type_id", None) is not None,
            }
        time.sleep(0.05)

    return sorted(found.values(), key=lambda item: item["topic_name"])


def make_dynamic_reader(interface: str | None, topic_name: str, runtime_s: float = 6.0):
    from cyclonedds.domain import DomainParticipant
    from cyclonedds.sub import DataReader
    from cyclonedds.topic import Topic

    os.environ["CYCLONEDDS_URI"] = cyclonedds_config(interface)
    participant = DomainParticipant(0)
    discovered = discover_topic_type_and_qos(participant, topic_name, runtime_s=runtime_s)
    if discovered is None:
        raise RuntimeError(f"No se descubrio publicacion DDS para {topic_name}")

    datatype, topic_qos, reader_qos = discovered
    topic = Topic(participant, topic_name, datatype, qos=topic_qos)
    reader = DataReader(participant, topic, qos=reader_qos)
    return participant, reader, datatype


def discover_topic_type_and_qos(participant: Any, topic_name: str, runtime_s: float = 6.0):
    from cyclonedds.builtin import BuiltinDataReader, BuiltinTopicDcpsPublication, BuiltinTopicDcpsTopic
    from cyclonedds.core import InstanceState, Qos, ReadCondition, SampleState, ViewState
    from cyclonedds.dynamic import get_types_for_typeid
    from cyclonedds.util import duration

    try:
        from cyclonedds import internal
    except Exception:
        internal = None

    publication_reader = BuiltinDataReader(participant, BuiltinTopicDcpsPublication)
    publication_condition = ReadCondition(
        publication_reader,
        SampleState.NotRead | ViewState.Any | InstanceState.Alive,
    )

    topic_qos = Qos()
    topic_reader = None
    topic_condition = None
    if internal is not None and getattr(internal, "feature_topic_discovery", False):
        topic_reader = BuiltinDataReader(participant, BuiltinTopicDcpsTopic)
        topic_condition = ReadCondition(
            topic_reader,
            SampleState.NotRead | ViewState.Any | InstanceState.Alive,
        )

    type_id = None
    reader_qos = None
    deadline = time.time() + runtime_s
    while time.time() < deadline:
        if topic_reader is not None and topic_condition is not None:
            for sample in topic_reader.take(N=20, condition=topic_condition):
                if sample.topic_name == topic_name:
                    topic_qos = sample.qos

        for publication in publication_reader.take(N=20, condition=publication_condition):
            if publication.topic_name != topic_name:
                continue
            if publication.type_id is not None:
                type_id = publication.type_id
            reader_qos = publication.qos
            break

        if type_id is not None and reader_qos is not None:
            datatype, _nested = get_types_for_typeid(
                participant,
                type_id,
                duration(seconds=max(1.0, runtime_s)),
            )
            return datatype, topic_qos, reader_qos

        time.sleep(0.02)

    return None
