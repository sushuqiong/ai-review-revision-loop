#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OCR layout QA for publication figures (Windows/git-bash friendly).

What it checks, per figure:
  * physical width in cm at the assumed dpi (flags anything wider than the column cap)
  * text boxes that touch or cross the canvas edge (clipping candidates, with coordinates)
  * pixel-level re-check of each candidate: a candidate whose bounding region is blank
    (min grey == 255 / near-zero ink) is reported as a FALSE POSITIVE, so you do not
    shrink a title that was never actually clipped
  * optional token presence check (e.g. required panel letters or axis words)

Usage
-----
  python ocr_figure_layout_qa.py <dir_or_files...> [--dpi 300] [--max-cm 17.0] [--need A,B,C,D]

Notes / pitfalls this script already handles
  * Tesseract on Windows needs TESSDATA_PREFIX; set it below or in the environment.
  * OCR fails on non-ASCII paths -> the image is copied to an ASCII temp dir first.
  * OCR reads grid lines / error bars as '-' '+' '5'; ignore such tokens, trust code-set font sizes.
  * A single stray character at the very edge is usually a real truncation of a longer
    word (check the zoomed crop), while a fully blank box is noise.
"""
import argparse, csv, os, shutil, subprocess, sys, tempfile

TESS = os.environ.get("TESSERACT_BIN", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA = os.environ.get("TESSDATA_PREFIX", r"C:\Program Files\Tesseract-OCR\tessdata")


def words(img_path, tmpdir):
    """OCR word boxes with confidence, via an ASCII-safe copy."""
    safe = os.path.join(tmpdir, "ascii_copy" + os.path.splitext(img_path)[1])
    shutil.copy(img_path, safe)
    env = dict(os.environ, TESSDATA_PREFIX=TESSDATA)
    r = subprocess.run([TESS, safe, "stdout", "--psm", "11", "tsv"],
                       capture_output=True, env=env)
    out = []
    for row in csv.DictReader(r.stdout.decode("utf-8", "replace").splitlines(), delimiter="\t"):
        t = (row.get("text") or "").strip()
        if not t:
            continue
        try:
            out.append(dict(t=t, c=float(row.get("conf") or -1),
                            x=int(row["left"]), y=int(row["top"]),
                            w=int(row["width"]), h=int(row["height"])))
        except Exception:
            pass
    return [w for w in out if w["c"] > 30]


def ink_stats(img_path, box, pad=8):
    """Fraction of non-white pixels around a box -> separates real text from noise."""
    from PIL import Image
    import numpy as np
    im = Image.open(img_path).convert("L")
    x, y, w, h = box
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(im.width, x + w + pad), min(im.height, y + h + pad)
    if x1 <= x0 or y1 <= y0:
        return 1.0, 0
    a = np.array(im.crop((x0, y0, x1, y1)))
    return float((a < 200).mean()), int(a.min())


def qa(path, dpi, max_cm, need):
    from PIL import Image
    with tempfile.TemporaryDirectory() as tmp:
        W, H = Image.open(path).size
        cm_w = W / dpi * 2.54
        ws = words(path, tmp)
        cand = [w for w in ws if w["x"] <= 2 or w["y"] <= 2
                or w["x"] + w["w"] >= W - 2 or w["y"] + w["h"] >= H - 2]
        real, fake = [], []
        for w in cand:
            frac, mn = ink_stats(path, (w["x"], w["y"], w["w"], w["h"]))
            (real if frac > 0.01 else fake).append((w["t"], w["x"], w["y"], round(frac, 4)))
        txt = " ".join(w["t"] for w in ws)
        missing = [t for t in need if t.lower() not in txt.lower()]
        return dict(file=os.path.basename(path), px=f"{W}x{H}", cm_w=round(cm_w, 2),
                    over_width=cm_w > max_cm + 0.05, words=len(ws),
                    clipped_real=real, clipped_false_positive=fake, missing_tokens=missing)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--max-cm", type=float, default=17.0)
    ap.add_argument("--need", default="")
    a = ap.parse_args()
    need = [t for t in a.need.split(",") if t]
    files = []
    for p in a.paths:
        if os.path.isdir(p):
            files += [os.path.join(p, f) for f in sorted(os.listdir(p))
                      if f.lower().endswith((".png", ".tif", ".tiff"))]
        else:
            files.append(p)
    bad = 0
    for f in files:
        r = qa(f, a.dpi, a.max_cm, need)
        flag = "OK  "
        if r["over_width"] or r["clipped_real"] or r["missing_tokens"]:
            flag, bad = "FAIL", bad + 1
        print(f"{flag} {r['file']}: {r['px']} = {r['cm_w']} cm | words={r['words']}")
        if r["over_width"]:
            print(f"       width {r['cm_w']} cm exceeds the {a.max_cm} cm column cap")
        if r["clipped_real"]:
            print(f"       REAL clipping (fix the label/title, it is too long): {r['clipped_real']}")
        if r["clipped_false_positive"]:
            print(f"       false positive (blank region, leave it alone): {r['clipped_false_positive']}")
        if r["missing_tokens"]:
            print(f"       missing expected tokens: {r['missing_tokens']}")
    print(f"\n{len(files)} figure(s), {bad} with issues")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
