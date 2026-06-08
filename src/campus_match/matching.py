from __future__ import annotations

from typing import Any

import numpy as np

from .kg import graph_similarity


def cosine_matrix(vectors: np.ndarray) -> np.ndarray:
    return vectors @ vectors.T


def _preference_compatible(a: dict[str, Any], b: dict[str, Any]) -> bool:
    pref_a = a.get("preferred_gender", "any")
    pref_b = b.get("preferred_gender", "any")
    gender_a = a.get("gender")
    gender_b = b.get("gender")
    return (pref_a == "any" or pref_a == gender_b) and (pref_b == "any" or pref_b == gender_a)


def _goal_conflict(a_goal: str, b_goal: str) -> bool:
    serious = {"长期关系", "认真了解"}
    casual = {"轻松社交", "先交朋友"}
    return (a_goal in serious and b_goal in casual) or (b_goal in serious and a_goal in casual)


def _communication_conflict(a: str, b: str) -> bool:
    high = {"高频分享", "外向主动"}
    low = {"慢热但深入", "尊重空间"}
    return (a in high and b in low) or (b in high and a in low)


def _conflict_penalty(a: dict[str, Any], b: dict[str, Any], penalties: dict[str, float]) -> tuple[float, list[str]]:
    penalty = 0.0
    reasons: list[str] = []
    if _goal_conflict(a.get("relationship_goal", ""), b.get("relationship_goal", "")):
        penalty += penalties.get("strong_goal_conflict", 0.30)
        reasons.append("关系目标存在明显差异")
    overlap_deal = set(a.get("deal_breakers", [])) & set(b.get("personality_tags", []))
    if overlap_deal:
        penalty += penalties.get("deal_breaker_hit", 0.40)
        reasons.append("雷点可能被触发：" + "、".join(sorted(overlap_deal)))
    if a.get("campus") != b.get("campus"):
        penalty += penalties.get("campus_distance", 0.05)
        reasons.append("校区不同，线下见面成本略高")
    if _communication_conflict(a.get("communication_style", ""), b.get("communication_style", "")):
        penalty += penalties.get("communication_conflict", 0.12)
        reasons.append("沟通节奏可能不同")
    return penalty, reasons


def _match_binary(a: Any, b: Any) -> float:
    return 1.0 if a == b and a else 0.0


def match_users(
    profiles: list[dict[str, Any]],
    text_vectors: np.ndarray,
    image_vectors: np.ndarray,
    config: dict[str, Any],
    top_k: int = 5,
    gnn_pair_scores: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    weights = config.get("matching", {}).get("weights", {})
    penalties = config.get("matching", {}).get("penalties", {})
    text_sim = cosine_matrix(text_vectors)
    image_sim = cosine_matrix(image_vectors)
    by_id = {p["user_id"]: p for p in profiles}
    gnn_lookup: dict[tuple[str, str], float] = {}
    for row in gnn_pair_scores or []:
        left = row.get("user_a")
        right = row.get("user_b")
        if not left or not right:
            continue
        score = float(row.get("gnn_link_score", 0.0))
        gnn_lookup[(left, right)] = score
        gnn_lookup[(right, left)] = score
    matches: list[dict[str, Any]] = []

    for i, user in enumerate(profiles):
        candidates: list[dict[str, Any]] = []
        for j, other in enumerate(profiles):
            if i == j:
                continue
            if not _preference_compatible(user, other):
                continue
            graph_scores = graph_similarity(user, other)
            graph_score = (
                0.45 * graph_scores["interest_jaccard"]
                + 0.35 * graph_scores["value_jaccard"]
                + 0.10 * graph_scores["date_jaccard"]
                + 0.10 * graph_scores["availability_jaccard"]
            )
            value_score = graph_scores["value_jaccard"]
            goal_score = _match_binary(user.get("relationship_goal"), other.get("relationship_goal"))
            comm_score = _match_binary(user.get("communication_style"), other.get("communication_style"))
            gnn_score = gnn_lookup.get((user["user_id"], other["user_id"]), 0.0)
            penalty, penalty_reasons = _conflict_penalty(user, other, penalties)

            score = (
                weights.get("text_similarity", 0.30) * float(text_sim[i, j])
                + weights.get("graph_similarity", 0.25) * graph_score
                + weights.get("value_similarity", 0.20) * value_score
                + weights.get("goal_match", 0.10) * goal_score
                + weights.get("communication_match", 0.05) * comm_score
                + weights.get("image_similarity", 0.10) * float(image_sim[i, j])
                + weights.get("gnn_link_score", 0.00) * gnn_score
                - penalty
            )
            candidates.append(
                {
                    "user_id": user["user_id"],
                    "candidate_id": other["user_id"],
                    "final_score": round(max(0.0, min(1.0, score)), 4),
                    "text_similarity": round(float(text_sim[i, j]), 4),
                    "image_similarity": round(float(image_sim[i, j]), 4),
                    "graph_similarity": round(graph_score, 4),
                    "value_similarity": round(value_score, 4),
                    "goal_match": goal_score,
                    "communication_match": comm_score,
                    "gnn_link_score": round(gnn_score, 4),
                    "gnn_weight": round(float(weights.get("gnn_link_score", 0.00)), 4),
                    "penalty": round(penalty, 4),
                    "penalty_reasons": penalty_reasons,
                    "common_interests": sorted(set(user.get("interests", [])) & set(other.get("interests", []))),
                    "common_values": sorted(set(user.get("values", [])) & set(other.get("values", []))),
                    "common_dates": sorted(set(user.get("preferred_date", [])) & set(other.get("preferred_date", []))),
                }
            )
        candidates.sort(key=lambda row: row["final_score"], reverse=True)
        matches.extend(candidates[:top_k])
    matches.sort(key=lambda row: (row["user_id"], -row["final_score"]))
    # attach compact profile snippets for easier downstream display
    for row in matches:
        candidate = by_id[row["candidate_id"]]
        row["candidate_summary"] = {
            "display_name": candidate.get("display_name"),
            "major": candidate.get("major"),
            "campus": candidate.get("campus"),
            "relationship_goal": candidate.get("relationship_goal"),
            "communication_style": candidate.get("communication_style"),
        }
    return matches
