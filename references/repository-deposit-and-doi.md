# 数据仓库归档与 DOI 回填（本用户：非开发者，Zenodo + GitHub 登录）

触发：稿子定稿、编辑/审稿人要求"数据集必须归档并给 DOI"（Scientific Data 第二轮起强制），
或用户说"DOI 后面再补，先做其它"。**DOI 一定要留占位并在拿到后回填**，不要手写假 DOI。

## 一、用户的既定偏好（照此默认执行）
- 仓库：**Zenodo**（用户已有 GitHub 登录，不要再让 ta 注册新账号）。
- 顺序：用户明确说"**还要改几轮呢，DOI 后面再补**" → 先把正文/包做完并留
  `[DOI to be inserted after Zenodo deposit]`，最后回填；不要为等 DOI 停工。
- 交给用户的操作必须**点击级**：菜单名 → 按钮名 → 编号步骤，并给"先看这个"文件名。
- 上传物 = **一个 ZIP**，文件名自解释（如 `★Zenodo上传-就选这个_v12.zip`）；
  另出一个投稿用 ZIP（稿件+图+封面信+指南）。

## 二、给用户的点击级步骤（可直接复用/改写）
1. 打包：把数据集目录压成 ZIP（脚本里 `shutil.make_archive`，输出到桌面，名字带 ★）。
2. 打开 https://zenodo.org → 右上角 **Sign in** → **Sign in with GitHub**（授权即登录）。
3. 头像 → **New upload**（或 https://zenodo.org/uploads/new）→ **Choose files** 选那个 ZIP。
4. 填元数据（**把下面模板整段贴给用户**，别让 ta 自己想描述文字）：
   - Upload type: `Dataset`；License: **CC BY 4.0**（Scientific Data 不接受 -NC/-SA）
   - Title / Description（含 scope、contents、limitations 三段式）/ Keywords 10 个左右
   - Related identifiers: `is supplemented by` → GitHub 仓库 URL
5. **Save draft** → 三项核查（Title / License / 文件）→ **Publish** → 得到 `10.5281/zenodo.xxxxxxxx`。
6. **首轮投稿允许匿名链接**：记录页 **Share → Copy link** 即可给审稿人；第二轮前必须 Publish。
7. 可选：代码也拿 DOI —— 见下面「二·补」，**本用户惯用这条**。

---

## 二·补 GitHub 集成拿 DOI（本用户惯用路径；2026-09 实测）

用户说"**之前我都是用 GitHub 上传的**"= 指 Zenodo 的 **GitHub 集成**，不是手动拖 ZIP。
优先走这条（ta 熟），**仓库须 public**（Zenodo 集成只能读公开仓库）。

只有第 2 步要用户动手，其余 agent 全程命令行可完成：

1. 建仓推送：
   ```bash
   gh repo create <name> --public --source=. --remote=origin --push
   ```
   仓库根放 `.zenodo.json`（预填元数据，**实测有效**，license/creators 会正确带进去——
   排查故障时**不要先去改它**）+ `README.md` / `LICENSE` / `CITATION.cff`。
   推送前扫一遍敏感信息（`grep -rIn -i "api[_-]\?key\|token\|secret\|sk-\|gho_" .`）。
2. **用户操作（点击级，照抄给 ta）**：
   `https://zenodo.org/account/settings/github/` → 找仓库（没列出就点 **Sync now**）→ 开关拨 **ON**
3. **自己验证开关真生效，不要靠用户口述**：
   ```bash
   gh api repos/<owner>/<repo>/hooks --jq '.[] | {url: .config.url, events}'
   ```
   必须看到 URL 指向 `zenodo.org/api/hooks/receivers/github/events/` 且 `events: ["release"]`。
4. 发 release：
   ```bash
   gh release create v1.0.0 --title "..." --notes-file /tmp/notes.md
   ```
5. 查投递状态：
   ```bash
   gh api repos/<owner>/<repo>/hooks/<hook_id>/deliveries \
     --jq '.[] | "\(.delivered_at) \(.event) \(.status_code)"'
   ```
   - `202` = **Accepted**（Zenodo 已收，进队列）
   - `409` + body `"The release has already been received"` = 重复投递，**无害**
   - `ping` / `202` = 刚开开关时的握手

## 二·补2 时序：**不要过早判定失败**（本项目最贵的一课）

