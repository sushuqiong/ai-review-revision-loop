#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""三线表格式体检（只读，不改文件）。

用法:
    python docx_table_format_audit.py "manuscript.docx" [other.docx ...]

逐表检查并报告:
  ① 表格宽度 vs 页面可用宽度  ② 末行底部封闭线  ③ 单元格显式字号
  ④ 表格样式 / 底纹(w:shd)     ⑤ 表格内容词数

判定基准（v19 课题2 实测值，换项目时按自己的稿子设）:
  主稿   边距 2.54 cm -> 可用 15.93 cm
  补充材料 边距 2.00 cm -> 可用 17.00 cm
  BMC 印刷整页宽 170 mm (6.69 in)，非 docx 页宽，勿混用。

退出码: 0 = 全部合格; 1 = 有不合格项。
"""
import sys
import os
import re

try:
    from docx import Document
    from docx.oxml.ns import qn
except ImportError:
    sys.exit("需要 python-docx:  pip install python-docx")


def borders_of(cell):
    """返回该单元格 tcBorders 的 {边: (val, sz)}；无则 {}"""
    out = {}
    tcPr = cell.find(qn("w:tcPr"))
    if tcPr is None:
        return out
    tb = tcPr.find(qn("w:tcBorders"))
    if tb is None:
        return out
    for e in tb.iterchildren():
        tag = e.tag.split("}")[1]
        out[tag] = (e.get(qn("w:val")), e.get(qn("w:sz")))
    return out


def has_line(bmap, side):
    v = bmap.get(side)
    if not v:
        return False
    return (v[0] or "").lower() not in ("nil", "none", "")


def audit(path):
    d = Document(path)
    sec = d.sections[0]
    avail_cm = (sec.page_width - sec.left_margin - sec.right_margin) / 360000  # EMU -> cm
    print("=" * 84)
    print(os.path.basename(path))
    print("  页面 %.2f cm | 边距 %.2f/%.2f cm | 可用宽 %.2f cm | 表数 %d"
          % (sec.page_width.cm, sec.left_margin.cm, sec.right_margin.cm,
             avail_cm, len(d.tables)))
    print("=" * 84)

    bad = 0
    for i, t in enumerate(d.tables, 1):
        el = t._tbl
        grid = el.find(qn("w:tblGrid"))
        ws = [int(g.get(qn("w:w")) or 0) for g in grid.findall(qn("w:gridCol"))] if grid is not None else []
        w_cm = sum(ws) / 1440 * 2.54

        rows = el.findall(qn("w:tr"))
        head = borders_of(rows[0].findall(qn("w:tc"))[0]) if rows else {}
        last = borders_of(rows[-1].findall(qn("w:tc"))[0]) if rows else {}

        # 显式字号：统计没有 w:sz 的 run 数
        nosz = 0
        szs = set()
        for r in rows:
            for c in r.findall(qn("w:tc")):
                for p in c.findall(qn("w:p")):
                    for run in p.findall(qn("w:r")):
                        rp = run.find(qn("w:rPr"))
                        if rp is None or rp.find(qn("w:sz")) is None:
                            nosz += 1
                        else:
                            szs.add(int(rp.find(qn("w:sz")).get(qn("w:val"))) / 2)

        st = el.find(qn("w:tblPr") + "/" + qn("w:tblStyle"))
        style = st.get(qn("w:val")) if st is not None else "(none)"
        shd = len(list(el.iter(qn("w:shd"))))

        over = w_cm > avail_cm + 0.05
        no_bottom = not has_line(last, "bottom")
        no_size = nosz > 0
        shade = shd > 0
        ok = not (over or no_bottom or no_size or shade)
        if not ok:
            bad += 1

        print("Table %-2d  %2d行 x %2d列" % (i, len(rows), len(ws)))
        print("   宽 %.2f cm (%.2f twips)  %s"
              % (w_cm, sum(ws), "超宽!" if over else "OK"))
        print("   首行 top=%s bottom=%s" % (head.get("top"), head.get("bottom")))
        print("   末行 bottom=%s  %s" % (last.get("bottom"), "缺底线!" if no_bottom else ""))
        print("   字号 %s | 无显式字号的 run = %d %s"
              % (sorted(szs) or "[]", nosz, "<- 需补" if no_size else ""))
        print("   样式 %s | w:shd %d %s" % (style, shd, "<- BMC 禁着色" if shade else ""))
        print("   => %s" % ("OK" if ok else "需修"))
        print("-" * 84)

    print("不合格表数: %d / %d" % (bad, len(d.tables)))
    return bad


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    total = sum(audit(p) for p in sys.argv[1:] if os.path.exists(p))
    print()
    print("总计不合格: %d" % total)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
