# 版式/图件实证核验 + md 规范化重排 + 运输性论文审稿人清单

本文件为 ai-review-revision-loop 的支撑材料（SKILL.md 已近长度上限，故不新增指针行；由 skill_view 的 linked_files 发现）。

## 0. 触发场景
- 用户质疑"你做得这么快/是不是又遗留很多问题/图表不符合学术风格"——必须用工具实证核验，禁止口头保证。
- 交付 docx 前、宣布 vN 完成前、投稿文件夹打包前。
- md 源经过多轮 docx→gfm 往返、多轮插入补充材料后，结构可能已错位。

## 1. 工具链（本机可用；环境相关命令见下，失败先查可用性再换路）
- docx→PDF：`/c/Program Files/LibreOffice/program/soffice.exe --headless --convert-to pdf --outdir <dir> <docx>`（首次可能慢，给 300-420s）。
- PDF 文本/结构：PyMuPDF（`import fitz`）；`page.get_text()`、`page.get_image_info()`（判断该页实际绘制的图，`get_images()` 会把共享资源字典里所有图都列出来，不可靠）。
- 图内文字 OCR/裁切检测：**Tesseract 命令行**，例如
  `tesseract fig.png stdout --psm 6` / `--psm 11 tsv`（拿到 bbox 后判定 bbox 距图片边缘 <3px 即可能被裁切）。
  注意：本机 `import pytesseract` 会因 pandas/numpy 二进制不兼容（`numpy.dtype size changed`）报错 → 直接用 CLI，不要为此装包。

## 2. 核验清单（每次收工前跑一遍，把结果写进回复）
结构（PDF 层面，需先归一化空白 `re.sub(r"\s+"," ",full)`，否则标题断行会导致误判）：
1. `# Tables` 在 `Table 1.` 之前；`# Figure legends` 在 `Figure 1.` 之前；`# Supplementary material` 在 `Supplementary Table S1.` 之前。
2. 补充表编号严格递增 S1→SN（`find(...)` 单调）。
3. 图与图注同页（逐页 `get_image_info()` + 行首 `^Figure (\d)\.` 匹配图注段落；正文里出现的 "Figure 3" 是引用，不是图注）。
4. 末段内容应是最后一张补充表的正文，而不是某个 section 标题。
5. 页数、原生三线表数量（docx `len(Document().tables)`）、嵌入图数量（`/word/media` 部件数）。
内容：
6. 残留/硬伤：`9-year 9-year`、`D-3/D-2`（0 被渲染成 D 的误读）、`HOL`、`0.E`、`≈0. 78`、千分位缺逗号、`[II-13]` 式引用、Figure 5 尾多余 `**`、Figure 6 标题与下一个标题粘连、模型标签重复（`Base (age+sex) (age+sex)`）。
7. 泄露：真实姓名/邮箱/单位/基金号是否出现在两版（匿名版必须无；单盲版按用户要求用占位符模板）。
8. 引用：`total refs == body cites used`，`missing == []`，无孤儿。

## 3. md 规范化重排（行级重建，禁止字符串拼接）
症状：`# Supplementary material` 跑到文件末尾；S15–S17 排在 S1 前；图与补充表交错；字符串替换导致整块重复（表格从 10 张变 14 张）。
算法（行级，一次到位）：
```
逐行扫描；遇 ^## Table N\. / ^!\[Figure N\] / ^\*\*Supplementary Table SN\. 开始捕获该块，
直到下一个同类标记或 ^#  标题；丢弃旧的 section 标题行；
其余行进 body；
输出 = body + "# Tables" + 表1..6 + "# Figure legends" + 图1..6(含图注) + "# Supplementary material" + S1..SN(按编号排序)
```
校验：再次统计各类标记数量（应各等于预期，无重复）、字符数与备份差异合理（±少量）、headings 顺序正确。
注意：正文里图注必须紧跟 `![Figure N](路径)` 行；图路径用绝对路径，docx 构建时才会嵌入。

