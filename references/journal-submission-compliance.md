# 目标期刊投稿合规核查 + 作者名单变更传播

用户会问：**「检查一下是否已满足投稿要求？」「怎么投稿？」**——并且常常**同时**要求改作者名单。
本文件给可直接照抄的流程与 BMC Gastroenterology 的实测清单（2026-09 校对官方 Submission guidelines）。

## 一、触发与流程

1. **先逐段读完期刊的 guidelines 文档**（docx/pdf），把**硬性数字约束**抄成表：
   行距、行号页码、分页符、主稿格式、图宽/图高/分辨率/单图大小、图注词数、表注词数、
   附加文件命名与是否需要正文列节、Availability 句式、Cover letter 必备项、APC、审稿模式。
2. 对交付目录跑**程序化核查**（见 §五 骨架），不要靠目检。
3. **分三档报告**：✅ 已满足 / ⚠️ 建议处理 / ❌ 必须改，并**明确说出哪些不影响投稿**
   （用户要的是"能不能投"，不是一张全红清单）。
4. 顺带产出「怎么投稿」的分步说明（见 §六）——用户会连问两次，第一次答完就存下来。

> ⚠️ 先排除**自己核查脚本的假阳性**。本轮脚本报"正文有裸露 URL"，
> 实际是 Availability 段里的仓库网址——**BMC 的 Availability 模板本身就要求给 hyperlink**。
> 报告前先看命中的上下文，别把模板要求当违规。

## 二、BMC Gastroenterology 实测清单

| 项 | 官方要求 | v19 实测 |
|---|---|---|
| 行距 | 双倍 | `Normal` 样式含 `w:line="480" w:lineRule="auto"` |
| 行号 / 页码 | 必须 | `w:lnNumType` + footer 的 `PAGE` 域 |
| 分页符 | 不要用 | `w:type="page"` = 0 |
| 主稿格式 | DOC/DOCX/RTF/TeX（须可编辑，PDF 不接受） | .docx |
| **图宽** | **整页 170 mm（6.69 in）** | 6 张图均 **7.2 in（183 mm）** → 排版时缩 0.93×，8.5 pt → 7.9 pt（尚可读，但严格说应出图即为 170 mm） |
| 图高 | ≤ 225 mm（**含图注**） | 最大 181 mm |
| 图分辨率 | ~300 dpi @ 最终尺寸 | 300 dpi |
| 图件格式 | EPS/PDF/Word/PPT/TIFF/JPEG/PNG/BMP/CDX | PDF（矢量优先）+ PNG |
| 单图大小 | ≤ 10 MB | 0.04–0.07 MB |
| 图标题 / 图注 | 标题 ≤15 词、图注 ≤300 词，**写在主稿里**（不是图形文件里） | Fig1 290 / Fig2 216 / Fig3 296 |
| 图例键（色键/符号键） | 应**放进图形内**，不放图注 | ⚠️ **与本用户"图内不放图例"的硬规则冲突** → 以用户为准，并在交付说明里点明这条冲突 |
| 表格 | 无底纹/着色；**不用逗号标数值**；表题在上、表注在下，均 ≤300 词；用 Word 表格对象（不是图/Excel 嵌入） | 无底纹 ✓；**千分位逗号 38 处** ⚠️（违规普遍，改会降可读性 → 报告让用户定） |
| 附加文件 | 命名 `Additional file 1…`；**正文另设一节逐条列出**（文件名 / 格式 / 标题 / 描述）；上传下拉选 **"Additional file"** 而非 "Supplementary material" | 需补该节 |
| Availability | 两种固定句式**二选一**：仓库式 `…available in the [repository] repository, [identifier + hyperlink]` / 附加文件式 `…included within the article (and its additional file(s))`；软件另需 project name / home page / archived version / OS / language / license | 现为描述式 → 建议改写 |
| 参考文献 | 网页 URL 须给编号进文献表；公开数据集须正式引用（Force 11） | NHANES 已在文献表 ✓ |
| Cover letter | **必含 5 项**：为何投本刊 / 期刊政策相关事项 / 利益冲突声明 / 全体作者已同意投稿 / 未一稿多投 | 5/5 ✓ |
| 版权 | CC BY 或 CC BY-NC-ND | 投稿时选 |
| APC | £2,590 / $3,390 / €2,890；有 country-tiered pricing 与机构 TA | 提示用户查机构协议 |
| 审稿 | 单盲 + **透明同行评审**（接收后审稿报告随文发表） | 预警用户 |

