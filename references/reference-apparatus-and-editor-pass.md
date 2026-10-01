# 投稿"附件装置"三件套：参考文献 / 编辑视角合规项 / 敏感性交代

来源：2026-09 EGFR 跨疾病资源 v14 定稿（作者一句 **"做了这么多工作，参考文献才 15 篇吗？"** 触发重构）。适用于任何要投 SCI 期刊的稿件，尤其数据资源稿（Scientific Data 等）。
配套：内容完备性清单见 `data-resource-descriptor-and-claim-audit.md` §13，格式合规见该文 §17，本文补齐**引用装置、编辑初审项、与"必须交代的聚合数字"**。

---

## 1. 参考文献：从"指针"升级为"完整装置"（本用户会直接质疑数量）

**触发信号**：正文只有方法文献 15 条，27 篇队列来源文献写成"see the origin_pmid column of cohort_registry.csv"。这在数据资源稿里**不合规**——数据集/队列必须作为可引用的文献条目出现。

**必须齐备的四类**（实测 52 条）：
| 类 | 内容 | 条数（实测） |
|---|---|---|
| 数据库/平台 | GEO、GEOquery、GDC（*NEJM* Grossman 2016）、cBioPortal（Cerami 2012 + Gao 2013）、CELLxGENE Discover（CZI 2025 *NAR*） | 6 |
| 数据来源论文 | 六个 TCGA 情境原文（LUAD/CRC/STAD *Nature*；PAAD *Cancer Cell* 2017；LIHC *Cell* 2017；ESCA *Nature* 2017） | 6 |
| 数据集引用（data citation） | 3 个 CELLxGENE collection（给 `https://cellxgene.cziscience.com/collections/<uuid>`）+ GEO 系列 `https://identifiers.org/geo/GSE…` | 4 |
| 队列来源文献 | **登记表里每个 accession 的 origin_pmid 逐条列出** | 27 |
| 方法/统计/软件 | GSVA、xCell、limma、metafor、Hartung 2001、Knapp & Hartung 2003、**DerSimonian-Laird 1986**、**Benjamini-Hochberg 1995**、**Hedges 1981**、SciPy、NumPy、R 版本、ggplot2、patchwork | 9–14 |

> 判据：正文出现"某方法/某数据库/某队列"就必须有可解析链接（DOI 或数据仓库 URL）。BH、DL、Hedges 这类**统计方法本体**最容易被漏（只引了 metafor）。

## 2. 元数据抓取：必须联网 + 严格校验，宁缺勿错

- **首选 PubMed E-utilities + Crossref 双源**：cohort 类用 esummary（有 `authors`/`volume`/`pages`/`doi`/`pmid`）；方法类用 Crossref `query.bibliographic`（`-A "build/1.0 (mailto:<邮箱>)"` 进 polite pool）。
- **校验规则（缺一不可，否则丢弃该条）**：题名关键词全部命中 + 期刊命中 + 年份落在窗口 + `difflib.SequenceMatcher` 相似度 ≥0.85。
- **两个实测踩坑**：
  1. **Crossref 会返回"Correction/Erratum"通告**（cBioPortal 那条就抓成了 `Correction: The cBio Cancer Genomics Portal…`）→ 必须显式排除题名含 `correction|erratum`，并回 PubMed 按题名取原文；
  2. **Crossref 未收录部分 TCGA 论文**（作者为 `The Cancer Genome Atlas Research Network`，标题索引差异大）→ 改用 PubMed "期刊+年份+关键词"检索（实测 `"Cancer Cell"[Journal] AND 2017[dp] AND pancreatic ductal adenocarcinoma AND integrated genomic characterization` 一击命中 PMID 28810144）。
- **作者串解析要容错**：PubMed 给 `Davis S`（无句点），Crossref 给 `Hänzelmann S.`（带句点且含变音符）——正则用 `[^\W\d_]` 类字符并先 `rstrip('.')`，否则一半条目落进 fallback 分支。
- **姓名格式**（Nature/Sci Data）：`Surname, A. B.`（缩写用**空格**连接），多作者加 ` et al.`；集体作者保留全称。

