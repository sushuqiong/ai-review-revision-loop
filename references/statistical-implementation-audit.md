# 统计实现审计（Statistical Implementation Audit）

> 触发：外部 AI 审稿（GPT6/Claude 等）指出「结果可能来自实现错误」而不是措辞问题；或自查时发现
> 某类样本整批消失、相关系数恒为 1、方差列全 NA、某癌种/某队列完全没有结果。
> 核心纪律：**实现 bug 优先于文字**——把每条指控当作可执行假设，先在公开结果表里验证数值形态，
> 修代码 → 重算 → 冻结结果 → 再改摘要/讨论 → 图表从冻结表自动重生成。

## 1. 静默丢弃类 bug（最危险：不报错，只让样本/队列消失）

### 1.1 子集索引错位（配对 design）
- 症状：配对相关恒为 1（或 ±1）、效应量方差全为 NA、整类配对队列被后续 `is.finite()` 过滤掉；
  结果表里"本来应该有数据的癌种"整列缺行。
- 根因：用子集内的位置去索引完整向量，例如
  `d <- y[match(common_ids, pid_case)] - y[match(common_ids, pid_ctrl)]`，
  其中 `pid_case/pid_ctrl` 是患者 ID 子集、`y` 是所有样本的完整分数向量 → 变成"同一组减自身"。
- 正确写法（先取子集，再按组内位置对齐）：
  ```r
  yc <- y[iscase]; yr <- y[!iscase]
  cc <- intersect(pidv[iscase], pidv[!iscase])         # 配对患者
  d  <- yc[match(cc, pidv[iscase])] - yr[match(cc, pidv[!iscase])]
  ri <- cor(yc[match(cc, pidv[iscase])], yr[match(cc, pidv[!iscase])])
  ```
- 强制核验：输出 `attempted rows vs finite rows`（应 200/200 而不是 0/200）、`median r`、
  `n cohorts with finite effect`。任何"整类样本 0 可估"都必须当成 bug 而不是生物学结论。
- **半修复陷阱（本类 bug 最容易二次复发）**：`yc <- y[match(cc, pidv[iscase])]` 看似已按 ID 匹配，
  实际仍是用**子集内位置**去索引**完整向量**——只有"病例恰好排在矩阵前部"时才偶然正确，
  病例/对照交错排序时仍退化为同组自减。必须两步走：
  `y_case <- y[iscase]; y_ctrl <- y[!iscase]; yc <- y_case[match(cc, pidv[iscase])]; yr <- y_ctrl[match(cc, pidv[!iscase])]`。
- **bug 数字签名（一眼识别）**：配对相关 = 1.00 / 中位数 r ≈ 0.99 / `dz = NaN` / 方差列全 0 或全 NA。
  真实配对相关通常 0.1–0.7（本项目修正后 median r = 0.11；0.99 是假象）。
  另一签名：`yi` 恰好为 0.0000 且 `vi` 恰好为 0 — 典型同组自减。
- 修复后必须**重跑全链**（效应量 → meta → 联合模型 → 证据矩阵 → 图表 → 正文数字），
  并在 tests/ 留下三条验证记录（手算比对、打乱顺序按 ID 连接、同输入连跑两次）：
  本项目正是该电池抓出"第一轮修复仍不完整"，否则错误数字会被直接写进摘要。

### 1.2 分层纳入条件互相污染
- 症状：A 层（如 meta 效应量）因方差缺失被过滤后，用同一个被过滤对象去汇总 B 层（如联合模型），
  B 层结论凭空缩小（"只剩 6 个稳健状态"其实是程序筛选假象）。
- 修复：**每层独立纳入条件**；并显式输出四类状态而不是二元结论：
  - `not analysed`（未分析/无数据）
  - `failed / not estimable`（模型失败或数据不足）
  - `estimated, not significant`（估计成功但不显著）
  - `robust`（估计成功且符合预设稳健规则）
- 报告时区分"没有数据"与"估计了但不显著"——这是审稿人最常抓的偷换。

### 1.3 事后符号翻转（非幂等）
- 症状：`d_adj <- -d_adj` 之类的补丁脚本重复运行会再次翻转；结果随运行次数变化。
- 修复：在模型里显式设定参照水平，永不事后翻转：
  ```r
  grp <- factor(group, levels = c("Control", "Case"))   # 系数即 Case - Control
  ```
- 校验：把同一脚本连跑两次，核心输出哈希/行值必须一致。

### 1.4 行数相等当成对齐
- 症状：反卷积分数（xCell/EPIC）与表达矩阵只检查 `nrow == ncol` 就按顺序拼接；
  上游任何排序变化都会错配，且不会报错。
