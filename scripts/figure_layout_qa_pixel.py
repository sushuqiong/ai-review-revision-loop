#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pixel-level figure layout QA (no vision model required).

Checks, per PNG:
  1. page geometry      width <= --max-cm (default 17.0) and height <= --max-cm-h (default 24.0)
  2. clipping           an OCR word box touching the canvas edge AND ink actually present in the
                        outer 4 px band at that edge (boxes that merely touch a blank margin are dismissed)
  3. text collisions    two OCR word boxes on the same line whose horizontal spans intersect AND whose
                        intersection rectangle contains ink (< --ink-frac => dismissed as an empty overlap)
  4. false positives    OCR fragments of ONE token are dismissed: adjacent boxes (gap <= 3 px) whose
                        concatenation matches a number (decimals are routinely split as 0.94 -> "0.9"+"4")
  5. required tokens    optional --need "A,B,C,D" sanity check that panel letters survive

Usage
  python figure_layout_qa_pixel.py <figure_dir> [--dpi 300] [--max-cm 17.0] [--max-cm-h 24.0]
                                  [--need "A,B,C,D"] [--tmp C:\\Users\\me\\ocr_tmp]

Environment notes
  * Tesseract must be on PATH or given via --tess; TESSDATA_PREFIX is set automatically when the
    default Windows install is detected (C:\\Program Files\\Tesseract-OCR\\tessdata).
  * Figures are copied into an ASCII-only temp directory before OCR (non-ASCII paths break tesseract).
  * Verdict is PASS only when a figure has 0 clipped tokens, 0 candidate collisions and geometry within limits.
