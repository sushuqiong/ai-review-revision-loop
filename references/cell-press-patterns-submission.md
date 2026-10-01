# Cell Press / Patterns 投稿特有要求 + OSF/Zenodo 预注册

来源：本会话实测（2026-08），依据 https://www.cell.com/patterns/authors 作者指南与期刊政策抓取。

## 1. Resource availability 段（Cell Press 研究文章必填，三段式）

手稿末尾必须含以下三个子段（替换泛化的 "Data availability"）：

### Lead contact
`Requests for further information and resources should be directed to and will be fulfilled by the lead contact, [Full Name] ([email@example.com]).`
- 只允许一名 lead contact，必须是通讯作者之一；作者列表需对应脚注。

### Materials availability
- 即使没有生成新材料也要写：`This study did not generate new unique reagents.`
- 若有新试剂/质粒/动物品系：列出仓库（Addgene/KOMP/ATCC）+ 目录号；有分发限制（MTA）要书面说明。

### Data and code availability
- 必须愿意共享所有数据与原始代码，除非法律/伦理禁止（如保密医疗记录）。
- 强烈推荐存入满足 FAIR 标准 + 数字长寿 + 社区支持的在线仓库（OSF/Zenodo 即符合）。
- 逐项列出每个工件 + 仓库链接/DOI：
  - 数据表（`Supplementary_Table_S1_v23.xlsx`）
  - 溯源数据（`source_registry_v23.jsonl`）
  - 编码手册（`public_incident_coding_manual_v23.md`）
  - schema 模板（`candidate_record_schema_v23.json`）
  - 分析脚本（复现全部统计的脚本）
  - 试点预注册链接 + 注册日期
- 结尾加 FAIR 声明句：`The repository meets the criteria for digital longevity, implementation of FAIR standards, and community support.`
- 发布后无法提供数据可能被撤稿。

## 2. Declaration of generative AI and AI-assisted technologies in the writing process

- 写作中使用生成式 AI 必须声明（放 Declaration of interests 之后新节）。
- 标准语句模板：
  `During the preparation of this work, the author(s) used [NAME TOOL / SERVICE] in order to [REASON]. After using this tool/service, the author(s) reviewed and edited the content as needed and take(s) full responsibility for the content of the published article.`
- 基础工具（语法/拼写/参考文献检查）不用声明；AI 不得列为作者；AI 用于数据分析须在 Methods/STAR Methods 报告（不属于写作声明）。

## 3. Patterns 其他要点

- Presubmission inquiry 可发 patterns@cell.com（2-5 工作日，含标题+摘要+重要性说明）。
- 支持 Cell Press Multi-Journal Submission (MJS)。
- 预注册：Cell Press 鼓励假设检验研究预注册；回顾性描述性审计不能预注册，预注册未来试点的方法承诺是合规加分项。

## 4. OSF/Zenodo 预注册工作流（边界与分工）

| 环节 | 谁做 |
|---|---|
| 创建账号（邮箱验证、人机验证） | 用户本人（约 5-10 分钟） |
| 创建项目 + 公开提交预注册表单（学术承诺） | 用户本人 |
| 预注册文档（标题/摘要/材料清单/试点 estimands/信度协议/停止规则/元数据/FAQ） | agent |
| 上传材料包 zip（预注册文档+数据表+溯源+schema+编码手册+crosswalk） | agent 打包，用户上传 |
| 中文逐步操作指南（OSF 路线 + Zenodo 备选路线） | agent |
| 用户拿到链接后回填（Readiness Checklist / Data and code availability / README / 包索引） | agent |

要点：
- 材料包放 `02_supplement/osf_upload_package/`（00_Preregistration_Submission.md 为主文档，REGISTRATION_GUIDE_中文.md 为指南）。
- 许可用 CC-BY-4.0（与所引 OECD 报告一致）。
- 预注册文档结构：①标题 ②作者 ③摘要≤300词 ④预注册内容（研究问题 RQ/假设 P、设计、主终点、信度协议：双编码者/κ/AC1/裁决前分歧、缺失处理、停止规则、统计边界）⑤对应论文的 Patterns 资源段（可直接复制进手稿）⑥元数据与许可 ⑦材料清单 ⑧注册步骤 ⑨期刊政策 FAQ。
- 若用户不想现在注册：Readiness Checklist 该行保持"开放"即可，审稿期间再补。

## 5. 英文手稿 Statements 段 Cell Press 化模板

```
## Resource availability
### Lead contact
...
### Materials availability
This study did not generate new unique reagents. The protocol schema (...) is a computational artifact and is deposited in the data repository.
### Data and code availability
All analyzed material derives from public sources. [artifacts + links]. The prospective pilot is preregistered at [link], registered [date]. The repository meets the criteria for digital longevity, implementation of FAIR standards, and community support.
## Ethics
No patient data, protected health information, or human-subject data were used. No ethical approval was required.
## Declaration of generative AI and AI-assisted technologies in the writing process
During the preparation of this work, the author(s) used [NAME] in order to [REASON]. After using this tool/service, the author(s) reviewed and edited the content as needed and take(s) full responsibility for the content of the published article.
## Conflict of interest / Funding / CRediT / Preprint
```
