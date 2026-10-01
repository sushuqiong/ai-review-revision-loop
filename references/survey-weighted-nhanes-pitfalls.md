# 复杂抽样 / NHANES 分析陷阱（v13 实证）

本文件记录在「GLM7 × 胆石症」课题 v12→v13 迭代中，**经官方文档与实跑数据共同证实**的四类陷阱。
四轮 AI 审稿都漏掉它们，因为审阅只比对「代理产出的文件之间是否自洽」。
教训：**每个数据派生声明都要回到一手来源（官方问卷/编码手册/实验室文档/原始论文）核对变量的真实覆盖范围与实现方式。**

---

## 1. NHANES III 结局变量有年龄分支（最高优先级 · 曾静默删掉 2,710 人）

**症状**：分析样本 `max(age) == 74`、`sum(age >= 75) == 0`，而全文件里 ≥75 岁有 2,710 人。
边界恰好卡在 75 岁 = 问卷跳转边界，是**分支遗漏**而非真实人群特征。

**机制**：NHANES III 家庭成人问卷 Section J 由检查项 **HAJ0**（REFER TO AGE OF SP）分支：

| HAJ0 | 人群 | 胆石诊断 | 胆囊手术 |
|---|---|---|---|
| 1 | 17–74 岁 | HAJ9 | HAJ12 |
| 2 | **≥75 岁** | **HAJ16** | **HAJ17** |

HAJ0 计数：1 → 17,340 人；2 → **2,710 人**。只读 HAJ9/HAJ12 会把 ≥75 岁全部识别为「结局缺失」而排除。

**后果**：历史层实际只覆盖 20–74 岁，而当代层含 ≥75 岁（P 264 人 / L 216 人）
→ 患病率、年龄相关暴露分布、跨期比较全部受影响；且会误报「无跨期异质性」或反之。

**adult.dat 固定宽度列位置**（`adult.sas` INPUT 段解析）：
HAJ0 = 1821；HAJ9 = 1840；HAJ12 = 1844；**HAJ16 = 1850；HAJ17 = 1851**。
清洗：7/8/9（refused/DK/missing）→ NA。lab.dat：G1P=1866（血糖 mg/dL）、**I1P=1918-1923（胰岛素 µU/mL）**、
TCP/TGP/LCP/HDP=1598-1624；exam.dat：BMPBMI / BMPWAIST。
时段 `MXPSESSR`（1=晨间）；权重 `WTPFSD6`（晨间空腹亚样本，实测 >0 者 100% 为时段 1）vs `WTPFMD6`（下午/晚间）——两者互斥，不可混用。

**统一结局写法**：
```r
d$dx_src <- ifelse(d$HAJ0 == 1, d$HAJ9,  ifelse(d$HAJ0 == 2, d$HAJ16, NA))
d$sx_src <- ifelse(d$HAJ0 == 1, d$HAJ12, ifelse(d$HAJ0 == 2, d$HAJ17, NA))
```

**修复后必做两件事**（否则跨期比较仍不成立）：
1. 报告各层**最大年龄与 ≥75 岁人数**；
2. 增做**三周期统一限定 20–74 岁的可比分析**（本例：N3 20–74 M3=2.130 vs 全年龄 M3=1.996，说明纳入 ≥75 会削弱关联）。

**通用化**：任何「按年龄/性别/生育史分支」的问卷模块都要先查分支检查项（NHANES 常见 check item 命名 HAJ0、SIA… 等），
不要假设一个变量全人群覆盖。判据：**样本年龄上限恰好等于某个问卷跳转阈值**。

---

## 2. Rao–Wu bootstrap：抽 m_h 还是 m_h−1（曾使 SE 系统性偏窄 30%）

**错误实现**（v12 实际代码）：层内 `k <- rmultinom(1, size = m_h, prob = rep(1/m_h, m_h))`，
乘数取 `k`，**无层内重缩放**，仅全局 `w/mean(w)` 归一到均值 1。

**为什么错**：多重归一只影响尺度与 IRLS 收敛，**不能替代层内乘数重缩放**。
分层均值下 `Var_multinom = Σ(m_h−1)s_h²/M²` 而 `Var_RaoWu = Σ m_h s_h²/M²`，
比值 `(m_h−1)/m_h`；本类数据层内几乎全是 **2 个 PSU** → 方差低估 1/2，**SE ≈ 0.707×**。

