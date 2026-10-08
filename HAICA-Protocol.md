# AI协作能力测评协议

Human–AI Collaboration Assessment Protocol，简称 **HAICA Protocol**。

当前版本：**V1.4**。任务包的 `protocol_version` 写作字符串 `"1.4"`。

HAICA Protocol 约定一道题要放哪些文件，以及平台怎样展示题面、接收交付物、判分和留档。出题者按这个格式打包，平台就能自动生成作答和评分流程。

协议规定输入、输出和权限边界。页面样式、云厂商和服务器实现由平台决定；V1.4 的评分 Agent 固定为独立 DeepSeek Harness + DeepSeek。`protocol_version` 标识任务包格式；`task_revision` 和 `source_revision` 用于识别题目内容和绑定记录。结果包、归档和判卷接口各自使用独立的格式标识，例如 `task-result/v1`、`assessment-archive/v1`、`python/v1` 和 `llm/v1`。

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

最小结构仍必须在 `task.toml` 中声明至少一个产物槽位，并在 `evaluation.toml` 中声明可执行的 `weighted_sum/v1` 评分计划（至少一条 rubric 和一个判卷器）。这个最小目录适用于仅使用平台 Agent Judge 的任务。引用材料或参考资料时，也必须提供相应文件。

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
4. 结束前可修改、重新提交，结束时选定最后成功版本，以及缺交到时的处理；
5. 允许使用的工具和禁止的行为。

平台读取 `task.toml` 中的 `assessment.duration_minutes` 作为本题的时间额度，将同一题库全部题目的额度相加，形成一轮评测共用的总作答时间，并在作答前显示。考生可以在题目间自由分配时间，单题额度不构成独立截止。题面不必重复时间；若注明，应与该字段一致并表述为计入题库的时间额度。单题题库的总时间等于该题额度。

题面不能写私有 rubric 权重、参考答案或模型提示。产物要求以 `task.toml` 为准，导入者应检查题面与配置一致。例如：

