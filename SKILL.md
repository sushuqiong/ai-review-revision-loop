---
name: ai-review-revision-loop
description: 用 AI 模拟高分期刊审稿人系统性审查医学论文，再按优先级修复的闭环流程。适用于论文 Major Revision 前自查、投稿前质量提升、以及"AI 审稿→针对性修复"的可复用工作流。
---

# AI 审稿 → 针对性修复闭环 (AI Review-Revision Loop)

## 逐轮实测记录（索引）

> 完整记录见 `references/version-round-logs.md`（v7→v22 每一轮的：外部 AI 意见、本轮实际落点、踩到的坑与修法）。
> 需要回溯「这类问题上次怎么解决的」时先读该文件。

## 触发条件
- 投稿前模拟审稿人自查；Major Revision 系统化修复；从高分期刊编辑/审稿人视角提升质量；多篇并行审查修复

> 支持文件见 references/、scripts/（含 desk-reject 分诊、投稿系统机制、docx/图件 QA、版本升版图表同步、图例重嵌审计、**外审要求"重算"的补算配方 review-demanded-recomputes-and-validation.md**、submission-package-consistency-audit.md、**figure-table-renumbering-and-order-compliance.md**、base-artifact-and-claim-audit.md）。
>
> **交付前必跑的两个脚本**（v22 事故催生）：
> - `scripts/check_figure_table_order.py <主线稿> [<补充材料>] [--figures Figures]` —— 四类顺序断言（Table / Table S / Figure / Figure S）+ 标题物理排列 + 越界引用 + 内嵌图高清与 md5。**这是"顺序合规"的唯一防线**。
> - `scripts/renumber_figure_table_refs.py --main X --supp Y [--apply]` —— 按首现序重编号（两阶段哨兵替换、范围/并列形式、块升序重排三坑已内建；先 dry-run 看映射）。

## 交付形态（本用户偏好，硬要求；细则见 references/delivery-conventions.md）
- 交付物一律 .docx；根目录"先看这个"说明 + 上传清单；一个栏位一个文件；表格三线表（补充材料：全部表在前、全部图在后）；改过的图附 `preview_*.png`。
- 操作说明写到"点哪里"级；主动列"其它明显问题"并给 A/B/C 选项；"你能做到吗"→自己做掉。
- 不要自爆：返修意见没提的问题不主动改、不单独立段交代。
- **交付后用户会重命名并手改文件 → 只在用户当前文件上做 run 级定点修改，绝不重跑构建脚本。**
- **投稿包只留投稿件（用户明确要求"文件夹里很多没用的文件投稿根本没用"）**：根目录 = 主线稿 docx+pdf + Cover letter + Title page + STROBE/清单 + Figures/ + Tables/ + 补充代码；**内部件**（进度/交接说明、README、`_过程备份/`、旧版本过程文件、`*_work/` 分析工作目录）与**目标期刊不要的件**（如 Frontiers 不要求 Highlights / Plain English；MDPI 才要）一律移入 `_内部文件（不投稿）/` 子目录，不删只移。提交前**统一文件命名**（去掉 `01_`/`02_` 数字前缀，与已是裸名的文件一致）。docx 改完必须**重渲染 PDF**（LibreOffice headless），否则 PDF 停留在旧编号。

## ⚠️ 验证范围的诚实性（本用户最愤怒的一次，最高优先级）

**事故**：v22 交付前我反复报告「遗留问题 0」，用户据此认为可以投稿；实际**全文图表编号完全没按
正文首次提及顺序**（主稿首次提及序 `1→7→6→2→3→4→5`；补充表 S1–S16 近乎全乱；补充图 S1/S2 需对调）。
用户**已提交 Frontiers 后**才发现，直接质问 *"为什么你反复检查都发现不了这个问题？这个问题不明显吗？"*

**根因比"漏了一条规则"更深，三条都要认**：
1. **清单驱动，不是规范驱动** —— 我检查的是"我改了什么"（数值一致、措辞、三线表、字体、字数），
   不是"该任务领域必须满足什么"（投稿规范）。**凡不在我清单里的项，跑一百遍也是 0。**
2. **把「0」当成了结论** —— `遗留问题 0` 只等于"我清单内的项都过了"，我却说成了"稿件没问题/可以投稿"。
3. **结构性改动后没做全量回归** —— 插入 3.10–3.13 新章节、新增 S14–S16 后，全篇首次提及顺序被改变，
   我只查了"新引用是否悬空"，没有重跑全文一致性。

**规则（今后一律遵守）**：
- **报告只用范围限定措辞**：*"我检查了 A/B/C/D，均通过；**未**检查 E/F/G"*。
  **永不**说"可以投稿""没有问题""已彻底完成"——只报范围，不替用户下结论。
- **清单双向构建**：从「我改了什么」＋「该任务领域必须满足的规范」两侧生成。
  投稿类任务**先把规范清单写出来再动手**（图表编号顺序、图表引用完整性、字数/限长、
  摘要不带引用、参考文献编号连续、图注与图内数据源一致、交付夹只留必需件…），
  不要等交付前才现凑。
- **任何"插入/重排/新增/删除"结构性改动之后，重跑全量断言**，不能只验被改动的局部。
- **用户的重复追问是清单盲区的信号**：*"你确定吗""真的没有明显问题吗""为什么你没发现"* 出现时，
  正确反应是**去补"我还没检查什么"**（换角度、换标准、从审稿人视角自上而下过一遍），
  而不是复述已有结论或重复跑同一套脚本。
- 顺序类规范要写成**可执行断言**，不能靠"逐项读一遍"（`references/figure-legend-content-and-image-reembed-audit.md` §11 有可直接运行的脚本）。

## 核心原则

### ⚠️ 验证不是自证：「我的清单通过」≠「没有问题」（v22 最严重的一次失手）

**事故**：v22 全过程中我反复汇报"遗留问题 0、可以投稿"，而**图表编号没有按正文首次提及顺序**
（主稿 Table `1→7→6→2→3→4→5`；补充表 S1–S16 几乎全乱）——这是投稿的基本规范，
**用户已提交 Frontiers 之后才发现**。用户质问："为什么让你反复检查都发现不了？这个问题不明显吗？"

**根因不是"没检查"，而是检查的形态**：

1. **自证循环**：清单是我写的、脚本是我跑的、"通过"是我宣布的 —— 清单里没有的项，跑一百遍也发现不了。
2. **只查"我改了什么"，没查"投稿必须满足什么"**：编号顺序从未写进任何断言。
3. **大改动后只回归改动点**：我新增了 3.10–3.13 章节与 S14–S16 表，**改变了全篇提及顺序**，
   却只检查"新引用是否悬空"。
4. **用结论性语言掩盖清单之外的风险**（最不可接受的一条）。

**三条硬约束（每次交付前自查）**：

- **自上而下按"规范"过一遍**，不要只按"改动"过一遍。投稿规范的最小集合：图表编号＝首次提及顺序、
  字数声明＝实算值、参考文献编号连续无孤儿、图注描述＝图内实际内容、字体/字号对标模板且文档内唯一、
  三线表、文件命名一致、补充材料内标题排列升序。
- **大改动后做全量回归**，不是"点回归"（插入章节/新增图表会改变全局编号与顺序）。
- **禁用结论性语言**：不说"没有问题了 / 可以投稿"。只说："我跑了 X/Y/Z 三类断言，均通过；
  **未覆盖的是 A/B**"—— 把没验证的面明确标出来，不要把"我查过的"等同于"它是好的"。

**判断标准**：一个问题明显不明显**不是**标准，**它是否被写成了断言**才是标准。
凡是"审稿人第一眼就会看"的项（编号顺序、字数、图表一致性、模板格式），**必须落成脚本断言**。

