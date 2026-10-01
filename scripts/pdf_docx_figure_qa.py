#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rendered-level QA for manuscript artefacts: figures (pixels), tables (three-line), PDFs (word boxes).

Why this exists: character-count heuristics mislead. Crop/bleed is provable at pixel level; text overflow and
collision are provable from the rendered PDF's word boxes; three-line table style is provable from the XML.

Usage:
    python pdf_docx_figure_qa.py --figures 02_figures --docx 01_manuscript/Paper.docx \
        --tables 03_tables/Tables.docx --pdf 01_manuscript/Paper.pdf 03_tables/SI.pdf [--tesseract PATH]

Exit code: 0 if no FAIL, 1 otherwise. Prints a per-check line and a summary. Optional deps are detected:
Pillow (figures), python-docx (tables), PyMuPDF (PDF word-box checks), Tesseract (legibility only).
"""
import argparse, os, re, shutil, subprocess, sys, tempfile

FAILS, WARNS, OKS = [], [], []
def rec(area, check, status, detail=""):
    line = f"[{status:4s}] {area}: {check}" + (f" -> {detail}" if detail else "")
    print(line)
    {"OK": OKS, "WARN": WARNS, "FAIL": FAILS}[status].append(f"{area}: {check}" + (f" ({detail})" if detail else ""))

# ---------------------------------------------------------------- figures
def qa_figures(figdir, tesseract=None):
    try:
        from PIL import Image, ImageStat
    except Exception:
        print("  (Pillow missing: figure pixel checks skipped)"); return
    exts = (".png", ".tif", ".tiff", ".jpg")
    files = sorted(f for f in os.listdir(figdir) if f.lower().endswith(exts)) if os.path.isdir(figdir) else []
    if not files:
        print("  (no figure files found)"); return
    tmp = os.path.join(tempfile.gettempdir(), "qa_ocr"); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    def ocr_words(path):
        if not tesseract:
            return []
        base = os.path.join(tmp, "t"); 
        try:
            Image.open(path).convert("L").save(base + ".png")
        except Exception:
            return []
        env = dict(os.environ); env.setdefault("TESSDATA_PREFIX", os.path.dirname(os.path.join(tesseract, "")) or "")
        r = subprocess.run([tesseract, base + ".png", "stdout", "--psm", "11"], capture_output=True, text=True, env=env)
        return [w for w in re.split(r"\s+", (r.stdout or "")) if w.strip()]
    for fn in files:
        p = os.path.join(figdir, fn)
        im = Image.open(p).convert("L"); w, h = im.size
        dpi6 = w / 6.2; hin = h / dpi6
        rec("figure", f"{fn} geometry", "OK" if hin <= 24 else "WARN",
            f"{w}x{h}px -> 6.2 x {hin:.1f} in at {dpi6:.0f} dpi")
        px = im.load(); band = 2; border = 0
        for x in range(w):
            for y in list(range(band)) + list(range(h - band, h)):
                if px[x, y] < 128: border += 1
        for y in range(h):
            for x in list(range(band)) + list(range(w - band, w)):
                if px[x, y] < 128: border += 1
        rec("figure", f"{fn} crop/bleed", "OK" if border == 0 else "FAIL", f"ink pixels in the outer band: {border}")
        dark = sum(1 for v in im.getdata() if v < 60) / (w * h)
        rec("figure", f"{fn} ink density", "OK" if 0.002 < dark < 0.25 else "WARN", f"dark fraction {dark:.3f}")
        if tesseract:
            small = im.resize((max(1, w // 2), max(1, h // 2))); sp = os.path.join(tmp, fn); small.save(sp)
            n1, n2 = len(ocr_words(p)), len(ocr_words(sp))
            ratio = n2 / max(1, n1) if n1 else 1.0
            rec("figure", f"{fn} legible at 50%", "OK" if ratio >= 0.75 else "WARN", f"OCR words {n2}/{n1} = {ratio:.2f}")
            words = " ".join(ocr_words(p)).lower()
            bad = [t for t in ("legend", "figure 1", "figure 2", "figure 3", "figure 4", "table")
                   if re.search(r"\b" + re.escape(t) + r"\b", words)]
            rec("figure", f"{fn} no in-figure legend or title", "OK" if not bad else "FAIL", f"found {bad}" if bad else "")
    shutil.rmtree(tmp, ignore_errors=True)

# ---------------------------------------------------------------- tables
EDGES = ("top", "left", "bottom", "right", "insideH", "insideV")
def qa_docx(path, label):
    try:
        from docx import Document
        from docx.oxml.ns import qn
    except Exception:
        print("  (python-docx missing: table checks skipped)"); return
    if not os.path.exists(path):
        rec("tables", f"{label} exists", "FAIL", "missing"); return
    d = Document(path)
    if not d.tables:
        rec("tables", f"{label} tables present", "WARN", "no tables in this document"); return
    issues = []
    for ti, t in enumerate(d.tables, 1):
        cols, rows = len(t.columns), len(t.rows)
        def edges_of(cell):
            out = {}
            tcPr = cell._tc.tcPr
            src = None
            if tcPr is not None:
                src = tcPr.find(qn("w:tcBorders"))
            if src is None:
                src = t._tbl.tblPr.find(qn("w:tblBorders"))
            if src is None:
                return out
            for e in EDGES:
                el = src.find(qn(f"w:{e}"))
                out[e] = el.get(qn("w:val")) if el is not None else "nil"
            return out
        vline = mid = 0
        for r in range(rows):
            b = edges_of(t.cell(r, 0))
            vline += sum(1 for e in ("left", "right", "insideV") if b.get(e) == "single")
            if 0 < r < rows - 1 and b.get("bottom") == "single": mid += 1
        empty_header = sum(1 for c in t.rows[0].cells if not c.text.strip())
        junk = sum(1 for r in t.rows for c in r.cells if c.text.strip().lower() in ("nan", "none", "na", "#n/a", "null"))
        longest = max((len(c.text) for r in t.rows for c in r.cells), default=0)
        if vline: issues.append(f"table {ti}: {vline} vertical rule(s)")
        if mid: issues.append(f"table {ti}: {mid} interior horizontal rule(s)")
        if empty_header: issues.append(f"table {ti}: {empty_header} empty header cell(s)")
        if junk: issues.append(f"table {ti}: {junk} nan/None cell(s)")
        if longest > 400: issues.append(f"table {ti}: longest cell {longest} chars (check the rendered page)")
    rec("tables", f"{label}: {len(d.tables)} tables", "OK" if not issues else "WARN", "; ".join(issues[:8]))

# ---------------------------------------------------------------- PDFs
def qa_pdf(path, label):
    try:
        import fitz
    except Exception:
        print("  (PyMuPDF missing: rendered-page checks skipped)"); return
    if not os.path.exists(path):
        rec("pdf", f"{label} exists", "FAIL", "missing"); return
    doc = fitz.open(path); overflow = []; overlap = []; words_total = 0
    for pno, page in enumerate(doc, 1):
        W, H = page.rect.width, page.rect.height
        ws = page.get_text("words"); words_total += len(ws)
        for x0, y0, x1, y1, txt, *_ in ws:
            if x1 > W - 1 or y1 > H - 1 or x0 < 1 or y0 < 1:
                overflow.append((pno, str(txt)[:30]))
        for i in range(len(ws)):
            ax0, ay0, ax1, ay1 = ws[i][:4]
            for j in range(i + 1, min(i + 6, len(ws))):
                bx0, by0, bx1, by1 = ws[j][:4]
                ix = min(ax1, bx1) - max(ax0, bx0); iy = min(ay1, by1) - max(ay0, by0)
                if ix > 2 and iy > 2:
                    a = (ax1 - ax0) * (ay1 - ay0); b = (bx1 - bx0) * (by1 - by0)
                    if (ix * iy) / max(1e-6, min(a, b)) > 0.45:
                        overlap.append((pno, str(ws[i][4])[:18], str(ws[j][4])[:18]))
    doc.close()
    rec("pdf", f"{label} word boxes ({words_total} words)",
        "OK" if not overflow else "FAIL", f"{len(overflow)} overflowing word(s): {overflow[:5]}")
    rec("pdf", f"{label} text collision", "OK" if not overlap else "FAIL",
        f"{len(overlap)} colliding pair(s): {overlap[:5]}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--figures"); ap.add_argument("--docx", action="append", default=[])
    ap.add_argument("--tables", action="append", default=[]); ap.add_argument("--pdf", nargs="*", default=[])
    ap.add_argument("--tesseract", default=None, help="path to tesseract binary (optional, for legibility)")
    a = ap.parse_args()
    if a.figures: print("=== figures ==="); qa_figures(a.figures, a.tesseract)
    if a.docx or a.tables:
        print("=== tables ===")
        for p in (a.docx or []) + (a.tables or []): qa_docx(p, os.path.basename(p))
    if a.pdf:
        print("=== rendered pages ===")
        for p in a.pdf: qa_pdf(p, os.path.basename(p))
    print(f"\n=== summary: {len(OKS)} OK | {len(WARNS)} WARN | {len(FAILS)} FAIL ===")
    for f in FAILS: print("  FAIL:", f)
    for w in WARNS: print("  WARN:", w)
    sys.exit(1 if FAILS else 0)

if __name__ == "__main__":
    main()
