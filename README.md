# AI Review-Revision Loop

A platform-neutral skill for systematically reviewing medical manuscripts with AI reviewers (simulating high-impact journal editors), then fixing issues by priority. 

## What it does
1. **AI peer review**: spawns reviewer subagents that actually read the manuscript (python-docx), cross-check numbers against analysis outputs (RDS/CSV), and verify references via PubMed — no fabricated opinions.
2. **Priority-based fixing**: data-integrity issues (P0) → methodology (P1) → formatting (P2) → language (P3).
3. **Honest recalculation**: every new number (E-value, quartile ORs, DCA) is recomputed in R, never invented.
4. **Submission packaging**: 7-folder delivery structure with vector figures (SVG/PDF/PNG), cover letters, and graphical abstracts.

## Key pitfalls documented
- DCA net benefit cannot exceed outcome prevalence (mathematically impossible values = data-integrity red flag)
- Recalibrated probabilities should not be used to assess calibration (circularity)
- Prediction-model papers must report the full formula (z-score constants + intercept + lambda)
- Vancouver references must follow first-appearance order
- Same-source time-window validation ≠ true external validation (use "temporal validation")
- Shared-component mathematical coupling between exposure and outcome must be discussed

## Files
- `SKILL.md` — the full workflow (trigger conditions, steps, pitfalls, verification checklist)

## License
MIT
