#!/usr/bin/env Rscript
# Template: paired-effect verification battery (three checks) for case-control module scores.
# Why: a paired-sample indexing error silently drops matched cohorts from meta-analysis and
#      produces tell-tale signatures (within-pair r = 1.00 / median r ~0.99 / var = 0 / yi = 0).
#      A "fix" that still indexes the full vector with subset positions is only correct when
#      cases happen to occupy the leading rows — this battery catches that half-fix.
# Copy into <repo>/tests/check_paired_effect.R, edit the CONFIG block, run:
#   Rscript tests/check_paired_effect.R | tee tests/check_paired_effect_log.txt
# Expect: check 1 gives plausible yi/vi and r in ~0.1-0.7; checks 2 and 3 print identical: TRUE.

suppressPackageStartupMessages({library(GSVA); library(metafor)})

## ---- CONFIG (edit per project) ----
ROOTS   <- c("path/to/processed_objects/root1", "path/to/root2")   # searched for <ACC>_processed.rds
GENE_SET_FILE <- "config/gene_sets_extended.csv"                   # columns: module, gene
PAIRED_ACC    <- c("GSE44076", "GSE32863", "GSE15471")             # cohorts with matched case/control
ACC   <- PAIRED_ACC[1]
FEAT  <- "WNT_CTNNB1"                                              # module to test
MIN_SIZE <- 3
## ----------------------------------

gs <- read.csv(GENE_SET_FILE, stringsAsFactors = FALSE)
mods <- lapply(split(toupper(gs$gene), gs$module), unique)

locate <- function(a) for (d in ROOTS) {
  f <- list.files(d, pattern = paste0("^", a, "_processed\\.rds$"), full.names = TRUE)
  if (length(f)) return(f[1])
}
obj <- readRDS(locate(ACC))
e <- obj$gene_expression                     # adjust to your object layout
m <- obj$sample_metadata                     # needs sample_id, group (Case/Control), optional patient_id
e <- e[, match(m$sample_id, colnames(e)), drop = FALSE]
pid <- if ("patient_id" %in% names(m)) as.character(m$patient_id) else as.character(m$sample_id)
grp <- factor(m$group, levels = c("Control", "Case"))   # explicit reference: coefficient = Case - Control

score <- function(expr) {
  genes <- intersect(mods[[FEAT]], rownames(expr))
  stopifnot(length(genes) >= MIN_SIZE)
  as.numeric(GSVA::gsva(GSVA::gsvaParam(expr, setNames(list(genes), FEAT),
                                        minSize = MIN_SIZE, kcdf = "Gaussian"),
                        verbose = FALSE)[1, ])
}

run <- function(expr, meta_order = NULL) {
  y <- score(expr)
  if (!is.null(meta_order)) {
    y <- y[match(meta_order, colnames(expr))]
    p <- pid[match(meta_order, m$sample_id)]
    g <- grp[match(meta_order, m$sample_id)]
  } else { p <- pid; g <- grp }
  cc <- intersect(p[g == "Case"], p[g == "Control"])
  # CRITICAL: subset FIRST, then match within each subset (never y[match(cc, subset_ids)])
  y_case <- y[g == "Case"]; y_ctrl <- y[g == "Control"]
  yc <- y_case[match(cc, p[g == "Case"])]
  yr <- y_ctrl[match(cc, p[g == "Control"])]
  ri <- suppressWarnings(cor(yc, yr)); ri <- if (is.finite(ri)) min(max(ri, -0.99), 0.99) else 0.2
  es <- metafor::escalc(measure = "SMCRH", m1i = mean(yc), m2i = mean(yr),
                        sd1i = sd(yc), sd2i = sd(yr), ri = ri, ni = length(cc))
  c(yi = as.numeric(es$yi), vi = as.numeric(es$vi), ri = ri,
    dz = mean(yc - yr) / sd(yc - yr), n = length(cc))
}

a  <- run(e)
cat(sprintf("[1] %s %s: yi=%.4f vi=%.6f ri=%.4f dz=%.4f n=%d\n",
            ACC, FEAT, a["yi"], a["vi"], a["ri"], a["dz"], a["n"]))
stopifnot(is.finite(a["yi"]), a["vi"] > 0, abs(a["ri"]) < 0.95)   # signature guards

set.seed(1); perm <- sample(colnames(e))
b <- run(e[, perm], meta_order = colnames(e[, perm]))
cat(sprintf("[2] shuffled order: yi=%.4f vi=%.6f  | identical to [1]: %s\n",
            b["yi"], b["vi"],
            isTRUE(all.equal(unname(a[c("yi","vi","ri")]), unname(b[c("yi","vi","ri")])))))

c2 <- run(e)
cat(sprintf("[3] repeat run: yi=%.4f vi=%.6f  | identical: %s\n",
            c2["yi"], c2["vi"],
            isTRUE(all.equal(unname(a[c("yi","vi")]), unname(c2[c("yi","vi")])))))