**正确 Rao–Wu**：每层抽 **m_h − 1** 个 PSU，乘数刻度 `m_h/(m_h−1)`：
```r
k <- tabulate(sample(seq_len(m_h), m_h - 1, replace = TRUE), nbins = m_h)  # 计数
wstar <- w * k[psu] * (m_h / (m_h - 1))                                    # 重缩放
```

**必做校验（否则无法察觉）**：把 bootstrap SE 与 **Taylor 线性化 SE**（`svyglm` 或自写 influence 函数
+ `survey::svytotal` 口径）对比：

| 方案 | boot SE / Taylor SE | 判定 |
|---|---|---|
| Rao–Wu（正确） | **0.99 – 1.19**（多数 ≈1.00–1.05） | 通过 |
| 抽 m_h 无缩放（v12） | **0.62 – 0.81**（多数 ≈0.70–0.80） | 系统性偏窄 |

**后果管理**：修正后 CI 变宽 → 原先「贴近 0 的显著增益」多会变为跨 0。
本例 P 系列 baseA 配对比较（GLM7 vs METS-IR / LAP / TyG / TyG-BMI）新 CI **全部含 0**，
即「GLM7 优于比较指标」的微弱显著性**消失**——这反而强化了「增量信息有限」的核心结论。
**把区间变化如实报告，不要因结论变弱而回避。**

参考实现要点：`as.svrepdesign(des, type="bootstrap", replicates=1000)` 是成熟的重复权重入口，可用于交叉校验；
自己手写时务必**所有指标共享同一批重复权重**，配对差在同 replicate 内相减，才能保留配对结构。

---

## 3. 复合指数 vs 其代数组分的「共同尺度」陷阱（曾据此写出错误归因）

**错误做法**：把完整指数与去掉某组分后的部分**各自标准化**，然后比较**各自的每-SD OR**，
据此声称「该组分承载了大部分关联」。两者 1 SD 不是同样大小的增量，OR 变小≠贡献被分解出来。

**实例**：N3 完整 GLM7 SD=0.6623、OR=1.267；metab SD=0.5404、OR=1.211。
换算到同一增量：`1.211^(0.6623/0.5404) ≈ 1.264 ≈ 1.267` —— 表面「下降」几乎全是尺度变化。

**正确做法**：统一换算成**同一个增量**再比：
```r
OR_common <- OR_component ^ (SD_full / SD_component)      # 换算到 1 个「完整指数 SD」
# 或等价：component_scaled <- component / sd(component) * sd(full)
```
本例 9 个（3 队列 × 3 设定）组合的共同尺度 OR 比全部落在 **0.999 – 1.020（差异 <2%）**
→ 必须**撤销**「age/BMI 承载大部分关联」的表述，改为「换算到共同尺度后二者关联强度基本相同」。
（仅在**未调整** age/BMI 的框架下 OR 比约 1.08–1.18，那是「指数多含了 age/BMI 变异」的**定义差异**，不是该说法的证据。）

**配套三条**：
- 术语：代数拆分 **不是统计残差**（它仍与 age/BMI 高度相关）→ 一律叫 **metabolic component**，禁用 "residual"。
- 比较条件：**同样本 + 相同协变量函数形式 + 共同增量**，三者缺一不可。
- 系数符号反转：当「组分本身」被作为协变量条件化时（如 GLM7 = log₁₀age + log₁₀BMI + 代谢部分，
  再把 age/BMI 放进模型），指数系数变号是**结构性现象**，不可解读为独立生物学反转。
  用**逐步调整**定位翻转步（本例 step0→step6：1.453→1.565→1.534→1.508→1.407→1.317→**0.835**，
  翻转发生在**加入 BMI 那一步**），并检查共线性（VIF）、`cor(指数, log组分)`、协变量集对指数变异的解释比例、
  高影响点（|标准化 dfbeta| > 2/√n）与剔除敏感性。

---

## 4. 单位/来源/周期重叠的核验（曾把他人论文写成「我们团队」）

**单位**：log10 内的**常数乘性换算**只平移 log 值 → 层内 z 分数不变 → **per-SD 推断不受影响**；
但**原始数值与已发表阈值不可互换**，且标准化**不能消除检测方法差异**。GLM7 类指数的换算：
胰岛素 µU/mL × 6.945 = pmol/L；TG mmol/L × 88.57 = mg/dL；胆固醇 mmol/L × 38.67 = mg/dL。