1. **审稿必须基于真实证据**：subagent 读 docx、核对 rds/txt、PubMed 验证——禁止凭空给意见
2. **修复必须真实计算**：新增数值一律用 R 重算
3. **诚实报告**：数学上不可能的值必须修正并记录
4. **隐私保护**：投稿材料注意署名/邮箱；GitHub 发布不含个人信息
5. **收工门槛 = 独立对抗性复检（禁止自满收工）**：本用户会反复以「？/你确定做好任务没有遗留问题？/能逐条回应审稿人意见了吗？不然继续完善」追问——每次宣布 vN 完成或收工前，必须 (a) 自跑 references/submission-readiness-adversarial-qa.md 的程序化清单（docx 残留/引用首现序/数字 vs RDS 锚点/图表几何/占位符/已声明文件存在性）；(b) 再派独立 subagent 对照审稿人逐条意见（GPT6/Claude 的 numbered list）复检。subagent 自报不算验证——关键数字、引用序、图序、占位符须父代理亲自复核。用户问「确定吗」时先自查再答，不要嘴硬。

5d. **同一视角重复审查会收敛——必须换视角升级**。本用户会直接点单：「再跑一次独立的第三方式对抗审查（换一个审查视角重查）」。实测教训：连续两轮 same-lens 审查（都以「资深医学期刊审稿人」身份，查审稿意见落实 + 文档一致性）均报「基本通过、无实质问题」；换成两个真不同的视角后，**立刻挖出前两轮全部漏掉的实质缺陷**——两个视角并行，互不重叠：
   - **复算视角（独立复算统计师）**：假装要从零重跑这篇论文，逐个重算正文里的每个数字，验算术自洽。抓出：图脚本里的硬编码 `override` 污染正文（2.506 vs 真值 2.518）、主稿与补充材料舍入互相矛盾、整张补充表无本版源数据。
   - **生产编辑视角（期刊 production editor）**：只问「这份稿包能否过编辑部初筛与制版」——不问统计对错。抓出：主图物理尺寸过大导致缩印后字号 <8pt、缺 Abbreviations 章节、多个缩写全文无全称、PDF 为 Type 3 字体。
   规则：每个大版本收尾，same-lens 复检之后再补一次**异视角**审查（并行两个），且**审查者报的错误也要自己复核**——本轮两位审查者都称「Table 5 只有 12 行 × 5 = 60 个配对」，实测是 14 数据行 × 5 = **70**，「70」是对的（假阳性；数自己的表，别信别人的计数）。两套视角的完整清单与实测发现见 references/multi-lens-adversarial-review.md。
5b. **每个 vN 收尾时交付一份 vN vs vN−1 的显式对比**（用户会直接点单：「最后把 v12 与 v11 做一次对比确认，确保 v12 确实更好」）。可程序化产出的对比维度：新增的实质分析/新结果（逐项列出 vN−1 没有的）、作者/基金/声明等就绪状态、表格与图（数量、图序、重叠/裁切自检）、摘要词数、引用编号首现序、残留扫描（占位符/内部修订语言/中文残留）。同时**必须包含被推翻或被削弱的旧结论**（本例：撤销「age/BMI 承载大部分关联」、N3 M4 由显著转不显著、配对优势消失），并说明为何"结论变弱但论文更好"。只列"更多更好"的对比是不合格的。
5c. **复合指标论文：先做代数恒等核查，再谈"成分与整体相当"**。若指数是成分之和（如 `GLM7 = metab + log10(age) + log10(BMI)`），则模型一旦已含这些成分项，"完整指数 vs 其余成分"就是**精确重参数化**（实测 |Δb|≤1e-15、OR 比 = 1.000000）——近 1 的 OR 比**很大程度是数学结构**，不是独立发现。必做：加一个 log10(age)+log10(BMI) 独立线性项的核查框架，报告哪些框架精确/哪些近似；表题定位为 "index interpretation and scale sensitivity"；`equivalent associations` → `numerically similar conditional associations`；**不得暗示"去掉组成项 ⇒ 该成分与 age/BMI 统计独立"**。见 `references/manuscript-consistency-and-scale-checks.md` §A。
5d. **共同增量尺度换算：OR 与 SD 必须同源；换算是重参数化、不改变 P 值**。事故模式：把**上一版样本**（如 20–74 岁子样本 SD=0.6623）算出的共同尺度值写进当前**全年龄样本**的结果段。审稿人的抓法 = 换算后区间隐含跨过 1 而源估计未跨 1（不可能）。任何队列重建后所有派生值必须重算。见 §B。
5e. **每轮批量编辑后必做跨文档同步复核**（本类任务每轮都会重犯）：批量替换/标题同步/S 编号重排/docx 自动构建会引入重复句、断句、过期编号、内部痕迹（构建脚本名/数据源名/版本串 `v13`）、表格单元格里的中文残留、双份声明。固定程序：枚举补充材料真实表图标题与主稿声明 diff；全文件扫禁用 token 表；**所有表格单元格**扫 CJK；重数摘要词数并重建 Title page 元数据；标题变更后断言其在**全部 N 个文件**中一致。见 §C/§D。
5f. **摘要词数按两种口径各数一次**（含/不含结构标签），按更严的达标；**Title page 元数据每轮从构建出的 docx 重算**，不得沿袭上一版（实测声明 9,112 词 vs 实际 10,670）。见 §D。
5g. **"无个体重叠"这类声明必须有明确边界**：不同论文用同一调查周期可以复用同一批参与者，"各周期独立抽样"**不足以**推出"与开发研究无个体重叠"。正确写法：「使用部分相同调查周期（可能含部分相同参与者），重叠程度无法从公开文件量化」。同类问题还有：测量方法变更**含截距偏移时 z 标准化无法消除**，不能只写进局限性了事——要用官方提供的桥接方程做敏感性分析。
6. **docx 是 zip 二进制，禁止用 patch 工具直改**：`patch` 在 .docx 上找不到 old_string 会触发 File-mutation verifier 警告（看似没改）。一切 docx 文字/表格/图片/段落顺序修改走 python-docx 脚本：段内多 run 替换用 `runs[0].text = new; 其余 run.text = ""`；删段 `p._p.getparent().remove(p._p)`；在锚点前插段/图用 `OxmlElement('w:p') + addprevious`；重复插图会使 media 变孤儿（rels 里 6 张/正文用 3 张）——用 zipfile 按 r:embed 白名单清 media。
7. **核验要到一手来源，禁止「代理产物互检」（v13 教训）**：连续 4 轮 AI 审稿都声称「已落实」，但审阅方式只是**比对代理自己产出的文件之间是否自洽**，因此漏掉了 3 个影响核心结果的错误。每一项由数据派生的声明都要回到**一手来源**核对：
   - 变量**真实覆盖范围/分支** → 官方问卷与编码手册（不要信「这个变量就是全人群」）；
     判据信号：样本年龄上限/有效数恰好卡在某个问卷跳转阈值。
   - 统计**实现方式** → 读被实际调用的函数体（不要信方法学段落的自述），并将 bootstrap 与 Taylor 线性化 SE 交叉校验。
   - **尺度依赖的比较** → 换算到共同增量后结论是否还成立（复合指数 vs 其代数组分必查）。
   - 文献**归属/单位/周期重叠** → 打开被引原文核对作者名单、单位制、所用数据周期。
   → 详细陷阱、判据与修复代码：`references/survey-weighted-nhanes-pitfalls.md`。
   注意：查实的问题若推翻既有表述，**如实撤销并改写**（本例撤销「age/BMI 承载大部分关联」、N3 M4 由显著转为不显著、配对优势消失）；结论变弱不等于论文变差，作者本人也认可「诚实阴性增量」的定位。

