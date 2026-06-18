from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

import numpy as np

from .embeddings import hash_embedding, profile_to_text
from .intent_search import INTENT_SEARCH_QUERIES, analyze_query_intent


def _tokens(text: str) -> list[str]:
    compact = text.lower()
    words = re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]{2,}", compact)
    chars = [ch for ch in compact if "\u4e00" <= ch <= "\u9fff"]
    bigrams = ["".join(chars[idx : idx + 2]) for idx in range(max(0, len(chars) - 1))]
    return [tok for tok in words + bigrams if tok.strip()]


def _profile_document(profile: dict[str, Any]) -> str:
    parts = [profile_to_text(profile)]
    for field in ["interests", "values", "personality_tags", "preferred_date", "available_time", "deal_breakers"]:
        parts.extend(str(item) for item in profile.get(field, []))
    for field in ["gender", "major", "campus", "school", "relationship_goal", "communication_style"]:
        value = profile.get(field)
        if value:
            parts.append(str(value))
    return "\n".join(parts)


def _normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    low = min(values)
    high = max(values)
    if math.isclose(low, high):
        return [0.5 for _ in values]
    return [(value - low) / (high - low) for value in values]


def _bm25_scores(query: str, documents: list[list[str]], k1: float = 1.5, b: float = 0.75) -> tuple[list[float], dict[str, float]]:
    query_terms = _tokens(query)
    if not documents:
        return [], {}
    n_docs = len(documents)
    avgdl = sum(len(doc) for doc in documents) / max(n_docs, 1)
    doc_freq: Counter[str] = Counter()
    for doc in documents:
        doc_freq.update(set(doc))
    idf = {
        term: math.log(1 + (n_docs - doc_freq.get(term, 0) + 0.5) / (doc_freq.get(term, 0) + 0.5))
        for term in set(query_terms)
    }
    scores: list[float] = []
    for doc in documents:
        tf = Counter(doc)
        dl = len(doc) or 1
        score = 0.0
        for term in query_terms:
            freq = tf.get(term, 0)
            if not freq:
                continue
            denom = freq + k1 * (1 - b + b * dl / max(avgdl, 1e-9))
            score += idf.get(term, 0.0) * freq * (k1 + 1) / denom
        scores.append(score)
    return scores, idf


def _graph_score(profile: dict[str, Any], profile_terms: list[str]) -> tuple[float, list[str]]:
    haystack_terms: list[str] = []
    for field in ["interests", "values", "personality_tags", "preferred_date", "available_time", "deal_breakers"]:
        haystack_terms.extend(str(item) for item in profile.get(field, []))
    for field in ["gender", "major", "campus", "relationship_goal", "communication_style", "school"]:
        value = profile.get(field)
        if value:
            haystack_terms.append(str(value))
    lower = " ".join(haystack_terms).lower()
    hits = [term for term in profile_terms if term.lower() in lower]
    return min(1.0, len(hits) / max(3, len(profile_terms[:8]))), hits


def _constraint_score(profile: dict[str, Any], hard_constraints: list[str]) -> tuple[float, list[str]]:
    if not hard_constraints:
        return 0.75, ["无硬条件，给默认可用分"]
    checks: list[str] = []
    satisfied = 0
    usable = 0
    for constraint in hard_constraints:
        if "性别偏好" in constraint:
            usable += 1
            ok = profile.get("gender") == "male"
            satisfied += int(ok)
            checks.append(f"{constraint}:{'满足' if ok else '不满足'}")
        elif "身高" in constraint:
            checks.append(f"{constraint}:当前无真实身高字段，仅展示占位")
    return (satisfied / usable if usable else 0.5), checks


def _top_rows(scored: list[dict[str, Any]], key: str, top_k: int) -> list[dict[str, Any]]:
    rows = sorted(scored, key=lambda row: row.get(key, 0), reverse=True)[:top_k]
    return [
        {
            "rank": idx,
            "user_id": row["user_id"],
            "display_name": row["display_name"],
            "score": round(float(row.get(key, 0.0)), 4),
            "matched_terms": row.get("matched_terms", [])[:5],
            "reason": row.get("reason", ""),
        }
        for idx, row in enumerate(rows, 1)
    ]


