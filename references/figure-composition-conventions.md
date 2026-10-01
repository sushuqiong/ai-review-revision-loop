# 补充图/多面板图的构图规范（本用户，多轮纠偏后定稿）

用户对图的要求很具体，且**会逐张挑**："标签位置不对"、"两组颜色应该不同吧"、"统计值和 p 值需要显示、注意不要重叠、显示要完全"。
下面每条都是被用户明确确立或否掉的。

---

## 1. 子面板字母：放在**绘图区之外**，位置/字体以作者**原图**为准

用户原话："ABCD 都要移动到图片的右上/左上方，**不是放在图片里面**，参考我的原图"。

- ❌ patchwork 默认 tag（`plot_annotation(tag_levels="A")`）会把字母画在**面板内部**左上角，压住数据/图例 → 用户不接受。
- ✅ 先**量作者原图**，照抄。本次量出作者的约定（Figure 4/5/6/7 一致）：

```python
for s in [sp for b in page.get_text("dict")["blocks"] for l in b.get("lines", []) for sp in l["spans"]]:
    if re.fullmatch(r"[A-J]", s["text"].strip()):
        print(s["text"], s["bbox"], s["size"], s["font"], "x=%.1f%%" % (100*s["bbox"][0]/page.rect.width))
# → ArialMT 24pt（**不加粗**）、颜色 #231815（不是纯黑）、
#   左列字母 x≈2.4%、右列 x≈49–53%，y 在每个面板行的最顶端 → **左上、绘图区之外**
```

- 生成图里怎么放在外面（确定性、可核验）：

```r
tag <- function(lab) list(
  labs(title = lab),
  theme(plot.title = element_text(hjust = 0, size = 13, colour = "#231815",
                                  family = "sans", face = "plain"),
        plot.title.position = "plot"))          # ← 关键：相对**整个子图**（含图例带）对齐
# hjust = 0 → 左上（与作者原图一致）；hjust = 1 → 右上
```

- 验证（读矢量文字层，不要靠眼睛/OCR）：

```python
# 字母 x 是否贴左边缘（≈2.4%）、y 是否在行顶；与"下方最近内容"的间隙是否 >0（不重叠）
gap = min(t[2] for t in spans if 同列 and 非字母 and t[2] > letter_y) - letter_bbox_y1
```

### 1.1 用户口述方位与参考件冲突时

本次用户先说"右上方"，但其原图是左上。处理：**按用户明确说的做，同时在汇报里量出原图的实际情况并请他确认**。用户回："我是想让你把它们的标签改到每个子图的左上方外侧，**刚才打错字了**"。
→ 教训：方位/风格类口述与其参考件冲突时，**量参考件 + 明确回问**，不要自己猜，也不要默默照做。

---

## 2. 图上**不写说明文字**

用户原话："你把图片说明的文字放在图片上方和下方干嘛，不是只在修改后的 figure legends 中说明就行了吗？**我原来的其它图片，都不用在图中说明这些文字的**"。

- 删掉：图顶的长标题、副标题（如 "FDR-adjusted: \*\*\*FDR<0.001 …"）、图下的整段 caption。
- 保留：坐标轴标签、图例、facet strip、以及**与原图同风格的短面板标题**（作者原图的面板本身带短标题）。
- 所有解释性内容进 Figure legends；星号/显著性口径也在图注里定义。

---

## 3. 图上**必须显示统计值与 P 值**

用户原话："图 BCD 的统计值和 p 值是否需要显示、但你都没显示，要显示出来的话，**注意不要重叠，并注意显示要完全**"。

### 3.1 先做空间算术，再选版式（本次的实战教训）

半宽面板（17cm 图 → 每格约 210pt）**放不下** forest 图 + 两列完整文本：

| 内容 | 需要宽度 |
|---|---|
| `-0.195 (-0.275, -0.114)` 23 字符 @6.7pt | ≈ 76pt |
| `< 0.001` 7 字符 | ≈ 23pt |
| forest 图本体 | ≈ 100–120pt |
| 合计 | ≈ 200–220pt → **正好卡死** |

**第一版就是被这个算错害的**：把 95% CI 也塞进右侧文本列，结果文本在面板右缘被**截断成 `-0.133 (-0.170, -0.09`** —— 正是用户警告的"显示不完全"。

**定稿方案**：只放两列紧凑值。

