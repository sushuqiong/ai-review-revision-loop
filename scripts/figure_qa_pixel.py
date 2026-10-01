#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Programmatic figure review without a vision model (six checks).

Usage:
    python figure_qa_pixel.py <figure_dir> [--expect expectations.json] [--tess <tesseract.exe>]

What it checks (see references/programmatic-figure-qa.md for the reasoning):
  1. page size / DPI       : PNG IHDR + pHYs            -> width <= 17.2 cm, height <= 24 cm, ~300 dpi
  2. edge clipping         : OCR word box touching the canvas edge *with ink in the edge strip*
  3. same-line collisions  : intersecting word boxes with ink inside the intersection rectangle
  4. label completeness    : expected panel letters / group names present (optional --expect JSON)
  5. print-size legibility : OCR again at 50% scale, token retention >= 0.6
  6. legend/title strip, margins, contrast

False positives are adjudicated, not reported blindly:
  * OCR splits numbers ("0.94" -> "0.9" + "4") and em-dashes into separate tokens -> dismissed
  * blank intersection rectangles -> dismissed
  * low-contrast tokens are printed with their text so single-character artefacts are obvious

Expectations file format (optional):
    {"Fig1_overview.png": {"letters": ["A","B","C"], "groups": ["LUAD","CRC","STAD"], "n_modules": 17}}
