# 7 分钟技术 PPT 与 3 分钟管理员后台演示稿 - 技术细节版

更新时间：2026-06-16

这版按老师懂技术、会追问模型和参数来准备。汇报时不要只说“用了知识图谱、向量检索、RAG”，要说清楚：

- 哪些模型是预训练后直接使用：`paraphrase-multilingual-MiniLM-L12-v2`、FAISS、BM25。
- 哪些模型是我们本地训练：GraphSAGE 链接预测、GCN 风险节点分类。
- 哪些是规则和图谱工程：本体校验、意图图谱、闪电搭子场景匹配、信用治理。
- 哪些地方调用了 API：访谈抽取和 RAG 回复各 10 条完整 trace，用来证明可以接入大模型；核心检索、图谱、排序和可视化不是靠 API 硬编。

## 0. 项目当前真实运行口径

| 模块 | 实际做法 | 关键参数和结果 | 答辩时不能说错 |
|---|---|---|---|
| 数据来源 | 固定随机种子 `seed=42` 生成合成校园用户，不使用真人隐私数据 | 120 个用户，字段包括兴趣、价值观、目标、时间、校区、雷点等 | 这是课程 demo 的合成数据，不是线上真实用户 |
| 文本向量 | SentenceTransformer 预训练模型编码画像文本 | `120 x 384`，模型路径 `.hf-models/paraphrase-multilingual-MiniLM-L12-v2` | MiniLM 没有被我们微调，直接作为 encoder |
| 图片向量 | RGB 颜色直方图 | 16 bins x 3 通道 = 48 维 | 没有实际跑 CLIP，配置里只是保留可替换入口 |
| 知识图谱 | 用户字段转本体三元组，再导出 Neo4j 产品图 | 画像三元组 3365 条，本体校验 3365/3365 | 不是只画图，图谱参与推荐解释和 RAG 证据 |
| Neo4j 产品图 | CSV + Cypher 导入文件已生成，前端也加载同一批节点关系可拖拽查看 | 5209 节点、14600 关系 | 全量图包括推荐、搭子、热度、首约、治理，不只是画像 |
| 混合检索 | Text-to-Graph 意图图谱 + BM25 稀疏检索 + Dense 稠密向量 + 图谱约束 + 硬条件重排 | BM25 `k1=1.5, b=0.75`；融合权重见第 3 页 | 不是普通搜索框 |
| FAISS ANN | Flat、IVF、HNSW 三种索引对比 | Flat avg 0.01097ms；IVF `nlist=8,nprobe=2`；HNSW `M=16,efSearch=32` | 数据小，所以这里只证明方法链路，不夸性能 |
| GraphSAGE | 本地 PyTorch 训练用户-用户链接预测 | 80 epoch，hidden 128，test AUC 0.7039 | 使用伪标签，不是人工标注恋爱成功数据 |
| GCN | 本地 PyTorch 训练风险节点分类 | 80 epoch，hidden 96，test AUC 0.9825，accuracy 0.88 | 风险标签来自合成治理规则 |
| RAG | query rewrite -> router -> Top-K retrieval -> compression -> LLM/template -> safety verifier | RAG API 10/10 成功；访谈抽取 API 10/10 成功 | 100 次 API 批量曾被中止，不作为最终结果展示 |

## 0.1 公网后台取图索引

公网链接：`https://caythelearner.github.io/campus-match-ai-demo/`

做 PPT 的同学只需要打开公网链接，先点 `管理员后台`，再优先进入顶部 tab `PPT取图`。这个页面已经把 7 页 PPT 对应的截图位置列出来。截图时尽量保留顶部 tab 名和卡片标题，这样 PPT 里的技术点和公网 demo 能对上。

| PPT 页 | 公网后台位置 | 建议截图区域 | 画面必须能证明什么 |
|---|---|---|---|
| 第 1 页 系统链路 | `管理员后台 -> 总览`，也可先看 `PPT取图` 第 1 张卡 | 星图看板、项目运行态、访谈抽取入口、Neo4j 产品图规模 | 这是实际后台，不是静态截图；能看到用户数、三元组数、Neo4j 节点/关系数 |
| 第 2 页 画像构建 | `管理员后台 -> 访谈抽取` | `4 轮访谈 -> 三元组样例` + `本体约束与图谱质量` | 访谈文本被抽成实体和三元组，并通过 ontology 校验 |
| 第 3 页 表征与检索 | `管理员后台 -> 技术证据` | `意图图谱样例`、`BM25 + 向量 + 图约束`、`FAISS ANN 索引对比` | Text-to-Graph、BM25、Dense、Graph、Constraint、Flat/IVF/HNSW 都有 trace |
| 第 4 页 产品图谱 | `管理员后台 -> Neo4j图谱` | `产品图可视化`，点击 U001 或推荐节点后截节点详情 | 图谱覆盖用户、推荐、GraphRAG、搭子、热度、首约、安全、治理，不只是画像三元组 |
| 第 5 页 排序学习 | `管理员后台 -> 技术证据`，可补 `匹配推荐` | `GNN 链接预测样例`、`GCN 风险节点分类`、匹配分数拆解 | GraphSAGE 输出 `gnn_link_score`，GCN 输出风险概率，二者接入排序/治理 |
| 第 6 页 聊天 RAG | `管理员后台 -> API Trace`，可补 `技术证据` | RAG trace 明细、完整 RAG 流水线 | 能看到 query rewrite、router、retrieval、context compression、final_suggestion、safety verifier |
| 第 7 页 动态闭环 | `管理员后台 -> 搭子任务` 和 `管理员后台 -> 关系安全` | 闪电搭子任务候选排序、关系热度、首约安全、信用治理 | 搭子匹配、热度曲线、地点安全和信用降权是后台可管理对象 |

如果截图里找不到对应内容，先确认页面右上角版本标记包含 `2026-06-16-ppt-public-map`。如果不是这个版本，浏览器开无痕窗口或在链接后加 `?v=20260616`。

## 1. 7 分钟 PPT 总体安排

建议做 7 页，每页只讲一个技术问题。不要堆术语，每页都围绕“为什么这样做、具体怎么做、结果在哪里验证”。

