# 投稿文件的长度纪律、格式一致性与声明清洗（v19 轮新增）

本文件覆盖 SKILL.md 未含的一类返工：**内容没算错，但"胖、乱、前后不一致"**。
用户的投诉句式是"字数有点多 / 太啰嗦 / 结构不清晰 / 显示有问题 / 前后矛盾"。

---

## 一、表格注释（table notes）的长度纪律

用户原话：「manuscript.docx 的总字数有点多，是不是因为你写的表格 Tables 的注释说明太啰嗦了？」

实测：7 个表的注释合计 **2,379 词**，占正文 12,725 词的 **19%** —— 确实偏多。

**先量再改**（表注 = 表标题之后、下一个 `Table`/`Figure`/章节标题之前、词数 > 15 的段落）：
```python
idx = [i for i, t in enumerate(ps) if re.match(r"^Table \d\.", t.strip())]
j = i + 1
while j < len(ps) and not re.match(r"^(Table \d\.|Figure \d\.|\d+\.\s+[A-Z])", ps[j].strip()):
    ...   # 累计该表注释词数
```

**精简原则：保内容、去冗词**

| 保留 | 删除 |
|---|---|
| 估计量定义（每 SD OR 的含义、OR 比值定义）| 与正文 / 表体重复的复述 |
| CI 构造 `exp(b ± t(0.975,ddf)·se)` 与 ddf 值 | **同一套 CI 公式在多个表重复陈述** → 只留一处完整，其余写 `CIs and P values as in Table 2` |
| 关键限定：`in-sample`、非预测验证、`12 设定相关而非独立`、`top-code`、`age-branched`、`common-increment` | 冗长解释句、重复的 `Values are…` 套话 |
| **任何数字**（含只出现在表注里的）| —— |

**本轮结果**：2,379 → **1,400 词（−41%）**；主稿 12,725 → **11,826 词**。

**验收三件**：① 逐表给"改前→改后"词数；② 抽查关键限定词仍在；
③ **主稿 7 表 + 补充 23 表的单元格改前改后逐字一致**（比对 cell 文本列表）——表格本体一个字都不能动。

> 注意：BMC 等刊对正文**没有**字数上限，所以"长"不是合规问题，是**可读性/编辑印象**问题。
> 不要用"违规"去说服自己动手，要用"审稿人不喜欢"。

---

## 二、补充材料表格的"格式漂移"——后追加的表会丢格式

用户原话：「Table S12 和 S13 的显示有问题，不能像 S1 到 S11 那样呈现吗？」

根因：S1–S9 一次性生成、格式统一；**S10–S13 是后续版本逐次追加的**，复制内容时漏了三样：

| 缺陷 | S1–S9（正常）| S10 / S11 / S12 / S13（漂移）|
|---|---|---|
| **末行底部封闭线** | `tcBorders/bottom(val=single, sz=12)` | **缺失** → 三线表没有底线，看起来"没画完" |
| **单元格显式字号** | `w:sz val=16`（8.0 pt）| **无** → 依赖继承，与其它表不一致 |
| **表格宽度** | 列宽和 ≈ 9,636 twips（**17.0 cm** = 页面可用宽度）| S10p2 / S12p1 / S12p2 = **9,854 twips（17.4 cm）→ 超出右边距** |

**直接跑 `scripts/docx_table_format_audit.py`**（本轮回新增）：逐表打印 `宽度 cm / 底线 ✓✗ / 首行字号`，
`--fix` 就地修复。修复要点：

- 末行每格补 `w:bottom`（`val=single, sz=12`）；**已有底线的不要重复加**
- 每个 run 补 `w:sz` **和 `w:szCs`**（只补 `w:sz` 在部分渲染器下无效）
- 超宽表：按比例缩放 `w:tblGrid/w:gridCol` **并同步每格 `w:tcW`** ——
  只改 gridCol 不改 tcW，Word 仍会按旧宽渲染（这是本类修复最常见的"改了没用"）

**验收**：不合格表数 = 0。

> 推论（值得推广）：**同一 docx 里"不同时期生成的同类对象"必定有格式漂移**。
> 主稿 7 个表同理，交付前应跑同一个脚本体检。

---

## 三、用户决定"不公开代码"时的声明清洗（必须全局 sweep）

用户原话：「我不想公开代码」（随即删掉了 reproduction ZIP 与 `Reproduction materials/` 目录）。

**残留不会只在一处。** 本轮实际命中 3 处：

1. `Title page` 的 Availability：`the analysis code and the numeric output … are provided with
   the manuscript as supplementary files (not deferred until publication)`
2. `Supplementary Materials` 里有一整个小节标题 **"Code and output availability statement"**
3. 该小节正文：`To make the analysis fully verifiable at the time of submission …`

