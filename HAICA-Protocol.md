# AI协作能力测评协议

Human–AI Collaboration Assessment Protocol，简称 **HAICA Protocol**。

当前版本：**V1.1**。任务包的 `protocol_version` 写作字符串 `"1.1"`。

HAICA Protocol 约定一道题要放哪些文件，以及平台怎样展示题面、接收交付物、判分和留档。出题者按这个格式打包，平台就能自动生成作答和评分流程。

协议规定输入、输出和权限边界。页面样式、云厂商、模型厂商和服务器实现由平台决定。`protocol_version` 标识任务包格式；`task_revision` 和 `source_revision` 用于识别题目内容和绑定记录。结果包、归档和判卷接口各自使用独立的格式标识，例如 `task-result/v1`、`assessment-archive/v1`、`python/v1` 和 `llm/v1`。

## 1. 任务包结构

### 完整结构：必选与可选文件

```text
my-task/
├── instruction.md                 # 必选：考生看到的题面和交付要求
├── task.toml                      # 必选：任务规则、产物槽位和环境要求
├── README.md                      # 可选：给任务维护者的说明，不发给考生
├── environment/                   # 可选：考生可以读取的公开材料
│   ├── requirements.toml          # 可选：公开环境说明，不放密钥
│   └── materials/                 # 可选：数据、参考文档、图片等
├── tests/                         # 必选：私有评分计划
│   ├── evaluation.toml            # 必选：判卷器、rubrics 和汇总规则
│   ├── checks/                    # 可选：Python 检查器
│   ├── references/                # 可选：私有基准、事实和参考答案
│   └── ...                         # 可选：其他只读评分资料
├── solution/                      # 可选：私有参考解，不发给考生
└── fixtures/                      # 可选：评分所需的固定夹具
```

### 最小结构：只包含必选文件

```text
my-task/
├── instruction.md                 # 题面、交付物和作答规则
├── task.toml                      # 机器可读任务配置
└── tests/
    └── evaluation.toml            # 至少一条 rubric 和一个判卷器
```

最小结构仍必须在 `task.toml` 中声明至少一个产物槽位，并在 `evaluation.toml` 中声明可执行的 `weighted_sum/v1` 评分计划（至少一条 rubric 和一个判卷器）。这个最小目录适用于仅使用平台 Agent Judge 的任务。采用 Python 判卷时，必须再提供所声明的 `tests/checks/*.py`；引用材料或参考资料时，也必须提供相应文件。

### 可见范围

| 文件 | 考生 | 评分端 | 说明 |
| --- | --- | --- | --- |
| `instruction.md` | 可见 | 可见 | 公开题面 |
| `environment/` | 可见 | 可见 | 公开材料和工具使用说明 |
| `task.toml` | 只看到其中的公开字段 | 可见 | 平台从中生成交付控件 |
| `tests/`、`solution/`、`fixtures/` | 不可见 | 可见 | 私有评分规则和参考资料 |
| `README.md` | 不发布 | 可见 | 维护说明 |

考生只能看到题面和公开材料。私有规则、参考事实、模型配置、权重、评分证据和内部错误都不能从题面、工作空间或提交接口泄露。

## 2. 题面与机器配置

所有 TOML 和 Markdown 使用 UTF-8。下面各表写明字段的类型、是否必填、允许值和用途。没有列出的字段会被拒绝，不会被悄悄忽略；布尔值写 `true` 或 `false`，不能写成带引号的文字。题包内的相对路径最多 1,024 个 UTF-8 字节、32 层，每个路径段最多 255 个 UTF-8 字节；不能越出题包。自定义描述放在第 9 节的 `extensions` 中。

### `instruction.md`

题面至少说清楚：

1. 要解决的问题、背景和可用材料；
2. 每个产物的 ID、用途、文件格式、数量和大小要求；
3. 必须满足的公开内容要求、数据口径与引用要求；
4. 一次性交卷，以及未交卷到时的处理；
5. 允许使用的工具和禁止的行为。

作答时限由平台读取 `task.toml` 中的 `assessment.duration_minutes`，在作答前显示给考生，题面不必重复。题面若注明时限，必须与该字段一致。

题面不能写私有 rubric 权重、参考答案或模型提示。产物要求以 `task.toml` 为准，导入者应检查题面与配置一致。例如：

```markdown
# 服务预约分析

阅读 environment/materials/ 中的数据，解释预约变化并提出建议。

## 交付物

- report：一份分析报告，Markdown 或 PDF，不超过 10 MiB。
- data：一份 CSV 指标表，列出计算结果和口径。

从工作空间为各交付项选择文件，确认内容后一次性提交整道题。
到时仍未成功提交的题目按未交卷处理；工作空间中的文件不会自动纳入评分。
提交后不能修改这次交付物。考生可查看整题总分，不显示逐条评分明细。
```

### `task.toml`

下面先写任务基本信息；第 3 节的 `[[assessment.artifacts]]` 至少添加一项后，才是完整配置。

```toml
[task]
name = "example/service-research"
description = "根据给定数据完成分析并交付报告。"

[assessment]
protocol_version = "1.1"
task_revision = "research-001"
title = "服务预约分析"
language = "zh-CN"
difficulity = "medium"
birthday = "2026-09-18T10:00:00+08:00"
duration_minutes = 60
evaluation = "tests/evaluation.toml"

[assessment.workspace]
scope = "shared_per_user"
compatible_profiles = ["linux-office"]
```

`[task]` 的字段：

| 字段 | 类型 / 必填 | 具体含义 |
| --- | --- | --- |
| `name` | 字符串 / 必填 | 任务身份，写成 `组织名/任务名`，例如 `example/service-research`。两部分都用小写字母、数字和单个连字符连接，各不超过 80 字符。平台使用斜杠后的名称作为任务 slug；同一平台不能发布后半部分相同、组织名不同的两个任务。 |
| `description` | 字符串 / 可选 | 给任务维护者和题库列表看的简述，1–10,000 字符。省略时由平台生成摘要。它不代替题面。 |

`[assessment]` 的字段：

