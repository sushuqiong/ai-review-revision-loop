#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Harvest citation metadata for a manuscript/reference list, with hard validation gates.

Why this exists: reference lists built from memory produce wrong DOIs, wrong years and (worst)
correction notices instead of the real paper. This script only accepts metadata returned by PubMed
E-utilities / Crossref, and rejects any candidate that fails a validation gate.

Usage
    python harvest_reference_metadata.py --out refs.json --pmids 17496320,28810144 ...
    python harvest_reference_metadata.py --out refs.json --targets targets.json

targets.json format (Crossref path, title-similarity + journal/year gates):
    {"gsva":  {"title": "GSVA gene set variation analysis for microarray and RNA-seq data",
               "journal": ["bmc bioinformatics"], "years": [2012, 2014]},
     "tcga_luad": {"title": "Comprehensive molecular profiling of lung adenocarcinoma",
               "journal": ["nature"], "years": [2013, 2015],
               "collective_author": "The Cancer Genome Atlas Research Network"}}

Output: {"pmid": {...}, "crossref": {...}, "unresolved": [...]}
Nothing is invented: an entry that fails validation is reported as unresolved and left out.
"""
import argparse, difflib, json, subprocess, sys, time, urllib.parse

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
UA = "egfr-resource-build/1.0 (mailto:corresponding@example.com)"   # Crossref asks for a contact address


def _curl(url, timeout=60):
    return subprocess.run(["curl", "-sS", "--max-time", str(timeout), "-A", UA, url],
                          capture_output=True, text=True).stdout


def eutils(path, **params):
    return _curl(EUTILS + path + "?" + urllib.parse.urlencode(params))


def pubmed_by_pmid(pmids, pause=0.4):
    """Batch esummary lookup: returns {pmid: record}. Author lists are truncated by NCBI — n_authors is the
    number of authors returned, so 'et al.' only reflects the returned slice."""
    out = {}
    for i in range(0, len(pmids), 100):
        chunk = [p for p in pmids[i:i + 100] if p]
        if not chunk:
            continue
        js = json.loads(eutils("esummary.fcgi", db="pubmed", id=",".join(chunk), retmode="json") or "{}")
        for uid, rec in (js.get("result") or {}).items():
            if uid == "uids":
                continue
            auth = rec.get("authors") or []
            doi = next((a.get("value", "") for a in (rec.get("articleids") or []) if a.get("idtype") == "doi"), "")
            out[uid] = dict(pmid=uid, first_author=(auth[0]["name"] if auth else "Unknown"),
                            n_authors=len(auth), title=(rec.get("title") or "").strip().rstrip("."),
                            journal=rec.get("source") or "", year=(rec.get("pubdate") or "")[:4],
                            volume=rec.get("volume") or "", pages=rec.get("pages") or "", doi=doi)
        time.sleep(pause)
    return out


def crossref_by_title(title, journal=None, years=None, collective_author=None, rows=5, min_ratio=0.85):
    """Return a validated record or None. Rejects corrections/errata and anything below the similarity gate."""
    url = ("https://api.crossref.org/works?rows=%d&query.bibliographic=%s"
           % (rows, urllib.parse.quote(title)))
    try:
        items = json.loads(_curl(url, 45))["message"]["items"]
    except Exception:
        return None
    best, best_ratio = None, 0.0
    for it in items:
        t = (it.get("title") or [""])[0]
        tl = t.lower()
        if "correction" in tl or "erratum" in tl:            # never cite a correction notice
            continue
        ratio = difflib.SequenceMatcher(None, tl, title.lower()).ratio()
        if ratio > best_ratio:
            best, best_ratio = it, ratio
    if not best or best_ratio < min_ratio:
        return None
    got_journal = (best.get("container-title") or [""])[0]
    year = ""
    for k in ("published-print", "published-online", "issued"):
        if best.get(k, {}).get("date-parts"):
            year = str(best[k]["date-parts"][0][0])
            break
    if journal and not any(j in got_journal.lower() for j in journal):
        return None
    if years and (not year.isdigit() or not (years[0] <= int(year) <= years[1])):
        return None
    auth = best.get("author") or []
    first = collective_author
    if not first:
        if auth:
            fam = auth[0].get("family", "")
            giv = (auth[0].get("given", "") or " ")[:1]
            first = f"{fam} {giv}.".strip()
        else:
            first = "Unknown"                                # caller must repair via PubMed
    return dict(first_author=first, n_authors=len(auth),
                title=(best.get("title") or [""])[0].strip().rstrip("."), journal=got_journal,
                year=year, volume=best.get("volume", ""), pages=best.get("page", ""),
                doi=best.get("DOI", ""), ratio=round(best_ratio, 3))


def repair_unknown_authors(records, pause=0.4):
    """Collective/author-less Crossref records: look the title up in PubMed and take its first author."""
    for key, rec in records.items():
        if rec.get("first_author") not in ("Unknown", "", "."):
            continue
        ids = json.loads(eutils("esearch.fcgi", db="pubmed", term=f'"{rec["title"]}"[Title]',
                                retmode="json", retmax=5)).get("esearchresult", {}).get("idlist", [])
        if not ids:
            ids = json.loads(eutils("esearch.fcgi", db="pubmed", term=rec["title"],
                                    retmode="json", retmax=5)).get("esearchresult", {}).get("idlist", [])
        js = json.loads(eutils("esummary.fcgi", db="pubmed", id=",".join(ids), retmode="json") or "{}")
        for uid, r in (js.get("result") or {}).items():
            if uid == "uids" or "correction" in (r.get("title") or "").lower():
                continue
            auth = r.get("authors") or []
            if auth:
                rec["first_author"] = auth[0]["name"] + (" et al." if len(auth) > 1 else "")
                break
        time.sleep(pause)
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--pmids", default="")
    ap.add_argument("--targets", default="")
    a = ap.parse_args()
    pmids = [p.strip() for p in a.pmids.split(",") if p.strip()]
    targets = json.load(open(a.targets, encoding="utf-8")) if a.targets else {}
    result = {"pmid": pubmed_by_pmid(pmids), "crossref": {}, "unresolved": []}
    for key, spec in targets.items():
        rec = crossref_by_title(spec["title"], spec.get("journal"), spec.get("years"),
                                spec.get("collective_author"))
        if rec:
            result["crossref"][key] = rec
        else:
            result["unresolved"].append(key)
    result["crossref"] = repair_unknown_authors(result["crossref"])
    json.dump(result, open(a.out, "w", encoding="utf-8"), indent=1)
    print(f"pmid records: {len(result['pmid'])} | crossref validated: {len(result['crossref'])} "
          f"| unresolved: {result['unresolved'] or 'none'}")
    print("wrote", a.out)


if __name__ == "__main__":
    sys.exit(main())
