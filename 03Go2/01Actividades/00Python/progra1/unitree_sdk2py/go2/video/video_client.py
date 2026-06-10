from __future__ import annotations

from ...mock_client import MockClient, OK


class VideoClient(MockClient):
    def __init__(self):
        super().__init__("videohub")

    def GetImageSample(self):
        self._ok("GetImageSample")
        return OK, b"SDK_PRUEBA_IMAGEN"
