# AI协作能力测评协议

Human–AI Collaboration Assessment Protocol，简称 **HAICA Protocol**。当前版本为 **V1.5**，新任务包使用 `protocol_version = "1.5"`。

HAICA Protocol 规定任务怎么写、交付物怎么提交、结果怎么评分和保存。

## V1.5：两层 rubric，同一产物合并判卷

评分只有两层：顶层 `rubric` 和其下可选的子 rubric（`scoring.components`）。**每条顶层 rubric 只对应一个待评产物，由一个 LLM 请求或一个 Agent 会话评完全部子项。** 子项继承同一产物和判卷器，逐项保留档位、理由和证据。

- `kind = "llm"`、`plugin_api = "llm/v1"`：一次请求提供完整输入，直接返回全部子项判定。能够直接阅读冻结文档、表格或图像判断的要求优先使用 LLM。
- `kind = "agent"`、`plugin_api = "agent/v1"`：一个 DeepSeek Harness 会话使用只读工具分步核对证据，返回全部子项判定。

多个视图仍属于同一个产物；原有文件集和目录也按声明的产物 ID 识别。私有参考基准不是额外的待评产物。`scoring.groups` 只是算分权重标签，不增加评分层级或模型调用。

后台脚本自动调度、校验、重试和汇总，不需要另一个 Agent 调度。失败以顶层 rubric 为单位重试，最多三次尝试；不拼接不同尝试、不挑高分，成功项不重跑。子项缺失或评分故障不会被当作零分，最终无法完成时整题总分为 `null`。

## 初始分、加减分与提交规则

**每题有一个初始分 `aggregation.base_score`，省略时默认 0；初始分 + 所有加分项满分必须恰好等于 100。** 初始分须为有限数值，不另设下界；加分满分只累计顶层 rubric 的 `weight`，不重复累计子项。减分项的单项与合计最高扣分均不受 100 分限制，最终可以为负分。例如初始 40 分配 60 分加分项，或初始 100 分只设扣分项，均符合规则。

沿用 `weighted_sum/v1`，有至少一个参与评分的产物通过有效性检查并得到 `evaluated` 结果时，总分为初始分加上带符号的 rubric 贡献；所有评分产物均缺交或无效时总分为 0，未参与评分的可选附件不单独授予初始分。rubric 的 `direction = "add" | "deduct"` 省略时为 `add`；`additive_deductive/v1` 是兼容别名。`weighted_components/v1`、依赖上限、`score_gate` 以及最终 half-up 两位小数算法均不变。部分缺交依然按 `missing_policy` 将依赖项贡献归零；必要评分失败时总分仍为 `null`，不能把服务故障当成无效产物记 0 分。

合并调用不合并、删除或放宽具体要求。迁移任务时保留题面、资料、criterion、档位、方向、权重和门槛，另建修订并验证同一组判定的算术结果一致。脚本继续做准入校验、客观测量和算分，不代替 V1.5 模型判卷。

系统默认作答（Rollout）为 **DeepSeek V4.1 Flash / low + DeepSeek Harness**；两种判卷方式均为 **DeepSeek V4.1 Flash / max**。实际模型标识、请求参数和证据须留档；直接 LLM 不伪造 Harness 轨迹。

考生可在评测结束前修改并重新提交；结束时选定每题最后一次成功提交，后台自动评分。私有评分内容不会进入题面或作答工作空间。

## 从哪里开始

- [完整协议](HAICA-Protocol.md)：字段、两层 rubric、结果与归档要求。
- [通用任务示例](examples/service-research/)：3 个产物、5 条顶层 rubric、16 个子项，演示直接 LLM 与 Agent。
- [V1.5 发布](https://github.com/tuzengji/HAICA-Protocol/releases/tag/v1.5.0)：协议与示例快照。

## 历史保全

V1.1/V1.2/V1.3/V1.4 题包继续按原规则执行；尤其 V1.3/V1.4 仍逐原子项使用独立 Harness 会话，不能用 V1.5 的 `llm/v1` 含义重解释旧包。旧公式和 Python 判卷器按原版本保留。升级框架不自动迁移题包或改写历史分数，新协议复评必须另外保存比较记录。

默认分支展示当前维护内容；[V1.4](https://github.com/tuzengji/HAICA-Protocol/releases/tag/v1.4.0)、[V1.3](https://github.com/tuzengji/HAICA-Protocol/releases/tag/v1.3.0)、[V1.2](https://github.com/tuzengji/HAICA-Protocol/releases/tag/v1.2.0)、[V1.1](https://github.com/tuzengji/HAICA-Protocol/releases/tag/v1.1.0) 和 [V1.0](https://github.com/tuzengji/HAICA-Protocol/releases/tag/v1.0.0) 标签与附件不覆盖。协议发布、框架代码、线上部署、题包迁移和真实模型验证分别核验。

公开仓库只包含协议与通用示例；真实题库、平台实现和评测数据分别维护。
