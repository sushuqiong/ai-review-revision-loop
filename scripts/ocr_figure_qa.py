#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OCR 版面质检：裁切 / 真实文字重叠 / 字号 / 关键标签缺失。

用法:
    python ocr_figure_qa.py <fig_dir> [--expect expect.json] [--out qa.csv]

要点（踩过的坑）:
  * 必须给 tesseract 传 TESSDATA_PREFIX，否则报 "Can't open tsv" 并静默返回 0 词。
  * 非 ASCII 路径先复制到 ASCII 临时目录。
  * 只统计"实质词"重叠（h>=29px, w>=25px, >=3 字母数字），否则网格线/误差棒端
    被误读的 '-'/'5'/'+'（高 4-8px）会刷出大量假阳性。
  * 字号以绘图代码设定为准；tesseract 量的是小写 x 高度，"<7pt" 计数会虚高。
  * 期望词表把情境名/模块名/关键数字写进去；OCR 读不到就是真实缺陷（曾抓到
    "malignant cell ()" 空括号 bug：脚本引用了不存在的列）。
"""
import argparse, csv, json, os, re, shutil, subprocess, tempfile
from PIL import Image

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSDATA = r"C:\Program Files\Tesseract-OCR\tessdata"
MIN_PT_PX = 29          # 7 pt at 300 dpi 附近的经验阈值
ARTIFACT_H = 10         # 低于此高度视为线条误读

def ocr_words(path, psm="11"):
    env = dict(os.environ, TESSDATA_PREFIX=TESSDATA)
    r = subprocess.run([TESS, path, "stdout", "--psm", psm, "tsv"],
                       capture_output=True, env=env)
    out = []
    for row in csv.DictReader(r.stdout.decode("utf-8", "replace").splitlines(), delimiter="\t"):
        t = (row.get("text") or "").strip()
        if not t:
            continue
        try:
            out.append(dict(text=t, conf=float(row.get("conf") or -1), x=int(row["left"]),
                            y=int(row["top"]), w=int(row["width"]), h=int(row["height"])))
        except Exception:
            pass
    return [w for w in words_ok(w) for _ in (0,)] if False else [w for w in out if w["conf"] > 30]

def words_ok(ws):  # placeholder to keep the comprehension above readable
    return ws

def iou(a, b):
    x1, y1 = max(a["x"], b["x"]), max(a["y"], b["y"])
    x2, y2 = min(a["x"] + a["w"], b["x"] + b["w"]), min(a["y"] + a["h"], b["y"] + b["h"])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    return (x2 - x1) * (y2 - y1) / float(min(a["w"] * a["h"], b["w"] * b["h"]))

def substantial(w):
    return w["h"] >= MIN_PT_PX and w["w"] >= 25 and len(re.sub(r"[^0-9A-Za-z]", "", w["text"])) >= 3

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fig_dir")
    ap.add_argument("--expect", help="JSON: {filename: [required tokens]}")
    ap.add_argument("--out", default="ocr_figure_qa.csv")
    ap.add_argument("--ascii_tmp", default=os.path.join(tempfile.gettempdir(), "ocr_tmp"))
    a = ap.parse_args()
    expect = json.load(open(a.expect, encoding="utf-8")) if a.expect and os.path.exists(a.expect) else {}
    shutil.rmtree(a.ascii_tmp, ignore_errors=True); os.makedirs(a.ascii_tmp, exist_ok=True)
    figs = [f for f in sorted(os.listdir(a.fig_dir)) if f.lower().endswith((".png", ".tif", ".tiff"))]
    rows = []
    for f in figs:
        dst = os.path.join(a.ascii_tmp, f)
        shutil.copy(os.path.join(a.fig_dir, f), dst)
        W, H = Image.open(dst).size
        ws = ocr_words(dst, psm="6") or ocr_words(dst, psm="11")
        real = [w for w in ws if w["h"] >= ARTIFACT_H]
        clip = [w for w in real if w["x"] <= 2 or w["y"] <= 2 or w["x"] + w["w"] >= W - 2 or w["y"] + w["h"] >= H - 2]
        strong = [w for w in real if substantial(w)]
        ov = [(x["text"], y["text"]) for i, x in enumerate(strong) for y in strong[i + 1:] if iou(x, y) > 0.3]
        txt = " ".join(w["text"] for w in real).lower()
        miss = [t for t in expect.get(f, []) if t.lower() not in txt]
        med = sorted(w["h"] for w in strong)[len(strong) // 2] if strong else 0
        rows.append(dict(file=f, size=f"{W}x{H}", cm_w=round(W / 300 * 2.54, 1), words=len(real),
                         median_text_h_px=med, clipping=len(clip), overlaps=len(ov),
                         missing=";".join(miss)))
        flag = "OK " if not (clip or ov or miss) else "FIX"
        print(f"{flag} {f:34} {W}x{H} ({W/300*2.54:.1f}cm) words={len(real):3} med_h={med:3} "
              f"clip={len(clip)} ov={len(ov)} miss={miss}")
    with open(a.out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    bad = [r for r in rows if r["clipping"] or r["overlaps"] or r["missing"] or r["cm_w"] > 17.05]
    print(f"\nfigures needing fixes: {len(bad)} -> {a.out}")
    return 1 if bad else 0

if __name__ == "__main__":
    raise SystemExit(main())