```markdown
# 服务预约分析

阅读 environment/materials/ 中的数据，解释预约变化并提出建议。

## 交付物

- report：一份分析报告，Markdown 或 PDF，不超过 10 MiB。
- data：一份 CSV 指标表，列出计算结果和口径。

从工作空间为各交付项选择文件，确认内容后提交整道题；测试结束前可以修改文件并重新提交。
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
protocol_version = "1.4"
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
| `protocol_version` | 字符串 / 必填 | 整个任务包采用的格式版本，当前固定为 `"1.4"`。环境说明沿用这个版本。 |
| `task_revision` | 字符串 / 必填 | 出题者给这份题目内容标记的修订号，例如 `research-001`，1–256 字符。它帮助人识别题目；平台另外计算整个题包的 SHA-256，实际评分绑定题包哈希。 |
| `title` | 字符串 / 必填 | 显示给考生的题目名称，1–256 字符。 |
| `language` | 字符串 / 必填 | 题面的主要语言标签，1–256 字符。建议使用 `zh-CN`、`en` 等语言代码；不会自动翻译内容。 |
| `difficulity` | 字符串 / 必填 | 题目难度，只能为 `low`、`medium`、`high`、`xhigh`、`max`，依次表示简单、一般、困难、很难、极难。字段拼写就是 `difficulity`。这是出题者的难度标注，不改变时间、权重或评分公式。 |
| `birthday` | 字符串 / 必填 | 出题者确认题面、材料和评分规则正式构造完成的时间；不是上传时间或考生作答时间。写带引号的 RFC3339 日期时间，必须有秒和明确时区，例如 `"2026-09-18T10:00:00+08:00"` 或 `"2026-09-18T02:00:00Z"`。可带 1–6 位小数秒，时分秒必须是普通有效时间（不接受闰秒），`T` 和 `Z` 大写；不接受只有日期、无时区、未知时区 `-00:00` 或未加引号的 TOML 日期值。 |
| `duration_minutes` | 整数 / 必填 | 本题计入题库总时间的分钟额度，范围 1–1,440。整轮总时间为所有题目的额度之和，不按评分权重折算，也不再对每题单独设截止；考生自由分配。题库总和可以超过单题的 1,440 分钟上限。云工作空间仅累计在线时间，退出或心跳失效后暂停。总额度、求和规则与计时方式在开始时冻结，并记录在本次评测的环境条件中。 |
| `evaluation` | 字符串 / 必填 | 私有评分计划的题包内相对路径，必须指向 `tests/` 内真实文件，通常为 `tests/evaluation.toml`。 |
| `workspace` | 配置表 / 必填 | 本题支持的工作空间配置，见下表。 |
| `artifacts` | 配置表数组 / 必填 | 1–30 个交付项，用 `[[assessment.artifacts]]` 逐项声明，详见第 3 节。 |
| `extensions` | 配置表 / 可选 | 带组织命名空间的描述元数据，详见第 9 节；不改变提交、判分或权限。 |

`[assessment.workspace]` 的字段：

| 字段 | 类型 / 必填 | 具体含义 |
| --- | --- | --- |
| `scope` | 字符串 / 必填 | 固定为 `shared_per_user`。同一用户在同一轮评测中的多道题共享一个工作空间；下一轮使用独立工作空间。 |
| `compatible_profiles` | 字符串数组 / 必填 | 至少一个且不重复。当前仅支持 `linux-office`，表示任务允许在哪种平台环境作答。Python、办公工具、字体等能力由平台统一配置；出题者不需要逐项声明。平台只能把题目分配到已经部署并验证可用的环境。 |

平台固定执行以下规则，不由题包开关控制：提交保存不可变副本，整轮结束前允许修改后重新提交；以最后一次成功提交为最终交付，整轮结束后才安排所有题目的评分；到时没有成功版本的题目按缺交处理。全部题目都有提交也不提前停止计时，考生仍可使用剩余时间完善产物。采集受控 Agent 的全部可获取轨迹，当前总分只评最终产物；考生只看到题面、交付要求、总分和公开状态。整轮结束后重做须由管理员建立新评测。

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
| `max_bytes_per_file` | 整数 / 必填 | 每个文件的最大字节数，1–209,715,200（200 MiB），不能超过本项的 `max_total_bytes`。 |
| `max_total_bytes` | 整数 / 必填 | **这个交付项内**所有文件的最大合计字节数，1–536,870,912（512 MiB）。不同交付项分别计算，题包不另设整题总容量字段。 |
| `missing_policy` | 字符串 / 必填 | 固定为 `zero_dependent_criteria`：缺少该项时，引用该项的 rubric 原始分和贡献均为 0，加分项不加分、减分项不扣分；没有引用它的 rubric 正常执行。 |
| `max_depth` | 整数 / 目录必填 | 只用于 `directory`，范围 1–32。直接位于所选目录内的文件深度为 1，`a/b.csv` 深度为 2。 |
| `required_paths` | 字符串数组 / 可选 | 仅用于目录，列出必有的文件相对路径，例如 `["src/main.py", "README.md"]`。省略或 `[]` 表示没有指定文件名；数量、深度和格式仍需符合本项限制。 |
| `labels` | 字符串数组 / 可选 | 非空且不重复的描述标签，省略或 `[]` 表示无标签。只用于展示或筛选；实际读取和判分由 `views`、`rubric.inputs`、`rubric.verifier` 决定。 |
| `max_chars` | 整数 / 可选 | 仅用于格式全部为 `md`、`txt` 的产物；限制每个文件的非空白字符数，1–10,000,000。省略则不加此项内容长度限制，但仍执行字节和视图上限。 |
| `max_pages` | 整数 / `pages` 视图可选 | 每个文档最多读取多少页，1–200，默认 200。 |
| `max_text_chars` | 整数 / `text` 视图可选 | 每个文字视图最多多少字符，1–2,000,000，默认 2,000,000。它控制判分读取量，与 `max_chars` 的非空白内容限制不同。 |
| `max_cells` | 整数 / `cells` 视图可选 | 每个表格视图最多多少单元格，1–100,000，默认 100,000。 |
| `max_cell_chars` | 整数 / `cells` 视图可选 | 每个文件的表格评分视图最多多少字符，1–2,000,000，默认 2,000,000。统计紧凑 JSON 中的单元格值、公式、定位信息和转义字符；使用 `ensure_ascii=False`、`separators=(",", ":")`，不把中文转换为 Unicode 转义。外层文件路径和哈希另计入整项评分预算。它限制读取内容量，不能用文件的 KB 数或单元格数量代替。 |
| `max_image_bytes` | 整数 / `pages` 或 `image` 视图可选 | 每张供判分使用的图像最多多少字节，1–4,194,304（4 MiB），默认 512 KiB；包括从文档渲染的页面图像。 |

没有声明相应视图时，不能填写它的读取上限。读取超限按输入无效处理，不能默默截掉后半部分再评分。平台在公开交付要求中展示这些限制；任务题面列出的产物限制应与配置一致。每个必交产物至少被一条 rubric 引用；只收集、不计分的附件应设为可选。

XLSX 评分只读取可见工作表，排除 `hidden` 和 `veryHidden` 工作表；公式与保存的计算缓存分别保留。平台不把缓存值冒充重新计算的结果。隐藏表不提供评分证据，也不计入可见单元格和字符限额。

路径使用 POSIX 相对路径，例如 `src/main.py`。每个用户产物的相对路径的 UTF-8 长度最多 1,024 字节、32 层；每个文件名或目录名的 UTF-8 长度最多 255 字节，目录产物还要满足自己的 `max_depth`。所选目录之前的工作空间路径、平台添加的存储及归档目录前缀，都不占用该产物的相对路径额度。禁止 `..`、绝对路径、软硬链接、特殊文件、跨平台保留名称、大小写冲突和 Unicode 规范化冲突。

文本和表格在提交发布前对不可变暂存副本预检；超过声明限制时应向考生反馈原因，保留上一成功版本并允许修正。PDF/Office 渲染可延后至隔离评分器；运行环境故障不能记作考生零分。办公文档解压保护上限为 512 MiB，文件条目最多 10,000。

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
| 单个交付文件 | 200 MiB |
| 每个交付项的文件合计 | 512 MiB |
| 单个 PDF/DOCX/PPTX 评分页数 | 200 页 |
| 单个文字视图 | 2,000,000 字符 |
| 单个表格视图 | 100,000 个单元格 / 2,000,000 个结构化字符 |
| 单张评分图像 | 4 MiB |


云端提交工作空间内的路径。平台复制、校验文件并再次确认授权和截止时间后，才发布本次提交。

提交清单及其归档 JSON 的平台处理上限为 512 MiB，覆盖当前最多 30 个产物、每项 1,000 个文件及其路径和哈希元数据；这不限制交付文件内容的合计大小。


## 4. 评分计划

`tests/evaluation.toml` 使用 UTF-8 TOML，属于私有评分资料。V1.4 新构造任务沿用 `weighted_sum/v1`，为每条 rubric 增加可选的 `direction` 标记：`add` 为加分、`deduct` 为减分，省略时默认 `add`。基础分默认为 0，加分项的最高得分合计 100，减分项的最高扣分不设统一上限。`additive_deductive/v1` 是相同规则的兼容别名。下面的配置假定 `task.toml` 已声明名为 `data` 和 `report` 的产物槽位：

```toml
protocol_version = "1.4"

[aggregation]
id = "weighted_sum/v1"
base_score = 0 # 可省略；显式声明也只能为 0
max_score = 100
round_decimals = 2
on_error = "withhold_total"

[[verifiers]]
id = "quality-judge"
kind = "llm"
plugin_api = "llm/v1"
model_profile = "deepseek-text-v1"
required_capabilities = ["text", "structured_output"]
timeout_seconds = 120

[[rubrics]]
id = "trend-analysis"
title = "分析月度趋势"
criterion = "报告是否用正确的月度数据支持趋势分析；有一组正确数据支持分析得 4，否则得 0。"
inputs = [{ artifact = "report", view = "text" }]
verifier = "quality-judge"
scale_max = 4
direction = "add"
weight = 50
evidence_required = true
anchors = ["0：没有正确数据支持分析", "4：有一组正确数据支持分析"]

[[rubrics]]
id = "actionable-advice"
title = "提出可执行建议"
criterion = "报告是否提出至少一项有数据依据且明确行动对象的改进建议；满足得 4，否则得 0。"
inputs = [{ artifact = "report", view = "text" }]
verifier = "quality-judge"
scale_max = 4
direction = "add"
weight = 50
evidence_required = true
anchors = ["0：没有符合要求的建议", "4：至少一项建议符合要求"]

