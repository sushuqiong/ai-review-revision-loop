# docx 表格格式取证 与 图-注一致性核查

来源：课题2 v19 投稿前（BMC Gastroenterology）实测。**每一个数字都来自实测，不是推测。**

---

## 一、三线表完整性取证（XML 层，不能只看渲染）

**核心教训**：表格由**不同批次脚本逐次追加**生成时，**后追加的表极易缺底线、缺显式字号、超页宽**。
v19 实测：Supplementary 23 个表中 **6 个缺底部封闭线、450 处 run 无显式字号、3 个表宽 17.4 cm 而可用只有 17.0 cm**；
主稿 7 表中 **Table 2 / Table 4 超宽**（Table 4 为 16.31 cm，可用仅 15.93 cm，约溢出 3.8 mm）。

### 三项必查

**① 表格宽度** = `w:tbl/w:tblGrid` 下所有 `w:gridCol/@w:w` 之和（twips）

```
可用宽 = (sections[0].page_width - left_margin - right_margin)
cm = twips / 1440 * 2.54
```

⚠️ **两个文档的基准不同，勿混用**：
- 主稿（边距 2.54 cm = 1 in）→ 可用 **15.93 cm**
- 补充材料（边距 2.0 cm）→ 可用 **17.00 cm**
- BMC 印刷整页宽 **170 mm = 6.69 in**（供参考，与 docx 页宽是两回事）

**② 末行底线**：`w:tbl/w:tr[last]/w:tc/w:tcPr/w:tcBorders/w:bottom` 的 `@w:val` 不为 `nil` / `none` / 缺省

三线表范式（全稿统一）：

| 行 | 边框 |
|----|------|
| 首行（表头）| `top(single, 12)` + `bottom(single, 6)` |
| 中间行 | 无 |
| 末行 | `bottom(single, 12)` |

⚠️ **判据是「值」不是「有没有」（v22 曾因此误判）**：`tblPr/tblBorders` **存在但每个子项 `w:val="none"`** → **合格**
（画线靠单元格级 `tcBorders`；本项目主稿 7 表即此结构，曾被误报为"7/7 异常"）。
真正不合格只有两种：`left` / `right` / `insideV` 的 `val` 不是 `nil` / `none`（= 有竖线），或单元格级边框整体缺失（= 表格无框）。

**③ 显式字号**：每个 `w:r` 的 `w:rPr/w:sz` 必须存在（缺则继承默认，跨表显示不一致）
- 主稿统一 **9.0 pt**（`w:sz="18"`）
- 补充材料 **8.0–8.5 pt**（`w:sz="16"/"17"`），列数多的宽表可 7.5 pt
- 两文档字号不同是**合理的**（列数不同），但**各自内部必须统一**

**④ 另查**：
- `w:tblPr/w:tblStyle` 是否为 Normal Table（无内置边框 → 必须靠单元格级 booktabs 边框，否则表格完全无框）
- 有无 `w:shd`（**BMC 明禁表格着色/底纹**）
- 单元格级 `w:tcBorders` 是否被写成**显式全 `none`**（与"无 tblBorders 元素"外观可能一致，但会阻断样式继承）

### 修法（只改宽度，绝不动内容）

按比例缩放 `gridCol` 与每个 `tc` 的 `w:tcW`，总和收到基准值（主稿 9028 twips、补充 9636 twips）：

```python
k = TARGET / sum(old); new = [max(700, round(x*k)) for x in old]
new[-1] += TARGET - sum(new)          # 误差补到最后一列
```

补底线/字号后**必须复验**：`grep -c` 关键值 + 抽表逐格比对 `cell.text` 列表改前后一致。

**可直接运行**：`scripts/docx_table_format_audit.py`（体检，只读）/ `scripts/docx_table_format_fix.py`（补齐，写回前自动备份）

---

## 二、图内文字 vs 正文图注 一致性

**方法**：
1. 图内文本层 → `pypdf.PdfReader(fig.pdf).pages[0].extract_text()`
2. 图注 → 主稿里 `Figure N.` 开头的段；补充图注在 Supplementary 里 `Figure SN.` **标题段 + 紧随说明段**（说明段常是独立段落，只读标题会严重低估图注长度）
3. 把图注里的数字 token 逐个在图内文本中查找

