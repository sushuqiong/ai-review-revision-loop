# 数据资源包的复现性与元数据卫生（Reproducibility & metadata hygiene）

**触发**：数据期刊（Scientific Data 等）审稿人问"checksum 设计""能否一键复现""版本号是否一致"
"数据集清单/流程数字对不上"。这类意见看似琐碎，但会被直接当作"复现未完成"扣分。

## 1. checksum / manifest 设计
- **校验清单不能包含自身**。`sha256sum -c` 的清单里只放**数据文件**；
  清单文件（inventory、checksums）自身的摘要**另写** `08_qc/manifest_checksum.txt`。
- README 写明验证命令：`sha256sum -c 08_qc/checksums_sha256.txt`（在包根执行）。
- 反例（曾被审稿人点名"设计不理想"）：`N files, with N−2 SHA-256 entries because the two
  verification files are self-referential` —— 这种解释性措辞应改为**结构性设计**（分文件）。

## 2. 正文里的数字必须"活取"，不能写死
- 文件数/校验数/文件夹数一律在构建时从实时清单计算并回填句子
  （正则刷新：`(\d{2,4}) data files`、`as \w+ folders`）。
- 实测：每加一个新文件（config.yml、requirements.txt…）都会让写死的 "107 files / 105 SHA" 过期，
  连续两轮被审稿人抓到 → 把"数字刷新"作为构建脚本的一步，而不是手工更新。

## 3. 版本号统一（发布号 vs 冻结模块号）
- 统一 **release 标识**：正文 tag、`00_VERSION.txt`、README、manifest、Git tag 必须一致（例：16.0）。
- 若某个组件**故意保持旧版本号**（如基因集自 v12 冻结未改），**必须加显式版本说明**：
  "module_version = v12.0-frozen-2026-09；17 个模块定义自 v12 冻结、本版未改动，故与发布号不同"。
- 绝不静默混用版本号。

## 4. 输入状态登记表（解决 "N vs N+1" 之争）
一张表解决所有"数据集数量矛盾"：每行 = **层级 / 状态 / 是否进入估计 / 是否产生可检验比较 / 原因**，
并带**数据集标识与版本**（单细胞：CELLxGENE collection UUID + dataset version + source DOI + 细胞数）。
- 被排除的数据集也要给全标识（否则"图上出现 117,266 细胞但正文只列 4 个输入"会被抓）。
- 摘要按"复核 N / 处理 M / 可检验 K / 排除原因"四段式表述，全局只用一个口径。

## 5. 筛选流程对账（让算术显式成立）
- 造一张流程表并**写出等式**，例如：`31 = 26（病例-对照）+ 1（treatment-response）+ 1（外部验证）+ 3（下载未采纳）`。
- 只在 Data Availability 出现、却在 Input data 未说明的系列（如外部验证队列）必须补一句定位。

## 6. 一键复现 + 干净目录测试
- 脚本路径解析改为 **config.yml + 脚本自身位置回推根目录**（`while (!file.exists(file.path(d,"00_VERSION.txt"))) d <- dirname(d)`）。
- **必须真的在干净副本里跑一次** shipped example，并把 `exit 0/非0` 与尾部输出记入
  `08_qc/qc_clean_directory_run.csv` —— 正文才敢写 "已在干净副本验证无绝对路径"。
- 源数据下载清单：accession + 检索日期（用本地文件 mtime 作为代理并**注明是代理**）+ 本地重建输入 sha256 +
  提供方 URL（`https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=<GSE>`）。

## 7. 工作区创建的坑
- 复制工作区后**必须验证顶层结构与文件数**：`cp -r` 落到已存在目录会生成**嵌套副本**
  （`v16/v15/...`），后续脚本静默写到错误位置。复制后立即 `ls -1 <dir>` + `find <dir> -type f | wc -l`。
- 长数据库任务用**受管后台**运行（terminal background=true + notify），不要用 shell 的 `nohup ... &`
  —— 工具调用结束后进程会被回收，日志空、误判为"已完成"。

## 8. 产物交付命名（本用户硬偏好）
- 数据资源线**只输出** `★Zenodo上传-就选这个_vN.zip`，且**放在项目文件夹内**
  （如 `C:\Users\fengq\Desktop\EGFR\★Zenodo上传-就选这个_v16.zip`），不要留在桌面根目录。
- **不要再生成 `★投稿上传-就选这个…` 包/文件夹**（用户 2026-09 明确要求取消）。

## 9. 结构型审计项（文档构建器替换时最易回归）
换成新的 docx 构建器/排版脚本后，必须复验这些**结构性**事实（文本类检查抓不到）：
- 正文内嵌表仍在（`len(doc.tables) >= 1`，Table 1）；
- `Figure captions` 标题**只出现一次**（正文若已有 `**Figure captions**` 段，构建器不要再加一份）；
- 内嵌图与磁盘 PNG **逐字节一致**（sha256 比对），图数 = 预期；
- 上标 run 数与正文编号数一致；`^1` 单位标记渲染为真上标；
- 最终必须重跑清单+重打包（任何一次 docx 重建都要重算 checksum）。
