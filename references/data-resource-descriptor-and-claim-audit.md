# 数据资源稿（Data Descriptor）与“声明 vs 交付物”审计

来源：2026-09 EGFR 跨疾病转录组资源 v12→v13（多轮 AI 审稿 + 复算核查）实战。适用于任何“把公共数据整理成可复用资源”的稿型（Scientific Data / Data in Brief / GigaScience 等），也适用于普通论文的终检。

> **投稿前最后一道闸**：三路独立冷读（编辑合规 / 统计方法 / 数据工程，3 个上下文全新的 subagent，只给文件与只读权限，必须带证据）——派发模板、指令要点、汇总处置纪律与高命中检查点见 **cold-review-delegation-protocol.md**。实测：作者自审 8+ 轮、历轮 AI 意见全部闭环之后，冷读仍抓出 6 条 Blocker（含“取中位不排序”“自引用校验值陈旧”“示例跑不通”）。
>
> **引用装置 / 编辑初审项 / 敏感性交代**：见 **reference-apparatus-and-editor-pass.md**（参考文献从"指针"升级为 52 条可解析条目；PubMed+Crossref 双源元数据与严格校验；首现顺序编号的机器核验；数据资源稿的作者块/attributions/内嵌 Table 1/Data Availability 重复 accession；阈值梯度与多重校正三口径；给"68% 一致率"这类聚合数字配可解释性）。
>
> **独立验证 / 代码可移植 / 终版收口**：见 **independent-verification-and-portability.md**（纯 Python 零项目依赖复算与容差纪律；配对-非配对效应量交代；config 驱动的代码四件套；换 docx 构建器后的产物不变量；DOI 插入脚本与 dry-run 纪律；产物在工作树外导致 commit 返回 1；"为什么不用 recount3/ARCHS4"定位段；Limitations + 许可分源 + 可比性降级）。
> **一条命令完整性闸**：`python scripts/verify_manuscript_integrity.py <md> --package dataset_package --tables 03_tables/Tables_vN.docx --docx <docx> --figures 02_figures`
> （引用编号 range-aware 连续性与未被引/悬空、更正通告与空作者、accession 粘连角标、占位符、计数 vs 清单、Supplementary Table 覆盖、docx 内嵌表/上标/图哈希不变量；任一 FAIL 退出码 1，可做构建门）。

## 1. 期刊硬性约束（Scientific Data，实测）
- 标题 ≤ 110 字符；摘要 ≤ 170 词（脚本化断言，勿目测）。
- 结构：Background & Summary / Methods / Data Records / Technical Validation / Usage Notes / Data Availability / Code Availability / Ethics / Author Contributions / Competing Interests / Acknowledgements(+Funding)。**不呈现研究结论**。
- 必须存数据仓库并给 DOI（首轮可用匿名链接，第二轮起强制）；许可 CC0 或 CC-BY，**不接受 -NC/-SA**。
- Technical Validation 只需 1–2 图/表 + 一段文字；但“验证证据”必须与声明同级（见 §4）。
- 图例与表格分别单独成文件（Word），正文图内**不放图例、不放总标题**。

## 2. 生成器 = 唯一数据源（本类任务第一铁律）
- 正文里每个数字由脚本从冻结表注入；构建器读 `results/*.csv`、`dataset_package/*`，用 f-string 填数。
- **禁止按“表首行”取值**。
  - 实例：`esc_mut[0]` 恰为 KRAS(0/96)，正文却写成 “TP53 reported in 0/96” → 两位 AI 审稿人一致判定“突变层错位/数据警报”。真因是模板 bug，数据本身是对的（TP53 86/96 = 89.6%）。
  - 修法：
    ```python
    def one(rows, **kw):
        hit=[r for r in rows if all(str(r.get(k,''))==str(v) for k,v in kw.items())]
        assert len(hit)==1, f"expected exactly one row for {kw}, found {len(hit)}"
        return hit[0]
    tp53 = one(mut, gene="TP53")
    ```
  - 同时全项目清查其它“首行/位置取值”模式（`x[0]`、`head(1)`、`$HR[1]`）；列名跨表不一致时（`HR` vs `hazard_ratio_per_1sd`、`p` vs `p_value`）用 `intersect(c(...), names(df))[1]` 自适应。
