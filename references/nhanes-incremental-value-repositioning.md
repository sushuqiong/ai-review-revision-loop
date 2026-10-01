# NHANES 复合指数论文"增量价值检验"重定位配方（v6 → v7 实例）

来源：课题2（GLM7 × 胆囊结石）依据 ChatGPT 对 v6 的深度审稿建议 + 用户确认"完全采纳重新定位"，从
"GLM7 预测胆囊结石"改写为"GLM7 与自报胆囊结石病史的关联及增量价值检验"，目标期刊 BMC Gastroenterology。
全部数字为真实重算（2026-08），可作同类论文（新复合指数套旧结局）的模板。

## 触发场景
AI 审稿人判定：创新不足（新指标套用旧结局）、指数内嵌年龄/BMI 造成结构性关联、判别力不优于 BMI/
现有代谢指标。此时修复 ≠ 措辞降级，而是**整体重定位为增量价值检验**。

## 分析重做（全部 survey-weighted）

### 1. 加权主分析（三结局 × 两周期）
- 权重：P 周期 WTSAFPRP、L 周期 WTSAF2YR（空腹亚组最小权重，NHANES 官方要求）
- svydesign(ids=~1, weights=~weight) + svyglm(family=quasibinomial)（P 系列用 quasibinomial 因加权方差）
- 结局拆分：gsd_dx (MCQ550==1) / gsd_sx (MCQ560==1) / gsd_combined (gallstone==1)
- 真实结果：M3 加权 OR——P 联合 1.731 (1.329–2.255) P=4.8e-05、dx 1.869、sx 1.850；
  L 联合 1.681 (1.295–2.182) P=1.0e-04、dx 1.518、sx 1.787

### 2. 增量价值比较（核心新分析）
- 模型：base（性别/种族/教育/PIR/吸烟/饮酒/HTN/年龄）vs +BMI vs +WHtR vs +TyG vs +TyG-WHtR vs +GLM7
- 加权 AUC + DeLong 95%CI + roc.test 配对 DeLong P（同一样本）
- 真实结果（P 周期）：base 0.744 → +GLM7 0.755（ΔAUC +0.011, P=0.0096）→ +BMI 0.768（Δ+0.024）；
  L 周期 base 0.713 → +GLM7 0.723（Δ+0.010, P=0.0589 边缘）→ +BMI 0.749（Δ+0.037）
- 结论模板："GLM7 增量有限（ΔAUC 0.010–0.011），低于 BMI/WHtR 的 0.024–0.037；主要信息来自年龄和肥胖组分"
- **增量小是研究发现而非缺陷**——写进摘要结论与 Cover letter 定位段

### 3. 敏感性（写进 Supplementary Materials）
- Table S1 未加权：P M3 OR=1.699、L 1.624（vs 加权 1.731/1.681，方向一致）
- Table S2 去年龄（指数含 age → 去掉 age 协变量）：P/L OR 均 1.85——证明非纯年龄驱动
- Table S3 加权四分位（P Q4=2.495、L Q4=3.118）+ M3b 过度调整（+BMI+waist）：P 1.226 P=0.24、
  L 0.819 P=0.22——肥胖组分解释大部分关联
- Figure S1 单指标 ROC（GLM7 vs TyG）：P 0.634 vs 0.596 P=1.6e-05；L 0.610 vs 0.599 P=0.29
  （L 周期不显著——如实报告）

### 4. 样本筛选流程（每步人数 + 缺失比例）
P：总 15,560 → GLM7 完整 4,508 → 结局完整 3,806 → 分析样本 2,998（409 例）
缺失：GLM7 71.0%（空腹亚组设计）、MCQ550/560 40.7%、权重 67.3%——全部写进方法

## 论文重写要点（对照 v6 的关键变化）
1. 标题加 "Incremental Value"：Association and Incremental Value of ... With Self-Reported
   Gallstone Disease History in Two NHANES Periods, 2017–2023
