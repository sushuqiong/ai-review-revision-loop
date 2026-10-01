# 投稿系统里的"元数据问题"：缩写清单与字符上限

投稿系统（Editorial Manager 等）会扔出一堆手稿之外的必填问题，典型是
**"Please enter all abbreviations that have been used in this manuscript at least three or more times"**
（并给格式示例：`MELD:model for end stage liver disease; AST: aspartate aminotransferase`）。

这类问题的正确姿势：**先读上限，再决定答案形状**。用户会直接把限制原文甩过来
（本轮：`Limit 200 characters`）。不要先把完整清单写出来再被"不能黏贴"打回。

## 一、审计方法（`scripts/abbrev_audit.py`）

1. **整词计数**，别用普通计数：`(?<![A-Za-z0-9\-])ABBR(?![A-Za-z0-9])`
   ——否则 `HBV` 会把 `HBV-related`/`HBV-infected` 也算进去，`CH`/`CL` 这类碎片会假命中。
2. **正文与图注分开数**（图注如果在手稿文件内，它也算"in this manuscript"）。
   报告两个数：`body X + legends Y`。本轮有 3 项（FDR 1+4、ssGSEA 2+3、SVM-RFE 2+3）
   是**靠图注才够 3 次**的——保留在清单里（多列不会被追问，少列才会）。
3. **逐项检查它在正文里是否真的写出过全称**。本轮抓到 **AST、ALT 各出现 4 次但从未写出全称**
   （第一次出现是公式 `FIB-4 = (Age × AST) / (Platelets × √ALT)`）。
   **而期刊给的示例正好是 `AST: aspartate aminotransferase`——说明他们会对正文**。
   这类"用了没定义"的项必须单独提醒用户，并给最小改法（`aspartate aminotransferase (AST)`）。
4. **排除三类不是缩写的项**（列进去显得不专业）：
   - 基因符号（CXCL9、COL1A2、FAT1…）
   - 数据库 accession（GSE84044、GSE83148）
   - 拉丁缩写（e.g.、vs.、et al.）
   可选加项：`Q1: quartile 1; Q4: quartile 4`（四分位标签通常不列，交给用户决定）。
5. **罗马数字、面板字母、分相位编号（Phase I/II/III）不算。**

## 二、200 字符的背包问题（不要凭感觉砍）

格式按期刊示例（**冒号后不留空格**，省字符）：`ABBR:full form; ABBR:full form; ...`

单项成本 = `len(abbr)+1+len(expansion)+2`，量级 16–60 字符：
- `FIB-4:Fibrosis-4` = 16
- `AIP:atherogenic index of plasma` = 32
- `BMI:body mass index` = 21
- `NHANES:National Health and Nutrition Examination Survey` = 59 ← 一项顶四项
- `CHARLS:China Health and Retirement Longitudinal Study` = 55

⇒ **200 字符实际只放得下 4–7 项**，31 项绝无可能。做法：
1. 用 `scripts/abbrev_audit.py --limit 200` 跑**背包最优解**（目标：覆盖的出现次数最多）
   与"项数最多"两个解，作为参考而不是最终答案。
2. 给出**一个主推 + 2–4 个带确切字符数的备选**（让用户按"想突出哪个方向"选）：
   - 核心向 = 结局+暴露+疾病+主队列+主协变量
   - 机制向 = 换入转录组学词（GEO/ECM/DEGs）
   - 队列向 = 保住两个队列
   - 保守向 = 只列 4 项最核心
3. 明确写出**被挤掉的那些**（附次数），并说明"不是不重要，是字符不够"。
4. 给一句可直接回答编辑的话：
   `The submission field is limited to 200 characters; the full list of 31 abbreviations
   (each used ≥3 times) is available in the manuscript and can be provided in any format required.`
5. 主动提议把完整清单挂到 Cover Letter / 返修附信里（用户可能想全给）。

## 三、动手前先确认"当前文件状态"（本轮踩过）

用户会在两轮之间继续改文件。本轮审计缩写时发现手稿 **mtime 是当天 02:16**、段落数从 174 变成
191，**Figure legends 整节被恢复、并新增了 Supplementary Figure S1–S8 图注**——这意味着
上一轮"手稿里图注整节被删"的结论**已经过时**，基于旧快照给的建议会是错的。

⇒ 每次拿用户文件做审计/修改前，先打印 `mtime + 文件大小 + 段落数`，并与上一轮的记录对照；
不一致就重新读一遍再下结论。同理，改动过的文件要**重新核对"上次的修复还在不在"**
（本轮复核确认 4 处定点修复全部存活）。

## 四、其它常见必填项（同一类问题的处理模板）

| 系统问什么 | 怎么答 |
|---|---|
| Word count（正文/摘要） | **永远现算**，标题页与手稿必须一致；任何文字改动后立刻重算（删掉一个 17 词从句 → 5,562 改 5,545） |
| Abbreviations | 见本文第一、二节 |
| "Does your manuscript contain X?" 类是非题 | 按事实答，**不要为了好看改口**；不确定的先问用户 |
| Cover letter / Title page / Highlights 是否重传 | 返修一般不重传（除 Figure legends 等被要求项）——但要提醒用户"哪些栏位必须传" |
| 图片格式 | 主投矢量 PDF；**主动问要不要 PNG/TIFF**，别自己往交付目录里塞 |
