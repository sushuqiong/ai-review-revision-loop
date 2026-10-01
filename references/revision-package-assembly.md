# 返修包组装（Resubmission Package Assembly）

本文是 `ai-review-revision-loop` 的配套参考，覆盖"返修意见已到手 → 组装并交付返修包"这一段。
（SKILL.md 已超 100 KB 上限，无法再加指针；本文件请视为该节内容的正式归属。）

---

## 0. 最高优先级：复用用户已提交的原件（用户多轮纠偏）

用户对"我上传过的东西你又重写了一遍"极其反感。规则：

- **Title Page / Highlights / Declaration of interest / Cover letter = 直接复制用户原文件**，只改**必须**改的字段（Title Page 通常只有字数）。
- 原件位置：用户投稿目录（如 `Desktop/<项目>/文稿!/`）。用户说"我传的都是时间近的" → **按文件 mtime 取最近的同名文件**，不要去翻旧的失败投稿版本。
- 拿不定时：**先读原件**再决定动不动，不要习惯性重新生成。
- Highlights 常见误解：以为要重写才合规。**先数原件的字符数**——本用户的 5 条本来就 ≤85 字符（Elsevier 上限），原样复制即可。

## 1. 审稿没提的，不改、不自爆

- 不主动改结论表述、不主动剔除基因/样本/次要结果、不主动扩大负面披露。
- 自己发现的新问题 → **只告知用户 + 给 A/B/C 选项**，由用户拍板（本用户明确要求这个格式）。
- **例外（不算"自爆"）**：原文有**事实性错误**（某句经复算不成立、文献卷号/作者数写错、Methods 描述与代码不符）→ 必须改，并主动告知用户改了哪里。判断标准：**是"被问到没被问到的内容"还是"事实错误"**。
  - 本次实例：原文"每个年龄十年内高 FIB-4 组 AIP 都更低"经复算在 30–39 岁层是反的（该层高 FIB-4 仅 13 人，P=0.376）→ 改成"在 40 岁及以上的每一层内……"，仍然有力且准确，并在交付说明里点出这是唯一被改动的实质结论表述。
  - 本次实例：参考文献 [44] 卷号 16 应为 17、作者数按 7 位处理但实际 5 位 → PubMed 核实后改正。

## 2. 正文：在用户原始 .docx 上**原位**修改

重新生成整篇会引入措辞漂移，违反"尽量不大改原手稿"。**必须**改成定点编辑，其余段落与原件逐字一致。

用 python-docx 做，三个工具函数：

```python
def set_text(p, txt):
    """保留第一个 run 的格式，替换整段文字"""
    runs = p.runs
    if runs:
        runs[0].text = txt
        for r in runs[1:]:
            r._element.getparent().remove(r._element)
    else:
        p.add_run(txt)

def clone_after(anchor, template, txt):
    """在 anchor 之后插入新段落，沿用 template 段落的格式"""
    new_p = copy.deepcopy(template._p)
    for child in list(new_p):                      # 清掉内容，保留 pPr
        if child.tag.endswith("}r"):
            new_p.remove(child)
    anchor._p.addnext(new_p)
    np = Paragraph(new_p, anchor._parent)
    np.add_run(txt)
    return np
```

插入位置：先 `print` 出所有非空段落的 `[index] text[:100]` 建立索引表，再用**原始索引 + 降序处理**做插入，避免索引漂移。新小节 = 标题段 + 正文段，都插在**上一小节正文段之后**（不要插在上一小节的标题和正文之间——本次踩过）。

### 引用改上标（ICMJE/Vancouver）

```python
CITE = re.compile(r"\[(\d+(?:\s*[–\-,]\s*\d+)*)\]")
for p in doc.paragraphs[:i_refs]:          # ← 只遍历正文，绝不含参考文献表
    for run in list(p.runs):
        parts = CITE.split(run.text)
        if len(parts) == 1: continue
        run_el = run._element               # ← 必须锚在 run 元素上
        run.text = parts[0]
        anchor = run_el
        for j in range(1, len(parts), 2):
            nr = copy.deepcopy(run_el); anchor.addnext(nr)
            R = Run(nr, p); R.text = parts[j]; R.font.superscript = True
            anchor = nr
            if parts[j+1]:
                ar = copy.deepcopy(run_el); nr.addnext(ar)
                Run(ar, p).text = parts[j+1]; anchor = ar
```