8. **清单的出处决定了它能查出什么——自拟清单不能自证清白（v22 最惨痛教训）**：连续多轮自跑程序化清单并报「遗留问题 0」，但清单从**一开始就没有**"图表编号必须按正文首次提及顺序"这一项，于是跑一百遍仍是 0；用户**投稿后**才发现主稿表号 1,7,6,2,3,4,5、补充表号近乎随机。规则：
   - (a) 每轮交付前，除自拟清单外必须过一遍**外部标准**（目标期刊 Author Guidelines、该学科投稿常识、审稿人必查项），不能只查"我改了什么"，要查"投稿必须满足什么"。
   - (b) 外部标准里**能机器化的项，当场写成脚本断言**（见 `scripts/check_figure_table_order.py`），不接受"我记得检查"。
   - (c) **禁止**用「遗留问题 0 / 可以投稿」这类结论性措辞。只能写「我的清单 N 项全过；外部标准中以下项尚未机器化验证」——把不确定性显式交还用户。
   - (d) 大改动（插入新章节/新增 S 表/改结构）之后必须做**全量回归**，不能只验改动点：插入 3.10–3.13 就把全篇引用顺序变了，而我只查了"新引用是否悬空"。
   - (e) 用户质问「为什么反复检查都发现不了」时，不要辩解"问题不明显"——如实承认是清单缺项 + 结论措辞过度自信，并当场把缺项变成脚本。

9. **本技能自身必须保持"远低于 100k 字符"**（用户明确要求"删改没用的旧内容"）。SKILL.md 一度涨到 99,993/100,000（余量 7，几近写死）。维护规则：**新增经验优先写进 `references/<topic>.md`，SKILL.md 只加一行索引**；单文件超过 ~8k 字符的章节就该下沉；逐轮实测记录（`### vN ...`）一律合并到 `references/version-round-logs.md`；重复的「新增验证项」章节要定期合并去重（曾积累 7 个同名章节）。当前健康水位 ≈ 27k 字符。

对大型英文组学/Atlas 稿件，比单 subagent 更有效的是**一次 delegate_task 派 3 个平行评审人**，各扮演一种
视角，`toolsets=["file"]` 让它自己读稿件 md + results/ 下的结果 CSV 做数字核对：

1. **统计/方法学评审人**：多检验负担与 FDR 作用域（per-cohort vs 全局 108 vs 每病 meta）、meta 假设
   （SMD 方差近似、k=1 是否混入计数、I² 在 k=2/3 无意义）、xCell 单框架、单变量 Cox 未校正分期/纯度、
   阈值规则无错误率定义、对照定义异质、CSV 与稿件数字逐一对账（n 不一致清单必报）
2. **临床-转化评审人**：核心叙事新意是否文献已知、归因是否过度（"统计归因冒充机制结论"是最高频火力）、
   矛盾信号（bulk 下调但 OS 保护）是否会被读成批次/污染伪差、负结果是否如实、转化价值分级
3. **编辑/定位评审人**：标题摘要是否与 Sanchez-Vega 式 pan-cancer 图谱撞车、Declarations/代码仓库/伦理/
   CRediT 缺失清单、图注编号与正文 callout 错位/悬空引用、参考文献数量与格式、对 IF>6 期刊 desk-reject
   判定依据、"升级叙事最该加哪两个分析"（指认工作区内已有数据可立即做的，如 cBioPortal clinical 里
   已有 CRC SUBTYPE / PATH_STAGE / AGE）

每人要求输出：**Top5 拒稿风险（高/中/低）+ 逐条可执行修改建议（引原句）+ 期刊梯度评估**；明确要求
"引述必须来自文件，勿编造"。三份意见回来后：先列"共识=必改 / 尖锐单方=甄别"，再按
（①单变量生存 → 多变量+纯度/亚型 ②meta k≥2 计数 ③sc 分母 ④"replication"措辞 → 同队列双流水线 = internal
consistency ⑤组成稳健语义 persistent vs emergent）优先级打定向补丁到 v0.4，最后 docx/pdf 打包（含 eutils
拉全 volume/issue/pages 的 Vancouver 题录、图注编号统一、Keywords/Declarations 补齐）。本会话实例产出：
三视角命中完全独立（统计抓 k=1/分母，临床抓 over-claim/文献锚点，编辑抓图号悬空/Declarations），且
三人无一人漏掉"同一 TCGA 两套 pipeline 自称 replication"——该点是本类稿件最典型死穴。

## 多 AI 意见综合（multi-reviewer synthesis）——用户会给 2-3 个 AI 的独立审稿 docx（ClaudeOpus/GPT/ZLM 等）让你综合升级出下一版工作包

触发：用户给出多份"XX的继续建议.docx"+ 旧版本工作包

触发：用户给出多份"XX的继续建议.docx"+ 旧版本工作包（vN/vN.1），要求升级为 vN+1 并同步生成后台支撑包/理论后台包/知识库。这是本技能的"输入是意见文件而非 subagent"变体，流程：

1. **读全部意见 → 分三栏**：共识（全部 AI 都提的）= 必改；单方尖锐意见 = 需甄别；反向意见（一个 AI 主张保留、另一个主张删除）= 裁决点
2. **裁决必须用数据说话**：AI 声称的"数字矛盾"（如 60+20+10+10+10=110≠100）先解析原始数据文件（source_registry.jsonl / Supplementary_Table_S1.xlsx）验证——实例：实测 stratum 分布是 60+20+10+10=100，是 v22.1 正文文字重复计数 AIID 家族，数据本身没错 → 修正文不修数据
3. **共识优先、少数意见部分采纳**：三 AI 一致要删的（G²/Noether/守恒律/时间膨胀）直接删；反向意见（"保留 Hallmark 核心"）折中为"保留但降级"（探索性 C1–C10、无操作阈值）——两方都部分满足
4. **跨版本统计量矛盾一次性解决**：v21 报 kappa=0.72、v22.1 又不报 → 新版明确"撤回"声明 + 未来信度研究的 provenance 要求（双编码者/日期/原始表/未调解向量），绝不携带不可审计的数字
5. **诚实边界贯穿**：标题去误导词（"AI health" 被读成医疗 AI 治理）、"interoperable" 降级 "candidate"、未拟合方程移出正文、删除未来纪年引用（AI Index 2026）
6. **删之外必须有增**：新版本要新增可辩护贡献（crosswalk、双估计量实证），否则变成纯防御性版本
7. **同步生成配套包**：工作包之外按旧版结构同步生成 后台支撑包/理论后台包/飞书 sync_staging/Obsidian 知识库；详见 references/multi-ai-review-synthesis.md

## 第四位 AI 评审 + 文献防幻觉验证（v23/v24 → v25 实例）

评审者会累积（本会话第 4 位 ChatGPT 对 v23/v24 给出新一轮意见，且与前三轮部分重叠）。多轮意见综合时新增规则：

8. **AI 声称的"新近文献"必须先经 arXiv API 核实再引用（防幻觉硬规则）**：ChatGPT 声称存在 2026 年 AAAI 论文、public-health-lens 预印本、RiskNet 数据库。逐条用 `export.arxiv.org/api/query` 验证：`search_query=all:"AI incident"+AND+all:"reporting"&sortBy=submittedDate&sortOrder=descending` 列近期相关论文、`id_list=` 按 ID 取单篇、`<entry>` 里提取 title/author `<name>`/published/`<id>`。本会话 9 篇全部真实存在（2604.19914 / 2606.08376 / 2511.05914 / 2604.23183 / 2604.21412 / 2607.05163 / 2605.16281 / 2603.04259 / 2604.24519），作者名单也从 API 拿到填入参考文献。**凡是 AI 意见里出现具体论文/项目名，一律先查证再写进参考文献；查不到的绝不引用**（ChatGPT 提到的另一个数据库就未通过验证）。配方见 references/arxiv-verification-wilson-intervals.md
9. **描述性比例用 Wilson 区间替代 Wald（AI 评审点名"置信区间不合适"）**：靠近边界的比例（91/100）Wald 区间（85.4–96.6%）偏窄且可能越界，Wilson 区间（83.8–95.2%）更稳健。但更根本的是：**非概率抽样语料不能做总体推断**——区间只标注为"descriptive precision statement about the sampled corpus"，正文显式写 "not confidence intervals for a population proportion"。公式 + Python 实现见 references/arxiv-verification-wilson-intervals.md
10. **范围/题目与样本不匹配 = 必须改题**：ChatGPT 指出"for agentic systems"标题但严格 agentic 样本仅 5/100 → 标题改为描述文档缺口本身，正文把 agentic 分层（5 definite / 40 unclear / 45 sensitivity）写成边界声明。同理 v24 正文零文内引用（孤立文献列表）是"严重倒退"，新版必须恢复编号引用并做全量 1..N 校验
11. **冲突裁决模式：先给对抗性分析，再 clarify 让用户定**：ChatGPT 主张删 C1–C10、用户历史偏好保留 → 先输出中立对抗性分析（支持/反对证据 + 风险收益），推荐折中方案（降级到补充材料），用户选"先看你的对抗性分析再定"后同意降级。**重大分歧不要自己拍板，用分析+选项让用户决策**
12. **三轮对抗性审查（程序化→人工→视觉/程序化）**：①程序化：引用 1..N 零孤儿（含 en-dash）、关键数字与计算值比对、残留词扫描（Noether/G²/Einstein/占位符）；②人工审稿：找无编号引用（图例提到 MIT AI Risk Repository 但参考表没有 → 补 [38]）、表述歧义（"recoverability 14/100" 未区分 present=0/partial=14 → 精确化）；③视觉/程序化：PDF 表格用 `page.get_drawings()` 验证恰好 3 条水平线（粗顶线 0.87 + 细表头线 0.55 + 粗底线 0.87，无竖线）——**vision 模型在低 DPI 下会误判"表格没有线"，程序化 line 提取是可靠判定**（见陷阱 34 的验证扩展）

