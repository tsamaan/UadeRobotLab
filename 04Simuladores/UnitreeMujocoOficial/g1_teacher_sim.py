from __future__ import annotations

import argparse
import json
import math
import os
import socketserver
import sys
import threading
import time
from pathlib import Path
from typing import Any

import mujoco
import mujoco.viewer
import numpy as np


os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

SCRIPT_DIR = Path(__file__).resolve().parent
SIMULATE_PYTHON_DIR = SCRIPT_DIR / "unitree_mujoco" / "simulate_python"

if not SIMULATE_PYTHON_DIR.exists():
    raise SystemExit(
        "No se encontro unitree_mujoco/simulate_python. "
        "Ejecuta primero run_g1_sim.ps1."
    )

sys.path.insert(0, str(SIMULATE_PYTHON_DIR))
os.chdir(SIMULATE_PYTHON_DIR)

from unitree_sdk2py.core.channel import ChannelFactoryInitialize  # noqa: E402
from unitree_sdk2py_bridge import UnitreeSdk2Bridge  # noqa: E402

import config  # noqa: E402


JOINT_INDEX = {
    "left_hip_pitch": 0,
    "left_hip_roll": 1,
    "left_hip_yaw": 2,
    "left_knee": 3,
    "left_ankle_pitch": 4,
    "left_ankle_roll": 5,
    "right_hip_pitch": 6,
    "right_hip_roll": 7,
    "right_hip_yaw": 8,
    "right_knee": 9,
    "right_ankle_pitch": 10,
    "right_ankle_roll": 11,
    "waist_yaw": 12,
    "waist_roll": 13,
    "waist_pitch": 14,
    "left_shoulder_pitch": 15,
    "left_shoulder_roll": 16,
    "left_shoulder_yaw": 17,
    "left_elbow": 18,
    "left_wrist_roll": 19,
    "left_wrist_pitch": 20,
    "left_wrist_yaw": 21,
    "right_shoulder_pitch": 22,
    "right_shoulder_roll": 23,
    "right_shoulder_yaw": 24,
    "right_elbow": 25,
    "right_wrist_roll": 26,
    "right_wrist_pitch": 27,
    "right_wrist_yaw": 28,
}


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def yaw_to_quat(yaw: float) -> np.ndarray:
    half = yaw * 0.5
    return np.array([math.cos(half), 0.0, 0.0, math.sin(half)])


def pose_with(base_pose: np.ndarray, overrides: dict[str, float]) -> np.ndarray:
    pose = base_pose.copy()
    for joint_name, value in overrides.items():
        pose[JOINT_INDEX[joint_name]] = value
    return pose


