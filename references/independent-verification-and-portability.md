# 独立验证、可移植性与终版收口（数据资源稿 v15 实战）

来源：2026-09 EGFR 跨疾病资源 v14→v15（GPT6 + 腾讯 Hy4 两份外部意见 → 逐条处置 → 对抗性审计 23/23）。
适用：任何被要求"证明你确实可复现 / 代码要能一键跑 / 数据要能被人复用"的稿子（数据资源稿尤甚）。
配套：引用装置与计数自洽见 `reference-apparatus-and-editor-pass.md` §9–§11；内容完备性见 `data-resource-descriptor-and-claim-audit.md` §13。

---

## 1. "验证不够独立"的标准答案：换语言、零项目依赖的复算脚本

审稿人对"用同一管线重跑得到完全相同结果"的判词是 **内部重跑 ≠ 独立可复现**。做法：写一个**纯 Python、不 import 项目任何模块**的脚本，只读随包的冻结表，重算三类量并与随包列比对，把结果落成一张 QC 表进包（实测 `08_qc/qc_independent_reimplementation.csv` + `09_reuse_examples/independent_check.py`）：

| 复算对象 | 输入 | 实测一致性 | 结论口径 |
|---|---|---|---|
| 未配对效应量 SMDH | 随包的 `mean_case/sd_case/n_case/mean_ctrl/sd_ctrl` | ~1e-5 | 受**随包数值已四舍五入**限制，容差写 1e-4 并注明原因 |
| REML + Hartung-Knapp 合并估计 | 随包的 `yi/vi` | **8e-17**（est）/ 2.5e-16（se） | 从随包精度值重算可达 1e-6 容差 |
| Benjamini-Hochberg 家族校正 | 随包的 p 列 + 家族定义 | **0.00e+00**（逐家族全等） | 全等即写"逐家族精确一致"，并说明是确定性算术 |

- **必须解释 "maximum absolute difference = 0"**：同一输入 + 确定性算术，0 差只说明"重算无误"，**不**说明独立复现；把这句话写进 Technical Validation，否则被当成自我循环。
- **容差要分来源**：从四舍五入后的汇总统计重算，误差上限由舍入位数决定（实测 1e-5）；容差写成 1e-6 会自造 FAIL，写成 1e-4 才诚实。
- **独立复算最常见的副产品 = 暴露文档歧义**：实测复算 SMDH 差 1.8e-2，追因发现随包用的是 **RMS 分母** `sqrt((sd_case²+sd_ctrl²)/2)`，而审稿人默认经典 Hedges 合并 SD → 必须在 Methods 里**命名分母**并声明"deliberately not the sample-size-weighted pooled SD"，否则这个差异会被读成数据错误。

## 2. 配对/非配对效应量的交代纪律（审稿人必问）

- 二分母不同 → **命名**：`SMDH`（RMS 分母的 Hedges 校正差）、`SMCRPH`（配对分数秩/相关混合）。
- 混合合并要显式：`paired and unpaired cohorts enter the same pooled estimate, with the measure used reported for every contributing cohort`，并随包 **unpaired-only 敏感性分析**。
- 配对判据与相关：`≥4 例患者同时贡献两种组织` 才按配对；主分析用**经验 r**，另给 `r=0.5/0.7` 敏感性，并**声明 r 自身的不确定性未传播**（列入 Limitations）。
- 只要表里还有 `k=1` 行，就不能写 "requires at least two cohorts"：k<2 行一律标 `pooled = "no (single cohort; not a pooled estimate)"`，p/FDR/CI/PI 置 `not applicable`（实测主表 5 行、非配对敏感性表 38 行需同步处理）。

## 3. 代码"一键复现"的最小交付（把扣分项变成加分项）

原措辞 `Paths inside the scripts point to the authors' working directories and must be adjusted` = 明确认输。补齐四件套并进包（`11_code/`）：

| 文件 | 作用 |
|---|---|
| `config.yml` | 唯一入口：`root_dir` + 各子目录名 + `r_binary/python_binary/threads/seed` |
| `run_all.R` | 读 `config.yml` 后按序跑随包脚本（存在性检查 + `message("skipped (not shipped)")`） |
| `requirements.txt` | Python 侧依赖上限（如 `numpy>=1.24,<2.0`，避免 numpy 2 破坏 h5py 二进制） |
| `sessionInfo.txt` | `Rscript -e 'writeLines(capture_output(file("sessionInfo.txt")), ...)'` 实测可写 |

Code Availability 相应改成："仓库 URL + **tag v15.0** + 包内 `11_code/`（config 驱动、相对路径）+ `run_order.md` + `environment.txt`"，并声明**已在干净目录跑通复用示例**。

## 4. 换 docx 构建器 = 静默回归，必须补"产物不变量"断言

**实测事故**：v15 为修排版换了 docx 构建器，**内嵌 Table 1 直接消失**（`len(doc.tables) == 0`），而 24 项审计里恰好没有这一项 → 收尾自查才发现。

