from __future__ import annotations

import random
from collections import defaultdict
from typing import Any


def generate_governance_records(
    profiles: list[dict[str, Any]],
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Generate synthetic governance/credit records.

    This module is for course-demo knowledge governance only. Real systems must
    use audited evidence, human review, appeal channels and privacy controls.
    """
    rng = random.Random(seed + 404)
    rows: list[dict[str, Any]] = []
    for profile in profiles:
        # Most users are normal; a few have synthetic negative events.
        no_show_count = rng.choices([0, 1, 2], weights=[0.78, 0.17, 0.05], k=1)[0]
        late_cancel_count = rng.choices([0, 1, 2], weights=[0.70, 0.24, 0.06], k=1)[0]
        unsafe_report_count = rng.choices([0, 1, 2, 3], weights=[0.86, 0.09, 0.04, 0.01], k=1)[0]
        harassment_flag_count = rng.choices([0, 1], weights=[0.96, 0.04], k=1)[0]
        positive_feedback_count = rng.randint(0, 5)

        credit_score = (
            100
            - 18 * no_show_count
            - 8 * late_cancel_count
            - 20 * unsafe_report_count
            - 40 * harassment_flag_count
            + 3 * positive_feedback_count
        )
        credit_score = max(0, min(100, credit_score))

        policy = _policy_from_events(
            credit_score=credit_score,
            no_show_count=no_show_count,
            unsafe_report_count=unsafe_report_count,
            harassment_flag_count=harassment_flag_count,
        )
        rows.append(
            {
                "user_id": profile["user_id"],
                "credit_score": credit_score,
                "events": {
                    "no_show_count": no_show_count,
                    "late_cancel_count": late_cancel_count,
                    "unsafe_report_count": unsafe_report_count,
                    "harassment_flag_count": harassment_flag_count,
                    "positive_feedback_count": positive_feedback_count,
                },
                "policy": policy,
                "governance_note": "合成治理事件，仅用于课程 demo；真实系统需要人工审核、证据留存和申诉机制。",
            }
        )
    return rows


def _policy_from_events(
    credit_score: int,
    no_show_count: int,
    unsafe_report_count: int,
    harassment_flag_count: int,
) -> dict[str, Any]:
    visibility_multiplier = 1.0
    reasons: list[str] = []
    actions: list[str] = []
    cooldown_hours = 0
    conditional_mute = False
    review_required = False

    if credit_score < 85:
        visibility_multiplier = 0.85
        actions.append("recommendation_downrank")
        reasons.append("信用分低于 85，推荐可见度轻度下降。")
    if credit_score < 70:
        visibility_multiplier = 0.60
        reasons.append("信用分低于 70，推荐可见度中度下降。")
    if credit_score < 50:
        visibility_multiplier = 0.30
        reasons.append("信用分低于 50，推荐可见度显著下降。")
    if no_show_count >= 2:
        cooldown_hours = max(cooldown_hours, 12)
        actions.append("lightning_post_cooldown")
        reasons.append("多次失约，闪电搭子发布进入 12 小时冷却。")
    if unsafe_report_count >= 2:
        visibility_multiplier = min(visibility_multiplier, 0.45)
        actions.append("safety_visibility_downrank")
        reasons.append("多次不适反馈，安全策略降低其曝光。")
    if unsafe_report_count >= 3 or harassment_flag_count >= 1:
        conditional_mute = True
        review_required = True
        visibility_multiplier = min(visibility_multiplier, 0.15)
        actions.append("conditional_mute")
        actions.append("manual_review_required")
        reasons.append("触发高风险规则，限制主动私聊/邀约并进入人工复核。")

    if not reasons:
        reasons.append("无明显治理风险，保持正常推荐。")
    return {
        "visibility_multiplier": round(visibility_multiplier, 2),
        "cooldown_hours": cooldown_hours,
        "conditional_mute": conditional_mute,
        "mute_scope": ["active_chat_invite", "lightning_post"] if conditional_mute else [],
        "review_required": review_required,
        "actions": sorted(set(actions)),
        "reasons": reasons,
    }


def governance_by_user(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {record["user_id"]: record for record in records}


def apply_governance_to_matches(
    matches: list[dict[str, Any]],
    governance_records: list[dict[str, Any]],
    top_k: int,
) -> list[dict[str, Any]]:
    governance = governance_by_user(governance_records)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in matches:
        candidate_policy = governance.get(row["candidate_id"], {}).get("policy", {})
        multiplier = float(candidate_policy.get("visibility_multiplier", 1.0))
        base_score = float(row.get("base_final_score", row["final_score"]))
        adjusted_score = max(0.0, min(1.0, base_score * multiplier))
        new_row = dict(row)
        new_row["base_final_score"] = round(base_score, 4)
        new_row["final_score"] = round(adjusted_score, 4)
        new_row["governance_penalty"] = round(base_score - adjusted_score, 4)
        new_row["candidate_governance"] = {
            "credit_score": governance.get(row["candidate_id"], {}).get("credit_score", 100),
            "policy": candidate_policy,
        }
        grouped[new_row["user_id"]].append(new_row)

    final_rows: list[dict[str, Any]] = []
    for user_id, rows in grouped.items():
        rows.sort(key=lambda item: item["final_score"], reverse=True)
        final_rows.extend(rows[:top_k])
    final_rows.sort(key=lambda item: (item["user_id"], -item["final_score"]))
    return final_rows


def apply_governance_to_scene_matches(
    scene_matches: list[dict[str, Any]],
    governance_records: list[dict[str, Any]],
    top_k: int,
) -> list[dict[str, Any]]:
    governance = governance_by_user(governance_records)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in scene_matches:
        candidate_policy = governance.get(row["candidate_id"], {}).get("policy", {})
        multiplier = float(candidate_policy.get("visibility_multiplier", 1.0))
        base_score = float(row.get("base_final_score", row["final_score"]))
        adjusted_score = max(0.0, min(1.0, base_score * multiplier))
        new_row = dict(row)
        new_row["base_final_score"] = round(base_score, 4)
        new_row["final_score"] = round(adjusted_score, 4)
        new_row["governance_penalty"] = round(base_score - adjusted_score, 4)
        new_row["candidate_governance"] = {
            "credit_score": governance.get(row["candidate_id"], {}).get("credit_score", 100),
            "policy": candidate_policy,
        }
        grouped[new_row["request_id"]].append(new_row)

    final_rows: list[dict[str, Any]] = []
    for request_id, rows in grouped.items():
        rows.sort(key=lambda item: item["final_score"], reverse=True)
        final_rows.extend(rows[:top_k])
    return final_rows
