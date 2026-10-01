# 投稿版式归一：字体 / 间距 / 篇幅 / 元数据（脚本生成 docx 的收尾工序）

来源：课题2 v22 投稿包（Frontiers in Medicine → Hepatobiliary Diseases）。
用户连续三轮反馈：「各个表格的字体和格式不统一」「有的地方段落前一片空白，有的地方直接接上一个内容」
「结论是不是太长太啰嗦，不够学术风」「首页 Word count 9,243 有没有问题」。

**这些都不是内容问题，而是脚本逐段生成 docx 累积的"版式债"。** 本文件给出可直接照做的归一工序。

---

## 0. 为什么脚本生成的 docx 一定会版式混乱

文档由多轮脚本逐段追加：早期段落按"紧凑排版"写了 9–11 pt，后期段落换了字号；
间距同理，各类元素（表标题 / Panel 标签 / 表注 / 分节标题）各写一套 before/after；
再叠加"本来想用来分隔"的空段落。**三层叠加** ⇒ 视觉上"忽大忽小、忽紧忽松"。
⇒ 交付前必须**集中做一次版式归一**，不要指望分段写入时保持一致。

---

## 1. 先读期刊模板，再定值（不要凭感觉）

```python
d = Document(TEMPLATE)
d.styles["Normal"].font.size          # Frontiers 模板 → 12.0 pt
d.styles["Normal"].font.name          # Times New Roman
```
- 模板用**样式继承**（run 不写字号）⇒ 修复也应"**样式层定值 + 清掉 run/段落层的散乱覆盖**"
- 本项目模板规范：Normal **12 pt**；Heading 1/2/3 **12 pt（加粗分层）**；Title 16 pt

---

## 2. 字体归一：必须写 raw XML（只设 `run.font.*` 不够）

```python
def force_run(r, size_pt, font="Times New Roman", bold=None):
    r.font.name = font; r.font.size = Pt(size_pt)
    rpr = r._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None: rf = OxmlElement('w:rFonts'); rpr.insert(0, rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'):
        rf.set(qn(a), font)
    for tag in ('w:sz', 'w:szCs'):
        e = rpr.find(qn(tag)) or OxmlElement(tag) appended
        e.set(qn('w:val'), str(int(size_pt * 2)))     # half-points!
```

**关键点**
- **清段落级覆盖**：删除每个 `w:pPr/w:rPr` 下的 `w:sz` / `w:szCs`（本项目清了 **167 处**，否则段落层会压过样式）
- **诊断口径**：只统计**实际生效字号** = `w:rPr/w:sz` 的值；只读 `run.font.size` 会漏掉 `None`（继承值），得出"看起来没问题"的假结论
- **表格同法处理**，且表格字号**可以小于正文**（本项目：主稿 9 pt / 补充 8 pt / 清单 9.5 pt）——
  但**每个文件内部必须只有一种**。判据：`同一文档内 字体或字号种类 > 1 的表数 == 0`
- 全套一起做（主稿 + 配套文件往往共用同一个错误习惯；本项目 7 个文件里 6 个 Normal 都是错的 11 pt）

---

## 3. 段落间距归一：按元素层级，不按"感觉加空行"

| 元素 | before (pt) | after (pt) |
|---|---|---|
| 文档标题 | 0 | 12 |
| 一级标题（Introduction / Supplementary Tables…） | 12 | 6 |
| 二级标题 / 表标题 / 图标题 | 10 | 4 |
| Panel 标签（`Panel A.`） | 8 | 3 |
| 正文 / 表注 | 0 | 6 |

行距统一 `1.0`（`w:line=240, w:lineRule=auto`）；**删除全部空段落**，分隔完全交给 `after`。

- 元素类型用文本正则 + 样式名判定：`^Table S?\d+\.`、`^Figure S?\d+\.`、`^Panel [A-Z]\.`、`style.name.startswith("Heading")`
- ⚠️ **删空段落时务必排除含图的段落**：
  `el.findall('.//' + qn('a:blip'))` 为空的才删，否则会把插图一起删掉

---

## 4. 篇幅规范（用户明确偏好，属硬要求）

- **Conclusions ≤ ~200 词，单段内分层**：机制/结构性质 → 本研究结果（带关键数值）→ 解读 → 报告建议。
  禁止把 Results 的细节再抄一遍。本项目 **308 词 → 180 词**后被认可