class G1TeacherState:
    def __init__(self, base_z: float, neutral_pose: np.ndarray) -> None:
        self.lock = threading.Lock()
        self.command_lock = threading.Lock()
        self.base_x = 0.0
        self.base_y = 0.0
        self.base_z = float(base_z) - 0.035
        self.yaw = 0.0
        self.forward = 0.0
        self.side = 0.0
        self.turn = 0.0
        self.motion_until = 0.0
        self.neutral_pose = neutral_pose.copy()
        self.target_pose = neutral_pose.copy()
        self.display_pose = neutral_pose.copy()
        self.gait_phase = 0.0
        self.last_action = "quieto"

    def start_motion(self, adelante: float, costado: float, giro: float, tiempo: float) -> None:
        adelante = clamp(float(adelante), -0.45, 0.45)
        costado = clamp(float(costado), -0.30, 0.30)
        giro = clamp(float(giro), -1.0, 1.0)
        tiempo = clamp(float(tiempo), 0.0, 10.0)

        with self.lock:
            self.forward = adelante
            self.side = costado
            self.turn = giro
            self.motion_until = time.perf_counter() + tiempo
            self.last_action = "movimiento"

    def run_motion(self, adelante: float, costado: float, giro: float, tiempo: float) -> None:
        with self.command_lock:
            self.start_motion(adelante, costado, giro, tiempo)
            time.sleep(clamp(float(tiempo), 0.0, 10.0))
            self.stop_motion()

    def stop_motion(self) -> None:
        with self.lock:
            self.forward = 0.0
            self.side = 0.0
            self.turn = 0.0
            self.motion_until = 0.0
            self.last_action = "quieto"

    def set_pose(self, overrides: dict[str, float]) -> None:
        with self.lock:
            self.target_pose = pose_with(self.neutral_pose, overrides)

    def reset_pose(self) -> None:
        with self.lock:
            self.target_pose = self.neutral_pose.copy()

    def run_pose_sequence(self, name: str, sequence: list[tuple[dict[str, float], float]]) -> None:
        with self.command_lock:
            with self.lock:
                self.last_action = name
            for overrides, duration in sequence:
                self.set_pose(overrides)
                time.sleep(duration)
            self.reset_pose()
            with self.lock:
                self.last_action = "quieto"

    def saludar(self) -> None:
        arm_up = {
            "right_shoulder_pitch": -0.20,
            "right_shoulder_roll": -1.80,
            "right_shoulder_yaw": 0.00,
            "right_elbow": 0.80,
            "right_wrist_pitch": 0.15,
            "right_wrist_yaw": 0.45,
        }
        wave_left = arm_up | {"right_wrist_yaw": -0.65, "right_shoulder_yaw": -0.20}
        wave_right = arm_up | {"right_wrist_yaw": 0.65, "right_shoulder_yaw": 0.20}
        self.run_pose_sequence(
            "saludar",
            [
                (arm_up, 0.45),
                (wave_left, 0.28),
                (wave_right, 0.28),
                (wave_left, 0.28),
                (wave_right, 0.28),
                (arm_up, 0.35),
            ],
        )

    def dar_beso(self) -> None:
        hand_to_mouth = {
            "right_shoulder_pitch": -1.00,
            "right_shoulder_roll": -0.50,
            "right_shoulder_yaw": 0.00,
            "right_elbow": 0.80,
            "right_wrist_pitch": 0.40,
            "right_wrist_yaw": -0.20,
        }
        throw_kiss = {
            "right_shoulder_pitch": -0.70,
            "right_shoulder_roll": -0.65,
            "right_shoulder_yaw": 0.25,
            "right_elbow": 0.35,
            "right_wrist_pitch": -0.20,
            "right_wrist_yaw": 0.50,
        }
        self.run_pose_sequence(
            "dar_beso",
            [
                (hand_to_mouth, 0.70),
                (hand_to_mouth, 0.35),
                (throw_kiss, 0.65),
                (throw_kiss, 0.25),
            ],
        )

    def step(
        self,
        dt: float,
    ) -> tuple[float, float, float, float, float, float, float, np.ndarray, str]:
        now = time.perf_counter()
        with self.lock:
            if self.motion_until and now >= self.motion_until:
                self.forward = 0.0
                self.side = 0.0
                self.turn = 0.0
                self.motion_until = 0.0

            cos_yaw = math.cos(self.yaw)
            sin_yaw = math.sin(self.yaw)
            world_vx = self.forward * cos_yaw - self.side * sin_yaw
            world_vy = self.forward * sin_yaw + self.side * cos_yaw

            self.base_x += world_vx * dt
            self.base_y += world_vy * dt
            self.yaw += self.turn * dt
            pose = self._pose_with_gait(dt)
            blend = min(1.0, dt * 8.0)
            self.display_pose += (pose - self.display_pose) * blend

            return (
                self.base_x,
                self.base_y,
                self.base_z,
                self.yaw,
                world_vx,
                world_vy,
                self.turn,
                self.display_pose.copy(),
                self.last_action,
            )

    def status(self) -> dict[str, Any]:
        with self.lock:
            return {
                "x": round(self.base_x, 3),
                "y": round(self.base_y, 3),
                "z": round(self.base_z, 3),
                "yaw": round(self.yaw, 3),
                "accion": self.last_action,
            }

    def _pose_with_gait(self, dt: float) -> np.ndarray:
        pose = self.target_pose.copy()
        speed = abs(self.forward) + abs(self.side) + 0.35 * abs(self.turn)
        if speed < 0.01:
            self.gait_phase = 0.0
            return pose

        self.gait_phase += dt * (4.0 + 2.0 * clamp(speed, 0.0, 0.6))
        swing = math.sin(self.gait_phase)
        opposite = -swing
        left_lift = max(0.0, swing)
        right_lift = max(0.0, opposite)

        pose[JOINT_INDEX["left_hip_pitch"]] = 0.10 * swing
        pose[JOINT_INDEX["right_hip_pitch"]] = 0.10 * opposite
        pose[JOINT_INDEX["left_knee"]] = 0.18 * left_lift
        pose[JOINT_INDEX["right_knee"]] = 0.18 * right_lift
        pose[JOINT_INDEX["left_ankle_pitch"]] = -0.06 * swing
        pose[JOINT_INDEX["right_ankle_pitch"]] = -0.06 * opposite
        pose[JOINT_INDEX["left_shoulder_pitch"]] = -0.08 * opposite
        pose[JOINT_INDEX["right_shoulder_pitch"]] = -0.08 * swing
        pose[JOINT_INDEX["waist_yaw"]] = 0.04 * swing
        return pose


