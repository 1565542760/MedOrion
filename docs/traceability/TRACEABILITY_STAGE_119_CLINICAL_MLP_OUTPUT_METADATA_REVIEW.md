## Stage 119R: clinical MLP shadow output calibration / limitations review

结论：**通过**

本轮复审对象是 clinical MLP fold5 shadow output 的 calibration / limitations hardening。整体判断是：这一步是有价值且足够稳的。它没有改变概率计算、没有改变 candidate label 选择、没有改变模型，只是在 shadow output metadata / limitations / calibration warning 上做了收紧。这样做是对的，因为它能明显降低 极端概率输出被误读成临床确证的风险。

### 1) calibration / limitation metadata 是否足够

通过。

当前新增的限制语义是足够强的：

- 
ot_for_diagnosis
- shadow_only
- 
ot_formal_recommendation
- 
ot_externally_validated
- internal_retrospective_evaluation_only
- probability_uncalibrated
- extreme_probability_not_clinical_certainty
- 
equires_doctor_review
- 
equires_quality_review_before_clinical_use

再加上 backend 的补充限制：

- ridge_runtime = temporary_mri3d_runner
- long_term_runtime_target = model_service_or_inference_service
- model_family = clinical_mlp
- old = fold5
- label_mapping = {CAP: 0, COP: 1}

这套组合已经足够明确地告诉下游：

- 这不是 diagnosis
- 这不是 recommendation
- 这不是可直接临床使用的结论
- 这是内部/回顾性的 shadow 结果

所以从防止误读的角度，我认为这套 metadata 是足够的。

### 2) 极端概率输出风险

通过，但需要继续保留可见警示。

probabilities = {CAP: 0.0, COP: 1.0} 这种极端输出，天然就容易让人误以为模型非常确定。现在补上：

- calibrated = false
- extreme_probability_not_clinical_certainty
- probability_uncalibrated

这已经大幅降低误读风险。

我认为目前还**不构成必须修改项**，但后续展示层最好继续做到两件事：

- 强制展示 raw logits
- 强制展示醒目的 calibration / validation warning

如果以后有前端或审计视图，我也建议把not externally validated与not for diagnosis做成明显的固定标识，而不是藏在折叠区里。

### 3) prediction_raw_json 边界

通过。

当前 prediction_raw_json 保存的是：

- logits
- label_mapping
- model_version_id
- input_snapshot_id
- 	race_id
- model_input_schema_id
- disease_task_feature_set_id
- eature_count
- mapped_feature_count
- 
unner_runtime
- dry_run_label

并且**不保存完整 clinical feature payload**，这点是正确的。

我的判断：

- 这个边界合理
- 这仍然主要是 provenance / audit 数据，不是临床原文数据
- PHI 风险可控

当然，input_snapshot_id、	race_id、model_version_id 依然是敏感关联标识，所以它们应继续只在受控审计范围内使用；但这不构成当前设计的必须修改项。

### 4) shadow audit / trace-evidence 边界

通过。

这一步写的是 shadow_inference_runs / shadow_inference_outputs，没有写 
ecommendation，也没有写 	race_events / evidence_nodes / evidence_edges，这是正确的。

它仍然不是正式 diagnosis，也不是 recommendation。它的结果是 shadow output，应该留在 shadow audit 侧，不应该自动进入病例 provenance graph。

### 5) temporary bridge 风险

通过。

这次在 metadata 上把桥接属性说得很清楚：

- ridge_runtime = temporary_mri3d_runner
- long_term_runtime_target = model_service_or_inference_service

这两项足够明确地表达这是短期桥，不是长期架构。

所以我认为：

- 当前 bridge 风险是可接受的
- 但后续仍应逐步迁回 model-service / inference-service
- 不建议继续把 backend 变成长期 subprocess 推理平台

### 6) 是否建议进入 Stage 120

建议进入 Stage 120，但推荐方向是：

**A. checkpoint review docs for 117/118/119**

理由：

- 现在的 bridge 与 metadata hardening 已经达到一个相对稳的阶段
- 先把 117/118/119 的 review 文档做整理和 checkpoint，更利于收束阶段边界
- 这会比立刻去做前端展示或继续扩模型族更稳

如果后续要做用户可见的展示，我建议在文档收口之后再考虑：

- B. frontend display clinical MLP shadow result with warnings

至于 imaging ResNet18 / multimodal provenance，我建议排后面，不要马上扩。当前临床 MLP bridge 还没必要立刻横向扩面。

### 7) 总结

Stage 119 的意义是：

- 保持 shadow 输出语义不变
- 但把输出的校准、限制和风险提示写得更硬
- 这样能明显降低极端概率被误读的风险
- 同时仍然不把结果升级成 diagnosis / recommendation

这一步是对的，而且和前面的桥接设计是连贯的。

### 合规确认

本轮复审未改代码、未改数据库、未执行 Alembic、未打开 shadow switch、未加入 allowlist、未训练、未写 recommendation、未写 trace/evidence、未改前端、未读其它 folds，也没有扫描、复制、移动模型文件。
