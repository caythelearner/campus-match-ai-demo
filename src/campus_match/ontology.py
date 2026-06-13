from __future__ import annotations

from collections import Counter
from typing import Any

from .interview_extraction import ENTITY_TYPE_BY_FIELD, RELATION_BY_FIELD


ONTOLOGY_CLASSES = [
    {"id": "User", "description": "校园用户主体，所有画像关系从 User 发出。"},
    {"id": "School", "description": "学院或所属院系。"},
    {"id": "Gender", "description": "用户性别或期待匹配对象性别。"},
    {"id": "Interest", "description": "兴趣或活动偏好，如剧本杀、编程、羽毛球。"},
    {"id": "Value", "description": "关系价值观，如边界感、真诚、共同进步。"},
    {"id": "PersonalityTag", "description": "人格、沟通和相处倾向标签。"},
    {"id": "RelationshipGoal", "description": "长期关系、认真了解、轻松社交等目标。"},
    {"id": "CommunicationStyle", "description": "慢热、外向主动、尊重空间等沟通方式。"},
    {"id": "TimeSlot", "description": "可用时间窗口。"},
    {"id": "DatePreference", "description": "理想约会/见面方式。"},
    {"id": "DealBreaker", "description": "雷点或不适合项。"},
    {"id": "Campus", "description": "校区或主要活动空间。"},
    {"id": "Major", "description": "专业背景。"},
]


KG_EXTRA_RELATIONS = [
    {"relation": "BELONGS_TO", "domain": "User", "range": "School", "field": "school"},
    {"relation": "HAS_GENDER", "domain": "User", "range": "Gender", "field": "gender"},
    {"relation": "PREFERS_GENDER", "domain": "User", "range": "Gender", "field": "preferred_gender"},
    {"relation": "HAS_PERSONALITY", "domain": "User", "range": "PersonalityTag", "field": "personality_tags"},
]


ONTOLOGY_RELATIONS = KG_EXTRA_RELATIONS + [
    {"relation": relation, "domain": "User", "range": ENTITY_TYPE_BY_FIELD[field], "field": field}
    for field, relation in RELATION_BY_FIELD.items()
]


def _profile_values(profile: dict[str, Any], field: str) -> set[str]:
    value = profile.get(field)
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(item) for item in value}
    return {str(value)}


def generate_ontology_validation(
    profiles: list[dict[str, Any]],
    triples: list[dict[str, str]],
) -> dict[str, Any]:
    user_ids = {profile["user_id"] for profile in profiles}
    profile_by_id = {profile["user_id"]: profile for profile in profiles}
    relation_to_rule = {row["relation"]: row for row in ONTOLOGY_RELATIONS}
    violations: list[dict[str, Any]] = []
    valid = 0
    coverage: Counter[str] = Counter()

    for triple in triples:
        subject = triple.get("subject", "")
        relation = triple.get("relation", "")
        obj = triple.get("object", "")
        rule = relation_to_rule.get(relation)
        if not rule:
            violations.append({"triple": triple, "reason": "关系不在本体 schema 中"})
            continue
        if subject not in user_ids:
            violations.append({"triple": triple, "reason": "subject 不是 User"})
            continue
        field = rule["field"]
        if obj not in _profile_values(profile_by_id[subject], field):
            violations.append({"triple": triple, "reason": f"object 未出现在用户画像字段 {field} 中"})
            continue
        valid += 1
        coverage[relation] += 1

    class_coverage = Counter()
    for relation, count in coverage.items():
        rule = relation_to_rule[relation]
        class_coverage[rule["range"]] += count
    class_coverage["User"] = len(user_ids)

    return {
        "status": "ok" if not violations else "partial",
        "ontology_classes": ONTOLOGY_CLASSES,
        "ontology_relations": ONTOLOGY_RELATIONS,
        "n_triples_checked": len(triples),
        "n_valid_triples": valid,
        "n_violations": len(violations),
        "valid_ratio": round(valid / max(len(triples), 1), 4),
        "relation_coverage": dict(coverage),
        "class_coverage": dict(class_coverage),
        "sample_violations": violations[:12],
        "schema_summary": "User 只能通过受控关系连接到 Interest/Value/Goal/Time/Date/DealBreaker/Campus/Major，避免图谱乱连。",
    }
