from __future__ import annotations

import math
import time
from dataclasses import dataclass

import numpy as np

from .go2_low_level import Go2LowLevelClient, JOINT_INDEX, MotorGains, WALK_READY_JOINT_POS


@dataclass
class TrotParams:
    thigh_length: float = 0.213
    calf_length: float = 0.213
    stance_height: float = 0.36
    swing_height: float = 0.095
    max_stride: float = 0.24
    duty_factor: float = 0.58
    frequency: float = 1.25
    kp: float = 70.0
    kd: float = 5.0


class Go2TrotController:
    """Controlador educativo de marcha trot sobre LowCmd."""

    LEG_PHASE = {"FR": 0.0, "RL": 0.0, "FL": 0.5, "RR": 0.5}
    SIDE_SIGN = {"FR": 1.0, "RR": 1.0, "FL": -1.0, "RL": -1.0}
    FRONT_SIGN = {"FR": 1.0, "FL": 1.0, "RR": -1.0, "RL": -1.0}

    def __init__(
        self,
        domain: int = 1,
        interface: str | None = "Ethernet",
        dt: float = 0.006,
        params: TrotParams | None = None,
    ) -> None:
        self.low = Go2LowLevelClient(domain=domain, interface=interface, dt=dt)
        self.dt = dt
        self.params = params or TrotParams()
        self.gains = MotorGains(kp=self.params.kp, kd=self.params.kd)

    def ready(self, duration: float = 3.0) -> None:
        self.low.walk_ready(duration=duration)
        self.low.hold(duration=1.0)

    def stop(self, duration: float = 0.5) -> None:
        self.low.interpolate_to(WALK_READY_JOINT_POS, duration=duration, gains=self.gains)
        self.low.hold(duration=0.2)

    def stand_down(self, duration: float = 1.0) -> None:
        self.low.stand_down(duration=duration)
        self.low.damp(duration=0.2)

    def Move(self, x: float = 0.0, y: float = 0.0, yaw: float = 0.0, duration: float = 2.0) -> None:
        x = self._clamp(x, -0.35, 0.35)
        y = self._clamp(y, -0.18, 0.18)
        yaw = self._clamp(yaw, -0.45, 0.45)

        start = time.perf_counter()
        while time.perf_counter() - start < max(0.0, duration):
            t = time.perf_counter() - start
            pose = self._pose_at(t, x=x, y=y, yaw=yaw)
            self.low.send_pose(pose, gains=self.gains)
            time.sleep(self.dt)

        self.stop(duration=0.35)

    def walk_forward(self, speed: float = 0.22, duration: float = 3.0) -> None:
        self.Move(x=speed, duration=duration)

    def turn_left(self, yaw: float = 0.35, duration: float = 2.0) -> None:
        self.Move(yaw=yaw, duration=duration)

    def _pose_at(self, t: float, x: float, y: float, yaw: float) -> np.ndarray:
        pose = WALK_READY_JOINT_POS.copy()
        speed_scale = min(1.0, abs(x) / 0.35 + abs(y) / 0.18 + abs(yaw) / 0.45)
        stride = self.params.max_stride * max(0.35, speed_scale)
        # En el MJCF oficial, este signo hace que x positivo avance en la vista.
        stride *= -1.0 if x >= 0 else 1.0
        lateral = 0.035 * y / 0.18 if y else 0.0
        yaw_stride = 0.045 * yaw / 0.45 if yaw else 0.0

        for leg, offset in self.LEG_PHASE.items():
            phase = (t * self.params.frequency + offset) % 1.0
            foot_x, foot_z = self._foot_trajectory(phase, stride)
            foot_x += self.SIDE_SIGN[leg] * yaw_stride

            hip_abduction = self.SIDE_SIGN[leg] * (0.03 + lateral)
            if yaw:
                hip_abduction += self.FRONT_SIGN[leg] * self.SIDE_SIGN[leg] * 0.025 * yaw / 0.45

            thigh, calf = self._leg_ik(foot_x, foot_z)
            pose[JOINT_INDEX[f"{leg}_hip"]] = hip_abduction
            pose[JOINT_INDEX[f"{leg}_thigh"]] = thigh
            pose[JOINT_INDEX[f"{leg}_calf"]] = calf

        return pose

    def _foot_trajectory(self, phase: float, stride: float) -> tuple[float, float]:
        duty = self.params.duty_factor
        if phase < duty:
            s = phase / duty
            foot_x = 0.5 * stride - stride * s
            foot_z = -self.params.stance_height
        else:
            s = (phase - duty) / (1.0 - duty)
            foot_x = -0.5 * stride + stride * s
            foot_z = -self.params.stance_height + self.params.swing_height * math.sin(math.pi * s)
        return foot_x, foot_z

    def _leg_ik(self, x: float, z: float) -> tuple[float, float]:
        l1 = self.params.thigh_length
        l2 = self.params.calf_length
        distance = math.sqrt(x * x + z * z)
        distance = self._clamp(distance, 0.12, l1 + l2 - 0.02)

        cos_knee = self._clamp((distance * distance - l1 * l1 - l2 * l2) / (2.0 * l1 * l2), -0.99, 0.99)
        knee = -math.acos(cos_knee)

        foot_angle = math.atan2(x, -z)
        hip_offset = math.acos(self._clamp((l1 * l1 + distance * distance - l2 * l2) / (2.0 * l1 * distance), -0.99, 0.99))
        thigh = foot_angle + hip_offset
        return thigh, knee

    @staticmethod
    def _clamp(value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, float(value)))
