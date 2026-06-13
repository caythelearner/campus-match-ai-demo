from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "demo" / "index.html"


def load_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def js_data(payload: dict[str, Any]) -> str:
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return data.replace("</", "<\\/")


def build_payload(root: Path) -> dict[str, Any]:
    return {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "imageBase": "assets",
        "profiles": load_json(root / "data/profiles.json", []),
        "matches": load_json(root / "outputs/matches_with_explanations.json", []),
        "sceneRequests": load_json(root / "outputs/scene_requests.json", []),
        "sceneMatches": load_json(root / "outputs/scene_matches.json", []),
        "relationshipDynamics": load_json(root / "outputs/relationship_dynamics.json", []),
        "dateContexts": load_json(root / "outputs/date_contexts.json", []),
        "governanceRecords": load_json(root / "outputs/governance_records.json", []),
        "chatRetrievalTraces": load_json(root / "outputs/chat_vector_retrieval_trace.json", []),
        "vectorSearchTraces": load_json(root / "outputs/vector_search_trace.json", []),
        "faissAnnBenchmark": load_json(root / "outputs/faiss_ann_benchmark.json", {}),
        "intentGraphTraces": load_json(root / "outputs/intent_graph_traces.json", []),
        "hybridSearchTraces": load_json(root / "outputs/hybrid_search_traces.json", []),
        "profileTagEvidence": load_json(root / "outputs/profile_tag_evidence.json", []),
        "graphAlgorithmTrace": load_json(root / "outputs/graph_algorithm_trace.json", {}),
        "embeddingMetadata": load_json(root / "indexes/embedding_metadata.json", {}),
        "gnnMetrics": load_json(root / "outputs/gnn_metrics.json", {}),
        "gnnPairScores": load_json(root / "outputs/gnn_pair_scores.json", []),
        "gnnRiskMetrics": load_json(root / "outputs/gnn_node_risk_metrics.json", {}),
        "gnnRiskScores": load_json(root / "outputs/gnn_node_risk_scores.json", []),
        "summary": load_json(root / "outputs/pipeline_summary.json", {}),
        "neo4jSummary": load_json(root / "outputs/neo4j/neo4j_trace_summary.json", {}),
        "neo4jNodes": load_csv(root / "outputs/neo4j/campus_match_ai_nodes.csv", []),
        "neo4jRelationships": load_csv(root / "outputs/neo4j/campus_match_ai_relationships.csv", []),
    }


def copy_demo_assets(root: Path, payload: dict[str, Any], output_dir: Path) -> None:
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    user_ids = {profile["user_id"] for profile in payload.get("profiles", []) if profile.get("user_id")}

    for old_asset in assets_dir.glob("U*.png"):
        if old_asset.stem not in user_ids:
            old_asset.unlink()

    for user_id in user_ids:
        source = root / "images" / f"{user_id}.png"
        if source.exists():
            shutil.copy2(source, assets_dir / source.name)


HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>搭个蛋 AI 星球舱</title>
  <style>
    :root {
      --bg: #f5f8f6;
      --panel: #ffffff;
      --panel-soft: #edf7f3;
      --ink: #17222a;
      --muted: #62737a;
      --line: #d5e3df;
      --accent: #087f73;
      --accent-strong: #075f57;
      --accent-soft: #d9f2ed;
      --blue: #2f64d6;
      --rose: #bd3b2f;
      --amber: #b97918;
      --green: #1f8f50;
      --violet: #6657c8;
      --cream: #fff8ea;
      --coral: #d45d43;
      --surface: linear-gradient(145deg, rgba(255, 255, 255, 0.94), rgba(246, 251, 248, 0.86));
      --shadow: 0 18px 42px rgba(31, 45, 48, 0.12);
      --shadow-soft: 0 8px 18px rgba(31, 45, 48, 0.07);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      background:
        radial-gradient(circle at 12% 14%, rgba(255,255,255,0.92) 0 2px, transparent 2.4px),
        radial-gradient(circle at 86% 16%, rgba(168,207,251,0.30), transparent 26%),
        radial-gradient(circle at 12% 74%, rgba(244,199,171,0.24), transparent 26%),
        linear-gradient(135deg, #fdfdfd 0%, #f3f1f8 48%, #ebf4f5 100%);
      background-size: 88px 88px, auto, auto, auto;
      color: var(--ink);
      font-family: Inter, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
      font-size: 14px;
      line-height: 1.5;
    }

    button,
    input,
    select {
      font: inherit;
    }

    button {
      cursor: pointer;
    }

    [hidden] {
      display: none !important;
    }

    @keyframes galaxyFloat {
      0% { transform: translate3d(0, 0, 0) rotate(0deg); }
      50% { transform: translate3d(0, -18px, 0) rotate(5deg); }
      100% { transform: translate3d(0, 0, 0) rotate(0deg); }
    }

    @keyframes galaxyFloatReverse {
      0% { transform: translate3d(0, 0, 0) rotate(0deg); }
      50% { transform: translate3d(0, 20px, 0) rotate(-5deg); }
      100% { transform: translate3d(0, 0, 0) rotate(0deg); }
    }

    .galaxy-orb {
      position: absolute;
      border-radius: 999px;
      pointer-events: none;
      z-index: 0;
    }

    .galaxy-orb.blue {
      width: 164px;
      height: 164px;
      right: 8%;
      top: 12%;
      background: radial-gradient(circle at 30% 30%, #ffffff, #a8cffb 42%, #7fa8d6 100%);
      box-shadow: 0 24px 48px rgba(126, 157, 214, 0.34), inset -12px -12px 22px rgba(20,35,64,0.10);
      animation: galaxyFloatReverse 8s ease-in-out infinite;
    }

    .galaxy-orb.gold {
      width: 78px;
      height: 78px;
      right: 27%;
      bottom: 16%;
      background: radial-gradient(circle at 30% 30%, #fff5d1, #f4c7ab 48%, #d69e7b 100%);
      box-shadow: 0 18px 34px rgba(214, 158, 123, 0.30), inset -7px -7px 14px rgba(95,58,34,0.10);
      animation: galaxyFloat 7s ease-in-out infinite 0.4s;
    }

    .galaxy-orb.dark {
      width: 34px;
      height: 34px;
      right: 5%;
      bottom: 35%;
      background: radial-gradient(circle at 30% 30%, #7b8190, #384151 50%, #111827);
      box-shadow: 0 16px 30px rgba(17,24,39,0.24), inset -5px -5px 10px rgba(0,0,0,0.34);
      animation: galaxyFloat 6.5s ease-in-out infinite;
    }

    .mode-shell {
      min-height: 100vh;
      padding: 36px 22px;
      display: grid;
      align-items: center;
      background:
        radial-gradient(circle at 12% 18%, rgba(255,255,255,0.90) 0 2px, transparent 2.4px),
        radial-gradient(circle at 72% 18%, rgba(168,207,251,0.44), transparent 22%),
        radial-gradient(circle at 82% 78%, rgba(244,199,171,0.42), transparent 22%),
        radial-gradient(circle at 20% 82%, rgba(216,196,255,0.34), transparent 24%),
        linear-gradient(135deg, #fdfdfd 0%, #f3f1f8 50%, #ebf4f5 100%);
      background-size: 92px 92px, auto, auto;
      position: relative;
      overflow: hidden;
    }

    .mode-shell::before {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      background:
        linear-gradient(120deg, transparent 0 48%, rgba(137, 126, 214, 0.16) 48.2% 48.45%, transparent 48.8%),
        linear-gradient(18deg, transparent 0 68%, rgba(244, 199, 171, 0.24) 68.2% 68.45%, transparent 68.8%);
      opacity: 0.9;
    }

    .mode-shell > * {
      position: relative;
    }

    .mode-inner {
      width: min(1100px, 100%);
      margin: 0 auto;
      z-index: 1;
    }

    .mode-hero {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(300px, 420px);
      gap: 30px;
      align-items: center;
      margin-bottom: 24px;
    }

    .mode-hero h1 {
      margin: 0;
      font-size: clamp(64px, 9vw, 118px);
      line-height: 0.88;
      letter-spacing: 0;
      color: #231f63;
      font-weight: 900;
      text-transform: uppercase;
    }

    .mode-hero h1 span {
      color: transparent;
      background: linear-gradient(90deg, #8aa8ff, #b58cff 58%, #efb28d);
      -webkit-background-clip: text;
      background-clip: text;
    }

    .mode-hero p {
      margin: 18px 0 0;
      color: #667085;
      font-size: 16px;
      max-width: 680px;
    }

    .mode-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(260px, 1fr));
      gap: 14px;
    }

    .mode-card {
      border: 1px solid rgba(255, 255, 255, 0.72);
      border-radius: 28px;
      background: rgba(255, 255, 255, 0.54);
      backdrop-filter: blur(18px);
      -webkit-backdrop-filter: blur(18px);
      box-shadow: 0 22px 54px rgba(72, 76, 135, 0.12);
      padding: 24px;
      text-align: left;
      color: inherit;
      min-height: 260px;
      display: grid;
      align-content: start;
      gap: 10px;
      position: relative;
      overflow: hidden;
    }

    .mode-card::before {
      content: "";
      position: absolute;
      left: 0;
      right: 0;
      top: 0;
      height: 100%;
      opacity: 0.68;
      background:
        radial-gradient(circle at 82% 18%, rgba(168,207,251,0.50), transparent 28%),
        radial-gradient(circle at 14% 80%, rgba(244,199,171,0.34), transparent 30%);
    }

    .mode-card:hover {
      border-color: rgba(255, 255, 255, 0.96);
      transform: translateY(-5px);
      box-shadow: 0 32px 74px rgba(72, 76, 135, 0.18);
    }

    .mode-card h2 {
      margin: 0;
      font-size: 22px;
      letter-spacing: 0;
    }

    .mode-card p {
      margin: 0;
      color: #667085;
    }

    .mode-card .tag-row {
      margin-top: 4px;
    }

    .mode-summary {
      background: rgba(255, 255, 255, 0.52);
      border: 1px solid rgba(255, 255, 255, 0.72);
      border-radius: 32px;
      padding: 16px;
      color: #344054;
      box-shadow: 0 24px 60px rgba(72, 76, 135, 0.12);
      backdrop-filter: blur(18px);
      -webkit-backdrop-filter: blur(18px);
    }

    .app {
      display: grid;
      grid-template-columns: 300px 1fr;
      min-height: 100vh;
      background:
        radial-gradient(circle at 20px 24px, rgba(8, 127, 115, 0.10) 1px, transparent 1.3px),
        linear-gradient(135deg, rgba(255, 248, 234, 0.82), transparent 34%),
        linear-gradient(225deg, rgba(217, 242, 237, 0.82), transparent 36%),
        #f6f9f7;
      background-size: 90px 90px, auto, auto, auto;
    }

    .sidebar {
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      border-right: 1px solid rgba(215, 225, 228, 0.9);
      background:
        radial-gradient(circle at 18px 22px, rgba(8, 127, 115, 0.10) 1px, transparent 1.3px),
        linear-gradient(180deg, rgba(255,255,255,0.97), rgba(240,248,245,0.95) 58%, rgba(255,248,234,0.95));
      background-size: 86px 86px, auto;
      box-shadow: 10px 0 28px rgba(28, 39, 49, 0.06);
    }

    .brand {
      padding: 18px 18px 14px;
      border-bottom: 1px solid var(--line);
      background:
        linear-gradient(135deg, rgba(8, 127, 115, 0.16), rgba(185, 121, 24, 0.08));
    }

    .brand h1 {
      margin: 0;
      font-size: 22px;
      line-height: 1.15;
      letter-spacing: 0;
    }

    .brand p {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 12px;
    }

    .search-wrap {
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
    }

    .search-wrap input,
    .search-wrap select,
    .toolbar select {
      width: 100%;
      height: 38px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.92);
      color: var(--ink);
      padding: 0 11px;
      outline: none;
    }

    .search-wrap input:focus,
    .toolbar select:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.14);
    }

    .user-list {
      overflow: auto;
      padding: 10px;
      display: grid;
      gap: 8px;
    }

    .user-button {
      border: 1px solid transparent;
      background: transparent;
      border-radius: 8px;
      padding: 8px;
      display: grid;
      grid-template-columns: 42px 1fr;
      gap: 10px;
      text-align: left;
      color: inherit;
      min-width: 0;
    }

    .user-button:hover,
    .user-button.active {
      background: #ffffff;
      border-color: #9fcfc7;
      box-shadow: var(--shadow-soft);
    }

    .avatar {
      width: 42px;
      height: 42px;
      border-radius: 8px;
      object-fit: cover;
      background: #edf1f5;
      border: 1px solid var(--line);
    }

    .user-button strong,
    .truncate {
      display: block;
      min-width: 0;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
    }

    .user-button span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-top: 2px;
    }

    .main {
      min-width: 0;
      padding: 20px 24px 36px;
      background:
        linear-gradient(90deg, rgba(255,255,255,0.28), transparent 42%),
        linear-gradient(180deg, rgba(255,255,255,0.16), transparent 28%);
    }

    .topbar {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 14px;
      align-items: start;
      margin-bottom: 14px;
      border: 1px solid rgba(207, 222, 219, 0.88);
      border-radius: 8px;
      background:
        linear-gradient(135deg, rgba(255,255,255,0.92), rgba(246,251,248,0.78));
      box-shadow: var(--shadow-soft);
      padding: 14px;
    }

    .topbar h2 {
      margin: 0;
      font-size: 24px;
      line-height: 1.2;
      letter-spacing: 0;
    }

    .topbar p {
      margin: 5px 0 0;
      color: var(--muted);
    }

    .tabs {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .top-actions {
      display: flex;
      gap: 8px;
      justify-content: flex-end;
      flex-wrap: wrap;
      margin-bottom: 8px;
    }

    .tab-button {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(238,247,245,0.82));
      color: var(--ink);
      padding: 8px 12px;
      min-height: 36px;
      box-shadow: 0 4px 10px rgba(28, 39, 49, 0.04);
    }

    .tab-button.active {
      background: linear-gradient(135deg, var(--accent), #0a6d8f);
      border-color: var(--accent);
      color: #ffffff;
      box-shadow: 0 10px 20px rgba(8, 127, 115, 0.24);
    }

    .metrics {
      display: grid;
      grid-template-columns: repeat(5, minmax(128px, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }

    .metric,
    .panel,
    .card {
      background: var(--surface);
      border: 1px solid rgba(207, 222, 219, 0.92);
      border-radius: 8px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }

    .metric {
      padding: 14px;
      min-height: 76px;
      position: relative;
      overflow: hidden;
    }

    .metric::before {
      content: "";
      position: absolute;
      left: 0;
      top: 0;
      right: 0;
      height: 4px;
      background: linear-gradient(90deg, var(--accent), var(--amber));
    }

    .metric span {
      color: var(--muted);
      font-size: 12px;
    }

    .metric strong {
      display: block;
      font-size: 24px;
      line-height: 1.2;
      margin-top: 6px;
      letter-spacing: 0;
    }

    .profile-grid {
      display: grid;
      grid-template-columns: minmax(260px, 340px) 1fr;
      gap: 14px;
      margin-bottom: 14px;
    }

    .panel {
      padding: 18px;
      min-width: 0;
    }

    .profile-media {
      display: grid;
      grid-template-columns: 92px 1fr;
      gap: 14px;
      align-items: center;
    }

    .profile-media img {
      width: 92px;
      height: 92px;
      border-radius: 8px;
      object-fit: cover;
      border: 1px solid var(--line);
      background: #edf1f5;
    }

    .profile-media h3 {
      margin: 0;
      font-size: 20px;
      letter-spacing: 0;
    }

    .profile-media p,
    .muted {
      color: var(--muted);
    }

    .profile-media p {
      margin: 4px 0 0;
    }

    .info-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 14px;
    }

    .info-item {
      border: 1px solid rgba(215, 225, 228, 0.84);
      border-radius: 8px;
      padding: 10px;
      min-width: 0;
      background: rgba(255, 255, 255, 0.72);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.72);
    }

    .info-item span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 4px;
    }

    .info-item strong {
      overflow-wrap: anywhere;
    }

    .tag-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 10px;
    }

    .tag {
      display: inline-flex;
      align-items: center;
      max-width: 100%;
      border-radius: 999px;
      padding: 4px 9px;
      background: linear-gradient(135deg, var(--accent-soft), #f4fbf9);
      color: var(--accent-strong);
      font-size: 12px;
      overflow-wrap: anywhere;
    }

    .tag.blue {
      background: #dbeafe;
      color: #1d4ed8;
    }

    .tag.rose {
      background: #fee4e2;
      color: var(--rose);
    }

    .section-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin: 2px 0 10px;
    }

    .section-head h3 {
      margin: 0;
      font-size: 18px;
      letter-spacing: 0;
    }

    .toolbar {
      min-width: 220px;
    }

    .cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(310px, 1fr));
      gap: 12px;
    }

    .card {
      padding: 16px;
      min-width: 0;
      transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
    }

    .card:hover {
      transform: translateY(-2px);
      border-color: #9fcfc7;
      box-shadow: 0 22px 48px rgba(31, 45, 48, 0.15);
    }

    .card-head {
      display: grid;
      grid-template-columns: 54px 1fr auto;
      gap: 10px;
      align-items: center;
      margin-bottom: 10px;
    }

    .card-head img {
      width: 54px;
      height: 54px;
      border-radius: 8px;
      object-fit: cover;
      border: 1px solid var(--line);
      background: #edf1f5;
    }

    .card h4 {
      margin: 0;
      font-size: 16px;
      letter-spacing: 0;
    }

    .score-pill {
      min-width: 66px;
      text-align: center;
      border-radius: 999px;
      padding: 6px 8px;
      background: linear-gradient(135deg, #e9f8ed, #f5fbf7);
      color: var(--green);
      font-weight: 700;
      font-size: 13px;
    }

    .score-list {
      display: grid;
      gap: 8px;
      margin: 10px 0;
    }

    .score-row {
      display: grid;
      grid-template-columns: 96px 1fr 44px;
      gap: 8px;
      align-items: center;
      color: var(--muted);
      font-size: 12px;
    }

    .bar {
      height: 8px;
      border-radius: 999px;
      background: #e2e9ed;
      overflow: hidden;
    }

    .bar i {
      display: block;
      height: 100%;
      width: 0;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--accent), var(--amber));
    }

    .copy {
      margin: 9px 0 0;
      color: #344054;
      overflow-wrap: anywhere;
    }

    .list {
      margin: 8px 0 0;
      padding: 0;
      list-style: none;
      display: grid;
      gap: 6px;
    }

    .list li {
      padding-left: 12px;
      position: relative;
      color: #344054;
    }

    .list li::before {
      content: "";
      position: absolute;
      left: 0;
      top: 10px;
      width: 4px;
      height: 4px;
      border-radius: 50%;
      background: var(--accent);
    }

    details {
      margin-top: 10px;
      border-top: 1px solid var(--line);
      padding-top: 10px;
    }

    summary {
      cursor: pointer;
      color: var(--accent-strong);
      font-weight: 700;
    }

    .path-list {
      margin-top: 8px;
      display: grid;
      gap: 6px;
    }

    .path-row {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px;
      background: #fbfcfe;
      color: #344054;
      overflow-wrap: anywhere;
    }

    .scene-layout,
    .two-col {
      display: grid;
      grid-template-columns: minmax(290px, 0.8fr) minmax(340px, 1.2fr);
      gap: 12px;
    }

    .kv {
      display: grid;
      grid-template-columns: 120px 1fr;
      gap: 8px;
      border-top: 1px solid var(--line);
      padding-top: 10px;
      margin-top: 10px;
    }

    .kv span {
      color: var(--muted);
    }

    .risk-low {
      color: var(--green);
    }

    .risk-medium {
      color: var(--amber);
    }

    .risk-high {
      color: var(--rose);
    }

    .heat-chart {
      width: 100%;
      height: 190px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background:
        radial-gradient(circle at 16px 18px, rgba(8,127,115,0.08) 1px, transparent 1.2px),
        linear-gradient(180deg, rgba(255,255,255,0.96), rgba(246,251,248,0.88));
      background-size: 76px 76px, auto;
      margin-top: 10px;
    }

    .table-wrap {
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.90);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 780px;
    }

    th,
    td {
      text-align: left;
      padding: 10px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }

    th {
      color: var(--muted);
      font-size: 12px;
      background: #fbfcfe;
      position: sticky;
      top: 0;
      z-index: 1;
    }

    tr:last-child td {
      border-bottom: 0;
    }

    .empty {
      padding: 24px;
      text-align: center;
      color: var(--muted);
      border: 1px dashed var(--line);
      border-radius: 8px;
      background:
        radial-gradient(circle at 14px 16px, rgba(8,127,115,0.08) 1px, transparent 1.2px),
        linear-gradient(145deg, rgba(255,255,255,0.86), rgba(248,252,250,0.76));
      background-size: 74px 74px, auto;
    }

    .user-app {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 320px 1fr;
      position: relative;
      isolation: isolate;
      overflow: hidden;
      background:
        radial-gradient(circle at 16% 12%, rgba(255,255,255,0.92) 0 2px, transparent 2.3px),
        radial-gradient(circle at 86% 16%, rgba(168,207,251,0.35), transparent 25%),
        radial-gradient(circle at 11% 80%, rgba(244,199,171,0.26), transparent 24%),
        radial-gradient(circle at 76% 76%, rgba(216,196,255,0.28), transparent 28%),
        linear-gradient(135deg, #fdfdfd 0%, #f3f1f8 48%, #ebf4f5 100%);
      background-size: 88px 88px, auto, auto, auto;
    }

    .user-app::before {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      z-index: -1;
      background:
        linear-gradient(115deg, transparent 0 36%, rgba(137, 126, 214, 0.13) 36.2% 36.45%, transparent 36.8%),
        linear-gradient(22deg, transparent 0 62%, rgba(244, 199, 171, 0.18) 62.2% 62.45%, transparent 62.8%),
        linear-gradient(160deg, transparent 0 72%, rgba(168, 207, 251, 0.14) 72.2% 72.45%, transparent 72.7%);
      opacity: 0.85;
    }

    .user-rail {
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      padding: 18px;
      background:
        radial-gradient(circle at 24% 10%, rgba(255,255,255,0.70) 0 2px, transparent 2.3px),
        radial-gradient(circle at 84% 20%, rgba(168,207,251,0.50), transparent 30%),
        linear-gradient(180deg, rgba(35,31,99,0.94), rgba(100,88,190,0.78) 44%, rgba(255,255,255,0.42) 100%);
      background-size: 82px 82px, auto;
      border-right: 1px solid rgba(255, 255, 255, 0.58);
      box-shadow: 18px 0 42px rgba(72, 76, 135, 0.16);
      color: #ffffff;
    }

    .user-main {
      min-width: 0;
      padding: 18px 22px 34px;
    }

    .user-rail .brand {
      border: 1px solid rgba(255,255,255,0.34);
      border-radius: 28px;
      background:
        linear-gradient(135deg, rgba(255,255,255,0.24), rgba(255,255,255,0.08));
      box-shadow: 0 18px 42px rgba(31,35,92,0.18);
      margin-bottom: 12px;
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
    }

    .user-rail .brand p,
    .user-rail .muted,
    .user-rail .copy {
      color: rgba(255,255,255,0.78);
    }

    .user-rail .panel {
      background: rgba(255,255,255,0.68);
      color: var(--ink);
      border-color: rgba(255,255,255,0.66);
      box-shadow: 0 18px 42px rgba(72,76,135,0.14);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
    }

    .user-rail .panel .muted,
    .user-rail .panel .copy {
      color: var(--muted);
    }

    .user-star-head {
      border: 1px solid rgba(255, 255, 255, 0.66);
      border-radius: 32px;
      background:
        radial-gradient(circle at 82% 18%, rgba(168,207,251,0.45), transparent 24%),
        radial-gradient(circle at 14% 82%, rgba(244,199,171,0.32), transparent 26%),
        linear-gradient(135deg, rgba(35,31,99,0.92), rgba(107,91,210,0.78) 54%, rgba(255,255,255,0.35));
      background-size: 88px 88px, auto, auto;
      color: #ffffff;
      padding: 24px;
      margin-bottom: 14px;
      box-shadow: 0 26px 64px rgba(72, 76, 135, 0.20);
      overflow: hidden;
      position: relative;
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
    }

    .user-star-head::after {
      content: "";
      position: absolute;
      left: 24px;
      right: 24px;
      bottom: 12px;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.34), transparent);
    }

    .user-star-head h2,
    .user-star-head p {
      color: inherit;
    }

    .user-nav {
      display: grid;
      grid-template-columns: repeat(4, minmax(90px, 1fr));
      gap: 8px;
      margin-top: 12px;
    }

    .user-tab-button,
    .planet-mode-button {
      border: 1px solid rgba(255, 255, 255, 0.46);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.18);
      color: #ffffff;
      padding: 10px 12px;
      min-height: 38px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.12);
    }

    .user-tab-button.active,
    .planet-mode-button.active {
      background: #ffffff;
      color: #10212c;
      border-color: #ffffff;
      font-weight: 700;
    }

    .planet-mode-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 10px 0;
    }

    .planet-mode-row .planet-mode-button {
      border-color: rgba(255,255,255,0.74);
      background: rgba(255,255,255,0.70);
      color: var(--ink);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
    }

    .planet-mode-row .planet-mode-button.active {
      background: linear-gradient(135deg, #231f63, #8aa8ff 70%, #efb28d);
      color: #ffffff;
      border-color: rgba(255,255,255,0.72);
    }

    .user-pane[hidden] {
      display: none !important;
    }

    .cosmic-panel {
      border: 1px solid rgba(255, 255, 255, 0.72);
      border-radius: 28px;
      background:
        radial-gradient(circle at 85% 18%, rgba(168,207,251,0.32), transparent 28%),
        radial-gradient(circle at 12% 82%, rgba(244,199,171,0.22), transparent 30%),
        linear-gradient(145deg, rgba(255,255,255,0.78), rgba(255,255,255,0.46));
      background-size: 96px 86px, auto;
      box-shadow: 0 22px 54px rgba(72,76,135,0.12);
      padding: 16px;
      position: relative;
      overflow: hidden;
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
    }

    .cosmic-panel::before {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(118deg, transparent 0 50%, rgba(137,126,214,0.10) 50.2% 50.5%, transparent 50.8%),
        linear-gradient(22deg, transparent 0 68%, rgba(244,199,171,0.14) 68.2% 68.5%, transparent 68.8%);
      background-size: auto;
      opacity: 0.9;
    }

    .cosmic-panel > * {
      position: relative;
    }

    .radar-search {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      margin: 10px 0;
    }

    .radar-search input,
    .message-input input {
      height: 40px;
      border: 1px solid rgba(207, 222, 219, 0.94);
      border-radius: 8px;
      padding: 0 12px;
      outline: none;
      width: 100%;
      background: rgba(255, 255, 255, 0.92);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.82);
    }

    .radar-visual-grid {
      display: grid;
      grid-template-columns: minmax(280px, 1fr) minmax(280px, 1fr);
      gap: 12px;
      margin-top: 12px;
    }

    .intent-map {
      width: 100%;
      height: 230px;
      border: 1px solid rgba(207, 222, 219, 0.88);
      border-radius: 8px;
      background:
        linear-gradient(90deg, rgba(8,127,115,0.06) 1px, transparent 1px),
        linear-gradient(0deg, rgba(8,127,115,0.05) 1px, transparent 1px),
        rgba(255,255,255,0.78);
      background-size: 34px 34px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.84);
    }

    .intent-node text {
      font-size: 10px;
      fill: #17313a;
      pointer-events: none;
    }

    .intent-node rect {
      rx: 6;
      stroke: rgba(23, 34, 42, 0.12);
      stroke-width: 1;
      filter: drop-shadow(0 5px 9px rgba(31,45,48,0.12));
    }

    .intent-edge {
      stroke: rgba(30, 88, 96, 0.34);
      stroke-width: 1.5;
    }

    .intent-node-query rect { fill: #17313a; }
    .intent-node-query text { fill: #ffffff; }
    .intent-node-explicit rect { fill: #d9f2ed; }
    .intent-node-inferred rect { fill: #fff1d2; }
    .intent-node-profile_term rect { fill: #e7ecff; }

    .retrieval-stack {
      display: grid;
      gap: 8px;
    }

    .retrieval-card {
      border: 1px solid rgba(207, 222, 219, 0.9);
      border-radius: 8px;
      padding: 10px;
      background: rgba(255,255,255,0.82);
    }

    .retrieval-card .score-pill {
      float: right;
      margin-left: 8px;
    }

    .score-split {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 6px;
      margin-top: 8px;
    }

    .score-mini {
      border: 1px solid rgba(215, 225, 228, 0.82);
      border-radius: 8px;
      padding: 6px;
      background: #f8fbfa;
      min-width: 0;
    }

    .score-mini span {
      display: block;
      color: var(--muted);
      font-size: 10px;
    }

    .score-mini strong {
      display: block;
      margin-top: 2px;
      font-size: 13px;
    }

    .path-strip {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      margin-top: 8px;
      align-items: center;
    }

    .path-chip {
      border: 1px solid rgba(8, 127, 115, 0.22);
      border-radius: 8px;
      padding: 4px 7px;
      background: rgba(217, 242, 237, 0.64);
      color: #12443e;
      font-size: 11px;
      max-width: 100%;
      overflow-wrap: anywhere;
    }

    .path-arrow {
      color: var(--muted);
      font-size: 12px;
    }

    .evidence-card {
      border: 1px solid rgba(207, 222, 219, 0.94);
      border-radius: 8px;
      padding: 12px;
      background:
        linear-gradient(145deg, rgba(255,255,255,0.96), rgba(240,248,245,0.82));
      box-shadow: var(--shadow-soft);
    }

    .evidence-card blockquote {
      margin: 10px 0;
      padding: 10px 12px;
      border-left: 3px solid var(--accent);
      background: rgba(217, 242, 237, 0.48);
      border-radius: 0 8px 8px 0;
    }

    .evidence-map {
      width: 100%;
      height: 116px;
      margin-top: 8px;
      border-radius: 8px;
      border: 1px solid rgba(207,222,219,0.9);
      background: #fbfdfc;
    }

    .poster-wall {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 12px;
      margin-top: 12px;
    }

    .mobile-intent-tree {
      display: none;
    }

    .message-input {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      margin-top: 10px;
    }

    .archive-grid {
      display: grid;
      grid-template-columns: minmax(280px, 0.8fr) minmax(320px, 1.2fr);
      gap: 12px;
    }

    .memory-strip {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      margin-top: 10px;
    }

    .day-strip {
      display: grid;
      grid-template-columns: repeat(7, minmax(54px, 1fr));
      gap: 8px;
      margin: 12px 0;
    }

    .day-pill {
      border: 1px solid rgba(215, 225, 228, 0.9);
      border-radius: 8px;
      padding: 8px;
      text-align: center;
      background:
        linear-gradient(145deg, rgba(255,255,255,0.86), rgba(245,250,247,0.72));
      color: var(--muted);
      min-height: 52px;
      box-shadow: 0 6px 14px rgba(31, 45, 48, 0.05);
    }

    .day-pill.active {
      border-color: var(--accent);
      background: linear-gradient(135deg, #d9f2ed, #fff5dd);
      color: var(--accent-strong);
      font-weight: 700;
      box-shadow: 0 10px 24px rgba(8, 127, 115, 0.14);
    }

    .action-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(170px, 1fr));
      gap: 10px;
      margin: 12px 0;
    }

    .action-context {
      display: grid;
      gap: 3px;
      margin-top: 14px;
      padding: 11px 12px;
      border: 1px solid rgba(207, 222, 219, 0.88);
      border-radius: 8px;
      background: linear-gradient(135deg, rgba(255,255,255,0.86), rgba(255,248,234,0.68));
      color: var(--ink);
    }

    .action-context strong {
      font-size: 15px;
    }

    .action-context span {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.55;
    }

    .action-button {
      border: 1px solid rgba(215, 225, 228, 0.86);
      border-radius: 8px;
      background:
        linear-gradient(145deg, rgba(255,255,255,0.92), rgba(246,251,248,0.76));
      color: var(--ink);
      padding: 12px;
      min-height: 92px;
      text-align: left;
      display: grid;
      gap: 4px;
      box-shadow: var(--shadow-soft);
    }

    .action-button:hover,
    .action-button.active {
      border-color: var(--accent);
      background: linear-gradient(135deg, #ffffff, #e8f7f3 64%, #fff4df);
      box-shadow: var(--shadow-soft);
    }

    .action-button strong {
      font-size: 15px;
    }

    .action-button span {
      color: var(--muted);
      font-size: 12px;
    }

    .experience-input {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      margin-top: 10px;
    }

    .experience-input input {
      height: 40px;
      border: 1px solid rgba(207, 222, 219, 0.94);
      border-radius: 8px;
      padding: 0 12px;
      outline: none;
      background: rgba(255,255,255,0.92);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.82);
    }

    .experience-input input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.14);
    }

    .timeline {
      display: grid;
      gap: 8px;
      margin-top: 12px;
    }

    .timeline-item {
      border-left: 3px solid var(--accent);
      background:
        linear-gradient(145deg, rgba(255,255,255,0.92), rgba(246,251,248,0.78));
      border-radius: 0 8px 8px 0;
      padding: 10px 12px;
      box-shadow: var(--shadow);
    }

    .timeline-item strong {
      display: block;
      margin-bottom: 2px;
    }

    .chat-window {
      display: grid;
      gap: 10px;
      max-height: 360px;
      overflow: auto;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background:
        radial-gradient(circle at 16px 18px, rgba(8,127,115,0.09) 1px, transparent 1.2px),
        linear-gradient(180deg, rgba(250,252,251,0.96), rgba(238,248,244,0.88));
      background-size: 84px 84px, auto;
    }

    .message {
      max-width: 78%;
      padding: 9px 11px;
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.96);
      border: 1px solid var(--line);
      box-shadow: 0 4px 12px rgba(16, 24, 40, 0.05);
    }

    .message.me {
      margin-left: auto;
      background: linear-gradient(135deg, var(--accent), #0a6d8f);
      border-color: var(--accent);
      color: #ffffff;
    }

    .message.ai {
      background: linear-gradient(135deg, #eef7f5, #fff8e7);
      border-color: #c9dedb;
    }

    .message.other {
      background: linear-gradient(135deg, #ffffff, #fff7df);
      border-color: rgba(224, 184, 95, 0.46);
    }

    .message.latest-feedback {
      outline: 2px solid rgba(15, 118, 110, 0.2);
      box-shadow: 0 8px 18px rgba(15, 118, 110, 0.12);
    }

    .message strong {
      display: block;
      font-size: 12px;
      margin-bottom: 2px;
      opacity: 0.78;
    }

    .counterpart-card {
      border: 1px solid rgba(15, 118, 110, 0.22);
      border-radius: 8px;
      background:
        linear-gradient(145deg, #ffffff, #eef8f6 68%, #fff5df);
      padding: 12px;
      margin-bottom: 10px;
      box-shadow: var(--shadow-soft);
      display: grid;
      gap: 8px;
    }

    .counterpart-card.is-empty {
      background: rgba(255, 255, 255, 0.78);
      border-color: var(--line);
      box-shadow: none;
    }

    .counterpart-card h4 {
      margin: 0;
      font-size: 15px;
    }

    .counterpart-card .reply-line {
      margin: 0;
      color: var(--ink);
      line-height: 1.65;
    }

    .quick-replies {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 10px;
    }

    .quick-reply {
      border: 1px solid rgba(215, 225, 228, 0.94);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.9);
      padding: 7px 10px;
      color: var(--ink);
      max-width: 100%;
    }

    .quick-reply:hover {
      border-color: var(--accent);
      background: var(--accent-soft);
    }

    .locked {
      opacity: 0.55;
      cursor: not-allowed;
    }

    .completion-banner {
      border: 1px solid #b7d8d2;
      background: linear-gradient(135deg, #eef8f6, #fff5df);
      color: var(--accent-strong);
      border-radius: 8px;
      padding: 12px;
      margin-top: 10px;
    }

    .feature-map {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 12px;
    }

    .feature-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      background:
        linear-gradient(145deg, rgba(255,255,255,0.94), rgba(246,251,248,0.84));
      padding: 14px;
      box-shadow: var(--shadow);
    }

    .feature-card h4 {
      margin: 0 0 8px;
      font-size: 16px;
      letter-spacing: 0;
    }

    .feature-card p {
      margin: 6px 0;
      color: #344054;
    }

    .dashboard-grid {
      display: grid;
      grid-template-columns: minmax(420px, 1.45fr) minmax(300px, 0.75fr);
      gap: 14px;
      align-items: stretch;
    }

    .graph-stage {
      min-height: 620px;
      border: 1px solid rgba(255, 255, 255, 0.24);
      border-radius: 8px;
      background:
        radial-gradient(circle at 18px 22px, rgba(255, 255, 255, 0.18) 1px, transparent 1.3px),
        linear-gradient(118deg, transparent 0 42%, rgba(255,255,255,0.08) 42.2% 42.5%, transparent 42.8%),
        linear-gradient(135deg, #172a2f 0%, #0e514a 54%, #74451e 100%);
      background-size: 82px 82px, auto, auto;
      box-shadow: 0 26px 64px rgba(24, 34, 48, 0.24);
      padding: 16px;
      overflow: hidden;
      color: #ffffff;
    }

    .graph-stage h3,
    .graph-stage p {
      margin-top: 0;
      color: inherit;
    }

    .knowledge-map {
      width: 100%;
      height: 500px;
      display: block;
      border: 1px solid rgba(23, 33, 43, 0.08);
      border-radius: 8px;
      background:
        radial-gradient(circle at 16px 16px, rgba(8,127,115,0.08) 1px, transparent 1.2px),
        linear-gradient(180deg, rgba(255,255,255,0.92), rgba(237,246,244,0.86));
      background-size: 82px 82px, auto;
    }

    .neo4j-map {
      width: 100%;
      height: 520px;
      display: block;
      border: 1px solid rgba(23, 33, 43, 0.08);
      border-radius: 8px;
      background:
        radial-gradient(circle at 16px 16px, rgba(8,127,115,0.08) 1px, transparent 1.2px),
        linear-gradient(180deg, rgba(255,255,255,0.94), rgba(239,248,244,0.88));
      background-size: 82px 82px, auto;
    }

    .neo-map-note {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.74);
      color: #344054;
      padding: 10px 12px;
      margin-bottom: 10px;
    }

    .neo-focus-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 8px;
      margin-top: 10px;
    }

    .neo-link {
      stroke: rgba(52, 64, 84, 0.24);
      stroke-width: 1.2;
    }

    .neo-link-strong {
      stroke: rgba(8, 127, 115, 0.42);
      stroke-width: 2;
    }

    .neo-node-user {
      fill: #0f766e;
    }

    .neo-node-match {
      fill: #2f64d6;
    }

    .neo-node-scene {
      fill: #b97918;
    }

    .neo-node-dynamic {
      fill: #6657c8;
    }

    .neo-node-safety {
      fill: #bd3b2f;
    }

    .neo-node-governance {
      fill: #7a4a21;
    }

    .neo-node-default {
      fill: #667085;
    }

    .neo-label {
      fill: #17212b;
      font-size: 10px;
      font-weight: 700;
      paint-order: stroke;
      stroke: rgba(255, 255, 255, 0.92);
      stroke-width: 3px;
      stroke-linejoin: round;
    }

    .neo-rel-label {
      fill: #51616a;
      font-size: 9px;
      paint-order: stroke;
      stroke: rgba(255, 255, 255, 0.88);
      stroke-width: 3px;
      stroke-linejoin: round;
    }

    .neo-clickable {
      cursor: pointer;
      outline: none;
    }

    .neo-clickable circle,
    .graph-clickable circle,
    .tech-card,
    .card,
    .action-button,
    .quick-reply {
      transition: transform 160ms ease, box-shadow 160ms ease, stroke-width 160ms ease, border-color 160ms ease, background 160ms ease;
      transform-box: fill-box;
      transform-origin: center;
    }

    .neo-clickable:hover circle,
    .neo-clickable:focus circle {
      stroke: #17222a;
      stroke-width: 3;
      transform: scale(1.1);
    }

    .neo-node-selected {
      stroke: #17222a;
      stroke-width: 4;
    }

    .neo-node-detail {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: linear-gradient(145deg, rgba(255,255,255,0.96), rgba(246,251,248,0.88));
      margin-top: 12px;
      padding: 12px;
    }

    .neo-detail-grid {
      display: grid;
      grid-template-columns: minmax(260px, 0.85fr) minmax(320px, 1.15fr);
      gap: 12px;
      align-items: start;
    }

    .neo-props,
    .neo-rels {
      display: grid;
      gap: 8px;
    }

    .neo-prop,
    .neo-rel-row {
      border: 1px solid rgba(213, 227, 223, 0.82);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.72);
      padding: 8px 9px;
    }

    .neo-prop span,
    .neo-rel-row span {
      display: block;
      color: var(--muted);
      font-size: 11px;
      margin-bottom: 3px;
    }

    .neo-prop strong,
    .neo-rel-row strong {
      color: var(--ink);
      font-size: 13px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }

    .neo-rel-row p {
      margin: 4px 0 0;
      color: #344054;
      font-size: 12px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }

    .neo-node-link {
      border: 0;
      background: transparent;
      color: var(--accent-strong);
      padding: 0;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      text-align: left;
    }

    .neo-node-link:hover,
    .neo-node-link:focus {
      text-decoration: underline;
      outline: none;
    }

    .graph-node-user {
      fill: #0f766e;
    }

    .graph-node-interest {
      fill: #2563eb;
    }

    .graph-node-value {
      fill: #b45309;
    }

    .graph-node-context {
      fill: #b42318;
    }

    .graph-clickable {
      cursor: pointer;
      outline: none;
    }

    .graph-clickable:hover circle,
    .graph-clickable:focus circle {
      stroke: #17222a;
      stroke-width: 3;
      transform: scale(1.1);
    }

    .graph-node-selected {
      stroke: #17222a;
      stroke-width: 4;
    }

    .graph-link {
      stroke: rgba(52, 64, 84, 0.26);
      stroke-width: 1.3;
    }

    .graph-label {
      fill: #17212b;
      font-size: 12px;
      font-weight: 700;
      paint-order: stroke;
      stroke: rgba(255, 255, 255, 0.9);
      stroke-width: 4px;
      stroke-linejoin: round;
    }

    .graph-legend {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }

    .dashboard-node-detail {
      border: 1px solid rgba(213, 227, 223, 0.82);
      border-radius: 8px;
      background: linear-gradient(145deg, rgba(255,255,255,0.96), rgba(246,251,248,0.88));
      margin-top: 12px;
      padding: 12px;
      color: var(--ink);
    }

    .dashboard-node-detail h3,
    .dashboard-node-detail p {
      color: var(--ink);
    }

    .dashboard-node-detail .muted,
    .dashboard-node-detail span {
      color: var(--muted);
    }

    .tech-card:hover,
    .card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow);
    }

    .legend-dot {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 5px 9px;
      background: #ffffff;
      color: #344054;
      font-size: 12px;
    }

    .legend-dot i {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      display: inline-block;
    }

    .dashboard-side {
      display: grid;
      gap: 12px;
    }

    .soft-kpi-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    .soft-kpi {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: linear-gradient(145deg, rgba(255,255,255,0.92), rgba(246,251,248,0.80));
      padding: 12px;
    }

    .soft-kpi span {
      display: block;
      color: var(--muted);
      font-size: 12px;
    }

    .soft-kpi strong {
      display: block;
      margin-top: 5px;
      font-size: 22px;
      line-height: 1.2;
    }

    .orbit-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: linear-gradient(145deg, rgba(255,255,255,0.94), rgba(246,251,248,0.84));
      box-shadow: var(--shadow);
      padding: 14px;
      overflow: hidden;
    }

    .orbit-card h4 {
      margin: 0 0 8px;
      font-size: 16px;
      letter-spacing: 0;
    }

    .mini-bars {
      display: grid;
      gap: 8px;
    }

    .mini-bar-row {
      display: grid;
      grid-template-columns: 82px 1fr 42px;
      gap: 8px;
      align-items: center;
      font-size: 12px;
      color: var(--muted);
    }

    .flow-strip {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 8px;
      margin-top: 12px;
    }

    .flow-step {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: linear-gradient(145deg, rgba(255,255,255,0.92), rgba(255,248,234,0.72));
      padding: 9px;
      min-height: 72px;
      color: #344054;
    }

    .flow-step strong {
      display: block;
      color: var(--ink);
      margin-bottom: 3px;
    }

    .tech-cockpit {
      border: 1px solid rgba(183, 216, 210, 0.78);
      border-radius: 8px;
      background:
        radial-gradient(circle at 10% 14%, rgba(8, 127, 115, 0.24), transparent 26%),
        radial-gradient(circle at 82% 4%, rgba(47, 100, 214, 0.18), transparent 28%),
        linear-gradient(135deg, #101a20 0%, #0d3836 58%, #243338 100%);
      color: #f6fbf9;
      padding: 16px;
      box-shadow: 0 24px 56px rgba(16, 26, 32, 0.22);
      overflow: hidden;
      position: relative;
    }

    .tech-cockpit::before {
      content: "";
      position: absolute;
      inset: 0;
      background:
        linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px);
      background-size: 42px 42px;
      pointer-events: none;
    }

    .tech-cockpit > * {
      position: relative;
      z-index: 1;
    }

    .tech-cockpit h3,
    .tech-cockpit p {
      color: inherit;
    }

    .tech-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 12px;
      margin-top: 12px;
    }

    .tech-card {
      border: 1px solid rgba(215, 225, 228, 0.82);
      border-radius: 8px;
      background: linear-gradient(145deg, rgba(255,255,255,0.95), rgba(240,248,246,0.84));
      box-shadow: var(--shadow-soft);
      padding: 13px;
      display: grid;
      gap: 8px;
    }

    .tech-card h4 {
      margin: 0;
      font-size: 15px;
      letter-spacing: 0;
    }

    .status-pill {
      display: inline-flex;
      width: fit-content;
      align-items: center;
      border-radius: 999px;
      padding: 4px 8px;
      font-size: 11px;
      font-weight: 700;
      border: 1px solid rgba(213, 227, 223, 0.86);
      background: #ffffff;
      color: #344054;
    }

    .status-ok {
      color: #075f57;
      background: #d9f2ed;
      border-color: #a8d9d0;
    }

    .status-partial {
      color: #8a4b0f;
      background: #fff1d6;
      border-color: #f2c46d;
    }

    .status-missing {
      color: #8a2318;
      background: #fde5df;
      border-color: #efb5a8;
    }

    .tech-flow {
      display: grid;
      grid-template-columns: repeat(6, minmax(130px, 1fr));
      gap: 8px;
      margin-top: 12px;
    }

    .tech-step {
      border: 1px solid rgba(183, 216, 210, 0.78);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.09);
      padding: 10px;
      min-height: 92px;
    }

    .tech-step strong {
      display: block;
      color: #ffffff;
      margin-bottom: 4px;
    }

    .tech-step span {
      color: rgba(246, 251, 249, 0.74);
      font-size: 12px;
      line-height: 1.4;
    }

    .trace-list {
      display: grid;
      gap: 8px;
    }

    .trace-row {
      display: grid;
      grid-template-columns: 62px 1fr 58px;
      gap: 8px;
      align-items: center;
      border: 1px solid rgba(213, 227, 223, 0.86);
      border-radius: 8px;
      padding: 8px;
      background: rgba(255, 255, 255, 0.74);
      color: var(--ink);
    }

    .trace-row span {
      color: var(--muted);
      font-size: 11px;
    }

    .trace-row strong {
      font-size: 13px;
      overflow-wrap: anywhere;
    }

    .source-chip {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 3px 7px;
      font-size: 11px;
      color: #075f57;
      background: #d9f2ed;
      border: 1px solid #b7d8d2;
    }

    /* Unified SoulGalaxy style for the student-facing app only. */
    #userApp {
      --u-ink: #17124a;
      --u-muted: #6d6a86;
      --u-line: rgba(255, 255, 255, 0.74);
      --u-panel: rgba(255, 255, 255, 0.62);
      --u-panel-strong: rgba(255, 255, 255, 0.78);
      --u-violet: #6d5df6;
      --u-violet-strong: #4f46b8;
      --u-blue: #8aa8ff;
      --u-peach: #efb28d;
      --u-shadow: 0 22px 56px rgba(84, 74, 132, 0.14);
      --u-shadow-soft: 0 10px 26px rgba(84, 74, 132, 0.10);
      color: var(--u-ink);
      background:
        radial-gradient(circle at 12% 8%, rgba(255,255,255,0.94) 0 2px, transparent 2.4px),
        radial-gradient(circle at 84% 12%, rgba(168,207,251,0.38), transparent 24%),
        radial-gradient(circle at 12% 82%, rgba(244,199,171,0.27), transparent 24%),
        radial-gradient(circle at 78% 78%, rgba(216,196,255,0.28), transparent 28%),
        linear-gradient(135deg, #fdfdfd 0%, #f3f1f8 48%, #ebf4f5 100%);
      background-size: 88px 88px, auto, auto, auto, auto;
    }

    #userApp::before {
      background:
        linear-gradient(115deg, transparent 0 36%, rgba(137, 126, 214, 0.12) 36.2% 36.45%, transparent 36.8%),
        linear-gradient(22deg, transparent 0 62%, rgba(244, 199, 171, 0.18) 62.2% 62.45%, transparent 62.8%),
        linear-gradient(160deg, transparent 0 72%, rgba(168, 207, 251, 0.14) 72.2% 72.45%, transparent 72.7%);
    }

    #userApp::after {
      content: "";
      position: fixed;
      right: 42px;
      top: 86px;
      width: 128px;
      height: 128px;
      border-radius: 999px;
      pointer-events: none;
      background: radial-gradient(circle at 30% 30%, #ffffff, #a8cffb 44%, #7fa8d6);
      box-shadow: 0 24px 48px rgba(126, 157, 214, 0.24), inset -12px -12px 22px rgba(20,35,64,0.10);
      opacity: 0.54;
      animation: galaxyFloatReverse 9s ease-in-out infinite;
      z-index: -1;
    }

    #userApp .user-rail {
      background:
        radial-gradient(circle at 22% 10%, rgba(255,255,255,0.90) 0 2px, transparent 2.4px),
        radial-gradient(circle at 84% 18%, rgba(168,207,251,0.38), transparent 28%),
        linear-gradient(180deg, rgba(255,255,255,0.66), rgba(236,232,255,0.42) 52%, rgba(255,247,223,0.34));
      border-right: 1px solid rgba(255,255,255,0.76);
      box-shadow: 18px 0 46px rgba(84, 74, 132, 0.12);
      color: var(--u-ink);
    }

    #userApp .user-main {
      background: linear-gradient(90deg, rgba(255,255,255,0.22), transparent 42%);
    }

    #userApp .brand,
    #userApp .panel,
    #userApp .card,
    #userApp .metric,
    #userApp .cosmic-panel,
    #userApp .mode-summary,
    #userApp .retrieval-card,
    #userApp .evidence-card,
    #userApp .counterpart-card,
    #userApp .completion-banner,
    #userApp .action-context,
    #userApp .info-item,
    #userApp .score-mini,
    #userApp .path-row {
      border: 1px solid var(--u-line);
      border-radius: 28px;
      background:
        radial-gradient(circle at 88% 16%, rgba(168,207,251,0.20), transparent 30%),
        linear-gradient(145deg, rgba(255,255,255,0.74), rgba(245,243,252,0.50));
      box-shadow: var(--u-shadow-soft);
      backdrop-filter: blur(18px);
      -webkit-backdrop-filter: blur(18px);
      color: var(--u-ink);
    }

    #userApp .user-rail .brand {
      background:
        radial-gradient(circle at 82% 16%, rgba(168,207,251,0.32), transparent 28%),
        linear-gradient(145deg, rgba(255,255,255,0.76), rgba(236,232,255,0.54));
      box-shadow: var(--u-shadow);
    }

    #userApp .user-rail .brand p,
    #userApp .user-rail .muted,
    #userApp .user-rail .copy,
    #userApp .muted,
    #userApp .copy,
    #userApp .kv span,
    #userApp .info-item span,
    #userApp .score-mini span,
    #userApp .action-button span,
    #userApp .profile-media p {
      color: var(--u-muted);
    }

    #userApp .user-star-head {
      border: 1px solid rgba(255,255,255,0.76);
      border-radius: 34px;
      background:
        radial-gradient(circle at 84% 16%, rgba(168,207,251,0.42), transparent 26%),
        radial-gradient(circle at 12% 86%, rgba(244,199,171,0.32), transparent 28%),
        linear-gradient(145deg, rgba(255,255,255,0.76), rgba(236,232,255,0.52));
      color: var(--u-ink);
      box-shadow: var(--u-shadow);
    }

    #userApp .user-star-head h2 {
      color: var(--u-ink);
    }

    #userApp .user-star-head p {
      color: var(--u-muted);
    }

    #userApp .user-tab-button,
    #userApp .planet-mode-button,
    #userApp .tab-button,
    #userApp .quick-reply,
    #userApp .action-button {
      border: 1px solid rgba(255,255,255,0.76);
      border-radius: 999px;
      background: rgba(255,255,255,0.62);
      color: var(--u-ink);
      box-shadow: var(--u-shadow-soft);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
    }

    #userApp .user-tab-button.active,
    #userApp .planet-mode-button.active,
    #userApp .planet-mode-row .planet-mode-button.active,
    #userApp .tab-button.active,
    #userApp .quick-reply.active,
    #userApp .action-button.active,
    #userApp .mobile-join-button {
      border-color: rgba(255,255,255,0.78);
      background: linear-gradient(135deg, var(--u-blue), var(--u-violet) 58%, var(--u-peach));
      color: #ffffff;
      box-shadow: 0 16px 32px rgba(109, 93, 246, 0.24);
    }

    #userApp .action-button {
      border-radius: 26px;
      background:
        radial-gradient(circle at 90% 16%, rgba(168,207,251,0.22), transparent 30%),
        rgba(255,255,255,0.62);
    }

    #userApp .search-wrap {
      border-bottom-color: rgba(255,255,255,0.58);
    }

    #userApp input,
    #userApp select,
    #userApp .radar-search input,
    #userApp .message-input input,
    #userApp .experience-input input {
      border: 1px solid rgba(255,255,255,0.76);
      border-radius: 999px;
      background: rgba(255,255,255,0.70);
      color: var(--u-ink);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.92), var(--u-shadow-soft);
    }

    #userApp input:focus,
    #userApp select:focus {
      border-color: rgba(109, 93, 246, 0.50);
      box-shadow: 0 0 0 4px rgba(109, 93, 246, 0.12), var(--u-shadow-soft);
    }

    #userApp .profile-media img,
    #userApp .card-head img,
    #userApp .avatar {
      border-radius: 22px;
      border-color: rgba(255,255,255,0.82);
      background: #ece8ff;
      box-shadow: 0 10px 22px rgba(84, 74, 132, 0.12);
    }

    #userApp .metric::before {
      background: linear-gradient(90deg, var(--u-blue), var(--u-violet), var(--u-peach));
    }

    #userApp .tag {
      background: rgba(236,232,255,0.82);
      color: var(--u-violet-strong);
    }

    #userApp .tag.blue {
      background: rgba(219,234,254,0.86);
      color: #3652c9;
    }

    #userApp .tag.rose {
      background: rgba(255,228,226,0.86);
      color: #c2415d;
    }

    #userApp .score-pill {
      background: linear-gradient(135deg, rgba(236,232,255,0.94), rgba(255,247,223,0.90));
      color: var(--u-violet-strong);
      box-shadow: 0 10px 20px rgba(109, 93, 246, 0.12);
    }

    #userApp .bar {
      background: rgba(236,232,255,0.78);
    }

    #userApp .bar i {
      background: linear-gradient(90deg, var(--u-blue), var(--u-violet), var(--u-peach));
    }

    #userApp .kv,
    #userApp details {
      border-color: rgba(255,255,255,0.62);
    }

    #userApp .list li {
      color: var(--u-muted);
    }

    #userApp .list li::before {
      background: var(--u-violet);
    }

    #userApp summary {
      color: var(--u-violet-strong);
    }

    #userApp .card:hover {
      border-color: rgba(255,255,255,0.94);
      box-shadow: 0 28px 62px rgba(84, 74, 132, 0.18);
    }

    #userApp .risk-low {
      color: #4f46b8;
    }

    #userApp .risk-medium {
      color: #b7791f;
    }

    #userApp .risk-high {
      color: #c2415d;
    }

    #userApp .path-chip,
    #userApp .source-chip {
      border-color: rgba(109,93,246,0.18);
      background: rgba(236,232,255,0.78);
      color: var(--u-violet-strong);
    }

    #userApp .intent-map,
    #userApp .evidence-map,
    #userApp .heat-chart {
      border-color: rgba(255,255,255,0.76);
      border-radius: 24px;
      background:
        linear-gradient(90deg, rgba(109,93,246,0.06) 1px, transparent 1px),
        linear-gradient(0deg, rgba(109,93,246,0.05) 1px, transparent 1px),
        rgba(255,255,255,0.54);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.84);
    }

    #userApp .intent-node-query rect { fill: #17124a; }
    #userApp .intent-node-explicit rect { fill: #ece8ff; }
    #userApp .intent-node-inferred rect { fill: #fff7df; }
    #userApp .intent-node-profile_term rect { fill: #e7f0ff; }
    #userApp .intent-edge { stroke: rgba(109, 93, 246, 0.34); }

    #userApp .day-pill {
      border-color: rgba(255,255,255,0.76);
      border-radius: 999px;
      background: rgba(255,255,255,0.62);
      color: var(--u-muted);
      box-shadow: var(--u-shadow-soft);
    }

    #userApp .day-pill.active {
      border-color: rgba(255,255,255,0.86);
      background: linear-gradient(135deg, var(--u-blue), var(--u-violet) 60%, var(--u-peach));
      color: #ffffff;
      box-shadow: 0 14px 28px rgba(109, 93, 246, 0.22);
    }

    #userApp .timeline {
      position: relative;
      padding-left: 18px;
    }

    #userApp .timeline::before {
      content: "";
      position: absolute;
      left: 5px;
      top: 4px;
      bottom: 4px;
      width: 2px;
      border-radius: 999px;
      background: linear-gradient(180deg, var(--u-blue), var(--u-violet), var(--u-peach));
      box-shadow: 0 0 14px rgba(109,93,246,0.42);
    }

    #userApp .timeline-item {
      border: 1px solid rgba(255,255,255,0.74);
      border-radius: 24px;
      background: rgba(255,255,255,0.62);
      box-shadow: var(--u-shadow-soft);
    }

    #userApp .chat-window {
      border: 1px solid rgba(255,255,255,0.72);
      border-radius: 30px;
      background:
        radial-gradient(circle at 86% 12%, rgba(168,207,251,0.20), transparent 30%),
        linear-gradient(180deg, rgba(255,255,255,0.62), rgba(236,244,250,0.42));
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.84), var(--u-shadow-soft);
    }

    #userApp .message {
      border: 1px solid rgba(255,255,255,0.76);
      border-radius: 22px 22px 22px 6px;
      background: rgba(255,255,255,0.78);
      box-shadow: 0 8px 20px rgba(84, 74, 132, 0.08);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
    }

    #userApp .message.me {
      border-radius: 22px 22px 6px 22px;
      border-color: rgba(255,255,255,0.72);
      background: linear-gradient(135deg, var(--u-blue), var(--u-violet));
      color: #ffffff;
    }

    #userApp .message.ai {
      background: linear-gradient(135deg, #fff7df, #ece8ff);
      border-color: rgba(255,255,255,0.78);
    }

    #userApp .message.other {
      background: rgba(255,255,255,0.82);
      border-color: rgba(255,255,255,0.78);
    }

    #userApp .message.latest-feedback {
      outline: 2px solid rgba(109,93,246,0.20);
      box-shadow: 0 12px 24px rgba(109,93,246,0.14);
    }

    @media (max-width: 980px) {
      .app {
        grid-template-columns: 1fr;
      }

      .sidebar {
        position: relative;
        height: auto;
        max-height: 440px;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }

      .topbar,
      .profile-grid,
      .scene-layout,
      .two-col,
      .mode-hero,
      .neo-detail-grid,
      .user-app,
      .archive-grid,
      .radar-visual-grid,
      .tech-flow {
        grid-template-columns: 1fr;
      }

      .user-rail {
        position: relative;
        height: auto;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }

      .tabs {
        justify-content: flex-start;
      }

      .metrics {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 560px) {
      .main {
        padding: 14px;
      }

      .metrics,
      .info-grid,
      .cards,
      .mode-grid,
      .action-grid,
      .user-nav,
      .radar-search,
      .score-split,
      .message-input,
      .memory-strip {
        grid-template-columns: 1fr;
      }

      .card-head {
        grid-template-columns: 48px 1fr;
      }

      .score-pill {
        grid-column: 1 / -1;
        width: max-content;
      }

      .score-row {
        grid-template-columns: 82px 1fr 38px;
      }
    }

    @media (max-width: 760px) {
      :root {
        --bg: #fdfdfd;
        --panel: rgba(255, 255, 255, 0.72);
        --panel-soft: #f3f1f8;
        --ink: #17124a;
        --muted: #6d6a86;
        --line: rgba(255, 255, 255, 0.78);
        --accent: #6d5df6;
        --accent-strong: #4f46b8;
        --accent-soft: #ece8ff;
        --shadow: 0 16px 38px rgba(84, 74, 132, 0.14);
        --shadow-soft: 0 8px 22px rgba(84, 74, 132, 0.10);
        --surface: linear-gradient(145deg, rgba(255, 255, 255, 0.78), rgba(245, 243, 252, 0.58));
      }

      body {
        background:
          radial-gradient(circle at 18% 4%, rgba(168, 207, 251, 0.40), transparent 28%),
          radial-gradient(circle at 88% 16%, rgba(244, 199, 171, 0.36), transparent 24%),
          linear-gradient(135deg, #fdfdfd 0%, #f3f1f8 52%, #ebf4f5 100%);
        background-attachment: fixed;
        color: var(--ink);
      }

      .mode-shell {
        min-height: 100svh;
        padding: 24px 16px 28px;
        background:
          radial-gradient(circle at 12% 18%, rgba(168, 207, 251, 0.58), transparent 23%),
          radial-gradient(circle at 86% 12%, rgba(244, 199, 171, 0.50), transparent 20%),
          linear-gradient(135deg, #fdfdfd 0%, #f3f1f8 54%, #ebf4f5 100%);
      }

      .mode-shell::before {
        background:
          linear-gradient(130deg, transparent 0 46%, rgba(255, 255, 255, 0.55) 46.2% 46.8%, transparent 47%),
          linear-gradient(32deg, transparent 0 68%, rgba(126, 113, 238, 0.18) 68.2% 68.5%, transparent 68.8%);
      }

      .mode-inner {
        max-width: 430px;
      }

      .mode-hero {
        display: grid;
        grid-template-columns: 1fr;
        gap: 16px;
        margin-bottom: 16px;
      }

      .mode-hero h1 {
        color: #17124a;
        font-size: clamp(42px, 13vw, 64px);
        line-height: 0.92;
        letter-spacing: 0;
      }

      .mode-hero h1 span {
        display: block;
        color: transparent;
        background: linear-gradient(100deg, #7c8cf6, #bd8cff);
        -webkit-background-clip: text;
        background-clip: text;
      }

      .mode-hero p {
        color: #6d6a86;
        font-size: 14px;
        line-height: 1.7;
      }

      .mode-summary,
      .mode-card,
      .panel,
      .card,
      .metric,
      .cosmic-panel,
      .retrieval-card,
      .evidence-card,
      .counterpart-card,
      .completion-banner,
      .action-context {
        border-color: rgba(255, 255, 255, 0.78);
        border-radius: 26px;
        background: rgba(255, 255, 255, 0.58);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        box-shadow: var(--shadow-soft);
      }

      .mode-grid {
        grid-template-columns: 1fr;
        gap: 12px;
      }

      .mode-card {
        min-height: 178px;
        padding: 20px;
        overflow: hidden;
      }

      .mode-card::before {
        height: 100%;
        width: 6px;
        right: auto;
        background: linear-gradient(180deg, #8ea3ff, #f0b58e);
      }

      .mode-card h2 {
        font-size: 21px;
        color: #17124a;
      }

      .app,
      .user-app {
        display: block;
        width: min(100%, 430px);
        min-height: 100svh;
        margin: 0 auto;
        overflow: visible;
        background:
          radial-gradient(circle at 18% 3%, rgba(168, 207, 251, 0.46), transparent 24%),
          radial-gradient(circle at 94% 10%, rgba(244, 199, 171, 0.42), transparent 22%),
          linear-gradient(135deg, #fdfdfd 0%, #f3f1f8 50%, #ebf4f5 100%);
      }

      .sidebar,
      .user-rail {
        position: relative;
        height: auto;
        max-height: none;
        padding: 14px 14px 0;
        border: 0;
        box-shadow: none;
        color: var(--ink);
        background: transparent;
      }

      .user-rail .brand,
      .brand {
        border: 0;
        border-radius: 26px;
        background:
          linear-gradient(145deg, rgba(255,255,255,0.72), rgba(236,232,255,0.58));
        box-shadow: var(--shadow-soft);
      }

      .user-rail .brand p,
      .user-rail .muted,
      .user-rail .copy {
        color: var(--muted);
      }

      .search-wrap {
        border: 0;
        padding: 10px 0;
      }

      .search-wrap input,
      .search-wrap select,
      .radar-search input,
      .message-input input,
      .toolbar select {
        height: 46px;
        border: 0;
        border-radius: 999px;
        background: rgba(255,255,255,0.66);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.92), var(--shadow-soft);
      }

      .main,
      .user-main {
        padding: 14px 14px calc(92px + env(safe-area-inset-bottom));
      }

      .topbar,
      .user-star-head {
        display: block;
        border: 0;
        border-radius: 32px;
        padding: 20px;
        margin-bottom: 14px;
        background:
          linear-gradient(145deg, rgba(255,255,255,0.72), rgba(236,232,255,0.58));
        color: var(--ink);
        box-shadow: var(--shadow);
      }

      .user-star-head h2,
      .topbar h2 {
        color: #17124a;
        font-size: 24px;
      }

      .user-star-head p,
      .topbar p {
        color: var(--muted);
      }

      .tabs {
        overflow-x: auto;
        flex-wrap: nowrap;
        justify-content: flex-start;
        padding-bottom: 4px;
      }

      .tabs::-webkit-scrollbar,
      .tag-row::-webkit-scrollbar,
      .quick-replies::-webkit-scrollbar,
      .day-strip::-webkit-scrollbar {
        display: none;
      }

      .tab-button,
      .quick-reply,
      .user-tab-button,
      .planet-mode-button,
      .action-button {
        border: 0;
        border-radius: 999px;
        box-shadow: var(--shadow-soft);
      }

      .tab-button.active,
      .quick-reply.active,
      .planet-mode-row .planet-mode-button.active,
      .action-button.active {
        background: linear-gradient(135deg, #7c8cf6, #6d5df6);
        color: #ffffff;
      }

      .user-nav {
        position: fixed;
        left: 50%;
        bottom: 0;
        z-index: 50;
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 6px;
        width: min(100%, 430px);
        transform: translateX(-50%);
        padding: 9px 12px calc(9px + env(safe-area-inset-bottom));
        border-top: 1px solid rgba(255,255,255,0.82);
        background: rgba(255,255,255,0.66);
        backdrop-filter: blur(22px);
        -webkit-backdrop-filter: blur(22px);
        box-shadow: 0 -10px 28px rgba(84, 74, 132, 0.12);
      }

      .user-tab-button {
        min-height: 54px;
        padding: 6px 4px;
        color: #77718f;
        background: transparent;
        box-shadow: none;
        font-size: 11px;
        display: grid;
        gap: 2px;
        place-items: center;
      }

      .user-tab-button::before {
        content: attr(data-icon);
        width: 28px;
        height: 28px;
        border-radius: 999px;
        display: grid;
        place-items: center;
        background: rgba(236,232,255,0.75);
        color: #5b50d8;
        font-size: 14px;
      }

      .user-tab-button.active {
        background: transparent;
        color: #17124a;
      }

      .user-tab-button.active::before {
        background: linear-gradient(135deg, #7c8cf6, #f0b58e);
        color: #ffffff;
        box-shadow: 0 10px 18px rgba(124, 140, 246, 0.28);
      }

      .metrics {
        display: flex;
        gap: 10px;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
        margin-bottom: 12px;
      }

      .metric {
        flex: 0 0 132px;
        min-height: 82px;
        scroll-snap-align: start;
      }

      .metric::before {
        background: linear-gradient(90deg, #8ea3ff, #f0b58e);
      }

      .profile-grid,
      .two-col,
      .archive-grid,
      .scene-layout,
      .radar-visual-grid,
      .tech-flow,
      .neo-detail-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 12px;
      }

      .profile-media {
        grid-template-columns: 58px 1fr;
      }

      .profile-media img,
      .card-head img,
      .avatar {
        border-radius: 20px;
      }

      .day-strip {
        display: flex;
        gap: 8px;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
      }

      .day-pill {
        flex: 0 0 62px;
        border-radius: 999px;
        scroll-snap-align: start;
      }

      .planet-mode-row,
      .tag-row,
      .quick-replies {
        flex-wrap: nowrap;
        overflow-x: auto;
        padding-bottom: 4px;
      }

      .action-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 9px;
      }

      .action-button {
        min-height: 92px;
        border-radius: 24px;
        background: rgba(255,255,255,0.58);
      }

      .radar-search {
        position: sticky;
        top: 8px;
        z-index: 12;
        grid-template-columns: 1fr auto;
        padding: 6px;
        border-radius: 999px;
        background: rgba(255,255,255,0.62);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        box-shadow: var(--shadow-soft);
      }

      .radar-search .tab-button {
        min-width: 74px;
      }

      .intent-map {
        display: none;
      }

      .radar-visual-grid .info-grid {
        display: none;
      }

      .mobile-intent-tree {
        display: grid;
        gap: 8px;
        margin-top: 10px;
      }

      .intent-tree-row {
        border-radius: 18px;
        padding: 10px 12px;
        background: rgba(236,232,255,0.72);
      }

      .intent-tree-row.inferred {
        background: rgba(255,247,223,0.78);
      }

      .intent-tree-row strong {
        display: block;
        color: #17124a;
        font-size: 12px;
        margin-bottom: 3px;
      }

      .mobile-match-card {
        min-height: 420px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        border-radius: 34px;
        background:
          radial-gradient(circle at 82% 12%, rgba(168,207,251,0.42), transparent 30%),
          radial-gradient(circle at 10% 88%, rgba(244,199,171,0.32), transparent 32%),
          rgba(255,255,255,0.64);
      }

      .mobile-match-card .card-head {
        align-items: center;
      }

      .mobile-match-card .card-head img {
        width: 72px;
        height: 72px;
        border-radius: 28px;
      }

      .swipe-actions {
        display: grid;
        grid-template-columns: 70px 1fr;
        gap: 12px;
        margin-top: 16px;
        position: sticky;
        bottom: calc(88px + env(safe-area-inset-bottom));
        z-index: 25;
      }

      .swipe-actions .tab-button {
        min-height: 58px;
        border-radius: 999px;
        font-weight: 800;
      }

      .swipe-actions .reject-button {
        background: rgba(255,255,255,0.76);
        color: #817899;
      }

      .lightning-hero {
        border-radius: 32px;
        padding: 18px;
        background:
          radial-gradient(circle at 82% 14%, rgba(168,207,251,0.42), transparent 30%),
          linear-gradient(135deg, rgba(236,232,255,0.84), rgba(255,247,223,0.72));
      }

      .lightning-list {
        display: grid;
        gap: 10px;
      }

      .lightning-person {
        min-height: 0;
        padding: 12px;
      }

      .lightning-person .card-head {
        grid-template-columns: 52px 1fr auto;
      }

      .lightning-person .card-head img {
        width: 52px;
        height: 52px;
        border-radius: 20px;
      }

      .mobile-join-button {
        width: 100%;
        min-height: 48px;
        margin-top: 12px;
        border-radius: 18px;
        background: linear-gradient(135deg, #7c8cf6, #6d5df6);
        color: #ffffff;
        font-weight: 800;
      }

      .retrieval-card,
      .poster-wall .card {
        border-radius: 26px;
      }

      .poster-wall {
        grid-template-columns: 1fr;
      }

      .poster-wall .card {
        position: relative;
      }

      .poster-wall .score-pill {
        position: absolute;
        top: 14px;
        right: 14px;
      }

      .chat-window {
        max-height: min(58svh, 520px);
        border: 0;
        border-radius: 30px;
        background:
          linear-gradient(180deg, rgba(255,255,255,0.64), rgba(236,244,250,0.44));
        padding: 14px;
      }

      .message {
        border: 0;
        border-radius: 22px 22px 22px 6px;
        background: rgba(255,255,255,0.78);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
      }

      .message.me {
        border-radius: 22px 22px 6px 22px;
        background: linear-gradient(135deg, #7c8cf6, #6d5df6);
      }

      .message.ai {
        max-width: 92%;
        background: linear-gradient(135deg, #fff7df, #ece8ff);
      }

      .message.other {
        background: rgba(255,255,255,0.82);
      }

      #messagesPane .two-col {
        display: flex;
        flex-direction: column;
      }

      #messagesPane .two-col > .panel:nth-child(2) {
        order: -1;
        max-height: 42svh;
        overflow: auto;
      }

      #messagesPane .message-input {
        position: sticky;
        bottom: calc(74px + env(safe-area-inset-bottom));
        z-index: 35;
        grid-template-columns: 1fr auto;
        padding: 8px;
        border-radius: 999px;
        background: rgba(255,255,255,0.66);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        box-shadow: var(--shadow);
      }

      .memory-strip {
        grid-template-columns: 1fr;
      }

      .timeline {
        position: relative;
        padding-left: 18px;
      }

      .timeline::before {
        content: "";
        position: absolute;
        left: 5px;
        top: 4px;
        bottom: 4px;
        width: 2px;
        background: linear-gradient(180deg, #8ea3ff, #f0b58e);
        box-shadow: 0 0 12px rgba(124,140,246,0.45);
      }

      .timeline-item {
        border-radius: 22px;
      }
    }
  </style>
</head>
<body>
  <section id="modeChooser" class="mode-shell">
    <div class="galaxy-orb blue"></div>
    <div class="galaxy-orb gold"></div>
    <div class="galaxy-orb dark"></div>
    <div class="mode-inner">
      <div class="mode-hero">
        <div>
          <h1>SOUL<br><span>GALAXY</span></h1>
          <p>把校园匹配做成一座会呼吸的星系：学生视角像 App，管理员视角看技术链路、知识图谱、RAG 检索和匹配理由。</p>
        </div>
        <div id="modeSummary" class="mode-summary"></div>
      </div>
      <div class="mode-grid">
        <button class="mode-card" data-mode="admin">
          <h2>管理员后台</h2>
          <p>给展示和答辩用：看数据从哪里来、推荐为什么成立、哪些关系需要提醒。</p>
          <div class="tag-row">
            <span class="tag">全量数据</span>
            <span class="tag blue">产品模块</span>
            <span class="tag rose">风险治理</span>
          </div>
        </button>
        <button class="mode-card" data-mode="user">
          <h2>学生视角</h2>
          <p>选一个学生身份，像正常使用 App 一样看推荐、找搭子、发消息、留下互动记录。</p>
          <div class="tag-row">
            <span class="tag">每日选择</span>
            <span class="tag blue">输入驱动</span>
            <span class="tag rose">画像更新</span>
          </div>
        </button>
      </div>
    </div>
  </section>

  <div id="adminApp" class="app" hidden>
    <aside class="sidebar">
      <div class="brand">
        <h1>Campus Match AI</h1>
        <p id="brandSubtitle">合成校园匹配 Demo</p>
      </div>
      <div class="search-wrap">
        <input id="userSearch" type="search" placeholder="搜索用户、专业、校区">
      </div>
      <div id="userList" class="user-list"></div>
    </aside>
    <main class="main">
      <header class="topbar">
        <div>
          <h2>Campus Match AI 管理员星图台</h2>
          <p id="generatedInfo"></p>
        </div>
        <div>
          <div class="top-actions">
            <button id="adminHome" class="tab-button">返回入口</button>
            <button id="adminToUser" class="tab-button">进入用户版</button>
          </div>
          <nav id="tabs" class="tabs" aria-label="Demo sections"></nav>
        </div>
      </header>
      <section id="metrics" class="metrics"></section>
      <section id="profile" class="profile-grid"></section>
      <section id="content"></section>
    </main>
  </div>

  <div id="userApp" class="user-app" hidden>
    <aside class="user-rail">
      <div class="brand">
	        <h1>搭个蛋</h1>
	        <p>选一个学生身份，走一遍 7 天互动</p>
      </div>
      <div class="search-wrap">
        <select id="experienceUserSelect"></select>
      </div>
      <section id="experienceProfile" class="panel"></section>
      <div class="top-actions" style="justify-content:flex-start;margin-top:12px">
        <button id="userHome" class="tab-button">返回入口</button>
        <button id="userToAdmin" class="tab-button">进入管理员版</button>
        <button id="resetExperience" class="tab-button">重置体验</button>
      </div>
    </aside>
    <main class="user-main">
      <header class="user-star-head">
        <div>
	          <h2>搭个蛋 AI 星球舱</h2>
          <p id="experienceStatus"></p>
        </div>
        <nav id="userTabs" class="user-nav" aria-label="User demo sections"></nav>
      </header>
      <section id="planetPane" class="user-pane">
        <section id="experienceMetrics" class="metrics"></section>
        <section class="cosmic-panel">
          <div class="section-head">
            <h3>星球</h3>
		            <span id="dayGuardText" class="muted">每天记录一个主线，其它页面照常可用</span>
          </div>
	          <div id="planetModeTabs" class="planet-mode-row"></div>
	          <div id="dayStrip" class="day-strip"></div>
	          <section id="planetModeContent"></section>
	          <div class="action-context">
	            <strong>今天重点推进什么</strong>
	            <span>这里选的是写进今天时间线的主线，不代表其它功能不能用。你仍然可以去雷达找人、在消息里聊天，最后只选一个最重要的进展来推进当天。</span>
	          </div>
	          <div id="actionGrid" class="action-grid"></div>
          <div class="experience-input">
	            <input id="experienceText" type="text" placeholder="说一句今天想做的事：想去图书馆、想找人吃饭、今天有点累">
	            <button id="submitExperience" class="tab-button active">推进今天</button>
          </div>
          <div id="completionBanner"></div>
        </section>
        <section id="experienceOutcome" class="two-col" style="margin-top:12px"></section>
        <section class="panel" style="margin-top:12px">
          <div class="section-head">
	            <h3>这几天发生了什么</h3>
            <span id="timelineCount" class="muted"></span>
          </div>
          <div id="experienceTimeline" class="timeline"></div>
        </section>
      </section>
      <section id="radarPane" class="user-pane" hidden></section>
      <section id="messagesPane" class="user-pane" hidden>
        <section id="chatPanel" class="two-col"></section>
        <div class="message-input">
          <input id="messageText" type="text" placeholder="自己输入一句话，例如：我们周五去图书馆旁边喝咖啡吗？">
          <button id="sendMessageButton" class="tab-button active">发送</button>
        </div>
      </section>
      <section id="archivePane" class="user-pane" hidden></section>
    </main>
  </div>
  <script>
    window.CAMPUS_MATCH_DEMO_DATA = __CAMPUS_DATA__;
  </script>
  <script>
    const data = window.CAMPUS_MATCH_DEMO_DATA;
    const byId = Object.fromEntries((data.profiles || []).map((profile) => [profile.user_id, profile]));
    const governanceById = Object.fromEntries((data.governanceRecords || []).map((record) => [record.user_id, record]));
    const matchesByUser = groupBy(data.matches || [], "user_id");
    const sceneMatchesByRequest = groupBy(data.sceneMatches || [], "request_id");
    const profileEvidenceByUser = groupBy(data.profileTagEvidence || [], "user_id");
    const hybridSearchTraces = data.hybridSearchTraces || [];
    const intentGraphTraces = data.intentGraphTraces || [];
    const radarTraceAliases = {
      "#会弹吉他": "想找个会弹吉他的阳光学长",
      "#学习搭子": "想找安静一点的学习搭子",
      "#体育搭子": "周三下午找人一起打羽毛球",
      "#185+": "找185+会拍照的体育生",
      "#摄影大拿": "找185+会拍照的体育生",
      "#金融男": "金融男",
      "#情绪稳定": "今天没胃口，想找个细心的人陪我散步"
    };
    const tabs = [
      ["dashboard", "星图看板"],
      ["features", "产品模块"],
      ["daily", "每日状态"],
      ["matches", "心动星球"],
      ["scenes", "闪电搭子"],
      ["dynamics", "关系热度"],
      ["dates", "线下安全"],
      ["governance", "知识治理"],
      ["tech", "技术证据"],
      ["graph", "图谱留痕"]
    ];
    const featureCatalog = [
      {
        name: "画像与标签证据",
        admin: "查看用户画像、兴趣价值观、雷点、标签证据和脱敏访谈片段。",
        user: "注册后通过轻量访谈生成灵魂卡片；点开标签能看到为什么会有这个标签。",
        tech: "结构化画像抽取 + 标签证据检索。",
        course: "知识获取、属性抽取、RAG 证据链。"
      },
      {
        name: "心动推荐与解释",
        admin: "查看 Top-K 推荐、分数拆解、共同点、差异点和风险提示。",
        user: "在心动星球看到推荐对象，以及一段能看懂的匹配理由。",
        tech: "Sentence-BERT 向量、图谱相似度、价值观匹配、GNN link score 融合排序。",
        course: "向量检索、图计算、链接预测。"
      },
      {
        name: "雷达与闪电搭子",
        admin: "查看搜索意图、任务场景、时间地点约束和候选搭子排序。",
        user: "用大白话说“想吃饭/运动/自习”，系统自动转成可检索的搭子需求。",
        tech: "意图图谱、混合检索、场景匹配、地点安全上下文。",
        course: "语义检索、知识图谱、上下文增强。"
      },
      {
        name: "聊天辅助与关系复盘",
        admin: "查看聊天 RAG 命中来源、热度曲线、回复延迟、共同话题和关系状态。",
        user: "聊天时得到更自然的破冰建议；互动几天后能看到关系热度和周报。",
        tech: "实时 Top-K 检索、聊天知识库、聚合指标、画像更新。",
        course: "RAG、动态知识管理、知识生命周期。"
      },
      {
        name: "首约策划",
        admin: "查看候选地点、公开程度、人流、天气和替代地点建议。",
        user: "想线下见面时，系统优先推荐短时、公开、方便结束的校园地点。",
        tech: "地点知识建模、图查询、风险上下文解释。",
        course: "图数据库、知识建模、情境化推荐。"
      },
      {
        name: "信用治理与安全",
        admin: "查看失约、迟取消、不适反馈、可见度降权和复核策略。",
        user: "守约和反馈会影响信用分；高风险行为会降低曝光或进入人工复核。",
        tech: "治理事件建模、动态图权重、策略解释。",
        course: "知识治理、动态图权重、风险控制。"
      },
      {
        name: "技术看板",
        admin: "集中查看 Neo4j 图谱、FAISS 对比、GraphRAG 路径和 GNN 训练结果。",
        user: "用户不直接看到这些技术细节，只感受到推荐更可解释、搜索更准、提醒更稳。",
        tech: "Neo4j CSV/Cypher、Flat/IVF/HNSW、GraphSAGE、GCN。",
        course: "图数据库、ANN 检索、图神经网络。"
      }
    ];
    const experienceActions = [
      {id: "interview", label: "认识一下", desc: "说说今天状态，让推荐更贴近你", deltaHeat: 0.03, deltaCredit: 0, course: "第2/3/9章"},
      {id: "match", label: "看今日推荐", desc: "看看谁和你比较合拍", deltaHeat: 0.06, deltaCredit: 0, course: "第4/7/10章"},
      {id: "scene", label: "找个搭子", desc: "饭、学习、运动都可以先发起", deltaHeat: 0.04, deltaCredit: 1, course: "第2/7/10章"},
      {id: "chat", label: "破冰聊天", desc: "用一个轻松问题把话接起来", deltaHeat: 0.08, deltaCredit: 0, course: "第9/10章"},
      {id: "date", label: "首约策划", desc: "先选短时、公开、方便结束的校园地点", deltaHeat: 0.10, deltaCredit: 1, course: "第3/5/10章"},
      {id: "feedback", label: "见后反馈", desc: "记录这次见面的真实感受", deltaHeat: 0.05, deltaCredit: 2, course: "第2/4章"}
    ];
    const quickReplies = [
      "这个话题我也接得上，你更喜欢轻松聊还是认真聊？",
      "你刚刚说的那个点我挺有共鸣的，可以多讲一点吗？",
      "如果第一次见面，我们选图书馆旁边的咖啡店会不会更轻松？",
      "我最近也在准备这门课，可以一起刷一套题。",
      "今天有点累，但还是想听听你最近在忙什么。",
      "我想找个运动搭子，最好别太赶。",
      "这周有空的话，我们可以先短短见一面。",
      "我有点慢热，但对这个话题挺感兴趣。"
    ];
    const chatRagKnowledgeBase = [
      {doc_id: "icebreaker_common_interest", source: "icebreaker_library", title: "共同兴趣开场", text: "看到你们有共同兴趣时，先问一个具体、轻松、可回答的问题；不要反复复述兴趣标签。", suggestion: "这个共同点可以聊，但先问对方偏好和雷点。", tags: ["破冰", "共同兴趣", "低压力"]},
      {doc_id: "activity_specific_reply", source: "activity_playbook", title: "具体活动推荐", text: "用户询问最近活动或共同爱好推荐时，不硬编不存在的活动名称；先确认偏好、时长、强度和雷点。", suggestion: "我不太想随便编活动名。可以先定方向：轻松、推理、沉浸，或者只交换一下最近喜欢的内容。", tags: ["活动推荐", "防幻觉", "破冰"]},
      {doc_id: "date_low_pressure", source: "date_safety_playbook", title: "低压力首约", text: "第一次见面建议选校内、公开、人流稳定、可短时结束的地点。", suggestion: "如果你愿意，我们先约一小时，聊不累再继续。", tags: ["首约", "安全", "边界"]},
      {doc_id: "study_buddy_reply", source: "scene_playbook", title: "学习搭子回复", text: "学习或刷题场景适合明确时间长度、地点和安静程度。", suggestion: "可以先一起学一小时，结束后再决定要不要继续。", tags: ["学习搭子", "时间窗口"]},
      {doc_id: "care_needed_reply", source: "emotion_weather_station", title: "低能量照顾", text: "对方说累、焦虑、没胃口时，不要强推见面或重口味饭局。", suggestion: "那今天先不用强行社交，我们可以轻松聊几句。", tags: ["情绪气象站", "照顾信号"]},
      {doc_id: "boundary_respect", source: "relationship_boundary_policy", title: "边界感提醒", text: "慢热或重视边界的用户不适合连续追问隐私，也不要催回复。", suggestion: "我们慢慢聊就好，不用一下子把节奏拉太满。", tags: ["边界感", "风险控制"]},
      {doc_id: "sports_group_reply", source: "scene_playbook", title: "运动搭子成局", text: "运动搭子适合明确项目、强度、时间和人数，避免临时爽约。", suggestion: "可以，我也想动一动。我们先定一个轻量一点的强度，时间合适就成局。", tags: ["运动搭子", "自动成群", "信用"]},
      {doc_id: "meal_buddy_reply", source: "scene_playbook", title: "饭搭子回复", text: "饭搭子适合先说口味、地点和预算，如果对方状态低，不要强推重口味。", suggestion: "可以呀。我们先选近一点、人多一点的地方，口味别太冒险。", tags: ["饭搭子", "地点", "照顾信号"]},
      {doc_id: "photo_walk_reply", source: "radar_playbook", title: "拍照 Citywalk", text: "拍照、Citywalk、看展适合低压力线下活动，能边走边聊，不必一直面对面。", suggestion: "这个我愿意。边走边聊会轻松一点，也可以顺手拍几张照片。", tags: ["摄影", "Citywalk", "低压力"]},
      {doc_id: "exam_pressure_reply", source: "emotion_weather_station", title: "考试压力安抚", text: "考试、论文、ddl 相关消息要先承接压力，再给一个小而具体的陪伴方案。", suggestion: "辛苦了。我们可以先不聊太重的，或者一起定个 40 分钟的小目标。", tags: ["学业压力", "情绪气象站", "陪伴"]},
      {doc_id: "feedback_after_date", source: "memory_museum", title: "见后反馈", text: "见后反馈需要记录感受、守时、边界和是否愿意继续，不直接下判断。", suggestion: "这次见面的感觉可以慢慢说，不用立刻给结论。舒服和不舒服的点都值得记下来。", tags: ["见后反馈", "记忆博物馆", "知识更新"]}
    ];
    const userTabs = [
      ["planet", "星球"],
      ["radar", "雷达"],
      ["messages", "消息"],
      ["archive", "档案"]
    ];
    const planetModes = [
      ["love", "心动星球"],
      ["lightning", "闪电搭子"]
    ];
    const state = {
      mode: "chooser",
      tab: "dashboard",
      adminDay: 1,
      userTab: "planet",
      planetMode: "love",
      radarQuery: "",
      radarTag: "",
      selectedUserId: (data.profiles && data.profiles[0] && data.profiles[0].user_id) || "",
      selectedDashboardNodeId: (data.profiles && data.profiles[0] && data.profiles[0].user_id) || "",
      selectedNeo4jNodeId: (data.profiles && data.profiles[0] && data.profiles[0].user_id) || "",
      selectedSceneId: (data.sceneRequests && data.sceneRequests[0] && data.sceneRequests[0].request_id) || "",
      experienceUserId: (data.profiles && data.profiles[0] && data.profiles[0].user_id) || "",
      experienceDay: 1,
      experienceComplete: false,
      selectedAction: "interview",
      experienceHeat: 0.34,
      experienceCredit: 100,
      experienceTags: [],
      experienceHistory: [],
      conversationUserId: "",
      chatMessages: [],
      dayChatCount: 0,
      dayTouched: false,
      actionLocks: {},
      chatLimitNoticeDay: 0,
      lastChatRag: null,
      lastDailyIntent: null,
      recentReplySignatures: [],
      recentReplyTopics: []
    };

    document.getElementById("userSearch").addEventListener("input", renderUserList);
    document.querySelectorAll("[data-mode]").forEach((button) => {
      button.addEventListener("click", () => showMode(button.dataset.mode));
    });
    document.getElementById("adminHome").addEventListener("click", () => showMode("chooser"));
    document.getElementById("adminToUser").addEventListener("click", () => showMode("user"));
    document.getElementById("userHome").addEventListener("click", () => showMode("chooser"));
    document.getElementById("userToAdmin").addEventListener("click", () => showMode("admin"));
    document.getElementById("resetExperience").addEventListener("click", resetExperience);
    document.getElementById("submitExperience").addEventListener("click", submitExperienceAction);
    document.getElementById("sendMessageButton").addEventListener("click", () => {
      sendChatMessage(document.getElementById("messageText").value);
      document.getElementById("messageText").value = "";
    });
    document.getElementById("messageText").addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        sendChatMessage(document.getElementById("messageText").value);
        document.getElementById("messageText").value = "";
      }
    });
    document.getElementById("experienceUserSelect").addEventListener("change", (event) => {
      state.experienceUserId = event.target.value;
      state.selectedUserId = event.target.value;
      resetExperience();
    });

    function groupBy(rows, key) {
      return rows.reduce((acc, row) => {
        const value = row[key];
        if (!acc[value]) acc[value] = [];
        acc[value].push(row);
        return acc;
      }, {});
    }

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      })[char]);
    }

    function fmt(value) {
      if (value === undefined || value === null || value === "") return "无";
      if (typeof value === "number") return Number(value).toFixed(value >= 10 ? 0 : 3);
      return escapeHtml(value);
    }

    function friendlyScore(value) {
      if (value === undefined || value === null || value === "") return "待定";
      const raw = Math.max(0, Math.min(1, Number(value) || 0));
      return `${Math.round((0.68 + raw * 0.27) * 100)}%`;
    }

    function imagePath(userId) {
      const base = data.imageBase || "../images";
      return `${base}/${escapeHtml(userId)}.png`;
    }

    function tags(items, cls = "") {
      const list = Array.isArray(items) ? items : [];
      if (!list.length) return `<span class="muted">无</span>`;
      return `<div class="tag-row">${list.map((item) => `<span class="tag ${cls}">${escapeHtml(item)}</span>`).join("")}</div>`;
    }

    function scoreBar(label, value) {
      const numeric = Math.max(0, Math.min(1, Number(value) || 0));
      return `
        <div class="score-row">
          <span>${escapeHtml(label)}</span>
          <div class="bar"><i style="width:${(numeric * 100).toFixed(1)}%"></i></div>
          <strong>${numeric.toFixed(2)}</strong>
        </div>
      `;
    }

    function metric(label, value) {
      return `<div class="metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
    }

    function scoreMini(label, value) {
      const numeric = Math.max(0, Math.min(1, Number(value) || 0));
      return `<div class="score-mini"><span>${escapeHtml(label)}</span><strong>${numeric.toFixed(2)}</strong></div>`;
    }

    function pathStrip(parts) {
      const list = Array.isArray(parts) ? parts : [];
      return `<div class="path-strip">${list.map((part, index) => `
        ${index ? `<span class="path-arrow">-></span>` : ""}
        <span class="path-chip">${escapeHtml(part)}</span>
      `).join("")}</div>`;
    }

    function compactLabel(value, max = 10) {
      const text = String(value ?? "");
      return text.length > max ? `${text.slice(0, max - 1)}…` : text;
    }

    function bestTraceForQuery(queryText) {
      const raw = String(queryText || "").trim();
      if (!hybridSearchTraces.length) return null;
      const alias = radarTraceAliases[raw] || radarTraceAliases[`#${raw.replace(/^#/, "")}`] || raw;
      if (!alias) return hybridSearchTraces[0];
      const direct = hybridSearchTraces.find((trace) => trace.query === alias || trace.query.includes(alias) || alias.includes(trace.query));
      if (direct) return direct;
      const cleaned = alias.replace(/^#/, "");
      let best = hybridSearchTraces[0];
      let bestScore = -1;
      for (const trace of hybridSearchTraces) {
        const hay = `${trace.query} ${(trace.intent && (trace.intent.activated_tags || []).join(" ")) || ""}`;
        const score = Array.from(cleaned).reduce((acc, char) => acc + (hay.includes(char) ? 1 : 0), 0);
        if (score > bestScore) {
          bestScore = score;
          best = trace;
        }
      }
      return best;
    }

    function renderIntentGraph(trace) {
      const intent = (trace && trace.intent) || trace || {};
      const nodes = intent.graph_nodes || [];
      const edges = intent.graph_edges || [];
      if (!nodes.length) return `<div class="empty">还没有意图图谱 trace。</div>`;
      const lanes = {query: 52, explicit: 190, inferred: 346, profile_term: 510};
      const laneCounts = {};
      const positioned = nodes.slice(0, 13).map((node) => {
        const kind = node.kind || "profile_term";
        laneCounts[kind] = (laneCounts[kind] || 0) + 1;
        const y = 38 + (laneCounts[kind] - 1) * 42;
        return {...node, x: lanes[kind] || 510, y: Math.min(y, 194)};
      });
      const byNodeId = Object.fromEntries(positioned.map((node) => [node.id, node]));
      return `
        <svg class="intent-map" viewBox="0 0 640 230" role="img" aria-label="intent graph">
          <defs>
            <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
              <path d="M0,0 L0,6 L7,3 z" fill="rgba(30,88,96,0.44)"></path>
            </marker>
          </defs>
          ${edges.map((edge) => {
            const source = byNodeId[edge.source];
            const target = byNodeId[edge.target];
            if (!source || !target) return "";
            return `<line class="intent-edge" x1="${source.x + 94}" y1="${source.y}" x2="${target.x - 6}" y2="${target.y}" marker-end="url(#arrow)"></line>`;
          }).join("")}
          ${positioned.map((node) => `
            <g class="intent-node intent-node-${escapeHtml(node.kind || "profile_term")}">
              <rect x="${node.x - 42}" y="${node.y - 15}" width="112" height="30"></rect>
              <text x="${node.x - 36}" y="${node.y + 4}">${escapeHtml(compactLabel(node.label, node.kind === "query" ? 12 : 9))}</text>
            </g>
          `).join("")}
        </svg>
      `;
    }

    function renderHybridTrace(trace, currentUserId = "") {
      if (!trace) return `<div class="empty">还没有混合检索结果。</div>`;
      const rows = (trace.top_k || []).filter((row) => row.user_id !== currentUserId).slice(0, 4);
      return `
        <div class="retrieval-stack">
          ${rows.map((row) => `
            <article class="retrieval-card">
              <span class="score-pill">${fmt(row.final_score)}</span>
              <strong>${escapeHtml(row.display_name || row.user_id)}</strong>
              <div class="muted">${escapeHtml(row.major || "")} / ${escapeHtml(row.campus || "")}</div>
              <p class="copy">命中：${escapeHtml((row.matched_tags || []).slice(0, 4).join("、") || row.reason || "语义相似")}</p>
              <div class="score-split">
                ${scoreMini("向量", row.vector_score)}
                ${scoreMini("关键词", row.sparse_score)}
                ${scoreMini("图谱", row.graph_score)}
                ${scoreMini("约束", row.constraint_score)}
              </div>
              ${pathStrip((row.graph_path || []).slice(0, 4))}
            </article>
          `).join("") || `<div class="empty">没有检索命中。</div>`}
        </div>
      `;
    }

    function renderIntentSummary(trace) {
      if (!trace) return `<div class="empty">输入一句需求后，这里展示意图拆解。</div>`;
      const intent = trace.intent || trace;
      const explicit = intent.explicit_intents || [];
      const inferred = intent.inferred_intents || [];
      const hard = intent.hard_constraints || [];
      const retrievers = trace.retrievers || [];
      return `
        <div class="info-grid">
          <div class="info-item"><span>显性意图</span><strong>${escapeHtml(explicit.join("、") || "无")}</strong></div>
          <div class="info-item"><span>隐性意图</span><strong>${escapeHtml(inferred.join("、") || "无")}</strong></div>
          <div class="info-item"><span>硬条件</span><strong>${escapeHtml(hard.join("、") || "无")}</strong></div>
          <div class="info-item"><span>检索链路</span><strong>${escapeHtml(retrievers.join(" + ") || "Text-to-Graph")}</strong></div>
        </div>
        <div class="mobile-intent-tree">
          <div class="intent-tree-row"><strong>你直接说出的需求</strong>${escapeHtml(explicit.join("、") || "还没有显性条件")}</div>
          <div class="intent-tree-row inferred"><strong>AI 推断出的偏好</strong>${escapeHtml(inferred.join("、") || "等待更多输入")}</div>
          <div class="intent-tree-row"><strong>硬条件过滤</strong>${escapeHtml(hard.join("、") || "不额外限制")}</div>
          <div class="intent-tree-row inferred"><strong>检索方法</strong>${escapeHtml(retrievers.join(" + ") || "Text-to-Graph + 向量检索")}</div>
        </div>
        ${(intent.warnings || []).length ? `<p class="copy"><strong>注意：</strong>${escapeHtml(intent.warnings.join("；"))}</p>` : ""}
      `;
    }

    function evidenceForTag(profile, tag) {
      const rows = profileEvidenceByUser[profile.user_id] || [];
      return rows.find((row) => row.tag === tag) || rows.find((row) => String(row.tag || "").includes(tag) || String(tag || "").includes(row.tag)) || rows[0] || null;
    }

    function renderEvidenceMap(row) {
      if (!row) return "";
      const labels = [row.user_id, row.source_type, row.tag, row.tag_type];
      return `
        <svg class="evidence-map" viewBox="0 0 520 116" role="img" aria-label="profile evidence path">
          <defs>
            <marker id="evidenceArrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
              <path d="M0,0 L0,6 L7,3 z" fill="rgba(30,88,96,0.44)"></path>
            </marker>
          </defs>
          <line x1="82" y1="58" x2="202" y2="58" class="intent-edge" marker-end="url(#evidenceArrow)"></line>
          <line x1="282" y1="58" x2="402" y2="58" class="intent-edge" marker-end="url(#evidenceArrow)"></line>
          ${labels.map((label, idx) => {
            const x = 22 + idx * 128;
            const cls = idx === 0 ? "query" : idx === 1 ? "explicit" : idx === 2 ? "inferred" : "profile_term";
            return `
              <g class="intent-node intent-node-${cls}">
                <rect x="${x}" y="39" width="94" height="36"></rect>
                <text x="${x + 8}" y="62">${escapeHtml(compactLabel(label, 9))}</text>
              </g>
            `;
          }).join("")}
        </svg>
      `;
    }

    function renderProfileEvidenceCard(row) {
      if (!row) return `<div class="completion-banner">当前标签还没有证据。</div>`;
      return `
        <div class="evidence-card">
          <div class="section-head">
            <h4>${escapeHtml(row.tag)} 证据</h4>
            <span class="score-pill">${fmt(row.confidence)}</span>
          </div>
          <div class="kv">
            <span>来源</span><strong>${escapeHtml(row.source_type)}</strong>
            <span>问题</span><strong>${escapeHtml(row.question)}</strong>
            <span>检索分</span><strong>${escapeHtml(row.retrieval_score)}</strong>
            <span>类型</span><strong>${escapeHtml(row.tag_type)}</strong>
          </div>
          <blockquote>${escapeHtml(row.sanitized_quote || row.quote)}</blockquote>
          <p class="copy">${escapeHtml(row.why_it_matters || "")}</p>
          ${pathStrip(row.rag_path || [])}
          ${renderEvidenceMap(row)}
        </div>
      `;
    }

    function currentProfile() {
      return byId[state.selectedUserId] || (data.profiles && data.profiles[0]) || {};
    }

    function showMode(mode) {
      state.mode = mode;
      document.getElementById("modeChooser").hidden = mode !== "chooser";
      document.getElementById("adminApp").hidden = mode !== "admin";
      document.getElementById("userApp").hidden = mode !== "user";
      if (mode === "chooser") {
        renderModeSummary();
      }
      if (mode === "admin") {
        state.selectedUserId = state.selectedUserId || state.experienceUserId;
        render();
      }
      if (mode === "user") {
        state.experienceUserId = state.experienceUserId || state.selectedUserId;
        renderUserExperience();
      }
    }

    function renderModeSummary() {
      const summary = data.summary || {};
      const neo4j = data.neo4jSummary || summary.neo4j_trace || {};
      document.getElementById("modeSummary").innerHTML = `
        <strong>当前 demo 数据</strong>
        <div class="kv">
          <span>用户</span><strong>${escapeHtml(summary.n_users || (data.profiles || []).length)}</strong>
          <span>画像三元组</span><strong>${escapeHtml(summary.n_triples || 0)}</strong>
          <span>匹配</span><strong>${escapeHtml(summary.n_matches || (data.matches || []).length)}</strong>
          <span>Neo4j 产品图</span><strong>${escapeHtml(neo4j.n_nodes || 0)} 节点 / ${escapeHtml(neo4j.n_relationships || 0)} 关系</strong>
        </div>
      `;
    }

    function render() {
      renderTabs();
      renderUserList();
      const isDashboard = state.tab === "dashboard";
      document.getElementById("metrics").hidden = isDashboard;
      document.getElementById("profile").hidden = isDashboard;
      if (!isDashboard) {
        renderMetrics();
        renderProfile();
      }
      const renderers = {
        dashboard: renderDashboard,
        features: renderFeatures,
        daily: renderDailyAdmin,
        matches: renderMatches,
        scenes: renderScenes,
        dynamics: renderDynamics,
        dates: renderDates,
        governance: renderGovernance,
        tech: renderTechEvidence,
        graph: renderGraph
      };
      renderers[state.tab]();
      const info = `生成时间 ${escapeHtml(data.generatedAt || "")} | 当前用户 ${escapeHtml(state.selectedUserId || "无")}`;
      document.getElementById("generatedInfo").innerHTML = info;
      document.getElementById("brandSubtitle").textContent = `${(data.profiles || []).length}人合成校园匹配 Demo`;
    }

    function renderTabs() {
      document.getElementById("tabs").innerHTML = tabs.map(([id, label]) => `
        <button class="tab-button ${state.tab === id ? "active" : ""}" data-tab="${id}">${label}</button>
      `).join("");
      document.querySelectorAll("[data-tab]").forEach((button) => {
        button.addEventListener("click", () => {
          state.tab = button.dataset.tab;
          render();
        });
      });
    }

    function renderMetrics() {
      const summary = data.summary || {};
      const neo4j = data.neo4jSummary || summary.neo4j_trace || {};
      const rows = [
        metric("合成用户", summary.n_users || (data.profiles || []).length),
        metric("画像三元组", summary.n_triples || 0),
        metric("匹配结果", summary.n_matches || (data.matches || []).length),
        metric("闪电任务", summary.n_scene_requests || (data.sceneRequests || []).length),
        metric("Neo4j 产品图", `${neo4j.n_nodes || 0}/${neo4j.n_relationships || 0}`)
      ];
      document.getElementById("metrics").innerHTML = rows.join("");
    }

    function renderUserList() {
      const query = document.getElementById("userSearch").value.trim().toLowerCase();
      const profiles = (data.profiles || []).filter((profile) => {
        const haystack = [
          profile.user_id,
          profile.display_name,
          profile.major,
          profile.campus,
          profile.relationship_goal,
          ...(profile.interests || [])
        ].join(" ").toLowerCase();
        return !query || haystack.includes(query);
      });
      document.getElementById("userList").innerHTML = profiles.map((profile) => `
        <button class="user-button ${profile.user_id === state.selectedUserId ? "active" : ""}" data-user="${escapeHtml(profile.user_id)}">
          <img class="avatar" src="${imagePath(profile.user_id)}" alt="${escapeHtml(profile.display_name)}" onerror="this.style.visibility='hidden'">
          <span>
            <strong>${escapeHtml(profile.display_name)} · ${escapeHtml(profile.user_id)}</strong>
            <span class="truncate">${escapeHtml(profile.major)} / ${escapeHtml(profile.campus)}</span>
          </span>
        </button>
      `).join("") || `<div class="empty">没有匹配的用户</div>`;
      document.querySelectorAll("[data-user]").forEach((button) => {
        button.addEventListener("click", () => {
          state.selectedUserId = button.dataset.user;
          state.selectedDashboardNodeId = state.selectedUserId;
          state.selectedNeo4jNodeId = state.selectedUserId;
          render();
        });
      });
    }

    function renderProfile() {
      const profile = currentProfile();
      const governance = governanceById[profile.user_id] || {};
      document.getElementById("profile").innerHTML = `
        <div class="panel">
          <div class="profile-media">
            <img src="${imagePath(profile.user_id)}" alt="${escapeHtml(profile.display_name)}" onerror="this.style.visibility='hidden'">
            <div>
              <h3>${escapeHtml(profile.display_name || "未选择用户")}</h3>
              <p>${escapeHtml(profile.school || "")} / ${escapeHtml(profile.major || "")} / ${escapeHtml(profile.grade || "")}</p>
              <p>${escapeHtml(profile.campus || "")}</p>
            </div>
          </div>
          <div class="info-grid">
            <div class="info-item"><span>关系目标</span><strong>${fmt(profile.relationship_goal)}</strong></div>
            <div class="info-item"><span>沟通风格</span><strong>${fmt(profile.communication_style)}</strong></div>
            <div class="info-item"><span>信用分</span><strong>${fmt(governance.credit_score ?? 100)}</strong></div>
            <div class="info-item"><span>推荐可见度</span><strong>${fmt(governance.policy && governance.policy.visibility_multiplier ? governance.policy.visibility_multiplier : 1)}</strong></div>
          </div>
        </div>
        <div class="panel">
          <div class="section-head"><h3>灵魂卡片</h3><span class="muted">${escapeHtml(profile.gender || "")} -> ${escapeHtml(profile.preferred_gender || "")}</span></div>
          <p class="copy">${escapeHtml(profile.self_intro || "")}</p>
          <p class="copy"><strong>理想型：</strong>${escapeHtml(profile.ideal_partner || "")}</p>
          ${tags(profile.interests)}
          ${tags(profile.values, "blue")}
          ${tags(profile.deal_breakers, "rose")}
        </div>
      `;
    }

    function renderDashboard() {
      const summary = data.summary || {};
      const neo4j = data.neo4jSummary || summary.neo4j_trace || {};
      const heatRows = buildDailyAdminRows(state.adminDay || 1);
      const avgHeat = heatRows.length ? heatRows.reduce((sum, row) => sum + row.heat, 0) / heatRows.length : 0;
      const riskyUsers = (data.governanceRecords || []).filter((record) => {
        const policy = record.policy || {};
        return record.credit_score < 85 || policy.conditional_mute || policy.visibility_multiplier < 1;
      });
      document.getElementById("content").innerHTML = `
        <div class="section-head">
          <h3>星图看板</h3>
          <span class="muted">把用户、兴趣、价值观、地点、任务和关系状态放到一张可讲的图里</span>
        </div>
        <div class="dashboard-grid">
          <section class="graph-stage">
            <div class="section-head">
              <div>
                <h3>CampusMatchAI 知识星图</h3>
                <p class="muted">这张图不只放画像，还写入推荐、搭子、聊天热度、首约安全和信用治理。</p>
              </div>
              <span class="score-pill">${escapeHtml(neo4j.n_nodes || 0)} nodes</span>
            </div>
            ${renderKnowledgeGraphSvg()}
            <div class="graph-legend">
              <span class="legend-dot"><i style="background:#0f766e"></i>用户</span>
              <span class="legend-dot"><i style="background:#2563eb"></i>兴趣</span>
              <span class="legend-dot"><i style="background:#b45309"></i>价值观</span>
              <span class="legend-dot"><i style="background:#b42318"></i>校区/目标</span>
            </div>
            ${renderDashboardNodeDetail()}
          </section>
          <aside class="dashboard-side">
            <section class="orbit-card">
              <h4>项目运行态</h4>
              <div class="soft-kpi-grid">
                <div class="soft-kpi"><span>用户画像</span><strong>${escapeHtml(summary.n_users || (data.profiles || []).length)}</strong></div>
                <div class="soft-kpi"><span>画像三元组</span><strong>${escapeHtml(summary.n_triples || 0)}</strong></div>
                <div class="soft-kpi"><span>匹配候选</span><strong>${escapeHtml(summary.n_matches || (data.matches || []).length)}</strong></div>
                <div class="soft-kpi"><span>关系热度</span><strong>${Math.round(avgHeat * 100)}%</strong></div>
              </div>
            </section>
            <section class="orbit-card">
              <h4>关系热度轨道</h4>
              <div class="mini-bars">
                ${heatRows.slice(0, 5).map((row) => `
                  <div class="mini-bar-row">
                    <span>${escapeHtml(row.pairId)}</span>
                    <div class="bar"><i style="width:${Math.round(row.heat * 100)}%"></i></div>
                    <strong>${Math.round(row.heat * 100)}%</strong>
                  </div>
                `).join("") || `<p class="muted">暂无关系热度</p>`}
              </div>
            </section>
            <section class="orbit-card">
              <h4>闪电搭子场景</h4>
              <div class="mini-bars">
                ${(data.sceneRequests || []).slice(0, 5).map((request) => `
                  <div class="path-row">
                    <strong>${escapeHtml(request.intent && request.intent.task_type || "task")}</strong>
                    <span class="muted">${escapeHtml(request.location && request.location.name || "")} / ${escapeHtml(request.safety_context && request.safety_context.risk_level || "low")}</span>
                  </div>
                `).join("") || `<p class="muted">暂无场景任务</p>`}
              </div>
            </section>
            <section class="orbit-card">
              <h4>治理与信用</h4>
              <p class="copy">触发推荐降权或复核的用户：${riskyUsers.length} / ${(data.governanceRecords || []).length}</p>
              ${tags(riskyUsers.slice(0, 4).map((record) => `${record.user_id} ${record.credit_score}`), "rose")}
            </section>
          </aside>
        </div>
        <div class="flow-strip">
          <div class="flow-step"><strong>注册</strong>AI 性格选择与模拟访谈</div>
          <div class="flow-step"><strong>画像</strong>标签抽取与灵魂卡片</div>
          <div class="flow-step"><strong>星球</strong>心动推荐或闪电搭子</div>
          <div class="flow-step"><strong>消息</strong>破冰、热度、首约</div>
          <div class="flow-step"><strong>档案</strong>周报、信用、记忆博物馆</div>
        </div>
      `;
      attachDashboardGraphEvents();
    }

    function renderKnowledgeGraphSvg() {
      const width = 980;
      const height = 520;
      const cx = width / 2;
      const cy = height / 2;
      const profiles = data.profiles || [];
      const concepts = buildGraphConcepts(profiles);
      const userNodes = profiles.map((profile, index) => {
        const angle = -Math.PI / 2 + (Math.PI * 2 * index) / Math.max(profiles.length, 1);
        return {
          id: profile.user_id,
          label: profile.display_name || profile.user_id,
          type: "user",
          x: cx + Math.cos(angle) * 170,
          y: cy + Math.sin(angle) * 120,
          profile
        };
      });
      const conceptNodes = concepts.map((concept, index) => {
        const angle = -Math.PI / 2 + (Math.PI * 2 * index) / Math.max(concepts.length, 1);
        return {
          ...concept,
          x: cx + Math.cos(angle) * 390,
          y: cy + Math.sin(angle) * 220
        };
      });
      const nodeByLabel = Object.fromEntries([...userNodes, ...conceptNodes].map((node) => [node.id, node]));
      const conceptIds = new Set(conceptNodes.map((node) => node.id));
      const edges = [];
      for (const profile of profiles) {
        const targets = [
          ...(profile.interests || []).slice(0, 2).map((item) => `interest:${item}`),
          ...(profile.values || []).slice(0, 2).map((item) => `value:${item}`),
          `context:${profile.campus}`,
          `context:${profile.relationship_goal}`
        ];
        for (const target of targets) {
          if (conceptIds.has(target)) edges.push([profile.user_id, target]);
        }
      }
      const matchEdges = (data.matches || []).slice(0, 10).map((match) => [match.user_id, match.candidate_id]);
      const allNodes = [...conceptNodes, ...userNodes];
      const nodeIds = new Set(allNodes.map((node) => node.id));
      if (!nodeIds.has(state.selectedDashboardNodeId)) {
        state.selectedDashboardNodeId = state.selectedUserId || (profiles[0] && profiles[0].user_id) || "";
      }
      return `
        <svg class="knowledge-map" viewBox="0 0 ${width} ${height}" role="img" aria-label="Campus Match AI knowledge graph">
          <defs>
            <filter id="nodeShadow" x="-30%" y="-30%" width="160%" height="160%">
              <feDropShadow dx="0" dy="5" stdDeviation="5" flood-color="#101828" flood-opacity="0.16"></feDropShadow>
            </filter>
          </defs>
          <g>
            ${edges.map(([source, target]) => {
              const a = nodeByLabel[source];
              const b = nodeByLabel[target];
              if (!a || !b) return "";
              return `<line class="graph-link" x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${b.x.toFixed(1)}" y2="${b.y.toFixed(1)}"></line>`;
            }).join("")}
            ${matchEdges.map(([source, target]) => {
              const a = nodeByLabel[source];
              const b = nodeByLabel[target];
              if (!a || !b) return "";
              return `<line x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${b.x.toFixed(1)}" y2="${b.y.toFixed(1)}" stroke="#0f766e" stroke-width="2.2" stroke-opacity="0.38" stroke-dasharray="5 6"></line>`;
            }).join("")}
          </g>
          <g>
            ${allNodes.map((node) => {
              const radius = node.type === "user" ? 19 : 13;
              const label = node.label.length > 7 ? `${node.label.slice(0, 7)}…` : node.label;
              const selectedClass = node.id === state.selectedDashboardNodeId ? " graph-node-selected" : "";
              return `
                <g class="graph-clickable" data-dashboard-node-id="${escapeHtml(node.id)}" tabindex="0" role="button" aria-label="查看 ${escapeHtml(node.label)} 节点">
                  <circle class="graph-node-${node.type === "user" ? "user" : node.kind}${selectedClass}" cx="${node.x.toFixed(1)}" cy="${node.y.toFixed(1)}" r="${radius}" filter="url(#nodeShadow)"></circle>
                  <text class="graph-label" x="${node.x.toFixed(1)}" y="${(node.y + radius + 15).toFixed(1)}" text-anchor="middle">${escapeHtml(label)}</text>
                  <title>${escapeHtml(node.label)}</title>
                </g>
              `;
            }).join("")}
          </g>
        </svg>
      `;
    }

    function buildGraphConcepts(profiles) {
      const counts = {interest: {}, value: {}, context: {}};
      for (const profile of profiles) {
        for (const item of profile.interests || []) counts.interest[item] = (counts.interest[item] || 0) + 1;
        for (const item of profile.values || []) counts.value[item] = (counts.value[item] || 0) + 1;
        for (const item of [profile.campus, profile.relationship_goal]) {
          if (item) counts.context[item] = (counts.context[item] || 0) + 1;
        }
      }
      const rows = [];
      for (const kind of ["interest", "value", "context"]) {
        const limit = kind === "interest" ? 7 : kind === "value" ? 6 : 5;
        Object.entries(counts[kind])
          .sort((a, b) => Number(b[1]) - Number(a[1]))
          .slice(0, limit)
          .forEach(([label, count]) => rows.push({id: `${kind}:${label}`, label, kind, count, type: "concept"}));
      }
      return rows;
    }

    function renderDashboardNodeDetail() {
      const profiles = data.profiles || [];
      const concepts = buildGraphConcepts(profiles);
      const conceptById = Object.fromEntries(concepts.map((node) => [node.id, node]));
      const nodeIds = new Set([...profiles.map((profile) => profile.user_id), ...concepts.map((node) => node.id)]);
      let selectedId = state.selectedDashboardNodeId || state.selectedUserId || (profiles[0] && profiles[0].user_id) || "";
      if (!nodeIds.has(selectedId)) selectedId = state.selectedUserId || (profiles[0] && profiles[0].user_id) || "";
      state.selectedDashboardNodeId = selectedId;
      const profile = byId[selectedId];
      const concept = conceptById[selectedId];
      if (!profile && !concept) return `<div class="dashboard-node-detail empty">点击图上的节点查看详情</div>`;

      const fields = [];
      const relations = [];
      if (profile) {
        const governance = governanceById[profile.user_id] || {};
        fields.push(
          ["节点 ID", profile.user_id],
          ["类型", "用户"],
          ["姓名", profile.display_name || profile.user_id],
          ["专业/学院", `${profile.major || ""} / ${profile.school || ""}`],
          ["校区", profile.campus || ""],
          ["关系目标", profile.relationship_goal || ""],
          ["沟通风格", profile.communication_style || ""],
          ["信用分", governance.credit_score ?? 100]
        );
        const conceptLinks = [
          ...(profile.interests || []).slice(0, 4).map((item) => ["LIKES", `interest:${item}`, item]),
          ...(profile.values || []).slice(0, 4).map((item) => ["VALUES", `value:${item}`, item]),
          ["LOCATED_AT", `context:${profile.campus}`, profile.campus],
          ["HAS_GOAL", `context:${profile.relationship_goal}`, profile.relationship_goal]
        ].filter((row) => row[2] && conceptById[row[1]]);
        conceptLinks.forEach(([relation, targetId, label]) => {
          relations.push({relation, targetId, label, note: "画像连接"});
        });
        (data.matches || [])
          .filter((match) => match.user_id === profile.user_id || match.candidate_id === profile.user_id)
          .slice(0, 5)
          .forEach((match) => {
            const outbound = match.user_id === profile.user_id;
            const otherId = outbound ? match.candidate_id : match.user_id;
            const other = byId[otherId] || {};
            relations.push({
              relation: outbound ? "RECOMMENDS" : "RECOMMENDED_BY",
              targetId: otherId,
              label: other.display_name || otherId,
              note: `匹配分 ${fmt(match.final_score)}`
            });
          });
      } else {
        const [kind, ...labelParts] = selectedId.split(":");
        const label = labelParts.join(":");
        const kindText = kind === "interest" ? "兴趣" : kind === "value" ? "价值观" : "校区/目标";
        fields.push(
          ["节点 ID", selectedId],
          ["类型", kindText],
          ["名称", concept.label],
          ["连接用户数", concept.count || 0]
        );
        profiles.filter((item) => {
          if (kind === "interest") return (item.interests || []).includes(label);
          if (kind === "value") return (item.values || []).includes(label);
          return item.campus === label || item.relationship_goal === label;
        }).slice(0, 8).forEach((item) => {
          relations.push({
            relation: kind === "interest" ? "LIKED_BY" : kind === "value" ? "VALUED_BY" : "USED_BY",
            targetId: item.user_id,
            label: item.display_name || item.user_id,
            note: `${item.major || ""} / ${item.campus || ""}`
          });
        });
      }

      return `
        <div class="dashboard-node-detail">
          <div class="section-head">
            <h3>节点详情：${escapeHtml(selectedId)}</h3>
            <span class="muted">${escapeHtml(profile ? "用户节点" : `${concept.kind} 概念节点`)}</span>
          </div>
          <div class="neo-detail-grid">
            <div>
              <h3>字段</h3>
              <div class="neo-props">
                ${fields.filter(([, value]) => hasValue(value)).map(([label, value]) => `
                  <div class="neo-prop">
                    <span>${escapeHtml(label)}</span>
                    <strong>${escapeHtml(shortText(value, 130))}</strong>
                  </div>
                `).join("")}
              </div>
            </div>
            <div>
              <h3>相连节点</h3>
              <div class="neo-rels">
                ${relations.length ? relations.map((row) => `
                  <div class="neo-rel-row">
                    <span>${escapeHtml(row.relation)}</span>
                    <strong><button type="button" class="neo-node-link" data-dashboard-node-id="${escapeHtml(row.targetId)}">${escapeHtml(row.targetId)} / ${escapeHtml(shortText(row.label, 34))}</button></strong>
                    ${row.note ? `<p>${escapeHtml(row.note)}</p>` : ""}
                  </div>
                `).join("") : `<div class="empty">当前概览图里没有更多连接</div>`}
              </div>
            </div>
          </div>
        </div>
      `;
    }

    function attachDashboardGraphEvents() {
      document.querySelectorAll("[data-dashboard-node-id]").forEach((item) => {
        item.addEventListener("click", () => {
          state.selectedDashboardNodeId = item.dataset.dashboardNodeId;
          if (byId[state.selectedDashboardNodeId]) state.selectedUserId = state.selectedDashboardNodeId;
          render();
        });
        item.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            state.selectedDashboardNodeId = item.dataset.dashboardNodeId;
            if (byId[state.selectedDashboardNodeId]) state.selectedUserId = state.selectedDashboardNodeId;
            render();
          }
        });
      });
    }

    function neoNodeGroup(node) {
      const label = node && node.label ? node.label : "";
      if (label === "User") return "user";
      if (["MatchRecommendation", "GraphRAGEvidence", "IceBreakerPrompt", "RiskReason"].includes(label)) return "match";
      if (["SceneRequest", "SceneCandidateRank", "SceneIntent"].includes(label)) return "scene";
      if (["RelationshipPair", "ChatDay", "ConversationTopic", "ProfileUpdate"].includes(label)) return "dynamic";
      if (["DatePlan", "CampusLocation", "WeatherContext", "RiskAssessment", "SafetyContext"].includes(label)) return "safety";
      if (["GovernanceRecord", "GovernanceEvent", "GovernanceAction", "PolicyReason"].includes(label)) return "governance";
      return "default";
    }

    function neoNodeLabel(node) {
      if (!node) return "";
      return node.display_name || node.name || node.text || node.description || node.node_id || "";
    }

    function shortText(value, max = 12) {
      const text = String(value ?? "");
      return text.length > max ? `${text.slice(0, max)}...` : text;
    }

    function hasValue(value) {
      return value !== undefined && value !== null && String(value).trim() !== "";
    }

    function neoNodeById() {
      return Object.fromEntries((data.neo4jNodes || []).filter((node) => node.node_id).map((node) => [node.node_id, node]));
    }

    function collectNeo4jFocusGraph() {
      const nodes = data.neo4jNodes || [];
      const relationships = data.neo4jRelationships || [];
      const nodeById = Object.fromEntries(nodes.filter((node) => node.node_id).map((node) => [node.node_id, node]));
      let focusId = state.selectedUserId || ((data.profiles || [])[0] && (data.profiles || [])[0].user_id) || "U001";
      if (!nodeById[focusId]) focusId = nodeById.U001 ? "U001" : ((nodes[0] && nodes[0].node_id) || "");
      const focusIds = new Set(focusId ? [focusId] : []);
      const seenRelIds = new Set();
      const focusRelationships = [];

      function addRelationship(row) {
        if (!row || !row.source_id || !row.target_id) return;
        if (!nodeById[row.source_id] || !nodeById[row.target_id]) return;
        const relId = row.rel_id || `${row.source_id}:${row.relation}:${row.target_id}:${focusRelationships.length}`;
        if (seenRelIds.has(relId)) return;
        seenRelIds.add(relId);
        focusRelationships.push(row);
        focusIds.add(row.source_id);
        focusIds.add(row.target_id);
      }

      const primaryTypes = new Set([
        "HAS_MATCH_RECOMMENDATION",
        "POSTED_SCENE_REQUEST",
        "HAS_RELATIONSHIP_PAIR",
        "PROPOSED_DATE_PLAN",
        "HAS_GOVERNANCE_RECORD"
      ]);
      relationships
        .filter((row) => (row.source_id === focusId || row.target_id === focusId) && primaryTypes.has(row.relation))
        .slice(0, 24)
        .forEach(addRelationship);

      const productTypes = new Set([
        "RECOMMENDS_USER",
        "RECOMMENDED_TO",
        "MATCH_COMMON_INTEREST",
        "MATCH_COMMON_VALUE",
        "MATCH_COMMON_DATE",
        "HAS_RISK_REASON",
        "SUGGESTS_ICEBREAKER",
        "HAS_GRAPHRAG_PATH",
        "REQUEST_AT_LOCATION",
        "HAS_SCENE_INTENT",
        "HAS_SAFETY_CONTEXT",
        "HAS_SCENE_CANDIDATE",
        "CANDIDATE_USER",
        "RANKED_FOR_REQUEST",
        "PAIR_USER",
        "PAIR_CANDIDATE",
        "HAS_COMMON_TOPIC",
        "HAS_CHAT_DAY",
        "HAS_PROFILE_UPDATE",
        "AFFECTS_USER",
        "DATE_WITH_USER",
        "DATE_AT_LOCATION",
        "HAS_WEATHER_CONTEXT",
        "HAS_RISK_ASSESSMENT",
        "HAS_GOVERNANCE_EVENT",
        "APPLIES_POLICY_ACTION",
        "HAS_POLICY_REASON"
      ]);
      for (let wave = 0; wave < 2; wave += 1) {
        for (const row of relationships) {
          if (focusRelationships.length >= 95) break;
          if (!productTypes.has(row.relation)) continue;
          if (focusIds.has(row.source_id) || focusIds.has(row.target_id)) addRelationship(row);
        }
      }

      return {
        focusId,
        nodes: Array.from(focusIds).map((id) => nodeById[id]).filter(Boolean),
        relationships: focusRelationships
      };
    }

    function renderNeo4jProductGraph() {
      const graph = collectNeo4jFocusGraph();
      if (!graph.nodes.length || !graph.relationships.length) {
        return `<div class="empty">Neo4j CSV 还没有生成，先运行 scripts/run_pipeline.py。</div>`;
      }
      const width = 1120;
      const height = 520;
      const groupNames = {
        user: "用户",
        match: "心动推荐",
        scene: "闪电搭子",
        dynamic: "聊天热度",
        safety: "首约/安全",
        governance: "信用治理",
        default: "画像"
      };
      const groupX = {
        user: 70,
        match: 245,
        scene: 405,
        dynamic: 565,
        safety: 735,
        governance: 900,
        default: 1060
      };
      const groupOrder = ["user", "match", "scene", "dynamic", "safety", "governance", "default"];
      const grouped = Object.fromEntries(groupOrder.map((group) => [group, []]));
      for (const node of graph.nodes) {
        const group = neoNodeGroup(node);
        grouped[group].push(node);
      }
      const positions = {};
      for (const group of groupOrder) {
        const list = grouped[group];
        const step = Math.max(24, Math.min(58, (height - 94) / Math.max(list.length - 1, 1)));
        const top = list.length <= 2 ? 210 - (list.length - 1) * 30 : 44;
        list.forEach((node, index) => {
          positions[node.node_id] = {
            x: groupX[group],
            y: Math.min(height - 38, top + index * step)
          };
        });
      }
      const relLabels = {
        HAS_MATCH_RECOMMENDATION: "推荐",
        RECOMMENDS_USER: "候选",
        POSTED_SCENE_REQUEST: "发布",
        HAS_SCENE_CANDIDATE: "排序",
        HAS_RELATIONSHIP_PAIR: "关系",
        HAS_CHAT_DAY: "热度",
        PROPOSED_DATE_PLAN: "首约",
        HAS_RISK_ASSESSMENT: "安全",
        HAS_GOVERNANCE_RECORD: "信用",
        HAS_GOVERNANCE_EVENT: "事件"
      };
      const primaryTypes = new Set(Object.keys(relLabels));
      const nodeCounts = graph.nodes.reduce((acc, node) => {
        const group = neoNodeGroup(node);
        acc[group] = (acc[group] || 0) + 1;
        return acc;
      }, {});
      const focusNodeIds = new Set(graph.nodes.map((node) => node.node_id));
      if (!focusNodeIds.has(state.selectedNeo4jNodeId)) {
        state.selectedNeo4jNodeId = graph.focusId;
      }
      return `
        <div class="neo-map-note">
          当前画的是 ${escapeHtml(graph.focusId)} 相关产品子图：推荐、搭子、聊天热度、首约安全和信用治理都能追到节点。点击任意节点可以看字段和相连关系。全量图是 ${(data.neo4jSummary && data.neo4jSummary.n_nodes) || (data.neo4jNodes || []).length} 节点 / ${(data.neo4jSummary && data.neo4jSummary.n_relationships) || (data.neo4jRelationships || []).length} 关系，见下面 CSV 和 Cypher。
        </div>
        <svg class="neo4j-map" viewBox="0 0 ${width} ${height}" role="img" aria-label="Neo4j product graph">
          <defs>
            <filter id="neoNodeShadow" x="-35%" y="-35%" width="170%" height="170%">
              <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#101828" flood-opacity="0.14"></feDropShadow>
            </filter>
          </defs>
          ${groupOrder.map((group) => `
            <text class="neo-rel-label" x="${groupX[group]}" y="22" text-anchor="middle">${escapeHtml(groupNames[group])}</text>
            <line x1="${groupX[group]}" y1="34" x2="${groupX[group]}" y2="${height - 24}" stroke="rgba(52,64,84,0.08)" stroke-width="1"></line>
          `).join("")}
          <g>
            ${graph.relationships.map((row, index) => {
              const a = positions[row.source_id];
              const b = positions[row.target_id];
              if (!a || !b) return "";
              const strong = primaryTypes.has(row.relation);
              const midX = (a.x + b.x) / 2;
              const midY = (a.y + b.y) / 2;
              const label = relLabels[row.relation] || "";
              return `
                <line class="${strong ? "neo-link-strong" : "neo-link"}" x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${b.x.toFixed(1)}" y2="${b.y.toFixed(1)}"></line>
                ${label && index < 38 ? `<text class="neo-rel-label" x="${midX.toFixed(1)}" y="${(midY - 4).toFixed(1)}" text-anchor="middle">${escapeHtml(label)}</text>` : ""}
              `;
            }).join("")}
          </g>
          <g>
            ${graph.nodes.map((node) => {
              const pos = positions[node.node_id];
              if (!pos) return "";
              const group = neoNodeGroup(node);
              const radius = group === "user" ? 18 : group === "default" ? 10 : 13;
              const label = shortText(neoNodeLabel(node), group === "user" ? 6 : 9);
              const selectedClass = node.node_id === state.selectedNeo4jNodeId ? " neo-node-selected" : "";
              return `
                <g class="neo-clickable" data-neo-node-id="${escapeHtml(node.node_id)}" tabindex="0" role="button" aria-label="查看 ${escapeHtml(node.node_id)} 节点">
                  <circle class="neo-node-${group}${selectedClass}" cx="${pos.x.toFixed(1)}" cy="${pos.y.toFixed(1)}" r="${radius}" filter="url(#neoNodeShadow)"></circle>
                  <text class="neo-label" x="${pos.x.toFixed(1)}" y="${(pos.y + radius + 13).toFixed(1)}" text-anchor="middle">${escapeHtml(label)}</text>
                  <title>${escapeHtml(`${node.node_id} / ${node.label} / ${neoNodeLabel(node)}`)}</title>
                </g>
              `;
            }).join("")}
          </g>
        </svg>
        ${renderNeo4jNodeDetails(graph)}
        <div class="neo-focus-grid">
          <div class="soft-kpi"><span>当前子图节点</span><strong>${graph.nodes.length}</strong></div>
          <div class="soft-kpi"><span>当前子图关系</span><strong>${graph.relationships.length}</strong></div>
          <div class="soft-kpi"><span>产品节点</span><strong>${graph.nodes.filter((node) => neoNodeGroup(node) !== "default").length}</strong></div>
          <div class="soft-kpi"><span>画像层</span><strong>${nodeCounts.default || 0}</strong></div>
        </div>
      `;
    }

    function renderNeo4jNodeDetails(graph) {
      const nodeById = neoNodeById();
      const focusNodeIds = new Set(graph.nodes.map((node) => node.node_id));
      let selectedId = state.selectedNeo4jNodeId || graph.focusId;
      if (!focusNodeIds.has(selectedId)) selectedId = graph.focusId;
      state.selectedNeo4jNodeId = selectedId;
      const node = nodeById[selectedId] || {};
      if (!node.node_id) return `<div class="neo-node-detail empty">没有选中的节点</div>`;

      const fieldLabels = {
        node_id: "node_id",
        label: "Label",
        name: "名称",
        display_name: "展示名",
        user_id: "用户 ID",
        major: "专业",
        school: "学院",
        campus: "校区",
        category: "类别",
        status: "状态",
        score: "分数",
        risk_level: "风险",
        day: "Day",
        text: "文本",
        description: "描述",
        time_slot: "时间",
        lat: "纬度",
        lon: "经度",
        credit_score: "信用分",
        source_ref: "来源文件"
      };
      const preferredFields = [
        "node_id",
        "label",
        "name",
        "display_name",
        "user_id",
        "major",
        "school",
        "campus",
        "category",
        "status",
        "score",
        "risk_level",
        "day",
        "text",
        "description",
        "time_slot",
        "lat",
        "lon",
        "credit_score",
        "source_ref"
      ];
      const used = new Set();
      const fields = [];
      for (const key of preferredFields) {
        if (hasValue(node[key])) {
          fields.push([fieldLabels[key] || key, node[key]]);
          used.add(key);
        }
      }
      for (const [key, value] of Object.entries(node)) {
        if (!used.has(key) && key !== "source" && hasValue(value)) fields.push([fieldLabels[key] || key, value]);
      }

      const connected = graph.relationships.filter((row) => row.source_id === selectedId || row.target_id === selectedId);
      const outCount = connected.filter((row) => row.source_id === selectedId).length;
      const inCount = connected.length - outCount;
      const relationRows = connected.slice(0, 24).map((row) => {
        const outbound = row.source_id === selectedId;
        const otherId = outbound ? row.target_id : row.source_id;
        const other = nodeById[otherId] || {};
        const otherName = (outbound ? row.target_name : row.source_name) || neoNodeLabel(other) || otherId;
        const meta = [
          hasValue(row.rank) ? `rank ${row.rank}` : "",
          hasValue(row.score) ? `score ${row.score}` : "",
          hasValue(row.weight) ? `weight ${row.weight}` : "",
          hasValue(row.day) ? `Day ${row.day}` : "",
          hasValue(row.heat) ? `heat ${row.heat}` : "",
          hasValue(row.risk_level) ? `risk ${row.risk_level}` : "",
          row.reason || row.evidence || ""
        ].filter(Boolean).join(" / ");
        return `
          <div class="neo-rel-row">
            <span>${outbound ? "出边 ->" : "<- 入边"} ${escapeHtml(row.relation)}</span>
            <strong><button type="button" class="neo-node-link" data-neo-node-id="${escapeHtml(otherId)}">${escapeHtml(otherId)} / ${escapeHtml(shortText(otherName, 34))}</button></strong>
            ${meta ? `<p>${escapeHtml(shortText(meta, 150))}</p>` : ""}
          </div>
        `;
      }).join("");

      return `
        <div id="neoNodeDetail" class="neo-node-detail">
          <div class="section-head">
            <h3>节点详情：${escapeHtml(selectedId)}</h3>
            <span class="muted">${escapeHtml(node.label || "")} / 出边 ${outCount} / 入边 ${inCount}</span>
          </div>
          <div class="neo-detail-grid">
            <div>
              <h3>字段</h3>
              <div class="neo-props">
                ${fields.slice(0, 18).map(([label, value]) => `
                  <div class="neo-prop">
                    <span>${escapeHtml(label)}</span>
                    <strong>${escapeHtml(shortText(value, 180))}</strong>
                  </div>
                `).join("")}
              </div>
            </div>
            <div>
              <h3>当前子图里的关系</h3>
              <div class="neo-rels">
                ${relationRows || `<div class="empty">这个节点在当前子图里没有相连关系</div>`}
              </div>
            </div>
          </div>
        </div>
      `;
    }

    function attachNeo4jGraphEvents() {
      document.querySelectorAll("[data-neo-node-id]").forEach((item) => {
        item.addEventListener("click", () => {
          state.selectedNeo4jNodeId = item.dataset.neoNodeId;
          renderGraph();
        });
        item.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            state.selectedNeo4jNodeId = item.dataset.neoNodeId;
            renderGraph();
          }
        });
      });
    }

    function renderFeatures() {
      document.getElementById("content").innerHTML = `
        <div class="section-head">
          <h3>产品模块与课程方法</h3>
          <span class="muted">管理员视角：把产品功能和实际跑过的技术链路对应起来</span>
        </div>
        <div class="feature-map">
          ${featureCatalog.map((feature) => `
            <article class="feature-card">
              <h4>${escapeHtml(feature.name)}</h4>
              <p><strong>管理员看到：</strong>${escapeHtml(feature.admin)}</p>
              <p><strong>用户会感知到：</strong>${escapeHtml(feature.user)}</p>
              <p><strong>技术实现：</strong>${escapeHtml(feature.tech)}</p>
              <p><strong>课程方法：</strong>${escapeHtml(feature.course)}</p>
            </article>
          `).join("")}
        </div>
      `;
    }

    function renderDailyAdmin() {
      const rows = buildDailyAdminRows(state.adminDay);
      const avgHeat = rows.length ? rows.reduce((sum, row) => sum + row.heat, 0) / rows.length : 0;
      const riskRows = rows.filter((row) => row.riskLevel !== "low").length;
      document.getElementById("content").innerHTML = `
        <div class="section-head">
          <h3>每日关系状态监控</h3>
          <div class="toolbar">
            <select id="adminDaySelect">
              ${Array.from({length: 7}, (_, index) => {
                const day = index + 1;
                return `<option value="${day}" ${day === state.adminDay ? "selected" : ""}>Day ${day}</option>`;
              }).join("")}
            </select>
          </div>
        </div>
        <div class="metrics">
          ${metric("监控关系", rows.length)}
          ${metric("平均热度", `${Math.round(avgHeat * 100)}%`)}
          ${metric("风险关系", riskRows)}
          ${metric("当天消息", rows.reduce((sum, row) => sum + row.messageCount, 0))}
          ${metric("建议干预", rows.filter((row) => row.adminAction !== "保持观察").length)}
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>关系</th>
                <th>热度</th>
                <th>互动指标</th>
                <th>共同话题</th>
                <th>风险/治理</th>
                <th>管理员建议</th>
              </tr>
            </thead>
            <tbody>
              ${rows.map((row) => `
                <tr>
                  <td><strong>${escapeHtml(row.pairLabel)}</strong><br><span class="muted">${escapeHtml(row.pairId)}</span></td>
                  <td>${scoreBar("heat", row.heat)}</td>
                  <td>消息 ${escapeHtml(row.messageCount)} 条<br>平均回复 ${escapeHtml(row.delay)} 分钟<br>积极比例 ${escapeHtml(Math.round(row.positiveRatio * 100))}%</td>
                  <td>${escapeHtml(row.topics || "无")}</td>
                  <td><span class="risk-${escapeHtml(row.riskLevel)}">${escapeHtml(row.riskText)}</span><br><span class="muted">${escapeHtml(row.governanceText)}</span></td>
                  <td>${escapeHtml(row.adminAction)}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
        <div class="panel" style="margin-top:12px">
          <h3>时间变化解释</h3>
          <p class="copy">管理员看到的是关系状态随天数变化的聚合指标：聊天热度、消息数、回复延迟、积极比例、共同话题命中和治理策略。用户端只看到自己的聊天、推荐和安全提醒，不看到全局监控表。</p>
          <p class="copy"><strong>方法依据：</strong>用动态知识管理记录关系变化，用图权重和向量排序调整推荐，再用 GraphRAG 把提醒解释成人能看懂的话。</p>
        </div>
      `;
      document.getElementById("adminDaySelect").addEventListener("change", (event) => {
        state.adminDay = Number(event.target.value) || 1;
        renderDailyAdmin();
      });
    }

    function buildDailyAdminRows(day) {
      const dynamics = data.relationshipDynamics || [];
      const sourceRows = dynamics.length ? dynamics : (data.matches || []).slice(0, 6).map((match, index) => ({
        pair_id: `M${index + 1}`,
        user_id: match.user_id,
        candidate_id: match.candidate_id,
        common_topics: match.common_interests || [],
        heat_curve: Array.from({length: 7}, (_, i) => ({
          day: i + 1,
          heat: Math.max(0.2, Math.min(0.9, Number(match.final_score || 0.4) + i * 0.03)),
          message_count: 12 + i * 5,
          avg_response_delay_min: 40 - i * 3,
          positive_ratio: 0.55 + i * 0.03
        }))
      }));
      return sourceRows.map((item) => {
        const point = (item.heat_curve || []).find((p) => Number(p.day) === Number(day)) || (item.heat_curve || [])[0] || {};
        const user = byId[item.user_id] || {};
        const candidate = byId[item.candidate_id] || {};
        const userGov = governanceById[item.user_id] || {};
        const candidateGov = governanceById[item.candidate_id] || {};
        const heat = Number(point.heat) || 0;
        const delay = Number(point.avg_response_delay_min) || 0;
        const positiveRatio = Number(point.positive_ratio) || 0;
        const govRisk = Math.min(userGov.credit_score ?? 100, candidateGov.credit_score ?? 100);
        let riskLevel = "low";
        let riskText = "正常";
        let adminAction = "保持观察";
        if (heat < 0.42 || delay > 45 || positiveRatio < 0.5) {
          riskLevel = "medium";
          riskText = "关系降温";
          adminAction = "触发 AI 破冰建议";
        }
        if (govRisk < 75 || (candidateGov.policy || {}).conditional_mute || (userGov.policy || {}).conditional_mute) {
          riskLevel = "high";
          riskText = "治理风险";
          adminAction = "降低可见度并进入人工复核";
        }
        return {
          pairId: item.pair_id || `${item.user_id}-${item.candidate_id}`,
          pairLabel: `${user.display_name || item.user_id} / ${candidate.display_name || item.candidate_id}`,
          heat,
          messageCount: Number(point.message_count) || 0,
          delay,
          positiveRatio,
          topics: (item.common_topics || []).join("、"),
          riskLevel,
          riskText,
          governanceText: `信用 ${userGov.credit_score ?? 100}/${candidateGov.credit_score ?? 100}`,
          adminAction
        };
      });
    }

    function renderMatches() {
      const rows = (matchesByUser[state.selectedUserId] || []).slice().sort((a, b) => Number(b.final_score) - Number(a.final_score));
      document.getElementById("content").innerHTML = `
        <div class="section-head"><h3>Top 匹配推荐</h3><span class="muted">${rows.length} 个候选</span></div>
        ${rows.length ? `<div class="cards">${rows.map(matchCard).join("")}</div>` : `<div class="empty">当前用户没有匹配结果</div>`}
      `;
    }

    function matchCard(match) {
      const candidate = byId[match.candidate_id] || {};
      const exp = match.explanation || {};
      const graphPaths = exp.graph_paths || [];
      const riskNotes = exp.risk_notes || [];
      return `
        <article class="card">
          <div class="card-head">
            <img src="${imagePath(candidate.user_id)}" alt="${escapeHtml(candidate.display_name)}" onerror="this.style.visibility='hidden'">
            <div>
              <h4>${escapeHtml(candidate.display_name || match.candidate_id)} · ${escapeHtml(candidate.user_id || "")}</h4>
              <div class="muted truncate">${escapeHtml(candidate.major || "")} / ${escapeHtml(candidate.campus || "")}</div>
            </div>
            <div class="score-pill">${fmt(match.final_score)}</div>
          </div>
          <div class="score-list">
            ${scoreBar("文本语义", match.text_similarity)}
            ${scoreBar("图谱相似", match.graph_similarity)}
            ${scoreBar("价值观", match.value_similarity)}
            ${scoreBar("GNN链接", match.gnn_link_score)}
            ${scoreBar("图片", match.image_similarity)}
          </div>
          <p class="copy">${escapeHtml(exp.reason || "")}</p>
          ${tags(match.common_interests || [])}
          ${tags(match.common_values || [], "blue")}
          ${riskNotes.length ? `<ul class="list">${riskNotes.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : ""}
          <details>
            <summary>GraphRAG 路径证据</summary>
            <div class="path-list">
              ${graphPaths.slice(0, 10).map((item) => `<div class="path-row"><strong>${escapeHtml(item.type)}：</strong>${escapeHtml(item.path)}</div>`).join("") || `<div class="muted">暂无路径</div>`}
            </div>
          </details>
        </article>
      `;
    }

    function renderScenes() {
      const requests = data.sceneRequests || [];
      if (!requests.length) {
        document.getElementById("content").innerHTML = `<div class="empty">没有闪电搭子任务</div>`;
        return;
      }
      if (!requests.some((item) => item.request_id === state.selectedSceneId)) {
        state.selectedSceneId = requests[0].request_id;
      }
      const request = requests.find((item) => item.request_id === state.selectedSceneId) || requests[0];
      const matches = sceneMatchesByRequest[request.request_id] || [];
      document.getElementById("content").innerHTML = `
        <div class="section-head">
          <h3>闪电搭子动态任务</h3>
          <div class="toolbar">
            <select id="sceneSelect">${requests.map((item) => `<option value="${escapeHtml(item.request_id)}" ${item.request_id === request.request_id ? "selected" : ""}>${escapeHtml(item.request_id)} / ${escapeHtml(item.intent && item.intent.task_type)} / ${escapeHtml(item.target_time_slot)}</option>`).join("")}</select>
          </div>
        </div>
        <div class="scene-layout">
          <div class="panel">
            <h3>${escapeHtml(request.request_id)} · ${escapeHtml(request.location && request.location.name)}</h3>
            <p class="copy">${escapeHtml(request.text)}</p>
            <div class="kv">
              <span>任务类型</span><strong>${escapeHtml(request.intent && request.intent.task_type)}</strong>
              <span>紧急度</span><strong>${escapeHtml(request.intent && request.intent.urgency)}</strong>
              <span>时间窗口</span><strong>${escapeHtml(request.target_time_slot)}</strong>
              <span>安全等级</span><strong class="risk-${escapeHtml((request.safety_context && request.safety_context.risk_level) || "low")}">${escapeHtml(request.safety_context && request.safety_context.risk_level)}</strong>
            </div>
            ${tags((request.safety_context && request.safety_context.notes) || [], "rose")}
          </div>
          <div>
            <div class="cards">${matches.map(sceneCard).join("") || `<div class="empty">没有候选搭子</div>`}</div>
          </div>
        </div>
      `;
      document.getElementById("sceneSelect").addEventListener("change", (event) => {
        state.selectedSceneId = event.target.value;
        renderScenes();
      });
    }

    function sceneCard(row) {
      const candidate = byId[row.candidate_id] || {};
      return `
        <article class="card">
          <div class="card-head">
            <img src="${imagePath(candidate.user_id)}" alt="${escapeHtml(candidate.display_name)}" onerror="this.style.visibility='hidden'">
            <div>
              <h4>${escapeHtml(candidate.display_name || row.candidate_id)} · ${escapeHtml(row.candidate_id)}</h4>
              <div class="muted truncate">${escapeHtml(candidate.major || "")} / ${escapeHtml(candidate.campus || "")}</div>
            </div>
            <div class="score-pill">${fmt(row.final_score)}</div>
          </div>
          <p class="copy">${escapeHtml(row.scene_reason || "")}</p>
          <div class="score-list">
            ${scoreBar("语义", row.semantic_score)}
            ${scoreBar("时间", row.time_score)}
            ${scoreBar("地点", row.location_score)}
            ${scoreBar("任务", row.task_score)}
            ${scoreBar("照顾信号", row.care_score)}
          </div>
        </article>
      `;
    }

    function renderDynamics() {
      const rows = data.relationshipDynamics || [];
      document.getElementById("content").innerHTML = `
        <div class="section-head"><h3>恋爱动态与画像更新</h3><span class="muted">${rows.length} 组关系</span></div>
        ${rows.length ? `<div class="cards">${rows.map(dynamicCard).join("")}</div>` : `<div class="empty">没有关系热度数据</div>`}
      `;
    }

    function dynamicCard(row) {
      const user = byId[row.user_id] || {};
      const candidate = byId[row.candidate_id] || {};
      const summary = row.heat_summary || {};
      return `
        <article class="card">
          <div class="section-head">
            <h3>${escapeHtml(row.pair_id)} · ${escapeHtml(user.display_name || row.user_id)} / ${escapeHtml(candidate.display_name || row.candidate_id)}</h3>
            <span class="score-pill">${escapeHtml(summary.status || "")}</span>
          </div>
          ${heatChart(row.heat_curve || [])}
          <div class="kv">
            <span>平均热度</span><strong>${fmt(summary.avg_heat)}</strong>
            <span>热度变化</span><strong>${fmt(summary.heat_delta)}</strong>
            <span>共同话题</span><strong>${escapeHtml((row.common_topics || []).join("、") || "无")}</strong>
          </div>
          ${(row.profile_updates || []).length ? `<ul class="list">${row.profile_updates.map((item) => `<li>${escapeHtml(item.target)} ${escapeHtml(item.operation)} ${escapeHtml(item.tag)}：${escapeHtml(item.evidence)}</li>`).join("")}</ul>` : `<p class="copy muted">暂无明显画像更新信号</p>`}
        </article>
      `;
    }

    function heatChart(points) {
      if (!points.length) return `<div class="heat-chart"></div>`;
      const width = 560;
      const height = 170;
      const pad = 26;
      const values = points.map((point) => Number(point.heat) || 0);
      const min = Math.min(...values, 0.2);
      const max = Math.max(...values, 0.9);
      const xStep = points.length > 1 ? (width - pad * 2) / (points.length - 1) : 0;
      const scaleY = (value) => height - pad - ((value - min) / Math.max(max - min, 0.01)) * (height - pad * 2);
      const coords = points.map((point, index) => [pad + index * xStep, scaleY(Number(point.heat) || 0)]);
      const path = coords.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
      return `
        <svg class="heat-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="relationship heat curve">
          <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="#d8dee8"></line>
          <line x1="${pad}" y1="${pad}" x2="${pad}" y2="${height - pad}" stroke="#d8dee8"></line>
          <polyline points="${path}" fill="none" stroke="#0f766e" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></polyline>
          ${coords.map(([x, y], index) => `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="5" fill="#0f766e"></circle><text x="${x.toFixed(1)}" y="${height - 8}" text-anchor="middle" font-size="11" fill="#667085">D${index + 1}</text>`).join("")}
        </svg>
      `;
    }

    function renderDates() {
      const rows = data.dateContexts || [];
      document.getElementById("content").innerHTML = `
        <div class="section-head"><h3>线下约会安全上下文</h3><span class="muted">${rows.length} 个方案</span></div>
        ${rows.length ? `<div class="cards">${rows.map(dateCard).join("")}</div>` : `<div class="empty">没有线下约会方案</div>`}
      `;
    }

    function dateCard(row) {
      const user = byId[row.user_id] || {};
      const candidate = byId[row.candidate_id] || {};
      const risk = row.risk_assessment || {};
      const location = row.location || {};
      const weather = row.weather || {};
      return `
        <article class="card">
          <div class="section-head">
            <h3>${escapeHtml(row.plan_id)} · ${escapeHtml(location.name || "")}</h3>
            <span class="score-pill risk-${escapeHtml(risk.risk_level || "low")}">${escapeHtml(risk.risk_level || "")}</span>
          </div>
          <p class="muted">${escapeHtml(user.display_name || row.user_id)} / ${escapeHtml(candidate.display_name || row.candidate_id)} / ${escapeHtml(row.proposed_time || "")}</p>
          <p class="copy">${escapeHtml(row.date_suggestion || "")}</p>
          <div class="kv">
            <span>地点类型</span><strong>${escapeHtml(location.category || "")}</strong>
            <span>校区</span><strong>${escapeHtml(location.campus || "")}</strong>
            <span>天气</span><strong>${escapeHtml(weather.condition || "")} ${escapeHtml(weather.temperature_c || "")}C</strong>
            <span>人流</span><strong>${escapeHtml(location.crowd_level || "")}</strong>
          </div>
          ${(risk.reasons || []).length ? `<ul class="list">${risk.reasons.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : ""}
        </article>
      `;
    }

    function renderGovernance() {
      const rows = data.governanceRecords || [];
      document.getElementById("content").innerHTML = `
        <div class="section-head"><h3>知识治理策略</h3><span class="muted">${rows.length} 个用户</span></div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>用户</th>
                <th>信用分</th>
                <th>可见度</th>
                <th>冷却</th>
                <th>复核</th>
                <th>策略原因</th>
              </tr>
            </thead>
            <tbody>
              ${rows.map(governanceRow).join("")}
            </tbody>
          </table>
        </div>
      `;
    }

    function governanceRow(row) {
      const user = byId[row.user_id] || {};
      const policy = row.policy || {};
      const reasons = policy.reasons || [];
      return `
        <tr>
          <td><strong>${escapeHtml(row.user_id)}</strong><br><span class="muted">${escapeHtml(user.display_name || "")} / ${escapeHtml(user.major || "")}</span></td>
          <td>${fmt(row.credit_score)}</td>
          <td>${fmt(policy.visibility_multiplier ?? 1)}</td>
          <td>${fmt(policy.cooldown_hours ?? 0)} h</td>
          <td>${policy.conditional_mute || policy.review_required ? `<span class="risk-high">是</span>` : `<span class="risk-low">否</span>`}</td>
          <td>${escapeHtml(reasons.join("；") || "无")}</td>
        </tr>
      `;
    }

    function statusPill(label, status) {
      const cls = status === "ok" ? "status-ok" : status === "partial" ? "status-partial" : "status-missing";
      return `<span class="status-pill ${cls}">${escapeHtml(label)}</span>`;
    }

    function methodEvidenceRows() {
      const summary = data.summary || {};
      const neo4j = data.neo4jSummary || summary.neo4j_trace || {};
      const emb = data.embeddingMetadata || {};
      const chatTraces = data.chatRetrievalTraces || [];
      const vectorTraces = data.vectorSearchTraces || [];
      const faissAnn = data.faissAnnBenchmark || {};
      const intentTraces = data.intentGraphTraces || [];
      const hybridTraces = data.hybridSearchTraces || [];
      const tagEvidence = data.profileTagEvidence || [];
      const firstVector = vectorTraces[0] || {};
      const graphAlgo = data.graphAlgorithmTrace || {};
      const gnn = data.gnnMetrics || {};
      const gnnRisk = data.gnnRiskMetrics || {};
      const gnnArtifact = gnn.status ? gnn : (summary.gnn_artifact || {});
      const textProviderActual = emb.text_provider_actual || emb.text_provider || "unknown";
      const textProviderRequested = emb.text_provider_requested || textProviderActual;
      const textEmbeddingStatus = emb.text_shape ? (textProviderActual === "sentence_transformer" ? "ok" : "partial") : "missing";
      const textEmbeddingText = textProviderActual === "sentence_transformer" ? "Sentence-BERT 已运行" : emb.text_shape ? "本地 fallback 已运行" : "待生成";
      const faissReady = Boolean(emb.faiss) || vectorTraces.some((trace) => trace.faiss_available);
      const graphAlgorithms = graphAlgo.algorithms || [];
      return [
        {
          name: "知识获取与画像抽取",
          status: "ok",
          statusText: "已离线运行",
          input: "data/users.json",
          process: "规则抽取；LLM 接口可切换",
          output: `data/profiles.json / ${summary.n_users || 0} 用户`,
          code: "src/campus_match/profile_extraction.py",
          page: "用户档案、星图看板"
        },
        {
          name: "知识图谱 / 三元组",
          status: "ok",
          statusText: "已运行",
          input: "data/profiles.json",
          process: "User-Interest-Value-Time-Location 建图",
          output: `data/triples.csv / ${summary.n_triples || 0} 条画像三元组`,
          code: "src/campus_match/kg.py",
          page: "星图看板、图谱留痕"
        },
        {
          name: "文本 / 视觉向量",
          status: textEmbeddingStatus,
          statusText: textEmbeddingText,
          input: "画像文本 + 图片",
          process: `文本 ${emb.text_shape ? emb.text_shape.join("x") : "无"}，provider=${textProviderActual}；图片 ${emb.image_shape ? emb.image_shape.join("x") : "无"}，provider=${emb.image_provider || "unknown"}`,
          output: textProviderActual === textProviderRequested ? "indexes/text_embeddings.npy / image_embeddings.npy" : `auto 请求 ${textProviderRequested}，实际 ${textProviderActual}`,
          code: "src/campus_match/embeddings.py / matching.py",
          page: "心动星球、匹配分数拆解"
        },
        {
          name: "FAISS 向量召回",
          status: faissReady ? "ok" : vectorTraces.length ? "partial" : "missing",
          statusText: faissReady ? "FAISS 已运行" : vectorTraces.length ? "numpy fallback" : "未生成",
          input: "语义 query + 画像向量索引",
          process: firstVector.backend || "IndexFlatIP / inner product Top-K",
          output: `outputs/vector_search_trace.json / ${vectorTraces.length} traces`,
          code: "src/campus_match/vector_search.py",
          page: "雷达筛选、技术证据"
        },
        {
          name: "FAISS ANN 索引对比",
          status: faissAnn.status === "ok" ? "ok" : faissAnn.status ? "partial" : "missing",
          statusText: faissAnn.status === "ok" ? "Flat/IVF/HNSW 已跑" : faissAnn.status || "未生成",
          input: "画像文本向量 + 相同 query",
          process: "Flat 精确检索 vs IVF 倒排聚类 vs HNSW 近邻图",
          output: `outputs/faiss_ann_benchmark.json / ${faissAnn.n_vectors || 0} vectors`,
          code: "src/campus_match/vector_search.py",
          page: "技术证据"
        },
        {
          name: "意图图谱 / Prompt 增强",
          status: intentTraces.length ? "ok" : "missing",
          statusText: intentTraces.length ? "已运行" : "未生成",
          input: "用户自然语言需求",
          process: "Text-to-Graph：显性意图 -> 隐性意图 -> 画像字段",
          output: `outputs/intent_graph_traces.json / ${intentTraces.length} traces`,
          code: "src/campus_match/intent_search.py",
          page: "雷达页、技术证据"
        },
        {
          name: "混合检索 + 重排",
          status: hybridTraces.length ? "ok" : "missing",
          statusText: hybridTraces.length ? "已运行" : "未生成",
          input: "意图图谱 + 文本向量 + 用户画像字段",
          process: "关键词检索 + 向量召回 + 图谱约束 + 加权 rerank",
          output: `outputs/hybrid_search_traces.json / ${hybridTraces.length} traces`,
          code: "src/campus_match/intent_search.py",
          page: "雷达页、技术证据"
        },
        {
          name: "画像标签证据 RAG",
          status: tagEvidence.length ? "ok" : "missing",
          statusText: tagEvidence.length ? "已运行" : "未生成",
          input: "画像标签 + 模拟访谈证据",
          process: "Tag -> Evidence 检索、脱敏展示、路径解释",
          output: `outputs/profile_tag_evidence.json / ${tagEvidence.length} 条证据`,
          code: "src/campus_match/profile_evidence.py",
          page: "用户档案、技术证据"
        },
        {
          name: "NetworkX 图算法",
          status: graphAlgo.status === "ok" ? "ok" : "missing",
          statusText: graphAlgo.status === "ok" ? "已运行" : "未生成",
          input: "画像三元组 + 推荐边",
          process: graphAlgorithms.join(" / ") || "degree, PageRank, community",
          output: `${graphAlgo.n_nodes || 0} 图节点 / ${graphAlgo.n_edges || 0} 图边`,
          code: "src/campus_match/graph_analytics.py",
          page: "管理员技术证据、星图看板"
        },
        {
          name: "GraphRAG 推荐解释",
          status: "ok",
          statusText: "已运行",
          input: "匹配候选 + 图路径证据",
          process: "共同兴趣、价值观、时间地点路径 -> 推荐理由",
          output: "outputs/matches_with_explanations.json",
          code: "src/campus_match/graph_rag.py",
          page: "心动星球、Neo4j 推荐节点"
        },
        {
          name: "聊天实时 RAG",
          status: chatTraces.length ? "ok" : "missing",
          statusText: chatTraces.length ? "预生成 trace + 浏览器实时检索" : "未生成",
          input: "用户消息 query + 破冰知识库 + 画像/匹配上下文",
          process: "浏览器端 hash embedding + inner product Top-K -> 回复生成",
          output: `outputs/chat_vector_retrieval_trace.json / ${chatTraces.length} traces；用户输入时实时重算`,
          code: "src/campus_match/chat_retrieval.py",
          page: "用户消息页、小助手建议、技术证据"
        },
        {
          name: "Neo4j 图数据库留痕",
          status: neo4j.n_nodes ? "ok" : "partial",
          statusText: neo4j.n_nodes ? "CSV/Cypher 已生成" : "待生成",
          input: "画像、推荐、搭子、热度、治理",
          process: "节点/关系 schema + 导入 Cypher",
          output: `${neo4j.n_nodes || 0} 节点 / ${neo4j.n_relationships || 0} 关系`,
          code: "src/campus_match/neo4j_trace.py",
          page: "图谱留痕"
        },
        {
          name: "动态知识管理",
          status: "ok",
          statusText: "已运行",
          input: "匹配关系 + 合成聊天指标",
          process: "7 天热度、回复延迟、积极比例、画像更新",
          output: `outputs/relationship_dynamics.json / ${summary.n_relationship_dynamics || 0} 组`,
          code: "src/campus_match/relationship_dynamics.py",
          page: "每日状态、关系热度、用户档案"
        },
        {
          name: "知识治理与风控",
          status: "ok",
          statusText: "已运行",
          input: "失约、迟取消、不适反馈、正反馈",
          process: "信用分、推荐降权、冷却、复核",
          output: `outputs/governance_records.json / ${summary.n_governance_records || 0} 条`,
          code: "src/campus_match/governance.py",
          page: "知识治理、用户信用"
        },
        {
          name: "GNN / GraphSAGE",
          status: gnnArtifact.status === "trained" ? "ok" : "partial",
          statusText: gnnArtifact.status === "trained" ? "已训练" : gnnArtifact.status === "missing_dependencies" ? "缺依赖，未训练" : "可选增强未启用",
          input: "User-Interest-Value 图 + 文本特征",
          process: gnnArtifact.status === "trained" ? `${gnnArtifact.backend || "graphsage"} 链接预测 / AUC ${gnnArtifact.test_auc ?? "待评估"} / 已接入排序` : gnnArtifact.status === "missing_dependencies" ? "缺 torch，未训练" : "链接预测待启用",
          output: `outputs/gnn_pair_scores.json / ${gnnArtifact.status || "not_run"}`,
          code: "src/campus_match/gnn.py",
          page: "心动星球推荐排序、技术证据"
        },
        {
          name: "GCN 节点分类",
          status: gnnRisk.status === "trained" ? "ok" : "partial",
          statusText: gnnRisk.status === "trained" ? "已训练" : "未启用",
          input: "User-Interest-Value 图 + 信用治理标签",
          process: gnnRisk.status === "trained" ? `${gnnRisk.backend || "gcn"} 风险节点分类 / AUC ${gnnRisk.test_auc ?? "待评估"} / Acc ${gnnRisk.test_accuracy ?? "待评估"}` : "节点分类待启用",
          output: `outputs/gnn_node_risk_scores.json / ${gnnRisk.status || "not_run"}`,
          code: "src/campus_match/gnn.py",
          page: "知识治理、技术证据"
        }
      ];
    }

    function renderTechEvidence() {
      const summary = data.summary || {};
      const neo4j = data.neo4jSummary || summary.neo4j_trace || {};
      const emb = data.embeddingMetadata || {};
      const chatTraces = data.chatRetrievalTraces || [];
      const vectorTraces = data.vectorSearchTraces || [];
      const faissAnn = data.faissAnnBenchmark || {};
      const intentTraces = data.intentGraphTraces || [];
      const hybridTraces = data.hybridSearchTraces || [];
      const tagEvidence = data.profileTagEvidence || [];
      const graphAlgo = data.graphAlgorithmTrace || {};
      const gnn = data.gnnMetrics || {};
      const gnnRisk = data.gnnRiskMetrics || {};
      const gnnPairs = data.gnnPairScores || [];
      const gnnRiskScores = data.gnnRiskScores || [];
      const firstTrace = chatTraces[0] || {};
      const firstVector = vectorTraces[0] || {};
      const firstAnnQuery = (faissAnn.queries || [])[0] || {};
      const topDocs = firstTrace.top_k || [];
      const vectorHits = firstVector.top_k || [];
      const firstHybrid = hybridTraces[0] || {};
      const firstEvidence = tagEvidence[0] || {};
      const graphPairs = graphAlgo.pair_evidence || [];
      const graphScores = graphAlgo.user_scores || [];
      const graphCommunities = graphAlgo.communities || [];
      document.getElementById("content").innerHTML = `
        <section class="tech-cockpit">
          <div class="section-head">
            <div>
              <h3>课程方法驾驶舱</h3>
              <p class="muted">这里展示真实跑过的输入、处理、输出和代码位置；用户端只展示自然解释。</p>
            </div>
            <span class="score-pill">${methodEvidenceRows().filter((row) => row.status === "ok").length}/${methodEvidenceRows().length} running</span>
          </div>
          <div class="tech-flow">
            <div class="tech-step"><strong>1 信息采集</strong><span>问卷/访谈文本进入画像抽取</span></div>
            <div class="tech-step"><strong>2 知识图谱</strong><span>生成三元组和 Neo4j 产品图</span></div>
            <div class="tech-step"><strong>3 向量召回</strong><span>文本/图片 embedding 参与排序</span></div>
            <div class="tech-step"><strong>4 GraphRAG</strong><span>路径证据生成推荐理由</span></div>
            <div class="tech-step"><strong>5 聊天检索</strong><span>消息 query 检索破冰知识库</span></div>
            <div class="tech-step"><strong>6 动态治理</strong><span>热度、信用和安全策略更新</span></div>
          </div>
        </section>
        <div class="metrics">
          ${metric("文本向量", emb.text_shape ? emb.text_shape.join(" x ") : "未生成")}
          ${metric("图片向量", emb.image_shape ? emb.image_shape.join(" x ") : "未生成")}
          ${metric("FAISS 检索 trace", vectorTraces.length)}
          ${metric("ANN 索引对比", faissAnn.status === "ok" ? `${(faissAnn.summary || []).length} indexes` : "未生成")}
          ${metric("意图图谱 trace", intentTraces.length)}
          ${metric("混合检索 trace", hybridTraces.length)}
          ${metric("标签证据", tagEvidence.length)}
          ${metric("聊天 RAG trace", chatTraces.length)}
          ${metric("图算法", graphAlgo.status === "ok" ? `${graphAlgo.n_nodes || 0}/${graphAlgo.n_edges || 0}` : "未生成")}
          ${metric("GNN 链接预测", gnn.status === "trained" ? `AUC ${gnn.test_auc}` : "未训练")}
          ${metric("GCN 风险分类", gnnRisk.status === "trained" ? `AUC ${gnnRisk.test_auc}` : "未训练")}
          ${metric("Neo4j 产品图", `${neo4j.n_nodes || 0}/${neo4j.n_relationships || 0}`)}
        </div>
        <div class="tech-grid">
          ${methodEvidenceRows().map((row) => `
            <article class="tech-card">
              <div class="section-head">
                <h4>${escapeHtml(row.name)}</h4>
                ${statusPill(row.statusText, row.status)}
              </div>
              <div class="kv">
                <span>输入</span><strong>${escapeHtml(row.input)}</strong>
                <span>处理</span><strong>${escapeHtml(row.process)}</strong>
                <span>输出</span><strong>${escapeHtml(row.output)}</strong>
                <span>代码</span><strong>${escapeHtml(row.code)}</strong>
                <span>页面</span><strong>${escapeHtml(row.page)}</strong>
              </div>
            </article>
          `).join("")}
        </div>
        <div class="two-col" style="margin-top:12px">
          <section class="panel">
            <div class="section-head">
              <h3>意图图谱样例</h3>
              ${statusPill(intentTraces.length ? "已生成" : "未生成", intentTraces.length ? "ok" : "missing")}
            </div>
            ${intentTraces.length ? `
              <p class="copy"><strong>用户需求：</strong>${escapeHtml((intentTraces[0] || {}).query)}</p>
              ${renderIntentGraph(intentTraces[0])}
              ${renderIntentSummary(intentTraces[0])}
            ` : `<div class="empty">还没有意图图谱 trace。</div>`}
          </section>
          <section class="panel">
            <div class="section-head">
              <h3>混合检索重排样例</h3>
              ${statusPill(firstHybrid.status || "未生成", hybridTraces.length ? "ok" : "missing")}
            </div>
            ${hybridTraces.length ? `
              <p class="copy"><strong>检索链路：</strong>${escapeHtml((firstHybrid.retrievers || []).join(" + "))}</p>
              <p class="copy"><strong>权重：</strong>向量 ${escapeHtml(firstHybrid.weights && firstHybrid.weights.vector)} / 关键词 ${escapeHtml(firstHybrid.weights && firstHybrid.weights.sparse)} / 图谱 ${escapeHtml(firstHybrid.weights && firstHybrid.weights.graph)} / 约束 ${escapeHtml(firstHybrid.weights && firstHybrid.weights.constraint)}</p>
              ${renderHybridTrace(firstHybrid)}
            ` : `<div class="empty">还没有混合检索 trace。</div>`}
          </section>
        </div>
        <div class="two-col" style="margin-top:12px">
          <section class="panel">
            <div class="section-head">
              <h3>画像标签证据 RAG</h3>
              ${statusPill(tagEvidence.length ? "已生成" : "未生成", tagEvidence.length ? "ok" : "missing")}
            </div>
            ${tagEvidence.length ? renderProfileEvidenceCard(firstEvidence) : `<div class="empty">还没有标签证据。</div>`}
          </section>
          <section class="panel">
            <div class="section-head">
              <h3>标签证据 Top 样例</h3>
              ${statusPill(tagEvidence.length ? `${tagEvidence.length} 条` : "未生成", tagEvidence.length ? "ok" : "missing")}
            </div>
            ${tagEvidence.length ? `
              <div class="trace-list">
                ${tagEvidence.slice(0, 5).map((row) => `
                  <div class="trace-row">
                    <span>${escapeHtml(row.user_id)}</span>
                    <strong>${escapeHtml(row.tag)}<br><span>${escapeHtml(row.source_type)} / ${escapeHtml(row.tag_type)}</span></strong>
                    <span>${escapeHtml(row.retrieval_score)}</span>
                  </div>
                `).join("")}
              </div>
            ` : `<div class="empty">还没有证据样例。</div>`}
          </section>
        </div>
        <div class="two-col" style="margin-top:12px">
          <section class="panel">
            <div class="section-head">
              <h3>FAISS ANN 索引对比</h3>
              ${statusPill(faissAnn.status || "未生成", faissAnn.status === "ok" ? "ok" : "missing")}
            </div>
            ${faissAnn.status === "ok" ? `
              <p class="copy"><strong>课件方法：</strong>${escapeHtml(faissAnn.course_method || "Flat / IVF / HNSW")}</p>
              <div class="trace-list">
                ${(faissAnn.summary || []).map((row) => `
                  <div class="trace-row">
                    <span>${escapeHtml(row.name)}</span>
                    <strong>${escapeHtml(row.index_type)}<br><span>${escapeHtml(row.description)}</span></strong>
                    <span>${escapeHtml(row.avg_search_ms)}ms / overlap ${escapeHtml(row.avg_overlap_with_flat_at_k)}</span>
                  </div>
                `).join("")}
              </div>
            ` : `<div class="empty">还没有 ANN 对比实验。运行 pipeline 后会生成。</div>`}
          </section>
          <section class="panel">
            <div class="section-head">
              <h3>同一 Query 的 Top-K 对比</h3>
              ${statusPill(firstAnnQuery.query || "未生成", faissAnn.status === "ok" ? "ok" : "missing")}
            </div>
            ${firstAnnQuery.query ? `
              <p class="copy"><strong>Query：</strong>${escapeHtml(firstAnnQuery.query)}</p>
              <div class="trace-list">
                ${(firstAnnQuery.results || []).map((result) => `
                  <div class="trace-row">
                    <span>${escapeHtml(result.name)}</span>
                    <strong>${escapeHtml((result.top_k || []).map((hit) => hit.user_id).join(" / "))}<br><span>${escapeHtml(JSON.stringify(result.params || {}))}</span></strong>
                    <span>${escapeHtml(result.avg_search_ms)}ms</span>
                  </div>
                `).join("")}
              </div>
            ` : `<div class="empty">还没有 query 对比结果。</div>`}
          </section>
        </div>
        <div class="two-col" style="margin-top:12px">
          <section class="panel">
            <div class="section-head">
              <h3>GNN 链接预测样例</h3>
              ${statusPill(gnn.status || "未生成", gnn.status === "trained" ? "ok" : "missing")}
            </div>
            ${gnn.status === "trained" ? `
              <p class="copy"><strong>课件方法：</strong>第4章链接预测。训练用户-属性图，预测两个用户未来形成连接的概率，并已接入推荐排序。</p>
              <p class="copy"><strong>训练指标：</strong>${escapeHtml(gnn.backend || "graphsage")} / AUC ${escapeHtml(gnn.test_auc)} / ${escapeHtml(gnn.n_train_pairs)} train pairs / ${escapeHtml(gnn.n_test_pairs)} test pairs</p>
              <div class="trace-list">
                ${gnnPairs.slice().sort((a, b) => Number(b.gnn_link_score) - Number(a.gnn_link_score)).slice(0, 3).map((row, idx) => `
                  <div class="trace-row">
                    <span>#${idx + 1}</span>
                    <strong>${escapeHtml(row.user_a)} -> ${escapeHtml(row.user_b)}<br><span>link prediction score</span></strong>
                    <span>${escapeHtml(row.gnn_link_score)}</span>
                  </div>
                `).join("")}
              </div>
            ` : `<div class="empty">还没有 GNN 链接预测结果。</div>`}
          </section>
          <section class="panel">
            <div class="section-head">
              <h3>GCN 风险节点分类</h3>
              ${statusPill(gnnRisk.status || "未生成", gnnRisk.status === "trained" ? "ok" : "missing")}
            </div>
            ${gnnRisk.status === "trained" ? `
              <p class="copy"><strong>课件方法：</strong>第4章节点分类。用用户邻域、兴趣、价值观和治理标签训练风险节点分类器。</p>
              <p class="copy"><strong>训练指标：</strong>${escapeHtml(gnnRisk.backend || "gcn")} / AUC ${escapeHtml(gnnRisk.test_auc)} / Acc ${escapeHtml(gnnRisk.test_accuracy)}</p>
              <div class="trace-list">
                ${gnnRiskScores.slice(0, 3).map((row) => `
                  <div class="trace-row">
                    <span>${escapeHtml(row.user_id)}</span>
                    <strong>risk probability ${escapeHtml(row.gnn_risk_probability)}<br><span>credit ${escapeHtml(row.credit_score)} / label ${escapeHtml(row.risk_label)}</span></strong>
                    <span>${escapeHtml(row.gnn_risk_probability)}</span>
                  </div>
                `).join("")}
              </div>
            ` : `<div class="empty">还没有 GCN 节点分类结果。</div>`}
          </section>
        </div>
        <div class="two-col" style="margin-top:12px">
          <section class="panel">
            <div class="section-head">
              <h3>FAISS 向量召回样例</h3>
              ${statusPill(firstVector.backend || "未生成", vectorTraces.length ? "ok" : "missing")}
            </div>
            ${firstVector.query ? `
              <p class="copy"><strong>语义需求：</strong>${escapeHtml(firstVector.query)}</p>
              <p class="copy"><strong>检索链路：</strong>${escapeHtml(firstVector.query_encoder || "unknown")} -> ${escapeHtml(firstVector.backend || "unknown")} / ${escapeHtml(firstVector.query_embedding_dim)} 维</p>
              <div class="trace-list">
                ${vectorHits.map((hit) => `
                  <div class="trace-row">
                    <span>#${escapeHtml(hit.rank)}</span>
                    <strong>${escapeHtml(hit.display_name || hit.user_id)}<br><span>${escapeHtml((hit.interests || []).join("、"))}</span></strong>
                    <span>${escapeHtml(hit.score)}</span>
                  </div>
                `).join("")}
              </div>
            ` : `<div class="empty">还没有 FAISS 检索 trace。运行 pipeline 后会生成。</div>`}
          </section>
          <section class="panel">
            <div class="section-head">
              <h3>NetworkX 图算法样例</h3>
              ${statusPill(graphAlgo.status || "未生成", graphAlgo.status === "ok" ? "ok" : "missing")}
            </div>
            ${graphAlgo.status === "ok" ? `
              <p class="copy"><strong>算法：</strong>${escapeHtml((graphAlgo.algorithms || []).join(" / "))}</p>
              <div class="trace-list">
                ${graphScores.slice(0, 3).map((row) => `
                  <div class="trace-row">
                    <span>${escapeHtml(row.user_id)}</span>
                    <strong>PageRank ${escapeHtml(row.pagerank)}<br><span>degree centrality ${escapeHtml(row.degree_centrality)}</span></strong>
                    <span>${escapeHtml(row.degree)}</span>
                  </div>
                `).join("")}
              </div>
              <p class="copy"><strong>共同邻居证据：</strong>${escapeHtml(graphPairs[0] ? `${graphPairs[0].user_id} -> ${graphPairs[0].candidate_id}，${graphPairs[0].common_neighbor_count} 个共同节点` : "暂无")}</p>
              <p class="copy"><strong>社区发现：</strong>${escapeHtml(graphCommunities[0] ? `${(graphCommunities[0].users || []).join("、")} / ${(graphCommunities[0].topics || []).slice(0, 3).join("、")}` : "暂无")}</p>
            ` : `<div class="empty">还没有图算法 trace。运行 pipeline 后会生成。</div>`}
          </section>
        </div>
        <div class="two-col" style="margin-top:12px">
          <section class="panel">
            <div class="section-head">
              <h3>聊天向量检索样例</h3>
              ${statusPill(firstTrace.status || "未生成", chatTraces.length ? "ok" : "missing")}
            </div>
            ${firstTrace.query ? `
              <p class="copy"><strong>用户消息：</strong>${escapeHtml(firstTrace.query)}</p>
              <p class="copy"><strong>检索方法：</strong>${escapeHtml(firstTrace.retrieval_method)} / ${escapeHtml(firstTrace.query_embedding_dim)} 维</p>
              <div class="trace-list">
                ${topDocs.map((doc) => `
                  <div class="trace-row">
                    <span>#${escapeHtml(doc.rank)}</span>
                    <strong>${escapeHtml(doc.title)}<br><span>${escapeHtml(doc.source)}</span></strong>
                    <span>${escapeHtml(doc.score)}</span>
                  </div>
                `).join("")}
              </div>
              <p class="copy"><strong>最终建议：</strong>${escapeHtml(firstTrace.final_suggestion)}</p>
            ` : `<div class="empty">还没有聊天检索 trace。运行 pipeline 后会生成。</div>`}
          </section>
          <section class="panel">
            <h3>答辩时怎么说</h3>
            <p class="copy">当前真实跑通的是：知识抽取、Sentence-BERT 文本向量、FAISS 向量召回、FAISS Flat/IVF/HNSW 对比、意图图谱、混合检索重排、画像标签证据 RAG、GraphRAG 解释、聊天实时 RAG、NetworkX 图算法、GNN 链接预测接入排序、GCN 风险节点分类、信用治理和 Neo4j 导入文件生成。</p>
            <p class="copy">CLIP 和本地大模型仍是增强项；如果环境没有依赖，前端会显示 fallback 或未启用，不把占位当成真实训练结果。</p>
            ${emb.text_provider_error ? `<p class="copy"><strong>Embedding fallback 原因：</strong>${escapeHtml(emb.text_provider_error).slice(0, 220)}</p>` : ""}
            ${tags(["聊天实时RAG", "FAISS ANN对比", "意图图谱", "混合检索", "标签证据RAG", "FAISS", "NetworkX", "GraphRAG", "GNN排序", "GCN分类", "Neo4j CSV/Cypher"], "blue")}
          </section>
        </div>
      `;
    }

    function renderGraph() {
      const neo4j = data.neo4jSummary || (data.summary && data.summary.neo4j_trace) || {};
      const labelCounts = neo4j.node_label_counts || {};
      const relationshipCounts = neo4j.relationship_counts || {};
      const scopeLabels = {
        profile_triples: "画像三元组",
        match_recommendations: "心动推荐",
        graph_rag_evidence: "GraphRAG 路径",
        scene_requests: "闪电搭子任务",
        scene_candidate_ranking: "搭子候选排序",
        relationship_heat_curve: "7 天聊天热度",
        date_plans: "首约方案",
        safety_context: "地点安全上下文",
        governance_records: "信用治理"
      };
      const graphScope = (neo4j.graph_scope || []).map((item) => scopeLabels[item] || item);
      document.getElementById("content").innerHTML = `
        <div class="section-head"><h3>Neo4j 产品运行图</h3><span class="muted">${fmt(neo4j.n_nodes || 0)} 节点 / ${fmt(neo4j.n_relationships || 0)} 关系</span></div>
        <div class="panel" style="margin-bottom:12px">
          <div class="section-head">
            <h3>这次不是只导画像</h3>
            <span class="tag">${escapeHtml(neo4j.n_profile_triples || (data.summary && data.summary.n_triples) || 0)} 条画像三元组</span>
          </div>
          <p class="copy">Neo4j CSV 现在覆盖完整 demo 链路：用户画像、推荐节点、GraphRAG 证据、闪电搭子任务、候选排序、聊天热度、首约安全和信用治理。画像三元组只是其中一层，不再拿它冒充整张图。</p>
          ${tags(graphScope, "blue")}
        </div>
        <div class="panel" style="margin-bottom:12px">
          <div class="section-head">
            <h3>产品图可视化</h3>
            <span class="muted">当前用户相关子图 / 全量见 CSV</span>
          </div>
          ${renderNeo4jProductGraph()}
          <div class="graph-legend">
            <span class="legend-dot"><i style="background:#0f766e"></i>用户</span>
            <span class="legend-dot"><i style="background:#2f64d6"></i>心动推荐</span>
            <span class="legend-dot"><i style="background:#b97918"></i>闪电搭子</span>
            <span class="legend-dot"><i style="background:#6657c8"></i>聊天热度</span>
            <span class="legend-dot"><i style="background:#bd3b2f"></i>首约/安全</span>
            <span class="legend-dot"><i style="background:#7a4a21"></i>信用治理</span>
          </div>
        </div>
        <div class="two-col">
          <div class="panel">
            <h3>节点标签</h3>
            ${objectBars(labelCounts)}
          </div>
          <div class="panel">
            <h3>关系类型</h3>
            ${objectBars(relationshipCounts)}
          </div>
        </div>
        <div class="panel" style="margin-top:12px">
          <h3>交付文件</h3>
          <div class="path-list">
            <div class="path-row">outputs/neo4j/campus_match_ai_nodes.csv</div>
            <div class="path-row">outputs/neo4j/campus_match_ai_relationships.csv</div>
            <div class="path-row">outputs/neo4j/import_campus_match_ai.cypher</div>
            <div class="path-row">outputs/neo4j/demo_queries.cypher</div>
          </div>
          ${tags(neo4j.recommended_screenshot_queries || [], "blue")}
        </div>
      `;
      attachNeo4jGraphEvents();
    }

    function resetExperience() {
      const profile = byId[state.experienceUserId] || (data.profiles || [])[0] || {};
      const governance = governanceById[profile.user_id] || {};
      const best = bestMatchForUser(profile.user_id);
      state.experienceDay = 1;
      state.experienceComplete = false;
      state.selectedAction = "interview";
      state.experienceHeat = 0.34;
      state.experienceCredit = governance.credit_score ?? 100;
      state.experienceTags = [...(profile.personality_tags || []).slice(0, 3)];
      state.experienceHistory = [];
      state.conversationUserId = (best && best.candidate_id) || "";
      state.chatMessages = initialChatMessages(profile);
      state.dayChatCount = 0;
      state.dayTouched = false;
      state.actionLocks = {};
      state.chatLimitNoticeDay = 0;
      state.lastChatRag = null;
      state.lastDailyIntent = null;
      state.recentReplySignatures = [];
      state.recentReplyTopics = [];
      document.getElementById("experienceText").value = "";
      renderUserExperience();
    }

    function renderUserExperience() {
      const profile = byId[state.experienceUserId] || (data.profiles || [])[0] || {};
      if (!profile.user_id) {
        document.getElementById("experienceOutcome").innerHTML = `<div class="empty">没有用户数据</div>`;
        return;
      }
      state.experienceUserId = profile.user_id;
      state.selectedUserId = profile.user_id;
      if (!state.experienceTags.length) {
        state.experienceTags = [...(profile.personality_tags || []).slice(0, 3)];
      }
      if (!state.conversationUserId || state.conversationUserId === profile.user_id || !byId[state.conversationUserId]) {
        const best = bestMatchForUser(profile.user_id);
        state.conversationUserId = (best && best.candidate_id) || "";
      }
      if (!state.chatMessages.length) {
        state.chatMessages = initialChatMessages(profile);
      }
      renderUserTabs();
      renderUserPaneVisibility();
      renderExperienceUserSelect();
      renderExperienceProfile(profile);
      renderExperienceMetrics(profile);
      renderPlanetModeTabs();
      renderPlanetModeContent(profile);
      renderDayStrip();
      renderActionGrid();
      renderExperienceOutcome(profile);
      renderChatPanel(profile);
      renderRadarPane(profile);
      renderArchivePane(profile);
      renderExperienceTimeline();
      updateExperienceControls();
      document.getElementById("experienceStatus").textContent = `${profile.display_name} · ${state.experienceComplete ? "7 天已结束" : `第 ${state.experienceDay} 天`} · ${userTabs.find((tab) => tab[0] === state.userTab)?.[1] || "星球"}`;
    }

    function renderUserTabs() {
      const icons = {planet: "✦", radar: "◎", messages: "◇", archive: "□"};
      document.getElementById("userTabs").innerHTML = userTabs.map(([id, label]) => `
        <button class="user-tab-button ${state.userTab === id ? "active" : ""}" data-user-tab="${id}" data-icon="${escapeHtml(icons[id] || "•")}">${label}</button>
      `).join("");
      document.querySelectorAll("[data-user-tab]").forEach((button) => {
        button.addEventListener("click", () => {
          state.userTab = button.dataset.userTab;
          renderUserExperience();
        });
      });
    }

    function renderUserPaneVisibility() {
      const paneByTab = {
        planet: "planetPane",
        radar: "radarPane",
        messages: "messagesPane",
        archive: "archivePane"
      };
      Object.values(paneByTab).forEach((id) => {
        document.getElementById(id).hidden = id !== paneByTab[state.userTab];
      });
    }

    function renderPlanetModeTabs() {
      document.getElementById("planetModeTabs").innerHTML = planetModes.map(([id, label]) => `
        <button class="planet-mode-button ${state.planetMode === id ? "active" : ""}" data-planet-mode="${id}">${label}</button>
      `).join("");
      document.querySelectorAll("[data-planet-mode]").forEach((button) => {
        button.addEventListener("click", () => {
          state.planetMode = button.dataset.planetMode;
          renderUserExperience();
        });
      });
    }

    function renderExperienceUserSelect() {
      const select = document.getElementById("experienceUserSelect");
      select.innerHTML = (data.profiles || []).map((profile) => `
        <option value="${escapeHtml(profile.user_id)}" ${profile.user_id === state.experienceUserId ? "selected" : ""}>
          ${escapeHtml(profile.display_name)} / ${escapeHtml(profile.major)} / ${escapeHtml(profile.campus)}
        </option>
      `).join("");
    }

    function renderExperienceProfile(profile) {
      const best = bestMatchForUser(profile.user_id);
      const candidate = best ? byId[best.candidate_id] : null;
      const convo = currentConversation(profile);
      const activeCandidate = convo.candidate || {};
      document.getElementById("experienceProfile").innerHTML = `
        <div class="profile-media" style="grid-template-columns:72px 1fr">
          <img src="${imagePath(profile.user_id)}" alt="${escapeHtml(profile.display_name)}" style="width:72px;height:72px" onerror="this.style.visibility='hidden'">
          <div>
            <h3>${escapeHtml(profile.display_name)}</h3>
            <p>${escapeHtml(profile.major)} / ${escapeHtml(profile.campus)}</p>
            <p>${escapeHtml(profile.relationship_goal)} / ${escapeHtml(profile.communication_style)}</p>
          </div>
        </div>
        <p class="copy">${escapeHtml(profile.self_intro || "")}</p>
        ${tags(state.experienceTags, "blue")}
        <div class="kv">
          <span>今日推荐</span><strong>${candidate ? escapeHtml(candidate.display_name) : "暂无"}</strong>
	          <span>合拍度</span><strong>${best ? friendlyScore(best.final_score) : "待定"}</strong>
          <span>正在聊天</span><strong>${activeCandidate.display_name ? escapeHtml(activeCandidate.display_name) : "还没开始"}</strong>
        </div>
      `;
    }

    function renderExperienceMetrics(profile) {
      const best = bestMatchForUser(profile.user_id);
      const rows = [
        metric("今天", state.experienceComplete ? "已结束" : `Day ${state.experienceDay}`),
        metric("聊天热度", `${Math.round(state.experienceHeat * 100)}%`),
        metric("信用", state.experienceCredit),
        metric("我的标签", state.experienceTags.length),
        metric("今日合拍度", best ? friendlyScore(best.final_score) : "待定")
      ];
      document.getElementById("experienceMetrics").innerHTML = rows.join("");
    }

    function renderPlanetModeContent(profile) {
      const container = document.getElementById("planetModeContent");
      if (state.planetMode === "lightning") {
        const scene = sceneForUser(profile.user_id);
        const sceneRows = scene ? (sceneMatchesByRequest[scene.request_id] || []) : [];
        const sceneLocked = isActionLocked("scene", scene ? scene.request_id : "default") || state.experienceComplete;
        container.innerHTML = `
          <div class="two-col">
            <div class="panel lightning-hero">
              <div class="section-head">
                <h3>闪电搭子</h3>
	                <span class="tag">附近 / 现在</span>
              </div>
	              <p class="copy"><strong>现在有人想：</strong>${escapeHtml(scene ? scene.text : "找一个同校区搭子。")}</p>
              <div class="kv">
	                <span>时间</span><strong>${escapeHtml(scene ? scene.target_time_slot : "今天")}</strong>
                <span>地点</span><strong>${escapeHtml(scene && scene.location ? scene.location.name : "校内公共区域")}</strong>
	                <span>地点安全</span><strong class="risk-${escapeHtml(scene && scene.safety_context ? scene.safety_context.risk_level : "low")}">${escapeHtml(scene && scene.safety_context ? scene.safety_context.risk_level : "low")}</strong>
              </div>
	              <button class="tab-button active mobile-join-button ${sceneLocked ? "locked" : ""}" id="joinSceneChat" ${sceneLocked ? "disabled" : ""}>${sceneLocked ? "已加入" : "加入这个局"}</button>
            </div>
            <div class="panel">
	              <h3>可能合适的人</h3>
              <div class="cards lightning-list">
                ${sceneRows.slice(0, 3).map((row) => {
                  const candidate = byId[row.candidate_id] || {};
                  return `
                    <article class="card lightning-person">
                      <div class="card-head">
                        <img src="${imagePath(candidate.user_id)}" alt="${escapeHtml(candidate.display_name)}" onerror="this.style.visibility='hidden'">
                        <div>
                          <h4>${escapeHtml(candidate.display_name || row.candidate_id)}</h4>
                          <div class="muted">${escapeHtml(candidate.major || "")} / ${escapeHtml(candidate.campus || "")}</div>
                        </div>
	                        <div class="score-pill">${friendlyScore(row.final_score)}</div>
                      </div>
	                      <p class="copy">${escapeHtml(friendlySceneReason(row, candidate))}</p>
                    </article>
                  `;
                }).join("") || `<div class="empty">暂无候选搭子</div>`}
              </div>
            </div>
          </div>
        `;
        const joinButton = document.getElementById("joinSceneChat");
        if (joinButton) {
          joinButton.addEventListener("click", () => {
            if (sceneLocked) return;
            const topRow = sceneRows[0] || {};
            const target = byId[topRow.candidate_id] || {};
            state.userTab = "messages";
            state.selectedAction = "scene";
            state.dayTouched = true;
            lockAction("scene", scene ? scene.request_id : "default");
            switchConversation(
              profile,
              target,
	              "临时聊天已经开好。先把时间、地点和要不要一起导航说清楚就行。",
              `我现在也方便加入。地点选 ${scene && scene.location ? scene.location.name : "校内公共区域"} 可以，先碰面 20 分钟也没问题。`
            );
            renderUserExperience();
          });
        }
        return;
      }

      const best = bestMatchForUser(profile.user_id);
      const candidate = best ? byId[best.candidate_id] || {} : {};
      const exp = (best && best.explanation) || {};
      const heartLocked = isActionLocked("heart", candidate.user_id || "none") || state.experienceComplete;
      const labLocked = isActionLocked("lab", candidate.user_id || "none") || state.experienceComplete;
      container.innerHTML = `
        <div class="two-col">
          <div class="panel mobile-match-card">
            <div class="section-head">
              <h3>心动星球</h3>
	              <span class="tag">慢慢了解</span>
            </div>
            ${best ? `
              <div class="card-head">
                <img src="${imagePath(candidate.user_id)}" alt="${escapeHtml(candidate.display_name)}" onerror="this.style.visibility='hidden'">
                <div>
                  <h4>${escapeHtml(candidate.display_name)} · ${escapeHtml(candidate.major || "")}</h4>
                  <div class="muted">${escapeHtml(candidate.campus || "")} / ${escapeHtml(candidate.relationship_goal || "")}</div>
                </div>
	                <div class="score-pill">${friendlyScore(best.final_score)}</div>
              </div>
              <p class="copy">${escapeHtml(exp.reason || "你们有共同兴趣和相近的相处期待。")}</p>
              ${tags(best.common_interests || [])}
              <div class="top-actions swipe-actions">
                <button id="skipMatch" class="tab-button reject-button" ${state.experienceComplete ? "disabled" : ""}>X</button>
                <button id="heartSwipe" class="tab-button active ${heartLocked || labLocked ? "locked" : ""}" ${heartLocked || labLocked ? "disabled" : ""}>${heartLocked || labLocked ? "已进入共鸣" : "心动 / 进入共鸣"}</button>
              </div>
            ` : `<div class="empty">暂无心动推荐</div>`}
          </div>
          <div class="panel">
            <h3>你们的进度</h3>
	            <p class="copy">这里只记录已经发生的互动。还没聊到的天数，不会提前剧透。</p>
            ${renderUserProgressChart()}
          </div>
        </div>
      `;
      const skip = document.getElementById("skipMatch");
      if (skip) {
        skip.addEventListener("click", () => {
          if (state.experienceComplete) return;
          state.chatMessages.push({from: "ai", speaker: "星球小助手", text: "已先跳过这位同学。你可以去雷达里按条件找人，或者切到闪电搭子找一个即时局。"});
          state.selectedAction = "match";
          renderUserExperience();
        });
      }
      const heart = document.getElementById("heartSwipe");
      if (heart) {
        heart.addEventListener("click", () => {
          if (heartLocked) return;
          state.selectedAction = "match";
          if (candidate.user_id) state.conversationUserId = candidate.user_id;
          state.dayTouched = true;
          lockAction("heart", candidate.user_id || "none");
          lockAction("lab", candidate.user_id || "none");
          state.userTab = "messages";
          state.experienceHeat = Math.max(0.1, Math.min(0.98, state.experienceHeat + 0.04));
	          state.chatMessages.push({from: "ai", speaker: "破冰小助手", text: ((exp.ice_breakers || [])[0]) || `已帮你和 ${candidate.display_name || "对方"} 打开共鸣实验室。先从一个轻松问题开始：如果周六下午完全自由，你最想怎么过？`});
          renderUserExperience();
        });
      }
      const lab = document.getElementById("openLab");
      if (lab) {
        lab.addEventListener("click", () => {
          if (labLocked) return;
          state.userTab = "messages";
          state.selectedAction = "chat";
          if (candidate.user_id) state.conversationUserId = candidate.user_id;
          state.dayTouched = true;
          lockAction("lab", candidate.user_id || "none");
	          state.chatMessages.push({from: "ai", speaker: "破冰小助手", text: ((exp.ice_breakers || [])[0]) || "先从一个轻松问题开始：如果周六下午完全自由，你最想怎么过？"});
          renderUserExperience();
        });
      }
    }

    function renderRadarPane(profile) {
      const tagsList = ["#185+", "#金融男", "#体育搭子", "#摄影大拿", "#会弹吉他", "#学习搭子", "#Citywalk", "#情绪稳定"];
      const q = state.radarQuery.trim().toLowerCase();
      const activeNeed = state.radarQuery || state.radarTag || "想找个会弹吉他的阳光学长";
      const trace = bestTraceForQuery(activeNeed);
      const filtered = (data.profiles || []).filter((item) => {
        if (item.user_id === profile.user_id) return false;
        const haystack = [
          item.display_name,
          item.major,
          item.campus,
          item.relationship_goal,
          ...(item.interests || []),
          ...(item.values || []),
          ...(item.personality_tags || [])
        ].join(" ").toLowerCase();
        const tagHit = !state.radarTag || haystack.includes(state.radarTag.replace("#", "").toLowerCase()) || state.radarTag === "#185+";
        return (!q || haystack.includes(q)) && tagHit;
      });
      const traceRows = trace ? (trace.top_k || []).filter((row) => row.user_id !== profile.user_id) : [];
      const displayRows = traceRows.length ? traceRows : filtered.map((item) => ({user_id: item.user_id, display_name: item.display_name, major: item.major, campus: item.campus, final_score: 0.52, matched_tags: (item.interests || []).slice(0, 3)}));
      document.getElementById("radarPane").innerHTML = `
        <div class="cosmic-panel">
          <div class="section-head">
            <h3>星际雷达</h3>
            <span class="muted">想找谁，直接说</span>
          </div>
          <div class="radar-search">
	            <input id="radarSearchInput" type="search" value="${escapeHtml(state.radarQuery)}" placeholder="比如：想找会弹吉他的人 / 想找学习搭子">
            <button id="radarSearchButton" class="tab-button active">搜索</button>
          </div>
          <div class="tag-row">
            ${tagsList.map((tag) => `<button class="quick-reply ${state.radarTag === tag ? "active" : ""}" data-radar-tag="${escapeHtml(tag)}">${escapeHtml(tag)}</button>`).join("")}
            <button class="quick-reply" data-radar-tag="">全部</button>
          </div>
          <div class="radar-visual-grid">
            <section class="panel">
              <div class="section-head">
                <h4>意图图谱</h4>
                <span class="muted">Text-to-Graph</span>
              </div>
              <p class="copy"><strong>当前需求：</strong>${escapeHtml(activeNeed)}</p>
              ${renderIntentGraph(trace)}
              ${renderIntentSummary(trace)}
            </section>
            <section class="panel">
              <div class="section-head">
                <h4>混合检索重排</h4>
                <span class="muted">${escapeHtml(trace ? trace.query_encoder : "none")} / ${escapeHtml(trace ? trace.status : "missing")}</span>
              </div>
              ${renderHybridTrace(trace, profile.user_id)}
            </section>
          </div>
	        <p class="copy"><strong>猜你想找：</strong>${escapeHtml(buildRadarIntent(state.radarQuery || state.radarTag))}</p>
        </div>
        <div class="poster-wall">
          ${displayRows.slice(0, 6).map((row) => {
            const item = byId[row.user_id] || row;
            return `
            <article class="card">
              <div class="card-head">
                <img src="${imagePath(item.user_id)}" alt="${escapeHtml(item.display_name)}" onerror="this.style.visibility='hidden'">
                <div>
                  <h4>${escapeHtml(buildPosterTitle(item))}</h4>
                  <div class="muted">${escapeHtml(item.major)} / ${escapeHtml(item.campus)}</div>
                </div>
              </div>
              <div class="score-pill">${fmt(row.final_score || 0.5)}</div>
              <p class="copy">${escapeHtml(item.ideal_partner || item.self_intro || "")}</p>
              ${tags((row.matched_tags || item.interests || []).slice(0, 4))}
		              <button class="tab-button active ${isActionLocked("radar", item.user_id) || state.experienceComplete ? "locked" : ""}" data-radar-chat="${escapeHtml(item.user_id)}" style="margin-top:10px" ${isActionLocked("radar", item.user_id) || state.experienceComplete ? "disabled" : ""}>${isActionLocked("radar", item.user_id) ? "已打开聊天" : "先聊一句"}</button>
            </article>
          `}).join("") || `<div class="empty">没有符合条件的寻人启事</div>`}
        </div>
      `;
      document.getElementById("radarSearchButton").addEventListener("click", () => {
        state.radarQuery = document.getElementById("radarSearchInput").value;
        renderUserExperience();
      });
      document.getElementById("radarSearchInput").addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          state.radarQuery = event.target.value;
          renderUserExperience();
        }
      });
      document.querySelectorAll("[data-radar-tag]").forEach((button) => {
        button.addEventListener("click", () => {
          state.radarTag = button.dataset.radarTag;
          renderUserExperience();
        });
      });
      document.querySelectorAll("[data-radar-chat]").forEach((button) => {
        button.addEventListener("click", () => {
          if (button.disabled) return;
          const target = byId[button.dataset.radarChat] || {};
          state.userTab = "messages";
          state.dayTouched = true;
          lockAction("radar", target.user_id || button.dataset.radarChat);
          switchConversation(
            profile,
            target,
	            `已帮你打开和 ${target.display_name || "对方"} 的聊天。先说你是从哪条启事看到 TA 的，会更自然。`,
	            "我看到你的消息了。可以先说说你想找什么样的搭子，时间和地点合适的话我愿意试试。"
          );
          renderUserExperience();
        });
      });
    }

    function buildRadarIntent(text) {
      if (!text) return "可以直接输入大白话，比如“找个周五能一起自习的人”。";
      const trace = bestTraceForQuery(text);
      const intent = trace && trace.intent;
      if (intent && (intent.explicit_intents || []).length) {
        return `显性需求：${(intent.explicit_intents || []).join("、")}；隐性意图：${(intent.inferred_intents || []).slice(0, 3).join("、")}`;
      }
      if (/吉他|音乐|弹/.test(text)) return "会音乐、愿意聊天、线下见面压力不大的人。";
      if (/学习|刷题|图书馆/.test(text)) return "想一起学习、时间能对上、地点适合安静见面的人。";
      if (/185|体育|健身|羽毛球/.test(text)) return "运动型、时间近、信用记录比较稳的人。";
      return "我会先按兴趣、时间、地点和相处边界帮你缩小范围。";
    }

    function friendlySceneReason(row, candidate) {
      const bits = [];
      if (Number(row.time_score) >= 0.8) bits.push("时间对得上");
      if (Number(row.location_score) >= 0.75) bits.push("离你不远");
      else bits.push("距离稍远，但可以当备选");
      if (Number(row.task_score) >= 0.75) bits.push("想做的事比较一致");
      if (Number(row.care_score) >= 0.6) bits.push("相处节奏会更温和");
      return `${candidate.display_name || "对方"}：${bits.join("，")}。`;
    }

    function buildPosterTitle(profile) {
      const interest = (profile.interests || [])[0] || "校园活动";
      const trait = (profile.personality_tags || [])[0] || "合拍";
      return `${trait}同学，想找${interest}搭子`;
    }

    function renderArchivePane(profile) {
      const governance = governanceById[profile.user_id] || {};
      const progressCount = state.experienceHistory.length;
      const evidenceRows = profileEvidenceByUser[profile.user_id] || [];
      const evidenceTags = [
        ...(profile.interests || []).slice(0, 3),
        ...(profile.values || []).slice(0, 3),
        ...state.experienceTags.slice(0, 3)
      ];
      const defaultEvidence = evidenceForTag(profile, evidenceTags[0]) || evidenceRows[0] || null;
      document.getElementById("archivePane").innerHTML = `
        <div class="archive-grid">
          <div class="cosmic-panel">
            <div class="profile-media">
              <img src="${imagePath(profile.user_id)}" alt="${escapeHtml(profile.display_name)}" onerror="this.style.visibility='hidden'">
              <div>
                <h3>${escapeHtml(profile.display_name)}</h3>
                <p>${escapeHtml(profile.school)} / ${escapeHtml(profile.major)} / ${escapeHtml(profile.grade)}</p>
	                <p>信用 ${escapeHtml(state.experienceCredit)} / 推荐曝光 ${fmt((governance.policy || {}).visibility_multiplier ?? 1)}</p>
              </div>
            </div>
            <p class="copy">${escapeHtml(profile.self_intro || "")}</p>
            <div class="tag-row">
              ${evidenceTags.map((tag) => `<button class="quick-reply" data-profile-evidence="${escapeHtml(tag)}">${escapeHtml(tag)}</button>`).join("")}
            </div>
            <div id="profileEvidence">${renderProfileEvidenceCard(defaultEvidence)}</div>
          </div>
          <div class="panel">
            <div class="section-head">
              <h3>记忆博物馆</h3>
	              <span class="muted">${state.experienceComplete ? "这一周的回顾" : "还在积累互动"}</span>
            </div>
            ${state.experienceComplete ? `
	              <p class="copy">这一周你们认真推进了 ${escapeHtml(progressCount)} 天，聊天热度到 ${Math.round(state.experienceHeat * 100)}%，最常出现的话题是 ${escapeHtml(state.experienceTags.slice(0, 3).join("、") || "共同兴趣")}。</p>
            ` : `
	              <p class="copy">周报还没到生成时间。现在只记录已经发生的事：完成 ${escapeHtml(progressCount)} 天，今天聊了 ${escapeHtml(state.dayChatCount)}/3 轮。</p>
            `}
            <div class="memory-strip">
              <div class="info-item"><span>聊天热度</span><strong>${Math.round(state.experienceHeat * 100)}%</strong></div>
              <div class="info-item"><span>新增标签</span><strong>${state.experienceTags.length}</strong></div>
              <div class="info-item"><span>信用分</span><strong>${state.experienceCredit}</strong></div>
            </div>
            ${renderUserProgressChart()}
          </div>
        </div>
      `;
      document.querySelectorAll("[data-profile-evidence]").forEach((button) => {
        button.addEventListener("click", () => {
          const tag = button.dataset.profileEvidence;
          document.getElementById("profileEvidence").innerHTML = renderProfileEvidenceCard(evidenceForTag(profile, tag));
        });
      });
    }

    function renderDayStrip() {
      document.getElementById("dayStrip").innerHTML = Array.from({length: 7}, (_, index) => {
        const day = index + 1;
        return `<div class="day-pill ${day === state.experienceDay ? "active" : ""}">Day<br>${day}</div>`;
      }).join("");
    }

    function renderActionGrid() {
      document.getElementById("actionGrid").innerHTML = experienceActions.map((action) => `
        <button class="action-button ${action.id === state.selectedAction ? "active" : ""} ${state.experienceComplete ? "locked" : ""}" data-action="${escapeHtml(action.id)}" ${state.experienceComplete ? "disabled" : ""}>
          <strong>${escapeHtml(action.label)}</strong>
          <span>${escapeHtml(action.desc)}</span>
        </button>
      `).join("");
      document.querySelectorAll("[data-action]").forEach((button) => {
        button.addEventListener("click", () => {
          if (state.experienceComplete) return;
          state.selectedAction = button.dataset.action;
          renderUserExperience();
        });
      });
    }

    function renderExperienceOutcome(profile) {
      const action = currentAction();
      const text = document.getElementById("experienceText").value.trim();
      const activeText = text || (state.lastDailyIntent && state.lastDailyIntent.raw_text) || "";
      const intent = text ? analyzeDailyIntent(text, action.id) : (state.lastDailyIntent || analyzeDailyIntent(activeText, action.id));
      const routedAction = experienceActions.find((item) => item.id === intent.route) || action;
      const result = buildExperienceResult(profile, routedAction, activeText, false, intent);
      const convo = currentConversation(profile);
      document.getElementById("experienceOutcome").innerHTML = `
        <div class="panel">
          <div class="section-head">
	            <h3>今天发生了什么</h3>
            <span class="tag">${state.experienceComplete ? "体验结束" : `Day ${state.experienceDay}`}</span>
          </div>
          ${renderDailyIntentCard(intent)}
          ${result.primary}
          ${renderLatestCounterpartFeedback(convo.candidate || {})}
        </div>
        <div class="panel">
          <div class="section-head">
	            <h3>下一步可以怎么走</h3>
	            <span class="muted">只放和你有关的提醒</span>
          </div>
          ${result.evidence}
        </div>
      `;
    }

    function renderExperienceTimeline() {
      document.getElementById("timelineCount").textContent = `${state.experienceHistory.length} 条进展`;
      document.getElementById("experienceTimeline").innerHTML = state.experienceHistory.length
        ? state.experienceHistory.map((item) => `
          <div class="timeline-item">
            <strong>Day ${escapeHtml(item.day)} · ${escapeHtml(item.action)}</strong>
            <p class="copy">${escapeHtml(item.summary)}</p>
          </div>
        `).join("")
        : `<div class="empty">还没有新的进展。选一个今天想做的事，再说一句你的想法。</div>`;
    }

    function initialChatMessages(profile) {
      const convo = currentConversation(profile);
      const candidate = convo.candidate || {};
      const exp = (convo.match && convo.match.explanation) || {};
      const opener = (exp.ice_breakers || [])[0] || "你们有一些共同兴趣，可以先从一个轻松问题开始。";
      return [
        {from: "ai", speaker: "星球小助手", text: `今天比较适合先和 ${candidate.display_name || "一位同学"} 聊聊。可以用这句开场：${opener}`},
        {from: "other", speaker: candidate.display_name || "对方", text: "嗨，我刚看到匹配理由，感觉共同点还挺具体的。你今天想先聊什么？"}
      ];
    }

    function renderChatPanel(profile) {
      const convo = currentConversation(profile);
      const candidate = convo.candidate || {};
      const best = convo.match;
      const exp = (best && best.explanation) || {};
      const iceBreakers = (exp.ice_breakers || []).slice(0, 2);
      const replies = Array.from(new Set([...iceBreakers, ...quickReplies])).slice(0, 6);
      const chatLocked = state.experienceComplete || state.dayChatCount >= 3;
      const latestFeedback = latestCounterpartFeedback();
      document.getElementById("chatPanel").innerHTML = `
        <div class="panel">
          <div class="section-head">
            <h3>和 ${escapeHtml(candidate.display_name || "推荐对象")} 聊天</h3>
	            <span class="muted">${state.experienceComplete ? "已结束，可以回看记录" : `今天还能聊 ${Math.max(0, 3 - state.dayChatCount)} 轮`}</span>
          </div>
          ${renderLatestCounterpartFeedback(candidate)}
          <div class="chat-window">
            ${state.chatMessages.map((message, index) => `
              <div class="message ${escapeHtml(message.from)} ${latestFeedback && latestFeedback.index === index ? "latest-feedback" : ""}">
                <strong>${escapeHtml(message.speaker)}</strong>
                ${escapeHtml(message.text)}
              </div>
            `).join("")}
          </div>
          <div class="quick-replies">
            ${replies.map((reply) => `<button class="quick-reply ${chatLocked ? "locked" : ""}" data-reply="${escapeHtml(reply)}" ${chatLocked ? "disabled" : ""}>${escapeHtml(reply)}</button>`).join("")}
          </div>
	          ${state.dayChatCount >= 3 && !state.experienceComplete ? `<div class="completion-banner">今天先聊到这里。点“推进今天”，让关系自然进入下一天。</div>` : ""}
        </div>
        <div class="panel">
          <div class="section-head">
	            <h3>小助手建议</h3>
	            <span class="muted">破冰、氛围、见面</span>
          </div>
          ${renderUserAssistantTip(profile, candidate, best)}
        </div>
      `;
      document.querySelectorAll("[data-reply]").forEach((button) => {
        button.addEventListener("click", () => sendChatMessage(button.dataset.reply));
      });
    }

    function renderUserAssistantTip(profile, candidate, best) {
      const exp = (best && best.explanation) || {};
      const risk = (exp.risk_notes || [])[0];
      const common = (best && best.common_interests || []).concat(best && best.common_values || []).slice(0, 4);
      if (state.experienceComplete) {
        return `
          <div class="completion-banner">
	            7 天已经走完了。现在可以回看聊天记录和这几天的变化。
          </div>
          <p class="copy">本周总结：你和 ${escapeHtml(candidate.display_name || "对方")} 的关系热度达到 ${Math.round(state.experienceHeat * 100)}%，画像新增 ${state.experienceTags.length} 个标签。</p>
        `;
      }
      return `
	        <p class="copy">可以先聊 ${escapeHtml(common.join("、") || "共同兴趣")}。别一上来问太私人的问题。</p>
	        <p class="copy">${risk ? `小提醒：${escapeHtml(risk)}` : "现在没有明显需要担心的点。"}</p>
	        <p class="copy">如果聊到见面，先选校内、人多、坐一会儿就能离开的地方。</p>
          ${renderChatRetrievalHint(profile)}
      `;
    }

    function chatRetrievalTraceForUser(profile) {
      const traces = data.chatRetrievalTraces || [];
      return traces.find((trace) => trace.user_id === profile.user_id) || traces[0] || null;
    }

    function fnvHash(text) {
      let hash = 2166136261;
      for (let i = 0; i < text.length; i += 1) {
        hash ^= text.charCodeAt(i);
        hash = Math.imul(hash, 16777619) >>> 0;
      }
      return hash >>> 0;
    }

    function browserChatEmbedding(text, dim = 128) {
      const vec = Array(dim).fill(0);
      const compact = String(text || "").toLowerCase().replace(/\s+/g, "");
      const grams = [];
      for (let i = 0; i < compact.length; i += 1) grams.push(compact.slice(i, i + 1));
      for (let i = 0; i < compact.length - 1; i += 1) grams.push(compact.slice(i, i + 2));
      for (let i = 0; i < compact.length - 2; i += 1) grams.push(compact.slice(i, i + 3));
      for (const gram of grams) {
        const hash = fnvHash(gram);
        const idx = hash % dim;
        vec[idx] += (hash & 1 ? 1 : -1) * (gram.length === 1 ? 0.45 : 0.7);
      }
      const norm = Math.sqrt(vec.reduce((sum, value) => sum + value * value, 0)) || 1;
      return vec.map((value) => value / norm);
    }

    function dotVector(a, b) {
      let sum = 0;
      for (let i = 0; i < Math.min(a.length, b.length); i += 1) sum += a[i] * b[i];
      return sum;
    }

    function normalizeReplySignature(text) {
      return String(text || "")
        .replace(/「[^」]{1,16}」/g, "「X」")
        .replace(/[0-9０-９]+/g, "N")
        .replace(/[，。！？、；：,.!?;:\\s]/g, "")
        .slice(0, 34);
    }

    function rememberGeneratedReply(reply, topic = "") {
      const signature = normalizeReplySignature(reply);
      if (signature) {
        state.recentReplySignatures = [signature, ...(state.recentReplySignatures || []).filter((item) => item !== signature)].slice(0, 8);
      }
      if (topic) {
        state.recentReplyTopics = [topic, ...(state.recentReplyTopics || []).filter((item) => item !== topic)].slice(0, 8);
      }
    }

    function pickFreshVariant(pool, seed, fallback) {
      const variants = (pool || []).filter(Boolean);
      if (!variants.length) return fallback || "这个问题挺好，我想先听听你的想法。";
      const used = state.recentReplySignatures || [];
      for (let offset = 0; offset < variants.length; offset += 1) {
        const reply = variants[(seed + offset) % variants.length];
        if (!used.includes(normalizeReplySignature(reply))) return reply;
      }
      return fallback || variants[seed % variants.length];
    }

    function pickFocusTopic(text, profile, candidate, best) {
      const known = [
        ...(best && best.common_interests || []),
        ...(profile.interests || []),
        ...(candidate.interests || []),
        ...(best && best.common_dates || [])
      ].filter(Boolean);
      const unique = Array.from(new Set(known));
      const direct = unique.find((topic) => topic && String(text || "").includes(topic));
      if (direct) return direct;
      if (/剧本|本格|推理/.test(text)) return "剧本杀";
      if (/电影|片子|观影/.test(text)) return "电影";
      if (/音乐|歌单|livehouse|Livehouse/.test(text)) return "音乐";
      if (/看展|展览|美术馆|博物馆/.test(text)) return "看展";
      if (/拍照|摄影/.test(text)) return "摄影";
      if (/羽毛球|篮球|足球|跑步|健身|运动/.test(text)) return "运动";
      if (/饭|吃|食堂|火锅|冒菜|咖啡/.test(text)) return "吃饭";
      return unique[0] || "";
    }

    function buildConversationRepairReply(text, topic, candidate) {
      if (topic === "剧本杀") {
        return "换个问法吧：如果真约剧本杀，你会更想玩轻推理、欢乐本，还是沉浸一点的本？我也想先避开太恐怖或太长的。";
      }
      if (/活动|推荐/.test(text)) {
        return `我不太想随便编一个活动名。我们可以先定${topic || "方向"}的偏好、时长和雷点，再去雷达里找合适的人或局。`;
      }
      return `这个点我想换个角度问：你对${topic || "这件事"}最在意的是过程舒服，还是结果明确？`;
    }

    function chatRagDocuments(profile, candidate, best) {
      const exp = (best && best.explanation) || {};
      const profileDoc = {
        doc_id: `profile_context_${profile.user_id}`,
        source: "profile_and_match_context",
        title: `${profile.user_id} 画像和匹配上下文`,
        text: [
          profile.self_intro || "",
          profile.ideal_partner || "",
          `兴趣：${(profile.interests || []).join("、")}`,
          `价值观：${(profile.values || []).join("、")}`,
          `关系目标：${profile.relationship_goal || ""}`,
          `沟通风格：${profile.communication_style || ""}`,
          `匹配对象：${candidate.display_name || ""}`,
          `共同兴趣：${(best && best.common_interests || []).join("、")}`,
          `共同价值观：${(best && best.common_values || []).join("、")}`,
          `推荐理由：${exp.reason || ""}`,
          ...(exp.ice_breakers || [])
        ].join("\\n"),
        suggestion: (exp.ice_breakers || [])[0] || "先从一个轻松问题开始。",
        tags: ["画像", "GraphRAG", "匹配理由"]
      };
      return [profileDoc, ...chatRagKnowledgeBase];
    }

    function retrieveChatRag(query, profile, candidate, best) {
      const dim = 128;
      const queryVec = browserChatEmbedding(query, dim);
      const docs = chatRagDocuments(profile, candidate, best).map((doc) => {
        const docVec = browserChatEmbedding(`${doc.text}\n${doc.suggestion}\n${(doc.tags || []).join(" ")}`, dim);
        let score = dotVector(queryVec, docVec);
        const haystack = `${doc.text}${doc.suggestion}${(doc.tags || []).join("")}`;
        if (/图书馆|咖啡|周五|见面|约/.test(query) && /首约|安全|图书馆|学习/.test(haystack)) score += 0.18;
        if (/累|焦虑|难过|没胃口|压力/.test(query) && /低能量|照顾|情绪/.test(haystack)) score += 0.24;
        if (/剧本杀|喜欢|推荐|活动|音乐|电影|展/.test(query) && /活动推荐|防幻觉/.test(haystack)) score += 0.28;
        if (/剧本杀|音乐|电影|展|摄影/.test(query) && /共同兴趣|破冰|画像/.test(haystack)) score += 0.12;
        if (/羽毛球|运动|跑步|健身|篮球|足球/.test(query) && /运动搭子|自动成群|信用/.test(haystack)) score += 0.24;
        if (/饭|吃|食堂|火锅|冒菜|咖啡|没胃口/.test(query) && /饭搭子|地点|照顾信号/.test(haystack)) score += 0.22;
        if (/拍照|Citywalk|散步|看展|走走/.test(query) && /摄影|Citywalk|低压力/.test(haystack)) score += 0.22;
        if (/考试|论文|ddl|绩点|复习|刷题/.test(query) && /学业压力|小目标|陪伴/.test(haystack)) score += 0.23;
        if (/反馈|见后|不舒服|还不错|下次/.test(query) && /见后反馈|记忆博物馆|知识更新/.test(haystack)) score += 0.24;
        return {...doc, score};
      });
      docs.sort((a, b) => Number(b.score) - Number(a.score));
      const topK = docs.slice(0, 3).map((doc, index) => ({
        rank: index + 1,
        doc_id: doc.doc_id,
        source: doc.source,
        title: doc.title,
        suggestion: doc.suggestion,
        tags: doc.tags || [],
        score: Number(doc.score).toFixed(4)
      }));
      return {
        trace_id: `CHAT_REALTIME_${Date.now()}`,
        user_id: profile.user_id,
        candidate_id: candidate.user_id || "",
        query,
        retrieval_method: "browser_hash_embedding + inner_product_top_k",
        query_embedding_dim: dim,
        top_k: topK,
        status: "realtime_vector_rag"
      };
    }

    function buildRagReply(text, profile, candidate, best) {
      const trace = retrieveChatRag(text, profile, candidate, best);
      const top = (trace.top_k || [])[0] || {};
      const topic = pickFocusTopic(text, profile, candidate, best);
      let reply = composeContextualReply(text, top, profile, candidate, best);
      if (/见面|约|线下|咖啡/.test(text) && !/校内|人多|一小时|短一点/.test(reply)) {
        reply += " 第一次可以先选校内、人多、坐一会儿就能结束的地方。";
      }
      if (/累|焦虑|难过|没胃口|压力/.test(text) && !/不用强行|轻松/.test(reply)) {
        reply += " 如果今天状态一般，我们就轻松聊几句，不急着推进。";
      }
      if ((state.recentReplySignatures || []).includes(normalizeReplySignature(reply))) {
        reply = buildConversationRepairReply(text, topic, candidate);
      }
      trace.final_reply = reply;
      trace.focus_topic = topic || "";
      state.lastChatRag = trace;
      rememberGeneratedReply(reply, topic);
      return reply;
    }

    function composeContextualReply(text, top, profile, candidate, best) {
      const commonInterests = (best && best.common_interests || []).slice(0, 2);
      const commonValues = (best && best.common_values || []).slice(0, 2);
      const style = candidate.communication_style || "舒服的节奏";
      const focusTopic = pickFocusTopic(text, profile, candidate, best);
      const topicLabel = focusTopic || commonInterests[0] || "这个话题";
      const activityVariants = focusTopic === "剧本杀" ? [
        "剧本杀我不会硬推荐一个不存在的活动。可以先看你偏好：轻推理、欢乐本、沉浸本，还是完全不恐怖的本？",
        "如果聊剧本杀，我更想先知道你的雷点：恐怖、情感、硬核推理、超长时长，哪个最不能接受？",
        "剧本杀可以作为破冰，但别一上来约太重的局。先从 3 小时以内、复盘友好的本开始会轻松点。",
        "你玩剧本杀更喜欢推理位、气氛位，还是安静观察？这个比问“有没有推荐”更容易聊出真实偏好。",
        "如果我们真找一场剧本杀，我会先排除恐怖和超长本，再看有没有轻量推理局。你能接受这个方向吗？"
      ] : [
        `我不太想随便编${topicLabel}的活动名。我们可以先定偏好、时长和雷点，再去雷达里找合适的人或局。`,
        `${topicLabel}这个方向可以聊，但我更想先知道你喜欢轻松一点，还是安排明确一点。`,
        `如果从${topicLabel}开始，我会先问你最想体验哪一类，而不是直接丢一个泛泛的推荐。`
      ];
      const variants = {
        icebreaker_common_interest: [
          `${topicLabel}这个共同点可以聊，但我想问具体一点：你更喜欢哪种风格，或者有没有明确雷点？`,
          `这个话题我接得上。我们先不聊太重的，你可以讲一个最近让你觉得有意思的细节。`,
          `我不想只复述“我们都喜欢${topicLabel}”。我更想知道你为什么会喜欢它。`
        ],
        activity_specific_reply: activityVariants,
        date_low_pressure: [
          "可以，但我更喜欢第一次短一点。校内、人多、能自然结束的地方会让我更安心。",
          "我愿意试试。我们先约 40 分钟左右，如果聊得舒服再继续，不用一开始就安排太满。"
        ],
        study_buddy_reply: [
          "可以，我也想找人一起学。我们先定一个小时，各自安静推进，结束后再聊两句。",
          "听起来挺合适。你想偏刷题还是偏复习？我可以配合一个不打扰的节奏。"
        ],
        care_needed_reply: [
          "那今天先别硬撑社交。我们可以轻松聊几句，或者我陪你把今天最烦的一件事拆小一点。",
          "我懂这种状态。今天不用强行热闹，我们慢慢说，哪怕只聊一点也可以。"
        ],
        boundary_respect: [
          `我们按${style}来就好，不用一下子把节奏拉满。你愿意说多少就说多少。`,
          "我不会连环追问。我们可以先停在舒服的范围里，慢一点也没关系。"
        ],
        sports_group_reply: [
          "可以，我也想动一动。先定一个轻量强度吧，别一上来就太卷；时间合适的话还能顺手拉个小局。",
          "运动局可以呀。你偏想认真打还是放松活动一下？我比较想先把时间和场地定清楚。"
        ],
        meal_buddy_reply: [
          "可以呀。我们选近一点、人多一点的地方，口味别太冒险；如果你今天状态一般，也可以换成散步。",
          "饭搭子可以，但我想先对齐一下口味和预算。你今天想吃清淡点还是正常吃？"
        ],
        photo_walk_reply: [
          "这个我愿意。边走边聊会比坐着尬聊轻松一点，也可以顺手拍几张照片。",
          "Citywalk 或拍照都挺适合第一次轻松见面。我们可以选一条短路线，不用安排太满。"
        ],
        exam_pressure_reply: [
          "辛苦了。我们可以先定一个很小的目标，比如 40 分钟只做一件事，做完就休息。",
          "考试压力大的时候别硬聊深话题。我们可以先互相报个进度，陪着把今天这点做完。"
        ],
        feedback_after_date: [
          "这次感受可以慢慢说，不用立刻下结论。舒服和不舒服的点都值得记下来。",
          "我想听真实感受。如果哪里让你不舒服，之后我们就避开；如果还不错，也可以慢慢继续。"
        ]
      };
      const pool = variants[top.doc_id] || [top.suggestion || buildPresetReply(text, profile, candidate, best)];
      const seed = fnvHash(`${text}|${top.doc_id || ""}|${candidate.user_id || ""}`);
      let reply = pickFreshVariant(pool, seed, buildConversationRepairReply(text, focusTopic, candidate));
      if (commonValues.length && /关系|继续|认真|舒服/.test(text)) {
        reply += ` 我觉得我们至少在${commonValues.join("、")}上挺接近，可以慢慢验证。`;
      }
      return reply;
    }

    function renderChatRetrievalHint(profile) {
      const trace = state.lastChatRag || chatRetrievalTraceForUser(profile);
      if (!trace) {
        return `<div class="completion-banner"><strong>AI 建议来源：</strong>等待用户输入后实时检索。</div>`;
      }
      const docs = trace.top_k || [];
      return `
        <div class="completion-banner">
          <strong>AI 建议来源：</strong>${state.lastChatRag ? "刚才这句回复由实时向量检索生成。" : "参考了预生成聊天检索 trace。"} 方法：${escapeHtml(trace.retrieval_method || "vector_top_k")}
          <div class="tag-row" style="margin-top:8px">
            ${docs.slice(0, 3).map((doc) => `<span class="tag blue">#${escapeHtml(doc.rank)} ${escapeHtml(doc.title || doc.source)} ${escapeHtml(doc.score || "")}</span>`).join("")}
          </div>
          ${state.lastChatRag ? `<p class="copy" style="margin-bottom:0"><strong>检索 query：</strong>${escapeHtml(trace.query)}</p>` : ""}
        </div>
      `;
    }

    function sendChatMessage(text) {
      if (state.experienceComplete) return;
      if (state.dayChatCount >= 3) {
        if (state.chatLimitNoticeDay !== state.experienceDay) {
          state.chatMessages.push({from: "ai", speaker: "星球小助手", text: "今天先聊到这里就好。点“推进今天”，明天再继续会更自然。"});
          state.chatLimitNoticeDay = state.experienceDay;
        }
        renderUserExperience();
        return;
      }
      const profile = byId[state.experienceUserId] || {};
      const convo = currentConversation(profile);
      const candidate = convo.candidate || {};
      const best = convo.match;
      const clean = String(text || "").trim();
      if (!clean) return;
      state.chatMessages.push({from: "me", speaker: "我", text: clean});
      state.chatMessages.push({from: "other", speaker: candidate.display_name || "对方", text: buildRagReply(clean, profile, candidate, best), feedback: true});
      const inferred = inferTagsFromText(clean);
      state.experienceTags = Array.from(new Set([...state.experienceTags, ...inferred])).slice(0, 8);
      state.experienceHeat = Math.max(0.1, Math.min(0.98, state.experienceHeat + 0.025 + (inferred.length ? 0.01 : 0)));
      state.dayChatCount += 1;
      state.dayTouched = true;
      state.chatLimitNoticeDay = 0;
      document.getElementById("experienceText").value = "";
      renderUserExperience();
    }

    function buildPresetReply(text, profile, candidate, best) {
      const interests = (best && best.common_interests || []).slice(0, 2);
      if (/图书馆|学习|刷题|考试|论文/.test(text)) {
        return "可以，我这周也想找人一起学。我们可以先约一小时，结束后再决定要不要继续。";
      }
      if (/饭|吃|食堂|火锅|咖啡/.test(text)) {
        return "听起来不错。要不选人多一点的地方，边吃边聊比较自然。";
      }
      if (/压力|累|焦虑|难过/.test(text)) {
        return "那今天先不用强行社交，我们可以轻松聊几句。你想吐槽还是想转移注意力？";
      }
      if (/见面|约|线下|咖啡/.test(text)) {
        return "可以，但我更倾向第一次短一点，选校内咖啡店或者图书馆旁边会安心些。";
      }
      if (/剧本|推理|本格/.test(text)) {
        return "剧本杀这个话题可以聊具体点。你更喜欢轻推理、欢乐本、沉浸本，还是复盘很强的硬核本？";
      }
      if (/电影|音乐|展|旅行/.test(text)) {
        return `${interests.length ? `我们可以从${interests[0]}聊起。` : "这个话题挺好接。"}你更在意活动本身好玩，还是两个人聊天舒服？`;
      }
      return "这个问题挺好，我想先听听你的想法。我们可以慢慢聊，不用一下子把节奏拉太满。";
    }

    function updateExperienceControls() {
      const input = document.getElementById("experienceText");
      const submit = document.getElementById("submitExperience");
      const banner = document.getElementById("completionBanner");
      const messageInput = document.getElementById("messageText");
      const messageSubmit = document.getElementById("sendMessageButton");
      const chatLocked = state.experienceComplete || state.dayChatCount >= 3;
      input.disabled = state.experienceComplete;
      submit.disabled = state.experienceComplete;
      submit.classList.toggle("locked", state.experienceComplete);
      messageInput.disabled = chatLocked;
      messageInput.placeholder = chatLocked ? "今天先聊到这里，推进到下一天后再继续" : "自己输入一句话，例如：我们周五去图书馆旁边喝咖啡吗？";
      messageSubmit.disabled = chatLocked;
      messageSubmit.classList.toggle("locked", chatLocked);
      banner.innerHTML = state.experienceComplete
	        ? `<div class="completion-banner"><strong>7 天体验已结束。</strong> 这段互动已经收尾，可以回看记录和周报。</div>`
        : "";
      document.getElementById("dayGuardText").textContent = state.experienceComplete
	        ? "这 7 天已经结束，现在是回看状态"
	        : "每天记录一个主线，其它页面照常可用";
    }

    function currentAction() {
      return experienceActions.find((action) => action.id === state.selectedAction) || experienceActions[0];
    }

    function actionLockKey(kind, id = "") {
      return `${state.experienceDay}:${kind}:${id}`;
    }

    function isActionLocked(kind, id = "") {
      return Boolean(state.actionLocks[actionLockKey(kind, id)]);
    }

    function lockAction(kind, id = "") {
      state.actionLocks[actionLockKey(kind, id)] = true;
    }

    function bestMatchForUser(userId) {
      return (matchesByUser[userId] || []).slice().sort((a, b) => Number(b.final_score) - Number(a.final_score))[0] || null;
    }

    function currentConversation(profile) {
      const best = bestMatchForUser(profile.user_id);
      const candidateId = state.conversationUserId || (best && best.candidate_id) || "";
      const candidate = byId[candidateId] || (best ? byId[best.candidate_id] || {} : {});
      const match = candidate.user_id
        ? ((matchesByUser[profile.user_id] || []).find((row) => row.candidate_id === candidate.user_id) || best)
        : best;
      return {candidate, match};
    }

    function latestCounterpartFeedback() {
      let hasUserMessage = false;
      for (let index = 0; index < state.chatMessages.length; index += 1) {
        if (state.chatMessages[index].from === "me") hasUserMessage = true;
      }
      for (let index = state.chatMessages.length - 1; index >= 0; index -= 1) {
        const message = state.chatMessages[index];
        if (message.from === "other" && (message.feedback || hasUserMessage)) {
          return {message, index};
        }
      }
      return null;
    }

    function renderLatestCounterpartFeedback(candidate) {
      const latest = latestCounterpartFeedback();
      if (!latest) {
        return `
          <aside class="counterpart-card is-empty">
            <div class="section-head">
	              <h4>对方刚刚说</h4>
              <span class="muted">等待互动</span>
            </div>
	            <p class="reply-line muted">你发出第一句话，或加入一个搭子局后，这里会显示对方的回应。</p>
          </aside>
        `;
      }
      const speaker = latest.message.speaker || candidate.display_name || "对方";
      return `
        <aside class="counterpart-card">
          <div class="section-head">
	            <h4>${escapeHtml(speaker)} 刚刚说</h4>
            <span class="tag">已收到</span>
          </div>
          <p class="reply-line">${escapeHtml(latest.message.text)}</p>
        </aside>
      `;
    }

    function switchConversation(profile, target, intro, reply) {
      const candidate = target || {};
      if (candidate.user_id) state.conversationUserId = candidate.user_id;
      state.chatMessages = [
		        {from: "ai", speaker: "星球小助手", text: intro},
        {from: "other", speaker: candidate.display_name || "对方", text: reply, feedback: true}
      ];
      state.lastChatRag = null;
    }

    function sceneForUser(userId) {
      return (data.sceneRequests || []).find((request) => request.requester_id === userId) || (data.sceneRequests || [])[0] || null;
    }

    function dynamicForUser(userId) {
      return (data.relationshipDynamics || []).find((item) => item.user_id === userId || item.candidate_id === userId) || (data.relationshipDynamics || [])[0] || null;
    }

    function hasUserProgress() {
      return (
        state.experienceHistory.length > 0 ||
        state.dayChatCount > 0 ||
        state.dayTouched
      );
    }

    function userProgressPoints() {
      const completed = state.experienceHistory
        .slice()
        .reverse()
        .map((item, index) => ({
          day: item.day,
          heat: Number(item.heat) || Math.min(0.92, 0.34 + (index + 1) * 0.07),
        }));
      if (!state.experienceComplete && (state.dayChatCount > 0 || state.dayTouched)) {
        completed.push({day: state.experienceDay, heat: state.experienceHeat});
      }
      return completed;
    }

    function renderUserProgressChart() {
      if (!hasUserProgress()) {
        return `
          <div class="empty">
	            还没有开始互动。先心动一下、进破冰聊天，或者在消息页发出第一句话，这里才会出现进度。
          </div>
        `;
      }
      const points = userProgressPoints();
      return `
        ${heatChart(points)}
	        <p class="copy muted">已经记录 ${escapeHtml(points.length)} 个进展点；完整周报会在第 7 天后出现。</p>
      `;
    }

    function dateForUser(userId) {
      return (data.dateContexts || []).find((item) => item.user_id === userId || item.candidate_id === userId) || (data.dateContexts || [])[0] || null;
    }

    function inferTagsFromText(text) {
      const rules = [
        [["饭", "吃", "食堂", "火锅", "咖啡"], "饭搭子"],
        [["图书馆", "学习", "刷题", "考试", "论文"], "学习搭子"],
        [["压力", "累", "焦虑", "难过", "没胃口", "烦"], "需要照顾型陪伴"],
        [["运动", "羽毛球", "跑步", "健身"], "运动搭子"],
        [["电影", "音乐", "展", "剧本", "拍照", "Citywalk"], "文艺共鸣"],
        [["见面", "约", "线下"], "愿意线下推进"],
        [["反馈", "感觉", "不舒服", "还不错"], "见后反馈"]
      ];
      const found = [];
      for (const [keywords, tag] of rules) {
        if (keywords.some((keyword) => text.includes(keyword))) found.push(tag);
      }
      return found;
    }

    function analyzeDailyIntent(text, fallbackActionId = "interview") {
      const value = String(text || "").trim();
      const tagsFound = inferTagsFromText(value);
      const scores = {
        interview: 0.2,
        match: 0,
        scene: 0,
        chat: 0,
        date: 0,
        feedback: 0
      };
      const reasons = [];
      const routeEffects = [];
      if (/吃|饭|食堂|火锅|咖啡|运动|羽毛球|跑步|健身|搭子|自习|学习|刷题|图书馆|拍照|Citywalk/.test(value)) {
        scores.scene += 0.72;
        reasons.push("识别到具体任务/搭子需求");
        routeEffects.push("雷达会优先看任务、时间和地点匹配");
      }
      if (/见面|约|线下|首约|咖啡/.test(value)) {
        scores.date += 0.78;
        reasons.push("识别到线下推进意图");
        routeEffects.push("首约策划会检查地点安全和低压力时长");
      }
      if (/聊|破冰|话题|怎么说|开场|回复|尴尬/.test(value)) {
        scores.chat += 0.68;
        reasons.push("识别到聊天/破冰需求");
        routeEffects.push("消息页会用实时 RAG 生成回复");
      }
      if (/累|压力|焦虑|难过|没胃口|烦|不想/.test(value)) {
        scores.chat += 0.5;
        scores.scene += 0.28;
        reasons.push("识别到低能量或照顾信号");
        routeEffects.push("推荐会偏向温和陪伴，避免强推重口味和高压力见面");
      }
      if (/推荐|心动|合适|对象|喜欢|看看谁/.test(value)) {
        scores.match += 0.66;
        reasons.push("识别到推荐浏览意图");
        routeEffects.push("星球会展示匹配理由和破冰入口");
      }
      if (/反馈|见后|感觉|不舒服|还不错|下次/.test(value)) {
        scores.feedback += 0.75;
        reasons.push("识别到见后反馈");
        routeEffects.push("档案会记录知识更新和信用反馈");
      }
      if (!value) {
        scores[fallbackActionId] += 0.5;
        reasons.push("未输入具体内容，沿用当前选择");
      }
      scores[fallbackActionId] = (scores[fallbackActionId] || 0) + 0.18;
      let route = fallbackActionId;
      for (const [key, score] of Object.entries(scores)) {
        if (score > (scores[route] || 0)) route = key;
      }
      const action = experienceActions.find((item) => item.id === route) || experienceActions[0];
      const routeTab = route === "scene" ? "radar" : route === "chat" ? "messages" : route === "date" ? "messages" : route === "feedback" ? "archive" : "planet";
      const routeMode = route === "scene" ? "lightning" : "love";
      return {
        raw_text: value,
        route,
        route_label: action.label,
        route_tab: routeTab,
        route_mode: routeMode,
        confidence: Math.max(0.52, Math.min(0.96, scores[route] || 0.52)),
        tags: tagsFound,
        reasons: reasons.length ? reasons : ["作为今日状态更新写入档案"],
        effects: routeEffects.length ? routeEffects : ["灵魂卡片会记录今天的状态"],
        scores
      };
    }

    function renderDailyIntentCard(intent) {
      if (!intent) {
        return `<div class="completion-banner">说一句今天想做的事，系统会自动判断是找搭子、破冰、首约策划还是记录状态。</div>`;
      }
      return `
        <div class="completion-banner">
          <strong>今日意图：</strong>${escapeHtml(intent.route_label)} / 置信度 ${Math.round(Number(intent.confidence || 0) * 100)}%
          <div class="tag-row" style="margin-top:8px">
            ${(intent.tags || []).map((tag) => `<span class="tag blue">${escapeHtml(tag)}</span>`).join("") || `<span class="tag">状态记录</span>`}
          </div>
          <p class="copy" style="margin-bottom:0"><strong>为什么：</strong>${escapeHtml((intent.reasons || []).join("；"))}</p>
          <p class="copy" style="margin-bottom:0"><strong>会影响：</strong>${escapeHtml((intent.effects || []).join("；"))}</p>
        </div>
      `;
    }

    function submitExperienceAction() {
      if (state.experienceComplete) return;
      const profile = byId[state.experienceUserId] || {};
      const selected = currentAction();
      const text = document.getElementById("experienceText").value.trim() || "今天想继续了解对方，也看看有没有合适的校园活动。";
      const intent = analyzeDailyIntent(text, selected.id);
      const action = experienceActions.find((item) => item.id === intent.route) || selected;
      state.selectedAction = action.id;
      state.lastDailyIntent = intent;
      state.userTab = intent.route_tab || state.userTab;
      state.planetMode = intent.route_mode || state.planetMode;
      if (intent.route === "scene") {
        state.radarQuery = text;
      }
      const inferred = inferTagsFromText(text);
      const textBoost = inferred.includes("需要照顾型陪伴") ? 0.02 : 0;
      const result = buildExperienceResult(profile, action, text, true, intent);
      const convo = currentConversation(profile);
      const best = convo.match;
      const candidate = convo.candidate || {};
      if (text) {
        state.chatMessages.push({from: "me", speaker: "我", text});
        state.chatMessages.push({from: "other", speaker: candidate.display_name || "对方", text: buildRagReply(text, profile, candidate, best), feedback: true});
        state.chatMessages.push({from: "ai", speaker: "星球小助手", text: result.assistant || "我先把今天的互动记下来了，下一步会按这个节奏来。"});
      }
      state.experienceHeat = Math.max(0.1, Math.min(0.98, state.experienceHeat + action.deltaHeat + textBoost));
      state.experienceCredit = Math.max(0, Math.min(100, state.experienceCredit + action.deltaCredit));
      state.experienceTags = Array.from(new Set([...state.experienceTags, ...inferred])).slice(0, 8);
      state.experienceHistory.unshift({
        day: state.experienceDay,
        action: action.label,
        course: action.course,
        summary: `${result.summary}（${intent.reasons.join("；")}）`,
        heat: state.experienceHeat,
        credit: state.experienceCredit
      });
      if (state.experienceDay >= 7) {
        state.experienceComplete = true;
        state.dayTouched = false;
      } else {
        state.experienceDay += 1;
        state.dayChatCount = 0;
        state.dayTouched = false;
        state.chatLimitNoticeDay = 0;
      }
      document.getElementById("experienceText").value = "";
      renderUserExperience();
    }

    function buildExperienceResult(profile, action, text, committed, intent = null) {
      const topMatch = bestMatchForUser(profile.user_id);
      const convo = currentConversation(profile);
      const best = action.id === "match" ? topMatch : (convo.match || topMatch);
      const candidate = action.id === "match" ? (topMatch ? byId[topMatch.candidate_id] || {} : {}) : (convo.candidate || {});
      const scene = sceneForUser(profile.user_id);
      const sceneRows = scene ? (sceneMatchesByRequest[scene.request_id] || []) : [];
      const datePlan = dateForUser(profile.user_id);
      const governance = governanceById[profile.user_id] || {};
      const inferred = inferTagsFromText(text);
      const exp = (best && best.explanation) || {};
      const inputNote = text ? `<p class="copy"><strong>你说：</strong>${escapeHtml(text)}</p>` : `<p class="copy muted">可以先说一句今天的想法。</p>`;
      const intentNote = "";

      if (action.id === "interview") {
        const extracted = inferred.length ? inferred : (profile.values || []).slice(0, 3);
        return {
	          summary: `今天多了解了你一点：${extracted.join("、") || "沟通节奏更清楚了"}。`,
	          assistant: `我先记下：${extracted.join("、") || "真诚、边界感、舒服的节奏"}。后面的推荐会更贴近你现在的状态。`,
          primary: `
            ${inputNote}
	            <p class="copy">今天的想法已经放进你的灵魂卡片里，之后推荐会更贴近你真实的状态。</p>
            ${tags(extracted, "blue")}
          `,
	          evidence: `
              ${intentNote}
		            <p class="copy"><strong>下一步：</strong>可以去看今日推荐，也可以直接挑一句轻松话题开始聊。</p>
		            <p class="copy"><strong>放心：</strong>这里只显示和你自己有关的变化，不会把别人的后台信息拿给你看。</p>
	          `
        };
      }
      if (action.id === "match") {
        return {
	          summary: best ? `你看了 ${candidate.display_name} 的推荐卡片。` : "今天暂时没有新的心动推荐。",
	          assistant: best ? `你和 ${candidate.display_name} 有几个共同点。先从共同兴趣聊起，别一上来问太重的问题。` : "今天先不用勉强，可以去找个轻量搭子。",
          primary: best ? `
            <div class="card-head">
              <img src="${imagePath(candidate.user_id)}" alt="${escapeHtml(candidate.display_name)}" onerror="this.style.visibility='hidden'">
              <div>
                <h4>${escapeHtml(candidate.display_name)} · ${escapeHtml(candidate.major || "")}</h4>
                <div class="muted">${escapeHtml(candidate.campus || "")} / ${escapeHtml(candidate.relationship_goal || "")}</div>
              </div>
	              <div class="score-pill">${friendlyScore(best.final_score)}</div>
            </div>
            <p class="copy">${escapeHtml(exp.reason || "你们有一些共同兴趣和相近的相处期待。")}</p>
            ${tags(best.common_interests || [])}
          ` : `<div class="empty">暂无候选</div>`,
	          evidence: `
              ${intentNote}
		            <p class="copy"><strong>可以这样开场：</strong>${escapeHtml(((exp.ice_breakers || [])[0]) || "我看到我们有共同兴趣，想听听你最近有什么推荐。")}</p>
		            <p class="copy"><strong>小提醒：</strong>${escapeHtml(((exp.risk_notes || [])[0]) || "先从轻松话题开始，保持边界感。")}</p>
	          `
        };
      }
      if (action.id === "scene") {
        const topCandidates = sceneRows.slice(0, 3).map((row) => byId[row.candidate_id]?.display_name || row.candidate_id).join("、");
        return {
	          summary: scene ? `你发起了一个搭子局。` : "你发起了一个搭子局。",
	          assistant: scene ? `我会优先找同校区、时间合适、地点更安全的人。现在这个地点风险是 ${scene.safety_context && scene.safety_context.risk_level}。` : "我会优先找时间和地点都合适的人。",
          primary: scene ? `
            ${inputNote}
	            <p class="copy"><strong>你发出的内容：</strong>${escapeHtml(scene.text)}</p>
            <div class="kv">
              <span>地点</span><strong>${escapeHtml(scene.location && scene.location.name)}</strong>
              <span>时间</span><strong>${escapeHtml(scene.target_time_slot)}</strong>
              <span>风险</span><strong class="risk-${escapeHtml(scene.safety_context && scene.safety_context.risk_level)}">${escapeHtml(scene.safety_context && scene.safety_context.risk_level)}</strong>
            </div>
          ` : `<div class="empty">暂无任务</div>`,
	          evidence: `
              ${intentNote}
		            <p class="copy"><strong>系统动作：</strong>已把这句话写入雷达搜索，进入闪电搭子视图后会按这个需求看候选。</p>
                <p class="copy"><strong>可以先看看：</strong>${escapeHtml(topCandidates || "暂无")}</p>
		            <p class="copy"><strong>见面提醒：</strong>${escapeHtml((scene && scene.safety_context && scene.safety_context.notes || []).join("；") || "第一次见面建议选择校内、人流较高的地点。")}</p>
	          `
        };
      }
      if (action.id === "chat") {
        const ice = exp.ice_breakers || [];
        return {
	          summary: `你准备开始破冰，聊天热度会升到 ${Math.round((state.experienceHeat + action.deltaHeat) * 100)}% 左右。`,
	          assistant: `问题可以具体一点，比如：${ice[0] || "最近有没有一个让你觉得放松的校园角落？"}`,
          primary: `
            ${inputNote}
	            <p class="copy"><strong>可以这样问：</strong>${escapeHtml(ice[0] || "从共同兴趣开始，问一个具体但不冒犯的问题。")}</p>
            ${renderUserProgressChart()}
          `,
	          evidence: `
              ${intentNote}
		            <p class="copy"><strong>现在的氛围：</strong>${Math.round(state.experienceHeat * 100)}%，适合继续轻松聊。</p>
		            <p class="copy"><strong>别着急：</strong>不要连续追问隐私，也不要催回复。</p>
	          `
        };
      }
      if (action.id === "date") {
        const location = (datePlan && datePlan.location) || {};
        const risk = (datePlan && datePlan.risk_assessment) || {};
        return {
	          summary: datePlan ? `你准备把第一次见面放在 ${location.name}。` : "你准备线下见面了。",
	          assistant: datePlan ? `第一次见面建议 30-60 分钟就好，地点选 ${location.name || "校内公共区域"}，聊不动也方便自然结束。` : "第一次见面短一点、公开一点会更舒服。",
          primary: datePlan ? `
            <p class="copy">${escapeHtml(datePlan.date_suggestion || "")}</p>
            <div class="kv">
              <span>地点</span><strong>${escapeHtml(location.name || "")}</strong>
              <span>校区</span><strong>${escapeHtml(location.campus || "")}</strong>
              <span>天气</span><strong>${escapeHtml(datePlan.weather && datePlan.weather.condition)} ${escapeHtml(datePlan.weather && datePlan.weather.temperature_c)}C</strong>
              <span>风险</span><strong class="risk-${escapeHtml(risk.risk_level || "low")}">${escapeHtml(risk.risk_level || "")}</strong>
            </div>
          ` : `<div class="empty">暂无线下方案</div>`,
	          evidence: `
              ${intentNote}
		            <p class="copy"><strong>见面提醒：</strong>${escapeHtml((risk.reasons || []).join("；") || "地点人流和安全等级较适合首约。")}</p>
		            <p class="copy"><strong>可以发给对方：</strong>如果你愿意，我们先约一小时，聊不累就继续。</p>
	          `
        };
      }
      return {
	        summary: `你提交了见后反馈，信用会到 ${Math.min(100, state.experienceCredit + action.deltaCredit)}。`,
	        assistant: "反馈已经记下。感觉不错会让后续推荐更稳定；如果不舒服，也会减少类似邀约。",
        primary: `
          ${inputNote}
	          <p class="copy"><strong>这次会记下：</strong>见面体验、守时情况、相处是否舒服。</p>
	          ${tags(["见面体验", "相处节奏", "信用记录"], "blue")}
        `,
        evidence: `
          ${intentNote}
		      <p class="copy"><strong>当前提醒：</strong>${escapeHtml(((governance.policy || {}).reasons || []).join("；") || "暂时没有需要特别注意的地方。")}</p>
		      <p class="copy"><strong>之后：</strong>你可以回看这 7 天的聊天记录和进展。</p>
        `
      };
    }

    function objectBars(obj) {
      const entries = Object.entries(obj).sort((a, b) => Number(b[1]) - Number(a[1]));
      if (!entries.length) return `<p class="muted">暂无数据</p>`;
      const max = Math.max(...entries.map((entry) => Number(entry[1]) || 0), 1);
      return `<div class="score-list">${entries.map(([label, value]) => `
        <div class="score-row">
          <span>${escapeHtml(label)}</span>
          <div class="bar"><i style="width:${((Number(value) || 0) / max * 100).toFixed(1)}%"></i></div>
          <strong>${escapeHtml(value)}</strong>
        </div>
      `).join("")}</div>`;
    }

    renderModeSummary();
  </script>
</body>
</html>
"""


def main() -> None:
    payload = build_payload(ROOT)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    copy_demo_assets(ROOT, payload, OUTPUT.parent)
    OUTPUT.write_text(HTML_TEMPLATE.replace("__CAMPUS_DATA__", js_data(payload)), encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    print(f"profiles: {len(payload['profiles'])}")
    print(f"matches: {len(payload['matches'])}")
    print(f"scene_requests: {len(payload['sceneRequests'])}")


if __name__ == "__main__":
    main()
