## Stage 107R: ownership-aware access helper review

结论：**通过**

本轮复审对象是 ownership-aware 的 case/snapshot access helper。整体实现方向是正确的：helper 仍然很窄，但已经从纯角色门禁推进到 角色 + case ownership/assignment混合判定。它没有把权限系统做重，也没有把 snapshot 做成脱离 case 的自由资源。

### 1) ownership-aware helper 语义是否合理

通过。

当前 helper 的核心顺序是合理的：

1. 先查 case，不存在 -> 404 case_not_found
2. 校验 ccess_level
3. dmin / super_admin 直接允许
4. owner_user_id / primary_doctor_id 命中时允许 summary/detail
5. 如果 case 已经存在 ownership policy / active assignments，则按 case policy 判定
6. 若 case 还没有 ownership policy，则保留 dev/stub fallback role logic

我认为这个顺序是对的，因为它保证了：

- 有正式 ownership 的 case，不再依赖 dev fallback
- 没有正式 ownership 的 case，仍能保持当前 skeleton 流程可用
- helper 不会因为引入 ownership 而一下子把整个开发路径掐断

unknown role deny 也合理。对于已经进入 ownership-aware 路径的 case，未知角色不应默认放行，这样更安全。

### 2) dev fallback 边界是否安全

通过，但要明确它仍然只是过渡态。

当前 fallback 只在 case 没有 ownership policy / active assignments 时触发，这个边界是合理的。它说明：

- production policy 一旦存在，就优先走 ownership / assignment
- dev/stub fallback 只服务于尚未建好 ownership 的旧 case 或测试 case

我认为当前阶段不构成必须修改项。唯一需要注意的是：

- 未来如果要更严格地区分 dev 与 production，可以再加一个环境开关
- 但现在 helper 的 fallback 只是一层过渡逻辑，不算安全漏洞

换句话说，它应该被看作兼容层，而不是最终权限策略。

### 3) role_on_case 权限映射是否合理

通过。

当前映射是：

- owner / primary_doctor / consulting_doctor -> summary/detail
- qc_reviewer -> summary
- uditor -> summary
- dmin_delegate -> summary/detail/admin

我的判断：

- owner / primary_doctor / consulting_doctor 给 summary/detail 是合理的
- uditor summary-only 是合理的
- dmin_delegate 能到 admin 也是合理的，因为它表达的是委托管理角色
- qc_reviewer 当前 summary-only 可以接受

如果后续质量复核流程需要更深入看 payload，再把 qc_reviewer 扩到 detail 也行，但**现在不是必须项**。当前 summary-only 对 skeleton 阶段是保守且安全的。

### 4) snapshot access 继承 case scope 是否正确

通过。


equire_snapshot_access 直接通过 snapshot.case_id 调 
equire_case_access，这是正确的。snapshot 不应该成为脱离病例的自由资源。

同时，trace-based snapshot list 逐条 snapshot 按 case scope 控制，也是合理的。它避免了某个 trace 下的快照被当成全局可读对象的风险。

这和 Stage 103 的设计是完全一致的：

- snapshot 仍然继承 case scope
- detail 仍然比 summary 更严格
- snapshot 不应脱离病例存在于访问语义之外

### 5) 错误码与安全行为

通过。

当前错误码语义是清楚的：

- 401 missing_token
- 403 access_denied
- 404 case_not_found
- 404 input_snapshot_not_found

我认为这组错误语义是合理的，而且足够覆盖主要 deny 分支。

synthetic nurse direct helper test -> 403 access_denied 说明 deny 分支已经被实测到，这很好。它至少证明 helper 不是只会放行，不会拦。

如果后续项目层面希望把 forbidden 语义统一成某个更宽泛的错误码，也可以再统一，但现在不是 blocker。

### 6) 是否建议进入 Stage 108

建议进入 Stage 108，但方向应继续偏安全治理，不建议直接往真实 shadow execution 推。

我推荐的方向是：

**A. access audit schema/design**

原因：

- helper 已经能做 ownership-aware 判定了
- 下一步最值得补的是谁在什么时间以什么模式访问了什么资源的审计语义
- 这比继续扩 shadow audit 或 trace/evidence 更能把治理闭环收住

如果团队更希望先把范围往 shadow audit read APIs 延伸，也可以作为后续路线，但我认为 A 更优先。

### 7) Stage 107 总结

这一版 helper 的价值是把权限控制从纯角色门禁推进到了角色 + ownership/assignment + fallback的混合判定。

它仍然很窄，也仍然保留 dev/stub 兼容性，但已经足够支持后续更细的 ownership 语义演进，不会让 system 一下子变重。

### 合规确认

本轮复审未改代码、未改数据库、未执行 Alembic、未加入 allowlist、未打开 shadow switch、未加载模型、未 	orch.load、未训练、未真实推理、未启用 GPU、未启用 Nginx、未改前端，也没有扫描、复制、移动或猜测任何 .pth/.pt/.onnx/.ckpt/.safetensors 文件。