[[rubrics]]
id = "incorrect-total"
title = "季度预约总量错误"
criterion = "检查指标表中声明的季度预约总次数；为 4350 或未声明该数值时原始分为 0，声明了其他数值时原始分为 1。原始分表示错误程度，不是正确程度。"
inputs = [{ artifact = "data", view = "cells" }]
verifier = "quality-judge"
scale_max = 1
direction = "deduct"
weight = 120
evidence_required = true
anchors = ["0：没有声明错误数值", "1：声明了错误数值，达到最高缺陷程度"]
```

加分项最高分合计为 100；示例扣分项最高可扣 120 分，展示扣分值可以超过 100。若两项加分各得 50 分，同时发生上述错误，最终得分为 -20 分。这只是字段与计算示例，具体权重必须由出题者依据任务价值确定。

核心内容、关键研究点、重要成果适合加分；格式问题、事实错误、逻辑问题、关键数据错误等适合扣分。由人类构造题目的时候来逐条判断 rubric 更适合哪种方式，并通过 `direction` 的两个选项标记；不填写等同于选择 `add`。纯加分任务不需要新增扣分项，也不需要重写原有加分标准。扣分项的 `criterion`、`anchors` 或 `levels` 必须独立说明缺陷及严重程度：原始分 0 表示未发现所定义的缺陷，`scale_max` 表示全额扣分。平台不会自动把旧正确性得分取反。

### 评分计划字段

`evaluation.toml` 的顶层字段：

| 字段 | 类型 / 必填 | 具体含义 |
| --- | --- | --- |
| `protocol_version` | 字符串 / 必填 | 固定为 `"1.4"`，必须与 `task.toml` 一致。 |
| `aggregation` | 配置表 / 必填 | 汇总每条 rubric 的分数，字段见下表。 |
| `verifiers` | 配置表数组 / 必填 | 1–100 个判卷器配置，用 `[[verifiers]]` 声明。 |
| `rubrics` | 配置表数组 / 必填 | 1–100 个评分项或汇总组，用 `[[rubrics]]` 声明。无子项时本条独立判卷；有子项时逐子项独立判卷，父组不再判卷。 |
| `extensions` | 配置表 / 可选 | 私有描述元数据，格式与任务配置中的扩展相同。 |

`[aggregation]` 的 `id`、`max_score`、`round_decimals`、`on_error` 均必填；V1.4 通过 rubric 的方向标记进行加减汇总。旧公式字段仅用于读取原版本题包和快照：

| 字段 | 类型 / 允许值 | 具体含义 |
| --- | --- | --- |
| `id` | 字符串 | V1.4 默认写 `weighted_sum/v1`，按 rubric 方向将加分减去扣分；也接受等价别名 `additive_deductive/v1`。V1.4 不接受 `formula/v1`，旧版本公式题仍按原算法执行。 |
| `base_score` | 数字 `0` / 可选 | V1.4 两个汇总标识下均可省略，默认 0；显式声明只允许 0。旧版本保留原字段约束。 |
| `max_score` | 数字 `100` | 每题最高分固定 100 分，不限制扣分项最高扣分，也不设置最终得分下界；不是题库权重。 |
| `round_decimals` | 整数 `2` | 只在最终总分上按十进制 half-up 舍入至两位小数；正负数均适用，中间贡献不先舍入。 |
| `on_error` | 字符串 `withhold_total` | 任一必要评分失败时，总分保持 `null`，等待重试，不能算成考生零分。 |
| `formula` | JSON 表达式字符串 / 仅旧版本公式模式必填 | V1.4 禁止此字段；旧公式模式只引用已完成的 rubric 原始分，不执行 Python 或任意表达式。规则见“历史声明式算分”。 |

每个 `[[verifiers]]` 的字段：

| 字段 | 类型 / 要求 | 具体含义 |
| --- | --- | --- |
| `id` | 字符串 / 必填 | 评分计划内唯一的小写 kebab-case 标识，最多 80 字符；rubric 用它选择判卷器。 |
| `kind` | 字符串 / 必填 | 固定为 `llm`，每个最小评分项由 DeepSeek Harness + DeepSeek 判分。 |
| `plugin_api` | 字符串 / 必填 | 固定为 `llm/v1`；这是接口标识，不随协议版本改成 v1.4。 |
| `timeout_seconds` | 整数 / 必填 | 每个最小评分项（含每个 component）单次判分最长运行秒数，1–3,600；超时记评分错误。 |
| `model_profile` | 字符串 / Agent Judge 必填 | 平台登记的逻辑配置：`deepseek-text-v1` 用于文字/表格，`deepseek-vision-v1` 还允许图像/页面。 |
| `required_capabilities` | 字符串数组 / Agent Judge 必填 | **判卷器的输入能力**，不是工作空间软件清单。必须包含 `text`、`structured_output`；需要看图时再包含 `image`，并选择视觉配置。成员不重复，不得要求配置没有的能力。 |

每个 `[[rubrics]]` 的字段：

| 字段 | 类型 / 必填 | 具体含义 |
| --- | --- | --- |
| `id` | 字符串 / 必填 | 评分项唯一标识，小写 kebab-case，最多 80 字符。 |
| `title` | 字符串 / 必填 | 管理员看到的评分项名称，1–10,000 字符。 |
| `criterion` | 字符串 / 必填 | 这一项具体检查什么、怎样扣分或给分，1–10,000 字符；应能独立执行，不能只写“质量好”。 |
| `inputs` | 配置表数组 / 必填 | 至少一组 `{artifact, view}`：`artifact` 必须是已声明产物的 ID；`view` 必须是该产物声明的视图。同一组不能重复。只把这些输入交给当前判卷器。 |
| `verifier` | 字符串 / 必填 | 引用一个已声明的 `verifiers[].id`。多条 rubric 可引用同一配置，但不会共享判分会话。 |
| `scale_max` | 数字 / 必填 | 当前评分项原始分满分，必须是有限正数，例如 4。 |
| `direction` | 字符串 / 可选 | 额外的方向标记，只能选择 `add`（加分）或 `deduct`（减分）；省略默认为 `add`。既有无标记的加权题继续按纯加分理解；旧版本题包无需补写字段。旧公式题沿用原公式，不据此解释成纯加分。 |
| `weight` | 数字 / 必填 | V1.4 中为有限正数，表示本项最高加分或扣分；所有 `add` 项（含省略标记的项）合计必须恰好为 100，`deduct` 项单项及总额不受 100 限制。旧加权模式所有权重合计 100；旧公式模式固定为 0。 |
| `evidence_required` | 布尔值 / 必填 | 固定为 `true`，要求判卷器给出可核验的产物位置和证据。 |
| `references` | 配置表数组 / 可选 | 私有参考文件，省略等于 `[]`。每项 `{id, path}` 的 `id` 是本评分项内唯一的 kebab-case 名称；`path` 是 `tests/`、`solution/` 或 `fixtures/` 内真实文件的相对路径。每个文件不超过 2 MiB。 |
| `scoring` | 配置表 / 可选 | 沿用 V1.3 的独立子项计划；每个 component 单独启动 DSH + DeepSeek，不进入考生投影。 |
| `measurement` | 配置表 / 可选 | 先从冻结文件提取客观数据，供独立 Judge 核验；不能产生评分或代替 Judge，见“客观测量”。 |
| `score_gate` | 配置表 / 可选 | 仅V1.4加分项可用，声明其他无门槛加分项的得分之和必须超过某阈值，本项才产生贡献；见“得分门槛”。 |
| `anchors` | 字符串数组 / 可选 | 非空、不重复的分档描述；加分项可写 `["0：未满足要求", "4：全部满足"]`，减分项可写 `["0：无所定义缺陷", "4：最严重缺陷"]`。填写时数组不能空；省略则只按 `criterion` 判断。 |
| `description` | 字符串 / 可选 | 评分项的补充说明，1–10,000 字符，只供评分端和管理员使用。 |

模型不能只凭 `files` 路径视图判分；需要读取文字、单元格、页面、图像，或明确声明的客观测量数据。只有同时配置 measurement 时，模型评分项才可将 files 用作测量输入及证据定位。`references` 不进入考生页面。平台保存这些材料的哈希，防止评分时引用发生变化。

### 判卷器与最小评分项

评分必须由后台程序全自动驱动。平台在评测结束、冻结并选定最终提交后自动入队；常驻评分脚本领取任务，按配置遍历每个最小评分项，启动 Harness、校验返回、重试失败项、汇总分数并交由归档服务保存。不能依赖人或另一个调度 Agent 逐项发消息、选择下一项或手工回填成绩。所有执行决策来自冻结的评分计划与程序状态。

V1.3/V1.4 的每一个实际评分项必须由独立的 **DeepSeek Harness + DeepSeek** 判卷。这里的“独立”指新进程、新 home、新 session，不是同一会话中的多条消息、多个工具调用或一次回答中的多行 JSON。

- 未声明 `scoring` 的 rubric 是一个最小评分项，单独启动一次判卷会话。
- 声明 `scoring` 时，父 rubric 只负责组织与汇总；**每一个 component 单独启动判卷会话**，包括零权重前提项。父组不再额外判分。禁止把两个或更多子项交给同一会话、同一最终回答或同一共享上下文。
- 最小项只给出一个可独立判断的要求。若“数据准确、表达自然、图表清晰”等要求能够分别得分，必须拆成不同 rubric 或 components，不能藏在一段 criterion、锚点或参考文档里后合并出分。
- 单次评分运行内，每次子项重试也创建新的进程、home 和 session；仅重试失败项，已成功的兄弟项不跟着重判。一个子项失败不跳过其他子项；总时限已耗尽的未执行项须明确记录失败，整题不出总分。
- 当前最小项只能读取其配置允许的冻结产物视图、题面及私有参考资料；不能接收兄弟项的判分结果、模型回答、上下文摘要或考生对话。共享原始只读文件不等于共享会话。公共基准可以复用，但每项都必须独立读取与核对。
- `llm/v1` 使用平台配置的官方 `deepseek-flash`，只开放读取和搜索本项评分证据；不开放 shell、网页检索、编辑工具或考生沙盒。任务包不写服务地址、密钥或启动命令。
- V1.3/V1.4 不接受以 Python 代替 Agent 的计分 rubric。程序仍负责提交准入、哈希/文件/视图校验、客观测量、依赖上限及声明式算分；`python/v1` 计分接口仅为历史 V1.1/V1.2 题包兼容保留。

缺交和不合规产物由公开的前置规则处理；没有可供模型评价的输入时，不伪造会话或标成“模型已判卷”。存储完整性或视图处理故障保持评分失败。这里的前置状态处理与下述对有效评分输入逐项独立判卷须分别留档。

Agent Judge 的执行边界（全部按一个最小评分项的一次尝试计算）：

| 范围 | 上限 |
| --- | --- |
| 每个最小评分项的判分尝试 | 最多 3 次，每次新建进程、home 和会话 |
| 每次尝试的模型调用 / 工具调用 | 256 次 / 512 次，工具只含 `read_evidence` 与 `search_evidence` |
| 每次模型响应 | 最多 131,072 个输出 token，包含思考内容；原始响应流最多 64 MiB |
| 每个最小评分项的文字与参考资料 | 序列化后合计 32,000,000 字符，包含文件元数据 |
| 每次尝试的完整输入包 | 512 MiB，包含图像编码 |
| 每次发给模型的 HTTP 请求体 | 48 MiB；超过 40 MiB 时，平台将图片按原始字节上传并改用文件标识引用，保留全部文字 |
| 每次模型请求的图片 | 最多 600 张，原始图片合计最多 200 MiB；每张仍遵守产物声明且不超过 4 MiB |
| 每次尝试的评分输入、临时数据和轨迹 | 合计 4 GiB；最终响应文件最多 1 MiB |
| 运行时间 | 不超过 `timeout_seconds`，同时不能超过整题评分剩余时间；整题评分预算由平台按全部最小项及重试次数计算，不以父组数量或旧版 86,400 秒截断 |

平台软件和原生库缓存不计入这 4 GiB，但仍受判卷容器的总内存、磁盘和进程限制约束。缓存中不能存放考生文件、模型密钥或评分记录。大型评分输入使用私有磁盘临时目录，并降低并发，不把扩大容量理解为无限占用内存。

图片文件引用只改变传输方式，不改变图片内容、分辨率或评分依据。平台保存图片原始字节、SHA-256、供应商文件标识及实际模型请求，归档时能核验文件标识对应哪张图。上传文件设置一小时自动过期，评分结束时尝试提前删除；发生中断时由到期机制清理。供应商的 48 MiB 请求体和图片限制见[DeepSeek 图像输入说明](https://api-docs.deepseek.com/guides/vision/)，到期字段见[Files API](https://api-docs.deepseek.com/guides/files_api/)。

`read_evidence` 可以按一个 `id`、一组 `ids`（1–1,000 个、不重复）或 `all=true` 读取证据，三种方式互斥。大记录无损拆分为有序块，保留原始 evidence ID 和定位；每次最多返回 250,000 文本字符、8 MiB 图像，`all=true` 读取下一批未读块并返回 `remaining`。必须反复读取直到为零；平台核验所有块均已成功返回，搜索或未完成的读取不计入完整覆盖。指定 ID 可以重读原文。工具不接收任意文件路径、URL 或其他 rubric 的 ID。

长会话采用官方 DSH 会话压缩，已读取历史可生成摘要以腾出上下文；不使用直接裁剪工具结果的插件。原始分块、模型请求响应及压缩事件完整归档，最终引文仍由平台对冻结原文校验，摘要不能作为新的证据来源。压缩并不保证模型判断无误，评分质量仍须通过校准和人工复核评估。

导入时，平台根据每条 rubric 的最大文件数、视图上限、参考资料和元数据计算组合输入预算；同时预估图像去重后的运行记录容量。声明的组合超过文字、完整输入包、图片总量或运行记录预算时拒绝导入，并指出超出的范围。限制较大的单项产物，不代表可以把多个这样的输入同时交给一条 rubric。

运行时仍须复核实际输入大小。产物超过声明的视图读取上限，按 `invalid_artifact` 处理；模型请求超限、超时或轨迹未完整保存属于评分失败，整题总分保持 `null`。平台不会截断资料后假装完成判分，也不会把服务失败算成考生零分。发布前应使用交付要求允许的最大文件数量和读取量试判。

系统默认配置为：Rollout 使用 **DeepSeek V4.1 Flash / low**，每个判卷项使用 **DeepSeek V4.1 Flash / max**。两者 API 模型标识均为 `deepseek-flash`，`thinking.type` 均为 `enabled`，`reasoning_effort` 分别固定为 `low` 与 `max`。后台网关必须核验实际出站参数，不能只改显示名称或依赖 SDK 默认值；不允许静默降级。每次运行记录实际请求参数、返回模型标识和配置哈希。

模型名映射依据 [DeepSeek 官方更新说明](https://api-docs.deepseek.com/updates/)，推理参数依据 [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/)。判卷显式设置 `max_tokens=131072`，与官方 max 模式的默认输出额度一致，避免沿用 16K 限制而在生成结果前截断思考；额度与响应流上限均记录在配置中，仍受单项时限和总轨迹容量约束。参数说明见 [Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/)。thinking 模式下 temperature 不起作用，平台不把它作为有效的评分控制参数。

`deepseek-flash` 是官方模型别名。平台保存请求的别名、响应中的模型标识和配置哈希；官方未提供不可变权重版本时，不能据此声称模型权重已经固定。跨时间比较分数需要另外做评分质量校准。

### 结构化子项评分（V1.3 起）

rubric 可声明私有 `scoring`，保留 `weighted_components/v1` 的计算方式。V1.4 沿用 V1.3 的执行粒度：有 N 个 components 就有 N 个独立 DSH + DeepSeek 判卷单位。无 `scoring` 时，本条 rubric 使用单独会话并返回下文的六字段结果。

父 rubric 的 `criterion` 和 `anchors` 仅用于维护者理解汇总组，不作为多项共同判卷指令发给子项 Agent。每个 component 的 `criterion` 必须自足；共用判分约束写入其可读参考资料。平台为每次调用生成仅含当前一个 component 的评分配置，移除兄弟项、组权重和 `supports_any` 关系，将局部 `scale_max` 设为 1。父组的原始量表、方向与权重仅用于最后汇总，不把方向或权重交给 Judge。一个父 rubric 下所有 components 继承同一方向，不单独声明 `direction`；需要混合加分和减分时必须拆成不同父 rubric。扣分组的每个 component 都必须自足地描述缺陷程度，`score` 越大表示扣分越多。

```toml
[rubrics.scoring]
id = "weighted_components/v1"
groups = [{ id = "facts", weight = 0.6 }, { id = "relations", weight = 0.4 }]

