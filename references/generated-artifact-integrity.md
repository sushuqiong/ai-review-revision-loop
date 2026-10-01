# 生成物完整性：只改生成器，不改生成物（v12 实测踩坑）

适用：任何"由脚本从冻结结果表生成正文/图/表"的稿件工程（本用户所有论文项目都是这种结构）。

## 一、铁律
**正文/图/表的数字由生成器脚本注入 ⇒ 文字修改必须落在生成器脚本里，不能直接改产物。**

产物（`Manuscript_draft_vN.md/.docx`、`FigN_*.png`、`Tables_vN.docx`）都是可再生的；直接编辑它们等于把改动
放在下一次重建会被抹掉的位置。

### 本次实测的失败链
1. 写了一个后处理脚本（`79_*.py`）去 patch 生成的 `DataDescriptor_v12.md`（加 ESCC 溯源、复现性段落）；
2. 同一条链里**又**运行了生成器 `71_v12_md_final.py`；
3. 生成器按自己的模板重建 md → **刚才的两段新内容被静默覆盖**；
4. 唯一的发现方式是我在脚本里打的断言 `print("manuscript updated:", phrase in s)` 输出了 `False`。

### 正确顺序（固定链路）
```
改生成器 → 运行生成器 → 断言关键短语在产物里（True 才继续）
        → 重建 docx/PDF → 重算校验值/清单 → 审计脚本（数字 vs 冻结表；占位符/陈旧数字）
        → 打包 ZIP → git add/commit/push
```
后处理只允许做**不进入产物**的事（复制文件、算 checksum、组装 ZIP）；要进产物的文字必须写进生成器。

## 二、防御性写法
```python
# 生成器里：改完立刻断言，把"静默失效"变成"响亮失败"
s = s.replace(old, new)
assert new in s, "anchor not found: " + old[:60]
# 生成后：打印可核对的指纹
print("manuscript updated:", "TCGA-layer reproducibility" in s)
print("title chars:", len(title), "| abstract words:", abw)
```
- 断言/指纹必须覆盖**这一轮新增的内容**，不能只检查总数（总数不变时最容易被覆盖而不自知）。
- 生成器的 patch 用 `assert old in s` 开头；锚点失配要报错，不要静默跳过。

## 三、与"钉住数字"的关系
- 产物里的数字**只允许**来自冻结结果表（`results/*.csv`），禁止手写；生成器负责注入。
- 想让某个数字永不漂移，就在生成器里把它从 CSV 读出来（如 `n_cc = len(case_control_rows)`），
  并在审计脚本里对"文中所述 vs 表格实际"做逐项比对——本用户会追问"数字与图表是否同源"。
- 图表同源同理：`FigN_*` 必须由当前冻结表重生成；补充图也**不得**沿用上一版文件（v9 旧图曾被直接复用）。

## 四、收工前的两条机器检查（缺一不可）
1. 数字 vs 冻结表（含摘要/图注/表注/正文一致性）；
2. 占位符 + 陈旧数字 + 跨文件一致（accession 集合、连接键可解析、期望文件存在）。
两项都 0 问题才允许宣布完成；产物被发现与生成器不一致时，先修生成器再重跑，不要手改产物。

> 说明：本文件与 references/public-data-resource-integrity-audit.md（数据自审）、
> references/figure-ocr-layout-qa.md（图表版面 QA）配套使用。
