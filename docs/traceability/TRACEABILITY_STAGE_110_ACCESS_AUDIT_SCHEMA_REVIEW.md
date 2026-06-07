## Stage 110R: access_audit_events schema candidate review

结论：**有条件通过**

本轮复审对象是 ccess_audit_events 的候选 ORM + Alembic migration。schema 方向本身是对的：它是系统访问审计，不是病例 provenance，不进入 trace/evidence，也不写 recommendation。字段、FK、索引整体能支撑后续访问审计、deny/allow 追踪和治理回放。

但有一个需要单独澄清的点：**Alembic 状态显示存在不一致迹象**。current 仍是旧 revision，而 history 已显示新 head；同时 lembic check 却返回 No new upgrade operations detected.。这和 尚未 apply 候选 migration这一事实并不完全一致，因此不建议把它直接当成可以进入 apply 的信号。建议先做 Stage 110B 的只读核查，再决定是否进入受限 apply。

### 1) ORM / migration 一致性

通过。

我核对到的字段、nullable、FK、index、unique 在 ORM 与 migration 之间整体对齐：

- id
- ccess_event_id
- ctor_user_id
- ctor_type
- ctor_role
- ccess_mode
- esource_type
- esource_id
- case_id
- patient_id
- 	race_id
- decision
- denial_reason
- policy_source
- equest_id
- oute_path
- method
- metadata_json
- created_at

关于 created_at / 没有 updated_at：这是合理的。ccess_audit_events 是 append-only 访问审计事件，天然适合只有 created_at，不需要 updated_at。

### 2) Alembic 状态异常

这里需要**重点澄清**。

当前描述是：

- current = 8c2f3a1e9d47
- history = 8c2f3a1e9d47 -> 4d9c8b2f1a6e head
- check = No new upgrade operations detected

如果新 revision 还未 apply，check 却没有提示数据库不是最新，这个状态不太常规。它通常意味着以下至少一种情况需要确认：

- 运行目录 / 容器内 Alembic revision 文件不同步
- env.py 读取的 metadata 与实际代码树不一致
- lembic check 执行的路径不是同一个仓库/同一个 env
- 版本文件存在，但没有被当前 lembic check 命令实际纳入比较

因此我建议把这个点作为 Stage 110B 的**只读核查项**，先不 apply：

- 确认 repo / runtime / container migration 文件是否一致
- 确认 lembic heads/current/history/check 是否在同一目录、同一 env 下执行
- 确认是否存在未同步 metadata 或命令路径问题

这不是 schema blocker，但它是 apply 前必须解释清楚的治理问题。

### 3) FK 设计

通过。

#### ctor_user_id nullable FK

合理。访问审计中允许匿名 / system / service 事件，nullable 能覆盖这些情况。

#### case_id / patient_id nullable FK

合理。并不是所有访问事件都必须能准确回挂到病例或患者，尤其是 deny / missing resource / system-level audit 场景。

#### 	race_id 不做硬 FK

合理。访问审计是系统层事件，不应强制绑定到病例 trace 的生命周期。

#### esource_id 不做 polymorphic FK

合理。访问审计本身就是 polymorphic resource audit，不应该被硬 FK 限死。

我认为这个设计不会妨碍 denied / missing resource 的记录，反而更适合 audit-only 场景。

### 4) Index 是否过度

整体不算过度，但偏完整型而不是极简型。

当前索引里我认为是合理的：

- ctor_user_id
- case_id
- patient_id
- 	race_id
- esource_type
- esource_id
- decision
- ccess_mode
- created_at
- (case_id, created_at)
- (actor_user_id, created_at)
- (resource_type, resource_id)
- (decision, created_at)

评价：

- 对治理回放和审计筛查是友好的
- 对 write-heavy 场景会稍微多一点，但还不构成必须删除项
- (resource_type, resource_id) 和 (decision, created_at) 都是有理由存在的，不建议本阶段删掉

如果未来审计写入量显著增大，再考虑延后某些组合索引也可以，但现在不是 blocker。

### 5) Taxonomy string / app-level validation

通过。

本阶段不建 DB enum 是可接受的。访问审计 taxonomy 往往比临床主数据更容易扩展，先用 string + app-level validation 保留灵活性更稳。

### 6) Privacy / PHI 边界

通过。

metadata_json 的边界写得是清楚的：

- 不存完整 clinical payload
- 不存 mapped_features / source_refs / doctor_provided_features 原文
- 不存 token / secrets
- 不存完整 request body
- 只存轻量上下文，例如 counts、mode、reason、policy branch

这是对的。

不过我建议后续 helper / emitter 在写入时继续强制 metadata sanitizer，避免工程上后来把它慢慢写胖。当前 schema 不要求存 full payload，这一点要在实现上持续守住。

### 7) 与 trace/evidence 边界

通过。

ccess_audit_events 是系统访问审计，不是 	race_events，也不写 evidence_nodes / evidence_edges，更不进入病例 provenance graph。这个边界是正确的。

### 8) 是否建议进入 Stage 110D restricted apply

建议先走 **Stage 110B 只读核查**，暂不直接进入受限 apply。

理由不是 schema 本身不行，而是 Alembic 状态存在需要解释的异常信号。只有这个点澄清后，才适合讨论 Stage 110D restricted apply approval。

### 9) 总结

Stage 110 的 schema 方向是对的，字段和边界都站得住：它把访问审计独立成一层，不污染病例 trace/evidence，也不强行把 polymorphic audit 做成硬外键。

当前唯一需要认真处理的是 Alembic 状态一致性问题。这个问题不应该直接带着去 apply，而应先做只读核查把环境/路径/metadata 对齐。

### 合规确认

本轮复审未改代码、未改数据库、未执行 Alembic、未加入 allowlist、未打开 shadow switch、未加载模型、未 	orch.load、未训练、未真实推理、未启用 GPU、未启用 Nginx、未改前端，也没有扫描、复制、移动或猜测任何 .pth/.pt/.onnx/.ckpt/.safetensors 文件。
