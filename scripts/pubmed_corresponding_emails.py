#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PubMed 通讯作者邮箱检索 —— 用 NCBI E-utilities 从已发表论文里取公开邮箱。

用途：期刊（BMC 系列等）要求 suggested reviewers 尽量给机构邮箱时，
不要留占位符、更不要编造 —— 本脚本从 PubMed 官方记录里取**论文中印出的
通讯作者邮箱**（`<Affiliation>` 字段），可溯源到具体 PMID。

用法
----
    python pubmed_corresponding_emails.py --author "Pepe MS" --hits 4
    python pubmed_corresponding_emails.py --query 'Cook NR[au] AND receiver operating characteristic' --hits 6
    python pubmed_corresponding_emails.py --author "Lumley T" --author "Vickers AJ" --hits 4
    python pubmed_corresponding_emails.py --json out.json --author "Portincasa P"

设计要点 / 踩过的坑（详见 references/suggested-reviewers-and-email-lookup.md）
------------------------------------------------------------------
1. **必须用 `[au]` 作者字段检索**。只按标题检索会返回**完全不相干的论文**
   （实测：查 "Pepe MS limitations odds ratio" 返回一篇腹放线菌病病例报告）。
2. **要逐篇试多个 PMID**，因为某一篇的 XML 可能不含邮箱，同一个人另一篇有。
3. **过滤出版商通用邮箱**（nlm/ncbi/elsevier/springer/wiley/oup/bentham/frontiers/…），
   否则会取到 `epub@benthamscience.net` 这类编辑部地址。
4. **核对返回的标题与你找的人/论文是否对应** —— 脚本会打印标题与作者供人工确认。
5. 取到的邮箱**可能是共同作者/资深作者**而非目标本人（实测：Bello-Chavolla 的
   METS-IR 论文里印的是 Aguilar-Salinas 的邮箱）。**如实标注**，不要张冠李戴。
6. 查不到就**如实说查不到**，给\"去其机构个人主页找\"的指引。**永不编造**。
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

# 出版商 / 编辑部 / 数据库本身的通用邮箱，一律丢弃
JUNK_MAIL = re.compile(
    r"nlm|ncbi|elsevier|springer|wiley|oup\b|oxford|bentham|frontiers|thieme|karger|"
    r"sagepub|tandf|informa|biomedcentral|plos|nature\.com|science\.org|"
    r"editorial|permissions|reprints?@|journals?@|support@|help@",
    re.I,
)

UA = {"User-Agent": "Mozilla/5.0 (compatible; reviewer-email-lookup/1.0)"}


def _get(url: str, timeout: int = 40) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as fh:
        return fh.read().decode("utf-8", "ignore")


def esearch(term: str, retmax: int = 6) -> list:
    """返回 PMID 列表（按相关度）。"""
    q = urllib.parse.quote(term)
    url = f"{EUTILS}esearch.fcgi?db=pubmed&retmax={retmax}&retmode=json&sort=relevance&term={q}"
    try:
        data = json.loads(_get(url))
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as exc:  # noqa: BLE001
        print(f"    [esearch 失败] {exc}", file=sys.stderr)
        return []


def efetch_meta(pmid: str) -> dict:
    """取单篇 XML 的标题 / 作者 / 机构 / 邮箱。"""
    xml = _get(f"{EUTILS}efetch.fcgi?db=pubmed&retmode=xml&id={pmid}")
    title = re.search(r"<ArticleTitle>(.*?)</ArticleTitle>", xml, re.S)
    title = re.sub(r"<[^>]+>", "", title.group(1)).strip() if title else ""
    authors = re.findall(r"<LastName>([^<]+)</LastName>\s*<ForeName>([^<]*)</ForeName>", xml)
    affs = re.findall(r"<Affiliation>([^<]{0,200})", xml)
    mails = {m for m in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", xml)
             if not JUNK_MAIL.search(m)}
    return {"pmid": pmid, "title": title,
            "authors": [f"{a} {b}".strip() for a, b in authors[:6]],
            "affiliations": affs[:2], "emails": sorted(mails)}


def lookup(term: str, hits: int = 6, pause: float = 0.45) -> dict:
    """对一个人/一组检索词，逐篇试到拿到邮箱为止。"""
    pmids = esearch(term, retmax=hits)
    tried = []
    for pmid in pmids:
        meta = efetch_meta(pmid)
        tried.append(meta)
        if meta["emails"]:
            return {"term": term, "found": True, "n_tried": len(tried), **meta}
        time.sleep(pause)
    return {"term": term, "found": False, "n_tried": len(tried),
            "last_title": tried[0]["title"] if tried else "",
            "tried": tried}


def main() -> int:
    ap = argparse.ArgumentParser(description="PubMed 通讯作者邮箱检索")
    ap.add_argument("--author", action="append", default=[],
                    help="作者名，如 'Pepe MS'（可重复；会自动加 [au] 字段）")
    ap.add_argument("--query", action="append", default=[],
                    help="完整 PubMed 检索式（可重复，优先级高于 --author）")
    ap.add_argument("--hits", type=int, default=6, help="每人最多试几篇（默认 6）")
    ap.add_argument("--json", help="把结果写到 JSON 文件")
    args = ap.parse_args()

    terms = list(args.query) + [f"{a}[au]" for a in args.author]
    if not terms:
        ap.print_help()
        return 2

    results = []
    for term in terms:
        print(f"\n■ {term}")
        res = lookup(term, hits=args.hits)
        results.append(res)
        if res["found"]:
            print(f"    邮箱: {'; '.join(res['emails'])}")
            print(f"    PMID: {res['pmid']}  ({res['n_tried']} 篇内命中)")
            print(f"    标题: {res['title'][:95]}")
            if res.get("authors"):
                print(f"    作者: {', '.join(res['authors'][:5])}")
            if res.get("affiliations"):
                print(f"    机构: {res['affiliations'][0][:120]}")
            print("    → 人工确认：标题/作者是否确实是你找的人（可能是共同或资深作者）")
        else:
            print(f"    未找到（已试 {res['n_tried']} 篇，PubMed 未印出邮箱）")
            if res.get("last_title"):
                print(f"    最近一篇: {res['last_title'][:90]}")
            print("    → 如实报告\"查不到\"，指引用户到其机构个人主页找；不要编造")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(results, fh, ensure_ascii=False, indent=2)
        print(f"\n结果已写入 {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
