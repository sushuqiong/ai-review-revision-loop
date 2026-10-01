# 参考文献编号 / 计数对账 / 独立复算 —— 数据资源稿被打回的高频三大块

来源：EGFR 跨病种转录组资源稿 v14→v15（GPT6 + 腾讯Hy4 两份审稿意见落地）。三块问题在各稿中反复出现，且都属于"审稿人一眼能看到、但构建脚本很容易埋雷"的类型。

## 1. 参考文献体系：一次性建，不要反复打补丁

### 致命写法（本次全部踩过）
| 错误写法 | 后果 | 正确做法 |
|---|---|---|
| 编号用"逐个 `md.replace(f"⟦{k}⟧", f"⟦{n}⟧")`" | 新编号与尚未替换的键碰撞 → 编号空洞/悬空（曾出现 48 标记 / 46 条） | **单趟正则 + 映射函数**：`re.sub(r"⟪([A-Za-z_0-9]+)⟫", lambda m: f"⟦{num[m.group(1)]}⟧", md)` |
| 用 PMID 等**数字键**做占位符 | 数字键与分配出的编号互撞 | 键一律非数字（`cohort_<pmid>` / `res_recount3` / `cbio1`） |
| 队列/数据集文献"追加到列表末尾" | 编号 ≠ 首现顺序；正文引用不到 | 正文里放**一个块占位符**，展开为区间（如 `references 8–34`） |
| 正文 accession 后紧跟角标引用号 | 抽取/复制成 `GSE139113`（真值 GSE13911 + 上标 3），审稿人判为"编号抄错" | accession **纯列表**列全，来源文献用**区间块**引用，accession→文献映射放补充登记表 |
| `md = re.sub(r"\s*\n\s*", " ", md)` 想清理换行 | 整篇文档折成一行，**参考文献块被清空**（曾写出空列表） | 清理**只作用于目标块**；并加守护：`if len(entries)<40: raise SystemExit("ABORT")` |

### 收尾必须核验（不通过就中止，不写盘）
- 正文引用的编号集合 == `1..N`（**区间要展开**再比较）
- 每条文献至少被引用一次；无 `Correction:`、无 `Unknown author`、无空作者（`^\d+\. \. `）
- 条目单行、无 HTML/Markdown 残留标签（Crossref 标题常带 `<i>`/换行）

### 样式转换（Scientific Data / Nature 风）
- 论文：`Surname, A. B. et al. Title. *J. Abbrev.* **Vol**, pages (Year). https://doi.org/10.xxxx`
- 数据集（data citation）：`Author. Title. *Database* https://identifiers.org/geo/GSE… (Year).`；CELLxGENE 用 collection URL
- **从结构化元数据重建条目**（JSON 字段），不要正则解析"拼好的字符串"——首作者格式（`Davis S` vs `Barrett T.`）会直接把正则打穿
- 对已有条目做回连时用**最长题名包含匹配**（normalize 去标点/小写），比正则稳健

### 元数据获取与校验（禁编造）
- PubMed `esummary` + Crossref `works`，逐条**严格校验**：题名相似度 ≥0.85（`difflib`）+ 期刊/年份白名单；不达标**丢弃并记录**，不猜
- **Crossref 会返回更正通告（Correction/Erratum）**：曾把 cBioPortal 引成 "Correction: The cBio …"，必须过滤标题含 correction/erratum 的记录并优先用 PubMed
- 联盟署名论文（TCGA 等）Crossref 常**作者列表为空** → 用集体作者 "The Cancer Genome Atlas Research Network"（PubMed 可查到）
- 元数据文件要**写回 JSON**：否则下一次"重建参考文献"会把已修好的条目再次污染（本次 cBioPortal 被二次引入即此原因）

## 2. 计数对账：Data Descriptor 死于"每段都合理、合起来对不上"

