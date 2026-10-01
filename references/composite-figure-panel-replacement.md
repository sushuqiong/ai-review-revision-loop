# 返修时"只换一个面板"——在已投稿的多面板图上做原位替换

> 触发：审稿人/编辑要求改**其中一张子图**（如 Figure 5F），但合成图是当年在 Illustrator 里拼好的
> （`.eps/.pdf/.tif/.svg`），单个面板 PDF 也在，**不能**要求用户自己去重拼。
> 关键约束：A–E、G、H 面板以及 A–H 字母标注必须**保持原样**（审稿人已看过旧图，整图重排风险大）。

## 一、先探明合成图的内部结构（决定可做什么）

```python
import fitz
d = fitz.open(composite_pdf); p = d[0]
print(p.rect, p.rotation)
print("text len:", len(p.get_text().strip()))   # ← 有文字层就能精确定位面板
print("images:", len(p.get_images(full=True)), "drawings:", len(p.get_drawings()))
```

**好消息**：Illustrator 导出的合成图通常**保留字体与文字层**。逐 span 打印坐标即可拿到面板字母：

```python
for b in p.get_text("dict")["blocks"]:
    for l in b.get("lines", []):
        for s in l["spans"]:
            if s["text"].strip() in list("ABCDEFGH"):
                print(s["text"], round(s["bbox"][0],1), round(s["bbox"][1],1), s["font"], s["size"])
```
本会话实测输出（Figure 5，595.276 × 990.13 pt）：
`A(14.7,11.2) B(294.0,11.2) C(14.0,253.6) D(293.4,253.6) E(14.7,489.5) F(294.7,489.5) G(13.4,737.0) H(293.4,737.0)`
→ 立即可读出版面是 **2 列 × 4 行**：左列 x≈15–285、右列 x≈295–576；行起点 y≈11 / 253.6 / 489.5 / 737.0。
（字母坐标是 span 的 **bbox 顶点**，不是基线——见第三节。）

## 二、量出目标单元格的"内容盒"，并把新面板按同一尺寸出图

渲染目标单元格 → 扫暗像素求内容 bbox（纯 PIL，无需 numpy）：
```python
clip = fitz.Rect(290, 492, 582, 734)          # 右列第 3 行，稍微放宽
pix = p.get_pixmap(dpi=200, clip=clip)
im = I.open(io.BytesIO(pix.tobytes("png"))).convert("L"); W,H = im.size; px = im.load()
sc = 72/200
rows = [sum(1 for x in range(W) if px[x,y] < 245) for y in range(H)]
cols = [sum(1 for y in range(H) if px[x,y] < 245) for x in range(W)]
# 取 rows/cols 中首个/末个 >1 的位置 → 内容 bbox
```
**关键一步：把新面板按这个盒子的物理尺寸重新出图**，而不是把现成的宽图塞进去。
本会话：目标内容盒 = 275.8 × 231.1 pt = **9.73 × 8.15 cm**，
于是 R 侧 `TARGETW <- 9.73; TARGETH <- 8.15`，`ggsave(width=TARGETW/2.54, height=TARGETH/2.54)`，
`base_size = 8` + `axis.text.x = element_text(size = 6.2, angle = 45)`。
这样新面板的字号**天然与邻近面板同量级**，不需要靠缩放去凑。

## 三、替换：redact → show_pdf_page → 重画字母

```python
# 1) 抹掉旧面板（范围放宽到含旧字母）
p.add_redact_annot(fitz.Rect(293.0, 487.0, 580.0, 733.0), fill=(1,1,1))
p.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE)     # 必须显式要求删图

# 2) 放新面板：保比例、居中
s  = min(TARGET.width/cb.width, TARGET.height/cb.height)
w,h = cb.width*s, cb.height*s
x0 = TARGET.x0 + (TARGET.width - w)/2
y0 = TARGET.y0 + (TARGET.height - h)/2
clip_src = fitz.Rect(x0 - cb.x0*s, y0 - cb.y0*s,
                     x0 - cb.x0*s + np_.rect.width*s, y0 - cb.y0*s + np_.rect.height*s)
p.show_pdf_page(clip_src, newdoc, 0, clip=cb)               # clip=cb → 只放内容盒，去掉源图白边

# 3) 重画面板字母
p.insert_text((294.7, 515.3), "F", fontname="helv", fontsize=24.0,
              color=(35/255, 24/255, 21/255))
```

### 这一步的三个坑（都真实踩过）
| 坑 | 现象 | 修法 |
|---|---|---|
| 嵌入字体无法复用 | `Exception: need font file or buffer` | 原始字母是 `ArialMT` 子集，**不能** `insert_text(fontname=s["font"])`；用 `"helv"`（Helvetica，与 Arial 同度量）。想更保真可 `insert_font(fontfile=...)` 指向系统 `arial.ttf` |
| 颜色单位 | `ValueError: need 1, 3 or 4 color components in range 0 to 1` | span 的 `s["color"]` 是 **打包整数**，要转成 0–1 浮点：`((c>>16)&255)/255, ((c>>8)&255)/255, (c&255)/255` |
| 字母位置偏高 | 新字母 bbox 顶点 472.7，而兄弟字母是 489.5（差 17 pt，肉眼可见没对齐） | `insert_text` 的 y **是基线**，不是 bbox 顶点。先用一次试插测出偏移（24 pt Arial 约 **+25.8 pt**），或直接令 `y_insert = 目标bbox_top + 25.8`。**插完必须重新读一遍字母坐标并与兄弟字母逐一比较** |

## 四、导出与验收

- **PyMuPDF 不能写 TIFF**：`get_pixmap(dpi=400).save("x.tiff")` → `ValueError: Image format tiff not in (...)`。
  正确做法：先出 PNG，再 `PIL.Image.open(png).save(tif, format="TIFF", compression="tiff_lzw", dpi=(400,400))`。
- 验收清单（全部机器可查，不要目测）：
  1. 重新 `get_text("dict")` 读字母列表 → 8 个字母位置与原图逐一相同（本会话最终 `F(294.7, 489.5)` 与 `E(14.7, 489.5)` 齐平）；
  2. 新面板内文**是矢量可检索文字** → 打印其 span，确认标题/副标题/每个显著性标记都在，且标记与统计表一一对应
     （本会话 `* ns * *** *** *** * *** *` ↔ FDR 值）；
  3. `len(p.get_images(full=True))` 与 patch 前一致（=212）→ 证明没有误删其它面板的图；
  4. 额外导两张 PNG 给用户自查：`preview_*_full.png`（整图）与 `preview_*_panelX.png`（裁切该单元格）。
- 提交用 PDF（矢量）+ 400 dpi LZW TIFF；**不要**让用户自己在 Illustrator 里重拼。

## 五、交付文件命名（避免用户拿错）
```
Figures/Figure5_<原图名>_REVISED.pdf      ← 直接替换系统里的 Figure 5 栏位
Figures/Figure5_<原图名>_REVISED.tiff     ← 同上（印刷版）
Figures/preview_Figure5_full.png          ← 让用户核对的预览
Figures/preview_Figure5_panelF.png        ← 让用户核对单面板
Figures/Figure5F_revised_*.pdf            ← 单面板备用（一般用不到，但保留）
```
并在 README/交付说明里写一句："Figure 5 直接传 `..._REVISED.pdf`，不要再用原图。"
