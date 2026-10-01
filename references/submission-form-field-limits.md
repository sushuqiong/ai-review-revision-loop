# 投稿系统表单栏位的硬性字符上限

触发：投稿系统里出现带硬上限的自由文本栏位，例如
`Please enter all abbreviations that have been used in this manuscript at least three or more times` +
`Limit 200 characters`。

## 陷阱：不要"截断"，要"求解"

用户第一次拿到 31 项缩写清单（1 075 字符）直接被告知超限。此时的错误反应是：
① 随手截取前几条；② 只给缩写不给全称；③ 让用户自己删。
正确反应：**把"栏位能放什么"当成一个带预算的优化问题** —— 用程序算，不要目测字符数。

## 方法（可复用）

1. **数真实出现次数**（不要凭印象排序）。在**当前那份手稿**上统计（用户可能已经改过文件名/内容）：

```python
import re
from docx import Document
P = [x.text for x in Document(MS).paragraphs]
i = next(k for k, t in enumerate(P) if t.strip() == "References")     # 正文与图注分开数
BODY, ALL = "\n".join(P[:i]), "\n".join(P)
def cnt(ab, hay):   # 词边界要排除连字符与字母数字
    return len(re.findall(r"(?<![A-Za-z0-9\-])" + re.escape(ab) + r"(?![A-Za-z0-9])", hay))
```

2. **建候选集并剔除"不是缩写"的东西**：基因符号（CXCL9/COL1A2）、数据集 accession（GSE84044）、
   拉丁缩写（e.g./vs./et al.）。这些列进去会显得不专业。
3. **按预算求解**（本轮：`ABBR:full form` 格式 + 分隔符 `; `，单价 16–60 字符，200 字符最多放 4–7 项）：

```python
items = [(ab, n, len(ab) + 1 + len(ex) + 2) for ab, n, ex in DATA]   # +2 为 "; "
best = {0: (0, set())}                       # used_chars -> (已覆盖出现次数, 选中集合)
for ab, n, c in items:
    nb = dict(best)
    for used, (val, sel) in best.items():
        if used + c <= LIMIT and (used + c not in nb or nb[used + c][0] < val + n):
            nb[used + c] = (val + n, sel | {ab})
    best = nb
```

4. **给 2–4 个候选方案**，各自标注**精确字符数**（`len()` 算出来，不许估）与选取逻辑：
   ① 覆盖出现次数最大化（纯频次）；② 条目数最大化；③ **核心项**：结局 + 暴露 + 疾病 + 主队列 + 主中介
   （本轮实际交付的就是这一版 —— 编辑更能接受"我列了最关键的几个"而非"我按频次挑的"）。
5. **格式照抄对方的示例**：示例 `MELD:model for end stage liver disease; AST: aspartate aminotransferase`
   冒号后无空格 → 照做，既合规范又能省下每项 1 个字符。
6. **主动交代被挤掉的部分**并给出话术（"栏位上限 200 字符，完整 31 项清单见手稿/返修信"），
   让用户在被追问时能答上。

## 附带发现：这类栏位是编辑的"对照检查钩子"

期刊举例 `AST: aspartate aminotransferase` 不是随意的 —— 顺着这条线索回查手稿，
本轮发现 **AST/ALT 各出现 4 次却从未写出全称**（首次出现就在 FIB-4 公式里）。
所以回答该栏位时**必须顺手扫一遍**：凡是出现 ≥3 次的缩写，是否都在手稿首次使用处定义了？
没定义的要么补进手稿，要么在栏位里给出全称 —— 否则编辑一对照就发现。

## 坑

- **不要用记忆里的数字**：把手稿当前文件重新统计一遍（用户会重命名、会手改内容）。
- **不要手工数字符**：`len()` 之外一律不可信，含空格与标点。
- 统计口径要说明：正文 + 图注是否都算？本轮把两栏数字都算出来，并标出"仅靠图注才够 3 次的项"
  （FDR / ssGSEA / SVM-RFE），让用户自己决定。
- 用户可能同时要求"不要黏贴上次那 31 项" ⇒ 交付物必须**与上一版显著不同**，不能只做删减。