## 外审驱动"科学重新定位"（AI 审稿建议重做分析框架，vN → vN+1 最大动作）

当 AI 审稿人（ChatGPT/Claude）对近定稿的复合指数-疾病论文给出"**研究框架本身过度声称**"的判断（本会话实例：ChatGPT 评 v6\"GLM7 与胆囊结石\"——创新不足、GLM7 内嵌年龄/BMI 造成结构性关联、AUC 不优于 BMI），修复不是措辞降级而是**整体重新定位为增量价值检验**。用户确认"完全采纳重新定位"后按以下框架重跑分析（目标期刊从 Scientific Reports 改投 BMC Gastroenterology）：

1. **加权分析升为主分析**：NHANES 官方要求用最小抽样子样本权重（P 周期 WTSAFPRP、L 周期 WTSAF2YR），未加权降为敏感性。审稿人把"非加权作主分析"列为重大统计质疑
2. **结局拆分**：自报疾病复合结局拆成 (a) 自报诊断 (b) 手术史 (c) 联合三套独立分析（MCQ550/MCQ560/联合）——复合结局混淆两种不同暴露-结局时间关系
3. **增量价值比较（核心新分析）**：base 临床模型 vs +BMI vs +WHtR vs +TyG vs +TyG-WHtR vs +GLM7，加权 AUC + 95%CI + DeLong P（roc.test 配对）；报告 ΔAUC。诚实结论模板：\"GLM7 ΔAUC 0.011 (P=0.0096) 低于 BMI 的 0.024——增量有限，主要信息来自年龄与肥胖组分\"。**增量小是研究发现而非缺陷**，写进摘要结论和 Cover letter 定位段
4. **删删删**：筛查阈值/candidate cut-point（RCS 中 OR=1 交叉点依赖人为参照值，非临床切点）、\"窗口期\"机制故事、\"优于人体测量学\"声称、亚组机制解释（不重复验证就降为探索性）
5. **术语再降级**：\"temporal validation\" 都过强 → \"later-period replication / replication in a non-overlapping NHANES period\"（同一 NHANES 体系后一波次横断面，非独立纵向验证）
6. **删一组分分析改名** component-omission robustness analysis，明确\"只说明指标对组分统计敏感程度，不证明生物机制\"
7. **补齐 ChatGPT 点名的盲区**：跨周期实验室可比性（TG 检测平台更替、LDL 计算方法统一 Friedewald、周期内 z 标准化敏感性）、逐步排除人数、缺失数据描述、完整病例局限、公开 R 代码+变量映射表
8. **产生新结果后同步重建一切**：新图（筛选流程图/加权森林图/增量价值 AUC 对比图）、新 Table、新 Cover letter/Highlights/Plain English/STROBE、新交付文件夹（精简为 分析代码+结果+图+投稿包+README，不要复制旧版审计/过程文件）。**补充材料同步生成**（Supplementary Materials.docx：Table S1 未加权敏感性 / S2 去年龄 / S3 加权四分位+M3b / Figure S1 单指标 ROC，数值全部来自重算 rds），并在主文稿补 "Supplementary Tables S1–S3" 引用

注意：这种重定位通常意味着**主要数字全部变化**（加权 OR、AUC、样本量），旧版所有衍生材料（Cover letter/Highlights/GA 说明）都要按新数字重做而非修补；同时用户要求"必要时多问意见"——重定位幅度大，先 clarify 确认用户接受工作量和方向再动手。完整可复现配方（数据准备/加权主分析/增量价值/流程图/交付结构）见 `references/nhanes-incremental-value-repositioning.md`

### 参考文献扩充验证流程（27→44 条，PubMed 逐条验证）
AI 审稿指出"参考文献太少"时，按此流程扩充（本会话 27→44 条全部验证通过）：
1. 读 docx 提取现有 References 段落 → 按主题列扩充清单：流行病学/代谢综合征/各指标原始文献（TyG→Simental-Mendía 2008、HOMA-IR→Matthews 1985、LAP→Kahn 2005、METS-IR→Bello-Chavolla 2018）/NHANES 官方设计文献（Johnson 2014、Terry 2024）/方法学批评（Cook 2007、Pepe 2004）/统计方法（Hanley-McNeil 1982、Lumley 2010、Robin pROC 2011）
2. **逐条 PubMed E-utilities 验证**（esearch + esummary 拿 PMID/题名/期刊/卷期/DOI）；无 PMID 的用 Crossref（DOI 10.xxxx 解析）
3. **验证必抓原稿引用错误**（本会话 27 条中发现 6 处：Aune 期刊错、Bello-Chavolla 张冠李戴成 omarigliptin 试验、Vickers 期刊错、Lumley 卷期 9(1)→9(8)、Chen TC 作者表错、Chen TC 从未被正文引用）
4. 按正文首现顺序重排编号 → 输出扩充版 docx（含"新增文献插入位置表"+"原→新编号映射表"）→ 用 python-docx 替换论文 References 段（先删旧文献段再 addnext 逆序插入新段）
5. **替换文献表 ≠ 重映射正文引用（v8 实测的最大坑）**：只换 References 段后，正文 `[n]` 仍指旧 27 条编号，与 44 条新表系统性错位约 23 处（TyG 定义引到胆石综述、GLM7 引到 MetS 论文）。必须：①按语义逐段重映射正文引用（`_fix_h1.py` 模式：段落索引 + 旧引用串 → 新引用串）②补引孤儿条目（重映射后 44 条中 15 条无引用）③**全量孤儿检查**：`_cite_check.py` 提取正文全部 `[n]`/`[n–m]` 引用（注意 en-dash 区间展开），断言 1..44 全部被引、无未引条目。语义映射表要基于文献内容（如正文"TyG 原始定义" → Simental-Mendía 条目），不能按编号猜
6. **锚文本补引必须限制首次出现且避开文献表**：用 `"METS-IR"` 作锚插 `[25]` 会命中正文 10+ 处（含摘要/讨论/表格）**并污染参考文献表自身条目**（"Wang... METS-IR [25] index with prevalence..."）。修法：按"段落索引 + 更长的唯一锚串"精确替换，或只替换第一次出现；跑完后 grep 文献表段（`^\d+\.\s`）确认无 `[n]` 残留。插入后的全稿校验必须扫"正文引用编号集合 == 1..N 全覆盖"而非仅扫关键词
7. 替换后全稿校验：无 `[Author placeholder]`、`[In preparation]` 残留；正文引用编号与文献表一一对应（44/44 零孤儿）

## 流程

