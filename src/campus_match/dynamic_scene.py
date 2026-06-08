from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

import numpy as np

from .embeddings import hash_embedding, profile_to_text


LOCATIONS = [
    {
        "name": "二食堂二楼",
        "campus": "邯郸校区",
        "category": "食堂",
        "crowd_level": "high",
        "security_level": "high",
        "suitable_tasks": ["meal", "chat"],
        "risk_note": "人流量高，适合临时饭搭子。",
    },
    {
        "name": "文科图书馆",
        "campus": "邯郸校区",
        "category": "学习",
        "crowd_level": "medium",
        "security_level": "high",
        "suitable_tasks": ["study", "quiet_chat"],
        "risk_note": "安静且开放，适合学习搭子和低压力见面。",
    },
    {
        "name": "江湾体育馆",
        "campus": "江湾校区",
        "category": "运动",
        "crowd_level": "medium",
        "security_level": "high",
        "suitable_tasks": ["sports"],
        "risk_note": "适合多人运动搭子。",
    },
    {
        "name": "张江校区咖啡角",
        "campus": "张江校区",
        "category": "咖啡",
        "crowd_level": "medium",
        "security_level": "high",
        "suitable_tasks": ["coffee", "chat", "study"],
        "risk_note": "适合初次见面，社交压力较低。",
    },
    {
        "name": "旧教学楼后门",
        "campus": "邯郸校区",
        "category": "偏僻地点",
        "crowd_level": "low",
        "security_level": "low",
        "suitable_tasks": ["walk"],
        "risk_note": "夜间人流量低，不建议作为首次见面地点。",
    },
]

SCENE_TEMPLATES = [
    "现在（18:30）{location}求一个吃饭搭子，想聊聊{topic}。",
    "现在想找人一起去{location}刷题，最好能安静学习一小时。",
    "今天没胃口，想找一个温和一点的人在{location}随便坐坐。",
    "预约明天下午在{location}打羽毛球，希望能凑到合适的运动搭子。",
    "周末想在{location}附近 Citywalk，找一个喜欢拍照的人。",
]


@dataclass(frozen=True)
class Intent:
    task_type: str
    urgency: str
    mood_signal: str
    avoid_tags: list[str]
    preferred_traits: list[str]
    query_text: str


def infer_scene_intent(text: str) -> Intent:
    """Lightweight intent extraction for scene-based buddy requests."""
    task_type = "chat"
    if any(word in text for word in ["吃", "饭", "食堂", "冒菜", "没胃口"]):
        task_type = "meal"
    if any(word in text for word in ["刷题", "学习", "图书馆", "期末", "算法课"]):
        task_type = "study"
    if any(word in text for word in ["羽毛球", "运动", "体育"]):
        task_type = "sports"
    if any(word in text for word in ["Citywalk", "散步", "拍照"]):
        task_type = "walk"

    urgency = "future" if any(word in text for word in ["预约", "明天", "周末", "下周"]) else "now"
    mood_signal = "neutral"
    avoid_tags: list[str] = []
    preferred_traits: list[str] = []
    if any(word in text for word in ["没胃口", "不舒服", "累", "难受"]):
        mood_signal = "care_needed"
        avoid_tags = ["火锅", "冒菜", "重口味", "酒局过多", "强迫社交"]
        preferred_traits = ["温和倾听", "安全感", "高质量陪伴", "情绪稳定"]

    return Intent(
        task_type=task_type,
        urgency=urgency,
        mood_signal=mood_signal,
        avoid_tags=avoid_tags,
        preferred_traits=preferred_traits,
        query_text=text,
    )


def generate_scene_requests(profiles: list[dict[str, Any]], n_requests: int = 12, seed: int = 42) -> list[dict[str, Any]]:
    rng = random.Random(seed + 2026)
    requesters = rng.sample(profiles, min(n_requests, len(profiles)))
    topics = ["算法课", "期末复习", "AI 项目", "独立电影", "实习焦虑", "校园生活"]
    rows: list[dict[str, Any]] = []

    for idx, profile in enumerate(requesters, 1):
        location = rng.choice(LOCATIONS)
        text = rng.choice(SCENE_TEMPLATES).format(location=location["name"], topic=rng.choice(topics))
        intent = infer_scene_intent(text)
        slot = rng.choice(["周三晚上", "周五晚上", "周六下午", "周末下午", "明天下午"])
        safety_context = _safety_context(location, intent)
        rows.append(
            {
                "request_id": f"R{idx:03d}",
                "requester_id": profile["user_id"],
                "text": text,
                "target_time_slot": slot,
                "location": location,
                "intent": intent.__dict__,
                "dynamic_factors": {
                    "urgency": intent.urgency,
                    "time_decay_weight": 1.0 if intent.urgency == "now" else 0.65,
                    "scene": intent.task_type,
                    "mood_signal": intent.mood_signal,
                },
                "safety_context": safety_context,
            }
        )
    return rows


