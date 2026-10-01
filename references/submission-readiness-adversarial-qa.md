# Submission-readiness adversarial QA checklist (docx manuscript, post-AI-review)

Used at the END of every AI-review→revision round before claiming "done". User repeatedly
asks "你确定没有遗留问题？能逐条回应审稿人意见了吗？" — run THIS, then an independent
subagent mapped against the reviewer's numbered opinions. Subagent self-reports are NOT
verification; re-verify the machine-checkable items yourself.

## 0. Map every reviewer opinion → evidence (table in your reply)
Reviewers (GPT-6, Claude) write numbered opinion lists. Produce a ✓/✗/△ per item with the
paragraph/table location as evidence. A "✗ = opinion was wrong, code is right" is still a
legit outcome IF you verified against primary source (CDC XPT/codebook), not assertion.

## 1. Machine QA on the .docx (python-docx; NEVER the patch tool — docx is a zip binary)
- Multi-run paragraph replace: `p.runs[0].text = new; for r in p.runs[1:]: r.text = ""`
  (runs are split by formatting; only touching one run leaves stale text behind).
- Delete paragraph: `p._p.getparent().remove(p._p)` — but read the WHOLE paragraph first;
  over-broad delete conditions (e.g. "if '.txt' in text") silently removed a legit
  cross-reference paragraph this session.
- Insert at anchor (before a heading / before References): build `OxmlElement('w:p')`,
  `anchor._p.addprevious(new_p)`, wrap `Paragraph(new_p, anchor._parent)`, add run.
- Re-inserting figures repeatedly (3×) left 3 orphan media (rels said 6 images, body used 3).
  Clean: zipfile — read word/document.xml, collect used `r:embed="rIdN"`, drop rels entries +
  `word/media/*` not referenced, rewrite word/_rels/document.xml.rels. Verify doc reopens and
  inline_shapes/blip count == intended (3).
- Figure order in docx XML: check paragraphs before "References" read Figure 1 → 2 → 3 with
  its blip after each label; naive `reversed()` + addprevious scrambles order.
- Word/character counts: count the four abstract bodies with labels stripped (Background…/
  Conclusions…), exclude the Keywords paragraph. In-label vs out-of-label counts differ by
  exactly the 4 labels — report the no-label number (≤350 for BMC).
- **Figures actually embedded, not just legends.** A generator can emit "Figure 1./2./3."
  legend paragraphs and embed ZERO images — v13 was reviewed as complete because the legends
  existed. Fingerprint: `doc.part.rels` has no `image` entries while legend text is present.
  Check `sum(1 for p in doc.paragraphs if p._p.findall('.//'+qn('a:blip')))` equals the
  expected count before declaring the manuscript figure-complete.
- **Verify the embedded images are the CURRENT files, and correctly paired.** Extract
  `word/media/imageN.png` from the .docx zip and hash-compare against the on-disk
  `FigN_vN.png`. Catches stale figures re-embedded from a previous version and label↔image
  swaps that text-only checks cannot see.
- **Every table needs a three-point FORMAT audit — tables appended in a later round silently
  miss format properties the earlier ones carry.** Text-only review passes (all numbers are
  present and correct) while the reader sees a broken table. Assert per table, at XML level:
  (a) **closing rule** — the last row's `w:tcPr/w:tcBorders/w:bottom` must exist and not be
  `nil`/`none`; a three-line table missing its bottom rule reads as "unfinished";
  (b) **explicit font size** — every run must carry `w:sz`; cells without one inherit the
  document default and render visibly larger than their neighbours;
  (c) **width ≤ the page's own text width** — sum `w:tblGrid/w:gridCol` and compare against
  `sections[0].page_width − left_margin − right_margin`. **That figure differs per document**:
  2.54 cm (1 in) margins ⇒ **15.93 cm** usable in the manuscript, but 2.0 cm margins ⇒
  **17.0 cm** in the supplementary — so a supplementary-width table pasted into the manuscript
  overflows the margin. Seen: 6 supplementary tables missing the closing rule, 450 cells
  missing an explicit size, 3 supplementary tables at 17.4 cm (> 17.0), and main-text Tables 2
  and 4 at 15.98 / 16.31 cm (> 15.93). Fix by rescaling columns **proportionally to the target
  sum** (content untouched) and by inserting the missing `w:tcBorders` / `w:sz` elements.
  The user notices this before you do — "Table S12 和 S13 的显示有问题，不能像 S1 到 S11 那样
  呈现吗？" — so run it proactively on every docx, both main text and supplementary.

## 2. Citation hygiene (Vancouver first-occurrence order)
- Scan text before "References": collect `[n]` tokens in first-occurrence order; require
  strict 1..N ascending and no orphan refs (every listed ref cited). Regex must ignore
  funding strings like "[2023]1" (not a citation).
- ANY mid-manuscript citation insert (e.g. adding ref [28] in Methods) can silently break
  the first-occurrence order of later refs (29→38→30 seen) — re-run the check after every
  citation edit; fix by moving the offending cite or renumbering.

## 3. Number consistency vs authoritative anchors
- Re-derive key numbers from RDS/TSV/log (never trust prose) and grep the docx for STALE
  values from the previous manuscript version (e.g. old N3 M3 OR 2.335/2.350 must not
  survive where 2.130 is current). Sweep abstract, tables, figure captions, cover letter,
  title page statistics together — they drift independently.