## 三、★ 作者名单变更的传播规程（本轮实测：全目录只有 4 处要改）

用户的原话往往是极简的：**「把作者 A 改成 B，在 C 前面加入 D，单位都是 1」**。
真正的工作量在**传播**，不在改名本身。

1. **grep 全部 docx（含 tables）**搜旧名 —— 不要只改主稿。python-docx 需同时扫
   `paragraphs` 与 `tables`。
2. **作者名只出现在两类段落**：**作者行** 与 **CRediT / Authors' contributions**。
   本轮实测：主稿 2 处（作者行 + Authors' contributions）、Title page 2 处（作者行 + CRediT），
   **其余 6 个投稿文件里没有任何个人作者名**（Cover letter 只署 `on behalf of all authors`）。
   → 先 grep 出**穷尽**的清单，再动手，避免改漏或改重。
3. **先读原文确认上下标风格**：主稿用 `1,†`（普通字符），Title page 用 `¹,†`（Unicode 上标）
   ——**同一份材料两套写法，两种都要写对**。
4. **CRediT 也要同步**：① 改名；② 为新增作者插一条贡献行，位置插在**对应作者名之后**的 `; ` 处。
   本轮新增：`; Senmei Liang (investigation, validation, writing–review and editing)`。
5. **参考文献里的同姓人名不是作者**（本轮 refs 里有 `Chen S / Chen X / Chen TC`）——**勿误改**。
6. **收工断言**：旧名全目录残留 `grep -c` = **0**；新名出现次数 = 预期
   （本轮 `Shiyao Yang` ×4、`Senmei Liang` ×4）；作者顺序逐文件与新名单比对。

## 四、⚠️ 陷阱：写文件时短变量名被替换成 `***`

写脚本时若把姓氏存进短变量（本轮 `SU = "[First Author]"`），某些写入路径会把 `SU` 当成凭据
**替换成字面 `***`**，脚本随后行为错误且**语法仍通过**（lint 不报错）。
- **防法**：变量名用 `N1/N2/NAME_A` 这类无歧义写法，或**直接把字面串写进表达式**。
- **写完 `grep` 复核关键行**没被污染（本轮就是靠 `grep AUTH_OLD_MAIN` 发现的）。

## 五、核查脚本骨架（python-docx + zipfile）

```python
z = zipfile.ZipFile(MAIN)
styles = z.read("word/styles.xml").decode("utf-8")
doc    = z.read("word/document.xml").decode("utf-8")
assert 'w:line="480"' in styles                 # 双倍行距
assert "lnNumType" in doc                       # 行号
assert "PAGE" in z.read("word/footer1.xml").decode("utf-8")   # 页码
assert doc.count('w:type="page"') == 0          # 无分页符
# 图宽（mm）：BMC 整页 = 170 mm
from PIL import Image
w, h = Image.open(png).size; in_w = w / 300
# 表内千分位逗号
import re; re.findall(r"\b\d{1,3}(?:,\d{3})+\b", table_text)
```

## 六、投稿分步（BMC 系列；其它 BMC 刊同构）

1. 期刊主页 → 右上 **"Submit manuscript"** → **Editorial Manager**；注册需 **ORCID**（免费）。
2. **Article type** = `Research article`；粘标题/结构化摘要（**摘要不带引文**）/ 关键词；
   按名单顺序录作者、标通讯作者。
3. **上传**：Manuscript（主文档，含表与内嵌图）· Title page · Cover letter ·
   Figure 1–n（**传 PDF**）· Additional file 1 = 补充材料 · Additional file 2 = Figure legends ·
   Additional file 3 = 复现材料（**先打成 1 个 ZIP**）· STROBE checklist。
4. **建议审稿人 / 回避审稿人填在投稿系统的专用字段里，不要写进 Cover letter**（见 §七）。
   若确实想写进 Cover letter，先问用户——本用户明确要求过"不要写"。
