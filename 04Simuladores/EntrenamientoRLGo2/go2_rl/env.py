from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path

import gymnasium as gym
import mujoco
import numpy as np
from gymnasium import spaces


DEFAULT_MODEL = (
    Path("..")
    / "UnitreeMujocoOficial"
    / "unitree_mujoco"
    / "unitree_robots"
    / "go2"
    / "flat_scene.xml"
)
REAR_FOOT_BODY_NAMES = ("RR_foot", "RL_foot")

FLAT_SCENE_XML = """<mujoco model="go2 flat scene">
  <include file="go2.xml"/>

  <statistic center="0 0 0.1" extent="0.8"/>

  <visual>
    <headlight diffuse="0.6 0.6 0.6" ambient="0.3 0.3 0.3" specular="0 0 0"/>
    <rgba haze="0.15 0.25 0.35 1"/>
    <global azimuth="-130" elevation="-20"/>
  </visual>

  <asset>
    <texture type="skybox" builtin="gradient" rgb1="0.3 0.5 0.7" rgb2="0 0 0" width="512" height="3072"/>
    <texture type="2d" name="groundplane" builtin="checker" mark="edge"
      rgb1="0.2 0.3 0.4" rgb2="0.1 0.2 0.3" markrgb="0.8 0.8 0.8"
      width="300" height="300"/>
    <material name="groundplane" texture="groundplane" texuniform="true" texrepeat="5 5" reflectance="0.2"/>
  </asset>

  <worldbody>
    <light pos="0 0 1.5" dir="0 0 -1" directional="true"/>
    <geom name="floor" size="0 0 0.05" type="plane" material="groundplane"/>
  </worldbody>
</mujoco>
"""


def ensure_flat_scene(model_path: Path) -> Path:
    if model_path.name == "flat_scene.xml" and not model_path.exists():
        model_path.write_text(FLAT_SCENE_XML, encoding="utf-8")
    return model_path


@dataclass
class Go2WalkEnvConfig:
    model_path: Path = DEFAULT_MODEL
    frame_skip: int = 10
    episode_seconds: float = 12.0
    target_velocity: float = 0.45
    target_height: float = 0.30
    action_scale_hip: float = 0.25
    action_scale_thigh: float = 0.45
    action_scale_calf: float = 0.55
    kp: float = 45.0
    kd: float = 3.0
    reset_noise: float = 0.03
    rear_activity_min_ratio: float = 0.55
    rear_activity_penalty_weight: float = 0.35
    tilt_penalty_weight: float = 0.20
    vertical_velocity_penalty_weight: float = 0.08
    action_rate_penalty_weight: float = 0.02
    rear_clearance_window: int = 60
    rear_clearance_target: float = 0.045
    rear_clearance_penalty_weight: float = 5.0


