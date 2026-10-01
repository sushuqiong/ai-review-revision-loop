# -*- coding: utf-8 -*-
"""Abbreviation audit for a manuscript + knapsack answer for submission fields with a char limit.

Run with the interpreter that has python-docx (this machine: D:/ProgramData/python.exe).

    python abbrev_audit.py Manuscript.docx                       # audit: counts + definition check
    python abbrev_audit.py Manuscript.docx --limit 200           # + best answers that fit the limit
    python abbrev_audit.py Manuscript.docx --dump-defs d.json    # write guessed defs, edit, re-run
    python abbrev_audit.py Manuscript.docx --defs d.json --limit 200

Counting is whole-token and split body/legends on purpose — see
references/submission-abbreviation-and-form-fields.md for why.
"""
import argparse, collections, json, os, re

LATIN = {"eg", "ie", "vs", "etc", "al", "et"}


def read_paras(path):
    from docx import Document
    return [p.text for p in Document(path).paragraphs]


def split_body_legends(paras):
    for i, t in enumerate(paras):
        if t.strip().lower() in ("references", "reference list"):
            return "\n".join(paras[:i]), "\n".join(paras[i:])
    return "\n".join(paras), ""


def flat(s):
    return re.sub(r"\s+", " ", s)


def count(ab, hay):
    return len(re.findall(r"(?<![A-Za-z0-9\-])" + re.escape(ab) + r"(?![A-Za-z0-9])", hay))


def candidates(all_text, min_total):
    tok = collections.Counter()
    for t in re.findall(r"(?<![A-Za-z0-9\-])[A-Za-z][A-Za-z0-9\-]{1,14}(?![A-Za-z0-9])", all_text):
        if re.search(r"[A-Z]{2,}", t) or re.match(r"^[A-Za-z]+-\d", t) or re.match(r"^[A-Z][a-z]+-[A-Z]", t):
            tok[t] += 1
    out = []
    for t, n in tok.items():
        if n < min_total or t.lower() in LATIN:
            continue
        if re.fullmatch(r"[IVX]+", t):          # roman numerals (Phase II / III)
            continue
        if re.fullmatch(r"[A-Z]{2,}\d+", t):    # GEO / dataset accessions (GSE84044, ...)
            continue
        out.append((t, n))
    return sorted(out, key=lambda z: -z[1])


def guess_definition(ab, all_text):
    best = ""
    for m in re.finditer(r"([A-Za-z][A-Za-z0-9 ,\-/&\+']{3,90}?)\s*\(" + re.escape(ab) + r"\)", all_text):
        cand = re.sub(r"^.*?[.;:]\s*", "", m.group(1).strip())
        cand = re.sub(r"^(and|the|of|with|to|in|for|a|an|using|including|such as)\s+", "", cand, flags=re.I)
        if len(cand) > len(best):
            best = cand
    for m in re.finditer(r"\(" + re.escape(ab) + r",\s*([^)]{3,70})\)", all_text):
        if len(m.group(1)) > len(best):
            best = m.group(1).strip()
    return best


def spelled_out(defn, all_text):
    if not defn:
        return "?"
    words = defn.split()
    probe = " ".join(words[:2]) if len(words) > 1 else words[0]
    return "yes" if re.search(re.escape(probe), all_text, re.I) else "NOT SPELLED OUT"


def render(abbrs, rows):
    """'; ' joined 'ABBR:expansion', preserving the row order"""
    ex = {ab: d for ab, n, d in rows}
    return "; ".join("%s:%s" % (ab, ex[ab]) for ab, n, d in rows if ab in abbrs)


def knapsack(rows, limit):
    """returns (max-coverage string, n items, max-items string, n items)"""
    def cost(ab, d):
        return len(ab) + 1 + len(d) + 2          # '; ' separator included

    def solve(score):
        best = {0: (0, frozenset())}
        for ab, n, d in rows:
            c = cost(ab, d)
            nb = dict(best)
            for used, (val, sel) in best.items():
                if used + c <= limit:
                    cand = (val + score(ab, n), sel | {ab})
                    if used + c not in nb or nb[used + c][0] < cand[0]:
                        nb[used + c] = cand
            best = nb
        k = max(best, key=lambda x: best[x][0])
        return best[k][1]

    cov = solve(lambda ab, n: n)                 # maximise occurrences covered
    many = solve(lambda ab, n: 1)                # maximise number of entries
    return render(cov, rows), len(cov), render(many, rows), len(many)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--min", type=int, default=3, help="minimum occurrences (journal says 3)")
    ap.add_argument("--limit", type=int, default=0, help="character limit of the submission field")
    ap.add_argument("--defs", help="JSON {ABBR: expansion} used instead of the auto-guess")
    ap.add_argument("--dump-defs", help="write the auto-guessed definitions to this JSON for curation")
    a = ap.parse_args()

    body, leg = split_body_legends(read_paras(a.docx))
    B, L, A = flat(body), flat(leg), flat(body + " " + leg)
    cands = candidates(A, a.min)

    defs = {}
    if a.defs and os.path.exists(a.defs):
        defs = json.load(open(a.defs, encoding="utf-8"))
    else:
        defs = {ab: guess_definition(ab, A) for ab, n in cands}

    print("%-12s %5s %8s %6s  %-34s %s" % ("ABBR", "body", "legends", "total", "expansion", "spelled out?"))
    print("-" * 108)
    rows = []
    for ab, n in cands:
        d = defs.get(ab, "")
        print("%-12s %5d %8d %6d  %-34s %s" % (ab, count(ab, B), count(ab, L), count(ab, A),
                                               d[:34], spelled_out(d, A)))
        if d:
            rows.append((ab, count(ab, A), d))
    if not a.defs:
        print("\nNOTE: expansions are AUTO-GUESSED. Read them, fix them, then --dump-defs and re-run.")

    if a.dump_defs:
        json.dump({ab: d for ab, n, d in rows}, open(a.dump_defs, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("wrote", a.dump_defs)

    full = render({ab for ab, n, d in rows}, rows)
    if a.limit:
        cov, k1, many, k2 = knapsack(rows, a.limit)
        print("\n" + "=" * 108)
        print("MAX OCCURRENCES COVERED  (%d chars, %d entries):\n%s" % (len(cov), k1, cov))
        print("\nMAX ENTRIES  (%d chars, %d entries):\n%s" % (len(many), k2, many))
    print("\nFULL LIST (%d chars, %d entries) — for a cover letter or an unlimited field:\n%s"
          % (len(full), len(rows), full))


if __name__ == "__main__":
    main()