[[rubrics.scoring.components]]
id = "fact"
group = "facts"
criterion = "提交材料包含正确的基础事实。"
levels = [{ id = "missing", score = 0, support_score = 0 }, { id = "correct", score = 1, support_score = 1 }]

[[rubrics.scoring.components]]
id = "relation"
group = "relations"
criterion = "提交材料用该事实支持了推论。"
levels = [{ id = "absent", score = 0, support_score = 0 }, { id = "partial", score = 0.5, support_score = 0.5 }, { id = "complete", score = 1, support_score = 1 }]
supports_any = [["fact"]]
```

- `groups` 为 1–16 组，ID 唯一，权重为有限非负数且恰好合计 1；零权重组用于独立核验前提，不增加得分。每组至少包含一个子项。
- `components` 为 1–128 项，ID 在本 rubric 内唯一；ID 使用最多 80 字符的小写 kebab-case。`group` 必须存在，`criterion` 为 1–4,000 字符。
- 每项的 `levels` 有 2–16 个唯一档位，均含 `id`、`score`、`support_score`。后两项为 0–1 的有限数值，须包含得分 0 和 1 的档位。`support_score` 单独声明该档位对后续关系的支持程度，允许局部算术错误保留方法分。
- 可选 `supports_any` 有 1–32 组依赖；每组含 1–128 个不重复 ID，只能引用本 rubric 中前面声明的子项，禁止循环。依赖仅由平台在收齐独立结果后计算，模型不得读取其他会话的分数；本项判断需要的事实仍须自己核验。
- 每个依赖组取实际支持分的最小值，多组取最大值作为上限；没有依赖时上限为 1。实际得分为 `min(score, 上限)`，实际支持分为 `min(support_score, 上限)`。
- 平台计算 `raw_score = scale_max × Σ(组权重 × 组内实际得分均值)`，使用精确有理数计算后写入结果数值；不按锚点取整，也不在子项计算阶段应用加减符号；整题汇总使用平台保存的精确分数及父项方向，最后统一舍入。

每个子项 Agent 的响应必须含 `status="completed"`、`scale_max=1`、`reason_code="evaluated"` 和 **恰好一个成员**的 `components` 数组；该成员只能是当前子项，并且只含 `id`、`level`、`feedback`、`evidence`。禁止返回其他子项、父组总分、`raw_score` 或自行应用依赖扣分。可选顶层 `feedback`、`evidence` 仍校验。子项缺失、重复、额外子项、非法档位或证据不符，均仅重试当前子项；仍失败则整题总分为 `null`。

平台收齐全部独立判断后，用原始 scoring 配置计算依赖上限、组内均分、原始量表和权重；模型不得代算或自由修改结果。即使前置项给出最低档，后续项也照常独立判卷，再由程序应用上限。失败项不会拖走其他项已完成的记录。

归档结果保存 `scoring_id`、`raw_score_fraction={numerator, denominator}` 和 `components` 计算明细（声明分、依赖上限、实际分）。另外保存 `component_results`：每项的 ID、状态、开始/结束时间、档位、理由、证据和独立 `execution_attempts`。父组的 execution_attempts 汇总全部尝试，每条含 component_id、attempt、session_id、模型配置与输入哈希、调用次数、耗时和错误。父组总分与说明由程序生成。

题目报告标记 `judging_granularity="one-component-per-session/v1"`，统计声明的最小项数、实际模型判卷完成数和失败数。零调用的缺交/无效输入不能冒充模型覆盖。每项和重试的会话身份、请求及原始响应都可独立追溯；考生不接收这些私有资料。

每个最小评分项独立调用一个判卷器；多个项可以引用同一个判卷器配置，每项和每次重试仍使用独立会话。Agent Judge 可以多轮读取证据再返回结果，平台同时保存 Harness 会话轨迹、模型请求响应和实际模型标识；这些资料只供管理员复核。平台可向 Agent Judge 提供只读定位标识：`evidence_ref` 指向当前文件视图；文字视图按顺序提供 `text_segments = [["t1", "原文块"], ...]`，每块最多 800 字符，逐块拼接就是完整原文。Judge 可返回 `{evidence_ref, locator_ref}` 选择文字块或表格位置，平台再补全路径、哈希和真实引文。原文不重复传输、不改写换行；最终结果中的 `text.quote` 仍须逐字存在于冻结文字视图中。

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
| `raw_score` | 有限数字，范围 0 到该 rubric 的 `scale_max`，两端都允许。加分项越大加得越多，减分项越大扣得越多；减分项不返回负原始分。 |
| `scale_max` | 数字，必须与当前 rubric 的原始满分完全一致。 |
| `reason_code` | `evaluated` 表示正常判分；`invalid_artifact` 表示产物内容无效，此时原始分必须为 0。 |
| `feedback` | 1–12,000 字符的非空文字，简要说明为什么给这个分数，仅供管理员查看。 |
| `evidence` | 1–200 项的证据数组，每项包含 `artifact_id`、`path`、`sha256`、`view`、`locator`；分别指向本次输入的交付项、文件相对路径、文件哈希、读取视图和具体位置。定位方式见下表。 |

脚本异常、超时、模型不可用、证据缺失属于评分失败，必须单独记录，不能转换成考生零分。Agent Judge 的内部工具可以使用平台分配的证据标识；平台将其解析成上述统一结果后再校验和归档。

判卷器成功返回时，`raw_score` 必须是有限数字，范围为 0 到该 rubric 的 `scale_max`（包括两端）；返回的 `scale_max` 必须与 rubric 完全一致；`feedback` 必须是非空文字；`evidence` 必须是数组。每条证据都要引用当前输入中真实存在的产物、相对路径、视图、哈希和定位信息。未声明 scoring 时，返回对象的顶层字段多一个、少一个或类型不对，都按判卷失败处理；结构化子项响应按前述专用接口校验。

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

V1.4 使用 `weighted_sum/v1`（兼容别名 `additive_deductive/v1`），初始基础分为 0。先将省略的 `direction` 视为 `add`，再将每个 rubric 的非负原始分换算为加分或扣分数额：

```text
本项数额 = raw_score / scale_max × weight
加分项 contribution = 本项数额
减分项 contribution = -本项数额
最终得分 = half-up 保留两位小数（Σ加分项数额 - Σ减分项数额）
```

所有加分项的 `weight` 必须恰好合计 100，减分项的单项和合计最高扣分均不设 100 分限制；每项 `weight` 仍必须是有限正数。允许没有减分项。`aggregation.max_score` 固定为 100，最终得分最高为 100，**可以为负分，不做 0 分下界截断，也不另作映射**。采用精确分数计算中间值，只在最终总分执行十进制 half-up 舍入；例如 1.235 → 1.24，-1.235 → -1.24。负分是有效成绩，不能当成缺分或评分失败。

缺失或无效产物继续按 `zero_dependent_criteria` 处理：依赖它的加分项和减分项原始分与贡献均为 0；不依赖它的评分项正常判卷。整项缺交与已提交材料中定义明确的错误要分别处理，不因方向变化把缺交自动记成最大扣分。任一必要评分环节失败时，总分为 `null`，并在管理员结果中写明失败原因。

管理员评分明细保留评分计划中的方向、最高加/扣分、非负原始分和带符号的 `contribution`，使逐项贡献之和可复核为最终得分；模型仍只输出当前项原始判断，由平台应用加减方向。

已有 V1.1/V1.2/V1.3 的无方向标记 `weighted_sum/v1` 题包和快照继续作为纯加分题执行：`contribution = raw_score / scale_max × weight`，所有权重合计 100，总分范围仍为 0–100。无需改题面、rubric、判卷器或题包文件，也无需升级版本或改变包哈希；旧版本继续按原版本校验和运行。已有 `formula/v1` 保留下节的原算法，不能把含扣分或门槛的公式自动当成纯加分。V1.3 已使用 `additive_deductive/v1` 的题包也保留自身规则。不自动迁移旧题包、历史成绩或正在进行的评测。

### 得分门槛

为保留任务既有的先决要求，加分 rubric 可显式声明 `score_gate = { rubrics = ["analysis", "evidence"], min_score_exclusive = 10 }`。平台仍逐项独立判分，等所有结果有效后，精确计算所列加分项的贡献之和；严格大于10时保留本项原贡献，否则本项贡献归零。原始裁决不改写，归档同时记录来源分数、精确分数、阈值、是否通过及归零前贡献。不向Judge传递此门槛、其他裁决或权重，也不让模型重算总分。

该字段只允许V1.4的加分项使用。`rubrics`必须含1–100个唯一的其他加分项ID；来源项不能自身带门槛，禁止自引用、循环及链式依赖。阈值须为非负有限数并小于来源项最高得分之和。任一评分项失败时仍保留空总分，不能把失败视为门槛不通过。未声明门槛的题包及历史版本算分完全不变；加分满分合计100及允许负分的汇总规则继续适用。

### 历史声明式算分

`formula/v1` 仅用于兼容 V1.3 已有题包和快照的扣分、乘法折扣、硬门槛和相对基线计分；V1.4 新题不使用此模式。每个实际判断沿用所属协议版本的判卷器与会话规则，程序只在全部结果有效后做算术。不得把算式或其他 Judge 的输出交给某个模型再次决定总分。

formula 是 JSON 字符串：数字为常数；字符串为本计划的 rubric ID，取该项 raw_score（有精确有理数记录时使用该记录）；数组为 `[操作, 参数...]`。允许 add、mul、min、max（1–100 个参数），sub、div（两个参数），以及 round（数值和 0–8 位小数）。round 的整个数值参数子树按 Python 浮点算术及 ties-to-even 舍入执行，以保留旧脚本的运算次序；不能仅把有理数最终转为浮点后舍入，因为 `round(0.7 / 112, 4)` 与先精确计算分数的结果可能不同。例如 `formula = '["mul",100,"correctness","validity"]'`，两个独立项的满分均为 1，表示有效性门槛乘正确度。

表达扣分可用 `["dedup-severity","n1","n2",...]`：每项只能返回 0/1/2，非零项必须提供原文引句；先按严重度降序、再按 ID 排序，重复或相互包含的引句不重复扣分。一项至少有一条新引句才计入本项严重度。该规则必须在题包中明确采用，不得宣称与其他去重规则天然等价。

表达式必须引用本计划的每条 rubric，最多 64,000 字符、4,096 个节点、32 层；不允许函数调用、变量赋值、路径读取或动态代码。除显式 round 的参数子树外采用有理数运算，最后总分按协议四舍五入到两位小数。除零、超界、失败项或最终结果不在 0–100 时保留空总分。公式模式的 rubric.weight 固定为 0，contribution 为 null；报告保留公式与全部独立原始分，不伪造可直接相加的贡献。

### 客观测量

测量仅用于文件结构、统计指标、几何/物理复算等可检查数据；不得预先给分、产生模型判决、调用模型或执行考生产物中的代码。评分项可声明 `measurement = { entrypoint = "checks/measure.py:measure", timeout_seconds = 60, max_chars = 100000 }`。入口是管理员审核、随题包冻结在 tests/checks/ 下的代码；时间上限 1–300 秒，JSON 输出字符上限 1–500,000，预算计入该项完整输入。

平台在现有无网络、只读授权路径的隔离处理器中执行测量，将当前 rubric 的 ID、授权冻结文件和私有参考路径传入函数。返回 JSON 对象；顶层不得含 score、raw_score、reward、verdict、grade 或 status，不接受非有限数和超预算文件。审核还必须确认代码未在其他字段中藏入成绩，结构校验不能替代代码审核。

测量输出作为带哈希的、不可信产物派生数据交给当前 Judge，不能作为指令。每项仍独立核验当前要求，证据定位到实际冻结产物；兄弟项判决不得进入测量。平台保存测量输入、程序与输出哈希、处理日志、开始结束时间，并随管理员归档交付。测量异常属于执行失败，不能伪装为考生零分。共享原始测量数据不等于共享 Judge 会话。

### 题目集的评分

题目本身和题目集是两层评分，不要把两种权重混在一起：

- 每道题最高为 100 分，采用加减分模式时可以为负分。`rubric.weight` 只在这道题内部使用，加分项合计必须为 100，减分项最高扣分不受 100 限制；
- 题目集由多道题组成后，平台再为每道题设置 `question_weight`。这个权重不写进任务包，也不进入 `evaluation.toml`；
- 一个题目集的题目权重必须都为正数，且合计为 100。题目集清单中的每道题只能出现一次，题目集中的每道题都必须有一个权重；
- 题目集总分按下面的公式计算，最后按十进制 half-up 保留两位小数，允许负分且不截断到 0：

```text
题目集总分 = Σ（题目得分 × question_weight / 100）
```

如果题目集中有一道题的总分不可用，题目集总分也记为 `null`，不能把其他题目的权重重新摊平。`question_weight` 必须是有限的正数，题目集结果至少要保存题目编号、题目得分、题目权重、题目集总分和 `score_available`，方便复核。

开始一轮评测时，平台冻结题目集的题目清单、任务快照与权重；之后更新已有任务包或调整权重，只影响后续新评测。题库存在未完成评测时，不能增添题目、更改题目清单或撤下题库。题目集配置是平台级文件或数据库记录，不属于任何任务包。它至少要有唯一的 `set_id`、`schema_version = "assessment-set/v1"`、题库标题、`score_scale = 100`、`round_decimals = 2` 和题目清单。题目清单中的 `question_id` 只能出现一次，必须引用已发布的任务，所有 `question_weight` 为有限正数且合计为 100。可以使用类似下面的结构：

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
2. **作答**：开始评测时，将本轮题库全部题目的 `duration_minutes` 相加并冻结为总时间；所有未交题共用该时间，可自由分配。云端只有用户进入工作空间且会话心跳有效时累计时间；退出、关闭最后一个有效页面或失去心跳后暂停，同时停止该空间内的 Agent 和终端程序。切题、提交一题、同轮重开单题或更新题包均不重置总时间。多道题共享本轮工作空间。已有评测沿用创建时冻结的计时规则，不因平台升级改写历史条件。
3. **选择交付物**：用户为每个交付项选择文件或目录。此时只是页面选择，没有提交副本，也不触发评分；原文件修改后，提交时读取的是修改后的实际内容。
4. **整题提交与修订**：每次接收全部所选交付项，核验授权、路径、格式、数量、容量、读取预算与哈希，再保存不可变副本。主动提交须包含所有必交项。成功后可继续工作并重新提交，历史版本保留；失败不覆盖已有成功版本。同一请求编号及内容重试只产生一份记录，编号复用于不同内容必须拒绝。仅修改工作空间文件不会改变已保存的提交。
5. **总时间耗尽**：服务端原子结束整轮，选定每题最后一次成功提交；未提交的题目生成空清单并按缺交处理。最后版本选定后统一排入评分队列。开始上传不等于提交成功；结束后才完成的在途上传不能替换最终版本。工作空间文件和页面选择不自动纳入评分。
6. **主动结束评测**：用户二次确认时展示最终提交状态；尚有题目未提交时须明确确认缺交计分（平台可禁止提前缺交结束）。服务端重新核验题目清单及提交版本；状态变更则要求刷新确认。原子选定每题最后成功版本、关闭全部作答并安排评分；发生失败不能只关闭一部分。随后停止工作空间写入、采集全部可获取轨迹、等待评分和生成归档；核验归档完整后才清空沙盒并恢复基线。
7. **重做与重判**：重做只能由管理员开放新作答，沿用原作答环境；同轮重开单题只继承题库剩余总时间，不能重新授予时间。总时间耗尽后须另开独立评测，云端须先完成原轮归档与重置。重判保留原评分运行和新运行。管理员可看详细 rubric，考生只看整题总分和公开状态。

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
    ├── request.json                # 当前最小项的 Harness 指令与只读证据包
    ├── response.json               # Agent Judge 最终响应、会话 ID、模型与用量
    ├── result.json                 # 校验后的单项或单 component 结果
    ├── harness-files.json          # Harness 原始文件到归档文件的对应表
    ├── harness-*                   # 会话 JSONL、事件、工具调用与模型往返原始文件
    ├── processor-request.json      # 受控视图处理请求，如适用
    └── processor.log               # 视图处理日志，如适用
```