四个坑（都实际踩到过）：
1. **`parent.addnext()` 里 parent 用 `run._element.getparent()`（= `<w:p>`）会把 run 插到段落外面**（跑到 body 层），引用数字从此"消失"→ 上标数为 0 但"残留 `[n]` 也为 0"。**必须锚在 run 元素上**。
2. **遍历范围必须 `[:i_refs]`**，否则参考文献表里的 `[1]` 也被转成上标，导致后面 `^\[\d+\]` 的编号改写匹配不到（表现为"references reformatted: 1"）。
3. `_p.addnext(el)` 是 lxml API，**返回 None**；要 `el = p._makeelement(...)` → `p.addnext(el)` → `Paragraph(el, p._parent)`，不能写成 `Paragraph(p.addnext(...), ...)`。
4. 替换整段前先确认该段**没有需要保留的内部格式**（斜体物种名等）；否则改用句子级 `.replace()` 而不是整段替换。

### 参考文献表格式

- `[n] Author...` → `n. Author...`：`re.sub(r"^\[(\d+)\]\s*", r"\1. ", text)`
- 编号**不用重排**（原稿本来就是按首现顺序），前提是本轮**不新增文献**。
- 想避免重排：新增分析**不引入新文献**，把文献引用写进 Response letter 的正文（响应信不受稿件文献表约束）。本次即用此策略保住了 54 条编号不动。
- 复核：编号连续 1..N、无重复、正文首现序严格递增、作者数 ≤6 全列 / ≥7 前 6 + et al.。

## 3. Figure Legends 源文件对账（容易丢信息）

用户原始的 legends docx 里**常有不止一套图注**，且编号互相矛盾。本次：详细版把 Figure 1 写成 NHANES 流程图、Figure 3 写成研究设计图；简版（= 正文那套 = 图文件名）是 Fig.1=研究设计 / Fig.2=NHANES / Fig.3=CHARLS。

处理：
- **以"图文件名 + 正文引用"为编号基准**（用户看得见这些），用**详细版的完整文字**（P 值、HR 区间、模型定义等细节），把顺序改正。
- 逐条比对，**一条信息都不丢**；顺手修原件的拼写/千分位（本次修了 "suppressio n" → "suppression"、"5946" → "5,946"）。
- 术语统一：原作用 "Supplementary" 就别混用 "Supplemental"（本次因混用返工过一次）。
- 最后**问用户确认用的是哪套**——这是唯一会影响外观的判断题。

## 4. 表格

- **主表（Table 1–3）：原样复制**进交付文件夹，不要重排/重绘。
- **补充表：一表一文件**（不要合并成一个 docx），且是**三线表**。
- 三线表实现（python-docx）：table style 用默认，然后

```python
borders = OxmlElement("w:tblBorders")
for edge, val in (("top","single"),("bottom","single"),("left","none"),
                  ("right","none"),("insideH","none"),("insideV","none")):
    e = OxmlElement("w:" + edge); e.set(qn("w:val"), val)
    if val == "single":
        e.set(qn("w:sz"), "8"); e.set(qn("w:color"), "000000")
    borders.append(e)
tblPr.append(borders)
# 表头行再给每个单元格加 w:tcBorders/bottom=single → 得到顶线+表头线+底线
```

## 5. 图件

- **图内不放说明文字**：`plot_annotation(title=..., caption=...)`、subtitle 一律删掉。只留坐标轴标签、图例、facet 条、子图字母。所有解释写进 Figure legends。**原图没有的东西不要加**（用户原图只在个别 panel 有短标题，不要额外发明 subtitle 去解释星号口径）。
- **子图字母照抄原图**：先用 PyMuPDF 从原合成图抽 span，拿到字母的 `font`（如 ArialMT）、`size`（24）、`color`（采样得 `#231815`）、`bbox`；patchwork 里用
  `plot_annotation(tag_levels="A") & theme(plot.tag = element_text(size=?, colour="#231815", family="sans", face="plain"))`。
  字号按页面宽度等比例缩放（原 24pt / 595pt 宽 → 17cm 页约 14pt）。
- 交付只放**上传需要的格式**（pdf + tiff），PNG 预览放 `核对预览/` 子目录。**删掉中间产物**（如单 panel 版本的三种格式副本）。
- 布局：多 panel 补充图用 `plot_layout(widths=c(1,1), heights=c(1,1))` 保证**等大**。

## 6. R / ggplot 陷阱（本次实际踩到）

