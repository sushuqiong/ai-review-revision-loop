# 图件机械质检（Figure Layout QA）— 出图后必跑

> 触发：任何一次"重画/改图/换版本图"。用户对图件长期不满（"你画图表总是有问题"），
> 但机器侧原本看不到图——本文件给出可执行、可复现的机械检查，把人眼验收降到最低。

## 0. 根因清单（先记住这三条，能消掉大部分"图有问题"）
1. **版宽**：图必须 **≤ 6.7 in（17.0 cm）@300 dpi（≤2010 px）**。超过版宽会被期刊缩排到 17 cm，
   字号随之等比缩小 → 印刷后跌破 7 pt。这是"字号过小"的第一根因。
   核对方式：导出规格表里 `cm_w ≤ 17.0`。
2. **字号单位**：ggplot `geom_text(size=)` 单位是 **mm**（3.0 mm ≈ 8.5 pt，2.7 mm ≈ 7.7 pt 为下限）；
   `theme(axis.text=element_text(size=))` 单位是 **pt**（≥9 pt）。混用即字号失控。
3. **只允许脚本从冻结结果表生成图**，禁止手改；改图后必须重跑本节质检。

## 1. OCR 版面质检配方（Windows / tesseract CLI）
```bash
# 直接可用（bash 里）
"/c/Program Files/Tesseract-OCR/tesseract.exe" fig.png stdout --psm 11 tsv
```
Python 调用（**必须设 TESSDATA_PREFIX**，否则报 `read_params_file: Can't open tsv`）：
```python
env = dict(os.environ, TESSDATA_PREFIX=r"C:\Program Files\Tesseract-OCR\tessdata")
r = subprocess.run([r"C:\Program Files\Tesseract-OCR\tesseract.exe", path, "stdout", "--psm", "11", "tsv"],
                   capture_output=True, env=env)
# TSV 列：level page block par line word left top width height conf text
```
要点：
- **含中文/非 ASCII 的路径**：先复制到 ASCII 临时目录（如 `C:\Users\<user>\ocr_tmp`）再 OCR，避免路径编码问题。
- 备选 OCR：`rapidocr_onnxruntime`（用 PATH 上的 `python`；某些解释器环境里 onnxruntime DLL 会失败，换解释器即可，别因此放弃机械检查）。
- `--psm 11`（稀疏文本）适合图内散布标签；`--psm 6` 适合整齐的长标签列表（可用来读回 y 轴标签全串）。

## 2. 判定指标与阈值
| 指标 | 阈值 | 说明 |
|---|---|---|
| clipping（文本框触及画布边缘 2 px 内） | **= 0** | 裁切/出界 |
| overlaps（两个实质词框 IoU>0.3） | **= 0** | 文字压叠 |
| missing tokens（关键标签缺失） | **= 0** | 情境名、模块名、数字、`n.e.` |
| 版宽 cm | **≤ 17.0** | 由规格表读 |

**假阳性过滤（重要，否则报告不可用）**：
- 网格线/误差棒端/刻度会被 OCR 成 `-` `+` `5` `=` `|` 等，**高度仅 4–8 px** → 忽略 `h < 10 px` 或长度 <6 px 的框。
- 统计 overlap 时只计入 **h ≥ 29 px 且 w ≥ 25 px 且含 ≥3 个字母数字字符**的框，否则会把"标签框 ∩ 网格线"全报成重叠。
- tesseract 的 `height` 约等于小写 x 高度（≈ 标称字号的 70%），所以"<7 pt 计数"几乎全是假阳性：
  **字号以源码设定为准，OCR 只用于几何缺陷（裁切/压叠/缺字）**。

## 3. 本轮修过的真实缺陷（同类问题优先怀疑）
| 症状 | 真因 | 修法 |
|---|---|---|
| 标签渲染成空括号 `malignant cell ()` | 绘图代码引用**不存在的列**（`sig$disease`，CSV 里叫 `context`）→ 静默变成空串 | 改为正确列名；出图后用 OCR 回读该标签确认，不靠肉眼 |
| 轴文字被星号/菱形标记压到 | 稳健性标记用 `geom_point(shape=8/23)` 叠在热图格子上，紧贴左侧标签 | 改**黑色格子描边**（`geom_tile(fill=NA, colour="black")`）表示稳健，图注同步改写 |
| 图被画成 90 cm 高不可用 | 行数 × 固定行高，未按行数收敛 | 高度按 `0.25 in × 行数 + 2.4`（长条形图）；单图高度 ≤ 11 in |
| 标签 OCR 读不到 / 读者看不出情境 | 情境名只靠颜色/图例 | 情境**后置加括号**写进标签：`WNT/b-cat / malignant cell (CRC)` |
| Supp 图是上一版、标题被裁 | 复用旧图 + 标题过长 | 从冻结表重生成、标题拆两行、加大 `plot.margin` |
| 图注提到图里没画的面板 | 图注与图件不同源 | 图注逐面板对照；文件名与内容一一对应（`fig2a_*` 只含 A） |

## 4. 出图/交付三段命令（写进项目规范，每次改图都跑）
```bash
Rscript scripts/<figures>.R          # 1) 从冻结表出图（宽 ≤6.7 in）
python  scripts/<tiff_export>.py     # 2) 导出 300 dpi TIFF，写规格表（核 cm_w ≤17.0）
python  scripts/<ocr_qa>.py          # 3) OCR 质检（clipping / overlaps / missing）
```
通过标准：**clipping=0、真实重叠=0、关键标签齐全、cm_w ≤17.0**；结果写成
`04_评审记录与报告/ocr_figure_qa.csv` 之类的表格留档，并把结论写进版本说明。

## 5. 交付给用户时
- 附**能自查的预览图**（`preview_*.png`）并写明"举报错时把截图发我"（本用户会截图，且可用离线 OCR 读图定位）。
- 明确说清哪张图是"投稿用"（TIFF，300 dpi、17 cm），避免用户传错原图。
