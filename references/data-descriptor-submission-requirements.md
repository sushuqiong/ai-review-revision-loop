# 数据资源论文（Data Descriptor）投稿硬要求与包结构

触发：GPT6/审稿人建议"转成数据资源论文"，或用户自己问"能不能把分析稿改成数据论文"。
本文件是从期刊指南 docx 里逐条提取后的**可执行**版本（Scientific Data 口径；npj 系列大体类似）。

## 一、硬指标（先自查，不合就别写）
| 项 | 要求 |
|---|---|
| 标题 | **≤110 字符**，少用缩写 |
| 摘要 | **≤170 词**（不是 250！）；只客观描述数据与用途，**不得写新科学发现** |
| 结构 | Title / Abstract / **Background & Summary** / Methods / **Data Records** / Data Overview（可选）/ **Technical Validation** / **Usage Notes**（可选）/ Data Availability / Code Availability / References / Author Contributions / Competing Interests / Acknowledgements / Funding / Ethics |
| 内容红线 | Data Descriptor **不呈现研究结论**；原稿的 Results/Discussion（预后、药物推断、分型）必须压缩或移出 |
| 图表 | Technical Validation 只允许 **1–2 张图/表 + 一段文字**；多了编辑会要求删 |
| 作者贡献 | 不得留"其他作者待定"之类占位；只写真实的 |
| 数据归档 | **必须有数据仓库 DOI**；首轮可用匿名下载链接，**第二轮起强制 depository**；许可必须 CC0/CC-BY（**不接受 -NC/-SA**）；要求单一下载单元 + https 直下 + 审稿人匿名访问 |
| 数据引用 | 用 DOI 形式 URL；CELLxGENE 等要补**完整 dataset/collection ID 与版本**；"no new data were generated" 须改写为"未采集新人体样本，但生成了新的整理/派生数据" |

## 二、"新增价值"怎么写（编辑必问）
不要写"我们算出 55/17/21 个显著状态"（那是分析结果）。要写**使用者省下了什么整理工作**：
样本核验与注释整理、基因映射与转换记录、逐平台基因覆盖、样本级评分、组成注释、可追溯的失败与排除记录。
一句话模板：*"使用者可以直接替换基因集/换组成校正方案/加队列，无需重复定位与清洗。"*

## 三、交付包 10 目录（GPT6 表格的可执行版）
```
01_cohort_registry/       注册表：accession、设计分类、平台、检测数/样本数/患者数、原论文 PMID、来源与下载溯源
02_sample_annotation/     逐样本：sample_id、patient_id、组织类型、病例/对照角色、配对关系、排除原因
03_expression/            基因映射与转换日志（原始矩阵不重复托管，注明来源 accession）
04_modules/               模块定义、逐平台覆盖、样本级评分（标注打分层次：GSVA / 成员均值 z / 单细胞均值）
05_composition/           组成分数（**必须含 sample_id**）+ 四类 compartment 构造规则 + join 审计
06_single_cell/           数据集审计、原始/整理标签与映射规则、供者级汇总、比较表（含实际检验类型）
07_estimates/             完整估计层：逐队列效应、meta 多种估计器、组成模型、driver、外部验证、
                          单细胞比较——**必须包含不显著与不可估计的结果**
08_qc/                    覆盖缺口、排除/标记日志、PH 检验、共线性、共同基因敏感性、join 审计、
                          file_inventory_and_checksums.csv（file/bytes/rows/sha256）、checksums_sha256.txt
09_reuse_examples/        可运行复用示例 + expected_output + 离线 demo 输入（demo 必须含被演示基因集成员）
10_environment/           session info、包版本、run order
00_README.md              字段字典、连接键、打分层次不可混用、已知局限、许可（派生数据 CC-BY / 代码 MIT）
```

## 四、必答的"复用性"三问（写进 Usage Notes）
1. 分数**只能队列内比较**，跨队列只能用效应量——不同平台同一模块纳入的基因可能不同。
2. 三层分数（bulk GSVA / 成员均值 z / 单细胞成员均值）**不是同一量纲，禁止拼接**。
3. 组成分数是**富集分数不是细胞比例**；不同层同疾病名**不代表同一批患者**，本资源不是患者级多组学资源。
4. 明确"这些分数**不是经验证的预后工具**"，外部未复制**不否定资源价值**，但必须如实说明。

## 五、投稿前一天的收尾顺序
① 样本/组织学/细胞标签核验 → ② 冻结核心数据范围（不能核验的扩展层**移除并删掉依赖它的主张**）→
③ 组包 + 校验值 → ④ 干净环境跑复用示例 → ⑤ 重写 Data Descriptor → ⑥ 归档拿 DOI（**点击级步骤 + 元数据模板 + 回填清单见 references/repository-deposit-and-doi.md**）→ ⑦ 回填占位 `[DOI to be inserted after deposit]`。