- 修复：按样本 ID 显式连接；设定可接受的丢失阈值（如 <10%）并记录日志：
  ```r
  common <- intersect(colnames(expr), comp$sample_id)
  stopifnot(length(common) >= 0.9 * ncol(expr))
  expr <- expr[, common]; comp <- comp[match(common, comp$sample_id), ]
  ```
- 验证测试：**打乱输入顺序后按 ID 连接，结果必须与原始一致**。

## 2. 效应量尺度与 meta（统一尺度是硬要求）

- 配对 d_z（均值差/SD差）与未配对 Hedges' g **不在同一尺度**，不能直接混池。
- **"统一尺度"要先统一分母——不是都叫"标准化效应量"就同尺度**（本项目 v10 被外部审稿明确驳回的写法）：
  | 度量 | 标准化分母 |
  |---|---|
  | `SMD`（未配对，Hedges g） | 两组**合并 SD** √[((n1−1)sd1²+(n2−1)sd2²)/(n1+n2−2)] |
  | `SMDH`（未配对，异方差） | √((sd1²+sd2²)/2) |
  | `SMCR`/`SMCRH`（配对，原始分标准化） | **sd1** |
  | `SMCRP`/`SMCRPH`（配对，合并 SD 标准化） | √((sd1²+sd2²)/2) |
  | `SMCC`（配对，变化分标准化） | √(sd1²+sd2²−2·ri·sd1·sd2) |

  → **真正同分母的组合是：未配对用 `SMDH` + 配对用 `SMCRPH`**（两者分母都是 √((sd1²+sd2²)/2)）。
  `SMD` + `SMCRH` 是**不同分母**，固定 ρ 敏感性不能解决这个问题（它只修配对协方差，不改分母）。
  ```r
  # 未配对（异方差、平均方差分母）
  es <- escalc(measure="SMDH",   m1i=mean(case), sd1i=sd(case), n1i=n1,
                                 m2i=mean(ctrl), sd2i=sd(ctrl), n2i=n0)
  # 配对（同一分母；ri 由匹配样本实证估计；ni 为完整配对数）
  es <- escalc(measure="SMCRPH", m1i=mean(case), m2i=mean(ctrl),
                                 sd1i=sd(case), sd2i=sd(ctrl), ri=ri, ni=npairs)
  # 汇总：主用 REML + Hartung-Knapp；DL 与 adhoc 作对照
  rma.uni(yi, vi, method="REML", test="knha")    # 标准 HK
  rma.uni(yi, vi, method="REML", test="adhoc")   # HK 但限制 SE 不得比未调整更小（Jackson 2017）
  rma.uni(yi, vi, method="DL")                   # z 检验
  ```
- 必做敏感性：`ri` 实证值 vs 固定 0.5 / 0.7；若显著集合一致，写明"结果对配对相关假设稳健"；
  若不一致，两个集合都要报告。
- 不要把自写的 REML 迭代函数当标准实现——要么用 metafor/meta 包，要么在附录给出与标准实现的一致性。
- **调整前后比较必须同分母**：原始效应常以组内 SD 标准化，调整后效应常以模型残差 SD 标准化；
  分母不同时不能说"校正消除了多少效应"。做法：在同一模型里同时拟合"不加成分"与"加成分"两组系数，
  统一除以**同一个**残差 SD 再比较。

## 3. 外部验证队列的样本审计（结论级问题）

1. **组织类型筛选**：必须用显式字段排除非肿瘤样本（GEO 常见 `dataset:ch1` / `source_name_ch1` 中的
   `Non Tumoral`、`normal adjacent`），并报告"排除多少样本/多少事件"。
   例：GSE39582 585 阵列 → 肿瘤 566 → 有生存 556 / 187 事件（原稿 573/190 混入了 17 例非肿瘤/3 事件）。
2. **重复与配对检查**：同患者肿瘤+癌旁可能携同一结局进入分析；公开记录无患者 ID 时如实声明。
3. **分期解析**：先打印原始取值表再写解析器——公共同一字段可能是数字 `0-4` 或罗马数字或 `N/A`；
   数字解析器不能只认罗马数字（否则有效分期被转成缺失，还误写成"公开记录无分期"）。
   `stage == 0`（原位/特殊编码）单独处理并声明。
4. **复制判定标准统一**：不要一边用 p 值、一边用 FDR；对候选信号预先规定同一标准与检验家族。
   "外部队列不显著"要写成 **not replicated**，不能写成 "no effect"；阴性结果给 95% CI。
