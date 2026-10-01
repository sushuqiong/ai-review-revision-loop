#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Figure READABILITY and COMPLETENESS audit (no vision model required).

Complements figure_layout_qa_pixel.py (which covers geometry / clipping / collisions).
Use both; this one answers "can a reader actually read it, and is everything there?".

Layers, per PNG:
  1. label completeness   expected tokens actually rendered (panel letters, all contexts, all module labels)
  2. print-size legibility OCR the figure at --scale (default 0.5, i.e. journal print size) and report the
                          fraction of full-size tokens that survive; < --min-retention (0.6) means some text is
                          too small -> raise the smallest font in the plotting script rather than shrinking the figure
  3. busy background      tokens whose local background has std > --busy-std (48): text sitting on bars/heatmaps
  4. legend/title strip   ink columns covering >= --strip-cover (0.55) of the width inside the outer
                          --strip-frac (0.035) bands -> a legend or overall title is present (these figures must not have one)
  5. margins              outermost ink bounding box; flags any margin < --min-margin px (content touching the edge)
  6. contrast             per-token text/background ratio from the 5th/95th percentiles of the box, skipping boxes
                          with std < 18 (graphical false positives). Single-character "tokens" are reported but
                          marked as OCR fragments, because dashes/plus signs/axes are read as characters.

Usage
  python figure_readability_audit.py <figure_dir> [--dpi 300] [--scale 0.5] [--min-retention 0.6]
                                     [--strip-cover 0.55] [--min-margin 8] [--need "A,B,C,D"]
                                     [--contexts "LUAD,CRC,STAD"] [--tess PATH] [--tmp DIR]

