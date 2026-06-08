from __future__ import annotations

import json
import os
from typing import Any

import requests


PROFILE_FIELDS = [
    "user_id",
    "display_name",
    "age",
    "gender",
    "preferred_gender",
    "school",
    "major",
    "grade",
    "campus",
    "relationship_goal",
    "interests",
    "values",
    "communication_style",
    "personality_tags",
    "available_time",
    "preferred_date",
    "deal_breakers",
    "self_intro",
    "ideal_partner",
    "implicit_intents",
]


def normalize_profile(user: dict[str, Any]) -> dict[str, Any]:
    """Rule-based extractor for synthetic survey data.

    This is the offline default. Replace or augment it with llm_extract_profile
    when API credentials are available.
    """
    profile = {field: user.get(field) for field in PROFILE_FIELDS if field in user}
    profile.setdefault("implicit_intents", [])
    if profile.get("relationship_goal") in {"长期关系", "认真了解"}:
        profile["implicit_intents"].append({"intent": "关系稳定性", "confidence": 0.82})
    if "边界感" in profile.get("values", []):
        profile["implicit_intents"].append({"intent": "尊重个人空间", "confidence": 0.78})
    if profile.get("communication_style") in {"慢热但深入", "温和倾听"}:
        profile["implicit_intents"].append({"intent": "低压力沟通", "confidence": 0.72})
    return profile


def build_profile_extraction_prompt(user: dict[str, Any]) -> str:
    return f"""你是校园匹配系统的用户画像抽取助手。请从问卷和自由文本中抽取结构化画像。

要求：
1. 只基于输入信息，不要编造。
2. 输出合法 JSON。
3. implicit_intents 中每项包含 intent 和 confidence，confidence 为 0-1。

输入用户：
{json.dumps(user, ensure_ascii=False, indent=2)}

输出字段：
user_id, interests, values, relationship_goal, communication_style, personality_tags,
preferred_date, deal_breakers, implicit_intents
"""


def llm_extract_profile(user: dict[str, Any]) -> dict[str, Any]:
    """OpenAI-compatible profile extraction.

    Required environment variables:
    - LLM_API_URL
    - LLM_API_KEY
    - LLM_MODEL

    The response parser assumes a chat-completions-like JSON response. Adjust
    this function for a specific provider if needed.
    """
    api_url = os.getenv("LLM_API_URL")
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")
    if not api_url or not api_key or not model:
        return normalize_profile(user)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是严格输出 JSON 的信息抽取助手。"},
            {"role": "user", "content": build_profile_extraction_prompt(user)},
        ],
        "temperature": 0.1,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    extracted = json.loads(content)
    merged = normalize_profile(user)
    merged.update(extracted)
    return merged


def extract_profiles(users: list[dict[str, Any]], use_llm: bool = False) -> list[dict[str, Any]]:
    extractor = llm_extract_profile if use_llm else normalize_profile
    return [extractor(user) for user in users]
