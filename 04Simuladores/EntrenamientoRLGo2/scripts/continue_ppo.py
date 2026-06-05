from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import VecNormalize

from go2_rl import Go2WalkEnv


CHECKPOINT_RE = re.compile(r"ppo_go2_(\d+)_steps\.zip$")


def make_env():
    return Monitor(Go2WalkEnv())


def checkpoint_steps(path: Path) -> int:
    match = CHECKPOINT_RE.search(path.name)
    return int(match.group(1)) if match else -1


def resolve_source(source_run: Path, source_checkpoint: str | None) -> tuple[Path, Path]:
    if not source_checkpoint:
        source_model = source_run / "model.zip"
        source_vecnormalize = source_run / "vecnormalize.pkl"
        if not source_model.exists():
            raise FileNotFoundError(f"No encontre modelo fuente: {source_model}")
        if not source_vecnormalize.exists():
            raise FileNotFoundError(f"No encontre VecNormalize fuente: {source_vecnormalize}")
        return source_model, source_vecnormalize

    checkpoint_dir = source_run / "checkpoints"
    if not checkpoint_dir.exists():
        raise FileNotFoundError(f"No existe carpeta de checkpoints: {checkpoint_dir}")

    candidates = [path for path in checkpoint_dir.glob("ppo_go2_*_steps.zip") if checkpoint_steps(path) >= 0]
    if not candidates:
        raise FileNotFoundError(f"No encontre checkpoints en: {checkpoint_dir}")

    if source_checkpoint == "latest":
        source_model = max(candidates, key=checkpoint_steps)
        steps = checkpoint_steps(source_model)
    else:
        steps = int(source_checkpoint)
        source_model = checkpoint_dir / f"ppo_go2_{steps}_steps.zip"

    source_vecnormalize = checkpoint_dir / f"ppo_go2_vecnormalize_{steps}_steps.pkl"
    if not source_model.exists():
        raise FileNotFoundError(f"No encontre checkpoint fuente: {source_model}")
    if not source_vecnormalize.exists():
        raise FileNotFoundError(f"No encontre VecNormalize del checkpoint: {source_vecnormalize}")
    return source_model, source_vecnormalize


def main() -> None:
    parser = argparse.ArgumentParser(description="Continua un entrenamiento PPO existente de Go2.")
    parser.add_argument("--source-run", default="runs/ppo_go2_flat_v1")
    parser.add_argument(
        "--source-checkpoint",
        default=None,
        help='Checkpoint a cargar: "latest" o numero de pasos. Si se omite usa model.zip final.',
    )
    parser.add_argument("--timesteps", type=int, default=1_000_000)
    parser.add_argument("--run-name", default="ppo_go2_flat_v2")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--check-only", action="store_true", help="Solo valida que el modelo cargue y sale.")
    args = parser.parse_args()

    source_run = Path(args.source_run)
    source_model, source_vecnormalize = resolve_source(source_run, args.source_checkpoint)

    run_dir = Path("runs") / args.run_name
    if run_dir.exists() and any(run_dir.iterdir()) and not args.check_only:
        raise FileExistsError(f"El run destino ya existe y no esta vacio: {run_dir}")

    env = make_vec_env(make_env, n_envs=1, seed=args.seed)
    env = VecNormalize.load(source_vecnormalize, env)
    env.training = True
    env.norm_reward = True

    model = PPO.load(
        source_model,
        env=env,
        tensorboard_log=str(run_dir / "tb"),
        seed=args.seed,
    )

    print(f"[OK] Cargado modelo: {source_model}")
    print(f"[OK] Cargada normalizacion: {source_vecnormalize}")
    print(f"[INFO] Timesteps previos del modelo: {model.num_timesteps}")

    if args.check_only:
        env.close()
        return

    run_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = CheckpointCallback(
        save_freq=25_000,
        save_path=str(run_dir / "checkpoints"),
        name_prefix="ppo_go2",
        save_vecnormalize=True,
    )

    model.learn(
        total_timesteps=args.timesteps,
        callback=checkpoint,
        progress_bar=True,
        reset_num_timesteps=False,
        tb_log_name=args.run_name,
    )

    model.save(run_dir / "model")
    env.save(run_dir / "vecnormalize.pkl")
    env.close()
    print(f"[OK] Modelo continuado guardado en {run_dir}")


if __name__ == "__main__":
    main()