- **Highlights 3–5 条**，每条尽量 ≤ ~115 字符（本项目从 7 条压到 5 条，原最长 259 字符）
- **正文字数声明必须实算**：口径 = `Introduction → Conclusions`，
  排除 abstract / references / figure legends / table captions / declarations。
  本项目首页写着 **9,243**（旧版遗留），实算 **9,922** ⇒ **版本升一次就重算一次**
- 摘要词数同理（本项目 Title page 原写 350，实为 341）

---

## 5. 章节插入的顺序陷阱（`addprevious` 锚点）

```python
anchor.addprevious(body)     # 先插正文
anchor.addprevious(heading)  # 再插标题  ⇒ 结果：正文在前、标题在后 ❌
```
且多次锚定同一 anchor 会打乱顺序 —— 本项目出现 **2.9 排在 2.8 之前**、**两个 "3.9"**（原章节与我新增章节撞号）。

**插入后必跑三项自检**
1. 每个 `^\d+\.\d+ 标题` 的下一非空段**不能是另一个标题**（说明标题掉到正文后面了）
2. 各章编号连续（方法 2.x / 结果 3.x）
3. 正文 `Section X.Y` 引用是否都真实存在（**重编号后尤其要查**；本项目重编号后引用全落在未变动编号上，安全）

**正确写法**：先生成完整块（heading + body 列表），再一次性 `for el in block: anchor.addprevious(el)`；
或把标题插到 anchor 前、正文插到标题后（`heading.addnext(body)`）。

---

## 6. 配套文件元数据同步清单（**版本升一次查一遍**）

标题 / Running title / 摘要词数 / 正文字数 / 表数·图数 / 参考文献条数 / 补充材料编号范围 / 目标期刊与栏目 /
建议审稿人 / Cover letter 对分析框架的描述。

本项目实测漏项（都在"主编稿之外"的文件里）：
- Title page：running title 还是 v21 旧句；word count 9,243；`Tables S1–S13`（应为 S16）
- **Cover letter：仍写"We analysed two modern periods … as the primary analysis"**，而最终决定是保留三时期框架
  ⇒ Cover letter 与主稿口径不一致是最容易被编辑看穿的硬伤，必须逐句对账
- Highlights：仍只报 P=0.072（选择性报告），正文已改为约束/放宽双口径并列

---

## 7. 补充材料顺序（用户偏好）

**所有表在前、所有图在后**。分节：
`Supplementary Data → Supplementary Tables → 表 S1…Sn → Supplementary Figures → 图 S1…Sn`

- 新追加到文末的表要**移回表区**（本项目 S14–S16 一度落在 Figure S1–S3 之后）
- 分节标题也要跟着挪（"Supplementary Tables" 曾错落在 S16 之后）
- 图注与图必须相邻（图紧跟其图注）

---

## 8. 收尾自检（每轮改稿必跑，逐项归零）

| 项 | 判据 |
|---|---|
| 字体 | 每文件正文 = TNR 12 pt，种类 = 1 |
| 表格字体 | 同一文档内字号种类 > 1 的表数 == 0 |
| 三线表 | 无竖线、无实际表级边框 |
| 间距 | 每文件间距种类 ≤ 4（按层级） |
| 空段落 | 0（除含图者） |
| 章节 | 编号连续 + 标题紧跟正文 + 交叉引用可解析 |
| 字数 | 首页声明 == 实算 |
| 图件 | 内嵌图 ≥2000 px 且与 `Figures/` md5 一致（见 figure-legend-content-and-image-reembed-audit.md） |
| 配套文件 | 标题/字数/编号范围/分析框架描述全部同步 |

---

## 9. ⚠️ 与图片重嵌工序的冲突（必读）

字体归一 / 间距归一都**必须用 python-docx 打开并保存**，
而 `doc.save()` 会**还原此前用 zip 级操作替换的图片**（主稿高清图被打回低清旧版，本项目**实际复发 2 次**）。

⇒ **强制收尾顺序**：
```
① python-docx 做完所有文字/样式/间距/结构改动（可反复保存）
② 【最后一步】zipfile 替换 word/media/*.png + 同步 wp:extent
③ 立即用「像素尺寸 + md5」双重复检
④ 此后不再用 python-docx 打开该文件
```
细节与诊断脚本见同目录 `figure-legend-content-and-image-reembed-audit.md` §9–§10。