- Meta/pooled period estimates often use a DIFFERENT (reduced) covariate set than per-layer
  main models — when meta OR ≠ main OR (2.335 vs 2.130) annotate "meta uses common
  cross-period covariate set; not directly comparable to Table 2", else readers misread.

## 3b. Submission-package cross-file sync (a 6–8-docx package drifts apart)
Each round rebuilds SOME of the package, so sync failures concentrate here. In the v12→v13
audit ALL four "high" findings were sync/cleanup — none were data problems — and every one
would be caught by editorial triage. Audit explicitly:
- **Title byte-identical** across manuscript, Title page, Cover letter, Highlights,
  Plain-English summary, STROBE, Supplementary. Typical drift: one file keeps the previous
  subtitle, another drops a qualifier ("survey-weighted"), a third differs in capitalisation.
  Fix: put the canonical string in a single constant, overwrite every occurrence (paragraphs
  AND table cells), then assert equality across all files.
- **Supplementary numbering must match the main-text declaration.** When the supplementary
  gains/splits/merges tables, renumber three places at once: the main-text declaration
  paragraph, the Title-page stat line ("Supplementary material: Tables S1–S8 …"), and every
  STROBE row citing S-numbers. Seen: main text declared S1–S7, the built supplementary had
  S1–S8, and STROBE still carried the previous version's numbering.
- **AI-generated docx residue** — grep the built docx (paragraphs AND table cells) for:
  build-script names (`_build_*.py`), internal data paths (`0X_数据/`, `_supp_out_*`),
  provenance sentences ("no estimate was entered by hand"), CJK left inside generated tables
  ("（仅常数）"), and previous-version artefacts ('earlier version', old title, stale numbers).
  Editors read these as machine-assembled. Strip before submission.
- **Correct-but-suspicious is not a bug**: the same quantity in two contexts with different
  denominators (633 ≥75-y at the PIR step vs 628 in the final analytic sample) is FINE when
  each is labelled with its step. Verify the labels; do not "fix" it by flattening the numbers.
- When a supplementary table's row count disagrees with the prose ("nine combinations" vs a
  6-row table), either add the missing rows or qualify the sentence — do not leave the
  mismatch, and do not silently reword to hide it.
- **Re-read every paragraph you batch-replaced.** A global `str.replace` pass rewrites prose
  you never looked at and can duplicate or truncate clauses. Seen in v13: rewriting the
  supplementary cross-reference produced "…listed in Table 3 of the main text and in Table 3
  of the main text of this file; the underlying estimates are given in the source table the
  outcome-definition sensitivity output." — a doubled clause plus a verb-less fragment. After
  ANY replace pass, re-extract the text and grep for repeated phrases and dangling clauses.
- **Every cross-reference must resolve.** Programmatically collect `Table N`, `Table SN`,
  `Figure SN`, and `Table N, Panel X` tokens and confirm each target exists (and that the
  named panel exists). Seen: an edit inserted "(Table 2, Panel B)" while Table 2 has only
  Panel A — the correct target was Table S3.
- **A prose "clarification" must not silently change table values.** While reconciling
  "nine combinations" with a 6-row table, the P-series row was left carrying the fully-linear
  M4 values (1.326 / 1.300) under an "age spline + linear BMI" header, against the source
  TSV's 1.284 / 1.271 — i.e. the fix introduced the very inconsistency it was meant to remove.
  Rule: whenever an edit touches a table AND its footnote, re-derive the row values from the
  source TSV and check that the footnote's worked example matches the rows.
- **Per-endpoint denominators legitimately differ.** dx / surgery / combined endpoints have
  different non-missing sets, so a four-category table built on the dx-non-missing subset can
  show sx = 417 while the outcome-specific sensitivity table shows 441 (and combined 509 vs
  534). Both are right. Do not flatten them — add a footnote stating each endpoint's own n,
  and for NHANES III name the age-branch recovery explicitly.

- **Word/stat counts on the Title page are DERIVED values — recompute them after the last
  text edit, never carry them forward.** Seen: title page declared 5,561 while the manuscript
  measured 5,562 (a user-side text cleanup added one word), and after a later 17-word clause
  deletion the correct value became 5,545. Recompute the count, then write it — the number
  follows the text, never the reverse. (Count the abstract as the four structured bodies
  without their labels; that reproduces an author's declared "245 words" exactly.)
- **A number in the Results prose must exist in the artefact it cites.** Seen: Results cited
  "per log-unit increase in stiffness (β = −0.061; 95% CI −0.107 to −0.014; P = 0.014;
  Supplementary Fig. S8C and Supplementary Table S2)" while Table S2 held only the two
  threshold exposures × 4 models — the cited model existed in NEITHER the table nor the
  Fingerprint: enumerate every "(estimate … Supplementary Table SN / Fig. SN)" pair and
    confirm the named artefact actually contains that row/panel.
    **升版后特有的变体 —— 版本漂移型孤儿数字（v21 实测，§3d 换口径的伴生缺陷）**：数值**真实存在，
    但只存在于上一版的源码文件里**，本版交付包无任何表/图承载。实测：正文写 "under the earlier
    spline specification it was +0.0064"，而 Table 4 只有 matched（Panel A）＋ linear（Panel B）
    两个面板，+0.0064 只存在于上一版 `v13_auc_markers.csv`。上面那条"引用的产物里没有这个数"的
    指纹**抓不到它**（数字确实能 grep 到，只是在本版产物之外）。判据：把正文每个独立数值确认在本版
    的主稿表格、补充材料表格、或图内文字层中至少出现一次；只在旧版源码出现 ⇒ 补进某个产物，
    或在原地标注其口径与样本使其可追溯。
