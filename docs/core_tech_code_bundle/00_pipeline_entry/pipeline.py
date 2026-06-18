from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .chat_retrieval import generate_chat_retrieval_traces
from .bm25_hybrid import generate_bm25_hybrid_traces
from .config import ProjectPaths
from .date_context import generate_date_contexts
from .dynamic_scene import generate_scene_requests, match_scene_requests
from .embeddings import build_embeddings
from .gnn import build_pseudo_link_labels, train_gcn_risk_classifier, train_graphsage_link_predictor
from .graph_analytics import generate_graph_algorithm_trace
from .graph_rag import explain_matches
from .governance import apply_governance_to_matches, apply_governance_to_scene_matches, generate_governance_records
from .image_generation import generate_images_for_profiles
from .interview_extraction import generate_interview_extraction_traces
from .intent_search import generate_hybrid_search_traces, generate_intent_graph_traces
from .io_utils import read_jsonl, write_csv, write_json, write_jsonl
from .kg import ProfileGraph, build_triples, export_networkx_graph, save_triples
from .matching import match_users
from .neo4j_trace import export_neo4j_trace
from .ontology import generate_ontology_validation
from .profile_evidence import generate_profile_tag_evidence
from .profile_extraction import extract_profiles
from .rag_pipeline import generate_rag_pipeline_traces
from .relationship_dynamics import generate_relationship_dynamics
from .synthetic_users import generate_users
from .vector_search import generate_faiss_ann_benchmark, generate_vector_search_traces