结构化子项使用 `<rubric-id>/components/<component-id>/<execution-number>/`，普通原子 rubric 沿用上图路径。index 和 metadata 必须同时记录 criterion_id、component_id（如适用）及 attempt，并校验身份一致；同名子项在不同父组下不得覆盖。历史 Python 记录保持原路径。中途失败时可能没有 `result.json`，但必须保留已获取的证据及失败原因。`harness-files.json` 记录原始路径和归档路径，不能假定 Harness 内部会话文件始终使用同一个名称。原始证据包括会话 JSONL、SDK 事件、`tool-calls.jsonl`、Harness 原生图像附件、每次模型请求/响应、HTTP 状态与完整性记录，以及运行日志。

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
4. 新题基础分为 0，每项方向为 `add` 或 `deduct`（省略按 `add`），加分项最高得分恰好合计 100，扣分项最高扣分均为有限正数；判卷器入口、输入能力、超时和网络权限符合约束；
5. 独立评分项在正确、部分正确、错误、缺交和恶意文件样例上返回可解释结果；
6. 每个原子 rubric / component（含零权重项）都有独立 DSH + DeepSeek 进程、home、session；同项重试也独立，已成功项不重跑；
7. 每个 `required = true` 的产物至少被一条 rubric 使用；如果产物只收集、不计分，应明确设为 `required = false`；
8. 考生可见内容不包含 rubric、权重、参考资料、模型配置、私有路径或凭据；
9. 重复提交、失败不覆盖、提交与结束并发、最后版本选定、结束后统一评分、到时缺交、旧版兼容、重判和归档均经过验证；
10. 结果包可以独立验证，缺分为 `null`，缺失和失败原因可区分；
11. 用不包含任何用户资料和任务文件的基线创建新工作空间。

