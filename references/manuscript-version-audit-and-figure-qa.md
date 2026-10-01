# 版本对版本低级错误扫描 · 手稿 docx 重建链 · 无视觉模型的图件 QA

三类可复用技法。触发场景：要判断"这一版是否比上一版更好"、"重建交付 docx/投稿包"、
"新增一张图但我没有视觉模型可用"。

---

## A. 版本对版本低级错误扫描（回答"vN 比 vN-1 更好吗？"）

不要靠读一遍下结论。**程序化全文扫描 + PDF 页级复核**，把结果排成一张对照表，
一列一个版本。这是本类项目里唯一能站住脚的"谁更好"证据。

### 扫描电池（正则逐项计数，命中次数直接进表）

```python
BATTERY = {
  "unclosed **":            lambda t: t.count("**"),
  "orphan ** at line end":  lambda t: len(re.findall(r"\*\*\s*(?:\n|$)", t)),
  "Table N.** pattern":     lambda t: len(re.findall(r"Table \d\.\*\*", t)),
  "nonexistent var names":  lambda t: t.count("wgt11"),          # 换成该项目的可疑变量名
  "false unavailability":   lambda t: t.count("weights were not available")
                                + t.count("could not be rebuilt"),
  "mislabeled table rows":  lambda t: t.count("Survey-weighted unadjusted"),
  "double spaces":          lambda t: len(re.findall(r"[A-Za-z]  +[A-Za-z]", t)),
  "space before punctuation": lambda t: len(re.findall(r"\s+[.,]", t)),
  "unbalanced parens":      lambda t: t.count("(") - t.count(")"),
  "unbalanced brackets":    lambda t: t.count("[") - t.count("]"),
  "'NA (' artifact":        lambda t: t.count("NA ("),
  "duplicated word":        lambda t: len(re.findall(r"\b(\w+)\s+\1\b", t, flags=re.I)),
  "placeholder brackets":   lambda t: len(re.findall(r"\[(?:Author|Affiliation|Institution|email|Corresponding|funding)", t, flags=re.I)),
  "NaN/None/undefined":     lambda t: len(re.findall(r"\b(?:NaN|None|undefined)\b", t)),
  "internal version tags":  lambda t: len(re.findall(r"\bv1[0-9]\b", t)),
}
```
文本来源 = docx 正文段落 **+ 表格单元格**（`[c.text for t in d.tables for r in t.rows for c in r.cells]`）。
漏掉表格就会漏掉整类错误（本项目 3 处误标就在表里）。再补 docx 级计数（表数/图数/词数）与
LibreOffice 转 PDF 后的页数。

### 已知假阳性（不要当问题报）
- `duplicated word`：表格数字列相邻重复值（`0 / 0`、`2,157 / 0`）会被 `\b(\w+)\s+\1\b` 命中。
- `"nan"`：出现在 `u**nan**swered` 这类普通词里。
- `"Supplementary Table S"` 顺序检测：正文交叉引用（Table S19/S7/S5）会先于补充材料区出现，
  造成"顺序不对"的假象。**先把空白压平**（`re.sub(r"\s+", " ", txt)`）再做顺序与完整性判断，
  否则换行会把 `Supplementary\nTable S1` 拆断而漏检。

### 通读结果时要找的三类真问题（按危险度排序）
1. **可被审稿人直接证伪的陈述** —— 优先级最高。例："X 不可用"（其实数据里一直有）、
   "无法重建"（其实重建成功）。这类"看似谦逊的局限声明"是假话，比数据不全危险得多。
2. **引用了不存在的变量名** —— 说明数字不是算出来的。例：`wgt11`（真实名为 `r1wtresp`）。
3. **正文残留内部工作版本号** —— `Additional pre-specified analyses (v16).`、
   `(v17_*.R, v10-v16 analysis scripts)`。投稿稿出现 `(vNN)` 是低级错误；版本越迭代越容易累积。
   收尾正则：`re.subn(r"\s*\(v1[0-9][^)]*\)", "", s)`，然后断言剩 0 个 `\bv1[0-9]\b`。

