#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""像素密度检查：客观诊断图表"大片空白/布局松散/左右留白过大"。

用法:
    python pixel_blank_check.py <image.png> [blank_threshold]

输出:
    - 图像尺寸
    - 最大连续空白行块（px 与占高 %）、最大连续空白列块（占宽 %）
    - 内容覆盖垂直/水平范围 + 上下左右留白
    - 空白块清单（前 5 个）

判定标准（本技能经验值）:
    - 上下/左右留白合计宜 < 15%
    - 内容应覆盖 >= 85% 画布
    - 单一空白块 > 20% 高度 = 必须修（流程图中通常是列内容与底部注释之间的空隙）

依赖: pip install pillow numpy
"""
import sys
import numpy as np
from PIL import Image


def max_block(sorted_idx):
    """输入递增索引列表，返回最大连续块长度。"""
    if not sorted_idx:
        return 0
    mx = cur = 1
    for i in range(1, len(sorted_idx)):
        if sorted_idx[i] == sorted_idx[i - 1] + 1:
            cur += 1
            mx = max(mx, cur)
        else:
            cur = 1
    return mx


def blank_blocks(sorted_idx):
    """输入递增索引列表，返回连续空白块 [(start, end), ...] 按长度降序。"""
    if not sorted_idx:
        return []
    blocks = []
    start = prev = sorted_idx[0]
    for b in sorted_idx[1:]:
        if b == prev + 1:
            prev = b
        else:
            blocks.append((start, prev))
            start = prev = b
    blocks.append((start, prev))
    blocks.sort(key=lambda x: x[1] - x[0], reverse=True)
    return blocks


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.005

    arr = np.array(Image.open(path).convert("L"))
    h, w = arr.shape
    nonwhite = arr < 245
    row_density = nonwhite.mean(axis=1)
    col_density = nonwhite.mean(axis=0)

    blank_rows = [i for i in range(h) if row_density[i] < threshold]
    blank_cols = [j for j in range(w) if col_density[j] < threshold]

    print(f"图像: {w}x{h}")
    print(f"最大连续空白行: {max_block(blank_rows)}px ({max_block(blank_rows)/h*100:.1f}% 高度)")
    print(f"最大连续空白列: {max_block(blank_cols)}px ({max_block(blank_cols)/w*100:.1f}% 宽度)")

    rows_nz = np.where(nonwhite.any(axis=1))[0]
    cols_nz = np.where(nonwhite.any(axis=0))[0]
    if len(rows_nz) > 0:
        print(f"内容垂直范围: {rows_nz[0]}-{rows_nz[-1]} ({(rows_nz[-1]-rows_nz[0]+1)}px / {h}px, 覆盖 {(rows_nz[-1]-rows_nz[0]+1)/h*100:.1f}%)")
        print(f"内容水平范围: {cols_nz[0]}-{cols_nz[-1]} ({(cols_nz[-1]-cols_nz[0]+1)}px / {w}px, 覆盖 {(cols_nz[-1]-cols_nz[0]+1)/w*100:.1f}%)")
        print(f"上空白: {rows_nz[0]}px | 下空白: {h-rows_nz[-1]-1}px | 左空白: {cols_nz[0]}px | 右空白: {w-cols_nz[-1]-1}px")

    rb = blank_blocks(blank_rows)
    print("\n最大空白块 (行):")
    for b in rb[:5]:
        print(f"  y={b[0]}-{b[1]} ({b[1]-b[0]+1}px, {(b[1]-b[0]+1)/h*100:.1f}%)")


if __name__ == "__main__":
    main()
