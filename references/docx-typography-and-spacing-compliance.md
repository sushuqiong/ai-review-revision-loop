# docx 排版合规（对标期刊模板）：字体三层层级 / 表格字号 / 段落间距

来源：2026-10-01 课题2 v22（Frontiers in Medicine 投稿）实测。用户反馈原话：
「字体大小还普遍不一致」「有的地方段落前一片空白，有的地方直接接上一个内容」。

## 0. 为什么会"看着不统一"：字号写在三个层级

Word/docx 的字号可能同时写在三处，渲染时**最内层优先**：

1. **样式层** `styles.xml` 的 Normal / Heading N 的 `w:rPr/w:sz`
2. **段落层** `w:pPr/w:rPr/w:sz`（整段默认字符格式）
3. **run 层** `w:r/w:rPr/w:sz`（只作用该段文字）

逐段生成文档时三层常各写各的 —— 实测同一文档出现 **6 种字号**（8.0 / 9.5 / 10.0 / 10.5 / 11.0 / 12.0），
而 Normal 样式自身定义为 9 pt（模板规范是 12 pt）。

**诊断**（分别打印三层）：

```python
from docx import Document
from docx.oxml.ns import qn
from collections import Counter
d = Document(path)
print("样式层:", d.styles["Normal"].font.name, d.styles["Normal"].font.size)
by = Counter()
for p in d.paragraphs:
    ppr = p._p.find(qn('w:pPr'))
    pr = ppr.find(qn('w:rPr')) if ppr is not None else None
    z = pr.find(qn('w:sz')) if pr is not None else None
    if z is not None:
        by["段落层:" + str(int(z.get(qn('w:val'))) / 2)] += 1
    for r in p.runs:
        rpr = r._element.find(qn('w:rPr'))
        z = rpr.find(qn('w:sz')) if rpr is not None else None
        by[str(int(z.get(qn('w:val'))) / 2) if z is not None else None] += 1
print(dict(by))
```

## 1. 对标模板的正确改法（三步，顺序不能反）

先读模板取规范值。实测 `Frontiers_Template.docx`：**Normal = Times New Roman 12.0 pt**；
Heading 1/2/3 也是 12 pt（靠加粗区分层级）；Title 16 pt；模板本身采用"样式继承"写法（run 不写字号）。

1. **改样式层**：把 Normal / Heading N / Title / Author List / List Bullet / Caption 的
   `font.name` + `font.size` 设为规范值。
2. **清段落层覆盖**：删掉每个段落 `w:pPr/w:rPr` 里的 `w:sz` / `w:szCs`，否则它们盖住样式层。
3. **规范 run 层**：

```python
r.font.name = "Times New Roman"; r.font.size = Pt(12)
rpr = r._element.get_or_add_rPr()
rf = rpr.find(qn('w:rFonts'))
if rf is None:
    rf = OxmlElement('w:rFonts'); rpr.insert(0, rf)      # 必须插到 rPr 首位
for a in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'):
    rf.set(qn(a), "Times New Roman")
for tag in ('w:sz', 'w:szCs'):
    e = rpr.find(qn(tag))
    if e is None:
        e = OxmlElement(tag); rpr.append(e)
    e.set(qn('w:val'), str(int(size.pt * 2)))            # 单位是半磅！12pt -> 24
```

两个易错点：**四个 `w:rFonts` 属性都要写**（只写 `r.font.name` 在中/日文回退时仍会变字体）；
**`w:sz` 单位是半磅**。

**验收**（每个文件内字体、字号都必须唯一）：

```python
fonts, sizes = Counter(), Counter()
for p in d.paragraphs:
    if p.style.name == "Title": continue
    for r in p.runs:
        if r.text.strip(): fonts[r.font.name] += 1; sizes[...] += 1
assert set(fonts) <= {"Times New Roman"} and len(sizes) == 1
```

## 2. 表格字号要单独查、单独统一

表格 run **不在** `doc.paragraphs` 里（在 `table.rows[].cells[].paragraphs`），上面的段落规范化碰不到它们。
实测主稿 7 个表中 T3/T4 大量 run **根本没写 `w:sz`**（回退样式默认），与 T0/T2（显式 9 pt）视觉不一致。