- **编辑顺序陷阱**：先手工 patch 生成的 md/docx，再重跑构建器 → 改动被静默覆盖。流程固定为：改生成器 → 重跑生成器 → 重跑 docx/PDF/ZIP → 重跑审计。
- 图脚本同样：把版式参数（宽 6.7 in、字号、标题文案）集中在一处，改版式只改那里。

## 3. 图表版式陷阱与机器质检（本用户硬要求）
- 版式：**图内无图例、无总标题**；面板说明用直标/分面/标题内短说明；图例单独 `Figure_legends_vN.docx`；表格 `Tables_vN.docx` **全三线表**（top/bottom 粗线 + 表头下线，无竖线）。
- 宽度一律 ≤ 6.7 in（17 cm @300 dpi），高分辨率 300 dpi，PNG+PDF 双份。
- **ggplot 静默丢数据**：`geom_col(aes(factor_label, numeric_value))` 会把因子当“柱高”→ 整层数据被丢弃，日志只给一行 `Removed N rows containing missing values`。
  - 正确写法：`aes(reorder(label, value), value) + coord_flip()`；且 coord_flip 后范围要用 **`scale_y_continuous`**（写成 `scale_x_continuous` 会对离散轴报错；干脆省掉 limits，避免误删）。
- **文字越界**：panel title 一长就被画布右缘截断（ggplot 不自动换行）。
  - 检测：Tesseract `--psm 11 tsv` 取词框，任一框 `x+w >= W-2` 或 `y+h >= H-2` 记疑似裁切。
  - 复核：把疑似框裁出、做像素检查——`array.min()==255` 且非白比例≈0 → **假阳性**（框贴近画布但无墨迹），别为它改图。
  - OCR 会把网格线/误差棒读成 `-`/`+`/`5`；字号以代码设定为准，不要凭 OCR 高度反推。
- 环境：Tesseract 需 `TESSDATA_PREFIX=C:\Program Files\Tesseract-OCR\tessdata`，且先把图复制到 ASCII 临时目录再 OCR（中文路径会失败）。
- **可直接跑的质检脚本**：`scripts/ocr_figure_layout_qa.py`（一条命令给出：物理宽度 cm 是否超栏宽、疑似裁切的词框坐标、**每个疑似框的像素级真假判定**、必需 token 缺失）。
  ```bash
  python scripts/ocr_figure_layout_qa.py 02_figures --dpi 300 --max-cm 17.0 --need "A,B,C,D"
  ```

## 4. 验证措辞分级（AI 审稿人必抓）
把“复现”分成三级，正文与表格分开写，绝不混用：
| 级别 | 判据 | 本用户可接受的写法 |
|---|---|---|
| 精确复现 | 重算统计量与随包值**绝对差 = 0** | “reproduced exactly (maximum absolute difference 0)” + 列比较数 |
| 秩一致 | 只保证排序一致 | “rank agreement only (Spearman 0.95–0.98)”，**并说明差异来源**（如聚合顺序：先按基因跨样本 z 再对成员取平均 vs 先平均再 z） |
| 敏感性分析 | 模型/协变量选择不同 | “sensitivity analysis”，不得当作独立效应估计 |

配套必写：每层分数的**构造规则**（TCGA=成员 z 均值；bulk=队列内 z 的 GSVA；单细胞=成员 log 归一表达均值）并声明三者不可拼接。

