# 参考文献装置 + Data Descriptor 合规（Sci Data / Nature 风格）

适用：数据资源稿（Data Descriptor）、需要 40+ 条真实文献的综述/资源论文、任何"参考文献被抓错/编号乱/正文与文献表脱钩"的返修。

## 1. 采集真实元数据（绝不编造）

- **队列/数据集来源文献**：PubMed E-utilities `esummary.fcgi?db=pubmed&id=<逗号批量≤100>&retmode=json`，每批 sleep 0.3–0.4 s。字段：`authors[0].name`、`title`、`source`、`pubdate`、`volume`、`pages`、`articleids[].idtype=="doi"`。
- **方法/工具经典文献**：Crossref `api.crossref.org/works?rows=N&query.bibliographic=<题名>`（加 `-A "<tool>/1.0 (mailto:<email>)"`）。
- **校验门（必须过才采用，否则丢弃并报告）**：
  1. 题名相似度 `difflib.SequenceMatcher` ≥ 0.85（精确题名检索）；
  2. 期刊 + 年份窗口 + 关键词包含（如 TCGA 各情境必须 *Nature*/*Cancer Cell*/*Cell* 且年份对）；
  3. 命中多条时取最高分并打印候选，人工可核。
  **宁可少一条，不可错一条**——错引的代价远大于缺引。
- **已知陷阱**：
  - Crossref 会把 **Correction/Erratum 通告**排在原文前面（cBioPortal 2012 就中过），必须过滤题名含 `Correction|Erratum` 的记录；
  - Crossref 题名可能带 `<i>R</i>`、`<b>` 等标记与内嵌换行 → 先 `re.sub(r"</?(i|b|sub|sup)>","",t)` 再压空白；
  - PubMed `esummary` 的作者字段是 `"Surname II"`（**无句点**），所以**不要正则解析已拼好的引文串**，要从结构化字段重建；
  - 变音符（Hänzelmann）会破坏 `[A-Za-z]` → 用 `[^\W\d_]` + `re.UNICODE`；
  - TCGA 记录无个人作者 → 署 `The Cancer Genome Atlas Research Network`；CELLxGENE 署 `CZI Cell Science Program`。

## 2. 格式（Nature / Sci Data）

```
论文      Surname, A. B. et al. Title. *Journal Abbrev.* **Vol**, pages (Year). https://doi.org/10.xxxx
数据集    Himes, B. E. et al. Title. *Gene Expression Omnibus* https://identifiers.org/geo/GSE193816 (2022).
          CZI Cell Science Program. <描述>. *CZ CELLxGENE Discover* https://cellxgene.cziscience.com/collections/<uuid> (2025).
软件      R Core Team. R: a language and environment for statistical computing, version 4.4.1. *R Foundation for Statistical Computing* https://www.R-project.org (2024).
```
- 缩写首字母**只留姓后一个逗号**：`Christenson, S. A. et al.`（不是 `Christenson, S., A.`）→ 缩写位用 `" ".join(c+"." for c in initials)`。
- 期刊缩写表按需给（`Nucleic Acids Research→Nucleic Acids Res.`、`New England Journal of Medicine→N. Engl. J. Med.`、`Controlled Clinical Trials→Control. Clin. Trials`…），**不认识的不要猜缩写**，保留原名。

## 3. 编号与文内引用（本次两轮审稿都抓这里）

- **首现顺序编号**：把每个来源做成非数字键 `⟪key⟫` 插到正文，再**单趟** `re.sub(r"⟪([A-Za-z_0-9]+)⟫", lambda m: f"⟦{num[m.group(1)]}⟧", md)`。
  **绝不要循环 `md.replace(f"⟦{k}⟧", ...)`**——数字键会与新编号碰撞（本项目出现过 46 条文献却 48 个标记、编号 47/48 悬空）。