```r
fD$txt  <- sprintf("%.3f", fD$beta)     # β
fD$ptxt <- fmtp(fD$p)                   # P（<0.001 或 %.3f）
rng <- diff(range(c(fD$lo, fD$hi)))
x1  <- max(fD$hi) + 0.10*rng            # β 列
x2  <- x1 + 0.30*rng                    # P 列
scale_x_continuous(limits = c(min(fD$lo) - 0.05*rng, x2 + 0.22*rng), expand = expansion(mult = c(0,0)))
# 表头
geom_text(data = data.frame(x = c(x1, x2), lab = c("\u03b2", "P"), y = length(labs) + 0.85), ...)
scale_y_discrete(expand = expansion(add = c(0.65, 1.35)))
```

95% CI 由**误差线**表示，精确值进补充表，并在图注写明 "the estimate (β) and its P value are labelled beside each model, with the 95% confidence interval drawn as the horizontal error bar; exact values are listed in Supplementary Tables S1/S2"。

### 3.2 组间 P 要单独占一行

箱线图分组上方同时放 "n = …/mean(SD)" 和 "Kruskal–Wallis P …" 会重叠 —— 本次 P 文本压在第一个分组标签上。做法：P 放到标签**上方一行**（`y = top_lab + 9`，`hjust = 0.5`），并把 `limits` 上界同步放宽（`top_lab + 17`）。

### 3.3 必跑的标注核验

```python
# 完整性：不能出现被截断的数字（如 "-0.133 (-0.170, -0.09"）
# 不重叠：同一 y 上，估计值列右边界 < P 列左边界
assert est.x1 < p.x0
# 无越界：任何 span 的 bbox 不得落到页面外
```

---

## 4. 图例必须**真的渲染出来**

用户是靠肉眼发现这一条的："图 C 是不是对应两个分组，**标签呢**？不同分组是否对应柱状图颜色应该不同？"

**真 bug**：`data.frame(\`>0.40\` = d4, \`>0.70\` = d7)` —— R 把非语法列名改写成 `X.0.40` / `X.0.70`，`pivot_longer` 后取到的值就不再等于 `scale_fill_manual(values = setNames(..., c(">0.40", ">0.70")))` 里的名字 → **静默失配：两组柱子同色，图例整个消失**（只留一条 "No shared levels found…" 警告，极易被日志淹没）。

修法：把标签作为**数据值**写进长表，并显式设水平。

```r
thr_lv <- c("> 0.40 (medium)", "> 0.70 (high)")
dl <- data.frame(gene = rep(hk, times = 2),
                 thr  = factor(rep(thr_lv, each = length(hk)), levels = thr_lv),
                 deg  = c(d4, d7))
scale_fill_manual(values = setNames(c("grey68", "#3C5488"), thr_lv), name = "STRING confidence")
```

核验两项：
1. 文字层里**每个预期图例标签都在**（`> 0.40 (medium)` / `> 0.70 (high)`）。
2. **按像素统计实际出现的填充色**（图例文字在 ≠ 颜色真的画出来了）：
   ```python
   cnt = Counter(im.crop(panelC).getdata())
   # 期望看到两种不同的主色，本次 rgb(172,172,172) + rgb(59,84,135)
   ```

---

## 5. 其它定稿项

- **四格等大**：`plot_layout(widths = c(1,1), heights = c(1,1))`（用户明确要求 1:1:1:1）。
- **单位的上标**：`kg/m2` 里 2 必须是真上标 → `labs(y = expression("BMI (kg/m"^2*")"))`；核验方式是文字层里出现**独立的 `2` span 且 y 更小**。
- **图例压数据**：箱线图图例移到 `legend.position = "top"`（不遮箱体）；参考线标注（如 `P = 0.05`）要留 headroom，用 `scale_x_continuous(limits=...)` 显式给右侧留位，否则贴边被裁。
- **防重叠基因名**：`ggrepel::geom_text_repel(..., max.overlaps = Inf, box.padding = .42, min.segment.length = 0)` + `expansion(mult = 0.16)`；`filter(hub == "yes")`（logical 转 factor 后别忘了改过滤条件）。
- **导出**：PDF（cairo_pdf）+ TIFF（400 dpi LZW，供 Elsevier 印刷）+ PNG（只进 `核对预览/` 给用户看，不投）。**PyMuPDF 不能写 TIFF**，渲染 PNG 后走 PIL。

---

## 6. 一张图定稿前的核验清单

- [ ] 面板字母：位置在**绘图区之外**、与作者原图同方位/同字体/同色；与下方内容间隙 > 0
- [ ] 图内无解释性标题/副标题/caption
- [ ] 每个面板的统计值与 P 值都在，**完整未截断**、彼此不重叠、不出页面
- [ ] 每个预期图例都渲染出来；分组颜色确实不同（像素抽样）
- [ ] 多面板等大
- [ ] 上标单位是真上标
- [ ] 文字层扫描：`spans outside page == 0`