## 3. 编号必须"按首现顺序"且可机器验证

生成器形态（**不要**用"逐个 `str.replace(key, num)`"，会因数字键与新编号碰撞产生空洞）：
```python
keys = sorted({m.group(1) for m in re.finditer(r"⟪([A-Za-z_0-9]+)⟫", md)},
              key=lambda k: md.index(f"⟪{k}⟫"))          # 键用非数字（cohort_GSE32863）
num  = {k: i+1 for i, k in enumerate(keys)}
md   = re.sub(r"⟪([A-Za-z_0-9]+)⟫", lambda m: f"⟦{num[m.group(1)]}⟧", md)   # 单趟映射
refs = [(num[k], ENTRIES[k]) for k in keys if ENTRIES.get(k)]
```
**落盘前断言**（不通过就 `sys.exit(1)`）：
```python
cited = [int(x) for x in re.findall(r"⟦(\d+)⟧", md)]
ok = sorted(set(cited)) == list(range(1, len(refs)+1))   # 连续、无空洞、无悬空
```
**双向核验**：① 每个条目至少被引用一次（无"幽灵文献"）；② 每个编号都有条目（无悬空标记）。
**docx 端**：`⟦n⟧` 不是上标，必须拆 run 渲染——
```python
TOK = re.compile(r"⟦(\d+(?:,\d+)*)⟧")
for m in TOK.finditer(text):
    p.add_run(text[pos:m.start()]); r = p.add_run(m.group(1)); r.font.superscript = True; pos = m.end()
```
并断言 `superscript run 数 > 0`（实测 51；此前正文的 `xCell8`/`GSVA7` 只是普通字符，被审稿人一眼看穿）。

## 4. 破坏性事故与恢复（本会话真实发生两次）

| 事故 | 原因 | 恢复 / 防呆 |
|---|---|---|
| 参考文献块被清空 | `md = re.sub(r"\s*\n\s*", " ", md)` **全文折叠** → 条目全并成一行，解析到 0 条，随后把空块写回 | ① 折叠只作用于**文献块内部**（`head,_,rest = md.partition("**References**")` 之后再折叠）；② 解析后加 **`if len(entries) < 40: raise SystemExit(...)` 安全闸**，宁可不写盘也不清空 |
| 前几轮补丁白做 | 锚点式替换脚本里任何一条 assert 失败 → 整个脚本退出、**不写盘** | 容错逐条应用 + 末尾无条件写盘 + 打印 `applied/skipped`（见主参考文件 §16） |
| 内容被毁后无从回溯 | 手工改的 md 没有版本 | **正文落在 git 仓库里**：`git -C <repo> show HEAD:manuscript/DataDescriptor_v14.md > <md>` 取回上一版，再按顺序重跑补丁链（B2→B3→B4） |

## 5. 数据资源稿的"编辑初审项"（结构合规 ≠ 能过初审）

| 项 | 要求 | 说明 |
|---|---|---|
| 作者块 | 姓名 + 单位 + 通讯作者 + **ORCID**（+Keywords） | 本会话发现整块缺失；ORCID 未知时明确写"to be supplied by the author"，别空着 |
| **Data Availability 必须重复 accession 清单** | 不能只写"见 registry CSV" | 逐条列 26 个 GSE + 排除系列 + 3 个 collection UUID + GEO 补充系列 + 6 个 GDC 项目号 |
| Code Availability | 仓库 URL + **tag/版本**（如 `v14.0`）+ 包内 `11_code/` + `run_order.md` + 环境清单 | 只说"archived in the deposit"会被要求补 |
| 正文必须内嵌 Table 1 | 表格不能只在 SI | 用三线表渲染器插入 docx；正文加"see Table 1" |
| Technical Validation 不得含研究结论 | 加总起句"本节仅报告数据质量与一致性核查，资源不作生物学结论"，把突变率/拷贝数/阳性数重述为**注释层属性** | 数据描述符不发表结果 |
| 章节顺序 | …Usage Notes → Data Availability → **Code Availability → References** → Author Contributions → Competing Interests → Acknowledgements → (Funding 独立) → Ethics(建议并入 Methods) | 逐版核对标题序列 |
| Cover letter | 独立文件，进投稿 ZIP | 实测原包缺 |
| **投稿 ZIP 不放内部文档** | 评审处置/状态/Zenodo 指南等"先看这个_*.md"属内部件 | 只放正文+补充材料+图，另加英文 `00_READ_ME_FIRST.txt` |
| 补充材料 | **PDF**（docx 不合规）；百行级明细存仓库不叫 supplementary | `soffice --headless --convert-to pdf`；图件 PDF 用 `device=cairo_pdf` 内嵌字体 |

