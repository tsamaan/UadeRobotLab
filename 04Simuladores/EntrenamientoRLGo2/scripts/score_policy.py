from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from go2_rl import Go2WalkEnv


CHECKPOINT_RE = re.compile(r"ppo_go2_(\d+)_steps\.zip$")
FOOT_BODY_NAMES = ("FR_foot", "FL_foot", "RR_foot", "RL_foot")


def checkpoint_steps(path: Path) -> int:
    match = CHECKPOINT_RE.search(path.name)
    return int(match.group(1)) if match else -1


def resolve_policy(run_dir: Path, checkpoint: str | None) -> tuple[Path, Path]:
    if checkpoint is None:
        model_path = run_dir / "model.zip"
        vec_path = run_dir / "vecnormalize.pkl"
        if not model_path.exists():
            raise FileNotFoundError(f"No encontre modelo final: {model_path}")
        if not vec_path.exists():
            raise FileNotFoundError(f"No encontre VecNormalize final: {vec_path}")
        return model_path, vec_path

    checkpoint_dir = run_dir / "checkpoints"
    candidates = [path for path in checkpoint_dir.glob("ppo_go2_*_steps.zip") if checkpoint_steps(path) >= 0]
    if not candidates:
        raise FileNotFoundError(f"No encontre checkpoints en: {checkpoint_dir}")

    if checkpoint == "latest":
        model_path = max(candidates, key=checkpoint_steps)
        steps = checkpoint_steps(model_path)
    else:
        steps = int(checkpoint)
        model_path = checkpoint_dir / f"ppo_go2_{steps}_steps.zip"

    vec_path = checkpoint_dir / f"ppo_go2_vecnormalize_{steps}_steps.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"No encontre checkpoint: {model_path}")
    if not vec_path.exists():
        raise FileNotFoundError(f"No encontre VecNormalize: {vec_path}")
    return model_path, vec_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalua una politica sin abrir viewer.")
    parser.add_argument("--run-dir", default="runs/ppo_go2_flat_v3_rear_fix_test")
    parser.add_argument("--checkpoint", default="latest", help='"latest", numero de pasos, o "final".')
    parser.add_argument("--steps", type=int, default=600)
    parser.add_argument("--deterministic", action="store_true")
    args = parser.parse_args()

    checkpoint = None if args.checkpoint == "final" else args.checkpoint
    model_path, vec_path = resolve_policy(Path(args.run_dir), checkpoint)

    env = DummyVecEnv([lambda: Go2WalkEnv()])
    env = VecNormalize.load(vec_path, env)
    env.training = False
    env.norm_reward = False

    model = PPO.load(model_path, env=env)
    obs = env.reset()

    rewards = []
    velocities = []
    rear_ratios = []
    front_activities = []
    rear_activities = []
    rear_penalties = []
    rear_clearances = []
    rear_clearance_penalties = []
    foot_heights = {name: [] for name in FOOT_BODY_NAMES}
    terminations = 0

    foot_body_ids = {name: env.envs[0].model.body(name).id for name in FOOT_BODY_NAMES}

    for _ in range(args.steps):
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
        for name, body_id in foot_body_ids.items():
            foot_heights[name].append(float(env.envs[0].data.xpos[body_id, 2]))
        if done[0]:
            terminations += 1
            obs = env.reset()

    env.close()

    print(f"[POLICY] model={model_path}")
    print(f"[POLICY] vecnormalize={vec_path}")
    print(
        "[SCORE] "
        f"reward_prom={sum(rewards) / len(rewards):.3f} "
        f"vel_x_prom={sum(velocities) / len(velocities):.3f} "
        f"rear_ratio={sum(rear_ratios) / len(rear_ratios):.3f} "
        f"front_act={sum(front_activities) / len(front_activities):.3f} "
        f"rear_act={sum(rear_activities) / len(rear_activities):.3f} "
        f"rear_pen={sum(rear_penalties) / len(rear_penalties):.3f} "
        f"rear_clearance={sum(rear_clearances) / len(rear_clearances):.3f} "
        f"rear_clear_pen={sum(rear_clearance_penalties) / len(rear_clearance_penalties):.3f} "
        f"terminations={terminations}"
    )
    for name, values in foot_heights.items():
        print(
            "[FOOT] "
            f"{name} "
            f"mean_z={sum(values) / len(values):.3f} "
            f"min_z={min(values):.3f} "
            f"max_z={max(values):.3f} "
            f"range_z={max(values) - min(values):.3f}"
        )


if __name__ == "__main__":
    main()
