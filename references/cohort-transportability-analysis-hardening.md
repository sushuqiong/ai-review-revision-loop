# 双库迁移 / 外部验证类稿件的审稿人驱动硬化清单

适用：CHARLS+NHANES（或任意两个公共队列）做"同一结局、同变量、双向外部验证"的论文（目标刊 Cardiovascular Diabetology 这类）。
来源：多轮对抗性评审（GPT6 + 腾讯Hy4）反复命中的意见 + 本会话逐条实测的解法。

## 0. 先定"一个主估计量"，再让全文同源
- 选一个并**首次出现处定义**：如 `9-year restricted concordance (known-status population)`（病例=9年内死亡、对照=≥9年存活）。
- Harrell's C 只作次要指标；IPCW（Uno/Graf）因对权重截断敏感 → 只作探索性敏感性。
- **删失稳健主窗**：把"行政随访必然完整"的周期（如 NHANES 1999–2010，所有入组者到随访截止仍有 ≥9 年潜在随访）设为主敏感性分析；该窗内 restricted 估计无偏，无需删失权重。
- 三口径并列时明确各自定义，**不要合并成"稳健"一句话**。

## 1. 复杂抽样不确定性（评审最爱打）
- NHANES 有 `psu`、`stra` 字段 → **PSU within stratum 有放回重抽**（B=300 足够稳定）后重算指标，得到 CI 与配对差 CI。
- 只说"个体 bootstrap"会被判"CI 偏窄"；个体重抽样只能在文中标注为保守近似。
- CHARLS 侧：Harmonized 文件里有抽样权重（`wgt11`；另有 `r1wtresp...`）；做一次加权复算即可结案（本会话：加权 HR 0.856 vs 未加权 0.855，加权一致性 0.799 vs 0.804）。
- 若某库确实无权重：**把目标人群写成 analytic sample**，不要写 population-representative。

## 2. 完整病例选择偏倚：MI + IPW 都要做，且要防"假 MI"
- 本机 `mice`、`metafor`、`survey` 均可用；m=20、maxit=5 足够。
- **关键坑**：MI 必须覆盖"全部合格者"。若结局变量是从分析子集（完整病例）里 join 进来的，MI 会**静默退化成完整病例分析**——症状是"插补后平均样本量 = 完整病例数"（本会话第一版即如此：mean n=7,745 = complete-case n）。正确做法：从 Harmonized CHARLS 原始文件的 `died20` / `fu_years`（或 `fu_years9`）取全集结局。
- IPW：`glm(included ~ age + sex + education)` on eligible；报告权重分位数与截尾（本会话：中位1.77、95th 2.30、max 6.57，无极端权重）；给出加权 HR。
- 两库都做才对称；某库做不了就在 Limitations 明说，不要只做一侧还宣称"稳健"。

## 3. 分期/入组限制的选择性（CKM 0–3 类）
- 若能拿到**限制前**的原始数据，就做"放开限制"敏感性：本会话 CHARLS 放开 CKM 0–3（≥45岁、无CVD、eGDR可得，n=6,597）→ HR 0.836 (0.701–0.997)，与限定队列 0.855 一致。
- 若分析文件本身是按限制构建的、重建需要回到 10 万级原始数据 → 如实写成 limitation，**不要**用"已限定目标人群"含糊过去。

## 4. 跨 20 年测量异质性（评委不信"局限声明"）
- **逐周期估计 + 随机效应 meta**：逐周期应用固定源模型算指标，逐周期拟合 HR，`metafor::rma(yi=log(HR), sei=...)` → 报告 pooled HR、I²、Q 的 P。
- 本会话：逐周期 AUC 0.770–0.813，pooled HR 0.856 (0.796–0.919)，**I²=11.2%，Q P=0.402** → 把"异质性"从辩解变成量化证据。
- 再配早/晚周期分层的"平均预测 vs 观测"（本会话 1999–2004 与 2005–2010 均过报约 10pp）。

## 5. 比例风险违背
- 同时给 `cox.zph`（残差检验）与 `eGDR × log(t)` 交互；说明二者备择假设不同。
- 更硬的做法：**分段 HR**（0–3 / 3–6 / 6–9 年；按 at-risk 限制 + 区间末端删失）——本会话 NHANES 0.856/0.748/0.866，CHARLS 0.788/0.878/0.858。
- 固定 HR 一律描述为"平均效应/近似效应"。

## 6. 复合指标 vs 自由分量（全文最锋利的一刀）
- 把比较写成"**freely estimated components (M1) vs fixed-coefficient composite (M2)**"，不要写成"eGDR 无预后价值"。
- 必报：**嵌套 LR 检验**（2 自由度；本会话 CHARLS P=0.009）+ ΔBrier + 校准 + **决策曲线净获益**（本会话阈值 5–30% 差异 ≤±0.0013 → "no clinically meaningful net-benefit gain"）；IDI/cNRI 降为支持性（本会话 IDI +0.0097、cNRI +0.261 对 M0，而 M2 vs M1 为负）。
- 只有 ΔC/ΔAUC 时结论最脆：Δ 在基线 AUC 已 0.78+ 时必然趋近 0，评审会直接驳。

## 7. 绝对风险 vs 排序能力必须分开说
- 标题/摘要/讨论/结论分别写：**discrimination transportability**（可迁移）与 **absolute-risk transportability**（不可迁移，需本地再校准）。
- 过报**机制分解**（把"校准不转运"从描述变解释）：保留源模型线性预测值，替换为目标库基线风险 → 本会话 mean pred 22.7% → 换 NHANES 基线后 14.7% → 观测 11.3%，即约 70% 来自基线风险差异、30% 来自 case-mix。
- 内部参照不能只是 apparent：做 **bootstrap 乐观校正**（本会话 9年AUC 0.8035→0.8021；NHANES 窗口 0.8081→0.8085）与交叉验证再校准（Brier 折外）。
- 再校准收益要**分方向**说：本会话前向 Brier 改善（Δ−0.0044, CI −0.0060~−0.0027）、反向中性（+0.0002）；不要写"显著改善校准"。
- 校准命名分清：calibration intercept(log-hazard scale) / slope / O:E / mean risk difference，四者分列。

## 8. 报告与合规收尾
- 主表每个模型都给 95% CI **并给模型间配对差及 CI**（结论若依赖 Δ≤0.006 尤其必须）。
- 声明多重重比较的探索性；交互/非线性检验标注 hypothesis-generating。
- Ethics 要写具体批号（CHARLS IRB00001052-11015；NHANES NCHS ERB）+ 数据 URL 与访问日期；基金/作者未定时用占位符，且**不得残留真实基金号/单位/邮箱**。
- 图与表由同一份结果对象生成；**不要用 markdown 表格文本解析来画图**（本会话产出过 `NA (0.926-NA)` 的坏图）——计算对象直出，并在 `ggsave` 前 `stopifnot(!any(is.na(...)))`。