2. 加权主分析；未加权降为敏感性
3. 结局统一命名 "self-reported history of gallstone disease"（不暗示当前超声确诊）
4. "temporal validation" → "later-period replication / replication in a non-overlapping
   NHANES period"
5. 删除：筛查阈值、candidate cut-point、"窗口期"机制故事、优于人体测量学声称、亚组机制解释
6. 删一组分分析改名 component-omission robustness analysis（不证明机制）
7. 方法补：跨周期实验室可比性（TG 检测平台更替、LDL 统一 Friedewald、周期内 z 标准化）、
   缺失数据、完整病例局限、公开 R 代码+变量映射表

## 交付文件夹结构（精简版，v7）
```
v7_交付_课题X/
├── 01_分析代码/   (按步骤编号的 R/py 脚本，含补充材料和 docx 生成)
├── 03_结果数据/   (全部 v7 rds)
├── 04_图表_矢量/  (Figure 1-5 + Figure S1 × SVG/PDF/PNG)
├── 05_论文投稿/   (论文 v7 + Cover letter/Highlights/Title page/Plain English/STROBE/Supplementary Materials)
└── 06_README/     (README：定位变化、核心结果表、文件清单、待办)
```
不复制旧版审计/过程文件；"其它多余文件少一点"是用户明确要求。

## 陷阱
- P/L 周期列名不一致（P 无 gender_cat/DM/TyG 列）→ 先 names() 对比再手动补
- 加权 svyglm 用 quasibinomial（binomial 会警告）；predict(type="response") 用于 roc
- 补充材料引用进正文用实际措辞（复数 "Tables S1–S3"），python-docx 跨 run 需整段重建
- 先 clarify 确认用户接受重定位工作量（本会话用户选"完全采纳"）

## 第二轮（v7 → v8）：ChatGPT 统计硬伤修复实操（2026-08 实例）

### TyG 单位修正（第一硬伤）
- 现象：表 1 TyG 均值 ≈4.0 → 混合单位（FBG mg/dL + TG mmol/L）；正确应 ≈8-9
- 修正：`TG_mgdl <- TG * 88.57; TyG_correct <- log(FBG * TG_mgdl / 2)`
- 结果：P 8.43 / L 8.59 ✓；注意 TyG 单独 log vs ln 对 AUC 无影响（单调变换），但 TyG-WHtR/TyG-BMI 乘积必须用修正后的 TyG 重算

### 每 SD 主效应（审稿人更认可）
- `d$x_sd <- d$x / sd(d$x, na.rm=TRUE)` — **在分析样本内**标准化，不是全队列
- 主表报每 SD OR；1 单位 log10 指数变化仅作补充
- 真实结果（每 SD, M3, 联合）：P 1.488 (1.229–1.802)、L 1.408 (1.185–1.672) 均显著

### GLM7-no-age 敏感性链（证明信息来自哪个组分）
- GLM7_noage = log10(BMI×FBG×Insulin×TG×LDL/HDL)（去 age 组分，模型仍调 age）
- GLM7_noage_nobmi = log10(FBG×Insulin×TG×LDL/HDL)（再去 BMI，模型调 age+BMI+waist）
- 真实结果：去 age 后 P 1.449 / L 1.386（仍显著→非纯年龄驱动）；去 age+BMI 后 P 1.122 P=0.29 / L 0.888 P=0.21（消失→肥胖组分解释大部分关联）
- 这是论文最有价值的诚实发现，写进 Results + Discussion

### 公平比较指标（上限 3 个：HOMA-IR / LAP / METS-IR）
- HOMA_IR = INS_uU × FBG / 405（INS_uU = Insulin pmol/L / 6.945）
- LAP = (waist − sex_adj) × TG；男 65 / 女 58（waist cm、TG mmol/L）
- METS_IR = ln[(2×FBG + TG) × BMI] / ln(2×FBG + TG)
- 真实结果（每 SD）：METS-IR 在 L 周期更强（OR 1.779 vs GLM7 1.408）——公平比较中 GLM7 非最佳，如实报告
- 不要恢复 AIP/VAI/CMI 等"指数动物园"（减分项）