- **唯一权威登记表**：`input_dataset_status.csv`，逐输入给出 layer / status / 是否进入估计 / 是否可检验 / 原因。所有"26 还是 27 还是 28""4 还是 5 个单细胞"的矛盾都由它一次性消解（单细胞实为"复核 5、处理 4、可检验 3"）。
- **流程账必须闭合**：本次唯一自洽式 `31 = 26（纳入）+ 1（treatment-response）+ 1（external-validation）+ 3（下载未采纳）`，做成 `curation_flow_reconciled.csv` 并补最后一行为"对账校验"。
- **正文里的文件数/SHA 数一律构建时从实时清单取**（曾手写 107 文件，实际已 121；改文件即漂移）。
- 正文数字与登记表要**程序化对照断言**（队列数、assay 记录数、患者数、平台数），不要靠人眼。

## 3. Technical Validation 的"独立性"与"分母命名"

- 交付一个**纯 Python 独立复算脚本**（不 import 项目管线）：从随包均值/SD 重算 1 个效应量、从随包 yi/vi 重算 1 个 REML+Hartung-Knapp 合并、对 1 个家族重算 BH。期望：合并/BH 可达 1e-16；**从四舍五入后的随包均值/SD 重算只能到 ~1e-5**——把该容差**写进表里**，否则会被当成不一致。
- **分母必须命名**：本资源用 RMS `sqrt((sd_case²+sd_control²)/2)`，不是经典合并 SD → 命名为 SMDH，并在正文显式说明"不是 Hedges g"。审稿人正是抓住这一点质疑"是否真是 pooled SD"。
- 说明"最大绝对差 = 0"：同输入 + 确定性算术 → 不构成独立证据，需另加独立实现。
- 配对/非配对合并规则要写明：是否同池、measure 是否逐队列标注、仅非配对作为敏感性、配对阈值（≥4 对）依据、经验 r 与 r=0.5/0.7 敏感性、**r 的不确定性不传播 → 列入 Limitations**。

## 4. 对抗性审查清单（投稿前逐项跑，见 scripts/manuscript_consistency_audit.py）
1. 规则/方法表述与代码实现方向一致（本次抓到转换规则**正文写反、代码正确**）
2. accession 未与引用数字粘连（`GSE\d{7,}` 应为 0 命中）
3. 无 Correction / Unknown author / 空作者；编号连续且全部被引用
4. 单细胞/数据集计数与登记表一致；流程账闭合
5. 每个被引用的补充表在表格文件里真实存在；S 编号区间统一
6. 正文文件数/SHA 数 == 实时清单
7. 校验链 `sha256sum -c` 全 OK
8. 关键措辞存在性断言（cautious comparability / Limitations / licence 拆分 / 分母命名）
9. docx 内嵌图与磁盘图逐字节一致；上标为真上标；标题无 Word 样式蓝线

## 5. 定位段：审稿必问"为什么不直接用 recount3 / ARCHS4 / DEE2 / refine.bio / Xena / Toil / GTEx"
一句可复用的应答："既有资源统一的是**表达矩阵层**；本资源统一的是**派生分数层**，并交付判断'两个分数能否比较'所需的覆盖度与可比性元数据。"逐个引用都要联网核验元数据（本次 refine.bio、GTEx 未通过严格校验 → **宁可不引**）。

---

## 6. 文献计量计数对账（narrative review 的 PubMed scan 被打回的三大块）

> 来源：2026-09 胃癌综述 Frontiers 大修。审稿人 1 第 3 条一句话点名四个主题对不上：
> 「年度值相加得 1,951 条 risk-model，而总数 1,812；950 vs 876；162 vs 148；690 vs 636。」

### 6.1 机制：**一条记录可以有两个出版年** —— 必须实测，不许推测

| 字段 | 含义 |
|---|---|
| `<ArticleDate><Year>` | **电子出版年** |
| `<PubDate><Year>` | **印刷/期号年** |

同一条记录两者**可以落在不同年份**。按年分组的序列会**在两个年份各计一次**，
而带日期范围的查询只计一次 ⇒ 年度和 > 总数。

**实测取证**（本项目 prognostic 主题）：

| 指标 | 值 |
|---|---|
| 解析记录 | 1,839 |
| 有电子年 | 1,592 |
| 有印刷年 | 1,839 |
| **电子年 ≠ 印刷年** | **147 条 = 8.0%** |
| 双计推得的年度和 | 1,839 + 147 = **1,986** |
| 审稿人观察到的超额 | 1,951 − 1,812 = 139 = **7.7%** |

