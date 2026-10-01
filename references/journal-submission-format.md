# Journal Submission Format Elements (对标已发表论文)

用户明确要求论文"写作规范对标已发表论文原文"（如
`C:\Users\fengq\Desktop\GLM7\先复现GLM7相关论文2\01_原始论文\GLM7_paper2.pdf`——
一篇 International Dental Journal 已发表论文）。以下为从该标杆逐项提取、并验证可落到
python-docx 的投稿格式清单，2026-08 三篇论文（Nutrients/BMC Gastro/Hepatol Comm 档）均已按此补齐。

## 标题页（Title page）
- 标题：简洁、无过度修辞（如 "Association Between X and Y: A Cross-Sectional Study"）
- 作者列表：`[Author 1] 1, [Author 2] 2, ...` 数字上标对应单位
- 单位占位：`1 Department..., University..., City, Country`（2-3 条）
- 通讯作者：`* Correspondence: [Name]; [Department...]; [E-mail]; [Tel]`（占位符即可）
- Running title、字数统计、Figures/Tables 计数（**注意与实际数一致**，subagent 常漏改）

## ARTICLE INFO 框（Elsevier 风格，摘要之前）
带边框的表格框：
```
ARTICLE INFO
Article history:
Received: [date]; Received in revised form: [date];
Accepted: [date]; Available online: [date]
```

## 结构化摘要 + Keywords
- 4 段式：Background / Methods / Results / Conclusions（Nutrients 用 Background/Methods/Results/Conclusions）
- 摘要中不得引用文献编号；关键词 4-7 个
- **字数声明要与实际一致**（subagent 常写 289 实际 255——审稿人会查）

## 声明区（Conclusion 与 References 之间）
- **Author Contributions**：CRediT 13 项角色（Conceptualization, Data curation, Formal analysis,
  Investigation, Methodology, Software, Validation, Visualization, Writing – original draft,
  Writing – review & editing 等），每项配 `[Author]` 占位
- **Declaration of interest**："The authors declare no conflict of interest."
- **Funding**：占位 `[Funding agency, grant number]` + funder 免责声明
- **Data availability**：公共数据源（如 NHANES https://wwwn.cdc.gov/nchs/nhanes/、CHARLS https://charls.pku.edu.cn/）
- **Ethics approval**：NCHS 伦理审查 + 书面知情同意；外部队列补自己的批准号
  （CHARLS：Biomedical Ethics Review Committee of Peking University, IRB00001052-11015）
- **Abbreviations 表**：只收正文实际出现的缩写（subagent 曾把未出现的 DII 也列入——删掉）

## 参考文献 Vancouver 规范
- 数字编号 = **正文首现顺序**；重排 refs 列表后必须重查正文引用（本会话两篇都出错）
- 常见错位模式：编号 15（如 NHANES 方法学文献）提前出现在 Vickers(11,12) 之前；
  正文 (7) 应为 (8)、正文 (8,9) 应为 (11,12)、正文 (12) 应为 (9) 等
- 作者：列前 6 位作者 + et al.（"Wang Z, et al." 不符合 Vancouver，须展开）
- 自动修复脚本模式见下方。

## 图/表编号规则
- 图题编号 = 正文引用顺序；图题物理顺序也要与编号一致（否则"图 5 出现在图 2 前"）
- 表题完整（含单位、缩写说明）；脚注说明模型调整变量（M1/M2/M3/M4 逐条列清）
- 删除候选标题残留（"Recommended title (candidate 1 of 3)"、"Alternative titles" 等）

## 矢量图生成（学术风 + 可编辑）
- 每图三格式：`ggsave(file, device="svg")` + `device="pdf"`（cairo_pdf）+ PNG 300dpi（ragg/agg_png）
- 样式：`theme_classic()` 白底无网格、Arial/Helvetica（systemfonts 注册）、图例 bottom、
  轴文字 ≥10pt、黑色细轴线、Lancet 配色（红 #ED0000 / 蓝 #00468B）
- 关键图类型：流程图（participant flow，必须含排除人数）、RCS 曲线（含 CI 带+rug）、
  森林图（含 CI 文本列）、ROC 对比（含 DeLong P）、DCA（含 treat-all/none 参考线）、校准曲线
- 预测模型论文补：LASSO 系数路径图（λ.min/λ.1se 双线）、GMS 分布密度图

## Cover letter + Graphical Abstract（投稿包）
- Cover letter：致编辑 → 标题 → 背景 → 核心发现（真实数值）→ 期刊契合度 → 原创/未一稿多投/
  作者同意/伦理声明 → 署名。**署名邮箱必须向用户确认**（本会话 subagent 自动填了旧邮箱，
  用户更正为 corresponding@example.com）。
- docx 生成后用 LibreOffice 转 PDF：`soffice --headless --convert-to pdf --outdir <dir> <file.docx>`
- Graphical Abstract：matplotlib 学术风 JPG ~1930×984px，暴露→机制箭头→结局 + 底部核心数值统计条

## python-docx 常用技术
```python
from docx import Document
# 读取与全文提取
doc = Document(path)
full = "\n".join(p.text for p in doc.paragraphs)
# 找含图片的段落
is_img = lambda p: bool(p._element.findall(
    './/{http://schemas.openxmlformats.org/drawingml/2006/main}blip'))
# 批量替换 run 文本（保留格式）
for p in doc.paragraphs:
    for r in p.runs:
        if old in r.text: r.text = r.text.replace(old, new)
```
### 图题物理顺序重排（段移动）
```python
body = doc.element.body
# 每图 = [图片段元素, 紧随的图题段元素]；先从 body 移除全部图块
for start_el, end_el in blocks:
    el = start_el
    while el is not None:
        nxt = el.getnext(); body.remove(el)
        if el is end_el: break
        el = nxt
# 按目标编号顺序 addnext 插回（anchor 为第一块前一个段）
anchor = paras[anchor_idx]._element
for num in target_order:
    start_el, end_el = blocks_by_num[num]
    anchor.addnext(end_el); anchor.addnext(start_el)
    anchor = end_el
```

### Vancouver 引用编号自动重映射
1. 从正文提取首现编号序列（regex 抓 `(N)` / `(N, M)`）
2. 建映射 `old -> new`（按首现顺序 1..K）
3. 重排 refs 列表（未引用文献追加末尾）
4. 替换正文：从大到小替换避免冲突；`(old)`、`(old, x)`、`(x, old)` 三种形态都要处理

## 隐私与署名
- 生成投稿材料时 subagent 可能自动填真实姓名/邮箱/单位——**必须逐字核对并让用户确认**
- GitHub 发布技能前 grep 个人信息：`grep -inE "用户名|邮箱|院校|手机|@\."`，为空才发布
- 用户投稿用邮箱（2026-08 确认）：corresponding@example.com
