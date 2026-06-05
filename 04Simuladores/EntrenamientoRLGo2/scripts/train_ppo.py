from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import VecNormalize

from go2_rl import Go2WalkEnv


def make_env():
    return Monitor(Go2WalkEnv())


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena PPO para caminar Go2 en MuJoCo.")
    parser.add_argument("--timesteps", type=int, default=200_000)
    parser.add_argument("--run-name", default="ppo_go2_walk")
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    run_dir = Path("runs") / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    env = make_vec_env(make_env, n_envs=1, seed=args.seed)
    env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.0)

    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=256,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.005,
        verbose=1,
        tensorboard_log=str(run_dir / "tb"),
        seed=args.seed,
    )

    checkpoint = CheckpointCallback(
        save_freq=25_000,
        save_path=str(run_dir / "checkpoints"),
        name_prefix="ppo_go2",
        save_vecnormalize=True,
    )
    model.learn(total_timesteps=args.timesteps, callback=checkpoint, progress_bar=True)

    model.save(run_dir / "model")
    env.save(run_dir / "vecnormalize.pkl")
    env.close()
    print(f"[OK] Modelo guardado en {run_dir}")


if __name__ == "__main__":
    main()
