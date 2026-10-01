# 投稿包格式与一致性审计（整包体检）

来源：2026-10-01 课题2 v22。用户对已"通过终审"的交付包仍指出问题：
「我要补充表呈现完再呈现图片。而且表格不全是三线表」——说明**逐文件的终审不等于整包体检**。

---

## 0. 用户硬规则（反复纠正，最高优先）

1. **补充材料 / 增补文件：全部表在前，全部图在后**，各自带分节标题
   （`Supplementary Tables` → Table S1…Sn；`Supplementary Figures` → Figure S1…Sn）。
   ⚠️ **新增表必须插进表区末尾**（最后一个 S 表之后、图区标题之前），
   **不要**用 `doc.add_table()` 追加到文件末尾——那会落到图区之后。
   文件开头说明文字里的表号范围也要同步（`S1–S13` → `S1–S16`）。
2. **所有交付文件的表格都必须是三线表**（无竖线、无行间线、无网格）。
   目录里任何 docx（含 STROBE / PRISMA 清单表）都在此规则内。
3. **配套文件是主稿的从属物**：每次主稿发生实质变更，必须回头同步
   Title page（词数/表号/running title）、Cover letter（期刊+栏目+分析框架）、
   Highlights、STROBE、Plain English。**最容易被漏的是"分析框架"这一项**。

---

## 1. 三线表判定：看"值"，不看"有没有"

**合格形态**：表级 `w:tblBorders` 各边 `w:val` 为 `none`/`nil`（或干脆无 `tblBorders`），
边框全部由**单元格级 `w:tcBorders`** 承担：
- 首行：`top(single,12)` + `bottom(single,6)`
- 末行：`bottom(single,12)`
- 左右：`nil`（**这一步决定"没有竖线"**）

**两个误判陷阱**：
- ❌ `tblBorders 存在 ⇒ 有边框` —— 必须逐个读每条边的 `w:val`（本项目主稿 7 表全是
  `val=none`，被脚本误报为"有边框"，白折腾一轮）。
- ❌ `tblStyle != '12' ⇒ 不合格` —— 本项目主稿用的是 **style 9**，同样是合格三线表。
  判据只认**边线值 + 有无竖线**，不认样式编号。

**真正的网格表**：`w:tblStyle val="35"`（Table Grid）+ 六边全 `single`。
本项目 9 个表中招：4 个旧表含表级边框，**5 个新加的表误用 `t.style = "Table Grid"`**。

**转换配方**（脚本化，可复用于任何 docx）：
```python
def three_line(tbl):
    tblPr = tbl.find(qn('w:tblPr'))                     # 1) style -> 12
    st = tblPr.find(qn('w:tblStyle')) or OxmlElement('w:tblStyle')
    st.set(qn('w:val'), '12'); tblPr.insert(0, st)
    b = tblPr.find(qn('w:tblBorders'))                  # 2) 删表级边框
    if b is not None: tblPr.remove(b)
    rows = tbl.findall(qn('w:tr'))
    for ri, tr in enumerate(rows):                      # 3) 逐格重建 tcBorders
        for tc in tr.findall(qn('w:tc')):
            tcPr = tc.find(qn('w:tcPr')) or OxmlElement('w:tcPr'); tc.insert(0, tcPr)
            ob = tcPr.find(qn('w:tcBorders'))
            if ob is not None: tcPr.remove(ob)
            tb = OxmlElement('w:tcBorders')
            for side in ('left', 'right'):
                e = OxmlElement('w:'+side); e.set(qn('w:val'), 'nil'); tb.append(e)
            if ri == 0:
                for side, sz in (('top','12'), ('bottom','6')):
                    e = OxmlElement('w:'+side)
                    e.set(qn('w:val'),'single'); e.set(qn('w:sz'),sz); e.set(qn('w:color'),'000000')
                    tb.append(e)
            if ri == len(rows)-1:
                e = OxmlElement('w:bottom')
                e.set(qn('w:val'),'single'); e.set(qn('w:sz'),'12'); e.set(qn('w:color'),'000000')
                tb.append(e)
            tcPr.append(tb)
```

---

## 2. 整包一致性清单（逐项脚本化，别靠肉眼）