### 第 1 步：派审稿 subagent（每篇论文 1 个，并行）
给每个 subagent 的 context 必须包含：
- 论文 docx 路径 + 读取方法（`D:\ProgramData\python.exe` + python-docx）
- 分析结果文件路径（rds/txt/csv）——供数值核对
- 目标期刊（决定格式标准：Nutrients/Elsevier/BMJ 系）
- 审查维度清单（必查项）：
  - **语言**：中式英语、口语化、过度声称（cross-sectional 不能说 causal）
  - **格式**：IMRAD、Abbreviations 表、参考文献 Vancouver 顺序、图题编号、标题残留
  - **统计深度**：样本量/EPV、多重比较校正、敏感性分析完整性、E-value、中介分析细节（bootstrap 次数、medsens）
  - **解释**：与既往文献具体对比、局限性诚实度、临床意义是否说过头
  - **图表**：缺失图（流程图/森林图/列线图）、分辨率、编号顺序
- 要求输出：逐条问题清单（高/中/低严重度）+ 具体修改建议 + major/minor revision 决定 + 保存审稿意见 md

### 第 2 步：修复（并行 subagent 或主线程）
按优先级修复：
- **P0 数据完整性**：数学不可能值、与管线输出不一致的数值、内部矛盾
- **P1 方法学**：公式可复现性（补常数/截距）、缺失比较对象（如 FLI/HSI）、术语过度声称（external→temporal validation）
- **P2 格式**：图编号、参考文献重排、Abbreviations 表、CRediT、Article history 框
- **P3 语言**：措辞降级、中式英语、删除候选标题残留

### 第 3 步：重新生成 + 验证
- 修改 docx 生成脚本或直接 python-docx 编辑，输出 v2/v3 版本（保留原文件）
- 验证：错误数值是否清除、新增内容是否到位、数值是否与 rds 一致

### 第 6 步：打包交付
仿照用户标杆（如 `新的CLD-AIP`）结构：
```
交付_课题X/
├── 01_原始数据/  (rds/xpt/csv)
├── 02_R代码/     (全部脚本)
├── 03_分析结果/  (rds/txt/报告)
├── 04_图表_矢量/ (SVG+PDF+PNG 三格式)
├── 05_论文投稿/  (docx+pdf+Cover letter+Graphical Abstract)
├── 06_审稿与修改/ (审稿意见+修改记录)
└── 07_README/   (README.md)
```
**交付文件夹必须"逻辑清晰、只含投稿相关文件、多余文件少"（用户明确要求）**：重定位/大版本升级时建议用更精简的结构（本会话 v7 实测 37 个文件、5 子目录即够）：
```
vN_交付_课题X/
├── 01_分析代码/   (按步骤编号的 R/py 脚本，如 01_v7_加权主分析.R)
├── 03_结果数据/   (重算 rds，命名 v7_*.rds)
├── 04_图表_矢量/  (Figure 1-N + Figure S1 × SVG/PDF/PNG)
├── 05_论文投稿/   (论文 + Cover letter/Highlights/Title page/Plain English/STROBE/TRIPOD/Supplementary)
└── 06_README/     (README：版本定位/核心结果表/文件清单/待办)
```
不要复制旧版审计报告、调试脚本、中间产物到新交付文件夹。另：GLM7 根目录会积累大量 subagent 调试残留（inspect_*.R / prep_* / verify_* / _tmp_* / _dump_*.txt / audit_*.R）——每轮工作结束主动 `ls` 根目录，把临时脚本删除、旧版本交付（如 `课题1_v8/`、`课题3_v7/`）归档到 `_归档_过程文件/`（先 clarify 确认哪些是最新交付不能删）。

### 第 4.5 步：去 AI 味（用户要求"用去AI味的 skill 完善手稿"，humanizer 标准）
论文内容定稿后、审计前，用户常要求去除 AI 写作痕迹（em dash 过多、Additionally/Moreover 堆砌、过度副词）。流程：
1. 加载 humanizer skill，按其 29 个 AI 模式清单扫描 docx（em dash、Additionally/Moreover/Furthermore、underscores/highlights、robust/demonstrated、In conclusion 等）
2. 优先修 em dash（9+ 个是典型信号）→ 改逗号/括号；冗余副词精简；**机械替换后必须做语言 QA**（见陷阱 53：不成对括号/粘连 token/表格注脚语义破坏）
3. 医学论文保持学术严谨——只去明显 AI 痕迹，不引入口语化；"earlier versions of this analysis"（诚实披露 TyG 修正）这类科学叙事不是 AI 味，保留
4. 去味后复查：em dash 计数归零、句子通顺、无标点错乱

### 第 5 步：投稿前全面审计（用户要求"从审稿人角度检查所有图/手稿/主要文件不要有低级错误"）审稿修复完成后、交付前，必须再做一轮**全文件审计**（可派 3 个 subagent 并行，每篇论文一个）：
- **数字交叉核对**：正文 ↔ 摘要 ↔ 表格 ↔ 图题 ↔ 分析 rds，所有样本量/OR/AUC/P 值逐一比对；表格内部加和闭合（如四分位 n 之和 = 总 n）
- **独立重算核心数值（数据可靠性审计，不止比对已有数字）**：用 R 从原始队列 rds 重算关键结果（样本量、OR、AUC、中介 ACME/PM），与论文表格逐位对比。目的不是验证脚本（脚本已验证过），而是抓**模型定义错配**这类隐蔽硬伤——本会话实例：①论文 Table 2 的 P 系列 DII OR（1.056/1.045）实为 FLI 定义队列的结果，正文却声称 CAP 队列（n=4,275），CAP 重算应为 1.048/1.041——表格与样本定义错配；②论文 Table 4 的 GLM7 OR（25.69/6.63）来自**漏掉 age 协变量的模型**，与正文\"Model 3 全调整\"定义矛盾，含 age 全调整为 33.0/6.78；③方法节声称\"accounted for survey design\"但主模型全是未加权 glm（survey 包仅用于 Table 1 描述）；④摘要称 \"adults aged ≥20 years\"但分析样本含 12-19 岁个体（18%）。审稿 subagent 应：读表时同时读正文模型定义句 → 独立重算关键模型 → 检查 (a) 表格数字来自哪个队列/模型 (b) 加权声明与实现 (c) 年龄/纳排表述与实际样本
- **表格 XML 结构解析**：docx 表格用 python-docx + lxml 检查 vMerge 合并单元格——本会话发现 Table 4 的 P interaction 列数值整体错位一行、表头重复两行；Table 6 的 8 个 leave-one-out 变异名堆叠在一个合并单元格而 OR 分散 8 行无法对应。审稿人必抓
- **文档嵌入图检查**：docx 内嵌图可能是旧版（文件更新了但 docx 未重新生成）——对比内嵌图时间戳与最新修复版；正文 Figure 编号 vs 图题 vs 图表目录文件名三方一致
- **TRIPOD 合规**（预测模型论文）：样本量/EPV、缺失数据处理、验证方法、区分度+校准度、模型公式可复现性（含截距）
- **标题页计数与实况**：Figures/Tables/References 声明数 vs 实际；词数声明 vs 实测（摘要 257 vs 宣称 289 这类）
- **残留检查**：占位符（[Author]/[date]/[Funding agency]）、候选标题残留、重复词（"mainly mainly"）、全角标点、Abbreviations 表只收实际出现的缩写
- 输出：完整问题清单（高/中/低），**只审计不修改**，保存到 `06_审稿与修改/投稿前审计/`

### 第 4 步：投稿格式元素补齐（用户核心要求："写作规范要对标已发表论文"）
用户会拿成品与**已发表论文原文**（如 `先复现GLM7相关论文2/01_原始论文/GLM7_paper2.pdf`）逐项比对，必须补齐这些期刊格式元素（详见 `references/journal-submission-format.md`）：
- 标题页：作者列表+单位上标、Corresponding author（姓名/单位/邮箱/电话占位）
- **ARTICLE INFO 框**：Article history（Received/Revised/Accepted/Available online）
- 结构化摘要（Background/Methods/Results/Conclusion）+ Keywords
- **CRediT** Author Contributions（13 项角色各配 [Author] 占位）
- Declaration of interest / Funding / Data availability / Ethics approval（含外部队列如 CHARLS 的伦理批准号）
- Abbreviations 缩写表（只收正文实际出现的缩写）
- 参考文献 Vancouver 格式：**按正文首现顺序编号**，subagent 重排 refs 后必须重新核对正文引用（常见错误：编号 15 提前出现、正文 (7)(8,9)(12) 与文献表错位）
- 图题编号 = 正文引用顺序；删除候选标题残留（"Recommended title (candidate 1 of 3)" 等）