def generate_bm25_hybrid_traces(
    profiles: list[dict[str, Any]],
    text_vectors: np.ndarray,
    dim: int = 384,
    query_encoder: Any | None = None,
    top_k: int = 5,
    queries: list[str] | None = None,
) -> list[dict[str, Any]]:
    documents_text = [_profile_document(profile) for profile in profiles]
    tokenized_docs = [_tokens(text) for text in documents_text]
    traces: list[dict[str, Any]] = []
    weights = {"bm25": 0.30, "dense": 0.32, "graph": 0.26, "constraint": 0.12}

    for idx, query in enumerate(queries or INTENT_SEARCH_QUERIES, 1):
        intent = analyze_query_intent(query)
        bm25_raw, idf = _bm25_scores(query, tokenized_docs)
        bm25_norm = _normalize(bm25_raw)
        if query_encoder is not None:
            query_vec = np.asarray(query_encoder.encode([query])[0], dtype=np.float32)
            encoder_name = getattr(query_encoder, "provider", "custom")
        else:
            query_vec = hash_embedding(query, dim=dim).astype(np.float32)
            encoder_name = "hash"
        dense_raw = (text_vectors.astype(np.float32) @ query_vec).tolist()
        dense_norm = _normalize([float(value) for value in dense_raw])

        scored: list[dict[str, Any]] = []
        for profile, bm25_score, dense_score in zip(profiles, bm25_norm, dense_norm):
            graph_score, graph_hits = _graph_score(profile, intent["profile_terms"])
            constraint_score, checks = _constraint_score(profile, intent["hard_constraints"])
            final = (
                weights["bm25"] * bm25_score
                + weights["dense"] * dense_score
                + weights["graph"] * graph_score
                + weights["constraint"] * constraint_score
            )
            matched_terms = sorted(set(graph_hits + [term for term in _tokens(query) if term in _profile_document(profile).lower()]))
            scored.append(
                {
                    "user_id": profile["user_id"],
                    "display_name": profile.get("display_name", profile["user_id"]),
                    "major": profile.get("major", ""),
                    "campus": profile.get("campus", ""),
                    "bm25_score": round(float(bm25_score), 4),
                    "dense_score": round(float(dense_score), 4),
                    "graph_score": round(float(graph_score), 4),
                    "constraint_score": round(float(constraint_score), 4),
                    "final_score": round(float(final), 4),
                    "matched_terms": matched_terms[:8],
                    "constraint_checks": checks,
                    "reason": "、".join(matched_terms[:4] or graph_hits[:4] or intent["profile_terms"][:3]),
                }
            )

        fused = sorted(scored, key=lambda row: row["final_score"], reverse=True)[:top_k]
        traces.append(
            {
                "trace_id": f"BM25_HYBRID_{idx:03d}",
                "query": query,
                "query_encoder": encoder_name,
                "tokenizer": "regex_words + chinese_char_bigrams",
                "bm25_params": {"k1": 1.5, "b": 0.75, "avg_doc_len": round(sum(len(doc) for doc in tokenized_docs) / max(len(tokenized_docs), 1), 2)},
                "weights": weights,
                "intent": intent,
                "idf_terms": [{"term": term, "idf": round(score, 4)} for term, score in sorted(idf.items(), key=lambda item: item[1], reverse=True)[:8]],
                "retrievers": {
                    "bm25_top_k": _top_rows(scored, "bm25_score", top_k),
                    "dense_top_k": _top_rows(scored, "dense_score", top_k),
                    "graph_top_k": _top_rows(scored, "graph_score", top_k),
                    "constraint_top_k": _top_rows(scored, "constraint_score", top_k),
                },
                "fused_top_k": [{"rank": rank, **row} for rank, row in enumerate(fused, 1)],
                "ablation_note": "BM25 负责精确词命中，dense 负责语义近邻，graph 负责画像字段约束，constraint 负责硬条件。",
                "status": "bm25_dense_graph_constraint_reranked",
            }
        )
    return traces
