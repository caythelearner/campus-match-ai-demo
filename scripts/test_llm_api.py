from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from campus_match.config import load_config  # noqa: E402
from campus_match.llm_client import call_llm_text  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Test configured LLM API with a tiny request.")
    parser.add_argument("--config", default=str(ROOT / "configs/default.json"))
    parser.add_argument("--prompt", default="用一句中文回复：连接正常。")
    args = parser.parse_args()

    load_config(args.config)
    text = call_llm_text(
        system="你是一个简短回复的测试助手。",
        user=args.prompt,
        temperature=0.0,
        max_tokens=80,
    )
    if not text:
        raise SystemExit("LLM is not configured. Fill ANTHROPIC_AUTH_TOKEN and ANTHROPIC_MODEL in .env.")
    print(text.strip())


if __name__ == "__main__":
    main()
