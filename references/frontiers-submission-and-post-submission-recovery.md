# Frontiers 投稿机制 + **已提交后才发现缺陷**的补救协议

来源：2026-10-01 课题2 v22（Front. Med. – Hepatobiliary Diseases, Manuscript ID 2016169）实测。
本用户会反复投 Frontiers，本文件覆盖"投出去之前"和"投出去之后才发现问题"两段。

---

## 1. 联系谁：Editorial Office，不是 Support Team

投稿页 `Need Help` 区通常给 4 个入口，其中两个是**超链接形式的邮箱**（截图/OCR 读不出明文地址，
不要凭记忆编造邮箱——让用户点链接，或走稿页的 `Send message to editorial office`）：

| 入口 | 用途 | 用不用 |
|---|---|---|
| Review Guidelines | peer review 流程说明 | 不用 |
| **Editorial Office** | **审稿政策、稿件事务**（编号/格式/更正） | ✅ **选这个** |
| Help Center | 自助帮助 | 不用 |
| Support Team | **技术问题**（登录、上传报错） | ❌ 不选 |

**判据**：属于「稿件本身的事务」→ Editorial Office；属于「系统/账号故障」→ Support Team。

## 2. Scope statement（投稿系统字段）

要求：一段，说明为什么属于所选期刊/专业（约 100–150 词）。写法（本次用户直接采用）：

1. 首句点名该病种属于**该栏目的核心范围**（如"胆石症是最常见的肝胆疾病之一"）；
2. 中段说明本研究与该专业的**实质关联**（病理/机制联系，而非"都用了同一数据库"）；
3. 结尾说明**对读者的可迁移价值**，并点出同一结构也适用于该领域其他常用工具
   （如 TyG-BMI / LAP / METS-IR）。

**规避两个坑**：
- 不写"NHANES 只是公共数据库二次分析"这类自我弱化——Frontiers 明确不欢迎"仅因用公共数据而缺乏
  临床意义的描述性研究"，要强调**可迁移的方法学结论**；
- 不宣称预测/筛查/诊断工具价值，必须与正文口径一致（否则 scope 与内容不符）。

同时准备一个 **~80 词短版**，多数系统有字符上限（约 500 字符）。

## 3. 交付夹整洁（用户明确要求："文件夹里很多没用的文件投稿根本没用"）

根目录**只留投稿必需件**，命名统一（去数字前缀）：

```
Manuscript.docx / Manuscript.pdf
Supplementary Materials.docx
Title page.docx  ·  Cover letter.docx  ·  STROBE checklist.docx
Figures/ (每图 pdf+png+jpg+tif)   Tables/ (Table 1..N.docx)   Supplementary Code/
```

移出到 `_内部文件（不投稿）/`：进度说明/README/`_过程备份`/工作目录，**以及期刊未要求的件**
（`Highlights.docx`、`Plain English summary.docx` 属 Elsevier 系列常见要求，**Frontiers 不要**）。

⚠️ 改完 docx 后**必须重新生成 PDF**（本次旧 PDF 是重编号前的版本，344 KB → 新 34 页）。

## 4. ⚠️ **已提交后**才发现缺陷 —— 补救协议

本次实况：图表编号乱序，用户**已提交**后才由用户发现。不要慌、不要擅自重投，按序做：

**第 1 步：先诚实归因，再给方案。** 用户会问"为什么反复检查都没发现"。回答要落到**机制**
（清单驱动 vs 规范驱动、"0"被当成结论、结构改动后无全量回归），不要只说"抱歉"，
也不要推给模型/环境。见 SKILL.md「验证范围的诚实性」。

**第 2 步：主动联系 Editorial Office**（比等审稿人指出更好——显得严谨）。模板：

> **Subject:** Manuscript <ID> – request to submit a corrected file (table/figure numbering)
>
> Dear Editorial Office,
> Our manuscript <ID> ("<title>") has just been submitted and is in initial validation.
> We have identified a **numbering inconsistency**: the main-text tables, and the supplementary
> tables and figures, are **not numbered in the order in which they are first cited in the text**.
> This affects only numbering and cross-references — no data, analyses, or conclusions are affected.
> We would like to upload a corrected version. Could you please advise whether we may submit the
> revised files now, or whether it would be preferable to include this correction together with the
> reviewer response at the revision stage?
> Sincerely, <corresponding author>, on behalf of all authors

**第 3 步：无论走哪条路，都先把修正包做好**，随时候传。修正动作见
`figure-legend-content-and-image-reembed-audit.md` §11（映射 + 哨兵两阶段替换 + 六处同步 + 断言）。

**第 4 步：给用户一份"新旧编号对照表"**，便于向编辑部说明、也便于日后回溯。

**提交状态常识**：Frontiers 提交后先进入 *initial manuscript validation*（编辑部核验），页面会显示
"NO ACTION IS REQUIRED FROM YOU"——这不代表不能申请更正常规性缺陷。

## 5. 投稿前必跑的规范清单（本次漏掉的就是第 1 条）

1. **图表编号 = 正文首次提及顺序**（Table / Table S / Figure / Figure S 四类分别断言）← 本次事故
2. 图表**引用完整性**（每个图表都被引用，无悬空引用、无孤儿图表）
3. 正文引用的数值在交付包中**有出处**（表/图/S 表可查）
4. 摘要词数 ≤ 期刊限长；**首页声明的字数 = 实测**（本次 9,243 是旧值，实测 9,922）
5. 图注与**图内数据源**一致（口径、样本量、base 形式）
6. 三线表、全表字体统一、段前段后间距按层级统一（无散乱空段落）
7. 交付夹只留必需件；PDF 与 docx 同步
8. 内嵌图分辨率（≥2000 px）且与 `Figures/` 逐字节一致