| 页码 | 标题 | 时间 | 要讲的技术关键 |
|---|---:|---:|---|
| 1 | 系统链路：从自然语言到可解释匹配 | 45s | 数据流、模块边界、哪些本地跑、哪些 API |
| 2 | 画像构建：访谈抽取、本体、三元组 | 60s | 合成数据、LLM 抽取 prompt、规则 fallback、本体校验 |
| 3 | 表征与检索：Text-to-Graph、MiniLM、BM25、FAISS | 75s | 显性需求抽取、隐性意图扩展、384 维向量、混合检索权重、ANN 对比 |
| 4 | 产品图谱：Neo4j 与 GraphRAG 证据 | 65s | 节点关系规模、路径证据、推荐解释 |
| 5 | 排序学习：匹配公式、GraphSAGE、GCN | 80s | 分数公式、伪标签、训练参数、AUC、治理降权 |
| 6 | 聊天 RAG：为什么回复不再重复 | 70s | query rewrite、路由、Top-K、上下文压缩、安全校验、API 参数 |
| 7 | 动态闭环：闪电搭子、热度、首约、安全 | 45s | 场景匹配公式、热度公式、信用阈值、前端展示 |

## 2. 每页 PPT 详细内容

这一节是做 PPT 和回答追问用的展开说明，不建议逐字念。真正上台限时口播用第 3 节。

### 第 1 页：系统链路 - 从自然语言到可解释匹配

PPT 放什么：

- 一张横向流程图：用户输入 -> 画像抽取 -> 向量表征 -> 知识图谱 -> 混合检索/图学习 -> RAG/匹配/治理 -> 前端展示。
- 标出两类界面：用户端手机交互、管理员端星图台。
- 右下角放真实运行规模：120 users、3365 triples、5209 nodes、14600 relationships。

公网取图：`管理员后台 -> 总览`。建议截“星图看板”和“项目运行态”，画面里要保留 `Neo4j 产品图 5209/14600` 和版本标记。

页面说明（备查，不建议逐字念）：

> 我们不是只做了一个好看的社交页面，而是把校园社交里的自然语言、兴趣、时间、地点、聊天状态和安全反馈，变成可以检索、可以解释、可以治理的知识系统。用户端看到的是心动星球和闪电搭子，后台看到的是模型链路和证据。当前数据是固定随机种子生成的 120 个合成校园用户，避免使用真实隐私数据。系统本地跑通了画像三元组、本体校验、MiniLM 向量、FAISS 检索、Neo4j 产品图、GraphSAGE 链接预测、GCN 风险分类和聊天 RAG；API 只用于少量访谈抽取与回复生成样例。

老师追问时这样答：

- 数据是不是假的：是合成数据，但字段、关系、检索、训练和治理链路都是真跑，适合课程 demo。
- 是否全靠大模型：不是。大模型只在 10 条访谈抽取和 10 条 RAG 回复里做示例；核心图谱、检索、排序、GNN、可视化都是本地程序跑出来的。
- 前端是不是静态截图：不是截图。GitHub Pages 是静态 demo，但加载的是生成后的 JSON/CSV trace；本地 `8023` API 才支持实时 `/api/chat-rag`。

### 第 2 页：画像构建 - 访谈抽取、本体、三元组

PPT 放什么：

- 左边放 4 轮访谈样例：兴趣、价值观、首约方式、雷点。
- 中间放实体抽取：Interest、Value、RelationshipGoal、CommunicationStyle、TimeSlot、DealBreaker、Campus。
- 右边放三元组和本体校验结果。

公网取图：`管理员后台 -> 访谈抽取`。建议截“4 轮访谈 -> 三元组样例”和“本体约束与图谱质量”，这里能直接看到三元组，不需要打开本地文件。

具体实现：

- 数据生成：`src/campus_match/synthetic_users.py`，固定 `seed=42`，生成 120 个用户。
- 字段池：36 个兴趣、15 个价值观、12 个雷点、15 个专业、8 个学院、4 个校区、4 类关系目标、6 类沟通风格、9 类约会偏好。
- 每个用户随机采样：
  - interests：4 到 7 个。
  - values：3 到 5 个。
  - deal_breakers：2 到 4 个。
  - available_time：2 到 3 个。
  - preferred_date：2 到 4 个。
- 画像抽取：`src/campus_match/profile_extraction.py` 先规则归一化，再追加隐性意图。
  - 如果目标是“长期关系/认真了解”，加 `关系稳定性 confidence=0.82`。
  - 如果 values 包含“边界感”，加 `尊重个人空间 confidence=0.78`。
  - 如果沟通风格是“慢热但深入/温和倾听”，加 `低压力沟通 confidence=0.72`。
- 访谈抽取：`src/campus_match/interview_extraction.py` 把每个用户构造成 4 个问答，再抽实体和关系。
  - API 模式：`temperature=0.1`，`max_tokens=1200`，要求返回 JSON。
  - 离线 fallback：按字段触发实体识别，生成 `LIKES/VALUES/HAS_GOAL` 等关系。
- 本体校验：`src/campus_match/ontology.py` 检查 relation 的 domain/range 和字段来源。

真实结果：

- 画像三元组：3365 条。
- 本体校验：3365/3365，通过率 1.0。
- 关系覆盖：`LIKES=648`，`VALUES=482`，`HAS_PERSONALITY=370`，`AVAILABLE_AT=307`，`PREFERS_DATE=358`，`DISLIKES=360`。
- API 访谈抽取：10 次尝试，10 次可用 trace。

页面说明（备查，不建议逐字念）：

> 画像不是前端手写标签。我们先用合成用户模拟注册资料，再把资料转成访谈问答，抽出兴趣、价值观、关系目标、沟通方式、时间偏好和雷点。比如“我喜欢古典音乐，也看重边界感”，会进入图谱成为 `User-LIKES-古典音乐` 和 `User-VALUES-边界感`。为了防止图谱乱连，我们定义了本体，要求 User 只能通过受控关系连接到 Interest、Value、Goal、Time、Date、DealBreaker、Campus、Major。最后 3365 条画像三元组全部通过校验。这样后面推荐和聊天的每个标签都能追溯到来源。

老师追问时这样答：

- 为什么要本体：没有本体，兴趣、价值观、雷点会混成同一类标签，图谱路径和推荐解释不可信。
- LLM 抽取失败怎么办：有 rule-based fallback，输出同样的实体和三元组结构。
- 训练了抽取模型吗：没有训练抽取模型；抽取部分用 prompt + 本地规则兜底。训练的是后面的 GraphSAGE 和 GCN。

### 第 3 页：表征与检索 - MiniLM、BM25、FAISS

PPT 放什么：

- 展示一条 query：“想找个会弹吉他的阳光学长”。
- 画 Text-to-Graph 小图：原始 query -> 显性需求 -> 隐性意图 -> 画像字段 -> 硬条件。
- 再画四路召回：BM25 稀疏检索、Dense 稠密向量、Graph 图谱约束、Constraint 硬条件。
- 放 FAISS Flat / IVF / HNSW 对比表。

