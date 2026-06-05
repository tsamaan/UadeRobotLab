from __future__ import annotations

import math
import time

import numpy as np

from .go2_low_level import Go2LowLevelClient, JOINT_INDEX, MotorGains, STAND_UP_JOINT_POS, WALK_READY_JOINT_POS
from .go2_trot_controller import TrotParams


class Go2HighLevelClient:
    """API de alto nivel para que los alumnos programen acciones del Go2."""

    def __init__(self, domain: int = 1, interface: str | None = "Ethernet", dt: float = 0.01) -> None:
        self.low = Go2LowLevelClient(domain=domain, interface=interface, dt=dt)
        self.dt = dt
        self.trot_params = TrotParams()
        self.trot_gains = MotorGains(kp=self.trot_params.kp, kd=self.trot_params.kd)

    def StandUp(self, duration: float = 1.2) -> None:
        self.low.stand_up(duration=duration)

    def StandDown(self, duration: float = 1.2) -> None:
        self.low.stand_down(duration=duration)

    def BalanceStand(self, duration: float = 0.5) -> None:
        self.low.hold(STAND_UP_JOINT_POS, duration=duration)

    def StopMove(self, duration: float = 0.4) -> None:
        self.low.interpolate_to(WALK_READY_JOINT_POS, duration=duration, gains=self.trot_gains)
        self.low.hold(duration=0.2)

    def Move(self, x: float = 0.0, y: float = 0.0, yaw: float = 0.0, duration: float = 1.0) -> None:
        x = self._clamp(x, -0.45, 0.45)
        y = self._clamp(y, -0.25, 0.25)
        yaw = self._clamp(yaw, -0.7, 0.7)
        end = time.perf_counter() + max(0.0, duration)

        while time.perf_counter() < end:
            now = time.perf_counter()
            pose = self._trot_pose(now, x=x, y=y, yaw=yaw)
            self.low.send_pose(pose, gains=self.trot_gains)
            time.sleep(self.dt)

        self.StopMove(duration=0.25)

    def Hello(self, duration: float = 2.0) -> None:
        end = time.perf_counter() + max(0.0, duration)
        while time.perf_counter() < end:
            wave = math.sin(time.perf_counter() * 10.0)
            pose = STAND_UP_JOINT_POS.copy()
            pose[JOINT_INDEX["FR_hip"]] = 0.35 + 0.20 * wave
            pose[JOINT_INDEX["FR_thigh"]] = -0.15
            pose[JOINT_INDEX["FR_calf"]] = -0.70
            self.low.send_pose(pose)
            time.sleep(self.dt)
        self.StopMove(duration=0.25)

    def Sit(self, duration: float = 1.0) -> None:
        pose = STAND_UP_JOINT_POS.copy()
        for leg in ("RR", "RL"):
            pose[JOINT_INDEX[f"{leg}_thigh"]] = 1.05
            pose[JOINT_INDEX[f"{leg}_calf"]] = -1.95
        self.low.interpolate_to(pose, duration=duration)

    def RiseSit(self, duration: float = 1.0) -> None:
        self.low.interpolate_to(STAND_UP_JOINT_POS, duration=duration)

    def Damp(self, duration: float = 0.25) -> None:
        self.low.damp(duration=duration)

    def move_for(self, adelante: float = 0.0, costado: float = 0.0, giro: float = 0.0, duracion: float = 1.0) -> None:
        self.Move(x=adelante, y=costado, yaw=giro, duration=duracion)

    def _trot_pose(self, now: float, x: float, y: float, yaw: float) -> np.ndarray:
        pose = WALK_READY_JOINT_POS.copy()
        params = self.trot_params
        leg_phase = {"FR": 0.0, "RL": 0.0, "FL": 0.5, "RR": 0.5}
        side_sign = {"FR": 1.0, "RR": 1.0, "FL": -1.0, "RL": -1.0}
        front_sign = {"FR": 1.0, "FL": 1.0, "RR": -1.0, "RL": -1.0}

        speed_scale = min(1.0, abs(x) / 0.35 + abs(y) / 0.18 + abs(yaw) / 0.45)
        stride = params.max_stride * max(0.35, speed_scale)
        stride *= -1.0 if x >= 0 else 1.0
        lateral = 0.035 * y / 0.18 if y else 0.0
        yaw_stride = 0.045 * yaw / 0.45 if yaw else 0.0

        for leg, offset in leg_phase.items():
            phase = (now * params.frequency + offset) % 1.0
            foot_x, foot_z = self._foot_trajectory(phase, stride)
            foot_x += side_sign[leg] * yaw_stride

            hip_abduction = side_sign[leg] * (0.03 + lateral)
            if yaw:
                hip_abduction += front_sign[leg] * side_sign[leg] * 0.025 * yaw / 0.45

            thigh, calf = self._leg_ik(foot_x, foot_z)
            pose[JOINT_INDEX[f"{leg}_hip"]] = hip_abduction
            pose[JOINT_INDEX[f"{leg}_thigh"]] = thigh
            pose[JOINT_INDEX[f"{leg}_calf"]] = calf
        return pose

    def _foot_trajectory(self, phase: float, stride: float) -> tuple[float, float]:
        params = self.trot_params
        if phase < params.duty_factor:
            s = phase / params.duty_factor
            return 0.5 * stride - stride * s, -params.stance_height

        s = (phase - params.duty_factor) / (1.0 - params.duty_factor)
        foot_x = -0.5 * stride + stride * s
        foot_z = -params.stance_height + params.swing_height * math.sin(math.pi * s)
        return foot_x, foot_z

    def _leg_ik(self, x: float, z: float) -> tuple[float, float]:
        params = self.trot_params
        l1 = params.thigh_length
        l2 = params.calf_length
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
