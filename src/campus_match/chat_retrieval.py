from __future__ import annotations

import hashlib
from typing import Any

import numpy as np

from .embeddings import hash_embedding, l2_normalize, profile_to_text


CHAT_KNOWLEDGE_BASE = [
    {
        "doc_id": "icebreaker_common_interest",
        "source": "icebreaker_library",
        "title": "共同兴趣开场",
        "text": "看到你们有共同兴趣时，先问一个具体、轻松、可回答的问题。",
        "suggestion": "这个共同点可以聊，但别反复复述标签；先问对方偏好和雷点。",
        "tags": ["破冰", "共同兴趣", "低压力"],
    },
    {
        "doc_id": "activity_specific_reply",
        "source": "activity_playbook",
        "title": "具体活动推荐",
        "text": "用户询问最近活动或共同爱好推荐时，不硬编不存在的活动名称；先确认偏好、时长、强度和雷点。",
        "suggestion": "我不太想随便编活动名。可以先定方向：轻松、推理、沉浸，或者只交换一下最近喜欢的内容。",
        "tags": ["活动推荐", "防幻觉", "破冰"],
    },
    {
        "doc_id": "date_low_pressure",
        "source": "date_safety_playbook",
        "title": "低压力首约",
        "text": "第一次见面建议选校内、公开、人流稳定、可短时结束的地点。",
        "suggestion": "如果你愿意，我们先约一小时，聊不累再继续。",
        "tags": ["首约", "安全", "边界"],
    },
    {
        "doc_id": "study_buddy_reply",
        "source": "scene_playbook",
        "title": "学习搭子回复",
        "text": "学习或刷题场景适合明确时间长度、地点和安静程度。",
        "suggestion": "可以先一起学一小时，结束后再决定要不要继续。",
        "tags": ["学习搭子", "时间窗口"],
    },
    {
        "doc_id": "care_needed_reply",
        "source": "emotion_weather_station",
        "title": "低能量照顾",
        "text": "对方说累、焦虑、没胃口时，不要强推见面或重口味饭局。",
        "suggestion": "那今天先不用强行社交，我们可以轻松聊几句。",
        "tags": ["情绪气象站", "照顾信号"],
    },
    {
        "doc_id": "boundary_respect",
        "source": "relationship_boundary_policy",
        "title": "边界感提醒",
        "text": "慢热或重视边界的用户不适合连续追问隐私，也不要催回复。",
        "suggestion": "我们慢慢聊就好，不用一下子把节奏拉太满。",
        "tags": ["边界感", "风险控制"],
    },
    {
        "doc_id": "sports_group_reply",
        "source": "scene_playbook",
        "title": "运动搭子成局",
        "text": "运动搭子适合明确项目、强度、时间和人数，避免临时爽约。",
        "suggestion": "可以，我也想动一动。我们先定一个轻量一点的强度，时间合适就成局。",
        "tags": ["运动搭子", "自动成群", "信用"],
    },
    {
        "doc_id": "meal_buddy_reply",
        "source": "scene_playbook",
        "title": "饭搭子回复",
        "text": "饭搭子适合先说口味、地点和预算，如果对方状态低，不要强推重口味。",
        "suggestion": "可以呀。我们先选近一点、人多一点的地方，口味别太冒险。",
        "tags": ["饭搭子", "地点", "照顾信号"],
    },
    {
        "doc_id": "photo_walk_reply",
        "source": "radar_playbook",
        "title": "拍照 Citywalk",
        "text": "拍照、Citywalk、看展适合低压力线下活动，能边走边聊，不必一直面对面。",
        "suggestion": "这个我愿意。边走边聊会轻松一点，也可以顺手拍几张照片。",
        "tags": ["摄影", "Citywalk", "低压力"],
    },
    {
        "doc_id": "exam_pressure_reply",
        "source": "emotion_weather_station",
        "title": "考试压力安抚",
        "text": "考试、论文、ddl 相关消息要先承接压力，再给一个小而具体的陪伴方案。",
        "suggestion": "辛苦了。我们可以先不聊太重的，或者一起定个 40 分钟的小目标。",
        "tags": ["学业压力", "情绪气象站", "陪伴"],
    },
    {
        "doc_id": "feedback_after_date",
        "source": "memory_museum",
        "title": "见后反馈",
        "text": "见后反馈需要记录感受、守时、边界和是否愿意继续，不直接下判断。",
        "suggestion": "这次见面的感觉可以慢慢说，不用立刻给结论。舒服和不舒服的点都值得记下来。",
        "tags": ["见后反馈", "记忆博物馆", "知识更新"],
    },
]


SAMPLE_QUERIES = [
    "我们周五去图书馆旁边喝咖啡吗？",
    "今天有点累，但还是想和对方聊几句。",
    "如果聊剧本杀，你更喜欢轻推理还是沉浸本？",
]


def _profile_context(profile: dict[str, Any], match: dict[str, Any] | None) -> str:
    parts = [profile_to_text(profile)]
    if match:
        parts.append("共同兴趣：" + "、".join(match.get("common_interests", [])))
        parts.append("共同价值观：" + "、".join(match.get("common_values", [])))
        explanation = match.get("explanation", {})
        parts.append("推荐理由：" + str(explanation.get("reason", "")))
        parts.extend(explanation.get("ice_breakers", []))
    return "\n".join(parts)