| 字段 | 类型 / 必填 | 具体含义 |
| --- | --- | --- |
| `protocol_version` | 字符串 / 必填 | 整个任务包采用的格式版本，当前固定为 `"1.1"`。环境说明沿用这个版本。 |
| `task_revision` | 字符串 / 必填 | 出题者给这份题目内容标记的修订号，例如 `research-001`，1–256 字符。它帮助人识别题目；平台另外计算整个题包的 SHA-256，实际评分绑定题包哈希。 |
| `title` | 字符串 / 必填 | 显示给考生的题目名称，1–256 字符。 |
| `language` | 字符串 / 必填 | 题面的主要语言标签，1–256 字符。建议使用 `zh-CN`、`en` 等语言代码；不会自动翻译内容。 |
| `difficulity` | 字符串 / 必填 | 题目难度，只能为 `low`、`medium`、`high`、`xhigh`、`max`，依次表示简单、一般、困难、很难、极难。字段拼写就是 `difficulity`。这是出题者的难度标注，不改变时间、权重或评分公式。 |
| `birthday` | 字符串 / 必填 | 出题者确认题面、材料和评分规则正式构造完成的时间；不是上传时间或考生作答时间。写带引号的 RFC3339 日期时间，必须有秒和明确时区，例如 `"2026-09-18T10:00:00+08:00"` 或 `"2026-09-18T02:00:00Z"`。可带 1–6 位小数秒，时分秒必须是普通有效时间（不接受闰秒），`T` 和 `Z` 大写；不接受只有日期、无时区、未知时区 `-00:00` 或未加引号的 TOML 日期值。 |
| `duration_minutes` | 整数 / 必填 | 本题可用的作答分钟数，范围 1–1,440。平台读取此字段，在作答前展示时限，题面不必重复。云工作空间仅累计在线作答时间，退出或心跳失效后暂停；独立 Windows 平台按连续时间计时。实际计时方式记录在本次评测的环境条件中。 |
| `evaluation` | 字符串 / 必填 | 私有评分计划的题包内相对路径，必须指向 `tests/` 内真实文件，通常为 `tests/evaluation.toml`。 |
| `workspace` | 配置表 / 必填 | 本题支持的工作空间配置，见下表。 |
| `artifacts` | 配置表数组 / 必填 | 1–30 个交付项，用 `[[assessment.artifacts]]` 逐项声明，详见第 3 节。 |
| `extensions` | 配置表 / 可选 | 带组织命名空间的描述元数据，详见第 9 节；不改变提交、判分或权限。 |

`[assessment.workspace]` 的字段：

| 字段 | 类型 / 必填 | 具体含义 |
| --- | --- | --- |
| `scope` | 字符串 / 必填 | 固定为 `shared_per_user`。同一用户在同一轮评测中的多道题共享一个工作空间；下一轮使用独立工作空间。 |
| `compatible_profiles` | 字符串数组 / 必填 | 至少一个且不重复。当前支持 `linux-office`、`windows-office`，表示任务允许在哪种平台环境作答。Python、办公工具、字体等能力由平台统一配置；出题者不需要逐项声明。平台只能把题目分配到已经部署并验证可用的环境。 |

平台固定执行以下规则，不由题包开关控制：整题一次性提交，成功后关闭这次作答；到时未成功提交则按未交卷处理；采集受控 Agent 的全部可获取轨迹；当前总分只评最终产物。考生作答前只看到题面和交付要求，作答后只看到整题总分和公开状态。重做必须由管理员建立新作答。

可选 `[platform]` 只用于导入时选择题库，不参与评分：

```toml
[platform]
set_slug = "general-capability"
set_title = "AI通用能力测试"
summary = "在工作空间使用 Agent 完成任务。"
```

| 字段 | 类型 / 必填 | 具体含义 |
| --- | --- | --- |
| `set_slug` | 字符串 / 可选 | 导入目标题库的标识，使用小写 kebab-case，最多 80 字符；省略时使用任务 slug。 |
| `set_title` | 字符串 / 可选 | 题库名称，1–10,000 字符；省略时使用题目 `title`。 |
| `summary` | 字符串 / 可选 | 题库摘要，1–10,000 字符；省略时使用 `task.description` 或平台摘要。 |

### `environment/requirements.toml`

这个文件可省略。保留它时，只写考生能看到的环境说明；格式版本来自 `task.toml` 的 `assessment.protocol_version`。

```toml
additional_software = []
note = "使用平台已有 Python、办公工具和 Agent。"
```

| 字段 | 类型 / 必填 | 具体含义 |
| --- | --- | --- |
| `additional_software` | 数组 / 可选 | 当前只接受空数组 `[]`，省略也表示无额外安装。任务包没有自动安装软件的权限；需要新软件时，由平台管理员先配置环境。 |
| `note` | 字符串 / 可选 | 给考生和管理员看的工具使用说明，1–10,000 字符，不包含密钥、私有路径或评分规则。 |

环境能力由平台维护。任务包不包含 `Dockerfile` 或环境安装入口，公开数据放在 `environment/` 下即可。

## 3. 产物要求

在 `task.toml` 中用一个或多个 `[[assessment.artifacts]]` 声明产物槽位（页面上的一个交付项）。平台根据这些槽位生成文件选择控件；用户为各项选好文件后，提交整道题时统一复制、校验和冻结文件。

```toml
[[assessment.artifacts]]
id = "report"
title = "分析报告"
description = "说明结论、证据、假设和限制。"
kind = "file"
content_type = "document"
formats = ["md", "pdf"]
views = ["text", "files"]
required = true
min_files = 1
max_files = 1
max_bytes_per_file = 10485760
max_total_bytes = 10485760
missing_policy = "zero_dependent_criteria"
```

每个产物的字段如下。除注明可选或有条件必填外，都必须填写：

