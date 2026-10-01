# 建议审稿人名单 + 公开邮箱检索

触发：投稿系统问 "suggested reviewers"，或用户说「起草建议审稿人名单，单独保存一份 Word 放桌面」。

## 一、★ 本用户的两条硬要求（v19 轮被明确纠正过）

用户原话：

> 「你写的《建议审稿人…》**太啰嗦、而且英文我看不懂**，另外，**他们的邮箱你不会直接帮我查询吗？**」

| 要求 | 做法 |
|---|---|
| **交付文档用中文** | 正文说明、推荐理由、用法、提示**全部中文**；只保留**必须英文**的部分（学者姓名、机构英文名、以及要粘进 Cover letter 的那一段）。**不要**整份文档用英文 |
| **精简** | 目标 **≤2 页 / ≤2,500 字符**。第一位候选人的版本写了 11 页 5,600 字符被投诉。做法：每人 4 行（姓名 / 单位 / **邮箱** / 一句推荐理由），不要长篇 "Why suitable" 论述 |
| **邮箱必须查好** | **禁止留 "E-mail source: …" 之类的占位符**。用 `scripts/pubmed_corresponding_emails.py` 直接查出真实邮箱填进去 |
| **查不到的如实标注** | 查不到的单独列「备选（需自行核验）」，写明去哪找（机构个人主页 / 该文通讯作者）。**永不编造邮箱** |

> 桌面只留**一份**文件。改了之后要**删掉旧的冗长版本**，否则用户会拿旧版对照再投诉一次。

## 二、候选人的选取：从**本文参考文献**里出（可溯源、零编造）

1. 提取主稿 Reference 列表。
2. 按**三类**各选 1–3 位，覆盖面最均衡：
   - **疾病流行病学**（本结局领域最权威的队列/Meta 分析作者）
   - **暴露指标原创者**（本文评价的复合指数的提出者，或对照指标的提出者）
   - **统计方法学**（复杂抽样 / 增量判别 / OR-vs-判别 的方法论文作者）
3. 每位都写清**对应本文哪篇文献**（如「你文献[6]的作者」）——这是最有力的推荐理由，也便于用户核对。
4. **检索式用作者字段**，见 §三 的坑。

### 必备：回避名单（写进 Cover letter）
- 被评价指标的**原始论文作者**与**回复作者**
- 针对该指标发表**评论/来信的作者**（本文若专门讨论该评论）
- 本稿**全体作者**及其近期合作者
- 作者**本单位**（含附属医院）任何人员

## 三、邮箱检索：`scripts/pubmed_corresponding_emails.py`

```bash
python scripts/pubmed_corresponding_emails.py --author "Pepe MS" --author "Portincasa P" --hits 5
python scripts/pubmed_corresponding_emails.py --query 'Cook NR[au] AND receiver operating characteristic' --hits 6
```

原理：NCBI E-utilities `esearch` → `efetch`（XML），从 `<Affiliation>` 里取**论文中印出的通讯作者邮箱**。
邮箱**可溯源到 PMID**，属公开学术信息。

### ★ 五个实测踩过的坑
| 坑 | 表现 | 防法 |
|---|---|---|
| **只按标题检索会查错人** | 查 `"Pepe MS" + limitations of the odds ratio` 返回一篇**腹放线菌病病例报告**；查 Cook 返回 Steyerberg 的邮箱 | **用 `[au]` 作者字段**（脚本 `--author` 已自动加） |
| 单篇 XML 可能没印邮箱 | 同一个人的某篇没有，另一篇有 | **逐篇试多个 PMID**（`--hits`），试到命中为止 |
| 取到出版商编辑部邮箱 | `epub@benthamscience.net` | 过滤 `nlm/ncbi/elsevier/springer/wiley/oup/bentham/frontiers/…`（脚本内置） |
| **取到的是共同/资深作者的邮箱** | 查 Bello-Chavolla 得到的是 `caguilarsalinas@yahoo.com`（该文通讯作者是资深作者） | **人工核对标题+作者**，如实写成「该文通讯作者为 X，可先联系他转达」 |
| 有些人 PubMed 根本没印 | Cook / Lumley 多篇均无 | **如实报告查不到** + 指引机构个人主页。**不编造** |

### 命中率参考（v19 轮实测 10 人）
命中 **6/10**：Shabanzadeh、Portincasa、Aune、Guerrero-Romero、Pepe、Vickers。
未命中 **4**：Cook、Bello-Chavolla（只得共同作者）、Lumley（R survey 包作者）、Lammert/Wang（只得出版商邮箱）。

## 四、可直接粘贴进 Cover letter 的英文段（模板）

> Suggested reviewers (institutional e-mail addresses): Prof. A (a@inst.edu); Prof. B (b@inst.edu);
> Prof. C (c@inst.edu). We have no co-authorship, supervisory, funding or institutional relationship with
> any of them. We request exclusion of the authors of the original \<index\> paper and its reply
> (refs. X, Y), the authors of the published comment (ref. Z), and anyone affiliated with our own institution.

（正文其余部分仍走 `references/journal-submission-compliance.md` §二 的 Cover letter 5 项要求。）

## 五、文档骨架（照抄，控制在 2 页内）

```
建议审稿人名单（<期刊名>）                     ← 标题，中文
稿件：<一句话>                                  ← 斜体小字
用法：投稿系统与 Cover letter 各填 3–5 位；以下邮箱均已从 PubMed 官方记录核实，可直接使用。  ← 1 句

1. <姓名>                                      ← 加粗
单位：<国别 机构>
邮箱：<邮箱>                                    ← 加粗 + 红色，方便用户抄
推荐理由：你文献[6]的作者。<一句话>。

… 重复 6 人 …

备选（邮箱需你自行核验，PubMed 未印出）          ← 加粗
- <姓名>（机构）—— <一句>。可到其<机构>个人主页查邮箱。

务必声明回避的人（写进 Cover letter）           ← 加粗 + 红色
- <列出>

可直接粘贴进 Cover letter 的英文段              ← 加粗
<§四 的模板段，斜体>

小提示                                          ← 加粗
- 建议用第 1、4、5 位…（各方向一位，命中率与说服力较均衡）
- 这些是已发表的通讯作者邮箱，属公开学术信息；若某位回复不便审稿，编辑会另找人，不影响投稿。
```

要点：**邮箱那一行是用户唯一要抄的东西** → 加粗 + 红色，让它跳出来。
