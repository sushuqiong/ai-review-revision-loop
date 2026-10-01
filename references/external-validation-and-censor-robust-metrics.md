# 外部验证 / 删失稳健 / 增量价值：可对抗审查的统计工具箱

来源：CHARLS+NHANES 双库 eGDR-CKM 死亡风险迁移研究（v10→v16，Cardiovascular Diabetology 目标刊）。
两份 AI 评审（GPT6 守规范、腾讯 Hy4 攻方法学）反复追打的就是本文件这些点——每一项都做成"从同一份输出生成"，才能过对抗性审查。

## 1. 判别度指标：单一估计量贯穿全文（最容易被抓的不一致）
- 全文只允许一个术语。推荐 **"9-year cumulative/dynamic AUC (restricted to participants with known 9-year status)"**；
  cases = 9 年内死亡，controls = 随访 ≥9 年仍存活；评估样本量必须写进表注（本例 2,428/10,289 与 919/5,922）。
- 不要混用 Harrell's C / time-dependent concordance / restricted concordance / C9；Harrell's C 若要报，必须每一步标注"辅证"。
- 快速实现（避免 O(n²)、可放进 bootstrap）：
  `C = mean(findInterval(r[cases], sort(r[controls])))/length(controls)`
  比 `survival::concordance()` 快几个数量级，且能承受 500–1000 次重抽样。
- **Table 4 / 主表 / 摘要 / 各 S 表数字必须来自同一次运行**；审计时用脚本逐 token 对账（本会话靠它抓出 Table4 0.742 vs S8 0.776、S13 CI 0.784 vs 0.783）。

## 2. 删失：用"行政随访充分的主窗"，不要把 IPCW 当主分析
- 主评估窗 = **潜在随访 ≥ 时间窗的调查周期**（本例 NHANES 1999–2010，n=12,154，全部可到 9 年）。窗内 restricted 估计**无偏且无需删失权重** → 作为 primary censoring-robust evaluation。
- 全队列 restricted（60% 可贡献 9 年结局）与稳定化 IPCW 降为敏感性；IPCW 必须写明**权重截断**与"删失独立于结局"假设，并声明不作主结论（本例 IPCW 给 0.719/0.766，与 restricted 0.776/0.785 差 0.06，若当主结论会被质疑）。
- 晚期周期"根本无 9 年随访支持"是行政设计事实，加权补不回来 —— 这句话要写进 Methods/Limitations。
- 陷阱：`summary(survfit(...), times=vector)` 报 `condition has length > 1`；`concordance(fit, newdata=, weights=)` 不接受 weights。用 `approx(G$time, G$surv, xout=...)` 手取删失 KM 值。
- Brier：**统一一个定义**并写明评估人群；若用"已知 9 年状态人群"，必须承认它由结局与随访长度共同筛出（不是 IPCW Brier 的替代）；配对 ΔBrier 定义为 `updated − direct`，点估计与 CI 的符号必须一致（本会话出现过 +0.0002 配 −0.0004~0 的符号矛盾，被评审直接抓住）。

## 3. 内部 vs 外部要公平（apparent performance 污染）
- 外部 9 年 AUC 不能对比内部 **apparent** 值。要么 bootstrap 做**同指标**乐观校正（本例 9y AUC：CHARLS 0.8035→0.8021；NHANES 0.8081→0.8085），要么在评估窗内重拟 local 模型。
- **local 模型必须与外部模型在同一评估窗内拟合/评价**：用全队列拟合、子窗评价 = 训练集内含评价对象（GPT6 直接点名为硬伤）。修法是窗内 refit（本例 Table 5 local 由 0.800/0.805/0.808/0.808 → 0.800/0.806/0.809/0.808，Δ 从 −0.026 变 −0.026~−0.030）。

## 4. "无增量价值"不能只靠 ΔC —— 三件套才立得住
ΔAUC/ΔC 是最不敏感的增量指标（基线 C 越高天花板越低）。必须同时给：
1. **嵌套似然比检验**：M2（eGDR 固定线性组合）数学上嵌套于 M1（三个自由分量），2 自由度。CHARLS χ²=9.42, P=0.009 → "固定复合**未完全复现**自由分量"，比"ΔC≈0"强得多；NHANES 用加权偏似然（χ² 量级不可直接解释，只报 P）。
2. **IDI / continuous NRI**（同一评估窗、已知 9 年状态人群）：本例 M2 vs M0 IDI +0.0097 / NRI +0.261；M1 vs M0 +0.0182 / +0.251；**M2 vs M1 −0.0085 / −0.074** → 精准表述"小幅增益、部分复现"。
3. **DCA 净获益**（阈值 5–30%）：差异 ≤±0.0013 → 把"临床意义不确定"升级为"no clinically meaningful net benefit"。
另：机制句要写透 —— eGDR 三分量信息已被 BMI/SBP/diabetes 等常规变量吸收，它提供的是**参数压缩与跨队列一致性，而非新测量信息**（用户明确喜欢这句话，建议提到摘要结论）。

## 5. 选择偏倚 / 时期 / 机制 —— 低成本高回报
- **IPW 纳入权重**替代（或补充）多重插补：对全部适格者拟合 `glm(included ~ age + sex + education)`，`w = 1/p`（截断 0.05），加权重拟主模型。本例 per-SD HR 0.858 (0.776–0.948) vs 0.855 → 一句"结果对选择偏倚稳健"。CHARLS 教育变量名是 `raeduc_c`（不是 edu11）。
- **日历对齐敏感性**：两库年代不重叠时要补"仅对齐年代周期"的分析（本例 NHANES 2011–2014、5 年窗、n=4,422 → 与主分析一致）。
- **过报分解**（Debray/Riley 思路）：把线性预测子与基线风险交叉代入 —— A=源模型+源基线(22.7%)、D=源 lp+目标基线(14.7%)、观测 11.3% → 约 70% 过报来自**基线风险差异**，30% 来自 case-mix。把"校准不转运"从描述变机制。
- **样条要报结点与非线性检验**：3 结点 ns 在 10/50/90 百分位（本例 6.3/10.0/11.7），非线性 LR P=0.878。
- PH 违背：`cox.zph` 与 `eGDR×log(time)` 检验不同备择，两者并列报告 + 给 2y/7y 时点 HR，措辞限定为"未发现所设定 log(time) 形式的证据"。

## 6. 分期/亚组定义的自洽审计（S13 那类"改一个条件人数却乱跳"）
改一个 stage-2 条件，绝不能改变由 eGFR 决定的 stage-3 人数。做 sensitivity 时必须：
- 生成**逐人转移矩阵**，核对人数守恒（本例 NHANES alt 规则少 74 人 = 缺 eGFR，必须显式说明而不是拿括号"补足"）；
- 各规则分别报 n / 事件数 / HR（不能只给一个笼统 "alternative HR"）；
- 所有人数由同一次程序运行输出。

## 7. R 计算坑（本会话踩过，复现即省数小时）
- `coxph()` 在函数内 + 外部构造的 formula → `model.frame.default` 找不到 data/对象；把权重做成**数据列**（`d$WW <- w; weights = WW`），或顶层直接拟合。
- 长代码不要用 `Rscript -e '...'`（本例两次 segfault）；写成 .R 文件跑。
- `%<>%` 需 magrittr；`ns()` 需 `library(splines)`。
- NHANES 的 `cycle_year` 是 integer/字符混用时要先 `as.integer` 再比较；`haven_labelled` 列用 `as.numeric(unclass(x))`。
