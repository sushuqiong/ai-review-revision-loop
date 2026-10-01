# NHANES 当代空腹问卷 / N3 协变量补提 / 共同 SD 尺度配方（GLM7×胆石 v10→v11 实测）

用途：审稿人说"XX 数据不可得/某期无变量"时，先用本文件核对 CDC 配套文件再写局限；
以及跨期 per-SD OR 不可比时的共同尺度修法。所有路径/列位来自 2026-09 实测。

## 1. 当代周期（2017-2023）空腹时长问卷文件 —— v10"无 PHPFAST 可查"的局限是错的
- P 周期（2017–2020 pre-pandemic）: `P_FASTQX.xpt` → 13,772×19，含 SEQN / PHAFSTHR（0–30 h）/ PHAFSTMN（0–59 min）/ PHDSESN（0/1/2 空腹亚样本标识）
- L 周期（2021–2023）: `FASTQX_L.xpt` → 8,727×19（末列名 PHDSESNZ）
- 派生: `PHPFAST_h = PHAFSTHR + PHAFSTMN/60`
- 实测：P/L 晨间空腹会话全部 ≥8h（P<8h=0, L<8h=0）；≥9h 仅排除 P 3 人 / L 32 人。
  结果不变（P M3 1.633→1.633；L M3 1.407→1.409；L M4 0.835→0.842, P=0.058）
- NHANES III 空腹时长在分析样本内本就全部满足（≥8.5 h），N3 敏感性用 ≥10h/≥12h 切点（M3 2.152/2.164）

## 2. CDC 新式下载路径（旧式 URL 返回 HTTP 200 + 20,905 字节的 HTML 假文件）
- 旧式 `https://wwwn.cdc.gov/Nchs/Nhanes/2021-2022/GLU_L.XPT` → 200 + HTML 错误页（不能只看状态码/必须看 size>100KB 或读 magic）
- 新式数据目录: `https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/<year>/DataFiles/<FILE>.xpt`
  - P_FASTQX（2017-2020）→ year=2017
  - FASTQX_L / GLU_L / INS_L（2021-2023）→ year=2021
  - 代码簿 .htm 与 XPT 同目录
- 验证变量名最可靠 = 下载 XPT `names(read_xpt())` + grep（2021–2023 空腹权重实测就是 WTSAF2YR，无 WTSAF2L —— 驳回审稿人错误主张的证据）

## 3. NHANES III adult.dat 固定宽度可补提的协变量（v10 曾误判"无 edu/smoke/HTN"）
从 adult.sas INPUT 行取列位（adult.dat 67MB，readLines+substr 或 read.fwf；ADULT.XPT 用 haven 解析失败，走固定宽度）：
| 变量 | 列位 | 含义 → 构造 |
|---|---|---|
| HFA8R | 1256–1257 | 最高年级/学位 → edu_cat（<12/12/>12 年对齐 P/L 三分类；P/L 用 DMDEDUC2 含 GED） |
| HAE2 | 1598 | 医生告知高血压 → HTN_f（仅医生告知、无血压实测，敏感性偏低，如实注明） |
| HAR1 | 2281 | 一生是否吸 ≥100 支 → smoke（与 P/L SMQ020 同构） |
| HAR3 | 2285 | 现在是否吸烟 → smoke 当前态（同构 SMQ040，跳过模式一致） |
| HAN6HS/IS/JS | 2164–2166 / 2167–2169 / 2170–2172 | 啤酒/葡萄酒/烈酒 月次数 → alcohol（任一>0 二分类，**替代** P/L ALQ101"终生≥12 杯/年"，口径差异写表注） |
| HAJ9 / HAJ12 | 1840 / 1844 | 胆石诊断/手术史（结局） |
- 缺失码：7/8/9、77/88/99、777/888/999 → NA（成人问卷的 refusal/don't know 编码）
- 分析样本补提后覆盖：smoke/alcohol/PIR 100%、edu 99.6%（缺 19）、HTN 99.3%（缺 39）
- 重跑对照（dx, per-SD）：N3 M3 旧(sex+race+PIR)=2.335(1.996–2.732) → 补提后(sex+race+edu+PIR+smoke+alcohol+HTN)=2.130(1.799–2.521)（−8.8%）；M4 1.307→1.283。
  注意：补提协变量会使分析样本略缩（n=5,345/354 → M3 完整 5,290/353）——正文 n 与表一致

## 4. 共同 SD 尺度（跨期 per-SD 不可比的正解）
- 问题：各期层内 z 标准化 → "1 SD"对应原始量不同（实测 GLM7 raw SD：P 0.7187 / L 0.6545 / N3 0.6623），跨期 per-SD OR 不可直接比较
- 修法：`GLM7_pSD = GLM7_raw / sd_P`（固定增量 = P 期 1 个 SD = 0.7187 raw 单位）。
  **注意：不要用 `raw/sd_own × sd_P`**——该式对 P 自身不自洽（1 单位 ≠ P 的 1 SD，P 行 OR 会变成 1.978 而非 per-SD 1.633）
- 结果（dx, M3 每 P-SD 增量）：P 1.633（不变，恒等自检）/ L 1.455 / N3(补协变量) 2.271；M4：1.326 / 0.820 / 1.310
- lnOR 比值应与理论 sd_P/sd_own（P 1.000 / L 1.098 / N3 1.085）吻合 → 自检
- 结论句模板："即便统一到 P-SD 增量尺度，跨期梯度 N3 > P > L 仍成立，非 SD 尺度假象"

## 5. 基准模型命名纪律（GPT6 二度评审）
- baseB 完整协变量含 age（代码 `c("age","gender_cat","race_cat","edu_cat","PIR_cat","smoke_f","alcohol_f","HTN_f","BMI")`）
- 正文禁用 "M3 covariates plus BMI" 简写（M3 不含 age/BMI → 读者误读 baseB 缺 age）；一律完整列：age, sex, race, edu, PIR, smoke, alcohol, HTN, BMI

## 6. v11 判别双 Panel 同源
- Table 4 Panel A（各指数 vs base 的 ΔAUC）、Panel B（GLM7 − 比较器配对差）、Figure 3 全部从同一 v10_auc_results.rds 的 `summary$<cohort>$<base>$auc_table/pair_table` 生成；表注注明舍入 ±0.0001
- 判别对象为 in-sample apparent increment（不赋予外部预测含义），bootstrap B=1,000 每层 PSU 重抽样（multinomial multiplier）、同一批重抽样用于全部模型、n_fail=0、权重重标度均值 1
