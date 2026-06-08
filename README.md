# Campus Match AI

面向课程项目的校园同学匹配系统代码骨架。

更新时间：2026-06-06

当前状态：本机 demo、Neo4j 留痕、分任务文档和桌面交付文件夹均已准备好。

桌面交付路径：

```text
C:\Users\cheng\Desktop\CampusMatchAI_小组作业_最新
```

定位：

> 用合成问卷模拟校园用户画像，结合知识图谱、向量检索、多模态图片、图计算/GNN 和 GraphRAG，完成可解释的 dating app 匹配推荐 demo。

## 1. 当前代码能做什么

默认离线可跑，不需要 API key：

1. 生成合成问卷用户。
2. 抽取/规范化结构化用户画像。
3. 生成合成图片占位图和图片 prompt。
4. 构建用户-兴趣-价值观-活动知识图谱三元组。
5. 生成文本 embedding 和图片 embedding。
6. 建 FAISS index，如果本机有 faiss。
7. 计算匹配分数。
8. 生成 GraphRAG 风格推荐解释。
9. 生成“闪电搭子”动态场景任务匹配。
10. 生成知识治理策略，包括信用分、推荐降权、冷却和条件禁言。
11. 生成恋爱热度曲线、画像更新信号和线下约会场景上下文。
12. 生成 Neo4j 图数据库留痕文件，包括节点 CSV、关系 CSV、导入 Cypher 和查询 Cypher。
13. 启动 Streamlit demo 查看结果。

可选增强：

1. 接入图像生成 API，替换占位图。
2. 接入 LLM API，替换模板解释和规则抽取。
3. 使用 sentence-transformers 替换 hash embedding。
4. 使用 CLIP 替换颜色直方图图片 embedding。
5. 使用 A100 训练 GraphSAGE 链接预测模型。
6. 将知识图谱导入本机 Neo4j，截图展示图谱路径和查询结果。

## 2. 快速开始

建议先在项目目录中运行：

```bash
cd campus_match_ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_pipeline.py --n-users 120 --top-k 5
streamlit run app.py
```

如果只是先验证默认代码，不想装全部深度学习依赖，可以先装最小依赖：

```bash
pip install numpy pillow requests streamlit networkx
python scripts/run_pipeline.py --n-users 30 --top-k 3
streamlit run app.py
```

生成 5 人静态 HTML 前端 demo：

```bash
pip install numpy pillow requests networkx
CUDA_VISIBLE_DEVICES=0 python scripts/run_pipeline.py --n-users 5 --top-k 3
python scripts/build_html_demo.py
```

然后在浏览器打开：

```text
demo/index.html
```

打开后先选择两个版本之一：

1. 管理员后台：查看全部用户数据、功能总览、课件对应、匹配分数、GraphRAG 路径、闪电搭子、关系热度、线下安全、知识治理和 Neo4j 留痕。
   - 默认进入“星图看板”：包含一张由 5 人画像、兴趣、价值观、校区、关系目标和匹配边生成的知识星图。
   - 看板同时展示关系热度轨道、闪电搭子场景、治理风险、核心 KPI 和从注册到记忆博物馆的产品流。
2. 用户体验版：选择成为某个用户，按产品动线进入四个 Tab：
   - 星球：顶部切换“心动星球 / 闪电搭子”，查看推荐人、右划心动、加入临时搭子聊天。
   - 雷达：广场搜索、热门 Tag 筛选、AI 语义联想、寻人启事墙和发起私聊。
   - 消息：推荐对象聊天室、AI 僚机、情绪气象站、共鸣实验室破冰话术和预设回复。
   - 档案：灵魂卡片、可点击标签证据、记忆博物馆、聊天热度周报和星际信用。
   输入一句当天想法后，页面会推进天数、热度、信用分和画像标签。

鲁棒性规则：

1. 用户体验最多 7 天，Day 7 完成后进入只读总结态，不能继续点击推进。
2. 每天最多 3 轮自由聊天，避免无限点击刷进度；点击“完成今天”后进入下一天并重置当天聊天次数。
3. 用户体验版只展示当前用户能看到的推荐、聊天、AI 僚机提示和安全提醒；课件对应、全局状态、治理和监控数据放在管理员后台。
4. 管理员后台新增“每日状态”，可按 Day 1-7 查看每组用户关系的热度、消息数、回复延迟、共同话题、治理风险和建议干预。

