# 投稿包规范化与提交合规（字体 / 间距 / 声明元数据 / 提交系统）

来源：2026-10 课题2 v22（Frontiers in Medicine – Hepatobiliary Diseases）投稿前返工。
配套脚本：`scripts/pre_submission_compliance_check.py`（一键跑完本文件第 1–3 节的机器可查项）。

---

## 0. 元教训：「遗留问题 0」≠「稿件合规」

本轮我连续多轮汇报"遗留问题 0、可以投稿"，用户却在**提交之后**发现主稿表编号根本没按正文首次提及顺序
（提及序 `1→7→6→2→3→4→5`，补充表更乱：`S13→S2→S11→S1→…`），并质问"为什么反复检查都没发现"。

根因不是"问题不明显"，而是**检查方式是清单驱动而非规范驱动**：
- 我的清单只有"引用**完整性**"，没有"编号**顺序性**"；
- 插入新章节/新图表后只查"新引用是否悬空"，没做**全量顺序复核**；
- 旧版就已乱序的编号被**当作既有事实沿用**，从未质疑编号体系本身；
- 我的自动检查全是"计数器式"（出现几次/是否一致），**从未写顺序性断言**。

⇒ **"0 遗留问题"只等于"我清单内都过了"。禁止用"可以投稿"这类结论性表述替代"我查了哪些项"。**
⇒ 拿到"是否合规"的追问时，先跑 `scripts/pre_submission_compliance_check.py`，用脚本输出说话。

---

## 1. 图表编号必须 == 正文首次提及顺序（投稿常识项，审稿人第一眼看）

必查四类：`Table N` / `Table SN` / `Figure N` / `Figure SN`。
乱序时按 `order` 生成 **旧→新** 映射后重编号，并同步：正文引用、表/图**标题本身**、补充材料内标题、
独立 `Tables/` 文件名、图件文件名（`FigureS1.*` ↔ `FigureS2.*` 这类需要对调）。
替换用带边界正则（`Table\s+S(\d+)(?![\d])`），**先长后短**，避免 `S1` 误吃 `S10`。
改完**重跑顺序断言直到四类全部递增**。

---

## 2. 按期刊模板统一字体（python-docx 的坑）

本轮症状：同一文档正文混用 **6 种字号**（8.0 / 9.5 / 10.0 / 10.5 / 11.0 / 12.0），
且 `Normal` 样式定义只有 **9 pt**，而 Frontiers 模板规范是 **Times New Roman 12 pt**。

**根因**：脚本逐段生成时，部分 run **只写了 `run.font.*` 或什么都没写**，Word 渲染回退到样式默认值；
不同批次生成用了不同字号；段落级 `w:pPr/w:rPr` 又叠加了一层覆盖。三者共存 ⇒ 视觉不一致。

**修复必须三层一起动**：
1. **样式层**：`Normal` → TNR 12 pt；`Heading 1/2/3` → TNR 12 pt（**加粗**区分层级）；`Title` → 16 pt
2. **清除段落级覆盖**：删掉 `w:pPr/w:rPr` 里的 `w:sz` / `w:szCs`
3. **run 层双写**（关键坑）：
   ```python
   r.font.name = FONT; r.font.size = Pt(12)          # 只写这个不够
   rpr = r._element.get_or_add_rPr()
   rf = rpr.find(qn('w:rFonts')) or <新建并 insert(0)>
   for a in ('w:ascii','w:hAnsi','w:eastAsia','w:cs'): rf.set(qn(a), FONT)   # ★ 四属性都写
   for tag in ('w:sz','w:szCs'): <新建或取，设 w:val = int(pt*2)>              # ★ 半磅单位
   ```
   **只设 `run.font.size` 而不同时写 `w:sz`/`w:szCs`，会出现"设了但没生效/部分生效"**。

模板规范先读模板再动手：`Document(模板)` → 看 `styles['Normal'].font.name/size`（模板通常靠**样式继承**，
run 层不写字号——所以"清 run 覆盖 + 样式层定义"才是与模板一致的做法）。

校验：按 run 统计 `w:sz` 分布，要求**每文件内字体集合 ⊆ {Times New Roman}、字号集合 ⊆ {12.0}**。
表格字号小于正文是排版惯例（8–10 pt 常见），各文件**内部一致**即可，不必跨文件统一。

---

## 3. 段落间距：按元素分类统一 + 删空段落

症状（用户原话）："有的地方段落前一片空白，有的地方直接接上一个内容"。
诊断：段落间距有 **9 种组合**混用，另有 **20 个空段落**（97 段中）——空段落本意是分隔，反而加剧不一致。

**统一规范（层级化，段前随层级递增）**：

| 元素 | 段前 | 段后 |
|---|---|---|
| 文档标题 | 0 | 12 |
| 一级标题（Supplementary Data / Tables / Figures） | 12 | 6 |
| Heading 2 / 表图标题（"Table S1." / "Figure 1."） | 10 | 4 |
| Panel 标签（"Panel A."） | 8 | 3 |
| 正文 / 表注 | 0 | 6 |

行距统一 `1.0`（`w:line="240" w:lineRule="auto"`）；**删除空段落**，分隔一律交给段后间距
（删之前**排除含 `a:blip` 的段落**，否则会把图删掉）。同一套规范要**全套文件都跑**——
本轮补充材料最乱、主稿次之，其余 5 个文件也各有 1–2 种不一致。

