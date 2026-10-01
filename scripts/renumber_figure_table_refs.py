#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Renumber figures/tables to FIRST-MENTION order (main + supplementary, all cross-refs).

Derived from the v22 remediation. The three traps this script exists to avoid:
  1. CYCLES. Plain sequential replace is unsafe: Table 1->1, 7->2, 6->3, 2->4 ... has
     cycles, so "Table 2" gets rewritten again after "Table 7" became "Table 2".
     Fix: two-phase sentinel substitution (mark to U+27E6..U+27E7, then strip).
  2. RANGE FORMS. "Tables 4-5" and generic "Tables S1-S13" behave differently:
     specific intervals map endpoint-wise then sort ascending; a GENERIC range
     (lo==1 and hi==old_max, meaning "all of them") must become 1..new_max, NOT be mapped.
  3. CONJUNCTIONS. "Tables 4 and 5" / "Tables 6, 7" - the second number is NOT preceded by
     the word "Table", so a naive `Tables?\\s+(\\d+)` regex silently leaves it stale.
  4. BLOCK REORDER. Insert blocks by iterating ASCENDING and calling anchor.addprevious(el)
     once per element. Using reversed() twice re-reverses and produces a descending file.

Usage:
  # 1) inspect only (prints old->new maps, changes nothing)
  python renumber_figure_table_refs.py --main Manuscript.docx --supp "Supplementary Materials.docx"
  # 2) apply (backs up both files first)
  python renumber_figure_table_refs.py --main Manuscript.docx --supp "Supplementary Materials.docx" --apply
  # 3) afterwards ALWAYS run scripts/check_figure_table_order.py
