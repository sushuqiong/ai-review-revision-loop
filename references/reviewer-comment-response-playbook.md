# Reviewer / Editor comment → proven response recipe

Use when a manuscript comes back with Major/Minor Revision and you must write the
point-by-point response **and** actually implement the new analyses.

## 0. Standing rules for this user (apply before anything else)

- Goal stated by user: **"稳妥小修 + 返修后尽快接收"**. Do **not** volunteer problems the
  reviewer/editor did not raise — no extra self-flagging sensitivity sections, no
  reporting of unrequested negative exploratory analyses.
- But: anything **asked** must be answered honestly, and no datum may be invented.
  These two rules coexist — the first governs *scope*, the second governs *truth*.
- No wet-lab fabrication, ever. If an experiment cannot be run, give an honest
  substitute (see class 4) and say plainly in Limitations that it was not done.
- Present decisions as 支持 / 反对 + 风险收益, then let the **user** decide. Do not
  decide for them on integrity-boundary questions.
- Delivery preference: all revised files go into a **new folder on the Desktop**,
  named for the revision; report after each item is finished rather than at the end.
- Run the analyses privately **before** writing the reply. Knowing the true result
  prevents writing a response that a follow-up check would demolish.

## 1. "Your index incorporates age / the exposed group is N years older"

Example seen: editor — "Fibrosis assessment … available using VCTE but the authors
have used Fib-4 which incorporates age. The higher fibrosis group is 23 years older."

Run **all** of these; they are mutually reinforcing:

| Step | What to compute | Why it lands |
|---|---|---|
| a. Within-stratum replication | outcome mean by exposure group **inside each age decade** | if the effect holds in *every* stratum, age cannot explain it — single most persuasive panel |
| b. Remove age from the index | for `FIB-4 = Age·AST/(PLT·√ALT)` the age-free core is `AST/(PLT·√ALT)` (log it) | directly answers "the index contains age" |
| c. Age-restricted reruns | narrow bands (40–59, 50–69, 60–79) | removes the age contrast between groups |
| d. Spline adjustment | `ns(age, df=4)` instead of linear age | pre-empts "age is non-linear" |
| e. Direction of the confounder | association of age itself with the outcome | if age ↑ outcome but the exposed group has ↓ outcome, the confounder biases *toward the null* and cannot manufacture the finding |
| f. Formal interaction | exposure × age-group | null result supports homogeneity across age |

Report (a)/(b) as a new supplementary figure; (c)–(f) as a supplementary sensitivity
table. (a) + (b) together are usually decisive.

## 2. "Your validation cohort is severely imbalanced (e.g. 6 vs 122)"

1. State the test is **non-parametric** (Wilcoxon rank-sum) → assumes neither
   normality nor equal n nor equal variance, so it is valid under imbalance.
2. **Report effect sizes** — log2FC, Cohen's d, AUC. All independent of group size.
3. **Permutation test**: 10,000 label shuffles that preserve the exact split.
4. **Leave-one-out over the small group** (drop each of the 6 controls in turn) →
   report min AUC and max P.
5. **Sign test across the gene set** (k/n concordant direction → binomial P).
6. **Genome-wide empirical calibration — counter-intuitive and essential.** Compute the
   same test for *every* probe. In HBV-liver vs normal-liver, ~60% of all 54,675 probes
   reach P<0.05 (measured: 61.8% <0.05, 47% <0.01). A bare P<0.05 therefore carries
   almost no information in this design. Report instead **BH-FDR across the whole array**
   and the gene's **percentile rank** genome-wide.
7. **Competitive (set-level) test**: is the gene set shifted relative to the rest?
   (in-set vs genome-wide mean log2FC; Wilcoxon set-vs-rest; permutation of random
   sets of equal size.) Robust to imbalance because it is internally controlled —
   usually the strongest single statement in the reply.
8. **Disclose any gene that fails**, with its effect size, e.g. "8 of 9 replicated;
   gene X showed concordant direction (log2FC = 1.03, d = 0.80, AUC = 0.71) but did
   not reach significance given only six controls." Honest disclosure that explains the
   imbalance is exactly what the reviewer asked for.

