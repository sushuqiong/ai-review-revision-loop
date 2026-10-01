# 投稿包文件清单 (Submission Package)

对标标杆：`C:\Users\fengq\Desktop\新的CLD-AIP\文稿！\投稿MDPI（Nutrients）的文件汇总\`
（内含 Cover letter.docx/pdf、Figures.zip、Graphical Abstract.jpg、Manuscript.docx/pdf、nutrients-template.dot、supplementary files.zip）

## 三篇论文实际生成的投稿包（本会话实例，2026-08）

### 通用文件（每篇论文都有）
| 文件 | 内容要点 | 生成方式 |
|---|---|---|
| `Cover letter_课题X.docx/pdf` | 致编辑 → 研究主题与核心发现（真实 OR/AUC/P）→ 创新性 → 为何适合该期刊 → 原创/未一稿多投/作者同意/伦理声明 → 署名 | python-docx 生成 docx，LibreOffice headless 转 pdf |
| `Highlights_课题X.docx` | 3-5 条，每条 ≤85 字符，**用真实数值**；脚本断言字符数；文末可附数据出处/诚实备注页（投稿前删除） | python-docx |
| `Title_page_课题X.docx` | 完整题目 + Running title + 作者 [占位符] + 单位占位 + 通讯占位 + 字数/表/图/文献统计 + 关键词 | python-docx |
| `Figures_课题X.zip` | 全部图 SVG+PDF+PNG 三格式打包（git-bash 无 zip，用 Python zipfile） | Python |
| `Graphical_Abstract_课题X.jpg` | matplotlib 学术风：暴露→机制→结局 + 核心数值，约 1900×980 px | matplotlib |

### 期刊特有文件
| 期刊系 | 必需文件 |
|---|---|
| MDPI (Nutrients) | STROBE Checklist（横断面 22 项逐项标章节）、Simple Summary（80 词通俗摘要）、Graphical Abstract 说明 docx |
| BMC (BMC Gastroenterology) | Plain English summary（100-150 词 3 段式）、**"Competing interests" 标题**（不是 Elsevier 的 "Declaration of interest"）、Consent for publication |
| Hepatology 系 | TRIPOD checklist（2022 版 27 条逐条标"已报告/部分/NA/需补"，常见分布 20/4/2/1）、Acknowledgments 段占位 |

## 生成要点与坑
1. **所有不确定信息用 [占位符]**（作者名、单位、邮箱、基金号、ORCID、日期）——绝不编造；真实信息仅当用户明确提供才填（如邮箱 corresponding@example.com 已确认）
2. **论文升版后必须同步所有衍生文件数值**（见 SKILL.md 陷阱 28）：grep Cover letter/Highlights/GA 说明里的关键数字，逐文件替换再重新转 PDF
3. **LibreOffice 转 PDF**：`"C:\Program Files\LibreOffice\program\soffice.exe" --headless --convert-to pdf --outdir <dir> <file.docx>`（git-bash 下中文路径显示乱码但文件正常）
4. **Highlights 字符数**：脚本断言 ≤85 chars/条（MDPI/Elsevier 硬性要求），过长的压缩到 80 左右
5. **Figures.zip**：Python `zipfile.ZipFile(out, "w", ZIP_DEFLATED)`，遍历 `04_图表_矢量/*.svg|*.pdf|*.png`，写入 basename
6. **投稿缺项检查表**：生成一份 docx 逐项核对期刊必需声明（Ethics/Consent/Data availability/Competing interests/Funding/Authors' contributions），发现缺失立即补占位文本

## 生成脚本
- 三个 subagent 分别生成，脚本保留在 `C:\Users\fengq\gen_submission_package.py`、`C:\Users\fengq\glm7_submission_gen.py`、课题3 目录 `build_submission_package.py`（可改参数重跑）
