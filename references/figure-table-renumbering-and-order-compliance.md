# 图表编号合规：按「正文首次提及顺序」重编号的完整流程

**触发**：用户/编辑指出「图表和补充图表的出现和命名顺序不对」；或交付前自检发现
`Table N` 的首次提及顺序 ≠ 1..N。**这是投稿常识项**——审稿人第一眼就会看，
但正因为太基础，检查清单里最容易漏（v22 事故：已提交 Frontiers 后才被用户发现）。

---

## 0. 判定标准（别搞混两件事）

| 对象 | 规则 | 是否必须单调递增 |
|---|---|---|
| **正文的首次提及顺序** | 决定编号（编号 = 首次被引用的次序） | **必须** |
| **文末表/图块的物理排列** | 按新编号升序排 | **必须** |
| 补充材料的标题物理排列 | 按新编号升序排（S1, S2, … Sn） | **必须** |
| **正文中引用其他表的次序** | 自然行文，可乱序 | **不必**（别把它当失败！） |

⇒ 断言脚本必须**分别**检查「引用首次出现的顺序」与「标题块的物理排列」，
用同一个正则同时抓两者会得到大量假 FAIL（v22 终审踩过：脚本把正文引用当标题，
报了 7 项假问题）。

---

## 1. 测量首次提及顺序

```python
import re
from docx import Document

def first_mentions(path, pat):
    paras = [p.text for p in Document(path).paragraphs]
    out = {}
    for i, t in enumerate(paras):
        for m in re.finditer(pat, t):
            out.setdefault(int(m.group(1)), i)      # 只记第一次
    return out

PATTERNS = [("Table",   r'\bTable\s+(\d+)(?![\dS])'),
            ("Table S", r'\bTable\s+S(\d+)'),
            ("Figure",  r'\bFigure\s+(\d+)(?![\dS])'),
            ("Figure S",r'\bFigure\s+S(\d+)')]

for label, pat in PATTERNS:
    fm = first_mentions(ms_path, pat)
    order = [k for k, _ in sorted(fm.items(), key=lambda kv: kv[1])]
    print(label, order, "OK" if order == sorted(order) else "❌ 需重编号")
```

**注意**：补充材料里的 `Figure SN` 引用要在**主稿**里测（编号由主稿的引用顺序决定）；
补充材料的**排列**另测（应为 S1..Sn 升序）。

---

## 2. 构造映射（旧→新）——常是置换环，必须两阶段替换

`v22` 的主稿表映射：`{1:1, 7:2, 6:3, 2:4, 3:5, 4:6, 5:7}`
—— 这是**一个环**（2→4→6→3→5→7→2）。直接顺序 `str.replace` 会二次替换、彻底改坏。

**两阶段哨兵法**：

```python
L, R = "\u27e6", "\u27e7"          # ⟦ ⟧ 文档里绝不会出现的哨兵
def two_phase(t, pat, mapping):
    t = re.sub(pat, lambda m: "%s%s%d%s" % (m.group(1), L, mapping.get(int(m.group(2)), int(m.group(2))), R), t)
    return t
# 全部规则跑完后再： t.replace(L,"").replace(R,"")
```

**替换顺序**：先长模式后短模式 —— 先 `Table S\d+` / `Figure S\d+`，再 `Table \d+`；
并用 `(?![\dS])` 负向断言，避免 `Table 1` 命中 `Table 1x` 或 `Table S1`。

---

## 3. 范围与并列形式（naive 逐号替换必翻车的三处）

| 形式 | 陷阱 | 正确做法 |
|---|---|---|
| `Tables 4–5`（具体两张） | 只替换到 `Tables` 后第一个数字 → `Tables 6–5` | 单独用范围正则 `Tables\s+(\d+)\s*[–-]\s*(\d+)`，映射后**重新排序为升序** |
| `Tables S1–S13`（**泛指全部**） | 同样是泛指，却按逐号映射 → `S4–S13` | 泛指要**整体替换成 `S1–Sn`**（n = 现有总数），**不映射** |
| `Tables 2 and 6`（并列） | 第二个数字前面没有 `Tables`，正则漏掉 → 只改了第一个 | 用上下文精确替换，或先把并列展开成 `Table 2` / `Table 6` 再替换 |

