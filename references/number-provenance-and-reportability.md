# 数字溯源与「不可报告」的格子（Number provenance & reportability）

来源：课题2 GLM7×胆石症 **v17 轮**。主稿经历了 v15→v16→v17 三轮批量编辑，
在一个**已通过多轮一致性扫描**的稿子里，仍浮现出一类全新缺陷：
**一个数字在稿中被引用四处，却没有任何输出文件能产生它。**

本文件处理「数字层」的四件事：从哪来 / 能不能报 / 口径变了怎么办 / 图是不是真的重制了。

---

## 1. 铁律：稿中每个数字都必须能落到一个 **landed 输出文件**

**症状（本轮实测最严重的一类）**

L 层非线性检验的 P 值 **0.974** 出现在：正文 §3.4、Table 3 脚注、Cover letter、README。
但 `01_数据/` 下两个相关输出文件记录该检验为 **NA**（`v17_L_unified_extras.txt` 与 `v17_T7_nl.txt`）。

**溯源结果**：0.974 **只存在于硬编码字符串里** ——
`_ms_content_v17.py`（内容模块）与 `_make_submission_v17.py`（投稿包生成器）。
即：某次会话把一个数写进了模板，**没有落盘任何能重算出它的输出**。

**同源问题（前一轮）**：v16 报的 L 层 dx/comb 非线性 **P=0.031 / 0.012** 同样不可复现 ——
全代码库与全输出文件里都找不到这两个值的产生过程；其中 0.031 与 v16 同段所报的
**L 层 M4 关联 P 值数值相同**，疑为句内误抄。

**通用判据（三条任一命中即须核查）**
- 该数字**在任何 `.rds/.txt/.tsv` 里都搜不到**，只出现在 docx / 内容模块 / 生成器脚本中；
- 该数字**与同段其他数字量级/来源不匹配**（如"非线性 P"恰好等于"关联 P"）；
- 该数字**只能由某次未留档的交互式会话**产生（无脚本、无 sink）。

**可复用检查**
```bash
# 稿中出现的每个"孤立"数值，反向搜全部输出文件
for v in 0.974 0.031 0.012; do
  echo "== $v =="; grep -rl -- "$v" 01_数据/ 02_复现代码/*.R 02_复现代码/*.py 2>/dev/null || echo "  无输出文件产生此值"
done
```
```python
# 正向：把稿中所有小数/百分数抓出来，标注是否在输出文件中出现过
import re, pathlib
nums = set(re.findall(r"\b\d+\.\d{2,4}\b", manuscript_text))
outs = "\n".join(p.read_text(errors="ignore") for p in pathlib.Path("01_数据").glob("*"))
orphan = sorted(n for n in nums if n not in outs and float(n) not in
                {float(x) for x in re.findall(r"\d+\.\d+", outs)})
print("无输出支撑的数值:", orphan)
```

**处置（两条路，二选一，不许含糊）**
1. **补落盘**：重跑并"**务必写文件**"（`sink()` / `writeLines()` / `saveRDS()`），
   把结果写进 `01_数据/`，在稿件中标明数据源与脚本路径；
2. **删掉**：改为如实表述并把"为什么不能给这个数"讲清楚（见第 2 节）。

⇒ 给 subagent 派分析任务时，指令里要**显式写死**：
> **务必把结果写成文件（sink / writeLines / saveRDS），不要只打印到控制台。**

（本轮之所以出现 0.974，一部分原因就是早期任务只要求"打印结果"，控制台输出未被留档。）

---

## 2. 「不可估计」是一个**合法结论**，不是待填的空

**机制**：`survey::regTermTest` 默认（`df = NULL`）用**模型残差自由度**作分母；
若 `rank(model.matrix) − 1 > degf(design)`，残差自由度为**负** → `pf()` 返回 `NaN` → **P = NA**。

**实测（L 层，`degf(design) = 15`）**

| 口径 | 结局 | 样条规格 | rank(nl) | `df.residual` | 默认检验 | **显式 `df = degf(design) = 15`** |
|---|---|---|---|---|---|---|
| 2,092 | dx | RCS 3 内结点 | 18 | **−2** | **P = NA（不可估计）** | F=2.486 **P=0.1003** |
| 2,092 | comb | RCS 3 内结点 | 18 | −2 | P = NA | F=2.182 **P=0.1326** |
| 2,056 | dx | RCS 3 内结点 | 18 | −2 | P = NA | F=2.797 P=0.0761 |
| 2,056 | comb | RCS 3 内结点 | 18 | −2 | P = NA | F=2.789 P=0.0766 |

**关键推论**：该层**唯一可估计的设置是显式 `df = degf(design)`**。
所以如果你手上有一个"默认设置下"的 P 值，**它不可能来自默认路径** —— 立刻回头查它从哪来（见第 1 节）。

**写法（三段式，可直接改用）**

> In the L series the non-linearity test is **not estimable** with the default survey residual degrees
> of freedom (the restricted-cubic-spline model has rank 18 under only 15 design degrees of freedom,
> giving a negative residual df). **With the denominator degrees of freedom set explicitly to the
> design df (15), the test gave F = 2.49 (P = 0.100) for diagnosis history and F = 2.18 (P = 0.133)
> for the combined definition.** Accordingly no period showed a departure from linearity, and the
> older value previously reported for this layer was **not reproducible and has been removed**.