公网取图：`管理员后台 -> 技术证据`。建议截“意图图谱样例”“BM25 + 向量 + 图约束”“FAISS ANN 索引对比”三个区域。

文本向量模型细节：

- 模型：`paraphrase-multilingual-MiniLM-L12-v2`，本地路径 `.hf-models/paraphrase-multilingual-MiniLM-L12-v2`。
- 使用方式：SentenceTransformer 直接编码，不微调。
- Transformer 配置：
  - `model_type=bert`
  - `hidden_size=384`
  - `num_hidden_layers=12`
  - `num_attention_heads=12`
  - `intermediate_size=1536`
  - `max_position_embeddings=512`
  - SentenceTransformer `max_seq_length=128`
- Pooling：句向量取 pooling 后输出 384 维，并做 normalize，所以内积检索可以近似看作余弦相似度。
- 输入文本：`self_intro + ideal_partner + interests + values + relationship_goal + communication_style + preferred_date + deal_breakers`。
- 输出结果：`text_embeddings.npy` shape 为 `120 x 384`。

图片向量细节：

- 实际 provider：`color_histogram`。
- 处理：图片缩放到 `224 x 224`，RGB 三个通道各做 16 bins 直方图。
- 维度：`16 x 3 = 48`，L2 normalize。
- 说明：配置里保留 `openai/clip-vit-base-patch32`，但当前没有下载和运行 CLIP，所以不要说“用了 CLIP 训练图片模型”。

BM25 与混合检索：

- Text-to-Graph：`src/campus_match/intent_search.py` 的 `analyze_query_intent()`。
  - 第一步：显性需求抽取，例如“会弹吉他、音乐兴趣、偏好男生、阳光气质”。
  - 第二步：隐性意图扩展，例如“音乐技能、艺术细胞、低压力聊天、外向主动、线下见面意愿”。
  - 第三步：图谱字段映射，例如映射到 `古典音乐、Livehouse、爵士、音乐节、音乐现场、male、外向主动、认真了解`。
  - 第四步：硬约束识别，例如 `性别偏好：男生`；身高这类没有真实字段的条件会标记 warning，不假装参与真实过滤。
  - 输出：`graph_nodes` 和 `graph_edges`，后台可视化里能看到 query 节点、显性需求节点、隐性意图节点、画像字段节点之间的关系。
- 分词：`regex_words + chinese_char_bigrams`，中文会额外拆成 bigram，避免只按空格切词。
- BM25 参数：`k1=1.5`，`b=0.75`，平均文档长度 `avg_doc_len=291.57`。
- BM25 公式含义：
  - `k1` 控制词频饱和，避免一个词重复太多次把分数拉爆。
  - `b` 控制文档长度归一化，避免长画像天然占便宜。
- BM25 混合权重：
  - BM25：0.30
  - Dense：0.32
  - Graph：0.26
  - Constraint：0.12
- 意图图谱混合权重：
  - Vector：0.34
  - Sparse：0.24
  - Graph：0.28
  - Constraint：0.14

FAISS 对比：

| 索引 | 参数 | 平均查询耗时 | 与 Flat Top-K 重合 | 结论 |
|---|---|---:|---:|---|
| Flat | `IndexFlatIP` | 0.01097 ms | 1.0000 | 精确暴力检索，适合小数据和基准 |
| IVF | `IndexIVFFlat`，`nlist=8`，`nprobe=2` | 0.00981 ms | 0.4000 | 倒排聚类思路对，但小数据下召回波动大 |
| HNSW | `IndexHNSWFlat`，`M=16`，`efConstruction=40`，`efSearch=32` | 0.01549 ms | 0.9333 | 图式 ANN，召回更接近 Flat |

页面说明（备查，不建议逐字念）：

> 检索不能只做筛选框。用户说“想找会弹吉他的阳光学长”，这句话先经过 Text-to-Graph，被拆成显性需求、隐性意图、画像字段和硬约束四层。显性需求是“会弹吉他、偏好男生”，隐性意图是“音乐技能、艺术细胞、外向主动”，再通过图谱扩散映射到古典音乐、Livehouse、音乐节、male、外向主动等画像字段。之后系统同时跑 BM25 稀疏检索、MiniLM 稠密向量检索、图谱约束和硬条件重排。BM25 解决精确词命中，Dense 向量解决语义相似，Graph 负责语义扩展和多跳证据，Constraint 保证性别、时间、地点等硬条件不被向量淹没。FAISS 部分我们做了 Flat、IVF、HNSW 对比，分别对应精确检索、倒排聚类和图式 ANN。

老师追问时这样答：

- 384 维怎么来的：来自 MiniLM 的 hidden size 和 SentenceTransformer pooling 输出，不是我们随便设的。
- 显性需求和隐性意图有什么用：显性需求保证可解释的硬匹配，隐性意图负责语义扩展和召回补全，两者一起进入混合检索重排。
- 为什么 IVF 重合率低：当前只有 120 条向量，`nlist=8,nprobe=2` 对小数据不稳定；这里展示 IVF 倒排聚类方法，不夸速度收益。
- 为什么还要 BM25：向量相似会泛化，但硬词和精确要求可能丢；BM25 保证“羽毛球、185、金融”等词可控。

### 第 4 页：产品图谱 - Neo4j 与 GraphRAG 证据

PPT 放什么：

- 后台 Neo4j 产品图截图，展示可拖拽节点。
- 一条推荐路径：`U001 - LIKES -> 剧本杀 <- LIKES - U010`，以及 `VALUES -> 边界感/安全感/坦诚沟通`。
- 右侧放节点和关系统计。

公网取图：`管理员后台 -> Neo4j图谱`。先点击或拖动一个节点，再截图“产品图可视化”和下面的节点详情。

图谱构建细节：

- 画像图：`src/campus_match/kg.py` 把用户字段转成三元组。
- 推荐解释：`ProfileGraph.path_evidence()` 找两人共同邻居。
- GraphRAG：`src/campus_match/graph_rag.py` 把图路径、匹配分数、差异点、风险点组织成推荐理由。
- Neo4j 导出：`src/campus_match/neo4j_trace.py` 生成：
  - `outputs/neo4j/campus_match_ai_nodes.csv`
  - `outputs/neo4j/campus_match_ai_relationships.csv`
  - `outputs/neo4j/import_campus_match_ai.cypher`
  - `outputs/neo4j/demo_queries.cypher`

Neo4j 产品图规模：