5. 系统合成 PDF → **逐页检查**（图变形 / 表断行 / 行号页码 / 字体）→ **Approve submission**
   → 收稿号（如 `BMG-D-26-XXXXX`）。

### 6.1 ★ 待上传文件夹的打包形态（用户会明确要求"单独打包成一个文件夹"）

```
课题2vN/★待上传_Upload/
├── 01_Manuscript.docx
├── 02_Title page.docx
├── 03_Cover letter.docx
├── 04_Supplementary Materials.docx     ← Additional file 1
├── 05_STROBE checklist.docx
├── 06_Highlights.docx                  ← BMC 非必需
├── 07_Plain English summary.docx       ← BMC 非必需
└── Figures/                            ← PDF 与 PNG 各一份
    Fig1.pdf Fig1.png  Fig2.pdf ...  FigureS3.png
```

- **文件名带序号前缀**，顺序 = 上传槽位顺序 → 用户不会传错
- 文件夹名用 `★` 前缀 + 中文（用户是**非开发者**，要一眼认出该传哪个）
- 图件 **PDF 与 PNG 都给**，并注明"优先传 PDF（矢量）"
- **系统字段专用文件不放进去**（如 `Suggested reviewers.docx`）——避免误传成附加文件

---

## 七、★ Cover letter 篇幅与"建议审稿人名单"的形态（本用户硬要求，v19 轮两次返工）

### 7.1 Cover letter 必须短 —— 这是一条会被反复投诉的红线
用户原话：**「你写得太啰嗦了，改成简洁」**。此前那版 **2,660 词 / 5 页**（把全部方法学细节
——设计顺序核验、共同尺度换算、甘油三酯桥接方程、IPW 五设定、自由度核算、分母闭合——
逐条抄进了 Cover letter），被直接打回。

**目标形态：1 页 / ≈400–500 词 / 16–18 段。** 本轮从 2,660 → **474 → 401 词**后通过。

| 段落 | 内容 | 词数上限 |
|---|---|---|
| 1 | 日期 + `Dear Editor, <期刊名>` | — |
| 2 | 投稿声明（标题 + 文章类型） | ~60 |
| 3 | `Why this journal.` 为何投本刊（范围匹配） | ~70 |
| 4 | `What we found.` 核心发现（**双侧结论**：主关联 + 增量判别的真实边界） | ~180 |
| 5 | `How this differs from existing work.` 与已有工作的区别 | ~60 |
| 6 | `Methodological points.` **≤4 条 bullet，每条约 1 行** | ~90 |
| 7 | `Statements.` **5 项必备**（见 §二表末 Cover letter 行） | ~60 |
| 8 | 结语 + 署名 + 通讯作者联系方式 | ~30 |

**铁律**：
- **方法学细节属于正文/补充材料，不属于 Cover letter。** 想往 Cover letter 里塞第 5 条 bullet
  或第 200 词时，一律先问自己"正文里有没有"——有就删。
- **5 项必备声明一个都不能少**（删到只剩 401 词时仍要保住）。
- **不要写 Reviewer suggestions / 回避名单 / 代码可得性**（后两者见 §七·3 与 §八）。

### 7.2 建议审稿人名单的形态：中文导航 + 英文可提交字段
用户原话（两轮返工）：
1. **「太啰嗦、而且英文我看不懂」** —— 首版是 11 页纯英文长文，被否。
2. **「他们的邮箱你不会直接帮我查询吗？」** —— **留空邮箱不合格**。
3. **「中的单位和推荐理由，你写成英文啊！」** —— 又不能全中文。

**最终形态（照此做）**：中文只用于**导航/说明**（标题、用法、"务必回避的人"、"小提示"）；
**可直接提交的字段一律英文**，且**逐字段成行**便于复制：

```
1. <Full Name>
   Affiliation: <English, 从论文 Affiliation 字段抄>
   E-mail: <实查所得>
   Why suitable: Author of ref. [N]. <一句话，英文>
```

- **只给 6 位候选**（用户选 3–5 位），按方向分 3 组：① 疾病流行病学 ② 该暴露指标原创者
  ③ 复杂抽样 / 增量判别统计。**每组给 1–2 位**，并给出"建议用第 1、4、5 位"这类明确推荐。
