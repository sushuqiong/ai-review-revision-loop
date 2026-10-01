# 图注 vs 图内内容一致性 + 重嵌图片的 extent 同步（多轮审查必查）

来源：2026-09-30 课题2 v21 的两轮对抗性审查。第一轮已逐条回应了外部 AI（GPT6）的全部建议，
第二轮**换角度**审查又抓出 3 个第一轮完全没看见的实质缺陷 —— 本文件记录这三类盲区与修复手法。

---

## 0. 最重要的教训：**审查 docx 正文 ≠ 审查了图**

第一轮结论曾是「变量名已核对，HAJ0 = 0 次」（在 `python-docx` 的段落文本里确实为 0）。
第二轮提取**图件 PDF 内文本**后发现：

```
Fig1.pdf: HAJ0 = 2 处（"HAJ0 age-branch outcome"、"HAJ0 age-branch: 17–74 y use HAJ9/HAJ12..."）
Fig2.pdf: HAJ0 = 1 处（"HAJ0 branch · n = 5,918 (458 dx)"）
```

即：**正文的表注/图注早已改成 HAJ9/HAJ12、HAJ16/HAJ17，但绘图脚本里硬编码的图内文字仍是
笔误 `HAJ0`** —— 而 HAJ0 在 NHANES 代码本里根本不是一个变量（正确应为 HAJ9/HAJ12 与 HAJ16/HAJ17）。
外部 AI 的原始意见就明确点了 Figure 1 图注里的这个笔误，第一轮「已核对」是**假阴性**。

**结论（写进 checklist）**：凡核对"变量名/术语/数字是否统一"，必须**三处都查**：
1. `docx` 段落与单元格（`paragraph.text` / `cell.text`）
2. **图件 PDF 内文本**（`pypdf` 的 `extract_text()`）
3. **绘图脚本源码**（图内文字往往硬编码在 build 函数里）

```python
# 图件文本抽取（本机路径示例）
from pypdf import PdfReader
t = " ".join((pg.extract_text() or "") for pg in PdfReader(pdf_path).pages)
t = " ".join(t.split())          # 归一化空白后再统计
print(t.count("HAJ0"), t.count("age-branched"))
```
⚠️ 反斜杠/正则不要写在 f-string 里（本机 Python 报错），预编译 `re.compile(...)` 后复用。

---

## 1. 图注描述 vs 图内实际数据源（最容易骗过审稿人的一类）

**症状**：图注写得完整、自洽，但描述的**不是**图里画的东西。

**本项目实例（Fig3）**：
- 图注原称 *"displays the pre-specified **LINEAR** age/BMI base models"*，并给出判别样本
  `n = 2,846 / 2,056 / 5,724`；
- 实际图内：**三个主行（P/L/NH3）画的是 matched log10 base 的 ΔAUC 点**，数据来自 v21 匹配重跑，
  样本为**关联样本** `2,885 / 2,092 / 5,918`；只有**面板内小注**才是线性口径值；
- 即图注的"口径 + 样本量"两项都与图内实际不符。

**为什么会发生**：图是**分次迭代**的（v19 线性版 → v21 换成匹配版），
**绘图脚本改了、图注没同步改**；或者图注是按"上一版设计意图"写的。

**核查动作（每张图都要做）**：
1. 从绘图脚本里读出**每个面板的数据来源**（本项目 `auc_val()` 的分支：主行取 `MM`＝v21 匹配源，
   overlay 行取 `md`＝v13 线性源），写成"图内实际 = ？"；
2. 把图注拆成几项声明（口径 / 样本量 / 统计量 / 是否 in-sample），逐项对照；
3. **样本量必须逐个口径核对**：同一张图里混用两套样本（关联样本 vs 判别样本）时，
   图注必须分别给出，不能只给一套。

**修复写法（把三部分都说清）**：
- 三个主行 = matched base（主分析），**关联样本** 2,885 / 2,092 / 5,918；
- 面板内小注 = 线性口径（function-form sensitivity）；
- overlay 行 = 线性形式 + **waist-complete 判别子集** n = 5,141（小于同年龄段关联样本 5,290，因需腰围）；
- 判别样本 2,846 / 2,056 / 5,724 = 线性口径敏感性所用样本。

---

## 2. 正文引用的数值必须在交付包中有出处

**症状**：正文引用了一个具体数值，但**表/图/补充材料里都找不到它**。

