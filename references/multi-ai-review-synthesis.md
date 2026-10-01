# Multi-AI Review Synthesis → Next Version Work Package (worked example: AI健康医学 v21/v22.1 → v23)

Session-tested workflow for: user supplies 2-3 AI review docx files + an old work package, asks for an upgraded vN+1 package plus synchronized backend/theory packages and knowledge bases.

> **Later round (v23/v24 → v25, 4th AI reviewer ChatGPT):** adds arXiv-API verification of AI-claimed 2025/2026 works, Wilson intervals for descriptive proportions, scope/title mismatch correction, and the three-pass adversarial review gate. See `references/arxiv-verification-wilson-intervals.md`.

## 0. Inputs and reading

- AI opinions are .docx: read with `D:\ProgramData\python.exe` + python-docx (paragraphs AND tables).
- Work package layout (this user's convention): `01_submission/ 02_supplement/ 03_figures/ 04_rebuttal/ 05_audit/ 06_whitepaper_cn/ 07_working/` + `README` + `hash_manifest.jsonl`.
- Backend packages: `01_science_core/ 02_reproducibility/ 03_mappings/ 04_audit/`; theory backend: `01_einstein_method/ 02_partial_observation/ 03_control_information/ 04_life_science_boundaries/ 05_... 06_... 07_audit/`.
- Knowledge bases: Feishu `*_sync_staging/` (docx per chapter + xlsx/jsonl data + staging_manifest.json), Obsidian vault (00_Index..07 navigation notes + mirrored package dirs).

## 1. Extract the three-column consensus table

Build a table: issue | source(s) | resolution | location. Sources = ClaudeOpus / GPT / ZLM style opinions. Rules:
- All-three-agree issues are must-fix (e.g., G² metric, Noether, conservation laws → delete outright).
- Single-AI sharp issues need verification (arithmetic errors, statistic contradictions).
- Opposing views (keep vs delete Hallmark) → partial adoption ("retained but demoted": exploratory C1–C10, no operational threshold).

## 2. Verify every numeric claim against raw data BEFORE propagating

AI reviewers claim contradictions; the raw files decide. Worked example:
- GPT: "60+20+10+10+10=110 ≠ 100". Parsed `source_registry_v22.1.jsonl` (100 lines) with a Counter over `source_stratum`/`source_family` → actual: AIID=60, OECD AIM=20, direct=20 (10 primary official + 10 direct company/regulatory) = 100. Verdict: manuscript TEXT was wrong (double-counted AIID family), data was right. Fix text, not data.
- ClaudeOpus: "Table 7 absent counts suspicious (runtime lineage absent=0, recurrence absent=0)". Verified against `Record summary` sheet: actually runtime_lineage absent=2, recurrence absent=35 — the claim did not hold at record level; v22.1's numbers were internally consistent.
- kappa contradiction (v21 0.72 vs v22.1 "none") → resolved by explicit withdrawal, not by reviving either number.

Key files to parse: `source_registry_*.jsonl` (provenance, strata), `Supplementary_Table_S1_*.xlsx` (sheets: case table / Record summary / Cluster summary). The xlsx summary sheets are pre-computed; recompute from the case sheet when adding new estimators.

## 3. Add new measurable contributions (not just deletions)

The v23 increment: (a) prior-art crosswalk — field-level table vs OECD reporting framework / OECD AIM / EU AI Act Art.73 / AIID / NIST AI RMF / MIT AI Risk Repository; (b) dual cluster-level estimators — `uniform disclosure` (all linked sources present) vs `cluster recoverability` (≥1 source present / ≥1 present-or-partial); computed from the case table grouped by dedup_group. Result demo: recurrence status 11.0% (strict) vs 70.3% (loose) on the same 91 clusters → "the missingness rule is part of the measurement".

```python
# Dual cluster estimator computation (openpyxl, D:\ProgramData\python.exe)
from collections import defaultdict, Counter
clusters = defaultdict(list)
for r in rows[1:]:
    clusters[str(r[dedup_idx])].append(r)
# per field: ge1 = any(v=='present'), ge1p = any(v in ('present','partial','suggestive')),
# uniform = all(v=='present'), strict = all(v=='present') [same as uniform here]
```

## 4. Cross-version statistic withdrawal pattern

When vN reported a reliability statistic that vN+1 disowned:
- Write an explicit withdrawal sentence in Methods: "An earlier version reported X (κ=0.72); that estimate cannot be reconstructed from retained provenance (coder identity, dates, raw sheets, unreconciled vectors missing) and is withdrawn."
- Do NOT carry the number anywhere in the new version.
- Specify future provenance requirements in the pilot/reliability section (two coders, randomized order, frozen protocol, raw sheets preserved, kappa + Gwet's AC1 for imbalanced prevalence, disagreements before consensus).

## 5. Honest-boundary edits reviewers force

- Title: drop misleading brand ("AI Health Infrastructure" reads as medical-AI governance) → descriptive title about the actual contribution.
- "minimum interoperable" → "candidate minimum" (interoperability never demonstrated).
- Unfitted equations (state-space, counting process) → remove from main text; replace with a measurement-definition paragraph; keep the log-rate structure as a pilot-only candidate note in the backend.
- Future-dated citations (AI Index 2026), unused citations (Wiener, Ashby, Noether, Prigogine) → delete.
- MedDRA attribution fix (ICH, not NCI).

## 6. Citation integrity check (with en-dash pitfall)

```python
import re
body = content.split('## References')[0]
cited = set()
for m in re.finditer(r'\[([0-9,\-\u2013\s]+)\]', body):   # \u2013 = en dash!
    for part in re.split(r'[,\s]+', m.group(1)):
        if '\u2013' in part or '-' in part:
            a, b = re.split(r'[\u2013\-]', part)
            cited.update(range(int(a), int(b)+1))
        elif part.isdigit():
            cited.add(int(part))
refs = [int(r) for r in re.findall(r'^(\d+)\.\s', content.split('## References')[1], re.M)]
print('orphan cited:', sorted(cited - set(refs)), 'uncited:', sorted(set(refs) - cited))
```
Pitfall: `[1–6]` (en dash) is NOT matched by `[0-9,\-\s]+` — always include `\u2013`.

## 7. Paywalled source verification via Crossref

OECD full text sits behind Cloudflare. `curl "https://api.crossref.org/works?query.title=Towards+a+common+reporting+framework+for+AI+incidents&rows=3"` returned DOI `10.1787/f326d4ac-en`, publisher OECD, date 2025-02-28. Enough for a framework-level crosswalk; label cells "framework-level, field-level reconciliation pending".

## 8. Package build pipeline (Windows / git-bash)

- md → docx: `pandoc file.md -o file.docx --reference-doc=<old_version_manuscript.docx>` — reuses the prior version's styles for consistency.
- md → pdf: `pandoc ... --pdf-engine=xelatex -V mainfont="DejaVu Serif" -V geometry:margin=2.5cm` (TinyTeX xelatex available at `~/AppData/Roaming/TinyTeX/bin/windows/xelatex`).
- Figures: matplotlib script (D:\ProgramData\python.exe has matplotlib 3.11) → PDF + PNG 300dpi; verify 1-2 key figures with vision_analyze for overlap/clipping (note: vision models are permissive — check numbers/labels yourself).
- xlsx: openpyxl; add new analysis sheets (e.g., "Cluster dual estimates") to the copied S1 workbook.
- Hash manifest: walk tree → sha256 per file → `hash_manifest_v23.jsonl`.
- Zip: Python `zipfile` (git-bash has no `zip`).

## 9. Deliverable structure for the upgraded version

- Work package vN+1: submission set (manuscript md/docx/pdf, cover letter, highlights, declarations, executive summary, figure legends, readiness checklist), supplement (materials + route + S1 xlsx + source_registry + schema JSON), figures, rebuttal (QA bank / revision-response map / safe sentence bank), audit (preflight report / risk register / upgrade map vN→vN+1), Chinese whitepaper, README, hash manifest, zip.
- Backend support package: measurement definition (replacing decorative equations), coding manual, preregistration template, crosswalk xlsx, claim-evidence matrix, source-truth audit (records strata reconciliation vN vs vN+1).
- Theory backend: methodology notes with mandatory non-implication statements, candidate failure-capability taxonomy, **abandoned-analogies register** (deleted constructs: G², Noether, conservation laws, time dilation — why deleted, what replaced them, discipline rule against re-introduction), controlled speculative extensions.
- Knowledge bases: mirror the package into Feishu staging (docx chapters + manifest) and Obsidian vault (navigation notes + package mirrors). Do not modify the shared source-of-truth evidence dirs in place — copy/update, preserve originals.