| 字段 | 类型 / 要求 | 具体含义 |
| --- | --- | --- |
| `id` | 字符串 / 必填 | 题内唯一标识，小写 kebab-case，最多 80 字符；rubric 通过这个值引用产物。改名称显示用 `title`，不要随意改 ID。 |
| `title` | 字符串 / 必填 | 文件选择项显示的名称，例如“分析报告”，1–10,000 字符。 |
| `description` | 字符串 / 必填 | 该产物要交什么、包含什么，1–10,000 字符。考生可以看到。 |
| `kind` | 字符串 / 必填 | `file` 选一个文件；`file_set` 选多个文件；`directory` 选一个目录并保留其相对目录结构。 |
| `content_type` | 字符串 / 必填 | 内容类别：`document` 文档、`presentation` 演示、`spreadsheet` 表格、`image` 图像、`code` 代码、`mixed` 混合。它描述内容，不自动决定判卷器。 |
| `formats` | 字符串数组 / 必填 | 允许的文件扩展名，小写、不带点、不重复、至少一个，见下方格式表。目录中的每个文件都必须符合。 |
| `views` | 字符串数组 / 必填 | 判分可以读取的内容形式，至少一个且不重复；可选 `text`、`pages`、`cells`、`image`、`files`。每一种允许格式必须能提供所有声明视图。 |
| `required` | 布尔值 / 必填 | `true` 表示主动提交时必须提供；`false` 表示可以不交。无论是否必交，缺失产物的计分行为都由 `missing_policy` 规定。 |
| `min_files` | 整数 / 必填 | 交付项有内容时，最少文件数，0–1,000，不能大于 `max_files`。必交项至少为 1；单文件项只能为 0 或 1。 |
| `max_files` | 整数 / 必填 | 最多文件数，1–1,000；单文件项固定为 1。 |
| `max_bytes_per_file` | 整数 / 必填 | 每个文件的最大字节数，1–52,428,800（50 MiB），不能超过本项的 `max_total_bytes`。 |
| `max_total_bytes` | 整数 / 必填 | **这个交付项内**所有文件的最大合计字节数，1–134,217,728（128 MiB）。不同交付项分别计算，题包不另设整题总容量字段。 |
| `missing_policy` | 字符串 / 必填 | 固定为 `zero_dependent_criteria`：缺少该项时，引用该项的 rubric 记零分；没有引用它的 rubric 正常执行。 |
| `max_depth` | 整数 / 目录必填 | 只用于 `directory`，范围 1–32。直接位于所选目录内的文件深度为 1，`a/b.csv` 深度为 2。 |
| `required_paths` | 字符串数组 / 可选 | 仅用于目录，列出必有的文件相对路径，例如 `["src/main.py", "README.md"]`。省略或 `[]` 表示没有指定文件名；数量、深度和格式仍需符合本项限制。 |
| `labels` | 字符串数组 / 可选 | 非空且不重复的描述标签，省略或 `[]` 表示无标签。只用于展示或筛选；实际读取和判分由 `views`、`rubric.inputs`、`rubric.verifier` 决定。 |
| `max_chars` | 整数 / 可选 | 仅用于格式全部为 `md`、`txt` 的产物；限制每个文件的非空白字符数，1–10,000,000。省略则不加此项内容长度限制，但仍执行字节和视图上限。 |
| `max_pages` | 整数 / `pages` 视图可选 | 每个文档最多读取多少页，1–40，默认 40。 |
| `max_text_chars` | 整数 / `text` 视图可选 | 每个文字视图最多多少字符，1–200,000，默认 200,000。它控制判分读取量，与 `max_chars` 的非空白内容限制不同。 |
| `max_cells` | 整数 / `cells` 视图可选 | 每个表格视图最多多少单元格，1–20,000，默认 20,000。 |
| `max_cell_chars` | 整数 / `cells` 视图可选 | 每个文件的表格评分视图最多多少字符，1–200,000，默认 100,000。统计紧凑 JSON 中的单元格值、公式、定位信息和转义字符；使用 `ensure_ascii=False`、`separators=(",", ":")`，不把中文转换为 Unicode 转义。外层文件路径和哈希另计入整项评分预算。它限制读取内容量，不能用文件的 KB 数或单元格数量代替。 |
| `max_image_bytes` | 整数 / `pages` 或 `image` 视图可选 | 每张供判分使用的图像最多多少字节，1–4,194,304（4 MiB），默认 4 MiB；包括从文档渲染的页面图像。 |

没有声明相应视图时，不能填写它的读取上限。读取超限按输入无效处理，不能默默截掉后半部分再评分。平台在公开交付要求中展示这些限制；任务题面列出的产物限制应与配置一致。每个必交产物至少被一条 rubric 引用；只收集、不计分的附件应设为可选。

XLSX 评分只读取可见工作表，排除 `hidden` 和 `veryHidden` 工作表；公式与保存的计算缓存分别保留。平台不把缓存值冒充重新计算的结果。隐藏表不提供评分证据，也不计入可见单元格和字符限额。

路径使用 POSIX 相对路径，例如 `src/main.py`。每个用户产物的相对路径的 UTF-8 长度最多 1,024 字节、32 层；每个文件名或目录名的 UTF-8 长度最多 255 字节，目录产物还要满足自己的 `max_depth`。所选目录之前的工作空间路径、平台添加的存储及归档目录前缀，都不占用该产物的相对路径额度。禁止 `..`、绝对路径、软硬链接、特殊文件、Windows 保留名称、大小写冲突和 Unicode 规范化冲突。

### 评分视图

| 视图 | 用途 |
| --- | --- |
| `files` | 文件名、大小、哈希和目录结构；不能单独作为模型判分内容 |
| `text` | UTF-8 文本、Markdown、可提取的文档文字 |
| `pages` | PDF、DOCX、PPTX 等页面渲染和文字 |
| `cells` | CSV、XLSX 的表格单元格 |
| `image` | PNG、JPEG 或页面图像 |

`content_type` 表明内容类别，`formats` 限定文件格式，`views` 决定评分端如何读取它；具体调用哪种判卷器，由 rubric 的 `verifier` 决定。格式必须支持所声明的全部视图；例如图像不能声明 `cells`，LLM 不能接收 `files` 路径视图。平台在生成视图时执行页数、字符数、单元格数和图像大小限制，超限应记录为输入无效而不是静默截断。

支持格式与视图的对应关系如下。扩展名全部小写、不带点，不能用通配符：

| 格式 | 可以声明的视图 |
| --- | --- |
| `md txt json py js ts tsx jsx html css sql sh toml yaml yml ipynb svg` | `text`、`files` |
| `pdf docx pptx` | `text`、`pages`、`files` |
| `xlsx csv` | `text`、`cells`、`files` |
| `png jpg jpeg` | `image`、`files` |
| `zip` | `files` |

导入和读取上限如下；任务也可以在槽位中设置更小的值：

| 范围 | 上限 |
| --- | ---: |
| 任务 ZIP 和解压后的任务包 | 各 64 MiB |
| 单个交付文件 | 50 MiB |
| 每个交付项的文件合计 | 128 MiB |
| 单个 PDF/DOCX/PPTX 评分页数 | 40 页 |
| 单个文字视图 | 200,000 字符 |
| 单个表格视图 | 20,000 个单元格 |
| 单张评分图像 | 4 MiB |

公开材料若分配到带有桌面文件桥的环境，还应满足每个材料 16 MiB、总量 64 MiB、最多 100 个文件的传输上限。

Windows 文件桥在一次交卷请求中流式上传 ZIP，按每个交付项分别检查解压后容量，不另设整题文件容量。云端提交传工作空间内的路径。两种入口都在完整接收、核验文件并再次确认授权和截止时间后，才发布这次提交。

提交清单及其归档 JSON 的平台处理上限为 512 MiB，覆盖当前最多 30 个产物、每项 1,000 个文件及其路径和哈希元数据；这不限制交付文件内容的合计大小。


## 4. 评分计划

`tests/evaluation.toml` 使用 UTF-8 TOML，属于私有评分资料。下面的配置假定 `task.toml` 已声明名为 `data` 和 `report` 的产物槽位，并提供 `tests/checks/check-data.py`：

```toml
protocol_version = "1.1"

[aggregation]
id = "weighted_sum/v1"
max_score = 100
round_decimals = 2
on_error = "withhold_total"

[[verifiers]]
id = "data-check"
kind = "python"
plugin_api = "python/v1"
entrypoint = "checks/check-data.py:run"
timeout_seconds = 30
network = "none"

[[verifiers]]
id = "quality-judge"
kind = "llm"
plugin_api = "llm/v1"
model_profile = "deepseek-text-v1"
required_capabilities = ["text", "structured_output"]
timeout_seconds = 120

[[rubrics]]
id = "accuracy"
title = "数据准确"
criterion = "交付物中的关键数据与参考资料一致。"
inputs = [{ artifact = "data", view = "cells" }]
verifier = "data-check"
scale_max = 4
weight = 50
evidence_required = true
anchors = ["0：没有可核验结果", "4：关键数据全部正确"]

[[rubrics]]
id = "quality"
title = "表达清楚"
criterion = "报告的结论、依据和限制表达清楚。"
inputs = [{ artifact = "report", view = "text" }]
verifier = "quality-judge"
scale_max = 4
weight = 50
evidence_required = true
anchors = ["0：没有可评估内容", "4：表达完整清楚"]
```

