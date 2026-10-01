# 参考文献与数据引用器具（journal-grade reference apparatus）

## 触发条件
手稿需要"可核验、格式合规"的参考文献表时：投稿前补全文献、被审稿人指出引用不足、
数据集稿需要 data citation、或用户质疑"参考文献才 N 篇吗？"。

**本用户预期（硬要求）**：文献数量必须与数据源规模匹配。27 个队列就要有 27 条来源文献逐条列出，
**不接受**"见 origin_pmid 列"这类指针。曾因只列 15 条被当面质疑。

## 流程
1. **先采集标识符**：登记表里的 PMID/DOI/accession；方法学与数据库代理由题名检索获得。
2. **抓真实元数据（禁止凭记忆写）**，两个源分工：
   - PubMed `esummary.fcgi?db=pubmed&id=<逗号分隔≤100>&retmode=json` → 取 `authors[0].name`、
     `title`、`source`、`pubdate`、`volume`、`pages`、`articleids` 中的 doi/pmid。
   - Crossref `https://api.crossref.org/works?rows=N&query.bibliographic=<题名>`（带
     `-A "tool/1.0 (mailto:<邮箱>)"`）→ 取 `title`、`container-title`、`volume`、`page`、
     `published-print/issued.date-parts`、`DOI`、`author`。
3. **严格校验后才采用**（宁缺勿错）：题名关键词子集 + 期刊名匹配 + 年份窗口 + `difflib.SequenceMatcher`
   题名相似度 ≥0.85。任一不过 → 丢弃并记录，不要凑数。
4. **渲染为 Nature/Sci Data 风格**：
   `Surname, A. B. et al. Title. *Journal Abbrev.* **Vol**, pages (Year). https://doi.org/10.xxxx`
5. **按正文首现顺序编号**，并落盘 `results/<...>_reference_metadata.json`（元数据留档，便于复核/重排）。
6. **数据集写 data citation，不写成论文**：
   - `CZI Cell Science Program. <数据集名>. *CZ CELLxGENE Discover* https://cellxgene.cziscience.com/collections/<uuid> (2025).`
   - `Author. Title. *Gene Expression Omnibus* https://identifiers.org/geo/GSE##### (Year).`
   - GDC 项目用 `TCGA-LUAD` 等标准 project ID 在 Data Availability 中点名（不必逐条进文献表）。

## 抓元数据的具体陷阱（全部实测踩过）
- **Crossref 会返回 "Correction:"/"Erratum:" 记录**，题名与原文几乎一致 → 必须显式过滤
  `if "correction" in title.lower()`，否则会引到更正通告（本项目曾把 cBioPortal 引成 Correction）。
- **集体作者记录（TCGA Research Network 等）在 Crossref 里 author 为空** → 抓不到作者；
  改用 PubMed（`"<期刊>"[Journal] AND <年>[dp] AND <关键词>`）或直接按已知命名写
  "The Cancer Genome Atlas Research Network."。
- **Crossref 题名可能带 HTML 标记与换行**（`<i>R</i>`、`<b>metafor</b>`）→ 写回前
  `re.sub(r"</?(i|b|sub|sup)>","",t)` 并把条目内换行折叠为空格。
- **PubMed esummary 作者名是 "Surname AB"（无标点）** → 规范化成 `Surname, A. B.`：
  姓与缩写之间一个逗号，缩写之间用空格（**不要** "Christenson, S., A."）。
- **带变音符的姓会击穿 ASCII 正则**（Hänzelmann/ä ö ü é）→ 用 `[^\W\d_]` 配 `re.UNICODE`，
  不要 `[A-Za-z]`。
- **`"<题名>"[Title]` 精确检索经常返回 0 条**（题名含冒号、副标题、括号时尤甚）→ 退回
  普通短语检索，或"期刊+年份+关键词"组合，再用相似度挑选。

## 编号与写回（两个必须遵守的机制）
- **单趟正则映射，不要逐个 `str.replace`**：先插入非数字键标记（如 `⟪gsva⟫`），算出首现顺序后
  `re.sub(r"⟪([A-Za-z_0-9]+)⟫", lambda m: f"⟦{num[m.group(1)]}⟧", md)` 一次性替换。
  顺序替换会出现键与新编号碰撞，产生 47/48 悬空编号。
- **只对文献块做处理，禁止整篇折叠空白**：曾用 `md=re.sub(r"\s*\n\s*"," ",md)` 把整篇折成一行、
  文献块被清空。正确做法：先 `partition("**References**")`，在块内按条目分块
  `re.split(r"\n(?=\d+\.\s)", body)`，条目内再折叠空白；替换旧表时用
  `re.search(r"\n\*\*", tail)` 定位下一节，丢弃旧列表正文。
- **写盘前加安全护栏**：`if len(entries)<40: raise SystemExit(...)`——否则一次坏解析就会把
  52 条文献整体覆盖为空（本项目发生过，只能从 git 恢复）。

## 交付前自检（写成断言，不通过就中止）
| 检查 | 判据 |
|---|---|
| 编号 | 文内编号恰好 = 1..N，无缺号无重号 |
| 覆盖 | 每条文献至少被引一次；无指向空号的标记 |
| 链接 | 每条都有 `https://doi.org/…` 或 `https://identifiers.org/…`/collection URL |
| 污染 | 无 `Correction`/`Erratum`、无 `<i>` 类残留、条目为单行 |
| 同步 | md/docx/pdf 同批产出；docx 上标 run 数 = 引用标记数 |
| 计数 | Data Availability 中 accession 数与登记表一致（本项目 26 + 2 + 3 + 1 + 6 项目） |
