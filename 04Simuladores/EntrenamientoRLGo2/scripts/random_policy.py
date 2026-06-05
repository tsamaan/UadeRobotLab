from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from go2_rl import Go2WalkEnv


def main() -> None:
    env = Go2WalkEnv(render_mode="human")
    obs, _ = env.reset()
    for _ in range(400):
        obs, reward, terminated, truncated, info = env.step(env.action_space.sample() * 0.2)
        if terminated or truncated:
            obs, _ = env.reset()
    env.close()


if __name__ == "__main__":
    main()
