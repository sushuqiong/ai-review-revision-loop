# 交付形态与交付后维护（本用户偏好，硬要求）

本文件是 SKILL.md "交付形态" 一节的完整版，含交付**之后**的维护规则。

## 一、交付物形态（每次返修都适用）

- 交付物**一律 .docx**（用户不开 .md）；根目录放一份"先看这个"说明 + 逐项上传清单。
- 操作类说明必须写到"点哪里"级（用户非开发者）：菜单名 → 按钮名 → 编号步骤。
  涉及浏览器/商店/扩展等操作，还要给自解释文件名（如 `★上传商店-就选这个文件.zip`）。
- 上传＝**一个栏位一个文件**，不要把多张图塞进一个 Word。补充材料也**逐份单独文件**
  （4 张补充表 = 4 个 docx，不要合并成一个大文件）。
- 表格一律**学术三线表**（无竖线；顶线/表头下线/底线），实现见
  `references/figure-ocr-layout-qa.md` §七·补。
- 程序化改过的图必须附 `preview_*.png` 供用户自查，并写明"直接传这个、不要用原图"。
  预览图放子目录（如 `Figures/核对预览/`），**不要和要上传的文件混在一起**。
- 主动列"其它明显问题"（用户会直接问"还有什么问题"）；跑了但未写入正文的分析要**告知并给
  A/B/C 选项**。
- 用户问"这你能做到吗"时，默认**自己做掉**（如原位替换合成图子面板），不要转成用户的手工操作。
- 用户会反复要求"不要自爆"：返修意见没提、审稿人不会查的问题**不要主动改、不要单独立段交代**。
  发现自己写的句子不成立时，**优先删掉那句可选的话**，而不是把它修饰成可见的说明。

## 二、交付**之后**的维护（本轮新增，最高优先级）

用户会把交付文件**重命名 + 手工修改**（本轮：`01_/02_/03_/07_*.docx` → `Manuscript_revised.docx`
等，并跑了一次全局"特殊字符→ASCII"清理、删掉了手稿里的 Figure legends 节）。

> **铁律：此后一律在用户当前文件上做 run 级定点修改，绝不重跑构建脚本。**
> 构建脚本从 pristine 原件重建，会静默抹掉用户的全部改动。

完整配方、反面教材（整段 `set_text` 压平上标、scratch 副本路径前缀替换失败导致在用户目录
误建文件）、备份与 diff 自证、以及**变更标蓝**的确定性做法，见
`references/docx-inplace-editing-and-change-marking.md`。

## 三、用户说"只检查不要改"时

纯只读审计：报告问题 + 位置（文件/段落号）+ 建议改法，**一行都不动**。
给出编号清单后用户会用编号选（如"2、3、4、5"）→ **只改这几个**，
并在回复里逐项说明，同时点明"其余项按你的选择未动"。

## 四、语气与文档风格

- 用户明确说过"**你写的 Word 文档的 AI 味普遍有点明显**"。
  ⇒ 回复信/说明文档用朴实文体：删掉 "We are sincerely grateful" 这类套话，
  去掉 First/Second/Third 的排比骨架，句子改短，**说事为主**。
- 署名（回复信）：只写通讯作者 **[Corresponding Author]**，不要写第一作者 [First Author]。
- 沟通与交付说明一律中文。
- ★ **「太啰嗦、而且英文我看不懂」**（v19 轮，针对建议审稿人名单）。
  ⇒ 面向用户的**辅助性交付文档**（名单、操作说明、清单、对照表）：
  1. **正文用中文**——只保留必须英文的部分（人名、机构、要粘贴进投稿系统的英文段）。
  2. **篇幅优先小**：目标 ≤2 页。单人/单项信息压到 3–5 行，**不要写长篇论述**。
     反面教材：11 页 5,600 字符被投诉 → 重做后 2 页 2,085 字符。
  3. **用户要"抄"的内容**（邮箱、数字、文件名）**加粗/标色**让它跳出来。
  4. 改了这类文档后**删掉旧版**，桌面上只留一份，否则用户会拿旧版再投诉一次。
  ⇒ 判断标准：**这份文档是给用户"照着做"的，不是给我自己"交代清楚"的。**

- ★ **手稿本身的行文纪律**（v22 轮，用户原话"太长太啰嗦、不够学术风不够严谨"）。
  最常被点的是 **Conclusions**：压到 **150–200 词**、**不复述 Results 已交代的细节**、
  不堆叠多重从句；结构 = 「结论性判断 → 结果（带关键数值与不确定性）→ 解读 → 一般化建议」。
  本项目 308 词单段 → **180 词**，关键数值全部保留。摘要/图注同理按此口径压缩。
  核查法见 `references/docx-and-figure-programmatic-qa.md` §9.6。

