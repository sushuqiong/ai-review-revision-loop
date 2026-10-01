#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
figure_label_color_probe.py —— 逐标签颜色探针（定位"白字/浅字不可见"类缺陷）

用途
----
用户说"数字显示不全 / 看不清 / 有几个白色的数字"时，用本脚本 5 分钟内定位：
从 PDF 文字层取每个标签的【精确坐标】，再到同分辨率 PNG 上采样该坐标的最深色。
  - 最深色接近 (17,17,17)/(0,0,0)  -> 深色文字, 可见
  - 最深色 == 柱体/元素填充色        -> 该处没有深色文字 => 标签是白/浅色 => 不可见

为什么必须"按坐标逐标签"
------------------------
整图 OCR 会被【跨面板同名标签】骗过。真实案例: Panel A 的 `8.9% (n=223)` 是白字
不可见, 但 Panel B 有同名同值且正常的深色标签, 于是整图 OCR 命中 -> 误判 A 没问题,
连改两轮都打偏。逐坐标采样没有这个盲区。

依赖: pypdf, Pillow, numpy   (pip install pypdf pillow numpy)

用法
----
python figure_label_color_probe.py FIG.pdf                     # 用同目录同名 PNG
python figure_label_color_probe.py FIG.pdf --png FIG.png
python figure_label_color_probe.py FIG.pdf --dark-max 80       # "深色"阈值(默认80)
python figure_label_color_probe.py FIG.pdf --only 223 194      # 只看含这些子串的标签
python figure_label_color_probe.py FIG.pdf --dump              # 打印全部标签坐标与颜色

退出码: 0 = 所有标签均为深色(可见)；1 = 存在疑似不可见标签
"""
import argparse
import os
import sys

try:
    import numpy as np
    from PIL import Image
    from pypdf import PdfReader
except ImportError as e:  # pragma: no cover
    sys.exit("缺少依赖: %s  (pip install pypdf pillow numpy)" % e)


def pdf_labels(pdf_path):
    """返回 [(x_pt, y_pt, size, text)]，坐标原点左下。cm 优先，全 0 时回退 tm。"""
    page = PdfReader(pdf_path).pages[0]
    w_pt = float(page.mediabox.width)
    h_pt = float(page.mediabox.height)
    out = []

    def visitor(text, cm, tm, fd, fs):
        t = text.strip()
        if not t:
            return
        x, y = (cm[4], cm[5]) if (cm and len(cm) >= 6) else (tm[4], tm[5])
        if x == 0 and y == 0:
            x, y = tm[4], tm[5]
        out.append((float(x), float(y), float(fs), t))

    page.extract_text(visitor_text=visitor)
    return out, w_pt, h_pt


def probe(pdf_path, png_path, dark_max=80, only=None, dump=False, pad=(4, 130, 16, 12)):
    """pad = (left, right, up, down) 采样框相对标签锚点的像素扩展量"""
    labels, w_pt, h_pt = pdf_labels(pdf_path)
    if not labels:
        sys.exit("PDF 文字层为空 —— 该 PDF 的文字可能是路径/栅格化的，改用 OCR 路线")

    im = Image.open(png_path).convert("RGB")
    arr = np.array(im).astype(int)
    H, W, _ = arr.shape
    sx = W / w_pt
    sy = H / h_pt

    rows, invisible = [], []
    for x_pt, y_pt, size, text in labels:
        if only and not any(k in text for k in only):
            continue
        px = int(round(x_pt * sx))
        py = int(round((h_pt - y_pt) * sy))
        l, r, up, dn = pad
        box = arr[max(0, py - up):py + dn, max(0, px - l):px + r]
        if box.size == 0:
            continue
        flat = box.reshape(-1, 3)
        lum = flat.mean(axis=1)
        darkest = tuple(int(v) for v in flat[lum.argmin()])
        is_dark = max(darkest) <= dark_max
        rows.append((px, py, size, darkest, is_dark, text))
        if not is_dark:
            invisible.append(text)

    print("=" * 78)
    print("figure_label_color_probe:  %s" % os.path.basename(pdf_path))
    print("  PNG %dx%d   PDF %.1fx%.1f pt   label=%d   dark_max=%d"
          % (W, H, w_pt, h_pt, len(rows), dark_max))
    print("=" * 78)
    print("%-8s %-8s %-6s %-22s %-6s %s" % ("px", "py", "size", "darkest RGB", "dark?", "text"))
    for px, py, size, darkest, is_dark, text in rows:
        if not dump and is_dark and not only:
            continue
        print("%-8d %-8d %-6.1f %-22s %-6s %s"
              % (px, py, size, str(darkest), "OK" if is_dark else "**NO**", text[:52]))

    if not only and not dump:
        print("\n(仅列出疑似不可见标签；--dump 可看全部)")

    print("-" * 78)
    if invisible:
        print("疑似【不可见/低对比度】标签 %d 个 —— 该处最深色就是元素填充色，" % len(invisible))
        print("说明标签被画成了白/浅色。修法: 改深色 + 单行 + 移到元素外侧, 并抬高 ylim。")
        for t in invisible:
            print("   * %s" % t)
    else:
        print("全部受检标签均为深色文字 -> 未发现白字/浅字缺陷。")
        print("若用户仍报\"看不清\", 改走 crowding 路线:")
        print("  scripts/figure_block_collision_check.py  (连通域最大连续墨迹块)")
    return 1 if invisible else 0


def main():
    ap = argparse.ArgumentParser(description="逐标签颜色探针：定位白字/浅字不可见缺陷")
    ap.add_argument("pdf")
    ap.add_argument("--png", default=None, help="同分辨率 PNG；默认取同名 .png")
    ap.add_argument("--dark-max", type=int, default=80, help="判定为深色的最大通道值(默认80)")
    ap.add_argument("--only", nargs="*", default=None, help="只看含这些子串的标签")
    ap.add_argument("--dump", action="store_true", help="打印全部标签")
    a = ap.parse_args()

    png = a.png or os.path.splitext(a.pdf)[0] + ".png"
    if not os.path.exists(png):
        sys.exit("找不到 PNG: %s  (用 --png 指定)" % png)
    sys.exit(probe(a.pdf, png, a.dark_max, a.only, a.dump))


if __name__ == "__main__":
    main()