`examples/service-research/` 是一个可导入的示例题包，用来演示多产物、文字与视觉 Agent Judge，以及 4 个加分汇总组、1 个减分汇总组下 16 个独立评分会话的配置。它的材料和数值只属于示例，不是协议字段，也不应复制到正式任务中。

## 版本兼容与历史保全

V1.0、V1.1、V1.2、V1.3 文档与已发布标签保持原样。V1.4 是独立版本；新建 V1.4 题包的 `task.toml`、`tests/evaluation.toml` 和提交清单使用相同版本，并记录新的 task_revision 与包哈希。框架可并存读取 V1.1/V1.2/V1.3/V1.4，不因框架更新强制升级已有题包，不用新默认值改写运行条件、提交、分数或归档。

旧版无方向标记的加权题默认按纯加分题继续测评，原题面、rubric、判卷器、协议版本和题包哈希均可保持不变。V1.4 的方向只是 rubric 的附加标记，省略表示 `add`；不要求把原有加分条目改写成缺陷描述，也不要求增加减分项。已有公式题仍按原公式执行；若要取消其中的扣分或改成 V1.4 的加减汇总，须由人类确认新评分含义，另建修订并验证，不能声称只补标记就保持了原行为。

V1.4 沿用 V1.2/V1.3 的提交规则，冻结 `finalization=last_successful_submission_at_assessment_end`、`deadline_action=freeze_latest_or_missing`、`grading_start=assessment_end`。旧 V1.1 作答保持创建时的一次提交规则。升级协议需开始新一轮，不能在进行中的评测中切换规则。

