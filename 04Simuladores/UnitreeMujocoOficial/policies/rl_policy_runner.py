from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


def missing_packages() -> list[str]:
    required = {
        "stable_baselines3": "stable-baselines3",
        "huggingface_sb3": "huggingface-sb3",
        "torch": "torch",
    }
    return [pip_name for module_name, pip_name in required.items() if importlib.util.find_spec(module_name) is None]


def check_sb3_model(model_path: Path) -> bool:
    try:
        from stable_baselines3 import SAC

        model = SAC.load(model_path)
    except Exception as exc:
        print("[ADAPTAR] El modelo existe, pero no carga limpio en este entorno.")
        print(f"          Error: {type(exc).__name__}: {exc}")
        print()
        print("          Esto suele pasar cuando el checkpoint fue guardado con otra combinacion")
        print("          de Python/NumPy/Stable-Baselines3. Hay que usar versiones compatibles")
        print("          o exportar la politica a ONNX/TorchScript.")
        return False

    print("[OK] Modelo SB3 cargado.")
    print(f"     Observation space: {model.observation_space}")
    print(f"     Action space     : {model.action_space}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Runner base para politica RL de Go2.")
    parser.add_argument("--model", default="models/best_model.zip", help="Ruta al modelo SB3/zip.")
    parser.add_argument("--domain", type=int, default=1)
    parser.add_argument("--interface", default="Ethernet")
    parser.add_argument("--check", action="store_true", help="Solo verifica dependencias y modelo.")
    args = parser.parse_args()

    missing = missing_packages()
    if missing:
        print("[FALTA] Dependencias RL no instaladas:")
        print("        py -3.10 -m pip install -r policies\\requirements_rl.txt")
        print("        Faltan: " + ", ".join(missing))
        raise SystemExit(2)

    model_path = Path(args.model)
    if not model_path.is_absolute():
        model_path = Path(__file__).resolve().parent / model_path

    if not model_path.exists():
        print("[FALTA] Modelo RL no encontrado:")
        print(f"        {model_path}")
        print()
        print("Candidato para investigar:")
        print("        https://huggingface.co/cagataydev/sac-unitree-go2-mujoco")
        print()
        print("Ojo: antes de usarlo hay que adaptar observaciones y acciones al unitree_mujoco oficial.")
        raise SystemExit(3)

    if args.check:
        if not check_sb3_model(model_path):
            raise SystemExit(5)
        print("[OK] Dependencias y modelo encontrados.")
        return

    print("[PENDIENTE] El runner RL todavia necesita el adaptador de observaciones/acciones.")
    print("            Flujo esperado: LowState/SportModeState -> obs -> policy -> LowCmd.")
    print(f"            Modelo detectado: {model_path}")
    raise SystemExit(4)


if __name__ == "__main__":
    main()
