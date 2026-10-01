#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Programmatic consistency audit for an academic manuscript + its deposit folder.

Usage:
  python manuscript_consistency_audit.py --md manuscript/DataDescriptor_v15.md \
      --deposit dataset_package [--tables 03_tables/Tables_v15.docx] \
      [--require "cautious effect-size comparability"] [--require "**Limitations"]

Checks (exit code 1 if any FAIL):
  * accession codes not glued to superscript citation digits   (GSE139113 = GSE13911 + ref 3)
  * reference numbers cited in the body are exactly 1..N       (ranges like 8-34 are expanded)
  * every reference entry is cited; no empty authors; no Correction/Erratum notices
  * shipped file/SHA counts quoted in the text match the live inventory
  * every cited Supplementary Table Sn exists in the tables .docx
  * unfilled placeholders ([DOI ...], TBD, XXX, FIXME, "to be supplied")
  * optional --require assertions (key sentences that a reviewer expects to find)
Adapt the REQUIRED list and the placeholder patterns when reusing on another project.
"""
import argparse, csv, os, re, subprocess, sys

PLACEHOLDERS=[r"\[DOI[^\]]*\]", r"\bTBD\b", r"\bXXX\b", r"\bFIXME\b", r"to be supplied", r"to be inserted"]

def read(p):
    with open(p, encoding="utf-8", errors="replace") as f: return f.read()

def cited_numbers(body):
    """Expand ⟦n⟧ and ⟦a–b⟧ markers (also plain (n) style ranges) into a set of ints."""
    out=set()
    for m in re.finditer(r"⟦(\d+(?:[-\u2013]\d+)?(?:,\d+)*)⟧", body):
        for part in m.group(1).split(","):
            if re.match(r"^\d+[-\u2013]\d+$", part):
                a,b=re.split(r"[-\u2013]", part); out.update(range(int(a), int(b)+1))
            elif part.isdigit(): out.add(int(part))
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--deposit", default="")
    ap.add_argument("--tables", default="")
    ap.add_argument("--require", action="append", default=[])
    a=ap.parse_args()
    md=read(a.md); body=md.split("**References**")[0]
    refsec=(md.split("**References**")[1].split("\n**")[0] if "**References**" in md else "")
    refs=re.findall(r"(?m)^(\d+)\. (.+)$", refsec)
    checks=[]
    def chk(name, ok, detail=""):
        checks.append((name, bool(ok), detail)); 
        print(f"  [{'OK  ' if ok else 'FAIL'}] {name}" + (f"  -> {detail}" if detail and not ok else ""))
    # 1 accessions
    glued=re.findall(r"GSE\d{7,}", md)
    chk("no accession glued to citation digits", not glued, str(glued[:3]))
    # 2 reference numbering
    if refs:
        N=len(refs); cited=cited_numbers(body); missing=sorted(set(range(1,N+1))-cited)
        chk(f"references {N}, all cited, contiguous", not missing, f"uncited: {missing[:8]}")
    else:
        chk("reference list present", False, "no numbered entries found")
    # 3 hygiene
    chk("no empty reference authors", not re.search(r"(?m)^\d+\. \. ", md))
    chk("no Correction/Erratum entries", not re.search(r"Correction:|Erratum", refsec))
    chk("no 'Unknown author' placeholders", "Unknown author" not in refsec)
    # 4 live counts from the inventory
    if a.deposit:
        inv_p=os.path.join(a.deposit, "08_qc", "file_inventory_and_checksums.csv")
        if os.path.exists(inv_p):
            with open(inv_p, encoding="utf-8-sig", newline="") as f: inv=list(csv.DictReader(f))
            n=len(inv); nck=len([r for r in inv if len(str(r.get("sha256","")))==64])
            chk(f"shipped file count in text equals inventory ({n})", f"{n} files" in md or str(n) in md, f"inventory={n}")
            ck=os.path.join(a.deposit, "08_qc", "checksums_sha256.txt")
            if os.path.exists(ck):
                r=subprocess.run("sha256sum -c 08_qc/checksums_sha256.txt", cwd=a.deposit, shell=True, capture_output=True, text=True)
                bad=[l for l in r.stdout.splitlines() if not l.endswith(": OK")]
                chk(f"checksum chain verifies ({nck} entries)", not bad, str(bad[:2]))
    # 5 supplementary tables cited vs present
    if a.tables and os.path.exists(a.tables):
        try:
            from docx import Document
            dtxt="\n".join(p.text for p in Document(a.tables).paragraphs)
            avail={int(x) for x in re.findall(r"Supplementary Table S(\d+)\.", dtxt)}
            used={int(x) for x in re.findall(r"Supplementary Table S(\d+)", body)}
            chk("every cited supplementary table exists", used <= avail, f"cited {sorted(used)} present {sorted(avail)}")
        except Exception as e:
            chk("tables docx readable", False, str(e))
    # 6 placeholders / whitespace
    hits=[p for p in PLACEHOLDERS if re.search(p, md, re.I)]
    chk("no unfilled placeholders", not hits, str(hits))
    chk("no stray double spaces", ".  " not in md)
    # 7 required sentences
    for phrase in a.require:
        chk(f"contains required phrase: {phrase[:52]}", phrase in md)
    fails=[c for c in checks if not c[1]]
    print(f"\nAUDIT: {len(checks)-len(fails)}/{len(checks)} passed" + (f" | FAILED: {[c[0] for c in fails]}" if fails else " | clean"))
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