**本项目实例**：正文写 *"under the earlier **spline** specification it was **+0.0064**"*，
但 Table 4 只有 **Panel A（matched）+ Panel B（linear）两个面板**，全稿与补充材料均无 spline ΔAUC 表。
核验后该值确有来源（前次分析的判别样本 csv：P/baseA/spline = +0.006396，n = 2,846），**并非编造**，
但读者无法从交付包验证 ⇒ 审稿人一定会问"这个数在哪"。

**核查动作**：把正文里所有形如 `+0.00xx`、`0.xxx (0.xxx–0.xxx)`、`n = …` 的具体值抽出来，
逐个在交付包（主表 / 补充表 / 图注）中找落点；找不到的就要**二选一**：
- 补进表格（工作量大，慎选），或
- **改写正文**：给出同一量在多个口径下的值 + 明确标注各自样本口径，使其可追溯

**本项目采用的修法**（保留信息且可追溯）：
> 同时给出三种函数形式的最大增量（matched +0.0040 / linear +0.0052 / spline +0.0064），
> 并标注各自样本（association sample vs waist-complete discrimination samples）。

---

## 3. 重嵌图片：宽高比一变，`wp:extent` 必须同步

**症状**：替换 docx 内 `word/media/imageN.png` 后图**轻微变形**（被拉伸/压扁）。

**根因**：`word/document.xml` 的 `<wp:extent cx cy>`（EMU）是**显示尺寸**，
留用的是**旧图**的宽高比。新图若因文字增删而高度变化（本项目 Fig3 面板标题加了一行样本量：
2160×1929 → 2160×1965；Fig1 因 `HAJ0`→`age-branched` 文本变长：2143 → 2157），
比例即失配。

**核查与修复**：
```python
from PIL import Image
r = Image.open(new_png).size[0] / Image.open(new_png).size[1]      # 新图真实比例
# 保持 cx 不动，按新比例重算 cy（EMU 整数）
new_cy = round(cx / r)
```
- 用 `zipfile` 就地重写 `word/document.xml`（其余条目原样拷贝），改前先备份 docx；
- 通过 `word/_rels/document.xml.rels` 建立 `rId → media/imageN.png` 映射，
  再按 `<w:drawing>` 块逐个匹配，**不要**按出现顺序盲改；
- 改完把 3 个 extent 的 `cx/cy` 与实际图片比例**再算一遍对照**（本项目 1.0014 / 1.5063 / 1.0992）。

⚠️ 宽高比变化 ≤0.5% 时肉眼看不出，但**变化 1–2% 就会明显**（本项目 Fig3 差 1.8%）。

---

## 4. 绘图脚本重跑后文件名可能带**旧版本后缀**（同步静默复制旧文件）

补充图的绘图脚本常以版本号命名输出：重跑后生成的是 `FigureS1_v19.pdf`，**不是** `FigureS1.pdf`。
按新名去同步 ⇒ 复制到的是**上一版的旧文件**，图内措辞根本没更新（本项目实测：
v22 目录里 FigureS1 仍是旧的 "gallstone diagnosis history"，而 v21 目录里 `FigureS1_v19.pdf` 才是新的）。

**规程**：
1. 重跑绘图脚本后先 `ls -lat <figdir>/ | head` 看**实际生成的文件名与时间戳**，不要假设文件名；
2. 若脚本会带版本后缀，先重命名（`FigureS1_v19.* → FigureS1.*`）再同步到交付目录；
3. 同步后**回读图内 PDF 文本**确认改动生效（只看文件时间戳不够——复制也可能失败）。

## 5. 主稿与补充材料**各自内嵌图**，必须分别重嵌 + md5 校验

一个交付包里往往有两个 docx 各带自己的图，映射不同名（易搞混）：

| docx | media 名 | 对应图 |
|---|---|---|
| 主稿 `01_Manuscript.docx` | `word/media/image2.png` / `image3.png` / `image4.png` | Fig1 / Fig2 / Fig3 |
| 补充材料 `04_Supplementary Materials.docx` | `word/media/image1.png` / `image2.png` / `image3.png` | FigureS1 / S2 / S3 |

- **媒体名会重复**（两个 docx 都有 `image2.png`，内容完全不同）⇒ 每个 docx 单独处理，别复用同一个映射；
- 关系在 `word/_rels/document.xml.rels` 里，用 `Id="rIdN" ... Target="media/imageN.png"` 定位，
  再按 `<w:drawing>` 块匹配 `r:embed="rIdN"` 改 `wp:extent`；