**要点**
- **如实报 NA/不可估计**，并解释是"检验参考分布的选择问题"（呼应 `survey-design-df-and-weighting.md` §1.3），
  **不要**写成"模型失效/超出可用信息"。
- 需要报数时用**显式 df** 并注明；不需要报数时，说"未检出偏离线性"即可，**不要塞一个无来源的 P**。
- 与其它层并列时要说明**口径差异**（P/N3 用默认即可，L 必须显式设 df），
  否则读者按默认设置复现不出同一个数。

---

## 3. 样本口径变更 → **重算**，不要在表里补单元格

**症状（本轮高危）**：Table S3 Panel C 的 L 列，**只有"最终分析样本"一个单元格被改成 2,092**，
而同列其余数值仍是旧口径 2,056 算出来的：

| 单元格 | 表内值 | 新口径应有值 | 判定 |
|---|---|---|---|
| 最终分析样本 | 2,092 ✓ | 2,092 | 已改 |
| 入组率 | 0.8521 | **0.8670**（= 2,092/2,413） | 未改 → **与 n 自相矛盾** |
| 方案 c 入组率 | 0.7476 | **0.7607**（= 2,092/2,750） | 未改 |
| ESS（IPW） | 1,271.0 | **1,290.2** | 未改 |
| M3 / M4 OR | 1.415 / 0.833 | **1.425 / 0.827** | 未改 |

⇒ 审稿人一眼看出「**名不副实的'三人对齐'**」——本轮最核心的卖点在 L 层不成立。

**根因**：口径变更被当成"换个数字"，实际它改变了**整列**（选择模型、权重、ESS、OR、CI 都要重算）。

**配方**
1. 口径一变（关联样本 2,056 → 2,092），**为该口径重跑整条链**：
   选择模型 → p̂ → 权重 → ESS → 加权 OR/CI → 截断敏感性 → bootstrap。
2. **只改一个格是不可接受的做法**；若时间不够，宁可**整列不动 + 显式声明该列是旧口径**。
3. **加派生恒等式断言**（最省事的自检）：
   ```python
   assert abs(entry_rate_a - n_analysis / n_model) < 1e-3   # 入组率
   assert abs(entry_rate_c - n_analysis / n_target_c) < 1e-3
   ```
   本轮即由 `2092/2413 = 0.8670 ≠ 0.8521` 暴露。
4. **同一口径变更要顺着所有下游走**：主表 → 补充表 → 图 → 图注 → 投稿包 → README。
   实测下游清单：Table 1/2/3/6/7、Figure 1/2、FigureS2/S3、Table S2/S3/S5/S11、Cover letter。

---

## 4. 补充材料是「残余汇聚处」——尤其当工作被拆给并行 subagent 时

**本轮现象**：主稿正文、主表、主图（Fig1/Fig2、Table 1/2/3/6/7）**逐格核对全对**；
而问题**全部集中在补充材料**：FigureS1/S2/S3 未重制 + 两张补充表口径错位。

**两条可操作的检测**

**(a) 图件是否真的重制过 —— 比 md5**

若一张图**显示的数值变了**，它的文件 md5 **必须变**。跨版本比 md5 即可发现"漏制"：
```python
import hashlib, os
def h(p): return hashlib.md5(open(p, "rb").read()).hexdigest()[:12]
for f in ["FigureS1", "FigureS2", "FigureS3"]:
    prev, cur = f"../课题2v16/03_图表/{f}_v16.png", f"03_图表/{f}_v17.png"
    print(f, h(prev), h(cur), "未重制!" if h(prev) == h(cur) else "已更新")
```
- 实测：三张补充图 v16↔v17 **md5 完全相同** → 本轮根本没重制（而主表已换口径）。
- ⚠️ **"md5 相同"不总是错**：若该图**显示的数值本就没变**（如 Fig3 用未变的判别样本），
  相同才是对的。判据是「**它显示的数值有没有变**」，不是「md5 有没有变」。
- 重制后仍须**重嵌入 docx**（见 `audit-defect-fix-recipes.md` 配方 2），并回读 md5 确认
  「与新图一致 = True」且「与旧图不同 = True」。

**(b) 一致性扫描必须覆盖"所有交付物"，不能只扫主稿**

主稿干净 ≠ 稿包干净。收尾扫描的清单要**显式列出全部 docx + 全部图 + 全部补充表**，
并把**每个 subagent 任务的产物都纳入**——残余最常落在**预算最先耗尽**的那个任务里。

**排版提示**：本轮把工作拆成「主稿修订」「图+补充材料」两个并行任务，图任务先耗尽预算 →
图成了残余。⇒ 并列任务时，**先给"图与补充材料"这类下游产物留足预算**，或
把它们排在主稿之后**串联**执行。

---

## 5. 收尾纪律（本文件对应的四条自检）

```python
# ① 无来源数字
orphan = numbers_in_manuscript - numbers_in_output_files      # 必须为空
# ② 不可估计格子
assert "P = NA" not in manuscript_text          # NA 不该被当成结果抄进稿里
# ③ 口径派生恒等式
assert abs(entry_rate - n_analysis / n_model) < 1e-3
# ④ 图件重制
assert all(fig_changed_where_values_changed)    # 值变则 md5 必变；重制后必重嵌
```

**一句话**：**能被复现的数字才叫结果；不能复现的，要么补落盘，要么删掉并把"为什么给不出"写成一句诚实的说明。**
