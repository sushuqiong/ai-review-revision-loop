#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交付前手稿程序化自检（md 真源）。

用法:
    python manuscript_integrity_audit.py <manuscript.md> [--abstract-limit 350] [--terms "9-year cumulative/dynamic AUC,restricted concordance"]

检查项（全部来自真实踩坑，非泛泛而谈）:
 1. 摘要词数 vs 期刊上限（CD/BMC = 350）
 2. 残留标记：旧版本句、修改说明式句子、OCR 类硬伤
 3. 模型标签一致性（Base/M0/M1/M2，无 M-1 残留）
 4. 术语混用（同一指标多种叫法）
 5. 主表/补充表编号与顺序（连续性 + S1..Sn）
 6. 引用：孤儿（未被引）、悬空（被引但无条目）
 7. 图片提及与图注编号互指
 8. 括号配平、重复词、多余空格、转义符
 9. 占位符清单（作者/基金/单位待填）
10. 表格数与图注数汇总
"""
import io
import re
import sys

LEFTOVERS = [
    "four methodological references", "near-equivalent", "no material gain",
    "confirmed the absence", "population-representative", "D-3", "D-2",
    "HOL cholesterol", "0.E", "II0I5", "M-1", "TODO", "MISS", "XXX",
]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    path = sys.argv[1]
    limit = 350
    terms = []
    for i, a in enumerate(sys.argv):
        if a == "--abstract-limit":
            limit = int(sys.argv[i + 1])
        if a == "--terms":
            terms = [t.strip() for t in sys.argv[i + 1].split(",") if t.strip()]
    s = io.open(path, encoding="utf-8").read()
    problems = []

    # 1 abstract length
    i, j = s.find("# Abstract"), s.find("# Background")
    if 0 <= i < j:
        words = len(re.sub(r"[#*]", " ", s[i:j]).split())
        print(f"[abstract] {words} words (limit {limit})")
        if words > limit:
            problems.append(f"abstract {words} words > {limit}")

    # 2 leftovers
    for k in LEFTOVERS:
        n = s.count(k)
        if n:
            print(f"[leftover] {k!r} x{n}")

    # 3/4 labels & terms
    print("[labels]", {k: s.count(k) for k in ["M-1", "Base (age+sex)", "M0", "M1", "M2"]})
    for t in terms:
        n = s.count(t)
        if n:
            problems.append(f"mixed term {t!r} x{n}")

    # 5 tables
    main = re.findall(r"^## Table (\d+)\.", s, re.M)
    supp = re.findall(r"\*\*Supplementary Table S(\d+)\.", s)
    print("[tables]", main, "| supp:", supp)
    if main and [int(x) for x in main] != list(range(1, len(main) + 1)):
        problems.append(f"main table numbering not contiguous: {main}")
    if supp and [int(x) for x in supp] != list(range(1, len(supp) + 1)):
        problems.append(f"supplement ordering not S1..Sn: {supp}")

    # 6 citations
    if "\n# References\n" in s:
        body, rest = s.split("\n# References\n", 1)
        refpart = rest.split("\n# Tables")[0] if "\n# Tables" in rest else rest
        listed = set(int(x) for x in re.findall(r"^(\d+)\. ", refpart, re.M))
        cited = set()
        for m in re.finditer(r"\[(\d+(?:,\d+)*(?:-\d+)?)\]", body):
            for p in re.split(r",", m.group(1)):
                p = p.strip()
                if re.match(r"^\d+-\d+$", p):
                    a, b = map(int, p.split("-"))
                    cited.update(range(a, b + 1))
                elif p.isdigit():
                    cited.add(int(p))
        # ignore obvious non-citation tokens (years / grant numbers)
        cited = {c for c in cited if c <= max(listed | {0})}
        orphan = sorted(listed - cited)
        dangling = sorted(cited - listed)
        print(f"[refs] listed {len(listed)} cited {len(cited)} orphan {orphan} dangling {dangling}")
        if orphan or dangling:
            problems.append(f"citations: orphan {orphan} dangling {dangling}")

    # 7 figures
    ment = sorted(set(re.findall(r"Figure (\d)", s)))
    caps = re.findall(r"\*\*Figure (\d)\.", s)
    print("[figures] mentioned", ment, "captions", caps)

    # 8 mechanics
    print("[mechanics] paren balance", s.count("(") - s.count(")"),
          "| doubled words", sorted(set(re.findall(r"\b([A-Za-z]+)\s+\1\b", s)))[:6],
          "| escapes", len(re.findall(r"\\[\[\]_\*#]", s)))

    # 9 placeholders
    ph = sorted(set(re.findall(r"\[(?:[A-Za-z][^\]]{0,40})\]|\[[^\]]*removed[^\]]*\]", s)))
    print("[placeholders]", ph[:12])

    print("\nRESULT:", "OK" if not problems else "ISSUES -> " + "; ".join(problems))
    return 0 if not problems else 2


if __name__ == "__main__":
    sys.exit(main())