- **重嵌后逐字节 md5 校验内嵌图 vs `Figures/`**（本项目 6/6 一致）：
  ```python
  a = hashlib.md5(zipfile.ZipFile(docx).read("word/media/imageN.png")).hexdigest()
  b = hashlib.md5(open(os.path.join(FIG, "FigN.png"), "rb").read()).hexdigest()
  assert a == b
  ```
  这条能同时抓住"没嵌进去""嵌了旧图""嵌错文件"三类问题——**比看图更可靠**。

---

## 6. 多轮审查的"角度设计"（避免第二轮只是重复第一轮）

两轮审查**必须换输入、换视角**，否则第二轮的边际发现为零。
本项目两轮各自的角度：

| 轮次 | 角度 | 代表性发现 |
|---|---|---|
| 第一轮 | 逐条回应**外部 AI 的 numbered list**（GPT6 的 8 类意见） | 概念表述过强、M4 函数形式、变量名、L 层自由度、预测色彩 |
| 第二轮 | **数值自洽性 + 交叉引用 + 因果语言 + 图内数据源** | 图注≠图内数据源、正文引用值无出处、图内 HAJ0 残留 |

第二轮的机器化检查清单（都很容易脚本化，且真能抓到东西）：
1. **P 值 vs 95% CI 一致性**：CI 含 1 ⇔ P>0.05；逐行比对（本项目 12 个 OR 全对口）。
2. **CI 的 log 尺度对称性**：`|ln(OR/lo)|` vs `|ln(hi/OR)|`，偏差 >5% 标记（本项目 24 个 CI 全过）。
3. **样本量序列单调性**：流程图各步必须递减（本项目三层序列全过）。
4. **摘要 vs 正文 vs 表格的三处一致**：关键数值逐个 count（本项目发现过"摘要只引敏感性口径、
   与主分析口径不一致"的实质错误）。
5. **因果语言扫描**：`causes / causal / leads to / attributable to` —— 命中的若是**否定用法**
   （"does not establish that X causes…"）则为合格，需人工判读，不能只看 count。
6. **占位符残留**：`TODO / TBD / PLACEHOLDER / [Author / FIXME`。
7. **图内数值 vs 表格数值**：图内不得残留被替换掉的旧口径数值（本项目曾要求 Fig2 不得出现
   旧线性 M4 值 1.326 / 0.826 / 1.244）。
8. **图注声明的样本量 vs 图内实际数据源**（见 §1）。

**判读纪律**：把"断言失败"与"真实缺陷"分开。本项目绘图脚本的自检会报 15–16 个
`MISSING / 缺失保留文字`，逐项排查后全是**断言过期**（把"坐标轴刻度值"当文本去 PDF 里找、
或旧版面板标题的保留断言未同步），**图本身正确** —— 但必须在报告里逐条说明"为何是断言问题"，
不能笼统说"是误报"。

---

## 7. 收尾自检（本轮新增项）

- [ ] 图内文本已抽取核对（变量名、术语、样本量），不只看 docx 正文
- [ ] 每张图的图注逐项对照图内实际（口径 / 样本量 / 统计量）
- [ ] 正文每个具体数值都能在交付包中定位
- [ ] 重嵌图片后 `wp:extent` 宽高比与实际 PNG 一致
- [ ] 两轮审查角度不重复，第二轮有独立发现（若为零，说明角度没换）
- [ ] 断言失败项已逐条定性（真实缺陷 or 断言过期），并写入报告
- [ ] `Tables/` 独立文件与主稿表格**逐行一致**（本轮复核 7/7 一致）


---

---

## 8. 图件措辞复核的最小闭环（每轮改稿都跑）

1. 抽取**每张图（含补充图）**的 PDF 文本：`Fig1-3.pdf` + `FigureS1-3.pdf`
2. 与正文的**权威措辞**逐项比对（本项目：`gallstone diagnosis history` → `self-reported physician-diagnosed gallstone history`）
3. 命中旧措辞 → 回到**绘图脚本**改（图内文字往往硬编码，正文改了脚本没改）→ 重跑（脚本自带 overlap/bounds/margin 自检须为 0 problems）
4. 同步 → 重命名坑（§4）→ 分别重嵌两个 docx（§5）→ **分辨率 + md5 双重校验**（§9）

---

## 9. 内嵌图"看起来嵌了"≠"真的嵌了"：必须比对**像素尺寸**（v22 终审抓出）