"""
import os
import re
import sys
import shutil
import argparse

L, R = "\u27e6", "\u27e7"          # sentinels

P_MAIN_T = r'\bTables?\s+(\d+)(?![\dS])'
P_SUPP_T = r'\bTables?\s+S(\d+)'
P_MAIN_F = r'\bFigures?\s+(\d+)(?![\dS])'
P_SUPP_F = r'\bFigures?\s+S(\d+)'

RE_CAP = re.compile(r'^(Table|Figure)\s+S?(\d+)\.')
RE_CONJ_T = re.compile(r'\bTables\s+(\d+)((?:\s*(?:and|,|&)\s*\d+)+)')


def load(path):
    from docx import Document
    return Document(path)


def first_mentions(doc, pat):
    out = {}
    for i, p in enumerate(doc.paragraphs):
        for m in re.finditer(pat, p.text):
            out.setdefault(int(m.group(1)), i)
    return out


def derive_maps(main_doc):
    """old -> new for each of the four classes, from main-text citation order."""
    maps = {}
    for key, pat in (("T", P_MAIN_T), ("TS", P_SUPP_T), ("F", P_MAIN_F), ("FS", P_SUPP_F)):
        fm = first_mentions(main_doc, pat)
        order = [k for k, _ in sorted(fm.items(), key=lambda kv: kv[1])]
        maps[key] = {old: new for new, old in enumerate(order, 1)}
    return maps


def _map_conjunctions(text, letter, m):
    """rewrite every number inside a conjunction group 'Tables 4 and 5'"""
    head, tail = m.group(1), m.group(2)

    def sub(mm):
        n = int(mm.group(1))
        return mm.group(0).replace(str(n), str(m.get(n, n)), 1)

    return "%s%s%s" % (letter, m.get(int(head), int(head)),
                       re.sub(r'(\d+)', lambda mm: str(m.get(int(mm.group(1)), int(mm.group(1)))), tail))


def _rw_ranges(text, m, old_max, new_max):
    """specific interval -> mapped endpoints sorted; generic 'all' -> 1..new_max"""
    lo, hi = int(m.group(1)), int(m.group(2))
    if lo == 1 and hi == old_max:
        return "Tables S1\u2013S%d" % new_max
    a, b = m.get(lo, lo), m.get(hi, hi)
    return "Tables S%d\u2013S%d" % (min(a, b), max(a, b))


def rewrite(text, maps, maxes):
    # --- supplementary tables ---
    m = maps["TS"]
    text = re.sub(r'\bTables\s+S(\d+)\s*[\u2013-]\s*S?(\d+)',
                  lambda mm: _rw_ranges(text, mm, maxes["TS_old"], maxes["TS_new"]), text)
    text = re.sub(r'\b(Tables)\s+S(\d+)', lambda mm: "%s S%s%d%s" % (mm.group(1), L, m.get(int(mm.group(2)), int(mm.group(2))), R), text)
    text = re.sub(r'\b(Table)\s+S(\d+)', lambda mm: "%s S%s%d%s" % (mm.group(1), L, m.get(int(mm.group(2)), int(mm.group(2))), R), text)
    # --- supplementary figures ---
    mf = maps["FS"]
    text = re.sub(r'\b(Figures)\s+S(\d+)', lambda mm: "%s S%s%d%s" % (mm.group(1), L, mf.get(int(mm.group(2)), int(mm.group(2))), R), text)
    text = re.sub(r'\b(Figure)\s+S(\d+)', lambda mm: "%s S%s%d%s" % (mm.group(1), L, mf.get(int(mm.group(2)), int(mm.group(2))), R), text)
    # --- main tables: conjunctions FIRST, then singular ---
    mt = maps["T"]
    text = RE_CONJ_T.sub(lambda mm: _map_conjunctions(text, mm.group(0)[:6], mm), text)
    text = re.sub(r'\b(Tables)\s+(\d+)(?![\dS])', lambda mm: "%s %s%d%s" % (mm.group(1), L, mt.get(int(mm.group(2)), int(mm.group(2))), R), text)
    text = re.sub(r'\b(Table)\s+(\d+)(?![\dS])', lambda mm: "%s %s%d%s" % (mm.group(1), L, mt.get(int(mm.group(2)), int(mm.group(2))), R), text)
    return text.replace(L, "").replace(R, "")


def renumber_doc(doc, maps, maxes, skip_captions=True):
    n = 0
    for p in doc.paragraphs:
        if skip_captions and RE_CAP.match(p.text.strip()):
            # caption's own number is rewritten separately by rewrite_captions()
            continue
        for r in p.runs:
            if r.text:
                t = rewrite(r.text, maps, maxes)
                if t != r.text:
                    r.text = t
                    n += 1
    for tbl in doc.tables:
        for tr in tbl.rows:
            for c in tr.cells:
                for p in c.paragraphs:
                    for r in p.runs:
                        if r.text:
                            t = rewrite(r.text, maps, maxes)
                            if t != r.text:
                                r.text = t
                                n += 1
    return n


def rewrite_captions(doc):
    """rewrite the number in caption paragraphs themselves"""
    n = 0
    for p in doc.paragraphs:
        s = p.text.strip()
        if not RE_CAP.match(s):
            continue
        for r in p.runs:
            m = re.match(r'^(Table|Figure)\s+S(\d+)\.', r.text)
            if m:
                kind, old = m.group(1), int(m.group(2))
                key = ("TS" if kind == "Table" else "FS")
                if key in doc._maps and old in doc._maps[key]:
                    r.text = re.sub(r'^Table\s+S\d+\.', 'Table S%d.' % doc._maps[key][old], r.text)
                    r.text = re.sub(r'^Figure\s+S\d+\.', 'Figure S%d.' % doc._maps[key][old], r.text)
                    n += 1
                break
    return n


def reorder_blocks(doc, kind):
    """move caption+body blocks so they appear in ascending order.

    The idiom matters: remove every block, then insert ASCENDING with
    anchor.addprevious(el) - one call per element. Do NOT use reversed() twice.
    """
    from docx.oxml.ns import qn
    body = doc.element.body
    els = list(body.iterchildren())
    blocks, cur = {}, None
    for el in els:
        if el.tag == qn('w:p'):
            t = "".join(n.text or "" for n in el.iter(qn('w:t'))).strip()
            m = RE_CAP.match(t)
            if m and m.group(1) == kind:
                cur = int(m.group(2))
                blocks[cur] = [el]
                continue
            if t.startswith("Supplementary"):
                cur = None
        if cur is not None:
            blocks[cur].append(el)
    keys = sorted(blocks)
    if keys != list(range(1, len(keys) + 1)):
        print("  !! %s blocks are not 1..N before reorder: %s" % (kind, keys))
    anchor = None
    for el in els:
        if el.tag == qn('w:p'):
            t = "".join(n.text or "" for n in el.iter(qn('w:t'))).strip()
            if t == "Supplementary Figures":
                anchor = el
                break
    for k in keys:
        for el in blocks[k]:
            body.remove(el)
    if kind == "Table" and anchor is not None:
        for k in keys:                      # ASCENDING
            for el in blocks[k]:
                anchor.addprevious(el)
    else:
        for k in keys:                      # append at end
            for el in blocks[k]:
                body.append(el)
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--main", required=True)
    ap.add_argument("--supp")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    ms = load(a.main)
    maps = derive_maps(ms)
    for k, lbl in (("T", "main Table"), ("TS", "Table S"), ("F", "main Figure"), ("FS", "Figure S")):
        print("%-12s %s" % (lbl, maps[k]))

    for key, old_key in (("TS", "TS"),):
        pass
    maxes = {
        "TS_old": max(maps["TS"]) if maps["TS"] else 0,
        "TS_new": len(maps["TS"]),
    }

    if not a.apply:
        print("\n(dry run - pass --apply to write)")
        return 0

    for path in [a.main] + ([a.supp] if a.supp else []):
        shutil.copy2(path, path + ".bak_renumber")
    ms._maps = maps
    n1 = renumber_doc(ms, maps, maxes, skip_captions=True)
    n2 = rewrite_captions(ms)
    ms.save(a.main)
    print("\n%s: %d ref runs, %d captions" % (os.path.basename(a.main), n1, n2))

    if a.supp:
        sp = load(a.supp)
        sp._maps = maps
        s1 = renumber_doc(sp, maps, maxes, skip_captions=True)
        s2 = rewrite_captions(sp)
        reorder_blocks(sp, "Table")
        reorder_blocks(sp, "Figure")
        sp.save(a.supp)
        print("%s: %d ref runs, %d captions, blocks reordered" % (os.path.basename(a.supp), s1, s2))

    print("\nnow run:  python scripts/check_figure_table_order.py \"%s\" \"%s\"" % (a.main, a.supp or ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