"""
import argparse, csv, itertools, os, re, shutil, subprocess, sys

NUM = re.compile(r"^\d+(\.\d+)?$|^[.,]$|^[-+]$")


def tess_path(explicit=None):
    if explicit:
        return explicit
    for c in (r"C:\Program Files\Tesseract-OCR\tesseract.exe", "tesseract"):
        if c == "tesseract" or os.path.exists(c):
            return c
    return "tesseract"


def ocr_words(img, tess, tmp):
    env = dict(os.environ)
    if os.path.exists(r"C:\Program Files\Tesseract-OCR\tessdata"):
        env["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"
    r = subprocess.run([tess, img, "stdout", "--psm", "11", "tsv"], capture_output=True, env=env)
    words = []
    for row in csv.DictReader(r.stdout.decode("utf-8", "replace").splitlines(), delimiter="\t"):
        t = (row.get("text") or "").strip()
        if not t:
            continue
        try:
            words.append(dict(t=t, c=float(row.get("conf") or -1), x=int(row["left"]), y=int(row["top"]),
                              w=int(row["width"]), h=int(row["height"])))
        except Exception:
            pass
    return [w for w in words if w["c"] > 30]


def qa_figure(path, dpi, max_cm, max_cm_h, ink, ink_frac, tess, tmp):
    from PIL import Image
    import numpy as np
    dst = os.path.join(tmp, os.path.basename(path))
    shutil.copy(path, dst)
    im = Image.open(dst).convert("L")
    W, H = im.size
    arr = np.array(im)
    cm_w, cm_h = W / dpi * 2.54, H / dpi * 2.54
    words = ocr_words(dst, tess, tmp)

    clipped = []
    for w in words:
        if w["x"] + w["w"] >= W - 2 or w["y"] + w["h"] >= H - 2 or w["x"] <= 2 or w["y"] <= 2:
            band = arr[max(0, w["y"]):w["y"] + w["h"], max(0, W - 4):W] if w["x"] + w["w"] >= W - 2 else None
            if band is None:                       # top / left / bottom edge
                band = arr[max(0, H - 4):H, max(0, w["x"]):w["x"] + w["w"]] if w["y"] + w["h"] >= H - 2 \
                       else arr[max(0, w["y"]):w["y"] + w["h"], 0:4]
            if band.size and (band < ink).mean() > 0.005:
                clipped.append(w["t"])

    candidates, dismissed = [], []
    for a, b in itertools.combinations(words, 2):
        if abs((a["y"] + a["h"] / 2) - (b["y"] + b["h"] / 2)) >= 0.5 * min(a["h"], b["h"]):
            continue
        x0, x1 = max(a["x"], b["x"]), min(a["x"] + a["w"], b["x"] + b["w"])
        y0, y1 = max(a["y"], b["y"]), min(a["y"] + a["h"], b["y"] + b["h"])
        if x1 <= x0 or y1 <= y0:
            continue
        crop = arr[max(0, y0):max(1, y1), max(0, x0):max(1, x1)]
        if crop.size == 0 or (crop < ink).mean() < ink_frac:
            dismissed.append((a["t"], b["t"], "blank intersection"))
            continue
        gap = max(a["x"], b["x"]) - min(a["x"] + a["w"], b["x"] + b["w"])
        merged = a["t"] + b["t"] if a["x"] <= b["x"] else b["t"] + a["t"]
        if gap <= 3 and (NUM.match(a["t"]) or NUM.match(b["t"]) or NUM.match(merged)):
            dismissed.append((a["t"], b["t"], "OCR fragmentation of one token"))
            continue
        candidates.append((a["t"], b["t"], round(float((crop < ink).mean()), 3)))

    return dict(file=os.path.basename(path), cm_w=round(cm_w, 1), cm_h=round(cm_h, 1), words=len(words),
                clipped=clipped, candidates=candidates, dismissed=dismissed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("figdir")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--max-cm", type=float, default=17.0)
    ap.add_argument("--max-cm-h", type=float, default=24.0)
    ap.add_argument("--ink", type=int, default=110)
    ap.add_argument("--ink-frac", type=float, default=0.02)
    ap.add_argument("--need", default="")
    ap.add_argument("--tess", default=None)
    ap.add_argument("--tmp", default=os.path.join(os.path.expanduser("~"), "figure_qa_tmp"))
    a = ap.parse_args()
    shutil.rmtree(a.tmp, ignore_errors=True)
    os.makedirs(a.tmp, exist_ok=True)
    tess = tess_path(a.tess)
    need = [t.strip() for t in a.need.split(",") if t.strip()]
    bad = 0
    figs = sorted(f for f in os.listdir(a.figdir) if f.lower().endswith(".png"))
    if not figs:
        print("no PNG files found in", a.figdir); return 2
    for f in figs:
        r = qa_figure(os.path.join(a.figdir, f), a.dpi, a.max_cm, a.max_cm_h, a.ink, a.ink_frac, tess, a.tmp)
        ok = (r["cm_w"] <= a.max_cm + 0.2 and r["cm_h"] <= a.max_cm_h and not r["clipped"] and not r["candidates"])
        missing = [t for t in need if t not in " ".join(w["t"] for w in ocr_words(os.path.join(a.tmp, f), tess, a.tmp))]
        if not ok or missing:
            bad += 1
        print(f"{'OK  ' if ok and not missing else 'FLAG'} {r['file']}: {r['cm_w']} x {r['cm_h']} cm | "
              f"words={r['words']} clipped={len(r['clipped'])} collisions={len(r['candidates'])} "
              f"dismissed={len(r['dismissed'])}" + (f" missing_tokens={missing}" if missing else ""))
        if r["clipped"]:
            print("      clipped (ink at edge):", r["clipped"][:5])
        if r["candidates"]:
            print("      candidate collisions:", r["candidates"][:5])
        if r["dismissed"]:
            why = {}
            for _, _, w in r["dismissed"]:
                why[w] = why.get(w, 0) + 1
            print("      dismissed:", why)
    print("\n" + ("PASS: within page limits, no clipping, no candidate collisions"
                  if bad == 0 else f"FLAGGED: {bad} figure(s) need attention"))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