### 投稿包完整清单（对标 `新的CLD-AIP/文稿！/投稿MDPI（Nutrients）的文件汇总`）
论文定稿后生成完整投稿包（docx + LibreOffice 转 pdf 双份，不确定信息一律 [占位符] 不编造），详见 `references/submission-package.md`：
- **Cover letter**（致编辑+核心发现+期刊契合度+原创/一稿多投/作者同意声明）
- **Highlights**（3-5 条，每条 ≤85 字符，用真实数值；MDPI/Elsevier 需要）
- **Title page**（独立标题页：题目/作者/单位/通讯/Running title/字数-表-图-文献统计）
- **STROBE checklist**（观察性研究）或 **TRIPOD checklist**（预测模型，27 条标准逐条标注论文位置，20 完整/4 部分/2 NA/1 需补是常见分布）
- **Plain English summary**（BMC 系必需，100-150 词通俗摘要）
- **Supplementary materials 清单**（建议新增项注明数据来源，不编造）
- **Graphical Abstract**（jpg + 设计说明 docx，可直接粘贴投稿系统）
- **Figures.zip**（全部图 SVG+PDF+PNG 打包，仿已发表论文投稿包）
- 缺项检查表（期刊必需声明逐项核对：BMC 用 "Competing interests" 不是 Elsevier 的 "Declaration of interest"；缺 Acknowledgments 段就给占位文本）

### 图表硬性要求（用户偏好，默认执行）
- **每张图必须 SVG + PDF + PNG 三格式**（SVG/PDF 可编辑矢量，PNG 300dpi）
- 学术风（Lancet/Nature）：白底、无网格（theme_classic）、Arial/Helvetica、图例底部、**字号≥12pt（用户明确嫌小过）**、黑色轴线、标题 14pt bold
- **配色只用 Lancet 五色**：红 #ED0000、蓝 #00468B、绿 #0099B4、橙 #ED7D31、灰 #7F7F7F（禁用 ggplot 默认彩色）
- R 生成：ggsave(device="svg"|"pdf"|"png")，cairo_pdf/svglite 保证 Unicode 安全；agg_png 渲染 300dpi
- 流程图必须 CONSORT 规范布局（T 形分叉、框内文字居中、侧排 Excluded 框），**不要手工硬编码散点坐标**（这是"图难看"的主因之一）
- 投稿包另需：Cover letter（docx+pdf，致编辑+核心发现+期刊契合度+原创声明）、Graphical Abstract（matplotlib 学术风 JPG，暴露→机制→结局+核心数值）
- 具体修复模式目录见 `references/figures-lancet-fixes.md`

## 常见陷阱（已踩坑记录）—— 索引

> 完整内容见 `references/common-pitfalls.md`（含触发条件与修复配方）。
> 遇到对应症状时**先读该文件**，不要凭记忆处理。
>
> 投稿流程类见 `references/frontiers-submission-and-post-submission-recovery.md`
> （Scope statement 写法；联系 **Editorial Office** 而非 Support Team；交付夹只留必需件 + 重生成 PDF；
> **已提交后才发现缺陷的补救协议**含给编辑部的邮件模板；投稿前必跑的 8 条规范清单）。

- 组学 Atlas 稿件专项（跨队列公共组学 v08→v09 实例：GPT6 第一性原理评审 → 先 rerun 后改文）

- **图表/补充图表编号未按首次提及顺序（v22 已提交后才被用户发现·最严重）**
## 校准/运输类统计陷阱（v8→v9 实测：审稿人点名后必须自查）
68. **校准斜率必须报 LP 尺度系数，而不是 exp(系数)**：把 `coxph(Surv~lp)` 的系数取指数（0.963→报成"slope 2.62"）会制造一个与十分位校准表**表面矛盾**的假问题——审稿人会用分位表（明明贴对角线）质问你。斜率理想值=1 是在 **linear predictor 尺度**；exp 版在完美校准时≈2.72，"怎么不是 1"本身就是穿帮信号。报告 `slope=0.96 (95%CI 0.92–1.00)` 并同时给十分位表，两证据才自洽。
69. **不同结局的跨队列"外部验证"不是真外部验证（v7 死穴）**：CHARLS 报新发 CVD、NHANES 报全因死亡，再拿一队列模型对另一队列做 C/校准，最多是"线性预测值对另一结局的排序能力"；审稿人会逐词打 external validation / transportable / cross-country calibration。修法（方案A）：两队列**统一主结局**（如全因死亡），CVD/CVD 死亡降为各队列内次要结局且**禁止跨结局校准**；标题改写为 "…all-cause mortality risk prediction and the limited incremental value of eGDR…"。
70. **运输模型只用两队列都能一一对应的共同变量**：CHARLS 没有可映射美国 race 的变量，把全中国人指成某个 NHANES race 类别临床不成立。race/教育/城乡等队列特异变量只进各自队列内扩展/敏感模型；运输模型用同一组共同变量（age/sex/smoking/BMI/TC/HDL/SBP/diabetes ± 组分 ± eGDR）。判别指标口径统一：内部 Harrell C 与外部时点 C 并列给出并注明定义，别拿不同指标互比还宣称"外部更高"。
71. **保护性 HR 的 E-value 用上限（最接近 null 的界）**：`v=1/HR`；`E = v + sqrt(v*(v-1))`。点估 0.855→E≈1.61，CI 上界 0.943→E≈1.31；用下限（0.775→2.13 一类）会被审稿人点名算错。S1 表的每个敏感性行都要分别给点估计 E 与置信界 E。
72. **"图与正文不一致"= 图是旧分析产物（v8 六张图全带 v7 数值）**：图内 CHARLS 7,817/940 死而正文已是 7,745/919。规则：**主结果每次变化，全部图必须从最终结果对象（rds/表）同一次重生成**，图注/图内数值同步；并跨目录（图表/、Figures/、TIFF/）删除旧名旧图（本会话曾留 Fig6_subgroup 旧图与新 5 图共存）。只改图注去适配旧图 = 审稿人一眼识破的偷懒。
73. **docx↔md 往返工程坑（表格"名称数值罗列"的根因）**：pandoc md→docx→gfm 会转义 `\[ \* \<`、References 多条目并成一段；**若用"按空行压平段落"归一化，pipe 表格行也会被并成一行 → 源 md 表格被破坏 → 新 docx 无原生表格（doc.tables==0）**，读者看到的就是"名称+数值简单罗列"。修法：压平时**以 `|` 开头的表格行必须保留为独立行**，只合并散文软换行；生成后先验 `doc.tables` 数量再谈样式。三线表：python-docx 在 tblPr 设 tblBorders（top/bottom single sz=12，left/right/insideV/insideH none，先删旧 tblBorders 与 Table Grid 样式）+ 表头行/末行 tcBorders bottom。
74. **正文引用"按首现重排"的健壮实现**：解析 `[n]`/`[n–m]`（**en-dash \u2013** 要显式处理），只认 1..N 内的编号（基金号 `[2023]` 之类方括号不是引用）；按全文（正文+表格+图注）首次出现顺序编号 → 重建 References 表 → 替换全部引用 token（连续号折叠为区间）→ 断言正文引用集合==1..N 全覆盖、无孤儿无悬空；**顺带删除零引用旧条目**（本会话 30 条 → 22 条全被引）。绝不手工改编号。
75. **R 小坑组（本会话全部实测）**：①公式在调用处构建再传 helper `coxph(f, data=d)` 会因公式环境找不到 'd' → 顶层直接拟合或 helper 内部重建公式；②`ns()` 需显式 `library(splines)`；③rms::Predict 在加权 cph+factor 组合下报 "Values in educf not in..." → 绕开：coxph+ns+vcov 手算 95%CI（基函数差 X，var=X V X'）；④riskRegression/Score 依赖新版 prodlim，装不上时手写 Uno 时点 AUC；⑤删失重时 IPCW 权重爆炸（G(9) 极小→DCA 数值荒谬），改用"完整随访 9 年子集"朴素 DCA。
76. **AI 评审流程的"文件输入变体"：先读评审 docx → 分栏 → 逐条给出"采纳/修复证据"，再动稿件**；全文重构（新写而非修补）是消除"新旧拼接/正文损坏（eGDR added littl# Discussion）"的唯一可靠手段——不要在同一字符串上叠补丁，直接整体重建 md 再统一重编号。完整工作流细节见 `references/mortality-transport-validation-and-docx-engineering.md`

