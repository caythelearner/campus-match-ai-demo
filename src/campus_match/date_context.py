from __future__ import annotations

import math
import random
from typing import Any


DATE_LOCATIONS = [
    {
        "name": "邯郸校区图书馆旁咖啡馆",
        "campus": "邯郸校区",
        "lat": 31.298,
        "lon": 121.504,
        "category": "咖啡馆",
        "crowd_level": "medium",
        "security_level": "high",
        "indoor": True,
        "suitable_for": ["咖啡馆", "图书馆学习", "聊天"],
    },
    {
        "name": "江湾体育馆",
        "campus": "江湾校区",
        "lat": 31.337,
        "lon": 121.503,
        "category": "运动",
        "crowd_level": "medium",
        "security_level": "high",
        "indoor": True,
        "suitable_for": ["运动", "羽毛球"],
    },
    {
        "name": "张江校区咖啡角",
        "campus": "张江校区",
        "lat": 31.205,
        "lon": 121.596,
        "category": "咖啡馆",
        "crowd_level": "medium",
        "security_level": "high",
        "indoor": True,
        "suitable_for": ["咖啡馆", "聊天"],
    },
    {
        "name": "校园湖边步道",
        "campus": "邯郸校区",
        "lat": 31.300,
        "lon": 121.500,
        "category": "散步",
        "crowd_level": "low",
        "security_level": "medium",
        "indoor": False,
        "suitable_for": ["散步", "Citywalk", "摄影"],
    },
]

WEATHERS = [
    {"condition": "晴", "rain_probability": 0.05, "temperature_c": 25, "wind": "微风"},
    {"condition": "多云", "rain_probability": 0.18, "temperature_c": 23, "wind": "微风"},
    {"condition": "小雨", "rain_probability": 0.72, "temperature_c": 20, "wind": "东北风"},
    {"condition": "大风", "rain_probability": 0.28, "temperature_c": 19, "wind": "大风"},
]


def generate_date_contexts(
    profiles: list[dict[str, Any]],
    matches: list[dict[str, Any]],
    max_plans: int = 8,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Generate synthetic date context with simulated LBS and weather.

    Real systems can replace this with user-authorized location and weather APIs.
    """
    rng = random.Random(seed + 1314)
    by_id = {profile["user_id"]: profile for profile in profiles}
    rows: list[dict[str, Any]] = []
    used: set[tuple[str, str]] = set()
    for match in sorted(matches, key=lambda row: row.get("final_score", 0), reverse=True):
        pair = tuple(sorted([match["user_id"], match["candidate_id"]]))
        if pair in used:
            continue
        used.add(pair)
        user = by_id[match["user_id"]]
        candidate = by_id[match["candidate_id"]]
        location = _choose_location(user, candidate, rng)
        weather = rng.choice(WEATHERS)
        user_pos = _jitter(location["lat"], location["lon"], rng, radius_km=1.8)
        candidate_pos = _jitter(location["lat"], location["lon"], rng, radius_km=2.2)
        user_distance = _haversine_km(user_pos["lat"], user_pos["lon"], location["lat"], location["lon"])
        candidate_distance = _haversine_km(candidate_pos["lat"], candidate_pos["lon"], location["lat"], location["lon"])
        risk = _risk_assessment(location, weather, max(user_distance, candidate_distance))
        rows.append(
            {
                "plan_id": f"D{len(rows) + 1:03d}",
                "user_id": user["user_id"],
                "candidate_id": candidate["user_id"],
                "proposed_time": rng.choice(["周五晚上", "周六下午", "周日下午", "明天下午"]),
                "location": location,
                "simulated_lbs": {
                    "user_position": user_pos,
                    "candidate_position": candidate_pos,
                    "user_distance_km": round(user_distance, 2),
                    "candidate_distance_km": round(candidate_distance, 2),
                    "same_campus_hint": location["campus"] in {user.get("campus"), candidate.get("campus")},
                },
                "weather": weather,
                "risk_assessment": risk,
                "date_suggestion": _date_suggestion(location, weather, risk),
                "privacy_note": "默认使用模拟地理位置和天气；真实系统必须用户授权，并只保留必要上下文。",
            }
        )
        if len(rows) >= max_plans:
            break
    return rows


def _choose_location(user: dict[str, Any], candidate: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    preferred = set(user.get("preferred_date", [])) | set(candidate.get("preferred_date", []))
    candidates = [
        location
        for location in DATE_LOCATIONS
        if preferred & set(location["suitable_for"]) or location["campus"] in {user.get("campus"), candidate.get("campus")}
    ]
    return rng.choice(candidates or DATE_LOCATIONS)


def _jitter(lat: float, lon: float, rng: random.Random, radius_km: float) -> dict[str, float]:
    # Rough conversion: 1 degree latitude is about 111 km.
    distance = rng.random() * radius_km
    angle = rng.random() * 2 * math.pi
    dlat = (distance * math.cos(angle)) / 111
    dlon = (distance * math.sin(angle)) / (111 * math.cos(math.radians(lat)))
    return {"lat": round(lat + dlat, 6), "lon": round(lon + dlon, 6)}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _risk_assessment(location: dict[str, Any], weather: dict[str, Any], max_distance_km: float) -> dict[str, Any]:
    score = 0.1
    reasons: list[str] = []
    if location["security_level"] == "medium":
        score += 0.15
        reasons.append("地点开放但人流不稳定。")
    if location["security_level"] == "low":
        score += 0.35
        reasons.append("地点安全等级较低。")
    if weather["rain_probability"] >= 0.6 and not location["indoor"]:
        score += 0.25
        reasons.append("降雨概率较高，户外见面体验和安全性下降。")
    if "大风" in weather["condition"] and not location["indoor"]:
        score += 0.18
        reasons.append("大风天气不适合户外初次见面。")
    if max_distance_km > 2.0:
        score += 0.08
        reasons.append("双方到达地点的距离略远。")
    level = "low"
    if score >= 0.55:
        level = "high"
    elif score >= 0.30:
        level = "medium"
    return {"risk_score": round(min(score, 1.0), 3), "risk_level": level, "reasons": reasons or ["风险较低。"]}


def _date_suggestion(location: dict[str, Any], weather: dict[str, Any], risk: dict[str, Any]) -> str:
    if risk["risk_level"] == "high":
        return f"不建议当前方案。{weather['condition']}且地点条件一般，建议改为室内、人流稳定的咖啡馆或图书馆附近。"
    if weather["rain_probability"] >= 0.6 and not location["indoor"]:
        return "建议改为室内地点，避免雨天户外见面。"
    return f"推荐在「{location['name']}」见面，控制在 30-60 分钟，保持轻松和边界感。"
