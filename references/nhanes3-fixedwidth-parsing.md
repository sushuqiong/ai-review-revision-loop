# NHANES III 固定宽度 .dat 数据解析配方（1988–1994，历史时期验证用）

本会话在 v7→v8 中首次成功使用 NHANES III（1988–1994）做"历史时期验证"，记录了完整的数据获取与解析流程。

## 1. 数据下载（CDC 官方路径，非 XPT）

NHANES III 与现代周期不同：**不是 XPT 文件，是固定宽度 .dat + SAS codebook（.sas）**。

```
基础 URL: https://wwwn.cdc.gov/nchs/data/nhanes3/
1a/ 子目录: adult.dat (67MB, 成人问卷), exam.dat (195MB, 体检), lab.dat (58MB, 实验室)
2a/ 子目录: lab2.dat (38MB, 权重+甲状腺激素，无胰岛素)
SAS 读取说明: https://wwwn.cdc.gov/nchs/data/nhanes3/1a/adult.sas / exam.sas / lab.sas
```

文件清单页面: `https://wwwn.cdc.gov/nchs/nhanes/nhanes3/datafiles.aspx`（grep `[a-z0-9]+\.(dat|xpt)`）。

## 2. 关键变量与列位置（本会话已解析验证）

| 文件 | 变量 | 含义 | 列 |
|------|------|------|-----|
| adult.dat | SEQN | 受试者 ID | 1–5 |
| | HSAGEIR | 年龄 | 18–19 |
| | HSSEX | 性别 | 15 |
| | DMPPIR | 收入贫困比 | 36–41 |
| | HAJ9 | Doctor ever told you had gallstones | 1840 |
| | HAJ12 | Have you ever had gallbladder surgery | 1844 |
| | HAJ16/17 | 复核询问 | 1850/1851 |
| | WTPFSD6 / SDPPSU6 / SDPSTRA6 | **晨间空腹权重** / PSU / strata | (adult.sas 内查；WTPFEX6 是 MEC 总权重勿用) |
| lab.dat | G1P | 空腹血浆葡萄糖 (mg/dL) | 1866–1870 |
| | TCP / TGP / LCP / HDP | 总胆固醇 / TG / LDL / HDL (mg/dL) | 1598–1624 |
| | **I1P / I1PSI** | **血清胰岛素 (uU/mL) / (pmol/L)** | **1918–1923 / 1924–1930** |
| | CEP | Serum creatinine（肌酐） | ~1915 |
| | WTPFSD6 / SDPPSU6 / SDPSTRA6 | **晨间空腹权重** / PSU / strata | (lab.sas 内查) |
| exam.dat | BMPBMI | BMI | (exam.sas 内查) |

## 3. ⚠️ 重大限制 → v10 修正：NHANES III **有**空腹胰岛素（I1P）

**早期（v7–v9）错误结论**：曾认为 lab.dat 无胰岛素、CEP 是肌酐故"NHANES III 未测胰岛素"，因而只能用六成分 GLM7_noins。
**v10 重建证实这是错的**（两位 AI 审稿人点名后核实 CDC lab.sas 全变量清单）：

| 变量 | 含义 | 列 |
|------|------|-----|
| **I1P** | **Serum insulin (uU/mL)**，如 "009.32" | **lab.dat 1918–1923** |
| **I1PSI** | Serum insulin (pmol/L)（NHANES 内部换算 ×6.0；文献标准 ×6.945，常数不影响 per-SD OR） | 1924–1930 |
| CEP | Serum creatinine（肌酐）——CEP 是肌酐这条没错，但不能据此推断"没测胰岛素" | ~1915 |

- 教训：**"某调查没测某变量"的结论必须 grep 该期全部 .sas 的完整变量清单**（本会话早期只扫了部分文件/关键字，漏掉 I1P）。`grep -iE "insulin|INS" lab.sas` 能找到 I1P/I1PSI/I2P/I2PSI。
- 因此 NHANES III 可构建**完整 7 成分 GLM7**：`GLM7 = log10[age×BMI×FBG×Insulin(pmol/L)×TG×LDL/HDL]`（I1P×6.945、TG÷88.57、LDL/HDL÷38.67），六成分 GLM7_noins 只是敏感性/与早期周期同构对照。

## 3b. 缺失码必须先清洗（888 系 + 临床范围），否则 OR 被拉低

