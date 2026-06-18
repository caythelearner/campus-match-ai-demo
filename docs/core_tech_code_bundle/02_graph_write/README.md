# 02_graph_write

这个目录对应“图谱写入”和“Neo4j 产品图导出”。

关键文件：

- `kg.py`：把画像转成三元组，并提供 `ProfileGraph`。
- `ontology.py`：校验 relation 的 domain/range 是否合法。
- `neo4j_trace.py`：导出 Neo4j 节点、关系、Cypher。
- `import_neo4j.py`：把导出文件真正写进 Neo4j。

对应输出：

- `data/triples.csv`
- `outputs/ontology_validation.json`
- `outputs/neo4j/campus_match_ai_nodes.csv`
- `outputs/neo4j/campus_match_ai_relationships.csv`
- `outputs/neo4j/import_campus_match_ai.cypher`