## 验证清单
- [ ] 校准斜率报告 LP 尺度系数（0.96 这类，不是 exp 后的 2.6x）；与十分位表自洽
- [ ] 保护性 HR 的 E-value 置信界用最接近 null 的上限（v+sqrt(v(v-1))，v=1/HR），点估计与置信界分列
- [ ] 跨库"外部验证"确认为**同结局同时间窗**；队列特异变量（race/教育）不在运输模型里；判别指标口径统一（内部 Harrell C vs 外部时点 C 并列注明）
- [ ] 主结果变化后全部图从最终 rds/表重生成，图注数值同步，旧图文件跨目录清干净（图表/ Figures/ TIFF/）
- [ ] md→docx 往返后 `doc.tables`>0（表格行未被压平合并）；三线表样式生效
- [ ] 全文重构版无新旧拼接残留（扫旧结局关键词/旧 C 值/正文夹 heading）；引用 1..N 全覆盖重排
- [ ] 审稿意见保存为 md 文件
- [ ] P0 数据完整性问题全部修复并重新计算
- [ ] 新增数值与 rds 数据一致（脚本可复现）
- [ ] 参考文献编号 = 正文首现顺序
- [ ] 参考文献 1..N 全部被正文引用、零孤儿（替换文献表后必须重映射正文引用并做全量引用集合校验）
- [ ] 图表 SVG/PDF/PNG 三格式齐全
- [ ] 图表文件名与论文图编号完全对齐（从 docx 提取图题清单核对，拆分图用顺序编号并同步文件/图内标题/正文引用/标题页计数）
- [ ] 图表布局无大片空白：vision 模型不可靠时用 scripts/pixel_blank_check.py 像素密度验证（留白合计<15%、内容覆盖≥85%）
- [ ] CONSORT 流程图箭头终点与排除文字/小框对齐：解析 SVG 的 stroke-dasharray line 终点 y 与 text y 对比（±1px），排除原因用虚线小框包裹而非裸文字；列间注释不放其它列方框中央
- [ ] 审稿 subagent 的 `_*.py/_*.txt` 调试残留已从桌面/工作目录清理或归档（防止用户当垃圾删除）
- [ ] 外部队列（CHARLS 等）数据列先查 class()，haven_labelled 须转 numeric 后再进 table()/glm()
- [ ] 交付文件夹 7 子目录齐全
- [ ] 投稿格式元素齐全（ARTICLE INFO/CRediT/Declarations/Abbreviations）
- [ ] Cover letter 署名邮箱经用户确认
- [ ] 隐私检查（GitHub 发布内容无个人信息）
- [ ] 终检脚本遍历 doc.tables（Title page 统计表/STROBE 清单都在表格里，段落扫描会误报缺失）
- [ ] 正文 Figure 1..N 均有引用 + References 前有完整 Figure legends（图题加粗标题）
- [ ] 流行病学关联论文自查剂量反应证据完整（RCS 曲线 + 四分位趋势图 + 对应 Results 小节；插入小节的所有 OR/CI 来自 R 重算，禁止手填印象值）
- [ ] 增量 AUC 对比图用点图+截断轴（AUC 值域窄时柱状图看不出差异），颜色按语义 3 类而非 6 类
- [ ] 标题页 "Figures: N" 计数与实际图文件/图题数三方一致
- [ ] 粗删除（句窗/关键词圈删）后 grep 邻近必需句与引用编号锚确认无伤（85）
- [ ] 一次性图修复已折入主图脚本或整图重跑后复核最终 PNG/TIFF 与 docx 内嵌 media 时间戳（86）
- [ ] 运输验证补 bootstrap ΔC 95%CI 时注明指标变体（rank-concordance vs IPCW-Uno 不可互比）；指数与糖代谢定义重叠时补 FPG/IFG 敏感性；NHANES 后期周期补 5 年主时点全套（C5/校准/O:E/LP 斜率）（87–89）
- [ ] 代码包入 GitHub 用 gh repo create --source . --push，Declarations 回填 URL 并附匿名镜像句（90）
- [ ] md 归一化/模糊锚只折叠行内空白不碰换行；若 md 已毁用上一份好 docx pandoc→gfm 恢复，并把 `<img src="media/...">` 正则换回 `![Figure N](abs.png)` 再重建 docx；往返后先 grep tmp 实际文本再写锚（91）
- [ ] 绝对风险公式已做中心化核查（手工公式 vs survfit(newdata) maxdiff≈0）并在 S 表写明 lp 以拟合样本均值中心化（92）
- [ ] 5y/9y 表述不含"人人可达"式错误：分周期表 + 受限周期（9y≤2010、5y≤2014）重报 C/校准（93）
- [ ] 缺失率分母=预先队列、样本称 analytic subsamples、补纳入vs排除比较；正文/Table5/未调整行 CI 全对齐单一拟合来源（94）
- [ ] OCC/Efron 乐观校正的加权 coxph 坑：权重做成数据列；测试集用固定子集+B≤100 防 Windows R 段错误；报告 app/opt/corr 三值（95）
- [ ] 再校准更新用 5 折 CV 做内部验证（held-out 折报 mean pred vs KM + Brier），不说\"表观改善=验证成功\"（96）
- [ ] eGDR 增量问题用外部同人群配对 ΔC bootstrap（Δ(M2−M0)/Δ(M1−M0)/Δ(M2−M1) 三对 CI）；\"1 参数固定组合追平 3 参数自由成分\"叙事；图与 S-table 同 CSV（97）
- [ ] gh 改仓库可见性：`gh repo edit <repo> --visibility private --accept-visibility-change-consequences`（90 扩展）


### 逐轮累积的验证项（已合并去重）

