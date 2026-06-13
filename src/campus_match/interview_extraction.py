from __future__ import annotations

import json
from typing import Any

from .llm_client import call_llm_text, llm_config_status, parse_json_response


RELATION_BY_FIELD = {
    "interests": "LIKES",
    "values": "VALUES",
    "relationship_goal": "HAS_GOAL",
    "communication_style": "PREFERS_COMMUNICATION",
    "available_time": "AVAILABLE_AT",
    "preferred_date": "PREFERS_DATE",
    "deal_breakers": "DISLIKES",
    "campus": "LOCATED_AT",
    "major": "STUDIES_IN",
}


ENTITY_TYPE_BY_FIELD = {
    "interests": "Interest",
    "values": "Value",
    "relationship_goal": "RelationshipGoal",
    "communication_style": "CommunicationStyle",
    "available_time": "TimeSlot",
    "preferred_date": "DatePreference",
    "deal_breakers": "DealBreaker",
    "campus": "Campus",
    "major": "Major",
}


def _interview_sentences(profile: dict[str, Any]) -> list[dict[str, Any]]:
    interests = profile.get("interests", [])[:3]
    values = profile.get("values", [])[:3]
    dates = profile.get("preferred_date", [])[:2]
    times = profile.get("available_time", [])[:2]
    breakers = profile.get("deal_breakers", [])[:2]
    return [
        {
            "question": "你平时最容易投入的事情是什么？",
            "answer": f"我平时比较喜欢{'、'.join(interests)}，如果有人也喜欢这些，会更容易聊起来。",
            "fields": ["interests"],
        },
        {
            "question": "你希望一段关系里最重要的东西是什么？",
            "answer": f"我会比较在意{'、'.join(values)}，关系目标更偏向{profile.get('relationship_goal')}。",
            "fields": ["values", "relationship_goal"],
        },
        {
            "question": "第一次见面你会觉得怎样比较舒服？",
            "answer": f"我更能接受{'、'.join(dates)}，通常{profile.get('communication_style')}，空闲时间主要是{'、'.join(times)}。",
            "fields": ["preferred_date", "communication_style", "available_time"],
        },
        {
            "question": "相处中有什么明显雷点？",
            "answer": f"我不太能接受{'、'.join(breakers)}，也希望对方理解我在{profile.get('campus')}活动比较多。",
            "fields": ["deal_breakers", "campus"],
        },
    ]


def _field_values(profile: dict[str, Any], field: str) -> list[str]:
    value = profile.get(field)
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _build_llm_prompt(profile: dict[str, Any], sentences: list[dict[str, Any]]) -> str:
    return f"""你是校园社交应用的信息抽取助手。

请只基于访谈文本抽取实体和三元组，不要编造。
输出合法 JSON，字段：
- extracted_entities: list，每项包含 text, entity_type, source_sentence, field, normalization
- extracted_triples: list，每项包含 subject, relation, object, object_type, source_sentence, confidence

允许的 relation：
LIKES, VALUES, HAS_GOAL, PREFERS_COMMUNICATION, AVAILABLE_AT, PREFERS_DATE, DISLIKES, LOCATED_AT, STUDIES_IN

用户 ID：{profile["user_id"]}
访谈文本：
{json.dumps(sentences, ensure_ascii=False, indent=2)}
"""


def _llm_extract_interview(profile: dict[str, Any], sentences: list[dict[str, Any]]) -> dict[str, Any] | None:
    content = call_llm_text(
        system="你是严格输出 JSON 的实体关系抽取助手。",
        user=_build_llm_prompt(profile, sentences),
        temperature=0.1,
        max_tokens=1200,
    )
    if not content:
        return None
    data = parse_json_response(content)
    if not isinstance(data.get("extracted_entities"), list) or not isinstance(data.get("extracted_triples"), list):
        return None
    return data


def _rule_extract_interview(profile: dict[str, Any], sentences: list[dict[str, Any]]) -> dict[str, Any]:
    extracted_entities: list[dict[str, Any]] = []
    extracted_triples: list[dict[str, Any]] = []
    highlights: list[dict[str, Any]] = []
    for sentence_idx, sentence in enumerate(sentences, 1):
        answer = sentence["answer"]
        for field in sentence["fields"]:
            relation = RELATION_BY_FIELD[field]
            entity_type = ENTITY_TYPE_BY_FIELD[field]
            for value in _field_values(profile, field):
                if value and value in answer:
                    extracted_entities.append(
                        {
                            "text": value,
                            "entity_type": entity_type,
                            "source_sentence": sentence_idx,
                            "field": field,
                            "normalization": value,
                        }
                    )
                    extracted_triples.append(
                        {
                            "subject": profile["user_id"],
                            "relation": relation,
                            "object": value,
                            "object_type": entity_type,
                            "source_sentence": sentence_idx,
                            "confidence": 0.92 if field in {"values", "relationship_goal", "communication_style"} else 0.86,
                        }
                    )
                    highlights.append({"sentence": sentence_idx, "span": value, "relation": relation})
    return {
        "extracted_entities": extracted_entities,
        "extracted_triples": extracted_triples,
        "highlights": highlights,
    }


def generate_interview_extraction_traces(
    profiles: list[dict[str, Any]],
    max_users: int = 8,
    use_llm: bool = False,
    llm_max_users: int = 2,
) -> list[dict[str, Any]]:
    traces: list[dict[str, Any]] = []
    llm_status = llm_config_status()
    for profile in profiles[:max_users]:
        sentences = _interview_sentences(profile)
        result = _rule_extract_interview(profile, sentences)
        llm_attempted = False
        llm_used = False
        llm_error = ""
        if use_llm and llm_status["configured"] and len(traces) < llm_max_users:
            llm_attempted = True
            try:
                llm_result = _llm_extract_interview(profile, sentences)
                if llm_result:
                    result["rule_extracted_entities"] = result["extracted_entities"]
                    result["rule_extracted_triples"] = result["extracted_triples"]
                    result["extracted_entities"] = llm_result["extracted_entities"]
                    result["extracted_triples"] = llm_result["extracted_triples"]
                    result["highlights"] = [
                        {
                            "sentence": triple.get("source_sentence"),
                            "span": triple.get("object"),
                            "relation": triple.get("relation"),
                        }
                        for triple in llm_result["extracted_triples"]
                    ]
                    llm_used = True
            except Exception as exc:  # noqa: BLE001
                llm_error = str(exc)
        traces.append(
            {
                "trace_id": f"INTERVIEW_TRACE_{len(traces) + 1:03d}",
                "user_id": profile["user_id"],
                "display_name": profile.get("display_name", profile["user_id"]),
                "raw_interview": sentences,
                "extracted_entities": result["extracted_entities"],
                "extracted_triples": result["extracted_triples"],
                "rule_extracted_entities": result.get("rule_extracted_entities", []),
                "rule_extracted_triples": result.get("rule_extracted_triples", []),
                "highlights": result["highlights"],
                "extraction_method": "llm_api_json" if llm_used else "rule_based_fallback",
                "llm_attempted": llm_attempted,
                "llm_used": llm_used,
                "llm_provider": llm_status["provider"] if llm_attempted else "",
                "llm_model": llm_status["model"] if llm_attempted else "",
                "llm_error": llm_error,
                "pipeline_steps": [
                    "模拟访谈原文",
                    "LLM JSON 抽取或本地字段触发实体识别",
                    "实体归一化到画像字段",
                    "按本体关系生成三元组",
                    "进入 Neo4j User-Entity 产品图",
                ],
                "status": "llm_entity_relation_extraction" if llm_used else "rule_based_entity_relation_extraction",
            }
        )
    return traces
