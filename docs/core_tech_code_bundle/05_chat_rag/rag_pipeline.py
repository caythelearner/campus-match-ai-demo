from __future__ import annotations

from typing import Any

from .chat_retrieval import CHAT_KNOWLEDGE_BASE, _profile_context, _retrieve
from .llm_client import call_llm_text, llm_config_status


def _rewrite_query(query: str) -> dict[str, Any]:
    intent = "icebreaker"
    route_hints = ["icebreaker_library", "profile_and_match_context"]
    if any(word in query for word in ["图书馆", "咖啡", "见面", "约", "周五"]):
        intent = "first_date"
        route_hints = ["date_safety_playbook", "scene_playbook", "profile_and_match_context"]
    if any(word in query for word in ["累", "焦虑", "没胃口", "难过"]):
        intent = "emotion_support"
        route_hints = ["emotion_weather_station", "relationship_boundary_policy", "profile_and_match_context"]
    if any(word in query for word in ["剧本杀", "活动", "推荐"]):
        intent = "activity_recommendation"
        route_hints = ["activity_playbook", "icebreaker_library", "profile_and_match_context"]
    if any(word in query for word in ["羽毛球", "运动", "跑步", "篮球"]):
        intent = "scene_buddy"
        route_hints = ["scene_playbook", "profile_and_match_context"]
    return {
        "original_query": query,
        "rewritten_query": f"{query}；请结合画像、匹配理由、安全边界，给出克制、可执行的下一句建议。",
        "intent": intent,
        "route_hints": route_hints,
    }


def _compress_context(top_docs: list[dict[str, Any]], max_items: int = 3) -> list[dict[str, Any]]:
    compressed = []
    for doc in top_docs[:max_items]:
        compressed.append(
            {
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "evidence": doc["text"][:90],
                "suggestion": doc["suggestion"],
                "score": doc["score"],
            }
        )
    return compressed


def _verify(query: str, suggestion: str, context: list[dict[str, Any]]) -> dict[str, Any]:
    flags: list[str] = []
    if any(word in suggestion for word in ["一定", "保证", "必须"]):
        flags.append("语气过强")
    if any(word in query for word in ["活动", "推荐", "剧本杀"]) and "编活动名" in " ".join(item["evidence"] for item in context):
        flags.append("已命中防编造活动策略")
    if any(word in query for word in ["见面", "约", "咖啡", "图书馆"]) and not any("公开" in item["evidence"] or "安全" in item["title"] for item in context):
        flags.append("线下安全证据不足")
    status = "pass" if "线下安全证据不足" not in flags and "语气过强" not in flags else "revise"
    return {
        "status": status,
        "flags": flags or ["无明显越界、编造或安全问题"],
        "rule": "检查越界语气、活动编造、线下安全证据。",
    }


def _llm_generate_answer(query: str, rewrite: dict[str, Any], context: list[dict[str, Any]]) -> str | None:
    context_text = "\n".join(
        f"[{idx + 1}] {item['title']}｜证据：{item['evidence']}｜建议：{item['suggestion']}"
        for idx, item in enumerate(context)
    )
    prompt = f"""请根据检索证据，为校园匹配聊天助手生成一句自然回复建议。

要求：
1. 只基于证据，不要编造具体活动名、地点或对方反馈。
2. 语气像真人，克制、具体、可拒绝，不要油腻。
3. 如果涉及线下见面，要保留安全边界。
4. 只输出一句中文回复，不要解释。

原始消息：{query}
改写意图：{rewrite.get("intent")}
检索证据：
{context_text}
"""
    return call_llm_text(
        system="你是校园社交产品中的聊天建议助手，只输出一句可发送的中文回复。",
        user=prompt,
        temperature=0.4,
        max_tokens=220,
    )


def generate_rag_pipeline_traces(
    profiles: list[dict[str, Any]],
    matches: list[dict[str, Any]],
    dim: int = 384,
    use_llm: bool = False,
    llm_max_traces: int = 4,
    max_profiles: int = 2,
) -> list[dict[str, Any]]:
    matches_by_user: dict[str, list[dict[str, Any]]] = {}
    for match in matches:
        matches_by_user.setdefault(match["user_id"], []).append(match)
    sample_queries = [
        "我们周五去图书馆旁边喝咖啡吗？",
        "我也注意到我们都提到了剧本杀，最近有没有相关活动推荐？",
        "今天有点累，但还是想和对方聊几句。",
        "周三下午想找人打羽毛球，怎么开口比较自然？",
    ]
    rows: list[dict[str, Any]] = []
    llm_status = llm_config_status()
    for profile in profiles[:max_profiles]:
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
        for query in sample_queries:
            rewrite = _rewrite_query(query)
            routed_docs = [
                doc
                for doc in documents
                if doc.get("source") in rewrite["route_hints"] or any(tag in rewrite["rewritten_query"] for tag in doc.get("tags", []))
            ]
            if profile_doc not in routed_docs:
                routed_docs.insert(0, profile_doc)
            retrieval_top_k = _retrieve(rewrite["rewritten_query"], routed_docs, dim=dim)
            compressed = _compress_context(retrieval_top_k)
            final_suggestion = compressed[0]["suggestion"] if compressed else "先从一个轻松问题开始。"
            generation_method = "retrieval_template"
            llm_attempted = False
            llm_used = False
            llm_error = ""
            if use_llm and llm_status["configured"] and len(rows) < llm_max_traces:
                llm_attempted = True
                try:
                    llm_answer = _llm_generate_answer(query, rewrite, compressed)
                    if llm_answer:
                        final_suggestion = llm_answer.strip().strip('"').strip("'")
                        generation_method = "llm_api_with_retrieved_context"
                        llm_used = True
                except Exception as exc:  # noqa: BLE001
                    llm_error = str(exc)
            verification = _verify(query, final_suggestion, compressed)
            if verification["status"] == "revise":
                final_suggestion = "先确认对方状态和边界，再给一个低压力、可拒绝的选择。"
                generation_method = f"{generation_method}_verified_rewrite"
            rows.append(
                {
                    "trace_id": f"RAG_PIPELINE_{len(rows) + 1:03d}",
                    "user_id": profile["user_id"],
                    "candidate_id": match.get("candidate_id") if match else "",
                    "query": query,
                    "steps": [
                        {"name": "query_rewrite", "output": rewrite},
                        {"name": "router", "output": {"selected_sources": rewrite["route_hints"], "n_routed_docs": len(routed_docs)}},
                        {"name": "retrieval", "output": retrieval_top_k},
                        {"name": "rerank", "output": [{"doc_id": doc["doc_id"], "score": doc["score"]} for doc in retrieval_top_k]},
                        {"name": "context_compression", "output": compressed},
                        {"name": "safety_verifier", "output": verification},
                        {"name": "final_answer", "output": final_suggestion},
                    ],
                    "final_suggestion": final_suggestion,
                    "generation_method": generation_method,
                    "llm_attempted": llm_attempted,
                    "llm_used": llm_used,
                    "llm_provider": llm_status["provider"] if llm_attempted else "",
                    "llm_model": llm_status["model"] if llm_attempted else "",
                    "llm_error": llm_error,
                    "status": "rag_rewrite_route_retrieve_rerank_compress_verify",
                }
            )
    return rows