- 节点：5209。
- 关系：14600。
- 图谱范围：画像三元组、推荐节点、GraphRAG 证据、闪电搭子任务、候选排序、7 天热度曲线、首约地点安全、信用治理。
- 重要节点类型：
  - `User=120`
  - `MatchRecommendation=600`
  - `GraphRAGEvidence=3599`
  - `SceneRequest=12`
  - `SceneCandidateRank=60`
  - `RelationshipPair=8`
  - `ChatDay=56`
  - `GovernanceRecord=120`

页面说明（备查，不建议逐字念）：

> 推荐不能只给一个合拍度。我们把用户、兴趣、价值观、推荐、GraphRAG 证据、闪电搭子、首约安全和治理事件都放进产品图谱。比如 U001 推荐 U010，不是因为一个黑盒分数，而是图里能看到共同兴趣“剧本杀”，共同价值观“边界感、安全感、坦诚沟通、情绪稳定”，还有共同偏好的“图书馆学习、运动、音乐现场”。GraphRAG 做的事情就是从图谱取这些路径证据，再把它变成用户能看懂的推荐理由和破冰建议。管理员端可以直接点节点，看字段、分数、证据路径和关系类型。

老师追问时这样答：

- Neo4j 是否真的能导入：能，CSV 和 Cypher 已生成；前端加载的是同一批节点关系，Neo4j Browser 可用 `demo_queries.cypher` 看真实查询。
- GraphRAG 和普通 RAG 差别：普通 RAG 检索文本，GraphRAG 先从图里取结构化路径，再让回复基于路径证据。
- 为什么有 5209 节点而不是 89 个：旧版本只算了局部画像图；现在产品图把推荐、证据、搭子、热度、首约和治理都入图。

### 第 5 页：排序学习 - 匹配公式、GraphSAGE、GCN

PPT 放什么：

- 左侧放匹配分数拆解条形图。
- 中间放 GraphSAGE 链接预测示意：User - Attribute - User。
- 右侧放 GCN 风险分类：正常节点、风险节点、治理动作。

公网取图：`管理员后台 -> 技术证据`，截“GNN 链接预测样例”和“GCN 风险节点分类”；如果需要展示分数如何进推荐，再补 `管理员后台 -> 匹配推荐` 的分数拆解。

匹配公式：

最终匹配分数来自多路加权：

`score = 0.27 * text_similarity + 0.22 * graph_similarity + 0.18 * value_similarity + 0.10 * goal_match + 0.05 * communication_match + 0.08 * image_similarity + 0.10 * gnn_link_score - penalty`

其中 `graph_similarity` 不是一个黑盒，而是：

`graph_similarity = 0.45 * interest_jaccard + 0.35 * value_jaccard + 0.10 * date_jaccard + 0.10 * availability_jaccard`

惩罚项：

- 关系目标强冲突：0.30。
- 雷点命中：0.40。
- 校区不同：0.05。
- 沟通节奏冲突：0.12。

治理后处理：

- 先算 `base_final_score`，再乘候选人的 `visibility_multiplier`。
- 例子：U001 -> U010，`base_final_score=0.6220`，U010 信用分 83，触发 `visibility_multiplier=0.85`，最后 `final_score=0.5287`。

GraphSAGE 链接预测：

- 任务：预测两个用户是否可能匹配，即 user-user link prediction。
- 节点：
  - User 节点：使用 384 维 MiniLM 文本向量。
  - Attribute 节点：兴趣、价值观、目标、沟通风格、时间、雷点、校区、专业，使用 deterministic hash embedding 到 384 维。
- 边：
  - User -> Interest/Value/Goal/Time 等属性。
  - 图中边按双向加入，方便邻居聚合。
- 伪标签构造：
  - `shared_interests >= 2`
  - `shared_values >= 1`
  - `same_goal == True`
  - 三个条件同时满足则 label=1，否则 label=0。
- 训练集处理：
  - 正样本保留。
  - 负样本最多取正样本的 2 倍，避免负样本压倒训练。
  - 80/20 train-test split。
- 模型结构：
  - 因当前环境没有 `torch_geometric`，实际 backend 是 `torch_mean_graphsage`。
  - 两层 mean GraphSAGE。
  - 每层包含 `self_linear` 和 `neighbor_linear`，邻居聚合为 `adj @ node_x`。
  - 编码后做 L2 normalize。
  - Decoder 为两端节点 embedding 点积，再过 sigmoid。
- 训练参数：
  - epochs：80。
  - hidden_dim：128。
  - optimizer：AdamW。
  - learning rate：`1e-3`。
  - weight_decay：`1e-4`。
  - loss：`binary_cross_entropy_with_logits`。
  - device：CPU。
- 训练结果：
  - n_users：120。
  - n_nodes：238。
  - n_edges：6010。
  - n_train_pairs：614。
  - n_test_pairs：154。
  - 输出 pair scores：7140，对应 120 个用户两两组合。
  - test AUC：0.7039。

GCN 风险节点分类：

- 任务：根据用户画像邻域和治理事件判断用户是否风险节点。
- 标签定义：满足以下任一条件为风险：
  - `credit_score < 85`
  - `visibility_multiplier < 1.0`
  - `review_required == True`
  - `conditional_mute == True`
- 信用分规则：
  - `credit_score = 100 - 18*no_show - 8*late_cancel - 20*unsafe_report - 40*harassment_flag + 3*positive_feedback`
  - 分数截断到 0 到 100。
- 模型结构：
  - 两层 GCN：`A_norm @ X -> Linear -> ReLU -> A_norm @ H -> Linear`。
  - `A_norm = D^-1/2 A D^-1/2`，A 包含 self-loop。
  - 最后接一个线性 classifier 输出风险 logit。
- 训练参数：
  - epochs：80。
  - hidden_dim：96。
  - optimizer：AdamW。
  - learning rate：`1e-3`。
  - weight_decay：`1e-4`。
  - loss：`binary_cross_entropy_with_logits`。
  - pos_weight：训练集中负样本数 / 正样本数，处理类别不平衡。
- 训练结果：
  - n_users：120。
  - n_nodes：260。
  - n_edges：6914。
  - n_positive：29。
  - n_negative：91。
  - n_train_nodes：95。
  - n_test_nodes：25。
  - test AUC：0.9825。
  - test accuracy：0.88。

页面说明（备查，不建议逐字念）：

> 排序不是一个简单相似度。最终分数融合了文本语义、图谱相似、价值观、关系目标、沟通方式、图片辅助和 GNN 链接预测。图谱相似又拆成兴趣、价值观、约会偏好和空闲时间的 Jaccard。GraphSAGE 负责在用户-属性图上学习“两个用户是否可能形成匹配边”，它不是用人工恋爱成功标签，而是用共同兴趣、共同价值观和目标一致构造伪标签，所以它是课程方法 demo，不宣称生产级准确率。GCN 用在治理侧，把信用事件和图邻域一起传播，判断哪些用户需要降权、冷却或复核。这样图学习进入了排序和管理，而不是只作为可视化装饰。

