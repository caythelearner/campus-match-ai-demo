# API 接入说明

本项目默认离线可跑。接入 API 只需要改少量函数。

更新时间：2026-06-06

当前建议：先不要让 API 阻塞主 demo。默认离线版本已经能生成合成用户、生活方式图占位图、知识图谱、Neo4j 留痕、向量、匹配、GraphRAG 解释、动态场景、恋爱热度、线下约会上下文和知识治理结果。

## 1. 图像生成 API

入口文件：

```text
src/campus_match/image_generation.py
```

核心函数：

```python
generate_image_via_api(prompt, output_path)
```

默认假设 API 支持：

```json
{
  "prompt": "...",
  "model": "...",
  "size": "1024x1024",
  "response_format": "url"
}
```

如果服务商返回：

```json
{
  "data": [
    {
      "url": "https://..."
    }
  ]
}
```

当前代码可以直接解析。

如果服务商返回 base64：

```json
{
  "data": [
    {
      "b64_json": "..."
    }
  ]
}
```

当前代码也可以解析。

如果字段名不同，只需要修改：

```python
image_url = ...
image_b64 = ...
```

## 2. LLM API

入口文件：

```text
src/campus_match/profile_extraction.py
src/campus_match/graph_rag.py
```

默认使用 OpenAI-compatible chat completions 形态：

```json
{
  "model": "...",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "temperature": 0.2
}
```

如果你们用百炼、硅基流动、OpenRouter 或其他兼容接口，通常只需要设置：

```bash
export LLM_API_URL="..."
export LLM_API_KEY="..."
export LLM_MODEL="..."
```

如果返回结构不是：

```python
resp.json()["choices"][0]["message"]["content"]
```

则修改对应解析逻辑。

## 3. 建议

1. 先离线跑通全链路。
2. 再接图片 API。
3. 最后接 LLM API。
4. 不要一开始就依赖 API，否则调试成本高。

## 4. Neo4j 接入

Neo4j 不算外部 API，但属于图数据库增强展示。本项目默认会生成 Neo4j 留痕文件，不需要数据库也能交付：

```text
outputs/neo4j/campus_match_ai_nodes.csv
outputs/neo4j/campus_match_ai_relationships.csv
outputs/neo4j/import_campus_match_ai.cypher
outputs/neo4j/demo_queries.cypher
outputs/neo4j/neo4j_trace_summary.json
```

如果本机已经安装 Neo4j Desktop 或 Neo4j Community，启动数据库后执行：

```bash
python scripts/import_neo4j.py --uri bolt://localhost:7687 --user neo4j --password 你的密码 --clear
```

Neo4j Browser 推荐截图查询：

```cypher
MATCH p=(u:User {node_id: 'U001'})-[r]->(x)
RETURN p
LIMIT 80;
```

如果没有时间安装 Neo4j，就在 Streamlit 的“Neo4j 图数据库留痕”区截图，作为第 5 章图数据库的实现证据。