5. 外部阳性必须过**分期校正**：仅年龄校正的名义显著不等于独立预后价值（例：VEGF/PDGF HR 1.16，
   p=0.042；age+stage 后 1.09，p=0.217 → 只能写"方向一致但未稳健复现"）。

## 4. 由 bug 派生的措辞规则（写进正文，防止再审被抓）

- 用 "directionally consistent, not significant after adjustment" 替代 "replicated"。
- 用 "not replicated in this cohort" 替代 "effect absent"。
- 交互分析 = effect-modification screen，不得命名为 "negative control"；不显著 ≠ 跨背景稳定。
- 亚型/自定义分类器（如从因子载荷自建的 basal/classical）不显著时不能写 "not subtype-driven"，
  只能写"在本分类与功效下未检出亚型特异效应"。
- 组成校正的解释分层：系数缩小 / 系数相近但 SE 增大 / 疾病与成分高度共线 / 模块与成分共享基因 /
  调整掉了机制本身——只报 p 是否越过 0.05 不足以支持"组成主导信号"。
- **修正此前分析错误 ≠ 方法学创新**：把"我们改正了配对索引/分母/筛选错误"写成主要贡献会被审稿人直接驳回；
  这类内容放代码仓库 ERRATA + 局限声明，贡献表述落在比较框架、判定规则、可复用资源，
  以及"哪些转录结论对组成与临床背景敏感"。
- **阴性结论用穷尽式表述，不留"例外"余地**：本项目无任何模块通过预定义外部复现标准时，
  写 "no module passed pre-specified external replication"，不写 "strict replication remains the exception"
  （后者暗示有阳性存在）。
- **亚组不可估时的措辞**：扩增/小亚组无法估计时写"该关联可在非扩增患者中估计，扩增组证据不足"
  （estimable in non-amplified; insufficient evidence in amplified），禁止写 "confined to / carried by
  non-amplified"（暗示两组效应不同，而不可估本身不支持该推断）。

## 5. 组学分母与驱动分层的样本资格（sample eligibility）

- **分母不能用别的分子层冒充**：突变率/驱动分层必须用 **profiled 样本列表**做分母。本项目 v10 的
  `n_sequenced` 实际取的是 `cna_ok`（CNA 样本数，PAAD 182），修正后按 cBioPortal
  `<study>_sequenced` 列表得 PAAD 173 → 突变率从"58.8%/182"变成"61.9%/173"。
- 取列表：`GET https://www.cbioportal.org/api/sample-lists/{sampleListId}/sample-ids`
  （sampleListId 从 `<CTX>_sample_lists.json` 里挑 `*_sequenced`）。
- **野生型只能定义在 profiled 样本内**：`driver+ = profiled & 有该基因突变记录`；
  `driver− = profiled & 无记录`；**非 profiled 患者从模型排除并计数上报**，不能默认当野生型。
- 与原始论文口径差异要写明而不是回避：本项目 PAAD KRAS 107/173 = 61.9%，而 TCGA 原始 PDAC 研究
  150 例中 140 例 KRAS 突变（93%）——样本子集/检出流程不同，声明"不可直接比较"。
- 资格四联数一起报：`n_analysed / n_driver_positive / n_driver_negative(wild-type) / n_excluded_not_profiled`
  （本项目 PAAD 164/98/66/13）。多组学驱动的交互检验同样只在这套资格内做。

## 6. 单细胞患者层比较（pairing 与 comparison type）

- **代码与正文必须一致**：正文写"配对 Wilcoxon"而代码是患者级 Mann-Whitney，是最容易被抓的硬伤。
  判定规则写进方法：≥5 个完整配对患者 → Wilcoxon signed-rank（报配对数与中位配对数）；
  否则用非配对 MW 并在结果表中**标注 `test_used`**。
- **比较类型必须分族**：`same-cell-type`（同一细胞标签在两组都有）与 `cell-identity`
  （恶性上皮 vs 正常上皮/结肠细胞）回答不同问题——后者包含细胞身份差异，不能当作同类型疾病效应。
- **FDR 按族分别校正**：把 identity 对比与同类型对比混进同一 BH 家族会放大 m、把真信号压掉
  （本项目混族时显著数 17→3；分族后 = 同类型 16 + 身份 12）。
- 建议输出字段：`context, module, cell_type, comparison_type, n_pairs, n_case_patients,
  n_control_patients, paired_median_diff, p_paired, p_unpaired, test_used, p_used, fdr, fdr_unpaired`
  （额外给一套"全部用非配对 MW"的敏感性列，便于与旧版结果对接）。

## 7. 主要终点规则与图 1 的证据层布局

