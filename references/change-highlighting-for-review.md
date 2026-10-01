# 「改动标蓝」核对版 + 去蓝标投稿版

## 触发

用户会说：

- "你相对我的原文做了改动和增加文字的地方，**全部改用蓝色字体标出来**，方便我核对"
- "我要看你这版改了什么"

这是**本用户的固定需求**（不是一次性请求）：返修稿交付后，用户要一份能一眼看出"改了什么"的核对版。默认就准备，别等问。

---

## 产出形态（硬要求）

| 位置 | 内容 | 能否投稿 |
|---|---|---|
| 用户点名的那些路径（如根目录 `01_Manuscript_JCEH_revised.docx`） | **蓝标核对版** | ❌ **不能** |
| `投稿用_去蓝标版本\`（同名文件） | 与核对版**逐字相同**、只是没有蓝色 | ✅ 投稿用 |

**必须**在 README 顶部和回复里都用 ⚠️ 写明："根目录这三个是核对版，不能直接投稿；投稿请用 `投稿用_去蓝标版本\` 里的同名文件。"

> 主动补一句："如果你更希望根目录就是投稿版、蓝标版单独放子文件夹（这样上传时不会拿错），说一句我马上调换。" —— 用户可能更想要这个（更安全，上传时不会拿错）。

---

## 标什么、不标什么（用户会核对这两条）

1. **按段落整段标蓝，不是逐词标蓝。** 并在汇报里明说 —— 用户接受，因为目的是"定位到需要重读的段落"。
2. **全篇统一的编辑性格式改动不标蓝**，并说明原因：
   - 正文引用 `[1]` → **上标**（主编要求）
   - 参考文献列表 `[1] Moon...` → `1. Moon...`
   逐处标蓝会得到 45 个上标 + 54 个编号全蓝，把真正的内容改动淹没；而且这两种在版面上本来就一眼可辨。

---

## 做法：确定性标记，**不要用 diff**

直接复用 `scripts/blue_marks.py`（`set_blue()` / `apply_blue_marks()` / `audit()`），别每次重打一遍：

```python
# blue_marks.py
import copy, os
from docx.shared import RGBColor
NO_BLUE = bool(os.environ.get("NO_BLUE"))
O, C = "\ue000", "\ue001"          # 私用区字符，正文绝不会出现
BLUE = RGBColor(0x00, 0x00, 0xFF)


def apply_blue_marks(doc, colour=None):
    """把 <O>…<C> 包住的片段染蓝，并删掉标记字符；NO_BLUE=1 时只删标记不上色"""
    colour = BLUE if colour is None else colour
    if NO_BLUE:
        colour = None
    n = 0
    for p in doc.paragraphs:
        if O not in p.text and C not in p.text:
            continue
        for run in list(p.runs):
            t = run.text
            if O not in t and C not in t:
                continue
            parts = [x for x in t.replace(C, O).split(O)]
            template = copy.deepcopy(run._element)
            parent = run._element.getparent()
            anchor = run._element
            anchor.addprevious(copy.deepcopy(template))
            prev = anchor.getprevious()
            used = False
            for i, seg in enumerate(parts):
                if seg == "":
                    continue
                nr = prev if not used else copy.deepcopy(template)
                if used:
                    prev.addnext(nr)
                from docx.text.run import Run
                R = Run(nr, p); R.text = seg
                if i % 2 == 1 and colour is not None:      # 标记对之间的奇数段
                    R.font.color.rgb = colour
                    n += 1
                prev = nr; used = True
            parent.remove(anchor)
    return n
```

在生成器里：

```python
# 整段是新增/重写 → 直接给 run 上色
def set_text(p, txt, blue=False):
    ...                       # 合并进首 run
    if blue and p.runs and not NO_BLUE:
        p.runs[0].font.color.rgb = BLUE

# 长段落里只新增一句 → 用标记包住那一句
new = old_prefix + O + "(* FDR < 0.05; *** FDR < 0.001; ns, not significant)." + C

# save 之前
apply_blue_marks(doc)
```

生成两份：

```python
env = dict(os.environ, NO_BLUE="1")
subprocess.run([PY, gen], env=env)                 # 先跑黑版
shutil.copy2(主路径文件, 投稿用_去蓝标版本/同名)     # 存干净件
subprocess.run([PY, gen])                          # 再跑蓝版
```

---

## 为什么不能靠 diff（本次实测证据）

第一版想用"逐词 diff 原文 vs 改后"自动标蓝，**失败**：

| 尝试 | 结果 |
|---|---|
| 直接 `difflib` 逐词 diff，归一化 `[n]` 方括号 | 标出 **79 段**，真实改动只有 **17 段** |
| 再加"上标 run 视为可忽略 token"的双侧归一化 | 仍然 79 段；且把整条参考文献标成全蓝 |

根因：引用从 `[1]` 变成上标后，token 序列在**每一处**引用位置都错位，`SequenceMatcher` 的 `replace` 块会吞掉大片"其实没变"的文字；上标位置又要靠累加 run 长度来定位，遇到 hyperlink/空 run 就漂移。

**结论：改动是"我知道我改了什么"，不是"从两份文件里猜我改了什么"。** 在生成器里显式标记，唯一可靠。

---

## 交付前必跑的四项验证

```python
# 1. 每个文件蓝标段落数 == 预期改动数
#    本次：manuscript 17 / title page 2 / figure legends 9
# 2. 干净版蓝标段落数 == 0
# 3. 核对版与干净版 **正文文字完全相同**（证明标色过程没改动内容）
tb == tc            # [p.text for p in Document(blue).paragraphs] 逐段比对
# 4. 残留标记字符 == 0
sum(p.text.count("\ue000") + p.text.count("\ue001") for p in doc.paragraphs) == 0
```

再跑一遍常规收工 QA（`scripts/qa_revised_manuscript.py`），确认标色没打乱引用上标/字数/编号（本次回归：0 项失败）。

---

## 汇报模板

> | 文件 | 蓝标处数 | 具体位置 |
> |---|---|---|
> | 01_Manuscript… | **17 处** | 摘要 Results；Methods 2.2.1/2.2.3/2.2.4/2.3.2/**新增 2.3.6**/2.5；Results 3.1.4/**3.1.5**/**新增 3.2.7**；Discussion；Limitations；参考文献 44；Fig.5 图注补句 |
>
> 两点标蓝规则：① 引用格式改动（`[1]`→上标）未标蓝（全篇统一、版面已可区分）；② 按段落整段标蓝，不是逐词。
