# -*- coding: utf-8 -*-
"""Anonymise personal identifiers before pushing this skill to a PUBLIC repo.

Identifier rules are kept OUT of this file so that the script itself can be public.
They are read from `scripts/anonymise_map.local.json` (git-ignored), e.g.:

    {
      "literals": {"Real Name": "[First Author]"},
      "regexes":  [[ "J[A-Z]{3}-D-\\\\d{2}-\\\\d{5}", "JCEH-D-XX-XXXXX" ]]
    }

Usage (from the skill root):
    python scripts/anonymise_skill.py [--check] [--map PATH]

Exit code is non-zero when any residue is found — always require "residue: 0"
before `git push`.
"""
import sys, io, os, re, json, argparse

TEXT_EXT = {".md", ".txt", ".py", ".yaml", ".yml", ".json", ".sh", ".html", ".css", ".js", ""}
SKIP_DIRS = {".git", "__pycache__", "node_modules"}
DEFAULT_MAP = os.path.join("scripts", "anonymise_map.local.json")


def load_map(path):
    if not os.path.exists(path):
        print("!! map not found: %s" % path, file=sys.stderr)
        print("   create it (git-ignored) with your literal/regex replacement rules.", file=sys.stderr)
        return None
    d = json.load(io.open(path, encoding="utf-8"))
    lits = list(d.get("literals", {}).items())
    rx = [(re.compile(p), r) for p, r in d.get("regexes", [])]
    return lits, rx


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in TEXT_EXT:
                yield os.path.join(dirpath, fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, do not write")
    ap.add_argument("--root", default=".")
    ap.add_argument("--map", default=DEFAULT_MAP)
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    rules = load_map(a.map if os.path.isabs(a.map) else os.path.join(root, a.map))
    if rules is None:
        return 2
    lits, rx = rules

    changed, residue = [], []
    for p in iter_files(root):
        if os.path.basename(p) == os.path.basename(a.map):
            continue
        try:
            t = io.open(p, encoding="utf-8", errors="strict").read()
        except Exception:
            continue
        t0 = t
        for lit, rep in lits:
            t = t.replace(lit, rep)
        for pat, rep in rx:
            t = pat.sub(rep, t)
        if t != t0:
            changed.append(os.path.relpath(p, root))
            if not a.check:
                io.open(p, "w", encoding="utf-8").write(t)
        for lit, _ in lits:
            if lit and lit in t:
                residue.append((os.path.relpath(p, root), lit))
        for pat, _ in rx:
            for m in pat.finditer(t):
                residue.append((os.path.relpath(p, root), m.group(0)))

    print("[%s] files changed: %d" % ("DRY-RUN" if a.check else "APPLIED", len(changed)))
    for f in sorted(changed):
        print("   " + f)
    if residue:
        print("\n!! RESIDUE (must be zero before pushing PUBLIC):")
        for f, s in residue[:25]:
            print("   %-52s %s" % (f[:52], s))
        return 1
    print("\nresidue: 0  OK to push")
    return 0


if __name__ == "__main__":
    sys.exit(main())
