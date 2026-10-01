# 生成式手稿 / 数据资源稿的硬坑（2026-09 实测，EGFR v12→v13）

适用：手稿、表格、图件的数字**由脚本从冻结表注入**的任何任务（数据资源稿 Data Descriptor、
投稿正文、补充材料）。这类任务最常见的失败不是分析错，而是**注入环节静默取错值**——
外部 AI 审稿人会把它读成"数据算错了"，实际是生成器 bug。

---

## 1. 禁止按位置取表值（本会话最严重的一次）

事故：生成器写 `esc_mut[0]`（突变分母表首行）却标注为 "TP53"，而首行其实是 **KRAS 0/96**
→ 正文印出 "TP53 is reported in 0/96"。两位审稿人（GPT6、Claude）都判定"食管鳞癌 TP53 不可能为 0，
突变层 join 错位，必改"。真相：数据没错（TP53 = 86/96），错的是模板取行方式。

规则：
```python
def one(rows, **kw):
    hit=[r for r in rows if all(str(r.get(k,""))==str(v) for k,v in kw.items())]
    assert len(hit)==1, f"expected exactly one row for {kw}, found {len(hit)}"
    return hit[0]
tp53 = one(mut_rows, gene="TP53")      # 而不是 mut_rows[0]
egfr = one(cna_rows, gene="EGFR")
```
- 断言必须**抛错**（找不到 / 命中多行都停），不允许 `if not hit: pass`。
- 全项目 `grep -n "\[0\]"` 清查同类"首行取值"模式，逐一改为键查找。
- 收工审计里加一条断言：关键基因的数值必须出现在正文（如 `"TP53 is reported mutated in 86" in md`）。

## 2. 只改生成器，不改生成物

事故：脚本 A 用 `patch` 直接编辑生成出来的 `DataDescriptor_v12.md`（改措辞、加段），
随后脚本 B（正文生成器）重跑 → **编辑被静默覆盖**，审计仍显示"通过"。

规则：
- 正文/表格/图件由生成器产出时，**所有文本改动都改生成器模板**，再重跑生成器。
- 一旦发现"我改过但文件里没有"，立刻怀疑生成器覆盖；把定稿链路固定为
  `生成器 → 构建 → 审计`，中间不插手工编辑。
- 顺序陷阱：`patch 正文` + `重跑生成器` 的脚本链必须调换顺序，否则前一步必然丢失。

## 3. 完整矩阵：缺口要保留并给原因，不能默默少行

审稿人会算 `队列 × 模块`：26 × 17 = 442，而交付表只有 434 → 直接被质问"缺的 8 行去哪了"。

规则：枚举全部组合，缺失项以 `measure = "not estimable"` + `not_estimable_reason` 保留：
```python
for acc in cohorts:
    for m in modules:
        if (acc,m) in have: continue
        reason = (f"only {npresent} of {nmem} module members present in this cohort"
                  if npresent and int(npresent) < 3 else
                  "module score has zero variance across the cohort's samples")
        ...
assert len(full) == len(cohorts)*len(modules)
```
同理：排除的样本/队列、判为不可检验的比较，都要**成表成行**（条数 + 原因），不要只在正文说一句。

## 4. 验证措辞分级（"复现"不能被滥用）

审稿人原话：*"精确复现与有序近似是两个等级，混用会削弱整体可信"*。

| 级别 | 判据 | 允许的说法 |
|---|---|---|
| 精确复现 | 重算统计量与交付值**绝对差 = 0** | reproduced exactly / maximum absolute difference 0 |
| 秩一致 | Spearman 相关（0.9x） | rank agreement only；必须写出差异来源（如聚合顺序） |
| 敏感性分析 | 换参数后结论数量变化 | sensitivity analysis；报告变化后的计数 |

配套硬规则：
- 交付每层评分必须写出**构造规则**（TCGA 层=先按基因跨患者 z 再对成员取均值；bulk=队列内 z 的 GSVA；
  单细胞=成员 log 归一化表达均值→供者均值），否则"重建分数 Spearman 0.95"无法解释。
- `p > 0.05` 只能写"未检出违反假设的证据"，不能写"假设成立"。
- 交付图/表里同时给"精确"和"秩一致"两类结果时，**另立一张验证证据表**（检查项 / 范围 / 结果 / 解读）。

## 5. 设计与分组必须由元数据推导

事故：配对设计写成硬编码队列名单 → 3 个队列（GSE41258/GSE13911/GSE179285）明明有 ≥4 例双组织患者
却被当非配对，主结果从 13 变 17（方向性错误）。

规则：
- 配对判定写成**元数据规则**（≥4 例患者同时贡献 case 与 control），输出 `paired` 标志列；
  在配对队列里明确"只有完整配对进入配对效应，其余样本不进"。
- 无患者 ID 的队列：标注"配对不可建立 → 按必需非配对，独立性不可推断"，不要默认它们独立。
- 设计不符的队列（如治疗应答 Responder/NonResponder）**单列并排除**，在注册表里给 design 列。

## 6. 可比性要量化，不能只当卖点

审稿人：*"核心卖点（跨队列可比）是断言而非验证"*。补三类可发表的检查：
- **方向一致性**：同情境同模块 k≥2 队列中，效应符号完全一致的占比（本例 112/165 = 68%）。
- **覆盖阈值敏感性**：按 gene coverage ≥0.60/0.80/0.90 逐级剔除后重跑合并，报 BH 存活数
  （本例 13/13/12/6）——展示"渐变退化"而非全有全无。
- **签名重叠审计**：模块基因集与去卷积面板（xCell 489 基因）的重叠比例（本例 17/17 模块 >20%，最高 100%）
  → 结论：组成调整只能定位为**敏感性分析**，不能声称分离出独立效应。
- **共线性双指标**：整体模型 R²（疾病~四成分）与**逐预测变量 VIF** 必须分别定义并解释，
  否则"R²=0.89 但 VIF=2.1"会被审稿人当成内部矛盾（算术 1/(1-0.89)≈9）。

## 7. 组成/派生表必须带连接键

事故：随包发布的 xCell 组成分数表只有 `(accession, epi, fib, end, imm)`，靠**行序**与原分析对齐
→ 不可直接 join、审稿人会质疑。修法：重建带 `sample_id + group` 的表 + `join_status` 审计列，
并**独立复算**（xCellAnalysis 重算 3 队列）给出 Pearson/Spearman 区间，把最低秩相关如实写出。

---

## 附：本会话可直接复用的检查清单

1. `grep -n "\[0\]"` 生成器 → 全部改为键查找 + 断言
2. 断言：正文关键数字（基因/样本/效应量）逐条出现在 md 中
3. 断言：完整矩阵行数 = 队列 × 模块；不可估计行有 reason
4. 断言：无陈旧表述（如 `"TP53 reported in 0"`）残留
5. 三张图 OCR 版面扫描 0 裁切（见 scripts/figure_layout_ocr_qa.py）
6. 验证证据表存在，且"精确/秩一致"分级正确
7. VERSION + CHANGELOG + curation_flow（筛选分母）随包发布
