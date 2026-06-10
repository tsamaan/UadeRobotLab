from __future__ import annotations

from dataclasses import dataclass

from ...mock_client import MockClient, OK


SPORT_PATH_POINT_SIZE = 30


@dataclass
class PathPoint:
    timeFromStart: float
    x: float
    y: float
    yaw: float
    vx: float
    vy: float
    vyaw: float


class SportClient(MockClient):
    def __init__(self, enableLease: bool = False):
        super().__init__("sport")
        self.enableLease = enableLease
        self.auto_recovery_enabled = True

    def Damp(self):
        return self._ok("Damp")

    def BalanceStand(self):
        return self._ok("BalanceStand")

    def StopMove(self):
        return self._ok("StopMove")

    def StandUp(self):
        return self._ok("StandUp")

    def StandDown(self):
        return self._ok("StandDown")

    def RecoveryStand(self):
        return self._ok("RecoveryStand")

    def Euler(self, roll: float, pitch: float, yaw: float):
        return self._ok("Euler", roll, pitch, yaw)

    def Move(self, vx: float, vy: float, vyaw: float):
        return self._ok("Move", vx, vy, vyaw)

    def Sit(self):
        return self._ok("Sit")

    def RiseSit(self):
        return self._ok("RiseSit")

    def SpeedLevel(self, level: int):
        return self._ok("SpeedLevel", level)

    def Hello(self):
        return self._ok("Hello")

    def Stretch(self):
        return self._ok("Stretch")

    def Content(self):
        return self._ok("Content")

    def Dance1(self):
        return self._ok("Dance1")

    def Dance2(self):
        return self._ok("Dance2")

    def SwitchJoystick(self, on: bool):
        return self._ok("SwitchJoystick", on)

    def Pose(self, flag: bool):
        return self._ok("Pose", flag)

    def Scrape(self):
        return self._ok("Scrape")

    def FrontFlip(self):
        return self._ok("FrontFlip")

    def FrontJump(self):
        return self._ok("FrontJump")

    def FrontPounce(self):
        return self._ok("FrontPounce")

    def Heart(self):
        return self._ok("Heart")

    def LeftFlip(self):
        return self._ok("LeftFlip")

    def BackFlip(self):
        return self._ok("BackFlip")

    def FreeWalk(self):
        return self._ok("FreeWalk")

    def FreeBound(self, flag: bool):
        return self._ok("FreeBound", flag)

    def FreeJump(self, flag: bool):
        return self._ok("FreeJump", flag)

    def FreeAvoid(self, flag: bool):
        return self._ok("FreeAvoid", flag)

    def WalkUpright(self, flag: bool):
        return self._ok("WalkUpright", flag)

    def CrossStep(self, flag: bool):
        return self._ok("CrossStep", flag)

    def StaticWalk(self):
        return self._ok("StaticWalk")

    def TrotRun(self):
        return self._ok("TrotRun")

    def HandStand(self, flag: bool):
        return self._ok("HandStand", flag)

    def ClassicWalk(self, flag: bool):
        return self._ok("ClassicWalk", flag)

    def AutoRecoverySet(self, enabled: bool):
        self.auto_recovery_enabled = bool(enabled)
        return self._ok("AutoRecoverySet", enabled)

    def AutoRecoveryGet(self):
        self._ok("AutoRecoveryGet")
        return OK, self.auto_recovery_enabled

    def SwitchAvoidMode(self):
        return self._ok("SwitchAvoidMode")
