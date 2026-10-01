# 期刊模板排版 + 章节插入 + 交付顺序 QA（投稿包定稿前必跑）

来源：2026-10 GLM7 课题2 v21→v22 定稿（Frontiers in Medicine 投稿包）。
**前提认知**：这个用户会在定稿后**亲自逐项核对 docx 内部细节**（字号、字数、表格样式、章节顺序、结论篇幅）。
本文件记录的六类问题**全部被用户当场指出过** —— 不是"可以顺手做"，而是"不做就会被打回"。

---

## 1. 程序化插入新章节：标题必须在正文之前，插完必须重编号 + 查交叉引用

**本次实测中招三处**：
- `anchor.addprevious(el)` 连续插入"正文 + 标题"时若顺序写反 ⇒ **标题跑到正文后面**（2.9 / 3.10 / 3.11 三处全中）
- 新章节与原有章节**撞号**（原 3.9 = IPW 敏感性，新增的"时间验证"也编了 3.9）
- 新章节落到**不属于它的位置**（2.9 排到了 2.8 Ethics 之前）

**正确做法**：
```python
# ① 整块插入：一个列表里标题在前、正文在后，一次循环
for el in [head, body1, body2]:
    anchor.addprevious(el)

# ② 已经插乱：把标题摘出来，重新挂到"它自己的正文"之前
body.remove(head); first_body_el.addprevious(head)

# ③ 位置错的整块：标题+正文一起收集，整体搬到正确标题之前
```

**插入后三连自检（脚本化，必跑）**：
1. 每个 `^\d+\.\d+\s` 标题的下一非空段**不能**还是标题
2. 各章编号连续（方法 2.x、结果 3.x 各自 1..n，重编号后再核一遍）
3. 正文中每个 `Section X.Y` 引用都真实存在，且语义仍指向原来那一节
   → **重编号 = 交叉引用失效风险**。本次引用恰好都落在未变动区间才安然无恙，**不可假定**。

---

## 2. 按目标期刊模板统一字体（全套文件，不只主稿）

- 模板：`Desktop\Frontiers_Template.docx`。Frontiers 规范：**Normal = Times New Roman 12 pt**；
  Heading 1/2/3 = 12 pt（靠加粗区分层级）；Title = 16 pt。模板本身用"样式继承"写法（run 不写字号）。
- **本次实测的病态**：Normal 样式被写成 **9–11 pt**；run 层混了 **6 种字号**（8 / 9.5 / 10 / 10.5 / 11 / 12）；
  段落级 `pPr/rPr` 里还有**第三套**覆盖（10 / 13 / 11 / 10.5 / 9.5 / 8）。
- **三层同时改，缺一不可**：
  1. **样式层**：`doc.styles['Normal'].font.size = Pt(12)`；Heading 1/2/3、Title、Author List、List Bullet、Caption 同步；并写 `w:rFonts`
  2. **段落层**：删掉 `pPr/rPr` 里的 `w:sz` / `w:szCs`（本次主稿 167 处）
  3. **run 层**：显式写 `w:rFonts`（ascii/hAnsi/eastAsia/cs）+ `w:sz` + `w:szCs`
     —— 只设 `run.font.size` 不够，Word 仍可能回退到样式值
- **全套都要改**，不能只改主稿：主稿 / Title page / Cover letter / Supplementary / STROBE / Highlights / Plain English
  （本次 7 个文件**全部**字号混乱，Normal 全是 11 pt）
- 表格字号惯例小于正文（8–10 pt），但**同一文档内必须一致**；统计要按**值**做 `Counter`，
  "存在 tblBorders" ≠ "有边框"（**取值**为 `none`/`nil` 才是合格）
- ⚠️ **顺序**：字体统一用 python-docx ⇒ **必须排在 zip 级换图之前**，
  否则刚换好的高清图会被 `save()` 还原（详见 `figure-legend-content-and-image-reembed-audit.md` §10）

---

