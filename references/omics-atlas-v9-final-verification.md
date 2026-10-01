# 组学 Atlas v9 终验轮 — 可复用细节（GPT6 评审 → v9 实测）

与 `omics-atlas-meta-method-review.md` 互补：那篇讲 rerun 主链（联合模型/统一 meta/外部队列审计/证据矩阵/符号 bug），本篇收 v9 终验轮的新增技术与投稿收口事项。

## 1. 跨层评分可比性（GPT6 第 6 节回应）
- **同队列 GSVA vs member-mean-z 一致性**：取覆盖双平台（GPL570/GPL6244/Agilent 等）的代表队列（≥6 个，含配对/未配对），同一队列内逐模块算 `cor(GSVA score, mean-z, method="spearman")`；v9 实测 median ρ=0.94（0.72–0.98）。
  - 写法落点：Methods 2.3（评分句后插一句"method differences unlikely to drive module-level conclusions"）；TCGA 层本就用 mean-z，两口径一致更稳。
- **关键状态级 LOOGO（不是全模块总体 r=0.93 就够）**：对 headline 状态（joint-robust、meta-sig、外部阳性与阴性各挑代表），逐队列删每个成员基因重算效应（GSVA per variant 或 mean-z；v9 用 GSVA），统计"队级别符号翻号"。
  - v9 实测：10 状态 × 11 队列 × 112 次留一 → 仅 2 次翻号，都在小幅状态：CRC ERBB-ligand 去 **NRG1**（GSE41258 −0.37→+0.09）；COPD SRC/FAK 去 **YES1**（GSE76925 −0.28→+0.11）。
  - 处置：写进 Methods 2.2（"two cohort-level sign changes, both in small-magnitude states…"）+ 与 hypothesis-generating 定位呼应（CRC ERBB-ligand 负向部分依赖 NRG1 → Discussion/Limitations 降级理由 +1）。小幅弱状态若审稿人自己删基因复现翻号，提前自曝是防打脸的唯一办法。

## 2. GEO/NCBI 获取机械配方（核验外部队列 n 时的必踩坑）
- **大 series matrix 断点续传**：`getGEO(GSEMatrix=TRUE)` 部分下载后 `curl -sL -C - --retry 4 -o X.gz URL`；gzip 头校验通过且 size>1MB 才算完成。多队列轮询用 for+retry 循环（每轮 sleep）。
- **990 字节伪缓存毒化 GEOquery**：curl 失败时留 990B 假 gz；GEOquery 见同名文件直接当缓存解析失败（"partial-or-error"）。重试前必须 `rm` 伪文件，或用 `-o name_sm.gz` + `mv` 命名避免命中缓存。
- **GPL 平台注释 = 明文 SOFT 却命名 .soft.gz**：`od -A d -t x1 -N 16` 看 magic；非 gzip 用文本读。解析：`!platform_table_begin` 后**跳过空行**再取表头行，`!platform_table_end` 结束。Agilent GPL4133：列有 `ID`(feature 号)、`SPOT_ID`、`GENE_SYMBOL`；表达行名先比 `ID`，覆盖小再比 `SPOT_ID`（`length(intersect())` 判定）。符号清洗：去 ` // ` / ` /// ` 多义、`---`、非 `^[A-Z0-9._-]+$`。
- **原论文补充临床表 ↔ GEO 样本匹配**（ACRG 实例）：Nature 附件页抓 `MOESM` 列表 → 下载 xls/xlsx → LibreOffice 转 xlsx → 找临床总表 sheet（FINAL 313×48 型）；GEO pData title 形如 "T107"（患者号），临床表 Tumor ID 一一对应 → **按 ID 匹配不按行序**（v9: 300/300 命中）。FU status 分布 + OS 中位数定事件编码（0/1 存活、2/3 死亡、4 敏感性），每一定义打印 n/事件。

## 3. 投稿收口四件套（终验轮固定交付）
1. **自动化终验脚本**（python）：摘要词数 + 摘要无引用；旧口径短语清单残留=0；引文 1..N 顺序违规 0/孤儿 0/悬空 0（token 展开必须支持 `[a,b]` 与 `[a-b]` 连字符区间）；主包文件齐全（01 稿件/02 图/06 清单需文件集）；图文件清单核对。
2. **GPT6 意见→回应确认表 md**：按意见原文小节编号 → ✅/◐/⏳ 三态 + v9 落点（正文小节/CSV 名）；◐ = "已声明局限"（stage 不可得、纯度=表达代理、sc 95%CI planned）；⏳ = 人工项。
3. **references_vancouver_vN txt 从重编号后的 md References 段重新生成**（旧编号 txt 必过期，移入 04 备份或删除，别让两个编号体系并存）。
4. **代码入仓 + Declarations URL**：`gh repo create <name> --public --source . --push`；库结构 scripts/atlas_pipeline + scripts/v9_reruns + results + reports + manuscript + README(运行顺序) + LICENSE(MIT)；Declarations 从"will be released"改为真实 URL 后重建 docx/pdf。历史脚本若被归档（archive 目录）记得从原 atlas scripts 目录回拷，别让仓库只剩 rerun 脚本。

## 4. 投稿系统 AI 必答 ≠ 正文 AI 声明（用户决定"正文不写"时）
- Springer Nature 系（npj/Editorial Manager）投稿系统强制单选："Were AI tools used in preparation?" —— 与正文声明分开处理，建议如实答 Yes 并给可复制描述句（LLM assisted parts of analysis scripting, drafting and editing; author verified analyses and takes full responsibility）。此文件/回答放 06_清单 供投稿当天粘贴。
- Cover letter 抬头（date/Editor 姓名/ORCID/Manuscript type）是人工字段 → 出"合成版占位 docx"（正文已定稿 + 占位 `〔…〕` 头部），不给空头承诺。

## 5. 复核技巧备忘
- 无视觉时审查成图：R `png::readPNG` 内容包围盒/留白率（内容%≈95 说明问题在图内空网格/空面板而非页边距——先看数据是否 NA 网格、自由分面空行、按基因分面空条，再决定重绘方向）。
- python heredoc 在 git-bash 双 EOF 会串台 → 用 `python -c` 或写脚本文件执行。
- 替换脚本里 `def rep(): ... s=s.replace()` 会因赋值把 s 变局部 → 用 `global s` 或返回新串再写盘。
