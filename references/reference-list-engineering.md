# 参考文献表的"工程化"重建（Reference-list engineering）

**触发**：审稿人指出"文献太少/编号错位/作者为空/角标与文字粘连/引用了更正通告"，
或需要把参考文献升级为 Nature / Scientific Data 数据引用格式。

## 编号规则（首现顺序）与"区块引用"
- 编号 = 正文首现顺序；**每条都必须被引用**。
- 当一批文献（如 27 篇队列来源）只在同一处成组引用时，用**区块占位符**：
  1. 正文写 `... (references ⟪COHORT_BLOCK⟫) ...`；
  2. 编号时把该占位符**当作一个位置**，占 `len(block)` 个号；
  3. 替换阶段把它展开为 **`⟦N–M⟧`**（不要先清空再补，否则引用号会消失 —— 实测踩过）。
- 校验必须**理解范围**：解析 `⟦12⟧`、`⟦8–34⟧`、`⟦3,7⟧`，把范围展开成数字集合，再断言
  `cited == set(1..N)` 且 `uncited == none`。

## 重编号实现纪律（血泪）
- **禁止**用连续字符串替换 `md.replace(f"⟦{key}⟧", f"⟦{num[key]}⟧")`：当 key 是数字（如 PMID、
  数据集编号）时会与"新分配的小整数"碰撞，造成空洞（实测出现 `[1, 38]` 悬空）。
- 正确做法：**单趟正则 + 映射函数**
  `re.sub(r"⟪([A-Za-z_0-9]+)⟫", lambda m: f"⟦{num[m.group(1)]}⟧" if m.group(1) in num else "", md)`
- key 一律用**非数字、可读**的名字：`geo`、`cohort_GSE32863`、`res_recount3`、`tcga_luad`。

## 元数据抓取的四类坑（Crossref/PubMed）
1. **更正通告 / Erratum**：按题名检索可能返回 `Correction: ...` 记录，必须过滤
   （`if "correction" in title.lower() or "erratum" in title.lower(): skip`），并改用原始论文记录。
2. **集体作者缺失**：TCGA 这类论文在 Crossref 常无作者 → 渲染成 `30. . Title`（空作者）或
   `Unknown author`。解决：对这类条目显式写集体作者（如 `The Cancer Genome Atlas Research Network.`）+
   DOI 链接；其余空作者用 PubMed 按题名回补。
3. **题名含 JATS/HTML 标记**：Crossref 题名可能带 `<i>R</i>`、`<b>metafor</b>` → 必须清洗
   `re.sub(r"</?(i|b|sub|sup|em|strong|span)[^>]*>", "", title)`。
4. **未通过校验就丢弃**：题名相似度 ≥0.85 + 期刊 + 年份三重校验，不合格**宁可不引**；
   期刊缩写要有显式映射表，表里没有的期刊**保留全名**（不要猜缩写）。

> ⚠️ **必须同时清洗"元数据 JSON"与"渲染文本"**：只改渲染文本，下一次重建会从 JSON 里
> 把坏条目（如更正通告、带标签题名）**重新引入**。实测 cBioPortal 条目因此复发两次。

## Scientific Data / Nature 数据引用格式
- 论文：`Surname, A. B. et al. Title. *Journal Abbrev.* **Vol**, pages (Year). https://doi.org/10.xxxx`
- 数据集（GEO 系列等）：`Author. Title. *Gene Expression Omnibus* https://identifiers.org/geo/GSE193816 (2022).`
- 单细胞集合：`CZI Cell Science Program. <label> single-cell dataset. *CZ CELLxGENE Discover* https://cellxgene.cziscience.com/collections/<uuid> (2025).`
- 软件/R：`R Core Team. R: a language and environment for statistical computing, version 4.4.1. *R Foundation for Statistical Computing* https://www.R-project.org (2024).`
- 定位段（回答"为什么不用 recount3/ARCHS4"）：**不硬引未核验资源**；只引校验通过的
  （recount3/ARCHS4/DEE2/Xena-Toil 已可核），未通过就让该资源不出现在参考文献里。

## 角标与文字的"粘连"（审稿人会当成抄错编号）
- 症状：正文出现 `GSE139113`、`GSVA51517`、`xCell v1.1.04949` —— 实际是 accession/工具名 + 上标号。
- 根治：**accession 一律纯文本列表**，来源文献走区块引用（`references 8–34`）+ 状态表链接；
  工具名与角标之间**加一个空格**（`GSVA ⟦15⟧`），避免复制/解析时粘连。

## 收工校验块（可写成脚本，每次重编号后必跑）
- 编号连续 `1..N`、无空洞、无悬空；每条文献至少被引用一次（范围引用按每个号算被引）
- 无空作者（`^\d+\. \. `）、无 `Correction:`、无 `Unknown author`、无 HTML 标签
- 每条都有可解析链接（https://doi.org/... 或 pubmed/identifiers.org）
- 文献条数、上标数量、docx 内上标 run 数三者对得上
