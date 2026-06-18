# Campus Match AI 核心技术代码包

这个文件夹是为了汇报和复核整理的“关键代码包”。它不是新实现，也不是伪代码，而是从项目正式源码中复制出来的核心模块副本，方便集中查看五条技术链路。

正式运行仍以原始源码为准：

- 主源码：`src/campus_match/`
- 运行入口：`scripts/run_pipeline.py`
- 静态 demo 生成：`scripts/build_html_demo.py`
- 输出 trace：`outputs/`
- 公网页面：`demo/index.html`

## 0. 全链路入口

文件：

- `00_pipeline_entry/run_pipeline.py`
- `00_pipeline_entry/pipeline.py`
- `00_pipeline_entry/default.json`

核心入口：

- `run_pipeline.py` 调用 `campus_match.pipeline.run_pipeline(...)`
- `pipeline.py` 从用户生成开始，依次跑画像、访谈抽取、图谱、向量、召回、GNN、RAG、闪电搭子、Neo4j 导出

重新跑全链路：

```bash
cd /data/newanyue/CampusMatchAI/campus_match_ai
python scripts/run_pipeline.py --run-gnn
python scripts/build_html_demo.py
```

关键输出：

- `outputs/pipeline_summary.json`
- `demo/index.html`

## 1. 抽取实体

文件：

- `01_entity_extraction/interview_extraction.py`

核心函数：

- `_interview_sentences(profile)`：把用户画像转成 4 轮模拟访谈
- `_build_llm_prompt(profile, sentences)`：构造 LLM 实体关系抽取 prompt
- `_llm_extract_interview(...)`：有 API 时让模型输出 JSON
- `_rule_extract_interview(...)`：无 API 时按字段和文本命中规则抽实体
- `generate_interview_extraction_traces(...)`：统一生成 trace

处理逻辑：

1. 每个用户先生成 4 轮问答：兴趣、价值观、首约偏好、雷点。
2. 抽取实体类型：`Interest`、`Value`、`RelationshipGoal`、`CommunicationStyle`、`TimeSlot`、`DatePreference`、`DealBreaker`、`Campus`、`Major`。
3. 抽取关系：`LIKES`、`VALUES`、`HAS_GOAL`、`PREFERS_COMMUNICATION`、`AVAILABLE_AT`、`PREFERS_DATE`、`DISLIKES`、`LOCATED_AT`、`STUDIES_IN`。
4. API 可用时用 LLM JSON 抽取；API 不可用时用本地规则兜底。

输出：

- `outputs/interview_extraction_traces.json`
- `outputs/interview_extraction_traces.jsonl`

后台展示：

- `管理员后台 -> 访谈抽取`

## 2. 图谱写入

文件：

- `02_graph_write/kg.py`
- `02_graph_write/ontology.py`
- `02_graph_write/neo4j_trace.py`
- `02_graph_write/import_neo4j.py`

核心函数：

- `kg.py -> build_triples(profiles)`：把画像字段转成三元组
- `kg.py -> ProfileGraph(...)`：把三元组组织成可查共同邻居的图
- `ontology.py -> generate_ontology_validation(...)`：检查关系类型和实体类型是否合法
- `neo4j_trace.py -> export_neo4j_trace(...)`：导出 Neo4j 节点、关系和 Cypher
- `import_neo4j.py`：把 CSV/Cypher 真导入 Neo4j 数据库

处理逻辑：

1. 用户画像字段先写成 `User -> Entity` 三元组。
2. 本体校验检查 domain/range，例如 `User - LIKES -> Interest` 合法，不能乱连。
3. Neo4j 产品图不只包含画像，还包含推荐、GraphRAG 证据、闪电搭子、关系热度、首约安全和治理记录。
4. 前端图谱和 Neo4j CSV/Cypher 使用同一批导出数据。

输出：

- `data/triples.csv`
- `outputs/ontology_validation.json`
- `outputs/neo4j/campus_match_ai_nodes.csv`
- `outputs/neo4j/campus_match_ai_relationships.csv`
- `outputs/neo4j/import_campus_match_ai.cypher`
- `outputs/neo4j/demo_queries.cypher`
- `outputs/neo4j/neo4j_trace_summary.json`

真导入 Neo4j：

```bash
python scripts/import_neo4j.py --uri bolt://localhost:7687 --user neo4j --password 你的密码 --clear
```

后台展示：

- `管理员后台 -> Neo4j图谱`
- `管理员后台 -> 技术证据`

## 3. 四路召回

文件：

- `03_four_way_retrieval/intent_search.py`
- `03_four_way_retrieval/bm25_hybrid.py`
- `03_four_way_retrieval/vector_search.py`
- `03_four_way_retrieval/embeddings.py`

核心函数：

- `intent_search.py -> analyze_query_intent(query)`：Text-to-Graph，把自然语言需求拆成显性需求、隐性意图、画像字段、硬条件
- `intent_search.py -> generate_hybrid_search_traces(...)`：Vector + Sparse + Graph + Constraint 加权召回
- `bm25_hybrid.py -> generate_bm25_hybrid_traces(...)`：BM25 + Dense + Graph + Constraint 四路融合
- `embeddings.py -> build_embeddings(...)`：生成文本向量和图片向量
- `vector_search.py -> generate_faiss_ann_benchmark(...)`：Flat / IVF / HNSW 对比