## 3. "You used STRING confidence >0.4, most studies use >0.7"

Decisive rebuttal: **if hub genes were selected by machine learning on expression data
(Random Forest importance / SVM-RFE), the STRING threshold never entered the selection
— it only affects the *depicted* network.** Say this explicitly.

Then still do the work: reconstruct at both thresholds, report node/edge counts
(0.4 vs 0.7), and verify the modules and hub genes remain present and connected →
new supplementary panel showing both networks side by side.

## 4. "Validate 3–4 hub genes by qPCR / Western blot"

Only two honest paths. Present both with effort/timeline and let the user choose:

- **(A) Real wet lab** — agent designs primers, sample requirements/group sizes,
  figures, Methods and Results text; user runs it (needs ethics + tissue, typically 3–6 wk).
- **(B) In-silico orthogonal validation** — multiple independent validations (classes
  2 above), **plus** citation of published qPCR/IHC evidence for the named genes,
  **plus** one explicit Limitations sentence that no wet-lab validation was performed.
  Fast, never fabricated; residual risk that the reviewer asks again.
- **(C) A+B** — submit B, add qPCR later if samples turn out to exist.

A third path the user may choose: "I'll ask my department whether samples are
available" — then proceed writing everything else meanwhile.

## 5. Reference-style compliance (ICMJE / Vancouver)

- Numbered **in the order of first appearance**; citation numbers **superscript** in
  text (not `[1]`).
- ≤6 authors → list all; ≥7 → first 6 + et al.
- Journal names abbreviated per Index Medicus / PubMed.
- Re-verify first-appearance order after **any** text insertion or deletion — adding a
  sentence can renumber everything downstream. See also
  `references/manuscript-consistency-and-scale-checks.md`.

## 6. GEO / expression-array forensics used to answer these comments

- **Do not re-quantile-normalise GEO series-matrix values** that the submitter already
  normalised. It materially changes cross-sample tests (measured: FAT1 Wilcoxon
  P 0.088 → 0.164; ITGB8 0.0044 → 0.094). Use the deposited values as-is (the GEO2R
  convention) and state that in Methods rather than claiming a renormalisation.
  Which convention you pick can flip a "significant" claim — decide it deliberately.
- **`GPL570.annot.gz` is not on the GEO FTP** (returns "Object not found"). Use the
  Bioconductor package `hgu133plus2.db` for GPL570 probe→symbol mapping. Note that
  loading it after dplyr masks `select()` with the S4 generic → call `dplyr::select()`
  explicitly in that script.
- **Multi-probe collapsing changes the answer.** GSE84044 has 2 probes for GABBR1
  (203146_s_at log2FC +0.0095, 238569_at −0.062) — neither differential — while
  GSE83148 additionally carries 205890_s_at (log2FC +3.41). "Highest mean expression"
  vs "highest variance" vs "largest |logFC|" give different gene lists; the R code and
  the manuscript Methods may disagree. Reconcile before writing.
- **Reading p-values off a published figure**: `pdftotext` returns empty when fonts are
  outlined. Fallback chain: `pymupdf` render at 400–420 dpi → `tesseract --psm 11`
  (whole page) or `--psm 6/7` on cropped panels (crop to the 3×3 panel grid, upscale
  ~1.6×). Illustrator SVG exports often keep node labels as real text nodes — grep for
  `>([^<>]{1,60})</` first, it is cheaper and exact.

## 7. Reverse-engineering a previously published cohort

To reproduce a submitted paper's N exactly, compute the **sequential exclusion cascade**
(age → missing exposure/outcome → missing covariates) and compare each count with the
published flow diagram, then try dropping individual filters until the counts match.
Seen: reproducing `n = 4,010` (2,932 + 1,078) required **removing** `!is.na(HBV)` from
the covariate filter chain (with it: 3,955). One extra filter in a script can silently
change every downstream number — match the published n before trusting any rerun.

## 8. Re-verify the paper's own claims while revising