## 6. 敏感性分析：把"判断性选择"全部变成可核验的表

审稿人对任何"我们设定了阈值/家族"都会追问。做法是**把选择本身当成结果来报告**：

1. **阈值梯度**（而非单点）：单细胞每供者细胞数 ∈ {无下限, ≥10, ≥20, ≥50}，一次读入逐细胞分数、四档一次算完（避免重复读 h5ad）。实测显著数 **家族 BH 37/41/32/30、全局 20–35** → 写"5 倍阈值变化下同量级，结论不依赖阈值"。
2. **多重校正家族三口径**：①比较类型家族（主）②**细胞类型家族**（新增）③全局。实测 53/49/39/40 vs 37/41/32/30 → 写明"显著数随家族大小变化，故该层定位为描述性"。
3. **诚实解释副作用**：可检验数**非单调**（≥50 时"不可检验"反而降到 24）——细胞数要求越严，越多臂变成"供者不交叠"，非配对检验因此合法。这句话必须主动写，否则会被当成 bug。

## 7. 给"聚合数字"配一段可解释性（防止被外推）

事故形态：正文写"跨队列方向一致性 112/165 = 68%"，读者会当成"新队列的期望一致率"。
**做法**：算清分布再写死结论——实测 **53 个不一致对全部由"单一队列反调"决定**（21 对 k=2 的 1:1，32 对 k=3 的 2:1），且**没有任何一对 k≥5**（资源内每情境最多 3 队列）：
> "Disagreement is narrow rather than diffuse … every discordant pair is decided by a single cohort and no pair draws on more than three cohorts; the 68% is a fraction of stable pairs, **not an expected agreement rate for an unseen cohort**."

配套动作：① 点名集中处（实测情境 NAFLD 10 / IBD 7 / PAAD 6 / STAD 6；模块 FGFR_AXIS 7 / SRC_FAK 5 / ERBB_RECEPTORS 5 / TIE_ANGPT_AXIS 4）；② 举 1–2 个具体分叉（"asthma 的 SRC_FAK 两正一负"）；③ Usage Notes 加一句"k=2–3 时单一队列即可翻转方向，不可外推"；④ 明细随包（每对给正/负队列名与效应范围）并做补充表。
**判据**：凡正文出现"比率/一致率/复现率"，就必须能回答"分母是什么、k 多大、谁在拖后腿"。

## 8. 交付前机器检查（本类任务收尾四条）

```
md/docx/pdf 时间戳同一分钟   |  关键短语在 md 与 docx 中计数相等
docx 内嵌图 sha256 == 磁盘   |  superscript run 数 > 0
引用编号连续 1..N 且每条被引  |  条目数 == 清单条数（文件数/SHA 条数由 manifest 现算）
`sha256sum -c` 零 FAILED/零告警/零 stderr  |  投稿 ZIP 无内部文档、无上一版残留
```

---

## 9. 角标污染：accession 与引用编号必须物理隔离（v15 外部审稿人判为"最严重"）

**症状**（腾讯 Hy4 一眼抓到并逐条还原）：Input data 里每个 accession 后面紧跟引用上标，任何文本抽取/复制都读成 `GSE139113`、`GSE273424`、`GSE8747329`（= `GSE13911`+`[3]`、`GSE27342`+`[4]`、`GSE87473`+`[29]`）。审稿人会以为"编号都抄错"。

**修法三件**：
1. accession **一律纯列表**（逗号分隔、**不带任何上标**）；
2. 队列来源文献收进**一个区块引用**：`each accession is cited with its origin publication in the reference list (references 8–34) and in Supplementary Table S20`；
3. 逐 accession ↔ 文献的映射落到随包状态表（S20），正文不再逐条挂角标。