**判定要点（防误报）**：
- **图注级信息本就不上图**，未命中属正常：bootstrap B=1,000、判别样本量（2,846 / 2,056 / 5,724 与 296 / 232 / 438 病例数）、CI 估计方法、自由度 —— 这些是"图注交代"而非"图内显示"
- **`dashed` / `dotted` / `solid` 指的是边框或线型，不是图内文字** → 图内查不到**不算矛盾**；正确做法是核对图内**对应块/行是否存在且数值一致**（v19：图注 `dashed block ... n = 5,290; 353 dx` ↔ 图内 `HAJ9/HAJ12 only · n = 5,290 (353 dx)` 逐字吻合）
- 提交前**必须逐项核对**：样本量 n、病例数、OR/CI 锚点、每 SD 单位、原点参考、面板编号 (A/B)、层名、模型名 (M1–M4 / base A/B)、层内注释

**可直接运行**：`scripts/fig_legend_consistency_check.py`

---

## 三、图内"白字白底不可见"缺陷（隐蔽，全图 OCR 读不出）

**用户症状描述**："某处数字显示不全/看不清，是**白色的几百的数字**"。

**根因类型**：matplotlib 把标签**硬编码为 `color="white"`**（常见于"给第 N 个分类用白字"的分支，
例如 `color="white" if ci == 3 else "#111111"`），而该标签位置**不在彩色填充区内**（落在白底上）
→ 白字白底 = 不可见，只有**压在彩色段上的那一小条露出残影** → 看起来像"残缺的白色数字"。

**为什么全图 OCR 查不出**：图中**别处有同名同值的深色标签**（例如另一面板也有 `8.9% (n=223)`），
OCR 命中会让人误判"该标签正常"。

**诊断法（决定性，一次定位）**：用 PDF 文本层的**精确坐标**换算到 PNG 像素，采样该标签 bbox 的**最深色像素**：

```
png_x = pdf_x * (png_W / pdf_W_pt)
png_y = (pdf_H_pt - pdf_y) * (png_H / pdf_H_pt)
```

| 采样到的最深色 | 结论 |
|---------------|------|
| ≈ 文字色（如 RGB(17,17,17)）| 文字正常可见 |
| = 柱体/填充色（如 RGB(200,16,46)）| **该处没有深色文字** → 白字或浅字问题 |

**修法二选一**：
- 改为深色（`#111111`）+ 移到填充区**外上方**（`va="bottom"`）+ 必要时**单行化** + 抬高 `ylim` 容纳
- 或按用户偏好**删掉图内标签，改在图注与正文用文字交代**（更简洁、避免突兀；v19 最终采用此方案）

---

## 四、图内去除标题/图例（用户要求图例单独成文件时）

- 只删**标题 / 图例键 / 脚注块**；**数据元素必须逐项保留** —— 计数链、点位、误差棒、面板、轴标签、面板字母、层内小注
- 用**纵向裁切**保宽度恒定：宽度保持原值，只减高度 → 可做**几何不变性证明**
  （v19：重叠区像素 MAE=0.0000、各子带最佳平移同为 dy=246 px、8 个面板英寸坐标偏差 0.000000）
- 验证三件套：`assert_removed`（已删文字残留 0）+ `assert_kept`（保留文字全在）+ 四边留白 >0 + PDF `Type3=0`
- ⚠️ **连通域审计必须先排除"近乎全宽的墨迹行"**（基线/轴脊，覆盖率 >85% 的行）：
  恢复底部基线后，柱子坐落在基线上 → 全图拓扑连通成 1 个 CC（v19 实测 1878 px）→ 会误报"标签拥挤"。
  排除后同一图的最大文字块从 1878 px 降为 288 px（真实值）。

**重嵌入 docx 时**：`word/media/imageN.png` 换字节后，必须**同步改写 `wp:extent` 与 `a:ext` 的 `cy`**
（cx 恒 5400000 EMU），使 `cy/cx == png_h/png_w`；改后回读 **md5 校验**。若新图与原图宽高比相同则 cy 不变。

---

## 五、补充材料装配顺序（用户硬要求：全部表在前、全部图在后）

v22 用户原话："**我要补充表呈现完再呈现图片。**"

**目标顺序**：
```
文件标题 → Supplementary Data（总说明）→ Abbreviations
→ 【Supplementary Tables 分节标题】→ Table S1 … Table SN（编号连续）
→ 【Supplementary Figures 分节标题】→ Figure S1 … Figure SM（图紧跟各自图注）
```

**最高频的错**：用 `doc.add_paragraph()` / `doc.add_table()` **追加到文档末尾**生成新补充表
→ 新表落到**补充图之后**（v22 实测：新增的 S14–S16 全被追加到 Figure S1–S3 后面）。

