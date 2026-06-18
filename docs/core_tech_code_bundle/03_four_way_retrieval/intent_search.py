from __future__ import annotations

import math
import re
from typing import Any

import numpy as np

from .embeddings import hash_embedding, profile_to_text


INTENT_SEARCH_QUERIES = [
    "想找个会弹吉他的阳光学长",
    "周三下午找人一起打羽毛球",
    "想找安静一点的学习搭子",
    "找185+会拍照的体育生",
    "今天没胃口，想找个细心的人陪我散步",
]


INTENT_RULES = [
    {
        "rule_id": "music_skill",
        "patterns": ["吉他", "音乐", "弹", "乐器"],
        "explicit": ["会弹吉他", "音乐兴趣"],
        "inferred": ["音乐技能", "艺术细胞", "低压力聊天"],
        "profile_terms": ["古典音乐", "Livehouse", "爵士", "音乐节", "音乐现场"],
    },
    {
        "rule_id": "sunny_senior",
        "patterns": ["阳光", "学长", "男生", "帅哥"],
        "explicit": ["偏好男生", "阳光气质"],
        "inferred": ["外向主动", "探索欲强", "线下见面意愿"],
        "profile_terms": ["male", "外向", "外向主动", "探索欲强", "认真了解"],
    },
    {
        "rule_id": "sports_partner",
        "patterns": ["体育", "羽毛球", "健身", "打球", "跑步", "篮球", "足球", "运动"],
        "explicit": ["运动搭子", "具体活动"],
        "inferred": ["即时搭子", "体力活动", "可自动成群"],
        "profile_terms": ["羽毛球", "健身", "跑步", "篮球", "足球", "网球", "运动"],
    },
    {
        "rule_id": "study_partner",
        "patterns": ["学习", "自习", "刷题", "图书馆", "算法课", "考试"],
        "explicit": ["学习搭子", "安静场景"],
        "inferred": ["低干扰陪伴", "共同进步", "时间窗口匹配"],
        "profile_terms": ["图书馆学习", "阅读", "AI", "编程", "商业分析", "共同进步", "自律"],
    },
    {
        "rule_id": "visual_filter",
        "patterns": ["185", "拍照", "摄影", "穿搭", "颜值"],
        "explicit": ["硬条件筛选", "视觉偏好"],
        "inferred": ["照片墙入口", "多模态风格", "需要人工确认"],
        "profile_terms": ["摄影", "美术馆", "Citywalk", "穿搭", "male"],
    },
    {
        "rule_id": "care_signal",
        "patterns": ["没胃口", "累", "不舒服", "散步", "细心", "治愈"],
        "explicit": ["照顾信号", "低强度活动"],
        "inferred": ["体贴陪伴", "安全地点", "情绪气象站"],
        "profile_terms": ["温和倾听", "情绪稳定", "高质量陪伴", "散步", "尊重空间"],
    },
    {
        "rule_id": "finance_male",
        "patterns": ["金融男", "金融"],
        "explicit": ["专业偏好"],
        "inferred": ["硬标签过滤", "共同职业话题"],
        "profile_terms": ["金融", "经济学", "工商管理", "male"],
    },
]