换/改构建器后必跑的不变量（写进审计脚本，N 项里必须有这几条）：
```
len(doc.tables) >= 1            # 正文内嵌表还在（Table 1）
docx 内嵌图 sha256 ∈ 磁盘图 sha256 集合，且数量 == 图数
superscript run 数 > 0 且 ≈ 引用条目数
关键短语在 md 与 docx 中计数相等（章节标题、S 编号、DOI）
"Figure captions" 文本在正文里（不能只存在于独立图例文件）
```
排版三坑（同批修掉）：
- **Word 标题样式自带蓝色横线/配色** → 数据资源稿一律用**加粗普通段落**（`bold=True`, 字号 14/12/11）代替 Heading 样式，标题下方不再出现"Word 风格蓝线"。
- 作者单位标记 `^1` 要渲染成**真上标**（正则 `\^(\d)` → superscript run），否则渲染后是普通字符（审稿人明确点名）。
- 图注除独立图例文件外，**正文里也要有一份**（审稿人会问"投稿系统里到底有没有对应文件"）。

## 5. 终版收口：DOI 插入脚本 + dry-run 纪律

形态：`scripts/F2_v15_insert_doi.py [--dry-run] <DOI>`，一条命令做完 8 件事：
1. **DOI 格式校验**（`^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$`，不合格直接退出）；
2. 替换**所有**占位符（正文 Data Records + Data Availability + 包内 README + 投稿信 + 投稿对照单；先 `grep` 出真实占位串再写正则）；
3. **刷新实时计数**（目录数、文件数、SHA 条数从磁盘/manifest 现算注入正文与 README）；
4. 重建 docx（内嵌 Table 1 + 上标 + 正文图注）+ PDF；
5. 重算清单与 `sha256sum -c` 链，打印 verified/problems；
6. 更新处置文档（把 DOI 项改"已闭环 + 链接"，"仍未闭环"一节改"无"）；
7. 重打包两个 ZIP（投稿包 README 写入 DOI）；
8. commit + tag + push，最后打印 `placeholders remaining: 0 | READY TO SUBMIT`。

**dry-run 三纪律**：
- 只读不写，报告"每文件 before → after"；跑完**用 `grep -c` 复核文件未被改动**（把这条写进脚本输出旁白，用户才敢信）。
- 报告占位符数量要用**一条合并正则**，不要遍历多条正则累加：`https://doi.org/[DOI to be inserted after deposit]` 会被两条正则同时匹配 → 报出"3 remaining"的假象（实测踩过）。
- 走查目标文件清单时把"零占位符"的文件也打印出来（`0 → 0`），证明覆盖范围完整。

## 6. 产物在 git 工作树之外 → `git commit` 会返回 1

实测：表格/正文 docx 产在工作目录（`EGFR的v15/`），而仓库在另一路径 → 重建后 `git add -A && git commit` 报 **nothing to commit（exit 1）**，日志仍停在旧提交，容易误判"已推送"。
修法：推送前显式把产物**复制进仓库**（`manuscript/`、`tables/`、`results/v15_*/`、`scripts/v12_data_resource/`），再 commit/tag/push，并打印 `git log --oneline -1` 自证。

## 7. "为什么不用现成资源"——数据资源稿的定位段（审稿人几乎必问）

审稿人必问：*Why not just use recount3 / ARCHS4 / refine.bio / DEE2 / UCSC Xena (Toil) / GTEx?*
可复用答案（不要空口说"我们更全"，而是**分工不同**）：

> Existing resources harmonize **expression matrices**; this resource harmonizes the **derived-score layer** and, critically, ships the **coverage and comparability metadata required to judge whether two scores may be compared at all**.

配套要点：per-cohort module coverage、显式对照组织本体、完整估计层（保留不显著/不可估计并给原因）、跨队列方向一致性的量化与其失效结构。
**元数据纪律**：这些对标资源也要**按题名严格校验后**才引（实测 recount3 Wilks 2021 *Genome Biol*、ARCHS4 Lachmann 2018 *Nat Commun*、DEE2 Ziemann 2019 *GigaScience*、Toil Vivian 2017 *Nat Biotechnol* 通过；refine.bio 与 GTEx 未通过严格校验 → **宁可不引也不硬凑**，在处置文档里写明"dropped, metadata not validated"）。

## 8. Limitations 小节 + 许可分源 + 措辞降级（Sci Data 吃这一套）

- **Limitations 小节**（放 Technical Validation 末尾，实测 10 条）：不作生物学结论、每情境仅 2–3 队列故单队列即可翻转、低覆盖模块不可直接比、模块与组成分数共享基因故仅敏感性、配对 r 不确定性未传播、单细胞描述性且阈值/家族影响显著数、某数据集无可检验比较、无新实验无前瞻外部验证、筛选非系统综述（以对账表替代）、上游条款约束。
- **许可必须分源**：作者自产（注释/模块定义/QC/估计层/代码）= CC-BY-4.0；GEO/TCGA-GDC/CELLxGENE 派生矩阵**不再授权**、按各自条款，不可再分发时**只给 accession + 校验 + 下载脚本**。
- **可比性降级**：把 "cross-disease comparability" 收窄为 **cautious effect-size comparability**，并给出 pair 级比率 + **Wilson 区间**（实测 112/165 = 68%，Wilson 60.4–74.5%，并声明 pair 级、非队列级）、k≥3 限制下的同值（67/99）、对照组织构成（16/26 用癌旁、且对照类与情境几乎完全混杂 → **声明 meta-regression 不可识别、不做**）。
- 对照组织本体要**可见**：正文写清构成，并**进 Table 1 加一列**（"Control tissue (cohorts)"，按情境给类别与队列数），只放在 CSV 里等于没写。
