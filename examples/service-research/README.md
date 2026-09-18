# HAICA Protocol 多产物任务示例

这个目录是一个符合 [HAICA Protocol V1.0](../../HAICA_Protocol.md)、可以导入平台的示例任务包，演示如何让一道题同时接收报告、数据表和图片，并用确定性检查与模型判卷共同评分。示例数据是为了演示协议而构造的，不代表真实业务。

评分流程如下：评分规则写在 `tests/evaluation.toml`，中控按 rubric 调用判卷器，示例展示了完整的配置关系。

## 文件结构

```text
service-research/
├── instruction.md                         公开题面和交付要求
├── task.toml                              任务规则与产物槽位（平台生成公开字段）
├── README.md                              本说明（不发给考生）
├── environment/
│   ├── requirements.toml                  公开的环境说明
│   └── materials/                         公开输入材料
│       ├── service-usage.csv
│       └── data-dictionary.md
└── tests/                                 私有评分配置和参考资料
    ├── evaluation.toml
    ├── checks/check_metrics.py
    └── references/
        ├── service-usage.csv
        ├── data-dictionary.md
        └── facts.md
```

考生只能看到 `instruction.md` 和 `environment/`。`tests/` 中的规则、检查器和参考资料只在评分端使用。题面和配置中的产物 ID 必须保持一致：`report`、`metrics`、`charts`。

## 题面产生的交付流程

考生从工作空间选择三类产物，确认后一次性提交整道题。选择文件时不复制内容；提交时才校验并冻结实际文件。到时仍未成功提交，系统按未交卷处理，所有产物视为缺交，不自动选取工作空间文件评分。交卷后考生只看到整题总分，管理员可以查看评分明细。

| 产物 | 示例要求 | 评分读取方式 |
| --- | --- | --- |
| `report` | 一份 Markdown、PDF 或 DOCX 报告 | `text` |
| `metrics` | 一份 UTF-8 CSV 指标表 | `cells`、`files` |
| `charts` | 1～3 张 PNG/JPEG 图表 | `image` |

三个交付项分别限制容量：报告最多 10 MiB，指标表最多 1 MiB，每张图最多 4 MiB、图表合计最多 12 MiB。容量只写在各项的 `max_total_bytes` 中；评分读取还受字符数、单元格数和图像字节上限约束。

## 评分配置

`tests/evaluation.toml` 展示四条相互独立的评分标准：

| 标准 | 判卷器 | 权重 |
| --- | --- | ---: |
| 指标计算准确 | Python，从固定数据重新计算 | 40 |
| 分析与建议有据可依 | 文字 Agent Judge | 30 |
| 来源与统计口径清楚 | 文字 Agent Judge | 15 |
| 图表准确且易读 | 视觉 Agent Judge，读取全部图表 | 15 |

`deepseek-text-v1` 和 `deepseek-vision-v1` 是平台注册的逻辑配置名。当前实现通过 DeepSeek Harness 调用官方 `deepseek-flash`，每条 rubric 和每次重试建立独立 Agent Judge 会话，只读本项证据，保存完整判分轨迹；文字配置不接收图像，视觉配置可以接收图像。服务地址、模型版本和凭据由平台管理，密钥不能放进任务包。

`linux-office` 和 `windows-office` 是环境配置名称。工具能力由平台统一提供，任务只声明允许在哪些环境作答；每次分配前，平台确认相应环境已经可用。

每条 rubric 独立调用判卷器，先得到 `raw_score/scale_max`，再由配置中的 `weighted_sum/v1` 聚合为百分制总分。缺少某项产物时，依赖该产物的标准按题面公开规则处理；判卷器故障应保留失败状态，不能伪装成考生零分。

## Python 检查器接口

`tests/checks/check_metrics.py:run(context)` 只接收评分引擎生成的只读上下文。示意结构如下：

```python
context = {
    "inputs": {
        "metrics": {"files": [{
            "path": "/readonly-submission/metrics/answer.csv",
            "relative_path": "answer.csv",
            "sha256": "引擎核验后的文件哈希",
        }]}
    },
    "references": {
        "source-data": "/readonly-task/tests/references/service-usage.csv",
    },
}
result = run(context)
```

这些路径由评分引擎生成，插件不能把用户输入当作服务端路径。引擎负责权限、哈希、格式和容量检查；插件只返回当前 rubric 的结果。`feedback` 和 `evidence` 进入管理员报告，不返回给考生。

## 导入前检查

导入前应验证：TOML 可以解析；公开材料与私有参考资料完整；每个 rubric 引用存在的产物和 view；所有权重合计 100；各项容量上限不超过平台限制；评分脚本不会访问网络或写入题包。先用正确、部分正确、错误和缺交样例试判，再将任务分配给考生。