**编号器必须支持"块占位"**（块在首现顺序里**消耗 N 个编号**，否则后续编号空洞 + 大量"未被引用"条目）：
```python
num={}; counter=0; block=None
for k in keys:                       # keys 为 ⟪key⟫ 的首现顺序，含 "COHORT_BLOCK"
    if k=="COHORT_BLOCK": block=(counter+1, counter+len(cohort)); counter+=len(cohort)
    else: counter+=1; num[k]=counter
md=re.sub(r"⟪([A-Za-z_0-9]+)⟫",
          lambda m: f"⟦{num[m.group(1)]}⟧" if m.group(1) in num
                    else (f"⟦{block[0]}\u2013{block[1]}⟧" if m.group(1)=="COHORT_BLOCK" and block else ""), md)
```
反面实测（连踩两次）：写成 `num[m.group(1)]` 会对 `COHORT_BLOCK` 抛 `KeyError`；写成 `… if k in num else ""` 则**静默清空**该占位 → 正文没有引用、块编号变成"未被引用文献"、编号校验报 `uncited: 8–34`。

**校验器必须 range-aware**：`⟦8–34⟧` 要展开为 8..34 再与条目数比对（见 `scripts/verify_manuscript_integrity.py`）。

## 10. 计数自洽：把"每段数字都合理、合起来对不上"变成一张能加总的表

审稿人最爱抓的就是这一类（数据集 4 vs 5、26/27/28 三套数字、正文 107 files vs 清单 121）。三个动作：

| 动作 | 形态 | 实测 |
|---|---|---|
| **输入状态登记表**（S20） | 每个输入一行：layer / status / 是否入估计 / 是否可检验 / **原因** | 27 登记系列 + 3 下载未采纳 + 1 外部验证 + 5 单细胞 + 6 TCGA 项目 = 42 行 |
| **对账恒等式**（S21） | 让"每一系列的去向"能相加 | **31 = 26 病例-对照 + 1 应答 + 1 外部验证 + 3 未采纳**（此前四套数字无解） |
| **计数从 manifest 现算** | 文件数/校验条数/目录数在构建时注入正文与 README | v14 手写 "107 files" → v15 实测 **121**，一次构建就陈旧 |

- 单细胞口径统一写成 **"复核 5 / 处理 4 / 可检验 3"**（哮喘处理后无可检验比较；LUAD 全为瘤组织被排除）——abstract、Methods、图注、S20 四处同口径；图里出现 LUAD 而正文只说"四个数据集"即自相矛盾。
- 审计项建议直接写成断言：`26 cohorts`、`2711 assay records`、`1086 patients`、`12 platforms` 都能在正文里被 grep 到（数字从登记表现算后注入）。

## 11. 重建会把"已修好的坏条目"重新装回（要修元数据，不只修文本）

**事故**：v14 已把 cBioPortal 的 `Correction: The cBio Cancer Genomics Portal…` 换成原文（Cerami 2012, *Cancer Discov* **2**, 401-404, doi 10.1158/2159-8290.CD-12-0095），但**只改了渲染后的 md**；v15 从 `results/*_reference_metadata.json` 重编号 → 更正通告复活，被审计脚本抓到。

**铁律**：
1. 坏记录在**元数据层**修（`meta["crossref"]["cbio1"]={...}`），渲染层只是投影；只修文本 = 下次重建必复发。
2. 每次重编号后重跑**坏条目三扫**：`Correction:`/`Erratum`、空作者（`(?m)^\d+\. \. `）、未引用编号。
3. 集体作者条目（TCGA 六篇）Crossref 常无 authors → 元数据里显式写 `The Cancer Genome Atlas Research Network.`，否则正文出现 `30. . Comprehensive molecular profiling…`（Nature 系对参考文献格式极严）。
4. 表格/文档里的"数字+元数据"也有同类问题：**表脚本路径写死在旧版本目录**（`V14=…`）会让产物写进上一版文件夹，重建时静默出错 → 复制脚本到新版本目录时全局替换版本变量并核验输出路径。
