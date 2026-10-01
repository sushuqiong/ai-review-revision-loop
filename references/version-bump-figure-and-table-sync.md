# 版本升级件同步：图重嵌 + 补充材料 + Tables 投放（课题2 v20→v21 实测）

来源：2026-09-30/10-01 课题2 v21（M4 口径由**线性** age/BMI 改为**匹配** log10 age/BMI）。
适用场景：论文已有交付包，本轮只改了**少数图的数值**或**一个分析口径**，需要把改动同步到
主稿 docx / 补充材料 / 独立 Tables / README，并给出终审结论。

顺序（可复用）：
① 口径定案 → ② 重跑主图 → ③ 生成补充图（+JPG）→ ④ 重嵌主稿图片 →
⑤ 同步补充材料 → ⑥ 重抽 Tables/ + 写 README → ⑦ 终审（含旧值上下文判定）

---

## 1. 重嵌主稿图片（`word/media/` 替换）

**图编号 ≠ media 编号。** 必须从关系表 + 正文出现顺序反推：

```bash
unzip -o -q ms.docx -d .            # 看 word/media/imageN.*
cat word/_rels/document.xml.rels | tr '>' '>\n' | grep -i image
```
- `word/_rels/document.xml.rels` 给出 `rId → media/imageN`；
- `document.xml` 中 `r:embed="rIdNN"` 的**出现先后 = 图注先后**（Figure 1 → Fig1）。
- 本项目实测映射：`rId11→image2.png=Fig1`、`rId12→image3.png=Fig2`、`rId13→image4.png=Fig3`。
- 用户若说"Fig2→image3.png、**非 image2**"，是在提醒你编号不对应 —— 以映射为准，不要按字面猜测。

替换方式：用 `zipfile` 重打包，**逐 entry 原样搬运，只替换 media 目标项**（不要解压后松散重压，会丢结构）。

```python
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename in MAP:                    # MAP: media 路径 -> 新图路径
            data = open(MAP[item.filename],'rb').read()
        zout.writestr(item, data)
```

**关键校验：宽高比必须与 XML `wp:extent cx/cy` 一致**（EMU，`cx/914400` = 英寸），
否则 Word 会把新图**拉伸变形**。本项目新旧比一致（1.0078 / 1.5062 / 1.1199）才可直接替换；
若不一致，必须**同时更新 `wp:extent` 与 `a:ext`** 的 cx/cy。

替换后读回验证尺寸：
```python
with zipfile.ZipFile(docx) as z, z.open('word/media/imageN.png') as f:
    print(Image.open(io.BytesIO(f.read())).size)
```

---

## 2. 补充材料（`04_Supplementary Materials.docx`）跨版本同步

**口径切换时不要删旧数值。** 旧值是 pre-specified **function-form sensitivity**，删掉会变成"隐藏分析"。
正确做法是**增量补充 + 标注**：
(a) 表格**新增匹配口径行**；(b) 表注补一句
`"… under the linear age/BMI functional form and retained as a function-form sensitivity;
under the matched log10 form …. "`。

**新增表行的安全做法**（不要用 `add_row()` 手工搬 10 列）：
```python
new_tr = copy.deepcopy(src_tr)     # 克隆一个结构完全正确的 w:tr
src_tr.addnext(new_tr)             # 紧跟其后插入
for tc, val in zip(new_tr.findall(qn('w:tc')), cells):
    set_cell(tc, val)
```
- **从下往上插入**（先插最后一层）→ 前面的行索引才不会漂移。
- `set_cell` 要**清空该单元格所有 `w:p` 里的子元素**再写一个新 `w:r/w:t`，
  并设 `t.set(qn('xml:space'), 'preserve')`（否则首尾空格被吞）。
- 表注/说明段落 patch：遍历 `doc.paragraphs` 找**唯一**锚点 → 清 runs → `add_run(全文)`。
  不要逐 run 拼，容易留下半句（本项目 §3.6 就是这样残留了自相矛盾的 `1.020`）。

---

## 3. `Tables/` 独立表格文件：必须从**当前主稿**重抽

**事故（本项目真实发生）**：v20 交付包的 `Tables/Table 2.docx`、`Table 6.docx` 仍是旧口径
（1.326 / 0.826 / 1.244）。这些文件直接复制进 v21，就会把**过期数字带进交付包**，
而主稿本身是对的 —— 审稿人对照两份文件时会发现矛盾。

**正确做法**：从**已更新的主稿**抽取，而不是沿用上一版目录：
```python
# 遍历 body：'Table N.' 标题段 -> 紧随的 w:tbl -> 其后第一个非空段落(表注)
newdoc.element.body.append(copy.deepcopy(tbl))   # 表
# 标题与表注用 add_paragraph 写入
```
抽完**必须验证**每个 `Table N.docx`：旧值残留 = `{}` 且新值命中 > 0。

---

## 4. 终审："旧值残留"要按**上下文**判定，不要一律判错

本项目终审脚本按 v20 值报 `STALE!`，但逐处查看上下文后确认**全部是有意保留**：
- 主稿 P021 / P061 / P072 都写了 `the linear age/BMI function-form sensitivity`；
- 补充材料 S3 Panel C、S5、S11、S12 的表注也显式标注了线性口径。

⇒ **审计脚本报残留 = 触发人工看上下文，不等于缺陷。**
判定标准：**该数字所在句子是否明确标注了它对应的口径**。

一份合格的终审报告应包含：文件清单（含大小）、每个 docx 的 `旧口径计数 vs 新口径计数`、
图件规格（px @300dpi）、以及**有意保留项的显式说明**。

---

## 5. 脚本 bug 与"自检误报"的归因（避免误改正确的图）

- **断言滞后**：图脚本的"保留文字"断言可能还是上一版的面板标题。本项目 `_make_figs_v21.py`
  报 15 个 `PROBLEM`，其中 11 个是 v19 旧标题的断言过期。
- **断言设计错**：4 个是把**坐标值当文本**核对 —— 匹配口径的 ΔAUC 只以**点/误差棒的位置**呈现，
  **不进 PDF 文本层**，所以 `"+0.0040" not in pdf_text` 是必然的。
- **函数签名变更未同步调用点**：`match_auc_tables()` 已返回 3 值，调用处仍写
  `MM, MAUC = match_auc_tables()` → `ValueError: too many values to unpack (expected 2)`。
  修法 `MM, _LMM, MAUC = match_auc_tables()`，并**grep 所有调用点**。
- 交付前先按**类型归因**（断言过期 / 断言设计错 / 真缺陷），**只有真缺陷才改图**。

---

## 6. 机位提示（本机）
- 一律「写 `.py` 脚本 + `python 脚本.py`」；`python -c` / heredoc 常触发审批或转义问题。
  heredoc 里的 `\\U`（Windows 路径 `\Users`）会被 Python 当 unicode 转义报
  `truncated \UXXXXXXXX escape` ⇒ 路径用 `chr(92)` 拼或直接写脚本文件。
- 长任务 background + 日志 + `EXIT=$?`。