- **候选来源 = 自己论文的参考文献作者**——天然同领域、可溯源、无利益关系。
- **回避名单单独一节**（红色标题），四类：被评价指数的原作者与其回复、公开评论的作者、
  本稿全体作者及其近期合作者、**本单位任何人**。
- 收尾给一段**可直接粘贴的英文声明**（含 4 位审稿人邮箱 + "no co-authorship, supervisory,
  funding or institutional relationship" + 回避请求）。

### 7.3 邮箱必须实查，且绝不编造 —— 用 `scripts/pubmed_reviewer_email_lookup.py`
**做 法**：PubMed E-utilities 的 `efetch` XML 里，**`<Affiliation>` 字段常含该文印出的
通讯作者邮箱**，可直接采信且可溯源至 PMID。

```bash
python scripts/pubmed_reviewer_email_lookup.py --author "Shabanzadeh DM" --topic "gallstone formation"
python scripts/pubmed_reviewer_email_lookup.py --pmid 15105181 16844493   # 已知 PMID 直取
python scripts/pubmed_reviewer_email_lookup.py --batch candidates.txt    # 每行 "姓名 | 检索式"
```

**本轮实测采信结果**（格式即交付格式）：

| 候选 | 邮箱（实查） | 来源 |
|---|---|---|
| Shabanzadeh DM | `daniel.moensted.shabanzadeh.01@regionh.dk` | PMID 29195671 |
| Portincasa P | `p.portincasa@semeiotica.uniba.it` | PMID 16844493 |
| Aune D | `d.aune@imperial.ac.uk` | PMID 26374741 |
| Pepe MS | `mspepe@u.washington.edu` | PMID 15105181 |
| Guerrero-Romero F | `guerrero.romero@gmail.com` | PMID 37315510 |
| Vickers AJ | `vickersa@mskcc.org` | PMID 17099194 |

**坑（本轮踩过）**：
- **检索式过宽会命中无关论文**（"Cook NR + ROC" 返回了别人的机器学习文；"Lumley" 返回了
  全球死亡率文）→ 必须 `[au]` 字段标签 + 主题词，并**核对返回标题**再采信。
- **命中的可能是同组资深作者**：METS-IR 那篇的通讯作者是 Aguilar-Salinas
  (`caguilarsalinas@yahoo.com`) 而非一作 Bello-Chavolla → **报告里要注明这一点**。
- **查不到就如实写"需查机构主页"，不要猜**（本轮 Cook / Bello-Chavolla / Lumley 三位即如此，
  列在"备选"节并给出查询途径）。

---

## 八、★ 用户"撤销某项承诺"后的传播规程（本轮：不公开代码）

用户说**「我不想公开代码」**——这不是删一个 ZIP 就完事。**旧承诺散落在多个文件里**，
不逐处清除就会对审稿人作出无法兑现的声明。

**必查清单**（本轮真实命中 2 处，都是硬矛盾）：

| 位置 | 本轮残留原文 | 处置 |
|---|---|---|
| **Title page** 的 Availability | "…**the analysis code** and the numeric output … **are provided with the manuscript as supplementary files**（not deferred until publication）" | 改写为只讲数据公开 + 补充材料表图，**删去代码与"not deferred"** |
| **Supplementary** 的独立小节 | 整节 **"Code and output availability statement"** + "to make the analysis fully verifiable at the time of submission" | **删标题**；正文改为"数值均由机器可读输出程序化生成，无手工录入" |

**方法**：全目录 grep 这些**承诺性措辞**，一处都不放过——
`analysis code` / `the code ` / `R script` / `Python` / `reproduction material` / `GitHub` /
`Zenodo` / `provided with the manuscript as supplementary files` / `not deferred` /
`verifiable at the time of submission` / `Code and output availability`。

**收工断言**：两文件对上述每个串的残留计数 **= 0**。

> ⚠️ 防假阳性：`script` 会命中 `descriptive` / `manuscript`，`code` 会命中
> `top-code` / `coded as 80 years`（年龄顶编码，属正常表述）。**先看上下文再判定**。

**同类触发**：用户改作者名单（见 §三）、改单位、改基金号、改目标期刊——都属"用户撤销/变更
既有承诺"，**传播规程相同：先 grep 穷尽，再改，最后按串计数断言**。