### 评分计划字段

`evaluation.toml` 的顶层字段：

| 字段 | 类型 / 必填 | 具体含义 |
| --- | --- | --- |
| `protocol_version` | 字符串 / 必填 | 固定为 `"1.1"`，必须与 `task.toml` 一致。 |
| `aggregation` | 配置表 / 必填 | 汇总每条 rubric 的分数，字段见下表。 |
| `verifiers` | 配置表数组 / 必填 | 1–100 个判卷器配置，用 `[[verifiers]]` 声明。 |
| `rubrics` | 配置表数组 / 必填 | 1–100 条评分标准，用 `[[rubrics]]` 声明。每条独立执行。 |
| `extensions` | 配置表 / 可选 | 私有描述元数据，格式与任务配置中的扩展相同。 |

`[aggregation]` 的四个字段均必填：

| 字段 | 类型 / 允许值 | 具体含义 |
| --- | --- | --- |
| `id` | 字符串 `weighted_sum/v1` | 采用“原始分比例乘权重，再求和”的算法。 |
| `max_score` | 数字 `100` | 每题满分固定 100 分，不是题库权重。 |
| `round_decimals` | 整数 `2` | 只在最终总分上四舍五入至两位小数；中间贡献不先舍入。 |
| `on_error` | 字符串 `withhold_total` | 任一必要评分失败时，总分保持 `null`，等待重试，不能算成考生零分。 |

每个 `[[verifiers]]` 的字段：

| 字段 | 类型 / 要求 | 具体含义 |
| --- | --- | --- |
| `id` | 字符串 / 必填 | 评分计划内唯一的小写 kebab-case 标识，最多 80 字符；rubric 用它选择判卷器。 |
| `kind` | 字符串 / 必填 | `python` 用脚本检查；`llm` 用平台配置的 Agent Judge。 |
| `plugin_api` | 字符串 / 必填 | `python` 固定用 `python/v1`；`llm` 固定用 `llm/v1`。 |
| `timeout_seconds` | 整数 / 必填 | 该条 rubric 的单次判分最长运行秒数，1–3,600；超时记评分错误。 |
| `entrypoint` | 字符串 / Python 必填 | 格式 `checks/file.py:function`，指向 `tests/checks/` 下实际存在的 Python 文件和函数名。模型判卷器不能填写。 |
| `network` | 字符串 / Python 必填 | 固定为 `none`，脚本不能联网。模型判卷器不能填写；它的联网权限由平台管理。 |
| `model_profile` | 字符串 / Agent Judge 必填 | 平台登记的逻辑配置：`deepseek-text-v1` 用于文字/表格，`deepseek-vision-v1` 还允许图像/页面。Python 判卷器不能填写。 |
| `required_capabilities` | 字符串数组 / Agent Judge 必填 | **判卷器的输入能力**，不是工作空间软件清单。必须包含 `text`、`structured_output`；需要看图时再包含 `image`，并选择视觉配置。成员不重复，不得要求配置没有的能力。Python 判卷器不能填写。 |

每个 `[[rubrics]]` 的字段：

| 字段 | 类型 / 必填 | 具体含义 |
| --- | --- | --- |
| `id` | 字符串 / 必填 | 评分项唯一标识，小写 kebab-case，最多 80 字符。 |
| `title` | 字符串 / 必填 | 管理员看到的评分项名称，1–10,000 字符。 |
| `criterion` | 字符串 / 必填 | 这一项具体检查什么、怎样扣分或给分，1–10,000 字符；应能独立执行，不能只写“质量好”。 |
| `inputs` | 配置表数组 / 必填 | 至少一组 `{artifact, view}`：`artifact` 必须是已声明产物的 ID；`view` 必须是该产物声明的视图。同一组不能重复。只把这些输入交给当前判卷器。 |
| `verifier` | 字符串 / 必填 | 引用一个已声明的 `verifiers[].id`。多条 rubric 可引用同一配置，但不会共享判分会话。 |
| `scale_max` | 数字 / 必填 | 当前评分项原始分满分，必须是有限正数，例如 4。 |
| `weight` | 数字 / 必填 | 当前评分项占整题的分数权重，必须是有限正数，全部 rubric 的权重恰好合计 100。 |
| `evidence_required` | 布尔值 / 必填 | 固定为 `true`，要求判卷器给出可核验的产物位置和证据。 |
| `references` | 配置表数组 / 可选 | 私有参考文件，省略等于 `[]`。每项 `{id, path}` 的 `id` 是本评分项内唯一的 kebab-case 名称；`path` 是 `tests/`、`solution/` 或 `fixtures/` 内真实文件的相对路径。每个文件不超过 2 MiB。 |
| `anchors` | 字符串数组 / 可选 | 非空、不重复的分档描述，例如 `["0：关键数据错误", "4：全部正确"]`。填写时数组不能空；省略则只按 `criterion` 判断。 |
| `description` | 字符串 / 可选 | 评分项的补充说明，1–10,000 字符，只供评分端和管理员使用。 |

模型不能只凭 `files` 路径视图判分；需要读取文字、单元格、页面或图像。`references` 不进入考生页面。平台保存这些材料的哈希，防止评分时引用发生变化。

### 判卷器

中控不执行题目作者自定义的总控脚本。它读取并校验 `evaluation.toml`，按其中的 `rubrics` 为每个评分项准备冻结产物视图，然后分别调用对应的 Python 或 LLM 判卷器，最后按 `aggregation` 汇总。脚本只负责当前评分项，平台保存各项的输入、输出和执行记录。

- `python/v1` 只能引用 `tests/checks/` 中的入口，网络必须为 `none`。它接收评分引擎生成的只读上下文，不能把考生输入解释为服务端路径，也不能修改任务包或工作空间。
- `llm/v1` 由 DeepSeek Harness 执行 Agent Judge，平台配置官方 `deepseek-flash` 模型。每条 rubric 和每次重试建立独立会话，只允许读取、搜索本项评分证据；不开放 shell、网页检索、编辑工具或考生沙盒。任务包只写逻辑 `model_profile` 和输入能力，不写服务地址、密钥或启动命令。
- 判卷器只允许 `python/v1` 和 `llm/v1`；总控流程由中控负责，不由任务包内脚本负责。

当前 Agent Judge 的平台预算如下，任务包不能通过配置扩大它们：

