## Stage 104R: snapshot RBAC helper skeleton review

结论：**通过**

本轮复审对象是 snapshot 的 RBAC helper skeleton。当前实现保持了一个很窄的权限骨架：只按现有角色和 case 存在性做判定，支持 summary / detail / admin 三档，没有引入新的数据库 schema，也没有把完整 ownership 系统一次性做重。这个方向是对的。

### 1) helper 放置与边界

通过。

pp/core/access_control.py 作为通用访问控制 helper 的位置是合理的。它不是把整套权限系统重做一遍，而是提供两个很窄的 helper：

- equire_case_access(db, user, case_id, access_level='summary')
- equire_snapshot_access(db, user, snapshot, mode='summary')

这种放置方式是合适的，因为它让后续 snapshot、shadow audit、eedback、quality review、	race/evidence 都有了可复用的 access gate 雏形。

当前 TODO 也足够清楚：

- case_owner_user_id
- ssigned_doctor_ids
- care_team_ids

这说明 helper 现在仍然只是 skeleton，没有假装自己已经实现了真正的 ownership policy。

### 2) summary / detail / admin 三档

通过。

三档设计是合理的：

- summary：适合 list / queue / overview
- detail：适合 full payload 查看
- dmin：适合管理与审计场景

当前代码里没有额外引入 auditor / service / internal 之类的新角色，这一点我认为是合理的。因为 Stage 104 的目标是先把 snapshot access 的骨架立住，而不是把角色体系一口气扩成完整医院权限模型。

我对当前角色集合的判断是：

- 先用现有角色做 skeleton 是对的
- 不在本阶段硬造新角色也是对的
- 未来如果要细分 auditor / service / internal，可以在 Stage 105+ 再做治理收口

### 3) case access / snapshot access 语义

通过。

当前语义是：

- snapshot 访问通过 snapshot -> case 走 case-scoped access
- 	race 列表里的 snapshot 结果也仍然要按每条 snapshot 对应的 case scope 控制
- skeleton 阶段先校验 case 存在 + 角色是否允许，是可接受的

我认为这条路是对的，因为它至少把访问边界绑在了 case 上，而不是让 snapshot、trace、shadow audit 变成脱离病例的 自由漂浮资源。

	race 相关 list 现在先取 snapshot rows，再按每个 case 做权限校验，这个实现对 skeleton 阶段是可以接受的。后续若要更强，可以再考虑把 case scope 前置或在 query 层做更强过滤，但这不是必须项。

### 4) PHI / privacy 边界

通过。

当前 list 仍然是 summary view，detail 才返回完整 payload，这个分层是符合预期的。对 PHI / provenance 风险的控制思路是正确的：

- list 只给最小摘要
- detail 才给完整 payload
- helper 接上之后，detail payload 的暴露风险是可控的

但我要把边界说清楚：

- mapped_features
- source_refs
- doctor_provided_features

这些字段仍然应该被视作敏感 clinical payload。当前 skeleton 可接受，但后续最好继续补：

- 访问审计
- 必要时字段级脱敏
- 更明确的 purpose / role 边界

### 5) 错误码与安全行为

通过。

当前行为我认为是合理的：

- 未登录：401 missing_token
- missing snapshot：404 input_snapshot_not_found
- missing case：404 case_not_found
- 权限不足：403 access_denied

我建议后续如果要统一项目语义，可以继续沿用 ccess_denied 这类明确语义，不必为了抽象统一而把错误码做得更花。当前阶段最重要的是清楚、稳定、可审计。

### 6) 是否需要在 Stage 105 前补更细 ownership 设计

建议可以暂缓，但不应永久拖延。

当前 helper 只是 role + case existence 的 skeleton，离真正 ownership policy 还有一段距离。TODO 已经指出了未来要补的字段，所以我认为：

- Stage 104 本身是合格的
- Stage 105 之前不一定要马上把完整 ownership schema 做出来
- 但后续最终还是要落到 ownership 概念上，否则 helper 会长期停留在角色门禁而不是资源归属门禁

### 7) 是否建议进入 Stage 105

建议进入 Stage 105。

我推荐的方向是：

**B. case ownership schema design**

理由：

- 当前 helper 已经有 skeleton
- 下一步最缺的是把 ownership 语义从 TODO 变成正式设计对象
- 一旦 ownership schema / policy 语义更清楚，后续 snapshot / shadow audit / trace / evidence / feedback 都更容易统一收口

如果团队希望优先补治理可观测性，那么 A. access audit schema contract 也值得排队，但我会把它放在 ownership 之后更稳。

### 8) Stage 104 总结

这一阶段的价值在于：

- 让 snapshot access 先有了一个窄而清楚的门
- 没有把权限系统做重
- 没有引入新的 schema
- 没有破坏现有 dev_doctor / skeleton 流程

它是一个很好的过渡点：先把 case/snapshot 的访问 helper 站稳，再往 ownership 和审计收口。

### 合规确认

本轮复审未改代码、未改数据库、未执行 Alembic、未加入 allowlist、未打开 shadow switch、未加载模型、未 	orch.load、未训练、未真实推理、未启用 GPU、未启用 Nginx、未改前端，也没有扫描、复制、移动或猜测任何 .pth/.pt/.onnx/.ckpt/.safetensors 文件。
