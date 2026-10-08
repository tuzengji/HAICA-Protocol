# AI协作能力测评协议

Human–AI Collaboration Assessment Protocol，简称 **HAICA Protocol**。当前版本为 **V1.4**，新任务包使用 `protocol_version = "1.4"`。

HAICA Protocol 规定任务怎么写、交付物怎么提交、结果怎么评分和保存。

## V1.4 的评分规则

**每题从 0 分开始，加分项最高得分合计 100 分，减分项最高扣分不设统一上限。最终得分 = 加分 rubric 得分之和 − 减分 rubric 得分之和，允许负分。** 沿用 `weighted_sum/v1`，在 rubric 上增加 `direction` 标记：`add` 为加分、`deduct` 为减分；省略时默认 `add`。`additive_deductive/v1` 是相同规则的兼容别名。只在最终汇总时按 half-up 保留两位小数，不截断到 0 分，也不另作映射。

核心内容、关键研究点、重要成果适合加分；格式问题、事实错误、逻辑问题、关键数据错误等适合扣分。由人类构造题目的时候来逐条判断 rubric 更适合哪种方式，再选择对应标记。纯加分题可以省略所有方向标记，不必改写原有评分标准或增设扣分项。减分项的原始分越大，扣分越多；其判断标准和档位必须据此编写，平台不会自动取反旧得分。

## 旧题继续测评

框架继续接受 V1.1/V1.2/V1.3 题包。旧版未填写方向的 `weighted_sum/v1` 题目默认按纯加分理解，无需改题面、rubric、判卷器、协议版本或题包文件。已有 `formula/v1` 题包继续按原公式、权重与原版本判卷方式执行；公式中的扣分或门槛不会因升级框架而取消。V1.4 新题不使用公式模式。

任务包和历史结果不自动迁移。主动改评分含义或升级协议时，另建修订并保留源包及历史分数；具体步骤见[完整协议的兼容说明](HAICA-Protocol.md#版本兼容与历史保全)。

## 独立判卷与提交

系统默认：作答（Rollout）使用 **DeepSeek V4.1 Flash / low**；判卷使用 **DeepSeek V4.1 Flash / max**。API 模型标识均为 `deepseek-flash`，实际请求等级和模型标识须留档。

V1.4 沿用 V1.3 的独立判卷：**每一个评分子项，单独启动一个 DeepSeek Harness + DeepSeek 判卷会话。** 没有子项的 rubric 自身就是最小评分项；有 components 的 rubric 只负责分组，逐 component 判分，包括零权重前提项。不能在同一会话里一次判完多个子项；同组 components 继承父 rubric 的方向，需要混合方向时拆为不同 rubric。

后台评分脚本自动领取最终提交、展开评分计划、启动各项会话、校验结果、重试失败项、计算依赖上限与权重，并保存完整证据。不需要人或另一个调度 Agent 逐次发起判卷。

每次尝试使用新的进程、home 和 session。各项不共享判分结果或上下文；公共原始材料可只读复用。分数由平台按声明的算式汇总。V1.4 计分项统一用 Agent Judge，文件校验和算分仍由程序完成；历史 Python 判卷器保留在原版本中，旧题继续测评不要求重写判卷器。

V1.4 沿用 V1.2/V1.3 的提交规则：考生在评测结束前可以修改并重新提交，结束时选定每题最后一次成功提交，后台自动评分。缺交和不合规输入按前置规则记录，评分故障不当作考生零分。可选 `measurement` 只提取客观数据，不能替代模型计分。

## 从哪里开始

- [完整协议](HAICA-Protocol.md)：字段、独立判卷粒度、结果与归档要求。
- [任务示例](examples/service-research/)：报告、数据表和图表，4 个加分组和 1 个减分组、16 个独立评分子项，演示两种方向标记。
- [V1.4 发布](https://github.com/tuzengji/HAICA-Protocol/releases/tag/v1.4.0)：协议与示例的发布快照。

## 版本维护与历史结果

默认分支展示最新维护内容，已发布标签与附件不覆盖：

- [V1.4](https://github.com/tuzengji/HAICA-Protocol/releases/tag/v1.4.0)
- [V1.3](https://github.com/tuzengji/HAICA-Protocol/releases/tag/v1.3.0)
- [V1.2](https://github.com/tuzengji/HAICA-Protocol/releases/tag/v1.2.0)
- [V1.1](https://github.com/tuzengji/HAICA-Protocol/releases/tag/v1.1.0)
- [V1.0](https://github.com/tuzengji/HAICA-Protocol/releases/tag/v1.0.0)

升级框架不自动迁移题包或改写历史成绩。旧产物采用新协议复评时，单独保存源/目标题包及产物哈希、时间、逐项调用与新结果，保留原评分。协议发布、框架代码同步、线上部署和实际复评分开核验。

公开仓库只包含协议与通用示例；真实题库、平台实现和评测数据分别维护。

V1.4维护补充：可选 `score_gate` 保留既有先决要求，由程序在全部独立裁决后执行贡献归零，不向Judge泄露其他裁决，也不修改原裁决。未声明门槛的题包不变；详见协议“得分门槛”。
