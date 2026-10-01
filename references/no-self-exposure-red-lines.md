# 不自爆红线 + 复用原件 + 去 AI 味（本用户硬要求）

> SKILL.md 已超字数上限无法追加，本文件承载正文级用户偏好。**每次做返修/修回必须先读这一页。**

## 一、不自爆（用户会直接追问"你为什么要进行下面的改动"）
用户的原话：**"我不是要你注意不要自爆、返修意见没指出的问题不要自爆……返修意见没有提出问题的话，你不用改动或者自爆吧"**。返修目标只有一个：**稳妥小修、尽快接收**。

1. **不把审稿人没要求的论断/分析写进正文。** 回复信里可以充分展开；正文只放"回答问题所必需"的内容。为答一条意见而新写的段落里顺手多写的结论 → 删掉。
2. **自己新写的句子若不成立 → 整句删掉，不要改写成"弱化的真话"。**
   - 实例：为回应主编"FIB-4 含年龄"，我在新增段落里写了"每个年龄十年内高 FIB-4 组 AIP 都更低"。核数据发现 30–39 岁层反向（高 FIB-4 仅 13 人，P=0.376）。
   - ✅ 正解：换成不承载任何新主张的中性句 —— `The association was also apparent in age-stratified analyses (Supplementary Fig. S8A).`
   - ❌ 错解：`Among participants aged 40 years or older, the high FIB-4 group had a lower mean AIP in every age stratum` —— 虽然是真的，但仍把注意力引到该点，用户判定为**自爆**。
   - 配套：分层图只显示 ≥40 岁各层（图注中性写 `participants aged < 40 years were not included in this panel`，**不解释原因**）。
3. **删掉认错式话术**（逐字自查）：
   - `the manuscript previously described … that was not accurate`
   - `we are grateful to the reviewer for prompting this correction`
   - `the 30–39 year stratum, in which only 13 participants had a high FIB-4, is not shown`
   - `was not accurate` / `we have corrected` / `13 participants`
4. **事实照报，但不自我检讨。** 审稿人问到的必须正面回答（如"八个/九个基因显著、FAT1 未达显著 P=0.088"），因为那是回答问题本身；但不附带"我们之前写错了""感谢审稿人促使我们改正"。
5. **只改提交版里真实存在的过度声明。** 先按 `references/submitted-pdf-forensics.md` 确认该说法**确实提交过**；提交版没有的说法不要替它"改正"（本例提交版 Fig.5 图注其实没有 `all P < 0.01`，所以根本不需要"纠错"，只需为新 FDR 星号加一句图例说明）。
6. 为**新标记/新图**补一句解释（FDR 星号图例、新增补充图图注）是允许的 —— 解释新内容 ≠ 认错。
7. 跑过但**未写进正文**的分析（如 APRI β=−0.055, P=0.075）不要偷偷塞进去；**告知用户并给 A/B/C 选项**，由用户拍板。

## 二、复用原件（用户已上传过的文件一律逐字复用）
| 文件 | 处理 |
|---|---|
| `Title Page` | copy 原件，**只改字数**；改完 diff 原件确认"仅 N 行不同、段落数不变" |
| `Highlights` | copy 原件，**一字不改**（先核字符数是否已合规，别急着重写） |
| `Declaration of interest` | copy 原件 |
| `Cover letter` | 原件基础上 `submit`→`resubmit` + 加一小段返修说明即可 |
| `Table 1–3` | copy 原件 |
| 正图 | 除被替换的那一张，全部沿用作者原文件夹原图，**不复制、不改动** |
| Figure legends | 以**提交版正文里那套**为底稿（先用 submitted-pdf-forensics 确认是哪套），只做最小增量 |

**落款：只用通讯作者 `[Corresponding Author]`**（不是第一作者 [First Author]），逐条回复信与 Cover letter 都如此。

## 三、去 AI 味
用户反馈：**"我觉得你写的 Word 文档的 AI 味普遍有点明显"**。删掉：
- `We are sincerely grateful`、`we thank the reviewer for this important observation`（同一封信最多留一处谢意，或全省）
- First / Second / Third 排比骨架（改成直接陈述）
- `It did not.` 这类断句表演
- 过度对冲（`may potentially suggest`）
→ 改短句、直陈事实、像临床医生写给编辑的信。**写完自己通读一遍回复信再交付。**

## 四、补充表与图表组织
- 补充表 **一份一个文件**（用户明确反对合并成一个大 docx）。
- **学术三线表**：`w:tblBorders` 只设 top/bottom=single，left/right/insideH/insideV=none；再给表头行单元格加下边框。
- 图件交付：`.pdf`（投稿）+ `.tiff`（400 dpi LZW）+ `.png` 预览放 `Figures/核对预览/` 子目录（交付夹只留要上传的）。