- 全文反复使用的判定词（`per-cohort robust`、`joint-model robust`、`strict external replication`）
  必须在方法里给出**可执行规则**：需要几份队列显著、是否必须包含发现队列、两队列与三队列如何统一
  判定、是否允许反向结论、外部验证要求名义显著还是 FDR 显著、多重检验的家族范围
  （如"每个 context 内 18 个检验各自 BH"；筛选后再做多变量生存要交代 FDR 分母）。
  并在补充表逐状态给出"通过/未通过原因"，否则 55/17/21 这类核心数字无法复核。
- **证据层不是逐级筛选**：本项目 STAD 的保守 meta 显著 = 0 而 joint 稳健 = 9，集合互不包含。
  Fig 1 必须画成**并行证据评估**（或明确标注各层独立），否则读者会误以为 21 个状态通过了前面的门。
- 组成校正的衰减要**量化**而不是断言：基础模型（`module ~ disease [+patient]`）与调整模型（+4 成分）
  用**同一样本**分别拟合，各自报 β/SE/CI，再给衰减比中位数（本项目 median |β_adj|/|β_base| = 0.87）。
- PAAD 式表述模板："调整组成分数后没有模块达到预设稳健标准；目前无法判断主要来自效应衰减还是
  估计精度下降"——不写"完全被组成解释/完全衰减"。

## 8. 收工验证电池（每次重算后必跑）

1. 手算一个配对队列的组均值差与 r，与程序输出比对。
2. 打乱样本顺序后按 ID 连接重跑，核心结果一致。
3. 干净环境连跑两次（同输入），核心输出一致（防非幂等补丁）。
4. 结果表 → 正文数字 → 图表三者一致性：**图表从冻结结果表自动生成**，
   Fig 上的总结数字（如 "55/73/19"）必须重新生成，禁止留旧版残留。
5. 多镜像一致性：工作目录 / 投稿包 / Git 仓库三处逐文件内容探针（不要假设 `cp` 成功——
   实际出现过 md 静默未覆盖、主包比工作区旧一个版本的情况）。

> **这一电池已脚本化，别再每轮手打**：`scripts/manuscript_number_provenance_check.py`
> ＋`templates/manuscript_number_provenance_rules.json`。它从**冻结结果表**重算头条数字（`csv_counts` 规则，
> 支持 `where` 过滤与 `group_by` 分癌种计数）、断言正文确实包含由这些数字拼出的字符串、扫描被取代的旧数字、
> 核引文（连续编号 / 全部被引 / 首现序非降）、摘要词数与 `\uXXXX` 残留，非零退出即未通过。
> **每轮修完必须把新作废的数字追加进规则文件的 `stale` 列表**（如 `retained 7`、`573 tumour`、`12 hits`）——
> 这是唯一能防止旧数字在多轮改写中悄悄回来的机制；本项目 v10→v11 的一致性冲突（结论残留 7、方法写 573
> 而结果写 556）正是靠该扫描在收口前抓到的。

## 9. 跨解释器 / 路径的复现陷阱（重跑前先解决，否则会误判为"数据缺失"）

- **处理对象用哪个环境产出的，就回到哪个环境的 venv 跑**：单细胞 h5ad 类脚本依赖
  `numpy/h5py/scipy` 的 ABI 组合，换解释器常见 `numpy.dtype size changed` 之类二进制不兼容。
  本项目可用的是产出对象的那套项目 venv（`<project>/.sc_venv/Scripts/python.exe`），
  先 `python -c "import numpy,h5py,scipy;print(numpy.__version__,h5py.__version__)"` 探一下再跑。
- **项目目录用通配符/rglob 动态定位，不要硬编码含中文的绝对路径**：
  同一路径串在不同解释器/编码下可能解析失败并**静默 miss**（表现为"[MISS] 数据集 A/B/C，只有无中文路径的那个成功"）。
  ```python
  cands = list(Path(r"C:/Users/<user>/Desktop").rglob("<project_dir_name>"))
  base  = next((c for c in cands if (c/"data_raw").is_dir()), cands[0])
  ```
  另外：同一项目可能存在多个同名目录树（如 `Desktop/EGFR胃癌/...` 与 `Desktop/EGFR/EGFR胃癌/...`），
  先用 `rglob` 列出全部候选并与实际数据文件存在性交叉验证，再固定使用。
- **bash heredoc 里的反斜杠会被吞**：`python - <<'EOF'` 内写 `r"\\uXXXX"` 这类正则/转义常被 shell 改写，
  导致 `re.error: incomplete escape \u` 或写出字面 `\uXXXX` 到产物。**一律把脚本写成文件再执行**
  （`write_file` → `python scripts/xx.py`），并把"产物里出现字面 `\uXXXX`"作为一项产物自检。
