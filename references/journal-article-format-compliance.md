# 期刊投稿格式合规：Cardiovascular Diabetology / BMC "Research article"

来源：该刊 `Research` 投稿要求页 + `General formatting guidelines`（后者本次未逐字核对，见文末"未经核实的主张"）。
用途：投稿前把**格式类**驳回理由一次性清掉；也用于核对 AI 审稿人提出的"该刊要求…"是否属实。

---

## 1. Graphical abstract（强烈建议）
- 约 **920 × 300 px**，JPEG / PNG / SVG，在 Snapp 提交时归入 **"figures"**。
- 图注 **≤ 30 词**。
- **图注必须是图片文件的一部分，且位于图片下方**——即图注要**烧进图片**，不是单独一段正文。
- 内容可与文中某张图相同，也可以另做或做合成图。
- 需符合 Springer 版权政策。

> 落地做法：用 `patchwork`/`cowplot` 排版后 `ggsave(width=9.20, height=3.00, dpi=100)` 得到
> 920×300 px；图注用 `labs(caption=...)` 或 `annotate` 画在底部，导出后**必须 OCR 复核图注确实
> 在图片内**（见 references/ 下图表取证专题）。

## 2. Research Insights（建议加，投稿时作为**表格**上传）
置于摘要下方，**< 200 词**，固定四问：
| 问题 | 限制 |
|---|---|
| What is currently known about this topic? | 最多 3 条 highlights |
| What is the key research question? | **必须写成疑问句** |
| What is new? | 最多 3 条 highlights |
| How might this study influence clinical practice? | 最多 1 条 highlight |

**每条 highlight ≤ 100 字符**（含空格与标点）——这是硬限制，写完后逐条数字符。

## 3. LLM / AI 使用声明
- LLM（如 ChatGPT）**不满足作者标准**，不得列为作者。
- **LLM 的使用必须写在 Methods 节**（若无 Methods 则写在合适的替代位置），并**说明其具体作用范围**。
- 只放在 Declarations 里**不合规**——这是常见驳回点。

## 4. Abstract / Keywords
- 摘要 **≤ 350 词**，结构化四段：**Background / Methods / Results / Conclusions**。
- **不得引用参考文献**；尽量减少缩写。
- 关键词 **3–10 个**。
- 若报告人体干预试验须注册号 + 注册日期，非前瞻注册须写 "retrospectively registered"。

## 5. Abbreviations（易漏）
- 缩写在正文**首次出现处定义**，并另设 **List of abbreviations** 节。

### 5.1 投稿系统栏位："列出使用 ≥3 次的全部缩写"——先问字符上限，再作答

**真实教训**：编辑要求 *"Please enter all abbreviations that have been used in this manuscript at
least three or more times. Some examples using correct format include - MELD:model for end stage
liver disease; AST:aspartate aminotransferase"*。我直接给出了 **31 项、1,075 字符**的清单，
用户连续退回两次：先 *"不能黏贴你上面的 31 项"*，再 *"人家还有要求：Limit 200 characters"*。

⇒ **规则：凡是"填某个投稿系统栏位"，先确认（或主动询问）该栏位的字符/词数上限，再产出内容。**
系统页面上显示的上限就是硬约束；上限不明时先问一句，比交一份超长的答案再返工便宜得多。
（同类现象见 §2 的 Research Insights：每条 highlight **≤100 字符**、§4 摘要 ≤350 词——
**该刊系的所有栏位都带硬计数**。）

**≤200 字符下"39 项缩写"怎么放**——这是个背包问题，不要凭感觉挑：

```python
# 成本 = len(缩写) + 1(冒号) + len(全称) + 2("; " 分隔)   价值 = 该缩写在全文的出现次数
# 用 DP 在 200 字符预算内最大化被覆盖的出现次数；也可改成最大化条目数，给用户两套备选
items = [(ab, n, len(ab) + 1 + len(full) + 2) for ab, n, full in DATA]
```
实测结论：200 字符**只能放 4–7 项**（`NHANES:National Health and Nutrition Examination Survey`
一项就吃掉 59 字符；`CHARLS`、`MASLD`、`SVM-RFE`、`ssGSEA` 这类长全称一项顶三四个）。

产出时给用户**一套推荐 + 3–4 套备选**，每套**标出精确字符数**与"OK / 超限"，让他挑；
推荐口径 = **最高频 + 最核心**（结局、暴露、疾病、主队列、主中介）。

**其余口径**：
- 用**期刊自己示例的格式**：冒号后**不留空格**（`MELD:model for end stage liver disease`），
  每项省 1 字符；分隔用 `; `；
