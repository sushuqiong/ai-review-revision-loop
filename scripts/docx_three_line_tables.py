# -*- coding: utf-8 -*-
"""Convert all tables in .docx files to academic three-line (booktabs) style.

Usage:
    python docx_three_line_tables.py [root_dir]
    # root_dir defaults to '.'; walks recursively, converts every .docx found.
    # Run with D:\\ProgramData\\python.exe on the user's Windows machine.

Three-line table spec (user's default for academic deliverables):
    - top rule:   1.75pt  (w:sz=14)
    - header rule:0.75pt  (w:sz=6), under the first (header) row only
    - bottom rule:1.75pt  (w:sz=14)
    - no vertical rules, no interior horizontal rules
    - strips Table Grid / tblStyle so the style can't re-add grid lines

Notes / pitfalls:
    - Must remove existing w:tblBorders BEFORE appending new ones, or Word
      keeps the old border set.
    - Must remove w:tblStyle (e.g. "Table Grid") or the grid lines return.
    - Header row: iterate table.rows[0].cells, dedupe by id(cell._tc) because
      merged cells repeat the same tc object.
    - Visual verification: LibreOffice headless render to PDF
      `soffice --headless --convert-to pdf --outdir <dir> file.docx`
      (output lands in Windows Temp if you pass an MSYS /tmp path), then
      pymupdf screenshot + vision check for exactly three horizontal rules.
"""
import os
import sys

from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def set_three_line_borders(table, top_sz=14, header_sz=6, bottom_sz=14):
    tbl = table._tbl
    tblPr = tbl.tblPr

    # 1) strip style that may force grid lines (e.g. "Table Grid")
    tblStyle = tblPr.find(qn("w:tblStyle"))
    if tblStyle is not None:
        tblPr.remove(tblStyle)

    # 2) remove existing border element before rebuilding
    old = tblPr.find(qn("w:tblBorders"))
    if old is not None:
        tblPr.remove(old)

    # 3) top + bottom rules; everything else nil
    borders = OxmlElement("w:tblBorders")
    for edge, sz in (("top", top_sz), ("bottom", bottom_sz)):
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(sz))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    for edge in ("left", "right", "insideH", "insideV"):
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), "nil")
        borders.append(el)
    tblPr.append(borders)

    # 4) header mid-rule: bottom border on every cell of the first row
    if len(table.rows) > 0:
        seen = set()
        for cell in table.rows[0].cells:
            if id(cell._tc) in seen:
                continue
            seen.add(id(cell._tc))
            tcPr = cell._tc.get_or_add_tcPr()
            old_tc = tcPr.find(qn("w:tcBorders"))
            if old_tc is not None:
                tcPr.remove(old_tc)
            tcB = OxmlElement("w:tcBorders")
            bottom = OxmlElement("w:bottom")
            bottom.set(qn("w:val"), "single")
            bottom.set(qn("w:sz"), str(header_sz))
            bottom.set(qn("w:space"), "0")
            bottom.set(qn("w:color"), "000000")
            tcB.append(bottom)
            tcPr.append(tcB)


def process_file(path):
    import docx  # import here so --help doesn't require python-docx
    d = docx.Document(path)
    n = 0
    for t in d.tables:
        set_three_line_borders(t)
        n += 1
    if n:
        d.save(path)
    return n


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    total_files = total_tables = 0
    for dirpath, dirnames, filenames in os.walk(root):
        if "__pycache__" in dirnames:
            dirnames.remove("__pycache__")
        for fn in sorted(filenames):
            if fn.endswith(".docx"):
                p = os.path.join(dirpath, fn)
                n = process_file(p)
                if n:
                    total_files += 1
                    total_tables += n
                    print(f"OK {os.path.relpath(p, root)}: {n} tables")
    print(f"\nConverted {total_files} files, {total_tables} tables to three-line style.")


if __name__ == "__main__":
    main()