def _contains_any(text: str, patterns: list[str]) -> bool:
    return any(pattern.lower() in text for pattern in patterns)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def analyze_query_intent(query: str) -> dict[str, Any]:
    normalized = query.strip().lower()
    matched_rules = [rule for rule in INTENT_RULES if _contains_any(normalized, rule["patterns"])]
    if not matched_rules:
        matched_rules = [
            {
                "rule_id": "general_social",
                "patterns": [],
                "explicit": ["自然语言寻人"],
                "inferred": ["兴趣相似", "边界感", "可聊天"],
                "profile_terms": ["兴趣", "边界感", "真诚", "情绪稳定"],
            }
        ]

    explicit = _dedupe([item for rule in matched_rules for item in rule["explicit"]])
    inferred = _dedupe([item for rule in matched_rules for item in rule["inferred"]])
    profile_terms = _dedupe([item for rule in matched_rules for item in rule["profile_terms"]])
    activated_tags = _dedupe(explicit + inferred + profile_terms)
    hard_constraints: list[str] = []
    warnings: list[str] = []
    if "185" in normalized:
        hard_constraints.append("身高185+")
        warnings.append("当前 demo 没有真实身高字段，只能展示为硬条件占位，不参与真实过滤。")
    if "男" in normalized or "学长" in normalized or "帅哥" in normalized or "金融男" in normalized:
        hard_constraints.append("性别偏好：男生")

    nodes = [{"id": "query", "label": query, "kind": "query", "score": 1.0}]
    edges = []
    for idx, item in enumerate(explicit, 1):
        node_id = f"explicit:{idx}"
        nodes.append({"id": node_id, "label": item, "kind": "explicit", "score": round(0.96 - idx * 0.03, 3)})
        edges.append({"source": "query", "target": node_id, "relation": "抽取", "weight": 0.95})
    for idx, item in enumerate(inferred, 1):
        node_id = f"inferred:{idx}"
        source_id = f"explicit:{min(idx, max(len(explicit), 1))}" if explicit else "query"
        nodes.append({"id": node_id, "label": item, "kind": "inferred", "score": round(0.88 - idx * 0.035, 3)})
        edges.append({"source": source_id, "target": node_id, "relation": "图谱扩散", "weight": round(0.82 - idx * 0.02, 3)})
    for idx, item in enumerate(profile_terms[:8], 1):
        node_id = f"term:{idx}"
        source_id = f"inferred:{min(idx, max(len(inferred), 1))}" if inferred else "query"
        nodes.append({"id": node_id, "label": item, "kind": "profile_term", "score": round(0.76 - idx * 0.025, 3)})
        edges.append({"source": source_id, "target": node_id, "relation": "映射到画像字段", "weight": round(0.72 - idx * 0.015, 3)})

    prompt_rewrite = (
        "请按显性需求、隐性意图和硬条件进行校园匹配："
        f"显性需求={','.join(explicit)}；隐性意图={','.join(inferred)}；"
        f"候选画像字段={','.join(profile_terms[:8])}。"
    )
    return {
        "query": query,
        "matched_rules": [rule["rule_id"] for rule in matched_rules],
        "explicit_intents": explicit,
        "inferred_intents": inferred,
        "activated_tags": activated_tags,
        "profile_terms": profile_terms,
        "hard_constraints": hard_constraints,
        "warnings": warnings,
        "graph_nodes": nodes,
        "graph_edges": edges,
        "prompt_rewrite": prompt_rewrite,
        "course_method": "第9章 Prompt 增强：Text-to-Graph 意图映射 -> 隐性意图扩散 -> Prompt 重构",
    }


