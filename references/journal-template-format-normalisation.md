# 按期刊模板统一 docx 字体与段落间距（用户反复反馈的两类问题）

**触发**：用户说「字体大小还普遍不一致」「参考期刊模板修改」「有的地方段落前一片空白、
有的地方直接接上一个内容」。这两类问题在**脚本分次生成的 docx** 里几乎必然出现。

---

## 一、先读模板的样式规范（不要凭习惯猜）

```python
from docx import Document
d = Document(template_path)
for s in d.styles:
    if s.font.name or s.font.size:
        print(s.name, s.font.name, s.font.size.pt if s.font.size else None)
print(d.styles["Normal"].font.name, d.styles["Normal"].font.size)
```

Frontiers 模板实测：**Normal = Times New Roman 12.0 pt**；Heading 1/2/3 = 12.0 pt（靠**加粗**区分层级）；
Title = 16.0 pt。模板采用**样式继承**写法（run 不写字号）——修复就照这个原则来。

---

## 二、字体不一致的根因与三层修复

**根因**：文档由脚本逐段生成，早期按"紧凑排版"写了 9–11 pt，后续增补段落又用了别的字号；
**且部分 run 没有显式 `w:sz`**，Word 渲染时回退到样式默认值 ⇒ 同一文档内出现 6 种字号混用。
（v22 主稿实测：Normal 样式是 **9 pt**，而 run 层混着 8.0 / 9.5 / 10.0 / 10.5 / 11.0 / 12.0。）

**三层都要处理**：

```python
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ① 样式层：把规范值写进样式
for name, size, bold in [("Normal", Pt(12), None), ("Heading 1", Pt(12), True),
                         ("Heading 2", Pt(12), True), ("Title", Pt(16), True),
                         ("Author List", Pt(12), None), ("List Bullet", Pt(12), None)]:
    st = doc.styles[name]; st.font.name = "Times New Roman"; st.font.size = size
    if bold is not None: st.font.bold = bold

# ② 段落层：删除散乱的 w:spacing 字号覆盖
for p in doc.paragraphs:
    ppr = p._p.find(qn('w:pPr'))
    if ppr is None: continue
    rpr = ppr.find(qn('w:rPr'))
    if rpr is None: continue
    for tag in ('w:sz', 'w:szCs'):
        e = rpr.find(qn(tag))
        if e is not None: rpr.remove(e)

# ③ run 层：显式写 w:rFonts(四属性) + w:sz + w:szCs
def force_run(r, size, bold=None):
    r.font.name = "Times New Roman"; r.font.size = size
    rpr = r._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None: rf = OxmlElement('w:rFonts'); rpr.insert(0, rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'):
        rf.set(qn(a), "Times New Roman")
    for tag in ('w:sz', 'w:szCs'):
        e = rpr.find(qn(tag))
        if e is None: e = OxmlElement(tag); rpr.append(e)
        e.set(qn('w:val'), str(int(size.pt * 2)))     # 半磅值
    if bold is not None: r.font.bold = bold
```

**只设 `run.font.size` 不够**：必须同时写 `w:rFonts` 四属性与 `w:sz`/`w:szCs`，
否则中英文字体不一致、或被样式回退覆盖。

**表格**：单独统一（正文 12 pt 时表格 8–10 pt 是排版惯例）。
⚠️ 用 `doc.add_table` / `t.style="Table Grid"` 新建的表**不是三线表**（有网格线）——
必须改成 `tblStyle=12`（或与既有合格表一致）+ 单元格级 `tcBorders`
（首行 top=12 粗、bottom=6 细；末行 bottom=12；左右 `nil`）。

---

## 三、段落间距不一致的根因与修复

**根因**：各类元素（表标题 / Panel 标签 / 表注 / 分节标题）的 `space_before/after` 各写成不同值，
再加上零散**空段落**当分隔符，最终同一文档出现 9 种间距组合 → 视觉上"有的地方一片空白、
有的地方紧贴"。

**修复：按角色分类，设统一间距；空段落全删（分隔交给段后间距）**

| 角色 | 段前 | 段后 |
|---|---|---|
| 文档标题 | 0 | 12 |
| 一级标题 / 表图标题（`Table N.` / `Figure N.` / `Supplementary Tables`） | 12 | 6 |
| 二级标题（`3.1 …`） | 10 | 4 |
| Panel 标签（`Panel A.`） | 8 | 3 |
| 正文 / 表注 | 0 | 6 |

```python
def classify(t, style):
    if style == "Title": return "title"
    if style.startswith("Heading 1"): return "h1"
    if style.startswith("Heading"): return "h2"
    if re.match(r'^(Table|Figure)\s+S?\d+\.', t): return "cap"
    if re.match(r'^Panel [A-Z]\.', t): return "panel"
    return "body"

# 删空段落（保留含图的段落！）
empties = [el for el in body.iterchildren()
           if el.tag == qn('w:p')
           and not "".join(n.text or "" for n in el.iter(qn('w:t'))).strip()
           and not el.findall('.//' + qn('a:blip'))]      # ← 这条不能漏
for el in empties: body.remove(el)

# 逐个段落写 pPr/w:spacing（before/after 用 twips = pt*20，line=240 单倍）
```

`line_spacing` 统一 1.0；同时把同一套值写进样式层（Normal / Heading 1 / Heading 2）。

---

## 四、验收指标（写成脚本，别目视）

- 每个文件内**正文字号种类数 = 1**、字体集合 ⊆ {Times New Roman}
- 每个文件内**表格字号种类数 = 1**（跨文件不同可以，文档内必须统一）
- 每个文件内**间距元组种类数 = 角色数**（不是 9 种、不是 1 种）
- **空段落数 = 0**（除含图的段落）
- **非三线表数 = 0**（判据：表级 `tblBorders` 全为 none/nil **且** 无 left/right 竖线）

---

## 五、⚠️ 顺序要求（与 §10 联动）

**所有 python-docx 的字体/间距/结构修改都要排在「图片重嵌」之前**。
python-docx 的 `save()` 会重建 OPC package，把此前 `zipfile` 级替换的 `word/media/*.png`
还原成旧版。正确流水线：

```
① python-docx 改文字/样式/间距/结构（可反复保存）
② 最后一步 zipfile 换图 + 同步 wp:extent
③ 立即校验内嵌图 md5 **与像素尺寸**
④ 此后不再用 python-docx 打开该文件
```

v22 实测：字体统一脚本保存主稿后，此前修好的高清图（2160 px）被打回低清旧版
（1342×1340 / 1135×753），且日志毫无异常——不主动复检就发现不了。
