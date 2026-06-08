from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from campus_match.config import load_config  # noqa: E402
from campus_match.pipeline import run_pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Campus Match AI pipeline.")
    parser.add_argument("--config", default=str(ROOT / "configs/default.json"))
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--n-users", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--run-gnn", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.n_users is not None:
        config["n_users"] = args.n_users
    if args.top_k is not None:
        config["top_k"] = args.top_k
    summary = run_pipeline(config, root=args.root, run_gnn=args.run_gnn)
    print("Pipeline completed.")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