| 范围 | 上限 |
| --- | --- |
| 每条 rubric 的判分尝试 | 最多 3 次，每次新建进程、home 和会话 |
| 每次尝试的模型调用 / 工具调用 | 12 次 / 64 次，工具只含 `read_evidence` 与 `search_evidence` |
| 每次模型响应 | 最多 6,000 个输出 token |
| 每条 rubric 的文字与参考资料 | 序列化后合计 3,000,000 字符，包含文件元数据 |
| 每次尝试的完整输入包 | 256 MiB，包含图像编码 |
| 每次发给模型的 HTTP 请求体 | 48 MiB；超过 40 MiB 时，平台将图片按原始字节上传并改用文件标识引用，保留全部文字 |
| 每次模型请求的图片 | 最多 600 张，原始图片合计最多 200 MiB；每张仍遵守产物声明且不超过 4 MiB |
| 每次尝试的评分输入、临时数据和轨迹 | 合计 1 GiB；最终响应文件最多 1 MiB |
| 运行时间 | 不超过 `timeout_seconds`，同时不能超过整题评分剩余时间；整题评分预算由平台计算，最长 3,600 秒 |

平台软件和原生库缓存不计入这 1 GiB，但仍受判卷容器的总内存、磁盘和进程限制约束。缓存中不能存放考生文件、模型密钥或评分记录。大型评分输入使用私有磁盘临时目录，并降低并发，不把扩大容量理解为无限占用内存。

