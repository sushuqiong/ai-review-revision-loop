# 期刊图件版面铁律 + OCR 机器质检

> 触发：用户说"**你画图表总是有问题**""注意 OCR 检查"；或任何要交稿的多面板图。
> 本用户对版面零容忍（字号、重叠、越界、裁切、图注与内容不符、旧版残留）。**改完图必须机器质检，不许目测交付。**

## 一、根因：版宽超标 → 字号被"缩"到 7pt 以下
期刊把图缩排到栏宽后再看字号。若出图物理宽度 > 17 cm，10 pt 字会被缩到 ~6.5 pt。
**强制：所有图 `width <= 6.7 in (17.0 cm)`，300 dpi → 像素宽 ≤ 2010 px。**
- R：`ggsave(f, g, width=6.7, height=..., dpi=300)`（宽永远写 6.7，不要 8~10）
- graphviz：`dot -Tpng -Gdpi=300 -Gsize=6.7,9.5! ...`（不加 `-Gsize` 会长到 40 cm 宽）

字号下限（按印刷尺寸，不看像素）：
| 元素 | 下限 |
|---|---|
| 坐标轴文字 | ≥ 9 pt（`theme(axis.text=element_text(size=9))`，ggplot 是 pt） |
| 图内数值/注释 | ≥ 8 pt（`geom_text(size=)` 单位是 **mm**：3.0 mm ≈ 8.5 pt；2.7 mm 是下限） |
| 图例 | ≥ 8 pt |
| 标题 | ≥ 10 pt 加粗 |
| 单图高度 | ≤ 11 in（否则整页放不下） |

## 二、内容一致性（比版式更常被抓）
1. **数字只能来自冻结结果表**（`results/*.csv`）；图注数字必须与正文、Table 1 一致。
2. **标签命名必须与结果表键一致**：绘图前统一 `lab()` 映射；映射后若有重复水平，`factor()` 会报错或颜色/数据错位（本会话曾因绘图用 `EPH`、结果表用 `EPH_RECEPTORS` 导致整行灰掉）。
3. **不可估计的格子显式标注 `n.e.`**，不留空白。
4. **面板不重复**：`fig2a_*` 只含 A 面板，别把"旧 A/B 图 + 新 B 图"叠在一起。
5. **图注逐项对照面板**（曾出现图注写"含扩增面板"而图里只有突变）。
6. 单细胞/分类图必须标出**统计单位的数量**（患者数/配对数），并在图注里说明配对 vs 非配对。

## 三、OCR 机器质检（本用户点名要求）
用 tesseract 词级框坐标做几何检查（`scripts/ocr_figure_qa.py`）：
```bash
python scripts/ocr_figure_qa.py   # 改脚本顶部 FIGDIR/EXPECT 即可
```
判读标准（**只看几何缺陷，不用它判字号**）：
- ✅ `clipping == 0`（无文字贴边/被裁）
- ✅ 真实文字重叠 == 0
- ✅ 关键标签可读（情境名、模块名、数字、`n.e.`、患者数/配对数）
- ⚠️ `below_7pt` 计数**不可信**：tesseract 只量小写 x 高度，10 pt 字也常被判成 6.5 pt；字号以第一节的代码设定为准
- ⚠️ 高度 < 10 px 的 `-` `+` `5` `=` `|` `_` 全是**网格线/误差棒端/刻度线**被误读，属假阳性；长标签会被 `|` 分隔符切成碎片（"缺词"多半是假阴性）

### tesseract 调用坑（否则整批图返回 0 词）
```python
env = dict(os.environ, TESSDATA_PREFIX=r"C:\Program Files\Tesseract-OCR\tessdata")
subprocess.run([r"C:\Program Files\Tesseract-OCR\tesseract.exe", path, "stdout", "--psm", "11", "tsv"],
               capture_output=True, env=env)
```
- 不传 `TESSDATA_PREFIX` → `read_params_file: Can't open tsv`，全部图 0 词（看似"图没字"，实为调用失败）
- 路径含中文时：先把图**复制到 ASCII 临时目录**（`C:\Users\<u>\ocr_tmp`）再 OCR
- 长标签换行/分隔符会让 OCR 碎片化；核验"缺词"时先在同一张图上模糊匹配前 3 个字母

## 四、迭代闭环（每改一次图都跑）
```
1) 从冻结表生成图（R 脚本，`ggsave` 宽=6.7）
2) 导出投稿 TIFF：PIL `save(..., format="TIFF", compression="tiff_lzw", dpi=(300,300))`，宽 >2008 px 时先缩到 2008
   并留 `figure_specs.csv`（file, px_w, px_h, cm_w, cm_h, MB, dpi）——cm_w 必须 ≤17.0
3) OCR 质检 → 修 → 再质检（记录到 04_评审记录与报告/ocr_figure_qa.csv）
4) 重建 docx/pdf（图换版后 docx 必须重建）与上传 ZIP
```
投稿命名：`Figure1.tif … Figure6.tif`、`FigureS1.tif/S2.tif`（不要中文名、不要 PNG+PDF 混传）。

## 五、已知易犯清单（本会话真实发生）
- [ ] 图宽 8–10 in（会被缩到 6.5 pt）→ 一律 6.7 in
- [ ] graphviz 未设 `-Gsize`，出图 43.9 cm 宽
- [ ] 28 行条形图高度算成 90 cm → 行高按 0.22–0.25 in/行 + 2.4 in 常数
- [ ] 图内数值 `size=2.5`（≈7 pt 边缘）→ 提到 3.2–3.4 mm
- [ ] 旋转 35° 的 x 轴标签 → 10 个情境可水平放置（0°）更易读也更好 OCR
- [ ] 复用旧版 Supp 图（v9 的图混进 v11 包）→ 全部从当前冻结表重生成
- [ ] 图注标题过长被裁 → 拆两行（title + subtitle）或加 `plot.margin`