- **A CI quoted in the prose must equal the CI in the table you built for the same model.**
  Seen: Results 3.2.3 "95% CI: −0.173 to −0.093" (the author's original text) vs my
  Supplementary Table S1 "−0.170, −0.096" (my recomputation) — same β = −0.133, CI differed by
  0.003. Rule: when a table reproduces a model already reported in the author's prose, the
  PROSE value is canonical unless you have re-derived the entire model; make the table match.
- **A range quoted in prose must be the actual min/max of the table.** Seen: prose
  "FDR 0.0012–0.011" vs Table S3's eight significant genes actually spanning 0.00034–0.005.
- **"Every stratum shows X" must hold for every stratum actually plotted.** A prose claim
  "within every age decade the high-FIB-4 group had a lower AIP" was false in the 30–39 band
  (n = 13, P = 0.376) — and that band was a panel in the supplementary figure. Either reword to
  the strata that hold ("from 40 years onwards") or drop the claim; never leave a claim the
  figure can contradict. Also: when the author asks NOT to self-expose, prefer deleting an
  optional sentence you introduced over qualifying it into visibility.

## 3c. After the USER hand-edits the delivered files (highest-risk window)

Delivery is not the end state. Seen: the user renamed `01_/02_/03_/07_*.docx` →
`Manuscript_revised.docx` / `Point-by-point response.docx` / `Title_Page_revised.docx` /
`Figure_Legends_revised.docx`, ran a global "special characters → ASCII" cleanup
(en dash → hyphen, straight → curly quotes, **all Unicode superscripts stripped**), and
deleted the in-manuscript Figure-legends section.

- ⇒ **NEVER re-run the build scripts to apply a later fix.** They rebuild from the pristine
  original and silently discard every user edit. Apply fixes **in place, at run level**, on the
  user's current file. Full recipe, pitfalls and the change-marking protocol:
  `references/docx-inplace-editing-and-change-marking.md`.
- **Backup first, diff after.** `shutil.copytree(delivery, "_backup_before_fix")` before the
  first edit; afterwards diff backup vs current and paste the complete change list in your
  reply ("只改了这 4 处，其余一字未动"). That diff is the only credible proof nothing else moved.
- **The cleanup breaks scientific notation.** `P = 1 × 10⁻⁴` → `1 × 10-4`,
  `2.9 × 10⁻⁷` → `10-7` (3 places here). After any user-side cleanup, grep `10\s?-\s?\d` and
  restore the superscript (or write `10^(-4)`).
- **User-side edits move the word count** → re-derive the Title-page number (see §3b).
- **"只检查、不要改" means read-only.** When the user asks you to audit files they intend to
  submit ("如果有的话，也不要做任何改动，而是详细告诉我，我决定是否手动改动"), produce findings with
  file + paragraph locations and make ZERO changes. If they then select items by number
  ("2、3、4、5"), fix exactly those and state explicitly which numbers you left untouched.

## 3d. 换口径 / 升版时的"传播同步"（v20→v21 的实质错误全部出自这里）

一轮改动的核心往往是**把某个敏感性口径提升为主分析**（或反之）。此后旧口径会以三种方式残留：

- **⭐ 摘要把被降级口径当主结果报（本轮唯一实质性错误，且方向是"少报"，故极易漏检）。**
  主分析从"约束协变量效应"（P=0.072，不显著）换为"放宽模型"（P=0.0026，显著）后，正文已写
  "the relaxed model is the primary heterogeneity analysis"，摘要却仍写 "No statistically
  significant cross-period heterogeneity was detected (P=0.072)" —— 摘要比正文**弱**，不是夸大。
  **指纹：摘要里某个检验的 P 与正文 "primary analysis" 段落里同一检验的 P 不是同一个数。**
  检查法：抽出正文每一句 "is the primary …" / "primary analysis"，取该处 P/估计值，再到摘要里
  找同一检验的数字；不一致即错。修法：**双口径并置、主分析在前**，敏感性在后，同时保留
  "P–L 直接比较无差异"这类谨慎结论（不可反向夸大成"最新周期反转"）。
- **独立交付的 `Tables/` 文件沿用上一版**（数值仍是旧口径）。本轮 `课题2v20/Tables/Table 2.docx`
  与 `Table 6.docx` 仍带 1.326 / 0.826 / 1.244。**规则：`Tables/*.docx` 必须从当前主稿 extract，
  绝不可复制上一版目录**；提取法见 §3e。提取后逐表与主稿正文 table **逐行断言文本相等**。
- **"旧值该保留"的情形必须显式标注口径，别当残留删掉。** 升版后旧口径作为 function-form
  sensitivity 保留是正确的，但每处都要带口径标签（"under the linear age/BMI functional form"）。
  终审扫描的通过条件不是"旧值 = 0 次"，而是"**旧值出现处均带口径标注**"——本轮主稿 3 处 +
  补充材料多处旧值全部合规，若按"旧值即错"处理会把应保留的对照值删掉。

### 两套分析样本 → 每个图注/表注都要回答"这是哪一套"
本轮并存 association sample（P 2,885 / L 2,092 / N3 5,918，**不需**腰围）与 discrimination
sample（2,846 / 2,056 / 5,724，**需**腰围）；连同一个比较的 NHANES III 20–74 岁子集在两处 n 也不同
（关联 5,290 / 353 dx vs 判别 5,141 / 340 dx）。**两者都对**，但图注不写明用哪一套即为缺陷——
用户会直接点名要求补（"补充 Fig3 图注说明"）。规则：任何出现样本量的图注/表注，读到它的人必须能
判断是关联样本还是判别样本；两套并存时在同一句里给出对照并说明差异原因（腰围要求）。

### 相邻表格的脚注符号冲突
Table 1 与 Table 2 都用 `† ‡` 但含义不同（年龄分支 / 跨时代定义差异 vs 匹配形式 / 线性敏感性）。
各表注自包含说明时风险低；若目标期刊要求全篇符号唯一，需在排版阶段改符号。终审把它列为
"**低风险观察项**"并主动告知用户，不要默默忽略，也不要擅自改（改符号要连动表格内标记，风险 > 收益）。

### 改动摘要后必须重算词数（哪怕只加一个从句）
为修上面的口径问题给摘要加一句 → 339 词涨到 **378**，超 Frontiers 350 上限。任何摘要编辑后都要
按四段 body 重新计数并断言 ≤ 上限。压缩时**删 hedge 与重复限定语，不删数字、CI、人群范围限定**
（本轮 378→339，关键 P 与 CI 全部保留）。

## 3e. docx 定点手术：换图 / 插行 / 提取独立表

> **操作主源另见** `references/version-bump-figure-and-table-sync.md`（含 zipfile 替换代码、
> `set_cell` 的 `xml:space="preserve"` 细节、从下往上插行、Tables 重抽后的验证断言、
> 以及"旧值都是有意保留"的终审判定）—— 该文件与本节的换图/插行/重抽内容重叠，以它为准，
> 本节只保留要点与 §3d 的配套提醒。

交付后升版常需要"只动图、只动几行"，重跑构建脚本会毁掉用户手改（§3c）。三个可复用动作：

- **替换内嵌图：先比宽高比，再决定要不要动 `wp:extent`。**
  ① 解压 → 读 `word/_rels/document.xml.rels` 建立 `rId → word/media/imageN.png` 映射；
  ② 用段落顺序确定每个 `r:embed` 对应哪张图——**`Figure N.` 图注顺序 ≠ media 编号顺序**
  （本轮 Fig2→image3、Fig3→image4；用户特意提醒"非 image2"，映射错了就是把 Fig3 贴到 Fig2 的位置）；
  ③ **比较新旧图宽高比**：
  - 比值一致（本轮 1.0079 vs 1.0075、1.5063 vs 1.5073）⇒ 直接替换 media 文件，`wp:extent` 不动，
    图不会变形；
  - 比值不同 ⇒ 必须同步改 `wp:extent` 的 `cx/cy`（EMU，914400 EMU = 1 in），否则拉伸变形。
  ④ 重写 zip 时遍历原 `infolist()` 逐条写出以保留全部其他成员；替换后重开并断言
  `word/media/imageN.png` 像素尺寸 == 新图尺寸。
- **往三线表里插行：`copy.deepcopy` 现有行再改单元格，不要手搭 `w:tr`。** 这样自动继承边框、
  字号、列宽，避免"新行少一条线"（§1 的格式漏洞）。`new_tr = copy.deepcopy(src_tr);
  src_tr.addnext(new_tr)`，再对每个 `w:tc` 清空其首个 `w:p` 子元素并写入新文本；
  **从下往上插**（`sorted(rows, reverse=True)`），否则先前插入的行会让后续行号偏移。
- **提取独立 `Tables/Table N.docx`**：遍历 `doc.element.body.iterchildren()`，遇 `Table N.` 标题段
  记录，取**紧随其后的 `w:tbl`** 与其后的表注段，连同标题一起写进新 Document（表格用
  `copy.deepcopy` 挂到 `newdoc.element.body`）。这是唯一能保证独立表文件与主稿数值一致的方式。

## 4. Reviewer statistical traps that recurred across rounds (survey/cross-era papers)
- Weight ↔ population mismatch: text may claim "morning/evening fasting weights WTPFSD6"
  while code/data restrict to morning (WTPFSD6>0 ⇔ MXPSESSR=1). Verify the coding, then
  write methods text EXACTLY as verified — don't add plausible-sounding qualifiers
  ("evening-session 36.8 h fasting") that contradict it.
- Questionnaire wording changes across cycles: same column name ≠ same question. Download
  each cycle's XPT and read the question text. Example: ≥2017 NHANES alcohol module has NO
  ALQ101; official ALQ111 = "ever had ≥1 drink"; P-cycle files can carry a column NAMED
  ALQ101 that equals official ALQ111 (legacy rename). Describe semantics ("ever drinker"),
  don't trust names.
- CI vs P on different inference distributions (normal z CI with Wald F/t P) — unify and
  state (e.g. exp(b ± t_{0.975,ddf}·se), ddf = degf).
- Interaction tested in model A (total-association, no age/BMI) but claimed for model B
  (M4 beyond age+BMI): run BOTH frameworks separately and state which P belongs to which.
- Association analysis vs discrimination analysis covariate sets drift (association got
  reconstructed covariates; AUC base B still used the old reduced set) — unify by re-merge.
- Coding "correction" claims: a pure constant rescale inside a per-SD analysis is
  inference-irrelevant (log10→ln of TyG scales index by constant; per-SD results identical)
  — don't sell it as a methodological contribution; find the real bug instead.
- "fully adjusted" overclaims — rename to "sociodemographic and lifestyle-adjusted".
- **Questionnaire skip logic / age-branch structural blanks** (highest-yield NHANES-III trap,
  and the single biggest finding of the v12→v13 round): outcome items can exist in TWO
  age-branched versions with the branch chosen by a check item. NHANES III Section J
  gallbladder: HAJ0=1 (17–74 y) → HAJ9 (diagnosis) / HAJ12 (surgery); HAJ0=2 (≥75 y) →
  HAJ16 / HAJ17. Reading ONLY HAJ9/HAJ12 silently converts every ≥75-y answer into
  "missing outcome". Fingerprint: the analytic sample's max age lands far below the survey's
  real range (74 vs 90) and a step labelled "outcome missing" eats a suspicious ~10% of the
  cohort (2,710 people here). Fix: `dx <- ifelse(HAJ0==1, HAJ9, HAJ16)` (same for surgery),
  then report BOTH the full-age result and a common-age-range restriction (20–74) — the
  truncated version is what earlier rounds silently reported. Before trusting any coded
  outcome, read the codebook for "CHECK ITEM … REFER TO AGE" branches.
- **Design-based bootstrap must be Rao–Wu, not a raw multinomial multiplier**: drawing m_h
  PSUs per stratum with weights = drawn counts (`rmultinom(1, size=m_h)`) and NO within-
  stratum rescale underestimates the variance by (m_h−1)/m_h — with the usual 2 PSUs/stratum
  SEs come out ~0.707× too small and CIs too narrow. Correct: draw m_h−1 PSUs with
  replacement and scale replicating PSUs by m_h/(m_h−1) (`survey::as.svrepdesign(type=
  "bootstrap")` or a hand-written equivalent). ALWAYS cross-check bootstrap SE against the
  Taylor-linearised SE (svyglm / svytotal): ratios should sit ≈0.99–1.19; a 0.67–0.81 ratio
  is the fingerprint of the uncorrected scheme. Then recompute every CI and paired
  comparison that depended on it — here the correction widened ΔAUC intervals enough that
  ALL 70 paired comparisons lost significance and the "index is superior" claims evaporated.
  Re-normalising weights to mean 1 is NOT a substitute for the within-stratum rescale.
- **Never compare per-SD ORs of differently-scaled indices** to argue one "carries" more of
  the association. Different indices have different SDs, so 1 SD is a different increment.
  Convert to a common increment first: `OR_common = OR_b ^ (SD_common / SD_b)`. Worked
  example: full-GLM7 (SD 0.657, OR 1.244) vs its metabolic component (SD 0.534, OR 1.184) →
  1.184^(0.657/0.534) = 1.231 ≈ 1.244 — the apparent "drop" was pure scale. After
  converting, all 9 layer×specification ratios fell in 0.999–1.020 (<2%), retracting the
  earlier "age and BMI carry most of the M4 association" claim. Also do not call an
  algebraic split a "residual" (it is not orthogonal to age/BMI) — call it a "component".
- **Unit systems inside a log10 product are per-SD irrelevant but not interchangeable**:
  pmol/L vs µU/mL and mmol/L vs mg/dL differ by multiplicative constants, which become an
  ADDITIVE constant inside log10 and drop out under within-layer z-scoring — so per-SD
  estimates are identical across unit systems. But raw index values and published
  thresholds must NOT be mixed between systems, and standardisation does not remove
  assay-method differences (e.g. the Aug-2021–Aug-2023 TG glycerol-blanked assay change, or
  which of Friedewald / Martin-Hopkins / NIH-Eq2 was used for calculated LDL). Say this
  explicitly; do not sell a constant rescale as a methodological contribution — that is
  where a real bug hides.
- **Reusing someone else's published index/formula — three things a reviewer checks, all of
  which were wrong once here**: (a) **attribution** — if the origin paper is another team,
  write "X et al. proposed <index>"; "our group previously reported" is a factual error the
  reviewer will catch by opening the cited PDF; (b) **units** — original may be pmol/L and
  mmol/L where you use µU/mL and mg/dL (constant inside log10 ⇒ per-SD results unchanged, but
  raw values and any published cut-offs are NOT interchangeable); (c) **sample overlap** — if
  their paper already covered your cycles, say so; calling your cycles "additional" is false.
  Ship a **variable-mapping table** (name / unit / measurement method per cycle) as a
  supplementary deliverable — it settles (b) in one place and pre-empts "which assay/which LDL?".
- **A correction that kills your own headline is a result, not a setback.** When the Rao–Wu
  fix widened every interval so that all 70 paired comparisons lost significance, the correct
  move was to report it plainly and reframe the paper around "strong total association, limited
  incremental discrimination" — the reviewer's own closing note said such an honest evaluation
  is publishable. Never soften a corrected CI, and never let a retired claim survive in the
  abstract, discussion, or cover letter (grep for it after the recompute).

## 5. Author/affiliation/funding/declaration block (fill from user, don't invent)
- First author + co-first (†, "contributed equally") + corresponding (*, listed LAST) +
  author order per user's explicit instruction. Affiliations numbered; map superscripts in
  title page and manuscript identically.
- Funding copied verbatim from the user's file; COI "none"; ethics "secondary analysis of
  de-identified public-use data, no additional approval".
- CRediT: draft from roles; corresponding author carries funding acquisition + supervision.
- Fill in main manuscript, Title page, AND Cover letter signature — the three drift apart.

## 6. Cover-letter wording for FIRST submission
Never write "revised manuscript / reviewer 'GPT-6' / Response to Reviewers file" — the
internal AI loop is real but the journal sees a first submission; phrase as "prior
independent methodological review". Signature = first author + corresponding author (name,
dept, institution, city/country, email).

