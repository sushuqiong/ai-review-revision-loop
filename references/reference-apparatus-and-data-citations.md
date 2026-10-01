# 参考文献与数据引用：10 类真实事故与硬规则

来源：v14→v16 三轮打磨。每一条都是**实际发生过并被外部审查抓到**的。

## 硬规则（违反任一条＝整轮返修）

1. **绝不手打文献。** 从 PubMed E-utilities + Crossref 抓取，严格校验后才用：
   `题名关键词命中 AND 期刊/年份窗口命中 AND 题名相似度 ≥ 0.85`，不达标就丢弃、绝不猜。
2. **按首现顺序编号，并用断言锁死**：正文引用号必须恰为 1..N、无空洞、每条文献至少被引用一次。批量同类型数据集（如 27 篇队列来源）用**区块引用**（`references 8–34`），并断言区块展开后条数正好等于登记表条数。
3. **accession 绝不与上标数字相邻**。`GSE13911` + 上标 `3` 在文本提取时变成 `GSE139113`（另一个真实编号）——外部审查者据此报「26 个编号全部被污染」。做法：accession 纯列表 + 区块引用 + 登记表映射。
4. **工具名与引用号之间留空格**，避免 `GSVA51517`、`xCell v1.1.04949` 式粘连。
5. **标识符保护**：DOI / UUID / URL / accession / 版本串里的连字符**永远保持连字符**；只有数字区间（0.33–0.62、页码 527–529）用 en dash。做全局替换前先保护/剥离标识符——本轮一次「短横线全量替换」把 DOI 里的连字符改成了 en dash（`s13059-021-02533–6`），必须回修。

## 10 类事故

| # | 症状 | 根因 | 修法 |
|---|---|---|---|
| 1 | cBioPortal 那条引到了 **Correction 更正通告** | Crossref 精确题名匹配命中更正记录 | 剔除题名含 correction/erratum 的记录；相似度阈值 |
| 2 | metafor 条目**题名被截断**（"Conducting Meta-Analyses in"） | 用正则二次解析已拼好的字符串 | 条目一律**从结构化元数据字段重建**，不重新解析成品串 |
| 3 | 六篇 TCGA 论文**作者为空** | Crossref 记录无作者列表 | 显式集体作者映射：`The Cancer Genome Atlas Research Network.` |
| 4 | 文献里出现 `<i>R</i>`、`<b>metafor</b>` | 元数据题名带标记语言 | 入库时 + 写列表前**双重清洗** |
| 5 | 队列文献只写「见 CSV 的 origin_pmid 列」 | 把数据来源当指针而非引用 | 必须真引用（Sci Data 硬要求）；编号进区块 |
| 6 | 编号空洞（正文 47/48，列表 46 条） | 用「逐个 replace」编号，数字键与新编号碰撞 | **单趟正则映射** + 编号后断言连续性 |
| 7 | 正文引用数与列表数不等 | 某些 marker 指向不存在的条目 | 断言 `cited == 1..N` 且 `every entry cited` |
| 8 | 数据集被写进图里却无来源标识 | 只在图注里出现 | 每个数据集在状态表里给出 collection/版本/DOI；被排除的给排除原因（本轮 LUAD 117,266 细胞） |
| 9 | 许可范围过宽 | 「派生数据全部 CC-BY-4.0」覆盖了再分发的 GEO/TCGA 矩阵 | **按来源拆分许可**；不可再分发时只给 accession+校验+下载脚本 |
| 10 | 缺少与既有 harmonization 资源的对比 | 没回答「为什么不用 recount3/ARCHS4/DEE2/refine.bio/Xena/Toil/GTEx」 | 加一段定位：既有资源统一**表达矩阵层**，本资源统一**派生分数层**并交付判断可比性所需的覆盖度/可比性元数据；按需引其原始论文 |

## 版式（Nature / Scientific Data 风格）

```
Surname, A. B. et al. Title sentence case. *Journal Abbrev.* **Vol**, pages (Year). https://doi.org/...
数据引用 : Author. Title. *Repository* https://identifiers.org/geo/GSE12345 (Year).
软件     : R Core Team. R: ... version 4.4.1. *R Foundation for Statistical Computing* https://www.R-project.org (2024).
```

- 期刊缩写查表，不臆造；卷号加粗、页码用 en dash、DOI 写成 https 链接。
- 26 队列规模的资源稿，40–60 条文献属正常。
- 抓取脚本见 `scripts/`（本 skill）与 playbook 仓库 `scripts/refs_and_manifest_reference.py`。