def apply_direct_pose(model: mujoco.MjModel, data: mujoco.MjData, target: np.ndarray) -> None:
    data.qpos[7 : 7 + model.nu] = target
    data.qvel[6 : 6 + model.nu] = 0.0


def apply_kinematic_base(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    base_x: float,
    base_y: float,
    base_z: float,
    yaw: float,
    world_vx: float,
    world_vy: float,
    turn: float,
) -> None:
    data.qpos[0] = base_x
    data.qpos[1] = base_y
    data.qpos[2] = base_z
    data.qpos[3:7] = yaw_to_quat(yaw)
    data.qvel[0] = world_vx
    data.qvel[1] = world_vy
    data.qvel[2] = 0.0
    data.qvel[3] = 0.0
    data.qvel[4] = 0.0
    data.qvel[5] = turn


def create_api_server(state: G1TeacherState) -> socketserver.ThreadingTCPServer:
    class ApiHandler(socketserver.StreamRequestHandler):
        def handle(self) -> None:
            raw = self.rfile.readline().decode("utf-8").strip()
            try:
                payload = json.loads(raw)
                response = handle_api_command(state, payload)
            except Exception as exc:
                response = {"ok": False, "error": str(exc)}
            self.wfile.write((json.dumps(response) + "\n").encode("utf-8"))

    host = str(getattr(config, "STUDENT_API_HOST", "127.0.0.1"))
    port = int(getattr(config, "STUDENT_API_PORT", 8765))
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    return socketserver.ThreadingTCPServer((host, port), ApiHandler)


def handle_api_command(state: G1TeacherState, payload: dict[str, Any]) -> dict[str, Any]:
    command = payload.get("command")
    if command == "estado":
        return {"ok": True, "estado": state.status()}
    if command == "movimiento":
        state.run_motion(
            payload.get("adelante", 0.0),
            payload.get("costado", 0.0),
            payload.get("giro", 0.0),
            payload.get("tiempo", 1.0),
        )
        return {"ok": True, "estado": state.status()}
    if command == "saludar":
        state.saludar()
        return {"ok": True, "estado": state.status()}
    if command in {"dar_beso", "dar_un_beso"}:
        state.dar_beso()
        return {"ok": True, "estado": state.status()}
    if command == "detenerse":
        state.stop_motion()
        state.reset_pose()
        return {"ok": True, "estado": state.status()}
    raise ValueError(f"Comando no soportado: {command}")