说明：默认图片是离线合成头像卡片，不是真人照片；如果配置图片 API，才会调用外部图像生成服务。静态 HTML 不需要持续启动端口服务；如远程环境需要预览，可临时运行 `python3 -m http.server`，看完后用 `fuser -k 端口/tcp` 关闭。

当前已验证命令：

```bash
CUDA_VISIBLE_DEVICES=0 python3 scripts/run_pipeline.py --n-users 5 --top-k 3
python3 scripts/build_html_demo.py
python3 scripts/run_pipeline.py --n-users 30 --top-k 5
python3 -m compileall src scripts app.py
```

验证结果摘要：

```text
n_users: 5
n_triples: 145
n_matches: 7
n_scene_requests: 5
neo4j_nodes: 255
neo4j_relationships: 478
html_demo: demo/index.html
compileall: 通过
```

## 3. 目录结构

```text
campus_match_ai/
  app.py                         # Streamlit demo
  configs/default.json            # 默认配置
  scripts/run_pipeline.py         # 一键跑全链路
  scripts/import_neo4j.py          # 可选：把图谱导入 Neo4j
  src/campus_match/
    synthetic_users.py            # 合成问卷数据
    profile_extraction.py         # 用户画像抽取，规则/LLM 可切换
    image_generation.py           # 图片 prompt、API 调用、占位图生成
    embeddings.py                 # 文本/图片 embedding
    kg.py                         # 三元组与图谱工具
    neo4j_trace.py                # Neo4j CSV/Cypher 留痕导出
    matching.py                   # 匹配排序
    graph_rag.py                  # 推荐解释
    governance.py                 # 信用分、推荐降权、条件禁言
    dynamic_scene.py              # 动态场景任务匹配
    relationship_dynamics.py      # 恋爱热度曲线与画像更新
    date_context.py               # 线下约会位置/天气/安全上下文
    gnn.py                        # GraphSAGE 链接预测加分项
    pipeline.py                   # 全链路编排
```

运行后会生成：

```text
data/
  users.jsonl
  profiles.jsonl
  triples.csv
  image_assets.csv
  pseudo_link_labels.jsonl
images/
  U001.png
  U001.prompt.txt
indexes/
  text_embeddings.npy
  image_embeddings.npy
  embedding_metadata.json
outputs/
  matches.jsonl
  matches_with_explanations.jsonl
  governance_records.jsonl
  scene_requests.jsonl
  scene_matches.jsonl
  relationship_dynamics.jsonl
  date_contexts.jsonl
  knowledge_graph.gexf
  neo4j/
    campus_match_ai_nodes.csv
    campus_match_ai_relationships.csv
    import_campus_match_ai.cypher
    demo_queries.cypher
    neo4j_trace_summary.json
  pipeline_summary.json
```

## 4. 如何接入图像生成 API

复制 `.env.example` 为 `.env`，或直接在 shell 中设置环境变量：

```bash
export IMAGE_API_URL="你的图像生成接口地址"
export IMAGE_API_KEY="你的 API key"
export IMAGE_API_MODEL="你的图像模型名"
export IMAGE_API_RESPONSE_MODE="url"
```

然后修改 `configs/default.json`：

```json
{
  "generation": {
    "image_provider": "api",
    "image_kind": "lifestyle"
  }
}
```

再运行：

```bash
python scripts/run_pipeline.py --n-users 100 --top-k 5
```

注意：`src/campus_match/image_generation.py` 中的 `generate_image_via_api` 是通用适配器。不同服务商的 payload/response 字段可能不同，到时候只需要小改这个函数。

## 5. 如何接入 LLM API

设置：

```bash
export LLM_API_URL="你的 chat completion 接口地址"
export LLM_API_KEY="你的 API key"
export LLM_MODEL="你的模型名"
```

如果要让 LLM 负责画像抽取，修改配置：

```json
{
  "generation": {
    "use_llm_profile_extraction": true
  }
}
```

