#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""三线表格式修复（写回文件；自动备份到同目录 _bak/）。

用法:
    python docx_table_format_fix.py "manuscript.docx" [--sz 18] [--target auto]

动作（只改格式，绝不改内容）:
  ① 末行补底部封闭线 bottom(single,12)
  ② 每个无 w:sz 的 run 补显式字号（--sz，默认 18 = 9.0pt；w:sz 单位是半磅）
  ③ 宽度超可用宽的表按比例缩放到基准值（--target，默认自动取"该文档多数表的宽度和"）

⚠️ 先跑 docx_table_format_audit.py 看清单，改完再跑一遍复验。
⚠️ 改后必须另做"数值零改动"校验：比对改前/改后每个 table cell 的 .text 列表逐字一致。
"""
import sys
import os
import shutil

try:
    from docx import Document
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except ImportError:
    sys.exit("需要 python-docx:  pip install python-docx")


def set_border(tcPr, tag, val="single", sz="12"):
    tb = tcPr.find(qn("w:tcBorders"))
    if tb is None:
        tb = OxmlElement("w:tcBorders")
        tcPr.append(tb)
    el = tb.find(qn("w:" + tag))
    if el is None:
        el = OxmlElement("w:" + tag)
        tb.append(el)
    el.set(qn("w:val"), val)
    el.set(qn("w:sz"), sz)
    el.set(qn("w:space"), "0")
    el.set(qn("w:color"), "000000")


def bottom_ok(cell):
    tcPr = cell.find(qn("w:tcPr"))
    if tcPr is None:
        return False
    tb = tcPr.find(qn("w:tcBorders"))
    if tb is None:
        return False
    b = tb.find(qn("w:bottom"))
    if b is None:
        return False
    return (b.get(qn("w:val")) or "").lower() not in ("nil", "none", "")


def ensure_tcPr(c):
    tcPr = c.find(qn("w:tcPr"))
    if tcPr is None:
        tcPr = OxmlElement("w:tcPr")
        c.insert(0, tcPr)
    return tcPr


def fix(path, sz_half_pt=18, target=None):
    bak = os.path.join(os.path.dirname(path), "_bak")
    os.makedirs(bak, exist_ok=True)
    shutil.copy2(path, os.path.join(bak, os.path.basename(path) + ".pre_tblfix"))
    print("已备份 -> _bak/%s.pre_tblfix" % os.path.basename(path))

    d = Document(path)
    sec = d.sections[0]
    avail_tw = int((sec.page_width - sec.left_margin - sec.right_margin) / 635)  # EMU -> twips

    if target is None:
        sums = []
        for t in d.tables:
            g = t._tbl.find(qn("w:tblGrid"))
            if g is not None:
                sums.append(sum(int(x.get(qn("w:w")) or 0) for x in g.findall(qn("w:gridCol"))))
        target = max(set(sums), key=sums.count) if sums else avail_tw
        target = min(target, avail_tw)
    print("基准宽度 = %d twips (%.2f cm) | 可用 = %d twips (%.2f cm)"
          % (target, target / 1440 * 2.54, avail_tw, avail_tw / 1440 * 2.54))

    n_border = n_sz = n_width = 0
    for i, t in enumerate(d.tables, 1):
        el = t._tbl
        rows = el.findall(qn("w:tr"))
        if not rows:
            continue

        # ① 末行底线
        for c in rows[-1].findall(qn("w:tc")):
            if not bottom_ok(c):
                set_border(ensure_tcPr(c), "bottom", "single", "12")
                n_border += 1

        # ② 显式字号
        for r in rows:
            for c in r.findall(qn("w:tc")):
                for p in c.findall(qn("w:p")):
                    for run in p.findall(qn("w:r")):
                        rp = run.find(qn("w:rPr"))
                        if rp is None:
                            rp = OxmlElement("w:rPr")
                            run.insert(0, rp)
                        if rp.find(qn("w:sz")) is None:
                            for tag in ("w:sz", "w:szCs"):
                                e = OxmlElement(tag)
                                e.set(qn("w:val"), str(sz_half_pt))
                                rp.append(e)
                            n_sz += 1

        # ③ 宽度收回
        grid = el.find(qn("w:tblGrid"))
        if grid is not None:
            old = [int(g.get(qn("w:w")) or 0) for g in grid.findall(qn("w:gridCol"))]
            if sum(old) > target + 20:
                k = target / sum(old)
                new = [max(700, int(round(x * k))) for x in old]
                new[-1] += target - sum(new)
                for g, v in zip(grid.findall(qn("w:gridCol")), new):
                    g.set(qn("w:w"), str(v))
                for r in rows:
                    for c, v in zip(r.findall(qn("w:tc")), new):
                        tcPr = ensure_tcPr(c)
                        w = tcPr.find(qn("w:tcW"))
                        if w is None:
                            w = OxmlElement("w:tcW")
                            tcPr.append(w)
                        w.set(qn("w:w"), str(v))
                        w.set(qn("w:type"), "dxa")
                n_width += 1
                print("   Table %d: %d -> %d twips" % (i, sum(old), sum(new)))

    d.save(path)
    print()
    print("修复: 补底线 %d 处 | 补字号 %d 处 | 宽度收回 %d 个表" % (n_border, n_sz, n_width))
    print("⚠️ 接着必须做数值零改动校验（cell.text 列表逐字比对），并重跑 audit 脚本复验。")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = [a for a in sys.argv[1:] if a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    sz = 18
    tgt = None
    for o in opts:
        if o.startswith("--sz="):
            sz = int(o.split("=")[1])
        elif o.startswith("--target="):
            tgt = int(o.split("=")[1])
    for p in args:
        fix(p, sz, tgt)


if __name__ == "__main__":
    main()
