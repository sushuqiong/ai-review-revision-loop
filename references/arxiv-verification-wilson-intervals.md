# arXiv API Citation Verification + Wilson Intervals (worked example: v23/v24 → v25)

Session-tested additions to the multi-AI review loop: a fourth AI reviewer (ChatGPT) named specific 2025-2026 works and flagged the Wald-interval choice. Two reusable recipes below.

## 1. Verify AI-claimed 2025/2026 works via arXiv API (anti-hallucination)

AI reviewers (especially ChatGPT) name concrete recent papers/projects. Before citing any of them, verify existence + get authors via arXiv API (no key needed).

### Search recent relevant papers (sorted by date)
```bash
curl -sL "http://export.arxiv.org/api/query?search_query=all:%22AI+incident%22+AND+all:%22reporting%22&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending" -o arx.xml
```

### Fetch specific IDs (for claimed titles → find ID via search, or if you have the ID)
```bash
curl -sL "http://export.arxiv.org/api/query?id_list=2606.08376,2511.05914" -o arx2.xml
```

### Parse entries (python, stdlib only)
```python
import re
c = open('arx2.xml', encoding='utf-8').read()
entries = re.findall(r'<entry>.*?</entry>', c, re.S)
for e in entries:
    aid = re.search(r'<id>http://arxiv.org/abs/(.*?)</id>', e).group(1)
    authors = re.findall(r'<name>(.*?)</name>', e)
    title = re.search(r'<title>(.*?)</title>', e, re.S).group(1).strip()
    date = re.search(r'<published>(.*?)</published>', e).group(1)[:10]
    print(aid, '|', title[:80], '|', ', '.join(authors[:3]) + (' et al.' if len(authors) > 3 else ''), '|', date)
```

### Rules learned
- **AI claims existence ≠ existence.** In the v25 session ChatGPT named 3 specific works; all 9 that eventually entered the reference list were verified via this API, and one claimed resource could NOT be verified and was NOT cited.
- Fill real authors into references (`Abraham S, Chen T, Chhun C, et al. ... arXiv:2604.19914`), not `[Author(s)]` placeholders.
- Keep a Readiness Checklist open item "re-verify author list against current paper metadata before submission" — arXiv metadata can change between versions.
- This complements the PubMed E-utilities flow for medical journals: 2025-2026 preprints (especially AI/governance) live on arXiv, not PubMed.

### v25 verified set (example, all real)
- arXiv:2604.19914 AI Incident Monitoring through a Public Health Lens (2026-04)
- arXiv:2606.08376 RiskNet: large-scale dataset of AI risk incidents from news (2026-06)
- arXiv:2511.05914 Designing Incident Reporting Systems for Harms from General-Purpose AI (2025-11, AAAI 2026 — 9 case studies)
- arXiv:2604.23183 Designing escalation criteria for international AI incident response (2026-04)
- arXiv:2604.21412 A pragmatic classification framework for AI incident monitoring (2026-04)
- arXiv:2607.05163 Open Problems in AI Incident Governance (2026-07)
- arXiv:2605.16281 Post-Deployment Accountability in AI Governance (2026-04)
- arXiv:2603.04259 When AI Fails, What Works? (2026-03)
- arXiv:2604.24519 Why AI Harms Can't Be Fixed One Identity at a Time (5300 incident reports, 2026-04)

## 2. Wilson interval for descriptive proportions (replaces Wald near 0/1)

AI reviewer: "91/100 reporting 85.4–96.6% looks like a plain Wald interval; 91/100 Wilson ≈ 83.8–95.2%." Correct — Wilson is the right choice for proportions near the boundary.

```python
import math

def wilson(x, n, z=1.96):
    """Wilson score interval for x successes / n trials. Returns (lo, hi) in proportion units."""
    if n == 0:
        return (0.0, 0.0)
    p = x / n
    denom = 1 + z*z/n
    centre = (p + z*z/(2*n)) / denom
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / denom
    return (centre - half, centre + half)

# Example: 91/100 -> (0.838, 0.952)
print(wilson(91, 100))
```

### Presentation rules (non-probability corpus)
- Report every proportion with numerator/denominator: "91/100 (91.0%; descriptive Wilson 95% interval 83.8–95.2%)".
- **Explicitly label** the interval a "descriptive precision statement about the sampled corpus" and add "not confidence intervals for a population proportion, because the corpus is not a probability sample".
- Apply the same to cluster-level estimators (91 clusters) and stratified results.

## 3. PDF three-line-table verification via pymupdf get_drawings()

Vision models misjudge thin rules at low DPI ("table has no lines"). Objective check:

```python
import fitz
doc = fitz.open(r'C:\Users\fengq\AppData\Local\Temp\...\manuscript.pdf')  # full Windows path!
page = doc[4]  # page containing the table
lines = []
for d in page.get_drawings():
    w = d.get('width')
    for item in d['items']:
        if item[0] == 'l':
            p1, p2 = item[1], item[2]
            if abs(p1.y - p2.y) < 0.5:  # horizontal rule
                lines.append((round(p1.y,1), round(p1.x,1), round(p2.x,1), round(w or 0, 2)))
for h in sorted(lines, key=lambda x: x[1]):
    print(h)
# booktabs three-line table = exactly 3 horizontal rules: thick top (~0.87), thin header (~0.55), thick bottom (~0.87); no vertical rules
```

Notes:
- `booktabs=true` pandoc variable produces these rules in xelatex PDFs.
- LibreOffice `soffice --headless --convert-to pdf` writes output to the Windows Temp dir (`C:\Users\fengq\AppData\Local\Temp\`), not MSYS `/tmp` — open with the full Windows path.

## 4. Scope/title mismatch correction (agentic 5/100)

When an AI reviewer notes the title overclaims the evidence base (e.g., "for agentic systems" but strict agentic n=5/100):
- Rewrite the title around what the data actually support (the documentation gap), not the aspirational subgroup.
- Keep the subgroup as a bounded stratum statement in Methods: strict agentic (n=5 definite; n=40 unclear; n=45 action-capable sensitivity layer).
- Verify the actual distribution from the data file (agentic column: `Counter` over values) before writing the numbers.

## 5. Three-pass adversarial review (v25 post-build gate)

1. **Programmatic pass**: citation integrity 1..N with en-dash handling; key numbers vs recomputed values (grep each claimed percentage); residual-term scan (Noether/G²/Einstein/placeholder/AI Index).
2. **Human reviewer pass**: find uncited named entities in figure legends (e.g., "MIT AI Risk Repository" without a reference number → add reference), imprecise "recoverability was 14/100" (distinguish present=0 vs partial=14).
3. **Visual/programmatic pass**: PDF table line extraction (section 3 above); figure rendering check; verify no LaTeX residue in PDF text (`\\[`, `\\sim`, `dN_k`).
