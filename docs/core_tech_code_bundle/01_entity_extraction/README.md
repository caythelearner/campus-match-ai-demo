# 01_entity_extraction

看这个目录时，重点打开 `interview_extraction.py`。

关键函数：

- `_interview_sentences(profile)`：把画像转成 4 轮访谈。
- `_build_llm_prompt(...)`：让 LLM 只按访谈文本抽实体和三元组。
- `_llm_extract_interview(...)`：API JSON 抽取。
- `_rule_extract_interview(...)`：规则兜底抽取。
- `generate_interview_extraction_traces(...)`：输出完整 trace。

对应输出：

- `outputs/interview_extraction_traces.json`
