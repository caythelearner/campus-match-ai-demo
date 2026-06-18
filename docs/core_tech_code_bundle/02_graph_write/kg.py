from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

from .io_utils import ensure_dir


def build_triples(profiles: list[dict[str, Any]]) -> list[dict[str, str]]:
    triples: list[dict[str, str]] = []
    for profile in profiles:
        uid = profile["user_id"]
        scalar_rels = {
            "STUDIES_IN": profile.get("major"),
            "BELONGS_TO": profile.get("school"),
            "LOCATED_AT": profile.get("campus"),
            "HAS_GOAL": profile.get("relationship_goal"),
            "PREFERS_COMMUNICATION": profile.get("communication_style"),
            "HAS_GENDER": profile.get("gender"),
            "PREFERS_GENDER": profile.get("preferred_gender"),
        }
        for rel, obj in scalar_rels.items():
            if obj:
                triples.append({"subject": uid, "relation": rel, "object": str(obj)})
        for rel, field in [
            ("LIKES", "interests"),
            ("VALUES", "values"),
            ("HAS_PERSONALITY", "personality_tags"),
            ("AVAILABLE_AT", "available_time"),
            ("PREFERS_DATE", "preferred_date"),
            ("DISLIKES", "deal_breakers"),
        ]:
            for obj in profile.get(field, []):
                triples.append({"subject": uid, "relation": rel, "object": str(obj)})
    return triples


def save_triples(path: str | Path, triples: list[dict[str, str]]) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["subject", "relation", "object"])
        writer.writeheader()
        writer.writerows(triples)


class ProfileGraph:
    def __init__(self, triples: list[dict[str, str]]) -> None:
        self.triples = triples
        self.user_rel_objects: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        for row in triples:
            subj = row["subject"]
            rel = row["relation"]
            obj = row["object"]
            if subj.startswith("U"):
                self.user_rel_objects[subj][rel].add(obj)

    def common_objects(self, user_a: str, user_b: str, relation: str) -> set[str]:
        return self.user_rel_objects[user_a][relation] & self.user_rel_objects[user_b][relation]

    def relation_set(self, user_id: str, relation: str) -> set[str]:
        return self.user_rel_objects[user_id][relation]

    def path_evidence(self, user_a: str, user_b: str) -> list[dict[str, str]]:
        rel_labels = {
            "LIKES": "共同兴趣",
            "VALUES": "共同价值观",
            "HAS_GOAL": "关系目标一致",
            "PREFERS_DATE": "约会偏好一致",
            "PREFERS_COMMUNICATION": "沟通风格一致",
            "AVAILABLE_AT": "空闲时间一致",
        }
        evidence: list[dict[str, str]] = []
        for rel, label in rel_labels.items():
            for obj in sorted(self.common_objects(user_a, user_b, rel)):
                evidence.append({"type": label, "path": f"{user_a}-[{rel}]->{obj}<-[{rel}]-{user_b}"})
        return evidence


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 0.0
    return len(left & right) / max(1, len(left | right))


def graph_similarity(profile_a: dict[str, Any], profile_b: dict[str, Any]) -> dict[str, float]:
    interests_a = set(profile_a.get("interests", []))
    interests_b = set(profile_b.get("interests", []))
    values_a = set(profile_a.get("values", []))
    values_b = set(profile_b.get("values", []))
    dates_a = set(profile_a.get("preferred_date", []))
    dates_b = set(profile_b.get("preferred_date", []))
    availability_a = set(profile_a.get("available_time", []))
    availability_b = set(profile_b.get("available_time", []))
    return {
        "interest_jaccard": jaccard(interests_a, interests_b),
        "value_jaccard": jaccard(values_a, values_b),
        "date_jaccard": jaccard(dates_a, dates_b),
        "availability_jaccard": jaccard(availability_a, availability_b),
    }


def export_networkx_graph(triples: list[dict[str, str]], output_path: str | Path) -> bool:
    try:
        import networkx as nx

        graph = nx.MultiDiGraph()
        for row in triples:
            graph.add_edge(row["subject"], row["object"], relation=row["relation"])
        ensure_dir(Path(output_path).parent)
        nx.write_gexf(graph, output_path)
        return True
    except Exception:
        return False
