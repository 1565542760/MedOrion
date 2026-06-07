## Stage 122R: clinical MLP shadow result UX polish review

结论：**通过**

本轮复审对象是 /cases/[caseId]/shadow-audit 上 clinical MLP shadow result 的 UX polish。整体判断是：这一步把页面进一步往 审计结果页方向推了，而且没有把它做得更像临床结论卡片。顶部强警示、候选标签弱化、概率/置信度降权、raw logits 默认收起，这些都属于正确的安全 UX 方向。

### 1) 是否发现必须修改项

没有必须修改项。

### 2) 是否仍有误读成 diagnosis / recommendation 的风险

有残余风险，但当前已经控制得比较好，且可接受。

原因是：

- 页面仍然是 shadow-audit
- 没有运行按钮
- 强警示在顶部
- 候选标签已经改成更弱的表述
- 概率 / 置信度的视觉权重降低
- raw logits 默认折叠

所以它不会轻易被误读成 diagnosis 或 recommendation。任何 shadow result 页面都不可能把误读风险降到零，但当前版本已经足够克制。

### 3) 安全警示是否足够醒目

通过。

当前安全警示包括：

- Shadow only
- Not for diagnosis
- Not a formal recommendation
- Probability is uncalibrated
- Extreme probability is not clinical certainty
- Not externally validated
- Requires doctor review
- Requires quality review before clinical use

这组提示足够醒目，也足够医生可理解。我认为把它放在顶部是正确的，能在视觉上先把语义钉住。

### 4) candidate_label 视觉是否足够克制

通过。

candidate_label 改成 Shadow candidate label / 模型旁路候选标签 这一方向是对的。它比直接写成某种诊断结果要克制得多。

我认为这一步的关键不是把字段删掉，而是把它从结论感里抽离出来。当前做到了这一点。

### 5) probabilities / confidence 是否仍过于突出

相对之前已经好多了，但仍建议保持克制。

我的判断：

- 现在它们已经没有那么主角化了
- 但概率和置信度本质上仍是很强的视觉信号
- 所以最好继续让警示文案压住它们，而不是让概率图表压过警示

因此：

- 当前不是必须修改项
- 但后续展示层如果还能再弱化一点，会更稳

### 6) raw logits 折叠展示是否合理

通过。

默认收起 raw logits 是正确的。它满足两个目的：

- 普通查看者不会被过多技术细节干扰
- 审计/复核人员仍然能展开看细节

这个交互很符合 shadow result 页的定位。

### 7) 空态 / 错误态是否安全

通过。

你给出的验证结果显示：

- 页面路由可用
- 参数化 shadow_run_id 也可用
- 其他页面也正常

这说明基础访问路径稳定。只要空态/错误态继续沿用 shadow 审计语境，我认为是安全的。

### 8) 没有运行按钮是否正确

正确，而且应该继续坚持。

这类页面最容易犯的错，就是把看结果和发起执行混在一起。当前没有运行按钮，这一点是对的。

### 9) 是否可以把 clinical MLP CAP/COP shadow path 标记为 usable shadow baseline

可以。

我的判断是：现在这条 clinical MLP CAP/COP shadow path 已经可以标记为 **usable shadow baseline**。理由是：

- one-shot bridge 已跑通
- 输出 metadata 已经硬化
- UI 也已经做成了安全的审计视图
- 没有写 recommendation
- 没有写病例 trace/evidence
- 没有把 shadow 伪装成 diagnosis

所以这条路径已经具备可用、可审、可复核的基础定义。

### 10) 是否建议进入下一阶段

建议进入下一阶段，优先方向选：

**A. Stage 123 status/release doc: clinical MLP shadow usable baseline**

理由：

- 现在最需要的是阶段收口和状态明确化
- 先把这条路径定成 usable shadow baseline，会比继续写更多 UX 细节更稳
- 之后如果还要做别的模型族，可以在这个基线之上平移，而不是继续加深这条链

如果后续要继续做体验打磨，可以把 **D. clinical MLP further UX polish** 作为次选，但我认为现在优先级低于 status/release doc。

### 11) 总结

Stage 122 的价值是：

- 把 clinical MLP shadow result 页进一步做成审计导向
- 候选标签、概率、置信度都被更克制地展示
- raw logits 默认收起
- 没有运行按钮
- 页面整体更像 shadow audit，而不是临床结论页

这一步是对的，也足够支持usable shadow baseline的阶段结论。

### 合规确认

本轮复审未改代码、未改数据库、未执行 Alembic、未触发模型运行、未写 shadow audit、未写 recommendation、未写 trace/evidence、未启用 Nginx、未训练、未读模型文件，也没有扫描、复制、移动任何模型文件。
