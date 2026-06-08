from __future__ import annotations

import time
from typing import Any

import numpy as np

from .embeddings import hash_embedding


VECTOR_SEARCH_QUERIES = [
    "想找会编程、能一起学习的人",
    "想找重视边界感，第一次适合咖啡馆见面的人",
    "想找运动搭子，最好能一起羽毛球或健身",
]


def _numpy_top_k(query_vec: np.ndarray, vectors: np.ndarray, top_k: int) -> tuple[np.ndarray, np.ndarray]:
    scores = vectors @ query_vec
    order = np.argsort(-scores)[:top_k]
    return scores[order], order


def _query_vector(query: str, dim: int, query_encoder: Any | None) -> tuple[np.ndarray, str]:
    if query_encoder is not None:
        query_vec = np.asarray(query_encoder.encode([query])[0], dtype=np.float32)
        encoder_name = getattr(query_encoder, "provider", "custom")
    else:
        query_vec = hash_embedding(query, dim=dim).astype(np.float32)
        encoder_name = "hash"
    return query_vec.astype(np.float32), encoder_name


def generate_vector_search_traces(
    profiles: list[dict[str, Any]],
    text_vectors: np.ndarray,
    image_vectors: np.ndarray,
    dim: int = 384,
    top_k: int = 3,
    query_encoder: Any | None = None,
) -> list[dict[str, Any]]:
    """Generate local vector retrieval traces.

    Uses FAISS when available and falls back to a numpy inner-product search.
    Both paths are deterministic and offline.
    """

    use_faiss = False
    faiss_error = ""
    text_index = None
    try:
        import faiss

        text_index = faiss.IndexFlatIP(text_vectors.shape[1])
        text_index.add(text_vectors.astype(np.float32))
        use_faiss = True
    except Exception as exc:  # noqa: BLE001
        faiss_error = str(exc)

    rows: list[dict[str, Any]] = []
    for query in VECTOR_SEARCH_QUERIES:
        query_vec, encoder_name = _query_vector(query, dim, query_encoder)
        if use_faiss and text_index is not None:
            scores, indices = text_index.search(query_vec.reshape(1, -1), top_k)
            score_list = scores[0]
            index_list = indices[0]
            backend = "faiss.IndexFlatIP"
        else:
            score_list, index_list = _numpy_top_k(query_vec, text_vectors, top_k)
            backend = "numpy_inner_product"

        hits = []
        for rank, (score, idx) in enumerate(zip(score_list, index_list), 1):
            profile = profiles[int(idx)]
            hits.append(
                {
                    "rank": rank,
                    "user_id": profile["user_id"],
                    "display_name": profile.get("display_name", profile["user_id"]),
                    "score": round(float(score), 4),
                    "major": profile.get("major", ""),
                    "campus": profile.get("campus", ""),
                    "interests": profile.get("interests", [])[:4],
                    "values": profile.get("values", [])[:4],
                }
            )

        rows.append(
            {
                "trace_id": f"VECTOR_TRACE_{len(rows) + 1:03d}",
                "query": query,
                "query_embedding_dim": int(query_vec.shape[0]),
                "query_encoder": encoder_name,
                "backend": backend,
                "faiss_available": use_faiss,
                "faiss_error": faiss_error,
                "top_k": hits,
                "image_embedding_dim": int(image_vectors.shape[1]) if image_vectors.size else 0,
                "status": "local_vector_search",
            }
        )
    return rows


