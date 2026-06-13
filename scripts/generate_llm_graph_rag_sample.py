from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from campus_match.config import load_config  # noqa: E402
from campus_match.graph_rag import build_explanation_prompt, llm_explanation, template_explanation  # noqa: E402
from campus_match.io_utils import write_json  # noqa: E402
from campus_match.kg import ProfileGraph  # noqa: E402


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a tiny LLM GraphRAG sample without running full pipeline.")
    parser.add_argument("--config", default=str(ROOT / "configs/default.json"))
    parser.add_argument("--match-index", type=int, default=0)
    parser.add_argument("--output", default=str(ROOT / "outputs/llm_graph_rag_sample.json"))
    args = parser.parse_args()

    load_config(args.config)
    profiles = json.loads((ROOT / "data/profiles.json").read_text(encoding="utf-8"))
    matches = json.loads((ROOT / "outputs/matches.json").read_text(encoding="utf-8"))
    triples = read_csv_dicts(ROOT / "data/triples.csv")
    if not matches:
        raise SystemExit("No matches found. Run scripts/run_pipeline.py first.")

    by_id = {profile["user_id"]: profile for profile in profiles}
    match = matches[min(max(args.match_index, 0), len(matches) - 1)]
    user = by_id[match["user_id"]]
    candidate = by_id[match["candidate_id"]]
    graph = ProfileGraph(triples)
    evidence = graph.path_evidence(user["user_id"], candidate["user_id"])
    prompt = build_explanation_prompt(user, candidate, match, evidence)

    result = llm_explanation(prompt)
    if result is None:
        raise SystemExit("LLM is not configured. Fill ANTHROPIC_AUTH_TOKEN and ANTHROPIC_MODEL in .env.")

    fallback = template_explanation(user, candidate, match, evidence)
    row = {
        "user_id": user["user_id"],
        "candidate_id": candidate["user_id"],
        "match_score": match.get("final_score"),
        "graph_evidence_count": len(evidence),
        "llm_explanation": result,
        "offline_fallback_for_comparison": fallback,
    }
    write_json(Path(args.output), row)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
