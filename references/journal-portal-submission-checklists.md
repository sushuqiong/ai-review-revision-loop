# 期刊投稿系统操作清单（Editorial Manager 系 / 通用）

用户会直接问"**怎么投稿 X 期刊？**"。答案要落到"点哪里、传哪个文件"级，
并给出**逐项文件映射**（用户最怕的是传错文件/漏传）。

本文以 **BMC Gastroenterology**（Editorial Manager）为模板；同一套流程覆盖
绝大多数 Editorial Manager / ScholarOne 期刊，差异只在文章类型名与附件栏名称。

## 一、动手前的合规自检（先跑，再答）

| 检查项 | 判据 |
|---|---|
| 摘要词数 | 目标刊上限（BMC 系 ≤350；PLOS 系 ≤300）。**为便于转投，统一压到 ≤300** |
| 摘要引文 | **必须 0**（BMC/PLOS 都要求摘要不列参考文献）。正文引用不受影响 |
| 结构化摘要 | Background / Methods / Results / Conclusions 四段 |
| 声明齐备 | Ethics / Consent / Availability / Competing interests / Funding / Authors' contributions / Acknowledgements |
| 缩写表 | 建议有（与正文实际使用的缩写对齐，不多不少） |
| 行号 + 页码 + 双倍行距 | BMC 排版要求；行号用 `w:lnNumType`，页码用页脚 PAGE 域 |
| 图件 | 宽度 ≤7.2 in、Type3=0、四边留白>0；**图内不放图例/整图标题** |
| 图表数/文献数与各文件声明一致 | 主稿、Title page、Cover letter 三处必须同数 |
| STROBE | 观察性研究必交 |

## 二、BMC Gastroenterology 投稿步骤（Editorial Manager）

1. 期刊主页 **bmcgastroenterol.biomedcentral.com** → 右上 **"Submit manuscript"**
   （或直接 `editorialmanager.com/bmcg/`）
2. 注册/登录（用通讯作者邮箱；建议机构邮箱）
3. 新建投稿，**Article type 选 `Research article`**（不要选 Brief report / Correspondence）
4. 逐屏填：Title → Abstract（粘四段，**不带引文**）→ Keywords → Authors（标通讯作者、
   填 ORCID、按 CRediT 标贡献）→ Funding（逐条基金编号）
5. **建议审稿人**：3–5 位，从参考文献里挑**利益无关**者（排除合作者/同单位）；
   须如实披露与候选人的关系
6. 上传文件（见 §三）→ 系统**自动合成 PDF** → **逐页检查**（图是否变形、表是否跨页断行、
   行号页码是否正常）→ **Approve submission**
7. 收到确认邮件 + 稿件号（如 `BMG-D-26-XXXXX`）

## 三、文件映射模板（按此清单上传，逐项打勾）

| 上传项 | 文件 |
|---|---|
| Manuscript | `05_论文投稿/论文_全文_投稿版_vN.docx`（含表与内嵌图）|
| Title page | `04_投稿材料/Title page_vN.docx` |
| Cover letter | `04_投稿材料/Cover letter_vN.docx`（**须指名期刊 + 适配理由**）|
| Figure 1–n | `03_图表/Fig*_vN.pdf`（**优先 PDF 矢量**；PNG 需 ≥300 dpi）|
| Figure legends | `04_投稿材料/Figure legends_vN.docx`（图例独立成文件，用户硬规则）|
| Supplementary | `04_投稿材料/Supplementary Materials_vN.docx`（选 **Additional file**，不是 Supplementary material）|
| STROBE checklist | `04_投稿材料/STROBE checklist_vN.docx` |
| 复现材料 | 打包成**一个 ZIP** 作为 Additional file（代码 + 数值输出）|
| Plain English summary | 可选 |
| Highlights | **BMC 不要求**，可不上传 |

## 四、费用与周期（BMC Gastroenterology）

- **APC US$3,390**（OA 必付）；中国一般无自动豁免 ——
  **投前建议问单位图书馆/科研处是否有 Springer Nature Transformative Agreement**（可免/打折）
- 初次决定通常 **4–8 周**（编辑初筛 ~1 周 + 外审）
- 单盲，通常 2–3 位审稿人；版权 CC BY 4.0

## 五、期刊选择：要如实告知"水刊"语境

用户自己维护了一份"SCI 水刊合辑"（`sci水刊合辑.docx`），**BMC Gastroenterology 与 PLOS ONE
都在该名单内**。当用户问"该不该投这本"时：
- 给**匹配度**判断（收稿范围是否覆盖主题）**和**层次判断**（是否在其水刊名单内），两者分开讲
- 同时给出更高级别但拒稿风险更高的备选（如 **Digestive and Liver Disease** IF≈4.0、
  **World Journal of Gastroenterology** IF≈5.4），并明说代价
- **不要**把"免 APC"等同于"更容易发表"（DDS 明确不鼓励微小增量研究）
- 结论要给**可执行选项**（A/B/C），让用户拍板

## 六、转投兼容性（一次做好，多次可用）

把摘要压到 **≤300 词且 0 引文**，就同时满足 BMC（≤350）与 PLOS（≤300），
**转投无需重写**。这是"一次做对、降低后续成本"的最划算动作，动手时优先做。
