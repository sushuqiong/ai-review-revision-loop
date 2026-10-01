#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""verify_manuscript_structure.py — 手稿 docx 的渲染级验收闸门（结构 + 图件 OCR）。

用法:
    python verify_manuscript_structure.py <folder> <docx1> [docx2 ...]
例:
    python verify_manuscript_structure.py "C:/Users/me/Desktop/V17" Manuscript_v17.docx Manuscript_v17_ANON.docx

做四件事（全部基于"渲染后"的真实版式，而不是文档内部 XML 顺序）:
  1) docx -> PDF (LibreOffice headless)
  2) 结构断言: Supplementary material 标题在 S1 之前; S1..Sn 位置单调递增;
              Tables 在 Table 1. 之前; Figure legends 在 Figure 1. 之前
  3) 逐页图/图注同页检查: 用 page.get_image_info()（勿用 page.get_images(), 后者在
     docx 转出的 PDF 上会返回文档级共享资源, 每页都报同样张数）
  4) 图件文本完整性 (若存在 Figures/*.png): 调 tesseract 二进制(勿依赖 pytesseract,
     其 pandas/numpy ABI 可能直接 import 失败); 断言 "NA (" 出现 0 次, 并报告
     贴边文字(疑似裁切)。旋转的纵轴标题常读不出, 不作为缺陷判据。

退出码: 0=全部通过; 1=有断言失败; 2=环境缺依赖/转换失败。
"""
import os
import re
import sys
import csv
import glob
import io
import struct
import subprocess

try:
    import fitz  # PyMuPDF
except Exception as e:  # pragma: no cover
    print("NEED PyMuPDF (pip install pymupdf):", e)
    sys.exit(2)

SOFFICE_CANDIDATES = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    "/usr/bin/soffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
]
TESS_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    "/usr/bin/tesseract",
]

def find_tool(cands):
    for c in cands:
        if os.path.exists(c):
            return c
    return None

def png_size(path):
    with open(path, "rb") as f:
        head = f.read(33)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", head[16:24])
    return (None, None)

def docx_to_pdf(soffice, folder, docx, tmp):
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp,
                    os.path.join(folder, docx)], check=False, timeout=600)
    pdf = os.path.join(tmp, os.path.splitext(docx)[0] + ".pdf")
    return pdf if os.path.exists(pdf) else None

def check_structure(pdf):
    doc = fitz.open(pdf)
    full = re.sub(r"\s+", " ", "\n".join(doc[i].get_text() for i in range(len(doc))))
    sup = [int(m.group(1)) for m in re.finditer(r"Supplementary Table S(\d+)\.", full)]
    pos = {n: full.rfind(f"Supplementary Table S{n}.") for n in sorted(set(sup))}
    results = {}
    results["pages"] = len(doc)
    results["supp_heading_before_S1"] = (
        full.find("Supplementary material") >= 0 and
        full.find("Supplementary material") < full.find("Supplementary Table S1.")
    )
    ordered = sorted(pos.items())
    results["supp_order_monotonic"] = all(ordered[i][1] < ordered[i + 1][1] for i in range(len(ordered) - 1))
    results["tables_before_table1"] = full.find("Tables") < full.find("Table 1.")
    results["figlegends_before_fig1"] = full.find("Figure legends") < full.find("Figure 1.")
    results["supp_numbers"] = [n for n, _ in ordered]
    col = []
    for i in range(len(doc)):
        imgs = doc[i].get_image_info()
        if imgs:
            legends = re.findall(r"(?m)^Figure (\d)\.", doc[i].get_text())
            col.append((i + 1, len(imgs), legends))
    results["figure_pages"] = col
    results["figures_without_legend_page"] = [p for p, n, lg in col if not lg]
    doc.close()
    return results

def check_figures(tess, figs_dir):
    out = []
    for p in sorted(glob.glob(os.path.join(figs_dir, "*.png"))):
        res = subprocess.run([tess, p, "stdout", "tsv", "--psm", "11"],
                             capture_output=True, text=True, timeout=300)
        rows = list(csv.DictReader(io.StringIO(res.stdout), delimiter="\t"))
        txt = " ".join((r.get("text") or "").strip() for r in rows if (r.get("text") or "").strip())
        W, H = png_size(p)
        edge = []
        for r in rows:
            t = (r.get("text") or "").strip()
            if not t:
                continue
            try:
                x, y, w, h = int(r["left"]), int(r["top"]), int(r["width"]), int(r["height"])
            except Exception:
                continue
            if W and (x <= 3 or y <= 3 or x + w >= W - 3 or y + h >= H - 3):
                edge.append(t)
        out.append({
            "file": os.path.basename(p),
            "size": f"{W}x{H}",
            "na_garbage": txt.count("NA ("),
            "edge_touching_text": edge[:6],
            "chars": len(txt),
        })
    return out

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    folder, docxs = sys.argv[1], sys.argv[2:]
    soffice = find_tool(SOFFICE_CANDIDATES)
    if not soffice:
        print("LibreOffice not found; cannot render PDF")
        return 2
    tmp = os.path.join(os.path.dirname(os.path.abspath(folder)), "_pdfcheck")
    os.makedirs(tmp, exist_ok=True)
    failed = False
    for docx in docxs:
        pdf = docx_to_pdf(soffice, folder, docx, tmp)
        if not pdf:
            print(f"!! {docx}: PDF conversion failed")
            failed = True
            continue
        r = check_structure(pdf)
        print(f"== {docx}: pages={r['pages']} suppN={r['supp_numbers']}")
        for k in ("supp_heading_before_S1", "supp_order_monotonic", "tables_before_table1", "figlegends_before_fig1"):
            print(f"   {k}: {r[k]}")
            if not r[k]:
                failed = True
        print(f"   figure pages (page, n_images, legends): {r['figure_pages']}")
        if r["figures_without_legend_page"]:
            print(f"   !! images on pages lacking a Figure legend: {r['figures_without_legend_page']}")
            failed = True
    tess = find_tool(TESS_CANDIDATES)
    figs = os.path.join(folder, "Figures")
    if tess and os.path.isdir(figs):
        print("\n-- figure OCR gate --")
        for row in check_figures(tess, figs):
            flag = "" if row["na_garbage"] == 0 else "  !! NA garbage"
            print(f"   {row['file']} {row['size']} chars={row['chars']} NA={row['na_garbage']}"
                  f" edge={row['edge_touching_text']}{flag}")
            if row["na_garbage"]:
                failed = True
    else:
        print("\n(Tesseract or Figures/ not found - figure OCR gate skipped)")
    print("\nRESULT:", "FAIL" if failed else "PASS")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
