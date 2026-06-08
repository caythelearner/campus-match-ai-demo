from __future__ import annotations

from collections import Counter
from typing import Any


def _pagerank_power_iteration(graph: Any, alpha: float = 0.85, max_iter: int = 80, tol: float = 1e-8) -> dict[Any, float]:
    nodes = list(graph.nodes())
    n_nodes = len(nodes)
    if not nodes:
        return {}

    rank = {node: 1.0 / n_nodes for node in nodes}
    base = (1.0 - alpha) / n_nodes
    for _ in range(max_iter):
        next_rank = {node: base for node in nodes}
        dangling_mass = sum(rank[node] for node in nodes if graph.degree(node) == 0)
        dangling_share = alpha * dangling_mass / n_nodes
        for node in nodes:
            next_rank[node] += dangling_share
        for node in nodes:
            degree = graph.degree(node)
            if degree == 0:
                continue
            share = alpha * rank[node] / degree
            for neighbor in graph.neighbors(node):
                next_rank[neighbor] += share
        delta = sum(abs(next_rank[node] - rank[node]) for node in nodes)
        rank = next_rank
        if delta < tol:
            break
    return rank


def generate_graph_algorithm_trace(
    profiles: list[dict[str, Any]],
    triples: list[dict[str, str]],
    matches: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run local NetworkX graph algorithms for course-method evidence."""

    try:
        import networkx as nx
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "missing_dependency",
            "library": "networkx",
            "error": str(exc),
        }

    graph = nx.Graph()
    relation_counter: Counter[str] = Counter()
    for row in triples:
        source = row["subject"]
        target = f"{row['relation']}:{row['object']}"
        relation = row["relation"]
        graph.add_node(source, node_type="User")
        graph.add_node(target, node_type=relation)
        graph.add_edge(source, target, relation=relation)
        relation_counter[relation] += 1

    user_ids = [profile["user_id"] for profile in profiles]
    degree_centrality = nx.degree_centrality(graph)
    pagerank = _pagerank_power_iteration(graph, alpha=0.85)

    user_scores = []
    for uid in user_ids:
        user_scores.append(
            {
                "user_id": uid,
                "degree_centrality": round(float(degree_centrality.get(uid, 0.0)), 4),
                "pagerank": round(float(pagerank.get(uid, 0.0)), 4),
                "degree": int(graph.degree(uid)) if graph.has_node(uid) else 0,
            }
        )
    user_scores.sort(key=lambda row: (row["pagerank"], row["degree_centrality"]), reverse=True)

    pair_rows = []
    for match in matches[:12]:
        left = match["user_id"]
        right = match["candidate_id"]
        if not graph.has_node(left) or not graph.has_node(right):
            continue
        left_neighbors = set(graph.neighbors(left))
        right_neighbors = set(graph.neighbors(right))
        common = sorted(left_neighbors & right_neighbors)
        try:
            path = nx.shortest_path(graph, left, right)
        except nx.NetworkXNoPath:
            path = []
        pair_rows.append(
            {
                "user_id": left,
                "candidate_id": right,
                "common_neighbor_count": len(common),
                "common_neighbors": common[:8],
                "shortest_path": path[:8],
                "shortest_path_length": len(path) - 1 if path else None,
                "match_score": match.get("final_score"),
            }
        )

    communities = []
    try:
        raw_communities = list(nx.algorithms.community.greedy_modularity_communities(graph))
        for idx, community in enumerate(raw_communities[:6], 1):
            users = sorted(node for node in community if str(node).startswith("U"))
            topics = sorted(node for node in community if not str(node).startswith("U"))[:8]
            communities.append({"community_id": idx, "users": users, "topics": topics, "size": len(community)})
    except Exception as exc:  # noqa: BLE001
        communities.append({"community_id": 0, "error": str(exc), "users": [], "topics": [], "size": 0})

    return {
        "status": "ok",
        "library": "networkx",
        "algorithms": ["degree_centrality", "pagerank", "common_neighbors", "shortest_path", "greedy_modularity_communities"],
        "n_nodes": graph.number_of_nodes(),
        "n_edges": graph.number_of_edges(),
        "relation_counts": dict(relation_counter),
        "user_scores": user_scores,
        "pair_evidence": pair_rows,
        "communities": communities,
    }
