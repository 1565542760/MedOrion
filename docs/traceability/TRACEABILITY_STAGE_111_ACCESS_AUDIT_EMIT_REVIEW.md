## Stage 111R: access audit emit helper skeleton review

结论：**通过**

本轮复审对象是 ccess_audit 的 emit helper skeleton 以及它在 model_input_snapshot detail read 路径上的接入。整体判断是：这一步的边界是合理的、足够窄，而且没有把访问审计做成主业务依赖。成功 detail read 记录 allowed audit row、deny 分支保留 skeleton，这个方向是对的。

### 1) emit helper 边界

通过。

pp/core/access_audit.py 作为独立 helper 放置是合理的。它把访问审计逻辑从 ccess_control 中拆了出来，符合 访问判断和访问记录分离的思路。

当前接线也很克制：

- 只接 GET /api/v1/model-input-snapshots/{input_snapshot_id} 的 detail read
- 暂不接 list
- 暂不接 trace/evidence
- 暂不接 shadow audit
- 暂不接 recommendations
- 暂不接 model registry
- 暂不接 orchestration

我认为这很合适。因为 snapshot detail 是一个天然的窄门，能验证审计写入链路，但不会一下子把整个系统都接上。

另外，emit_access_audit_event 失败后只记录日志并返回 None，不让主业务 500，这个策略是合理的。访问审计本来就应该是尽力而为的旁路记录，不应该把主读取流程变成审计强依赖。

### 2) sanitizer 是否足够

通过，但要保持警惕。

当前 sanitizer 的策略是：

- 只保留 JSON 兼容值：str / int / float / bool / null / list / dict
- 屏蔽 key：	oken / authorization / password / secret / mapped_features / source_refs / doctor_provided_features / request_body / raw_payload
- 深度超过 4 层会转安全摘要
- metadata_json 不保留完整 clinical payload

我的判断：

- 当前 blocked key 集合是合理的
- depth limit = 4 也合理
- 从设计上看，已经能显著降低 PHI/secret 泄漏风险

但我建议明确把它当作安全基线，不要把它当成绝对不会泄漏的证明。后续如果访问审计要向更多资源扩展，最好继续强化 metadata whitelist 或更严格的字段选择器。

所以：

- **当前没有必须修改项**
- 但未来的收紧方向是明确的：优先 whitelist，而不是只依赖 blacklist

### 3) access audit 与 trace/evidence 边界

通过。

这次写的是 ccess_audit_events，不是 	race_events，也没有写 evidence_nodes / evidence_edges。这个边界是正确的。

它的定位是：

- 系统访问审计
- 不是病例 provenance
- 不进入病例证据图

这点必须坚持。否则 access audit 会慢慢侵入临床证据链，最后把谁看过什么与临床上发生了什么混在一起。

这次没有写 evidence，是正确的；也没有把访问审计变成病例图的一部分，这一点我认为是合格的。

### 4) allowed detail read 行为

通过。

当前行为很符合预期：

- detail read 成功时写 allowed audit row
- esource_type = model_input_snapshot
- esource_id = snap_89c6813a45054fb3
- case_id / patient_id / trace_id 与 snapshot 对齐
- policy_source = dev_fallback 在当前 dev/stub case 下可接受

我认为这些字段足够支撑这次访问发生在什么病例、什么资源、什么模式下的审计需要。

尤其是：

- esource_type / resource_id 足够表达资源定位
- case_id / patient_id / trace_id 足够表达病例归属
- ccess_mode = detail 足够表达访问级别

policy_source = dev_fallback 在当前 dev/stub 阶段是可以接受的，但后续如果进入 production ownership semantics，最好让 policy_source 更清晰地映射到真实 ownership / assignment 路径。

### 5) denied 分支

通过。

当前 denied 分支有 skeleton，说明设计上已经考虑到了拒绝访问的审计可能性，这点是对的。

关于两个细节，我的看法是：

- **未登录 401**：当前不写 audit 是可接受的。因为它甚至还没进入 user-bound access path。
- **missing snapshot 404**：当前不写 audit 也可接受，后续再决定是否补。

也就是说，当前先把已认证后的 detail read allowed/denied接起来是合理的；未登录和 not found 的审计可以作为下一阶段增强，不是本阶段 blocker。

### 6) 计数和范围

通过。

这次验证后：

- ccess_audit_events +2 是预期行为
- ecommendations / trace / evidence / shadow / snapshot / assignments 未变化也是正确边界

这正说明访问审计是旁路写入，没有污染病例图、没有污染推荐、没有污染 shadow 运行链。

### 7) 是否建议进入 Stage 112

建议进入 Stage 112，但方向应继续偏安全治理。

我推荐的方向是：

**A. extend audit emit to denied access attempts**

理由：

- 当前 allowed detail read 已经打通了
- 下一步最值得补的是 denied / forbidden 访问尝试的审计覆盖
- 这样可以把访问安全链条补完整，同时仍然不碰真实 shadow execution

如果团队后续更想先扩到 shadow audit read APIs，也可以排在后面，但我认为当前最优先还是把 denied 访问审计补齐。

### 8) 总结

Stage 111 的价值在于：

- 把访问审计从设计层推进到了实际 emit helper
- 但只接了一个很窄的 detail read 场景
- 没有把主业务变成审计依赖
- 没有把 access audit 混进病例 trace/evidence

这是一种很健康的推进方式：先证明 audit 能写、能隔离、能脱敏，再慢慢扩边界。

### 合规确认

本轮复审未改代码、未改数据库、未执行 Alembic、未加入 allowlist、未打开 shadow switch、未加载模型、未 	orch.load、未训练、未真实推理、未启用 GPU、未启用 Nginx、未改前端，也没有扫描、复制、移动或猜测任何 .pth/.pt/.onnx/.ckpt/.safetensors 文件。