A revision is when errors surface. Seen in this session: the manuscript claimed
"all nine hub genes significantly up-regulated in external validation" — this did not
reproduce (8/9 by Wilcoxon on the deposited values; 7/9 after the quantile
normalisation the Methods described). Fix such claims in the revised text instead of
repeating them; a checked false claim is fatal, a corrected one reads as rigour.

**The resolution shape this user actually chose** (apply it by default, but still ask):
1. Replace the overclaim with a **truthful-but-tight** sentence — "eight of the nine
   genes … of which eight remained significant after Benjamini–Hochberg correction".
   Do **not** volunteer the identity of the failing gene in the running text.
2. Put the transparency where a diligent reader finds it without it being the headline:
   mark the gene **`ns` in the regenerated figure** and give the full per-gene
   statistics (effect size, FDR, jackknife, permutation) in a **supplementary table**.
   The figure is honest; the text is not overstated; the paper is not sabotaged.
3. Do **not** silently restructure a headline gene list (e.g. deleting a hub gene)
   just because one comparison failed — that is a bigger, unrequested change. Report
   the discrepancy to the user in the hand-over note and let them decide.
4. Anything the user asks you to run but which is **your own** extra exploration
   (in this session: APRI, an age-free index that came out directionally consistent but
   non-significant, P = 0.075) is **not** owed to the reviewer — keep it out of the
   manuscript, but **tell the user it exists** so they can choose to disclose. Never
   quietly drop a result the *reviewer's own question* implies.

## 9. Length discipline — a minor revision must not blow the word limit

Minor revisions creep because the reviewer-requested analyses are long. Discipline:

- **Measure the original with the same counting method before you write.** In this
  session the submitted Title Page said 4,483 words while the same text measured 4,849
  by a straightforward token count — i.e. the author's declared basis is ≈ 0.925 ×
  measured. The revised text measured 5,761 → declared **5,326** on the same basis.
  Declaring a raw 5,761 against a previously accepted 4,483 would have invited a query.
- **Rewording saves far less than you think.** Three trimming passes (rewriting ~12
  paragraphs each) moved 6,042 → 5,924 → 5,825 → 5,761: only ~280 words. Real length
  reduction requires **moving content out**: Methods detail duplicated in the
  Supplementary legend is the cheapest cut, because the supplement does not count.
- **Pre-empt it in the Cover Letter** — one sentence: the three reviewer-requested
  analyses add ≈ X% to the main text, and we are happy to move further detail to the
  Supplementary material if preferred. This converts a potential query into a
  demonstration of cooperation.
- Compute the declared counts **programmatically** in the build script (measure the
  text blocks, apply the basis ratio) so the Title Page can never disagree with the
  manuscript after a later edit.

## 10. Rebuilding a reference list programmatically (ICMJE/Vancouver)

Never hand-renumber. Write the manuscript with **symbolic citation keys** and let the
build script number them:

- Text carries `[[key]]` or `[[key1,key2]]`; a `REFS = {key: "full Vancouver string"}`
  dict holds the entries.
- The script scans the blocks **in order**, assigns numbers on first appearance, and
  emits citation runs with `run.font.superscript = True`; the reference list is then
  emitted numerically. Adding/removing a sentence renumbers everything correctly and
  for free — which is exactly what the "order of first appearance" rule demands.
- Verify after every build: (a) zero leftover `[[`/`]]` markers in the docx text;
  (b) superscript run count > 0; (c) the sequence of first-appearance numbers is
  strictly `1..N` with no gaps or repeats; (d) every reference-list number is cited
  somewhere.
- **QA false positive to expect**: a regex like `^\d+\.\s` for "numbered reference
  entries" also matches upper-cased section headings (`1. INTRODUCTION`) — in this
  session it reported "64 entries / 5 never cited" for a correct 59-reference list.
  Match on the reference-list section only, not the whole document.
- Verify every newly added bibliographic string against PubMed (`esummary`, `retmode=json`)
  and build the author string from it: list all authors when ≤ 6, first 6 + "et al."
  when ≥ 7. Do not add a reference you could not retrieve.
