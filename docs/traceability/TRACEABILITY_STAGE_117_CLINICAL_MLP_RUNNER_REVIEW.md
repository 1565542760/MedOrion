## Stage 117R: clinical MLP fold5 standalone runner review

结论：**通过**

本轮复审对象是 CAP/COP clinical MLP fold5 的 standalone runner。整体判断是：它作为一个短期桥接器是可接受的，边界也比较清楚。它能独立吃 JSON、做输入校验、验证权重 hash、只读加载 preprocess artifact、CPU-only forward、输出 JSON，但没有写 DB、没有写 shadow audit、没有写 recommendation、没有写病例 trace/evidence。作为 runner bridge这一步是合适的，但不应被当成长期架构终点。

### 1) standalone runner 边界

通过。

我认为这个 runner 作为短期桥接是可接受的，理由是：

- 位置放在 pp/model-runners 是合适的
- 运行目录同步到 /srv/medorion/app/model-runners 也合理
- 它的定位很像受控 one-shot bridge，而不是后台长期服务
- 代码本身已经明确表现出不是长期架构：它只是一个 CLI runner，依赖固定 artifact 路径和固定输入契约

所以这一步是可以接受的，但要继续明确它不是最终执行平面。

### 2) 模型文件 / artifact 边界

通过。

这部分边界是对的：

- 只读 exact fold5 文件
- 在 	orch.load 前先做 sha256 校验
- 没有读其它 fold
- 没有扫描目录
- 没有 glob
- 没有复制 / 移动 / 猜测其它权重文件
- preprocess artifact 路径是显式、单一、只读的 JSON 文件

我认为这些做法符合治理要求，尤其是只读 exact artifact + sha256 before load这一点很关键。它不是在模型目录里到处找，而是在一个明确授权路径上做受控加载。

preprocess artifact 路径也可以接受，因为它同样是显式、单一路径，不是目录扫描，也不是隐式猜测。

### 3) 输入契约

通过。

当前输入约束是合理的：

- model_version_id 固定校验合理
- 
ot_for_diagnosis 必须为 	rue 合理
- 36 features 固定顺序合理
- Striated_shadow.1 保留正确
- 缺 feature 直接 input_insufficient 正确

这个 runner 没有试图做帮你补齐输入的聪明默认逻辑，而是明确失败。这样是对的，因为它与前面 Stage 58-60 / 98B-100 / 101-102 的输入治理语义一致：不能硬凑输入，不能把默认值伪装成医生输入。

### 4) 运行安全

通过。

当前安全设置是足够作为短期 shadow bridge 的：

- CPU-only
- CUDA_VISIBLE_DEVICES=''
- map_location='cpu'
- model.eval()
- 	orch.no_grad()
- batch=1
- 线程数限制

我认为这套设置足够保守，至少不会把它偷偷变成 GPU 推理或并发推理平面。

### 5) 输出语义

通过。

当前输出是：

- candidate_label：CAP / COP
- probabilities：CAP / COP
- confidence
- uncertainty
- limitations

这组输出已经足够作为后续 shadow_inference_outputs 的候选来源语义，但**它仍然不是 diagnosis，也不是 recommendation**。

这一点非常重要：

- runner 可以产出模型结果
- 但这些结果在治理上仍然只是候选输出 / shadow bridge output
- 不应被当成正式临床结论
- 也不应被当成 recommendation

当前 limitations 里明确带着 
ot_for_diagnosis、shadow_only、
ot_formal_recommendation，这对边界表达是有帮助的。

### 6) 错误语义

通过。

当前错误语义已经足够覆盖主要失败场景：

- input_insufficient
- 
ot_for_diagnosis_required
- model_version_mismatch
- rtifact_hash_mismatch
- 	orch_load_failed
- inference_failed

这组错误码已经能支撑一个受控 bridge 的常见故障回放。我认为是够用的。

如果后续想再细分，比如把 preprocess artifact 缺失、runtime 不可用、输出形态异常等拆得更细，也可以作为增强项，但不是必须项。

### 7) 是否建议进入 Stage 118

建议进入 Stage 118，但方向应该继续保持只写 shadow audit，不写 recommendation / trace/evidence。

推荐方向：

**A. backend one-shot endpoint calls runner subprocess and writes shadow audit**

理由：

- 现在 runner 已经可以独立跑通
- 下一步最自然的是把它接成一个受控 backend one-shot 调用
- 但必须只写 shadow audit，不写 recommendation / trace/evidence
- 这会把 runner 从手工桥接推向受控执行面，但仍然保留治理边界

我不建议现在直接把它搬进 model-service 作为长期服务，也不建议跳到更广的执行面。

### 8) 总结

Stage 117 的价值是：

- 证明 fold5 runner 可以在受控环境里独立执行
- 证明它有输入校验、hash 验证、CPU-only 推理和输出语义
- 但它仍然不是正式诊断，不是 recommendation
- 也没有进入病例 trace/evidence 或 shadow audit 写入面

它是一个非常典型的短期桥接器：能用，但不应该演变成永久架构。

### 合规确认

本轮复审未改代码、未改数据库、未执行 Alembic、未打开 shadow switch、未加入 allowlist、未训练、未写 recommendation、未写 trace/evidence、未改前端、未读其它 fold、未扫描、复制、移动模型文件。
