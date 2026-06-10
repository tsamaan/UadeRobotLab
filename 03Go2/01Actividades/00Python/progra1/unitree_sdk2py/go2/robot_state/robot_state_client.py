from __future__ import annotations

from dataclasses import dataclass

from ...mock_client import MockClient, OK


@dataclass
class ServiceState:
    name: str | None = None
    status: int | None = None
    protect: bool | None = None


class RobotStateClient(MockClient):
    def __init__(self):
        super().__init__("robot_state")
        self.services = {
            "sport_mode": ServiceState("sport_mode", 1, False),
            "obstacles_avoid": ServiceState("obstacles_avoid", 0, False),
        }

    def ServiceList(self):
        self._ok("ServiceList")
        return OK, list(self.services.values())

    def ServiceSwitch(self, name: str, switch: bool):
        state = self.services.setdefault(name, ServiceState(name, 0, False))
        state.status = int(bool(switch))
        return self._ok("ServiceSwitch", name, switch)

    def SetReportFreq(self, interval: int, duration: int):
        return self._ok("SetReportFreq", interval, duration)
