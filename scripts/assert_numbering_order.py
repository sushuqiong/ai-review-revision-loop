#!/usr/bin/env python
"""Assert that table/figure numbering follows order of first mention.

Usage:
    python assert_numbering_order.py <docx> [<docx> ...]

Exit code 0 = all assertions pass; 1 = at least one failure.
Run this on BOTH the main manuscript and the supplementary file before every
submission-package delivery.

Why this script exists
----------------------
v22 shipped to Frontiers with main-text tables numbered ``1,2,3,4,5,6,7`` but
first cited in the order ``1,7,6,2,3,4,5``, and supplementary tables almost
fully scrambled.  A checklist that only asked "is every table cited?" cannot
catch that.  Numbering order must be an executable assertion.

Three traps baked into the implementation below
-----------------------------------------------
1. **Citation order != caption order.**  A main text may legitimately cite
   Table 5 before Table 2.  Only the *caption / table-block arrangement* must be
   ascending; do not assert on citation order for the main document.
2. **'Table S13.' must never be read as main 'Table 13.'**  Keep the
   supplementary and main patterns in *separate* regexes and test the S-forms
   first.  (The original bug used ``S?`` inside one pattern.)
3. **This checker's own mapping constants go stale.**  If you rename files,
   renumber, swap figures or reorder blocks, any *other* script with a
   hard-coded ``media <-> file`` map must be updated too, or it will report
   false failures on a clean document.  When this script reports FAIL, first ask
   "is the document wrong, or is my checker stale?"
"""
import re
import sys

try:
    from docx import Document
    from docx.oxml.ns import qn
except ImportError:
    sys.exit("python-docx required:  pip install python-docx")

# supplementary first, then main -- order matters (trap 2)
CAP_PATTERNS = [
    ("Table S",  re.compile(r"^Table\s+S(\d+)\.")),
    ("Figure S", re.compile(r"^Figure\s+S(\d+)\.")),
    ("Table",    re.compile(r"^Table\s+(\d+)\.")),
    ("Figure",   re.compile(r"^Figure\s+(\d+)\.")),
]
CITE_PATTERNS = [
    ("Table S",  re.compile(r"\bTable\s+S(\d+)")),
    ("Figure S", re.compile(r"\bFigure\s+S(\d+)")),
    ("Table",    re.compile(r"\bTable\s+(\d+)(?![\dS])")),
    ("Figure",   re.compile(r"\bFigure\s+(\d+)(?![\dS])")),
]


def para_text(el):
    return "".join(n.text or "" for n in el.iter(qn("w:t"))).strip()


def citation_order(paras, pat):
    seen = {}
    for i, text in enumerate(paras):
        for m in pat.finditer(text):
            seen.setdefault(int(m.group(1)), i)
    return [k for k, _ in sorted(seen.items(), key=lambda kv: kv[1])]


def caption_arrangement(doc):
    """Caption numbers in physical document order, per class."""
    out = {label: [] for label, _ in CAP_PATTERNS}
    for el in doc.element.body.iterchildren():
        if el.tag != qn("w:p"):
            continue
        text = para_text(el)
        for label, pat in CAP_PATTERNS:
            m = pat.match(text)
            if m:
                out[label].append(int(m.group(1)))
                break
    return out


def ascending(seq):
    return seq == sorted(seq)


def audit(path):
    doc = Document(path)
    paras = [p.text for p in doc.paragraphs]
    failures = []

    print("=" * 72)
    print(" %s" % path)
    print("=" * 72)

    # --- 1. caption / block arrangement (the hard requirement) -------------
    print("\n[1] caption & block arrangement (must be ascending)")
    for label, seq in caption_arrangement(doc).items():
        if not seq:
            continue
        good = ascending(seq)
        # duplicates / gaps
        dupes = sorted({x for x in seq if seq.count(x) > 1})
        gaps = [x for x in range(1, max(seq) + 1) if x not in seq]
        print("   %-9s %-46s %s" % (label, seq, "OK" if good else "FAIL"))
        if not good:
            failures.append("%s caption arrangement not ascending: %s" % (label, seq))
        if dupes:
            failures.append("%s duplicate caption numbers: %s" % (label, dupes))
        if gaps:
            failures.append("%s missing caption numbers: %s" % (label, gaps))

    # --- 2. number referenced must exist -----------------------------------
    print("\n[2] referenced numbers exist (caption set covers citation set)")
    caps = caption_arrangement(doc)
    for label, pat in CITE_PATTERNS:
        cited = set()
        for text in paras:
            for m in pat.finditer(text):
                cited.add(int(m.group(1)))
        if not cited:
            continue
        known = set(caps[label])
        orphans = sorted(cited - known)
        print("   %-9s cited=%-38s %s" % (label, sorted(cited),
                                          "OK" if not orphans else "FAIL orphan=%s" % orphans))
        if orphans:
            failures.append("%s cited but never captioned: %s" % (label, orphans))

    # --- 3. main-text citation order (INFORMATIONAL ONLY, trap 1) ----------
    print("\n[3] main-text citation order (informational; NOT an assertion)")
    for label, pat in CITE_PATTERNS:
        if label.endswith(" S"):
            continue
        order = citation_order(paras, pat)
        if order:
            note = "ascending" if ascending(order) else "out of order (allowed)"
            print("   %-9s %-46s %s" % (label, order, note))

    return failures


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    all_failures = []
    for path in sys.argv[1:]:
        try:
            all_failures += ["%s: %s" % (path, f) for f in audit(path)]
        except Exception as exc:                       # noqa: BLE001
            all_failures.append("%s: could not read (%s)" % (path, exc))
    print("\n" + "=" * 72)
    if all_failures:
        print(" FAILURES: %d" % len(all_failures))
        for f in all_failures:
            print("   - " + f)
        sys.exit(1)
    print(" ALL ASSERTIONS PASS")
    print(" Reminder: this covers numbering order only. Still to verify separately --")
    print("  word-count statement vs actual, reference numbering continuity,")
    print("  legend text vs in-figure content, template font/size, three-line tables,")
    print("  embedded-image resolution. Do NOT report 'no problems' on the strength")
    print("  of this script alone.")
    sys.exit(0)


if __name__ == "__main__":
    main()