**症状**：`Figures/` 里明明是 2160 px 高清图，但**主稿里的图其实是低清旧版**。本项目终审实测：

```
word/media/image2.png (Fig1): docx=1342×1340   Figures/=2160×2157   ← 低清旧版！
word/media/image3.png (Fig2): docx=1135×753    Figures/=2160×1434   ← 低清旧版！
word/media/image4.png (Fig3): docx=2160×1965   Figures/=2160×1965   ✓
```

**为什么会这样**（分次替换的必然产物）：
1. 早前一次重嵌时 `Figures/` 里放的还是低清版 ⇒ 嵌进去的也是低清版，**当时 md5 校验通过**（两边都是旧图，正好一致）；
2. 后来又为"改一处图内措辞"重跑绘图脚本、把**高清版**同步进了 `Figures/`；
3. **但没有人再重嵌 docx** ⇒ 主稿里一直躺着重嵌前的低清图。

⇒ **"md5 一致"只在同一时刻有意义；一旦 `Figures/` 被替换过，docx 必须重新嵌一次。**
（**为什么会反复变回旧版**：见 §10 —— python-docx 每次 save() 都会重建 package 并覆盖 zip 级替换。）

**核查动作（终审必跑，且要看尺寸不看字节）**：
```python
from PIL import Image
import io, zipfile, hashlib
z = zipfile.ZipFile(docx)
for media, fig in [("word/media/image2.png", "Fig1.png"), ("word/media/image3.png", "Fig2.png")]:
    a = z.read(media); b = open(os.path.join(FIG, fig), "rb").read()
    ia, ib = Image.open(io.BytesIO(a)), Image.open(io.BytesIO(b))
    print(media, ia.size, ib.size,
          "md5同" if hashlib.md5(a).digest() == hashlib.md5(b).digest() else "md5异")
```
**判据**：`ia.size == ib.size` **且** md5 相同才算通过。**尺寸不等 = 内嵌的是旧版。**

**修复**：按 §3 的方式重嵌（同时同步 `wp:extent` 宽高比）+ 重新做尺寸/md5 双校验。
本项目修复后 3 张图均 2160 px 宽、md5 一致。

⚠️ **改图内措辞（哪怕只改一个词）也必须走完整条链**：重跑 → 同步 → 重嵌 → 校验。
"只改了文字没改数据"**不**代表可以不重嵌。

⚠️ **元教训**：脚本打印"嵌入 image2.png ← Fig1.png"只是**声明**，不是**证据**。
证据 = 从 docx 里**读出来**并与源文件比对（尺寸 + md5）。
所有"已重嵌 / 已同步 / 已完成"的结论，都要用这种方式复核一遍 —— 本项目正是一次"报成功但没生效"
的重嵌，直到终审比对尺寸才暴露。


---

## 10. ⚠️ 根因补充：python-docx 的 save() 会**还原** zip 级图片替换

**症状**：图片替换后 md5 校验通过 ✅，但随后又跑了一次"字体统一/文字修改"脚本（用 python-docx 打开+保存），
**图片悄悄变回旧版**，而脚本日志毫无异常。本轮实测踩中两次。

**根因**：`python-docx` 的 `doc.save()` 会**重建整个 OPC package**。
用 `zipfile` 直接替换 `word/media/*.png` 的改动不属于 python-docx 的文档模型，
一旦用 python-docx 重新保存，就会以**它打开时读到的内容**为准写回。

**正确顺序（务必遵守）**：
```
① 用 python-docx 完成全部文字/样式/结构/表格修改（可反复保存）
② 【最后一步】再用 zipfile 替换 word/media/*.png + 同步 wp:extent
③ 立即校验内嵌图 md5 与 Figures/ 源文件一致
④ 此后不再用 python-docx 打开该文件（否则回到 ① 之前的状态）
```

**每次 python-docx 保存后都要复检**（本轮就是靠这条抓回来的）：
```python
import zipfile, hashlib, io
z = zipfile.ZipFile(docx)
assert hashlib.md5(z.read("word/media/image3.png")).hexdigest() == \
       hashlib.md5(open("Figures/Fig2.png","rb").read()).hexdigest()
```
更稳的判据是**比对像素尺寸**（旧版往往分辨率更低，如 1342×1340 vs 2160×2157）：
```python
from PIL import Image
print(Image.open(io.BytesIO(z.read("word/media/image2.png"))).size)   # 应为高分辨率
```