## 7. Figure deliverables on disk (this user asks for vector twice a round)
- Ship **PNG at 300 dpi AND a vector PDF** for every figure, side by side in the figure
  folder. The user has explicitly requested the vector PDF set ("把图片补 PDF 矢量版"); treat
  it as part of the deliverable, not an optional extra.
- Generation pattern that works: one plot script calls `savefig(... .png)` then
  `savefig(... .pdf)` back-to-back (drop `bbox_inches='tight'` when the layout is hand-placed
  in axes coordinates — it can shave the intended margin to zero).
- Programmatic margin check before calling figures done (PIL, no vision model needed):
  binarise (`a < 245`) on the greyscale PNG, take `np.where(ct.any(axis=…))` for rows/cols and
  assert all four margins > 0. A margin of 0 px means content is flush to the canvas edge and
  will look clipped in print. Also plot-element overlap self-checks belong INSIDE the plot
  script (bbox intersection over `ax.texts`) so a rerun reports `0 overlap` itself.
- Prefer running the check on every figure after ANY rerun — a fix that widens a column can
  push the rightmost label to the edge (seen: right margin collapsed to 0 px, fixed by
  extending the axes xlim past the text rather than moving the text).
- **`figsize` must equal the TARGET PRINT SIZE, not "whatever fits the content".** A figure
  built 14–18 in wide with 11–14.5 pt text is legible on screen and illegible in print: a
  journal column is ~3.4 in (single) / ~7 in (full width), so at 7 in the effective font size
  falls to ~4–5 pt, far below the ≥8 pt production floor. Set `figsize` to ≤7.2 in wide and
  size fonts against THAT canvas (body ≥8 pt, inner notes ≥7 pt, titles ≥9 pt); if it no longer
  fits, cut content (merge rows, shorten labels, abbreviate and define in the caption) — never
  enlarge the canvas. A `MIN_FS` assertion is worthless if it is asserted on an oversized canvas.
