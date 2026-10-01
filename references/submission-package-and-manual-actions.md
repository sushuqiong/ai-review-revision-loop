# 投稿交付物打包 + 人工项指南（Submission Package & Manual-Action Guide）

> 触发：稿件经过 N 轮"AI 审稿→修复"后已定稿（vN），需要交付**可直接上传**的文件包；
> 用户为非开发者，只有作者名单/Cover 抬头/AI 问答这类必须本人做的事留给他。
> 目标：把"能自动化的全做掉"，剩下的写成分步可照做的指南（点哪里、填什么、示例文本）。

## 1. 图件：投稿规格与常见坑

- **规格**：TIFF / 300 dpi / 单栏约 8.5 cm、双栏上限约 **17 cm**。像素换算：17 cm @300 dpi ≈ **2008 px**。
- **归一化脚本套路**（PIL，`Image.LANCZOS`）：
  ```python
  TARGET_PX = 2008                       # 17.0 cm at 300 dpi
  if w > TARGET_PX: im = im.resize((TARGET_PX, round(h*TARGET_PX/w)), Image.LANCZOS)
  im.save(out, format="TIFF", compression="tiff_lzw", dpi=(300,300))
  ```
  同时输出 `figure_specs.csv`（file, px_w, px_h, cm_w, cm_h, size_MB, dpi）——审稿/投稿系统问规格时直接给。
- **流程图/网络图最常超宽**：不要用 `-Gsize=6.7,4.2!` 强制长宽比（会把内容压扁成 17×2.5 cm 不可读）；
  正确做法是**改布局**（把横向并行层改成纵向堆叠，删 `rank=same`），再用默认 dpi 渲染后归一化。
- 若投稿系统只收 PDF 图：保留一份同源 PDF（ggplot `ggsave(.pdf)` / graphviz `-Tpdf`），与 TIFF 同时交付。
- 同一张图的多个面板按面板名交付（`Figure2A.tif`、`Figure2B.tif`），与正文图注中 (A)/(B) 一一对应。

## 2. 上传 ZIP：自解释命名 + 内部顺序说明

- ZIP 名对用户自解释，例如 `★投稿上传-就选这个_v{NN}.zip`（放在项目父目录，用户一眼能找到）。
- 内部结构固定，并**每个关键动作都配"先看这个"**：
  ```
  00_上传顺序.txt                     ← 逐步上传顺序 + 每步对应文件
  00_先看这个_人工项填写指南.md
  00_先看这个_送审自查包.md
  00_先看这个_投稿清单.md
  01_Manuscript/01_Manuscript_vNN.docx | 02_Manuscript_vNN.pdf | 03_Cover_Letter_vNN.txt
  02_Figures_TIFF/Figure1..N, FigureS1..N + figure_specs.csv
  03_Supplementary_Tables/            ← 用补充表正式编号命名
  04_修改说明_vNN.md
  ```
- **打包时必须过滤被取代的版本**：`... and "_v9" not in f and "_v10" not in f`（本项目首包就混进了
  `TableS9_evidence_matrix_v9.csv`）；并把**冻结表导出的表重命名为正式补充表编号**
  （`v11_evidence_matrix.csv` → `TableS9_evidence_matrix_v11.csv`）。
- 上传文件**不要用中文文件名**（投稿系统常报错），中文只留在"给用户看的指南"里。
- ZIP 通常是二进制产物，不进 git 仓库；仓库里放生成脚本 + 清单即可。

## 3. 人工项指南（结构模板，用户按步照做 ≈20–30 分钟）

顺序即优先级，每步写清"打开哪个文件/点哪里/填什么/示例文本"：

1. **第 0 步 投稿前自检**：给一条可复制命令跑一致性脚本（如 `python tests/check_vNN_consistency.py`），
   并要求"看到 RESULT: PASS 再往下；FAIL 把输出发我"。让用户不必判断数字。
2. **作者名单 + CRediT**：给可改的示例块（作者行 + 单位 + 通讯 + CRediT 逗号列表），
   附一句"只有真实参与者才写；不写 AI/工具名"。
3. **Cover letter 抬头**：给 5 行模板（日期 / Dear Editor 或编辑姓名 / 期刊名 / Manuscript type / ORCID），
   并明确"正文段落不要动"。
4. **图件上传对照表**：投稿系统的图名 ↔ 本地文件名（含面板与补充图），并注明规格表位置。
5. **投稿系统逐屏步骤**：Article type → Title/Abstract（提示摘要词数上限与超限处理）→ Authors
   （提醒共同作者会收确认邮件）→ Upload files（按第 2 节顺序）→ **AI 使用问答** → Declarations
   （Competing interests / Data availability + 代码仓库 URL）→ Reviewers → Approve & Submit（截图留档）。
