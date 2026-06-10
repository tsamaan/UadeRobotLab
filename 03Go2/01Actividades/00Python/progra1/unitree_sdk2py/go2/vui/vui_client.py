from __future__ import annotations

from ...mock_client import MockClient, OK


class VuiClient(MockClient):
    def __init__(self):
        super().__init__("vui")
        self.switch_enabled = 1
        self.volume = 5
        self.brightness = 5

    def SetSwitch(self, enable: int):
        self.switch_enabled = int(enable)
        return self._ok("SetSwitch", enable)

    def GetSwitch(self):
        self._ok("GetSwitch")
        return OK, self.switch_enabled

    def SetVolume(self, level: int):
        self.volume = int(level)
        return self._ok("SetVolume", level)

    def GetVolume(self):
        self._ok("GetVolume")
        return OK, self.volume

    def SetBrightness(self, level: int):
        self.brightness = int(level)
        return self._ok("SetBrightness", level)

    def GetBrightness(self):
        self._ok("GetBrightness")
        return OK, self.brightness
