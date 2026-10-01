# 比对表必须逐篇核对全文（审稿人最容易抓的硬伤）

来源：2026-09 Frontiers 大修。审稿人 1 第 1 条直接指出补充材料里的
「11 项预后研究对照表」**多行与原文不符**，并点名三处。逐篇核对后**全部属实**，
另发现 4 处未被点名的同类错误。

---

## 0. 教训（写在这里是为了不再犯）

**不要凭"印象/主题相似"填对照表。** 本项目表格的队列信息是**推测生成**的，
看起来专业（TCGA-STAD 发现 + GSE 外部验证 + LASSO-Cox），实际上把不同论文的
设计混成了一个模板。这类错误**审稿人一查原文就会发现**，且直接否定
「验证质量」这一类结论 —— 因为整张表就是论据。

> 判据：**表里每一行都必须能指回原文的一句具体表述。指不回去的，就不该写。**

---

## 1. 触发条件

- 审稿意见出现「does not agree with the original articles」「should be reconstructed」
  「checked against their full texts」「linked to its supporting passage」
- 自己交付的任何**研究对照表 / 证据表 / 方法学汇总表**（Supplementary 里的尤其危险）
- 表里有 **cohort / validation / endpoint / 样本量** 这类"事实性"栏位

---

## 2. 核对流程（可复用）

### 2.1 取全文：Europe PMC 优先；NCBI 要分接口对待 ★

**Europe PMC 最稳**（检索 + OA 全文一次搞定）：

```python
import json, re, urllib.request, urllib.parse

# ① 检索：拿 PMID / PMCID / 是否 OA
def epmc(query, n=3):
    url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
           + urllib.parse.urlencode({"query": query, "format": "json",
                                     "pageSize": n, "resultType": "core"}))
    return json.loads(urllib.request.urlopen(url, timeout=30).read())

r = epmc('TITLE:"<论文标题（建议截取前半句）>"')["resultList"]["result"][0]
pmid, pmcid, oa = r.get("pmid"), r.get("pmcid"), r.get("isOpenAccess")

# ② 拿全文 XML（仅 OA 有 pmcid）
def fulltext(pmcid):
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
    return urllib.request.urlopen(url, timeout=40).read().decode("utf-8", "ignore")

text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fulltext(pmcid)))
```

- 标题精确检索失败时退回宽松检索（去掉 `TITLE:` 与引号）。
- **非 OA**（`pmcid is None`）只能拿摘要 —— 此时表格里必须写清信息来自摘要，
  或该行留空，**不要靠猜补齐**。

#### NCBI eutils：`esearch` 与 `efetch` 是两回事（2026-09 实测更正）

⚠️ 旧版本这里写过"本机直连 NCBI `esearch` 一律 0 命中，容易误判成查无此文"——
**这条是错的，不要据此跳过 NCBI。** 实测：

| 接口 | 行为 |
|---|---|
| `esearch` (GET) | **正常可用**，返回真实 count 与完整 PMID 列表（一次取回 4460 条无压力） |
| `efetch` (GET) | **会被限流**，返回 `302 → misuse.ncbi.nlm.nih.gov` |

即：**只有 `efetch` 需要绕**。取"某主题共多少条 / 全部 PMID"这种批量任务，
`esearch` 直接用，不必绕道 Europe PMC。

`efetch` 的可用写法（本项目一次拿到 1839/1840 条）：

```python
HEADERS = {"User-Agent": "hermes-revision/1.0 (mailto:<你的邮箱>)",
           "Content-Type": "application/x-www-form-urlencoded"}

def efetch_post(batch, attempt=0):
    body = urllib.parse.urlencode({
        "db": "pubmed", "retmode": "xml", "id": ",".join(batch),
        "tool": "hermes-revision", "email": "<你的邮箱>"}).encode()
    req = urllib.request.Request(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
        data=body, headers=HEADERS, method="POST")        # ★ POST 而非 GET
    try:
        raw = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "ignore")
        if "misuse.ncbi" in raw:
            raise RuntimeError("blocked")
        return raw
    except Exception:
        if attempt < 4:
            time.sleep(8 * (attempt + 1))                 # 8/16/24/32s 退避
            return efetch_post(batch, attempt + 1)
        return ""

for i in range(0, len(pmids), 200):                       # ★ 每批 200 条
    xml = efetch_post(pmids[i:i+200])
    time.sleep(2)                                          # ★ 批间 2s，不加这一句会被封
```

