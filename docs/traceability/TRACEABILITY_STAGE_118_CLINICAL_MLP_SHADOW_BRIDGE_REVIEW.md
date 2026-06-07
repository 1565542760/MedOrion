## Stage 118R: clinical MLP one-shot shadow bridge review

结论：**通过**

本轮复审对象是 clinical MLP fold5 的 one-shot shadow bridge。整体判断是：这一步可以作为短期 bridge 接受，且边界还算清楚。backend 通过 subprocess 调 runner，使用固定 36-feature schema 顺序，运行在 CPU-only / no_grad / eval / batch=1 / concurrency=1 的受控条件下，并把结果写入 shadow audit output。它仍然不是 diagnosis，也不是 formal recommendation；它仍然只应被看作 shadow / assistant / not_for_diagnosis 的桥接执行面。

### 1) shadow bridge 边界

通过。

当前做法是：

- backend one-shot endpoint 通过 subprocess 调 MRI3D runner
- backend 发送 CAP/COP 36 features，且是固定 schema 顺序
- runner/backend 继续保持 
ot_for_diagnosis=true
- CPU-only
- 
o_grad
- eval
- batch=1
- concurrency=1
- backend 容器对 MRI3D env / models / runner path 使用只读挂载

我认为这个边界是可接受的，尤其作为短期 bridge 来说很合理。它比把 torch 直接塞进 backend image 更克制，也比把这一层做成长期服务更保守。

但我也要明确说：这仍然不是长期架构。后续应该回到 model-service / inference-service 方向，而不是继续让 backend 长期承担 subprocess bridge 责任。

### 2) clinical safety wording

通过。

当前仍然只能叫：

- shadow
- assistant
- not_for_diagnosis

不能叫 diagnosis，不能写 formal recommendation，不能进 default/canary。当前写 shadow audit output 是可接受的，因为它的定位仍然是审计化的 shadow 结果，而不是正式临床结论。

我认为现有的边界描述是够清楚的，前提是前端和文档也继续保持这种措辞，不要把它包装成正式诊断。

### 3) output 语义 / calibration 风险

通过，但建议后续做校准与限制语义增强。

当前 one-shot success 的极端输出：

- probabilities = {CAP: 0.0, COP: 1.0}
- confidence = 1.0

这在展示上是很 硬的结果，容易让人误读成模型已经被临床验证为绝对确定。所以我认为：

- 这不构成必须修改项
- 但需要在 UI / audit / limitations 中明确标注 calibration / validation limitation

我建议后续增强以下信息：

- raw logits
- softmax temperature note（如果未来有）
- calibration warning
- low evidence / internal validation warning
- not externally validated

从当前代码看，runner 已经输出了 logits、confidence、uncertainty、limitations，这很好；但仍建议在后续的展示或审计说明里补一句极端概率不等于临床诊断确定性。

### 4) input / snapshot provenance

通过。

当前输入 provenance 是正确的：

- 使用 case_model_input_snapshot 作为输入引用是对的
- 不写 	race/evidence 是对的
- 不修改 snapshot 是对的
- 36 features fixed order 继续保持是对的
- Striated_shadow.1 保留正确

这一步说明 snapshot 作为输入 provenance 已经能接到 one-shot bridge 上了，但它仍然只是输入，不是输出，也不是病例证据。

### 5) access audit / shadow audit 分界

通过。

这次 one-shot 本身写 shadow_inference_runs / shadow_inference_outputs 是正确的，不新增 	race/evidence 也是正确的。

关于 ccess_audit_events 增加到 6，我认为这是可接受的。它更像是 snapshot read / related API 行为带来的访问审计痕迹，而不是病例图污染。只要 access audit 仍然不记录 clinical payload，这个增长就是合理的。

### 6) deployment / runtime risk

通过。

当前 deployment 方案我认为是可接受的短期桥接：

- backend container 对 MRI3D env / model path / runner path 使用只读挂载
- subprocess bridge 不需要把 torch 打进 backend image
- env isolation 和超时控制是有的

但同样要强调：这是短期桥接，不是长期运行面。后续长期方向仍然应该迁回 model-service / inference-service，这样边界会更清楚。

### 7) 是否建议进入 Stage 119

建议进入 Stage 119，但我建议优先方向是：

**A. Stage 118B hardening: calibration/limitations/output metadata polish**

理由：

- 当前 bridge 已经能跑通
- 下一步最值得补的是把输出的校准、限制和审计说明写得更稳
- 这比立刻做前端展示或扩更大模型族更安全

如果团队之后要做前端 safe view，我认为可以排在 Stage 119 的后半或下一步，但我不会先把重心放到 C。当前最需要的是把 shadow output 的语义边界再钉牢一点。

### 8) 总结

Stage 118 的价值在于：

- 临床 MLP fold5 的 one-shot shadow bridge 已经跑通
- 仍然保持了 not_for_diagnosis、CPU-only、no_grad、eval、batch=1、concurrency=1
- 结果写入 shadow audit output，而不是 recommendation / trace / evidence
- 但它仍然应该被看作短期 bridge，而不是长期架构终点

### 合规确认

本轮复审未改代码、未改数据库、未执行 Alembic、未打开 shadow switch、未加入 allowlist、未训练、未写 recommendation、未写 trace/evidence、未改前端、未读其它 folds，也没有扫描、复制、移动模型文件。