- **Vector PDFs must use TrueType, not Type 3.** matplotlib's default emits Type 3 glyph
  procedures that some publisher preflight tools flag as "font not embedded". Set
  `matplotlib.rcParams['pdf.fonttype'] = 42` (and `ps.fonttype = 42`) at the top of every plot
  script. Verify programmatically: decompress the PDF stream and require
  `count('Type3') == 0` and `count('FontFile2') > 0`. Re-run after regenerating AND re-embed
  the fresh files into the .docx (see the stale-image hash check above).

### 7b. 图件几何自检的三个坑（本轮实测，每个都浪费过一轮迭代）

**(1) 中文字体 bbox 天生高 → 绝对不要用"bbox 相交"判重叠。**
`Microsoft YaHei` 的 span bbox 高度 ≈ 1.5 × 字号，两行 9 pt 文字行距 17 pt 时 **bbox 仍然相交**：
本轮 Fig1/Fig2 第一次跑出 5–6 处"重叠"、第二次 3 处"行距过紧"，**全部是假阳性**，真实排版完全正常。
两个正确判据：
- **同基线横叠**：按 y 中心分组，只在**同一组内**比较 x 区间是否相交（真正会撞的只有同一行里相邻的文本块）；
- **行距过紧**：相邻两组 y 中心距 < 0.85 × 两者最大字号 才报警。
改成这两条后：0 重叠 / 0 过紧 / 0 越界，且与肉眼一致。