6. **AI 使用问答备答文案**（Springer Nature 系为强制必答，与正文是否写 AI 声明无关；如实作答）：
   > Large-language-model tools were used to assist with parts of the data-analysis scripting (R/Python),
   > with drafting and editing of the manuscript text, and with editorial review of the analyses.
   > All statistical analyses were verified against the public source data by the author, and the author
   > takes full responsibility for the content of the manuscript.
7. **提交后**：确认收到 Submission received 邮件；拿到 Manuscript ID 后回填到清单顶部并发给助手登记。
8. **禁令一条**：不要自行改动正文数字；要改先说句子，助手同步改表/图/一致性测试。

## 4. 非开发者协作约定（本项目实证有效）

- 文件名自解释（`★…就选这个`、`00_先看这个_…`），并在回复里说明"先看哪个"。
- 出错时让用户截图，助手用离线 OCR 读图（vision 模型不可用时也可行）。
- 交付回复给"结论 + 文件位置 + 还剩几件事(几分钟)"，不要把过程日志堆给用户。
- 三处镜像（工作目录 / 投稿包 / Git 仓库）**逐文件内容探针**核验，不要假设 `cp` 成功——
  本项目实际出现过 md 静默未覆盖、主包比工作区旧一个版本。

## 5. 返修（Revision）与首次投稿的差别

- 系统路径不同：Author Main Menu → **Submissions Needing Revision** → 该稿件 → **Revise Submission**（不是 New Submission）。
- **真正必需的是两份**：Revised Manuscript + **Response to Reviewers**（逐条回复是本轮核心交付物）。
  Cover Letter 栏位通常仍在但**非必需**；若正文因审稿人要求的新分析明显加长，**建议仍传**并在信里
  主动说明增幅（"三项新增分析约 +19% 篇幅，如需精简可将细节移入补充材料"），比让编辑事后发现好。
- **一个栏位一个文件**：Manuscript / Response to Reviewers / Title Page / Cover Letter / Figure Legends /
  Figure 1..N / Supplementary Material / Highlights / Declaration of Interest 各占一栏；
  **不要把所有图塞进一个 Word**。补充图也一张一个文件（优先 `.tiff`）。
- 各刊栏位名略有差异，找不到就投到最接近的栏位或 Supplementary Material，编辑不会因此退稿——
  这句必须写进指南，否则用户会卡住。
- 附"点哪里"级步骤（用户非开发者）：登录 → Submissions Needing Revision → Revise Submission →
  一路 Next/Proceed 到 **Attach Files** → 逐文件 `Choose File` + 选 **Item Type** + `Attach This File` →
  `Proceed / Build PDF` → **逐页翻查**（正文是新的、回复信在、换过的图生效）→ `Approve Submission`。
- 图换版时（如只替换 Figure 5F）：交付说明必须写"**直接传 `..._REVISED.pdf`，不要再用原图**"，
  并另附 `preview_*.png` 供用户自查 → 见 `references/composite-figure-panel-replacement.md`。
- 原稿格式硬要求每次都要复查（Elsevier 常见）：**Highlights 每条 ≤85 字符**、上标数字引用、
  正文无残留方括号编号、观察性研究须随附 STROBE 清单。

## 6. 交付说明本身也要给 Word（本用户偏好）

- 用户**不开 .md**。除 `.md` 原件外必须同时产出同名 `.docx`（分级标题、表格、加粗、`code` 全保留），
  并在回复里说"先看这个 .docx"。
- 生成后自检：`len(doc.paragraphs)` / `len(doc.tables)` 与 md 规模相称；关键短语做 `in` 探针
  （"上传清单""已核实""怎么点"）。
- **字数类数字必须与标题页一致**（本项目 README 先写 5,326、标题页 5,320 → 交付前必须对齐；
  这类不一致用户一眼就会看到）。
- **自写 md→docx 解析器的表格三坑**：
  1. 单元格里的**转义竖线 `\|`**（如 `\|logFC\|`）会让朴素 `split("|")` 多切出列 → 名列数 > 表头列数 →
     `IndexError` 崩掉整个转换。对策：解析前改写（`\|logFC\|` → "logFC 绝对值"），
     并让表格处理**按表头列数截断补空**：`row = (row + [""]*ncol)[:ncol]`。
  2. 分隔行 `|---|---|` 必须整行跳过（判据：所有单元格字符集 ⊆ `-: `）。
  3. **不要只看"文件已生成"**：本项目第一次转换静默用了**旧版 md**（脚本在表格处抛异常，
     错误被 `| grep` 吞掉，输出被误读为成功，docx mtime 一直没变）。必须打印计数并核对 mtime。
