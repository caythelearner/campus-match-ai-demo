from __future__ import annotations

import argparse
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from campus_match.config import load_config  # noqa: E402
from campus_match.io_utils import write_jsonl  # noqa: E402
from campus_match.llm_client import llm_config_status  # noqa: E402
from campus_match.realtime_rag import generate_realtime_chat_rag  # noqa: E402


class DemoApiHandler(SimpleHTTPRequestHandler):
    server_version = "CampusMatchDemoAPI/0.1"

    def __init__(self, *args: Any, directory: str | None = None, **kwargs: Any) -> None:
        super().__init__(*args, directory=directory or str(ROOT / "demo"), **kwargs)

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/chat-rag":
            self._send_json({"ok": False, "error": "unknown endpoint"}, status=404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            query = str(payload.get("query", "")).strip()
            if not query:
                self._send_json({"ok": False, "error": "query is required"}, status=400)
                return
            trace = generate_realtime_chat_rag(
                self.server.profiles,  # type: ignore[attr-defined]
                self.server.matches,  # type: ignore[attr-defined]
                user_id=str(payload.get("user_id") or ""),
                candidate_id=str(payload.get("candidate_id") or ""),
                query=query,
                dim=int(self.server.config.get("embedding_dim", 384)),  # type: ignore[attr-defined]
                use_llm=True,
            )
            trace["llm_config"] = llm_config_status()
            self.server.runtime_traces.append(trace)  # type: ignore[attr-defined]
            write_jsonl(ROOT / "outputs/realtime_chat_api_traces.jsonl", self.server.runtime_traces)  # type: ignore[attr-defined]
            self._send_json({"ok": True, "trace": trace})
        except Exception as exc:  # noqa: BLE001
            self._send_json({"ok": False, "error": str(exc)}, status=500)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve demo/index.html with a local server-side LLM RAG endpoint.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8023)
    parser.add_argument("--config", default=str(ROOT / "configs/default.json"))
    args = parser.parse_args()

    config = load_config(args.config)
    profiles = json.loads((ROOT / "data/profiles.json").read_text(encoding="utf-8"))
    matches = json.loads((ROOT / "outputs/matches_with_explanations.json").read_text(encoding="utf-8"))
    handler = lambda *h_args, **h_kwargs: DemoApiHandler(*h_args, directory=str(ROOT / "demo"), **h_kwargs)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    server.config = config  # type: ignore[attr-defined]
    server.profiles = profiles  # type: ignore[attr-defined]
    server.matches = matches  # type: ignore[attr-defined]
    server.runtime_traces = []  # type: ignore[attr-defined]
    status = llm_config_status()
    print(f"Serving demo at http://localhost:{args.port}/")
    print(f"LLM configured: {status.get('configured')} provider={status.get('provider')} model={status.get('model')}")
    server.serve_forever()


if __name__ == "__main__":
    main()