| # | 检查 | 判据 |
|---|---|---|
| 1 | 标题一致性 | 每个交付文件的段落+表格里都有新标题、且**旧标题 0 处** |
| 2 | 旧措辞残留 | **用词边界匹配**（见 §3 假阳性） |
| 3 | **过时计数** | Title page 的摘要/正文词数须与主稿**实测**一致（本项目停留在 350 词，实际 341）；Supplementary 表号范围须与补充材料实际表数一致 |
| 4 | **配套文件 vs 最终分析框架** | 本项目 Cover letter 仍写"两期为主分析、N3 为敏感性"，而用户已决定**保留三时期并列** → 属实质不一致，必须改 |
| 5 | 重复段落 | 先**剔除空段**再比；本项目"11/20 组重复"全是空段 |
| 6 | 图表引用 | Table 1..n、Figure 1..m 在正文均被引用 |
| 7 | Tables/ 与主稿 | 逐表逐格文本相等 |
| 8 | 内嵌图 | 主稿/补充材料内 `word/media/*` 与 `Figures/` 源文件 **md5 一致** |

改完任何一处"编号/词数/框架"都要**重跑整张清单**——这类缺陷是级联的。

---

## 3. 程序化检查的假阳性陷阱（本项目全部踩过）

| 陷阱 | 症状 | 正解 |
|---|---|---|
| **子串匹配** | `proves` 命中 `improves`（P014/P077）；`causes` 命中 `because`；`HAJ0` 命中 XML 命名空间里的 `graphic` | 用 `re.finditer(r'\bproves?\b', ...)`；关键词一律**词边界**；命中后**逐条读上下文**再判定，不要把计数当结论 |
| **XML 字符串搜索找图片** | `'graphic' in ch.xml` 把含 `w:graphicFrame` 命名空间的普通段落当成图 | 用元素精确判定：`p.findall('.//' + qn('a:blip'))` |
| **边框存在性** | 见 §1 | 读 `w:val` |
| **重复段落** | 空段被计成重复 | `if p.text.strip()` 先过滤 |
| **过强表述扫描** | `causal`/`causes` 常出现在**否定句**里（"does not establish that BMI causes…"） | 命中后必须读整句；否定用法 = 合格 |

---

## 4. 外部 AI 说"这是笔误"时，先核实代码本/构建脚本

**HAJ0 案例（本项目一次真实的判断纠偏）**：
外部 AI 指出图注里的 `HAJ0 age-branch outcome`"很可能是笔误"。核实数据构建脚本后确认：

> **HAJ0 是 NHANES III 的真实变量**（Section J 年龄分支指示项）：
> `HAJ0 = 1` → 17–74 y，`dx = HAJ9`、`sx = HAJ12`；
> `HAJ0 = 2` → ≥75 y，`dx = HAJ16`、`sx = HAJ17`。

**真正的错误**是把 HAJ0 当成了**结局变量**（图内），
而正文/表注里的 `keyed on the HAJ0 age branch`、`HAJ0 age-branch` 是**准确的技术描述**。

**操作规程**：
1. 收到"某变量名是笔误"的意见 → 先在**数据构建脚本 / 代码本**里 grep 该变量是否真实存在；
2. 区分两种情况：**变量不存在（改名）** vs **变量用错位置（改用法，别删正确提及）**；
3. 修完做三处核对：正文、表注、**图内 PDF 文本**——图内文字常与正文不同步。

---

## 5. Highlights / Plain English 规范

- **Highlights：3–5 条**，每条尽量 ≤120 字符；>200 字符基本必删。
  本项目原 7 条、2 条达 259/256 字符 → 改写为 5 条 × 105–114 字符。
- **Plain English**：无硬性字数，但 >400 词偏长，可主动提示用户是否压缩。
- 二者都必须**同步最新结论口径**（本项目 Highlights 里"只报 P=0.072"的选择性表述要
  改为双口径并列，并补上时间验证/模拟的新结果）。

---

## 6. 用户拒绝"结构大改"时的等效处理

外部 AI 常有一条"把主分析换成 X、把 Y 降为补充"的结构性建议。用户明确
**不做结构大改**时，不要硬改也不要不改，而是把该意见转成**可核查的声明**：

1. 主稿新增独立小节，明确"该比较**不是**某结论的证据"
   （本项目 3.11 节：三层比较是跨数据层异质性评估，**不是时间趋势证据**）；
2. 全文检索被否定的表述（`temporal trend` / `time trend`）计数应为 **0 或仅否定用法**；
3. 同栏目/讨论里列出已具备的支撑（historical sensitivity layer 定位、跨层变量协调映射）；
4. **连带同步** Cover letter / Highlights / Plain English 的同一句口径——
   否则出现"主稿改了、投稿信还在讲两期为主"这类不一致（本项目真实发生）。

---

## 7. 收尾

- 所有修改前的 docx 备份放 `_过程备份/`，**交付夹本身只留投稿文件**；
- 旧版本的过程文件（上一版审查报告等）移出交付夹，别混在投稿包里；
- 每轮改完把"发现的问题 + 修复方式"追加进项目的 `00_进度与交接说明.md`。