## 5. 数据完整性审计清单（每版必跑）
1. **样本级去重**：跨队列样本 ID 重复数（实测 0 才算过关），逐队列 `n_unique_patient_id`。
2. **设计分类必须由元数据推导**，不得硬编码：例如“≥4 例双组织患者即配对”。实例：v11 硬编码清单把 3 个真有配对患者的队列当非配对（GSE41258/44 对、GSE13911/31 对、GSE179285/11 对）→ 主结果 17→13 全变；修法是把 `paired` 判据写进脚本（缺患者 ID 的队列→按必需非配对并标记）。
3. **分组标签要核**：治疗应答队列（Responder vs NonResponder）不是病例-对照，须单列并写排除理由；登记表按 `design` 分类（N 病例-对照 + 1 排除）。
4. **组织学/亚型混用**：多组织学癌种（ESCA=腺癌+鳞癌）必须用**患者级**字段筛亚型；分母与效应量同步重算（实例：突变分母 185→96，TP53 89.6%）。
5. **矩阵完整性**：队列 × 模块应有行数 vs 实际行数，差额**逐行补“不可估计 + 原因”**（实例 442 = 434 + 8：4 对仅 2/3 成员、4 对仅 2/6 成员），不要留缺口让审稿人算。
6. **覆盖度与可比性**：给“共有基因集敏感性”（中位 Spearman、方向不一致模块、共有基因不足模块）+ **覆盖阈值敏感性**（0.6/0.8/0.9 下显著状态数，实例 13/13/12/6）+ 方向一致性（实例 112/165=68%）。
7. **同源耦合**：模块分数与反卷积分数来自同一矩阵 → 做**签名重叠审计**（实例：17/17 模块 >20% 成员落在 xCell 489 基因面板内，最高 100%）→ 把“调整模型”降级为敏感性分析。
8. **共线性报数要能自洽**：整体模型 R²（疾病~四成分，中位 0.33/最高 0.89）与**逐预测变量 VIF**（中位 2.09/最高 4.53）是两个对象，必须分别定义，否则会被读成矛盾（`1/(1-R²)` 只适用于单变量）。
9. **生存层**：`cox.zph` 全特征检验；措辞写“未检出违反 PH 的证据”，不写“PH 假设成立”。
10. **上游标识要联网核**：缓存/文件名里的版本 ID 会失效（实例：CELLxGENE 缓存 dataset_version_id 全部 404）。改为调 API 按 collection 取当前 dataset_version_id，并用**细胞数+标题**与本地文件对齐；把 dataset_version_id / collection_id / 许可写进 `01_cohort_registry/cellxgene_sources.csv`。

## 6. “声明 vs 交付物”终检（宣布完成前必跑，脚本化）
逐条把正文承诺映射到包里的文件：
- 正文说“可运行的下载→结果通路” → 包里必须有该脚本（且路径/依赖写明），否则改措辞或补脚本。
- 图例引用的补充图必须真的存在，否则删引用（宁可少发一张，也别发一张身份不清的旧图）。
- 交付夹不得残留上一版文件（`*_v12.*` 混进 v13）。
- 正文/README 里的仓库 URL、数据集标识、DOI 占位符数量要与现实一致（改名后旧链接会跳转，但引用必须写新名）。
- 结构断言：行数（如 442 = 26×17）、关键基因/队列的值（TP53=86/96）、摘要词数、标题字符数、“无占位符”扫描（TODO/TBD/YOUR_MATRIX/待定）。
- 脚本形态：一个 `9x_adversarial.py` 把上述要点写成 `(name, ok, detail)` 列表并打印 PASS/FAIL，每版重跑。

## 7. 仓库与归档卫生
- 改名：`gh repo rename <new> --repo <owner>/<old> --yes`（旧链接自动跳转），随后 `git remote set-url origin <new>` 并更新正文 Data Availability（注明“renamed from X”）。
- 包内固定带 `00_VERSION.txt` + `00_CHANGELOG.md`（更新=发新版本，旧 DOI 保持可引）；`07_estimates/PROVENANCE.md` 逐表写“出自哪个版本/是否受某次修正影响”。
- 计算 SHA-256 清单（`08_qc/file_inventory_and_checksums.csv` + `checksums_sha256.txt`），并在正文写明文件数与总大小。

## 8. 可直接复用的独立复算套路
- **bulk 模块分数与效应量**：随机挑 3 个队列（覆盖配对/非配对/不同平台）从 rds 重算 GSVA→z→SMDH/SMCRPH，与随包表比对（实例：Spearman 1.00；效应量与 SE 最大绝对差 0）。
- **组成分数**：用 `xCell::xCellAnalysis()` 重算，取原始管线的 4 个区室定义（`Epithelial cells`/`Fibroblasts`/`Endothelial cells`/`ImmuneScore`），比对 Pearson/Spearman（实例 0.71–0.95 / 0.48–0.94），低的如实披露。
- **生存层**：从随包分数重拟合 uni 与 age+stage Cox，比对 HR（实例 68 例比较最大绝对差 0）。
- 复算脚本一律写入 `results/vNN_qc_*_verification.csv` 并进包：审稿人要的不是“我说可复现”，是**可点的证据文件**。

