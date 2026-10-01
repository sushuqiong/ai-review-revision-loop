#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Citation audit + optional first-appearance renumbering for academic manuscript markdown.

Why this exists: a naive scanner that only parses comma lists "[9,10]" will mis-report
cohort-registry ranges such as "[21-50]" (hyphen or en-dash \u2013) as 30 "uncited"
orphan references. Real problems are usually different: dangling numbers, genuinely
uncited entries, and first-appearance-ordering violations (ref 9/10 appearing before 4-8).

Usage:
  python citation_audit_renumber.py <manuscript.md>          # audit only
  python citation_audit_renumber.py <manuscript.md> -r       # audit + renumber by first appearance

Behaviour:
  - Parses reference entries (lines like "N. text") below "## References" (configurable).
  - Scans body citation tokens; token parts may be comma lists AND hyphen/en-dash ranges.
  - Audit prints: listed count, duplicates, dangling (>max), uncited, ordering violations.
  - With -r: builds old->new by first appearance, rewrites every token, reorders the
    reference list, then re-verifies (violations==0, list sequential).
  - After md renumbering you MUST rebuild the docx/pdf from the md (citations changed).
"""
import re
import sys

REF_HEADER = "## References"


def expand(token):
    """Expand a token like '9,10' or '21-50' or '21\u201350' into a list of ints."""
    out = []
    for part in token.split(","):
        part = part.strip()
        m = re.match(r"^(\d+)\s*[-\\u2013]\s*(\d+)$", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if b < a:
                a, b = b, a
            out += list(range(a, b + 1))
        elif part.isdigit():
            out.append(int(part))
    return out


def parse_refs(refsec):
    entries = []
    for line in refsec.splitlines():
        m = re.match(r"^\s*(\d+)\.\s", line)
        if m:
            entries.append((int(m.group(1)), line))
    return entries


def audit(body, refs):
    """Return dict of audit stats over a body string."""
    refnums = [n for n, _ in refs]
    order, flat = [], []
    for m in re.finditer(r"\[(\d+(?:\s*[,-\u2013]\s*\d+)*)\]", body):
        for v in expand(m.group(1)):
            flat.append(v)
            if v not in order:
                order.append(v)
    mx = max(refnums) if refnums else 0
    dangling = sorted({v for v in flat if v < 1 or v > mx})
    uncited = [n for n in refnums if n not in set(flat)]
    seen = set()
    dups = [n for n in refnums if n in seen or seen.add(n)]
    prev, vio, first_bad = 0, 0, []
    for n in order:
        if n < prev:
            vio += 1
            if len(first_bad) < 10:
                first_bad.append((prev, n))
        prev = n
    return dict(listed=len(refnums), maxnum=mx, dupnums=dups,
                unique_cited=len(order), dangling=dangling, uncited=uncited,
                violations=vio, first_bad=first_bad, order_head=order[:40])


def main():
    path = sys.argv[1]
    do_renumber = "-r" in sys.argv
    s = open(path, encoding="utf-8").read()
    body, sep, refsec = s.partition(REF_HEADER)
    refs = parse_refs(refsec)
    stats = audit(body, refs)
    print(f"refs listed: {stats['listed']}  max: {stats['maxnum']}  duplicate nums: {len(stats['dupnums'])}")
    print(f"unique cited: {stats['unique_cited']}  dangling: {stats['dangling']}")
    print(f"uncited: {stats['uncited']}")
    print(f"first-appearance ordering violations: {stats['violations']}  descents: {stats['first_bad']}")
    if not do_renumber:
        return
    # Renumber by first appearance
    order = []
    for m in re.finditer(r"\[(\d+(?:\s*[,-\u2013]\s*\d+)*)\]", body):
        for v in expand(m.group(1)):
            if v not in order:
                order.append(v)
    old2new = {v: i + 1 for i, v in enumerate(order)}
    uncited_old = [n for n, _ in refs if n not in old2new]

    def repl(m):
        nums = expand(m.group(1))
        return "[" + ",".join(str(old2new[n]) for n in nums) + "]"

    body2 = re.sub(r"\[(\d+(?:\s*[,-\u2013]\s*\d+)*)\]", repl, body)
    refmap = dict(refs)
    ordered = sorted(((old2new[n], refmap[n]) for n in refmap if n in old2new), key=lambda x: x[0])
    for n in uncited_old:  # keep genuinely uncited entries appended (flagged in audit)
        ordered.append((n, refmap[n]))

    def renum(line, new):
        m = re.match(r"^(\s*)\d+\.\s(.*)$", line)
        return f"{m.group(1)}{new}. {m.group(2)}" if m else line

    refs_out = "\n".join(renum(line, new) for new, (_, line) in enumerate(ordered, 1))
    open(path, "w", encoding="utf-8").write(body2 + sep + "\n" + refs_out + "\n")
    s2 = open(path, encoding="utf-8").read()
    b2, _, r2 = s2.partition(REF_HEADER)
    st2 = audit(b2, parse_refs(r2))
    rn = [int(re.match(r"^\s*(\d+)\.", l).group(1)) for l in r2.splitlines() if re.match(r"^\s*\d+\.", l)]
    print("renumbered -> violations:", st2["violations"], "| list sequential:",
          rn == list(range(1, len(rn) + 1)), "| listed:", len(rn))
    # REMINDER: rebuild docx/pdf from the md after renumbering.


if __name__ == "__main__":
    main()
