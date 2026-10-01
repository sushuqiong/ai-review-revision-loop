# 原位改稿与图表 QA 工具箱（Minimal In-Place Revision Toolkit）

返修（Revision）阶段的实操工具箱。核心目标：**在作者已提交的原件上做最小改动**，而不是重新生成一份"更好的"文件。
本文覆盖 python-docx 原位改稿、合并图子面板原位替换、图件矢量文字层 QA、R/ggplot 与 markdown→docx 的已知坑。

**姊妹文件**：
- `references/change-highlighting-for-review.md` —— 用户要求"把改动/新增的地方标蓝方便我核对"时的做法（确定性标记法、为什么不能用 diff、去蓝标投稿版、四项验证）。
- `references/figure-composition-conventions.md` —— 补充图构图规范（子面板字母放**绘图区之外**、图上不写说明文字、图上**必须**显示统计值与 P 值、图例必须真渲染、非语法列名坑）。
- `references/composite-figure-panel-replacement.md` —— 合并图子面板原位替换完整流程。

---

## 0. 三条硬规则（先读）

1. **复用作者原件，禁止重写**。Title Page / Highlights / Declaration of interest / Cover letter / Figure legends / Table 1–3 一律从作者已上传的原文件出发。
   - Highlights、Declaration：**原样复制**（`shutil.copy2`）。
   - Title Page：只改必须变的字段（如字数），其余逐字保留。
   - Cover letter：只把 "submit" 改 "resubmit" + 加一段返修说明。
   - Figure legends：用**提交版原文**，再补新增图注。
   - 重写＝把作者已定稿的话换成"你的话"，用户会直接质问"不能借用原文的信息吗？这些我都上传过"。
2. **先用作者提交的合并 PDF 建立 ground truth**，再决定改什么。作者通常有 `JCEH-D-XX-xxxxx.pdf` 之类的 Editorial Manager 合并版。逐项核对：图注是简版还是详版？补充图注到底交了没有？原始声明里真的写了那句话吗？
   → 本地常有**多套互相矛盾的历史草稿**（本次：用户 Figure Legends 文件里同时存在 "Figure 1." 和 "Fig.1" 两套图注，且 Figure 1–3 编号互相冲突；只有合并 PDF 是事实）。
3. **绝不自爆**。返修意见没提的问题，不主动声明、不加未要求的 caveat、不写"原稿这里不准确我们已经改正"。
   - 自己新写的句子若经不起复核 → **删掉这句**，而不是加限定语。（本次教训：为回答主编"FIB-4 含年龄"新写的 "within every age decade…" 在 30–39 层反了；正确做法不是改成 "aged 40 years or older"，而是整句删掉、只说 "the association was also apparent in age-stratified analyses"。）
   - 回复信里禁止出现 `the manuscript previously described X, which was not accurate`、`We are grateful to the reviewer for prompting this correction` 这类自我检讨。
   - **审稿人直接问到的内容必须正面如实回答**（例："组间不平衡会不会影响显著性" → 必须报告 n/9 显著、哪个未达显著）。那不是自爆。

---

## 1. python-docx 原位改稿

### 1.1 三个基本动作

```python
def set_text(p, txt):
    """整段替换，保留首个 run 的格式（字体/字号）"""
    runs = p.runs
    if runs:
        runs[0].text = txt
        for r in runs[1:]:
            r._element.getparent().remove(r._element)
    else:
        p.add_run(txt)

def clone_after(anchor, template, txt):
    """在 anchor 之后插入一段，格式抄 template（用于新增小节标题/正文）"""
    import copy
    from docx.text.paragraph import Paragraph
    new_p = copy.deepcopy(template._p)
    for child in list(new_p):
        if child.tag.endswith("}r"):
            new_p.remove(child)          # 清掉模板正文，只留段落属性
    anchor._p.addnext(new_p)
    np = Paragraph(new_p, anchor._parent)
    np.add_run(txt)
    return np
```

插入顺序：**先插正文再插标题**，两次都 `clone_after(anchor, ...)`，就能得到 `anchor → 标题 → 正文`：

```python
clone_after(ps[anchor_i], ps[body_i], body_text)   # 先正文
clone_after(ps[anchor_i], ps[head_i], head_text)   # 再标题，插到 anchor 与正文之间
```

用 anchor 段（前一小节的正文段）而不是用 `addprevious`——`addprevious` 会把标题插到前一节标题和正文之间，造成 "2.3.6 标题 → 2.3.5 正文" 的错位（本次踩过）。