### 本类项目的一次真实结果（worked example）
| 检查项 | v16 | v17 | v18(修后) |
|---|---|---|---|
| 页数 / 词数 | 21 / 7,233 | 22 / 7,993 | 24 / 9,023 |
| 未闭合 `**` | 1 | 1 | 0 |
| 不存在的变量名 | 0 | 1 | 0 |
| "不可用/无法重建"假陈述 | 0 | 3 | 0 |
| 表行误标 | 3 | 3 | 1（剩下的是另一库的表，正确） |
| 内部版本号残留 | 2 | 5 | 0 |
| 括号不配平 | 0 | 0 | 0 |

**典型形态**：新版内容更全（页数/词数/补充表增加）却**引入了上一版没有的事实错误**，
且上一版的老毛病一个没修。所以"更好"必须分维度回答：**结构完整度** vs **事实准确性**，
后者对投稿更要命。汇报时直接分维度给判定，不要给单一结论。

### 顺带查"假回应表"的出处
若发现某张补充表数字不可复现，去 `grep -l` 生成它的编辑脚本——数常见于脚本里
**硬编码文本块**（而不是计算产物）。把该脚本路径作为证据写进报告，比只报"数字不对"有力得多。

---

## B. 手稿 docx 重建链（md → docx 双版本 + 投稿包）

可复现链（本类项目已验证）：

1. **md → docx**：`pandoc <md> -o <docx> --standalone`，
   图片用绝对路径写在 `![](C:/.../FigN.png)`，pandoc 会自动嵌入。
2. **三线表**：python-docx 后处理——`tblBorders` 只留 `top`/`bottom`（`single`, sz 8），
   `left/right/insideH/insideV` 设 `val="none"`；再给**首行**每个单元格加 `tcBorders/bottom`
   作为表头细线。表格文字降到 8.5pt。
3. **`Supplementary material` 标题设 `page_break_before = True`**，保证补充材料另起页。
4. **匿名版**：对 md 做替换后再走同一链路（姓名/单位/邮箱/基金号/GitHub 账号）。
   双盲更严的做法是**连基金占位符也去掉**（只留"信息已移除"的说明），否则匿名版仍带着
   基金线索位。
5. **封面信/清单复用规则**：用户已定稿过的封面信**只改必须项**（版本号 + 结论段的数字），
   其余原样。若 `.md` 源被清理过，**从 docx 用 python-docx 反抽正文**再改，不要重写。

6. **\"装进期刊模板\" ≠ 注入样式**。期刊 logo 在 `word/header*.xml` + `word/media/*`，**不在正文**；
   只把模板的 `styles.xml` 注进来的结果是\"同款样式、首页却没有 logo\"——用户一眼就能看出来
   （本项目被连续纠正两次）。正确做法是在 **OOXML 包层**以模板为底合并：清空模板 body 占位内容
   **但保留 `sectPr`**（它绑定页眉引用），注入本稿 body，重映射 `r:embed` 的 rId，
   `[Content_Types].xml` 补图片扩展名。
   **收尾四条必查**：模板 logo 还在 `word/media/`；`sectPr` 的 `headerReference/@r:id` 仍指向
   `header*.xml`；body 图指向**新** rId 且新 rId 在 rels 里；段/表/单元格文本逐字一致。
   完整配方、技术检查真/假报鉴别、表底线/字号/宽度三要素体检见 skill
   `cohort-methods-sensitivity-kit` 的 `references/journal-submission-packaging.md`。

### 卫生检查（每次重建后跑）
- 匿名版泄露扫描：`["姓名","邮箱","单位","GitHub账号","基金号","ORCID","163.com"]` 逐项断言 0 命中。
- 图注编号齐全 1..N；主表编号 1..M；补充表编号 1..S 且**升序无缺**（压平空白后再判）。
- 残留 `**`：pandoc 对**嵌套 markdown** 处理不干净。典型写法
  `**Figure 5. 标题。** 说明句。*Left: ...*` 会渲染出孤立星号。
  **修法：把图注里嵌套的强调全部拉平为纯文本**，一句到底。
- zip 内文件的**新鲜度**：先重建 docx、再刷源 md 副本、**最后**打 zip。顺序颠倒会把旧副本打进包。

---

## C. 无视觉模型可用时的图件 QA 三件套

当 vision 端点不可用时，**不要直接声明"无法自检美观度"**——用下面三招做客观检测，
本项目靠它抓出一个真 bug（森林图右侧两列数字叠印）。

