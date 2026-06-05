from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from go2_rl import Go2WalkEnv


CHECKPOINT_RE = re.compile(r"ppo_go2_(\d+)_steps\.zip$")


def checkpoint_steps(path: Path) -> int:
    match = CHECKPOINT_RE.search(path.name)
    return int(match.group(1)) if match else -1


def latest_checkpoint(run_dir: Path) -> tuple[Path, Path, int] | None:
    checkpoint_dir = run_dir / "checkpoints"
    if not checkpoint_dir.exists():
        return None

    candidates = [path for path in checkpoint_dir.glob("ppo_go2_*_steps.zip") if checkpoint_steps(path) >= 0]
    if not candidates:
        return None

    model_path = max(candidates, key=checkpoint_steps)
    steps = checkpoint_steps(model_path)
    vec_path = checkpoint_dir / f"ppo_go2_vecnormalize_{steps}_steps.pkl"
    if not vec_path.exists():
        return None
    return model_path, vec_path, steps


def wait_until_stable(path: Path, seconds: float = 1.0) -> bool:
    if not path.exists():
        return False
    size_before = path.stat().st_size
    time.sleep(seconds)
    return path.exists() and path.stat().st_size == size_before and size_before > 0


def evaluate(model_path: Path, vec_path: Path, seconds: float, deterministic: bool) -> None:
    env = DummyVecEnv([lambda: Go2WalkEnv(render_mode="human")])
    env = VecNormalize.load(vec_path, env)
    env.training = False
    env.norm_reward = False

    model = PPO.load(model_path, env=env)
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

    while time.perf_counter() - start < seconds:
        action, _ = model.predict(obs, deterministic=deterministic)
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
        avg_reward = sum(rewards) / len(rewards)
        avg_vel = sum(velocities) / len(velocities)
        avg_rear_ratio = sum(rear_ratios) / len(rear_ratios)
        avg_front_activity = sum(front_activities) / len(front_activities)
        avg_rear_activity = sum(rear_activities) / len(rear_activities)
        avg_rear_penalty = sum(rear_penalties) / len(rear_penalties)
        avg_rear_clearance = sum(rear_clearances) / len(rear_clearances)
        avg_rear_clearance_penalty = sum(rear_clearance_penalties) / len(rear_clearance_penalties)
        print(
            "[EVAL] "
            f"reward_prom={avg_reward:.3f} "
            f"vel_x_prom={avg_vel:.3f} "
            f"rear_ratio={avg_rear_ratio:.3f} "
            f"front_act={avg_front_activity:.3f} "
            f"rear_act={avg_rear_activity:.3f} "
            f"rear_pen={avg_rear_penalty:.3f} "
            f"rear_clearance={avg_rear_clearance:.3f} "
            f"rear_clear_pen={avg_rear_clearance_penalty:.3f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Mira checkpoints de entrenamiento sin cortar el training.")
    parser.add_argument("--run-dir", default="runs/ppo_go2_walk_v1")
    parser.add_argument("--seconds", type=float, default=12.0, help="Segundos visibles por checkpoint.")
    parser.add_argument("--poll", type=float, default=30.0, help="Cada cuantos segundos busca checkpoints nuevos.")
    parser.add_argument("--once", action="store_true", help="Evalua solo el ultimo checkpoint y sale.")
    parser.add_argument("--deterministic", action="store_true")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    seen_steps = -1

    while True:
        latest = latest_checkpoint(run_dir)
        if latest is None:
            print(f"[WAIT] Todavia no hay checkpoint completo en {run_dir / 'checkpoints'}")
            if args.once:
                raise SystemExit(1)
            time.sleep(args.poll)
            continue

        model_path, vec_path, steps = latest
        if steps <= seen_steps:
            if args.once:
                print(f"[INFO] Ultimo checkpoint ya evaluado: {steps} steps")
                return
            time.sleep(args.poll)
            continue

        if not wait_until_stable(model_path) or not wait_until_stable(vec_path):
            print(f"[WAIT] Checkpoint {steps} todavia se esta escribiendo...")
            time.sleep(args.poll)
            continue

        print(f"[VIEW] Evaluando checkpoint {steps} steps")
        print(f"       modelo: {model_path}")
        evaluate(model_path, vec_path, seconds=args.seconds, deterministic=args.deterministic)
        seen_steps = steps

        if args.once:
            return
        time.sleep(args.poll)


if __name__ == "__main__":
    main()
