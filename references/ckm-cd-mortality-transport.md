# CKM eGDR 跨库运输性论文（CHARLS+NHANES → Cardiovasc Diabetol）——v10→v14 实战坑与规则

本文件沉淀 "外部AI评审→逐版改稿"（GPT6/chatGPT 每轮产 docx 意见）期间反复踩到、修复后值得复用的技术规则。主流程见 SKILL.md（ai-review-revision-loop）。

## 交付形态（用户偏好）
- 每版产出：`Manuscript_draft_vX_0.docx`（投稿版）+ `Manuscript_draft_vX_ANONYMIZED.docx`（双盲版：**保留标题**，掩作者/单位/邮箱/基金号；AI-use 声明不删）；项目根与 `投稿包_*` 各一份；图 PNG+TIFF300dpi 同步 `图表/` 与 `Figures/`；`00_状态与明天继续.md` 追加版本日志。
- 用户同时收集多位外部AI意见（此处 GPT6 等），要求**逐条对照落位**并保留"意见→处理→位置"对照表（md/docx），这是质控证据。
- 评审意见常含"已能确认的图文矛盾"清单：逐项核，不改就删表述，不手写"看起来合理"的数值。

## docx↔md 管线铁律（本会话多次中招）
- md→docx 用 `/d/Pandoc/pandoc.exe -o x.docx --standalone`；docx→md 用 `-t gfm --wrap=none` 会：把管道表改成无空格管道、把 `<` 转义为 `\<`、把中括号转义为 `\[`、把图换成 HTML `<img src="media/...">`（需 regex 换回绝对路径 md 图）、段落变长行、元数据 title 丢失（要重新插入 `--- title: ...`）。
- **恢复受污染 md**：用最近一份好 docx `pandoc -t gfm` 还原再打补丁，比手修快。
- 补丁锚点失效高频原因：①数字引用经 renumber 变动；②全角/半角与弯引号；③空白被压平；④句子已被前轮替换。先用正则/索引切片找实际文本再替换，避免 "replace-first-occurrence 打到摘要" 的惨案。
- `renumber_clean.py`（按首现重排引用）若"总数不涨"，先查脚本 `P` 是否指向旧文件（曾指向 v9_raw 导致 v12 改 22→27 失败）；运行后验证 `total refs == body cites used == 引用列表条数`、无孤儿。
- docx 三线表样式（booktabs 风：顶/底 12=1.5pt、表头下 6、无竖线）用 python-docx tblBorders/tcBorders 脚本，任何 pandoc 重建后**必须重跑**。

## 统计一致性（外部评审的"结果整合"轮，评审要求单一估计量贯穿全文）
- 定一**个**主估计量并命名精确（勿"single estimator"含糊）。本项目定为：9y cumulative/dynamic AUC = 事件(≤9y 死亡) vs 对照(≥9y 存活) 的秩一致性（findInterval 加速，O(n log n)，可 bootstrap B=500–1000）。Harrell's C（全随访）、Uno IPCW C、Brier 都要显式区分并各自命名。
- "仅用结局已知者"要主动写明占分析样本比例与评估样本量（2,428/10,289、919/5,922），并承认删失选择；晚期周期无 9y 随访时给"潜在随访充分周期(1999–2010)"敏感性。
- 建模权重 vs 性能评估权重 vs 重抽样权重分三层交代；合并多年份 NHANES 权重按 NCHS：1999–2002 四年权重×4/20、其余二年×2/20；空腹子样本用空腹权重。
- Brier 口径统一："已知 9y 状态人群"；配对 ΔBrier 定义要固定（如 Δ=updated−direct）且 S9/S11 两处一致；IPCW-Graf 若未稳定化会出离谱值（本项目 REV 0.60），如实弃用并说明。
- 中心化：`basehaz(centered=T)` 的 H0 对应均值中心参考；`predict(type="lp")` 即 β′(x−x̄_fit)。手工公式与 `survfit(newdata)` 逐人核对（本项目 max diff=0）并写进 S 表。
- 敏感性/阶段表数字必须守恒（列和=样本量）；改规则要分别命名（main/no-FRS/no-FRS+no-TG）并逐规则给 n/事件/HR；missing 处理不能写"缺失当作正常"，要写"不计入该判据"并做替代规则敏感性。
- 队列间特征表勿互相拷贝（曾把 CHARLS 纳入者特征误贴 NHANES 段）。

## R 细节（Windows）
- coxph 在自定义函数里配外部公式 + data=参数会报 "找不到对象 dat"：顶层直接调用或用公式内列名。
- `c(HR=exp(b*sd))` 名字会被具名系数污染成 `HR.eGDR11` → 用 `unname()` 再组向量。
- survSplit 在此数据上曾段错误 → 用 `tt(x,t)` 时间交互代替（eGDR×log(time)）。
- 加权 bootstrap 的 coxph 权重须作为数据列传入（`weights=WW`），否则公式环境找不到 `w`；concordance(newdata=) 不接受 weights 参数。

## 图
- 每版数值变化→图必须真重生成（勿只改图注）；Fig 里加逐步排除数/十分位观测%标注。
- Figure 2 CVD 死亡次结局更新为 0.837 (0.733–0.956) 且标签标 1999–2014 周期。