def _chat_embedding(text: str, dim: int) -> np.ndarray:
    """Chinese-friendly deterministic embedding for short chat retrieval."""
    vec = hash_embedding(text, dim=dim).astype(np.float32) * 0.45
    compact = "".join(ch for ch in text.lower() if not ch.isspace())
    grams = list(compact)
    grams.extend(compact[idx : idx + 2] for idx in range(max(0, len(compact) - 1)))
    grams.extend(compact[idx : idx + 3] for idx in range(max(0, len(compact) - 2)))
    for gram in grams:
        digest = hashlib.sha256(gram.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 else -1.0
        vec[idx] += 0.55 * sign
    return l2_normalize(vec.reshape(1, -1))[0]


def _retrieve(query: str, documents: list[dict[str, Any]], dim: int) -> list[dict[str, Any]]:
    query_vec = _chat_embedding(query, dim=dim)
    doc_vectors = np.vstack([_chat_embedding(doc["text"] + "\n" + doc["suggestion"], dim=dim) for doc in documents])
    scores = doc_vectors @ query_vec
    for idx, doc in enumerate(documents):
        haystack = doc["text"] + doc["suggestion"] + "".join(doc["tags"])
        if any(word in query for word in ["图书馆", "咖啡", "周五", "见面", "约"]) and any(word in haystack for word in ["首约", "安全", "图书馆", "学习"]):
            scores[idx] += 0.18
        if any(word in query for word in ["累", "焦虑", "难过", "没胃口"]) and any(word in haystack for word in ["低能量", "照顾", "情绪"]):
            scores[idx] += 0.24
        if any(word in query for word in ["剧本杀", "喜欢", "推荐", "活动"]) and any(word in haystack for word in ["活动推荐", "防幻觉"]):
            scores[idx] += 0.28
        if any(word in query for word in ["剧本杀", "喜欢", "音乐", "电影", "展"]) and any(word in haystack for word in ["共同兴趣", "破冰"]):
            scores[idx] += 0.12
        if any(word in query for word in ["羽毛球", "运动", "跑步", "健身", "篮球", "足球"]) and any(word in haystack for word in ["运动搭子", "自动成群", "信用"]):
            scores[idx] += 0.24
        if any(word in query for word in ["饭", "吃", "食堂", "火锅", "冒菜", "咖啡", "没胃口"]) and any(word in haystack for word in ["饭搭子", "地点", "照顾信号"]):
            scores[idx] += 0.22
        if any(word in query for word in ["拍照", "Citywalk", "散步", "看展", "走走"]) and any(word in haystack for word in ["摄影", "Citywalk", "低压力"]):
            scores[idx] += 0.22
        if any(word in query for word in ["考试", "论文", "ddl", "绩点", "复习", "刷题"]) and any(word in haystack for word in ["学业压力", "小目标", "陪伴"]):
            scores[idx] += 0.23
        if any(word in query for word in ["反馈", "见后", "不舒服", "还不错", "下次"]) and any(word in haystack for word in ["见后反馈", "记忆博物馆", "知识更新"]):
            scores[idx] += 0.24
    order = np.argsort(-scores)
    rows = []
    for rank, idx in enumerate(order[:3], 1):
        doc = documents[int(idx)]
        rows.append(
            {
                "rank": rank,
                "doc_id": doc["doc_id"],
                "source": doc["source"],
                "title": doc["title"],
                "text": doc["text"],
                "suggestion": doc["suggestion"],
                "tags": doc["tags"],
                "score": round(float(scores[int(idx)]), 4),
            }
        )
    return rows


def generate_chat_retrieval_traces(
    profiles: list[dict[str, Any]],
    matches: list[dict[str, Any]],
    dim: int = 384,
) -> list[dict[str, Any]]:
    """Offline vector retrieval trace for chat suggestions.

    This is intentionally deterministic and local: it proves that chat guidance
    can be retrieved by vector similarity without claiming an online LLM call.
    """

    matches_by_user: dict[str, list[dict[str, Any]]] = {}
    for match in matches:
        matches_by_user.setdefault(match["user_id"], []).append(match)

    rows: list[dict[str, Any]] = []
    for profile in profiles[:3]:
        best = sorted(matches_by_user.get(profile["user_id"], []), key=lambda row: row.get("final_score", 0), reverse=True)
        match = best[0] if best else None
        profile_doc = {
            "doc_id": f"profile_context_{profile['user_id']}",
            "source": "profile_and_match_context",
            "title": f"{profile['user_id']} 画像和匹配上下文",
            "text": _profile_context(profile, match),
            "suggestion": (match or {}).get("explanation", {}).get("ice_breakers", ["先从一个轻松问题开始。"])[0],
            "tags": ["画像", "GraphRAG", "匹配理由"],
        }
        documents = [profile_doc, *CHAT_KNOWLEDGE_BASE]
        for query in SAMPLE_QUERIES:
            top_k = _retrieve(query, documents, dim)
            rows.append(
                {
                    "trace_id": f"CHAT_TRACE_{len(rows) + 1:03d}",
                    "user_id": profile["user_id"],
                    "candidate_id": match.get("candidate_id") if match else "",
                    "query": query,
                    "query_embedding_dim": dim,
                    "retrieval_method": "hash_embedding + inner_product_top_k",
                    "top_k": top_k,
                    "final_suggestion": top_k[0]["suggestion"] if top_k else "先从轻松问题开始。",
                    "status": "offline_vector_retrieval",
                }
            )
    return rows