### 1.2 正文引用改上标：run 级切分

```python
CITE = re.compile(r"\[(\d+(?:\s*[\u2013\-,]\s*\d+)*)\]")

for p in doc.paragraphs[:i_refs]:          # ← 只扫正文，见下方 1.3
    for run in list(p.runs):
        if "[" not in run.text:
            continue
        parts = CITE.split(run.text)
        if len(parts) == 1:
            continue
        run_el = run._element
        run.text = parts[0]
        anchor = run_el                     # ← 锚点必须是 run 元素
        for j in range(1, len(parts), 2):
            nr = copy.deepcopy(run_el)
            anchor.addnext(nr)
            R = Run(nr, p); R.text = parts[j]; R.font.superscript = True
            anchor = nr
            if parts[j + 1]:
                ar = copy.deepcopy(run_el)
                nr.addnext(ar)
                A = Run(ar, p); A.text = parts[j + 1]
                anchor = ar
```

**致命坑**：如果写成 `parent = run._element.getparent(); parent.addnext(nr)`，`parent` 是 `<w:p>`，run 会被插到**段落元素之外**（body 层）。后果是：`p.text` 里再也搜不到 `[n]`（看起来"转换成功、无残留"），但引用数字**实际已从正文流中丢失**。验证方法是数上标 run 的数量是否等于正文里 `CITE.findall` 的总数。

**范围坑**：`CITE` 会误伤数学表达式的方括号吗？不会——`log10[TG/HDL-C]`、`ln[TG × fasting glucose / 2]`、`[HBcAb]`、`[eGFR]` 都不匹配纯数字模式。但**必须**排除参考文献段（见下）。

### 1.3 参考文献段必须单独处理

- 引用上标转换的扫描范围用 `doc.paragraphs[:i_refs]`（`i_refs` = "References" 段索引）。若把参考文献段也扫进去，`[1] Moon AM...` 的开头 `[1]` 会变成上标，随后 `^\[(\d+)\]` 再也匹配不到，条目改造静默失败。
- 条目改造：`re.sub(r"^\[(\d+)\]\s*", r"\1. ", text)`。
- 改完必须验：条目数、编号是否严格 `1..N`、正文是否还有残留 `[n]`。

### 1.4 图注区在 References 之后

本次的 Figure legends 小节在参考文献**后面**（docx 段序上位于 `i_refs` 之后）。任何"只在正文里找图注"的循环（`doc.paragraphs[:i_refs]`）都会漏掉它。要改图注就扫全文。

### 1.5 lxml 的 `addnext()` 返回 None

```python
# ✗ 会崩：'NoneType' object has no attribute 'add_r'
new_p = anchor._p.addnext(anchor._p.makeelement(qn("w:p"), {}))
np = Paragraph(new_p, anchor._parent)

# ✓ 先造元素，再插入，再包 Paragraph
new_el = anchor._p.makeelement(qn("w:p"), {})
anchor._p.addnext(new_el)
np = Paragraph(new_el, anchor._parent)
```

### 1.6 整段替换必须在"引用转上标"之前（顺序硬约束）

`set_text()` 把段落所有 run 合并进首个 run —— **包括上标 run**。所以任何**事后**对含引用段落的 `set_text()`，都会把该段的上标引用压平成普通文字，而且**不留痕迹**：正文里搜不到 `[13]`（方括号早在转换时就被消费掉了），看起来"零残留、很干净"，实际引用 13 已不再是小标。

本次症状：把探针去重那句话的修正放在了转换之后对 Methods 2.2.1 整段 `set_text()` → `[13]` 被压平 → 引用首现序变成 `1…12, 14…54`，**引用 13 表现为"从未被引用"**。这一条只有靠"上标编号集合 == 1..N"才能发现（看"上标 run 数 ≈ 引用出现数"是发现不了的）。

正确顺序（一次成型，文本替换全部前置）：

```
加载原件 → 段落/句子级文本替换(set_text) → 插入新段落 → 引用转上标 → 参考文献条目改造 → save
```

如果确实要分多轮编辑：每轮改完文本后**重跑**一次上标转换（幂等——不含方括号的段落会被跳过），但前提是该轮没有把方括号本身改掉。

---

## 2. 字数口径校准

不同口径差得很远，**必须用作者已提交的 PDF/标题页反推口径**，不要自己选一个。

本次实测（同一份正文）：

