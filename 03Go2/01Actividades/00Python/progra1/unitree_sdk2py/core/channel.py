from __future__ import annotations

from typing import Any, Callable


_initialized = False
_domain_id = 0
_network_interface = None


def ChannelFactoryInitialize(id: int = 0, networkInterface: str | None = None):
    global _initialized, _domain_id, _network_interface
    _initialized = True
    _domain_id = id
    _network_interface = networkInterface
    print(
        "[SDK PRUEBA] ChannelFactoryInitialize("
        f"id={id!r}, networkInterface={networkInterface!r}) -> OK"
    )
    return None


class ChannelPublisher:
    def __init__(self, name: str, type: Any):
        self.name = name
        self.type = type
        self.initialized = False

    def Init(self):
        self.initialized = True
        print(f"[SDK PRUEBA] ChannelPublisher({self.name!r}).Init() -> OK")

    def Close(self):
        self.initialized = False
        print(f"[SDK PRUEBA] ChannelPublisher({self.name!r}).Close() -> OK")

    def Write(self, sample: Any, timeout: float | None = None):
        print(
            f"[SDK PRUEBA] ChannelPublisher({self.name!r}).Write("
            f"sample={sample!r}, timeout={timeout!r}) -> True"
        )
        return True


class ChannelSubscriber:
    def __init__(self, name: str, type: Any):
        self.name = name
        self.type = type
        self.initialized = False
        self.handler: Callable | None = None

    def Init(self, handler: Callable | None = None, queueLen: int = 0):
        self.initialized = True
        self.handler = handler
        print(
            f"[SDK PRUEBA] ChannelSubscriber({self.name!r}).Init("
            f"handler={handler!r}, queueLen={queueLen!r}) -> OK"
        )

    def Close(self):
        self.initialized = False
        print(f"[SDK PRUEBA] ChannelSubscriber({self.name!r}).Close() -> OK")

    def Read(self, timeout: int | None = None):
        print(
            f"[SDK PRUEBA] ChannelSubscriber({self.name!r}).Read("
            f"timeout={timeout!r}) -> None"
        )
        return None