def generate_faiss_ann_benchmark(
    profiles: list[dict[str, Any]],
    text_vectors: np.ndarray,
    dim: int = 384,
    top_k: int = 5,
    query_encoder: Any | None = None,
    queries: list[str] | None = None,
    repeats: int = 50,
) -> dict[str, Any]:
    """Compare Flat, IVF and HNSW FAISS indexes on the same profile vectors.

    The dataset is intentionally small in this demo, so this is a method trace
    rather than a performance claim. It shows the course concepts: exact flat
    search, IVF coarse quantization, and HNSW graph navigation.
    """

    try:
        import faiss
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "missing_dependencies",
            "error": str(exc),
            "course_method": "第7章向量数据库：Flat / IVF / HNSW 对比",
        }

    vectors = np.asarray(text_vectors, dtype=np.float32)
    if vectors.size == 0:
        return {"status": "empty", "reason": "No vectors available."}

    n_items, vector_dim = vectors.shape
    benchmark_queries = queries or VECTOR_SEARCH_QUERIES
    query_vectors = []
    encoder_name = "hash"
    for query in benchmark_queries:
        query_vec, encoder_name = _query_vector(query, dim, query_encoder)
        query_vectors.append(query_vec.reshape(1, -1))

    indexes: list[dict[str, Any]] = []

    flat = faiss.IndexFlatIP(vector_dim)
    flat.add(vectors)
    indexes.append(
        {
            "name": "Flat",
            "index_type": "faiss.IndexFlatIP",
            "index": flat,
            "description": "精确暴力检索；结果最稳，但大规模时速度和内存压力更高。",
            "params": {"metric": "inner_product"},
        }
    )

    nlist = max(1, min(8, int(np.sqrt(n_items)) or 1))
    ivf = faiss.IndexIVFFlat(faiss.IndexFlatIP(vector_dim), vector_dim, nlist, faiss.METRIC_INNER_PRODUCT)
    min_train = max(nlist * 40, n_items)
    if n_items < min_train:
        rng = np.random.default_rng(2026)
        repeats_needed = int(np.ceil(min_train / n_items))
        train_vectors = np.tile(vectors, (repeats_needed, 1))[:min_train].copy()
        train_vectors += rng.normal(0.0, 1e-4, size=train_vectors.shape).astype(np.float32)
        norms = np.linalg.norm(train_vectors, axis=1, keepdims=True)
        train_vectors = train_vectors / np.maximum(norms, 1e-12)
    else:
        train_vectors = vectors
    ivf.train(train_vectors.astype(np.float32))
    ivf.add(vectors)
    ivf.nprobe = max(1, min(nlist, 2))
    indexes.append(
        {
            "name": "IVF",
            "index_type": "faiss.IndexIVFFlat",
            "index": ivf,
            "description": "先聚类到倒排桶，再只扫部分桶；对应课件里的 IVF / K-Means / 倒排表。",
            "params": {"nlist": nlist, "nprobe": int(ivf.nprobe), "metric": "inner_product"},
            "training_vectors": int(train_vectors.shape[0]),
        }
    )

    try:
        hnsw = faiss.IndexHNSWFlat(vector_dim, 16, faiss.METRIC_INNER_PRODUCT)
    except TypeError:
        hnsw = faiss.IndexHNSWFlat(vector_dim, 16)
    hnsw.hnsw.efConstruction = 40
    hnsw.hnsw.efSearch = 32
    hnsw.add(vectors)
    indexes.append(
        {
            "name": "HNSW",
            "index_type": "faiss.IndexHNSWFlat",
            "index": hnsw,
            "description": "构建多层近邻图，查询时沿图导航；对应课件里的图式 ANN 检索。",
            "params": {"M": 16, "efConstruction": 40, "efSearch": 32},
        }
    )

    query_rows: list[dict[str, Any]] = []
    flat_reference: dict[str, list[int]] = {}
    for query, query_vec in zip(benchmark_queries, query_vectors):
        per_index = []
        for item in indexes:
            index = item["index"]
            start = time.perf_counter()
            scores = indices = None
            for _ in range(max(1, repeats)):
                scores, indices = index.search(query_vec, min(top_k, n_items))
            elapsed_ms = (time.perf_counter() - start) * 1000.0 / max(1, repeats)
            assert scores is not None and indices is not None
            ids = [int(idx) for idx in indices[0] if int(idx) >= 0]
            if item["name"] == "Flat":
                flat_reference[query] = ids
            reference = set(flat_reference.get(query, ids))
            overlap = len(set(ids) & reference) / max(1, min(top_k, len(reference)))
            hits = []
            for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), 1):
                if int(idx) < 0:
                    continue
                profile = profiles[int(idx)]
                hits.append(
                    {
                        "rank": rank,
                        "user_id": profile["user_id"],
                        "display_name": profile.get("display_name", profile["user_id"]),
                        "score": round(float(score), 4),
                    }
                )
            per_index.append(
                {
                    "name": item["name"],
                    "index_type": item["index_type"],
                    "description": item["description"],
                    "params": item["params"],
                    "avg_search_ms": round(float(elapsed_ms), 5),
                    "overlap_with_flat_at_k": round(float(overlap), 4),
                    "top_k": hits,
                }
            )
        query_rows.append({"query": query, "results": per_index})

    summary_rows = []
    for item in indexes:
        name = item["name"]
        matches = [result for row in query_rows for result in row["results"] if result["name"] == name]
        summary_rows.append(
            {
                "name": name,
                "index_type": item["index_type"],
                "params": item["params"],
                "avg_search_ms": round(float(np.mean([row["avg_search_ms"] for row in matches])), 5),
                "avg_overlap_with_flat_at_k": round(float(np.mean([row["overlap_with_flat_at_k"] for row in matches])), 4),
                "description": item["description"],
            }
        )

    return {
        "status": "ok",
        "course_method": "第7章向量数据库：Flat 精确检索 vs IVF 倒排聚类 vs HNSW 图式近邻检索",
        "n_vectors": n_items,
        "dim": vector_dim,
        "top_k": top_k,
        "repeats": repeats,
        "query_encoder": encoder_name,
        "summary": summary_rows,
        "queries": query_rows,
    }
