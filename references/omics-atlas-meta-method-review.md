# Omics-atlas methodological review & rerun recipes (v08→v09)

Session-tested recipes for cross-cohort public-omics atlas manuscripts when a
first-principles reviewer (GPT6-type) forces re-derivation of what the statistics
can and cannot show. Three reruns changed headline numbers — do reruns BEFORE
rewriting text, then rebuild all derived materials.

## Rerun 1 — joint composition model (not residual-then-test)

Residualizing module scores on composition and re-testing in a second step is not
equivalent to adjusting composition inside the model, and over-removes disease
signal. Per cohort and module fit instead:

```r
# paired cohorts keep patient factor (module score as outcome)
fit <- lm(y ~ group + epi + fib + end + imm + pid, data=dat)   # pid for matched
# fallback (record `fallback=TRUE`) if patient factor singular:
fit <- lm(y ~ group + epi + fib + end + imm, data=dat)
cf <- summary(fit)$coefficients
d_adj <- cf["groupCase","Estimate"] / summary(fit)$sigma
se_adj <- cf["groupCase","Std. Error"] / summary(fit)$sigma
p_adj <- cf["groupCase","Pr(>|t|)"]
```

Report adjusted effect + SE + CI per cohort (never only an FDR flag), plus design
rank/full-rank flag and the fallback log. Then define composition-robust states as
≥2 adjusted cohorts FDR<0.05 (per-cohort BH) with stable majority direction.

Observed consequence (26-cohort atlas): xCell-residual pipeline reported 19
composition-robust states; the joint model left 6 (overlap 5). PAAD effects were
attenuated under both; IBD JAK-STAT survived joint adjustment (resolves a
previously flagged residual-vs-single-cell contradiction).

## Rerun 2 — unified-scale meta-analysis

Paired mean-change standardized by SD of paired differences (d_z) is NOT on the
same scale as unpaired Hedges' g. Convert paired effects to the g scale:

```r
g_eq <- d_z * sqrt(2*(1 - r))          # r = empirical within-pair correlation
V    <- 2*(1 - r)/np + g_eq^2/(2*(np-2))
# unpaired cohorts: Hedges' g with usual variance
# r: estimate from matched pairs per module when np>=8, else 0.5 (do r=0.3/0.7 sensitivity)
```

Pool with DL (anti-conservative at k=2-3) and REML variance + Hartung-Knapp
adjustment (t, k-1 df) as the conservative layer; report both, with per-disease BH.
Observed: DL sig 73→31, REML/HK sig 4→11 after unification; PAAD left both sets.
Caution: near-perfect empirical r yields very tight CIs (k=2) — report and
re-check under fixed r.

REML/HK impl core (R):

```r
reml_tau <- function(y,v){ k<-length(y); t<-0
  for(i in 1:300){ w<-1/(v+t); mu<-sum(w*y)/sum(w)
    num<-sum(w^2*(k/(k-1)*(y-mu)^2 - v)); den<-sum(w^2)
    if(!is.finite(num)||!is.finite(den)||den<=0) break
    nt<-max(0,num/den); if(!is.finite(nt)) break
    if(abs(nt-t)<1e-9){t<-nt;break}; t<-nt }
  if(!is.finite(t)) 0 else t }
hk <- function(y,v,t){ k<-length(y); w<-1/(v+t); mu<-sum(w*y)/sum(w)
  if(k<=1) return(c(mu,NA,NA,NA,NA)); q<-sum(w*(y-mu)^2)
  se<-sqrt(max(q/((k-1)*sum(w)),1e-12)); p<-2*pt(-abs(mu/se), df=k-1)
  tc<-qt(.975,k-1); c(mu,se,p,mu-tc*se,mu+tc*se) }
```

## Rerun 3 — external-cohort identity & sample-count audit

Before interpreting any external OS result:
1. Count arrays in GEO series vs analysable (time>0 & event 0/1) vs events; verify
   no duplicate sample ids, no adjacent-normal rows leaking into the tumour
   analysis (label via source_name/characteristics), and OS annotation one-to-one.
2. Adjust positives with age AND stage where available (parse TNM stage robustly);
   report HR + 95%CI per model (uni / +age / +age+stage).
3. For external negatives, give 95%CIs and classify direction vs TCGA
   (consistent-wide / attenuated / opposite) instead of "not significant".
4. Report the same patient-identity checks for every external cohort, not only the
   headline one. ACRG/GSE62254 survival came from the paper's ESM sheet FINAL;
   GEO key `patient: <N>` mapped 300/300 to clinical Tumor IDs.

## Writing rules that follow the reruns

- If user asks for a statement that contradicts what was actually done (e.g.,
  "AI was not used" when LLM-assisted analysis/drafting occurred), refuse the
  false positive; offer standard/minimal disclosure wording; if the user insists
  on omission after being informed, delete the statement and keep an internal
  note that the journal form may ask separately. Never write the affirmative lie.
- Zenodo DOI is optional when all primary data are already public (no new data
  deposit obligation) — Data-availability can promise code release only.
- Title: prefer "composition-aware" over "composition-adjudicated" unless the
  joint-model analysis actually adjudicates (reviewer language test).
- Restructure: per-state evidence matrix CSV first, then rewrite abstract/results/
  conclusions from the matrix; keep DepMap/CPTAC/drug maps in supplement as
  descriptive anchors.
