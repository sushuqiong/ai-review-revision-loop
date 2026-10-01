# 公共数据 / 数据资源类稿件的完整性自审（提交前必跑）

适用：多队列公共组学（GEO/cBioPortal/CELLxGENE）的 meta 分析稿、**数据资源稿（Data Descriptor）**、
以及任何"我们把别人的数据重新整理后分析/发布"的工作。GPT6 类外部评审最爱打的点全部集中在这里。

## 铁律：判定必须由元数据推导，禁止硬编码
v11 最严重的错误就是：脚本里硬编码 12 个"配对队列"，另有 3 个队列（GSE41258 / GSE13911 / GSE179285）
元数据里明明有 ≥4 例双组织患者，却被当成非配对 → 违反独立性/配对假设，主结果从 13 变成 17（假阳性增加）。
**修法**：`paired <- has_patient_id && length(intersect(pid[case], pid[control])) >= 4`，并把该判定写进结果表
（n_both_arm_patients / measure 列），让读者能复核。任何 `c("GSE...")` 形式的分析清单都要当成 bug 处理。

## 8 项必查（每项都能产出可交付的 QC 表）
| # | 检查 | 判据 / 处置 | 本次实际命中 |
|---|---|---|---|
| 1 | 样本跨队列重复 | 全域 sample_id 计频，>1 即冲突（本次 0，可写进技术验证） | 0 重复，可正面陈述 |
| 2 | 队列**设计**分类 | 逐队列看 group 取值：出现 `Responder/NonResponder`、`inflamed/non-inflamed`、时间序列 → **不是病例-对照**，须单列并排除 | GSE16879 被误计入"27 个病例-对照队列" |
| 3 | 患者标识可用性 | `patient_id` 缺列或全 NA 或恒为 1 值 → 标 `patient_identity_available=no`，该队列**按必需为非配对**，并在注册表与正文写明 | 9 个队列无患者 ID |
| 4 | 组织学口径 | 肿瘤类型字段优先用**患者级**（`DISEASE_TYPE`/`PRIMARY_DIAGNOSIS`）；样本级字段可能是全填一个值（cBioPortal 的 ESCA 样本级 CANCER_TYPE 全是 adenocarcinoma，不可用） | ESCC 混入 89 例腺癌 → 结论撤回 |
| 5 | 组成分数可连接性 | 每张随包发布的表都必须含样本键；若原分析靠行序对齐，必须重建带 sample_id 的表并附 join 审计 | 组成分数表原本无 sample_id |
| 6 | 生存层假设 | 每个 Cox 特征跑 `cox.zph`，报 p 值与"违反数"（本次 17 个检验 0 违反） | 之前完全没做 |
| 7 | 组成模型共线性 | 逐队列 `R²(case ~ epi+fib+end+imm)` 与 VIF；用于解释"调整后不显著"是共线还是真衰减（本次中位 R²=0.33、最大 0.89、中位 VIF 2.09） | 之前只用文字推测 |
| 8 | 覆盖差异的共同基因集敏感性 | 用"所有队列共有成员"重算效应，与全成员比较：报中位 Spearman + 方向不一致队列比例；共有基因过少的模块标"不可跨平台比较" | FGFR/JAK-STAT/SRC-FAK 方向不一致；TAM-AXL/TIE-ANGPT 共有基因不足 |
| 9 | **派生数值的独立复算（三族都要验，不只组成）** | 从原始数据**重跑**整条链并与随包表逐值比对：①组成分数；②样本级模块分数 + 效应量/SE；③TCGA 生存层 Cox。报一致性类型（精确 vs 秩相关）与最大绝对差，偏低处如实披露 | ① 组成 Pearson 0.71–0.95 / Spearman 0.48–0.94（GSE13911 纤维 0.48、量级 0.91）；② 3 队列 69/196/236 样本分数 **Spearman 1.00**，49 个效应量/SE **最大绝对差 0**；③ 68 个 Cox 比较 **HR 最大绝对差 0** |
| 10 | **配对/非配对合并的权重不对称** | 配对队列方差更小 → meta 中权重更高；必须同时提供**固定 ρ（0.5/0.7）敏感性**结果并说明差异（本用户会追问"为什么两套数字不一样"） | 实证 ρ 主结果 13 vs 固定 ρ 17，需并列披露 |

### 9/10 两项的实现要点
- 复算脚本要复用**原管线的 compartment 定义**（本项目：`epi=\"Epithelial cells\"`、`fib=\"Fibroblasts\"`、
  `end=\"Endothelial cells\"`、`imm=\"ImmuneScore\"`），否则相关性会被"聚合规则不同"污染；
  xCell 用 `xCell::xCellAnalysis(as.matrix(ex))`（旧版 `rawEnrichmentAnalysis` 签名已不匹配）；
  行名先 `toupper()` 并去重再跑。