def run_pipeline(config: dict[str, Any], root: str | Path, run_gnn: bool = False) -> dict[str, Any]:
    paths = ProjectPaths.from_config(root, config)
    seed = int(config.get("seed", 42))
    n_users = int(config.get("n_users", 120))
    top_k = int(config.get("top_k", 5))

    users = generate_users(n_users=n_users, seed=seed)
    write_jsonl(paths.data_dir / "users.jsonl", users)
    write_json(paths.data_dir / "users.json", users)

    gen_cfg = config.get("generation", {})
    profiles = extract_profiles(users, use_llm=bool(gen_cfg.get("use_llm_profile_extraction", False)))
    write_jsonl(paths.data_dir / "profiles.jsonl", profiles)
    write_json(paths.data_dir / "profiles.json", profiles)

    profile_tag_evidence = generate_profile_tag_evidence(profiles)
    write_jsonl(paths.outputs_dir / "profile_tag_evidence.jsonl", profile_tag_evidence)
    write_json(paths.outputs_dir / "profile_tag_evidence.json", profile_tag_evidence)

    interview_extraction_traces = generate_interview_extraction_traces(
        profiles,
        max_users=int(gen_cfg.get("interview_extraction_max_users", 8)),
        use_llm=bool(gen_cfg.get("use_llm_interview_extraction", False)),
        llm_max_users=int(gen_cfg.get("llm_interview_max_users", 2)),
    )
    write_jsonl(paths.outputs_dir / "interview_extraction_traces.jsonl", interview_extraction_traces)
    write_json(paths.outputs_dir / "interview_extraction_traces.json", interview_extraction_traces)

    image_rows = generate_images_for_profiles(
        profiles,
        paths.images_dir,
        provider=gen_cfg.get("image_provider", "placeholder"),
        kind=gen_cfg.get("image_kind", "lifestyle"),
        write_prompts=bool(gen_cfg.get("generate_prompt_files", True)),
    )
    write_csv(paths.data_dir / "image_assets.csv", image_rows)

    triples = build_triples(profiles)
    save_triples(paths.data_dir / "triples.csv", triples)
    export_networkx_graph(triples, paths.outputs_dir / "knowledge_graph.gexf")
    graph = ProfileGraph(triples)

    ontology_validation = generate_ontology_validation(profiles, triples)
    write_json(paths.outputs_dir / "ontology_validation.json", ontology_validation)

    embeddings = build_embeddings(profiles, image_rows, paths.indexes_dir, config)
    vector_search_traces = generate_vector_search_traces(
        profiles,
        embeddings["text"],
        embeddings["image"],
        dim=int(config.get("embedding_dim", 384)),
        top_k=min(3, len(profiles)),
        query_encoder=embeddings.get("text_embedder"),
    )
    write_jsonl(paths.outputs_dir / "vector_search_trace.jsonl", vector_search_traces)
    write_json(paths.outputs_dir / "vector_search_trace.json", vector_search_traces)

    faiss_ann_benchmark = generate_faiss_ann_benchmark(
        profiles,
        embeddings["text"],
        dim=int(config.get("embedding_dim", 384)),
        top_k=min(5, len(profiles)),
        query_encoder=embeddings.get("text_embedder"),
    )
    write_json(paths.outputs_dir / "faiss_ann_benchmark.json", faiss_ann_benchmark)

    intent_graph_traces = generate_intent_graph_traces()
    hybrid_search_traces = generate_hybrid_search_traces(
        profiles,
        embeddings["text"],
        dim=int(config.get("embedding_dim", 384)),
        query_encoder=embeddings.get("text_embedder"),
        top_k=5,
    )
    write_jsonl(paths.outputs_dir / "intent_graph_traces.jsonl", intent_graph_traces)
    write_json(paths.outputs_dir / "intent_graph_traces.json", intent_graph_traces)
    write_jsonl(paths.outputs_dir / "hybrid_search_traces.jsonl", hybrid_search_traces)
    write_json(paths.outputs_dir / "hybrid_search_traces.json", hybrid_search_traces)

    bm25_hybrid_traces = generate_bm25_hybrid_traces(
        profiles,
        embeddings["text"],
        dim=int(config.get("embedding_dim", 384)),
        query_encoder=embeddings.get("text_embedder"),
        top_k=5,
    )
    write_jsonl(paths.outputs_dir / "bm25_hybrid_traces.jsonl", bm25_hybrid_traces)
    write_json(paths.outputs_dir / "bm25_hybrid_traces.json", bm25_hybrid_traces)

    governance_records = generate_governance_records(profiles, seed=seed)
    write_jsonl(paths.outputs_dir / "governance_records.jsonl", governance_records)
    write_json(paths.outputs_dir / "governance_records.json", governance_records)

    pseudo_labels = build_pseudo_link_labels(profiles)
    write_jsonl(paths.data_dir / "pseudo_link_labels.jsonl", pseudo_labels)

    gnn_artifact = None
    gnn_risk_artifact = None
    gnn_pair_scores: list[dict[str, Any]] = []
    if run_gnn:
        gnn_artifact = train_graphsage_link_predictor(profiles, embeddings["text"], paths.outputs_dir)
        pair_scores_path = paths.outputs_dir / "gnn_pair_scores.jsonl"
        if pair_scores_path.exists():
            gnn_pair_scores = read_jsonl(pair_scores_path)
        gnn_risk_artifact = train_gcn_risk_classifier(
            profiles,
            embeddings["text"],
            governance_records,
            paths.outputs_dir,
        )

    matches = match_users(
        profiles,
        embeddings["text"],
        embeddings["image"],
        config,
        top_k=top_k,
        gnn_pair_scores=gnn_pair_scores,
    )
    if config.get("governance", {}).get("enabled", True):
        matches = apply_governance_to_matches(matches, governance_records, top_k=top_k)
    write_jsonl(paths.outputs_dir / "matches.jsonl", matches)
    write_json(paths.outputs_dir / "matches.json", matches)

    explained = explain_matches(profiles, matches, graph, use_llm=False)
    write_jsonl(paths.outputs_dir / "matches_with_explanations.jsonl", explained)
    write_json(paths.outputs_dir / "matches_with_explanations.json", explained)

    graph_algorithm_trace = generate_graph_algorithm_trace(profiles, triples, explained)
    write_json(paths.outputs_dir / "graph_algorithm_trace.json", graph_algorithm_trace)

    chat_retrieval_traces = generate_chat_retrieval_traces(
        profiles,
        explained,
        dim=int(config.get("embedding_dim", 384)),
    )
    write_jsonl(paths.outputs_dir / "chat_vector_retrieval_trace.jsonl", chat_retrieval_traces)
    write_json(paths.outputs_dir / "chat_vector_retrieval_trace.json", chat_retrieval_traces)

    rag_pipeline_traces = generate_rag_pipeline_traces(
        profiles,
        explained,
        dim=int(config.get("embedding_dim", 384)),
        use_llm=bool(gen_cfg.get("use_llm_rag_generation", False)),
        llm_max_traces=int(gen_cfg.get("llm_rag_max_traces", 4)),
        max_profiles=int(gen_cfg.get("rag_pipeline_max_profiles", 2)),
    )
    write_jsonl(paths.outputs_dir / "rag_pipeline_traces.jsonl", rag_pipeline_traces)
    write_json(paths.outputs_dir / "rag_pipeline_traces.json", rag_pipeline_traces)

    scene_cfg = config.get("scene_matching", {})
    scene_requests = generate_scene_requests(
        profiles,
        n_requests=int(scene_cfg.get("n_requests", 12)),
        seed=seed,
    )
    scene_matches = match_scene_requests(
        profiles,
        scene_requests,
        top_k=int(scene_cfg.get("top_k", 5)),
        embedding_dim=int(config.get("embedding_dim", 384)),
    )
    if config.get("governance", {}).get("enabled", True):
        scene_matches = apply_governance_to_scene_matches(
            scene_matches,
            governance_records,
            top_k=int(scene_cfg.get("top_k", 5)),
        )
    write_jsonl(paths.outputs_dir / "scene_requests.jsonl", scene_requests)
    write_json(paths.outputs_dir / "scene_requests.json", scene_requests)
    write_jsonl(paths.outputs_dir / "scene_matches.jsonl", scene_matches)
    write_json(paths.outputs_dir / "scene_matches.json", scene_matches)

    dynamics_cfg = config.get("relationship_dynamics", {})
    relationship_dynamics = generate_relationship_dynamics(
        profiles,
        matches,
        max_pairs=int(dynamics_cfg.get("max_pairs", 8)),
        days=int(dynamics_cfg.get("days", 7)),
        seed=seed,
    )
    write_jsonl(paths.outputs_dir / "relationship_dynamics.jsonl", relationship_dynamics)
    write_json(paths.outputs_dir / "relationship_dynamics.json", relationship_dynamics)

    date_cfg = config.get("date_context", {})
    date_contexts = generate_date_contexts(
        profiles,
        matches,
        max_plans=int(date_cfg.get("max_plans", 8)),
        seed=seed,
    )
    write_jsonl(paths.outputs_dir / "date_contexts.jsonl", date_contexts)
    write_json(paths.outputs_dir / "date_contexts.json", date_contexts)

    neo4j_summary = export_neo4j_trace(
        profiles,
        triples,
        paths.outputs_dir / "neo4j",
        matches=explained,
        scene_requests=scene_requests,
        scene_matches=scene_matches,
        relationship_dynamics=relationship_dynamics,
        date_contexts=date_contexts,
        governance_records=governance_records,
    )

    summary = {
        "n_users": len(profiles),
        "n_triples": len(triples),
        "n_matches": len(matches),
        "n_chat_retrieval_traces": len(chat_retrieval_traces),
        "n_rag_pipeline_traces": len(rag_pipeline_traces),
        "n_vector_search_traces": len(vector_search_traces),
        "faiss_ann_benchmark_status": faiss_ann_benchmark.get("status"),
        "n_intent_graph_traces": len(intent_graph_traces),
        "n_hybrid_search_traces": len(hybrid_search_traces),
        "n_bm25_hybrid_traces": len(bm25_hybrid_traces),
        "n_profile_tag_evidence": len(profile_tag_evidence),
        "n_interview_extraction_traces": len(interview_extraction_traces),
        "n_llm_interview_api_attempts": sum(1 for row in interview_extraction_traces if row.get("llm_attempted")),
        "n_llm_interview_extraction_traces": sum(1 for row in interview_extraction_traces if row.get("llm_used")),
        "ontology_validation_status": ontology_validation.get("status"),
        "ontology_valid_ratio": ontology_validation.get("valid_ratio"),
        "n_llm_rag_api_attempts": sum(1 for row in rag_pipeline_traces if row.get("llm_attempted")),
        "n_llm_rag_pipeline_traces": sum(1 for row in rag_pipeline_traces if row.get("llm_used")),
        "graph_algorithm_trace_status": graph_algorithm_trace.get("status"),
        "n_governance_records": len(governance_records),
        "n_scene_requests": len(scene_requests),
        "n_scene_matches": len(scene_matches),
        "n_relationship_dynamics": len(relationship_dynamics),
        "n_date_contexts": len(date_contexts),
        "neo4j_trace": neo4j_summary,
        "text_embedding_shape": list(np.asarray(embeddings["text"]).shape),
        "image_embedding_shape": list(np.asarray(embeddings["image"]).shape),
        "run_gnn": run_gnn,
        "gnn_artifact": gnn_artifact,
        "gnn_risk_artifact": gnn_risk_artifact,
        "n_gnn_pair_scores": len(gnn_pair_scores),
        "paths": {
            "data_dir": str(paths.data_dir),
            "images_dir": str(paths.images_dir),
            "indexes_dir": str(paths.indexes_dir),
            "outputs_dir": str(paths.outputs_dir),
        },
    }
    write_json(paths.outputs_dir / "pipeline_summary.json", summary)
    return summary
