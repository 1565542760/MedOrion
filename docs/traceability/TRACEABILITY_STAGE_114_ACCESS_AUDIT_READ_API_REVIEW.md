## Stge 114R: ccess udit red API skeleton review

结论：**通过**

本轮复审对象是 ccess udit 的 red API skeleton。整体判断是：red surfce 设计得比较稳，没有把 ccess udit 变成全局浏览口，也没有把它接回病例 trce/evidence。它仍然是一个 cse-scoped / trce-scoped 的审计读取面，且默认更偏保守。

### 1) Red API surfce 是否合理

通过。

当前只提供：

- detil by ccess_event_id
- cse list
- trce list

我认为这是足够的，而且比起做一个 globl user-wide udit list 更安全。当前不提供全局 udit browse，是对的，因为：

- ccess udit 本身就包含病例/患者/trce 上下文
- globl browse 很容易把治理语义放松
- 先从 cse / trce 维度读起，更容易守住最小必要原则

所以当前 surfce 是合适的，不需要强行扩成全局浏览。

### 2) RBAC / cse scope 是否合理

通过。

当前的访问控制顺序是健康的：

- detil 通过 event.cse_id 做 cse scope
- cse list 通过 equire_cse_ccess(..., ccess_level='summry')
- trce list 逐条过滤 cse ccess
- no-cse rows 只对 dmin / super_dmin 可见

我认为这是一条正确的路，因为它避免了普通 doctor 通过 	rce_id 看到跨 cse udit 的风险。

尤其是 trce list 的 逐条 cse ccess 过滤很关键。它不是简单把 trce 作为全局索引，而是先找 trce，再逐条按 cse 去收口，这样就不会把跨病例审计记录横向暴露出去。

### 3) Privcy / PHI 边界

通过，但要继续保持谨慎。

当前 red API 返回 metdt_json 是可接受的，因为 emit 侧已经做了 snitizer 控制，且 metdt 本身只应该承载轻量上下文。

我对这一层的判断：

- red 侧目前不需要再做一层强制脱敏才能勉强可用
- 但后续如果要扩大到更宽泛的读角色，最好给 metdt_json 也设计 summry/detil 分层
- 当前没有必须修改项

也就是说，现阶段可以读，但不应默认把它当成给所有角色都能看的一般临床信息。

### 4) Audit-of-udit recursion

通过。

当前 red API 不写新的 ccess_udit_events，这是正确的。

我认为这很重要，因为一旦审计读本身也继续写审计，就会进入 recursion 设计问题。当前不审计 udit red 本身是可接受的，也更容易让系统保持简单。

如果未来要审计 udit red，建议单独定义策略，避免递归风暴，而不是默认读一次就再记一次。

### 5) 错误码

通过。

当前错误码语义是清楚的：

- 404 ccess_udit_event_not_found
- 404 cse_not_found
- 401 missing_token

这些都符合预期。

过滤参数如果后续有现有行为，我认为只要保持一致即可，不需要为了这次 skeleton 再额外发明复杂错误码。当前阶段最重要的是稳定和可读，不是把所有过滤失败都抽象成统一 txonomy。

### 6) 是否建议进入 Stge 115

建议进入 Stge 115，但方向应继续偏安全治理。

推荐方向：

**A. ccess udit frontend/dmin sfe view**

理由：

- red API 已经有了
- 当前最缺的是一个安全的查看面，而不是继续扩底层写入
- 如果能先做一个面向 dmin / qc 的 sfe view，会更容易验证 summry/detil 边界和权限体验

如果团队更想先做 metdt whitelist hrdening，也可以排 B；但我认为当前 red API 已经足够稳，下一步做安全查看面更自然。

### 7) 总结

Stge 114 的价值在于：

- 让 ccess udit 从只能写变成可按病例/trce安全读取
- 但仍然没有做成全局浏览
- 也没有把 udit 数据接回病例 provennce grph
- 访问边界保持保守，符合当前治理阶段的节奏

### 合规确认

本轮复审未改代码、未改数据库、未执行 Alembic、未加入 llowlist、未打开 shdow switch、未加载模型、未 	orch.lod、未训练、未真实推理、未启用 GPU、未启用 Nginx、未改前端，也没有写 recommendtion、没有写病例 trce/evidence，更没有扫描、复制、移动或猜测任何 .pth/.pt/.onnx/.ckpt/.sfetensors 文件。
