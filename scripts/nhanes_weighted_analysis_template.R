# NHANES 复合指数论文加权分析模板 (v8 项目验证可用, 2026-08)
# 用途: 复合代谢指数(GLM7 等) × 疾病结局的 survey-weighted 增量价值检验
# 依赖: dplyr, survey, pROC, rms, haven
# 用法: 按数据列名调整后整段运行; 输出保存为 vN_results.rds

suppressPackageStartupMessages({ library(dplyr); library(survey); library(pROC) })

# ============ 0. 单位换算 (NHANES 常见陷阱) ============
# TG mmol/L -> mg/dL (x88.57); LDL/HDL/TC mmol/L -> mg/dL (x38.67)
# Insulin pmol/L -> uU/mL (/6.945); FBG 已是 mg/dL
# TyG_correct = ln[FBG(mg/dL) * TG(mg/dL) / 2]   # 典型值 8-9, 若≈4 说明单位混用
# HOMA_IR     = INS_uU * FBG / 405
# LAP         = (waist - sex_adj) * TG;  男 65 / 女 58
# METS_IR     = ln[(2*FBG + TG) * BMI] / ln(2*FBG + TG)

calc_indices <- function(d) {
  d %>% mutate(
    TG_mgdl = TG * 88.57, LDL_mgdl = LDL * 38.67, HDL_mgdl = HDL * 38.67,
    INS_uU = Insulin / 6.945,
    TyG_correct = log(FBG * TG_mgdl / 2),
    HOMA_IR = INS_uU * FBG / 405,
    LAP = (waist - ifelse(gender == 1, 65, 58)) * TG,
    METS_IR = log((2*FBG + TG) * BMI) / log(2*FBG + TG),
    GLM7_noage = log10(BMI * FBG * Insulin * TG * LDL / HDL),
    GLM7_noage_nobmi = log10(FBG * Insulin * TG * LDL / HDL))
}

# ============ 1. 分析样本 + 每SD标准化 (在分析样本内!) ============
mk_an <- function(d) {
  d <- d %>% filter(is.finite(GLM7), is.finite(weight), !is.na(gsd_combined),
    !is.na(age), !is.na(gender_cat), !is.na(race_cat), !is.na(edu_cat), !is.na(PIR_cat),
    !is.na(smoke_f), !is.na(alcohol_f), !is.na(HTN_f), !is.na(SDMVPSU), !is.na(SDMVSTRA))
  for (v in c("GLM7","GLM7_noage","GLM7_noage_nobmi","TyG_correct","HOMA_IR","LAP","METS_IR")) {
    d[[paste0(v, "_sd")]] <- d[[v]] / sd(d[[v]], na.rm = TRUE)
  }
  d
}

# ============ 2. 加权主分析 (每SD, svyglm) ============
covs_m3 <- "gender_cat + race_cat + edu_cat + PIR_cat + smoke_f + alcohol_f + HTN_f + age"
run_svy <- function(d, xvar, covs = covs_m3, outcome = "gsd_combined") {
  d$y <- d[[outcome]]; d$x <- d[[xvar]]
  d <- d %>% filter(!is.na(y), is.finite(x))
  svy <- svydesign(ids = ~1, weights = ~weight, data = d)
  m <- svyglm(as.formula(paste0("y ~ x + ", covs)), design = svy, family = quasibinomial())
  b <- coef(m)["x"]; se <- sqrt(diag(vcov(m)))["x"]
  c(OR = exp(b), lo = exp(b - 1.96*se), hi = exp(b + 1.96*se), P = summary(m)$coefficients["x", 4])
}

# ============ 3. 加权 AUC (pROC weights 参数 - 最可靠) ============
wtd_auc <- function(y, pred, w) {
  ok <- is.finite(pred)
  r <- roc(y[ok], pred[ok], weights = w[ok], quiet = TRUE)
  ci <- ci.auc(r, method = "delong")       # 加权 DeLong CI (已验证可用)
  c(AUC = as.numeric(auc(r)), lo = ci[1], hi = ci[3])
}
# 增量比较 (配对): roc.test(r0, r1, method="delong") 在同一样本上

# ============ 4. 周期异质性检验 (合并队列 + 交互项) ============
# both <- bind_rows(Pm, Lm) %>% mutate(period_f = factor(period))
# svy_both <- svydesign(ids=~SDMVPSU, strata=~SDMVSTRA, weights=~weight, data=both, nest=TRUE)
# m_int <- svyglm(gsd_combined ~ GLM7_sd * period_f + covs_m3, design=svy_both, family=quasibinomial())
# 交互项 P 显著 => 周期效应不一致; 不显著 => 两周期一致(强证据点)

# ============ 5. RCS (rms 包, 必须 fun=exp 转 OR 尺度) ============
# library(rms)
# d_rcs <- d %>% select(gsd_combined, GLM7, all_of(cov_vars))  # 只留建模列
# dd <<- datadist(d_rcs); options(datadist = "dd")             # 全局赋值!
# f <- lrm(gsd_combined ~ rcs(GLM7, 4) + 协变量, data = d_rcs, x = TRUE, y = TRUE)
# pred <- Predict(f, GLM7 = seq(min,max,length=60), ref.zero = TRUE, fun = exp)  # fun=exp!
# an <- anova(f); p_nl <- an[rownames(an)[grepl("Nonlinear", rownames(an))], "P"]

# ============ 6. PSU/strata 提取 (在 DEMO 文件, 不在 cohort rds) ============
# demo <- haven::read_xpt("P_DEMO.xpt")
# d <- d %>% left_join(demo %>% select(SEQN, SDMVPSU, SDMVSTRA), by = "SEQN")
