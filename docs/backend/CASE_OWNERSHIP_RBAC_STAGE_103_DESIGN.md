# MedOrion Stage 103: Case Ownership / RBAC Hardening Design

## 1. Goals

Stage 103 的目标是把 MedOrion 后续访问边界写清楚，避免 snapshot、shadow audit、feedback、quality review、trace/evidence 等接口默认暴露给所有已登录用户。

本阶段关注的是**访问治理设计**，不是代码实现，也不是数据库建模。它的产出是可供后续 helper / middleware / API enforcement 使用的权限原则和资源访问规则。

核心目标：

- 明确 case ownership 与 patient/case-level access 的治理方向
- 明确 snapshot detail payload 的访问边界
- 明确 doctor / qc / admin / service / auditor 的职责差异
- 明确 provenance / audit 数据的最小必要访问原则
- 为后续 snapshot、shadow audit、trace/evidence、feedback、quality review 的统一授权提供文档依据

---

## 2. Non Goals

Stage 103 不做以下事情：

- 不改代码
- 不改数据库
- 不执行 Alembic
- 不改前端
- 不改变现有 `dev_doctor` 行为
- 不启用真实模型
- 不写 recommendation
- 不写病例 trace / evidence
- 不处理生产 SSO 或医院真实权限系统

本阶段只输出设计，不落库、不上线、不改实现。

---

## 3. Current State

当前状态如下：

- snapshot API 已接 `require_roles`
- 未登录访问返回 `401 missing_token`
- `dev_doctor` 可以访问测试数据
- snapshot list 默认返回 summary
- snapshot detail 才返回完整 payload
- 但目前尚未有完整的 case ownership / patient-level access 规则

这意味着系统已经具备“认证边界”，但还没有“资源归属边界”。

---

## 4. Role Model Draft

Stage 103 建议先抽象出以下角色：

### doctor

面向临床使用者。默认只应访问自己负责或参与的 case，以及与这些 case 直接相关的 provenance、feedback、trace、shadow summary。

### qc

面向质量复核人员。默认可访问与质量审查相关的 case、quality review、feedback、shadow audit summary，以及与审查任务直接关联的 provenance/trace 摘要。

### admin

面向平台管理者。可做管理、审计、排障和最小必要的数据查看，但仍应遵守 case scope 与敏感 payload 最小暴露原则。

### service / internal

面向后端系统服务调用。权限应最小化，通常只允许执行必要的系统间调用，不应默认拥有广泛的临床数据浏览权限。

### auditor / read-only

面向只读审计场景。默认只允许访问必要摘要，必要时可脱敏查看 detail，不应默认获得完整临床 payload。

### future patient-facing role

当前阶段不启用。可作为未来能力预留，但不进入本阶段实现范围。

---

## 5. Ownership Concepts

Stage 103 建议定义以下 ownership / scope 概念：

- `case_owner_user_id`
- `assigned_doctor_ids`
- `care_team_ids`
- `qc_reviewer_ids`
- `organization_scope`
- `tenant_scope`
- `break_glass_access` / emergency access

说明：

- 上述概念是未来 policy 设计对象
- 如果当前 schema 还没有这些字段，也不应在本阶段强行落库
- `break_glass_access` 应明确作为未来能力，不作为本阶段默认路径

当前骨架阶段可以先把这些概念写进设计文档，为后续 helper / middleware 提供语义锚点。

---

## 6. Access Rules By Resource

以下访问规则是 Stage 103 的建议治理草案。

### patients

- doctor：仅限自己负责/参与的患者
- qc：限质量复核所需患者
- admin：可按组织/租户范围查看
- service/internal：仅系统所需最小访问
- auditor：尽量只看脱敏或摘要

### cases

- doctor：仅限自己负责/参与的 case
- qc：仅限复核范围内的 case
- admin：组织/租户范围内的 case
- service/internal：最小权限
- auditor：只读摘要优先

### recommendations

- 与 case 绑定，按 case scope 访问
- doctor 可看自己 case 的 recommendation
- qc 可看复核 case 的 recommendation
- admin 可看审计所需 recommendation
- auditor 默认只看摘要

### traces

- 必须 case-scoped
- doctor / qc / admin 均应通过 case scope 判断
- trace 不应作为脱离 case 的公开资源

### evidence_nodes / evidence_edges

- 必须 case-scoped
- 仅在对应 case 的授权范围内可访问
- 原始 evidence 可能包含临床敏感信息，应尽量优先摘要/可控 detail

### doctor_feedback

- 按 case scope / doctor scope 访问
- doctor 可创建与查看自己相关反馈
- qc 可看复核范围内 feedback
- admin 可做审计查看

