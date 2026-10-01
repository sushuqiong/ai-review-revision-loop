# 期刊选择与投稿包装 (Journal selection & submission packaging)

来源：课题2 GLM7×胆石症 **v18 定稿轮**。稿件内容已收敛后，剩下的全是「选哪本刊 + 把包打对」。
分两部分：**A 选刊**（判断与建议）／**B 包装**（可核验的合规清单）。

---

## A. 选刊

### A1. 用户会拿自己的「水刊清单」来对照你推荐的期刊

本用户的桌面上有一份 `SCI水刊合辑.docx`（约 100 本，含 `BMG Gastroenterology`、`PLOS ONE`、
`Digestive Diseases and Sciences` 等）。当另一个 AI（GPT6）给出投稿排序、而用户问
「你也觉得应该首选 X 吗？」时，**他真正在问的是「X 在不在我这份低层次名单上」**。

⇒ **回答前必须先读那份清单并逐条比对**（`python-docx` 读段落即可，纯文本列表）。
本轮实测：GPT6 推荐的**三本全部在用户的名单里**（BMC Gastroenterology 第 75 条、
PLOS ONE 第 20 条、DDS 第 79 条）——这个事实本身就是要说的第一句话。

### A2. 三方权衡，不要只说「匹配」

| 维度 | 要问的问题 |
|---|---|
| **适配度** | 收稿范围是否明确覆盖本稿结局与设计？（BMC Gastroenterology 明列消化疾病流行病学 + 胆石病 ✓）|
| **分层感知** | 该刊是否在用户的低层次名单上？投了是否「够格」？ |
| **费用** | APC（BMC Gastroenterology US$3,390；PLOS ONE US$2,477；DDS 订阅路线免 APC）|

**诚实结论模板**：「同意作为**务实首选**，但保留三点」——
1. 若用户要的是**发出来/被引用/流程顺**：同意；并明说本文新意水平使其**现实天花板就在中低档**，
   往上打（IF≈4–6 的 GI 刊）大概率因新意不足被拒或 desk reject，白耗 3–6 个月。
2. 若用户要的是**避开低层次**：BMC Gastroenterology **不能满足**，如实讲。
3. **可以并且应该给出与 GPT6 不同的意见**：本例本文核心是**阴性/不显著增量**结论，
   PLOS ONE **明确欢迎阴性结果**，故对本文是更"诚实匹配"的选择（且 APC 更低）；
   代价是它同样在名单上、且部分单位对其评价更低。给出**双选**并让用户拍板。

### A3. 「N 本刊都适配」时，用「先做包装、再投」把转投成本降到零

**包装要求取交集**：BMC 摘要上限 350 词、PLOS ONE 上限 300 词，**二者都要求摘要不列参考文献**。
⇒ 直接压到 **≤300 词且零引文**，两家都能投，转投无需重写。
**这是最省时的建议，优先于任何"要不要加分析"的讨论。**

---

## B. 包装（合规清单）

### B1. BMC 系列硬性要求（实测核查项）

```
[ ] 结构化摘要 Background / Methods / Results / Conclusions
[ ] 摘要词数 ≤ 350（BMC Gastroenterology）
[ ] 摘要内【零】参考文献引用  ← 踩过的点：方法段写数据来源时带了 [25][26]
[ ] 稿件类型命名正确（Research article）— 投稿系统与 Cover letter 都要对
[ ] Declarations 含: Ethics approval and consent to participate / Consent for publication /
    Availability of data and materials / Competing interests / Funding /
    Authors' contributions / Acknowledgements
[ ] 参考文献编号连续 + 正文【首现序严格递增】
[ ] 关键词若干（本稿 6 个）
[ ] 表数 / 图数 / 文献数在 Title page 与正文实测一致
```

### B2. 词数口径：**一次锁定、写明口径、三文件同步**

同一稿实测出现**三方打架**：Title page `6,999` / Cover letter `7,100` / 构建器 `6,690` /
实算 `7,260`。根因是**没人写过口径**，每个文件各按自己的感觉填。

⇒ 铁律：
1. 选定**一个**口径并**在 Title page 明写**，例如
   `Main text word count (Introduction through Conclusions, excluding section headings, table titles and figure legends): 7,260 words.`
2. **同样口径**同步 Cover letter 的 statistics 行。
3. 用**整篇扫描**统计（界定 `1. Introduction` → `Declarations`），不要只对某几段求和。
4. 摘要给出**两种口径**（含/不含 4 个结构标签）并注明差异，避免编辑自己算出来对不上。

### B3. Cover letter 要素清单（逐项可核验）

```
[ ] 日期（投稿当天改）
[ ] 称呼【指名期刊】← 踩过的点：只写 "Dear Editor,"，没写刊名
[ ] 投稿声明 + 【为何投这本刊】的 scope-fit 一句 ← 踩过的点：完全没有适配说明
    （例：「The study falls squarely within the journal's scope — digestive disease epidemiology,
      with gallstone disease as the outcome — …」）
[ ] What this study found（主结果 + 关键 CI/P）
[ ] How this study differs from what has already been published（含与既有评论/回复的边界）
[ ] Methodological points（本文的透明度卖点：设计顺序核验、bootstrap、桥接、IPW 三计数…）
[ ] Manuscript statistics（摘要词数 / 正文词数 / 表 / 图 / 文献）← 必须与终稿一致
[ ] 未一稿多投声明 + 无利益冲突 + 伦理说明
[ ] 基金（与 Title page 同一串号）
[ ] 署名 + 通讯作者联系方式
```