图片文件引用只改变传输方式，不改变图片内容、分辨率或评分依据。平台保存图片原始字节、SHA-256、供应商文件标识及实际模型请求，归档时能核验文件标识对应哪张图。上传文件设置一小时自动过期，评分结束时尝试提前删除；发生中断时由到期机制清理。供应商的 48 MiB 请求体和图片限制见[DeepSeek 图像输入说明](https://api-docs.deepseek.com/guides/vision/)，到期字段见[Files API](https://api-docs.deepseek.com/guides/files_api/)。

`read_evidence` 可以按一个 `id`、一组 `ids`（1–1,000 个、不重复）或 `all=true` 读取证据，三种方式互斥。`all=true` 一次读取本条 rubric 已准备的全部产物视图、私有参考和题面，因此 64 次工具调用不等于只能读取 64 份证据。工具不接收文件路径、URL 或当前评分项之外的 ID；判卷完成前必须读过本项全部证据。

导入时，平台根据每条 rubric 的最大文件数、视图上限、参考资料和元数据计算组合输入预算；同时预估图像去重后的运行记录容量。声明的组合超过文字、完整输入包、图片总量或运行记录预算时拒绝导入，并指出超出的范围。限制较大的单项产物，不代表可以把多个这样的输入同时交给一条 rubric。

运行时仍须复核实际输入大小。产物超过声明的视图读取上限，按 `invalid_artifact` 处理；模型请求超限、超时或轨迹未完整保存属于评分失败，整题总分保持 `null`。平台不会截断资料后假装完成判分，也不会把服务失败算成考生零分。发布前应使用交付要求允许的最大文件数量和读取量试判。

`deepseek-flash` 是官方模型别名。平台保存请求的别名、响应中的模型标识和配置哈希；官方未提供不可变权重版本时，不能据此声称模型权重已经固定。跨时间比较分数需要另外做评分质量校准。

Python 入口必须是 `run(context)` 这样的单参数函数；函数名与 `entrypoint` 冒号后的名称一致。引擎提供以下上下文，检查器返回结果字典，不自行读写平台的提交记录：

```python
context = {
    "protocol_version": "1.1",
    "rubric": {"id": "accuracy", "scale_max": 4},  # 本条 rubric 的完整配置
    "inputs": {
        "data": {
            "files": [{
                "path": "/受控冻结目录/answer.csv",
                "relative_path": "answer.csv",
                "sha256": "由引擎提供的真实 SHA-256",
                "size_bytes": 128,
            }],
            "cells": [],  # 本条 inputs 声明的视图，由处理器填充
        },
    },
    "references": {"source-data": "/受控题包目录/tests/references/data.csv"},
}
```

`path` 是引擎授予读取权限的本地路径，证据必须使用 `relative_path`。检查器不能自行拼接其他服务端路径；未声明的参考资料不进入 `references`。这段代码只说明字段形状，实际评分输入由引擎生成。

每个 rubric 独立调用一个判卷器；多个 rubric 可以引用同一个判卷器配置，每次执行仍是独立调用。Agent Judge 可以多轮读取证据再返回结果，平台同时保存 Harness 会话轨迹、模型请求响应和实际模型标识；这些资料只供管理员复核。平台可向 Agent Judge 提供只读定位标识：`evidence_ref` 指向当前文件视图；文字视图按顺序提供 `text_segments = [["t1", "原文块"], ...]`，每块最多 800 字符，逐块拼接就是完整原文。Judge 可返回 `{evidence_ref, locator_ref}` 选择文字块或表格位置，平台再补全路径、哈希和真实引文。原文不重复传输、不改写换行；最终结果中的 `text.quote` 仍须逐字存在于冻结文字视图中。

下面是判卷器成功时返回的 JSON；`contribution` 由中控计算，判卷器不能自行填写：

```json
{
  "status": "completed",
  "raw_score": 3,
  "scale_max": 4,
  "reason_code": "evaluated",
  "feedback": "简短的判分理由",
  "evidence": [{"artifact_id": "data", "path": "answer.csv", "sha256": "0000000000000000000000000000000000000000000000000000000000000000", "view": "cells", "locator": {"kind": "csv_rows", "rows": [2, 4]}}]
}
```

成功结果必须恰好包含下面六个字段：

| 字段 | 类型 / 含义 |
| --- | --- |
| `status` | 字符串，固定为 `completed`，表示本次判分成功完成。 |
| `raw_score` | 有限数字，范围 0 到该 rubric 的 `scale_max`，两端都允许。 |
| `scale_max` | 数字，必须与当前 rubric 的原始满分完全一致。 |
| `reason_code` | `evaluated` 表示正常判分；`invalid_artifact` 表示产物内容无效，此时原始分必须为 0。 |
| `feedback` | 1–12,000 字符的非空文字，简要说明为什么给这个分数，仅供管理员查看。 |
| `evidence` | 1–200 项的证据数组，每项包含 `artifact_id`、`path`、`sha256`、`view`、`locator`；分别指向本次输入的交付项、文件相对路径、文件哈希、读取视图和具体位置。定位方式见下表。 |

脚本异常、超时、模型不可用、证据缺失属于评分失败，必须单独记录，不能转换成考生零分。Agent Judge 的内部工具可以使用平台分配的证据标识；平台将其解析成上述统一结果后再校验和归档。

判卷器成功返回时，`raw_score` 必须是有限数字，范围为 0 到该 rubric 的 `scale_max`（包括两端）；返回的 `scale_max` 必须与 rubric 完全一致；`feedback` 必须是非空文字；`evidence` 必须是数组。每条证据都要引用当前输入中真实存在的产物、相对路径、视图、哈希和定位信息。返回对象的顶层字段多一个、少一个或类型不对，都按判卷失败处理。

证据中的 `path`、`sha256` 和定位信息必须引用评分输入。示例里的全零哈希只是占位符，实际判卷不能照抄。各类定位方式如下：

| `locator.kind` | 必须提供的定位信息 |
| --- | --- |
| `text` | `quote`：文字视图中逐字存在的非空引文 |
| `page` | `page`：页面视图中存在的页码 |
| `image` | 当前 `image` 视图中的文件 |
| `cell` | `sheet` 和 `cell`：表格视图中存在的工作表与单元格 |
| `csv_rows` | `rows`：CSV 真实物理行号，从 1 开始；只能配 `cells` 或 `files` |
| `file` | 只用于 `files` 视图，说明文件级检查 |
| `absence` | 说明该文件中缺少的具体内容，例如 `expected_metric` |

除整项产物缺交由引擎生成记录外，`absence` 也必须引用实际输入文件、哈希和视图。文字或图像判卷不能只引用文件名作为评分证据。

判卷器异常、超时、返回格式不合规或视图处理失败时，不要求判卷器伪造成功 JSON。中控会保存一条标准失败记录：`status = "error"`、`raw_score = null`、`contribution = null`、`reason_code = "verifier_error"`，并附上安全的错误说明、执行次数、重试记录和错误类型。只要有一条 rubric 进入这个状态，整道题的总分就是 `null`；管理员可以据此重试或重判，考生不会看到私有错误细节。

评分参考文件必须来自 `tests/`、`solution/` 或 `fixtures/`；交给文字或视觉模型的参考文本必须是有效 UTF-8，单个文件不超过 2 MiB。判卷器只能读取任务快照和冻结提交，不能读取其他用户或可变工作路径。

### 汇总规则

对于每条 rubric：

```text
贡献 = raw_score / scale_max × weight
总分 = 四舍五入到 round_decimals 位的所有贡献之和
```

协议把每道题的满分固定为 100，`aggregation.max_score` 必须为 100。rubric 权重总和必须为 100；只在最后一步舍入。缺少产物时，按该槽位的 `missing_policy` 处理依赖它的 rubric；无关 rubric 不受影响。任一必要评分环节失败时，总分为 `null`，并在管理员结果中写明失败原因。

### 题目集的评分

题目本身和题目集是两层评分，不要把两种权重混在一起：

- 每道题的满分固定为 100 分。`rubric.weight` 只在这道题内部使用，合计必须为 100；
- 题目集由多道题组成后，平台再为每道题设置 `question_weight`。这个权重不写进任务包，也不进入 `evaluation.toml`；
- 一个题目集的题目权重必须都为正数，且合计为 100。题目集清单中的每道题只能出现一次，题目集中的每道题都必须有一个权重；
- 题目集总分按下面的公式计算，最后保留两位小数：

```text
题目集总分 = Σ（题目得分 × question_weight / 100）
```

如果题目集中有一道题的总分不可用，题目集总分也记为 `null`，不能把其他题目的权重重新摊平。`question_weight` 必须是有限的正数，题目集结果至少要保存题目编号、题目得分、题目权重、题目集总分和 `score_available`，方便复核。

开始一轮评测时，平台冻结题目集的题目清单、任务快照与权重；之后更新已有任务包或调整权重，只影响后续新评测。题库存在未完成评测或正在进行的 Windows 作答时，不能增添题目、更改题目清单或撤下题库。题目集配置是平台级文件或数据库记录，不属于任何任务包。它至少要有唯一的 `set_id`、`schema_version = "assessment-set/v1"`、题库标题、`score_scale = 100`、`round_decimals = 2` 和题目清单。题目清单中的 `question_id` 只能出现一次，必须引用已发布的任务，所有 `question_weight` 为有限正数且合计为 100。可以使用类似下面的结构：

```toml
[assessment_set]
set_id = "general-capability"
schema_version = "assessment-set/v1"
title = "能力测评题库"
score_scale = 100
round_decimals = 2

[[assessment_set.questions]]
question_id = "research-report"
question_weight = 60

[[assessment_set.questions]]
question_id = "data-analysis"
question_weight = 40
```

题目集结果使用 `schema_version = "assessment-set-result/v1"`，包含 `set_id`、`score_scale = 100`、`round_decimals = 2`、`questions`、`total_score` 和 `score_available`。每个题目结果包含 `question_id`、`question_weight`、`score` 和 `score_available`。题目明细与权重只供管理员查看；考生只得到总分和是否可用。整轮归档把配置保存为 `assessment-set.json`，把结果保存为 `assessment-set-result.json`。

## 5. 作答生命周期

1. **开始**：平台锁定不可变题目快照，创建本轮评测、作答和工作空间的独立标识，并注入 `instruction.md` 和 `environment/`。每条云端作答必须属于本轮评测，不能临时接入其他评测或未关联评测的作答。
2. **作答**：云端只有用户进入工作空间且会话心跳有效时累计时间；退出、关闭页面或失去心跳后暂停，同时停止该空间内的 Agent 和终端程序。多道题共享本轮工作空间。独立 Windows 平台按连续时间计时，其环境和计时条件单独记录。
3. **选择交付物**：用户为每个交付项选择文件或目录。此时只是页面选择，没有提交副本，也不触发评分；原文件修改后，提交时读取的是修改后的实际内容。
4. **整题提交**：用户确认后，平台一次性接收全部选择，核验授权、路径、格式、数量、容量和哈希，再冻结副本并创建一份提交清单。主动提交必须满足所有必交项。校验或复制失败不算交卷；成功提交后不能替换该次交付物。
5. **到时未交卷**：按未交卷处理，平台生成产物清单为空的截止记录，依赖缺失产物的 rubric 记零分。页面选择和工作空间文件都不会自动纳入评分；这些文件仍可随整轮工作空间归档。提交是否成功由服务端确认，开始上传不等于已经交卷。
6. **结束评测**：用户二次确认后结束整轮评测。平台可以设置是否允许尚有题目未交卷时提前结束；允许时，确认窗口必须列出尚未正式交卷的题目及其交付项，并要求用户明确确认缺交计分。确认后，平台为这些题目生成空产物清单，按缺交规则评分；已经正式提交的产物与评分记录保留。页面选择和工作空间文件不会因此自动交卷。服务端须重新核对未交题目清单，清单变化时要求重新确认；记录失败不能只关闭其中一部分题目。随后平台停止写入并冻结工作空间，收集所有可获取 Agent 线程的轨迹，等待在途评分完成，再归档评分证据；确认归档完整后才清空沙盒并恢复基线。未开启提前结束时，须等所有题目已提交或已截止后才能结束。
7. **重做与重判**：重做只能由管理员开放新作答，沿用原作答环境；更换云端或 Windows 环境必须另行分配独立评测。重判保留原评分运行和新运行。管理员可看详细 rubric，考生只看整题总分和公开状态。

正式提交使用平台生成的 `manifest.json`。字段定义如下；这些字段由系统生成，出题者和考生不需要编写：

| 字段 | 含义 |
| --- | --- |
| `protocol_version` | 这次作答绑定的任务协议版本。 |
| `submission_id` | 本次正式提交的唯一标识。 |
| `session_id` | 对应作答的唯一标识。 |
| `task_package_hash` | 本次作答绑定的完整题包 SHA-256。 |
| `submitted_at` | 服务端记录正式提交、到时关闭或提前结束缺交的时间，带时区。 |
| `reason` | `candidate` 表示考生成功提交；`deadline` 表示到时关闭；`assessment_end` 表示用户确认提前结束评测，关闭尚未交卷的题目。 |
| `artifacts` | 正式提交的产物列表；到时或提前结束仍未交卷时为空。每项保存 `artifact_id`（交付项 ID）和 `files`（冻结文件清单）。 |
| `finish_confirmation` | `reason = "assessment_end"` 时保存的确认记录。`assessment_id` 是本轮评测标识，`user_id` 是确认者的用户标识，`confirmed_at` 是带时区的确认时间，`acknowledge_missing` 必须为 `true`，`unsubmitted_attempt_ids` 是当时确认按缺交处理的全部作答标识。该记录只供管理员复核，不发给其他考生。 |
| `administration`、`administration_hash` | 平台冻结的本次作答条件及其规范化 JSON 哈希，包括环境、Agent、计时和可见范围；用于说明这份分数是在什么条件下得到的。 |
| `files[].path` | 文件在提交根目录内的相对路径。 |
| `files[].relative_path` | 文件在该交付项中的相对路径。 |
| `files[].size_bytes` | 冻结文件的实际字节数。 |
| `files[].sha256` | 冻结文件的小写 SHA-256，用于核验内容。 |

平台生成并核验路径、大小和哈希，不能信任考生自行上传的清单。归档同时保存这个清单和冻结文件。

## 6. 评分与过程证据

每次判分都应保存 `judge-evidence/v1`：

```text
judge-evidence/
├── index.json
└── <rubric-id>/<execution-number>/
    ├── metadata.json               # 执行身份、状态、实际模型与完整性记录
    ├── request.json                # Python 输入或 Harness 指令与只读证据包
    ├── response.json               # Agent Judge 最终响应、会话 ID、模型与用量
    ├── result.json                 # 校验后的统一六字段结果
    ├── harness-files.json          # Harness 原始文件到归档文件的对应表
    ├── harness-*                   # 会话 JSONL、事件、工具调用与模型往返原始文件
    ├── input.json                  # Python 输入，如适用
    ├── processor-request.json      # 受控视图处理请求，如适用
    └── processor.log               # 视图处理日志，如适用
```

这些文件按实际执行类型保存：Python 检查器不生成 Harness 文件；中途失败时可能没有 `result.json`，但必须保留已获取的证据及失败原因。`harness-files.json` 记录原始路径和归档路径，不能假定 Harness 内部会话文件始终使用同一个名称。原始证据包括会话 JSONL、SDK 事件、`tool-calls.jsonl`、Harness 原生图像附件、每次模型请求/响应、HTTP 状态与完整性记录，以及运行日志。

Agent Judge 返回结果后，平台还须确认同一会话的原生日志已经保存完毕：事件顺序连续，包含本次调用的完成事件，最后回答与返回结果一致。文件存在不等于保存完整；检查不通过时，本次判分失败，已取得的记录仍须保留。归档时再次检查，历史失败或不完整记录如实标注，不得冒充完整记录，也不得覆盖后来成功重试的结果。

重复出现的图像可以按内容哈希只保存一份。请求记录须保留图像的 MIME 类型、字节数、SHA-256 和归档内引用，并记录原始请求的哈希及重建方式；结合图像文件必须能完整还原实际请求。对发送给模型的内容不作删减。页面图像允许在保留完整页面的前提下有界压缩和缩放，实际尺寸、编码质量和渲染哈希应随视图保存，便于复核。平台当前先渲染最长边 1600 像素、JPEG 质量 85；超过声明上限时逐步降低质量，最低 60，再缩小尺寸，最长边不低于 1000 像素。不裁剪、不删页，实际参数写入 `page-manifest.json`；仍无法容纳时报告处理失败。

平台记录程序标识、请求和响应字节、重试、超时、异常、输入输出大小、哈希和脱敏说明。不得记录 API 密钥、授权头或其他凭据；隐藏思维过程不是必需证据。无法取得原始 I/O 时，记录具体缺失原因，不能补造请求或响应。判分会话与考生会话独立保存，不混为同一条 Agent 轨迹。

过程证据包括：

- 用户工作空间中的文件事件和提交清单；
- 所有受控 Agent 线程的索引、事件和模型交互证据；
- 工具调用、失败、重试和终止原因；
- 运行环境标识、采集时间、文件哈希和采集缺失清单。

同一轮评测的工作空间与轨迹是 `shared_assessment`。它可能包含其他题目的草稿和 Agent 活动，不能在单题结果中伪称为该题独占过程，也不能声称捕获了已删除或未记录的活动。

## 7. 完成资料与归档

平台把每道题的完成资料生成在已验证的整轮归档中。单题结果格式标识为 `task-result/v1`，不是用户上传的交付物。

### 整轮归档 `assessment-archive/v1`

整轮归档保存一次评测的共享资料，再从同一份冻结 ZIP 生成每道题的结果。`source_revision` 是整轮归档的整数修订号；每次评分或采集资料改变，都生成新的归档修订并保留旧修订。

```text
assessment-<assessment-id>-v<revision>.zip
├── manifest.json                         # 身份、修订、文件清单和哈希
├── assessment.json                       # 用户、题库、作答清单 和结束状态
├── environment/
│   ├── freeze.json                        # 冻结时刻和工作空间状态
│   └── baseline.json                      # 基线与重置信息，不含任务文件
├── workspace-evidence/                    # 整轮工作空间、Agent 和模型证据
└── tasks/<question-id>/
    ├── packages/<task-package-hash>/      # 不可变题目快照
    └── attempts/<attempt-id>/
        ├── attempt.json
        ├── submissions/<submission-id>/
        │   ├── submission.json
        │   ├── files/                     # 冻结交付物副本
        │   └── grading/<evaluation-id>/outputs/
        └── completion/                    # 见下方单题完成资料
```

标准文件的责任边界如下：

| 文件 | 至少记录什么 |
| --- | --- |
| `result.json` | 作答状态、题目身份、总分、满分、`task_package_hash`、`source_revision` |
| `artifacts.json` | 每个产物槽位的提交标识、选中的相对路径、大小、哈希、正式交卷时间、校验状态 |
| `trajectory.json` | 线程 ID、Agent 标识、事件顺序、开始/结束时间、终止状态、证据文件引用和未采集原因 |
| `grading.json` | 每次评分运行、rubric、判卷器/模型配置版本、重试、状态、原始分、贡献、错误和证据引用 |
| `collection.json` | 采集范围、文件数量、完整性校验、遗漏项目、失败原因和重试结果 |
| `report.md` | 给管理员看的可读摘要；不能替代上述机读文件 |

`manifest.json` 必须列出除它自身以外的所有 ZIP 成员，并逐项记录大小和哈希；`workspace-evidence/` 是整轮共享范围，不能按题目伪造独占轨迹。只有该归档验证通过，平台才可以重置沙盒。

### 整轮归档中的单题目录

```text
tasks/<question-id>/attempts/<attempt-id>/completion/
├── report.md          # 人类可读摘要
├── result.json        # 作答身份、状态、总分或 null
├── artifacts.json     # 每次正式提交和文件哈希
├── trajectory.json    # 共享工作空间中的线程和模型证据索引
├── grading.json       # 全部评分运行、有效运行和判分证据索引
└── collection.json    # 采集范围、完整性和缺失原因
```

### 管理员下载的独立结果包

```text
task-result-<attempt-id>-v<revision>.zip
├── manifest.json
├── report.md
├── result.json
├── artifacts.json
├── trajectory.json
├── grading.json
├── collection.json
├── attempt.json
├── task/                         # 不可变题目快照
├── submissions/<submission-id>/files/
├── submissions/<submission-id>/grading/<evaluation-id>/outputs/
│   └── judge-evidence/           # 私有判分原始证据
├── evidence/                     # 整轮共享工作空间、Agent 和模型证据
└── environment/                  # 本轮环境和基线信息
```

除 `report.md` 外的五个标准文档使用 UTF-8 JSON，并包含 `schema_version = "task-result/v1"` 与 `attempt_id`；`report.md` 是人类可读摘要，也必须写明同一组身份。`manifest.json` 和 `result.json` 是评测、题目、作答、`task_package_hash` 和 `source_revision` 的权威来源，其他文档通过 `attempt_id` 和归档内路径与它们关联；这些关键身份不能用缺失或猜测的值代替。

结果包中的评分字段由平台生成；出题者只负责前面三类 TOML 配置、公开题面及私有评分资料。

结果包的机读约束：

- 路径是 ZIP 根目录下的 POSIX 相对路径，禁止绝对路径、`..`、重复项、链接和特殊文件；
- `sha256` 必须是小写 64 位十六进制，`bytes` 必须是非负整数；
- `manifest.files` 不列出 `manifest.json` 自身，清单中的成员集合必须与 ZIP 完全相同；
- `result.json.total_score` 在评分不可用时为 `null`，不能用零代替；
- `grading.json` 保留全部评分运行记录，并明确 `effective` 运行；评分失败、采集缺失和缺交产物是三种不同状态；
- 结果包写入后不可覆盖。若从同一源归档重新导出，必须得到相同修订；新的评分或采集结果创建新修订，并保留源归档哈希；
- 结果包内的文件哈希不包含它所在 ZIP 的自身哈希，避免递归校验。

### 归档与重置顺序

平台接受结束评测请求后按以下顺序执行：

1. 停止计时、阻止新的写入和提交；
2. 收集可访问的工作空间、Agent 线程、模型证据、提交副本和评分运行记录；
3. 等待在途评分完成，生成 `assessment-archive/v1`，校验文件路径、大小、哈希和身份；
4. 生成并验证每道题的 `task-result/v1`；
5. 将归档设为只读，记录遗漏、失败和重试结果；
6. 只有在归档验证成功后，删除本轮沙盒并从不含任务文件、用户文件和密钥的基线恢复。

任何采集失败都必须保留源资料并提供重试入口；不能为了完成归档而删除失败上下文。

## 8. 安全、隐私与权限

- 任务包、用户交付物、工作空间、轨迹和评分证据默认属于私有评测资料；考生不能读取 `tests/`、`solution/`、`fixtures/` 或其他用户空间。
- 任务包导入和结果包导出都拒绝路径穿越、软链接、硬链接、特殊文件、ZIP 炸弹、加密 ZIP、大小写冲突和 Unicode 路径碰撞。
- 判卷器运行在受控进程中：网络默认关闭，超时和资源上限由平台设置；模型提示必须把考生内容当作数据，不能让交付物改变评分规则或工具权限。
- 工作空间文件先经过类型、容量、哈希和视图检查，再交给判卷器；提交清单保存的是冻结副本，不是随后可变的工作路径。
- 管理员可以下载、重试、重判和重开，但所有动作都应留下审计记录。归档删除、保留期、导出审批和删除请求由平台隐私政策另行规定，归档中记录实际删除或未采集项目。

## 9. 扩展规则与发布检查

协议允许扩展，但扩展不能改变核心安全边界、公开/私有边界、总分语义或结果包身份。自定义元数据放在命名空间下：

```toml
[assessment.extensions.example-org.metadata]
rubric_family = "research"
```

`extensions` 的每个组织名使用小写 kebab-case，最多 80 字符；组织名下面必须且只能包含 `metadata` 表。`metadata` 可以使用字符串、有限数字、布尔值、数组和嵌套表，日期要写成字符串，不能放 TOML 日期对象。`extensions` 整体转成 UTF-8 JSON 后不超过 64 KiB；只允许描述性数据，不允许脚本、模板执行器、网络配置、凭据或动态导入路径。评分计划中的扩展使用同样的 `[extensions.<namespace>.metadata]` 结构。

发布任务前逐项检查：

1. 任务包路径、编码、文件类型、硬链接和链接检查通过；
2. `task.toml`、`evaluation.toml` 可解析且没有拼写字段；
3. 每个产物槽位都有题面说明，所有 rubric 引用存在的产物和 view；
4. 权重合计 100，判卷器入口、输入能力、超时和网络权限符合约束；
5. Python 检查器在正确、部分正确、错误、缺交和恶意文件样例上返回可解释结果；
6. 模型判卷器要求结构化输出和定位证据，且每条 rubric 独立调用；
7. 每个 `required = true` 的产物至少被一条 rubric 使用；如果产物只收集、不计分，应明确设为 `required = false`；
8. 考生可见内容不包含 rubric、权重、参考资料、模型配置、私有路径或凭据；
9. 一次性提交、到时未交卷、重做、重判、归档、重试和重置流程均经过验证；
10. 结果包可以独立验证，缺分为 `null`，缺失和失败原因可区分；
11. 用不包含任何用户资料和任务文件的基线创建新工作空间。

`examples/service-research/` 是一个可导入的示例题包，用来演示多产物、Python 检查器、文字 Agent Judge 和视觉 Agent Judge 的组合。它的材料和数值只属于示例，不是协议字段，也不应复制到正式任务中。