def run_headless_check(model: mujoco.MjModel, data: mujoco.MjData, state: G1TeacherState) -> None:
    for step_index in range(int(4.0 / model.opt.timestep)):
        if step_index == int(0.5 / model.opt.timestep):
            state.start_motion(adelante=0.20, costado=0.0, giro=0.35, tiempo=10.0)
        if step_index == int(1.5 / model.opt.timestep):
            state.stop_motion()

        (
            base_x,
            base_y,
            base_z,
            yaw,
            world_vx,
            world_vy,
            turn,
            target_pose,
            _,
        ) = state.step(model.opt.timestep)
        apply_kinematic_base(model, data, base_x, base_y, base_z, yaw, world_vx, world_vy, turn)
        apply_direct_pose(model, data, target_pose)
        mujoco.mj_forward(model, data)

    print(
        "G1 stability OK: "
        f"base_z={data.qpos[2]:.3f} "
        f"x={data.qpos[0]:.3f} "
        f"y={data.qpos[1]:.3f} "
        f"yaw={state.status()['yaw']:.3f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulador docente G1 sobre Unitree MuJoCo.")
    parser.add_argument("--check-model", action="store_true")
    parser.add_argument("--check-stability", action="store_true")
    args = parser.parse_args()

    model = mujoco.MjModel.from_xml_path(config.ROBOT_SCENE)
    data = mujoco.MjData(model)
    model.opt.timestep = config.SIMULATE_DT

    if args.check_model:
        print(f"G1 XML OK: nq={model.nq} nv={model.nv} nu={model.nu}")
        return

    state = G1TeacherState(base_z=float(data.qpos[2]), neutral_pose=data.qpos[7 : 7 + model.nu])

    if args.check_stability:
        run_headless_check(model, data, state)
        return

    lock = threading.Lock()
    viewer = mujoco.viewer.launch_passive(model, data)
    api_server = create_api_server(state)
    api_host, api_port = api_server.server_address

    print(f"[API] Escuchando comandos de alumnos en {api_host}:{api_port}")
    print("[API] Metodos: movimiento(...), saludar(), dar_beso(), detenerse()")

    def api_thread() -> None:
        api_server.serve_forever(poll_interval=0.1)

    def simulation_thread() -> None:
        ChannelFactoryInitialize(config.DOMAIN_ID, config.INTERFACE)
        unitree = UnitreeSdk2Bridge(model, data)

        if config.USE_JOYSTICK:
            unitree.SetupJoystick(device_id=0, js_type=config.JOYSTICK_TYPE)
        if config.PRINT_SCENE_INFORMATION:
            unitree.PrintSceneInformation()

        while viewer.is_running():
            step_start = time.perf_counter()

            with lock:
                (
                    base_x,
                    base_y,
                    base_z,
                    yaw,
                    world_vx,
                    world_vy,
                    turn,
                    target_pose,
                    _,
                ) = state.step(model.opt.timestep)

                data.xfrc_applied[:] = 0.0
                apply_kinematic_base(
                    model,
                    data,
                    base_x,
                    base_y,
                    base_z,
                    yaw,
                    world_vx,
                    world_vy,
                    turn,
                )
                apply_direct_pose(model, data, target_pose)
                mujoco.mj_forward(model, data)

            time_until_next_step = model.opt.timestep - (
                time.perf_counter() - step_start
            )
            if time_until_next_step > 0:
                time.sleep(time_until_next_step)

        api_server.shutdown()
        api_server.server_close()

    def viewer_thread() -> None:
        while viewer.is_running():
            with lock:
                viewer.sync()
            time.sleep(config.VIEWER_DT)

    threads = [
        threading.Thread(target=api_thread, name="g1_api", daemon=True),
        threading.Thread(target=simulation_thread, name="g1_sim"),
        threading.Thread(target=viewer_thread, name="g1_viewer"),
    ]
    for thread in threads:
        thread.start()
    for thread in threads[1:]:
        thread.join()


if __name__ == "__main__":
    main()
