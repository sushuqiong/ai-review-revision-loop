# 代码发布与构建卫生（Code Release & Build Hygiene）

> 触发：论文声明 "code available at GitHub"、外部 AI 审稿要看/核脚本、或需要从冻结结果重建
> 图表/正文/投稿包。核心纪律：**审稿人会真的下载你的仓库跑**——发布物必须能读、能追、能复现，
> 修改过的结论必须带更正说明。

## 1. 仓库最小可用集
- `scripts/`（按阶段分子目录，如 `atlas_pipeline/`、`vN_reruns/`；文件名保留编号，便于按顺序复现）
- `config/`（**所有基因集/参数文件**；最常被审稿人抓的缺口：脚本读 `config/gene_sets_extended.csv`
  但仓库里没有它）
- `results/`（冻结结果表：证据矩阵、meta、外部验证、逐队列表）
- `manuscript/`（正文 md，便于对照数字）
- `reports/`（每轮修订单据：v7…v16，含 bug 修复与重算说明）
- `tests/`（验证脚本 + 运行日志）
- `ERRATA_vN.md`（**关键**：外部审稿抓到的实现错误、影响范围、修正前后数字，逐条写清）
- `LICENSE`（代码 MIT 常见）、`README.md`（overview → 目录 → 运行顺序 → 路径说明 → 验证方法）

## 2. 路径问题（审稿人最常抱怨）
- 绝对路径（`C:/Users/xxx/...`）必须处理：要么改相对路径 + `BASE_DIR`，要么在 README 明确写
  "scripts 里的 `ROOTS` 为分析机示例路径，请改为本机布局"，并在每个脚本顶部集中定义 `ROOTS`。
- 依赖预生成的本地 RDS 时，在 README 列出生成顺序（哪一步产出哪个对象），不要只给中间脚本。

## 3. 幂等与可复现核验（发布前必跑）
- 同输入连跑两次核心输出一致（禁止 `-1` 翻转类补丁脚本；参照水平在模型里显式设定）。
- 打乱样本顺序、按 ID 连接后核心结果一致。
- 手算一个小例子与程序输出比对。
- 测试脚本 + 日志一起入库（`tests/check_*.R`、`tests/*_log.txt`）——外部审稿看到测试会显著加分。
- **把"正文数字 vs 冻结结果表"的核验也做成脚本入库**：`scripts/manuscript_number_provenance_check.py`
  （配 `templates/manuscript_number_provenance_rules.json`）从结果表重算头条数字、断言正文含该字符串、
  扫描旧数字残留与引文顺序，非零退出即未通过。仓库里放一份带 `stale` 列表的规则文件，
  审稿人能自己跑通"数字确实来自这些表"这一步。
- 发布后在干净目录 `git clone` 一次，按 README 跑通最小示例再宣布完成。

## 4. 构建链卫生（本轮踩到的坑）
- **脚本顺序**：分节构建脚本（builder）与收尾脚本（finisher）不可乱序重跑——重跑 builder 会用旧源
  覆盖 finisher 的成果。做法：builder 只产出，finisher 只在前者之后运行；或在 builder 中做幂等检测。
- **git-bash heredoc 吞反斜杠**：`python - <<'EOF'` 里的 `\\uXXXX`/正则容易被打散成 `\u`。
  涉及反斜杠、Unicode、正则的脚本一律写成 `.py` 文件再运行，不要走 heredoc。
- **Unicode 转义残留**：用 Python 字符串拼 `\u2265`、`\u03b2` 时若误写成双反斜杠，会以字面量写入 md。
  收尾固定加一遍 `re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1),16)), s)`，并扫描残留为 0。
- **多副本一致性探针**：工作目录 / 投稿包 / Git 仓库三处逐文件比对关键词（版本号、新数字、GitHub URL）。
  实际发生过 `cp` 静默未覆盖、主包 md 比工作区旧一个版本的情况——不要假设 cp 成功。
- **图表必须从冻结结果表生成**：图上总结数字（如 "55/73/19" 旧版）最容易残留；重新生成后逐图核对
  正文引用数字与命名（模块名 EPH vs EPH_RECEPTORS 不一致会导致整行灰块）。
- **空操作补丁会触发文件校验警告**：`patch` 的 `old_string` 与 `new_string` 相同时工具会拒绝（identical），
  文件确实未被修改，于是文件变更校验器报 "N file(s) were NOT modified this turn"。**不要发相同字符串的补丁**；
  若用户追问该警告，用 `git status` + 读该文件 + 查脚本产物时间戳三件事回答"未修改是正确结果"。
- **含中文的路径不要写字面量**：同一台机器上，另一个 Python 环境（venv）可能无法解析含中文的路径字面量
  （`os.path.exists` 返回 False 而目录其实存在）；且项目目录可能嵌套在想不到的位置
  （本项目实际是 `Desktop\EGFR\EGFR胃癌\EGFR_ERBB_context_project_v1`，不是 `Desktop\EGFR胃癌\...`）。
  做法：用 `Path(base).rglob("<project_dir_name>")` 动态定位（挑带 `data_raw/` 的那个），并打印实际使用的路径。
- **单细胞 h5ad 脚本要用项目自带 venv 的解释器**：通用 Python 常出现 `h5py/numpy` ABI 不匹配
  （`numpy.dtype size changed`）；优先用项目内 `.sc_venv/Scripts/python.exe`（本项目该环境 numpy 1.26 / h5py 3.11 可用）。

## 5. 更正说明（ERRATA）写法
- 逐 bug 一节：症状（审稿人可观测迹象）→ 根因（贴出错误代码行）→ 修复（贴出正确写法）→
  影响范围（哪些样本/队列被静默丢弃、哪些结论作废）→ 修正前后数字对照。
- 若同一 bug 修了两轮才彻底，要把"第二轮"也写进 ERRATA（例如：第一轮修复仍用子集位置索引整向量，
  经三重验证脚本发现后二次修正；median r 从 0.99 假象纠正为 0.11）。
- 正文的 Limitations / Data & Code availability 中一句话指向 ERRATA，并声明"所有数字均来自修正管线"。