## 9. 生成型稿件的“静默数值错误”类（三路冷读才抓到，自审多轮仍漏）
| 错误 | 症状 | 检测/修法 |
|---|---|---|
| **不排序取中位** | 正文写 median R²=0.15 / VIF=2.77，随包表为 0.33 / 2.09（`x[len(x)//2]` 恰取到某一行的值） | 一律 `statistics.median(x)` / `np.median`；全项目 grep `len(.*)//2`、`[...//2]` 逐一排查 |
| **阈值文字与代码不一致** | Methods 写“<3 成员→not scorable”，脚本实为 `length(common) < 2`，3 个模块被错标 consistent | 措辞必须写**代码里实现的那条**；要么改代码重算、要么改文字，二者不许打架 |
| **重复且互相冲突的图注** | 同一 docx 里 md 生成的 “Figure captions”（Fig3 A–C）与脚本追加的 “Figures”（Fig3 A–D）并存 | 图注只保留一处权威来源；docx 内插图段只指向正文/独立图例文件，不重复文本 |
| **计数漂移** | 文件数 64 vs 清单 69；患者模块对 29,451 vs 20,451；README 1,138 vs 正文 1,086 | 建“计数台账”：队列/样本/患者/文件数/词数/字符数**全部从同一变量渲染**到正文、表、README、仓库指南；缺值写“unknown”，**绝不用 1 占位**（1,138 正是 9 个无患者 ID 队列各记 1 的结果） |
| **声明级夸张** | 正文称 sample 级分数 Spearman 1.00，但随包无该层证据文件（只有效应量/SE 的 diff） | 每句“已复现”都要有对应 QC 文件；补 `qc_bulk_score_level_reproducibility.csv`（逐模块 Spearman/Pearson/max abs z diff） |
| **k=1 被当成合并估计** | 主合并表含 5 行 k=1（`meta_unpaired_only` 有 38 行）却带 est/se/p/FDR/预测区间；Methods 又写“requires at least two cohorts” → 两者打架 | 所有 k<2 行统一标 `pooled = "no (single cohort; not a pooled estimate)"`，p/FDR/CI/PI 置 `not applicable`；正文写明该规则（写"requires ≥2"就必须让表里没有伪装成合并的 k=1 行） |
| **被取代的旧表还留在包里** | `per_state_evidence_matrix.csv` 仍是上一版的合并值，与主表 **51 行不一致**（CRC/IBD/STAD 各 17），而 `PROVENANCE.md` 只轻描淡写写 "partially reflects" | 用修正后的逐队列效应**全量重算**并另存 `..._v14recomputed.csv`；凡是"某次修正后必须重算"的表，要么重算要么移出包，不能带病共存 |
| **两表分母来自不同样本宇宙** | 驱动层 `n_analysed 508 + excluded_not_profiled 58 = 566 > 分母 534`（PAAD 177>173）；读者会直接相加 | 两表并置时必须加列/加注说明各自口径（"profiled universe 来自源研究，未检测样本在其之外"），否则算术上不可能通过 |
| **包内元数据与稿件不同版** | `00_VERSION.txt` 写 v13、README 标题 (v13)、CHANGELOG 无 v14 条目，而稿件是 v14；正文文件数 82 vs 实际 86 | 元数据三处同改 + 计数从清单变量渲染 |

## 10. 校验值与包自足性（`sha256sum -c` 必须一条命令通过）
- **自引用陷阱**：清单/校验文件把自己也写进去，而写入时用的还是旧哈希 → `sha256sum -c` 直接 FAILED，整套完整性声明失效。
  - 修法：**两遍生成**——先写全部数据文件，最后再写 `file_inventory_and_checksums.csv` 与 `checksums_sha256.txt`（跳过自身），并在文件内用一行注明“self-reference: 自身哈希由对方文件记录”。
- **跨平台可用性**：LF 换行 + **正斜杠相对路径**（Windows 用 `newline="\n"` 且 `rel.replace("\\","/")`）；末尾不要留空行（GNU sha256sum 会报 “improperly formatted”）。
- **校验文件只许有"哈希 + 两空格 + 路径"行**：注释行（`#`）和空行同样触发 `WARNING: 1 line is improperly formatted`——GNU 工具不认注释。说明性文字写到**单独的 `08_qc/checksums_README.md`**（写清自引用豁免与 `sha256sum -c` 用法），实测这样才是 `verified 97 / problems: none / stderr: none` 的干净态。生成器里也要同步改（否则下次重建又写回注释行）。
- **CSV 编码统一**：清掉 UTF-8 BOM（`utf-8-sig` 写出的文件会让 `read.csv`/`pandas` 首列变成 `\ufeffaccession`，而 README 又把它声明为 join key）。全包统一 plain UTF-8，并在 README 写明编码与 `rows` 列语义（数据行=不含表头）。
- **包必须自足**：README/run_order/PROVENANCE 里点名的每个文件都要真的在包里（实例：`cbio_v3_patient_module_scores.csv`、`figure_layout_qa.csv` 缺失；run_order 引用未随包发布的脚本）。做不到就改引用，指向 GitHub 仓库 + commit/DOI。
- **声明了 join key 就必须真给 key**：正文写“composition scores keyed by sample identifier”，则主表必须含 `sample_id`（实例：主表只有行序，靠 `join="by position"` 的对齐，属不可核验）。