### 加权 AUC 的正确实现（pROC weights 参数）
```r
r <- roc(d$y, d$pred, weights = d$weight, quiet = TRUE)
a <- as.numeric(auc(r))
ci <- ci.auc(r, method = "delong")            # 加权 DeLong CI，已验证可用
dt <- roc.test(r0, r1, method = "delong")     # 配对加权 AUC 比较
```
- 手写加权 C-statistic 大权重下恒 0（浮点/等值/索引 bug）——不要重造
- PSU/strata（SDMVPSU/SDMVSTRA）在 DEMO 文件：`left_join(demo %>% select(SEQN, SDMVPSU, SDMVSTRA), by="SEQN")`

### 周期异质性检验（合并队列）
- `bind_rows` 两周期 + period_f 因子 + 交互项 `GLM7_sd * period_f`（svyglm）
- 真实结果：交互 P=0.72 → 两周期效应一致，是强证据点

### NHANES III 超声验证（客观结局升级）
- NHANES III (1988–94) 文件：成人 20-74 岁 + 胆囊超声（区分超声胆石 vs 胆囊切除/缺失）
- 三层证据设计：III 超声 + 2017–2020 自报 + 2021–2023 重复；不合并个体数据
- 各时期用各自权重/PSU/strata；固定 GLM7 公式与单位；分别报原始尺度+每 SD 效应
- 最后效应量分层汇总或 meta 分析；只能称"客观结局和历史时期验证"非地域外部验证

#### NHANES III 实测落地（2026-08：设计可行但有两个硬限制）
- **下载 URL**：`https://wwwn.cdc.gov/nchs/data/nhanes3/{1a|2a}/{FILE}.dat`（adult.dat 67MB 含胆石 HAJ9/HAJ12/HAJ16/17；exam.dat 195MB 含 BMPBMI；lab.dat 58MB 含 G1P 空腹血糖、TCP/TGP/LCP/HDP 血脂 mg/dL；**lab2.dat 只在 2a/** 且只是权重+甲状腺）。每个 .dat 配 .sas 代码簿（INPUT 语句给每变量列区间）→ R 固定宽度解析（readLines + substr + 正则提取列号）
- **关键变量列**（已验证）：HAJ9 col 1840（自报胆石）、HAJ12 col 1844（胆囊手术）、HAJ16/17 col 1850-51（复核）；G1P col 1866-70；TCP/TGP/LCP/HDP col ~1598-1624；BMPBMI 在 exam；WTPFEX6 权重、SDPPSU6/SDPSTRA6 设计变量
- **硬限制①：NHANES III 没有空腹胰岛素也没有 C-peptide**（CEP 是肌酐！）→ 完整 GLM7 和 HOMA-IR 无法计算 → 用 `GLM7_noins = log10(age × BMI × G1P × TGP × LCP / HDP)` 变体并在论文中明确披露"III 用无胰岛素变体"。TyG（无胰岛素）仍可算
- **硬限制②：III 的胆囊超声变量不在成人/体检主文件**（超声检查在独立文件）——若只想用自报胆石（HAJ9/HAJ12），adult.dat 已够；要超声客观结局需再找超声文件
- 实测队列：18,162 人合并（adult+lab+exam inner_join by SEQN）；胆石 dx=1,006 / sx=929 / combined=1,156；GLM7_noins 均值≈7.93
- 完整解析器+读取脚本见 `nhanes-data-access` 技能 `references/nhanes3-fixed-width.md`

### RCS 重算（v8 数据后图注必须同步）
- rms：`dd <<- datadist(d)`（全局赋值，d 只留建模列）+ `lrm(gsd ~ rcs(GLM7,4) + covs)`
- `Predict(f, GLM7=gseq, ref.zero=TRUE, fun=exp)` 转 OR 尺度（默认是概率）
- 非线性 P：`anova(f)` rownames 含 "Nonlinear" 的行；参考点改中位数（审稿人偏好）
- 真实结果：P 非线性 P=0.728（样本定义变化 vs v6 的 0.216）——改图必须同步正文/图注