默认推荐先不用 LLM 抽取，因为合成问卷本来已经结构化。LLM 更适合用于：

1. 把规则生成的画像改写得更自然。
2. 生成更自然的推荐解释。
3. 生成更好的破冰话题。

## 6. 如何使用更强 embedding

默认使用 `hash` 文本 embedding，优点是离线可跑，缺点是语义质量一般。

如果 A100 环境能访问模型或已有缓存，修改 `configs/default.json`：

```json
{
  "embedding": {
    "text_provider": "sentence_transformer",
    "text_model_name": "BAAI/bge-small-zh-v1.5",
    "image_provider": "clip",
    "clip_model_name": "openai/clip-vit-base-patch32"
  }
}
```

然后重新跑 pipeline。

## 7. 如何使用 Neo4j 留痕

默认运行 pipeline 后会自动生成 Neo4j 留痕文件，不要求本机必须安装 Neo4j：

```bash
python scripts/run_pipeline.py --n-users 120 --top-k 5
```

重点文件：

```text
outputs/neo4j/campus_match_ai_nodes.csv
outputs/neo4j/campus_match_ai_relationships.csv
outputs/neo4j/import_campus_match_ai.cypher
outputs/neo4j/demo_queries.cypher
outputs/neo4j/neo4j_trace_summary.json
```

如果本机安装了 Neo4j Desktop 或 Neo4j Community，并且数据库已经启动，可以直接用 Python 导入：

```bash
pip install neo4j
python scripts/import_neo4j.py --uri bolt://localhost:7687 --user neo4j --password 你的密码 --clear
```

导入后在 Neo4j Browser 中运行：

```cypher
MATCH p=(u:User {node_id: 'U001'})-[r]->(x)
RETURN p
LIMIT 80;
```

也可以打开 `outputs/neo4j/demo_queries.cypher`，里面已经准备好共同兴趣匹配、推荐节点证据、闪电搭子候选排序、7 天聊天热度和雷点冲突查询。汇报时建议截图：

1. 用户画像邻域图。
2. 共同兴趣匹配查询。
3. 推荐节点 + GraphRAG 路径 + 风险原因。
4. 闪电搭子任务与候选排序。
5. 7 天聊天热度曲线。
6. 雷点冲突或信用治理查询。

本项目的 Neo4j 交付分两层：

1. 默认交付：`outputs/neo4j/` 中的 CSV/Cypher/summary 文件，前端也会展示这些留痕。Neo4j 产品图覆盖画像三元组、心动推荐、GraphRAG 证据、闪电搭子、聊天热度、首约安全和信用治理。
2. 加分展示：本机或 A100 环境安装 Neo4j 后，用 `scripts/import_neo4j.py` 导入并截图。

## 8. 分任务说明

### 任务 A：合成数据

文件：

```text
src/campus_match/synthetic_users.py
```

需要改的地方：

1. 兴趣池 `INTERESTS`。
2. 价值观池 `VALUES`。
3. 雷点池 `DEAL_BREAKERS`。
4. 自我介绍模板。
5. 理想型模板。

### 任务 B：图片生成

文件：

```text
src/campus_match/image_generation.py
```

需要改的地方：

1. `build_image_prompt`：控制头像/生活方式图 prompt。
2. `generate_image_via_api`：适配具体 API 的请求和响应。

建议生成“生活方式图”而不是真实人脸，避免肖像和伦理风险。

### 任务 C：知识图谱

文件：

```text
src/campus_match/kg.py
src/campus_match/neo4j_trace.py
scripts/import_neo4j.py
```

需要改的地方：

1. 新增实体类型。
2. 新增关系类型。
3. 增加更多图谱路径证据。
4. 调整 Neo4j 节点/关系 schema。
5. 补充 Cypher 演示查询。

### 任务 D：向量检索

文件：

```text
src/campus_match/embeddings.py
```

需要改的地方：

1. 替换文本 embedding 模型。
2. 使用 CLIP 做图片 embedding。
3. 添加 HNSW/IVF 对比实验。

### 任务 E：匹配算法

文件：

```text
src/campus_match/matching.py
```

需要改的地方：

1. 调整权重。
2. 增加冲突规则。
3. 增加互动反馈特征。
4. 接入 GNN 分数。