V1.2 及后续版本提交记录保存 `revision`、`previous_submission_id` 与 `selection_state`：最新成功但尚未结束为 provisional，更早版本为 superseded，结束选定版本为 final；已有旧提交视为 final。所有版本的原始清单和文件不可变。只有 final 版本进入评分与题库总分，其他版本保留在整轮归档及单题产物索引，禁止通过重判入口提前评分或改变最后版本选择。

管理员报告必须区分内容已评、材料无效、缺交和评分服务异常，并记录实际 LLM 执行情况。流程 completed 不能解释成模型已读取并评价全部内容。新协议下复评旧产物应另建比较记录，不覆盖原评分或历史归档。

V1.4 沿用 V1.3 的 Linux 云工作台环境，compatible_profiles 必须为 ["linux-office"]；协议不定义独立桌面连接、桌面提交或连续计时入口。历史 V1.1 环境标识只用于原资料的读取和复核。

V1.3 引入逐子项独立判卷；V1.4 沿用该执行方式和 V1.2 的容量、作答与提交生命周期，并明确 rubric 的可选加减方向及其默认值。旧 V1.2 的结构化 rubric 仍按该版本的组级会话执行，旧 V1.1/V1.2 的 Python 判卷器也继续受支持。继续评测旧题不要求将其转为 Agent Judge。

