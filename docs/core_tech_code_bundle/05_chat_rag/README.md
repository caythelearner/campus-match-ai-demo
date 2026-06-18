# 05_chat_rag

这个目录对应“聊天 RAG 检索和回复生成”。

关键文件：

- `chat_retrieval.py`：聊天知识库、画像上下文、Top-K 检索。
- `rag_pipeline.py`：离线 RAG trace，包含 rewrite、router、retrieval、compression、generation、verifier。
- `realtime_rag.py`：本地服务端实时 RAG 入口。

RAG 流程：

1. `query_rewrite`
2. `router`
3. `Top-K retrieval`
4. `context_compression`
5. `LLM/template generation`
6. `safety_verifier`

对应输出：

- `outputs/chat_vector_retrieval_trace.json`
- `outputs/rag_pipeline_traces.json`
- `outputs/realtime_chat_api_traces.jsonl`