**固定动作**：用一组关键词 sweep **全部**投稿文件（主稿 + 5–7 份投稿材料 + 补充材料）：

```
analysis code | provided with the manuscript as supplementary files | not deferred |
reproduction | reproduction_materials | Additional file 3 | GitHub | Zenodo |
Code and output availability | verifiable at the time of submission
```

**替换模板**（保留数据可得性，去掉代码承诺）：
> Availability of data and materials: All data analysed are publicly available from the CDC/NCHS
> NHANES website (https://wwwn.cdc.gov/nchs/nhanes/) and the NHANES III public-use files. The
> variable mapping across the three survey layers, the derived analysis samples and the full set of
> supplementary tables and figures are provided with the manuscript as Supplementary Materials
> (Tables S1–S13 and Figures S1–S3), so that every reported estimate can be traced to a tabulated
> input. No individual-level or otherwise restricted data were used.

**验收**：上述关键词在**全部**投稿文件中的残留 = 0。

> 同理可推广：**任何"用户改变主意"的决定（撤掉数据、撤掉代码、换目标期刊、改名）都要做一次
> 关键词 sweep**，因为声明散落在主稿 / 标题页 / 补充材料 / Cover letter / STROBE 五处以上。

---

## 四、Figure legends 到底放哪里（三处分工，不要做重复文件）

| 图的类别 | 图注放哪 | 依据 |
|---|---|---|
| **主图**（Figure 1–3，作为独立图片文件上传）| **主稿正文内** | BMC：*"Figure titles (max 15 words) and legends (max 300 words) should be provided in the main manuscript, not in the graphic file."* |
| **补充图**（Figure S1–S3）| **Supplementary Materials 文件内** | 随补充图走 |
| 单独的 `Figure legends.docx` | **冗余 → 删** | 主图图注已在主稿、补充图图注已在补充材料，该文件两头重复 |

本轮据此删掉 `Figure legends.docx`（归档 `_bak/`），README 记录删除原因。
**BMC 不要求单独的图注文件。**

**图注长度**：BMC 只规定**上限 300 词、无下限**。主图图注长（本轮 290 / 216 / 296 词）是因为它们
必须承载方法学限定（样本量、CI 估计法、主/敏感性设定、in-sample 性质）；补充图注短
（25 / 81 / 36 词）是正常的。**不要为了"字数对称"给补充图注注水。**

---

## 五、Cover letter 的长度与"建议审稿人"的归属

用户原话：「Cover letter 你写得太啰嗦了，改成简洁」。

- 实测 **2,660 词 / 24 段** → **401 词 / 16 段（1 页）**
- 删掉的是 **12 条方法学细节长段（约 1,800 词）**：设计顺序核验、共同尺度换算、
  TG 桥接方程、IPW 五设定、自由度核算、分母闭合……
  **这些本来就在正文与补充材料里，Cover letter 不需要复述。**
- 保留：① 为何投本刊 ② 双侧核心结果（1 段）③ 与已有工作的区别（1–2 句）
  ④ 方法学要点（**4 条 bullet**）⑤ 期刊要求的声明 ⑥ 结语 + 署名

★ **建议审稿人与回避名单不写进 Cover letter**：投稿系统有专门的 `Suggested reviewers` /
`Opposed reviewers` 字段，写进正文是重复。用户明确要求删掉；系统字段内容从独立的名单文档复制。

**BMC 要求 Cover letter 必含 5 项**（缺一项编辑会退回）：
① 为何应发表于本刊 ② 期刊政策相关事项 ③ 利益冲突声明 ④ 全体作者已同意投稿 ⑤ 未一稿多投。
改完后**逐项 grep 确认**（关键词：`Why this journal` / `Statements` / `no competing interests` /
`All authors have approved` / `has been published or is under consideration elsewhere`）。

---

## 六、投稿前"清单 + 交叉引用"终检（每轮都要跑）

| 检查 | 判据 | 本轮真实命中 |
|---|---|---|
| 补充材料编号顺序 | `Table S1…S13` 连续，**三个 Figure S 在末尾** | Table S13 排在 Figure S3 **之后**（后追加导致）|
| 补充项目全部被引 | 正文逐一 grep `Table S1–S13` 与 `Figure S1–S3` | **3 个孤儿表：S1 / S2 / S5** |
| 主稿有补充材料清单段 | References 之前有一段 `Supplementary material`（BMC 要求正文列出附加文件：文件名/格式/标题/描述，≤120 词）| 缺失 |
| 文件名与正文声明一致 | 正文点名的文件名（如 `Supplementary Materials.docx`）与实际交付文件名**逐字一致** | —— |
| 洁净度 | 全部 docx：中文 0 / 内部痕迹 0（`_build` `_ms_content` `v1x` `01_数据`）/ 占位符 0 | 仅用户自用的名单文档含中文（**不上传，无需清零**）|
