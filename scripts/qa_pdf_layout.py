#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PDF figure/GA layout QA — exact, no OCR, no vision model needed.

Reads the PDF **text layer** (matplotlib/ggplot/Illustrator all emit real text spans), so it
sees each label's exact string, bbox, font size and colour. Far more reliable than OCR for
small type, and it catches the two failure modes OCR cannot: silently clipped labels and
duplicated drawing (same text painted twice at the same spot).

Checks
  1. out-of-bounds : any span bbox within TOL pt of the page edge
  2. overlap       : any two span bboxes intersecting by > AREA pt^2 (real text-on-text)
  3. min font size : any span smaller than MINPT pt (journal floor)
  4. missing text  : --expect TOKEN (repeatable) must appear in the page text

Usage
  python qa_pdf_layout.py FIG.pdf                     # all checks, min font 9.0
  python qa_pdf_layout.py FIG.pdf --min-font 8
  python qa_pdf_layout.py FIG.pdf --expect "0.377" --expect "FDR"
  python qa_pdf_layout.py FIG.pdf --dump              # print every span in reading order
  python qa_pdf_layout.py FOLDER/ --pattern "*.pdf"   # batch

Exit code 0 = clean, 1 = findings (so it can gate a build script).
"""
import argparse
import glob
import itertools
import os
import sys

import fitz  # PyMuPDF


def collect(page, tol):
    spans = []
    for blk in page.get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for s in line["spans"]:
                t = s["text"].strip()
                if t:
                    spans.append({
                        "t": t,
                        "b": fitz.Rect(s["bbox"]),
                        "size": round(s["size"], 1),
                        "color": "#%06x" % s["color"],
                        "font": s["font"],
                    })
    return spans


def check(path, min_font=9.0, tol=2.0, area=1.5, expect=(), dump=False, quiet=False):
    doc = fitz.open(path)
    name = os.path.basename(path)
    problems = []
    for pno, page in enumerate(doc, 1):
        W, H = page.rect.width, page.rect.height
        spans = collect(page, tol)

        oob = [s for s in spans
               if s["b"].x0 < tol or s["b"].y0 < tol or s["b"].x1 > W - tol or s["b"].y1 > H - tol]
        small = [s for s in spans if s["size"] < min_font]
        ov = []
        for a, b in itertools.combinations(spans, 2):
            inter = a["b"] & b["b"]
            if not inter.is_empty and inter.get_area() > area:
                ov.append((a, b, inter.get_area()))

        if not quiet:
            print("=" * 92)
            print("%s  p%d  %.0f x %.0f pt  (%.2f x %.2f cm)  |  spans %d  |  min font %.1f pt"
                  % (name, pno, W, H, W / 72 * 2.54, H / 72 * 2.54, len(spans),
                     min((s["size"] for s in spans), default=0)))
            print("   out-of-bounds : %d" % len(oob))
            for s in oob[:10]:
                print("      %-46s %s" % (s["t"][:46], [round(v, 1) for v in s["b"]]))
            print("   overlaps      : %d" % len(ov))
            for a, b, ar in ov[:10]:
                print("      (%.1f pt2) %r  <->  %r" % (ar, a["t"][:40], b["t"][:40]))
            print("   below %.1f pt  : %d" % (min_font, len(small)))
            for s in small[:10]:
                print("      %4.1f pt  %s" % (s["size"], s["t"][:60]))
            print("   fonts         : %s" % sorted({s["font"] for s in spans}))

        page_text = page.get_text()
        for tok in expect:
            if tok not in page_text:
                print("   MISSING EXPECTED TEXT: %r" % tok)
                problems.append("%s p%d: missing %r" % (name, pno, tok))

        if oob or ov or small:
            problems.append("%s p%d: oob=%d overlap=%d small=%d" % (name, pno, len(oob), len(ov), len(small)))

        if dump:
            print("   --- spans in reading order ---")
            for s in sorted(spans, key=lambda z: (round(-z["b"].y0 / 6), z["b"].x0)):
                print("      y%-6.0f x%-6.0f %4.1f  %s" % (s["b"].y0, s["b"].x0, s["size"], s["t"][:76]))
    doc.close()
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--min-font", type=float, default=9.0)
    ap.add_argument("--tol", type=float, default=2.0)
    ap.add_argument("--area", type=float, default=1.5)
    ap.add_argument("--expect", action="append", default=[])
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--pattern", default="*.pdf")
    a = ap.parse_args()

    if os.path.isdir(a.path):
        files = sorted(glob.glob(os.path.join(a.path, a.pattern)))
    else:
        files = [a.path]
    if not files:
        print("no PDFs found"); return 1

    allp = []
    for f in files:
        allp += check(f, a.min_font, a.tol, a.area, a.expect, a.dump)

    print("=" * 92)
    if allp:
        print("RESULT: %d finding(s)" % len(allp))
        for p in allp:
            print("   !!", p)
        return 1
    print("RESULT: clean (no out-of-bounds, no overlap, no text below %.1f pt)" % a.min_font)
    return 0


if __name__ == "__main__":
    sys.exit(main())
