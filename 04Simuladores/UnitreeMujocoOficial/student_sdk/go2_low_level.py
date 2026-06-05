from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher
from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowCmd_
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowCmd_
from unitree_sdk2py.utils.crc import CRC


JOINT_NAMES = (
    "FR_hip",
    "FR_thigh",
    "FR_calf",
    "FL_hip",
    "FL_thigh",
    "FL_calf",
    "RR_hip",
    "RR_thigh",
    "RR_calf",
    "RL_hip",
    "RL_thigh",
    "RL_calf",
)
JOINT_INDEX = {name: index for index, name in enumerate(JOINT_NAMES)}

STAND_UP_JOINT_POS = np.array(
    [
        0.00571868,
        0.608813,
        -1.21763,
        -0.00571868,
        0.608813,
        -1.21763,
        0.00571868,
        0.608813,
        -1.21763,
        -0.00571868,
        0.608813,
        -1.21763,
    ],
    dtype=float,
)

STAND_DOWN_JOINT_POS = np.array(
    [
        0.0473455,
        1.22187,
        -2.44375,
        -0.0473455,
        1.22187,
        -2.44375,
        0.0473455,
        1.22187,
        -2.44375,
        -0.0473455,
        1.22187,
        -2.44375,
    ],
    dtype=float,
)

WALK_READY_JOINT_POS = np.array(
    [
        0.0,
        0.62,
        -1.24,
        0.0,
        0.62,
        -1.24,
        0.0,
        0.62,
        -1.24,
        0.0,
        0.62,
        -1.24,
    ],
    dtype=float,
)


@dataclass
class MotorGains:
    kp: float = 50.0
    kd: float = 3.5


class Go2LowLevelClient:
    """Cliente didactico para publicar LowCmd al simulador oficial de Unitree."""

    def __init__(self, domain: int = 1, interface: str | None = "Ethernet", dt: float = 0.002) -> None:
        self.domain = domain
        self.interface = interface
        self.dt = dt
        self.crc = CRC()
        self.current_pose = STAND_DOWN_JOINT_POS.copy()

        if interface and interface.lower() not in {"auto", "default"}:
            ChannelFactoryInitialize(domain, interface)
        else:
            ChannelFactoryInitialize(domain)

        self.publisher = ChannelPublisher("rt/lowcmd", LowCmd_)
        self.publisher.Init()
        self.cmd = self._create_low_cmd()

    def stand_up(self, duration: float = 1.2) -> None:
        self.interpolate_to(STAND_UP_JOINT_POS, duration=duration)

    def stand_down(self, duration: float = 1.2) -> None:
        self.interpolate_to(STAND_DOWN_JOINT_POS, duration=duration)

    def walk_ready(self, duration: float = 1.0) -> None:
        self.interpolate_to(WALK_READY_JOINT_POS, duration=duration, gains=MotorGains(kp=45.0, kd=3.0))

    def pose(self) -> np.ndarray:
        return self.current_pose.copy()

    def set_joint(self, pose: np.ndarray, joint_name: str, q: float) -> np.ndarray:
        updated = pose.copy()
        updated[JOINT_INDEX[joint_name]] = float(q)
        return updated

    def send_pose(self, joint_pos: np.ndarray, gains: MotorGains | None = None) -> None:
        gains = gains or MotorGains()
        for index in range(12):
            self.cmd.motor_cmd[index].q = float(joint_pos[index])
            self.cmd.motor_cmd[index].kp = float(gains.kp)
            self.cmd.motor_cmd[index].dq = 0.0
            self.cmd.motor_cmd[index].kd = float(gains.kd)
            self.cmd.motor_cmd[index].tau = 0.0
        self.cmd.crc = self.crc.Crc(self.cmd)
        self.publisher.Write(self.cmd)
        self.current_pose = joint_pos.copy()

    def hold(self, joint_pos: np.ndarray | None = None, duration: float = 1.0) -> None:
        pose = self.current_pose if joint_pos is None else joint_pos
        end = time.perf_counter() + max(0.0, duration)
        while time.perf_counter() < end:
            self.send_pose(pose)
            time.sleep(self.dt)

    def interpolate_to(
        self,
        target_pose: np.ndarray,
        duration: float = 1.0,
        gains: MotorGains | None = None,
    ) -> None:
        start_pose = self.current_pose.copy()
        start_time = time.perf_counter()
        duration = max(duration, self.dt)
        while True:
            elapsed = time.perf_counter() - start_time
            phase = min(1.0, elapsed / duration)
            smooth = 0.5 - 0.5 * np.cos(np.pi * phase)
            pose = start_pose * (1.0 - smooth) + target_pose * smooth
            self.send_pose(pose, gains=gains)
            if phase >= 1.0:
                break
            time.sleep(self.dt)

    def damp(self, duration: float = 0.25) -> None:
        end = time.perf_counter() + max(0.0, duration)
        while time.perf_counter() < end:
            for motor in self.cmd.motor_cmd:
                motor.mode = 0x01
                motor.q = 0.0
                motor.kp = 0.0
                motor.dq = 0.0
                motor.kd = 0.0
                motor.tau = 0.0
            self.cmd.crc = self.crc.Crc(self.cmd)
            self.publisher.Write(self.cmd)
            time.sleep(self.dt)

    @staticmethod
    def _create_low_cmd() -> LowCmd_:
        cmd = unitree_go_msg_dds__LowCmd_()
        cmd.head[0] = 0xFE
        cmd.head[1] = 0xEF
        cmd.level_flag = 0xFF
        cmd.gpio = 0
        for motor in cmd.motor_cmd:
            motor.mode = 0x01
            motor.q = 0.0
            motor.kp = 0.0
            motor.dq = 0.0
            motor.kd = 0.0
            motor.tau = 0.0
        return cmd