## 3. 声明性元数据的漂移（每轮改稿后一律重算）

本次被用户当场指出的例子：
| 位置 | 声明值 | 实际值 |
|---|---|---|
| 首页 Word count | 9,243（旧版遗留） | **9,922** |
| 补充材料说明 | Tables S1–**S13** | S1–**S16** |
| 标题页 Abstract word count | 350 | **341** |
| Running title | 上一版措辞 | 需同步 |
| Cover letter 分析框架 | "two modern periods as primary" | 与最终三时期框架不符 |

**规则：凡文档"自己声明自己"的数字，每轮改稿后全部重算** —— 正文字数、摘要字数、表数、图数、
参考文献数、补充材料编号范围、Running title、Cover letter 里的分析设计描述。
**口径写清楚**：正文 = Introduction → Conclusions，**排除**摘要 / 参考文献 / 图注 / 表注 / 声明（Abbreviations、Funding 等）。

---

## 4. 交付顺序与三线表（用户硬要求）

- **补充材料必须"先全部表格、后全部图片"**（用户原话：*"我要补充表呈现完再呈现图片"*）：
  新增表整块移到 `Supplementary Figures` 标题**之前**；分节标题 `Supplementary Tables` 要落在 `Table S1` **之前**。
  修复前实测：新增的 S14–S16 排在 Figure S1–S3 **之后**，且 `Supplementary Tables` 错落在 S16 之后。
- **三线表转换配方**：
  - `tblStyle` → 用**该文档中已合格表**所用的那个样式（本项目主稿 `'9'`、补充材料 `'12'`）
  - 删 `tblPr/tblBorders`；逐格写 `tcBorders`：`left`/`right` = `nil`，
    第 1 行 `top(sz=12)` + `bottom(sz=6)`，末行 `bottom(sz=12)`，中间行 `top`/`bottom` = `nil`
  - **检测要按取值**：竖线值为 `nil`/`none` 才算合格；`tblBorders` 存在但全为 `val="none"` 是**合格**表（别误判）
  - 用 python-docx 建表时若写了 `style="Table Grid"`（style id 35）会带网格线 —— **交付前必须转三线**
- 交付夹整洁：过程备份移入 `_过程备份/`，上一版文件移入 `_v##过程文件/`，交付夹内只留投稿文件。

---

## 5. 结论（Conclusions）篇幅与写法

用户明确反感"**太长太啰嗦、不够学术**"。本项目 Conclusions 原为 **308 词单段**
（从句层层堆叠 + 复述 Results 已交代的细节），被要求精简 ⇒ **180 词**，收成四层结构：

> **代数/结构性结论 → 本研究结果（带关键数值与不确定性）→ 解读 → 报告建议**

- 经验值：**150–200 词**；保留关键数值与 CI，**不复述全部结果、不铺陈动机**
- 检查法：`len(re.findall(r'\S+', conclusions_text))`，超 250 词就该收紧

---

## 6. 定稿前终审清单（每轮改完跑一遍，目标是"遗留问题 = 0"）

1. **字体统一**：7 个文件 × 每个文档内字号/字体唯一（`Counter` 按值校验）
2. **三线表合规**：主稿 / 补充材料 / STROBE 全表（按值检测竖线与表级边框）
3. **内嵌图**：md5 **且像素尺寸**双重校验（6 张；低清旧版往往尺寸更小，见 §10 of figure-legend...）
4. **Tables/ 与主稿**：逐表文本一致（主稿改过字体/内容后必须**重新提取**）
5. **章节编号连续 + 交叉引用有效**
6. **字数与所有声明一致**（首页/标题页/补充材料说明）
7. **图件 4 格式齐全**：pdf / png / jpg / tif（6 图 × 4 = 24 文件，300 dpi、双栏 ≥305 dpi）
8. **表全在前、图全在后**
9. 输出"遗留问题数"，逐项归零或如实说明 —— **不允许只报"已完成"而不带这个计数**
