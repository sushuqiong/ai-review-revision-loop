# 死亡率运输验证 + docx 工程（v7→v9 会话实录）

CKM/eGDR 双队列论文（CHARLS+NHANES，Cardiovascular Diabetology）迭代实录。外部 AI 审稿人（ChatGPT）在
v7/v8 给出的核心批评、对应重分析与全部可复现要点。

## 1. 科学故事重构：跨结局 → 同结局真外部验证（方案A）

v7 致命伤：CHARLS 建模"9 年新发 CVD"、NHANES 验证"9 年全因死亡"，反向再验——审稿人判定这不是 external
validation（基线风险/校准截距/斜率都绑定结局），最多是"线性预测值对另一结局的排序能力"。修复：

- 两队列主结局统一为**全因死亡**（CHARLS 需能从原始波次 Exit/Sample Info 构建死亡时间：`fu_death =
  ifelse(death_any, death_date, last_date) - 2011.5`；NHANES 用死亡文件随访月）。
- 新发 CVD（CHARLS）/CVD 死亡（NHANES，UCOD_LEADING∈{1,5}）降为**各队列内次要结局**，明写 "No
  cross-outcome calibration was performed"。
- 标题模板：`Cross-country transportability of all-cause mortality risk prediction and the limited
  incremental value of <index> in adults with CKM stages 0-3: <cohortA> and <cohortB>`。
- 模型阶梯 M-1(age+sex)/M0(+常规)/M1(+腰围/高血压/HbA1c 组分)/M2(+复合指数)，同时测"复合指数 vs 其原始
  组分"（M1≥M2 ⇒ 组合无增量）。
- 运输模型**只用共同变量**（本会话把 race/education 移出，仅留队列内敏感模型）；内部 Harrell C 与外部
  9 年时点 C(IPCW) 并列报告并注明口径，避免"拿不同指标互比"。

## 2. 两个统计误报（审稿人点名后必须自查）

**校准斜率**: `coxph(Surv(t,e) ~ lp)` 的**系数本身就是斜率**（理想 1）。把系数取指数（0.963→2.62）制造了
与十分位表矛盾的假象。本会话真值：CHARLS→NHANES slope=0.844(0.807–0.882)、反向 0.937(0.878–0.995)。
十分位表（weighted KM @9y 观测 vs 预测）与斜率同报才自洽。

**E-value（保护性 HR）**: v=1/HR；置信界取最接近 null 的上限。
`E = v + sqrt(v*(v-1))`。例：HR 0.855(0.775–0.943) → 点估 v=1.170 → E=1.61；上界 0.943 → v=1.060 → E=1.31。
使用下限（0.775→E≈2.13）是审稿人点名的常见错。每个敏感性行分别给点估 E 与置信界 E。

## 3. 真·同结局运输结果（诚实结论模板）

- 内部 Harrell C：CHARLS M-1 .775 → M0 .785 → M1 .787 → M2 .786；NHANES .768/.783/.786/.785（eGDR/组分
  增量 ≤0.002 → "no evidence of material improvement"）。
- 外部 9y 时点 C：CHARLS-M2→NHANES 0.742；NHANES-M2→CHARLS 0.779。
- 校准：前向 slope .844 + CITL 过报（mean pred 21.8% vs obs 11.3%）；反向 slope .937 + CITL 贴合（13.1% vs
  13.1%）→ 结论 "**Discrimination transported, absolute risk did not; local recalibration necessary**"。
- 交互：age<60 CHARLS HR 0.75 vs ≥60 0.89 (P-int .09)；NHANES 0.72/0.88 (P-int .001)。prediabetes 两库 NS
  (P≥.29)——撤销旧版"带内衰减"解读（那是子集分层误读，正式交互检验才能下结论）。

## 4. docx/md 工程：往返破坏与"按首现重排"

- **表格丢失根因**：把 pandoc gfm 回源 md 做"软换行压平"时，若把 `|` 表格行也并成一行，md 表格被破坏；
  pandoc 再转 docx 得到 `doc.tables == 0`（用户看到的就是"名称数值简单罗列"）。修复：压平只合并非表格散文
  段落（表格行 `ls.startswith("|")` 必须保留独立行）；回源后先验 `doc.tables>0` 再继续。
- pandoc 转义：回源 gfm 会转义 `\[`、`\*`、`\<`，处理前统一反转义（`replace("\\[","[").replace("\\<","<")`）。
- 三线表 docx：python-docx 对每个表 tblPr 设 `tblBorders`（top/bottom single sz=12；left/right/insideH/
  insideV none；先删旧 tblBorders 与 Table Grid 样式），再表头行与末行每格 `tcBorders bottom single sz=6/12`。
  可复用：academic 技能 `docx_three_line_tables.py`。
- 引用重排算法：正则 `\[((?:\d+)(?:[,\u2013-](?:\d+)(?:\u2013\d+)?)*)\]`（en-dash 区间）；
  只把 1..N 内数字当引用（基金号 `[2023]` 排除）；全文件（含表格/图注）按首现顺序编号；重建 References 表
  并替换所有 token（连续折叠 `[2-5]`）；跑完断言引用集合==1..N、无孤儿；顺带删除零引用旧条目。本会话
  renumber_clean.py 一把从 30 条清到 22 条全被引。

## 5. R 小坑（本会话实测）

- `coxph` 公式在调用处构建再传入 helper（`data=d`）→ "找不到对象 dat"。顶层直接拟合，或 helper 内重建公式。
- `ns()` 需要显式 `library(splines)`。
- 加权 cph + factor + rms::Predict 报 "Values in educf not in ..." → 绕开用 coxph+ns+vcov 手算 RCS CI：
  `X = predict(nsk,grid) - predict(nsk,ref); logHR=X%*%b[1:3]; se=sqrt(rowSums((X%*%V[1:3,1:3])*X))`。
- riskRegression::Score 依赖新版 prodlim，装不上 → 手写 Uno 时点 AUC（case=event≤9, control=fu≥9,
  IPCW=1/G(t)）。
- 删失重时 IPCW 权重爆炸（G(9) 极小 → DCA NB 荒谬如 -900）→ 用"完整随访 9 年子集"朴素 DCA。
- `concordance(m)` 返回命名字符串需 unname；`c(HR=exp(b),...)` 命名被 coef 名污染成 `HR.e` → unname()。

## 6. 图"仍是旧版"的系统性修复

审稿人对照图内数字与正文：v8 六张图全带 v7 数值（7,817/940 死 vs 7,745/919）。规则：
1. 主结果一变，所有图从最终 rds/结果对象重画，图注/图内标注同步；2. 删除全部旧图文件（图表/、Figures/、
   TIFF/ 常残留旧名旧图如 Fig6_subgroup）；3. 5 图版式：流程图(真实样本链)、森林(主+次要结局每SD HR+CI)、
   双向校准(十分位点±95%CI+identity+LP斜率+CITL)、RCS(双库 CI 带)、互补亚组(按层真实拟合+交互 P)。
4. 图嵌入 docx：md 里 `![Figure N](C:/abs/path.png)` 绝对路径，pandoc --standalone 嵌入（media 计数=图数）。

## 7. 交付复盘节奏

- 每轮：读评审 docx → 给"采纳/驳回+证据"分栏 → 做分析 → 全文（新写而非修补）→ 重编号 → 图重生成 →
  pandoc+三线表 → 项目根+投稿包双份同步 → 更新 `00_状态与明天继续.md`。
- 用户口头禅："？"= 继续干活不要停；先执行后汇报；作者/单位元数据一律占位符由用户后补。
