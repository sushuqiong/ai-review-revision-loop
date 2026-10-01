# Vancouver/ICMJE 参考文献重建 + 投稿格式硬要求

> 触发：编辑说"please ensure all references follow the journal style (ICMJE/Vancouver)"，
> 或任何要求"上标数字、按首次出现顺序编号"的期刊（Elsevier 系常见）。

## 一、不要手工重排号——用"符号键 + 自动编号"

**做法**：正文里用 `[[key]]` 写引用，由生成脚本按**首次出现顺序**分配编号并输出文献表。
这样改稿增删引用后**永远自洽**，也不会出现"文献表编号对、正文编号错"的经典事故。

```python
CITE = re.compile(r"\[\[([^\]]+)\]\]")
REFS = {"vallet2007": "Vallet-Pichard A, ... Hepatology 2007;46:32-6.", ...}

def build_ref_order(blocks):
    for _, t in blocks:
        for m in CITE.finditer(t):
            for k in m.group(1).split(","):          # 支持 [[a,b]] 一句多引
                k = k.strip()
                if k not in num:
                    num[k] = len(order) + 1; order.append(k)

def rich(par, text):
    """把 [[key]] 渲染成上标数字（docx: run.font.superscript = True）"""
    pos = 0
    for m in CITE.finditer(text):
        par.add_run(text[pos:m.start()])
        r = par.add_run(",".join(str(num[k.strip()]) for k in m.group(1).split(",")))
        r.font.superscript = True                # ← 期刊要求的"上标"
        pos = m.end()
    par.add_run(text[pos:])
```
产出后**机器自检**（本会话实测全部通过）：
```python
seq = []                                          # 按文档顺序收集所有上标数字
for p in doc.paragraphs:
    for r in p.runs:
        if r.font.superscript and re.match(r"^[\d,]+$", r.text.strip()):
            seq += [int(x) for x in r.text.split(",")]
first_seen = list(dict.fromkeys(seq))
assert first_seen == list(range(1, len(first_seen) + 1))     # 严格递增、无跳号、无重复
# 注意：用 ^\d+\.\s 抓"文献表条目"时会把 "1. INTRODUCTION" 这类小节标题也算进去，
#       导致"文献表 64 条、实际 59 条"的假警报——按 ^\d+\. [A-Z][a-z] 之类收紧正则。
```

## 二、作者数与期刊名：必须逐条核，不能凭印象

规范（Elsevier/ICMJE）：
- **≤6 位作者 → 全部列出**；**≥7 位 → 前 6 位 + et al.**
- 期刊名用 **Index Medicus/PubMed 缩写**（`Am J Gastroenterol`、`J Hepatol`、`Nucleic Acids Res`）
- 正文**上标**、文献表**按编号排列**（非字母序）

用 PubMed esummary 一次拿到权威字段（作者名、卷、期、页、DOI），别靠记忆：
```python
j = json.load(urlopen("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                      "?db=pubmed&id=%s&retmode=json" % pid))["result"][pid]
authors = [a["name"] for a in j["authors"]]          # 长度决定"全列"还是"前6+et al."
vol, iss, pages, yr = j["volume"], j["issue"], j["pages"], j["pubdate"]
```

**本会话真实抓到的错**（都是原稿里存在的）：
- 一条文献卷号写成 `Front Immunol 2026;16:1765221`，实际是 **`2026;17:1765221`**（2025=卷16、2026=卷17）；
- 同一篇按"7 位作者"处理（前 6 + et al.），**实际只有 5 位**（`Hua L, Shen L, Tao Y, Wang C, Shao X`）→ 应**全部列出**。
  → 结论：**卷号与作者数都要核**，只核 DOI 不够。

## 三、容易漏掉的投稿格式硬要求

| 项目 | 要求 | 本会话情况 |
|---|---|---|
| **Highlights** | Elsevier 硬性：3–5 条，**每条 ≤85 字符（含空格）** | 原稿每条都超；重写为 5 条，最长 82 字符。**生成时用 `len()` 断言并打印每条长度** |
| 摘要 | 结构化（Introduction and Objectives / Materials and methods / Results / Conclusions）、**摘要内不带引用** | 已合规；字数按同口径声明 |
| 标题页 | 需含字数、图表数量、缩写表、CRediT、基金、伦理、数据可得性 | 增补"Supplementary Figures: 8 / Supplementary Tables: 4" |
| STROBE/CONSORT | 正文写了"followed the STROBE guidelines"就必须**同时提交清单** | 原稿缺 → 主动提示用户，并提出可代为生成 |
| 引用括号 | 改上标后**不能残留方括号编号** | 自检 `re.findall(r"\[\[|\]\]", full_text)` 必须为空 |
| 语言 | 英文正文里**不得混入中文字符** | 自检 `re.findall(r"[\u4e00-\u9fff]", text)` 应为 0 |

## 四、返修答复里怎么讲这件事
逐条列你做了什么（而不是"已按要求修改"）：
1. 所有正文引用改为**上标数字，按首次出现顺序**；
2. 作者列表逐条核对（≤6 全列 / ≥7 前 6 + et al.）；
3. 期刊名改用 Index Medicus 缩写；卷/期/页逐条补齐；
4. **新增文献逐条经 PubMed 核对**（列出新文献及其核对方式）；
5. 已清除正文中残留的方括号编号。
