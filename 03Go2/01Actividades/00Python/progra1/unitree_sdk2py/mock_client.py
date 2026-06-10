from __future__ import annotations

from dataclasses import dataclass, field
from time import strftime
from typing import Any


OK = 0


@dataclass
class CommandRecord:
    service: str
    command: str
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)


class MockClient:
    """Base simple para clientes falsos con la forma del SDK real."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.timeout = 1.0
        self.initialized = False
        self.history: list[CommandRecord] = []

    def SetTimeout(self, timeout: float):
        self.timeout = float(timeout)
        self._print("SetTimeout", timeout=self.timeout, result=None)
        return None

    def Init(self):
        self.initialized = True
        self._print("Init", result=None)
        return None

    def WaitLeaseApplied(self):
        self._print("WaitLeaseApplied")
        return None

    def GetLeaseId(self):
        self._print("GetLeaseId")
        return None

    def GetApiVersion(self):
        return "mock"

    def GetServerApiVersion(self):
        self._print("GetServerApiVersion", result=(OK, "mock"))
        return OK, "mock"

    def _ok(self, command: str, *args: Any, **kwargs: Any) -> int:
        self.history.append(CommandRecord(self.service_name, command, args, kwargs))
        self._print(command, *args, **kwargs, result=OK)
        return OK

    def _print(self, command: str, *args: Any, result: Any = OK, **kwargs: Any):
        parts = [repr(arg) for arg in args]
        parts.extend(f"{key}={value!r}" for key, value in kwargs.items())
        params = ", ".join(parts)
        print(f"[SDK PRUEBA {strftime('%H:%M:%S')}] {self.service_name}.{command}({params}) -> {result!r}")