- 权重不对称不要只写进 limitation，要在 Methods 明说"配对队列获更高权重，故同时给出固定相关敏感性"，
  并把两套结果都放进 `07_estimates/`。

### 9 的三族复算：实现要点与"表象差异"的解释
| 族 | 复算方式 | 本次结果 | 关键陷阱 |
|---|---|---|---|
| 组成分数 | `xCell::xCellAnalysis()` 重跑，按原 compartment 定义取 `Epithelial cells / Fibroblasts / Endothelial cells / ImmuneScore` | Pearson 0.71–0.95 | 行名先 `toupper()` 去重；旧版 `rawEnrichmentAnalysis` 签名不匹配 |
| 样本级模块分数 + 效应量 | GSVA（或原管线口径）重算 → 配对用 SMCRPH（实证 r）、非配对用 SMDH（metafor） | 分数 Spearman **1.00**；效应量/SE 最大绝对差 **0** | 必须与原管线**同一聚合顺序**；否则见下条 |
| TCGA 生存层 | 用随包分数重拟合 `coxph`（uni 与 age+stage），逐特征比对 HR/p | 68 个比较 HR 最大绝对差 **0** | 不同癌种 stage 列名不同（`PATH_STAGE` vs `CLINICAL_STAGE`）→ 自适应取列，缺失时跳过而非报错 |

**聚合顺序会制造"看起来不一致"的假象**：原管线是 **先按基因跨患者 z → 逐患者对成员取均值**；
若复算写成"先对成员取均值 → 再 z"，秩相关仍达 0.95–0.98，但绝对 z 差可达 2.6–3.8。
⇒ 结论表述必须分开写：**秩次序一致（Spearman）** vs **绝对值一致（需同聚合规则）**，
并把每层的构造规则（bulk=队列内 z 的 GSVA；TCGA=先基因 z 后成员均值；单细胞=成员 log 归一化表达均值）
写进 Methods，声明三者不可混用。

> 检查清单本身（生成物是否来自生成器、改动是否可能被重建覆盖）见 references/generated-artifact-integrity.md。

## 另外三项"交付即被打回"的细节
- **突变分母**：只能用 mutation-profiled 样本列表作分母；措辞必须是
  "no mutation reported in the selected mutation data"，不要写 "explicit wild type"（未检测≠野生型）；
  未在 profiled 列表中的样本标 not assayed/unknown。
- **复用示例必须真跑**：随包示例要能在干净环境离线跑通，并提供 expected_output；
  demo 输入矩阵必须**包含被演示基因集的成员**（否则 GSVA 报 "No identifiers could be matched"），
  行名统一 `toupper()` 再匹配。
- **校验值与清单**：交付前生成 `file_inventory_and_checksums.csv`（file/bytes/rows/sha256）+
  `checksums_sha256.txt`，并在 Data Records 写明文件数与总大小。

## 可复用检测片段（R）
```r
# 设计分类审计
tab <- table(md$group)                      # 出现 Responder/NonResponder 等 → 非病例-对照
# 患者标识可用性
npid <- length(unique(pid[!is.na(pid) & pid != ""]))
real_id <- "patient_id" %in% names(md) && npid > 1
n_both  <- if (real_id) length(intersect(pid[grp=="Case"], pid[grp=="Control"])) else 0L
paired  <- real_id && n_both >= 4
```
```python
# 跨队列重复样本
import csv, collections
cnt = collections.Counter(r["sample_id"] for r in all_rows)
print([k for k, v in cnt.items() if v > 1])
```

## 自审产出物的去向
QC 表一律进数据包 `08_qc/`：design·dedup·patient-id·histology 排除日志·PH·共线性·共同基因敏感性·join 审计·
checksums。正文 Technical Validation 只引用结论（"no sample identifier is duplicated"、"0 PH violations"），
不要把结果式分析塞进去。

## 本用户工作方式（影响，执行顺序）
- **授权自主**：用户原话"调用一切工具和方法，需要什么就装什么、下载什么"——缺包/缺数据直接装、直接下，
  不要转成让用户操作；但装完要在报告里说明装了什么。
- **多轮迭代是常态**："还要改几轮呢" → 每轮都产出可复核的 QC 表 + ERRATA/报告条目，
  并让审计脚本自动扫描陈旧数字与占位符，避免下一轮重新发现同一问题。
- **外部标识最后补**："DOI 后面再补，先做好其它任务" → 正文先留
  `[DOI to be inserted after Zenodo deposit]` 占位，不要停工等 DOI。
- **执行节奏**：把"重建 ZIP + git commit + push + 统计"这类长链命令**拆成小步**跑——
  长链一旦触发审批拦截会整条失败（本次实测被 BLOCKED，且被要求不得重试同一命令）；
  被拦后停下来向用户要一句"可以"，再继续。
- 收工前必跑两条审计脚本（数字 vs 冻结表；占位符/陈旧数字/跨文件一致/连接键），**两项都 0 问题才宣布完成**。
