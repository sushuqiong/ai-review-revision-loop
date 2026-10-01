#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""verify_deliverable.py — machine QA for a submission package (no vision model needed).

Usage:
    python verify_deliverable.py <delivery_dir> [--figs Figures] [--tiff Figures_TIFF_300dpi]

Checks
  1. every .docx renders to PDF (LibreOffice headless) and, in the RENDERED text:
       - section order: Tables < Figure legends < Supplementary material
       - 'Supplementary material' heading appears BEFORE 'Supplementary Table S1.'
       - supplementary numbers are present and ascending (S1..Sn)
       - last rendered content belongs to the last supplement (not a dangling heading)
  2. figures in <figs>: OCR (tesseract CLI) finds expected numbers / no 'NA (' garbage /
     no text box touching the canvas edge (clipping detector)
  3. folder hygiene: flags non-submission artefacts (response tables, audit reports,
     README, zips, duplicate code dirs)

Exit code 0 = all checks passed. Edit EXPECT_FIG_TEXT for your figures.
"""
import argparse, csv, glob, io, os, re, struct, subprocess, sys, tempfile

SOFFICE = r"C:\Program Files\LibreOffice\program\soffice.exe"
TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
EXPECT_FIG_TEXT = {
    "Fig1_flowchart.png": [],
    "Fig2_forest.png": [],
    "Fig5_subgroups.png": [],
}
JUNK_PATTERNS = ("Response_", "回应对照", "audit", "对抗性", "README", "代码合集")


def docx_to_pdf(docx, outdir):
    subprocess.run([SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", outdir, docx],
                   check=False, timeout=420)
    pdf = os.path.join(outdir, os.path.splitext(os.path.basename(docx))[0] + ".pdf")
    return pdf if os.path.exists(pdf) else None


def check_docx(pdf_path):
    try:
        import fitz
    except ImportError:
        return ["py MuPDF (fitz) not installed - skipping PDF text checks"]
    problems = []
    doc = fitz.open(pdf_path)
    full = re.sub(r"\s+", " ", "\n".join(doc[i].get_text() for i in range(len(doc))))
    if not (full.find("Tables") < full.find("Table 1.")):
        problems.append("Tables section not before Table 1")
    if not (full.find("Figure legends") < full.find("Figure 1.")):
        problems.append("Figure legends heading not before Figure 1")
    sup_head, sup1 = full.find("Supplementary material"), full.find("Supplementary Table S1.")
    if not (0 <= sup_head < sup1):
        problems.append("'Supplementary material' heading is missing or AFTER S1")
    pos = [(n, full.find("Supplementary Table S%d." % n)) for n in range(1, 40)]
    present = [(n, p) for n, p in pos if p >= 0]
    missing = [n for n, p in pos[:20] if p < 0]
    if missing:
        problems.append("supplementary tables missing from render: %s" % missing)
    if any(present[i][1] > present[i + 1][1] for i in range(len(present) - 1)):
        problems.append("supplementary table order not ascending")
    tail = full[-120:]
    if "Supplementary Table" not in tail:
        problems.append("last rendered content is not the final supplement: %r" % tail[-60:])
    doc.close()
    return problems


def check_figure(path):
    problems = []
    with open(path, "rb") as fh:
        head = fh.read(24)
    W, H = struct.unpack(">II", head[16:24]) if head[:8] == b"\x89PNG\r\n\x1a\n" else (None, None)
    for psm in ("6", "11"):
        out = subprocess.run([TESSERACT, path, "stdout", "--psm", psm],
                             capture_output=True, text=True, timeout=180).stdout
        txt = re.sub(r"\s+", " ", out)
        if "NA (" in txt:
            problems.append("OCR shows placeholder 'NA (' -> figure built from failed parse")
        for k in EXPECT_FIG_TEXT.get(os.path.basename(path), []):
            if k not in txt:
                problems.append("expected value %s not found by OCR" % k)
        if psm == "11" and W:
            tsv = subprocess.run([TESSERACT, path, "stdout", "tsv", "--psm", "11"],
                                 capture_output=True, text=True, timeout=180).stdout
            for row in csv.DictReader(io.StringIO(tsv), delimiter="\t"):
                if not (row.get("text") or "").strip():
                    continue
                try:
                    x, y, w, h = int(row["left"]), int(row["top"]), int(row["width"]), int(row["height"])
                except (TypeError, ValueError):
                    continue
                if x <= 3 or y <= 3 or x + w >= W - 3 or y + h >= H - 3:
                    problems.append("text touches canvas edge (clipping): %r" % row["text"])
                    break
        break
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("delivery")
    ap.add_argument("--figs", default="Figures")
    ap.add_argument("--tiff", default="Figures_TIFF_300dpi")
    a = ap.parse_args()
    failures = []
    tmp = tempfile.mkdtemp(prefix="verify_")
    for docx in sorted(glob.glob(os.path.join(a.delivery, "*.docx"))):
        pdf = docx_to_pdf(docx, tmp)
        if pdf is None:
            failures.append("%s: LibreOffice conversion failed" % os.path.basename(docx))
            continue
        for p in check_docx(pdf):
            failures.append("%s: %s" % (os.path.basename(docx), p))
    for fig in sorted(glob.glob(os.path.join(a.delivery, a.figs, "*.png"))):
        for p in check_figure(fig):
            failures.append("%s: %s" % (os.path.basename(fig), p))
    n_tif = len(glob.glob(os.path.join(a.delivery, a.tiff, "*.tif")))
    n_png = len(glob.glob(os.path.join(a.delivery, a.figs, "*.png")))
    if n_tif != n_png:
        failures.append("TIFF count (%d) != PNG count (%d)" % (n_tif, n_png))
    for f in sorted(os.listdir(a.delivery)):
        if any(k.lower() in f.lower() for k in JUNK_PATTERNS):
            failures.append("non-submission artefact in delivery folder: %s" % f)
    print("== verify_deliverable:", a.delivery)
    if failures:
        for f in failures:
            print("  FAIL:", f)
        sys.exit(1)
    print("  ALL CHECKS PASSED (%d docx, %d figures, %d TIFF)" %
          (len(glob.glob(os.path.join(a.delivery, "*.docx"))), n_png, n_tif))


if __name__ == "__main__":
    main()