| 口径 | 原稿 | 说明 |
|---|---|---|
| 正则分词 `[A-Za-z0-9'’\-]+` | 4,849 | 会把 `-0.133` 之类拆开 |
| 空白分词（`text.split()`） | 4,638 | 最接近常规"字数" |
| 作者标题页申报值 | 4,483 | 比空白分词还宽约 3% |
| 结构化摘要（4 段）空白分词 | **245** | **与标题页 "Abstract: 245 words" 完全一致** |

结论：
- **摘要**口径 = 结构化摘要**四段正文**的空白分词数（不含标题、作者、Keywords、ABSTRACT 页眉）。要压到目标区间就按这个口径算，并让脚本自动挑选落在区间内的候选版本（本次给出 A–D 四个候选，脚本选出 250 词的那个）。
- **正文**口径 = 空白分词（Introduction → References）。作者申报值可能比实测宽，要**如实告知**并给用户 A/B/C 选项（保持实测 / 用作者旧口径 / 再压缩），不要默默挑一个好看的数字。

---

## 3. 合并图子面板原位替换（要点摘录）

完整流程见 `references/composite-figure-panel-replacement.md`。本次新增的要点：

- **用文本层定位面板网格**：`page.get_text("dict")` 里 A/B/C… 字母 span 的 bbox 就是每个子面板左上角。多面板图通常有 2 列 × N 行。
- **量内容 bbox**：`get_pixmap(dpi=200, clip=区域)` → PIL `L` 模式 → 逐行/逐列统计暗像素 → 取边界。注意 clip 别跨到相邻面板（会把邻面板内容算进来）。
- **换面板**：`add_redact_annot(rect, fill=(1,1,1))` → `apply_redactions()` → `show_pdf_page(clip, src_doc, 0, clip=src_content_bbox)`。按目标框等比缩放居中，避免拉伸变形。
- **字母要重画**：原图的字母常是 **ArialMT 24pt、颜色 #231815**（不是纯黑、不加粗）。但复合图里嵌的是**字体子集**，`insert_text(fontname=<原字体名>)` 会报 `need font file or buffer` → 用 `fontname="helv"`（Arial 度量等价）。
- **字母基线对齐**：`insert_text` 的 y 是**基线**，原 span 的 bbox[1] 是**顶边**。先试一次，量出新 span 的 bbox[1]，反推 `y_correct = y_trial + (bbox_top_wanted - bbox_top_got)`。本次第一版高了 17pt。
- **PyMuPDF 不能写 TIFF**（`Image format tiff not in (...)`）→ 渲染 PNG 后走 PIL：`im.save(path, format="TIFF", compression="tiff_lzw", dpi=(400,400))`。
- **R 的 `ggsave(..., device=cairo_pdf, compression="lzw")` 会报"参数没有用"并中止**——`compression` 只给位图设备。

---

## 4. 图件 QA：读矢量文字层，不要靠 OCR

**这是本次最大的效率提升。** cairo_pdf 产出的 PDF 文字是**真实文本**，可以直接读：

```python
spans = [(s["text"].strip(), round(s["bbox"][0],1), round(s["bbox"][1],1), round(s["size"],1))
         for b in page.get_text("dict")["blocks"]
         for l in b.get("lines", []) for s in l["spans"] if s["text"].strip()]
```

可以精确检查：
- 统计标记个数：`Counter(t for t,*_ in spans if t in ("*","**","***","ns"))` → 期望 9 个（4×`***` + 4×`*` + 1×`ns`）。
- 关键 label 是否存在：`P = 0.05`、`kg/m`（+ 单独的 `2` span 且 y 更小 ⇒ 真上标）、各基因名。
- **裁剪检查**：任何 span 的 bbox 落到页面外 ⇒ 会被裁掉。
- 面板字母位置是否与其它字母同一 y（对齐）。

OCR 对小号字**不可靠**：本次 OCR 反复漏报 `***`、`P<0.001`、`P = 0.05`，害我误判"注释丢了"；换成文字层后一次查清。OCR 只用于**没有文字层**的图（如作者用 Illustrator 导出的老图）。

**还要查"图例是否真的渲染出来了"。** 本次某面板两组柱子同色、图例整个消失（`data.frame(\`>0.40\`=…)` 把非语法列名改写成 `X.0.40` → `scale_fill_manual` **静默失配**，只留一条极易被淹没的 warning）。文字层扫描和"标记个数"检查**都发现不了它**——必须**逐条列出期望的图例标签去 grep**，再用像素抽样确认分组颜色确实不同。详见 `figure-composition-conventions.md` §4。