- 逐表统计 `r.font.name` / `w:sz`，**一个表内出现 >1 种即不合格**。
- 统一目标：正文表 9 pt、补充材料表 8 pt、清单类 9.5 pt（表格小于正文是惯例；**同一文档内必须唯一**）。
- 改完必须**从主稿重新提取**独立的 `Tables/Table N.docx`，否则两边漂移。

## 3. 段落间距：先删空段落，再按层级设

实测：同一文档内 **9 种间距组合** + **20 个空段落**（97 段中）→ 视觉上"有的地方一片空白、有的紧贴"。

```python
by = Counter()
for p in d.paragraphs:
    ppr = p._p.find(qn('w:pPr'))
    sp = ppr.find(qn('w:spacing')) if ppr is not None else None
    b = sp.get(qn('w:before')) if sp is not None else None
    a = sp.get(qn('w:after'))  if sp is not None else None
    by[(int(b)/20 if b else None, int(a)/20 if a else None)] += 1
print(dict(by))          # 种类数 >4 就该统一
```

（`w:before` / `w:after` 单位 **twips**，1 pt = 20 twips）

**修复顺序**：

1. **删空段落 —— 但必须排除含图的段落**，否则图直接丢：

```python
empties = [el for el in body.iterchildren()
           if el.tag == qn('w:p')
           and not "".join(n.text or "" for n in el.iter(qn('w:t'))).strip()
           and not el.findall('.//' + qn('a:blip'))]      # ← 关键
```

2. **按元素类型设统一间距**（层级越高段前越大）：

| 元素 | 段前 | 段后 |
|---|---|---|
| 文档标题 | 0 | 12 |
| 一级标题 / 表图标题 | 12 | 6 |
| 二级标题 / Panel 标签 | 8–10 | 3–4 |
| 正文 / 表注 | 0 | 6 |

3. 行距统一 1.0，并把 Normal / Heading 样式层的 `paragraph_format` 也一起设（双保险）。
4. 验收：间距种类 ≤4、非装图空段 = 0。

## 4. "三线表"判定别只看样式名

`tblStyle` 可能是 `12`（规范）、`9`（另一种三线样式），也可能是 `35` = **Table Grid（有网格线，不合格）**。
**不要靠名字判断**，验两条：

```python
tp = t.find(qn('w:tblPr')); tb = tp.find(qn('w:tblBorders')) if tp is not None else None
real = any(x.get(qn('w:val')) not in (None, 'none', 'nil') for x in (tb if tb is not None else []))
vert = any((tc.find(qn('w:' + s)) is not None
            and tc.find(qn('w:' + s)).get(qn('w:val')) not in (None, 'nil', 'none'))
           for tc in t.iter(qn('w:tcBorders')) for s in ('left', 'right'))
```

三线表实现 = **首行 `top`(粗 12) + `bottom`(细 6)、末行 `bottom`(粗 12)**，左右写 `nil`，行间无横线。
修复 Table Grid：把 style 改成 `12` + 逐单元格写上述 `tcBorders`。

## 5. ⚠️ 改文字的脚本会回滚此前用 zip 替换的图片

`python-docx` 的 `save()` 会**重建整个 OPC package**；此前用 `zipfile` 直接替换的
`word/media/*.png` 不在其文档模型里，一保存就**退回旧图**（本次实测踩中两次：
Fig1 2160×2157 → 1342×1340）。

⇒ **铁律：所有 python-docx 的文字/样式/间距/结构修改全部做完，最后才做 zip 级图片替换；
此后不再用 python-docx 打开该文件。** 完整复盘见
`figure-legend-content-and-image-reembed-audit.md` §10。

## 6. ⚠️ 审计脚本本身也会错：报 FAIL 先验"检查器"，别先改文档

本轮终审先报了 7 项"遗留问题"，复核后**全部是检查方法过时**：

- 用**引用出现顺序**当**标题物理排列**（引用本来就可以乱序，不该按升序断言）；
- 正则 `^(Table|Figure)\s+S?(\d+)\.` 把补充材料的 `Table S13.` 误判成主稿 `Table 13.`；
- **硬编码的"图片 ↔ 文件"映射没有随 `FigureS1 ↔ S2` 对调而更新** → 全部假阳性。

⇒ 只要改过任何映射（文件改名、编号重排、图对调、表块重排），**必须同步更新审计脚本里的映射常量**。
审计报 FAIL 时先问"是文档错了，还是我的检查器过时了"，再动手改交付物。
