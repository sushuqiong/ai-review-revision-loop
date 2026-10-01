# AIID mongodump 上下文恢复 + LLM 双编码信度配方（v25 实测）

## 场景
数据表（v21–v24）的 `source_excerpt` / `description` 列是占位文本（"public-source limitation: AIID snapshot record; ... evidence remains descriptive."），`source_registry` 的 `*_evidence_excerpt` 全是 "No recoverable public evidence..."。任何基于这些占位的"第二编码"（人类或 AI）都无意义——两个编码者会对同样的空文本判 absent，kappa 是虚假的。**这正是 v21 报告的 κ=0.72 无法重建的根因**。

## 真实上下文来源（Obsidian 知识库归档）
```
AI健康医学_Obsidian知识库_v23/10_Public_Incident_Evidence/00_sources/
├── aiid_backup_20260720.tar.bz2   # AIID mongodump（100MB）
│   └── mongodump_full_snapshot/aiidprod/incidents.bson + reports.bson
├── recheck_snapshots/AIID001_<hash>.txt   # AIID incident 页面快照（81 个，部分空）
└── snapshots/OECD01_*.txt, DIR01_*.txt    # OECD AIM + 官方报告快照（各 10 个）
```

## 两套编号系统（关键陷阱）
- **registry case_id**：AIID01–AIID40（v16 重新编号，多对一：AIID01 有 7 条记录）、OECD01–10（每条 2 条）、DIR01–10、PUB01–10
- **AIID 原生 incident_id**：快照文件名 `AIID001_<hash>` 的 001 是原生 id，≠ registry case_id
- 直接按 case_id 映射快照 → 全错（registry AIID01=Uber 事件，快照 AIID001=YouTube Kids）

## 正确匹配链（60/60 成功）
```python
import tarfile, io, bson, re
tar = tarfile.open(tarbz2, "r:bz2")
incidents = list(bson.decode_file_iter(io.BytesIO(tar.extractfile("mongodump_full_snapshot/aiidprod/incidents.bson").read())))
reports   = list(bson.decode_file_iter(io.BytesIO(tar.extractfile("mongodump_full_snapshot/aiidprod/reports.bson").read())))
# 1) incident.reports 是 report_id 列表 → report._id → incident_id
report2inc = {str(rid): str(inc["incident_id"]) for inc in incidents for rid in inc.get("reports", [])}
# 2) registry.source_url 归一化 → reports.bson 的 url → _id
def norm(u):
    u = re.sub(r"^https?://", "", str(u or "")).strip()
    u = re.sub(r"^www\.", "", u); u = re.sub(r"[#?].*$", "", u)
    return u.rstrip("/")
url2rep = {norm(r.get("url")): r for r in reports}
# 3) registry row → url → report._id → incident_id → incidents.bson(title, description)
```
注意：reports.bson **没有 incident_id 字段**（关联只在 incident.reports 数组）；pymongo 安装：`D:\ProgramData\python.exe -m pip install pymongo`。

## LLM 独立编码（cross-method reproducibility check）
1. 生成工作表：每条记录给出 case_id + stratum + title + 真实上下文（AIID 用 incident title+description[:450]；OECD/DIR 用快照文本[:450]；无快照的 PUB 用标题兜底）+ 5 个空白编码列（runtime_lineage / exposure_denominator / follow_up_window / recurrence_status / closure_basis）
2. LLM 只读上下文独立判断（不看第一编码），值域 present/partial/absent/unclear/not_applicable
3. 与第一编码（xlsx 的 *_present 列）对齐计算：
```python
def gwet_ac1(a, b, cats):
    n = len(a); po = sum(1 for x,y in zip(a,b) if x==y)/n
    pe = 0.0; K = len(cats)
    for k in cats:
        p1 = sum(1 for x in a if x==k)/n; p2 = sum(1 for y in b if y==k)/n
        pk = (p1+p2)/2; pe += pk*(1-pk)
    pe = pe/(K-1) if K>1 else 0
    return (po - pe)/(1 - pe) if pe < 1 else 0
```
4. **必须同时报 raw + Cohen's κ + Gwet's AC1**：absent 占主导时 κ 失真（raw 90% 但 κ=0.00，甚至为负），AC1 是 prevalence-robust 统计；正文解释为何 κ 不适用

## v25 实测结果（90 条对齐）
| 字段 | raw | κ | AC1 |
|---|---|---|---|
| Exposure denominator | 90.0% | 0.00 | 0.90 |
| Closure basis | 85.6% | 0.32 | 0.85 |
| Follow-up window | 73.3% | −0.15 | 0.72 |
| Runtime lineage | 67.8% | 0.00 | 0.65 |
| Recurrence status | 38.9% | −0.01 | 0.30 |

**结果成为论文加分点**：三个核心缺失字段跨方法稳健（AC1 0.72–0.90 → "缺失非单一编码程序产物"），复发状态不稳定（AC1 0.30 → 方法学支持"复发是判定问题而非简单缺失"）。

## 科学诚信红线
- LLM 编码 ≠ 人类 inter-coder reliability。正文/补充材料必须如实写 "cross-method reproducibility check; machine reproducibility result, not a human inter-coder reliability study"
- 人类信度留给真实第二编码员（用户愿当）：20 条随机子样本工作表（random.seed 固定、带真实上下文、约 15 分钟），回来才算 Cohen's κ + AC1
- 第一编码 provenance 不完整（无第二编码者身份/日期/原始分歧表/未调解向量）→ 永远不报告人类 κ
