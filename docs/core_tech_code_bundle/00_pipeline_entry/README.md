# 00_pipeline_entry

这个目录对应“全链路怎么串起来”。

关键文件：

- `run_pipeline.py`：命令行入口。
- `pipeline.py`：真正的全链路编排。
- `default.json`：用户数量、embedding 维度、匹配权重、RAG/API 开关等配置。

核心顺序：

1. 生成/读取用户画像。
2. 访谈抽取实体和三元组。
3. 构建画像图谱并做本体校验。
4. 生成文本/图片向量。
5. 跑四路召回和 FAISS 对比。
6. 训练 GraphSAGE/GCN。
7. 计算推荐匹配。
8. 生成 GraphRAG、聊天 RAG、闪电搭子、关系热度。
9. 导出 Neo4j 产品图。

运行：

```bash
python scripts/run_pipeline.py --run-gnn
python scripts/build_html_demo.py
```