## 11. “可运行示例”是契约，不是装饰
- 交付前**必须实际跑一遍**并比对 `expected_output/`；实例：example2 读了不存在的列 `beta_adj`（`Error in filter(): 找不到对象`），而 expected_output 是另一条路径生成的 → “runnable examples” 声明为假。
- 修法：重写脚本（读实际存在的表）→ **跑脚本生成** expected_output（不要手搬列）→ README 写清 ratio 是逐行还是全局（同一文件里 170 个互异值 vs 一个常数，读者会误解）。
- 建议在构建脚本里加一步“跑示例 → diff expected → 不一致就 fail”，把这类问题挡在发布前。
- 示例输入若依赖随机子集，确保**含模块成员基因**（否则 GSVA 报 “No identifiers … could be matched”）；行名统一 `toupper()`；输出附 `sample_id` 列，否则用户无法把分数映回样本。

## 12. 图件高度上限与“拆图而非压图”
- 版式检查常只核宽度（≤17 cm）而漏高度：实测 Fig2 = 31 cm、Fig3 = 29 cm，超期刊单页上限（约 23–25 cm）。
- 压缩高度会让字号跌破下限（本用户要求轴 ≥9 pt、注释 ≥8 pt；ggplot `size` ≈ pt/2.845）。**OCR 可读词数骤降是字号/拥挤的代理信号**（同一图 190→99 词）。
- 正确处置：**拆图**——把敏感性/耦合类面板移出主图（实例：Fig2 只留 A–C 验证，新增 Fig4 装共同基因集敏感性与共线性），每张 ≤22.6 cm，字号回到 ≥8.5 pt；拆完更新正文引用、图注、图例文件与打包脚本的图列表（四处联动，别漏）。
- 拆图后必须重跑：审计脚本里“图表数量/被引用图号”的断言（原写死 3 张，拆图后要改成 4）。