- NHANES III 特殊缺失哨兵：**888/8888/88888/888888 及 777/999 系**（SAS 格式 .M/.R/.D 落盘值）→ NA；再加临床合理范围过滤（G1P 50–400、TG 20–2000、LDL 20–300、HDL 5–150、I1P 1–300 uU/mL）；HAJ9/HAJ12 的 7/8/9 → NA。
- **坑**：`c(50,400,"label")` 会把区间向量强转字符 → 字符串比较批量误删 1.7 万人。区间必须是纯数值向量。
- 清洗效果（v10 实测）：adult 20,050 → ≥20 岁 18,825 → 晨间空腹亚样本(WTPFSD6>0) 7,832（病例 543）→ 结局完整 6,902 → 7 成分完整 5,945 → +PIR 最终 5,368（病例 412；dx 354 / sx 345）。OR 从污染的 1.196 变 1.68+，**不能把污染值当主结果再在局限性里"验证方向"**。

## 3c. 空腹亚样本权重 = WTPFSD6（不是 WTPFEX6）

- **WTPFEX6 = Total MEC examined sample final weight（MEC 体检总权重）**——v8/v9 用错。
- **WTPFSD6 = Total morning subsample final weight（晨间空腹亚样本权重）= 正确选择**；与 lab 时段变量 MXPSESSR=morning 交叉验证 100% 吻合。WTPFMD6=下午/傍晚样本。
- 附带发现：NHANES III 血糖/胰岛素/TG 实际对几乎所有时段体检成人都测（不只晨间）；晨间样本 PHPFAST 中位 12.3h。

## 4. SAS codebook 解析 → 固定宽度读取

```r
parse_sas <- function(sas_file) {
  lines <- readLines(sas_file, warn = FALSE)
  vars <- list(); in_input <- FALSE
  for (ln in lines) {
    if (grepl("^\\s*INPUT", ln)) in_input <- TRUE
    if (in_input) {
      m <- regmatches(ln, regexec("^\\s*([A-Z0-9_]+)\\s+(\\d+)(?:-(\\d+))?", ln))
      if (length(m[[1]]) > 1) {
        vname <- m[[1]][2]; start <- as.numeric(m[[1]][3])
        end <- if (nzchar(m[[1]][4])) as.numeric(m[[1]][4]) else start
        vars[[vname]] <- c(start = start, end = end)
      }
      if (grepl(";", ln)) in_input <- FALSE
    }
  }
  vars
}

read_fwf_vars <- function(dat_file, vars, keys) {
  lines <- readLines(dat_file, warn = FALSE)
  df <- data.frame(row.names = seq_along(lines))
  for (v in keys) {
    if (!v %in% names(vars)) { df[[v]] <- NA; next }
    pos <- vars[[v]]
    df[[v]] <- sapply(lines, function(ln) {
      s <- substr(ln, pos["start"], pos["end"])
      suppressWarnings(as.numeric(trimws(s)))
    })
  }
  df
}
```

## 5. 本会话实测结果（v8 论文 Layer 3 旧口径 vs v10 重建）

**v8 旧口径（未清洗缺失码、无胰岛素、权重 WTPFEX6——已废弃，勿复用）**：
- adult + lab + exam 三文件按 SEQN 合并 → 18,162 行；胆石 combined = 1,156（dx 1,006 / sx 929）
- GLM7_noins 每SD 加权 OR M2 1.172 (1.057–1.301) P=0.003——**该值建立在污染数据上（8888 缺失码当真实值 + WTPFEX6 权重），AI 审稿人点名后弃用**

**v10 重建（正确口径）**：
- 完整 7 成分 GLM7（含 I1P 胰岛素）、缺失码清洗、权重 WTPFSD6、svydesign(strata=SDPSTRA6, PSU=SDPPSU6, wt=WTPFSD6 缩放, quasibinomial)
- 分析样本 n=5,368（dx 354 / sx 345），加权患病率 combined 5.74%（dx 5.23% / sx 4.78%）
- 每SD OR（combined）：M1 = 2.066 (1.778–2.401) P=1.5e-12；M2(+age+sex+race) = 1.784 (1.489–2.138) P=1.4e-07；M3(+PIR) = 1.772 (1.483–2.117) P=1.5e-07——与 P/L 当代周期（M3 OR≈1.6）高度一致，三时期一致性叙事反而更稳
- PHPFAST≥8h 敏感性 M2 = 1.706（n=5,945）

## 6. 陷阱

- 权重极大（0~741,000），裸 `glm(y~x, weights=weight)` 数值爆炸（coef 1e15、预测全≈0、AUC 恒 0.5）→ 必须先缩放 `w_scaled <- weight / mean(weight[weight>0])`，pROC 加权 AUC 仍用原始权重
- 列位置用 SAS codebook 解析而非硬编码（不同文件列不同）
- 年龄是整数（HSAGEIR），成人筛选 ≥20