---

## 九、★ 交付物清单去重：同一内容出现在多处 = 冗余，要主动报告

用户会直接问：**「X.docx 是要单独上传的吗，还是已经包含在 Y 里了？」**

**先建"内容 × 文件"矩阵再回答**，不要凭印象。本轮实测：

| 内容 | 主稿 | Supplementary | Figure legends.docx |
|---|---|---|---|
| Figure 1/2/3 图注 | ✅ | — | ✅ **重复** |
| Figure S1/S2/S3 图注 | — | ✅ | ✅ **重复** |

**结论**：`Figure legends.docx` **完全冗余** → **建议不上传**（BMC 不要求单独的图注文件，
主图图注必须在主稿里）。用户保留在 `04_投稿材料/` 备查即可。

**顺带解释"为什么有的图注长有的短"**（用户会问）：主图（流程图/森林图/多面板 ΔAUC）必须承载
**方法学限定**（样本量、CI 估计方法、主基准 vs 敏感性设定、估计量的 in-sample 性质），
故 200–300 词；补充图是敏感性分析，坐标轴已自解释，故 25–80 词。
**BMC 只限上限 300 词、无下限** → 不违规；但 **<30 词的建议补一句**（如样条图补
"the curve is drawn on the log scale with the reference set at the median GLM7"）。

---

## 十、★ 补充材料（Supplementary）的结构自检

用户原话：**「字数多、啰嗦，而且文档内容的呈现结构不清晰」**。

**逐项核对**：
1. **编号是否单调**。本轮实测断裂：`…S12 → Figure S1 → S2 → S3 → **S13**` ——
   **Table S13 排在 Figure S3 之后**。⇒ 表格与图各自成组、按编号顺序排。
2. **是否有孤儿项**：正文 `grep "Table S n"` 逐个查 S1…Sn 是否被引。
   本轮 **Table S2、Table S5 未被正文引用**（内容有价值 → 补引用，而非删表）。
3. **是否有该删的小节**：如 §八 的代码可得性小节。
4. **主稿是否有"补充材料清单"节**：BMC 要求附加文件在正文另设一节逐条列出
   （文件名 / 格式 / 标题 / 描述）。本轮主稿**缺该节** → 需补回。
5. **表注是否过度**：⚠️ **别用正则数表注**——初版正则只捞到 866 词，实际逐段读出来是
   **7 个表共 2,379 词**（全文 12,725 词）。**逐表列出词数再判断**：

   | 表 | 改前 | 改后 |
   |----|------|------|
   | Table 1 | 521（122+230+169 三条脚注）| 298 |
   | Table 2 | 294 | 208 |
   | Table 3 | 398 | 200 |
   | Table 4 | 359 | 210 |
   | Table 5 | 115 | 84 |
   | Table 6 | 404 | 234 |
   | Table 7 | 288 | 166 |
   | **合计** | **2,379** | **1,400（−41%）** |

   **精简原则**：可删的是"**同一数值已在该表表体或正文出现**的复述"，以及
   **同一套 CI/df 公式在多个表中的重复陈述**（只留一处，如 Table 2，其余写
   `CIs and P values as in Table 2`）。
   **必须保留**：估计量定义、CI 构造式（`exp(b ± t(0.975, ddf) × se)` 与 ddf 数值）、
   关键限定（in-sample / 非预测验证、"12 个设定相关而非独立"、top-code、age-branched、
   common-increment）、加权 vs 未加权与 n 的含义、**任何数字**。
   另注意 **"Abbreviations" 常被误计入表注**（它是独立必需节，别删）。
   ⇒ **期刊无正文字数上限时，长篇本身不是合规问题**，报告时要讲清这一点；
   但用户会拿总字数说事，**先给逐表词数表，再给精简幅度**，这一步能直接消掉用户的疑虑。

### 报告节奏（用户会连问）
先给 **✅ 已满足 / ⚠️ 建议处理 / ❌ 必须改** 三档并**明说哪些不影响投稿**，
再把"待你决定"的项**逐条列出 + 各给一条建议**，末尾**明确问 1–2 个问题**（不要开放式长问）。
