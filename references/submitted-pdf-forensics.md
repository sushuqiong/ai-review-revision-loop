# 用作者"提交版合并 PDF"定事实（返修第一步）

## 为什么必须做
本地草稿文件夹常含**多套互相矛盾**的变体（图注两套、编号冲突、旧版方法段）。判断"当初到底交了什么"**唯一可靠依据**是 Editorial Manager 生成的**合并 PDF**（作者桌面上的 `<稿号>.pdf`，本例 `JCEH-D-XX-XXXXX.pdf`）。
先读它，再决定改什么——否则会把"作者从没交过的东西"当成缺失内容去补，或把"本来没问题的地方"当成错误去改（＝自爆）。

## 扫描配方（PyMuPDF，无需 OCR）
```python
import fitz, re
d = fitz.open(PDF)
print(len(d))
for i, p in enumerate(d):
    first = [l.strip() for l in p.get_text().splitlines() if l.strip()][:1]
    print("p%-3d %s" % (i+1, first[0][:90] if first else "(image page)"))
```
- 逐页首行即可还原合并结构：Cover letter → Manuscript（正文页码 1..N 重新起编）→ Declarations → Figures → Tables → Supplementary Figures → Title Page → CRediT。**页码重新起编处/files 边界**。
- 全文 flatten（`re.sub(r"\s+"," ",txt)`）后按候选串做 `in` 判定。

## 它回答的 6 个问题（每条都会改变你该做什么）
| 问题 | 判定方法 | 结论用法 |
|---|---|---|
| 交的是哪套图注？ | 对每套变体取"独有短句"（如 `Dot size represents the mapped gene count` vs `Dot size indicates gene count`）逐一 `in` 判定 | 命中那套 = 提交版 → **只在其基础上增量**，不要重写 |
| Fig.1–3 的编号顺序？ | 同时看**图文件名**和**正文引用** | 三者一致的那个顺序为准（本例 Fig.1=研究设计、Fig.2=NHANES、Fig.3=CHARLS），另一套是弃稿 |
| 补充图注交了吗？ | 对 S1–S5 图注独有短语做 `in` | 若全 False → 它们**从未提交**；补上 S1–Sn 属**补强**，不是"改动提交内容" |
| 某个说法真的交过吗？ | 搜该说法的独有串（例：`all indicated comparisons achieving high statistical significance`、`P = 1.6 × 10`） | 若不存在 → **不存在需要"改错"的地方**，正文只需为新标注加一句解释即可（**避免自爆**） |
| 参考文献是什么格式？ | `re.findall(r"^\[\d+\]|^\d+\.\s", txt, re.M)` | 方括号 → 需按主编意见转上标 |
| 页数/图表数 | 页面标题行（`Supplementary Figure S5`…） | 核对交付清单完整性 |

## 字数口径校准（必做，且必须先做）
标题页申报的摘要词数 = **摘要"结构段落"按空白切分的词数**，精确吻合。
```python
LAB = ("Introduction and Objectives", "Materials and methods", "Results:", "Conclusions:")
abs_para = [t for t in ps if t.strip().startswith(LAB)]
n = len(re.sub(r"\s+", " ", " ".join(abs_para)).strip().split())   # 提交版 → 245 = 标题页申报值 ✔
```
规则：
1. **先在提交版上把申报值复现出来**（复现成功才算找到口径），再报修订稿的数字。
2. 摘要 = 上述口径（**含** `Introduction and Objectives:` 等 4 个段首标签，**不含** 标题/关键词/ABSTRACT 标题）。
3. 正文若复现不出申报值（本例申报 4,483，实测 4,638），**照实报告可复现的那个数并说明口径**，不要硬凑申报值。
4. 标题页、README、正文三者数字必须**逐字一致**（交付前用脚本回读标题页 docx 与正文实体比对）。

## 附带发现（顺手就查）
- 参考文献条目：作者数与期刊规范（≤6 全列 / ≥7 前 6 + et al.）可对 PubMed `esummary` 批量核；本例查出卷号错（16 应为 17）**且**作者数错（按 7 位处理，实际 5 位）。
- 提交版正文里的过度声明（如 `all nine hub genes … all P < 0.05`）需按真实复算结果改写；但**只改这一句**，不要顺手扩写。
