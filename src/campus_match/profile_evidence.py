from __future__ import annotations

from typing import Any


def _tag_records(profile: dict[str, Any]) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    for tag in profile.get("interests", []):
        records.append(("兴趣", str(tag)))
    for tag in profile.get("values", []):
        records.append(("价值观", str(tag)))
    for tag in profile.get("personality_tags", []):
        records.append(("性格", str(tag)))
    for tag in profile.get("deal_breakers", []):
        records.append(("雷点", str(tag)))
    for field, label in [("relationship_goal", "关系目标"), ("communication_style", "沟通风格")]:
        value = profile.get(field)
        if value:
            records.append((label, str(value)))
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for item in records:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _evidence_text(profile: dict[str, Any], tag_type: str, tag: str) -> tuple[str, str, str]:
    if tag_type == "兴趣":
        return (
            "AI模拟访谈",
            "你理想中的周六下午是怎样的？",
            f"我大概率会安排一点和「{tag}」有关的事，这种活动让我比较放松，也更容易自然聊天。",
        )
    if tag_type == "价值观":
        return (
            "AI模拟访谈",
            "一段关系里你最希望被怎样对待？",
            f"我会很在意「{tag}」，如果这个点对不上，后面相处会比较消耗。",
        )
    if tag_type == "性格":
        return (
            "画像归纳",
            "朋友通常怎么形容你？",
            f"身边朋友会说我有点「{tag}」，熟起来以后表达会更自然。",
        )
    if tag_type == "雷点":
        return (
            "风险偏好访谈",
            "什么情况会让你立刻想退出一段关系？",
            f"我比较不能接受「{tag}」，这类边界需要一开始就说清楚。",
        )
    if tag_type == "关系目标":
        return (
            "关系目标确认",
            "你更想要什么节奏的关系？",
            f"我现在更偏向「{tag}」，希望不要一上来就压力太大。",
        )
    return (
        "沟通偏好访谈",
        "如果对方让你舒服，通常是怎么沟通的？",
        f"我更适应「{tag}」这种沟通方式，节奏稳定时会更愿意继续了解。",
    )


def generate_profile_tag_evidence(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create tag-level RAG evidence for the soul card.

    These records are synthetic but source-grounded in each generated profile:
    the UI can click a tag and show why it exists, what source produced it,
    and which retrieval path connected the tag to the user profile.
    """

    rows: list[dict[str, Any]] = []
    for profile in profiles:
        user_id = profile["user_id"]
        for idx, (tag_type, tag) in enumerate(_tag_records(profile), 1):
            source_type, question, quote = _evidence_text(profile, tag_type, tag)
            confidence = 0.92 if tag_type in {"价值观", "关系目标", "沟通风格"} else 0.86
            if tag_type == "雷点":
                confidence = 0.88
            evidence_id = f"EVID_{user_id}_{idx:03d}"
            rows.append(
                {
                    "evidence_id": evidence_id,
                    "user_id": user_id,
                    "tag": tag,
                    "tag_type": tag_type,
                    "source_type": source_type,
                    "question": question,
                    "quote": quote,
                    "sanitized_quote": quote.replace(profile.get("display_name", ""), "TA"),
                    "confidence": round(confidence, 3),
                    "retrieval_score": round(confidence - 0.05 + min(idx, 6) * 0.006, 3),
                    "why_it_matters": _why_it_matters(tag_type, tag),
                    "rag_path": [
                        f"User:{user_id}",
                        f"Evidence:{evidence_id}",
                        f"Tag:{tag}",
                        f"Type:{tag_type}",
                    ],
                    "course_method": "第10章 RAG：标签点击 -> 检索证据 -> 脱敏展示；第2章隐性知识显性化",
                }
            )
    return rows


def _why_it_matters(tag_type: str, tag: str) -> str:
    if tag_type == "兴趣":
        return f"用于匹配共同活动和破冰话题，例如从「{tag}」生成低压力开场。"
    if tag_type == "价值观":
        return f"用于判断长期相处兼容度，避免只按外貌或硬条件排序。"
    if tag_type == "性格":
        return f"用于选择聊天节奏、实验室任务难度和首约场景。"
    if tag_type == "雷点":
        return f"用于风险提醒和推荐降权，减少明显边界冲突。"
    if tag_type == "关系目标":
        return f"用于过滤节奏不一致的候选人。"
    return f"用于生成更贴近本人节奏的聊天建议。"