处理逻辑：

1. Query 先做 Text-to-Graph。例如“想找个会弹吉他的阳光学长”会拆出：
   - 显性需求：会弹吉他、偏好男生
   - 隐性意图：音乐技能、艺术细胞、外向主动
   - 画像字段：古典音乐、Livehouse、音乐节、male 等
   - 硬条件：性别偏好男生
2. BM25 负责精确词命中。
3. Dense 向量负责语义相似。
4. Graph 负责画像字段和图谱扩展命中。
5. Constraint 负责硬条件，防止向量相似度盖过明确需求。

主要权重：

- `intent_search.py`：`vector 0.34 + sparse 0.24 + graph 0.28 + constraint 0.14`
- `bm25_hybrid.py`：`bm25 0.30 + dense 0.32 + graph 0.26 + constraint 0.12`
- BM25 参数：`k1=1.5`，`b=0.75`

输出：

- `outputs/intent_graph_traces.json`
- `outputs/hybrid_search_traces.json`
- `outputs/bm25_hybrid_traces.json`
- `outputs/vector_search_trace.json`
- `outputs/faiss_ann_benchmark.json`
- `indexes/text_embeddings.npy`
- `indexes/text_flat.index`

后台展示：

- `管理员后台 -> 技术证据`
- `用户端 -> 雷达`

## 4. 潜在链接预测

文件：

- `04_link_prediction/gnn.py`
- `04_link_prediction/matching.py`

核心函数：

- `gnn.py -> build_pseudo_link_labels(profiles)`：构造可解释伪标签
- `gnn.py -> train_graphsage_link_predictor(...)`：训练 GraphSAGE 链接预测
- `gnn.py -> train_gcn_risk_classifier(...)`：训练 GCN 风险节点分类
- `matching.py -> match_users(...)`：把 `gnn_link_score` 融入最终推荐排序

处理逻辑：

1. 构建用户-属性图：用户节点连接兴趣、价值观、目标、沟通方式、时间、校区等属性节点。
2. 用户节点特征来自文本向量；属性节点使用 deterministic hash embedding。
3. 没有真实恋爱成功标签，所以用共同兴趣、共同价值观、关系目标一致等规则构造伪标签。
4. GraphSAGE 学习用户和邻居属性的表示，输出用户对之间的 `gnn_link_score`。
5. `matching.py` 里把这个分数按权重接入最终匹配分。

匹配公式位置：

- `04_link_prediction/matching.py -> match_users(...)`

默认匹配权重：

- `text_similarity 0.27`
- `graph_similarity 0.22`
- `value_similarity 0.18`
- `goal_match 0.10`
- `communication_match 0.05`
- `image_similarity 0.08`
- `gnn_link_score 0.10`

输出：

- `outputs/graphsage_link_predictor.pt`
- `outputs/gnn_metrics.json`
- `outputs/gnn_pair_scores.json`
- `outputs/gcn_risk_classifier.pt`
- `outputs/gnn_node_risk_scores.json`

后台展示：

- `管理员后台 -> 技术证据`
- `管理员后台 -> 匹配推荐`

## 5. 聊天 RAG 检索

文件：

- `05_chat_rag/chat_retrieval.py`
- `05_chat_rag/rag_pipeline.py`
- `05_chat_rag/realtime_rag.py`

核心函数：

- `chat_retrieval.py -> _retrieve(...)`：对聊天知识库和画像上下文做 Top-K 检索
- `rag_pipeline.py -> _rewrite_query(query)`：query rewrite + router
- `rag_pipeline.py -> _compress_context(...)`：压缩 Top-K 证据
- `rag_pipeline.py -> _llm_generate_answer(...)`：用检索证据生成回复
- `rag_pipeline.py -> _verify(...)`：安全校验，防止编活动名、越界语气、线下安全证据不足
- `realtime_rag.py -> generate_realtime_chat_rag(...)`：服务端实时 RAG 入口

处理逻辑：

1. 用户消息先进 `query rewrite`，变成更适合检索的查询。
2. `router` 判断意图：破冰、活动推荐、情绪照顾、首约安全、闪电搭子。
3. 从画像、匹配理由、破冰库、活动库、安全库里取 Top-K。
4. 压缩证据，只保留 doc_id、标题、证据、建议、分数。
5. 有 API 时用 LLM 结合证据生成一句自然回复；无 API 时使用检索模板。
6. safety verifier 检查是否编造活动、语气过强、线下安全证据不足。

输出：

- `outputs/chat_vector_retrieval_trace.json`
- `outputs/rag_pipeline_traces.json`
- `outputs/realtime_chat_api_traces.jsonl`

后台展示：

- `管理员后台 -> API Trace`
- `管理员后台 -> 技术证据`
- `用户端 -> 消息`

## 这 5 个模块和公网 demo 的关系

公网 `demo/index.html` 不重新训练模型，也不现场导入 Neo4j。它把上述输出 trace 和 CSV 数据打包成静态页面展示：

- 构建脚本：`scripts/build_html_demo.py`
- 读取输出：`outputs/*.json`、`outputs/neo4j/*.csv`
- 最终页面：`demo/index.html`

因此，公网页面展示的是已经跑过的结果；真正算法实现仍然在本文件夹对应的源码副本和项目原始源码中。
