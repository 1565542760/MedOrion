## Stage 121R: clinical MLP shadow result frontend safety review

结论：**通过**

本轮复审对象是 /cases/[caseId]/shadow-audit 上的 clinical MLP CAP/COP shadow result 前端展示。整体判断是：这页的设计边界是健康的。它只读展示 shadow result，没有运行按钮，没有写后端数据，也没有把 shadow result 伪装成 diagnosis 或 formal recommendation。只要当前警示文案保持醒目，这个前端面是可接受的。

### 1) 是否发现必须修改项

没有必须修改项。

### 2) 是否存在把 shadow result 误读成 diagnosis / recommendation 的风险

有风险，但目前被控制住了，而且是可接受的。

原因是：

- 页面明确是 shadow-audit
- 没有运行按钮
- 有明显的安全警示
- 展示内容是 shadow result 的审计信息，而不是正式临床结论

我认为这类风险在任何 shadow result 页面上都存在，关键在于文案和交互是不是持续把它压住。现在的设计已经在正确方向上了。

### 3) 警示文案是否足够醒目、克制、医生可理解

通过。

当前警示包括：

- Shadow only
- Not for diagnosis
- Not a formal recommendation
- Requires doctor review
- Requires quality review before clinical use
- 概率未校准
- 极端概率不等于临床确定性
- 未经过外部验证
- 仅供 shadow 审计和医生复核参考

这组文案我认为是合适的，语气也比较克制，不会过度制造恐慌，但足够清楚地提醒医生：这不是临床结论。

### 4) raw logits 折叠展示是否合理

通过。

折叠展示 raw logits 是合理的：

- 默认不打扰主视图
- 但对审计和技术复核保留细节
- 便于在需要时查看校准、极端概率和输出分布

我认为这是一个比较平衡的选择。对医生来说，默认先看摘要更好；对质量复核或技术回放来说，raw logits 可以在需要时展开。

### 5) candidate_label / probabilities / confidence 是否需要更弱化展示

建议**适度弱化**，但不是必须修改项。

我的判断是：

- 这几个字段保留是对的
- 但展示层可以继续把它们放在 shadow output summary语境里，而不是诊断结论语境里
- 如果前端样式上有能力，建议在视觉层级上让警示文案更高于概率数值本身

也就是说，不需要删除这些字段，但建议它们不要成为页面上最强的视觉主角。

### 6) 空态 / 错误态是否安全

通过。

从你给出的验证结果看：

- route 可用
- 参数化访问可用
- 其他页面也正常返回

这说明当前页面至少在基础路径上是稳定的。只要空态和错误态继续沿用这是 shadow 审计，不是诊断的文案风格，我认为是安全的。

### 7) 没有运行按钮是否正确

正确。

这一点我认为非常关键。既然这是 shadow result 只读页，就不应该在页面里塞运行按钮。否则会把查看结果和发起执行混到一起，语义会立刻变糊。

当前没有运行按钮，是合适的，也是应该坚持的。

### 8) 是否建议进入下一阶段

建议进入下一阶段，但我不建议立刻扩到 imaging 或 multimodal。

推荐方向：

**C. clinical MLP shadow result UX polish**

理由：

- 当前 clinical MLP shadow UI 已经能安全展示
- 还有一些可读性和层级上的小细节可以继续优化
- 这比马上横向扩到 imaging / multimodal 更稳

如果团队希望在这个点上停一下并标记clinical MLP shadow path usable，那也是可以的；但从产品体验角度，我会优先建议做一点 UX polish 再收口。

### 9) 总结

Stage 121 的价值是：

- 把 clinical MLP shadow result 做成了可读的前端页面
- 页面是只读的，没有把 shadow 结果伪装成 diagnosis
- 安全警示、raw logits、无运行按钮这几个关键点都处理得对
- 当前更像是一个可用的 shadow review view，而不是临床结论页

### 合规确认

本轮复审未改代码、未改数据库、未执行 Alembic、未触发模型运行、未写 shadow audit、未写 recommendation、未写 trace/evidence、未启用 Nginx、未训练、未读模型文件，也没有扫描、复制、移动任何模型文件。
