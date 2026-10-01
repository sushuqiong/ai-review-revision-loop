#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 PubMed E-utilities 查候选审稿人的**已发表通讯作者邮箱**。

为什么需要它：本用户会直接质问「他们的邮箱你不会直接帮我查询吗？」
——建议审稿人名单里**留空邮箱是不合格的**。但**绝不能编造**邮箱。
本脚本取的是论文 PDF/记录里印出的对应作者邮箱（`<Affiliation>` 字段内），
属公开学术信息，可溯源到具体 PMID。

用法：
    # 1) 先按"作者姓 + 主题"模糊定位，看命中哪几篇、邮箱是什么
    python pubmed_reviewer_email_lookup.py --author "Shabanzadeh DM" --topic "gallstone formation"

    # 2) 已知 PMID 时直接取
    python pubmed_reviewer_email_lookup.py --pmid 15105181 16844493

    # 3) 批量：每行 "候选人姓名 | 检索式"
    python pubmed_reviewer_email_lookup.py --batch candidates.txt

输出：控制台表 + `--json out.json`（含 pmid / title / emails / affiliations / authors），
便于直接把"姓名 + 单位 + 邮箱"写进审稿人名单。

诚实规则（脚本本身无法判断，由使用者负责）：
  * 只报告 XML 里**真实存在**的邮箱；查不到就明确写"未印出，需查机构主页"，**不要猜**。
  * 若命中的论文通讯作者是同组的资深作者（如 `caguilarsalinas@yahoo.com` 对应
    Bello-Chavolla 的 METS-IR 论文），要在报告里**注明这是该文的通讯作者而非本人**。
  * 检索式过宽会命中完全无关的论文（本脚本第一版就曾把 Pepe/Cook 查成别的文章）。
    务必用 `[au]` 字段标签 + 主题词，并**核对返回的标题**再采信邮箱。
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

# 过滤掉出版方/数据库的通用邮箱，它们不是作者本人
DROP_RE = re.compile(
    r"nlm|ncbi|elsevier|springer|wiley|oup\b|bentham|frontiers|"
    r"submission|editorial|permissions|journals?@",
    re.I,
)
MAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
AFF_RE = re.compile(r"<Affiliation>([^<]{0,200})")
TITLE_RE = re.compile(r"<ArticleTitle>(.*?)</ArticleTitle>", re.S)
AUTH_RE = re.compile(r"<LastName>([^<]+)</LastName>\s*<ForeName>([^<]*)</ForeName>")
AUTH_RE = re.compile(r"<LastName>([^<]+)</LastName>\s*<ForeName>([^<]*)</ForeName>")
PMID_RE = re.compile(r"<PMID[^>]*>(\d+)</PMID>")


def _get(url, timeout=40, retries=3):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")
        except Exception as exc:  # 网络抖动重试，而非直接失败
            last = exc
            time.sleep(1.5 * (i + 1))
    raise RuntimeError("E-utilities 请求失败：%s" % last)


def esearch(term, retmax=6, sort="relevance"):
    url = (EUTILS + "esearch.fcgi?db=pubmed&retmode=json&retmax=%d&sort=%s&term=%s"
           % (retmax, sort, urllib.parse.quote(term)))
    data = json.loads(_get(url))
    return data.get("esearchresult", {}).get("idlist", [])


def efetch(pmid):
    return _get(EUTILS + "efetch.fcgi?db=pubmed&retmode=xml&id=%s" % pmid)


def parse(xml, pmid=""):
    mails = sorted({m for m in MAIL_RE.findall(xml) if not DROP_RE.search(m)})
    t = TITLE_RE.search(xml)
    title = re.sub(r"<[^>]+>", "", t.group(1)).strip() if t else ""
    title = re.sub(r"\s+", " ", title)
    affs = [re.sub(r"\s+", " ", a).strip() for a in AFF_RE.findall(xml)]
    authors = ["%s %s" % (ln, fn) for ln, fn in AUTH_RE.findall(xml)]
    return {
        "pmid": pmid or (PMID_RE.search(xml).group(1) if PMID_RE.search(xml) else ""),
        "title": title,
        "emails": mails,
        "affiliations": affs[:3],
        "authors": authors[:6],
    }


