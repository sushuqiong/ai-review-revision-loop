# 渲染级质检 + 包清单设计（字符级检查不算验证）

来源：v15→v16 一轮对抗性审查。用户反复问「图表有没有你常犯的错误」，**字符数/文本级检查既会误报又漏真问题**，必须落到「渲染后的页面」和「真实的包」上。

## 1. 渲染级页面质检（PyMuPDF 词框）——最强替代方案

vision 模型不可用时，这是能证明「无越界、无文字重叠」的硬证据：

```bash
python scripts/rendered_page_qa.py 稿.pdf 补充材料.pdf
# 输出示例：pages 39 words 8623 | overflow 0 | overlapping pairs 0
```

原理：`page.get_text("words")` 取每个词的 bbox，判断 (a) 是否越出页面框（x1>W-1 / y1>H-1，即裁切或溢出），(b) 词框两两交叠面积 / 较小框面积 > 0.45（即文字压字）。
判读：**两个数都必须是 0**。把每一步修复后的数字记进质检表，作为可复现证据。

实测教训：
- 用「单元格字符数 > 70」判断表格溢出 → 大量误报（长描述格在 7–8 pt 下正常换行）；换渲染级检测后 0 越界 0 重叠，且真正的问题（跨页溢出）在渲染级一眼可见。
- OCR 判「图内是否有图例/总标题」时必须**整词匹配**（`\btable\b`）：否则图里的 "not testable" 会被当成 "table" 报 FAIL（本轮真实误报）。

## 2. 图件像素级质检（配合使用）

六项：边带墨迹（外 2px 内是否有 ink，>0 即裁切/出血）、打印尺寸（宽 ≤6.7 in、高 ≤24 cm）、dpi（≥300）、墨迹密度（0.002–0.3）、缩 50% 后 OCR 可读性（≥0.75）、图内无图例/总标题（整词匹配）。
实测：Fig1 缩 50% 可读性 0.60 → 提高最小字号后 0.83；四图最终 0 裁切/0 碰撞/0 越界。

## 3. 包清单设计（避免自引用措辞）

```
08_qc/checksums_sha256.txt              每行一个数据文件；**不含自身**
08_qc/file_inventory_and_checksums.csv  file,bytes,rows,sha256（无自引用行）
08_qc/manifest_checksum.txt             上面两个清单文件自身的 sha256
```

- 验证：`sha256sum -c 08_qc/checksums_sha256.txt`，从包根目录执行。
- **禁止**写「N files, with N−2 SHA-256 entries because the two verification files are self-referential」——这种措辞本身就会被审稿人挑（GPT6 v15 明确点名）。
- 正文里的文件数/行数必须**构建时现算注入**，不得手写：一次修改后正文仍写 107，实际 121，被审计抓出。

## 4. 工具会在自己的项目上抓到真缺陷（本轮实证）

写完 `package_manifest.py` 后回测 v16 真包：

```
verified 128 | problems ['08_qc/qc_adversarial_review_v16.csv: FAILED']
```

原因：后来新增的对抗性审查 CSV 没进清单。修复＝重跑 `package_manifest.py` 重建清单 + 重打归档包 → `verified 129 | problems none`。
**教训：每新增/删除一个包内文件，必须重建清单；打包前先 `--check`。**

## 5. 收工前的渲染级门槛

| 检查 | 门槛 | 工具 |
|---|---|---|
| 图：裁切/出血 | 0 | `scripts/figure_qa_pixel.py`（本 skill 已有） |
| 图：缩 50% 可读性 | ≥0.75 | 同上 |
| 图：图内图例/总标题 | 无（整词匹配） | 同上 |
| 页面：越界词数 | 0 | `scripts/rendered_page_qa.py` |
| 页面：文字重叠对 | 0 | 同上 |
| 包：校验 | 0 个 FAILED | `scripts/package_manifest.py --check` |
| 正文数字 vs 包内 CSV | 全一致 | 见 ai-review-revision-loop 的自查清单 |
