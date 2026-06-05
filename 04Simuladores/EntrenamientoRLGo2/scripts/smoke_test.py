from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from go2_rl import Go2WalkEnv


def main() -> None:
    env = Go2WalkEnv()
    obs, _ = env.reset(seed=1)
    total_reward = 0.0
    for _ in range(100):
        action = np.zeros(env.action_space.shape, dtype=np.float32)
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        if terminated or truncated:
            break
    env.close()
    print("obs_shape:", obs.shape)
    print("steps:", env.step_count)
    print("total_reward:", round(total_reward, 3))
    print("last_info:", info)


if __name__ == "__main__":
    main()
