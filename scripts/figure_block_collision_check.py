#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
figure_block_collision_check.py — 检测"整块面板标签互相压叠"（用户口中的"数字显示不全/不清"）

判据（见 references/figure-ocr-layout-qa.md §十五）：
  面板数据区的【最大连续墨迹块宽度】必须 < 350 px。
  单个 > 350 px 的连续墨迹块 = 标签被串成一整块（常见元凶：面板底部的全宽基线）。

不同于逐行列投影（§十二，只抓单行内刻度粘连），本脚本按"行段 → 段内最长连续列段"测量整块。

用法:
  python figure_block_collision_check.py FIG.png
  python figure_block_collision_check.py FIG.png --y0 740 --y1 1120        # 只测面板数据区
  python figure_block_collision_check.py FIG.png --expect 223 194 365 92   # 附带逐标签 OCR 回读
  python figure_block_collision_check.py FIG.png --invert                   # 浅色/白字（柱内标签）

依赖: numpy, Pillow, tesseract CLI（TESSDATA_PREFIX 由本脚本自动设置）
"""
import argparse
import os
import subprocess
import sys

import numpy as np
from PIL import Image

TESS_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
]
TESSDATA_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tessdata",
    "/usr/share/tesseract-ocr/5/tessdata",
    "/usr/share/tessdata",
]


def find_tess():
    for p in TESS_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def set_tessdata(env):
    for d in TESSDATA_CANDIDATES:
        if os.path.isdir(d):
            env["TESSDATA_PREFIX"] = d
            return d
    return None


def row_segments(ink, min_ink=8, gap=6):
    """把墨迹行切成行段（文字行/数据行）。"""
    rows = ink.sum(axis=1)
    ys = [y for y in range(ink.shape[0]) if rows[y] > min_ink]
    if not ys:
        return []
    segs, s, prev = [], ys[0], ys[0]
    for y in ys[1:]:
        if y - prev <= gap:
            prev = y
        else:
            segs.append((s, prev))
            s = prev = y
    segs.append((s, prev))
    return segs


def longest_run(cols):
    """给定墨迹列索引数组，返回最长连续段的长度。"""
    if len(cols) == 0:
        return 0
    best = cur = 1
    for i in range(1, len(cols)):
        if cols[i] - cols[i - 1] <= 2:
            cur += 1
        else:
            best = max(best, cur)
            cur = 1
    return max(best, cur)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("png")
    ap.add_argument("--y0", type=int, default=None, help="面板数据区起始 y（默认自动取下半部）")
    ap.add_argument("--y1", type=int, default=None, help="面板数据区结束 y")
    ap.add_argument("--thr", type=int, default=350, help="最大连续块阈值 px（默认 350）")
    ap.add_argument("--dark", type=int, default=235, help="暗墨迹阈值（默认 235）")
    ap.add_argument("--invert", action="store_true", help="测浅色/白字（柱内标签）")
    ap.add_argument("--base", default=None, help="柱体填充色 R,G,B —— 用它做偏离度二值化（抓低对比度柱内文字）")
    ap.add_argument("--expect", nargs="*", default=[], help="期望被 OCR 读出的 token 列表")
    args = ap.parse_args()

    im = Image.open(args.png).convert("RGB")
    W, H = im.size
    y0 = args.y0 if args.y0 is not None else int(H * 0.5)
    y1 = args.y1 if args.y1 is not None else H
    print(f"[i] {os.path.basename(args.png)}  {W}x{H}  测量区 y{y0}..{y1}")

    a = np.array(im).astype(int)[y0:y1, :, :]

    if args.base:
        base = np.array([int(x) for x in args.base.split(",")])
        dev = np.abs(a - base).sum(axis=2)
        ink = dev > 30
        print(f"[i] 偏离度二值化 base={base.tolist()} (>30)")
    else:
        lum = a.mean(axis=2)
        ink = (lum > 235) if args.invert else (lum < args.dark)

    segs = row_segments(ink)
    if not segs:
        print("[X] 测量区内无墨迹 —— 检查 --y0/--y1 或阈值")
        return 1

    print(f"[i] 行段 {len(segs)} 个，逐段最长连续墨迹块：")
    worst, worst_at = 0, None
    for s, e in segs:
        cols = np.where(ink[s:e + 1, :].any(axis=0))[0]
        if len(cols) == 0:
            continue
        runs, st, prev = [], cols[0], cols[0]
        for x in cols[1:]:
            if x - prev <= 2:
                prev = x
            else:
                runs.append(prev - st + 1)
                st = prev = x
        runs.append(prev - st + 1)
        mx = max(runs)
        if mx > worst:
            worst, worst_at = mx, (y0 + s, y0 + e)
        flag = "  <== 超阈值" if mx > args.thr else ""
        print(f"    y{y0+s}-{y0+e} (高{e-s+1})  最长连续块 {mx} px  最长行段内簇数 {len(runs)}{flag}")

    ok = worst <= args.thr
    print()
    print(f">>> 最大连续墨迹块 = {worst} px @ y{worst_at}  (阈值 {args.thr})  -> "
          f"{'PASS' if ok else 'FAIL —— 标签被串成一整块'}")
    if not ok:
        print("    常见元凶：面板底部的【全宽基线/坐标轴线】把柱+标签+刻度串成一块。")
        print("    处置：删掉全宽基线（保留短刻度线、柱底即坐标区下沿），再加大轴高/柱间距。")

    tess = find_tess()
    if args.expect and tess:
        env = dict(os.environ)
        td = set_tessdata(env)
        if not td:
            print("[!] 未找到 tessdata 目录，跳过 OCR")
        else:
            print(f"\n[i] OCR 回读（tesseract={tess}, tessdata={td}）")
            hits = {}
            for psm in ("11", "6"):
                r = subprocess.run([tess, args.png, "-", "--psm", psm],
                                   capture_output=True, text=True,
                                   encoding="utf-8", errors="ignore", env=env)
                txt = r.stdout
                for tok in args.expect:
                    if tok in txt:
                        hits.setdefault(tok, psm)
            miss = [t for t in args.expect if t not in hits]
            for tok in args.expect:
                print(f"    {'OK ' if tok in hits else 'MISS'} {tok}"
                      + (f"  (psm{hits[tok]})" if tok in hits else ""))
            print(f"    -> {len(args.expect)-len(miss)}/{len(args.expect)} 命中"
                  + (f"，缺: {miss}" if miss else ""))
    elif args.expect:
        print("[!] 未找到 tesseract，跳过 OCR 回读")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
