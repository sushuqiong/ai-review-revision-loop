# 期刊投稿硬要求与上传清单（按刊累积）

触发：稿件定稿后用户问"**怎么投 X 刊？**"、需要产出投稿包、或需要判断"现在可以投了吗"。
本文件是**可执行**版本（从期刊指南 + 实测合规检查提取），逐刊累积。
数据资源类论文（Scientific Data / npj）见同目录 `data-descriptor-submission-requirements.md`。

---

# 一、BMC 系列（以 BMC Gastroenterology 为实例）

## 1.1 硬指标（投稿前逐条自查）
| 项 | 要求 | 实测手法 |
|---|---|---|
| 文章类型 | **Research article**（不选 Brief report / Correspondence）| 系统下拉框 |
| 摘要词数 | **≤350 词** | 按"**含** 4 个结构标签"计；交付时同时报"含标签/不含标签"两个数 |
| 摘要引文 | **必须为 0** | `re.findall(r"\[\d", abst)` == 0；**正文引用不得跟着删** |
| 摘要结构 | Background / Methods / Results / Conclusions | 四段齐 |
| Declarations | **7 项各自独立成小节**（挤成一段会被要求拆开）| 见 §1.4 |
| **Ethics 项** | **不能写 "Not applicable"** | 写"原调查经 NCHS 伦理审查委员会批准、参与者书面知情同意；本二次分析使用公开去标识化数据，无需额外审批"。**与 Methods 的伦理叙述不得冲突**，Title page 与主稿要一致 |
| Abbreviations | 需独立缩略语表 | 条目须与正文**实际使用**一致：别列正文没用的，别漏正文大量用的 |
| 排版 | **双倍行距 + 连续行号 + 页码** | 见 §1.4 |
| 观察性研究 | 必须附 **STROBE checklist** | 交叉引用要与补充材料编号一致（如 S1–S13）|
| 正文词数 | BMC **无严格上限**（PLOS ONE 限 7,000）| 要留转投余地就压在 7,000 内 |
| 关键词 | 通常 5–6 个 | |
| APC | 约 US$3,390（OA 必付）| **先问机构图书馆/科研处有无 Springer Nature Transformative Agreement**，可能免付或打折 |

## 1.2 投稿入口与流程（Editorial Manager）
1. 期刊主页 `https://bmcgastroenterol.biomedcentral.com/` → 右上 **"Submit manuscript"**；
   或直接 `https://www.editorialmanager.com/bmcg/`
2. 注册（用**通讯作者的机构邮箱**，非个人邮箱）；准备 **ORCID**
3. 新建投稿 → **Article type: Research article** → Title / Abstract（不带引文）/ Keywords /
   Authors（标 Corresponding author；CRediT 贡献按 Title page 录）
4. **Funding information** 有独立栏位（基金号逐个填）
5. 上传文件（见 §1.3）
6. **Suggested reviewers**：3–5 位，从参考文献里挑**利益无关**的同行
   （排除合作者 / 同单位），并**如实披露关系**
7. 系统合成 PDF → **逐页检查**（图是否变形、表是否跨页断行、行号页码是否正常）→ **Approve submission**
8. 收到确认邮件 + 稿件编号（形如 `BMG-D-26-XXXXX`）

## 1.3 上传栏位映射（一个栏位一个文件）
| 上传项 | 文件 |
|---|---|
| Manuscript | `论文_全文_投稿版_vN.docx`（含表 + 图）|
| Title page | `Title page_vN.docx`（作者 / 单位 / 通讯作者 / 基金）|
| Cover letter | `Cover letter_vN.docx` |
| Figure 1–n | `Fig1_vN.pdf` …（**优先 PDF 矢量**；PNG 需 300 dpi+）|
| Figure S1–Sn | `FigureS1_vN.pdf` … |
| Figure legends | `Figure legends_vN.docx` —— **本用户硬要求：图例单独成 Word，图内上/下都不放图例** |
| STROBE checklist | `STROBE checklist_vN.docx` |
| Additional file | 补充材料 + 复现材料（**打包成 1 个 ZIP**）|

⚠️ 下拉里选 **"Additional file"**（补充材料 / 复现材料都走这个），
**不要**选 "Supplementary material"（那是给统计附录的）。
⚠️ 复现材料**必须先打成 ZIP** 再上传，否则"数据可得性声明"里点名的文件**并没有真正随稿**——
这是审稿人最容易抓、也最难解释的一类问题。

