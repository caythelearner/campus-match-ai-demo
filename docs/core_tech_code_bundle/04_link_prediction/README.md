# 04_link_prediction

这个目录对应“潜在链接预测”和“最终推荐排序”。

关键文件：

- `gnn.py`：GraphSAGE 链接预测、GCN 风险节点分类。
- `matching.py`：把文本、图谱、图片、GNN 分数合成最终匹配分。

关键点：

- GraphSAGE 预测用户 A 和用户 B 是否可能匹配。
- 没有真实恋爱成功标签，所以使用共同兴趣、共同价值观、关系目标一致构造伪标签。
- `gnn_link_score` 以默认 `0.10` 权重进入最终匹配排序。

对应输出：

- `outputs/graphsage_link_predictor.pt`
- `outputs/gnn_metrics.json`
- `outputs/gnn_pair_scores.json`
- `outputs/gcn_risk_classifier.pt`
- `outputs/gnn_node_risk_scores.json`
