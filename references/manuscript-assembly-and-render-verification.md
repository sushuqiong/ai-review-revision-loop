# 手稿组装 / 渲染级验收（markdown → docx 多轮迭代的硬坑与闸门）

适用：用 pandoc(+python-docx 后处理三线表) 反复增补章节、补充表、图注的手稿（v9→v17 这类长链迭代）。
本文件只记"会真出事"的坑与可复跑闸门；细则操作见 SKILL.md 主文。

## 1. 规范尾部顺序（唯一权威）
```
正文 → Declarations → References → Tables(## Table 1..N) → Figure legends(图+图注) → Supplementary material(S1..Sn)
```
补充材料必须在文件**最末**；`# Supplementary material` 标题必须在 **S1 之前**。

## 2. 两个必踩的坑（都在本会话真实发生过）
**坑 A：用 `s[:i] + block + s[i:]` 且锚点选 `# Figure legends`**
→ 新增的补充表(S15/S18/S19)被插到 Figure legends **之前**，即跑到补充材料区之外。
症状：读者看到"`Supplementary material` 标题后面什么都没有"（标题被挤到文件末尾），或编号出现 S18 在 S14 前面的乱序。

**坑 B：用字符串 replace 做"重排"**
→ 块与块重叠匹配，产生**重复内容**：主表数 9→10 变 14、全文字数暴涨（7,564→10,487）、docx 内表格数对不上。
症状：docx 表数/页数异常、字数与编辑前备份不符。

**正确做法：行级解析重建尾部**
```python
# 逐行扫描，按行首标记分类收集，再按规范顺序重新输出
^## Table (\d+)\.            -> tables[n]
^!\[Figure (\d)\]            -> figs[n]（含其后图注段落）
^\*\*Supplementary Table S(\d+)\. -> supps[n]
^# (Tables|Figure legends|Supplementary material)$ -> 丢弃旧标题
其余 -> body
# 输出: body + "# Tables" + tables1..N + "# Figure legends" + figs1..N + "# Supplementary material" + supps1..Sn
```
- 先 `cp file file_backup_before_restructure.md`，事后对比字数/标记数。
- 完工自检：`len(re.findall(r"^## Table \d+\.", s))`、supp 标记数、`^!\[Figure \d\]` 数 三者必须等于预期且**无重复**；若预期 N 张表却出现 N+k，多半是块边界吞并了别的块。

## 3. 渲染级验收（唯一能证明"读者看到的是对的"的手段）
docx 内部的 XML 顺序 ≠ 渲染顺序；必须 **docx→PDF→按页取文本**：
```bash
soffice --headless --convert-to pdf --outdir <tmp> <docx>
```
然后用 PyMuPDF 断言（脚本：`scripts/verify_manuscript_structure.py`）：
1. `full.find("Supplementary material") < full.find("Supplementary Table S1.")`
2. `S1..Sn` 的 index **单调递增**
3. `"Tables" before "Table 1."`、`"Figure legends" before "Figure 1."`
4. 图与图注同页：`page.get_image_info()` 有图时，同页文本须有 `^Figure N\.` 图注；逐页打印对照
5. 泄露扫描：真实单位名 / 邮箱 / 基金号 token 在两版（署名版+匿名版）都必须为 0
6. 占位符确认：`[Department` / `[funding body` 存在（作者/基金信息未填时）

**坑 C：`page.get_images()` 在 docx 转出的 PDF 上会返回"文档级共享资源"**，导致每页都报同样数量的图（如每页 6 张）。
→ 必须用 `page.get_image_info()`（只返回该页实际绘制的图）。

**坑 D：python-docx 读段落时 `p.text` 不含 markdown 的 `#`**，用 `^# ` 正则找标题会全部落空；应按"标题文本精确等于 'Tables'/'Figure legends'/'Supplementary material'"来判定。

## 4. 图件文本完整性（OCR 闸门，能抓出"看起来正常其实坏了"的图）
`pytesseract` 在部分环境的 pandas/numpy ABI 下 import 直接失败（`numpy.dtype size changed`）——**绕开它，直接调二进制**：
```bash
tesseract fig.png stdout tsv --psm 6      # 版式/整行
tesseract fig.png stdout tsv --psm 11     # 稀疏文本 + 坐标
```
判据：
- 期望数值全部出现（如 HR 数组、CI、样本数、排除数）
- **`"NA ("` 计数必须为 0** —— 本会话正是靠这一条抓出 Fig5 全亚组标签变成 `NA (0.926-NA)`（图是由 markdown 表格文本解析生成的，解析失败仍出图）
- 文字包围盒距图像边缘 ≤3px = 疑似被裁切
- 纵轴等**旋转文本**OCR 常读不出（如 "Hazard ratio"）→ 不据此判缺陷，需人眼或视觉模型确认

## 5. 出图与图注的一致性
- 图注里写的"图中要素"必须真在图里：本会话 Fig5 图注原写"with interaction P values"而新图未标 P → 改为"interaction P values are reported in Table N"。
- 让图**由最终结果表/计算对象直接驱动**（或反之），不要两处手抄：Fig5 改为由 Table 6 数值生成后，图表天然同源。
- 图内数值标签的 x 位置必须落在 `scale_x_continuous(limits=...)` 内，否则被裁切；长字符串用"轴扩展 + 独立右侧标签列"。

## 6. 匿名版与署名版
- 两版必须**同源同内容**，仅身份/基金/仓库链接不同；每次改正文都要重建两版，并逐版跑第 3 节断言。
- 匿名版保留伦理批号、数据 URL 无害；必须清除：姓名、邮箱、单位、基金号、私有仓库 URL、可识别致谢。
