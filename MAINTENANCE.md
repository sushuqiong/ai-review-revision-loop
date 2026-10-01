# Maintenance & Publishing

This skill lives at `~/.hermes/skills/academic/ai-review-revision-loop/` (Hermes) and is
mirrored to a **public** GitHub repository:

> https://github.com/sushuqiong/ai-review-revision-loop

## After every edit → push

Run these three steps from the skill root:

```bash
cd ~/.hermes/skills/academic/ai-review-revision-loop     # or E:/Apps/Hermes/hermes/skills/academic/ai-review-revision-loop on Windows

# 1) strip anything that identifies a person or an unpublished manuscript
python scripts/anonymise_skill.py            # applies the map; add --check for a dry run

# 2) commit (amend if the previous commit was never pushed, so history stays clean too)
git add -A
git commit -m "<what changed>"
git log --oneline -1                          # sanity check

# 3) push
git push origin master
```

## Why the anonymise step is mandatory

The repository is **PUBLIC**. Reference files routinely quote real project details, so before
pushing, personal identifiers must be replaced:

| Identifier | Replaced with |
|---|---|
| author names | `[First Author]` / `[Corresponding Author]` |
| personal e-mail addresses | `corresponding@example.com` / `user@example.com` |
| journal submission IDs (e.g. `<JOURNAL>-D-YY-NNNNN`) | `JCEH-D-XX-XXXXX` |
| manuscript IDs (e.g. `<MS>-NNNNNNN`) | `MS-XXXXXXX` |

`scripts/anonymise_skill.py` does this and **exits non-zero if any residue remains** — always
confirm it prints `residue: 0  OK to push` before step 3.

## History hygiene

A file can be anonymised while the **commit history still contains the original text**.
If the commit carrying the personal data has **not been pushed yet**, rewrite it:

```bash
python scripts/anonymise_skill.py
git add -A
git commit --amend -m "<same message>"        # rewrites the unpushed commit
git log -p --all | grep -nE "<the literals from your local map>"   # must print nothing
git push origin master
```

If it **has already been pushed**, amend + `push --force-with-lease` (coordinate first) or
accept that the identifier is public and consider rotating it.

## Layout

```
SKILL.md                  # index + hard rules (kept under 30k chars; long content lives in references/)
references/               # 120+ topic files (pitfalls, per-round logs, checklists, recipes)
scripts/                  # runnable helpers (anonymise_skill.py, verify_manuscript_structure.py, ...)
templates/                # json/md templates consumed by the workflow
```

**Keep `SKILL.md` lean.** It is loaded on every invocation, so long material must be
downsunk into `references/<topic>.md` and referenced by a one-line pointer. When it
approaches the size limit, split by topic rather than truncating.
