## Coursework Stage C5R: case imaging input candidate schema / API skeleton review

结论：**通过**

本轮复审对象是 case_imaging_inputs 的候选 ORM + migration + API skeleton。整体判断是：它把影像输入明确做成了一个独立的、以 case 为中心的元数据/引用层，没有把 tabular case_model_input_snapshot 和 raw imaging payload 混在一起，也没有把影像输入做成病例证据链或模型运行触发器。这条边界是正确的。

### 1) ORM / migration 一致性

通过。

我核对到的字段、nullable/default、JSONB、FK、index、unique 在 ORM 与 migration 之间整体对齐：

- id
- input_asset_id
- case_id
- patient_id
- 	race_id
- modality
- source_type
- storage_uri
- deidentified
- 
ot_for_diagnosis
- provenance_json
- quality_flags_json
- created_at
- updated_at

评价：

- deidentified / 
ot_for_diagnosis 在 ORM 和 migration 中都是强制 true 语义，这很好
- provenance_json / quality_flags_json 用 JSONB 承载轻量元数据是合理的
- created_at / updated_at 维持项目习惯，也合理
- 	race_id 不做硬 FK 也符合当前审计/引用层定位

这份 schema 没有把 raw binary 影像内容放进表里，因此它确实是 candidate schema，不是影像存储层。

### 2) case_imaging_inputs 是否独立于 case_model_input_snapshot

通过。

这点我认为是本次 C5 里最重要的边界之一：

- case_model_input_snapshot 仍然是 tabular / model-input provenance
- case_imaging_inputs 是 imaging reference / metadata 层
- 两者没有混在一起

当前 case_imaging_inputs 只保存：

- storage_uri
- provenance_json
- quality_flags_json
- case / patient / trace / modality / source_type 等引用与上下文

没有把影像二进制、临床推理结果或模型输出塞进来，这个边界是对的。

### 3) API skeleton 是否合理

通过。

当前 API surface：

- POST /api/v1/cases/{case_id}/imaging-inputs
- GET /api/v1/cases/{case_id}/imaging-inputs
- GET /api/v1/imaging-inputs/{input_asset_id}

我认为这组接口是合理的：

- 写入按 case 组织
- 列表按 case 组织
- 详情按 input asset 读

同时，列表返回 summary、detail 返回完整 provenance/reference，这个方向也符合先最小暴露的原则。

### 4) RBAC / case scope

通过。

当前实现沿用了 equire_case_access，这很好，因为影像输入本来就应该继承 case scope，而不是成为一个脱离病例的自由资源。

我对当前 RBAC 的判断是：

- case scope 正确
- detail 仍然需要 case-level access
- list 仍然需要 case-level access

这符合项目当前的 ownership / RBAC 设计节奏。

### 5) PHI / payload 边界

通过。

当前设计是只保存 metadata/reference，不返回真实 image payload，不上传二进制影像，这是对的。

我认为以下边界是合理的：

- 不存影像二进制
- 不做文件上传/下载为核心能力
- storage_uri 只是引用，不是影像内容本体
- provenance_json / quality_flags_json 只承载轻量元数据

storage_uri 本身仍然是敏感引用信息，因此 detail 访问必须继续 case-scoped；但这不构成当前 schema 的 blocker。

### 6) deidentified=true、
ot_for_diagnosis=true 的强制策略

通过。

这两个字段作为强制策略是足够清楚的，而且和之前的模型输入 / shadow / runner 管道语义一致。

这意味着：

- 这不是原始临床诊断通道
- 这不是可直接临床使用的影像内容
- 这条链路是用于治理、参考和候选输入准备

如果后续要更严格，也可以在更上层加二次 policy，但当前强制 true 的方式是合适的。

### 7) 与 access audit / shadow audit / trace / evidence 的边界

通过。

这条链路保持得很干净：

- 不写 recommendation
- 不写 trace / evidence
- 不触发 shadow
- 不把影像输入直接塞进病例 provenance graph

这点很重要。case_imaging_inputs 作为输入 reference 层是对的，但它不应该默认升级成病例证据图的一部分，也不应该自动触发任何模型执行。

### 8) Alembic 状态裁决

可接受，且符合候选 migration 未 apply的预期状态。

当前：

- 候选 head 9c6a5d4e3f2 已存在
- DB current 仍是 4d9c8b2f1a6e
- lembic check 提示 Target DB not up to date

这正是未 apply 候选 migration 时应当看到的状态，不是异常。

因此，这里**不需要**像 Stage 110 那样额外做 Alembic 路径一致性澄清；它本身就是预期的未 apply 状态。

### 9) 是否建议进入 C5D restricted apply

建议进入 **C5D restricted apply**。

原因：

- ORM / migration 一致
- schema 与 API skeleton 边界清楚
- case scope / RBAC 路径正确
- PHI 和 payload 边界是保守的
- 没有把影像输入和 tabular snapshot 混在一起
- 没有写 recommendation / trace / evidence / shadow

我没有看到必须先修改再 apply 的 blocker。

### 10) 总结

C5 的价值在于：

- 让 imaging input 形成独立的候选 schema / API 骨架
- 明确它只是 metadata / reference 层
- 继续保持 not_for_diagnosis / deidentified / case-scoped 的治理原则
- 不把影像输入误写成临床结论、病例证据或模型执行触发器

这条路线是稳的。

### 合规确认

本轮复审未改代码、未改数据库、未执行 Alembic upgrade/stamp/downgrade、未写 imaging rows、未上传/读取/复制影像文件、未触发模型/torch.load/训练/推理、未写 recommendation / trace / evidence / shadow audit、未打开 shadow switch / allowlist。
