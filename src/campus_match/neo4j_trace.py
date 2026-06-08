from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .io_utils import ensure_dir, write_csv, write_json


RELATION_ENTITY_LABELS = {
    "STUDIES_IN": "Major",
    "BELONGS_TO": "School",
    "LOCATED_AT": "Campus",
    "HAS_GOAL": "RelationshipGoal",
    "PREFERS_COMMUNICATION": "CommunicationStyle",
    "HAS_GENDER": "Gender",
    "PREFERS_GENDER": "Gender",
    "LIKES": "Interest",
    "VALUES": "Value",
    "HAS_PERSONALITY": "PersonalityTag",
    "AVAILABLE_AT": "TimeSlot",
    "PREFERS_DATE": "DatePreference",
    "DISLIKES": "DealBreaker",
}


NODE_FIELDS = [
    "node_id",
    "label",
    "name",
    "user_id",
    "display_name",
    "major",
    "school",
    "campus",
    "gender",
    "preferred_gender",
    "relationship_goal",
    "communication_style",
    "category",
    "status",
    "score",
    "risk_level",
    "day",
    "text",
    "description",
    "time_slot",
    "lat",
    "lon",
    "credit_score",
    "source_ref",
    "source",
]


RELATIONSHIP_FIELDS = [
    "rel_id",
    "source_id",
    "relation",
    "target_id",
    "source_name",
    "target_name",
    "rank",
    "score",
    "weight",
    "reason",
    "evidence",
    "day",
    "heat",
    "message_count",
    "avg_response_delay_min",
    "positive_ratio",
    "risk_level",
    "source_ref",
    "source",
]


def _stable_node_id(label: str, value: str) -> str:
    digest = hashlib.sha1(f"{label}:{value}".encode("utf-8")).hexdigest()[:12]
    return f"{label}_{digest}"


def _empty_node_row() -> dict[str, str]:
    return {field: "" for field in NODE_FIELDS}


def _empty_relationship_row() -> dict[str, str]:
    return {field: "" for field in RELATIONSHIP_FIELDS}


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, list | dict):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def _join(values: list[Any] | tuple[Any, ...] | set[Any] | None) -> str:
    return "、".join(str(value) for value in values or [] if value is not None)