**(2) 越界要判"超出纸张"，不是"超出我设定的文本框"。**
LibreOffice 对 CJK（含标点悬挂）会把行尾字符放到文本框架外几 pt：本轮 docx 有 10 处文本
超出 2.6 cm 边距 **6 pt（2.1 mm）**，但页面宽 595 pt、文字最右 528 pt，**没有被裁切**。
⇒ 判越界用纸张边界；否则你会去"修"一个根本不存在、用户也看不见的问题。
（真裁切的形态是文字被页边截断或图片出血被切，与本条不同。）

**(2b) 但"越界 0"不等于干净 —— 必须同时查"贴边"。**
矢量图件的页宽常是**小数**（实测 `page.rect.width = 453.54`，查看器显示成 454），
于是 `x1 > W + 1` 这个判据会**正好漏掉 1 pt 级的超界**，报出"越界 0"的假绿灯。
两条判据一起用：
```python
oob  = bbox.x1 > W + 1 or bbox.x0 < -1 or bbox.y1 > H + 1 or bbox.y0 < -1  # 超出纸张
near = bbox.x1 > W - 3 or bbox.x0 < 3                                       # 贴边/压框线
```
加 `near` 后本轮**立刻暴露 3 行超界文字**（两处是内容行长 1 pt，一处是文字压在框线上）。
`附近` 报出来的东西比 `越界` 更实用：它同时抓"压框线"和"贴页面边缘"，
而且**都不会被裁切**，属于"评委/编辑一眼看出不齐"的那类观感缺陷。