---

## 4. 声明元数据必须与实测对齐（每轮必查）

本轮抓到 4 处过时声明（全部在标题页/首页，不在正文，极易漏）：

| 项 | 症状 → 处理 |
|---|---|
| **正文词数** | 首页写 9,243（旧版遗留）→ 实测 9,922。口径=**Introduction→Conclusions**，排除摘要/参考文献/图注/表注/声明 |
| **摘要词数** | 写 350 → 实测 341 |
| **Running title** | 保留旧标题文案 → 与新标题同步 |
| **补充材料范围** | 写 "Tables S1–S13" → 实际已到 S16 |

**规则**：凡正文增删内容，**必须回头改首页声明**；`scripts/pre_submission_compliance_check.py` 的第 2 项会直接比对。

---

## 5. 结论段篇幅与结构（本用户明确偏好）

用户原话："结论 conclusion 是不是太长太啰嗦了，不够学术风不够严谨？"
原稿：**308 词单段到底**，从句层层堆叠，还重复了 Results 已交代的细节。

**目标形态（改后 180 词，用户接受）**：一段、约 150–190 词、四层递进、无重复铺垫：
1. **一般性结论**（本研究对象的性质，如代数共线/结构性事实）
2. **本研究结果**（关键数值 + 不确定性，一句带过，不复述全部结果）
3. **解读**（"因此应理解为 X 而非 Y"）
4. **可推广的方法学建议**（一句话）

⇒ 交付前自查：Conclusions 是否 **≤ ~200 词**、是否单段、是否出现已在 Results 写过的数字堆砌。

---

## 6. 提交系统合规（Frontiers 实例）

### 6.1 Scope statement（投稿系统必填）
要求：简短说明稿件为何属于所选期刊/专业。**100–150 词、一段**。写作骨架：
1. 首句把这个疾病/主题**明确挂到该栏目的核心范围**（例："胆石症是肝胆疾病中最常见者之一"）
2. 一句讲与专业的**实质关联**（病理机制层面，如"胆石形成 ↔ 胰岛素抵抗/内脏肥胖"）
3. 一句讲**对读者的价值**（同结构也适用于该领域常用指标 TyG-BMI / LAP / METS-IR）
4. **呼应期刊对"有意义研究"的要求**——强调方法学结论可迁移，避免被判"缺乏临床意义的描述性研究"
5. **不要自曝弱点**（如"只是公共数据库分析"），且措辞要与正文定位一致（不宣称预测/筛查工具）

若系统限字数（如 500 字符≈80 词），准备一长一短两版。

### 6.2 该联系哪个邮箱：**Editorial Office**，不是 Support Team
稿件页 "Need Help" 区通常有四个入口，其中两个是邮箱链接：

| 入口 | 用途 | 该不该用 |
|---|---|---|
| Review Guidelines / Help Center | 纯文档自助 | 不需要 |
| **Editorial Office** | **审稿政策、稿件事务**（编号修正、换文件、范围问题） | **← 稿件问题选这个** |
| Support Team | **技术问题**（登录失败、上传报错、系统故障） | 不选 |

⇒ 判据一句话：**"稿件本身的事"找 Editorial Office；"系统不好使"找 Support Team。**
邮箱多为超链接（截图 OCR 读不出明文），**点链接取准确地址，不要凭记忆猜**。

### 6.3 已提交后才发现格式问题
主动给 Editorial Office 发信说明（比等审稿人指出更好）：

> Subject: Manuscript <ID> – request to submit a corrected file (table/figure numbering)
> Dear Editorial Office,
> Our manuscript <ID> has just been submitted and is in initial validation. We have identified a numbering
> inconsistency: the main-text tables, and the supplementary tables and figures, are not numbered in the order
> in which they are first cited in the text. This affects only numbering and cross-references — no data,
> analyses or conclusions are affected. Could you please advise whether we may submit the revised files now,
> or whether it would be preferable to include this correction with the reviewer response at the revision stage?
> …

**要点**：① 给 Manuscript ID；② 明确"只影响编号与交叉引用"以打消数据疑虑；③ 给编辑部两个选项让其决定；
④ 附通讯作者署名与邮箱。

---

## 7. 操作顺序（与 §10 联动，务必遵守）

```
① python-docx 完成全部文字 / 字体 / 间距 / 结构 / 表格修改（可反复保存）
② 【最后一步】zipfile 替换 word/media/*.png + 同步 wp:extent
③ 立即校验内嵌图 md5 **与像素尺寸**
④ 此后不再用 python-docx 打开该文件
```
本轮因违反此顺序，高清图被 python-docx 的 `save()` **还原成低清旧版两次**（详见 figure-legend 专题 §9/§10）。

---

## 8. 交付目录整洁

- 改前备份一律放 `_过程备份/`，**交付夹本身只留投稿文件**；旧版本产物移到 `_v21过程文件/` 这类隔离目录
- 用户常**自己给文件重命名**（去掉 `01_`/`04_` 数字前缀，变成 `Manuscript.docx` / `Materials.docx` /
  `page.docx` / `letter.docx` / `checklist.docx` / `summary.docx`）——**下次接手先 list 目录确认实际文件名**，
  不要假设带数字前缀的旧名还在
