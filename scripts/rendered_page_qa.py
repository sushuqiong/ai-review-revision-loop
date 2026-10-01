#!/usr/bin/env python3
"""渲染级页面质检：词框越界 + 文字重叠。收工前两个数都必须是 0。

用法:  python rendered_page_qa.py 稿.pdf [补充材料.pdf ...] [--overlap-ratio 0.45]
依赖:  pip install pymupdf

背景（见 references/rendered-page-and-package-qa.md）：字符数/文本级检查既误报又漏真问题；
这是 vision 模型不可用时证明「无裁切、无压字」的硬证据。实测 SI PDF 39 页 8623 词 → 0 / 0。
"""
import argparse, sys

ap = argparse.ArgumentParser()
ap.add_argument("pdfs", nargs="+")
ap.add_argument("--overlap-ratio", type=float, default=0.45)
ap.add_argument("--min-px", type=float, default=2.0)
a = ap.parse_args()

try:
    import fitz
except ImportError:
    sys.exit("需要 pymupdf: pip install pymupdf")

total_bad = total_ovl = 0
for pdf in a.pdfs:
    doc = fitz.open(pdf)
    bad, ovl, words_n, pages = [], [], 0, 0
    for pno, page in enumerate(doc, 1):
        pages += 1
        W, H = page.rect.width, page.rect.height
        ws = page.get_text("words")
        words_n += len(ws)
        for x0, y0, x1, y1, t, *_ in ws:
            if x1 > W - 1 or y1 > H - 1 or x0 < 1 or y0 < 1:
                bad.append((pno, t.strip()[:30]))
        for i in range(len(ws)):
            for j in range(i + 1, min(i + 6, len(ws))):
                ix = min(ws[i][2], ws[j][2]) - max(ws[i][0], ws[j][0])
                iy = min(ws[i][3], ws[j][3]) - max(ws[i][1], ws[j][1])
                if ix > a.min_px and iy > a.min_px:
                    A = (ws[i][2] - ws[i][0]) * (ws[i][3] - ws[i][1])
                    B = (ws[j][2] - ws[j][0]) * (ws[j][3] - ws[j][1])
                    if (ix * iy) / max(1e-6, min(A, B)) > a.overlap_ratio:
                        ovl.append((pno, ws[i][4].strip()[:20], ws[j][4].strip()[:20]))
    doc.close()
    total_bad += len(bad); total_ovl += len(ovl)
    print(f"{pdf}: pages {pages} words {words_n} | overflow {len(bad)} | overlapping pairs {len(ovl)}")
    for x in bad[:8]:
        print("   overflow:", x)
    for x in ovl[:8]:
        print("   overlap:", x)

print(f"\nsummary: overflow {total_bad} | overlap {total_ovl}")
sys.exit(1 if (total_bad or total_ovl) else 0)