def build_neo4j_tables(
    profiles: list[dict[str, Any]],
    triples: list[dict[str, str]],
    matches: list[dict[str, Any]] | None = None,
    scene_requests: list[dict[str, Any]] | None = None,
    scene_matches: list[dict[str, Any]] | None = None,
    relationship_dynamics: list[dict[str, Any]] | None = None,
    date_contexts: list[dict[str, Any]] | None = None,
    governance_records: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    nodes_by_id: dict[str, dict[str, str]] = {}
    profile_names = {profile["user_id"]: profile.get("display_name", profile["user_id"]) for profile in profiles}
    rel_counter = 0

    def add_node(node_id: str, label: str, name: str, **props: Any) -> str:
        if not node_id:
            node_id = _stable_node_id(label, name)
        row = nodes_by_id.get(node_id, _empty_node_row())
        row.update({"node_id": node_id, "label": label, "name": _cell(name), "source": "campus_match_ai"})
        for key, value in props.items():
            if key in row:
                row[key] = _cell(value)
        nodes_by_id[node_id] = row
        return node_id

    def add_relationship(source_id: str, relation: str, target_id: str, **props: Any) -> None:
        nonlocal rel_counter
        if not source_id or not target_id:
            return
        rel_counter += 1
        row = _empty_relationship_row()
        row.update(
            {
                "rel_id": f"REL_{rel_counter:06d}",
                "source_id": source_id,
                "relation": relation,
                "target_id": target_id,
                "source_name": _cell(props.pop("source_name", nodes_by_id.get(source_id, {}).get("name", source_id))),
                "target_name": _cell(props.pop("target_name", nodes_by_id.get(target_id, {}).get("name", target_id))),
                "source": "campus_match_ai",
            }
        )
        for key, value in props.items():
            if key in row:
                row[key] = _cell(value)
        relationships.append(row)

    for profile in profiles:
        add_node(
            profile["user_id"],
            "User",
            profile.get("display_name", profile["user_id"]),
            user_id=profile["user_id"],
            display_name=profile.get("display_name", ""),
            major=profile.get("major", ""),
            school=profile.get("school", ""),
            campus=profile.get("campus", ""),
            gender=profile.get("gender", ""),
            preferred_gender=profile.get("preferred_gender", ""),
            relationship_goal=profile.get("relationship_goal", ""),
            communication_style=profile.get("communication_style", ""),
            text=profile.get("self_intro", ""),
            description=profile.get("ideal_partner", ""),
            source_ref="data/profiles.json",
        )

    relationships: list[dict[str, str]] = []
    for triple in triples:
        relation = triple["relation"]
        label = RELATION_ENTITY_LABELS.get(relation, "KnowledgeTag")
        target_name = triple["object"]
        target_id = _stable_node_id(label, target_name)
        add_node(target_id, label, target_name, source_ref="data/triples.csv")
        add_relationship(
            triple["subject"],
            relation,
            target_id,
            source_name=profile_names.get(triple["subject"], triple["subject"]),
            target_name=target_name,
            source_ref="data/triples.csv",
        )

    for rank, match in enumerate(matches or [], start=1):
        uid = match.get("user_id", "")
        cid = match.get("candidate_id", "")
        match_id = f"MATCH_{uid}_{cid}"
        explanation = match.get("explanation", {}) or {}
        add_node(
            match_id,
            "MatchRecommendation",
            f"{uid}->{cid}",
            user_id=uid,
            score=match.get("final_score"),
            status="ranked",
            description=explanation.get("reason", ""),
            source_ref="outputs/matches_with_explanations.json",
        )
        add_relationship(uid, "HAS_MATCH_RECOMMENDATION", match_id, rank=rank, score=match.get("final_score"))
        add_relationship(match_id, "RECOMMENDS_USER", cid, score=match.get("final_score"), reason=explanation.get("reason", ""))
        add_relationship(uid, "RECOMMENDED_TO", cid, score=match.get("final_score"), reason=explanation.get("reason", ""))

        for item in match.get("common_interests", []) or []:
            target_id = add_node(_stable_node_id("Interest", item), "Interest", item, source_ref="outputs/matches_with_explanations.json")
            add_relationship(match_id, "MATCH_COMMON_INTEREST", target_id, evidence=item)
        for item in match.get("common_values", []) or []:
            target_id = add_node(_stable_node_id("Value", item), "Value", item, source_ref="outputs/matches_with_explanations.json")
            add_relationship(match_id, "MATCH_COMMON_VALUE", target_id, evidence=item)
        for item in match.get("common_dates", []) or []:
            target_id = add_node(_stable_node_id("DatePreference", item), "DatePreference", item, source_ref="outputs/matches_with_explanations.json")
            add_relationship(match_id, "MATCH_COMMON_DATE", target_id, evidence=item)
        for idx, reason in enumerate((match.get("penalty_reasons") or []) + (explanation.get("risk_notes") or []), start=1):
            reason_id = add_node(_stable_node_id("RiskReason", reason), "RiskReason", reason, risk_level="medium", source_ref="outputs/matches_with_explanations.json")
            add_relationship(match_id, "HAS_RISK_REASON", reason_id, rank=idx, reason=reason)
        for idx, prompt in enumerate(explanation.get("ice_breakers", []) or [], start=1):
            prompt_id = add_node(_stable_node_id("IceBreakerPrompt", prompt), "IceBreakerPrompt", prompt, text=prompt, source_ref="outputs/matches_with_explanations.json")
            add_relationship(match_id, "SUGGESTS_ICEBREAKER", prompt_id, rank=idx)
        for idx, path in enumerate(explanation.get("graph_paths", []) or [], start=1):
            evidence_text = path.get("path", "")
            evidence_id = add_node(_stable_node_id("GraphRAGEvidence", evidence_text), "GraphRAGEvidence", path.get("type", "路径证据"), text=evidence_text, source_ref="outputs/matches_with_explanations.json")
            add_relationship(match_id, "HAS_GRAPHRAG_PATH", evidence_id, rank=idx, evidence=evidence_text)

    request_by_id = {request.get("request_id"): request for request in scene_requests or []}
    for request in scene_requests or []:
        request_id = request.get("request_id", "")
        requester_id = request.get("requester_id", "")
        intent = request.get("intent", {}) or {}
        safety = request.get("safety_context", {}) or {}
        location = request.get("location", {}) or {}
        add_node(
            request_id,
            "SceneRequest",
            request.get("text", request_id),
            user_id=requester_id,
            category=intent.get("task_type", ""),
            status=intent.get("urgency", ""),
            risk_level=safety.get("risk_level", ""),
            text=request.get("text", ""),
            time_slot=request.get("target_time_slot", ""),
            source_ref="outputs/scene_requests.json",
        )
        add_relationship(requester_id, "POSTED_SCENE_REQUEST", request_id, reason=request.get("text", ""))
        location_name = location.get("name") or safety.get("location")
        if location_name:
            location_id = add_node(
                _stable_node_id("CampusLocation", location_name),
                "CampusLocation",
                location_name,
                campus=location.get("campus", ""),
                category=location.get("category", ""),
                risk_level=safety.get("risk_level", ""),
                description=_join(location.get("suitable_tasks", [])),
                source_ref="outputs/scene_requests.json",
            )
            add_relationship(request_id, "REQUEST_AT_LOCATION", location_id, risk_level=safety.get("risk_level", ""))
        intent_id = add_node(f"INTENT_{request_id}", "SceneIntent", intent.get("task_type", request_id), category=intent.get("task_type", ""), text=intent.get("query_text", ""), source_ref="outputs/scene_requests.json")
        safety_id = add_node(f"SAFETY_{request_id}", "SafetyContext", safety.get("location", request_id), risk_level=safety.get("risk_level", ""), description=_join(safety.get("notes", [])), source_ref="outputs/scene_requests.json")
        add_relationship(request_id, "HAS_SCENE_INTENT", intent_id, reason=intent.get("query_text", ""))
        add_relationship(request_id, "HAS_SAFETY_CONTEXT", safety_id, risk_level=safety.get("risk_level", ""))

    for rank, row in enumerate(scene_matches or [], start=1):
        request_id = row.get("request_id", "")
        candidate_id = row.get("candidate_id", "")
        rank_id = f"SCENE_MATCH_{request_id}_{candidate_id}"
        add_node(
            rank_id,
            "SceneCandidateRank",
            f"{request_id}->{candidate_id}",
            user_id=row.get("requester_id", ""),
            score=row.get("final_score"),
            status="ranked",
            risk_level=(row.get("safety_context", {}) or {}).get("risk_level", ""),
            description=row.get("scene_reason", ""),
            source_ref="outputs/scene_matches.json",
        )
        add_relationship(request_id, "HAS_SCENE_CANDIDATE", rank_id, rank=rank, score=row.get("final_score"), reason=row.get("scene_reason", ""))
        add_relationship(rank_id, "CANDIDATE_USER", candidate_id, score=row.get("final_score"))
        add_relationship(row.get("requester_id", ""), "SCENE_MATCHED_WITH", candidate_id, score=row.get("final_score"), reason=row.get("scene_reason", ""))
        req = request_by_id.get(request_id, {})
        if req:
            add_relationship(rank_id, "RANKED_FOR_REQUEST", request_id, reason=req.get("text", ""))

    for pair in relationship_dynamics or []:
        pair_id = pair.get("pair_id", "")
        summary = pair.get("heat_summary", {}) or {}
        add_node(
            pair_id,
            "RelationshipPair",
            f"{pair.get('user_id')} / {pair.get('candidate_id')}",
            user_id=pair.get("user_id", ""),
            score=pair.get("base_match_score"),
            status=summary.get("status", ""),
            description=f"avg_heat={summary.get('avg_heat', '')}; heat_delta={summary.get('heat_delta', '')}",
            source_ref="outputs/relationship_dynamics.json",
        )
        add_relationship(pair.get("user_id", ""), "HAS_RELATIONSHIP_PAIR", pair_id, score=pair.get("base_match_score"))
        add_relationship(pair_id, "PAIR_USER", pair.get("user_id", ""))
        add_relationship(pair_id, "PAIR_CANDIDATE", pair.get("candidate_id", ""))
        for topic in pair.get("common_topics", []) or []:
            topic_id = add_node(_stable_node_id("ConversationTopic", topic), "ConversationTopic", topic, source_ref="outputs/relationship_dynamics.json")
            add_relationship(pair_id, "HAS_COMMON_TOPIC", topic_id, evidence=topic)
        for point in pair.get("heat_curve", []) or []:
            day = point.get("day")
            day_id = f"CHATDAY_{pair_id}_D{day}"
            add_node(
                day_id,
                "ChatDay",
                f"{pair_id} Day {day}",
                day=day,
                score=point.get("heat"),
                status=summary.get("status", ""),
                source_ref="outputs/relationship_dynamics.json",
            )
            add_relationship(
                pair_id,
                "HAS_CHAT_DAY",
                day_id,
                day=day,
                heat=point.get("heat"),
                message_count=point.get("message_count"),
                avg_response_delay_min=point.get("avg_response_delay_min"),
                positive_ratio=point.get("positive_ratio"),
                evidence=f"shared_topic_hits={point.get('shared_topic_hits', '')}",
            )
        for idx, update in enumerate(pair.get("profile_updates", []) or [], start=1):
            tag = update.get("tag", "")
            update_id = add_node(
                f"PROFILE_UPDATE_{pair_id}_{idx}",
                "ProfileUpdate",
                tag,
                user_id=update.get("target", ""),
                category=update.get("operation", ""),
                description=update.get("evidence", ""),
                source_ref="outputs/relationship_dynamics.json",
            )
            add_relationship(pair_id, "HAS_PROFILE_UPDATE", update_id, rank=idx, evidence=update.get("evidence", ""))
            add_relationship(update_id, "AFFECTS_USER", update.get("target", ""), evidence=tag)

    for plan in date_contexts or []:
        plan_id = plan.get("plan_id", "")
        location = plan.get("location", {}) or {}
        weather = plan.get("weather", {}) or {}
        risk = plan.get("risk_assessment", {}) or {}
        lbs = plan.get("simulated_lbs", {}) or {}
        add_node(
            plan_id,
            "DatePlan",
            plan.get("date_suggestion", plan_id),
            user_id=plan.get("user_id", ""),
            time_slot=plan.get("proposed_time", ""),
            risk_level=risk.get("risk_level", ""),
            description=plan.get("date_suggestion", ""),
            source_ref="outputs/date_contexts.json",
        )
        add_relationship(plan.get("user_id", ""), "PROPOSED_DATE_PLAN", plan_id, reason=plan.get("date_suggestion", ""))
        add_relationship(plan_id, "DATE_WITH_USER", plan.get("candidate_id", ""))
        if location.get("name"):
            location_id = add_node(
                _stable_node_id("CampusLocation", location.get("name", "")),
                "CampusLocation",
                location.get("name", ""),
                campus=location.get("campus", ""),
                category=location.get("category", ""),
                risk_level=risk.get("risk_level", ""),
                lat=location.get("lat", ""),
                lon=location.get("lon", ""),
                description=_join(location.get("suitable_for", [])),
                source_ref="outputs/date_contexts.json",
            )
            add_relationship(plan_id, "DATE_AT_LOCATION", location_id, risk_level=risk.get("risk_level", ""), evidence=_cell(lbs))
        weather_id = add_node(_stable_node_id("WeatherContext", json.dumps(weather, ensure_ascii=False)), "WeatherContext", weather.get("condition", plan_id), category=weather.get("condition", ""), score=weather.get("rain_probability", ""), description=f"{weather.get('temperature_c', '')}C {weather.get('wind', '')}", source_ref="outputs/date_contexts.json")
        risk_id = add_node(f"DATE_RISK_{plan_id}", "RiskAssessment", risk.get("risk_level", plan_id), risk_level=risk.get("risk_level", ""), score=risk.get("risk_score", ""), description=_join(risk.get("reasons", [])), source_ref="outputs/date_contexts.json")
        add_relationship(plan_id, "HAS_WEATHER_CONTEXT", weather_id, score=weather.get("rain_probability", ""))
        add_relationship(plan_id, "HAS_RISK_ASSESSMENT", risk_id, risk_level=risk.get("risk_level", ""), reason=_join(risk.get("reasons", [])))

    for record in governance_records or []:
        uid = record.get("user_id", "")
        record_id = f"GOV_{uid}"
        policy = record.get("policy", {}) or {}
        add_node(
            record_id,
            "GovernanceRecord",
            f"{uid} credit {record.get('credit_score')}",
            user_id=uid,
            credit_score=record.get("credit_score"),
            status="review_required" if policy.get("review_required") else "normal",
            score=policy.get("visibility_multiplier", ""),
            description=record.get("governance_note", ""),
            source_ref="outputs/governance_records.json",
        )
        add_relationship(uid, "HAS_GOVERNANCE_RECORD", record_id, score=record.get("credit_score"))
        for event_name, count in (record.get("events", {}) or {}).items():
            if not count:
                continue
            event_id = add_node(f"GOV_EVENT_{uid}_{event_name}", "GovernanceEvent", event_name, user_id=uid, category=event_name, score=count, source_ref="outputs/governance_records.json")
            add_relationship(record_id, "HAS_GOVERNANCE_EVENT", event_id, weight=count)
        for action in policy.get("actions", []) or []:
            action_id = add_node(_stable_node_id("GovernanceAction", action), "GovernanceAction", action, category=action, source_ref="outputs/governance_records.json")
            add_relationship(record_id, "APPLIES_POLICY_ACTION", action_id, reason=action)
        for reason in policy.get("reasons", []) or []:
            reason_id = add_node(_stable_node_id("PolicyReason", reason), "PolicyReason", reason, risk_level="medium", source_ref="outputs/governance_records.json")
            add_relationship(record_id, "HAS_POLICY_REASON", reason_id, reason=reason)

    return list(nodes_by_id.values()), relationships


def _node_label_cypher(labels: list[str]) -> str:
    lines = [
        "LOAD CSV WITH HEADERS FROM 'file:///campus_match_ai_nodes.csv' AS row",
        "MERGE (n:CampusMatchNode {node_id: row.node_id})",
        "SET n += row,",
        "    n.node_label = row.label;",
        "",
    ]
    for label in labels:
        lines.extend(
            [
                "LOAD CSV WITH HEADERS FROM 'file:///campus_match_ai_nodes.csv' AS row",
                f"WITH row WHERE row.label = '{label}'",
                "MATCH (n:CampusMatchNode {node_id: row.node_id})",
                f"SET n:{label};",
                "",
            ]
        )
    return "\n".join(lines)


def _relationship_cypher(relations: list[str]) -> str:
    lines: list[str] = []
    for relation in relations:
        lines.extend(
            [
                "LOAD CSV WITH HEADERS FROM 'file:///campus_match_ai_relationships.csv' AS row",
                f"WITH row WHERE row.relation = '{relation}'",
                "MATCH (s:CampusMatchNode {node_id: row.source_id})",
                "MATCH (t:CampusMatchNode {node_id: row.target_id})",
                f"MERGE (s)-[r:{relation} {{rel_id: row.rel_id}}]->(t)",
                "SET r += row;",
                "",
            ]
        )
    return "\n".join(lines)


def build_import_cypher(node_labels: list[str], relations: list[str]) -> str:
    return "\n".join(
        [
            "// Campus Match AI Neo4j import trace.",
            "// Copy the two CSV files into Neo4j's import directory before running this file in Neo4j Browser.",
            "CREATE CONSTRAINT campus_match_node_id IF NOT EXISTS",
            "FOR (n:CampusMatchNode) REQUIRE n.node_id IS UNIQUE;",
            "",
            _node_label_cypher(node_labels),
            _relationship_cypher(relations),
        ]
    )


def build_demo_queries(sample_user_ids: list[str]) -> str:
    user_a = sample_user_ids[0] if sample_user_ids else "U001"
    user_b = sample_user_ids[1] if len(sample_user_ids) > 1 else "U002"
    return f"""// Campus Match AI Neo4j demo queries.
// 1. 查看某个用户的画像图谱邻域。
MATCH p=(u:User {{node_id: '{user_a}'}})-[r]->(x)
RETURN p
LIMIT 80;

// 2. 基于共同兴趣找候选匹配对象。
MATCH (u1:User {{node_id: '{user_a}'}})-[:LIKES]->(i:Interest)<-[:LIKES]-(u2:User)
WHERE u1 <> u2
RETURN u2.node_id AS candidate_id,
       u2.display_name AS candidate_name,
       collect(i.name) AS common_interests,
       size(collect(i)) AS score
ORDER BY score DESC
LIMIT 10;

// 3. GraphRAG 可解释路径：共同兴趣、价值观、约会偏好和关系目标。
MATCH p=(u1:User {{node_id: '{user_a}'}})-[r]->(x)<-[r2]-(u2:User {{node_id: '{user_b}'}})
WHERE type(r) = type(r2)
  AND type(r) IN ['LIKES', 'VALUES', 'PREFERS_DATE', 'HAS_GOAL', 'PREFERS_COMMUNICATION', 'AVAILABLE_AT']
RETURN p, type(r) AS evidence_type
LIMIT 30;

// 4. 查看推荐节点：分数、理由、GraphRAG 路径和风险原因。
MATCH p=(:User {{node_id: '{user_a}'}})-[:HAS_MATCH_RECOMMENDATION]->(m:MatchRecommendation)
OPTIONAL MATCH (m)-[:HAS_GRAPHRAG_PATH]->(e:GraphRAGEvidence)
OPTIONAL MATCH (m)-[:HAS_RISK_REASON]->(risk)
RETURN m.node_id AS match_id,
       m.score AS score,
       m.description AS reason,
       collect(DISTINCT e.text) AS graph_paths,
       collect(DISTINCT risk.name) AS risk_reasons
LIMIT 10;

// 5. 查看闪电搭子任务和候选排序。
MATCH p=(:User {{node_id: '{user_a}'}})-[:POSTED_SCENE_REQUEST]->(req:SceneRequest)-[:HAS_SCENE_CANDIDATE]->(rank:SceneCandidateRank)-[:CANDIDATE_USER]->(candidate:User)
RETURN req.node_id AS request_id,
       req.text AS request_text,
       candidate.display_name AS candidate_name,
       rank.score AS score,
       rank.description AS reason
ORDER BY toFloat(rank.score) DESC
LIMIT 20;

// 6. 查看 7 天聊天热度曲线。
MATCH (:User {{node_id: '{user_a}'}})-[:HAS_RELATIONSHIP_PAIR]->(pair:RelationshipPair)-[r:HAS_CHAT_DAY]->(day:ChatDay)
RETURN pair.node_id AS pair_id,
       r.day AS day,
       r.heat AS heat,
       r.message_count AS message_count,
       r.positive_ratio AS positive_ratio
ORDER BY pair_id, toInteger(day);

// 7. 检查潜在雷点：候选人的标签是否命中当前用户 DISLIKES。
MATCH (u1:User {{node_id: '{user_a}'}})-[:DISLIKES]->(bad)
MATCH (u2:User {{node_id: '{user_b}'}})-[r]->(bad)
RETURN u1.node_id AS user_id,
       u2.node_id AS candidate_id,
       bad.name AS possible_deal_breaker,
       type(r) AS candidate_relation
LIMIT 20;
"""


def export_neo4j_trace(
    profiles: list[dict[str, Any]],
    triples: list[dict[str, str]],
    output_dir: str | Path,
    matches: list[dict[str, Any]] | None = None,
    scene_requests: list[dict[str, Any]] | None = None,
    scene_matches: list[dict[str, Any]] | None = None,
    relationship_dynamics: list[dict[str, Any]] | None = None,
    date_contexts: list[dict[str, Any]] | None = None,
    governance_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    trace_dir = ensure_dir(Path(output_dir))
    nodes, relationships = build_neo4j_tables(
        profiles,
        triples,
        matches=matches,
        scene_requests=scene_requests,
        scene_matches=scene_matches,
        relationship_dynamics=relationship_dynamics,
        date_contexts=date_contexts,
        governance_records=governance_records,
    )

    nodes_csv = trace_dir / "campus_match_ai_nodes.csv"
    relationships_csv = trace_dir / "campus_match_ai_relationships.csv"
    import_cypher = trace_dir / "import_campus_match_ai.cypher"
    demo_queries = trace_dir / "demo_queries.cypher"
    summary_path = trace_dir / "neo4j_trace_summary.json"

    write_csv(nodes_csv, nodes)
    write_csv(relationships_csv, relationships)

    node_labels = sorted({row["label"] for row in nodes})
    relations = sorted({row["relation"] for row in relationships})
    import_cypher.write_text(build_import_cypher(node_labels, relations), encoding="utf-8")
    demo_queries.write_text(build_demo_queries([profile["user_id"] for profile in profiles[:2]]), encoding="utf-8")

    summary = {
        "enabled": True,
        "artifact_dir": str(trace_dir),
        "nodes_csv": str(nodes_csv),
        "relationships_csv": str(relationships_csv),
        "import_cypher": str(import_cypher),
        "demo_queries": str(demo_queries),
        "n_nodes": len(nodes),
        "n_relationships": len(relationships),
        "graph_scope": [
            "profile_triples",
            "match_recommendations",
            "graph_rag_evidence",
            "scene_requests",
            "scene_candidate_ranking",
            "relationship_heat_curve",
            "date_plans",
            "safety_context",
            "governance_records",
        ],
        "n_profile_triples": len(triples),
        "node_label_counts": dict(Counter(row["label"] for row in nodes)),
        "relationship_counts": dict(Counter(row["relation"] for row in relationships)),
        "recommended_screenshot_queries": [
            "用户画像图谱邻域",
            "推荐节点 + GraphRAG 路径 + 风险原因",
            "闪电搭子任务与候选排序",
            "7 天聊天热度曲线",
            "首约地点安全评估",
            "信用治理事件和策略动作",
        ],
    }
    write_json(summary_path, summary)
    return summary
