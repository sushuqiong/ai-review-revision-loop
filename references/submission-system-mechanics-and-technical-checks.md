# 投稿系统机制、技术检查与模板装配

来源：2026-09-30 课题2 v19 的 BMC Gastroenterology 技术检查（15 项）、
Frontiers in Endocrinology 模板装配、以及 J Gastroenterol 规格核对。

---

## 1. BMC/Springer Nature 技术检查（technical check）机制

### 1.1 它扫的是**主稿文件**，不是全部上传文件
**实测**：检查邮件列出 15 项"Table caption(s) missing for (Table Sx) **in the manuscript**"，
覆盖 S1–S13（补充表的编号），但**不报**主表 1–7。

**根因**：检查器**在主稿里**查找它从正文引用中发现的每一个 "Table X" 的 caption。
主表的 caption 就在表上方 ⇒ 通过；补充表的 caption 在 Supplementary 文件里 ⇒ 判为缺失。

**修法**：在主稿加一节 `Supplementary Material`，**逐条列出每个补充表/补充图的标题**
（本项目加了 S1–S13 + Figure S1–S3 共 16 条，每条 ≤15 词，放在 References 之前）。

**反向结论**：**补充材料文件本身没问题**。诊断这类报错时，**先比对"主表通过 / 补充表不通过"**
这一分布特征，就能立刻定位是"主稿缺清单"而不是"补充文件格式错"。

### 1.2 自动解析的**假报错**：把小数当表号
同一次检查还报了两项：
```
Table caption(s) missing for (Table 1.014) in the manuscript.
Table caption(s) missing for (Table 0.825) in the manuscript.
```
**不存在这两个表**。来源是正文中"表号 + 小数"相邻的句子：
- *"…0.826 in Table 2 and **1.014** in Panel B of **Table 6**…"*
- *"…reproduces the 0.826 of **Table 2**… gives **0.825**…"*

**处置**：**不要为假报错改稿**。回邮件/在系统备注里说明（模板可直接用）：
> Regarding items N and M ("Table 1.014" / "Table 0.825"): no tables with these numbers exist in
> the manuscript. These are automatic-parse artefacts — the strings are decimal numerical values
> that appear in text adjacent to cross-references to Tables 2 and 6. All tables in the manuscript
> and in the supplementary file carry captions.

**并在报告里明确告诉用户"这两项是假报错，重传后可能再现，不必追"** —— 否则用户会反复返工。

### 1.3 技术检查 ≠ 审稿意见
- 纯自动流程，**不涉及学术判断**；按清单改完重传即可。
- 邮件通常给短期限（本项目 **2 天**），并写 **"Do not change anything else in your manuscript"**
  ⇒ **只传它要求的那一个文件**，其余一律不动。
- 重传后**不要**指望系统再问"是否预印本"之类元数据问题 —— 那些只在**初次投稿**流程问一次，
  答案已存档。用户问"为什么这次没有预印本选项"时，答案是**正常**（不是故障）。

---

## 2. Frontiers 模板装配（官方 Word 模板）

### 2.1 章节顺序（模板硬要求）
```
Title → Author List → Affiliations → * Correspondence: + email → Keywords(5–8) → Abstract
→ Introduction → …（正文各节）…
→ Conflict of Interest → Author Contributions → Funding → Acknowledgments
→ References → Supplementary Material → Data Availability Statement
→ Tables（置末）→ Figure legends（置末）
```
- 模板 [25]：*"**Tables should be inserted at the end of the manuscript.**"*
- 模板 [20]：*"**Figure legends should be placed at the end of the manuscript.**"*
  （图本身**单独上传**，系统自动嵌到文末）
- **首页必须写字数与图表数**：*"Please indicate the number of words and the number of figures and
  tables included in your manuscript on the first page."* ⇒ 加一行
  `Word count: 9,301 (main text, excluding the abstract, references, figure legends, table captions and declarations); 7 tables; 3 figures.`
- **字数口径**：仅算正文（+脚注+文内引用），**不含**摘要/章节标题/图表注/基金/致谢/参考文献。

### 2.2 从官方模板导入样式时的**三个坑**（本项目全踩到）
1. **模板的 `Heading 1-5` 引用 `numId`，但模板包里没有 `numbering.xml`** ⇒ 原样移植会产生
   **悬空编号**（或与正文手工编号叠加成 "1. 1. Introduction"）。
   ⇒ **导入后必须剥离 `w:numPr` / `w:ind`，并把 `basedOn` 从 `ListParagraph` 改回 `Normal`。**
2. **模板样式自带主题色**（本项目 `Title=17375E` 深蓝、`Heading1=365F91`、`Heading2/3=4F81BD`、
   `Caption/Subtitle` 同系）。⇒ 目标是**全黑正文**时，要**样式级**（不只 run 级）把 `w:color`
   改成 `000000`，并清 `w:themeColor`；同时清 `Title` 的段落下框线 `w:pBdr`。
   **只改 run 级会漏** —— 颜色来自样式继承。
3. **`link` 到未导入的字符样式** ⇒ 一并剥离 `w:link`。

### 2.3 "装进模板"的两种做法与取舍
- **激进**：以模板为基底，清空占位内容，再把正文段落 + 表格对象搬进去。
  爆炸半径大（本项目 7 表 + 3 图 + 200+ 段），且会改变 `tblStyle`。
- **稳妥（本项目采用，并**如实告知用户**）**：以稿件为基底，**注入模板的 styles.xml + theme1.xml**，
  把段落样式 id **按名重映射**（如 `36→Title`、`2→Heading1`、`3→Heading2`），页面设置套用模板。
  验证：段落文本数、表格单元格数、表格数、内嵌图数**前后完全一致**。
- **副作用要主动披露**：改 `tblStyle`（如 `"12"→"TableNormal"`）会使表 XML 的 **md5 变化**，
  即使单元格文本 100% 一致。**报告里要写清"md5 变化的唯一原因是样式属性 token"**，
  避免用户误以为数值被改。

---

## 3. 投稿包组装与同步纪律

- **名词区分**：BMC 用 "Additional file N"；Frontiers 用 "Supplementary Material"（**单数**）；
  J Gastroenterol 用 "Online Resource N"。**全文（含 STROBE、Title page）必须统一**。
- **上传槽位映射表**要写进交付说明（每个文件 → 哪个槽位），并给"建议用 PDF"这类格式指引。
- **打包后必给 sha256 清单**（工作副本 vs 上传副本）：
  本项目**两次**出现"上传目录与工作副本分裂"。典型症状：`04_投稿材料/Cover letter.docx` 是旧版，
  而 `★待上传_Upload/03_Cover letter.docx` 是新版 ⇒ **极易投出旧文件**。
- **打包脚本不要留在被冻结的版本目录里**；用户说"不要改动 vN"时，连脚本追加也算改动。

---

## 4. 交付前程序化自检（在终验清单里加这几条）
```text
[ ] 主稿是否含每个补充表/补充图的 caption（技术检查最容易卡这里）
[ ] 通知类报错先判别真假：不存在实体的（如 "Table 1.014"）判为解析伪影，不改稿
[ ] 目标刊字数口径：含不含参考文献？据此判断需不需要砍
[ ] 首页是否写了字数与图表数（Frontiers 要求）
[ ] Tables / Figure legends 是否在文末（Frontiers 模板要求）
[ ] 声明节是否拆成独立 Heading 1 且顺序符合模板
[ ] 模板样式颜色是否已全改黑（样式级，非 run 级）
[ ] Additional file / Supplementary Material / Online Resource 称谓全文统一
[ ] 上传目录与工作副本 sha256 逐一 SAME
```