- [ ] 论文 supplementary 声明清单（"Supplementary material. Table S1..SN" 段）为 S 表权威源：解析最大 S 号，逐一断言 Supplementary docx 存在对应表格标题（缺的按 RDS 补插到 Figure S1 锚前）；Title page/STROBE/封面三处 "S1–S6" 计数串已同步；新 S 表在正文有一处引用
- [ ] 最终 docx（作者回填/嵌图/补表之后）重跑引用首现序列断言 1..N 严格递增 + 无孤儿 + 无悬空——每版独立验，不因上版修过而跳过
- [ ] N3/任何时段的权重-时段措辞与数据一致（table(session, weight>0) 实证后落笔；晨间权重不写 morning/evening；长空腹极值归因中性化）
- [ ] 作者块回填后三处（主稿作者行+单位/Title page/CL 落款）序号†/*/邮箱断言一致；CRediT/致谢无占位；全包 CJK 扫描归零
- [ ] M3 改名类全文替换覆盖摘要段（grep 旧措辞含 Background/Results 首行）
- [ ] 删"QA 痕迹/Data cross-check"段前打印整段文本人工判定：内部文件名（anchors_*.tsv/extract_log_*.txt/_v12 后缀）才删，纯正文交叉引用段保留；误删后用相邻表标题做锚 addprevious 恢复（v12 轮 6）
- [ ] docx 孤儿媒体已清理：`doc.part.rels` image 关系数 == 正文 a:blip 引用数（zipfile 重写 rels + 删 word/media 未引用图），重开后断言段落/表/图数不变（v12 轮 7）
- [ ] 摘要每次编辑后按"不含标签"口径回测并回填 Title page 词数（doc.tables 与段落都查）；计数逐段剥离 Background:/Methods:/Results:/Conclusions: 标签再合计（v12 轮 8）
- [ ] "两期变量定义不同"类审稿主张已下载两期官方 XPT 验证（列名 vs 语义分两层），派生列名与官方列逐人比对后再裁决改文/重建
- [ ] 交互检验与声称的模型框架匹配：M4 反转的跨期异质性用 M4 框架合并模型（+age+BMI）另测，并与 M1–M3 框架并列标注；队内反转 vs 合并框架不反转两设定都写
- [ ] 组分分解分析已做（GLM7−log10(age)−log10(BMI)=metab，模型含 rcs(age)+BMI 多形式）并据此定位反转来源
- [ ] 判别分析协变量与关联分析同源（重建变量并入判别文件后重跑 base B）
- [ ] CI 统一 exp(b±t₀.₉₇₅,ddf×se) 与 Wald F 配对，边缘结果按 t 分布如实报
- [ ] "fully adjusted" 已全文替换为 sociodemographic and lifestyle-adjusted（复合指数含 age/BMI 组分时）
- [ ] 每张嵌入图的图注声称映射与实际 aes/facet 映射逐字核对一致；面板标题短名、完整协变量放图注
- [ ] delegate 半成品逐项续跑并回读断言；收尾前整份 todo 与真实状态核对（用户会看 Tasks 面板）
- [ ] 全画布坐标图（add_axes([0,0,1,1])）：图例/文本列总宽不超 xlim（扩 xlim 留右缘更干净）；挪列后重跑内置 check_overlap=0；图内模型标签与正文改名同步（grep 图脚本旧词）（v12 轮 9）
- [ ] 图右缘无 glyph 触边：PIL 深色像素行聚类确认非整行满宽、四角白、非白占比~4%；修复后重跑边界检查出现 >0px 边距；重嵌 docx 后重开断言图序图数（v12 轮 10）
- [ ] 正文/投稿包声称的每个文件（Response to Reviewers、Supplementary Materials、Figures.zip）已在盘（os.path.exists 断言）；声称"响应审稿人"就生成或删句（H1/H2）
- [ ] 投稿包所有 docx 无 CJK 残留；双语基金只取英文段，中文"原文"整段删除不留字符垃圾（H3）
- [ ] 首投 Cover letter = original research article + prior independent methodological review，不点名内部 AI 代号（H1/L3）
- [ ] meta/合并模型期别 OR 若与主结果口径不同（如 N3 2.335 vs 2.130）已显式标注不可直接比较（M2）
- [ ] 表内四分类/组合行算术闭合；口径差额（如 dx 缺失者全 sx+）已在表注写明（M3）
- [ ] R 版本串从 sessionInfo 实读回填（M4）；40 条文献零悬空（每 ref 至少一处正文引用）（M1）
- [ ] 单条引用增删后重跑 Vancouver 首现序列断言 1..N 严格递增（本轮 [38] 提前断裂实例）
- [ ] 每个对照/派生指数已 grep 实际计算行并与原始文献公式逐项核对（含结构：BMI 乘数位置、HDL 分母）；分布均值/SD/切点对照文献典型值；与相关指数相关性合理（127）
- [ ] 修正任一对照指数后，其依赖的 Table/图/配对比较/讨论措辞/Cover letter 全部重跑刷新，不残留旧值
- [ ] 删\"占位符\"前先看整段文本，占位符与必需内容同段时只清片段不删段；误删后按已知内容在 References 前恢复并回读验证（128）
- [ ] 图重画后已用 a:blip XML 定位替换 docx 内嵌图（删 w:drawing + add_picture），并删除 \"[FigN_filename]\" 占位段后回读断言图数不变（129）
- [ ] 期刊结构化摘要已核对限长并按轮压缩（每轮读数词），Title page 统计表词数同步（在 doc.tables 里，非段落）（130）
- [ ] Python 构建脚本常量未被同名二次赋值（subagent 补丁后 grep 常量名出现次数）；「not str/not dict」报错先查尾部同名重定义（125）
- [ ] 补充材料 docx 回读断言：doc.tables==声明表数、inline_shapes==图数、表题/图题段落 1..N 齐全、Title page 声明清单与实产一致（126）
- [ ] 中途插表后 `^## Table` 序列 1..N 无重复（先插后只 shift 旧标题，120）
- [ ] 共享 stage-3 定义的替代分期规则：stage3 人数/0–2 限制集/HR 构造性一致；计数列和=n（或写显式子集 n），不括号硬凑（121）
- [ ] 插入/替换后 grep 插入点 ±120 字符无粘连残留（122）
- [ ] 新主要分析口径下 M-1/M0/M1/M2 全部有外/本/Δ（独立主表或表注），配对增量同口径可读（123）
- [ ] 补充材料 S1..SN 数值序重排且被引 S 号存在（124）
- [ ] 判别指标已按定义正名（cumulative/dynamic AUC / Uno's C / Harrell's C 三者不混标）且表题/方法给评估样本量（cases/controls）
- [ ] 每对"点估计+95%CI"符号同侧（配对 bootstrap 输出回读，禁止手打转录）
- [ ] Brier 评分人群定义写死（known 9y status + weights），删失敏感性与充分随访周期佐证已注明；IPCW-Graf 朴素实现若数值荒谬已弃用并如实记录
- [ ] AI-use statement 在匿名版中保留；每轮迭代后用最新 md 重生成 ANONYMIZED docx 并断言脱敏（107）
- [ ] 每轮评审后产出"意见→处置对照表"md/docx（内部质控，不随稿提交）
- [ ] 数值终检用全文件扫描（含 References 之后的 S 表/Table），只扫 body 会误报 ABSENT（116）
- [ ] Funding/项目号不带方括号书写，避免污染引文扫描器（117）
- [ ] censoring-robust 口径三件套：潜在随访充分周期主评估 + 全队列 restricted 次级（标评估样本占比与 cases/controls）+ IPCW 标注假设的敏感性；权重三层交代（118）
- [ ] 每对"点估计+CI"符号同侧回读后再跑 renumber 与双 docx 重建（119）

### ⚠️ 编号顺序硬规范（v22 事故后必跑，最容易被漏）

- **图表编号必须等于正文首次提及顺序**（Table / Table S / Figure / Figure S 四类分别断言）。
- 只查「引用完整性」不够——必须写**顺序性断言**（首次出现段落号递增）。
- 修正时先算 `old→new` 映射，用**哨兵字符两阶段替换**避免循环；并同步：正文引用、表/图**标题本身**、
  文末表块/图块**物理排列**、补充材料内部标题与排列、`Tables/` 文件名、`Figures/` 文件名。
- 范围引用分两种：**泛指全部**（`Tables S1–S13` → `Tables S1–S16`，不按映射）与**具体区间**（按映射后取升序）。
- **「遗留问题 0」只等于「我清单内的项过了」，不等于稿件无规范问题**——不得据此说「可以投稿」。
- 可运行脚本与完整流程见 `references/figure-legend-content-and-image-reembed-audit.md` §11。
- **排版合规（对标期刊模板）**：字体分**样式层/段落层/run 层**三级、表格字号要单独查（表格 run 不在
  `doc.paragraphs` 里）、段落间距按元素层级统一并**删除空段落（排除装图段落）**、三线表不能只看样式名。
  诊断脚本与验收断言见 `references/docx-typography-and-spacing-compliance.md`。
- ⚠️ 该文件 §6 另记一条元教训：**审计脚本自己会过时**（改了映射/编号后未同步检查器 → 假阳性），
  报 FAIL 时先验检查器再改交付物。
- **直接运行现成断言，别每次手写**：
  `python scripts/assert_numbering_order.py <Manuscript.docx> <Supplementary.docx>`
  （校验四类标题排列升序、引用编号有对应标题、并单列主稿引用顺序供人工判断；退出码非 0 即有 FAIL。
  收尾提示会明确写出"本脚本只覆盖编号顺序"，防止又拿它当"全文没问题"的证明。）

