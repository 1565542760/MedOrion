## Stage 106R: case ownership schema candidate review

结论：**通过**

本轮复审对象是 case ownership 的候选 ORM + Alembic migration。整体判断是：这份 schema 作为 ownership 基座是合适的，边界也保持得比较克制，没有把 case ownership 做成过重的权限系统，也没有影响现有 MVP skeleton 的行为。

### 1) ORM / migration 一致性

通过。

我核对到的字段、nullable、FK、index、unique 在 ORM 与 migration 之间整体对齐：

- cases.owner_user_id
- cases.primary_doctor_id
- cases.organization_id
- cases.access_policy_status
- cases.created_by
- cases.updated_by
- case_assignments.assignment_id
- case_assignments.case_id
- case_assignments.user_id
- case_assignments.role_on_case
- case_assignments.assignment_status
- case_assignments.assigned_by
- case_assignments.assigned_at
- case_assignments.revoked_by
- case_assignments.revoked_at
- case_assignments.reason
- created_at / updated_at 由 TimestampMixin 保持一致

有一个**轻微实现差异**需要如实说明：

- ssignment_status 在 ORM 里有 default='active'
- migration 里没有额外写 DB-level server_default

这不构成 blocker，因为当前它不会破坏表结构一致性，只是应用层默认和数据库层默认不完全同构。作为候选 schema 是可接受的；如果后续希望更强一致性，可以在下一轮再决定是否补 DB default，但这不是本阶段必须项。

### 2) cases 表新增字段是否合理

通过。

#### owner_user_id

建议保留 nullable。当前作为候选 ownership schema，先允许空值最稳，不会破坏现有 case。

#### primary_doctor_id

建议保留 nullable。同样合理。它适合表达临床主责医生，但在现阶段不应强制所有 case 都有值。

#### organization_id

使用 string(64) + nullable 是可接受的。因为当前阶段它更像组织/租户标识语义，而不是立即绑定某个强外键实体。

#### ccess_policy_status

合理。它为后续 policy 治理提供一个轻量状态位，比现在直接把权限逻辑写死在 helper 里更稳。

#### created_by / updated_by

有必要。它们补的是审计与责任链，不是重复字段。

#### 命名/冲突

当前没有看到与现有 cases 字段的明显重复或命名冲突。新增字段的命名都比较直白，易于后续在 helper / UI / audit 中复用。

### 3) case_assignments 表是否合理

通过。

#### ssignment_id

作为唯一字符串是合理的。UniqueConstraint('assignment_id') 足以满足当前审计/外部引用需要，不必在本阶段引入更重的复合唯一约束。

#### 核心字段

case_id / user_id / role_on_case / assignment_status 这组字段已经足够支撑初始 assignment 语义。

#### 责任链字段

ssigned_by / assigned_at / revoked_by / revoked_at / reason 也都合理，能够表达基本的分配和撤销过程。

#### 是否需要 expires_at / scope

当前不属于必须项。若未来要表达临时授权、限定范围或短期生效，可以再加，但 Stage 106 作为 schema candidate 不需要为了未来所有可能性把表一次做重。

#### 不使用 DB enum

可接受。现在先用字符串字段更灵活，也更容易和现有项目的 skeleton / review 阶段保持一致。

### 4) FK / index / constraint 是否合理

通过。

#### FK 名称安全性

我看过这批命名，整体是安全的，没有明显超过 PostgreSQL 63 字符限制的风险。k_case_assignments_* 和 k_cases_* 这套名字都比较克制。

#### index 命名安全性

同样安全。ix_cases_* 和 ix_case_assignments_* 都在合理范围内。

#### 是否过度索引

没有明显过度。case_assignments 的 (case_id, user_id) 和 (case_id, role_on_case) 对预期查询是合理的。

#### 是否缺少必要索引

当前这版已经足够满足 ownership / assignment 的基础查询。

如果后续重点会查 ssigned_at / evoked_at 的时间序列，再考虑补索引即可，但这不构成本阶段 blocker。

#### 是否暂时不做 partial unique 是对的

是的，对。现在不做 partial unique 是合理的，因为这还是候选 ownership 基座，不需要提前把 active assignment 的唯一性策略绑死。

### 5) backward compatibility

通过。

这一点我认为是本次 schema 的优点：

- 新字段都是 nullable
- 不 backfill
- 不把 dev_doctor 写成 production owner
- 不改变 equire_case_access 当前行为

这意味着现有 case 不会被破坏，现有 helper 行为也不会被打乱。作为候选 schema，这种保守推进是对的。

### 6) 与 Stage 104 helper 衔接

通过。

这份 schema 足够支撑后续 helper 语义升级，尤其是：

- equire_case_access
- equire_snapshot_access
- summary / detail / admin
- doctor owner / assigned access
- qc reviewer access
- auditor summary / read-only
- admin scoped override

换句话说，现在的 helper skeleton 已经有了向真正 ownership policy 过渡的结构基础，不会因为 schema 太薄而卡死。

### 7) 是否建议进入受限 apply

建议进入 **Stage 106D restricted apply approval**。

原因：

- ORM / migration 总体一致
- backward compatibility 设计是稳的
- 没有影响 recommendation / trace / evidence / shadow audit 的边界
- ownership 语义也已经足够支撑后续授权 helper 设计

### 8) 总结

Stage 106 的意义是把 case ownership 从 文档里的 policy 概念推进到可落地的 schema 基座。这版 schema 并不重，但它足够成为后续 RBAC / access helper / audit 的核心依托。

它没有试图一步做完所有权模型，这是好的。先把 ownership 关键字段和 assignment 轨迹立住，后面再继续细化政策，会更稳。

### 合规确认

本轮复审未改代码、未改数据库、未执行 Alembic、未加入 allowlist、未打开 shadow switch、未加载模型、未 	orch.load、未训练、未真实推理、未启用 GPU、未启用 Nginx、未改前端，也没有扫描、复制、移动或猜测任何 .pth/.pt/.onnx/.ckpt/.safetensors 文件。