老师追问时这样答：

- GNN 训练了什么：训练了 GraphSAGE 链接预测，输出 `gnn_link_score`，并以 0.10 权重进入匹配排序。
- Graph 还训练了什么：训练了 GCN 风险节点分类，输出 `gnn_risk_probability`，用于后台治理展示。
- 标签从哪里来：合成 demo 里没有真人成功匹配标签，所以 GraphSAGE 用可解释伪标签；GCN 用治理规则生成风险标签。
- AUC 能不能说明真实业务有效：不能直接说明线上有效，只能说明在当前构造标签下模型学到了图结构规律。汇报要诚实说这是方法验证。

### 第 6 页：聊天 RAG - 为什么回复不再重复

PPT 放什么：

- 一条流水线：用户消息 -> query rewrite -> router -> retrieval -> rerank -> compression -> generation -> verifier。
- 展示一条“剧本杀”活动问题的 trace，说明为什么不再反复问同一句。
- 放 API 统计：访谈抽取 10/10、RAG 回复 10/10。

公网取图：`管理员后台 -> API Trace` 截 RAG trace 明细；也可以到 `管理员后台 -> 技术证据` 截“完整 RAG 流水线”。

RAG 知识库：

`CHAT_KNOWLEDGE_BASE` 当前有 11 类知识：

- 共同兴趣开场。
- 具体活动推荐，含防编造策略。
- 低压力首约。
- 学习搭子。
- 低能量照顾。
- 边界感提醒。
- 运动搭子成局。
- 饭搭子回复。
- 拍照 Citywalk。
- 考试压力安抚。
- 见后反馈。

检索实现：

- 聊天检索不是直接调用 MiniLM，而是 `_chat_embedding`：
  - 384 维 deterministic hash embedding。
  - 加入中文字符 unigram、bigram、trigram，增强短句召回。
  - query 和 doc embedding 做 inner product。
- 规则增强分：
  - 首约/咖啡/图书馆相关：安全和学习文档 +0.18。
  - 累/焦虑/没胃口：情绪照顾文档 +0.24。
  - 剧本杀/推荐/活动：防编造活动文档 +0.28。
  - 运动：运动搭子文档 +0.24。
  - 饭局：饭搭子文档 +0.22。
  - 拍照/Citywalk：低压力线下文档 +0.22。
  - 考试/论文/ddl：学业压力文档 +0.23。
  - 见后反馈：记忆博物馆文档 +0.24。
- Top-K：取前 3 条证据。

RAG 生成链路：

1. `query_rewrite`：把原始消息改写为“结合画像、匹配理由、安全边界，给出克制、可执行建议”。
2. `router`：按意图选择来源，例如 `emotion_weather_station`、`date_safety_playbook`、`activity_playbook`。
3. `retrieval`：从画像上下文和知识库中取 Top-K。
4. `rerank`：按检索分排序。
5. `context_compression`：只保留 doc_id、title、90 字证据、suggestion 和 score。
6. `generation`：优先用 API 生成，没配置 API 时用检索模板。
7. `safety_verifier`：检查是否编造活动、语气过强、线下安全证据不足。

API 参数：

- Provider：Anthropic-compatible。
- Model：`claude-opus-4-8`。
- RAG 生成：`temperature=0.4`，`max_tokens=220`。
- 访谈抽取：`temperature=0.1`，`max_tokens=1200`。
- 环境变量：`ANTHROPIC_BASE_URL`、`ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_MODEL`。
- 文档和 PPT 不写 API key，只写配置项。

真实结果：

- `outputs/rag_pipeline_traces.json`：12 条 RAG trace，其中 10 条 API 使用成功。
- 例子：
  - 输入：“我也注意到我们都提到了剧本杀，最近有没有相关活动推荐？”
  - 命中 `activity_specific_reply`，规则要求不要编造不存在的活动名。
  - 输出：“可以先聊聊你喜欢的类型 - 是偏好轻松情感本，还是硬核推理本？”
- `outputs/realtime_chat_api_traces.jsonl`：本地实时 API 产生过 2 条 server trace。

页面说明（备查，不建议逐字念）：

> 早期聊天回复像模板，会反复出现同一句“剧本杀你想玩轻量本还是硬核推理”。我们改成了 RAG 链路。用户输入后，系统先判断意图，再路由到画像、破冰库、活动库、首约安全库或情绪气象站，检索 Top-K 证据，压缩后再生成回复。对于“最近有没有剧本杀活动推荐”，系统会优先命中防编造活动策略，所以不会硬编某个活动名，而是先问用户偏好和雷点。这里的重点不是直接问大模型，而是先把证据检索出来，再让回复受证据约束。

老师追问时这样答：

- 聊天现在是不是向量检索：是，聊天建议走 384 维短文本向量检索 + 规则加权 Top-K。
- 是否训练了聊天模型：没有训练生成模型；使用 RAG 控制上下文和回复边界。
- 为什么不总是 API：静态 GitHub Pages 无法安全保存 key，所以公网 demo 展示 trace；本地 API 版可实时调用。

### 第 7 页：动态闭环 - 闪电搭子、热度、首约、安全

PPT 放什么：

- 闪电搭子排序卡：任务、时间、地点、安全等级、候选人分数拆解。
- 关系热度曲线。
- 信用治理策略卡。

公网取图：`管理员后台 -> 搭子任务` 截任务候选排序；`管理员后台 -> 关系安全` 截热度、首约安全和信用治理。

闪电搭子场景匹配：

- 意图识别：`infer_scene_intent()`。
  - 吃饭/冒菜/没胃口 -> `meal`。
  - 刷题/图书馆/算法课 -> `study`。
  - 羽毛球/运动/体育 -> `sports`。
  - Citywalk/散步/拍照 -> `walk`。
  - 明天/周末/下周 -> `future`，否则 `now`。
  - 没胃口/累/难受 -> `care_needed`，同时屏蔽重口味、强迫社交等 avoid_tags。
- 分数公式：
  - `final = 0.28*semantic + 0.22*time + 0.20*location + 0.20*task + 0.10*care - safety_penalty`
  - 高风险地点 `safety_penalty=0.15`。
- 当前结果：
  - scene_requests：12。
  - scene_matches：60。

关系热度曲线：

- 这是后台演示用的合成历史样本，不在新用户刚进入时当真实 7 天结果展示。
- 每对关系生成 7 天聚合指标：
  - message_count。
  - avg_response_delay_min。
  - positive_ratio。
  - shared_topic_hits。