## 五、本主题相关的其它 reference / script（本轮新增）

| 文件 | 用途 |
|---|---|
| `references/docx-inplace-editing-and-change-marking.md` | 用户手改后的 run 级定点修、备份+diff 自证、变更标蓝 |
| `references/graphical-abstract-production.md` | 产出可上传的 Graphical Abstract（量原图、只用正文数字、纵向网格、机检） |
| `references/figure-ocr-layout-qa.md` §九 | PDF 文字层质检（越界/重叠/字号）+ 4 个 ggplot 真坑 |
| `references/submission-readiness-adversarial-qa.md` §3b/§3c | 投稿包跨文件一致性 + 用户手改后的复检 |
| `references/journal-submission-compliance.md` | 目标期刊硬性约束核查（BMC 实测清单）+ 作者名单变更传播规程 + 投稿分步 |
| `references/submission-artifact-hygiene.md` | **长度纪律与格式一致性**：表注精简（2,379→1,400 词）、补充表格式漂移（底线/字号/超宽）、"不公开代码"的声明 sweep、Figure legends 三处分工、Cover letter 压到 1 页、投稿前清单+交叉引用终检 |
| `scripts/docx_table_format_audit.py` | docx 全表格式体检（宽 cm / 底线 / 字号），`--fix` 就地补底线+补字号+收窄超宽表 |
| `references/suggested-reviewers-and-email-lookup.md` | 建议审稿人名单（中文精简版骨架）+ 公开邮箱检索 + 回避名单 + Cover letter 模板段 |
| `scripts/qa_pdf_layout.py` | 直接命令行跑的 PDF 版面机检（`--expect` 可查关键数字是否渲染出来） |
| `scripts/pubmed_corresponding_emails.py` | 用 NCBI E-utilities 查已发表论文里的通讯作者邮箱（可溯源到 PMID，禁止编造） |
| `references/external-validation-and-censor-robust-metrics.md` | **预测模型/外部验证类稿件必读**：单一估计量贯穿全文、删失稳健主窗 vs IPCW 敏感性、Brier 统一定义与配对Δ符号、内部 apparent→乐观校正、local 模型窗内重拟、ΔC 不足时补 IDI/NRI+嵌套LR检验+DCA、IPW 处理 complete-case 选择偏倚、日历对齐、"过报分解"(基线风险 vs case-mix)、分期人数守恒审计、R 计算坑（coxph 函数内 data 丢失、长 `-e` segfault、`%<>%`/`ns()` 依赖） |
| `references/markdown-docx-roundtrip-pitfalls.md` | **md↔docx 往返与补丁安全**：pandoc docx→gfm 的四类破坏（`\[`转义、丢 YAML 标题、图片变 `<img src=media/rIdN>`、表格管道压扁）、禁止 `re.sub(r"\s+"," ")`（会压掉全部换行毁掉 md）、锚点先 find 再替换/整段切片、renumber 脚本目标常量必须核对、基金号 `[2023]1` 被当引文、补充表按 S\d+ 重排、三线表样式+表数/media 数校验、匿名版掩字段清单、python zipfile 打包 |

| `references/docx-and-figure-programmatic-qa.md` §9 | **交付包套件级一致性 + 终稿十项验收**：套件级表格字体统一（须同时写 `w:rFonts` 四属性 + `w:sz` + `w:szCs`，python-docx 部分 run 无显式字号导致同文档内不一致）、程序化新建表默认**非**三线表（Table Grid→style 12 + 单元格边框）、首页声明计数过期（word count 口径 = Introduction→Conclusions 排除声明；running title/补充表范围同批过期）、补充材料「**表全在图前**」+ 判图片要用 `a:blip` 而非 `'graphic' in xml`、插入小节后的**标题-正文配对/编号连续/交叉引用**三项断言、Conclusions 篇幅纪律 |
| `references/figure-legend-content-and-image-reembed-audit.md` §9 | **内嵌图分辨率实测**：`Figures/` 换过图之后 docx **必须重嵌**（改图内文字也算）；验收要比对**像素尺寸 + md5**（"md5 一致"只在同一时刻有意义），脚本打印"已嵌入 imageN ← FigN"只是**声明**不是**证据** |

> ⚠️ 维护提示：本 skill 的 `SKILL.md` 已达平台 100,000 字符上限，**无法再追加内容**。
> 新增知识一律写成 `references/` 或 `scripts/` 下的支持文件，并在本文件里登记一行；
> 如需继续扩充 SKILL.md 正文，必须先把已有长段落下沉到 references/。