## 1.4 Declarations 三项格式的 python-docx 实现（都踩过坑）

**7 项拆成独立段落**：按标签切分原长段，`copy.deepcopy(p._p)` + `addnext` 逐个插回，
保留原格式、不丢内容。

**双倍行距**——必须写进 `styles.xml` 的 Normal：
```xml
<w:spacing w:after="120" w:line="480" w:lineRule="auto"/>
```
⚠️ 用 `paragraph_format.line_spacing_rule = DOUBLE` 之后再设 `line_spacing = None`，
**会把行距清掉**（实测回读为 None，XML 里根本没写进去）。要么只设 rule 不设 None，
要么直接改 XML。

**行号**——`sectPr` 加：
```xml
<w:lnNumType w:countBy="1" w:restart="continuous" w:distance="360"/>
```

**页码**——footer 段落里放 `fldChar begin` + `instrText " PAGE "` + `fldChar end`。
⚠️ 该字段在 **`word/footer1.xml`**，**不在 `document.xml`** —— 校验时要读对部件，
否则会误判"页码没加上"。

## 1.5 Cover letter 要点（BMC 版，逐条核）
- 称呼**指名期刊**：`Dear Editor, BMC Gastroenterology`
- 首段写**期刊适配**：明确该刊范围覆盖本研究方向
  （例：`digestive disease epidemiology, with gallstone disease as the outcome`）
- 声明文章类型为 **Research article**
- 声明：未他投 / 全体作者同意 / 无利益冲突 / 二次分析无需额外伦理
- 基金列表照抄（含项目号）
- **日期改成投稿当天** —— 交付稿常留着项目启动日，投稿前必改
- **统计行**（摘要词数 / 正文字数 / 表数 / 图数 / 文献数）必须与终稿**逐一致**；
  本轮就是这里出现三方不一致（Title page 6,999 / Cover letter 7,100 / 实测 7,260）

---

# 二、选刊的一般判据（用户会问"你也觉得应该投 X 吗？"）

不要只复述推荐。按这四步给判断：

1. **先查用户自己的黑名单**。用户会附"水刊合辑"之类的清单——
   **先去清单里查被推荐的刊在不在**。本轮推荐的三本（BMC Gastroenterology / PLOS ONE / DDS）
   **全在用户的水刊清单里**，这一条必须主动说出来，否则等于没回答。
2. **匹配度 vs 目标**分开讲：
   - 要"发出来、能被引用、流程顺畅"→ 匹配度优先，接受中低档
   - 要"避开低层次、有分量"→ 老实说**本稿的现实天花板在哪**（复核他人指数 + 单一结局 + 阴性增量
     通常就在中低档），强行投高刊只会浪费 3–6 个月
3. **结局性质要匹配刊的取向**：阴性 / 不显著结果 → 明确欢迎阴性结果的刊（如 PLOS ONE）
   比临床专科刊更"诚实匹配"，即使后者声望略高。
4. **把"包装工作"和"选刊"绑定给建议**：摘要压到 300 词内并删摘要引文，
   **两家都满足、转投不用重写**——这类"一次投入、两刊可用"的动作优先做。

---

# 三、投稿前"可投了吗"的判定模板

不要凭感觉答。跑程序化清单，逐项给 OK/X：

```python
# 1 硬指标：摘要词数(含标签) / 摘要引文数(应 0) / 结构化 4 段
# 2 声明：7 项齐备（含 Authors' contributions / CRediT）
# 3 结构：表数 / 内嵌图数 / 文献编号 1..n 连续 / 首现序无逆序
# 4 补充材料：S1..Sn 全覆盖引用，无孤儿
# 5 洁净度：每个 docx 中文 0 / 内部痕迹 0（v14-v18、_build、_ms_content、01_数据、code/、GPT、reviewer）/ 占位符 0
# 6 图件：宽 7.2 in / PDF Type3=0 / 四边留白 >0 / 内嵌图 md5 与 03_图表 逐位一致
# 7 声明点名的文件真实存在（逐个 os.path.exists）
# 8 词数口径三处一致（主稿 / Title page / Cover letter）
```
**输出必须是"未通过项: N"**，并列出每一项的证据。**N=0 才说"可以投"**。
用户会追问"你确定没有遗留问题？"——所以每次宣布就绪前都要**再跑一遍这个清单**，
并**派独立 subagent 换视角复查**（见 `submission-readiness-adversarial-qa.md`）。
