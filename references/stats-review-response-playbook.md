# 审稿人统计意见 → 快速补做清单（临床预测模型/外部验证类稿件）

来源：GPT6 与腾讯 Hy4 对 CHARLS+NHANES 运输性稿件的两轮意见，逐条补做并已验证可行。审稿人对"预测模型 + 增量价值"类稿件的意见高度模板化，本清单可直接按序执行。

## 最常见的 8 条意见与实现方式

| 审稿意见 | 实现（R） | 交付形态 |
|---|---|---|
| "无增量价值"只靠 ΔC，ΔC 不敏感 | ① 嵌套 **似然比检验**（M1 vs M2 = 固定权重复合 vs 自由分量；M0 vs M1）②**IDI + 连续 NRI**（限定结局已知人群：病例/对照的预测概率差） | 正文一句 + 补充表 |
| 固定复合指标 vs 自由分量 | M2 是 M1 的**固定系数线性约束**（eGDR = a − b·腰围 − c·高血压 − d·HbA1c），故 LR 检验 df = 自由参数数 − 1。结论措辞：复合"捕获了大部分"而非"等效"（P 显著时）| 补充表 |
| 提出"临床意义不确定"却无临床效用 | **决策曲线分析**（净获益 NB = TP/n − FP/n·pt/(1−pt)），阈值 5–30% | 补充表（差 ≤±0.0013 时写"无净获益差异"）|
| 完整病例排除率高 → 选择偏倚 | **逆概率纳入权重 IPW**：对全合格样本 logistic 回归 P(入组 ~ 年龄+性别+教育)，`w = 1/p`（截断 0.05）后再拟合主模型；比多重插补便宜得多，用于敏感性足够 | 补充表（HR 前后对比）|
| 内部(apparent) vs 外部比较不公平 | **9 年 AUC 的 bootstrap 乐观校正**（apparent − mean(apparent_boot − test_on_original)）；每个模型都要做，不能只做 M2 | 表脚注 + 补充表 |
| 时代/日历不对齐 | **日历对齐敏感性**：取与主队列重叠年份的目标队列周期（如 NHANES 2011–2014）做 5 年分析 | 补充表 |
| 行政删失导致晚期入组无 9 年随访 | 设**主评估窗**＝目标队列中"全部具有 ≥9 年潜在随访"的周期（如 NHANES 1999–2010）；在该窗内 restricted 估计无偏；全队列 restricted 与 **IPCW（Uno AUC / Graf Brier，权重截断 0.05）**并列作敏感性，并声明 IPCW 对截断与删失独立假设敏感 | 主表（窗矩阵）+ 补充表 |
| local 模型用全队列拟合、子集评价（表观污染） | **评价窗内重新拟合 local 模型**；否则 external−local 差混入过拟合 | 主表更新 |

## 措辞纪律（审稿人反复盯的点）
- "no evidence of effect modification" ≠ "confirmed the absence"；不显著写"未发现明确证据"。
- 小差异 + CI 未跨 0 ≠ 等效；无等效界值就不写 "equivalent/near-equivalent"，只报差值与 CI。
- 平均校准改善 ≠ 整体预测误差改善：Brier 的 Δ 方向要分迁移方向报告，正向改善、反向中性/略差就要如实分开写。
- 校正 = 表观(in-sample) 与 折外(CV/bootstrap) 必须分开标注；阴性结果（反向再校准无获益）是资产，保留并强调。
- 过报机制要分解：分别用来源模型 LP + 目标队列基线风险（case-mix 与 baseline hazard 拆分），把"校准不转运"从描述升级为机制（本稿约 70% 来自基线风险）。
- 剂量反应：报**结点位置（10/50/90 百分位）+ 非线性 P**，不能只凭图说"近似线性"。

## R 实操坑（本会话实际阻塞过）
- `%<>%` 需要 `library(magrittr)`；`ns()` 需要 `library(splines)`（只挂 survival 会报"没有 ns 这个函数"）。
- **加权 coxph 在函数内用变量名取权重**常报"找不到对象 w"：把权重先写成 data 的列（`d$WW <- w`），再 `weights = WW`。
- `summary(survfit(...), times = 向量, extend = TRUE)` 会报 `if (!extend)` 长度错误；改用 KM 的 `approx(G$time, G$surv, xout = ...)` 取 G(t)。
- `concordance(fit, newdata = ..., weights = ...)` 不接受该 weights 参数 → 去掉 weights 参数或改自算。
- 加权 `concordance`/大对象 bootstrap 在 21k 样本上偶发 **segfault**：降低 B、改用秩一致性自算（`findInterval` 版 O(n log n)），或把 `Rscript -e` 长内联脚本改写成 `.R` 文件运行（长内联本身也易崩）。
- `complete.cases` 的变量清单决定人群：补一个变量会静默缩小 n，必须同步核对所有 n 与事件数（本会话曾因加 `gly_status` 过滤使分期人数少 74 人）。
- 数据列名要先探：`grep("edu|psu|stra", names(d), value=TRUE)` 再写模型，避免整段脚本跑 5 分钟后才报"找不到对象 edu11"。
- 嵌套 LR 检验在 NHANES 加权偏似然下 chi-square 量级会失真（权重放大 loglik）→ 只报 P，注明"weighted statistics are not design-based"。