**数值一致性**：Cover letter 里的**每一个数**都要与终稿逐字对齐。本轮抓出 3 类不一致：
- 某层样本口径改了，Cover letter 仍是旧值（`1.415` / `0.833` → 应为 `1.425` / `0.827`）；
- 阈值表述漂移（`|ΔOR| ≤ 0.012` → 正文实为 `below 0.014`）；
- **最大效应量漏给不确定性**（只写 `+0.0064`，应写 `+0.0064 (95% CI −0.0004 to 0.0198)`），
  并按「小而不稳、但不能排除约 0.02 的正向增量」措辞——**审稿人/编辑最看重的就是这句**。
- 另：删除无意义遗留词（本例 `calibre` → `sample definition`；注意近形词可躲过禁用串扫描）。

### B4. Highlights

- 每条 **≤85 字符**（逐条打印字符数自检）；
- 数值与主稿同档（`1.633/1.416/1.996` → 可写 `1.63, 1.42, 2.00`）；
- **BMC Gastroenterology 不强制要求 highlights**（属可选/附加材料）——不要为它过度投入，但保留以便转投；
- ⚠ 若摘要用的是"放宽模型"的 P 值（本例 `P=0.0015`，而主要约束模型为 `P=0.028`），
  highlights 沿用同一取舍即可，但**要在 README 里标明这是有意取舍**，避免下一轮被当矛盾。

### B5. Title page 要素清单

标题 / running title / 作者 + 单位 + 共同贡献标记 / 通讯作者 / 摘要词数（含口径）/ 正文词数（含口径）/
表数·图数·文献数 / 关键词 / 补充材料清单 / Declarations（7 项）/ CRediT 分工 / 致谢。

### B6. 随稿上传的文件集

```
主稿（Research article）
Supplementary Materials（含最终编号，如 S1–S13 + Figure S1–S3）
全部图件（PNG + PDF，每图一个文件）
Cover letter
Title page
STROBE / 相应报告规范 checklist
（若声明"随稿提供代码"，则 Reproduction materials/ 必须真存在且文件名与声明逐项一致）
```

---

## C. ⚠️ 包装链路的一个高危陷阱（本轮真实事故）

**症状**：包装完成后，为取"权威词数"而重跑 `_build_docx_vN.py` →
**交付稿被静默覆盖回打包前版本**（摘要 299→342 词、Table S13 消失、7 表→8 表）。

**根因（两步叠加）**：

1. **包装是直接编辑 docx 做的**（`_vN_bmc_pack.py` 用 python-docx 改 docx），**没有回写内容模块**；
   而 `_ms_content_vN.py` 仍是打包前的状态 ⇒ **模块陈旧**。
2. `_build_docx_vN.py` 是**生成器**：它不"更新"而是**覆盖**输出文件。
   ⇒ 用陈旧模块跑生成器 = 用旧版本覆盖交付稿。

**✓ 铁律**：

```
[ ] 只要交付稿是"打补丁"改出来的，**绝不要**再跑生成器 —— 除非先把模块同步。
[ ] 交付稿定稿后立刻做一份**不可被脚本覆盖**的备份（_bak/vN_final/），并在事故恢复时优先用它。
[ ] 恢复链：① 从"包装前备份"还原 5 份 docx → ② 重跑包装脚本 → ③ 重跑后置修正脚本
    → ④ 跑合规校验。**每一步都保留脚本**（可重跑是唯一能救回来的原因）。
[ ] 把这条写进 README 顶部警告 + 附上正确的四步重建命令。
```

**更深的教训**：`_extract_*_content.py` → 改模块 → 构建，这条"可复现链"**只有在每一轮都坚持**
才有意义。一旦某轮改成打补丁，**链条就断了**，而且断裂是**静默的**——
下一次有人（包括你自己）跑生成器时才会暴露，那时交付稿已被覆盖。

---

## D. 收尾自检（打包完成后跑一遍）

```python
# 1) 摘要：词数 + 零引文
abst = [p for p in paras if p.strip().startswith(("Background:","Methods:","Results:","Conclusions:"))]
assert sum(len(re.findall(r"\S+", p)) for p in abst) <= 350
assert sum(len(re.findall(r"\[\d", p)) for p in abst) == 0
# 2) 声明 7 项（撇号归一化后再匹配，见 docx-programmatic-edit-safety.md §12）
norm = text.replace("\u2019", "'")
for k in ["Ethics approval and consent to participate","Consent for publication",
          "Availability of data and materials","Competing interests","Funding",
          "Authors' contributions","Acknowledgements"]:
    assert k in norm, k
# 3) 计数声明 vs 实测；4) 引用编号连续 + 首现序无逆序
# 5) Sn 与 Figure Sn 全部被正文引用；6) 声明点名的文件真实存在（含 Reproduction materials）
# 7) 三文件的摘要词数 / 正文词数 / 表数 一致
# 8) Cover letter 关键数值与终稿逐字对齐（含最大效应量的 95% CI）
```
