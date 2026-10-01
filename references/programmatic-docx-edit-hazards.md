# 程序化 docx 编辑的事故目录（改稿类任务最高频错误源）

> 本文件是 `ai-review-revision-loop` 的支撑材料。**动手批量改稿前先读它。**
> 结论先行：多轮迭代中，脚本/subagent 批量改 docx **引入的新错常多于修掉的错**。下列 6 类反复复发，全部已在本项目（NHANES 三周期稿 v13→v19）实际发生。

---

## §1 全局替换（blanket find-replace）——最严重

**症状**：同稿存在**字面相同、语义不同**的值，全局替换一次污染全稿。

**实例**（v18→v19 实际发生，被审查者抓出）：
- 存在两个不同的 L 层样本：**关联样本 2,092（236 dx）** 与 **判别/腰围完整样本 2,056（232 dx）**。
- 为统一"L 层口径"执行全局 `"2,056" → "2,092"` → **20+ 处把判别样本也改了**，导致：
  - Figure 1 图注句内自相矛盾（写 2,092 却称"比关联样本少 36 人"）
  - 补充表出现 **分析样本(n=2,092) > 设计框(n=2,057)** 的逻辑不可能
  - 该错误被修回后，**又一次从备份恢复时被带回**（同一错犯三次）

**判据/规则**：
- **禁止**无条件全局替换。
- 替换前 `text.count(old)` 与"预期处数"比对，不符即停。
- 逐处判断语境；改完**逐处输出表**：`位置 | 改前 | 改后 | 判据`。
- 对"同字面不同义"的候选值，先建立**语义映射**（哪个值属于哪个实体），再按实体定向替换。

**自检**：替换后重新扫描**被替换串**是否为 0，同时**被保留语境**仍存在。

---

## §2 引用标记插在"第一个句号"→ 切开小数

**症状**：为补交叉引用，用"在关键词后第一个 `.` 处插入"的启发式 → 命中小数内部。

**实例**：
```
改前：the M4 per-SD OR was 0.826 (0.688–0.991; P=0.041)
改后：the M4 per-SD OR was 0 (Table S11).826 (0.688–0.991; P=0.041)   ← 数字被切开
```
同类：`age 26 (Figure S1).0/52.0/74.0`、`weighted 2 (Figure S2).5%`。

**规则**：
- 插入点**必须是句末**，或"`.` + 空格 + 大写字母"的句边界。
- 用正则找边界：`\. (?=[A-Z])`；**禁止**直接用 `str.find('.')`。
- 插完自检两条正则，必须为 0 命中：
  - `\)\.[0-9]`（引用后紧跟小数）
  - `\.[0-9]+\s*\((Table|Figure)`

---

## §3 "只改半个分句"→ 段内自相矛盾

**症状**：同一段内前后两个分句给**同一个量**的两个值；只改一处，另一处成为硬矛盾。

**实例**（v19 被审查者抓出）：
> "Pooling the three periods … gives **1.012** on the own-SD scale and **1.014** on the common-increment scale, the L-period quantity reported in Panel B of Table 6 … The adjustment set therefore accounts for only a small part … (period-specific fit 0.830 versus 0.809; **pooled fit 1.020 versus 0.990**), whereas most of it reflects the estimation strategy"

前句已统一为 1.012/1.014，后句括号里仍留变体模型的 **1.020** 与 **0.991/0.990**。

**规则**：
- 改一个数值前，先在该段 `count()` 该值**及其所有相邻/同义值**。
- 改完**通读整段**（不是通读被改的那一句）。
- 段落级"兄弟值"清单示例：`1.012 / 1.014 / 1.018 / 1.020 / 0.991 / 0.990` 同属"受约束合并模型 L 期 OR"。

---

## §4 builder / 内容模块与交付稿脱钩 → 覆盖交付稿

**症状**：最终交付稿是**直接 patch docx** 得到的；builder 的 `_ms_content_vNN.py` 仍是旧版。此时运行 `_build_docx_vNN.py` 会**用旧内容静默覆盖交付稿**。

**实例**：核查词数时误跑 builder（内容模块为打包前版本：摘要 342 词 / 8 表），交付稿被覆盖成旧版（BMC 打包成果全失）。靠 `_bak/v18_pre_bmc/` 恢复。

**规则**：
- 交付前在 README 明写：
  > ⚠️ 构建链已与交付稿不同步。**除非要重建，不要运行 `_build_docx_vNN.py`**。
- 给出**有序恢复配方**（照抄可跑）：
  ```bash
  # 1) 恢复到"直接编辑前"的状态
  cp _bak/<阶段>/论文_全文_投稿版_vNN.docx 05_论文投稿/
  cp _bak/<阶段>/*.docx 04_投稿材料/
  # 2) 依次重放各 fix 脚本（顺序重要）
  python _vNN_fix1.py && python _vNN_fix2.py && python _vNN_fix3.py && python _vNN_fix4.py
  # 3) 终验
  python _vNN_FINAL.py     # 必须输出 未通过项: 0
  ```
- 每阶段写 fix 脚本时**自带备份**（`shutil.copy2` 到 `_bak/`），使回滚点可枚举。
- 清理时**不要删**fix 脚本与内容模块——它们是恢复配方的组成部分。若确要移走，同步更新配方路径。

**相关坑**：内容模块可能有多版本依赖链（`_ms_content_v18.py` 内 `import _ms_content_v17`）。清理时把上游模块移走会导致 builder `ModuleNotFoundError`。**要么保留整链，要么明确声明不可重建。**