**8.0% vs 7.7% 几乎吻合 → 机制证实。** 另外三个主题超额同量级
（8.4% 单细胞 / 9.5% 空间 / 8.5% AI-ML），一致性排除了"查询范围不同"的解释。

> ★ **不要用"可能是电子/印刷年重叠"这种推测句回复审稿人。**
> 去 `efetch` 把两个字段都取回来、算出百分比，用实测数字回答。
> 取数写法见 `cited-study-table-verification.md` 第 2.1 节
> （`efetch` 要 POST + 每批 ≤200 + 批间 sleep 2s）。
> ⚠️ PubMed XML **没有** `PubStatus="epublish"/"ppublish"`；用
> `pubmed`/`medline`/`entrez` 当出版年会得到"电子年 0 条"的假结果。

### 6.2 第二种不一致：**固定日期窗口内的索引滞后**

日期窗口（如 2019-01-01 → 2026-06-30）固定，但 **PubMed 持续把落在窗口内的新记录加进来**。
同一套查询在返修日重跑会多于首投日：

| 主题 | 首投日 | 返修重跑 |
|---|---|---|
| Public omics | 4,416 | 4,460 |
| Prognostic | 1,812 | 1,840 |
| Single-cell | 876 | 904 |
| Spatial | 148 | 159 |
| AI/ML | 636 | 662 |

**处理方式（不做的话 PMID 列表与正文数字对不上）**：
- 正文**保留首投日数字**并注明检索日；
- 补充材料**同时给出两套数字**并解释原因；
- **PMID 级记录集用重跑那套**（完整、当前可取），并写明它对应**重跑日**。

### 6.3 第三种：**"不在检索语料里" ≠ "不在 PubMed 里"**

S4 表原有一列 `likely_not_in_pubmed`，审稿人指出
"some records marked likely_not_in_pubmed are indexed there"。
按 DOI 逐条 `esearch` 复核 61 条后：**121/135 实际都在 PubMed 有索引。**

修法：**拆成三个独立字段**，并在补充文档写明区分理由：

| 字段 | 取值 |
|---|---|
| `pubmed_indexing_status` | `indexed_in_pubmed` / `not_found_by_doi_query` / `no_identifier_available` |
| `search_corpus_membership` | `yes`（PMID 落在该主题检索结果集内）/ `no` / `not_determined` |
| `topic_eligible_for_review` | 按题名判主题是否合格 |

复核要点：对缺 PMID 的记录用 `f'{doi}[DOI] OR {doi}[AID]'` 走 `esearch`。

### 6.4 第四种：**两个计数看起来矛盾，其实是两种定义**（S1 的 0 vs S3 的 46）

审稿人问："Table S1 里 external-validation mentions 是 0，Table S3 却是 46/100，怎么解释？"
查清后发现是**两种不同的量**，不是错误：

| 表 | 量的定义 |
|---|---|
| S1 的 `*_mentions` 列 | **主题交叉计数**：该 100 条记录中，**本身是**某主题（如 external validation 研究）的有几条 ⇒ prognostic 行为 0 |
| S3 的 `mentions_*` 列 | **术语提及标记**：题名/摘要里**提到**该术语的有几条 ⇒ 46 |

⇒ 一句"该记录是不是外验证研究"vs"该记录有没有提外验证"。
回复里要把**两种定义并列写清楚**，而不是含糊说"样本不同"。

### 6.5 交付自查断言

```python
checks = {
  "年度和>总数已解释":       "year-assignment rule" in supp_text,
  "两套计数都在":            str(first_run) in supp_text and str(rerun) in supp_text,
  "PMID 列表存在":           all(os.path.exists(f"Supplementary_File_S2_pmid_list_{t}_v14.csv")
                                 for t in topics),
  "S4 三字段分离":           {"pubmed_indexing_status", "search_corpus_membership",
                              "topic_eligible_for_review"} <= set(header),
  "无裸 likely_not_in_pubmed": "likely_not_in_pubmed" not in header,
  "S1/S3 定义已并存说明":      "topic cross-tabulation" in supp_text
                              and "term-mention flag" in supp_text,
}
```