class Go2WalkEnv(gym.Env):
    """Gymnasium environment for training a Go2 walking policy in MuJoCo.

    The policy outputs desired joint-position offsets. The environment applies a
    PD controller and sends torques to the official Unitree MuJoCo model.
    """

    metadata = {"render_modes": ["human"], "render_fps": 50}

    def __init__(self, config: Go2WalkEnvConfig | None = None, render_mode: str | None = None):
        self.config = config or Go2WalkEnvConfig()
        self.render_mode = render_mode

        model_path = ensure_flat_scene(self.config.model_path)
        self.model = mujoco.MjModel.from_xml_path(str(model_path))
        self.data = mujoco.MjData(self.model)
        self.dt = float(self.model.opt.timestep) * self.config.frame_skip
        self.max_steps = max(1, int(self.config.episode_seconds / self.dt))

        self.default_qpos = self.model.key_qpos[0].copy()
        self.default_ctrl = self.model.key_ctrl[0].copy()
        self.action_scale = np.array(
            [
                self.config.action_scale_hip,
                self.config.action_scale_thigh,
                self.config.action_scale_calf,
            ]
            * 4,
            dtype=np.float32,
        )
        self.ctrl_low = self.model.actuator_ctrlrange[:, 0].copy()
        self.ctrl_high = self.model.actuator_ctrlrange[:, 1].copy()
        self.rear_foot_body_ids = [self.model.body(name).id for name in REAR_FOOT_BODY_NAMES]

        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(self.model.nu,), dtype=np.float32)
        obs_size = 3 + 3 + 3 + 12 + 12 + 12 + 1
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(obs_size,), dtype=np.float32)

        self.viewer = None
        self.step_count = 0
        self.last_action = np.zeros(self.model.nu, dtype=np.float32)
        self.rear_foot_height_history = [
            deque(maxlen=self.config.rear_clearance_window) for _ in self.rear_foot_body_ids
        ]

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)

        self.data.qpos[:] = self.default_qpos
        self.data.qvel[:] = 0.0
        self.data.qpos[0] += self.np_random.uniform(-0.03, 0.03)
        self.data.qpos[1] += self.np_random.uniform(-0.03, 0.03)
        self.data.qpos[7:] += self.np_random.normal(0.0, self.config.reset_noise, size=12)
        self.last_action[:] = 0.0
        self._clear_rear_foot_history()
        self.step_count = 0

        for _ in range(20):
            self._apply_pd(self.default_ctrl)
            mujoco.mj_step(self.model, self.data)
        self._record_rear_foot_heights()

        return self._get_obs(), {}

    def step(self, action):
        action = np.clip(np.asarray(action, dtype=np.float32), -1.0, 1.0)
        target = self.default_ctrl + self.action_scale * action
        previous_action = self.last_action.copy()

        x_before = float(self.data.qpos[0])
        torque_sum = 0.0
        for _ in range(self.config.frame_skip):
            torque = self._apply_pd(target)
            torque_sum += float(np.mean(np.square(torque)))
            mujoco.mj_step(self.model, self.data)
        self._record_rear_foot_heights()

        x_after = float(self.data.qpos[0])
        velocity_x = (x_after - x_before) / self.dt
        self.step_count += 1

        reward, reward_info = self._reward(
            velocity_x,
            torque_sum / self.config.frame_skip,
            action,
            previous_action,
        )
        self.last_action = action.copy()
        obs = self._get_obs()
        terminated = self._terminated()
        truncated = self.step_count >= self.max_steps

        if self.render_mode == "human":
            self.render()

        info = {
            "x_position": x_after,
            "x_velocity": velocity_x,
            **reward_info,
        }
        return obs, reward, terminated, truncated, info

    def render(self):
        if self.render_mode != "human":
            return None
        if self.viewer is None:
            import mujoco.viewer

            self.viewer = mujoco.viewer.launch_passive(self.model, self.data)
        if self.viewer.is_running():
            self.viewer.sync()
        return None

    def close(self):
        if self.viewer is not None:
            self.viewer.close()
            self.viewer = None

    def _apply_pd(self, target: np.ndarray) -> np.ndarray:
        joint_pos = self.data.sensordata[0:12]
        joint_vel = self.data.sensordata[12:24]
        torque = self.config.kp * (target - joint_pos) - self.config.kd * joint_vel
        torque = np.clip(torque, self.ctrl_low, self.ctrl_high)
        self.data.ctrl[:] = torque
        return torque

    def _clear_rear_foot_history(self) -> None:
        for history in self.rear_foot_height_history:
            history.clear()

    def _record_rear_foot_heights(self) -> None:
        for body_id, history in zip(self.rear_foot_body_ids, self.rear_foot_height_history):
            history.append(float(self.data.xpos[body_id, 2]))

    def _rear_clearance_penalty(self, speed_gate: float) -> tuple[float, float]:
        if speed_gate <= 0.0:
            return 0.0, 0.0

        deficits = []
        clearances = []
        for history in self.rear_foot_height_history:
            if len(history) < max(5, self.config.rear_clearance_window // 3):
                continue
            clearance = max(history) - min(history)
            clearances.append(clearance)
            deficits.append(max(0.0, self.config.rear_clearance_target - clearance))

        if not deficits:
            return 0.0, 0.0

        avg_deficit = float(np.mean(deficits))
        avg_clearance = float(np.mean(clearances))
        penalty = self.config.rear_clearance_penalty_weight * speed_gate * avg_deficit
        return penalty, avg_clearance

    def _get_obs(self) -> np.ndarray:
        qpos = self.data.qpos
        qvel = self.data.qvel
        quat = qpos[3:7]
        gravity_body = self._rotate_inverse(quat, np.array([0.0, 0.0, -1.0]))

        joint_pos = self.data.sensordata[0:12] - self.default_ctrl
        joint_vel = self.data.sensordata[12:24]
        lin_vel = self._rotate_inverse(quat, qvel[0:3])
        ang_vel = self._rotate_inverse(quat, qvel[3:6])

        obs = np.concatenate(
            [
                gravity_body,
                lin_vel,
                ang_vel,
                joint_pos,
                joint_vel,
                self.last_action,
                np.array([self.config.target_velocity], dtype=np.float32),
            ]
        )
        return obs.astype(np.float32)

    def _reward(
        self,
        velocity_x: float,
        torque_cost: float,
        action: np.ndarray,
        previous_action: np.ndarray,
    ):
        quat = self.data.qpos[3:7]
        gravity_body = self._rotate_inverse(quat, np.array([0.0, 0.0, -1.0]))
        upright = max(0.0, float(-gravity_body[2]))
        height = float(self.data.qpos[2])
        joint_vel = self.data.sensordata[12:24]

        velocity_error = velocity_x - self.config.target_velocity
        velocity_reward = float(np.exp(-2.5 * velocity_error * velocity_error))
        alive_reward = 0.15
        upright_reward = 0.5 * upright
        height_penalty = 2.0 * abs(height - self.config.target_height)
        torque_penalty = 0.0008 * torque_cost
        action_penalty = 0.01 * float(np.mean(np.square(action)))
        lateral_penalty = 0.15 * abs(float(self.data.qvel[1]))
        vertical_velocity_penalty = self.config.vertical_velocity_penalty_weight * abs(float(self.data.qvel[2]))
        action_rate_penalty = self.config.action_rate_penalty_weight * float(
            np.mean(np.square(action - previous_action))
        )
        tilt_penalty = self.config.tilt_penalty_weight * float(np.linalg.norm(gravity_body[:2]))

        front_activity = float(np.mean(np.abs(joint_vel[0:6])))
        rear_activity = float(np.mean(np.abs(joint_vel[6:12])))
        rear_activity_ratio = rear_activity / (front_activity + 1e-6)
        speed_gate = float(np.clip((velocity_x - 0.10) / 0.25, 0.0, 1.0))
        rear_activity_penalty = (
            self.config.rear_activity_penalty_weight
            * speed_gate
            * max(0.0, self.config.rear_activity_min_ratio - rear_activity_ratio)
        )
        rear_clearance_penalty, rear_clearance = self._rear_clearance_penalty(speed_gate)

        reward = (
            1.8 * velocity_reward
            + alive_reward
            + upright_reward
            - height_penalty
            - torque_penalty
            - action_penalty
            - lateral_penalty
            - vertical_velocity_penalty
            - action_rate_penalty
            - tilt_penalty
            - rear_activity_penalty
            - rear_clearance_penalty
        )
        return reward, {
            "reward_velocity": velocity_reward,
            "reward_upright": upright_reward,
            "penalty_height": height_penalty,
            "penalty_torque": torque_penalty,
            "penalty_rear_activity": rear_activity_penalty,
            "penalty_tilt": tilt_penalty,
            "penalty_vertical_velocity": vertical_velocity_penalty,
            "front_joint_activity": front_activity,
            "rear_joint_activity": rear_activity,
            "rear_activity_ratio": rear_activity_ratio,
            "penalty_rear_clearance": rear_clearance_penalty,
            "rear_clearance": rear_clearance,
        }

    def _terminated(self) -> bool:
        height = float(self.data.qpos[2])
        quat = self.data.qpos[3:7]
        gravity_body = self._rotate_inverse(quat, np.array([0.0, 0.0, -1.0]))
        upright = float(-gravity_body[2])
        return height < 0.16 or height > 0.55 or upright < 0.45

    @staticmethod
    def _rotate_inverse(quat: np.ndarray, vec: np.ndarray) -> np.ndarray:
        w, x, y, z = quat
        q_vec = np.array([x, y, z], dtype=np.float64)
        t = 2.0 * np.cross(q_vec, vec)
        rotated = vec + w * t + np.cross(q_vec, t)
        return rotated
