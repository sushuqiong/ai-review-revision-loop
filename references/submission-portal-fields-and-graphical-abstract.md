# 投稿系统字段（有字数上限）与图形摘要（Graphical Abstract）

两类"最后一公里"交付物：它们都不在正文里，却都在编辑第一眼看到的位置。

---

## 一、字段有字数上限时：先算成本，再决定写什么

实测（JCEH / Editorial Manager 缩写栏）：

> Please enter all abbreviations that have been used in this manuscript at least three or more times.
> Some examples using correct format include - MELD:model for end stage liver disease; AST: aspartate aminotransferase
> **Limit 200 characters**

全量清单 31 项 ≈ **1,075 字符** → 根本放不下。**不要先写全再删**（会被截断且顺序乱），先算成本。

### 成本结构
- 格式照期刊例子：`ABBR:full form`，多项用 `; ` 分隔。
- **冒号后不加空格**（照第一个例子 `MELD:model...`）——每项省 1 字符。
- 单项成本 = `len(缩写) + 1 + len(全称) + 2`。带长全称的最贵：
  `NHANES:National Health and Nutrition Examination Survey` = 59 字符，**一项顶三四项**；
  CHARLS 56、MASLD 54、SVM-RFE 63、ssGSEA 58 同理。
- ⇒ **200 字符 ≈ 最多 4–7 项**。这是硬约束，要向用户说明"不是你不努力"。

### 怎么选（当成背包问题，别凭感觉挑）
把"出现次数"当价值、字符数当重量，跑 0/1 背包（DP over ≤ limit）：

| 目标 | 结果（本轮实测） |
|---|---|
| A 覆盖的出现次数最大 | `AIP; NHANES; FIB-4; BMI; ECM; TG; HBV` = 193 字符，覆盖 206 次 |
| B 项数最多 | 9 项，但全是短项，语义零散 |
| **C 核心语义优先（推荐主答复）** | 结局 AIP + 暴露 FIB-4 + 疾病 CLD/CHB + 主队列 NHANES + 主中介 BMI = **179 字符** |

**交付方式**：一个主答复（贴即可用）+ 2–4 个备选（各标字符数），并说明"被挤掉的不是不重要，是字符不够"。
备一句编辑追问时的应答：

> The submission field is limited to 200 characters; the full list of N abbreviations (each used ≥3 times) is available in the manuscript and can be provided in any format required.

### 计数必须现算，且分清"正文 / 图注"
- 从**用户当前文件**统计（用户会在两轮之间改稿；见 docx-inplace-editing-and-change-marking.md §七）。
- **正文与图注分开数**：本轮 FDR 正文 1 + 图注 4、ssGSEA 2+3、SVM-RFE 2+3 —— 只算正文就掉到 3 次以下。
  多列不会出错，少列会被追问 → 保留在清单里并说明口径。
- 排除三类**不是缩写**的东西：基因符号（CXCL9/COL1A2…）、数据库 accession（GSE84044/GSE83148）、
  拉丁缩写（e.g./vs./et al.）。
- 可选加项（Q1/Q4 四分位标签等）单独列出让用户决定，**不要塞进主答复**。

### 顺手做一次"用了但没定义"检查（高命中率）
逐个缩写 grep 它的全称是否在正文里出现过。本轮真实命中：**AST、ALT 各用 4 次却从未写出全称**
（首次出现在 `FIB-4 = (Age × AST) / (Platelets × √ALT)`，后文只有协变量列表 `ALT, AST`）——
而**期刊给的例子恰好就是 `AST: aspartate aminotransferase`**，说明编辑会拿字段对照正文查。
⇒ 主动报告并给出两行定点修改方案（最小改动：`(Age × AST [aspartate aminotransferase]) / (Platelets × √ALT [alanine aminotransferase])`，
或改协变量句为 `alanine aminotransferase (ALT), aspartate aminotransferase (AST)`）。

---

## 二、图形摘要（Graphical Abstract）

用户拿**自己原来的 GA** 来要求"修改完善，输出新 PDF 随返修稿上传"。要点：**改，不要重画一个风格不同的**。

### 先读原图，读出它的视觉语言
```python
pg = fitz.open(old_ga)[0]
pg.rect                       # 页面尺寸 —— 新版沿用它
# spans 的 font / size / color + get_drawings() 的填充色 → 字体族、字号阶梯、配色
```
本轮读到的：DejaVuSans（说明原图也是 matplotlib 产物）、字号 9–16 pt + 标题 24 pt、
配色 navy `#1C2833` + 三条 phase 色（红 `#C0392B` / 橙 `#D35400` / 绿 `#1E8449`）+ 同色浅底 + 紫 `#7D3C98`。

**沿用原图页面尺寸**（本轮 1166.4 × 576 pt = 41.15 × 20.32 cm）：用户一眼认得出"是我那份改的"，
也避免系统尺寸校验出意外。**沿用原图配色**，改版才不突兀。

### 内容纪律：每一个数字都要在手稿里找得到
- GA 上出现的**每一个数字**都必须能在正文/表里 grep 到（本轮 16 项全部对上）。
- **别用你自己的重算值**：第一版我写了重算的 `−0.169 to −0.097`，而作者原稿（canonical）是
  `−0.173 to −0.093`。这类"表/图用重算值、正文用作者原值"的漂移在同一包里很常见（见
  submission-readiness-adversarial-qa.md §3b）——**GA 必须跟正文**。
- 标点风格跟作者当前手稿：作者已把 en dash 统一成连字符 → GA 也要 `2015-2018`、`Child-Pugh`、
  `immune-fibrotic`。术语也跟手稿（手稿写 `FDR` 就别在 GA 写 `BH-FDR`）。
- **把返修的新结果写进 GA**：本轮在 Phase II 加 `Not explained by the age component of FIB-4` +
  `FIB-4 core β = −0.131`，GA 立刻成为"返修已回应编辑意见"的第一眼证据。
- 不引入手稿没有的数（GA 里的 OR/HR、EMMeans 全部取自正文）。

### 版式骨架（3 phase + 结论带）
- 三层 phase：每格 = 标题条（实色）+ 副标题（灰斜体）+ 3 条要点 + 右下角"产出" + 右上角"成本"。
- **每个 phase 配一个真实数据小图**（本轮：Phase II 两根柱 0.377 vs 0.244；Phase III OR/HR 条形 +
  参考线 1.0）——比纯文字 GA 强得多，而数据本来就在手稿里。
- 底部结论带（紫）：`THE LIPID PARADOX` + 2 行结论 + `Clinical implication` + 机制锚点一句。
- 中文用 `Microsoft YaHei`（本机可用）、拉丁文 Arial；`pdf.fonttype = 42`；最小字号 ≥ 9 pt。
- 输出 **矢量 PDF**（系统通常收 PDF/TIFF/PNG）并**主动问用户要不要 600 dpi PNG/TIFF 备份**。

### 几何自检（必做，但要避开假阳性）
越界判"超出纸张"；重叠判**同一基线上 x 区间相交**；行距判相邻行 y 中心距 ≥ 0.85 × 字号。
**不要把"任两个 bbox 相交"当重叠** —— 中文字体 bbox 天生高，会得到 5–6 处全假的重叠报警，
详见 `submission-readiness-adversarial-qa.md` §7b。