**正确做法**：先定位图区分节标题元素（文本为 `"Supplementary Figures"` 的段落），
逐块 `target.addprevious(new_el)` 插入其**前**；若要搬动已有块，`body.remove(el)` 后重新 `addprevious`。
（本项目搬动 S14–S16 整块 = 16 个 body children，含标题/表/表注，一次插入到位。）

**装配后必查三项**：
1. `"Supplementary Tables"` 分节标题是否在 **Table S1 之前**（v22 曾错落在最后一张表之后）
2. 首页总说明的编号范围是否同步（"contains Tables S1–**S13**" 在加了 S14–S16 后必须改成 S1–S16）
3. 有无冗余顶层标题（v22：`"Supplementary Material"` 与 `"Supplementary Data"` 重复 → 删前者）

**可复用校验**：遍历 `doc.element.body.iterchildren()`，依次打印所有 `Table S*` / `Figure S*` 标题、
各分节标题、以及**真含图**的段落（判法见 §七），肉眼确认顺序与归属。

---

## 六、程序化「新增表格」的样式陷阱：Table Grid 不是三线表

**症状**：新写的表带完整网格线，与全文其余三线表不一致（用户会直接指出"表格不全是三线表"）。

**根因**：`doc.add_table(...)` 后写 `t.style = "Table Grid"`（`tblStyle/@w:val` 常落到 `35`）
→ Word 内置网格样式，**有竖线与行间线**。

**正确做法**（照抄全稿合格表的实现，样式 id = `12`）：
- `tblPr/tblStyle/@w:val = "12"`
- **表级 `tblBorders` 各项 `val="none"`**（不用表级边框）
- 画线全靠**单元格级** `tcPr/tcBorders`：首行 `top(12) + bottom(6)`；中间行全 `nil`；
  末行额外 `bottom(12)`；**每个单元格 `left(nil) + right(nil)`**（去竖线）

**批量修复既有表**：对每张异常表 ①重设 `tblStyle=12` ②移除表级 `tblBorders`
③**重写**每个 `tc` 的 `tcBorders`（必须先删旧元素再 append，只 append 会残留旧竖线）。
v22 实测一次修好 9 张表（5 张含表级边框 + 4 张新表误用 Table Grid），修后 **27/27 合规**。

**修完的验收**：逐表检查 `tblStyle==12` 且无表级实线边框 且无单元格级 `left/right` 实线。

---

## 七、「文档里有没有图」要按 `a:blip` 判，别用字符串匹配

**踩坑**：`'graphic' in paragraph.xml` 判图 → **大量假阳性**。
原因：`w:graphicFrame` 等**命名空间声明**本身就含 "graphic"；正文文本也可能偶然含该子串。
v22 因此误报"Table S1 前、Table S8 中间各有一张图"，实际全文只有 3 张图（Figure S1–S3）。

**正确**：`para.findall('.//' + qn('a:blip'))` → 取 `r:embed` → 到 `word/_rels/document.xml.rels`
反查 `word/media/imageN.png`；再用 **md5 与交付目录的图源比对**，确认内嵌的到底是哪一版。

**同类假阳性的通用规则**：正则搜术语/特征串时加词边界或白名单。
v22 用 `prove\w*` 搜"过强表述"命中了 `improves`（误报）；
搜"时间趋势"时 `temporal trend` 的唯一命中是**否定用法**
（"rather than as evidence of a temporal trend"）→ 必须读上下文，不能只看计数。

---

## 八、术语「疑似笔误」：先查数据构建代码，再决定改还是留

**实例（v22）**：外部 AI 指出图注 `HAJ0 age-branch outcome` 是笔误，建议改为 HAJ9/HAJ16。
- 若不查证就全局替换 → 会把**正确的技术描述改错**

核查 `v13_1_n3_outcome_rebuild.R` 后确认：**HAJ0 是 NHANES III 的真实变量**
（Section J 年龄分支指示：`HAJ0=1` → 17–74 y 用 HAJ9/HAJ12；`HAJ0=2` → ≥75 y 用 HAJ16/HAJ17）。

**分情形判定**：

| 用法 | 判定 |
|---|---|
| 把 HAJ0 当 **outcome**（"HAJ0 age-branch outcome"）| ❌ 错 → 改 "age-branched HAJ9/HAJ16 outcome" |
| 把 HAJ0 当**分支键**（"keyed on the HAJ0 age branch"）| ✅ 准确 → **保留，不要动** |

**规则**：任何"变量名可能有误"的外部意见，先 `grep` 数据构建 / R 脚本确认该变量是否真实存在、
扮演什么角色（结局变量？分支键？协变量？），再决定改还是留。
改动前后都对 **主稿 + 补充材料 + 图内文本**三处做残留/命中计数。