def lookup(term, retmax=6, verbose=True):
    """返回 [(pmid, record)]；第一个含邮箱的即为可采信项。"""
    out = []
    for pmid in esearch(term, retmax=retmax):
        try:
            rec = parse(efetch(pmid), pmid)
        except Exception as exc:
            if verbose:
                print("    ! PMID %s 抓取失败：%s" % (pmid, exc))
            continue
        out.append((pmid, rec))
        time.sleep(0.4)  # 尊重 NCBI 频率限制
    return out


def report(label, term, retmax=6, as_json=False):
    print("=" * 78)
    print("■ %s" % label)
    print("  检索式：%s" % term)
    rows = lookup(term, retmax=retmax)
    hit = None
    for pmid, rec in rows:
        if rec["emails"]:
            hit = (pmid, rec)
            break
    if hit:
        pmid, rec = hit
        print("  ✅ 邮箱：%s" % "; ".join(rec["emails"][:3]))
        print("     PMID %s | %s" % (pmid, rec["title"][:90]))
        if rec["authors"]:
            print("     作者(前4)：%s" % "; ".join(rec["authors"][:4]))
        if rec["affiliations"]:
            print("     单位：%s" % rec["affiliations"][0][:150])
        print("     ⚠️ 核对标题/作者是否确为该候选人本人的论文，再采信邮箱。")
    else:
        print("  ❌ 本次检索的 %d 篇 PubMed 记录中**未印出邮箱**。" % len(rows))
        print("     → 如实写「需查机构主页」，不要猜测。可改标题字段精确检索：")
        print('        --topic "确切论文标题"  或  --pmid <已知PMID>')
    if as_json:
        return {"label": label, "term": term, "rows": [r for _, r in rows]}
    return None


def main():
    ap = argparse.ArgumentParser(description="查候选审稿人的已发表通讯作者邮箱")
    ap.add_argument("--author", help="作者姓，如 'Lumley T'（会自动加 [au] 字段标签）")
    ap.add_argument("--topic", help="主题/标题关键词")
    ap.add_argument("--pmid", nargs="*", help="已知 PMID，直接取")
    ap.add_argument("--batch", help="批量文件：每行 '姓名 | 检索式'，忽略 # 注释")
    ap.add_argument("--retmax", type=int, default=6, help="每次检索取前 N 篇（默认 6）")
    ap.add_argument("--json", help="把结果另存为 JSON")
    a = ap.parse_args()

    collected = []
    if a.pmid:
        for pmid in a.pmid:
            rec = parse(efetch(pmid), pmid)
            print("=" * 78)
            print("■ PMID %s" % pmid)
            print("  标题：%s" % rec["title"][:100])
            print("  邮箱：%s" % ("; ".join(rec["emails"]) or "（未印出）"))
            if rec["affiliations"]:
                print("  单位：%s" % rec["affiliations"][0][:160])
            collected.append({"label": "PMID " + pmid, "term": "", "rows": [rec]})
            time.sleep(0.4)

    if a.batch:
        with open(a.batch, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                label, _, term = line.partition("|")
                if not term:
                    print("跳过无法解析的行：%s" % line)
                    continue
                r = report(label.strip(), term.strip(), a.retmax, as_json=True)
                if r:
                    collected.append(r)

    if a.author or a.topic:
        parts = []
        if a.author:
            parts.append("%s[au]" % a.author)
        if a.topic:
            parts.append(a.topic)
        term = " AND ".join(parts)
        r = report(a.author or a.topic, term, a.retmax, as_json=True)
        if r:
            collected.append(r)

    if not collected:
        ap.print_help()
        return 1

    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(collected, fh, ensure_ascii=False, indent=2)
        print("\n已写出 %s" % a.json)
    print("\n提示：把结果写进审稿人名单时，按《journal-submission-compliance.md》§七 的形态"
          "（中文导航 + 英文可提交字段），并**不要把审稿人写进 Cover letter**。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
