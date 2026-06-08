from __future__ import annotations

import random
from typing import Any


TOPICS = ["考研", "火锅", "独立电影", "算法课", "Citywalk", "实习", "咖啡", "羽毛球", "AI 项目"]


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _unique_pairs(matches: list[dict[str, Any]], max_pairs: int) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    pairs: list[dict[str, Any]] = []
    for match in sorted(matches, key=lambda row: row.get("final_score", 0), reverse=True):
        a = match["user_id"]
        b = match["candidate_id"]
        key = tuple(sorted([a, b]))
        if key in seen:
            continue
        seen.add(key)
        pairs.append(match)
        if len(pairs) >= max_pairs:
            break
    return pairs


def generate_relationship_dynamics(
    profiles: list[dict[str, Any]],
    matches: list[dict[str, Any]],
    max_pairs: int = 8,
    days: int = 7,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Generate synthetic relationship heat curves and profile update signals.

    This module intentionally uses simulated aggregate chat metrics. It does not
    inspect real private chat content.
    """
    rng = random.Random(seed + 520)
    by_id = {profile["user_id"]: profile for profile in profiles}
    rows: list[dict[str, Any]] = []

    for idx, match in enumerate(_unique_pairs(matches, max_pairs), 1):
        user = by_id[match["user_id"]]
        candidate = by_id[match["candidate_id"]]
        base = float(match.get("final_score", 0.5))
        common_topics = match.get("common_interests") or rng.sample(TOPICS, 2)
        if len(common_topics) < 2:
            common_topics = common_topics + rng.sample(TOPICS, 2 - len(common_topics))

        heat_curve: list[dict[str, Any]] = []
        trend = rng.uniform(-0.04, 0.06)
        for day in range(1, days + 1):
            msg_count = max(0, int(rng.gauss(28 + 35 * base + 5 * day * max(trend, 0), 8)))
            avg_response_delay_min = max(2, int(rng.gauss(42 - 20 * base - 3 * day * max(trend, 0), 10)))
            positive_ratio = _clamp(rng.gauss(0.45 + 0.35 * base + trend * day, 0.08))
            shared_topic_hits = rng.randint(0, 3) + int(base > 0.55)
            heat = _clamp(
                0.30 * base
                + 0.25 * min(msg_count / 80, 1)
                + 0.25 * positive_ratio
                + 0.10 * min(shared_topic_hits / 4, 1)
                + 0.10 * (1 - min(avg_response_delay_min / 120, 1))
            )
            heat_curve.append(
                {
                    "day": day,
                    "message_count": msg_count,
                    "avg_response_delay_min": avg_response_delay_min,
                    "positive_ratio": round(positive_ratio, 3),
                    "shared_topic_hits": shared_topic_hits,
                    "heat": round(heat, 3),
                }
            )

        avg_heat = sum(point["heat"] for point in heat_curve) / len(heat_curve)
        last_heat = heat_curve[-1]["heat"]
        first_heat = heat_curve[0]["heat"]
        heat_delta = last_heat - first_heat
        profile_updates = _profile_updates(avg_heat, heat_delta, user, candidate, common_topics)
        rows.append(
            {
                "pair_id": f"P{idx:03d}",
                "user_id": user["user_id"],
                "candidate_id": candidate["user_id"],
                "base_match_score": match.get("final_score"),
                "common_topics": common_topics[:4],
                "heat_curve": heat_curve,
                "heat_summary": {
                    "avg_heat": round(avg_heat, 3),
                    "first_heat": round(first_heat, 3),
                    "last_heat": round(last_heat, 3),
                    "heat_delta": round(heat_delta, 3),
                    "status": _heat_status(avg_heat, heat_delta),
                },
                "profile_updates": profile_updates,
                "privacy_note": "合成聊天指标，仅用于课程 demo；真实系统应在用户授权后只使用脱敏摘要。",
            }
        )
    return rows


def _heat_status(avg_heat: float, heat_delta: float) -> str:
    if avg_heat >= 0.72 and heat_delta >= 0:
        return "升温稳定"
    if heat_delta >= 0.12:
        return "快速升温"
    if heat_delta <= -0.12:
        return "热度下降"
    if avg_heat < 0.38:
        return "互动偏冷"
    return "平稳了解"


def _profile_updates(
    avg_heat: float,
    heat_delta: float,
    user: dict[str, Any],
    candidate: dict[str, Any],
    common_topics: list[str],
) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    evidence = f"7日平均热度 {avg_heat:.2f}，热度变化 {heat_delta:+.2f}，共同话题：{'、'.join(common_topics[:3])}"
    if avg_heat >= 0.70:
        updates.append(
            {
                "target": "pair",
                "tag": "高共鸣互动",
                "operation": "add_or_strengthen",
                "evidence": evidence,
            }
        )
    if heat_delta >= 0.12:
        updates.append(
            {
                "target": "pair",
                "tag": "关系升温",
                "operation": "add_or_strengthen",
                "evidence": evidence,
            }
        )
    if avg_heat < 0.40:
        updates.append(
            {
                "target": user["user_id"],
                "tag": "需要低压力沟通",
                "operation": "add_or_strengthen",
                "evidence": evidence,
            }
        )
    if user.get("communication_style") == "慢热但深入" and avg_heat >= 0.60:
        updates.append(
            {
                "target": user["user_id"],
                "tag": "熟悉后更活跃",
                "operation": "add_or_strengthen",
                "evidence": evidence,
            }
        )
    if candidate.get("communication_style") == "慢热但深入" and avg_heat >= 0.60:
        updates.append(
            {
                "target": candidate["user_id"],
                "tag": "熟悉后更活跃",
                "operation": "add_or_strengthen",
                "evidence": evidence,
            }
        )
    return updates
