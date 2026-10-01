# 补充图制作 + 几何/文字层质检（ggplot + PyMuPDF）

本用户对图件的容忍度极低（"画图总有问题"）。**禁止用 OCR 质检小字**（8pt 标注 OCR 会漏、会糊），一律读 **PDF 文字层**。

## §0 先量作者原图，再仿它的风格
不要凭感觉定子图字母的字号/颜色/位置——用 PyMuPDF 量：
```python
letters = [(s["text"].strip(), s["bbox"], s["size"], s["font"])
           for b in pg.get_text("dict")["blocks"] for l in b.get("lines",[]) for s in l["spans"]
           if re.fullmatch(r"[A-J]", s["text"].strip())]
print(pg.rect)   # 页面尺寸 → 换算"字母宽 = 页宽百分比"
```
本例实测：作者原图 Fig.4/5/6/7 的字母为 **ArialMT 24pt、非加粗、近黑 (35,24,21)**，位于每个子图的**左上方外侧**（第二列字母 x≈页宽 50%）；页宽 595pt。字号要按**页宽比例**换算到自己的图（例：17cm=482pt 的图 → 24×482/595 ≈ 19pt，实际取 13pt 折中）。

## §1 子图字母必须放在绘图区之外
- `patchwork::plot_annotation(tag_levels="A")` 把字母放在**面板内部**（会压数据/图例）→ 用户会明确投诉"标签要在图外面"。
- 免 tag 的做法（每张子图各自加，位置完全可控）：
```r
tag <- function(lab) list(
  labs(title = lab),
  theme(plot.title.position = "plot",                       # 相对整个子图（含图例/分面条）对齐
        plot.title = element_text(hjust = 1, size = 13, colour = "#231815",
                                  family = "sans", face = "plain", margin = margin(b = 1))))
pS6A <- <ggplot> + tag("A")
```
效果：字母落在**该子图右上角、绘图区之上**，与顶部图例/分面条不冲突。
- 用 `plot_layout(widths=c(1,1), heights=c(1,1))` 保证用户要的"A:B:C:D = 1:1:1:1"等大。
- 图上**不要**标题式说明文字和底部说明段（作者原图也没有），全部写进 Figure legends。

## §2 文字层质检清单（改完必跑）
```python
sp = [(s["text"].strip(), s["bbox"][0], s["bbox"][1], s["bbox"][2], s["bbox"][3], s["size"])
      for b in pg.get_text("dict")["blocks"] for l in b.get("lines",[]) for s in l["spans"] if s["text"].strip()]
```
1. **字母位置**：打印 `x0/页宽`，右格应 ≈95%，左格 ≈43–47%；`y0` 应贴近页面顶部（≈14pt）＝在绘图区外。
2. **越界/裁切**：`[s for s in sp if s[1]<-1 or s[2]<-1 or s[3]>W+1 or s[4]>H+1]` 必须为 0。
3. **截断**：把某个 span 与**期望的完整字符串**比对。截断的 span 会长这样：`-0.133 (-0.170, -0.09`（数字被切一半）→ 说明被面板右边缘裁掉了。
4. **相邻文字列重叠**：同一行内左列 `x1` 必须 < 右列 `x0`（本例 β 列止于 429.6，P 列起于 442.0 → 安全）。
5. **标记计数**：如 `Counter(t for t in sp if t in ("*","**","***","ns"))` 应等于你预期的数量（本例 4×`*`+4×`***`+1×`ns`）。

## §3 本项目踩过的 ggpht/R 坑（全部静默失败，务必按此写）
| 坑 | 症状 | 修法 |
|---|---|---|
| `scale_x_continuous(limits=...)` | 超界的 `geom_text` **被丢弃**，什么都没报 | 用 `coord_cartesian(xlim=...)`（不丢数据）或把文字列算进 limits |
| `aes(y = Inf)` + `vjust > 1` | 标注被裁掉/与标题重叠 | 显式 `limits = c(NA, ymax*1.13)`，标注放在 `ymax*1.015` |
| `max(x)`（默认 `na.rm=FALSE`） | 只要有一个 NA（如 n=1 的层的 sd）→ **全部标注消失** | `max(x, na.rm=TRUE)`，并先过滤每组 n<10 的稀疏层 |
| `data.frame(`>0.40`=...)` | R 自动改名 `X.0.40` → `scale_fill_manual(names)` 不匹配 → **两组同色 + 图例消失**（本例用户直接投诉"不同分组颜色应该不同"） | 显式长表：`data.frame(gene=…, thr=factor(rep(lv, each=n), levels=lv), deg=…)` |
| `c(`\u2265 12.0` = ...)` | `错误: \uxxxx sequences not supported inside backticks` | 写成变量 `c3 <- "\u2265 12.0"` 再用 `setNames(cols, c(...))` |
| 同一 `geom_text` 的数据含重复行 | 标注被画两遍（同坐标叠印，看着略粗） | `data = df %>% distinct(ageband, p)` |
| 半幅宽面板放"β (95% CI)"文字列 | 文本被右边缘**截断**成 `-0.133 (-0.170, -0.09` | 只放紧凑的 **β** 与 **P** 两列（表头 `β` / `P`），95% CI 交给误差线表示 + 精确值写进补充表，并在图注注明 |

## §4 导出与命名
- **PyMuPDF 不能写 TIFF**：`get_pixmap(dpi=400).save(x.tiff)` → `ValueError: Image format tiff not in (...)`。
  正解：`pix = pg.get_pixmap(dpi=400); pix.save(tmp.png)` → `PIL.Image.open(tmp.png).save(out.tiff, format="TIFF", compression="tiff_lzw", dpi=(400,400))`。
- 每张图给三份：`.pdf`（矢量，投稿）+ `.tiff`（400 dpi LZW，印刷）+ `.png`。
- **PNG 预览放进 `Figures/核对预览/` 子目录**，交付夹里只留要上传的 pdf/tiff——否则用户会问"你搞出那么多文件干什么"。
- 程序化改过的图必须附 `preview_*.png` 并明确写"直接传这个、不要用原图"。

## §5 原位替换作者合成图里的某一个子面板（用户问"这你能做到吗"＝直接做掉）
1. 合成图**有文字层**（Illustrator 导出）→ 用字母 span 的 bbox 定位它属于哪一列/行。
2. 量出该面板的**内容 bbox**（在裁切区域内对像素求 ink bbox）。
3. 用**该 bbox 的宽高比**生成替换面板（不要用你自己的宽比，否则留白/拉伸）。
4. `page.add_redact_annot(rect, fill=(1,1,1))` → `page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE)`。
5. `page.show_pdf_page(clip, src_doc, 0, clip=content_bbox_of_new)`，按 s=min(sx,sy) 保比例居中。
6. 重画字母：`page.insert_text((x0, y_base), "F", fontname="helv", fontsize=24, color=(35/255,24/255,21/255))`
   - 原图嵌的是子集字体（`ABCDEF+ArialMT`）→ `insert_text` 抛 `need font file or buffer`，退回 `"helv"`（视觉等同 Arial）。
   - **y 是基线**：要匹配原字母 bbox 的 y0=Y，插入 y ≈ Y + 1.08×size（本例先写 498.5 高了 17pt，改 515.3 后与相邻字母完全对齐）。
7. 校验：字母列表 A–H 齐全且 y0 一致；`xobjects/images` 数量不变；导出 400 dpi TIFF。
