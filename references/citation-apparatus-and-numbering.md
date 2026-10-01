# 参考文献装置：采集 → 校验 → 首现编号 → 上标渲染（2026-09 实战）

## 触发场景
- 数据资源稿/Data Descriptor 或任何论文被指出"文献太少 / 正文没有引用标记 / 编号顺序与正文不符 / 输入数据集无法追溯"。
- 用户一句「做了这么多工作，参考文献才 15 篇吗？」就是本类问题的典型信号：**交付前必须自查文献装置的完备性，而不是等用户问**。

## 完备性清单（先枚举，再动手）
1. **数据库/平台**：GEO、GEOquery、GDC、cBioPortal、CELLxGENE Discover（平台论文，不要只写官网 URL）。
2. **数据来源逐条引用**：每个 accession（如 27 个 GSE）都要有来源文献；每个 TCGA 情境要有该情境的原文；每个单细胞数据集要有 dataset citation（collection ID / accession）。
   → 只写"详见 CSV 的 origin_pmid 列"**不算引用**，审稿人会直接指出违反 data-citation 要求。
3. **统计方法**：metafor、Hartung-Knapp（2001 与 2003 两条）、DerSimonian-Laird、Benjamini-Hochberg、Hedges 校正。
4. **软件/工具**：GSVA、xCell、limma、SciPy、NumPy、R、ggplot2、patchwork。
   经验量级：一个跨 26 队列 + 6 癌种 + 单细胞的数据资源稿 ≈ **50 条**；只有 15 条一定有遗漏。

## 采集：只用权威 API，禁止凭记忆写 DOI/PMID
- **PubMed E-utilities**：`esummary.fcgi?db=pubmed&id=<逗号分隔≤100>&retmode=json`（批量取标题/作者/期刊/年/卷/页/DOI）；`esearch.fcgi?...&retmax=8` 先找 ID。间隔 ≥0.3s。
- **Crossref**：`api.crossref.org/works?rows=5&query.bibliographic=<题名>`（带 `-A "<agent> (mailto:...)"`）。
- 结果落盘成 JSON（`<project>/results/<vN>_reference_metadata.json`），后续构建只读缓存、可复现。

## 校验闸门（不合格就丢弃，宁缺勿错）
- **题名相似度**：`difflib.SequenceMatcher(None, returned.lower(), expected.lower()).ratio() >= 0.85`，比"关键词子集"可靠（关键词法会漏掉正确条目，也会放进错误条目）。
- **加期刊 + 年份窗口**双闸门（例：TCGA 情境论文 = *Nature*/*Cell*/*Cancer Cell* + 对应年；SciPy = *Nat Methods* 2020）。
- **必须排除更正/勘误记录**：题名含 `correction` / `erratum` 的一律跳过。实战中 cBioPortal 2012 就曾被抓成 "Unknown author Correction: The cBio Cancer Genomics Portal…"，正确记录是 Cerami E 2012 *Cancer Discov*，DOI 10.1158/2159-8290.CD-12-0095。
- **集体作者**：Crossref 常缺作者（记录里 author 为空）→ 先用 PubMed 按题名补；TCGA 系列统一写 `The Cancer Genome Atlas Research Network`。构建完成后断言正文/列表中 **`Unknown author` 出现次数为 0**。
- 少数数据集/软件类条目无 DOI 是正常的：给 accession / collection ID / 版本号，不要编造 DOI。

## 编号规则：按正文首现顺序
- 在正文里先用**非数字键**占位 `⟪gsva⟫`、`⟪cohort_GSE32863⟫`，最后**单趟正则映射**成数字：
  ```python
  keys = sorted({m.group(1) for m in re.finditer(r"⟪([A-Za-z_0-9]+)⟫", md)},
                key=lambda k: md.index(f"⟪{k}⟫"))
  num = {k: i+1 for i, k in enumerate(keys)}
  md = re.sub(r"⟪([A-Za-z_0-9]+)⟫", lambda m: f"⟦{num[m.group(1)]}⟧" if m.group(1) in num else "", md)
  ```
- **不要用逐个 `str.replace` 重编号**：新编号会与"尚未替换的数字型占位符"碰撞，实测产生 `48 markers / 46 entries` 的悬空编号。
- 队列 accession 逐个上标：在 Input data 里写 `(GSE32863⟪cohort_GSE32863⟫, GSE19804⟪…⟫, …)`，让"每条文献都被引用"自动成立。

## 硬性自检（写进构建脚本，不通过直接 `sys.exit(1)`）
```python
cited = [int(x) for x in re.findall(r"⟦(\d+)⟧", md)]
assert sorted(set(cited)) == list(range(1, N+1))        # 连续、无空洞、无越界
assert set(markers) - {str(n) for n,_ in refs} == set()  # 无悬空标记
# 每条文献都被引用；缺失条目数的键要显式打印出来
```

## 上标渲染（md 只是文本，docx 才是交付）
- 构建 docx 时把 `⟦n⟧` 拆成独立 run 并设 `run.font.superscript = True`，其余文字常规 run。
- 交付前断言：**上标 run 数 == 文内标记数**（本项目 52/52）。曾经只在 md 里写成 `xCell8` 这样的普通数字，被审稿人一眼看穿"上标引用未落地"。

## 替换参考文献块时的两个坑
1. **旧列表必须裁掉**：`head, _, tail = md.partition("**References**")` 之后，tail 里仍跟着旧列表；要再定位下一个 `\n**` 段头，只保留它之后的内容，否则新列表会被插到旧列表**前面**（现象：文件里同时存在 52 条新列表和 15 条旧列表）。
2. **锚点会随版本漂移**：给生成器打的补丁经常锚点不匹配（例：正文实际写 `Gene Expression Omnibus`，我写的是 `(GEO)`；`handled by limma` 只存在于生成器、不在 md 里）。
   → 用**容错逐条应用**：每处改动单独 try，失败打印 `SKIP (anchor absent)` 并继续，最后统一写盘；不要因为一条锚点不匹配就整体中止（否则前面成功的改动全部丢失）。
   → 一旦交付稿 md 成为事实来源，**直接在 md 上做定点编辑**，不要再回头改生成器。

## 其他踩过的坑（同类任务通用）
- Python 关键字参数名不能含点：`significant_fdr_0.05=37` 是语法错误 → 用 `**{"significant_fdr_0_05": 37}` 或换名列。
- 原生 Windows Python **读不到 MSYS 的 `/tmp`**；要恢复"上一版正文"用 `git -C <repo> show HEAD:<path>` 取回（比临时备份可靠，因为提交过）。
- 期刊大纲会约束章节顺序：Scientific Data 要求 References 在 **Code Availability 之后**，Ethics 并入 Methods 子标题，且**不允许单独 `Abbreviations:` 段**（改为首次出现处行内定义）。