**检测方法随时间变化必须披露**：NHANES 2021–Aug 2023 周期**甘油三酯检测方法变更**
（glycerol-blanked assay 停用、换新设备）；LDL-C 在 CDC 文件中提供**三种公式**
（Friedewald / Martin-Hopkins / NIH Equation 2）→ 须写明用了哪一种及理由。

**归属**：写 "our group previously reported X" 之前，**核对被引论文的实际作者列表**。
本例原论文为 Wang Z, Chen S, Feng X, ... Xu S（Adv Sci 2025;12(42):e10552），与本稿作者无重叠
→ 必须改写为 "Wang et al. proposed ..."。

**周期重叠**：原研究已用 NHANES 2013–2023，本稿的 2017–2020 / 2021–2023 都在其内
→ 属**周期重叠**，不能称 "additional cycles"。

⚠️ **不要写「无个体层面重叠」**（v14 被审稿人明确纠正的过强声明）：审稿人抓的逻辑是
——「不同调查周期之间样本独立」与「不同论文用同一批周期、可能复用同一批参与者」是两件事。
原研究覆盖 2013–2023，本稿的周期在其内，**除非逐个核对过纳入人员，不能声称无个体重叠**。
正确口径：

> "This analysis uses some of the same NHANES cycles as the index-development study (and possibly
> some of the same participants); the extent of overlap cannot be quantified from public-use files.
> The study should therefore be positioned as a re-evaluation under a different outcome, not as an
> independent replication."

即：**贡献定位改为「新结局下的再评估与增量价值检验」**，这不妨碍研究的价值，但必须如实披露。

**交付件**：加一份**三周期变量映射表**（变量名 / 单位 / 检测或计算方法 / 跨期可比性注记）
作为补充材料 Table S1，并附**单位换算表**——这是回应「可核对性」质疑最省事、最有效的一件材料。

---

## 5. 跨周期池化分析（合并交互 + meta）的四个坑

做「三周期合并、检验指数 × 时期交互」这类分析时（v14 实测）：

1. **PSU / strata 必须加期前缀**，否则 `svydesign(nest=TRUE)` 会把不同周期里同名的
   PSU/层错并成一个：
   ```r
   d$strata_u <- paste0(d$period, "_", d$strata)
   d$psu_u    <- paste0(d$period, "_", d$psu)
   des <- svydesign(ids = ~psu_u, strata = ~strata_u, weights = ~w, data = d, nest = TRUE)
   ```
   症状：`degf()` 或 PSU 计数明显偏小（实测未加前缀时 PSU 只数到 7 个）。
2. **交互检验的 ddf ≠ 设计的 degf**。`regTermTest(fit, ~index:period)` 返回自己的 ddf
   （实测设计 degf=89，而交互检验 ddf = 79（总关联框架）/ 77（M4 框架））。
   正文须报**检验自己的 ddf**；照抄 degf 会被复算视角抓出来。
3. **期特定 OR 要从同一个池化模型取对比**，不是各层单跑一遍：
   ```r
   # 参考期
   b <- coef(fit)["index"]; V <- vcov(fit)["index","index"]
   # 其他期 (delta method)
   k <- paste0("index:period", pr)
   b <- coef(fit)["index"] + coef(fit)[k]
   V <- vcov(fit)["index","index"] + vcov(fit)[k,k] + 2*vcov(fit)["index",k]
   ```
   各层单跑得到的是**分层模型**估计，与池化模型的期特定对比**不是同一个量**。
4. **共同协变量集要真「共同」**：只选三时期都有的变量（sex、race 归 4 类、PIR 连续）。
   用各层自己的模型协变量集做 meta，会让各层估计不可比（旧表口径不一致的根源）。
   逆方差 meta：`Q = Σ(y−ȳ_w)²/v`、`I² = max(0,(Q−(k−1))/Q)`；
   再补 DerSimonian–Laird 随机效应作敏感性（实测 τ²=0.0325，pooled 1.833 vs 固定效应 1.814）。

**口径自检的判据**：表里每个 `n` 都应等于该层**分析样本**（本例 2,885 / 2,056 / 5,918），
池化 `n` = 三者之和（10,859）。若某个 `n` 对不上样本链上的**任何一跳**
（旧表写 N3 `n=5,345`，而样本链是 6001/5942/5918/5724），那就是口径漏了一环，
必被复算视角判为「不可溯源」。

**注**：合并模型与分层模型的差异**不止于协变量个数**——合并模型还约束其余协变量的系数
跨期相同。写讨论时不要把两者的差异全部归因于「少加了几个协变量」。