- 断言：`sorted(set(cited)) == list(range(1,N+1))`；每条文献至少被引用一次；无悬空号。
- **数据集/队列文献必须有文内锚点**：在 Input data 段把 accession 逐个列出并挂编号（`GSE32863⟦17⟧, GSE19804⟦18⟧, …`），不要写成"见 CSV 的某列"（Sci Data 不接受指令式引用）。
- docx 里必须渲染成**真上标**：`run.font.superscript=True`，并断言上标 run 数 > 0（正文写 `xCell8` 只是普通字符，审稿人会抓）。

## 4. Data Descriptor 编辑合规清单（Sci Data）

| 项 | 要求 |
|---|---|
| Data Availability | **必须复述 accession 清单**（不能只指向随包 CSV）；逐条给 GEO/CELLxGENE/GDC 项目号 |
| Code Availability | 仓库 URL + **release tag**（如 `tag v14.0`）+ 包内 `11_code/`、`run_order.md`、`environment.txt` |
| 作者信息 | 作者行 + 单位 + **通讯作者与邮箱** + **ORCID**；ORCID 先联网核验：`curl -H "Accept: application/json" https://pub.orcid.org/v3.0/<id>/personal-details`，比对注册名（连字符差异可接受） |
| 关键词 | 单独 `**Keywords**` 行 |
| Table 1 | **内嵌进正文 docx**（不能只在 SI），正文有引用 |
| Technical Validation | **只报数据质量/一致性**；不得出现生物学结论（突变率、显著状态数等要重述为"注释层属性"并声明不作生物学结论） |
| 缩写 | **首次出现处定义**，禁止 `Abbreviations:` 小节（指南明文禁止） |
| 章节序 | …Usage Notes → **Data Availability → Code Availability → References** → Author Contributions → Competing Interests → Acknowledgements → **Funding**（独立）；**Ethics 放 Methods 子标题** |
| 计数 | 目录数（"eleven folders"）、文件数、SHA 条数、S 表编号一律**由 manifest 现算**后回填，再重建 |
| 投稿包 | 只放正文/补充/图 + 英文 `00_READ_ME_FIRST.txt`；**内部处置笔记不进投稿包** |

**本用户署名口径（EGFR 数据资源线）**：第一作者 [First Author]，通讯作者 [Corresponding Author]（corresponding@example.com）；全稿用复数 `the authors`。

## 5. 收尾交付物（让用户"填空即出终版"）

1. **Cover letter**（英文，抬头写全作者 + 落款通讯作者 + ORCID）；
2. **投稿系统填写对照单**：Article type / Title / Abstract 全文 / 作者表(ORCID+角色) / Keywords / Data & Code Availability / Competing interests / Funding / Ethics / 上传文件清单 / 仓库元数据 / 投稿前自检命令，逐栏可复制；
3. **DOI 插入脚本**：`scripts/F2_*_insert_doi.py <DOI>` 一次性替换占位符 → 重建 docx/PDF → 重算清单与 SHA-256 → 重打包 → `git tag -f v14.0` + push → 打印 READY。

## 6. 文本手术事故与护栏（本次真踩过）

- **禁止** `re.sub(r"\s*\n\s*", " ", md)` 作用于**整篇**文档——会把全稿折成一行、参考文献块被解析为 0 条并写成空块。只对**目标块**做折叠。
- **破坏性重写前加护栏**：解析后 `if len(entries) < 40: raise SystemExit("ABORT…")`，再落盘。这条护栏是在把 52 条文献清空之后才加的。
- 需要按编号强制修正个别条目时，**按块切分**解析：`re.split(r"\n(?=\d+\.\s)", body)`，再 `re.match(r"^(\d+)\.\s+(.*)$", ch, re.S)`，条目内 `re.sub(r"\s+"," ",t)`。
- f-string **不能含反斜杠**（先在外部算好再插值）；`re.sub` 替换串写 `r"\17"` 会报 *invalid group reference*，要用 `r"\g<1>7"`。
- **内联 `python -c` 会触发审批门**（超时即阻断）→ 一律把脚本写成文件再执行；损坏文件从 git 恢复：`git show HEAD:<path> > <path>`。
- 干跑验证脚本（本目录 `scripts/verify_reference_apparatus.py`）在任何文献手术前后各跑一次。