- 热度公式：
  - `heat = 0.30*base_match + 0.25*min(msg_count/80,1) + 0.25*positive_ratio + 0.10*min(shared_topic_hits/4,1) + 0.10*(1-min(avg_delay/120,1))`
- 当前结果：
  - relationship pairs：8。
  - chat day nodes：56。

首约与安全：

- 首约计划：8 条。
- 地点属性：校区、经纬度、类别、人流、安保、是否室内、适合活动。
- LBS 和天气：当前是模拟数据，不调用真实定位和天气 API。
- 风险评估：人流低、安保低、夜间/偏僻等会提高风险；建议公开地点和 30-60 分钟低压力见面。

信用治理：

- 信用分公式见第 5 页。
- 策略阈值：
  - `<85`：推荐可见度 0.85，轻度降权。
  - `<70`：推荐可见度 0.60，中度降权。
  - `<50`：推荐可见度 0.30，显著降权。
  - `no_show_count >= 2`：闪电搭子发布 12 小时冷却。
  - `unsafe_report_count >= 2`：安全曝光降权，最高压到 0.45。
  - `unsafe_report_count >= 3` 或 `harassment_flag_count >= 1`：限制主动私聊/邀约，进入人工复核，可见度最高 0.15。

页面说明（备查，不建议逐字念）：

> 最后一页讲动态闭环。心动星球偏长期关系，闪电搭子偏即时任务，所以闪电搭子不能用同一套恋爱排序。它更看重任务、时间窗口、地点距离、候选人的活动匹配和安全上下文。关系热度不是新用户一进来就看到的真实 7 天数据，而是后台演示用的历史样本，计算时用消息数、回复延迟、积极比例和共同话题。治理侧则把爽约、不安全反馈、骚扰标记和正反馈转成信用分，再影响推荐可见度、冷却和人工复核。这样产品不是一次性推荐，而是会随交互和治理反馈更新。

老师追问时这样答：

- 闪电搭子跟心动星球有什么区别：闪电搭子是任务场景排序，心动星球是关系兼容排序。
- 热度曲线是不是偷看聊天内容：demo 使用合成聚合指标；真实系统应该只在授权后保存脱敏摘要。
- 安全策略是不是模型判断：当前主要是规则和图谱属性，GCN 做风险节点辅助分类。

## 3. 7 分钟逐页技术口播稿

下面是**限时口播版**。按中文技术汇报约每分钟 230-250 字设计，正文控制在 7 分钟内；每页下面给出估算字数和公网后台指向。正式汇报时只念“口播”，不要把文件路径、代码文件名念出来。

### 第 1 页，0:00-0:40，系统链路

口播：

> 我们这套系统的主线，是把校园社交里的自然语言、兴趣、价值观、时间地点和安全反馈，变成可检索、可解释、可治理的知识系统。用户端看到的是心动星球和闪电搭子，管理员端看到的是证据链。后台总览能直接看到当前规模：120 个合成用户、3365 条画像三元组、5209 个 Neo4j 产品图节点和 14600 条关系。技术链路按课上知识组织：先做知识获取和本体建模，再做向量检索和图检索，最后接入 RAG、图学习和治理策略。也就是说，PPT 不是单独讲概念，每个技术点都能在公网后台找到对应画面。

估算：约 192 字，约 48-50 秒。

PPT 上指：`管理员后台 -> 总览`，指用户数、画像三元组、Neo4j 产品图规模。

### 第 2 页，0:40-1:30，画像抽取和本体

口播：

> 第二页讲知识获取。注册资料本来是自然语言，不能直接用于图查询，所以我们把每个用户模拟成 4 轮访谈，再抽取兴趣、价值观、关系目标、沟通方式、约会偏好和雷点。抽取结果不是散乱标签，而是受控三元组，例如用户通过 LIKES 连接兴趣，通过 VALUES 连接价值观，通过 DISLIKES 连接雷点。这里对应课上的实体识别、关系抽取和本体约束。本体校验的作用是防止关系乱连，比如价值观不能被写成地点，雷点不能被写成兴趣。API 抽取只是证明大模型可以接入；没有 API 时，规则 fallback 仍然产出同样结构。后台能看到访谈、三元组和 3365/3365 的校验结果。

估算：约 211 字，约 51-55 秒。

PPT 上指：`管理员后台 -> 访谈抽取`，截“4 轮访谈 -> 三元组样例”和“本体约束与图谱质量”。

### 第 3 页，1:30-2:35，Text-to-Graph 和混合检索

口播：

> 第三页讲检索。普通筛选只能匹配显性词，但用户经常说的是口语需求，比如“想找会弹吉他的阳光学长”。系统先做 Text-to-Graph，把这句话拆成显性需求、隐性意图、画像字段和硬条件。显性需求保证可解释，隐性意图负责扩展召回，例如从“吉他”扩展到音乐技能、艺术细胞和 Livehouse。检索阶段不是单路向量，而是 BM25、Dense 向量、Graph 约束和 Constraint 四路融合。MiniLM 输出 384 维文本向量；BM25 负责精确词；图约束负责多跳语义扩展；硬条件保证性别、时间、地点不被相似度淹没。FAISS 部分展示 Flat、IVF、HNSW 三种索引对比，分别对应精确检索、倒排聚类和近似最近邻图。由于数据量小，我们不夸速度收益，只说明索引结构和召回差异。这里和课上向量数据库、稀疏检索、ANN 检索是对应的。

估算：约 255 字，约 61-67 秒。

PPT 上指：`管理员后台 -> 技术证据`，截“意图图谱样例”“BM25 + 向量 + 图约束”“FAISS ANN 索引对比”。

### 第 4 页，2:35-3:25，Neo4j 和 GraphRAG

口播：

> 第四页讲图数据库和 GraphRAG。我们没有只画一个兴趣图，而是把产品运行过程也入图：用户、推荐、GraphRAG 证据、闪电搭子任务、聊天热度、首约安全和信用治理都在同一张产品图里。GraphRAG 的核心不是把资料全塞进 prompt，而是先做子图检索和多跳路径查询。比如 U001 和 U010，系统先查共同邻居，找到共同兴趣“剧本杀”、共同价值观“边界感”和共同约会偏好，再把这些路径作为推荐理由和破冰话题。可解释性来自图路径，而不是模型临场编出来。后台图谱节点可以拖拽，也可以点开字段；老师追问某条推荐为什么成立时，就沿着节点详情和相连关系讲。这里展示的是图数据库结构和路径证据，不是装饰图。

估算：约 235 字，约 56-61 秒。

PPT 上指：`管理员后台 -> Neo4j图谱`，点击节点后截“产品图可视化”和节点详情。

