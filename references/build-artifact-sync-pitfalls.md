# 构建产物同步铁律（2026-09 实战教训：两轮独立冷读都因此抓到 Blocker）

## 1. 手稿 md 一改，立刻重建 docx/pdf
- 第二轮与第三轮冷读都是靠这条抓到 Blocker：**md 时间戳 23:16 vs docx 22:10**，关键词计数 **新段落 md=1 / docx=0**（"Single-cell sensitivity analyses"、"Input data"、"200 comparisons" 全部只在 md）。
- 规则：**改 md 的同一个脚本里就重建 docx/pdf**。不要"先改文本、稍后统一打包"——中间态就是投稿硬伤。

## 2. 重建后必须双向自检（写进构建脚本，不通过就报错）
1. **段落对齐**：md 里每个 `##`/`**` 段落标题与关键短语，必须在 docx 抽取文本中逐一出现（缺一即失败）。注意排除 `**Figure …` 这类跨行图注造成的假阳性。
2. **插图对齐**：docx 内嵌图必须与 `02_figures/*.png` **逐字节 sha256 一致**。曾出现 docx 内嵌的是**旧版 Fig3**（与磁盘图 36,881 像素不同）。
   - 正确取法：遍历 `doc.part.rels.values()`，`rel.reltype` 含 `image` → `rel.target_part.blob`。
   - 反例：`doc.part.related_parts['media/image1.png']` 会 `KeyError`。
3. **上标引用**：md 里 `xCell8`/`GSVA7` 只是普通字符。docx 构建时用正则
   `(GEOquery|Genomic Data Commons|cBioPortal|CELLxGENE|GEO|GSVA|xCell|metafor|Hartung-Knapp|limma|R)(\d+(?:,\d+)*)`
   拆 run，数字设 `run.font.superscript=True`，并断言上标 run 数 > 0。参考文献编号必须与正文**首现顺序**一致（曾出现 9/10/11/12 错位：limma 与 metafor/Hartung/Knapp 顺序颠倒）。

## 3. 正文数字一律从 manifest 现算
- 文件数 / SHA 条数 / 补充表编号 / 目录数 都要在构建时从 `file_inventory_and_checksums.csv`、实际目录现算后回填 md，再重建 docx。
- 教训：手写死数字会连续过期——本项目经历了 **82 → 86 → 101 → 107** 四轮追改，每轮都被审稿人抓到。
- 口径要写清：`N files`（含两名自引用文件）与 `N-2 SHA entries`；`ten folders` → `eleven folders`（新增 `11_code/` 后必须同步）。

## 4. 投稿 ZIP 与内部文档分离
- 投稿包只放：正文 docx/pdf、`Supplementary_Information.pdf`、表格 docx、图例 docx、4 图 PNG+PDF，另加英文 `00_READ_ME_FIRST.txt`。
- **不要**把"先看这个_评审处置.md""状态与待办.md""Zenodo 上传指南.md"打进投稿 ZIP——内部语气 + 过期数字会被编辑视为不规范（第三轮冷读 M6）。
- 中文文件名尽量少；必要时统一前缀。

## 5. 重复文件与"重算副本"
- 重算后不要同时保留 `X.csv` 与 `X_v14recomputed.csv`（逐字节相同 = 冗余，被判为未清理）。
- 主表与**所有**敏感性表的 k=1 行统一置 `not applicable` + `pooled="no (single cohort; not a pooled estimate)"`；只改敏感性表漏主表会被抓（第三轮 M1）。

## 6. 交付前的机器检查清单（可脚本化）
| 检查 | 判定 |
|---|---|
| md/docx/pdf 时间戳 | 三者同一分钟内 |
| 关键短语计数 | md 与 docx 逐一相等 |
| 内嵌图 sha256 | 4/4 与磁盘一致 |
| 上标 run 数 | > 0 且与引用条数相符 |
| 补充表编号 | 正文与 SI PDF/表格 docx 一致（S1–S17） |
| 文件数与 SHA 条数 | 稿件数字 == manifest 现算值 |
| `sha256sum -c` | 零 FAILED、零告警、零 stderr |
| 投稿 ZIP 清单 | 无内部笔记、无 vN-1 残留、docx/pdf 与工作区同版 |
| 图表 QA 脚本输出 | 若有 FLAGGED，需在 `08_qc/figure_qa_notes.md` 说明并给出复核方法（勿只口头称"假阳性"） |
