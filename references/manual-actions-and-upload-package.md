# 投稿包组装 + 人工项"点哪里填什么"指南（模板）

> 本用户偏好：**自解释文件名**（如 `★投稿上传-就选这个_v11.zip`）、**桌面整洁**、**逐项可执行**、
> 凡是不能由机器代填的一律列成"人工项"并给出示例文本。每次宣布"包已就绪"时，必须同时给出人工项清单。

## 1. 一次性上传 ZIP 的结构（内部名即用途）
```
★投稿上传-就选这个_v<NN>.zip
├─ 00_上传顺序.txt                     # 1..N 步，对应投稿系统各屏
├─ 00_先看这个_人工项填写指南.md
├─ 00_先看这个_投稿清单.md
├─ 00_先看这个_送审自查包.md
├─ 01_Manuscript/01_Manuscript_v<NN>.docx / 02_*.pdf / 03_Cover_Letter_v<NN>.txt
├─ 02_Figures_TIFF/Figure1..N.tif, FigureS1..n.tif, figure_specs.csv
├─ 03_Supplementary_Tables/TableS9_evidence_matrix_v<NN>.csv, …
└─ 04_修改说明_v<NN>.md
```
打包时**按版本号过滤**：`_v9`/`_v10` 旧表不要混进新包（本会话出现过旧证据矩阵被夹带）。

## 2. 人工项填写指南（本用户认可的写法）
逐屏、从"点哪里"写起，含**可直接粘贴的示例文本**：
1. **投稿前自检**：给出可复制的命令（一致性脚本），并写明通过标志（`RESULT: PASS`）。
2. **作者名单 + CRediT**：给作者行与 CRediT 两个可直接改的样例；注明"只有真实参与者才写、不放工具名"。
3. **Cover letter 抬头**：给 5 行模板（日期 / Dear Editor / 期刊 / 稿件类型 / ORCID），并强调**正文段不要改**。
4. **图件上传对照表**：系统里的 "Figure N" ↔ 本地 `FigureN.tif`；说明同一图多面板怎么传；禁止中文名、禁止 PNG+PDF 混传。
5. **投稿系统逐屏**（Springer Nature 为例）：Article type → Title/Abstract（注明摘要词数上限与超限处理）→ Authors → Upload files（顺序）→ **AI 使用问答** → Declarations（Competing interests = None；Data availability = GitHub 链接）→ Reviewers → Approve & Submit。
6. **AI 使用问答备答**（如实作答 Yes）：
   > Large-language-model tools were used to assist with parts of the data-analysis scripting (R/Python), with drafting and editing of the manuscript text, and with editorial review of the analyses. All statistical analyses were verified against the public source data by the author, and the author takes full responsibility for the content of the manuscript.
   （正文里不写 AI 声明 ≠ 系统问答可以答 No；系统记录不可改。）
7. **提交后**：确认收件邮件、把 Manuscript ID 登记进 `04_评审记录与报告`。

## 3. 送审自查包（给第三方/审稿人）
一页讲清四件事：① 本版相对上版改了什么（附 ERRATA 文件）；② **每个数字来自哪张表、哪个脚本**（溯源表）；③ 最可能被追问的 5–6 问 + 现成答案（含"为什么两种估计器差这么多"）；④ 复现命令块（含所需 Python/R 环境）。
目的：让外部审查直接定位，而不是重新猜。

## 4. 收工话术
宣布完成时给出：本版关键口径表（勿回退的数字）、文件清单（01–06 + ZIP 路径）、**人工项 4–5 条**、
以及一句建议（送第三方再审一轮）。不要只说"已完成"。