**判别泛指 vs 具体**：看语义。`"This file contains Tables S1–S16"`/`"all supplementary tables"`
= 泛指；`"the L-series diagnostics of Tables S8–S9"` = 具体两张。

**顺序修复后务必回读核对**：`grep` 出所有 `Tables?\s+S?\d+\s*[–-]\s*S?\d+` 逐一目视。

---

## 4. 双向交叉引用（最容易只改一半）

- **补充材料里会引用主稿的表**（如 `"match Table 2 of the main text"`、`"main-text Table 6"`）
  → 必须按**主稿映射**同步。
- **主稿里会引用补充表/图**（`Table S13`、`Figure S2`）→ 按**补充映射**同步。
- **表内的单元格**也可能有引用（crosswalk 表尤其多）→ 段落替换循环之外，**必须再跑一遍表格单元格**。
- 补充材料内部互相引用（`as documented in Table S11`）→ 按补充映射同步，但**跳过标题段落本身**
  （`^Table S\d+\.` 的段落已在新编号状态，再映射会二次改坏）。

---

## 5. 物理重排标题块（块 = 标题 + 表 + 表注）

```python
# 收集块
blocks, cur = {}, None
for el in body.iterchildren():
    t = t_of(el)
    m = re.match(r'^(Table|Figure)\s+S?(\d+)\.', t)
    if el.tag == qn('w:p') and m:
        cur = (m.group(1), int(m.group(2))); blocks[cur] = [el]; continue
    if el.tag == qn('w:p') and t.startswith("Supplementary"):   # 分节标题终止块
        cur = None; continue
    if cur is not None: blocks[cur].append(el)
```

⚠️ **排列时的经典 bug**：`for blk in reversed(blocks): ... anchor.addprevious(el)` 会把顺序**再反一次**
（v22 实际发生：排成 S16→S1 降序）。**升序插入就直接正序遍历 + `anchor.addprevious(el)`**，
不要 `reversed`。

```python
for k in sorted(tbl_keys):            # 升序
    for el in blocks[k]:
        figures_heading.addprevious(el)   # 表全部插到 "Supplementary Figures" 之前
for k in sorted(fig_keys):            # 图追加到文末
    for el in blocks[k]: body.append(el)
```

主稿同理：拿到 `Table N.` 标题 + 紧随的 `w:tbl`，作为一个块整体搬到目标位置。

---

## 6. 连带产物：文件名与内嵌图

重编号后**这些东西必须一起改**，漏一个就自相矛盾：

1. `Tables/Table N.docx` → 从重排后的主稿**重新提取**（不是重命名，因为内容顺序也变了）
2. `Figures/FigureS1.* ↔ FigureS2.*` 对调（**所有格式**：pdf/png/jpg/tif 一起换）
3. **补充材料内嵌图与图注的配对**：移动图块时图会跟着块走，但**校验必须按「图注顺序」配对**，
   不能用硬编码 `image1↔FigureS1`（对调后该映射已失效，v22 终审因此误报 2 项 FAIL）

```python
# 正确做法：按文档顺序，找到每个图注后面第一个 blip，再与 Figures/ 做 md5 匹配
for el in body.iterchildren():
    m = re.match(r'^Figure\s+(S?\d+)\.', t_of(el))
    if m: cur = m.group(1)
    if el.findall('.//'+qn('a:blip')) and cur:
        media = rid2media[blip.get(qn('r:embed'))]
        print(cur, media, "->", md5_match_in(Figures_dir, z.read("word/media/"+media)))
```

4. **转换后的 PDF** 是旧编号 → 必须用修正后的 docx 重新导出。
5. 改完再跑一次 §1 的断言，四类（Table / Table S / Figure / Figure S）全部递增才算完成。

---

## 7. 已提交后才发现怎么办

主动给 **Editorial Office** 发消息（不是 Support Team——后者只管技术故障），说明：
「编号与首次引用顺序不一致，仅影响编号与交叉引用，不影响数据/分析/结论，请求提交修正版」，
并问「现在提交修正版，还是随返修一并提交」。同时**立即把修正版做好**，等编辑回信即可上传。

---

## 8. 一句话教训

编号顺序**必须写成脚本断言**，不能靠"逐项读一遍"来保证；
而「我的检查清单全部通过」**不等于**「稿件没有规范问题」——别用"遗留问题 0"给用户虚假安心。
