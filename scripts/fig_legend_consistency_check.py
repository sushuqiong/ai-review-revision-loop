#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""图内文字 vs 正文图注 一致性核查 + "白字白底不可见"诊断。

用法:
  A) 一致性核查:
     python fig_legend_consistency_check.py --figs figdir --manuscript manuscript.docx \
            [--supp "Supplementary Materials.docx"]

  B) 定位"某标签是白字/浅字"缺陷（用户报"数字显示不清/是白色的数字"）:
     python fig_legend_consistency_check.py --probe figure.pdf figure.png \
            --labels "8.9%:129.3,283.1" "n=223:124.0,274.4"

     坐标取自 PDF 文本层（pt）。脚本换算到 PNG 像素后采样该 bbox 的最深色：
       最深色 ≈ 深灰/黑  -> 文字可见
       最深色 = 柱体色    -> 该处没有深色文字 => 白字/浅字问题

设计要点（避免误报，务必读）:
  * 图注里的"图注级信息"本就不上图，未命中属正常: bootstrap B、判别样本量与病例数、CI 方法、自由度。
  * dashed / dotted / solid 指边框或线型，不是图内文字 -> 图内查不到不算矛盾;
    应核对图内"对应块/行是否存在且数值一致"。
  * 图注往往 = 标题段 + 紧随的独立说明段; 只读标题会严重低估长度（实测 25 词 vs 284 词）。
"""
import sys
import os
import re
import argparse

# ---------------------------------------------------------------- 一致性核查

def fig_text(pdf_path):
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("需要 pypdf:  pip install pypdf")
    r = PdfReader(pdf_path)
    return re.sub(r"\s+", " ", " ".join(p.extract_text() for p in r.pages))


def doc_paras(path):
    from docx import Document
    return [p.text.strip() for p in Document(path).paragraphs]


def legend_for(tag, paras):
    """取 'Figure N.' 标题段 + 紧随的非空说明段（直到下一个 Table/Figure 标题）。"""
    for i, t in enumerate(paras):
        if t.startswith(tag + "."):
            out = [t]
            j = i + 1
            while j < len(paras) and not re.match(r"^(Table |Figure )", paras[j] or "x"):
                if paras[j]:
                    out.append(paras[j])
                j += 1
            return " ".join(out)
    return ""


# 图注级信息（本就不上图）—— 命中不了不算问题
EXPECTED_OFF_FIGURE = re.compile(
    r"^(1,?000|2,?846|2,?056|5,?724|296|232|438|5,?290|353|2,?885|2,?092|5,?917|5,?918|458|"
    r"2021|2023|1988|1994|20|74|300|0\.975)$"
)


def consistency(figs_dir, manuscript, supp=None):
    figs = sorted(f for f in os.listdir(figs_dir) if f.lower().endswith(".pdf"))
    mpar = doc_paras(manuscript)
    spar = doc_paras(supp) if supp and os.path.exists(supp) else []
    bad = 0
    for f in figs:
        stem = os.path.splitext(f)[0]
        n = re.search(r"(\d+)", stem)
        if not n:
            continue
        num = n.group(1)
        main_fig = stem.lower().startswith("fig") and "s" not in stem.lower()[:5]
        tag = ("Figure " + num) if main_fig else ("Figure S" + num)
        lg = legend_for(tag, mpar) or legend_for(tag, spar)
        ft = fig_text(os.path.join(figs_dir, f))
        print("=" * 84)
        print("%s  图内 %d 字符 | 图注 %d 词" % (tag, len(ft), len(re.findall(r"\S+", lg))))
        if not lg:
            print("   ⚠️ 未找到图注")
            continue
        nums = {x for x in re.findall(r"\d[\d,\.]*\d|\d", lg) if len(x.replace(",", "")) >= 2 or "." in x}
        miss = []
        for x in sorted(nums):
            if x in ft or x.replace(",", "") in ft.replace(",", ""):
                continue
            if EXPECTED_OFF_FIGURE.match(x):
                continue
            miss.append(x)
        print("   图注数字 %d | 图内未命中且非图注级 %d" % (len(nums), len(miss)))
        if miss:
            bad += 1
            print("   ❗需人工确认: " + ", ".join(miss[:20]))
        else:
            print("   OK")
    print()
    print("疑似不一致的图数: %d / %d" % (bad, len(figs)))


# ------------------------------------------------------- 白字/浅字缺陷探针

def probe(pdf_path, png_path, labels):
    import numpy as np
    from PIL import Image
    from pypdf import PdfReader

    r = PdfReader(pdf_path)
    box = r.pages[0].mediabox
    W_pt, H_pt = float(box.width), float(box.height)
    im = Image.open(png_path).convert("RGB")
    a = np.array(im).astype(int)
    H, W, _ = a.shape
    sx, sy = W / W_pt, H / H_pt
    print("PDF %.1f x %.1f pt | PNG %d x %d px | 缩放 %.4f x %.4f" % (W_pt, H_pt, W, H, sx, sy))
    for lab in labels:
        name, coords = lab.split(":")
        xpt, ypt = [float(v) for v in coords.split(",")]
        px, py = int(round(xpt * sx)), int(round((H_pt - ypt) * sy))
        sub = a[max(0, py - 14):py + 10, max(0, px - 6):px + 130]
        if sub.size == 0:
            print("  %-14s 越界" % name)
            continue
        flat = sub.reshape(-1, 3)
        lum = flat.mean(axis=1)
        darkest = tuple(flat[lum.argmin()])
        print("  %-14s PNG(%4d,%4d) 最深色 RGB%s" % (name, px, py, darkest), end="")
        if max(darkest) < 90:
            print("  -> 文字可见")
        else:
            print("  -> ❗无深色文字（疑似白字/浅字，与填充色同色）")


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--figs")
    ap.add_argument("--manuscript")
    ap.add_argument("--supp")
    ap.add_argument("--probe", nargs=2, metavar=("PDF", "PNG"))
    ap.add_argument("--labels", nargs="*", default=[])
    a = ap.parse_args()
    if a.probe:
        if not a.labels:
            sys.exit("--probe 需配 --labels NAME:xpt,ypt [...]")
        probe(a.probe[0], a.probe[1], a.labels)
    elif a.figs and a.manuscript:
        consistency(a.figs, a.manuscript, a.supp)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
