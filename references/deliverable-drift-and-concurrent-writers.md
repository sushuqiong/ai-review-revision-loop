# 交付件漂移检查（图 / 表 / 清单 / 系数文件）

> 本文件是对 `references/submission-readiness-adversarial-qa.md` 程序化清单的补充：
> 那份清单查"正文里改干净没有"，这份查**"改了正文、别的层没跟上"**。
> 通用取证脚本与完整配方在 skill `cohort-methods-sensitivity-kit`：
> `scripts/deliverable_token_scan.py`（占位符/旧数字/千分位/字面标题/内部版本号）
> 与 `references/deliverable-consistency-audit.md`（MD5、OCR、CSV 反推、重建流程）。

## 两条必查（实测各中过一次）

1. **docx / zip 落后 md 一整轮。**
   md 是工作文件，审稿人看不到。做法：`ls -la` 比 docx、zip、md 的 mtime；
   **审查顺序永远是"先 docx/zip/图 → 再 md"**，md 改完不等于交付件改完。
   重建后必须再跑一次残留扫描，确认占位符与旧数字归零。

2. **图"按构造就是旧的"。**
   判据一：跨版本 `md5sum`——相同的图 = 从未重绘（改多少图注都没用）。
   判据二：图脚本里**硬编码**估计值（`HR=c(.855,.849)` / `slope=0.844`）⇒ 分析一变这张图就假；
   只有"脚本内重新拟合"或"读当前结果文件"的图才可信。
   判据三：`tesseract Fig.png stdout --psm 6` 直接读图上印的数字，与正文表逐项比。

## 一条跨会话风险

**同一份稿可能有另一个会话/AI 在同时改**（长论文项目尤其）。现象：工作目录出现你没写过的
`*reconcile*.py`；docx mtime 晚于你上次读取；你自己的 `replace()` 大面积报 MISS
（不是字符串写错，是别人已经先改了）。
读-改-写竞态下**最后一次写入会静默覆盖另一方全部编辑**。处理：停止盲写 → 比对关键数字是否
两边收敛（本项目两边独立重抽样给出同一配对差值）→ 在报告里明确要求"只留一个会话写这份稿"。

## 与本用户相关的两条纪律

- **不单方面改主结论**：分析层发现"主结论复现不出"时（例：按最终权重设定重算后校准非对称性反向），
  把重算值 + 一条可复现命令列给用户拍板；只静默修 QA 级不一致（Brier、分母、图注计数、模型名、千分位）。
  本项目实测用户对"AI 代填人类判断"极敏感，宁可留显式遗留项。
- **代码默认不公开**：期刊/外部 AI 评审要求"公开仓库 + 持久标识符"时，用合规长表
  （脚本作为投稿附件供审阅 + available from the corresponding author on reasonable request;
  not held in a public repository），**不要**留 `[PUBLIC REPOSITORY … 待填]` 占位符，
  也不要在匿名版写"仓库标识符已移除"（等于承认存在仓库）。
