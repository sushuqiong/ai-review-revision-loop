# Graphical Abstract：一条独立的交付线（不是"再来一张图"）

GA 与数据图是**两个不同的交付物**：数据图要可读、可检、符合版宽；GA 要**一眼讲完整个故事**，
通常还要保留作者原版的版式语言（用户会说"修改完善"，不是"重做"）。返修时用户会要求
"输出新的 PDF 版本随返修手稿一起上传"。

## 一、先读用户原版，量出它的版式语言（不要一上手就画）

```python
import fitz
pg = fitz.open(user_ga)[0]
print(pg.rect.width, pg.rect.height)          # 本轮：1166.4 × 576 pt = 41.15 × 20.32 cm
for b in pg.get_text("dict")["blocks"]:       # 字体 / 字号 / 文字颜色
    for l in b["lines"]:
        for s in l["spans"]:
            s["font"], round(s["size"], 1), "#%06x" % s["color"]
for d in pg.get_drawings():                   # 色板（圆角框/色带的填充色）
    d.get("fill")
pg.get_text()                                 # 原版把哪些数字/说法放进了 GA
```

本轮量出来的原版：Arial 系字体、字号 9–24 pt、三条分相位色带（红 `#C0392B` / 橙 `#D35400` /
绿 `#1E8449`）+ 紫色 `#7D3C98` 结论带 + 同色浅底（`#FADBD8`/`#FDEBD0`/`#D5F5E3`/`#E8DAEF`），
深色标题带 `#1C2833`。

**沿用原版的页面尺寸 + 色板 + 分相位结构**，用户才会觉得是"同一个 GA 的升级版"，
而不是"你另做了一张"。页面尺寸不变还有个好处：投稿系统里替换后版面观感一致。

## 二、用 matplotlib 按 pt 直画（可控、可机器校验）

```python
W, H = 1166.4, 576.0                                  # 与原版同尺寸（pt）
fig = plt.figure(figsize=(W / 72, H / 72))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
plt.rcParams["font.family"] = "Arial"                 # 无则 DejaVu Sans
plt.rcParams["pdf.fonttype"] = 42                     # TrueType 嵌入，期刊可读
```
三个小工具函数（`rbox()` 圆角框 = `FancyBboxPatch(boxstyle="round,pad=0,rounding_size=7")`；
`tx()` 文本；`arrow()` = `FancyArrowPatch(arrowstyle="-|>")`）。**字号下限在 `tx()` 里统一夹紧**：

```python
def tx(x, y, s, size=10, ...):
    size = max(size, 9.0)        # 用户硬规则：任何文字不得 < 9 pt，一处也别放过
```

版面按**显式纵坐标网格**摆放（标题带 → 三栏分相位面板 → 结论带），每一条文字都给死 y，
不要靠自动换行——自动换行是"副标题压住正文首行"这类事故的成因。

## 三、内容规则（比版式更容易出事）

1. **GA 里的每个数字都必须能在手稿里 grep 到。** 本轮 GA 一度用了自己复算的
   `−0.169/−0.097`，而手稿是 `−0.173/−0.093` → 改用手稿值。
   **优先用"手稿里已经写着的值"**（校正均值、OR/HR、β、E-value），不要用你后台复算的值。
2. **顺手把返修新增的结论放进 GA**——GA 是回应主编关切的最省字的地方。本轮在 Phase II
   加了 "Not explained by the age component of FIB-4（FIB-4 core β = −0.131）"+"consistent in the
   VCTE subsample"，并把手稿改定的 "8/9 replicated" 写进 Phase I。
3. **短横线/术语与手稿对齐**（用户做过 en dash → hyphen 全局清理时尤其重要）。
4. **不做示意图**：宁可少画一个面板，也不要画"方向对但数值是编的"曲线。
   相位 III 就用真实的 OR/HR 条形图（参考线 = 1.0），不要画无从核对的轨迹示意。

## 四、收工前必跑

`scripts/qa_pdf_layout.py`：越界 0、重叠 0、min(size) ≥ 9 pt、字体已嵌入
（`get_fonts(full=True)` 里能看到 `+ArialMT` 之类的子集前缀）。
本轮实测：连抓"副标题压住正文首行"和"柱状图数值标签压住正文行"两处真重叠，
调整基线/柱高后才 0 重叠。

## 五、交付与追问

- 主交付 = **矢量 PDF**（Elsevier 收 PDF/TIFF/EPS）。放交付目录根，命名
  `Graphical_Abstract_revised.pdf`。
- **主动问一句要不要 PNG/TIFF**（有些投稿系统 GA 栏位只收图片格式），别自己先塞进目录里
  制造冗余文件——用户对交付目录的整洁度敏感。
- GA 里的"顺带提醒"（本轮提醒了 README 因用户重命名而过时）值得说，但要放在最后、一句话。

## 六、坑

- **坐标系**：matplotlib 是 y 向上，PyMuPDF 是 y 向下。凡是用 PyMuPDF 校验 matplotlib 输出，
  面板矩形要换算 `pdf_y = H - mpl_y`，否则"面板包含性"检查完全无意义（本轮先犯了这个错，
  报告里出现了假的"越界"条目）。
- `plt.figure(figsize=(W/72, H/72))` 里 W/H 是 pt，**不要**再乘 2.54 之类；尺寸单位混乱会让
  25 pt 的字变成 4 pt。
- 保存路径与 `os.makedirs` 的顺序：先建目录再 `savefig`，并且**别用 `x if cond else None`
  这种带条件表达式的单行保存语句**——它会被后续的批量文本替换误伤而静默消失（本轮 PNG
  就因此没生成，只有 PDF 出来了）。