---

## §5 词数/计数口径不一致

**症状**：同一稿在不同文件出现多个"正文词数"（本项目同时存在 6,999 / 7,100 / 7,260 / 7,350），因为未声明口径。

**规则**：
- 选定**一个**口径并在**每处引用词数的文件**里写明，例如：
  > Main text word count (Introduction through Conclusions, **excluding section headings, table titles and figure legends**): 7,260 words.
- Title page / Cover letter / 正文声明**三处同值**；摘要词数同理（区分"含结构标签"与"不含"）。
- 口径改动后，**同步所有引用处**（本项目有 Title page 2 处 + Cover letter 1 处）。

---

## §6 "看似同源、实则不同模型"的数值并列

**症状**：同一段并列两个数，读者以为同源，实则来自不同模型设定。

**实例**：Table 6 Panel B 的 L 期 OR = **1.012 / 1.014**（权威源 `01_数据/v17_pooled_and_T7.txt`，n=10,895 / cases=996 / degf=89，race 4 类 + 分类 PIR）；而正文另引 **1.018 / 1.020**（来自 v18 变体，**数值 PIR**）。正文曾把后者与前者写成"同一量"。

**规则**：
- 任何引用数值，先 `grep` 锁定 `01_数据/*.txt` 的**权威源**，逐值比对 F/P/OR/CI/n/degf。
- **变体模型的数一律删除**，不在同一段并列；确有必要则单独注明"另一参数化下为 X"。
- 每个数值问一句："这个数出自哪一份冻结输出？"

---

## §7 领域专用陷阱：样条"结点数"的两种惯例

**这是最隐蔽的一类——代码正确、术语错误。**

| 惯例 | 写法 | 3 个结点时的含义 | 非线性 df |
|------|------|------------------|-----------|
| 内结点惯例（R `splines::ns(x, knots=)`） | 指定**内结点** | 3 内结点 + 2 边界 = **5 总结点** | 基列 4 = 1 线性 + **3 非线性** |
| 总结点惯例（Hmisc `rcspline.eval(nk=)` / `rms::rcs(x, 3)`） | 指定**总结点数** | 3 总结点 | 返回 **nk−2 = 1** 个非线性项 |

**实例**：代码用 `ns(z, knots = q10,q50,q90)` → rank 15→18（+3），自洽；但稿中写 "**3 knots**"（读者按总结点惯例理解为 1 个非线性 df）→ 审查者判为"结点数/模型秩/非线性 df 不一致"。

**规则**：
- 全稿统一写 **"three interior knots at the 10th, 50th and 90th percentiles (five knots in total), giving three non-linear degrees of freedom"**，或统一写总结点惯例并给出对应的 1 df。
- **两套惯例不得混用**：若敏感性分析用了另一惯例（如 `ns(df=2)` = 1 个非线性 df），必须在同一处**显式标注"the three-total-knot (Hmisc) convention"**。
- 报告非线性检验时**同时给出**：实际内结点位置、边界结点、基列数、被检系数、分子 df、分母 df（默认残差 df 与显式设计 df 两种）。
- 分层样本的**设计自由度可能小于样条模型秩**（本例 L 层 degf=15，样条秩 18 → 默认残差 df = −2 → 默认检验 **不可估计**）。此时须显式令分母 df = 设计 df，并**如实写明该层检验受设计自由度限制**；**不要**据此宣称"无偏离线性"，也不要据负残差 df 宣称模型无效。

---

## §8 批量编辑后的强制自查（最小可执行集）

```python
# 1) 引用切开数字
assert not re.search(r'\)\.[0-9]', full)
assert not re.search(r'\.[0-9]+\s*\((Table|Figure)', full)
# 2) 段内兄弟值（把每轮改过的值及其同义值列进来）
for para in paras_edited:
    sibs = [v for v in SIBLINGS if v in para]
    assert len(sibs) <= 1, (para[:80], sibs)
# 3) 引用首现序严格递增
order = first_occurrence_order(main_text)
assert order == sorted(order), [ (order[i],order[i+1]) for i in range(len(order)-1) if order[i+1]<order[i] ]
# 4) 废弃串清零（每轮追加）
DEPRECATED = ["0.974","0.588","1.752","93.4","caliber","calibre","1.018 on the own-SD","settled"]
assert sum(full.count(d) for d in DEPRECATED) == 0
# 5) 交叉引用完整
assert all(f"Table S{i}" in full for i in range(1, N_S+1))
```

**原则**：每轮把新废弃的字符串**追加**进 `DEPRECATED`，让清单随迭代增长；终验脚本跑它，输出"未通过项: 0"才算收工。

---

## §9 流程层教训

- **"宣布完成"之前必须重扫**：本项目每一轮"我修完了"之后，独立审查者都能找到新错。**修完 → 立刻重扫 → 再报完成**。
- **审查者也会误报**：本项目出现过假阳性（把 Table 5 的 14 行误计为 12 行、把合法 CI 上界 `0.991` 当旧值、把合法比值 `1.020` 当残留）。**每条审查发现都要先独立复算/溯源再改**，不要照字面改——照字面改会引入新矛盾。
- **修一半 = 制造新矛盾**：只改被点名的位置而不改其"兄弟位置"，是 §3 的通例。审查意见给出的"建议处理"往往是**多处**，要全扫。