## 六、静默错列 / 静默失标签（v11 真实事故，最危险的一类）
症状：图看起来"正常"，但某段文字**静默变成空值**——因为绘图代码引用了结果表里**不存在的列**。
```r
# sc_v11_patient_paired.csv 的列名是 context，不是 disease
sig$ylab <- paste0(lab(sig$module), " / ", sig$cell_type, " (", sig$disease, ")")  # 静默输出 "()"
```
R 不会报错（`NULL` 参与 `paste0()` 得到空串），所以**必须靠渲染后断言**发现：
```bash
# 1) psm 6 整行读一遍，人眼扫是否有 "()" "NA" "NULL" 之类的空槽
tesseract fig.png stdout --psm 6 | grep -nE '\(\)|NA|NULL|^ +[A-Za-z]+ /.* /$'
# 2) 在质检脚本里对每张图断言"期望 token 必须出现"（情境名、n.e.、配对数、数字），缺一即 FAIL
```
**教训**：凡是把数据列拼进标签（`paste0(..., df$col, ...)`），渲染后必须断言该 token 出现在 OCR 文本里；
只做"几何检查（裁切/重叠）"而不做"token 存在性检查"，这类 bug 会一路带到投稿。

### 重叠判定的正确量法（避免自己骗自己）
- 只对 **高度 ≥29 px 且宽 ≥25 px 且含 ≥3 个字母数字字符** 的框两两算 IoU（>`0.3` 记一次重叠）
- OCR 垃圾框（`_`、`e`、`@`、`Ee`、高度 4–8 px 的 `-`/`5`/`+`/`=`/`|`）全部排除——否则每张热图都会"报 5–18 处重叠"，把真问题淹没
- 稳健性标记（星号/菱形 glyph）画在坐标轴文字与首个 tile 之间会与标签框交叠：**改用黑色格子描边**（`geom_tile(fill=NA, colour="black", linewidth=1.1)`）并在图注写明"black-bordered tiles = robust"，几何冲突与"看不清哪个是稳健"一并解决
- 通过标准：`clipping == 0` 且 `真实重叠 == 0` 且 `期望 token 缺失 == 0`；三条全绿才允许重建 docx/TIFF/ZIP

## 七、多面板 title 挤撞 / patchwork 版面（本会话真实发生，OCR 才能看出来）
2 面板并排（各约 8.5 cm 宽）时，**面板标题会在中缝撞在一起**，OCR 把两个标题连成一串乱码——
这是最容易漏判的一类缺陷，因为它只在 OCR 里显现，肉眼看图常以为是"正常的小字"。
OCR 症状：`A Hub gene expression, GSE83148 (122 CHB vs 6 nonhdiffect sizes (independent of group size)`
（两个标题被无缝拼接）、或主标题在右缘被截：`... external validation «`、`... STRING confiden`。
对策（三条同时做）：
1. `plot_annotation(title = )` 主标题**手动换行**（`"...\nimbalance in ..."`），别指望自动折行；
2. 面板标题缩短到 ≤ 8 个词，必要时用 `+ theme(plot.title = element_text(size = 8.2))` 单独压字号，
   不要动 `base_size`（会连带压小轴文字）；
3. 质检时**逐面板裁切**再 OCR（按 3×3 或 2×2 网格裁，放大 1.6×），比整页 OCR 更容易定位撞车位置。

## 八、出图代码的静默/报错坑（R + ggplot，本会话真实踩到）
| 症状 | 根因 | 修法 |
|---|---|---|
| `check_required_aesthetics` 报缺 x 美学 | `geom_text(data=, aes(y=Inf, label=..), inherit.aes=FALSE)` —— 关掉继承后 **x 也必须显式给**（=Inf 也不行） | `aes(x = gene, y = Inf, label = lab)` |
| `\uxxxx sequences not supported inside backticks` | R 源码里在反引号/`scale_*_manual` 的取值里写 `"\u2265"` 之类转义 | 图内一律用 ASCII：`">=8.0"`、`"LSM >=12"`、`"beta"`；Unicode 只放在**文本**（图注/docx）里 |
| `第二个参数必需为列表` / `不能强制将"list"对象强制为"double"` | `jsonlite::fromJSON` 对"数组的数组"返回 **matrix**、对"字典"返回 **list**：`do.call(rbind, mat)` 与 `as.numeric(dict[key])` 都会炸 | `unlist()` 度数/字典；边表 `if (is.matrix(e)) as.data.frame(e) else as.data.frame(do.call(rbind, lapply(e, unlist)))` |
| `select()` 找不到 data.frame 的方法 | 加载 `*..db` 注释包后，`AnnotationDbi::select` 这个 **S4 泛型**掩盖了 `dplyr::select` | 显式写 `dplyr::select()` |
| `geom_boxplot(size=)` 弃用警告 | ggplot2 ≥3.4 用 `linewidth` | 改 `linewidth=`，`size=` 只留给 `geom_text`/`geom_point` |

**规律**：这些坑都不会让图"难看"，只会让图**报错或静默错位**。所以只要脚本改动过绘图基因/网络布局，
就必须重跑一次"生成 → OCR → 断言 token"闭环，不能只看文件是否生成成功。