- 顺序用**正文首次出现顺序**；
- **剔除**三类：基因符号（CXCL9/COL1A2…）、数据库编号（GSE84044…）、拉丁缩写（e.g. / vs. / et al.）；
- **计数口径要说明**：按整份手稿（正文 **+ 图注**）计数，并主动告知"FDR、ssGSEA、SVM-RFE 这几项是
  靠图注才够 3 次的"——**多列不会出错，少列才可能被追问**；
- 顺带查一遍**正文里有没有用了 ≥3 次却从未写全称的缩写**（本轮抓到 `AST`/`ALT` 只出现在
  FIB-4 公式里、全文无全称，而期刊给的示例恰恰就是 `AST:aspartate aminotransferase`）
  → 这类要提醒用户回正文补全称，并给出最小改动写法；
- 编辑若追问"为什么不全"，回：*"The submission field is limited to 200 characters; the full list of
  N abbreviations (each used ≥3 times) is available in the manuscript and can be provided in any
  format required."*

## 6. Declarations（必须含**全部**子标题）
顺序与名称照抄，缺一不可；不适用者写 "Not applicable"：
1. Ethics approval and consent to participate（须给**伦理委员会名称 + 批件号**）
2. Consent for publication
3. Availability of data and materials
4. Competing interests（用作者**缩写**逐个指代；无则写 "The authors declare that they have no competing interests"）
5. Funding（须声明资助方是否有具体角色）
6. Authors' contributions（用**缩写**指代）
7. Acknowledgements（可写 "Not applicable"）
8. Authors' information（**可选**）

## 7. Availability of data and materials
- 必须写"支撑结论的**最小数据集**"在哪；允许"合理请求"型声明，但外部验证/建模类研究
  更应给**公开仓库或匿名审稿链接**，并公开：完整变量映射、最终数据字典、**每个模型的完整系数
  与 baseline hazard**、运行环境与版本、生成表格图形的脚本、原始数据下载说明与访问限制。
- 引用公开数据集时给**持久标识符**（DOI，写成完整 URL），宜进参考文献列表（DataCite 最低信息）。
- 可用句式模板共 6 种（仓库链接 / 合理请求 / 已含于文中 / 因故不公开 / 无数据 / 第三方许可限制）。

## 8. References / 链接 / 脚注
- **Vancouver** 体例；期刊/DOI/书章/在线文档/数据库/数据集各给样例。
- **所有 URL（含作者自建网站）都要编号进参考文献列表**，格式：
  `站点标题. URL. Accessed 20 May 2013.` ——**必须带访问日期**，不写在正文里。
- **用脚注，不用尾注**；正文脚注连续编号，表格脚注用上标小写字母（显著性用 *）。

## 9. Title page
- 标题宜含研究设计（如 "X is a risk factor for Y: a case control study"）。
- 列出**全部作者全名 + 单位地址**；指明通讯作者。
- 协作组作为作者时，组名需同时出现在标题页与提交系统。

---

## 10. 投稿前程序化自检清单（本项目实测有效）
```text
[ ] 摘要 ≤350 词、四段式、无引用
[ ] 关键词 3-10
[ ] List of abbreviations 存在，且正文缩写首次出现处有定义
[ ] 投稿系统栏位**先确认字符上限**再作答（缩写栏位、Research Insights、GA 图注都带硬计数）
[ ] Declarations 八个子标题齐全（缺一即驳回）
[ ] LLM 使用已写入 Methods（不是只在 Declarations）
[ ] Graphical abstract ≈920×300 px，图注 ≤30 词且烧在图内下方（OCR 复核）
[ ] Research Insights 作为表格，<200 词，每条 ≤100 字符，四问齐全
[ ] Availability 声明含最小数据集位置 + 持久标识符
[ ] 所有 URL 已编号进参考文献并带访问日期
[ ] 表格为原生表格 + 三线表；图表文件名可自解释
[ ] 图 300 dpi TIFF（另有版权/尺寸要求时以 General formatting guidelines 为准）
```

## 11. 未经核实的主张（不要当期刊政策引用）
AI 审稿人常以"该刊格式指南明确要求 X"下断言。本项目遇到一条：
**"该刊不建议用逗号表示千位数值"**——该主张**未能在本文核对的页面上证实**。
处置原则：
- 先去期刊的 **General formatting guidelines** 逐字核对；核对不到就不要写成"期刊要求"。
- 若该改动**低风险且可逆**（去千分位逗号、统一术语），照改无妨，但**不要**在对用户的报告里
  宣称"这是期刊硬性要求"——如实写"审稿人提出、未在页面上证实、已按低风险处理"。
- 反之，凡是**会改变科学主张/数字**的"期刊要求"，必须先核实再动。