def _profile_terms(profile: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for field in ["interests", "values", "personality_tags", "preferred_date", "available_time", "deal_breakers"]:
        terms.extend(str(item) for item in profile.get(field, []))
    for field in ["gender", "major", "campus", "relationship_goal", "communication_style", "school"]:
        value = profile.get(field)
        if value:
            terms.append(str(value))
    return terms


def _sparse_score(query: str, profile: dict[str, Any], profile_terms: list[str]) -> tuple[float, list[str]]:
    haystack = profile_to_text(profile).lower() + "\n" + " ".join(_profile_terms(profile)).lower()
    hits = [term for term in profile_terms if term.lower() in haystack]
    query_tokens = [tok for tok in re.findall(r"[\w\u4e00-\u9fff]+", query.lower()) if len(tok) >= 2]
    hits.extend(tok for tok in query_tokens if tok in haystack)
    hits = _dedupe(hits)
    denom = max(4, len(profile_terms[:8]) + len(query_tokens))
    return min(1.0, len(hits) / denom), hits


def _graph_constraint_score(profile: dict[str, Any], profile_terms: list[str]) -> tuple[float, list[str]]:
    terms = _profile_terms(profile)
    term_text = " ".join(terms).lower()
    matched = [term for term in profile_terms if term.lower() in term_text]
    score = min(1.0, len(matched) / max(3, len(profile_terms[:8])))
    return score, matched


def _constraint_score(profile: dict[str, Any], hard_constraints: list[str]) -> float:
    if not hard_constraints:
        return 0.75
    satisfied = 0
    usable = 0
    for constraint in hard_constraints:
        if "性别偏好" in constraint:
            usable += 1
            satisfied += int(profile.get("gender") == "male")
        elif "身高" in constraint:
            continue
    return satisfied / usable if usable else 0.5


def _cosine_scores(query_vec: np.ndarray, vectors: np.ndarray) -> np.ndarray:
    scores = vectors @ query_vec
    if scores.size == 0:
        return scores
    min_score = float(scores.min())
    max_score = float(scores.max())
    if math.isclose(max_score, min_score):
        return np.full_like(scores, 0.5, dtype=np.float32)
    return ((scores - min_score) / (max_score - min_score)).astype(np.float32)


def generate_intent_graph_traces(queries: list[str] | None = None) -> list[dict[str, Any]]:
    rows = []
    for idx, query in enumerate(queries or INTENT_SEARCH_QUERIES, 1):
        trace = analyze_query_intent(query)
        trace["trace_id"] = f"INTENT_TRACE_{idx:03d}"
        rows.append(trace)
    return rows


def generate_hybrid_search_traces(
    profiles: list[dict[str, Any]],
    text_vectors: np.ndarray,
    dim: int = 384,
    query_encoder: Any | None = None,
    top_k: int = 5,
    queries: list[str] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, query in enumerate(queries or INTENT_SEARCH_QUERIES, 1):
        intent = analyze_query_intent(query)
        if query_encoder is not None:
            query_vec = np.asarray(query_encoder.encode([query])[0], dtype=np.float32)
            encoder_name = getattr(query_encoder, "provider", "custom")
        else:
            query_vec = hash_embedding(query, dim=dim).astype(np.float32)
            encoder_name = "hash"
        vector_scores = _cosine_scores(query_vec, text_vectors.astype(np.float32))

        scored = []
        for profile, vector_score in zip(profiles, vector_scores):
            sparse, sparse_hits = _sparse_score(query, profile, intent["profile_terms"])
            graph_score, graph_hits = _graph_constraint_score(profile, intent["profile_terms"])
            constraint = _constraint_score(profile, intent["hard_constraints"])
            final = 0.34 * float(vector_score) + 0.24 * sparse + 0.28 * graph_score + 0.14 * constraint
            matched_tags = _dedupe(sparse_hits + graph_hits)
            if not matched_tags:
                matched_tags = _profile_terms(profile)[:3]
            scored.append(
                {
                    "user_id": profile["user_id"],
                    "display_name": profile.get("display_name", profile["user_id"]),
                    "major": profile.get("major", ""),
                    "campus": profile.get("campus", ""),
                    "final_score": round(float(final), 4),
                    "vector_score": round(float(vector_score), 4),
                    "sparse_score": round(float(sparse), 4),
                    "graph_score": round(float(graph_score), 4),
                    "constraint_score": round(float(constraint), 4),
                    "matched_tags": matched_tags[:6],
                    "reason": "、".join(matched_tags[:3]) if matched_tags else "语义相似",
                    "graph_path": [
                        f"Query({query})",
                        "IntentGraph",
                        "ProfileTerms(" + "、".join(intent["profile_terms"][:3]) + ")",
                        f"User({profile['user_id']})",
                    ],
                }
            )
        scored.sort(key=lambda row: row["final_score"], reverse=True)
        rows.append(
            {
                "trace_id": f"HYBRID_TRACE_{idx:03d}",
                "query": query,
                "intent_trace_id": f"INTENT_TRACE_{idx:03d}",
                "query_encoder": encoder_name,
                "retrievers": ["sparse_keyword", "semantic_vector", "graph_constraint", "reranker"],
                "weights": {"vector": 0.34, "sparse": 0.24, "graph": 0.28, "constraint": 0.14},
                "intent": intent,
                "top_k": [
                    {"rank": rank, **row}
                    for rank, row in enumerate(scored[:top_k], 1)
                ],
                "course_method": "第7章混合检索 + 第10章检索后重排：稀疏命中、向量召回、图谱约束、加权 rerank",
                "status": "hybrid_retrieval_reranked",
            }
        )
    return rows