主动升级旧题到 V1.4 时，须同步 task 与 evaluation 的版本并新建修订；若来源早于 V1.3，还须按 V1.3 起的执行约束，将 Python 计分项或隐含多项要求改成原子 Agent 评分项并重新校准。已经满足这些条件的 V1.3 加权题可保留原题面、权重、criterion 与档位，不写方向即为纯加分。只有人类决定将某项改为减分时，才为该项写 `direction = "deduct"`，并确认 criterion 与档位自足地描述缺陷程度；平台不会取反旧原始分。版本升级与评分含义改变都须保存新 task_revision 和包哈希，原包及历史结果继续保留。

V1.4 对应独立的 v1.4.0 发布快照；同版本后续维护更新进入默认分支，不移动已有标签或替换 Release 附件。协议发布、框架源码支持、线上部署和实际题包迁移分别核验。

总判卷时限必须按各组的子项数量 × 每项单次时限 × 最多三次尝试估算，并计入视图处理和实际并发。不能沿用只有父组数量的预算，也不能用合并子项会话节省调用数。框架在每个父组内串行执行子项，父组之间受统一并发上限约束；大图文输入按原有规则降低并发。

服务进程崩溃后的整次评分恢复或管理员主动重判属于新的评分运行，须另建运行编号和证据目录并保留原记录；不能把这种整次重跑冒充某个子项的一次重试。
