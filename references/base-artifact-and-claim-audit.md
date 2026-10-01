# 基线版本一致性 + 回复信声明核对

返修任务里最容易翻车、且审稿人一眼能看穿的两类问题。二者都已在本项目实际发生过。

---

## 1. 修订前必须锁定「审稿人实际看到的那个文件」

**症状**：拿项目里的 markdown 源稿（如 `*_source.md`）改成 vN+1，但作者实际提交给期刊的是 DOCX。
两者可能**不是同一版本**——源 md 常是更早的草稿，作者或其它 AI 在导出 DOCX 前又改过。

**后果**：修订稿丢失提交版里的编辑；或把已被删掉的旧句重新引入；回复信引用的文字与审稿人所见不符。

**流程（每次返修开工前必做）**：

1. 找到权威基线 = 作者上传到投稿系统的那个文件（通常是 `manuscript/*_Frontiers.docx` / `*_JGC.docx`）。
   - 项目里带 `_reference_`、`internal_archive_stale_pdfs/`、`README_DO_NOT_UPLOAD` 的都是**历史副本**，不是基线。
   - 若只有 PDF，注意 PDF 可能由更早版本导出 → 与 DOCX 也不一致。
2. 对基线 DOCX 与准备修改的源文件做**句子级**比对（不是段落级——段落级会把"前70字符相同、后半不同"的差异吞掉）。
3. 把「基线有、源文件没有」的句子逐条补回；把「源文件有、基线没有」的逐条判断是旧文本还是有意新增。
4. 比对结果记入 change log，作为返修证据留档。

**句子级比对脚本**（docx vs md；阈值 60 字符即可，实测 400+ 句里噪声可忽略）：

```python
from docx import Document
import re
d = Document(DOCX_PATH)
docx_txt = "\n".join(p.text for p in d.paragraphs if p.text.strip())
md = re.sub(r"[|#*]", " ", open(MD_PATH, encoding="utf-8").read())

def sents(t):
    t = re.sub(r"\s+", " ", t)
    return [s.strip() for s in re.split(r"(?<=[.;:])\s+", t) if len(s.strip()) > 60]

A, B = sents(docx_txt), sents(md)
Bn = [re.sub(r"\s+", " ", x).lower() for x in B]
for s in A:                                  # 基线有、源文件没有
    if not any(re.sub(r"\s+", " ", s).lower()[:60] in b for b in Bn):
        print("MISSING:", s[:200])
```

**反向也要查**：`A` 与 `B` 互换，找出源文件独有的句子，判断是不是旧文本回流。

---

## 2. 回复信里每一条声明，都必须与实际交付物逐条核对

**症状**：写回复信时先按"我打算做的"措辞，实际只改了正文文字、没真做数据重构 → 声称"已重构字段"但 CSV 字段没动；声称"已核验参考文献"但其实没查。

**这是返修里最危险的自伤**：审稿人拿回复信逐条对照文件，一处对不上，全部声明的可信度都受损。

**硬规则：回复信定稿前，为每条 `Changes made:` 生成一个「可验证断言」，然后真的去验证。**

| 回复信里的措辞类型 | 必须能通过什么验证 |
|---|---|
| "已新增 Table N" | DOCX 里 `len(doc.tables)` 与正文引用编号一一对应 |
| "已重构补充表格字段" | 打开该 CSV，字段名列表里真的有那几列 |
| "已补充 PMID/DOI 级记录集" | 那批文件真的存在且行数对得上 |
| "已核验 2026/in press 参考文献" | 真的逐条查过索引库，并把结果写进回复 |
| "已修正 Figure X 的拼写" | 真的重新渲染过图；**没重画就不能写"corrected"** |
| "已删除重复句" | 该句在全文中出现次数 == 1 |

**没做就三选一**：① 真去做；② 把措辞降到事实（"we verified consistency" ≠ "we corrected"）；③ 从回复信里删掉。
**绝不能保留一句做不到的承诺。**