### 任务 F：GraphRAG 解释

文件：

```text
src/campus_match/graph_rag.py
```

需要改的地方：

1. 推荐解释 prompt。
2. 破冰话题风格。
3. 安全审核规则。
4. LLM API 适配。

### 任务 G：前端展示

文件：

```text
app.py
```

需要改的地方：

1. 页面样式。
2. 展示图谱路径。
3. 增加以图搜图/以文搜图页面。
4. 增加 like/pass 反馈。

### 任务 H：动态场景任务匹配

文件：

```text
src/campus_match/dynamic_scene.py
```

需要改的地方：

1. 场景任务模板，如饭搭子、学习搭子、运动搭子、Citywalk。
2. 模拟地点知识库，如食堂、图书馆、体育馆、咖啡角和安全等级。
3. 动态权重，包括当前/未来、时间窗口、地点、任务类型和照顾型陪伴信号。
4. 安全提醒文案。

### 任务 I：恋爱动态与线下约会上下文

文件：

```text
src/campus_match/relationship_dynamics.py
src/campus_match/date_context.py
```

需要改的地方：

1. 热度曲线指标，如消息数、回复延迟、积极比例、共同话题命中。
2. 画像更新规则，如关系升温、高共鸣互动、熟悉后更活跃。
3. 线下约会地点知识库，如经纬度、室内/户外、人流、安全等级。
4. 天气上下文和安全建议规则。真实系统可替换为天气 API 和用户授权位置。

### 任务 J：知识治理与惩罚项

文件：

```text
src/campus_match/governance.py
```

需要改的地方：

1. 合成治理事件，如失约、迟取消、不适反馈、骚扰标记、正反馈。
2. 信用分计算规则。
3. 推荐可见度下降倍率。
4. 条件禁言、闪电搭子冷却、人工复核规则。

## 9. 推荐开发顺序

1. 先跑通默认 pipeline。
2. 改合成数据池，让画像更像你们学校同学。
3. 接图像 API，生成真实合成头像/生活方式图。
4. 换成真实 embedding 模型和 CLIP。
5. 调匹配权重，做 Top-5 推荐展示。
6. 导出或导入 Neo4j，准备图数据库截图。
7. 强化 GraphRAG 推荐解释。
8. 加动态场景任务匹配，体现时变、场景和知识更新。
9. 加恋爱热度曲线和线下约会天气/地点上下文。
10. 加知识治理惩罚项，体现推荐程度下降和条件禁言。
11. 加 GNN 链接预测作为 A100 亮点。
12. 美化 Streamlit 或换 React 前端。

## 10. 课程汇报时可以强调

1. 知识管理：隐性偏好显性化。
2. 知识图谱：用户-兴趣-价值观-活动 schema。
3. 图数据库：Neo4j 留痕、Cypher 查询、可视化路径。
4. 图计算：Jaccard、最短路径、链接预测。
5. 多模态：AI 合成图片 + CLIP 图文对齐。
6. 向量数据库：embedding + FAISS 检索。
7. Prompt：画像抽取、推荐解释。
8. RAG：GraphRAG 生成可解释推荐。
9. 动态知识管理：场景任务、时间窗口、地点安全上下文和动态重排。
10. 时变画像：基于合成互动指标生成热度曲线和画像更新信号。
11. 知识治理：基于反馈事件动态调整推荐可见度、冷却和条件禁言。

## 11. 伦理说明

本项目默认只使用合成数据：

1. 不采集真实同学问卷。
2. 不使用真实人脸。
3. 不做颜值打分。
4. 图片标注为 AI-generated synthetic image。
5. 推荐解释强调共同兴趣、价值观和沟通风格，不鼓励冒犯式搭讪。

## 12. 当前交付包内容

桌面文件夹已同步：

```text
CampusMatchAI_小组作业_最新/
  campus_match_ai/          # 代码、数据、输出、文档
  pdf版本课件/              # 课程 PDF
  silu.md                   # 同伴原始思路参考
  项目最新框架与待办.md     # 当前唯一权威说明
```

后续如果继续改代码或文档，需要重新同步这个桌面文件夹。