**推论**：任何"先改文字、后换图"的流水线，都必须把换图排在**最后**；
若交付前还有别的脚本要动正文，**换图之后就别再动了**，或者把换图脚本固定为收尾步骤重跑一次。

**延伸**：同理，其他"绕过 python-docx 直接改包内文件"的操作（如替换 header/footer/media、
改 `word/_rels/document.xml.rels`）都会被下一次 `doc.save()` 覆盖 —— 统一排到最后。

**本会话实际复发 2 次**：字体归一、间距归一各触发一次（旧版低清图 1342×1340 又回到 docx 里，而脚本日志毫无异常）。
⇒ 当作**硬性收尾工序**执行：任何动用 python-docx 的改动做完后，**换图脚本固定作为最后一步重跑一次**，
并立刻用 §9 的**像素尺寸**判据复检（不要只看 md5 —— 若 `Figures/` 也恰好是旧图，md5 会"一致"而假通过）。


---

## 11. ⚠️ 最容易漏的投稿硬规范：图表编号**必须等于正文首次提及顺序**

> **完整重编号流程见** `references/figure-table-renumbering-and-order-compliance.md`
> （映射构造与置换环、范围/并列形式的坑、块重排、双向交叉引用、断言方法、已提交后的补救）。
> **字体/间距不一致的模板化修复见** `references/journal-template-format-normalisation.md`。

**事故记录（v22，已提交后才被用户发现）**：
主稿正文首次提及顺序是 `1 → 7 → 6 → 2 → 3 → 4 → 5`，而表编号是 `1..7` 固定顺序 ⇒ **Table 7/Table 6 在 Table 2 之前被引用**。
补充表更严重：提及顺序 `S13 → S2 → S11 → S1 → S7 → S4 → S10 → S6 → S3 → S12 → S5 → S9 → S14 → S16 → S15 → S8`，
等于 **S1–S16 几乎全部需要重编号**；补充图也需 S1↔S2 对调。用户已提交 Frontiers 后才发现。

**为什么会漏（真正的教训）**：
1. 检查清单里只有"**引用完整性**"（每个图表是否被引用），**没有"顺序性"**（编号是否随首次提及递增）；
2. 前几轮改动**插入过新章节**（3.10–3.13）与新图表（S14–S16），**改变了提及顺序**，但只查了"新引用是否悬空"，没做全量顺序复核；
3. 旧编号在更早版本就已乱序（S1–S13），被**当作既有事实沿用**，没有质疑编号体系本身；
4. 自动检查脚本都是"计数器"式（出现次数/一致性），**从未写过顺序性断言**。

⇒ **"遗留问题 0"只等于"我的清单内都过了"，不等于"稿件没有规范问题"。不要用这个结论给用户虚假安心。**

**必做检查（每次交付前，必跑）**：
```python
import re
from docx import Document
def first_mentions(paras, pat):
    out = {}
    for i, t in enumerate(paras):
        for m in re.finditer(pat, t):
            out.setdefault(int(m.group(1)), i)      # 首次出现段落号
    return out

doc = Document(path); paras = [p.text for p in doc.paragraphs]
for label, pat in [("Table", r'\bTable\s+(\d+)(?![\dS])'),
                   ("Table S", r'\bTable\s+S(\d+)'),
                   ("Figure", r'\bFigure\s+(\d+)(?![\dS])'),
                   ("Figure S", r'\bFigure\s+S(\d+)')]:
    fm = first_mentions(paras, pat)
    order = [k for k, _ in sorted(fm.items(), key=lambda kv: kv[1])]
    print(label, order, "OK" if order == sorted(order) else "❌ 乱序，需按此顺序重编号")
```

**修正动作（乱序时）**：
1. 由 `order` 生成 **旧编号 → 新编号** 映射（`{old: new}`）
2. **先替换长编号再替换短编号**（避免 `S1` 误匹配 `S1x`；用 `\bTable\s+S(\d+)(?![\d])` 之类边界）
3. 同步更新：正文引用、表/图**标题本身**、补充材料内的标题、独立 `Tables/` 文件名、图件文件名
4. **重跑上面的顺序检查**，直到四类（Table / Table S / Figure / Figure S）全部 `order == sorted(order)`
5. 表内若有跨表引用（如 "as in Table S3"），一并检查

**教训一句话**：编号顺序是**审稿人第一眼就会看**的投稿常识项，**必须写成脚本断言**，不能靠"逐项读一遍"来保证。