1. **Tesseract OCR 读全部文字**（`--psm 6`）：
   判据是"读出来是否连贯"。**数字互相叠印会表现为乱码**，例如
   `0.80 (0.68aRE4)82` 其实是 `0.80 (0.68-0.94)` 与 `822` 压在同一个位置。
   这是 OCR 最容易抓、肉眼在缩略图上最容易漏的一类缺陷。
2. **像素边界检测**（PIL + numpy）：
   `nonwhite = (a.sum(axis=2) < 720)`，检查四边 2px 内是否有墨迹 → 判断是否裁切；
   再看 ink bbox 到画布边缘的**留白像素数**（右侧留白 <50px 就偏紧）。
3. **PyMuPDF 复核版面**：docx→PDF 后确认每张图与其图注**同页**、补充材料标题位置正确。

### C-2. 用户说"图里有数字看不清/显示不全"时的三种真因（本项目各踩一次）

不要猜是哪一处。**先分类**，每类有决定性判据。

**① 白字白底 → 完全不可见（最难发现）**
症状：用户描述为"**几个白色的数字**、显示不全"。
根因：脚本里按条件给标签设了 `color="white"`（本项目 `color="white" if ci == 3 else "#111111"`），
而该标签落在**白底**上——承载它的彩色段只有 5.5 pt 高，装不下两行 8.5 pt 白字，
只有压在彩段上的那一小条露出残影。

**决定性判据**：从 PDF 文本层取**精确坐标**，回 PNG 采样该处的**最深色**：
```python
reader.pages[0].extract_text(visitor_text=lambda t, cm, tm, fd, fs: rec(t, tm))  # 取 (x, y)
px = x * (PNG_W / PDF_W_PT);  py = (PDF_H_PT - y) * (PNG_H / PDF_H_PT)
darkest = rgb[py-14:py+10, px-4:px+120].reshape(-1, 3).min(axis=0)
#   深色文字 -> 近 (17,17,17)      |     无可见文字 -> 只剩柱体/线段色
```
该处最深色 ≈ 填充色 ⇒ **那里没有可见文字**。这是唯一能证明"字不可见"的手法；
OCR 只会给你乱码，像素直方图只会给你"背景占多数"。

**② OCR 结果**不能**定位问题面板**
同一张图里存在**重复标签**时（本项目 Panel A 与 Panel B 都有 `8.9% (n=223)`），
OCR 读到的命中**无法说明是哪个面板**——我据此连续两轮改错了面板，
还把另一个面板改难看，被用户直接点破。

**规则**：出现重复标签 → 必须用 **PDF 坐标**，或**逐面板裁图后单独 OCR**。
拿 OCR 的整图结果去定位，等于没定位。

**③ 拥挤/重叠 → 连通域最大连续墨迹宽度**
症状：n 值"显示不全"。本项目实测 Panel B 的**全部标签挤成一个 1914 px 的连续墨迹块**。
```python
runs, cur = [], 0
for c in ink_cols: cur = cur + 1 if c else 0; runs.append(cur)
max_run = max(runs)      # 阈值经验值 ~350 px
```
修完验收：`max_run` **1914 → 169 px**，且 OCR 能逐条读出全部编号。
**假阳性警告**：底部**基线/轴脊是贯穿全宽的横线**，会伪装成"最大连续墨迹"。
审计前先剔除"占宽度 >85% 的行"，否则永远报 FAIL。同理，**轴标题行**（如
`Per-SD OR (95% CI, M3 (log scale)`）本来就是连续文本，别当成"标签重叠"——
要测的是**刻度标签行**，不是轴标题行。

修完图尺寸会变 → 回填 docx 时 `wp:extent/@cy` 与 `a:ext/@cy` 必须按新宽高比重算（`cx` 一般不变），
收尾 md5 回读比对。


**不要让两列数字共享同一个右对齐边界**。把"数值列"做成**独立面板**再用
`patchwork` 横向拼接：`pf | pm | pr`（森林 | HR(95%CI) | Deaths/n），
各面板 x 轴独立、`axis.text = element_blank()`，`plot_layout(widths = ...)`。
一旦共用一个边界，窄列会向左伸进宽列，必然叠印。

### 图数据必须重算，不要读中间产物
出图脚本里**重新拟合**再画（本项目就发现中间 RDS 的周期数据已被变量复用污染）。
图上每个点都要能追到一次真实拟合。