### 第 5 页，3:25-4:55，匹配公式、GraphSAGE、GCN

口播：

> 第五页讲排序和图学习。最终匹配不是一个单独相似度，而是多路加权：文本语义、图谱相似、价值观、关系目标、沟通方式、图片辅助和 GNN link score 共同决定分数。图谱相似又拆成兴趣、价值观、约会偏好和空闲时间的 Jaccard，所以每一项都能解释。GraphSAGE 做的是链接预测，对应课上的图表示学习：用户节点用 384 维文本向量，属性节点用 hash embedding，两层 mean aggregation 学习邻居信息，预测两个用户是否可能形成匹配边。因为没有真实恋爱成功标签，这里用共同兴趣、共同价值观和目标一致构造伪标签，所以汇报时只说课程方法验证。GCN 做风险节点分类，把信用事件和图邻域一起传播，输出风险概率，辅助后台降权、冷却和复核。两者分工不同：GraphSAGE 解决“谁可能匹配”，GCN 解决“谁需要治理”。后台同时展示 gnn_link_score、risk probability 和 AUC，所以模型没有停留在概念层。

估算：约 285 字，约 68-74 秒。

PPT 上指：`管理员后台 -> 技术证据`，截“GNN 链接预测样例”和“GCN 风险节点分类”；需要分数拆解时补 `匹配推荐`。

### 第 6 页，4:55-6:00，聊天 RAG

口播：

> 第六页讲 RAG。聊天回复不能只靠模板，也不能直接把所有资料丢给大模型。系统先做 query rewrite 和 router，判断这是破冰、活动推荐、情绪照顾还是首约安全；再从画像、匹配理由、破冰库和安全库里取 Top-K 证据，压缩后再生成回复，最后做 safety verifier。这样做的结果是，像“剧本杀有没有活动推荐”这种问题，会先命中“不要编造活动名”的证据，再引导用户确认偏好，而不是反复抛同一句硬核推理问题。这里对应课上的 RAG、证据压缩和生成约束。公网后台展示的是完整 trace：用户问题、命中文档、最终回复和安全校验都能看到，所以这页的重点是“先检索证据，再生成回答”。即使公网不能暴露 API key，同学也能用 trace 截图证明链路跑通过。

估算：约 243 字，约 58-63 秒。

PPT 上指：`管理员后台 -> API Trace` 和 `技术证据`，截 RAG trace、Top-K evidence、safety verifier。

### 第 7 页，6:00-6:50，闪电搭子、热度和治理

口播：

> 最后一页讲动态知识更新。心动星球偏长期关系，闪电搭子偏即时任务，所以闪电搭子单独按任务、时间、地点、活动类型、照顾信号和安全地点排序。关系热度不是用户一进来就看到 7 天结果，而是后台演示用的历史聚合指标，由消息数、回复延迟、积极比例和共同话题计算。治理侧把爽约、不安全反馈、骚扰标记和正反馈转成信用分，再影响推荐可见度、发布冷却和人工复核。这里对应课上的动态知识管理和知识治理。用户端只看到自己的提醒和建议，管理员端看到聚合指标和策略原因。收束到产品逻辑上，就是系统不只做一次推荐，而是让图谱、检索、排序和治理随着交互持续更新。

估算：约 237 字，约 57-62 秒。

PPT 上指：`管理员后台 -> 搭子任务` 和 `关系安全`，截候选排序、热度、安全和信用治理。

总估算：正文约 1658 个口播单位，按 230-250 字/分钟约 6分38秒-7分13秒。实际汇报时正常停顿和换页后基本落在 7 分钟左右。

## 4. 3 分钟管理员后台演示路线

公网链接：

`https://caythelearner.github.io/campus-match-ai-demo/`

演示前准备：

- 打开网页。
- 切到 `管理员后台`。
- 浏览器缩放 90% 或 100%。
- 先点 `PPT取图` 看 7 页 PPT 对应的公网取图索引，再按演示顺序切换 `访谈抽取`、`技术证据`、`Neo4j图谱`、`API Trace`。

### 0:00-0:25 总览：后台管什么

操作：

- 进入管理员后台。
- 先停留在 `总览`，再点一下 `PPT取图` 说明每页 PPT 都能在公网找到对应证据。

讲什么：

> 这里是管理员星图台，不是用户 App。它主要看四件事：第一，数据和图谱规模；第二，检索和 RAG 的证据链；第三，GNN 和 GCN 的训练结果；第四，安全和信用治理。当前 demo 有 120 个合成用户、3365 条画像三元组、5209 个 Neo4j 产品图节点、14600 条关系。

要点：

- 指一下 `Neo4j 产品图 5209/14600`。
- 指一下 `画像三元组 3365`。
- 如果切到 `PPT取图`，指出每页 PPT 的截图路径都在这里，做 PPT 的同学不用看本地代码。

### 0:25-1:10 Neo4j 产品图：拖拽和点节点

操作：

- 打开 `Neo4j图谱`。
- 拖动一个用户节点。
- 点一个用户节点，再点推荐节点或 GraphRAG 证据节点。

讲什么：

> 这块展示的是产品运行图，不是装饰图。节点包括用户、兴趣、价值观、推荐、GraphRAG 证据、闪电搭子、首约安全和治理记录。点击节点可以看到 label、name、score、evidence 等字段。老师如果追问 Neo4j 文件，后台下面也列了 CSV 和 Cypher 路径：nodes.csv、relationships.csv、import_campus_match_ai.cypher 和 demo_queries.cypher。

要点：

- 一定要点节点，展示右侧字段。
- 拖动节点，证明不是静态图片。
- 讲“推荐为什么可信”：看共同兴趣、共同价值观、GraphRAG 路径。

### 1:10-1:50 检索与 RAG：展示 Top-K 证据

操作：

- 切到 `技术证据`。
- 展示一个 query 的 Top-K。
- 展示 RAG steps。

讲什么：

> 这里可以看到搜索不是只靠关键词。比如“会弹吉他的阳光学长”，系统先做 Text-to-Graph，把自然语言 query 变成显性需求、隐性意图、画像字段和硬条件。显性需求保证可解释，隐性意图通过图谱扩散补召回。后面再做 BM25 稀疏检索、Dense 稠密向量检索、Graph 约束和硬条件融合排序。聊天这里展示的是 RAG trace：query rewrite、router、retrieval、rerank、context compression、final answer 和 safety verifier。它解释了为什么现在不会一直重复同一句剧本杀问题，因为活动推荐会命中防编造和安全边界策略。

要点：

