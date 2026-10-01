# 数据描述符（Scientific Data Data Descriptor）编辑视角检查清单

用于投稿前以"编辑/审稿人"身份自查数据资源稿。每项都注明"编辑为什么在意"与"本项目的处置"。

## 结构与硬性限制
| 项 | 要求 | 检查 |
|---|---|---|
| 章节顺序 | Background & Summary → Methods → Data Records → Technical Validation → Usage Notes → **Data Availability → Code Availability → References** → Author Contributions → Competing Interests → Acknowledgements → Funding | 本用户曾把 References 放到 Data Availability 之前，**被编辑判为不合规** |
| Ethics | 作为 Methods 的子标题，不单独立节 | 已并入 Methods |
| Funding | 独立子标题；Acknowledgements 不用于陈述资助 | 已拆分 |
| 标题 | ≤110 字符（无冒号括号更稳） | 105 字符 |
| 摘要 | ≤170 词 | 159 词 |
| 缩写 | **首次出现处定义，禁止 "Abbreviations:" 小节**（期刊明文禁止） | 已删除该小节、改为行内定义 |
| 不呈现研究结论 | Technical Validation 只报数据质量/一致性；"descriptive or summary statistics" 不受欢迎 | 加总起句声明"本节仅报告数据质量与一致性、资源不作生物学结论"，把突变率/拷贝数/单细胞计数重述为**注释层属性** |

## Data Records / Data Availability（最常被抓）
- Data Records 要有**数据字典级说明**（文件、格式、字段含义），不能只列文件夹名。
- 文件数、SHA 条数、补充表编号、目录数一律**从 manifest 现算后回填**（手写必过期：本项目经历 82→86→101→107 四轮追改）。
- **Data Availability 必须重复 accession 清单**（不能写"见 registry CSV"）：26 个病例-对照 GSE + 被排除/外部验证系列 + CELLxGENE collection UUID + GEO 单细胞系列 + GDC 项目 ID（TCGA-LUAD/COADREAD/STAD/PAAD/LIHC/ESCA）。
- 许可：数据 CC-BY-4.0（不接受 -NC/-SA）；上游数据条款需点名（GEO 条款、GDC 开放条款、CELLxGENE 条款）；声明无新采集样本、无受控数据。
- DOI：数据仓库 DOI 未出时用显式占位符并在交付说明里标为唯一阻塞项（本用户接受占位符，但要求交付文档写清）。

## Code Availability
- 不能只说"archived in the deposit"：要写**仓库 URL + 版本 tag**、包内代码目录（如 `11_code/`）、
  `run_order.md`、环境版本清单；并**诚实说明脚本内路径需按 README 调整**（否则"端到端可复现"是空话）。

## 表格与补充材料
- **Table 1 必须出现在正文**（编辑会检查"每个元素在主文被讨论"）：本项目原先只在 SI，已内嵌为三线表并加引用。
- 超大表（数百行明细）**移出补充表**、改为"摘要 + 仓库路径引用"（期刊明确不建议把 oversize 表当 supplementary）。
- SI 需为 **PDF**；同一批表另存 machine-readable（docx/csv）随包。
- 图：PNG 300 dpi + **字体内嵌的 PDF**（R 用 `ggsave(..., device=cairo_pdf)`）；图内不放图例与总标题；
  图注须说明误差/统计处理（中位横杠含义等）。

## 作者信息与投稿信（最容易被"技术性退稿"的一类）
- 必填：作者姓名 + 单位 + **通讯作者邮箱** + ORCID；关键词。
- **署名口径要与用户既有惯例核对**：本项目正文按 [First Author] + corresponding@example.com 写，
  但用户其它项目要求"落款只署通讯作者 [Corresponding Author]"——两处口径冲突时必须先问，不要自行拍板。
- **Cover Letter** 单独成文并进投稿包：一句话说明稿件类型、资源规模、差异化（可比性被量化而非假定）、
  数据/代码可用性、无伦理问题、未一稿多投。

## 投稿包内容（投稿 ZIP ≠ Zenodo 包）
- 投稿 ZIP：正文 docx/pdf、Cover letter、SI PDF、同批表格 docx、图例 docx、图 PNG+PDF、英文 `00_READ_ME_FIRST.txt`。
- **内部文档（评审处置、状态与待办、上传指南）绝不进投稿 ZIP**——内部语气 + 过期数字会被编辑视为不规范。
- Zenodo 包：数据 + 代码 + manifest + SHA-256 + 复用示例 + 示例期望输出。

## 仍会被追问的可选加固（提前准备说辞）
- 单细胞细胞数阈值只做了一档（≥10/供者）→ 备好 20/50 的梯度或说明为何单档足够。
- 多重检验策略（家族 BH vs 全局 BH）两套数字都给出，并说明显著数差异来源。
- 跨队列一致率（如 68%）要给出"不一致情形点名"，避免被外推。
- SI 加目录页；大表说明跨页如何处理。
