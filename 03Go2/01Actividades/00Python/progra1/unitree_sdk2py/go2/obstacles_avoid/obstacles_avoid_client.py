from __future__ import annotations

from ...mock_client import MockClient, OK


class ObstaclesAvoidClient(MockClient):
    def __init__(self):
        super().__init__("obstacles_avoid")
        self.enabled = False
        self.uses_remote_commands_from_api = False

    def SwitchSet(self, on: bool):
        self.enabled = bool(on)
        return self._ok("SwitchSet", on)

    def SwitchGet(self):
        self._ok("SwitchGet")
        return OK, self.enabled

    def Move(self, vx: float, vy: float, vyaw: float):
        return self._ok("Move", vx, vy, vyaw)

    def UseRemoteCommandFromApi(self, isRemoteCommandsFromApi: bool):
        self.uses_remote_commands_from_api = bool(isRemoteCommandsFromApi)
        return self._ok("UseRemoteCommandFromApi", isRemoteCommandsFromApi)

    def MoveToAbsolutePosition(self, vx: float, vy: float, vyaw: float):
        return self._ok("MoveToAbsolutePosition", vx, vy, vyaw)

    def MoveToIncrementPosition(self, vx: float, vy: float, vyaw: float):
        return self._ok("MoveToIncrementPosition", vx, vy, vyaw)