- 指出 MiniLM 384 维、FAISS `IndexFlatIP`。
- 指出 BM25 参数 `k1=1.5,b=0.75`。
- 指出显性需求、隐性意图、画像字段之间的图谱路径。
- 指出 RAG Top-K 文档和 final_suggestion。

### 1:50-2:30 GNN 与治理：展示训练结果和分数如何进排序

操作：

- 仍在 `技术证据`，滚到 `GNN 链接预测样例` 和 `GCN 风险节点分类`。
- 如需展示分数如何进入推荐，再切到 `匹配推荐` 看分数拆解。

讲什么：

> 这块说明图不只是画出来，还进入了模型。GraphSAGE 做用户-用户链接预测，输出 `gnn_link_score`，以 0.10 权重进入最终匹配分数。GCN 做风险节点分类，把治理事件和图邻域传播后得到风险概率。治理策略再把信用分转成可见度 multiplier，例如信用分低于 85 就推荐轻度降权，严重不安全反馈会限制主动邀约并进入复核。

要点：

- GraphSAGE：80 epoch、hidden 128、AUC 0.7039。
- GCN：80 epoch、hidden 96、AUC 0.9825、accuracy 0.88。
- 强调伪标签和合成治理标签，不夸成真实业务模型。

### 2:30-3:00 闪电搭子、热度、首约安全

操作：

- 切到 `搭子任务` 展示闪电搭子候选排序。
- 再切到 `关系安全` 展示热度、首约安全和信用治理。

讲什么：

> 最后看动态闭环。闪电搭子不是恋爱推荐公式，它按任务、时间、地点、活动类型、照顾信号和安全地点排序。热度曲线是后台合成历史样本，用消息数、回复延迟、积极比例和共同话题算出来；首约安全则看地点是否公开、人流和安保等级。这样后台能管的不只是推荐结果，还有解释、风险、场景和后续关系变化。

收尾：

> 总结一下，我们的技术重点不是“页面像 App”，而是从画像抽取、向量检索、图谱、RAG、GNN 到治理都能在后台看到证据和参数。

## 5. 参数速查表

| 类别 | 参数 |
|---|---|
| 随机种子 | `seed=42` |
| 用户数 | 120 |
| Top-K 推荐 | 5 |
| 文本 embedding | `120 x 384` |
| 图片 embedding | `120 x 48` |
| MiniLM | 12 layers、12 heads、hidden 384、intermediate 1536、max_seq_length 128 |
| BM25 | `k1=1.5`、`b=0.75`、`avg_doc_len=291.57` |
| BM25 hybrid weights | BM25 0.30、Dense 0.32、Graph 0.26、Constraint 0.12 |
| Intent hybrid weights | Vector 0.34、Sparse 0.24、Graph 0.28、Constraint 0.14 |
| Matching weights | Text 0.27、Graph 0.22、Value 0.18、Goal 0.10、Communication 0.05、Image 0.08、GNN 0.10 |
| Penalties | Goal conflict 0.30、Deal breaker 0.40、Campus 0.05、Communication 0.12 |
| FAISS Flat | `IndexFlatIP` |
| FAISS IVF | `nlist=8`、`nprobe=2` |
| FAISS HNSW | `M=16`、`efConstruction=40`、`efSearch=32` |
| GraphSAGE | 80 epochs、hidden 128、AdamW lr 1e-3、weight_decay 1e-4、AUC 0.7039 |
| GCN | 80 epochs、hidden 96、AdamW lr 1e-3、weight_decay 1e-4、AUC 0.9825、accuracy 0.88 |
| RAG retrieval | Top-3 evidence |
| RAG API | `temperature=0.4`、`max_tokens=220` |
| Interview API | `temperature=0.1`、`max_tokens=1200` |
| Neo4j 产品图 | 5209 nodes、14600 relationships |

## 6. 最容易被老师追问的问题

### 1. 你们真正训练了模型吗？

训练了两个本地模型：

- GraphSAGE 链接预测：预测用户 A 和 B 是否可能匹配，结果接入推荐分数。
- GCN 风险节点分类：预测用户是否风险节点，结果用于后台治理展示。

没有训练：

- MiniLM 文本向量模型。它是预训练 encoder，我们直接使用。
- 生成式聊天模型。聊天生成通过 RAG + 少量 API 调用验证。
- CLIP 图片模型。当前图片向量是 48 维颜色直方图。

### 2. GraphSAGE 的 base knowledge 是哪里来的？

不是外部知识库，也不是网上爬的数据。base knowledge 来自合成用户画像和本体：

- 用户字段：兴趣、价值观、目标、沟通方式、时间、雷点、校区、专业。
- 图边：User 连接这些属性节点。
- 伪标签：共同兴趣至少 2 个、共同价值观至少 1 个、关系目标一致。

所以它学到的是“画像图结构下的匹配可能性”，不是现实世界的恋爱成功率。

### 3. GCN 风险分类为什么 AUC 这么高？

因为风险标签来自合成治理规则，模型输入里也包含治理属性节点，所以任务比真实风控简单。答辩时要说这是课程方法验证：展示 GCN 节点分类如何接入产品治理，不把它包装成线上风控准确率。

### 4. 聊天回复到底是不是向量检索？

是。聊天 RAG 先用 384 维短文本向量检索 Top-3，再叠加规则分数，最后才生成或取模板建议。不是单纯规则模板，也不是直接把用户问题扔给大模型。

### 5. API 调用到底做了什么？

两类：

- 访谈抽取：让模型把模拟问答转成实体和三元组 JSON。
- RAG 回复：把 Top-K 检索证据喂给模型，让它输出一句克制、可发送的中文回复。

最终文档展示的是 10 条访谈抽取和 10 条 RAG 回复完整结果。曾尝试 100 次批量调用，用户看到约 50 条后停止以保护额度；那次中断不作为最终实验结果。

### 6. GitHub Pages 上为什么不能实时 API？

GitHub Pages 是静态托管，不能安全保存 API key，也没有后端进程。所以公网 demo 展示生成后的 trace。要实时调用 `/api/chat-rag`，需要本地或服务器启动 `scripts/serve_demo_api.py`。

## 7. PPT 结论页可以怎么收

不要说“我们用了很多 AI 技术”。应该这样说：

> 我们的核心贡献是把校园社交里原本模糊、不可解释的信息，组织成了可检索的向量、可追溯的知识图谱、可解释的 GraphRAG 路径和可学习的图模型分数。用户端负责把复杂技术变成自然交互，管理员端负责把模型、图谱、检索、RAG 和治理证据摊开给老师看。当前数据是合成 demo，但算法链路、训练 trace、导出文件和前端可视化都是实际跑通的。
