# AI协作能力测评协议

Human–AI Collaboration Assessment Protocol，简称 **HAICA Protocol**。当前版本为 **V1.3**，任务包使用 `protocol_version = "1.3"`。

HAICA Protocol 规定任务怎么写、交付物怎么提交、结果怎么评分和保存。

## V1.3 的评分规则

系统默认：作答（Rollout）使用 **DeepSeek V4.1 Flash / low**；判卷使用 **DeepSeek V4.1 Flash / max**。API 模型标识均为 `deepseek-flash`，实际请求等级和模型标识须留档。

**每一个评分子项，单独启动一个 DeepSeek Harness + DeepSeek 判卷会话。** 没有子项的 rubric 自身就是最小评分项；有 components 的 rubric 只负责分组，逐 component 判分，包括零权重前提项。不能在同一会话里一次判完多个子项。

后台评分脚本自动领取最终提交、展开评分计划、启动各项会话、校验结果、重试失败项、计算依赖上限与权重，并保存完整证据。不需要人或另一个调度 Agent 逐次发起判卷。

每次尝试使用新的进程、home 和 session。各项不共享判分结果或上下文；公共原始材料可只读复用。分数由平台按声明的算式汇总。新版本计分项统一用 Agent Judge，文件校验和算分仍由程序完成；历史 Python 判卷规则保留在原版本中。

V1.3 沿用 V1.2 的提交规则：考生在评测结束前可以修改并重新提交，结束时选定每题最后一次成功提交，后台自动评分。缺交和不合规输入按前置规则记录，评分故障不当作考生零分。

当前维护版还支持声明式 `formula/v1`，用于把独立判断按原题的扣分、折扣或基线公式汇总；可选 `measurement` 只提取客观数据，不能替代模型计分。这两项维护更新见当前完整协议；已发布的 V1.3.0 快照保持原样。

## 从哪里开始

- [完整协议](HAICA-Protocol.md)：字段、独立判卷粒度、结果与归档要求。
- [任务示例](examples/service-research/)：报告、数据表和图表，4 个汇总组、16 个独立评分子项。
- [最新发布](https://github.com/tuzengji/HAICA-Protocol/releases/latest)：协议与示例的发布快照。

## 版本维护与历史结果

默认分支展示最新维护内容，已发布标签与附件不覆盖：

- [V1.3](https://github.com/tuzengji/HAICA-Protocol/releases/tag/v1.3.0)
- [V1.2](https://github.com/tuzengji/HAICA-Protocol/releases/tag/v1.2.0)
- [V1.1](https://github.com/tuzengji/HAICA-Protocol/releases/tag/v1.1.0)
- [V1.0](https://github.com/tuzengji/HAICA-Protocol/releases/tag/v1.0.0)

升级框架不自动迁移题包或改写历史成绩。旧产物采用新协议复评时，单独保存源/目标题包及产物哈希、时间、逐项调用与新结果，保留原评分。协议发布、框架代码同步、线上部署和实际复评分开核验。

公开仓库只包含协议与通用示例；真实题库、平台实现和评测数据分别维护。
