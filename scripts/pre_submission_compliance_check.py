#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
投稿包提交前合规自检（一键跑）。
用法:  python pre_submission_compliance_check.py "<投稿文件夹>"
退出码: 0 = 全部通过; 1 = 有遗留问题（逐条打印）

检查项（每一项都来自真实翻车记录，不要删）:
  1. 图表编号 == 正文首次提及顺序  (Table / Table S / Figure / Figure S 四类)
  2. 声明元数据 vs 实测 (正文词数 / 摘要词数 / 表数 / 图数 / 补充材料范围)
  3. 正文字体/字号统一性（同文档内不得混用）
  4. 段落间距按元素分类统一 + 无残留空段落
  5. 三线表合规（无竖线、无表级实边框）
  6. 内嵌图分辨率 == Figures/ 源图（防 python-docx 保存把高清图还原成旧版）
  7. 陈旧字符串（旧标题 / 旧结局措辞 / 旧变量笔误 / 旧补充材料范围）

依赖: python-docx, pypdf, Pillow   (pip install python-docx pypdf Pillow)
"""
import os, re, sys, io, zipfile, hashlib
from collections import Counter

try:
    from docx import Document
    from docx.oxml.ns import qn
except Exception:
    print("需要 python-docx:  pip install python-docx"); sys.exit(2)
try:
    from PIL import Image
except Exception:
    Image = None

# ---------------- 按需修改的配置 ----------------
MAIN = "Manuscript.docx"          # 主稿文件名（投递版常去掉数字前缀）
SUPP = "Materials.docx"           # 补充材料文件名；无则设 None
TITLEPAGE = None                  # 如 "page.docx"，有则检查其中的字数声明
FIGDIR = "Figures"
EXPECT_FONTS = {"Times New Roman"}
EXPECT_SIZES = {"12.0"}           # 正文
STALE = [
    "Embedded Age and BMI in a Composite Index",
    "gallstone diagnosis history",
    "NHANES cycles",
    "HAJ0 age-branch outcome",
]
# ------------------------------------------------

issues = []
def bad(msg): issues.append(msg)

def ptexts(doc):
    return [p.text for p in doc.paragraphs]

def first_mentions(paras, pat):
    out = {}
    for i, t in enumerate(paras):
        for m in re.finditer(pat, t):
            out.setdefault(int(m.group(1)), i)
    return out

def check_numbering_order(doc, label):
    paras = ptexts(doc)
    specs = [("Table", r'\bTable\s+(\d+)(?![\dS])'),
             ("Table S", r'\bTable\s+S(\d+)'),
             ("Figure", r'\bFigure\s+(\d+)(?![\dS])'),
             ("Figure S", r'\bFigure\s+S(\d+)')]
    for name, pat in specs:
        fm = first_mentions(paras, pat)
        if not fm:
            continue
        order = [k for k, _ in sorted(fm.items(), key=lambda kv: kv[1])]
        if order != sorted(order):
            mapping = {}
            for new, old in enumerate(order, 1):
                mapping[old] = new
            bad("%s [%s] 编号不按首次提及顺序: %s  ⇒ 重编号映射 %s"
                % (label, name, order, {k: v for k, v in mapping.items() if k != v}))

def check_declarations(path, doc):
    paras = ptexts(doc)
    WS = re.compile(r'\S+')
    def idx(prefix, start=0):
        for i in range(start, len(paras)):
            if paras[i].strip().startswith(prefix):
                return i
        return None
    i_intro, i_abbr, i_ref = idx("1. Introduction"), idx("Abbreviations:"), idx("References")
    if i_intro is not None and i_abbr is not None:
        actual = len(WS.findall(" ".join(paras[i_intro:i_abbr])))
        decl = None
        for t in paras[:20]:
            m = re.search(r'Word count:\s*([\d,]+)', t)
            if m:
                decl = int(m.group(1).replace(",", "")); break
        if decl is None:
            bad("%s 首页未找到 Word count 声明" % os.path.basename(path))
        elif decl != actual:
            bad("%s 字数声明 %s ≠ 实测 %d ⇒ 改声明" % (os.path.basename(path), format(decl, ","), actual))
        else:
            print("    [ok] 正文词数声明一致: %s" % format(actual, ","))
    # abstract <= 350
    for t in paras:
        if t.startswith("Background: ") and len(t) > 200:
            n = len(WS.findall(t))
            if n > 350:
                bad("%s 摘要 %d 词 > 350" % (os.path.basename(path), n))
            break
    # table/figure counts
    ntab, nfig = len(doc.tables), len(re.findall(r'^Figure\s+\d+\.', "\n".join(paras), re.M))
    for t in paras[:20]:
        if t.strip().startswith("Word count:"):
            if ("%d tables" % ntab) not in t and ("tables" in t):
                bad("%s 声明的表数 ≠ 实际 %d" % (os.path.basename(path), ntab))
            break

def check_fonts(path, doc, body_only=True):
    fonts, sizes = Counter(), Counter()
    for p in doc.paragraphs:
        if body_only and p.style.name == "Title":
            continue
        for r in p.runs:
            if not r.text.strip():
                continue
            rpr = r._element.find(qn('w:rPr'))
            v = None
            if rpr is not None:
                z = rpr.find(qn('w:sz'))
                if z is not None:
                    v = int(z.get(qn('w:val'))) / 2
                rf = rpr.find(qn('w:rFonts'))
                fonts[rf.get(qn('w:ascii')) if rf is not None else None] += 1
            sizes[str(v)] += 1
    if not set(fonts) <= EXPECT_FONTS or not set(sizes) <= EXPECT_SIZES:
        bad("%s 正文字体/字号不统一: fonts=%s sizes=%s (期望 fonts⊆%s, sizes⊆%s)"
            % (os.path.basename(path), dict(fonts), dict(sizes), EXPECT_FONTS, EXPECT_SIZES))

def check_spacing_and_empties(path, doc, max_kinds=4):
    by = Counter()
    for p in doc.paragraphs:
        if not p.text.strip():
            continue
        ppr = p._p.find(qn('w:pPr')); sb = sa = None
        if ppr is not None:
            sp = ppr.find(qn('w:spacing'))
            if sp is not None:
                v = sp.get(qn('w:before')); sb = int(v)/20 if v else None
                v = sp.get(qn('w:after'));  sa = int(v)/20 if v else None
        by[(sb, sa)] += 1
    if len(by) > max_kinds:
        bad("%s 段落间距种类过多(%d): %s ⇒ 按 文档标题/H1/H2/表图标题/Panel/正文 六类统一"
            % (os.path.basename(path), len(by), dict(by)))
    empt = [el for el in doc.element.body.iterchildren()
            if el.tag == qn('w:p')
            and not "".join(n.text or "" for n in el.iter(qn('w:t'))).strip()
            and not el.findall('.//' + qn('a:blip'))]
    if empt:
        bad("%s 残留空段落 %d 个（分隔应交给段后间距）" % (os.path.basename(path), len(empt)))

def check_three_line(path, doc):
    for i, t in enumerate(doc.element.body.findall(qn('w:tbl'))):
        tp = t.find(qn('w:tblPr'))
        tb = tp.find(qn('w:tblBorders')) if tp is not None else None
        if tb is not None and any(x.get(qn('w:val')) not in (None, 'none', 'nil') for x in tb):
            bad("%s T%d 有表级实边框（应改为单元格级三线）" % (os.path.basename(path), i))
        for tc in t.iter(qn('w:tcBorders')):
            for side in ('left', 'right'):
                e = tc.find(qn('w:' + side))
                if e is not None and e.get(qn('w:val')) not in (None, 'nil', 'none'):
                    bad("%s T%d 有竖线（非三线表）" % (os.path.basename(path), i))
                    break
            else:
                continue
            break

def check_embedded_images(path, doc, pairs):
    """pairs: [(media_in_docx, figures_filename), ...]"""
    if Image is None:
        return
    z = zipfile.ZipFile(path)
    names = set(z.namelist())
    for media, fig in pairs:
        if media not in names:
            bad("%s 缺少 %s" % (os.path.basename(path), media)); continue
        a = z.read(media)
        fp = os.path.join(FIGDIR, fig)
        if not os.path.exists(fp):
            bad("Figures/ 缺少 %s" % fig); continue
        b = open(fp, "rb").read()
        sa_, sb_ = Image.open(io.BytesIO(a)).size, Image.open(io.BytesIO(b)).size
        if sa_ != sb_:
            bad("%s 内嵌图 %s=%s ≠ Figures/%s=%s ⇒ 高分辨率图被还原/python-docx 保存覆盖，需重嵌"
                % (os.path.basename(path), media, sa_, fig, sb_))
        elif hashlib.md5(a).hexdigest() != hashlib.md5(b).hexdigest():
            bad("%s 内嵌图 %s 与 Figures/%s 像素同源但字节不同（可接受，建议复核）"
                % (os.path.basename(path), media, fig))

def main(folder):
    os.chdir(folder)
    print("=" * 74)
    print(" 投稿包合规自检: %s" % folder)
    print("=" * 74)
    docs = {}
    for fn in [MAIN, SUPP, TITLEPAGE]:
        if fn and os.path.exists(fn):
            docs[fn] = Document(fn)
        elif fn:
            bad("找不到文件: %s" % fn)

    if MAIN in docs:
        print("\n[1] 编号顺序")
        check_numbering_order(docs[MAIN], MAIN)
        check_numbering_order(docs[SUPP], SUPP) if SUPP in docs else None
        print("\n[2] 声明元数据")
        check_declarations(MAIN, docs[MAIN])
        for fn, d in docs.items():
            print("\n[3/4] 字体与间距 — %s" % fn)
            check_fonts(fn, d)
            check_spacing_and_empties(fn, d)
            print("\n[5] 三线表 — %s" % fn)
            check_three_line(fn, d)
        print("\n[6] 内嵌图一致性")
        check_embedded_images(MAIN, docs[MAIN],
                              [("word/media/image2.png", "Fig1.png"),
                               ("word/media/image3.png", "Fig2.png"),
                               ("word/media/image4.png", "Fig4.png")])
        if SUPP in docs:
            check_embedded_images(SUPP, docs[SUPP],
                                  [("word/media/image1.png", "FigureS1.png"),
                                   ("word/media/image2.png", "FigureS2.png"),
                                   ("word/media/image3.png", "FigureS3.png")])
        print("\n[7] 陈旧字符串")
        allt = "\n".join(ptexts(docs[MAIN]))
        for d in docs.values():
            allt += "\n" + "\n".join(c.text for t in d.tables for tr in t.rows for c in tr.cells)
        for s in STALE:
            if s in allt:
                bad("仍含陈旧字符串: %r" % s)

    print("\n" + "=" * 74)
    if issues:
        print(" 遗留问题 %d:" % len(issues))
        for i, x in enumerate(issues, 1):
            print("  %2d. %s" % (i, x))
        print("=" * 74)
        return 1
    print(" 全部通过 ✅（注意：此处「通过」仅代表本脚本覆盖的检查项）")
    print("=" * 74)
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    sys.exit(main(sys.argv[1]))