配套：定稿后跑一遍程序化断言清单（见 `references/submission-readiness-adversarial-qa.md`），把回复信文本也纳入扫描对象，而不只扫手稿。

---

## 3. 补充材料的"重构"必须真的重构

本项目的三个实例（都是"声称改了、其实没改"）：

- **S2 计数协调**：回复信说"PMID 级记录集与年份归属规则已写入 Table S2"，实际 Table S2 只有 `topic,year,count,query` 四列。→ 需真的取回 PMID 列表 + 新建说明文档。
- **S3 编码规则**：回复信说"编码规则/提取流程/检索日期/排序设置已提供"，实际只有 per-record 的 `mentions_*` 布尔列。→ 需新写 `Supplementary_File_S3_coding_rules.md`。
- **S4 字段分离**：回复信说"已拆成 indexing / corpus membership / topic eligibility 三个字段"，实际只改了正文一句。→ 需真的重建 CSV。

**做 S4 这类拆分时，顺手把审稿人的怀疑点验一遍**：本项目按 DOI 逐条复查被标 `likely_not_in_pubmed` 的记录，发现 **121/135 实际在 PubMed 有索引**（审稿人的怀疑是对的）。把复查结果写进回复信，比单纯改字段名有说服力。

---

## 4. Zenodo 存档（审稿人要求公开仓库 + DOI 时）

**两条路**：
- **GitHub 集成**（用户习惯）：Zenodo settings → GitHub → 打开该仓库开关（会产生 webhook，事件 `release`）→ 发 GitHub Release → Zenodo 自动抓快照出 DOI。
  - **必须 public 仓库**；private 仓库集成拿不到内容。
  - **归档慢，实测约 40 分钟**。别用 Zenodo 的 `search` 接口轮询——索引滞后，会误判成"没成功"。
  - 正确查法：`GET https://zenodo.org/api/deposit/depositions`（需 token）或 `GET /api/records/{conceptrecid}`；也可以看 GitHub 侧 webhook 投递状态：`gh api repos/{owner}/{repo}/hooks` → `.../hooks/{id}/deliveries`。
  - webhook 响应 **202 = Accepted**（成功入队）；**409 = "The release has already been received"**（同一 release 的重复投递，无害）。两者都不是失败。
- **手动上传 / REST API**：建 token（scope `deposit:write` + `deposit:actions`）后可全自动；但 `deposit/depositions?size=` 上限 25，写 50 会 400。

**引用哪个 DOI**：
- **concept DOI**（`10.5281/zenodo.<conceptrecid>`）恒定指向最新版本 → 手稿 Data Availability 里首选，因为返修会多版本迭代。
- 版本 DOI 指向单个快照。若已发多个 release，版本会堆叠（本项目 v1.0.0/v1.0.1/v1.0.2/v1.1.0），引用 concept DOI 可避免"引用的版本缺文件"。
- 用 `GET /api/records/{id}` 读 `conceptdoi` 字段拿到 concept DOI。

**发 Release 前先自检**：`.zenodo.json` 放在仓库根（可预填 metadata，实测生效）；仓库里不能有 token/密钥。

---

## 5. 渲染产物必须回读校验

源标记里的问题在渲染后才暴露。本项目实例：markdown 里多了一行 `|---|---|---|---|` 分隔符 → 投稿 PDF 渲染出一个**只有表头没有内容的空表格** → 审稿人回意见"Table 3 contains only a header and no content""有两个 Table 4"。

**构建后必查**：`len(doc.tables)`、每个表的行列数、正文引用的 Table/Figure 编号集合是否 == 实际编号集合、全文是否残留 `**` / `|---` / 占位符方括号。

**图件文字**用 OCR 抽查（本机 tesseract，需 `TESSDATA_PREFIX`）；注意有 `_reference_` 后缀的图是低分辨率历史副本，OCR 会明显变差，别据此误判拼写。
