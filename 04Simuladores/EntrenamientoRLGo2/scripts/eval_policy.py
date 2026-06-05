from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from go2_rl import Go2WalkEnv


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalua una politica PPO de Go2.")
    parser.add_argument("--run-dir", default="runs/ppo_go2_walk")
    parser.add_argument("--seconds", type=float, default=20.0)
    parser.add_argument("--deterministic", action="store_true")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    env = DummyVecEnv([lambda: Go2WalkEnv(render_mode="human")])
    env = VecNormalize.load(run_dir / "vecnormalize.pkl", env)
    env.training = False
    env.norm_reward = False

    model = PPO.load(run_dir / "model", env=env)
    obs = env.reset()
    start = time.perf_counter()
    rewards = []
    velocities = []
    rear_ratios = []
    front_activities = []
    rear_activities = []
    rear_penalties = []
    rear_clearances = []
    rear_clearance_penalties = []
    while time.perf_counter() - start < args.seconds:
        action, _ = model.predict(obs, deterministic=args.deterministic)
        obs, reward, done, info = env.step(action)
        step_info = info[0]
        rewards.append(float(reward[0]))
        velocities.append(float(step_info.get("x_velocity", 0.0)))
        rear_ratios.append(float(step_info.get("rear_activity_ratio", 0.0)))
        front_activities.append(float(step_info.get("front_joint_activity", 0.0)))
        rear_activities.append(float(step_info.get("rear_joint_activity", 0.0)))
        rear_penalties.append(float(step_info.get("penalty_rear_activity", 0.0)))
        rear_clearances.append(float(step_info.get("rear_clearance", 0.0)))
        rear_clearance_penalties.append(float(step_info.get("penalty_rear_clearance", 0.0)))
        if done[0]:
            obs = env.reset()
        time.sleep(0.02)

    env.close()
    if rewards:
        print(
            "[EVAL] "
            f"reward_prom={sum(rewards) / len(rewards):.3f} "
            f"vel_x_prom={sum(velocities) / len(velocities):.3f} "
            f"rear_ratio={sum(rear_ratios) / len(rear_ratios):.3f} "
            f"front_act={sum(front_activities) / len(front_activities):.3f} "
            f"rear_act={sum(rear_activities) / len(rear_activities):.3f} "
            f"rear_pen={sum(rear_penalties) / len(rear_penalties):.3f} "
            f"rear_clearance={sum(rear_clearances) / len(rear_clearances):.3f} "
            f"rear_clear_pen={sum(rear_clearance_penalties) / len(rear_clearance_penalties):.3f}"
        )


if __name__ == "__main__":
    main()
