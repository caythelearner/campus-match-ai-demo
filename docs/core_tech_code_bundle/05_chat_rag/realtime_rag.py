from __future__ import annotations

from datetime import datetime
from typing import Any

from .chat_retrieval import CHAT_KNOWLEDGE_BASE, _profile_context, _retrieve
from .rag_pipeline import _compress_context, _llm_generate_answer, _rewrite_query, _verify


def _best_match(matches: list[dict[str, Any]], user_id: str, candidate_id: str = "") -> dict[str, Any] | None:
    rows = [row for row in matches if row.get("user_id") == user_id]
    if candidate_id:
        direct = next((row for row in rows if row.get("candidate_id") == candidate_id), None)
        if direct:
            return direct
    if not rows:
        return None
    return sorted(rows, key=lambda row: row.get("final_score", 0), reverse=True)[0]


def generate_realtime_chat_rag(
    profiles: list[dict[str, Any]],
    matches: list[dict[str, Any]],
    user_id: str,
    query: str,
    candidate_id: str = "",
    dim: int = 384,
    use_llm: bool = True,
) -> dict[str, Any]:
    profile_by_id = {profile["user_id"]: profile for profile in profiles}
    profile = profile_by_id.get(user_id) or (profiles[0] if profiles else {})
    match = _best_match(matches, profile.get("user_id", ""), candidate_id)
    candidate_id = candidate_id or (match or {}).get("candidate_id", "")
    profile_doc = {
        "doc_id": f"profile_context_{profile.get('user_id', 'unknown')}",
        "source": "profile_and_match_context",
        "title": f"{profile.get('user_id', 'unknown')} 画像和匹配上下文",
        "text": _profile_context(profile, match),
        "suggestion": (match or {}).get("explanation", {}).get("ice_breakers", ["先从一个轻松问题开始。"])[0],
        "tags": ["画像", "GraphRAG", "匹配理由"],
    }
    documents = [profile_doc, *CHAT_KNOWLEDGE_BASE]
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
    generation_method = "retrieval_template_server"
    llm_error = ""
    llm_used = False
    if use_llm:
        try:
            llm_answer = _llm_generate_answer(query, rewrite, compressed)
            if llm_answer:
                final_suggestion = llm_answer.strip().strip('"').strip("'")
                generation_method = "realtime_llm_api_with_retrieved_context"
                llm_used = True
        except Exception as exc:  # noqa: BLE001
            llm_error = str(exc)
    verification = _verify(query, final_suggestion, compressed)
    if verification["status"] == "revise":
        final_suggestion = "先确认对方状态和边界，再给一个低压力、可拒绝的选择。"
        generation_method = f"{generation_method}_verified_rewrite"
    return {
        "trace_id": f"CHAT_API_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "user_id": profile.get("user_id", ""),
        "candidate_id": candidate_id,
        "query": query,
        "steps": [
            {"name": "query_rewrite", "output": rewrite},
            {"name": "router", "output": {"selected_sources": rewrite["route_hints"], "n_routed_docs": len(routed_docs)}},
            {"name": "retrieval", "output": retrieval_top_k},
            {"name": "rerank", "output": [{"doc_id": doc["doc_id"], "score": doc["score"]} for doc in retrieval_top_k]},
            {"name": "context_compression", "output": compressed},
            {"name": "llm_answer", "output": final_suggestion},
            {"name": "safety_verifier", "output": verification},
        ],
        "top_k": retrieval_top_k,
        "final_suggestion": final_suggestion,
        "final_reply": final_suggestion,
        "generation_method": generation_method,
        "llm_attempted": use_llm,
        "llm_used": llm_used,
        "llm_error": llm_error,
        "status": "server_realtime_rag",
    }
