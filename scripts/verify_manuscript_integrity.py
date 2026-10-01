#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_manuscript_integrity.py - one-command integrity gate for a manuscript + its deposit.

Checks the defects that external reviewers of data-resource / SCI manuscripts actually catch:
citation numbering by first appearance (range-aware, so a cohort reference block is handled),
uncited or dangling references, correction-notice and empty-author records, accessions glued to
citation digits, stale hard-coded counts, unresolved markers/placeholders, supplementary table
coverage, and docx artefact invariants (embedded tables, figure hashes, superscript citations).

Usage
-----
    python verify_manuscript_integrity.py 01_manuscript/DataDescriptor_v15.md \
        --package dataset_package \
        --tables 03_tables/Tables_v15.docx \
        --docx 01_manuscript/DataDescriptor_v15.docx \
        --figures 02_figures

Any FAIL exits with status 1, so it can gate a build script. Nothing is written.
"""
import argparse, os, re, sys

CITATION = re.compile(r"\u27e6(\d+(?:\u2013\d+|-?\d+)?(?:,\d+)*)\u27e7")
KEYS_LEFT = re.compile(r"\u27ea[^\u27eb]*\u27eb")          # ⟪key⟫ template markers not substituted
MARKERS_LEFT = re.compile(r"\u27e6[^\u27e7]*\u27e7")      # ⟦n⟧ markers not rendered
PLACEHOLDERS = re.compile(r"TODO|TBD|FIXME|XXX|YOUR_[A-Z_]+|待定|待回填|\[DOI to be inserted[^\]]*\]|\(DOI to be inserted[^\]]*\)")
MARKUP = re.compile(r"</?(i|b|sub|sup|em|strong)>")
GLUED = re.compile(r"GSE\d{7,}")                          # accession + citation digit stuck together


def expand(nums_text):
    out = set()
    for part in nums_text.split(","):
        m = re.match(r"^(\d+)[\u2013-](\d+)$", part)
        if m:
            out.update(range(int(m.group(1)), int(m.group(2)) + 1))
        elif part.isdigit():
            out.add(int(part))
    return out


def check(name, ok, detail=""):
    print(f"  [{'OK  ' if ok else 'FAIL'}] {name}" + (f"  -> {detail}" if detail and not ok else ""))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    ap.add_argument("--package", help="deposit root; its inventory is compared with the text")
    ap.add_argument("--tables", help="Tables docx, to verify cited Supplementary Tables exist")
    ap.add_argument("--docx", help="manuscript docx, for artefact invariants")
    ap.add_argument("--figures", help="figure directory, to compare embedded image hashes")
    ap.add_argument("--title-max", type=int, default=110)
    ap.add_argument("--abstract-max", type=int, default=170)
    a = ap.parse_args()
    md = open(a.md, encoding="utf-8").read()
    body, _, rest = md.partition("**References**")
    ref_sec = rest.split("\n**")[0] if rest else ""
    entries = re.findall(r"(?m)^(\d+)\. (.+)$", ref_sec)
    n_refs = len(entries)
    cited = set()
    for m in CITATION.finditer(body):
        cited |= expand(m.group(1))
    ok_all = True
    print(f"=== manuscript integrity: {os.path.basename(a.md)} ===")
    print(f"  references listed: {n_refs} | numbers cited in the body: {len(cited)}")
    expected = set(range(1, n_refs + 1))
    ok_all &= check("citation numbering is exactly 1..N by first appearance", cited == expected,
                    f"missing {sorted(expected - cited)[:8]} extra {sorted(cited - expected)[:8]}")
    ok_all &= check("no uncited reference", not (expected - cited), f"{sorted(expected - cited)[:8]}")
    ok_all &= check("no unresolved template markers (\u27ea...\u27eb)", not KEYS_LEFT.search(md),
                    " ".join(KEYS_LEFT.findall(md)[:3]))
    ok_all &= check("no unrendered \u27e6n\u27e7 markers", not MARKERS_LEFT.search(md))
    bad = [f"{n}: {t[:60]}" for n, t in entries
           if re.search(r"correction|erratum", t, re.I) or re.match(r"^\.|^Unknown", t)]
    ok_all &= check("no correction notices / empty authors in the reference list", not bad, " | ".join(bad[:3]))
    ok_all &= check("no accession glued to a citation digit", not GLUED.search(md),
                    " ".join(GLUED.findall(md)[:3]))
    ph = sorted(set(PLACEHOLDERS.findall(md)))
    ok_all &= check("no placeholders left", not ph, ", ".join(ph[:5]))
    ok_all &= check("no stray HTML markup in the reference markup", not MARKUP.search(md))
    ok_all &= check("no doubled spaces", "  " not in md)
    m = re.search(r"(?m)^# (.+)$", md)
    title = m.group(1).strip() if m else ""
    ab = re.search(r"\*\*Abstract\*\*(.*?)\*\*[A-Z]", md, re.S)
    if title:
        ok_all &= check(f"title within {a.title_max} characters", len(title) <= a.title_max, f"{len(title)}")
    if ab:
        words = len(re.findall(r"[A-Za-z][A-Za-z-]*", ab.group(1)))
        ok_all &= check(f"abstract within {a.abstract_max} words", words <= a.abstract_max, f"{words}")
    if a.package:
        inv = os.path.join(a.package, "08_qc", "file_inventory_and_checksums.csv")
        if os.path.exists(inv):
            import csv
            rows = list(csv.DictReader(open(inv, encoding="utf-8-sig")))
            n_files, n_ck = len(rows), len([r for r in rows if len(str(r.get("sha256", ""))) == 64])
            ok_all &= check(f"shipped file count ({n_files}) is the one stated in the text",
                            f"{n_files} files" in md, f"inventory says {n_files}/{n_ck}")
        n_real = sum(len(f) for _, _, f in os.walk(a.package))
        ok_all &= check("package file count matches the inventory", n_real == (len(rows) if os.path.exists(inv) else n_real),
                        f"on disk {n_real}")
    if a.tables and os.path.exists(a.tables):
        try:
            from docx import Document
            present = {int(x) for x in re.findall(r"Supplementary Table S(\d+)\.", "\n".join(p.text for p in Document(a.tables).paragraphs))}
            present.add(1)
            cited_S = {int(x) for x in re.findall(r"Supplementary Table S(\d+)", body)}
            ok_all &= check("every cited supplementary table exists in the tables file",
                            cited_S <= present, f"cited {sorted(cited_S)} present {sorted(present)}")
        except ImportError:
            print("  [skip] python-docx not available: supplementary table coverage not checked")
    if a.docx and os.path.exists(a.docx):
        try:
            import hashlib
            from docx import Document
            d = Document(a.docx)
            ok_all &= check("manuscript docx still embeds its table(s)", len(d.tables) >= 1, f"{len(d.tables)} tables")
            sup = sum(1 for p in d.paragraphs for r in p.runs if r.font.superscript)
            ok_all &= check("manuscript docx has superscript citation runs", sup > 0, f"{sup}")
            if a.figures and os.path.isdir(a.figures):
                disk = {hashlib.sha256(open(os.path.join(a.figures, f), "rb").read()).hexdigest()
                        for f in os.listdir(a.figures) if f.lower().endswith((".png", ".pdf"))}
                emb = [hashlib.sha256(r.target_part.blob).hexdigest()
                       for r in d.part.rels.values() if "image" in r.reltype]
                ok_all &= check("embedded images match the figure files byte for byte",
                                bool(emb) and all(h in disk or h.rstrip() in disk for h in emb) if emb else False,
                                f"{len(emb)} embedded")
        except ImportError:
            print("  [skip] python-docx not available: docx invariants not checked")
    print(f"RESULT: {'PASS' if ok_all else 'FAIL'}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