## 4. 图件生成陷阱
- **不要用"解析正文表格文本"生成图**：Token/正则解析失败会产出 HR 列为 `NA (...-NA)` 的坏图，且外观"看起来正常"。要用分析对象或已验证的表值直驱。
- 生成后 OCR 复验：关键数值必须全部命中、`NA (` 计数为 0、无贴边文字。
- 常见裁切成因：数值标签写在 `x = 1.03` 而 `scale_x_continuous(limits=c(.4,1.15))` → 必然裁切；坐标上限要预留标签宽度（如扩到 1.55/1.6），或把标签放到独立右列。
- 亚组森林图建议把交互 P 值放表里、图上只标 HR(CI)，避免图注与图不一致。

## 5. docx↔md 往返与脚本陷阱
- docx→gfm 往返会转义 `\[ \] \_ \*`，并可能丢失 YAML 标题元数据；修改前先 unescape，内容修改尽量在往返之前完成。
- 引用重排脚本：路径必须指向当前稿（曾误指旧稿导致"始终 22 条"的假象）；从 refs 块解析 allowed keys，打印 `total refs / body cites used / missing`。
- 经费号/项目号写成 `([2023]1)` 会被引用解析器当成引文 token（出现 31–40 的"悬空编号"）→ 去掉方括号写成 `(2023-1)`。
- 每次改动后跑一次重排脚本；若 `used` 与列表长度不一致，先查未引用条目再定稿。

## 6. 视觉模型不可用时的处理（配置修复，不是"工具坏了"）
- 症状：`vision_analyze` 返回 404 model not found / Permission denied，通常是 `auxiliary.vision.model` 指向已下线模型。
- 修复：`hermes config set auxiliary.vision.model <provider 自带 supports_vision 的模型>`（provider=custom 且 base_url/api_key 已配好）。
- 配置在会话启动时缓存 → **需重启 Hermes 会话才生效**；在此之前用 PDF+OCR 完成版式与文字核验，并在回复中如实说明"像素级审美仍建议人工过目"。

## 7. 运输性/外部验证类论文：审稿人高频追问清单（GPT6/Hy4 实测）
1. 估计量命名唯一化（Harrell C / 时点 C / 累积-动态 AUC / known-status 限制性一致性不可混用）；给出评估人群、事件数与删失处理。
2. 主评估窗选择：优先"行政随访充分"的周期子集（如 NHANES 1999–2010 有 ≥9 年潜在随访），并说明该窗内 restricted 估计无偏。
3. 复杂抽样：PSU/分层 bootstrap 或 replicate weights；未加权队列要收窄目标人群表述（"analytic subsample"）。
4. 完整病例选择偏倚：IPW（报权重分位数/截断）或 MI；两库方案要一致或说明差异。
5. 固定系数复合 vs 自由估计组分：嵌套 LR 检验（2 df）+ ΔBrier + 校准 + DCA 为主；NRI/IDI 为支持性。
6. PH 偏离：分段 HR（0–3/3–6/6–9 年）或时间交互/RMST；固定 HR 说明为平均效应。
7. 校准指标分列：calibration intercept（log-hazard 尺度）、slope、O:E、mean risk difference（不要把平均风险差叫 calibration-in-the-large）。
8. 乐观校正（bootstrap）与配对 ΔBrier（同一留出样本、给 CI）。
9. 过报机制分解：基线风险 vs case-mix（用来源 lp 换用目标基线风险），把"校准不转运"变成机制解释。
10. 时期/测量异质性：早/晚周期分别报校准；腰围阈值跨国产差异列为迁移限制。
11. 结局定义：cause-specific vs 累积发生率、ICD/UCOD 映射、周期可比性（如 2015–2018 死因编码不全需限窗）。
12. 复现信息：变量映射、权重缩放规则、软件版本、基线累积风险估计方法（Breslow + 中心化参照向量，逐人核对 survfit）。

## 8. 投稿目录卫生（本用户硬要求）
- 目录只留投稿必需：手稿双版、封面信双版、清单、TRIPOD、图（PNG+300dpi TIFF）、Code bundle。
- 移出过程件：AI 回应对照表、对抗性审查报告、README（如无必要）、重复代码目录、重复 zip；过程件留在项目目录备查。
- 作者/单位/ORCID/邮箱/基金号一律占位符模板（用户后续手补）；单盲版也不要留真实科室名混在"placeholder"标签下。
- 封面信数字必须与当前稿一致（外部一致性、设计 CI、LR/NRI/IDI/DCA、再校准方向差异）。
