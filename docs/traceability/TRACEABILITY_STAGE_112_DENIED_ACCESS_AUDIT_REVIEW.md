## Stage 112R: denied snapshot access audit review

结论：**通过**

本轮复审对象是 snapshot detail 路径上的 denied access audit skeleton。当前实现保持了一个很健康的边界：只在认证后的 detail 403 分支补一条 denied audit，而不改变主业务错误码，也不扩散到 list / trace / shadow / recommendation / registry / orchestration。这个方向是对的。

### 1) denied emit 边界

通过。

当前接入点只在：

- GET /api/v1/model-input-snapshots/{input_snapshot_id}
- equire_snapshot_access(..., mode='detail') 的 403 捕获处

这条边界是足够窄的。它验证了 denied audit 的落点，但不会把访问审计一下子铺满所有资源。

我认为当前阶段不接以下路径是合理的：

- 不接 missing_token
- 不接 missing_snapshot
- 不接 list
- 不接 trace
- 不接 shadow
- 不接 recommendation
- 不接 registry
- 不接 orchestration

另外，当前不为测试补写 ownership 数据也是对的。Stage 112 的重点是审计 emit 行为，而不是去伪造 production ownership。

### 2) denied audit 语义

通过。

当前 denied row 的语义是清楚的：

- decision = denied
- denial_reason = access_denied
- policy_source = denied_no_policy
- esource_type = model_input_snapshot
- ccess_mode = detail

这套字段足以表达：

- 是什么资源
- 什么模式
- 为什么被拒绝
- 发生在什么病例上下文里

我认为这个语义已经足够用于审计和回放，没有明显歧义。

### 3) metadata_json / PHI 边界

通过，但应继续保持警惕。

当前 metadata_json 只存轻量摘要，不存完整 clinical payload，这一点是正确的。你给出的样例里，eason、untime_stub、mapped_feature_count、missing_feature_count 等字段都属于可接受的轻量上下文，不构成完整 PHI 外泄。

我对这部分的判断是：

- 当前边界是安全的
- mapped_feature_count / missing_feature_count 这类计数是安全的
- 目前没有明显 PHI 泄漏风险

但后续仍建议往更严格方向走：

- 更明确的 metadata whitelist
- 更严格的 sanitizer 策略

也就是说，当前可以接受，但不应把它视为最终上限。

### 4) 主业务错误行为

通过。

当前错误行为保持稳定：

- 403 仍然是 ccess_denied
- 401 missing_token 不变
- 404 input_snapshot_not_found 不变
- audit 写入不改变主业务错误码

这点很重要，因为访问审计应该是旁路记录，而不是把业务错误语义改掉。

这次 helper-level 403 仍然返回 ccess_denied，说明 audit 的引入没有污染主错误链路。

### 5) access audit 与 trace/evidence 边界

通过。

ccess_audit_events +2 是预期的；ecommendations / trace / evidence / shadow / snapshot / assignment 计数不变也是正确边界。

这说明：

- 访问审计仍然是旁路
- 没有进入病例 provenance graph
- 没有污染临床证据链

这条边界必须继续守住。

### 6) 是否建议进入 Stage 113

建议进入 Stage 113，但我支持你给出的方向：先做收口，再扩面。

推荐方向：

**A. clean up/checkpoint Stage 110R + 111R review docs**

理由：

- Stage 112 已经证明 denied audit 能写
- 现在仓库里故意保留了两份未跟踪复审文档，先把 review 文档收干净更稳
- 在这之后，再决定要不要扩到 shadow audit read APIs 或更严格的 metadata whitelist

如果后续想往审计读取接口推进，B/C/D 都可以排队，但我仍然认为现在先做 A 更合适。

### 7) 总结

Stage 112 的价值在于：

- 把 denied access audit 也补上了
- 但仍然只在 snapshot detail 这一条窄路上落点
- 主业务错误码没有被改
- audit 仍然不进入病例 trace/evidence

这是一个很健康的治理推进节奏：先把 allowed / denied 的 audit 行为跑通，再决定是否进一步扩展覆盖面。

### 合规确认

本轮复审未改代码、未改数据库、未执行 Alembic、未加入 allowlist、未打开 shadow switch、未加载模型、未 	orch.load、未训练、未真实推理、未启用 GPU、未启用 Nginx、未改前端，也没有扫描、复制、移动或猜测任何 .pth/.pt/.onnx/.ckpt/.safetensors 文件。