Exit code 0 = all layers clean, 1 = something flagged.
Environment: Tesseract on PATH or --tess; TESSDATA_PREFIX auto-set for the default Windows install;
figures are copied to an ASCII-only temp dir first (non-ASCII paths break tesseract).
"""
import argparse, csv, os, shutil, subprocess, sys

DEFAULT_TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
DEFAULT_TESDATA = r"C:\Program Files\Tesseract-OCR\tessdata"


def ocr(img, tess):
    env = dict(os.environ)
    if os.path.exists(DEFAULT_TESDATA):
        env["TESSDATA_PREFIX"] = DEFAULT_TESDATA
    r = subprocess.run([tess, img, "stdout", "--psm", "11", "tsv"], capture_output=True, env=env)
    out = []
    for row in csv.DictReader(r.stdout.decode("utf-8", "replace").splitlines(), delimiter="\t"):
        t = (row.get("text") or "").strip()
        if not t:
            continue
        try:
            out.append(dict(t=t, x=int(row["left"]), y=int(row["top"]), w=int(row["width"]), h=int(row["height"])))
        except Exception:
            pass
    return out


def audit(path, a, tess, tmp):
    import numpy as np
    from PIL import Image
    dst = os.path.join(tmp, os.path.basename(path))
    shutil.copy(path, dst)
    im = Image.open(dst).convert("L")
    W, H = im.size
    arr = np.array(im)
    tk = ocr(dst, tess)

    # 1 label completeness
    def missing(tokens, words):
        return [t for t in tokens if t.lower() not in words.lower()]
    words = " ".join(x["t"] for x in tk)
    miss_need = missing(a.need, words)
    miss_ctx = missing(a.contexts, words)

    # 2 print-size legibility
    small = os.path.join(tmp, "small_" + os.path.basename(path))
    Image.open(dst).resize((max(1, int(W * a.scale)), max(1, int(H * a.scale))), Image.LANCZOS).save(small)
    tk_small = ocr(small, tess)
    retention = len(tk_small) / max(1, len(tk))

    # 3 busy background
    busy = 0
    for t in tk:
        box = arr[max(0, t["y"]):t["y"] + t["h"], max(0, t["x"]):t["x"] + t["w"]]
        if box.size < 30:
            continue
        bg = box[box > np.percentile(box, 60)]
        if bg.size and bg.std() > a.busy_std:
            busy += 1

    # 4 legend / title strip
    def cover(band):
        col = (band < 110).mean(axis=0)
        return float((col > 0.02).mean())
    top = cover(arr[:max(1, int(H * a.strip_frac)), :])
    bottom = cover(arr[int(H * (1 - a.strip_frac)):, :])

    # 5 margins
    ink = np.argwhere(arr < 200)
    if ink.size:
        mt, mb = int(ink[:, 0].min()), int(H - 1 - ink[:, 0].max())
        ml, mr = int(ink[:, 1].min()), int(W - 1 - ink[:, 1].max())
    else:
        mt = mb = ml = mr = 0

    # 6 contrast
    ratios, worst = [], []
    for t in tk:
        box = arr[max(0, t["y"]):t["y"] + t["h"], max(0, t["x"]):t["x"] + t["w"]].astype(float)
        if box.size < 40 or box.std() < 18:          # skip boxes without readable contrast
            continue
        fg, bg = float(np.percentile(box, 5)), float(np.percentile(box, 95))
        if bg > fg:
            ratio = (bg + 5) / (fg + 5)
            ratios.append(ratio)
            if ratio < 3 and len(t) > 1:             # single chars are OCR fragments, not labels
                worst.append((t["t"], round(ratio, 2)))

    return dict(file=os.path.basename(path), cm=(round(W / a.dpi * 2.54, 1), round(H / a.dpi * 2.54, 1)),
                tokens=len(tk), miss_need=miss_need, miss_ctx=miss_ctx, retention=round(retention, 2),
                busy=busy, top=round(top, 2), bottom=round(bottom, 2),
                margins=(mt, mb, ml, mr), min_contrast=round(min(ratios), 2) if ratios else None, worst=worst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("figdir")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--scale", type=float, default=0.5)
    ap.add_argument("--min-retention", type=float, default=0.6)
    ap.add_argument("--busy-std", type=float, default=48.0)
    ap.add_argument("--strip-frac", type=float, default=0.035)
    ap.add_argument("--strip-cover", type=float, default=0.55)
    ap.add_argument("--min-margin", type=int, default=8)
    ap.add_argument("--need", default="")
    ap.add_argument("--contexts", default="")
    ap.add_argument("--tess", default=DEFAULT_TESS if os.path.exists(DEFAULT_TESS) else "tesseract")
    ap.add_argument("--tmp", default=os.path.join(os.path.expanduser("~"), "figure_readability_tmp"))
    a = ap.parse_args()
    a.need = [t.strip() for t in a.need.split(",") if t.strip()]
    a.contexts = [t.strip() for t in a.contexts.split(",") if t.strip()]
    shutil.rmtree(a.tmp, ignore_errors=True)
    os.makedirs(a.tmp, exist_ok=True)
    figs = sorted(f for f in os.listdir(a.figdir) if f.lower().endswith(".png"))
    if not figs:
        print("no PNG files found in", a.figdir)
        return 2
    flagged = 0
    for f in figs:
        r = audit(os.path.join(a.figdir, f), a, a.tess, a.tmp)
        problems = []
        if r["miss_need"]:
            problems.append(f"missing panel letters {r['miss_need']}")
        if r["miss_ctx"]:
            problems.append(f"missing labels {r['miss_ctx']}")
        if r["retention"] < a.min_retention:
            problems.append(f"print-size retention {r['retention']} < {a.min_retention} (raise the smallest font)")
        if max(r["top"], r["bottom"]) >= a.strip_cover:
            problems.append(f"legend/title strip detected (top {r['top']} / bottom {r['bottom']})")
        if min(r["margins"]) < a.min_margin:
            problems.append(f"content touches the edge (margins {r['margins']})")
        if problems:
            flagged += 1
        print(f"{'FLAG' if problems else 'OK  '} {r['file']}: {r['cm'][0]} x {r['cm'][1]} cm | tokens={r['tokens']} "
              f"| print-size retention={r['retention']} | busy-bg tokens={r['busy']} "
              f"| strips top/bottom={r['top']}/{r['bottom']} | margins={r['margins']} | min contrast={r['min_contrast']}")
        for p in problems:
            print("      ->", p)
        if r["worst"]:
            print("      real low-contrast labels (single-char OCR fragments excluded):", r["worst"][:5])
    print("\n" + ("PASS: labels complete, readable at print size, no legend/title strip, margins intact"
                  if flagged == 0 else f"FLAGGED: {flagged} figure(s)"))
    return 0 if flagged == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