要点：**POST + 每批 ≤200 + 批间 sleep 2s + 指数退避重试**。缺 sleep 那句即会被限流。
被限流时先降速重试，**不要就此断言"NCBI 不可用"**。

**`efetch` 返回的日期字段**（做年份对账时会用到，见
`references/reference-apparatus-and-count-reconciliation.md`）：
PubMed XML **没有** `PubStatus="epublish"/"ppublish"`，实际用的是：

| 字段 | 含义 |
|---|---|
| `<ArticleDate><Year>` | **电子出版年** |
| `<PubDate><Year>` | **印刷/期号年** |
| `<PubMedPubDate PubStatus="pubmed"/"medline"/"entrez">` | 入库/索引日期，**不是**出版年 |

用错字段会得到"电子年 0 条"这种假结果。

### 2.2 抽取三件事（按表头逐项）

```python
# (a) 所有 GEO 编号
print(sorted(set(re.findall(r"GSE\d{3,6}", text))))
# (b) 含队列关键词的句子 —— 这是判断"发现队列 / 验证设计"的主要依据
for s in re.split(r"(?<=[.;])\s+", text):
    if re.search(r"(?:validation|discovery|training|external|independent)\s+"
                 r"(?:cohort|set|dataset)", s, re.I) and len(s) < 400:
        print("-", s[:260])
# (c) 报告了哪些性能要素（决定 Calibration / DCA 栏位写 Yes 还是 Not reported）
for k in ["calibration curve", "decision curve", "net benefit", "nomogram",
          "tNM stage", "clinicopathologic", "c-index", "concordance index"]:
    print(k, k in text.lower())
```

`(b)` 里要特别警惕两类**不是**外部验证的设计：
- `randomly assigned to a training set … and a testing set` ⇒ **同一队列内部拆分**
- `discovery cohort` + `validation cohort` 都来自**同一家医院** ⇒ 单中心，不是外部

### 2.3 本项目的实际核对结果（留作对照示例）

| 研究 | 表里原来写的 | 全文核对后 |
|---|---|---|
| Chang 2023 | GEO (GSE15459, **GSE26901**) | GEO (**GSE66229**, GSE15459) |
| Cai 2024 | **TCGA-STAD 发现 / GSE15459 验证** | **SYSUCC 发现队列(12例) + SYSUCC 验证队列(231例)** + TCGA 交互分析 |
| Jiang 2025 | GEO (**GSE84437**) 外部验证 | **TCGA 内部随机训练/测试划分**，无外部验证 |
| Zhu 2024 | GSE15459 + MR | **GSE84433, GSE84437, GSE84426** |
| Li 2024 | GEO (**4 个队列**) | **GSE62254 (ACRG, n=300)** 单一外部验证 |
| Yang 2025a | GSE15459 | **GSE15460 (n=248)** |
| Yang 2025b | GSE15459, GSE62254 | **GSE84437, GSE26253** |

⇒ **11 行里 7 行有错。** 不要以为"错一两行"是运气问题。

---

## 3. 重写表格时的硬规则

1. **加 PMID 列** —— 每行标注来源 PMID，审稿人可自行核验，也逼着自己核过。
2. **`Not reported` ≠ `not performed`** —— 原文没写就写 `Not reported`，
   **绝不写 ✗ / No**（那是在断言"作者没做"，是另一回事，且你没证据）。
   表格注里也要写明这一点。
3. **脚注统一用 `Note.`，不要用 `†`** —— 有审稿人专门指出
   "表注用了剑号但表里没有对应标记"。
4. **补充表里的引用编号必须与正文参考文献表一致** ——
   本项目补充表写 `(34)–(44)`、正文是 `37–47`，被要求一并更正。
5. **结论句跟着改** —— 表改了，正文里"这些研究的验证质量……"那句必须重写为
   "验证设计差异很大（外部 GEO 验证 / TCGA 内部拆分 / 单中心），
   因此应按**单个研究的设计**而非按主题比较验证质量"。

---

## 4. 交付前自查（写进断言）

```python
checks = {
  "每行有 PMID":        all(re.search(r"PMID\s*\d+", row) for row in table_rows),
  "无 ✗ 断言":          "✗" not in table_text,
  "Not reported 出现":  "Not reported" in table_text,
  "表注用 Note.":       "Note." in note and "†" not in note,
  "编号与正文一致":     set(re.findall(r"\((\d+)\)", table_text)) <= set(ref_numbers),
}
```

配套：新建 `references/cited-study-table-verification.md` 时同步在 SKILL.md 的
「支持文件」一行里登记（见 SKILL.md 顶部提示块）。