- **反引号里不能用 `\uXXXX`**：`` c(`\u2265 12.0` = ...) `` 直接报错 `\uxxxx sequences not supported inside backticks`。
  → 标签先赋变量：`lab <- "\u2265 12.0"`，再用 `scale_*_manual(values = setNames(cols, labs))`。
  另外 `scale_*_manual(values=c(...))` 的**名字必须与数据里的 levels 完全一致**，否则报 "No shared levels found" 且图例空白；用 `setNames()` 最稳。
- `filter(col)`：col 变成 factor 后报 `must be a logical vector` → 改 `filter(col == "yes")`。
- **`max(x, na.rm=FALSE)` 遇某层 n=1**（sd/se = NA）→ 锚点值变 NA → `geom_text(y = anchor*1.03)` 的标注**被静默全部丢弃**，同时 `scale_*(limits=c(0, NA))` 悄悄改变坐标范围。
  → 锚点一律 `na.rm=TRUE`，并**先过滤掉每组样本量过小的层**（本次：某年龄层高 FIB-4 仅 1 人，改为每组 ≥10 人才作图）。这类层不画反而更严谨，图注里写明"样本量不足的层未显示"。
- **`y = Inf` + `vjust > 1`** 的标注会随 `scale_*_continuous(expand=)` 被裁掉 → 改**显式数据坐标 + 显式 limits**。
- 同类标注**每个层只画一次**：`geom_text` 的 data 若每层有两行（两个分组），会叠画两次同位置文字（看起来偏粗）→ 先 `distinct(level, p)`。

## 7. 图件 QA：用**矢量文本层**，不要只靠 OCR

tesseract 对小字号/45° 旋转文字极不可靠（本次多轮 OCR 都没看出"标注根本没画出来"）。
**从生成的 PDF 抽文本层**才是可靠手段：

```python
pg = fitz.open(pdf)[0]
spans = [(s["text"].strip(), s["bbox"], s["size"])
         for b in pg.get_text("dict")["blocks"]
         for l in b.get("lines", []) for s in l["spans"] if s["text"].strip()]
# 1) 标注是否存在/数量对：Counter(t for t,*_ in spans if t in ("*","**","***","ns"))
# 2) 是否被裁到画布外：bbox 超出 page.rect 的 span 数应为 0
# 3) 上下标是否正确：如 "BMI (kg/m" 与单独的 "2" 两个 span，且 "2" 的 y 更小（抬升）
```

## 8. 数据源 URL 变更：NHANES / CDC

- 现行路径：`https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/<年>/DataFiles/<FILE>.xpt`
  （例：`.../Public/2017/DataFiles/LUX_J.xpt`；R 里用 `haven::read_xpt()` 直接读）
- **陷阱**：旧路径 `Nchs/Nhanes/<yyyy-yyyy>/<FILE>.XPT` 现在返回 **HTTP 200，但内容是 HTML "Page Not Found"**，而且不同文件长度都恰好 **20905 字节** —— 只看状态码会以为下载成功。
  → 下载后**校验内容**（`file` 命令 / 长度 / 魔术字节），不要只看 `%{http_code}`。
- 复算纪律：写新分析前，**先从原始数据重建分析队列并复现原文数字**（本次复现 n=4,010、低/高危 2,932/1,078、排除链 7,377→7,025→813、Model 4 β=−0.133 全部吻合）。只有地基对上了，新分析的数值才敢往正文写。
  - 副产品：发现原 R 代码多写了一项 `!is.na(HBV)` 把样本算成 3,955 → 修正并备份原文件。

## 9. 诚实处理"新分析不支撑原文"

审稿人/编辑点名要求的新分析如果不支撑原文，**全部模型都报**（含方向相反的粗模型），并给出机理解释，**不要只挑校正模型**。
本次：VCTE 粗模型正相关（LSM≥8 那组 BMI 36.0 vs 29.0，体脂混杂是已知的弹性成像局限），校正后翻转为负且显著 → 两种都写进 Results 和 Supplementary Table，并说明"因弹性成像受体脂影响，未校正估计反映的是肥胖—血脂轴"。
用户明确认可这个调子："支持性证据 + 如实说明混杂"。

## 10. 交付前 QA 清单

- docx 内无 `[[` 占位符残留、无 `[n]` 方括号引用、上标引用数 = 正文引用数。
- 参考文献：编号 1..N 连续、首现序严格递增、列全/et al. 规则正确。
- 图：span 数、显著性标记计数、超界 span 数 = 0；新增/改动图附 preview。
- 字数：Title Page 与正文实测一致，并写明计数口径（用户上次投稿的口径）。
- 交付说明里逐个列出：哪些沿用原件、哪些新建、哪个文件必须替换原图。
