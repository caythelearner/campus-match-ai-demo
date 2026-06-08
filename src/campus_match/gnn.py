from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .embeddings import hash_embedding
from .io_utils import ensure_dir, write_json, write_jsonl


def train_gnn_link_predictor_placeholder(
    profiles: list[dict[str, Any]],
    text_vectors: np.ndarray,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Optional GNN placeholder.

    This function records the intended GNN task and produces a deterministic
    baseline artifact. Replace with torch-geometric training when dependencies
    and labels are ready.
    """
    output_dir = ensure_dir(output_dir)
    artifact = {
        "status": "placeholder",
        "task": "User-User link prediction on User-Interest-Value-Goal graph",
        "n_users": len(profiles),
        "feature_shape": list(text_vectors.shape),
        "recommended_next_step": "Use torch_geometric GraphSAGE encoder and dot-product decoder.",
    }
    write_json(output_dir / "gnn_placeholder.json", artifact)
    return artifact


def build_pseudo_link_labels(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels: list[dict[str, Any]] = []
    for i, a in enumerate(profiles):
        for b in profiles[i + 1 :]:
            shared_interests = len(set(a.get("interests", [])) & set(b.get("interests", [])))
            shared_values = len(set(a.get("values", [])) & set(b.get("values", [])))
            same_goal = a.get("relationship_goal") == b.get("relationship_goal")
            label = int(shared_interests >= 2 and shared_values >= 1 and same_goal)
            labels.append({"user_a": a["user_id"], "user_b": b["user_id"], "label": label})
    return labels


def _auc_score(labels: list[int], scores: list[float]) -> float:
    pos = [(s, i) for i, (y, s) in enumerate(zip(labels, scores)) if y == 1]
    neg = [(s, i) for i, (y, s) in enumerate(zip(labels, scores)) if y == 0]
    if not pos or not neg:
        return 0.0
    wins = 0.0
    total = len(pos) * len(neg)
    for ps, _ in pos:
        for ns, _ in neg:
            if ps > ns:
                wins += 1.0
            elif ps == ns:
                wins += 0.5
    return wins / total


def _profile_attribute_nodes(profile: dict[str, Any]) -> list[str]:
    attrs: list[str] = []
    for field, prefix in [
        ("interests", "Interest"),
        ("values", "Value"),
        ("personality_tags", "Personality"),
        ("preferred_date", "Date"),
        ("available_time", "Time"),
        ("deal_breakers", "DealBreaker"),
    ]:
        for value in profile.get(field, []):
            attrs.append(f"{prefix}:{value}")
    for field, prefix in [
        ("relationship_goal", "Goal"),
        ("communication_style", "Comm"),
        ("campus", "Campus"),
        ("major", "Major"),
    ]:
        value = profile.get(field)
        if value:
            attrs.append(f"{prefix}:{value}")
    return attrs


def _governance_attribute_nodes(record: dict[str, Any]) -> list[str]:
    attrs: list[str] = []
    events = record.get("events", {})
    for field in ["no_show_count", "late_cancel_count", "unsafe_report_count", "harassment_flag_count"]:
        count = int(events.get(field, 0) or 0)
        if count > 0:
            attrs.append(f"GovernanceEvent:{field}:>=1")
            attrs.append(f"GovernanceEvent:{field}:{min(count, 3)}")
    positive_count = int(events.get("positive_feedback_count", 0) or 0)
    if positive_count > 0:
        attrs.append(f"GovernanceEvent:positive_feedback_count:>=1")
    policy = record.get("policy", {})
    for action in policy.get("actions", []):
        attrs.append(f"GovernanceAction:{action}")
    score = int(record.get("credit_score", 100) or 100)
    if score < 50:
        attrs.append("CreditBand:<50")
    elif score < 70:
        attrs.append("CreditBand:50-69")
    elif score < 85:
        attrs.append("CreditBand:70-84")
    else:
        attrs.append("CreditBand:85+")
    return attrs


def train_graphsage_link_predictor(
    profiles: list[dict[str, Any]],
    text_vectors: np.ndarray,
    output_dir: str | Path,
    epochs: int = 80,
    hidden_dim: int = 128,
    seed: int = 42,
) -> dict[str, Any]:
    """Train a lightweight GraphSAGE user-user link predictor.

    The graph is homogeneous:
    - User nodes use profile text embeddings.
    - Attribute nodes use deterministic hash embeddings.
    - Edges connect users to interests, values, goals, communication styles, etc.
    - User-user pseudo labels are generated from overlap rules.

    This is intentionally compact so it can be modified for the final report.
    """
    output_dir = ensure_dir(output_dir)
    try:
        import torch
        import torch.nn.functional as F
        from torch import nn
    except Exception as exc:  # noqa: BLE001
        artifact = train_gnn_link_predictor_placeholder(profiles, text_vectors, output_dir)
        artifact["status"] = "missing_dependencies"
        artifact["error"] = str(exc)
        write_json(output_dir / "gnn_metrics.json", artifact)
        return artifact
    try:
        from torch_geometric.nn import SAGEConv

        gnn_backend = "torch_geometric_sageconv"
    except Exception as exc:  # noqa: BLE001
        SAGEConv = None  # type: ignore[assignment]
        gnn_backend = "torch_mean_graphsage"
        pyg_error = str(exc)
    else:
        pyg_error = ""

    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dim = int(text_vectors.shape[1])

    node_to_idx: dict[str, int] = {}
    features: list[np.ndarray] = []

    def add_node(node_id: str, feature: np.ndarray) -> int:
        if node_id in node_to_idx:
            return node_to_idx[node_id]
        node_to_idx[node_id] = len(node_to_idx)
        features.append(feature.astype(np.float32))
        return node_to_idx[node_id]

    user_index: dict[str, int] = {}
    for profile, vector in zip(profiles, text_vectors):
        user_index[profile["user_id"]] = add_node(f"User:{profile['user_id']}", vector)

    edges: list[tuple[int, int]] = []
    for profile in profiles:
        uid_idx = user_index[profile["user_id"]]
        for attr in _profile_attribute_nodes(profile):
            attr_idx = add_node(attr, hash_embedding(attr, dim=dim))
            edges.append((uid_idx, attr_idx))
            edges.append((attr_idx, uid_idx))

    edge_index_np = np.asarray(edges, dtype=np.int64).T
    x = torch.tensor(np.vstack(features), dtype=torch.float32, device=device)
    edge_index = torch.tensor(edge_index_np, dtype=torch.long, device=device)
    mean_adj = torch.eye(len(node_to_idx), dtype=torch.float32, device=device)
    for source, target in edges:
        mean_adj[source, target] = 1.0
    mean_adj = mean_adj / mean_adj.sum(dim=1, keepdim=True).clamp_min(1.0)

    labels = build_pseudo_link_labels(profiles)
    pos = [row for row in labels if row["label"] == 1]
    neg = [row for row in labels if row["label"] == 0]
    if not pos or not neg:
        artifact = {
            "status": "skipped",
            "reason": "Pseudo labels did not contain both positive and negative samples.",
            "n_users": len(profiles),
        }
        write_json(output_dir / "gnn_metrics.json", artifact)
        return artifact

    rng.shuffle(pos)
    rng.shuffle(neg)
    neg = neg[: min(len(neg), max(len(pos) * 2, 1))]
    pair_rows = pos + neg
    rng.shuffle(pair_rows)
    split = max(1, int(len(pair_rows) * 0.8))
    train_rows = pair_rows[:split]
    test_rows = pair_rows[split:] or pair_rows[:]

    def rows_to_tensors(rows: list[dict[str, Any]]) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        left = [user_index[row["user_a"]] for row in rows]
        right = [user_index[row["user_b"]] for row in rows]
        y = [float(row["label"]) for row in rows]
        return (
            torch.tensor(left, dtype=torch.long, device=device),
            torch.tensor(right, dtype=torch.long, device=device),
            torch.tensor(y, dtype=torch.float32, device=device),
        )

    train_left, train_right, train_y = rows_to_tensors(train_rows)
    test_left, test_right, test_y = rows_to_tensors(test_rows)

    class GraphSageLinkPredictor(nn.Module):
        def __init__(self, input_dim: int, hidden: int) -> None:
            super().__init__()
            if SAGEConv is None:
                raise RuntimeError("SAGEConv is unavailable.")
            self.conv1 = SAGEConv(input_dim, hidden)
            self.conv2 = SAGEConv(hidden, hidden)

        def encode(self, node_x: torch.Tensor, edges_t: torch.Tensor) -> torch.Tensor:
            h = F.relu(self.conv1(node_x, edges_t))
            h = self.conv2(h, edges_t)
            return F.normalize(h, p=2, dim=-1)

        def decode(self, z: torch.Tensor, left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
            return (z[left] * z[right]).sum(dim=-1)

        def forward(self, node_x: torch.Tensor, edges_t: torch.Tensor, left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
            z = self.encode(node_x, edges_t)
            return self.decode(z, left, right)

    class MeanGraphSageLayer(nn.Module):
        def __init__(self, input_dim: int, output_dim: int) -> None:
            super().__init__()
            self.self_linear = nn.Linear(input_dim, output_dim)
            self.neighbor_linear = nn.Linear(input_dim, output_dim)

        def forward(self, node_x: torch.Tensor, adj_t: torch.Tensor) -> torch.Tensor:
            neighbor_x = adj_t @ node_x
            return self.self_linear(node_x) + self.neighbor_linear(neighbor_x)

    class TorchMeanGraphSageLinkPredictor(nn.Module):
        def __init__(self, input_dim: int, hidden: int) -> None:
            super().__init__()
            self.conv1 = MeanGraphSageLayer(input_dim, hidden)
            self.conv2 = MeanGraphSageLayer(hidden, hidden)

        def encode(self, node_x: torch.Tensor, adj_t: torch.Tensor) -> torch.Tensor:
            h = F.relu(self.conv1(node_x, adj_t))
            h = self.conv2(h, adj_t)
            return F.normalize(h, p=2, dim=-1)

        def decode(self, z: torch.Tensor, left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
            return (z[left] * z[right]).sum(dim=-1)

        def forward(self, node_x: torch.Tensor, adj_t: torch.Tensor, left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
            z = self.encode(node_x, adj_t)
            return self.decode(z, left, right)

    if SAGEConv is not None:
        model = GraphSageLinkPredictor(dim, hidden_dim).to(device)
        graph_input = edge_index
    else:
        model = TorchMeanGraphSageLinkPredictor(dim, hidden_dim).to(device)
        graph_input = mean_adj
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)

    for _ in range(epochs):
        model.train()
        optimizer.zero_grad()
        logits = model(x, graph_input, train_left, train_right)
        loss = F.binary_cross_entropy_with_logits(logits, train_y)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        test_logits = model(x, graph_input, test_left, test_right)
        test_probs = torch.sigmoid(test_logits).detach().cpu().numpy().tolist()
        test_labels = test_y.detach().cpu().numpy().astype(int).tolist()
        auc = _auc_score(test_labels, test_probs)

        all_pair_scores: list[dict[str, Any]] = []
        z = model.encode(x, graph_input)
        for i, a in enumerate(profiles):
            for b in profiles[i + 1 :]:
                left = torch.tensor([user_index[a["user_id"]]], dtype=torch.long, device=device)
                right = torch.tensor([user_index[b["user_id"]]], dtype=torch.long, device=device)
                score = torch.sigmoid(model.decode(z, left, right)).item()
                all_pair_scores.append(
                    {
                        "user_a": a["user_id"],
                        "user_b": b["user_id"],
                        "gnn_link_score": round(float(score), 4),
                    }
                )

    metrics = {
        "status": "trained",
        "backend": gnn_backend,
        "backend_note": pyg_error,
        "device": str(device),
        "n_users": len(profiles),
        "n_nodes": len(node_to_idx),
        "n_edges": len(edges),
        "n_train_pairs": len(train_rows),
        "n_test_pairs": len(test_rows),
        "epochs": epochs,
        "hidden_dim": hidden_dim,
        "test_auc": round(float(auc), 4),
    }
    write_json(output_dir / "gnn_metrics.json", metrics)
    write_jsonl(output_dir / "gnn_pair_scores.jsonl", all_pair_scores)
    write_json(output_dir / "gnn_pair_scores.json", all_pair_scores)
    try:
        torch.save(model.state_dict(), output_dir / "graphsage_link_predictor.pt")
    except Exception:
        pass
    return metrics


def train_gcn_risk_classifier(
    profiles: list[dict[str, Any]],
    text_vectors: np.ndarray,
    governance_records: list[dict[str, Any]],
    output_dir: str | Path,
    epochs: int = 80,
    hidden_dim: int = 96,
    seed: int = 42,
) -> dict[str, Any]:
    """Train a GCN-style node classifier for governance risk.

    This maps the course GCN node-classification case to the campus product:
    user nodes are classified as normal/risk using synthetic governance labels,
    while graph neighborhoods provide interest/value/context signals.
    """

    output_dir = ensure_dir(output_dir)
    try:
        import torch
        import torch.nn.functional as F
        from torch import nn
    except Exception as exc:  # noqa: BLE001
        artifact = {
            "status": "missing_dependencies",
            "task": "GCN node classification for campus governance risk",
            "error": str(exc),
        }
        write_json(output_dir / "gnn_node_risk_metrics.json", artifact)
        return artifact

    rng = np.random.default_rng(seed + 909)
    torch.manual_seed(seed + 909)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dim = int(text_vectors.shape[1])

    governance_by_id = {record["user_id"]: record for record in governance_records}
    node_to_idx: dict[str, int] = {}
    features: list[np.ndarray] = []

    def add_node(node_id: str, feature: np.ndarray) -> int:
        if node_id in node_to_idx:
            return node_to_idx[node_id]
        node_to_idx[node_id] = len(node_to_idx)
        features.append(feature.astype(np.float32))
        return node_to_idx[node_id]

    user_index: dict[str, int] = {}
    for profile, vector in zip(profiles, text_vectors):
        user_index[profile["user_id"]] = add_node(f"User:{profile['user_id']}", vector)

    edges: list[tuple[int, int]] = []
    for profile in profiles:
        uid_idx = user_index[profile["user_id"]]
        for attr in _profile_attribute_nodes(profile):
            attr_idx = add_node(attr, hash_embedding(attr, dim=dim))
            edges.append((uid_idx, attr_idx))
            edges.append((attr_idx, uid_idx))
        record = governance_by_id.get(profile["user_id"], {})
        for attr in _governance_attribute_nodes(record):
            attr_idx = add_node(attr, hash_embedding(attr, dim=dim))
            edges.append((uid_idx, attr_idx))
            edges.append((attr_idx, uid_idx))

    labels: list[int] = []
    user_node_indices: list[int] = []
    for profile in profiles:
        record = governance_by_id.get(profile["user_id"], {})
        policy = record.get("policy", {})
        is_risk = (
            int(record.get("credit_score", 100)) < 85
            or float(policy.get("visibility_multiplier", 1.0)) < 1.0
            or bool(policy.get("review_required"))
            or bool(policy.get("conditional_mute"))
        )
        labels.append(int(is_risk))
        user_node_indices.append(user_index[profile["user_id"]])

    pos = [idx for idx, label in enumerate(labels) if label == 1]
    neg = [idx for idx, label in enumerate(labels) if label == 0]
    if not pos or not neg:
        artifact = {
            "status": "skipped",
            "task": "GCN node classification for campus governance risk",
            "reason": "Risk labels did not contain both positive and negative classes.",
            "n_users": len(profiles),
            "n_positive": len(pos),
            "n_negative": len(neg),
        }
        write_json(output_dir / "gnn_node_risk_metrics.json", artifact)
        return artifact

    rng.shuffle(pos)
    rng.shuffle(neg)

    def split_class(indices: list[int]) -> tuple[list[int], list[int]]:
        if len(indices) <= 1:
            return indices[:], []
        split = min(len(indices) - 1, max(1, int(len(indices) * 0.8)))
        return indices[:split], indices[split:]

    train_pos, test_pos = split_class(pos)
    train_neg, test_neg = split_class(neg)
    train_rows = train_pos + train_neg
    test_rows = test_pos + test_neg
    rng.shuffle(train_rows)
    rng.shuffle(test_rows)

    x = torch.tensor(np.vstack(features), dtype=torch.float32, device=device)
    n_nodes = len(node_to_idx)
    adj = torch.eye(n_nodes, dtype=torch.float32, device=device)
    for source, target in edges:
        adj[source, target] = 1.0
    degree = adj.sum(dim=1).clamp_min(1.0)
    inv_sqrt = torch.pow(degree, -0.5)
    adj_norm = inv_sqrt[:, None] * adj * inv_sqrt[None, :]

    user_nodes_t = torch.tensor(user_node_indices, dtype=torch.long, device=device)
    labels_t = torch.tensor(labels, dtype=torch.float32, device=device)
    train_idx = torch.tensor(train_rows, dtype=torch.long, device=device)
    test_idx = torch.tensor(test_rows or train_rows, dtype=torch.long, device=device)
    train_y = labels_t[train_idx]

    class GCNLayer(nn.Module):
        def __init__(self, input_dim: int, output_dim: int) -> None:
            super().__init__()
            self.linear = nn.Linear(input_dim, output_dim)

        def forward(self, node_x: torch.Tensor, adj_t: torch.Tensor) -> torch.Tensor:
            return self.linear(adj_t @ node_x)

    class GcnRiskClassifier(nn.Module):
        def __init__(self, input_dim: int, hidden: int) -> None:
            super().__init__()
            self.conv1 = GCNLayer(input_dim, hidden)
            self.conv2 = GCNLayer(hidden, hidden)
            self.classifier = nn.Linear(hidden, 1)

        def forward(self, node_x: torch.Tensor, adj_t: torch.Tensor) -> torch.Tensor:
            h = F.relu(self.conv1(node_x, adj_t))
            h = self.conv2(h, adj_t)
            return self.classifier(h).squeeze(-1)

    model = GcnRiskClassifier(dim, hidden_dim).to(device)
    n_pos_train = float(train_y.sum().item())
    n_neg_train = float(len(train_rows) - n_pos_train)
    pos_weight = torch.tensor([n_neg_train / max(n_pos_train, 1.0)], dtype=torch.float32, device=device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)

    for _ in range(epochs):
        model.train()
        optimizer.zero_grad()
        logits = model(x, adj_norm)[user_nodes_t][train_idx]
        loss = F.binary_cross_entropy_with_logits(logits, train_y, pos_weight=pos_weight)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        user_logits = model(x, adj_norm)[user_nodes_t]
        user_probs = torch.sigmoid(user_logits)
        test_probs = user_probs[test_idx].detach().cpu().numpy().tolist()
        test_labels = labels_t[test_idx].detach().cpu().numpy().astype(int).tolist()
        predictions = [int(prob >= 0.5) for prob in test_probs]
        accuracy = sum(int(pred == label) for pred, label in zip(predictions, test_labels)) / max(len(test_labels), 1)
        auc = _auc_score(test_labels, test_probs)

    risk_rows = []
    for idx, profile in enumerate(profiles):
        record = governance_by_id.get(profile["user_id"], {})
        risk_rows.append(
            {
                "user_id": profile["user_id"],
                "credit_score": record.get("credit_score", 100),
                "risk_label": labels[idx],
                "gnn_risk_probability": round(float(user_probs[idx].item()), 4),
            }
        )
    risk_rows.sort(key=lambda row: row["gnn_risk_probability"], reverse=True)

    metrics = {
        "status": "trained",
        "task": "GCN node classification for campus governance risk",
        "course_method": "第4章 GCN 节点分类：用图邻域传播识别风险节点",
        "backend": "torch_gcn_node_classification",
        "device": str(device),
        "n_users": len(profiles),
        "n_nodes": n_nodes,
        "n_edges": len(edges),
        "n_positive": len(pos),
        "n_negative": len(neg),
        "n_train_nodes": len(train_rows),
        "n_test_nodes": len(test_rows),
        "epochs": epochs,
        "hidden_dim": hidden_dim,
        "test_auc": round(float(auc), 4),
        "test_accuracy": round(float(accuracy), 4),
    }
    write_json(output_dir / "gnn_node_risk_metrics.json", metrics)
    write_jsonl(output_dir / "gnn_node_risk_scores.jsonl", risk_rows)
    write_json(output_dir / "gnn_node_risk_scores.json", risk_rows)
    try:
        torch.save(model.state_dict(), output_dir / "gcn_risk_classifier.pt")
    except Exception:
        pass
    return metrics