**当"注释好像没渲染"时，先查数据而不是查样式**：本次 S8 面板 A 的 P 值全部消失，根因是 `head_room <- max(m + 1.96*se)` 遇到某个 n=1 的组算出 `sd = NA` → `max(..., na.rm=FALSE) = NA` → 所有 `y = NA` → 文本被静默丢弃，`limits=c(0, NA)` 还把 y 轴退回数据范围。修法：`na.rm=TRUE` + 过滤掉样本太少的分层 + 用**显式 limits** 而不是 `expansion()`。

---

## 5. R / ggplot 已知坑

| 症状 | 原因 | 修法 |
|---|---|---|
| `错误: \uxxxx sequences not supported inside backticks` | 反引号内的名字里写了 `\u2265` 之类转义 | 把 label 先存成变量再 `setNames(values, labs)`，或全用 ASCII（`>= 12.0`） |
| `No shared levels found between names(values) of the manual scale and the data's fill values` | `scale_*_manual(values=c(\`A\`=...))` 的名字与数据水平对不上（含上面那种转义失败） | 一律 `setNames(c(...), data_levels)`；logical 数据先把 `hub` 转成 `factor(c("no","yes"))` |
| `geom_text(..., y = Inf, vjust = 1.3)` 看不见 | 超出面板范围被裁 | 用显式位置：`y = ytop * 1.015` + `scale_y_continuous(limits = c(NA, ytop * 1.13))` |
| `filter(hub)` 报 `must be a logical vector, not a <factor>` | 把 logical 列改成 factor 后忘了改过滤条件 | `filter(hub == "yes")` |
| 同一位置文字被画两遍（视觉发粗） | `geom_text` 继承了多行数据（每个分层两行） | `data = df %>% distinct(group, p) %>% mutate(y = ...)` |
| `ggsave(compression="lzw")` 到 cairo_pdf 中止 | cairo_pdf 不支持该参数 | 只在 tiff/png 设备上传 compression |
| heredoc 写 .R 失败（exit -1 / 内容错乱） | bash 与 R 的转义冲突 | 用 `write_file` 写 .R 文件，别用 `cat > x.R <<EOF` |
| `Rscript -e '...'` 段错误 | 内联脚本的引号/转义 | 写成 `.R` 文件再跑 |

---

## 6. Markdown → docx 转换坑

- **表格里的转义竖线 `\|`**：`line.split("|")` 会多切出单元格，行宽超过表头 → `IndexError`。转换器要按表头列数截断/补齐：
  ```python
  ncol = max(len(r) for r in raw)
  row = (row + [""] * ncol)[:ncol]
  ```
  同时把源 md 里的 `\|` 换掉。
- **东亚字体**：`nrm._element.rPr.rFonts.set(...)` 在 `rPr` 为 None 时崩 → 用 `nrm._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")`。
- 支持 `**粗体**` / `` `代码` `` / `~~删除线~~` 的最小富文本切分：
  `re.split(r"(\*\*[^*]+\*\*|`[^`]+`|~~[^~]+~~)", txt)`。
- 三线表：表格级 `w:tblBorders` 设 top/bottom = single、left/right/insideH/insideV = none，再给表头行单元格加 `w:bottom` 单线。

---

## 7. 收工自检清单（本次实际跑过的）

- [ ] 手稿旧表述已清除（逐条 grep 旧句子，含"已改过的那句"的原始措辞）
- [ ] 上标引用数 == 正文 `[n]` 出现次数；正文残留 `[n]` == 0
- [ ] 参考文献条数 + 编号严格 `1..N`；被引但未列 / 已列但未被引 == 0
- [ ] 参考文献偏离规范项已逐条核对（作者数 ≤6 全列 / ≥7 取前 6 + et al.）
- [ ] 每张图的矢量文字层检查：标记个数、关键 label、有无越界 span
- [ ] 每个 docx 段落数非 0、补充表行数合理
- [ ] 文件名/时间戳确认复用件（原样复制的 Highlights/Declaration 时间戳应保持不变）
- [ ] 交付夹无冗余变体（同名重复图、废弃中间版本已删；预览 PNG 收进子目录）
- [ ] **上标编号集合 == `1..N`**（不是"个数差不多"）——见 1.6
- [ ] **术语全文统一**：`Supplementary` vs `Supplemental` 只留一个；含 cover letter、图注、表名、**文件名**
- [ ] 图表引用带**完整前缀**：写 `Supplementary Table S1`，不要裸写 `Table S1`（读者无法判断是否在补充材料）
- [ ] 改了文件名后：旧名文件已删、生成器路径已改、README/交付说明里的名字已同步
- [ ] 标题页申报的字数 == 实测字数（用同一口径）
- [ ] 复检脚本本身也验一遍（见下）
- [ ] **标蓝核对版**（用户要"改动标蓝"时）：核对版蓝标段落数 == 改动处数；去蓝标版 == 0；**两者正文逐字相同**；无残留 `\ue000/\ue001`
- [ ] 每张图：字母在**绘图区之外**（方位/字体/颜色照作者原图量）、图内无说明文字、统计值与 P 值**完整显示**且不重叠、每个预期**图例都渲染出来了**
- [ ] 生成的 docx 里没有**字面反斜杠转义**（grep `u2217` / `r"\\u[0-9a-fA-F]{4}"`，见 §8.3）

