from __future__ import annotations

import json
import os
from typing import Any

import requests


def _clean_json_text(content: str) -> str:
    return content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()


def parse_json_response(content: str) -> dict[str, Any]:
    return json.loads(_clean_json_text(content))


def _extract_openai_text(payload: dict[str, Any]) -> str:
    return str(payload["choices"][0]["message"]["content"])


def _extract_anthropic_text(payload: dict[str, Any]) -> str:
    content = payload.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "\n".join(part for part in parts if part)
    raise KeyError("Anthropic response did not contain text content.")


def _looks_configured_secret(value: str | None) -> bool:
    return bool(value and value.isascii() and " " not in value and value.lower() not in {"none", "null", "your_api_key"})


def llm_config_status() -> dict[str, Any]:
    """Return non-secret LLM configuration metadata for traces and UI."""
    openai_ready = bool(
        os.getenv("LLM_API_URL")
        and _looks_configured_secret(os.getenv("LLM_API_KEY"))
        and os.getenv("LLM_MODEL")
    )
    anthropic_ready = bool(
        os.getenv("ANTHROPIC_BASE_URL")
        and _looks_configured_secret(os.getenv("ANTHROPIC_AUTH_TOKEN") or os.getenv("ANTHROPIC_API_KEY"))
        and (os.getenv("ANTHROPIC_MODEL") or os.getenv("LLM_MODEL"))
    )
    if openai_ready:
        return {"configured": True, "provider": "openai_compatible", "model": os.getenv("LLM_MODEL")}
    if anthropic_ready:
        return {
            "configured": True,
            "provider": "anthropic_compatible",
            "model": os.getenv("ANTHROPIC_MODEL") or os.getenv("LLM_MODEL"),
        }
    return {"configured": False, "provider": "none", "model": ""}


def _call_openai_compatible(system: str, user: str, temperature: float, max_tokens: int) -> str | None:
    api_url = os.getenv("LLM_API_URL")
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")
    if not api_url or not _looks_configured_secret(api_key) or not model:
        return None

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    try:
        return _extract_openai_text(data)
    except Exception:
        return _extract_anthropic_text(data)


def _call_anthropic_compatible(system: str, user: str, temperature: float, max_tokens: int) -> str | None:
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    token = os.getenv("ANTHROPIC_AUTH_TOKEN") or os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("ANTHROPIC_MODEL") or os.getenv("LLM_MODEL")
    if not base_url or not _looks_configured_secret(token) or not model:
        return None

    endpoint = base_url.rstrip("/")
    if not endpoint.endswith("/messages"):
        endpoint = f"{endpoint}/v1/messages"

    payload = {
        "model": model,
        "system": system,
        "messages": [{"role": "user", "content": user}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "x-api-key": token,
        "anthropic-version": os.getenv("ANTHROPIC_VERSION", "2023-06-01"),
        "Content-Type": "application/json",
    }
    resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    try:
        return _extract_anthropic_text(data)
    except Exception:
        return _extract_openai_text(data)


def call_llm_text(system: str, user: str, temperature: float = 0.2, max_tokens: int = 900) -> str | None:
    """Call a configured LLM provider.

    Supported environment styles:
    - OpenAI-compatible: LLM_API_URL, LLM_API_KEY, LLM_MODEL
    - Anthropic-compatible: ANTHROPIC_BASE_URL, ANTHROPIC_AUTH_TOKEN, ANTHROPIC_MODEL

    If nothing is configured, returns None so the offline fallback path can run.
    """
    return _call_openai_compatible(system, user, temperature, max_tokens) or _call_anthropic_compatible(
        system,
        user,
        temperature,
        max_tokens,
    )
