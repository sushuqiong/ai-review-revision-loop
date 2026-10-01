# md ↔ docx 往返的补丁安全与投稿包流水线（血泪版）

背景：CKM/eGDR 稿件 v9→v16 全靠 `05_英文稿件_manuscript_final.md`（单一真源）→ pandoc → python-docx 三线表 → 交付 docx。
一旦为了"救回被改坏的文件"做 `pandoc docx → gfm` 往返，下面每一步都会咬人；每次都用脚本先审计再动手。

## 1. pandoc docx→gfm 的四个隐形破坏
1. **转义**：`[12]` 变 `\[12\]`、`_` 变 `\_`、`*` 变 `\*`（S4 的 `1 - exp(-H0*exp(lp))` 就这样逃过多次补丁）。
   → 先 `s.replace("\\[","[").replace("\\]","]").replace("\\_","_")`，公式改用内联 code 包住。
2. **YAML/metadata 丢失**：title/author 块没了，标题整段消失（匿名化脚本因此被评审说"标题被一起删掉"）。
   → 重建 docx 前必须确认 md 顶部有 `---\ntitle: "..."\n---`；匿名版**保留 title、只掩作者**。
3. **图片变 HTML 且无实体**：`<img src="media/rId24.png" style=... alt="Figure 1" />`，media 文件并未导出。
   → 用正则换回 markdown 绝对路径：`<img src="media/[^"]*" ... alt="Figure N" />` → `![Figure N](C:/.../图表/FigN_*.png)`；重建后核对 docx `media` 部件数（本例应为 6）。
4. **表格管道被压扁**：`| Model | HR |` 变 `|Model|HR|`，所有基于表格行的字符串锚点全部 MISS。
   → 改表格优先"整表重写 + 分节切片"，不要逐格 replace。

## 2. 绝对禁止：对 md 用 `re.sub(r"\s+", " ", s)`
本会话用它做"空格清理"，把**全部换行压成空格**，整篇 markdown 结构当场毁掉，只能靠 docx→gfm 抢救。
→ 清理只允许 `re.sub(r"[ \t]+", " ", s)`（不含 `\n`）。

## 3. 补丁锚点纪律（本项目 MVP 教训）
- 字符串锚点会随每次重排漂移 → 每次 patch 先 `print(s.find(anchor))`，MISS 就打印上下文再改。
- 大段修改优先**按标题切片**：`a = s.find("**Transportability (same outcome).**"); b = s.find("\n\n**", a)`，整段替换，不做局部拼字。
- 引用编号脚本（renumber-by-first-appearance）必须显式声明目标文件常量：
  本会话 `renumber_clean.py` 的 `P` 仍指向旧的 `..._v9_raw.md`，连续多轮"重排成功"实际都在改旧文件，导致新引用永不入表（`total refs: 22` 卡死）。
  → 动引用前先 `grep 'P = r"' renumber_clean.py`，并核对输出的 refs 数 = 预期条数。
- 基金号里的 `[2023]1` 会被引文扫描当成编号 → 改为 `(2023-1)`。
- 补充材料块会互相穿插 → 收尾时按 `**Supplementary Table S(\d+)` 提取全部块、按数值排序重建（本例 S1–S17 一次性归位）。

## 4. 三线表与交付校验（本机固定流程）
- 必须用 `D:\ProgramData\python.exe`（系统 python 曾 exit 2）；样式 = 顶/底 `w:sz=12`、表头下 `w:sz=6`、`insideV/insideH = none`。
- 每次构建后打印三个数：`len(d.tables)`（含新表后应为 10）、`media` 部件数（6）、表头边框特征；有一样不对就不算完成。
- 匿名版 = 从同一份 md 正则掩掉：author/affiliations/email/机构/**基金号**（评审会查"匿名是否彻底"），标题保留；建完用 `github.com`/邮箱/姓名/机构关键词做 assert。
- 投稿包：单盲+双盲手稿、对应两版 Cover letter（标题与最新数字必须同步）、Submission checklist、TRIPOD+AI、图 PNG **和** TIFF 300dpi、Code_bundle、README；git-bash 里没有 `zip` → 用 python `zipfile` 打包（本例 194 条目）。

## 5. 多 AI 评审回合的固定产物
每轮为每个评审源各出一份 `Response_<GPT6|Hy4>_vN_to_vN+1.md/docx`（意见→处置→位置三列，内部质控不随稿投稿）。
用户会拿它判断"是否逐条回应到位"；缺这份就会被要求返工。
