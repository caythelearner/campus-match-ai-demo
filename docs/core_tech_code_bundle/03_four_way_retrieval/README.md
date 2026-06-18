# 03_four_way_retrieval

这个目录对应“四路召回”：BM25、Dense、Graph、Constraint。

关键文件：

- `intent_search.py`：Text-to-Graph，把自然语言 query 拆成显性需求、隐性意图、画像字段、硬条件。
- `bm25_hybrid.py`：BM25 + Dense + Graph + Constraint 融合。
- `vector_search.py`：FAISS / ANN 检索实验。
- `embeddings.py`：文本向量和图片向量生成。

主要权重：

- Intent hybrid：`vector 0.34 + sparse 0.24 + graph 0.28 + constraint 0.14`
- BM25 hybrid：`bm25 0.30 + dense 0.32 + graph 0.26 + constraint 0.12`

对应输出：

- `outputs/intent_graph_traces.json`
- `outputs/hybrid_search_traces.json`
- `outputs/bm25_hybrid_traces.json`
- `outputs/faiss_ann_benchmark.json`