### quality_reviews

- qc 优先
- doctor 可看与自己 case 相关的 review 摘要或详情，视策略而定
- admin 可查看审计所需内容

### model_input_snapshots

**重点：snapshot detail payload 需要比 summary 更严格。**

- summary 可在 case scope 下做最小暴露
- detail/full payload 需要更强权限
- raw `mapped_features` / `source_refs` / `doctor_provided_features` 应视作敏感 clinical payload

### shadow_inference_runs / outputs

- 默认不是正式临床结论
- 应按 case scope 访问
- summary 优先，detail 更严格
- 不能默认广泛暴露给所有登录用户

### orchestration_runs / steps / invocations

- 这类资源属于 orchestration audit
- 默认与病例审计分离，但仍应遵循 case scope / task scope / role scope
- 对普通 doctor 不应默认开放过多内部路由细节

### model_registry / model_versions

- registry metadata 可以较宽，但仍应受认证和角色约束
- artifact / provenance detail 要谨慎
- 真实 artifact 相关信息不应默认给所有角色

---

## 7. Summary vs Detail Access

建议将访问策略分成 summary 和 detail 两层：

### summary/list

- 默认可较宽，但仍需 case scope
- 适合列表页、队列页、复核页
- 只返回 counts、状态、时间戳、最少标识符

### detail/full payload

- 需要更强权限
- 应限制在 case scope + role scope + purpose scope 内
- 原始临床 payload 只能给有明确需要的角色

### 对 snapshot 的特别要求

`mapped_features`、`source_refs`、`doctor_provided_features` 应视作敏感 clinical payload。  
前端默认不应展开 full payload，除非用户已经通过 detail 授权。

---

## 8. PHI / Sensitive Data Handling

建议采用最小必要原则：

- 列表页不暴露完整临床 payload
- detail 访问必须可审计
- 后续可考虑字段级脱敏
- `source_refs` 可能包含 EMR / lab / observation 引用，不应默认外泄
- `mapped_features` 也可能携带敏感临床状态或组合特征，需要视为受保护 provenance

这不是说这些数据不能存，而是说它们不应被当作普通列表数据或公开接口数据来处理。

---

## 9. Audit Logging Recommendation

建议未来增加访问审计，但本阶段不建表。

建议记录：

- who accessed
- what resource
- `case_id` / `patient_id`
- access mode (`summary` / `detail` / `admin`)
- purpose
- timestamp

这类审计记录后续可用于：

- 安全追踪
- 合规检查
- 数据泄露排查
- 敏感 payload 访问回溯

---

## 10. API Enforcement Plan

建议后续用 helper / middleware 统一执行访问边界：

- `require_case_access(user, case_id, access_level)`
- `require_snapshot_access(user, snapshot, mode=summary/detail)`
- `require_shadow_audit_access(user, case_id, mode=summary/detail)`

建议的 `mode` 值：

- `summary`
- `detail`
- `admin`

实施顺序建议：

1. 先在 snapshot 上试点
2. 再扩到 shadow audit
3. 再扩到 trace / evidence

这样可以避免一口气把所有 provenance/audit 接口都改得过重。

---

## 11. Backward Compatibility

Stage 103 必须保留 dev/stub 阶段的可用性：

- `dev_doctor` 在 dev 环境仍可访问测试 case
- production 模式必须收紧 ownership
- 不破坏现有 MVP skeleton 流程

建议做法是：

- 开发环境保留较宽松的测试访问
- 生产环境收紧到 case ownership / role scope / tenant scope

这样既不伤开发效率，也不让治理规则在真实环境中失控。

---

## 12. Stage 104 Recommendation

建议 Stage 104 的优先方向是：

**A. RBAC helper skeleton for case/snapshot access**

原因：

- 当前最需要的不是前端页面，而是统一的授权 helper
- 先把 case/snapshot 的 access level 定义好，后面 trace/evidence、shadow audit、feedback、quality review 都能复用
- 这是最能降低后续治理分叉风险的一步

可作为后续顺序：

1. Stage 104：RBAC helper skeleton
2. Stage 105：access audit schema contract（如需要）
3. Stage 106：frontend safe-detail UX

---

## Summary

Stage 103 的定位是把 MedOrion 的访问治理从“已登录可用”推进到“按 case / role / purpose 收口”。

它不改变现有 MVP skeleton 的功能，但为后续 snapshot、shadow audit、feedback、quality review、trace/evidence、model registry 的访问规则提供统一语义。

如果后续要继续往前推进，最值得先做的是 case/snapshot access helper，而不是直接扩大 UI 或 shadow execution 面。
