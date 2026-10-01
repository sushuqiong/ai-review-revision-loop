#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manuscript number-provenance check (正文数字 vs 冻结结果表一致性).

Why: in multi-round revision loops the manuscript, tables and figures drift out of sync.
Text keeps a superseded number (e.g. "retained 7" after the rerun produced 17), or a figure
legend keeps an old count ("12 hits" while the frozen table has 17). Hand-checking 170 states
every round is how errors survive to submission. This script makes the check mechanical.

What it verifies
  1. csv_counts  – recompute headline numbers from FROZEN result tables and assert the manuscript
                   contains the string(s) built from those numbers (never hand-typed).
  2. citations   – reference list sequential; every listed reference cited; first-appearance
                   ordering non-decreasing; optional range syntax like [21-50].
  3. abstract    – word count under a limit; optional "no citations in abstract".
  4. hygiene     – literal \\uXXXX escape residue, markdown residue, stale strings absent,
                   required strings present, forbidden/placeholder strings absent.

Usage
  python manuscript_number_provenance_check.py --manuscript Manuscript_draft_v11.md \
      --rules rules.json [--quiet]
Exit code 0 = PASS, 1 = FAIL (details printed). No third-party dependencies.

Rules file (see templates/manuscript_number_provenance_rules.json for a starter):
{
  "abstract_max_words": 300,
  "abstract_must_not_cite": true,
  "stale":  ["retained 7", "573 tumour", "12 hits"],
  "required": ["556 tumour samples", "61.9%", "0.87"],
  "csv_counts": [
    {"name": "meta_bh_sig",
     "path": "results/v11_meta_primary_reml_knha.csv",
     "where": "k>=2 and fdr<0.05",
     "group_by": "disease",
     "expect": ["retained {n} "]},
    {"name": "composition_robust",
     "path": "results/v11_joint_summary.csv",
     "where": "joint_robust==TRUE",
     "expect": ["{n} of 170 states were composition-robust"]},
    {"name": "sc_paired_tests",
     "path": "results/sc_v11_patient_paired.csv",
     "where": "fdr<0.05 and comparison_type==same-cell-type",
     "expect": ["{n} same-cell-type comparisons"]}
  ]
}
`where` supports `col OP value` terms joined by ` and ` with OP in >= <= == != > <,
plus the pseudo-term `contains:<substring>` for substring matches on any column value.
`expect` strings are formatted with {n} (count), and optionally {n_<group>} for group counts.
Paths are resolved relative to the rules file; absolute paths work too.
"""
import argparse, csv, json, os, re, sys

OPS = [">=", "<=", "==", "!=", ">", "<"]


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def as_number(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def build_predicate(where):
    if not where:
        return lambda row: True
    terms = []
    for raw in [t.strip() for t in where.split(" and ")]:
        if raw.startswith("contains:"):
            needle = raw.split(":", 1)[1].strip()
            terms.append(("__contains__", needle, needle))
            continue
        m = re.match(r"^([A-Za-z_][\w.]*)\s*(>=|<=|==|!=|>|<)\s*(.+)$", raw)
        if not m:
            raise SystemExit(f"cannot parse where-term: {raw!r}")
        col, op, val = m.group(1), m.group(2), m.group(3).strip()
        if val[:1] in "\"'":
            val = val.strip("\"'")
        terms.append((col, op, val))

    def pred(row):
        for col, op, val in terms:
            if col == "__contains__":
                if not any(val in str(v) for v in row.values() if v is not None):
                    return False
                continue
            x = row.get(col)
            if x is None or x == "":
                return False
            num_val = as_number(val)
            if num_val is not None:
                x = as_number(x)
                if x is None:
                    return False
            if op == ">=" and not x >= val:
                return False
            if op == "<=" and not x <= val:
                return False
            if op == ">" and not x > val:
                return False
            if op == "<" and not x < val:
                return False
            if op == "==" and not x == val:
                return False
            if op == "!=" and not x != val:
                return False
        return True

    return pred


def csv_count_checks(rules, base_dir):
    out = []
    for spec in rules.get("csv_counts", []):
        path = spec["path"]
        if not os.path.isabs(path):
            path = os.path.join(base_dir, path)
        if not os.path.exists(path):
            out.append((spec["name"], None, None, [f"result table missing: {path}"]))
            continue
        rows = read_rows(path)
        pred = build_predicate(spec.get("where"))
        hits = [r for r in rows if pred(r)]
        groups = {}
        if spec.get("group_by"):
            for r in hits:
                groups[str(r.get(spec["group_by"], "NA"))] = groups.get(str(r.get(spec["group_by"], "NA")), 0) + 1
        fmt = dict(n=len(hits))
        fmt.update({f"n_{k}": v for k, v in groups.items()})
        fmt.update({f"n_{k.replace(' ', '_')}": v for k, v in groups.items()})
        expects = [e.format(**fmt) for e in spec.get("expect", [])]
        out.append((spec["name"], len(hits), groups, expects))
    return out


def check_citations(text, fail):
    body, sep, ref = text.partition("## References")
    if not sep:
        fail.append("no '## References' section found")
        return {}
    nums = [int(m.group(1)) for line in ref.splitlines() if (m := re.match(r"\s*(\d+)\.\s", line))]
    if not nums:
        fail.append("reference list is empty")
        return {}

    def expand(tok):
        out = []
        for part in tok.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-")
                out += list(range(int(a), int(b) + 1))
            else:
                out.append(int(part))
        return out

    order = []
    for m in re.finditer(r"\[(\d+(?:\s*[-,]\s*\d+)*)\]", body):
        for v in expand(m.group(1)):
            if v not in order:
                order.append(v)
    if nums != list(range(1, len(nums) + 1)):
        fail.append("reference numbering is not sequential 1..N")
    uncited = [n for n in nums if n not in set(order)]
    if uncited:
        fail.append(f"listed but never cited: {uncited}")
    dangling = [v for v in order if v not in set(nums)]
    if dangling:
        fail.append(f"cited but not listed: {sorted(set(dangling))}")
    if any(order[i] < order[i - 1] for i in range(1, len(order))):
        bad = [(order[i - 1], order[i]) for i in range(1, len(order)) if order[i] < order[i - 1]][:5]
        fail.append(f"first-appearance numbering violated, e.g. {bad}")
    return {"refs": len(nums), "cited": len(order)}


def check_abstract(text, rules, fail):
    m = re.search(r"## Abstract(.*?)## 1\.", text, re.S)
    if not m:
        fail.append("abstract section not delimited by '## Abstract' ... '## 1. Introduction'")
        return {}
    abstract = m.group(1)
    words = len(re.findall(r"\S+", abstract))
    limit = rules.get("abstract_max_words")
    if limit and words > limit:
        fail.append(f"abstract is {words} words (limit {limit})")
    if rules.get("abstract_must_not_cite", False) and re.search(r"\[\d", abstract):
        fail.append("abstract contains bracketed citations")
    return {"abstract_words": words}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manuscript", required=True)
    ap.add_argument("--rules", required=True)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    base_dir = os.path.dirname(os.path.abspath(args.rules))
    rules = json.load(open(args.rules, encoding="utf-8"))
    text = open(args.manuscript, encoding="utf-8").read()
    fail, info = [], {}

    if not args.quiet:
        print(f"manuscript: {args.manuscript}")

    # 1) frozen-table numbers must appear in the text
    for name, n, groups, expects in csv_count_checks(rules, base_dir):
        if n is None:
            fail += expects
            print(f"  [MISS] {name}: {expects[0] if expects else 'unavailable'}")
            continue
        line = f"  {name}: n={n}"
        if groups:
            line += f"  groups={groups}"
        print(line)
        for e in expects:
            if e in text:
                print(f"    OK   text contains: {e!r}")
            else:
                fail.append(f"{name}: manuscript does not contain {e!r} (frozen table says n={n})")

    # 2) citations
    cinfo = check_citations(text, fail)
    info.update(cinfo)

    # 3) abstract
    info.update(check_abstract(text, rules, fail))

    # 4) hygiene
    residue = len(re.findall(r"\\u[0-9a-fA-F]{4}", text))
    if residue:
        fail.append(f"literal \\uXXXX escape residue: {residue} occurrence(s)")
    for st in rules.get("stale", []):
        if st in text:
            fail.append(f"superseded text still present: {st!r}")
    for req in rules.get("required", []):
        if req not in text:
            fail.append(f"required text missing: {req!r}")
    for bad in rules.get("forbidden", []):
        if bad in text:
            fail.append(f"forbidden text present: {bad!r}")

    print("\nsummary:", {k: v for k, v in info.items()})
    print("RESULT:", "PASS" if not fail else "FAIL")
    for f in fail:
        print("  -", f)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