**(2c) 图内总标题 / 图例 = 与图注重复，用户明令禁止。**
用户标准原文：「**图 Lancet/NEJM 风（无重叠/越界/裁切；图内上方下方都不放图例与总标题，
图例单独成 Word）**」。本轮 6 张图（报告 4 + 综述 2）图内顶部都留了一行总标题，
与图下/文末 `图 N　标题` **完全重复** → 一律删除。
- 判据：图内 **top 6% 区**出现与图注同义的整行文字即为标题；
- 删除后**确认留下的顶区文字是内容性标签**（"阶段 1　准备"、"第一层·公共数据发现"），这些要留；
- **例外：standalone 单页图（如单独交付/上传的 PRISMA 流程图）保留标题是正当的** ——
  它本身就是一份独立图件，要跟用户说清这个区别，别一刀切。

**(3) 往图里加数字前先量空间，加完回读文字层。**
把 `β (95% CI)` 塞进半宽 panels → 文本在面板右缘被截成 `-0.133 (-0.170, -0.09`（数字断在句中，
正好是用户最反感的"显示不全"）。两种可行做法：
- ① 只放 **β 与 P 两列**（95% CI 由误差线表达、精确值放附表），并在脚本里实测
  **"β 列右端 x < P 列左端 x"**（本轮 429.6 < 442.0 ✓）；
- ② 把该面板改成整行宽度。
→ 任何"往图里加数字"的改动都要**回读图内文字层**核对完整性，不能只核对数值对不对。
另：写绘图 helper 时**坚持全部用关键字参数**（`ha=` / `va=` / `weight=`）。本轮
`tx(x, y, s, size, color, "center")` 把 `"center"` 当成 `weight` →
`ValueError: weight='center' is invalid`；位置参数错位是这类 helper 的头号坑。

> 投稿系统字段（字数上限）与图形摘要的做法另见
> `references/submission-portal-fields-and-graphical-abstract.md`。

## 8. Source-vs-manuscript audits that only a full recompute catches

These defects are invisible to prose/consistency review — they need someone to recompute the
numbers from source. Run them before declaring a version done (full lens in
`references/multi-lens-adversarial-review.md`):

- **Hardcoded `override` dicts in figure/table scripts.** Grep plot scripts for `override` /
  hand-written value literals. Seen: `_make_supp_figs_v13.py` carried
  `override = {("N3","dx_nosx"): (2.506, 1.710, 3.672)}` while the source TSV and an
  independent refit both gave **2.518403 (1.715231–3.697668)** — the fabricated value had
  propagated into the manuscript's sensitivity table. Rule: diff every script-sourced
  table/figure value against its source TSV before submission; delete the override and
  regenerate rather than "fixing" the manuscript to match it.
- **Rounding must be identical in main text and supplementary.** Main text was truncating
  where the supplementary rounded, producing directly contradictory cells for the same source
  value: `1.752` vs `1.753` (source 1.7526004), `2.249` vs `2.250` (2.2496265), `1.624` vs
  `1.623` (1.6234728). Derive both from one formatter, then assert the triple appears nowhere.
- **After any single-value correction, sweep the WHOLE package for the stale value** —
  paragraphs AND table cells, manuscript AND supplementary. Editing one occurrence is not a fix.
- **Tracked changes / comments must be provably absent.** Unzip the docx and assert
  `w:ins` / `w:del` / `w:moveFrom` / `commentReference` counts are all 0 and `trackChanges` is
  false. Cheap, binary, and the kind of thing editorial triage checks first.
- **Don't confuse a reviewer's arithmetic with your own data.** Two independent reviewers both
  reported "Table 5 has 12 rows × 5 = 60 paired comparisons"; the table actually had 14 data
  rows × 5 = **70** (Panels A+B plus the two NHANES-III 20–74 rows). Count your own tables
  (`len(t.rows) - 1`) before accepting — or acting on — a reviewer's count.

## 8b. Target-journal compliance + journal-choice advisory (do this BEFORE the last polish round)

Once a target journal is named, the remaining work changes shape: it stops being "find more
errors" and becomes "satisfy this journal's hard rules". Check these mechanically — they are
binary and editorial triage checks them first.

### Abstract rules bite hardest (both are hard limits, and they differ per journal)

| | BMC Gastroenterology | PLOS ONE |
|---|---|---|
| Word cap | **350** | **300** |
| References in abstract | **not allowed** | **not allowed** |
| Structure | Background / Methods / Results / Conclusions | same |

- ⇒ **Compress to ≤300 words and strip ALL abstract citations**, then BOTH journals are
  satisfied and switching targets needs no rewrite. This is cheap insurance; do it even if
  you are only submitting to one.
