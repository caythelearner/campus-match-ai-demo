from __future__ import annotations

import json
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parent


@st.cache_data
def load_json(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    st.set_page_config(page_title="Campus Match AI", layout="wide")
    st.title("Campus Match AI")
    st.caption("知识图谱 + 向量检索 + 多模态 + GraphRAG 的校园匹配 demo")

    profiles = load_json(ROOT / "data/profiles.json")
    matches = load_json(ROOT / "outputs/matches_with_explanations.json")
    scene_requests = load_json(ROOT / "outputs/scene_requests.json")
    scene_matches = load_json(ROOT / "outputs/scene_matches.json")
    relationship_dynamics = load_json(ROOT / "outputs/relationship_dynamics.json")
    date_contexts = load_json(ROOT / "outputs/date_contexts.json")
    governance_records = load_json(ROOT / "outputs/governance_records.json")
    neo4j_summary = load_json(ROOT / "outputs/neo4j/neo4j_trace_summary.json")
    if not profiles or not matches:
        st.warning("还没有生成数据。请先运行：python scripts/run_pipeline.py --n-users 120 --top-k 5")
        return

    by_id = {p["user_id"]: p for p in profiles}
    governance_by_id = {g["user_id"]: g for g in governance_records} if governance_records else {}
    user_ids = [p["user_id"] for p in profiles]
    selected = st.sidebar.selectbox("选择用户", user_ids)
    user = by_id[selected]

    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.subheader("当前用户")
        image_path = ROOT / "images" / f"{selected}.png"
        if image_path.exists():
            st.image(str(image_path), caption="AI-generated synthetic image")
        st.json(
            {
                "id": user["user_id"],
                "major": user.get("major"),
                "campus": user.get("campus"),
                "goal": user.get("relationship_goal"),
                "style": user.get("communication_style"),
                "interests": user.get("interests"),
                "values": user.get("values"),
                "deal_breakers": user.get("deal_breakers"),
            }
        )
    with col_b:
        st.subheader("自我介绍")
        st.write(user.get("self_intro", ""))
        st.subheader("理想型")
        st.write(user.get("ideal_partner", ""))

    st.divider()
    st.subheader("Top 匹配推荐")
    user_matches = [m for m in matches if m["user_id"] == selected]
    if not user_matches:
        st.info("当前用户没有匹配结果。")
        return

    for match in user_matches:
        candidate = by_id[match["candidate_id"]]
        with st.expander(f"{candidate['display_name']} / {candidate['major']} / score={match['final_score']}", expanded=True):
            c1, c2, c3 = st.columns([1, 2, 2])
            with c1:
                candidate_image = ROOT / "images" / f"{candidate['user_id']}.png"
                if candidate_image.exists():
                    st.image(str(candidate_image), caption=candidate["user_id"])
            with c2:
                st.write("**共同兴趣**", "、".join(match.get("common_interests", [])) or "无")
                st.write("**共同价值观**", "、".join(match.get("common_values", [])) or "无")
                st.write("**共同约会偏好**", "、".join(match.get("common_dates", [])) or "无")
                st.write("**候选人简介**", candidate.get("self_intro", ""))
                gov = match.get("candidate_governance", {})
                if gov:
                    st.write("**知识治理/信用策略**")
                    st.write(f"信用分：{gov.get('credit_score', 100)}")
                    st.write(f"推荐降权：{match.get('governance_penalty', 0)}")
                    policy = gov.get("policy", {})
                    if policy.get("conditional_mute"):
                        st.warning("该候选触发条件禁言/人工复核策略")
                    for reason in policy.get("reasons", []):
                        st.write("- " + reason)
            with c3:
                exp = match.get("explanation", {})
                st.write("**推荐理由**")
                st.write(exp.get("reason", ""))
                st.write("**风险提示**")
                for item in exp.get("risk_notes", []):
                    st.write("- " + item)
                st.write("**破冰话题**")
                for item in exp.get("ice_breakers", []):
                    st.write("- " + item)
            with st.popover("查看 GraphRAG 路径证据"):
                st.json(match.get("explanation", {}).get("graph_paths", []))

    st.divider()
    st.subheader("Neo4j 图数据库留痕")
    st.caption("pipeline 默认生成 Neo4j 节点/关系 CSV、导入 Cypher 和查询 Cypher；本机装好 Neo4j 后可一键导入并截图。")
    if neo4j_summary:
        neo4j_col_a, neo4j_col_b = st.columns(2)
        with neo4j_col_a:
            st.write("**图谱规模**")
            st.json(
                {
                    "nodes": neo4j_summary.get("n_nodes"),
                    "relationships": neo4j_summary.get("n_relationships"),
                    "node_label_counts": neo4j_summary.get("node_label_counts"),
                }
            )
        with neo4j_col_b:
            st.write("**留痕文件**")
            st.code(
                "\n".join(
                    [
                        "outputs/neo4j/campus_match_ai_nodes.csv",
                        "outputs/neo4j/campus_match_ai_relationships.csv",
                        "outputs/neo4j/import_campus_match_ai.cypher",
                        "outputs/neo4j/demo_queries.cypher",
                    ]
                )
            )
            st.write("**导入命令**")
            st.code(
                "python scripts/import_neo4j.py --uri bolt://localhost:7687 --user neo4j --password 你的密码 --clear",
                language="bash",
            )
        st.write("**建议截图查询**")
        for item in neo4j_summary.get("recommended_screenshot_queries", []):
            st.write("- " + item)
    else:
        st.info("当前没有 Neo4j 留痕摘要。请重新运行 pipeline。")

    st.divider()
    st.subheader("闪电搭子：动态场景任务匹配")
    st.caption("模拟 LBS、当前空闲时间、具体任务、场景意图和地点安全属性，体现动态性、时变和场景化。")
    if not scene_requests or not scene_matches:
        st.info("当前没有场景任务数据。请重新运行 pipeline。")
        return

    request_options = [
        f"{r['request_id']} / {r['requester_id']} / {r['intent']['task_type']} / {r['target_time_slot']}"
        for r in scene_requests
    ]
    selected_request_label = st.selectbox("选择一个动态任务", request_options)
    selected_request_id = selected_request_label.split(" / ", 1)[0]
    request = next(r for r in scene_requests if r["request_id"] == selected_request_id)

    req_col_a, req_col_b = st.columns(2)
    with req_col_a:
        st.write("**实时流文本**")
        st.write(request["text"])
        st.write("**动态因子**")
        st.json(request["dynamic_factors"])
    with req_col_b:
        st.write("**地点安全上下文**")
        st.json(request["safety_context"])

    st.write("**候选搭子排序**")
    request_matches = [m for m in scene_matches if m["request_id"] == selected_request_id]
    for row in request_matches:
        candidate = by_id[row["candidate_id"]]
        with st.expander(f"{candidate['display_name']} / scene_score={row['final_score']}"):
            st.write(row["scene_reason"])
            gov = row.get("candidate_governance", {})
            if gov:
                st.write("**治理策略**")
                st.write(f"信用分：{gov.get('credit_score', 100)} / 降权：{row.get('governance_penalty', 0)}")
                policy = gov.get("policy", {})
                if policy.get("cooldown_hours"):
                    st.write(f"闪电搭子冷却：{policy['cooldown_hours']} 小时")
                if policy.get("conditional_mute"):
                    st.warning("该候选触发条件禁言/人工复核策略")
            st.json(
                {
                    "semantic_score": row["semantic_score"],
                    "time_score": row["time_score"],
                    "location_score": row["location_score"],
                    "task_score": row["task_score"],
                    "care_score": row["care_score"],
                }
            )

    st.divider()
    st.subheader("恋爱动态：热度曲线与画像更新")
    st.caption("使用合成聊天聚合指标模拟关系热度变化，不读取真实聊天内容。")
    if relationship_dynamics:
        dynamic_options = [
            f"{item['pair_id']} / {item['user_id']} - {item['candidate_id']} / {item['heat_summary']['status']}"
            for item in relationship_dynamics
        ]
        selected_dynamic_label = st.selectbox("选择一组互动关系", dynamic_options)
        selected_pair_id = selected_dynamic_label.split(" / ", 1)[0]
        dynamic = next(item for item in relationship_dynamics if item["pair_id"] == selected_pair_id)
        heat_points = [{"day": p["day"], "heat": p["heat"]} for p in dynamic["heat_curve"]]
        st.write("**热度摘要**")
        st.json(dynamic["heat_summary"])
        st.write("**热度曲线数据**")
        st.line_chart([point["heat"] for point in heat_points])
        st.write("**共同话题**", "、".join(dynamic.get("common_topics", [])))
        st.write("**画像更新信号**")
        if dynamic.get("profile_updates"):
            for update in dynamic["profile_updates"]:
                st.write(f"- `{update['target']}` {update['operation']} `{update['tag']}`：{update['evidence']}")
        else:
            st.write("暂无明显画像更新信号。")
        st.caption(dynamic.get("privacy_note", ""))
    else:
        st.info("当前没有恋爱动态数据。请重新运行 pipeline。")

    st.divider()
    st.subheader("线下约会：位置/天气/安全上下文")
    st.caption("默认使用模拟 LBS 与天气；真实系统必须用户授权，并只保留必要上下文。")
    if date_contexts:
        date_options = [
            f"{item['plan_id']} / {item['user_id']} - {item['candidate_id']} / {item['risk_assessment']['risk_level']}"
            for item in date_contexts
        ]
        selected_date_label = st.selectbox("选择一个线下约会方案", date_options)
        selected_plan_id = selected_date_label.split(" / ", 1)[0]
        plan = next(item for item in date_contexts if item["plan_id"] == selected_plan_id)
        plan_col_a, plan_col_b = st.columns(2)
        with plan_col_a:
            st.write("**地点与时间**")
            st.json(
                {
                    "proposed_time": plan["proposed_time"],
                    "location": plan["location"],
                    "simulated_lbs": plan["simulated_lbs"],
                }
            )
        with plan_col_b:
            st.write("**天气与风险**")
            st.json(
                {
                    "weather": plan["weather"],
                    "risk_assessment": plan["risk_assessment"],
                }
            )
        st.write("**RAG 风格建议**")
        st.write(plan["date_suggestion"])
        st.caption(plan.get("privacy_note", ""))
    else:
        st.info("当前没有线下约会上下文数据。请重新运行 pipeline。")

    st.divider()
    st.subheader("知识治理：信用分、推荐降权与条件禁言")
    st.caption("使用合成失约/不适反馈事件演示治理策略；真实系统需要人工审核和申诉机制。")
    if governance_by_id:
        gov = governance_by_id.get(selected)
        if gov:
            st.json(gov)
        flagged = [
            item
            for item in governance_records
            if item["policy"].get("conditional_mute") or item["policy"].get("visibility_multiplier", 1.0) < 1.0
        ]
        st.write(f"触发治理策略用户数：{len(flagged)} / {len(governance_records)}")
        for item in flagged[:5]:
            st.write(
                f"- `{item['user_id']}` credit={item['credit_score']} "
                f"visibility={item['policy']['visibility_multiplier']} "
                f"actions={', '.join(item['policy'].get('actions', [])) or 'none'}"
            )


if __name__ == "__main__":
    main()