## 13. 数据资源稿的“内容完备性”清单（v13→v14 被外部审稿人逐条点名的，结构合规≠内容够）
结构对了仍会被退：以下每一项都曾被判“高优先级”，缺失即不可送外审。
| 项 | 要求 | 落地文件 |
|---|---|---|
| 参考文献与文内引用 | 方法类必引（GSVA、xCell、metafor、Hartung-Knapp、limma、GEOquery、TCGA/GDC、cBioPortal、CELLxGENE、R 版本、期刊政策）+ **每个队列的来源文献**（登记表 `origin_pmid` 逐行） | 正文 References 段 |
| **检索与筛选过程** | 数据库、检索日期（含复核日期）、关键词、候选数、去重规则、纳入/排除标准、**排除系列逐条给原因**（应答设计、下载未采纳等） | `08_qc/curation_flow.csv` + Methods 首段 |
| 表达 QC | 每队列样本/基因数、缺失比例、样本均值分布、**>3 MAD 异常样本（标记不删并说明理由）**、零方差基因数 | `08_qc/qc_expression_matrix_per_cohort.csv` |
| 转换规则确定性 | 例：整数比例 >0.90 且 max >50 视为已取对数，否则 `log2(x+1)`；给每队列输入最大值/整数比例/转换后 min-median-max | `transformation_log.csv` + `transformation_summary_per_cohort.csv` |
| 模块溯源 | 全基因列表 + **成对 Jaccard 重叠矩阵**（实测全部 0 → 作为“模块不重复计数”的卖点）+ 版本历史 | `04_modules/module_overlap_matrix.csv` + `00_CHANGELOG.md` |
| 效应量完整公式 | SMDH/SMCRPH 定义、共享分母、经验组内相关 r、**零方差→不可估计**、最小 k、以及 k/τ²/I²/95%CI/**95% 预测区间**同表报告 | `meta_primary_with_prediction_intervals.csv` |
| 覆盖度一等公民 | 每条效应行带 `module_coverage` 与 `members_present`；主分析全队列 + 预设阈值（0.60/0.80/0.90）敏感性 | `07_estimates/per_cohort_effects.csv` |
| 患者级 + **研究级**重复审计 | 除样本身份外，按来源文献查“同一研究拆成多队列”；给留一法去重敏感性 | `qc_study_level_overlap_audit.csv` + `qc_study_dedup_sensitivity.csv` |
| **对照类型本体** | 癌旁/非炎症/健康供者/非病变 等分类逐队列标注，**不静默合并**；跨类不池化 | `01_cohort_registry/contrast_ontology.csv` |
| 生存层数据字典 | 终点、时间单位、删失规则、协变量、缺失处理、软件与数据版本 | `07_estimates/survival_data_dictionary.md` |
| 归一化与细胞阈值 | 单细胞写清归一化（如库大小 1e4+log1p）、细胞→供者汇总、每臂最少供者；**未设每供者最少细胞数也要写明** | Methods + `06_single_cell/` |
| 上游版本核实 | 缓存 ID 会失效 → 联网按 collection 取当前 `dataset_version_id`，用**细胞数+标题**与本地文件对齐后入库 | `01_cohort_registry/cellxgene_sources.csv` |
| 简化复用示例 | 从 accession 重建一个系列（脚本 + 输出位置 + 运行方式）；示例必须离线可跑并含 expected_output | `03_expression/download_and_rebuild_one_series.R` |

## 14. 与“同源耦合”对抗：必须提供**非重叠标记**的替代方法
- 只声明“调整模型仅作敏感性分析”不够；审稿人会要“非重叠标记集或另一种组成估计”。做法：
  1. 自建小标记面板（每区室 5–6 个经典基因，全部 `toupper()` 匹配）；
  2. **算它与模块基因集的重叠**（实测 24 个标记仅 1 个与模块重合 → 独立性成立，这句话可直接写进正文）；
  3. 逐样本算均值并**队列内 z**，与 xCell 同区室比 Spearman/Pearson。
- **诚实报告弱项**：实测上皮 0.28 / 成纤维 0.29 / 内皮 0.58 / 免疫 0.56 → 必须写“内皮与免疫中等、上皮与成纤维弱，故仅作粗粒度独立核查，不替代 xCell”。**不得只报好看的区室**。
- 反面教训：作者曾在汇报里凭截断日志口报“0.48–0.58”，与随包 CSV（0.28–0.58）不符 → **凡对外数字一律现场从冻结 CSV 读**，并报“最弱值”。

## 15. 图件“结构性可读”四件套（v14 定稿做法）
1. **标题自动折行**：ggplot 不换行，长标题会被画布右缘静默裁掉（OCR 见 `lowe:`/`scorabl`/`non-sic` 这类残词即中招）。
   ```r
   wrap_title <- function(x, width = 38) vapply(as.character(x), function(s) paste(strwrap(s, width=width), collapse="\n"), character(1))
   labs(title = wrap_title("..."))   # width 38 比 46 更保险
   ```
2. **轴标签一律水平**（`angle = 0`）：45° 旋转既降低可读性，又让 OCR 词框互相交叠，制造“重叠”假阳性。
3. **图内用短标签，全长映射写进独立图例文件**（如 `IGF_INSR` = `IGF_INSR_AXIS`、`REC` = `RECEPTORS`），并在图注里给映射规则。
4. **密集明细移出主图**：165 对 context-module 明细做成 `Supplementary Table S10`，主图只留“按情境的一致性分布（散点+中位横杠）”。
- OCR 碰撞判定要能抗假阳性：两词框同行且横向相交 **且** 交集矩形内有墨迹（<2% 视为空）**且** 二者不是同一数字被拆段（水平间距 ≤3 px 且拼接后匹配 `^\d+(\.\d+)?$`）才算候选碰撞；裁切判定要额外验证**边缘 4 px 带内确有墨迹**（框贴边但空白 = 假阳性）。最终判定用“0 裁切 + 0 候选碰撞 + 宽 ≤17.0 cm + 高 ≤24 cm”四条同时成立。
- 四张图定稿后同步四处：正文引用、图注、独立图例文件、ZIP/打包脚本的图列表；审计里“图表数量”“被引用图号”的断言一起改。
- **可直接跑**：`scripts/figure_layout_qa_pixel.py`（几何+裁切+碰撞+假阳性抗性一次给出，判定四条同时成立才算 PASS）：
  ```bash
  python scripts/figure_layout_qa_pixel.py 02_figures --dpi 300 --max-cm 17.0 --max-cm-h 24.0 --need "A,B,C,D"
  ```
  （旧版仅词框裁切的 `scripts/ocr_figure_layout_qa.py` 仍可用于快速宽度检查。）
6. **可读性/完整性另跑一层**（几何过关 ≠ 读者能读）：`scripts/figure_readability_audit.py`
   ```bash
   python scripts/figure_readability_audit.py 02_figures --dpi 300 --scale 0.5 --min-retention 0.6 \
       --need "A,B,C,D" --contexts "LUAD,CRC,STAD,PAAD,HCC,ESCC,IBD,COPD,NAFLD,Asthma"
   ```
   实测阈值与判读（v14）：
   | 层 | 判据 | 实测 | 处置 |
   |---|---|---|---|
   | **打印尺寸可读率** | 缩到 `--scale 0.5`（≈期刊印刷尺寸）再 OCR，`tokens_small/tokens_full ≥ 0.6` | Fig1 **0.60 → 0.83**（其余 0.93/0.95/1.04） | 唯一有效手段是**提高最小字号**（模块标签 7.5→8.3、注释 3.1→3.2 ≈8.8 pt），不是继续缩图 |
   | 标签完整性 | 面板字母 + 全部情境名/模块短名都在 OCR 文本里 | 全在 | 改图时最容易漏某一面板；短名映射写进独立图例文件 |
   | **图例/总标题条带** | 外侧 3.5% 带内墨迹列覆盖 ≥ **0.55** 才算有图例/总标题 | 0.14–**0.47** → 无条带（0.46 是双面板轴标签，不是图例） | 阈值取 0.30 会误判；取 0.55 并点名是哪两面板造成 |
   | 边距 | 最外墨迹到画布 ≥ 8 px | 44–81 px | 内容贴边即"图被裁"的信号 |
   | 对比度 | 词框 5/95 分位之比 <3，**先跳过 box std<18 的框**、**排除单字符 token** | 报出的低对比全是 `5`/`+`/`a`/`&`/`-` 等 OCR 碎片 | 不排除就会把坐标轴/散点当成"文字看不清"，白改一轮 |
   | 压色块文字 | 词框内局部背景 std >48 | 1–3 处（贴柱数值标签） | 数值标签改 `#1A1A1A` 并移到柱外 |

## 16. 工具使用纪律（本环境实测，shape 为“改用脚本文件”）
- 复杂逻辑一律**写成脚本文件再执行**（如 `scripts/9x_v14_xxx.py`）。内联 `python -c "…"` 与含反引号/`<`/多行的 heredoc 容易触发审批门或被 bash 解析破坏（实测一次因 heredoc 里的反引号直接报 `command not found`）。
- 每步落一个 `results/*_log.txt`，后续诊断只看日志尾部；长任务用后台 + 完成通知，避免前台超时。
- GPT6/Claude 的意见文档用 `read_file`（可直接解析 .docx）读取并**先落盘成 `_refs/` 文本**，再逐条对照处置。
- **改生成器文本用"容错逐条应用"**：锚点式替换脚本若写成"任一条不匹配就 assert 退出"，会导致**前面已成功的替换全部丢失**（实测：11 条里第 3 条锚点不符 → 脚本未写盘，前 2 条白做）。正确形态：
  ```python
  applied, skipped = [], []
  for old, new, label in edits:
      if old in s: s = s.replace(old, new, 1); applied.append(label)
      else: skipped.append(label)          # 不中断
  open(p, "w", encoding="utf-8").write(s)   # 无论成功几条都写盘
  print("applied:", applied, "| skipped:", skipped)
  ```
  先**从生成文件里 grep 出真实句子**再当锚点（凭记忆写的锚点十有八九差一个标点）；或改用"前缀定位 + 到下一个分隔符为止"的段替换。
- **两个反复踩的语法坑**：① `re.sub` 的反引用写 `\17` 会被解析成"第 17 组"→ 必须写 `\g<1>7`；② 中文串里夹半角双引号（`"…"已对数化"…"`）会让 Python 字符串提前闭合 → 外层用单引号或把内层引号去掉。
- **协作节奏（本用户，多次实测）**：一轮任务结束时**不要在"还剩两项你选哪个"处停下等拍板**——本会话两次收到"你是不是卡住了？/你又卡住了吗？"都发生在作者刚列完 A/B 选项之后。只要剩余项**不阻塞**（不需要用户提供 DOI/凭据/人工目检），就**直接做掉下一项并汇报结果**；真正需要用户输入的（DOI、上传、目检图）才单列"只剩这些"。

## 17. 投稿包格式合规（Sci Data 实测被点名的，与内容同等重要）
| 项 | 要求 | 落法 |
|---|---|---|
| 补充材料 | **PDF 格式**（docx 不合规），超大表（上百行）"应存仓库、不要叫 supplementary" | `soffice --headless --convert-to pdf` 导出 `Supplementary_Information.pdf`；165 行明细表改成"摘要 + 仓库路径"，明细留在 `08_qc/*.csv` |
| 图件 PDF | 需内嵌字体（LibreOffice/期刊排版会因字体替换走版） | ggsave 加 `device = cairo_pdf`（先 `capabilities("cairo")` 确认）；PNG 仍作主交付 |
| **代码要随包** | 正文写 "code … archived in the deposit" 就必须真有 | 建 `11_code/` + `README_code.md`（列出脚本与"路径需按包布局调整"的说明）；只写"见 GitHub"则改措辞 |
| 章节顺序 | Data Availability → Code Availability → **References**（参考文献在 code availability 之后）；Ethics 建议作 Methods 子标题 | 逐版核对标题序列，别沿用旧顺序 |
| 陈旧版本文件 | 投稿目录里残留 `*_v13.*` 会被上传错版本 | 每版发布前清 `01_manuscript/`、`03_tables/` 里上一版的同名文件 |
| 重复文件 | 同一内容两个文件名会让审稿人以为有两套结果（实测 `module_coverage_gaps.csv` ≡ `platform_module_coverage.csv`；`meta_primary_reml_knha.csv` ≡ `..._with_prediction_intervals.csv`） | 定期按 sha256 分组查重，多余件删除 |
| 版本元数据 | `00_VERSION.txt` / README 标题 / `00_CHANGELOG.md` 必须与稿件同版（实测包自述仍是 v13 而稿件是 v14） | 升版时三处同改 + 补该版变更条目 |
| 计数一致 | 正文"82 files"实则 86、README "18 队列有患者 ID" 实则 17 | **文件数/队列数一律从清单变量渲染**，不手写 |

## 18. 单一真源：一条判据只能有一个实现
实测事故：**log2 变换判据在"内部管线"与"外部复用示例"里写反了**——管线是"整数比例>0.90 且 max>50 → 视为原始强度、需 log2"，示例写成 `if (!(…)) log2` → 对**已对数化**的系列又取了一次对数（二次对数），而正文声称"同一确定性规则"。
- 规则要**抽成一个函数/一段常量**，管线、示例、随包重建脚本三处共用；改判据后**三处同步 + 重跑示例**（实测：修好二次对数后方向一致仍 9/17、耗时 1.6 min 不变 → 这本身是"单调变换不改变方向"的稳健性证据，可写进回复）。
- 判据必须在**日志里打印实际取值**（`integer fraction 0.000, input max 14.45 -> raw intensities: FALSE -> log2 applied: FALSE`），否则二次对数这类错误在结果里看不出来。

## 19. 外部复用示例（"资源可用性"的唯一硬证据）
- 选**不在资源内**的队列（实测 GSE54129：111 肿瘤/21 癌旁），从 accession 走完整路径：下载 → 探针映射 → 同一变换规则 → 冻结模块打分 → 与资源内同情境合并估计比方向。
- 报告四件：**可打分模块数**（17/17）、**方向一致率**（9/17 = 53%）、**运行时间**（1.6 min）、**脚本与输出文件**。
- **措辞纪律**：这是"复用成本与跨队列方向一致性的限度"示例，**不是外部验证**（正文/README/图注三处都别写成 validation）。
- 下载要**持久缓存 + 重试**（实测首次重跑因 NCBI `schannel: server closed abruptly` 失败 → `destdir` 指向 `results/external_cache/`、4 次重试 + `Sys.sleep(20)`，第二次直接复用缓存）。
- 探针→符号映射要带**平台注释回退**（GPL570 的 series matrix 里没有 `Gene symbol` 列 → 候选列名列表 + `getGEO(annotation(eset))` 表兜底），否则在 `avereps` 处报 `No probe IDs` 白跑一轮。