- Seen this session: abstract was **363 words with 2 citations** (`[25]`/`[26]` for the NHANES
  data sources) → over BMC's 350 cap AND rule-breaking. Fix = drop the bracket markers, write
  the sources as plain text ("NHANES 2017–March 2020, NHANES 2021–August 2023 and NHANES III
  1988–1994"), and compress 363 → **299** (Background 96→68, Methods 94→81, Results 127→112,
  Conclusions 46→38). **Compress by deleting hedges and duplicated qualifiers — never by
  dropping a number, a CI, or a population-scope qualifier.**
- Verify: count the four labelled bodies; assert `citation_count == 0` over exactly those
  paragraphs while the BODY citations stay untouched.

### Declaration block (BMC requires all of these; scan with both apostrophes, see docx ref §12)

`Ethics approval and consent to participate` · `Consent for publication` ·
`Availability of data and materials` · `Competing interests` · `Funding` ·
`Authors' contributions` · `Acknowledgements`

### Focus the paper when the journal wants a single contribution

When the manuscript has accumulated reviewer-driven sections (a point-by-point
"comment vs reply vs this study" correspondence table is the classic case), a clinical
journal wants them OUT of the body. Seen: Table 8 (correspondence, 7×3) **moved to
supplementary as Table S13**, main tables 8 → 7, all four cross-references updated, the
supplementary declaration renumbered to S1–S13, and the Title page / Cover letter / STROBE
stat lines synced. Then restate **one** core contribution in the Introduction's last
paragraph and the Discussion's first.

### Journal-choice advisory (the user will ask "你也觉得应该首选 X 吗？")

This user keeps their own low-tier/"水刊" journal list on the Desktop and attaches it when
asking. Before endorsing or disputing a recommendation:

1. **Check the recommended journals against the user's own list** and say so. Seen: all three
   journals the reviewer ranked (BMC Gastroenterology #75, PLOS ONE #20, DDS #79) were on the
   user's own list — that fact is the real answer to "should this be first choice?", and
   withholding it would be useless reassurance.
2. **Give your own independent lean, not just agreement.** The user asks precisely because
   they want a second opinion. Disagreeing on stated grounds is welcome; silent compliance is
   not.
3. **Frame by objective, not by journal quality**: "publish smoothly + citable" vs "avoid the
   low-tier bucket" lead to different picks. State the realistic ceiling plainly — for a
   re-evaluation paper with a largely negative incremental finding, mid/low-tier is the honest
   target and a top-GI submission mostly burns 3–6 months.
4. **Offer a 3-way triage (A 全修 / B 投出去 / C 只修硬伤)** with your recommendation, and let
   the user decide. This user chose C (fix only the self-contradiction + the two items a
   reviewer will directly ask about) — respect that choice when it comes; don't re-litigate.
5. Note the practical fixables you cannot settle without a target journal (journal name in the
   cover letter, which word cap applies) as **explicit pre-submission manual steps**.

## 9. When to STOP the loop (the counterweight to §0–§8)

The checklist above pushes toward another round. It needs a counterweight, because the
AI-reviewer loop is **open-ended by construction** and will never self-terminate.

**Observed pattern across v12 → v18 (7 rounds, same manuscript):** the reviewer never once
said "ready to submit". Each round returned 5–8 items. But the *character* of the findings
changed decisively:

| Phase | Typical findings | Nature |
|---|---|---|
| early (v12–v14) | age-branch skip logic silently dropping 2,710 participants; Rao–Wu bootstrap SEs 30% too small; per-SD comparison of differently-scaled indices | **substantive** — the conclusions were wrong |
| middle (v15–v16) | IPW target-population vs selection-model sample mismatch; complete-case definitions inconsistent across layers; df accounting | **methodological** — conclusions held, reporting was indefensible |
| late (v17–v18) | spline knot *terminology* vs df; a constrained interaction test masking the heterogeneity it reported; wording of algebraic identity | **reporting/consistency** — mostly not affecting results |

⇒ **Operational rule: classify every finding as substantive / methodological / cosmetic, and
decide the next round on that mix, not on the raw count.**

- Any **substantive** finding ⇒另一轮，无商量（这类会改变结论）。
- **Methodological** ⇒ 一轮，且同一轮内把所有同类扫完（别一次修一个）。
- 只剩 **cosmetic** ⇒ **建议投出去**。真实期刊审稿人的意见是**有界的、可执行的**；
  AI 审稿人的意见是**无界的**——继续迭代会进入"为满足形式要求而改稿"的收益递减区。
- 明确的退出信号：**你开始为满足审稿人的形式要求而修改，而不是为纠正错误而修改。**

**How to tell the user (they will ask "还会被找茬吗？"):** answer honestly with the mix —
"(a) 检测到的问题已全部清零并验证；(b) 但基于 7 轮观察，AI 审稿人从未说过'可以投'，
且每轮必然找出 5–8 条；(c) 本轮剩下的 N 条属于 cosmetic/口径类"。然后给出**分类后的**
剩余项清单 + 明确的 A/B 建议（再修一轮 vs 投出去），**并说明自己倾向哪一个**。

**Also state the known-soft-spot list explicitly** rather than claiming a clean bill of health —
name the items you *know* are still arguable (e.g. 保留下来的旧口径敏感性表、两处不同调整集
的估计值并存、字数口径差异)。审稿人最反感的是"宣称无问题"，其次才是问题本身。

**Do not let the honesty rule in §0 be inverted into endless iteration.** §0 says "don't
declare done without independent QA"; this section says "don't let independent QA become a
perpetual motion machine". Both are needed.