def match_scene_requests(
    profiles: list[dict[str, Any]],
    scene_requests: list[dict[str, Any]],
    top_k: int = 5,
    embedding_dim: int = 384,
) -> list[dict[str, Any]]:
    profile_by_id = {profile["user_id"]: profile for profile in profiles}
    profile_vectors = {
        profile["user_id"]: hash_embedding(profile_to_text(profile), dim=embedding_dim)
        for profile in profiles
    }

    rows: list[dict[str, Any]] = []
    for request in scene_requests:
        requester = profile_by_id[request["requester_id"]]
        intent = Intent(**request["intent"])
        query_vec = hash_embedding(intent.query_text, dim=embedding_dim)
        location = request["location"]
        candidates: list[dict[str, Any]] = []

        for profile in profiles:
            if profile["user_id"] == requester["user_id"]:
                continue

            semantic = float(np.dot(query_vec, profile_vectors[profile["user_id"]]))
            time_score = _time_compatible(request["target_time_slot"], profile)
            loc_score = _location_score(location, profile)
            task_score = _task_score(intent, profile)
            care_score = _care_score(intent, profile)
            safety_penalty = 0.15 if request["safety_context"]["risk_level"] == "high" else 0.0

            final = (
                0.28 * semantic
                + 0.22 * time_score
                + 0.20 * loc_score
                + 0.20 * task_score
                + 0.10 * care_score
                - safety_penalty
            )
            candidates.append(
                {
                    "request_id": request["request_id"],
                    "requester_id": requester["user_id"],
                    "candidate_id": profile["user_id"],
                    "final_score": round(max(0.0, min(1.0, final)), 4),
                    "semantic_score": round(semantic, 4),
                    "time_score": round(time_score, 4),
                    "location_score": round(loc_score, 4),
                    "task_score": round(task_score, 4),
                    "care_score": round(care_score, 4),
                    "scene_reason": _scene_reason(intent, requester, profile, location, request["target_time_slot"]),
                    "safety_context": request["safety_context"],
                }
            )

        candidates.sort(key=lambda x: x["final_score"], reverse=True)
        rows.extend(candidates[:top_k])
    return rows


def _time_compatible(request_slot: str, profile: dict[str, Any]) -> float:
    available = set(profile.get("available_time", []))
    if request_slot in available:
        return 1.0
    if "周末" in request_slot and any("周六" in x or "周日" in x for x in available):
        return 0.8
    if "晚上" in request_slot and any("晚上" in x for x in available):
        return 0.6
    return 0.1


def _location_score(location: dict[str, Any], profile: dict[str, Any]) -> float:
    return 1.0 if location["campus"] == profile.get("campus") else 0.35


def _task_score(intent: Intent, profile: dict[str, Any]) -> float:
    interests = set(profile.get("interests", []))
    preferred_dates = set(profile.get("preferred_date", []))
    if intent.task_type == "meal" and ({"咖啡", "烘焙"} & interests or "咖啡馆" in preferred_dates):
        return 0.8
    if intent.task_type == "study" and ({"阅读", "AI", "编程", "商业分析"} & interests or "图书馆学习" in preferred_dates):
        return 0.9
    if intent.task_type == "sports" and ({"羽毛球", "网球", "健身", "跑步", "篮球", "足球"} & interests):
        return 1.0
    if intent.task_type == "walk" and ({"Citywalk", "摄影", "旅行", "美术馆"} & interests):
        return 0.9
    return 0.35


def _care_score(intent: Intent, profile: dict[str, Any]) -> float:
    if intent.mood_signal != "care_needed":
        return 0.5
    values = set(profile.get("values", []))
    style = profile.get("communication_style", "")
    traits = values | set(profile.get("personality_tags", [])) | {style}
    positive = len(traits & set(intent.preferred_traits)) / max(1, len(intent.preferred_traits))
    risky = len(set(profile.get("deal_breakers", [])) & set(intent.avoid_tags))
    return max(0.0, min(1.0, 0.35 + 0.65 * positive - 0.25 * risky))


def _safety_context(location: dict[str, Any], intent: Intent) -> dict[str, Any]:
    risk_level = "low"
    notes = [location["risk_note"]]
    if location["security_level"] == "low":
        risk_level = "high" if intent.urgency == "now" else "medium"
        notes.append("建议改到人流更稳定、开放度更高的地点。")
    return {
        "location": location["name"],
        "security_level": location["security_level"],
        "crowd_level": location["crowd_level"],
        "risk_level": risk_level,
        "notes": notes,
    }


def _scene_reason(
    intent: Intent,
    requester: dict[str, Any],
    candidate: dict[str, Any],
    location: dict[str, Any],
    slot: str,
) -> str:
    parts = [
        f"任务场景为「{intent.task_type}」，目标时间为「{slot}」。",
        f"地点「{location['name']}」与候选人校区匹配度较高。"
        if location["campus"] == candidate.get("campus")
        else "候选人与地点不在同一校区，但仍可作为备选。",
    ]
    common_interests = sorted(set(requester.get("interests", [])) & set(candidate.get("interests", [])))
    if common_interests:
        parts.append("双方有共同兴趣：" + "、".join(common_interests[:3]) + "。")
    if intent.mood_signal == "care_needed":
        parts.append("该请求包含低食欲/需要照顾信号，系统提高了温和陪伴类特征权重。")
    return "".join(parts)