"""
import argparse, csv, itertools, json, os, re, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image

NUM = re.compile(r"^\d+(\.\d+)?$|^[.,]$|^[-+]$")
INK = 110          # grey level below which a pixel counts as ink
ARTIFACT = 0.02    # <2% ink inside a candidate intersection => OCR bounding-box artefact


def ocr_words(path, tess, env):
    r = subprocess.run([tess, path, "stdout", "--psm", "11", "tsv"], capture_output=True, env=env)
    out = []
    for row in csv.DictReader(r.stdout.decode("utf-8", "replace").splitlines(), delimiter="\t"):
        t = (row.get("text") or "").strip()
        if not t:
            continue
        try:
            out.append(dict(t=t, c=float(row.get("conf") or -1), x=int(row["left"]), y=int(row["top"]),
                            w=int(row["width"]), h=int(row["height"])))
        except Exception:
            pass
    return [w for w in out if w["c"] > 30]


def check(path, name, tess, env, expect=None, tmp=None):
    im = Image.open(path).convert("L")
    W, H = im.size
    arr = np.array(im)
    dpi = im.info.get("dpi", (None, None))[0]
    words = ocr_words(path, tess, env)
    res = {"file": name, "cm_w": round(W / 300 * 2.54, 2), "cm_h": round(H / 300 * 2.54, 2),
           "dpi": round(dpi) if dpi else "n/a", "tokens": len(words)}
    # 1 page size
    res["size_ok"] = res["cm_w"] <= 17.2 and res["cm_h"] <= 24.0
    # 2 clipping (box at edge AND ink in the edge strip)
    clipped = []
    for w in words:
        if w["x"] <= 2 or w["y"] <= 2 or w["x"] + w["w"] >= W - 2 or w["y"] + w["h"] >= H - 2:
            strip = arr[max(0, w["y"]):w["y"] + w["h"], max(W - 40, W - 1):W]
            if strip.size and (strip < INK).mean() > 0.005:
                clipped.append(w["t"])
    res["clipped"] = clipped
    # 3 collisions with adjudication
    real, dismissed = [], []
    for a, b in itertools.combinations(words, 2):
        if abs((a["y"] + a["h"] / 2) - (b["y"] + b["h"] / 2)) >= 0.5 * min(a["h"], b["h"]):
            continue
        x0, x1 = max(a["x"], b["x"]), min(a["x"] + a["w"], b["x"] + b["w"])
        y0, y1 = max(a["y"], b["y"]), min(a["y"] + a["h"], b["y"] + b["h"])
        if x1 <= x0 or y1 <= y0:
            continue
        crop = arr[max(0, y0):max(1, y1), max(0, x0):max(1, x1)]
        frac = float((crop < INK).mean()) if crop.size else 0.0
        if frac < ARTIFACT:
            dismissed.append((a["t"], b["t"], "blank intersection"))
            continue
        gap = max(a["x"], b["x"]) - min(a["x"] + a["w"], b["x"] + b["w"])
        merged = (a["t"] + b["t"]) if a["x"] <= b["x"] else (b["t"] + a["t"])
        if gap <= 3 and (NUM.match(a["t"]) or NUM.match(b["t"]) or NUM.match(merged)):
            dismissed.append((a["t"], b["t"], "OCR fragmentation of one number"))
            continue
        real.append((a["t"], b["t"], round(frac, 3)))
    res["collisions"], res["dismissed"] = real, len(dismissed)
    # 4 label completeness
    if expect:
        texts = [w["t"] for w in words]
        joined = " ".join(texts)
        res["missing_letters"] = [l for l in expect.get("letters", []) if l not in texts]
        res["missing_groups"] = [g for g in expect.get("groups", []) if g.lower() not in joined.lower()]
        if expect.get("n_modules"):
            res["n_modules_note"] = "check module short labels manually against the legend mapping"
    # 5 print-size legibility
    small = os.path.join(tmp, "small_" + name)
    Image.open(path).resize((max(1, W // 2), max(1, H // 2)), Image.LANCZOS).save(small)
    res["retention_50pct"] = round(len(ocr_words(small, tess, env)) / max(1, len(words)), 2)
    # 6 strips, margins, contrast
    def cover(band):
        return round(float(((band < INK).mean(axis=0) > 0.02).mean()), 2)
    res["top_strip"], res["bottom_strip"] = cover(arr[:max(1, int(H * 0.035)), :]), cover(arr[int(H * 0.965):, :])
    ink = np.argwhere(arr < 200)
    res["margins_px"] = dict(top=int(ink[:, 0].min()), bottom=int(H - 1 - ink[:, 0].max()),
                             left=int(ink[:, 1].min()), right=int(W - 1 - ink[:, 1].max())) if ink.size else {}
    lows = []
    for w in words:
        box = arr[max(0, w["y"]):w["y"] + w["h"], max(0, w["x"]):w["x"] + w["w"]].astype(float)
        if box.size < 40 or box.std() < 18:      # graphical false positive: no readable contrast in the box
            continue
        fg, bg = float(np.percentile(box, 5)), float(np.percentile(box, 95))
        if bg > fg and (bg + 5) / (fg + 5) < 3:
            lows.append((w["t"], round((bg + 5) / (fg + 5), 2)))
    res["low_contrast_tokens"] = lows
    res["pass"] = (res["size_ok"] and not clipped and not real and res["retention_50pct"] >= 0.6
                   and res["top_strip"] < 0.55 and res["bottom_strip"] < 0.55)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fig_dir")
    ap.add_argument("--expect", help="JSON file with per-figure expectations")
    ap.add_argument("--tess", default=r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    ap.add_argument("--tessdata", default=r"C:\Program Files\Tesseract-OCR\tessdata")
    a = ap.parse_args()
    exp = json.load(open(a.expect, encoding="utf-8")) if a.expect else {}
    env = dict(os.environ, TESSDATA_PREFIX=a.tessdata)
    tmp = tempfile.mkdtemp(prefix="figqa_")
    rows = []
    for f in sorted(x for x in os.listdir(a.fig_dir) if x.lower().endswith(".png")):
        src = os.path.join(a.fig_dir, f)
        dst = os.path.join(tmp, f)          # copy to an ASCII temp dir (non-ASCII paths break OCR)
        shutil.copy(src, dst)
        r = check(dst, f, a.tess, env, exp.get(f), tmp)
        rows.append(r)
        print(f"\n[{'PASS' if r['pass'] else 'CHECK'}] {f}: {r['cm_w']}x{r['cm_h']} cm @ {r['dpi']} dpi | tokens={r['tokens']}")
        print(f"  clipped={len(r['clipped'])} {r['clipped'][:3]} | collisions={len(r['collisions'])} {r['collisions'][:3]}"
              f" | dismissed={r['dismissed']}")
        print(f"  print-size retention@50% = {r['retention_50pct']} | strips top {r['top_strip']} bottom {r['bottom_strip']}"
              f" | margins {r['margins_px']}")
        if r.get("missing_letters") or r.get("missing_groups"):
            print(f"  MISSING letters={r.get('missing_letters')} groups={r.get('missing_groups')}")
        if r["low_contrast_tokens"]:
            print(f"  low-contrast tokens (usually single-char OCR artefacts): {r['low_contrast_tokens'][:6]}")
    bad = [r for r in rows if not r["pass"]]
    print("\n" + ("ALL FIGURES PASS the programmatic checks" if not bad else f"{len(bad)} figure(s) need attention"))
    print("Reminder: machine checks cover geometry and the text layer only; ask the author for the final visual check.")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
