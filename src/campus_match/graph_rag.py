from __future__ import annotations

import json
import hashlib
from typing import Any

from .kg import ProfileGraph
from .llm_client import call_llm_text, parse_json_response


def build_explanation_prompt(
    user: dict[str, Any],
    candidate: dict[str, Any],
    match: dict[str, Any],
    graph_evidence: list[dict[str, str]],
) -> str:
    payload = {
        "user": {
            "id": user["user_id"],
            "self_intro": user.get("self_intro"),
            "goal": user.get("relationship_goal"),
            "style": user.get("communication_style"),
            "deal_breakers": user.get("deal_breakers", []),
        },
        "candidate": {
            "id": candidate["user_id"],
            "self_intro": candidate.get("self_intro"),
            "goal": candidate.get("relationship_goal"),
            "style": candidate.get("communication_style"),
            "deal_breakers": candidate.get("deal_breakers", []),
        },
        "match_scores": match,
        "graph_evidence": graph_evidence,
    }
    return f"""你是校园匹配系统的 GraphRAG 推荐解释助手。

请只基于输入证据生成推荐解释，不要编造不存在的信息。
输出 JSON，字段包括：
- reason: 80 字以内的推荐理由
- common_points: 共同点列表
- differences: 差异点列表
- risk_notes: 风险或注意事项列表
- ice_breakers: 2 条自然、克制的破冰话题

输入：
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""


def template_explanation(
    user: dict[str, Any],
    candidate: dict[str, Any],
    match: dict[str, Any],
    graph_evidence: list[dict[str, str]],
) -> dict[str, Any]:
    common_parts = []
    if match.get("common_interests"):
        common_parts.append("共同兴趣：" + "、".join(match["common_interests"][:4]))
    if match.get("common_values"):
        common_parts.append("共同价值观：" + "、".join(match["common_values"][:4]))
    if match.get("common_dates"):
        common_parts.append("约会偏好相近：" + "、".join(match["common_dates"][:3]))
    if match.get("goal_match"):
        common_parts.append(f"关系目标都偏向「{user.get('relationship_goal')}」")
    if match.get("communication_match"):
        common_parts.append(f"沟通风格都偏「{user.get('communication_style')}」")

    risk_notes = list(match.get("penalty_reasons", []))
    governance = match.get("candidate_governance", {})
    governance_policy = governance.get("policy", {})
    if governance_policy.get("reasons"):
        risk_notes.extend(governance_policy["reasons"])
    if not risk_notes:
        risk_notes = ["未发现强冲突，但仍建议保持边界和真实沟通"]
    reason = "；".join(common_parts[:3]) if common_parts else "文本画像和图谱路径显示存在一定相似度"
    ice_seed = match.get("common_interests") or match.get("common_dates") or ["校园活动"]
    ice_breakers = build_ice_breakers(user, candidate, ice_seed)
    return {
        "reason": reason,
        "common_points": common_parts,
        "differences": [
            f"你是{user.get('communication_style')}，对方是{candidate.get('communication_style')}",
            f"你在{user.get('campus')}，对方在{candidate.get('campus')}",
        ],
        "risk_notes": risk_notes,
        "ice_breakers": ice_breakers,
        "graph_paths": graph_evidence,
    }


def _stable_offset(seed: str, size: int) -> int:
    if size <= 0:
        return 0
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % size


def build_ice_breakers(
    user: dict[str, Any],
    candidate: dict[str, Any],
    ice_seed: list[str],
) -> list[str]:
    topic = ice_seed[0] if ice_seed else "校园活动"
    preferred = (candidate.get("preferred_date") or ["散步"])[0]
    seed = f"{user.get('user_id')}|{candidate.get('user_id')}|{topic}|{preferred}"
    topic_templates = {
        "剧本杀": [
            "你喜欢偏推理、欢乐还是沉浸一点的剧本杀？我不太想上来就选太长或太恐怖的本。",
            "剧本杀这个点挺适合破冰。你通常更在意剧情、队友氛围，还是最后复盘？",
            "如果真约一场剧本杀，你会想先试轻量本，还是直接玩硬核推理？",
            "聊剧本杀前我想先确认雷点：恐怖本、情感本、硬核推理、超长时长，你最想避开哪种？",
            "你玩剧本杀时更喜欢当推理位、气氛位，还是安静观察到最后复盘？",
            "如果从剧本杀开始破冰，我会倾向先选轻量局。你会觉得这样舒服吗？",
            "你有没有玩过印象很深的本？不用剧透，可以只说它为什么让你记得住。",
            "剧本杀可以聊，但我不想只停在标签上。你喜欢它是因为推理、角色，还是一起复盘的氛围？",
        ],
        "摄影": [
            "你拍照更喜欢扫街、人像，还是随手记录生活？我可以先听听你的风格。",
            "如果一起拍照，你会更想去校园角落、江边，还是展馆附近走走？",
        ],
        "电影": [
            "你最近更想看轻松一点的片子，还是能聊很久的那种电影？",
            "电影这个话题挺好接。你是更看剧情、镜头，还是看完以后想一起聊感受？",
        ],
        "音乐": [
            "你最近常听哪一类音乐？我想先从一首歌开始认识你。",
            "如果聊音乐，你会更想交换歌单，还是找个 Livehouse 活动一起看看？",
        ],
    }
    generic_templates = [
        f"你提到「{topic}」的时候我挺感兴趣的。你更喜欢轻松一点，还是认真投入一点？",
        f"如果从「{topic}」开始聊，你会先推荐一个入门选择，还是讲一次印象最深的经历？",
        f"这个共同点可以慢慢聊。你对「{topic}」有没有明确雷点，或者特别喜欢的方向？",
        f"聊「{topic}」的话，我想先听你自己的版本：你是怎么开始喜欢它的？",
        f"我不想只把「{topic}」当标签。它对你来说更像放松、社交，还是认真投入的事？",
        f"如果我们把「{topic}」变成一次轻量活动，你会希望它控制在多久比较舒服？",
    ]
    first_pool = topic_templates.get(topic, generic_templates)
    second_pool = [
        f"如果周末有空，你会更想选择{preferred}，还是先短短散个步熟悉一下？",
        f"第一次不用安排太满。你觉得{preferred}这种节奏舒服，还是先线上多聊一会儿？",
        "我比较想知道你的真实偏好：第一次见面你更喜欢有明确活动，还是留一点自由聊天的空间？",
    ]
    first = first_pool[_stable_offset(seed, len(first_pool))]
    second = second_pool[_stable_offset(seed + "|second", len(second_pool))]
    return [first, second]


def llm_explanation(prompt: str) -> dict[str, Any] | None:
    content = call_llm_text(
        system="你是严格输出 JSON 的 GraphRAG 推荐解释助手。",
        user=prompt,
        temperature=0.2,
        max_tokens=900,
    )
    if not content:
        return None
    return parse_json_response(content)


def explain_matches(
    profiles: list[dict[str, Any]],
    matches: list[dict[str, Any]],
    graph: ProfileGraph,
    use_llm: bool = False,
) -> list[dict[str, Any]]:
    by_id = {profile["user_id"]: profile for profile in profiles}
    rows: list[dict[str, Any]] = []
    for match in matches:
        user = by_id[match["user_id"]]
        candidate = by_id[match["candidate_id"]]
        evidence = graph.path_evidence(user["user_id"], candidate["user_id"])
        explanation = None
        if use_llm:
            prompt = build_explanation_prompt(user, candidate, match, evidence)
            try:
                explanation = llm_explanation(prompt)
            except Exception as exc:  # noqa: BLE001
                explanation = {"llm_error": str(exc)}
        if not explanation or "llm_error" in explanation:
            fallback = template_explanation(user, candidate, match, evidence)
            if explanation and "llm_error" in explanation:
                fallback["llm_error"] = explanation["llm_error"]
            explanation = fallback
        row = dict(match)
        row["explanation"] = explanation
        rows.append(row)
    return rows