- **归档有队列延迟**：实测 **release 15:56 发出 → Zenodo 记录 16:35 生成，约 39 分钟**。
- 这段窗口内：**公开搜索 API 命中 0**（`/api/records?q=...`），
  **用户看 `https://zenodo.org/me/uploads` 也可能是空的**。
  这两件事**都不能**证明失败。
- ❌ 错误做法：等 6 分钟搜不到 → 怀疑 `.zenodo.json` → 改名 → 再发 v1.0.1、v1.0.2 试错。
  结果 concept 下多出一串内容几乎相同的重复版本，还要向审稿人解释。
- ✅ 正确做法：**先确认 webhook 存在 + 投递码 202**，然后**用已认证接口查**（不依赖搜索索引）：
  ```bash
  curl -s -H "Authorization: Bearer $TOK" \
       "https://zenodo.org/api/deposit/depositions?size=25"   # size 上限 25
  curl -s "https://zenodo.org/api/records/<conceptrecid>"     # 取最新版
  ```
  用户建 token：`https://zenodo.org/account/settings/applications/tokens/new/`
  → scopes 勾 `deposit:write` + `deposit:actions`。**用完提醒 ta 立即 Revoke**——
  用户确实会马上吊销，之后再调返回 `403` 是**预期的**，不是环境问题。

## 二·补3 引用哪个 DOI：优先 **concept DOI**

一次修订常产出多个版本（内容相近）。此时正文 Data Availability 引用 **concept DOI**
（`conceptdoi`，形如 `10.5281/zenodo.<conceptrecid>`）——它**恒定解析到最新版**，
不用因为补了一个附件就重发手稿。版本 DOI 留给"必须钉死某一版"的场合。

- 占位符仍先写 `[REPOSITORY DOI]`，拿到后回填 concept DOI ＋
  一句 `(concept DOI, resolving to the latest version)`。
- **回填点 ≥2 处**：Data Availability ＋ 正文首次介绍补充材料的那一段。
- 回填后**重新生成 docx**，并断言 `old_doi not in full_text`（本项目漏过一次）。

## 三、描述文字模板（按实际内容替换数字）
```
Curated resource that reorganises public human tissue transcriptomes into a comparable,
annotation-rich form for cross-disease reuse.

Contents: (1) cohort registry with source accessions, platforms and origin publications;
(2) sample-level annotation including tissue type, case-control role, paired relations and
documented exclusion reasons; (3) gene-mapping and transformation provenance; (4) seventeen
module definitions with per-platform gene coverage and sample-level scores; (5) expression-derived
composition scores with four aggregated compartments; (6) patient-level summaries and donor-aware
comparisons from single-cell datasets, with raw and curated cell labels kept separate;
(7) a complete estimates layer including non-significant and non-estimable results;
(8) quality-control records; (9) two runnable reuse examples with expected outputs;
(10) software environment and run order.

Scope: {N} case-control cohorts ({n_assay} assay records, {n_patient} unique patients,
{n_platform} platforms) across ten contexts. Derived data released under CC-BY-4.0; source data
remain under the terms of GEO, TCGA/GDC (via cBioPortal) and CELLxGENE.

Limitations: module gene coverage is incomplete for part of the cohorts; composition scores are
enrichment scores rather than cell proportions; cohort count is not patient count; the resource is
not a patient-level multi-omics resource; module scores are not validated prognostic tools.
```

## 四、拿到 DOI 后回填清单（一次性做完，别漏）
1. 正文 Data Availability 与 Code Availability 的占位符 → 换成 `https://doi.org/10.5281/zenodo.xxxxxxx`
2. `dataset_package/00_README.md`（How to cite / repository 段落）
3. 交付包 checklist 与 `04_评审记录与报告` 的最新报告
4. 重新生成 docx/pdf + 校验清单（inventory/checksums 会因 README 改动而变化）并推送 GitHub
5. 归档记录写进报告：DOI、发布时间、版本号（后续更新用 **New version**，绝不覆盖旧 DOI）

## 五、坑
- 仓库要求 **单一下载单元 + https 直下 + 匿名可访问**；不要把数据拆成几十个零散文件传。
- 不要写"all primary data are already public and no additional data deposit is required"
  （上游公开不能替代你新生成的派生数据归档）。
- `no new data were generated` 必须改写为"未采集新人体样本，但生成了新的整理与派生数据"。
- CELLxGENE 等来源要补完整 dataset/collection ID 与版本，不能只写短编号。