### 7.1 验证"校验器"——本次三个假警报

QA 脚本自己会错，误报比漏报更浪费时间（会逼你去改本来正确的东西）：

| 写法 | 问题 | 正确写法 |
|---|---|---|
| `rev.count("eight of the nine")` | `rev` 是**段落列表**，`list.count` 数的是"等于该字符串的元素" | `"\n".join(rev).count(...)` |
| `r"^\d+\.\s[A-Z][a-z]"` 数参考文献 | 漏掉机构作者条目（`8. GBD 2019 Hepatitis B Collaborators.`） | `r"^\d+\.\s"` |
| `r"^Fig\.\d"` 数图注 | 漏掉 `Fig. 1`（点数后有空格） | `r"^Fig\.\s?\d"` |

用 `scripts/qa_revised_manuscript.py` 跑这套检查，它的正则已按上表修正。

---

## 8. 多轮"打补丁式"改生成器脚本的两个坑

1. **跨行拼接的字符串会躲开 `str.replace`。** 生成器里常写：

   ```python
   NOTE = ("… (Supplemental "
           "Figure S6); …")        # 源码里根本不存在连续的 "Supplemental Figure"
   ```

   `s.replace("Supplemental Figure", "Supplementary Figure")` **静默不命中**，交付件于是残留旧词（本次改了 3 轮才清干净）。修法：替换**更短的 token**（`"Supplemental "` → `"Supplementary "`），改完再 `grep -c` 生成出的 docx 文本复核词频；或按行号定点改。
2. **改名要连带三处**：生成器里的路径、**已落盘的旧名文件**（`os.remove`）、以及 README/交付说明里的文件名。漏一处用户第一次打开文件夹就会发现对不上。
3. **转义层数会静默出错，产出"字面反斜杠"。** 用补丁脚本去写生成器源码时，多转义一层就会把 `\u2217` 变成字面量：补丁脚本里写 `"\\\\u2217"` → 生成器源码里成了 `"\\u2217"` → Python 求值成**反斜杠 + u2217 文本**，交付的 docx 图注里就真的印着 `(\u2217 FDR < 0.05; \u2217\u2217\u2217 …)`。本次就是这样，直到标蓝核对时才被看见。
   - **预防**：能写 ASCII 就写 ASCII（星号用 `*`、不等式用 `>=`），别为了排版用 `\uXXXX`。
   - **探测**：交付前 grep 生成出的 docx 文本——`"u2217" in text` / 正则 `r"\\u[0-9a-fA-F]{4}"`；同源问题也会出现在 `\n`、`\t`、`\u2013` 上。
   - 这是"生成器脚本被补丁脚本反复改写"这一模式的通病：**每多一层工具，转义就少一层**。

---

## 9. 收工汇报时的措辞（本用户偏好）

- 只报**一个**数字。不要写"已压到 250 词（提交版 245 词，标题页填 250）"——用户会回"到底是多少个词，不能统一吗？"。要写成：`提交版 245 → 修改后 250；标题页、正文、README 三处一致`，并把三处核对结果列成一行。
- 交付前主动列出"我这轮自己抓出并修掉的问题"（含**我自己引入的 bug**）。本次主动报了上标压平与术语不统一两处，用户反应是正面的。
- 用户说"千万不要有低级错误"时，交付前必须跑一遍 `scripts/qa_revised_manuscript.py` 并**报出通过/失败计数**，而不是只说"已检查"。
