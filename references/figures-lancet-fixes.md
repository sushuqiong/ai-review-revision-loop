# Lancet 风格医学图表修复模式（实战目录）

本文件来自实际三课题论文图表重绘/优化经历。用户对"难看/重叠/字号小"的反馈是真实信号，vision 模型常误判为"没问题"——以下模式是可客观执行的修复方案。

## 通用规范（所有图）
- 字号：轴标签/刻度/图例/图内注释 **≥12pt**，轴标题 13pt，图题 14pt bold（SVG 以 72dpi 输出 px=pt，验证时按此换算）
- Lancet 五色：#ED0000(红) #00468B(蓝) #0099B4(绿) #ED7D31(橙) #7F7F7F(灰)
- theme_classic + 白底 + 无网格 + 黑色细轴线(linewidth 0.5) + 图例底部 + plot.margin 加大防裁切
- 输出三格式：svglite(SVG) + cairo_pdf(PDF) + agg_png(300dpi PNG)，`library(ragg)` 记得加载

## 流程图（CONSORT 规范）
- **不要手工硬编码散点坐标**（x=c(...), y=c(...) 是"图难看"主因）：框会歪、间距不均、文字溢出
- 正确做法：主队列垂直居中 → T 形分叉线 → 各分支队列框 → 各自再分叉到结局框；Excluded 用水平箭头从主框连到右侧
- 框内文字 13pt bold + 数据行 12.5pt 全部居中；用 `strwidth` 实测文字宽度确保无溢出
- 配色：Lancet 蓝边框+浅蓝填充主框，灰边框白底结果框

## RCS 剂量-反应图
- 主图 75% + 底部 DII 分布直方图 25%，**共享 x 轴**（scale 用 coord_cartesian 避免裁剪警告）
- 曲线 Lancet 红 #ED0000、CI 带 #FFB3B3 半透明、OR=1 灰虚线
- P 值注释（P-overall / P-nonlinear）放左上角空白区，加白底避免压曲线
- 注意 Predict() 默认只在 10–90% 分位数内预测，y 轴范围要容纳 CI 带完整显示

## 森林图（最常出重叠问题的图）
- **左右文本列整体移出绘图区**：`coord_cartesian(xlim=..., clip="off")`，用 systemfonts 精确算文本宽度，动态设 plot.margin（左列 ~234pt / 右列 ~191pt）
- 验证：左侧文本右缘 < 绘图区左缘、右侧文本左缘 > 绘图区右缘、最右缘 < 画布宽
- 修 y 轴残留变量名：`labs(y=NULL)`
- 图宽要够（8.6→11.5in），字号 8→12pt
- CI 区间用 rms 的 lrm 时注意设计矩阵不含截距列，协方差 CI 需手动处理

## DCA 决策曲线（patchwork 合并时图例易丢失）
- **核心坑**：子图设 `legend.position="none"` 再靠 patchwork `guides="collect"` 合并 → 图例被完全丢弃、整体缺失
- 修复：子图保留 legend（不设 none），让 patchwork 收集；合并为底部完整图例（含 Treat all / Treat none 参考线）
- 曲线加 alpha=0.9 防互相遮挡；Treat none 用浅灰 dotted 与 Treat all 区分

## ROC 曲线
- AUC/DeLong 注释锚定右下空白角 (x=0.99, y=0.035, vjust=0)，不与曲线重叠
- 图例底部单行；多模型对比时 AUC 可移入图例（nrow=2）

## 四分位/剂量反应图
- 数值标签偏移 UCL+0.30（不是 +0.18），y 上限加缓冲（4.6→5.2），防标签压误差棒
- 长 CI（如 OR=52.2 (37.6–72.4)）会顶到图边：x 上限扩到 ~900，hjust=-0.1

## 校准图
- 散点用 shape=21 + 白边（防被拟合线遮挡），红/蓝双色，注释 12pt

## LASSO 路径图
- matplotlib 默认 12 色换成 Lancet 衍生 12 色（5 核心色+深浅色调）
- 标签 12pt、变量名全部渲染（用 ggrepel 防重叠）

## 中介路径图
- grid/graphviz 画三节点路径：圆角矩形节点、主箭头带路径系数、灰色虚线直接效应
- 底部标注 ACME + 中介比例 + 95%CI
- **路径系数必须与中介分析模型一致（重大坑）**：mediation 包的 med_m 是 `lm(GLM7 ~ DII + 协变量)`（调整后 a≈0.022），而裸 `lm(GLM7 ~ DII)` 未调整时 a 可能≈0（本会话实测 -0.0008）。图若用未调整系数会画出错误方向/大小的 a，且显著性标注也对不上。修复：从与 mediate() 相同的调整模型 `lm(GLM7 ~ DII + gender_cat + race_cat + edu_cat + PIR_cat + smoke + alcohol + HTN + age)` 取 coef，并用 `ifelse(p<0.001,"***",...)` 动态生成星号
- 长文本节点（如 "Metabolic dysfunction-associated steatotic liver disease"）会溢出到相邻面板：**全称换行缩成 3-4 行**（label 内加 \n），画布加宽（12→13in），coord_cartesian 范围扩大（xlim 上限 11.6→12.6），patchwork widths 拉开（1.35:1）
- 面板 B 柱状图误差棒不一致时（一组 CI 过宽如 CAP PM -139.9%~365.7%）：**保留能显示那组的误差棒，另一组加脚注**（plot.caption）诚实说明 "95% CI not shown due to width when ADE≈0"，不要静默省略也不要在图上画超长误差棒
- 面板 A/B 用 patchwork 组合后，务必用 vision 或人工确认 A 面板无文字溢出到 B（geom_label 长文本是最大嫌疑）

## 校准图（coord_equal 是标题被裁切的主因）
- 不要用 `coord_equal()`（强制 x/y 等比例会压缩绘图区，14pt 标题被推到画布外）→ 改用 `coord_cartesian(xlim=c(0,1), ylim=c(0,1))`，plot.margin 加大（上 18pt）
- 特殊字符 χ²（U+03C7）在 sans 字体下触发 `mbcsToSbcs conversion failure` 警告、可能显示为乱码 → 图内标注用 "Chi2" 代替；→ (U+2192) 同理用 "->"
- 散点用 shape=21 + 白边（防被拟合线遮挡），红/蓝双色，注释 12pt

## LASSO 路径图（曲线重叠 + 标签指向不清）
- 12 条曲线在 λ 大时都压到 0 线上必然重叠——无法完全消除，但可让标签可读：
- **标签只在 λ.min 终点标注**（`geom_text_repel(data=lbl_df, direction="y", nudge_x=+0.35, xlim=c(log(lmin)-0.3, log(lmin)+1.2))`），颜色与曲线一致（`aes(label=Variable, color=Variable)`），不用中途多标签
- 图高加大（5.8→7in）、图宽 10in，给标签留空间；`max.overlaps=30`、`box.padding=0.5`
- scale_x_reverse（λ 轴反向）时 nudge_x 方向要注意（正向即往图左）

## 四分位趋势图（多行注释重叠）
- 两条 P for trend 若都放 (x=4.3, y=4.85) 必然重叠 → 给 trend_txt 加 `yy` 列（如 4.85 / 4.30），`geom_text(aes(x=4.3, y=yy, label=t))` 分开放置
- 数值标签偏移 UCL+0.30（不是 +0.18），y 上限加缓冲（4.6→5.2），防标签压误差棒
- 长 CI（如 OR=52.2 (37.6–72.4)）会顶到图边：x 上限扩到 ~900，hjust=-0.1

## 森林图（文字重叠的两种解法）
- 左右文本列整体移出绘图区：`coord_cartesian(xlim=..., clip="off")`，用 systemfonts 精确算文本宽度，动态设 plot.margin
- **改短文本后必须同步更新宽度计算**：把 "(n = %d, events = %d)" 缩短为 "(n = %d)" 时，`left_w_in <- max(txtw(...))` 的格式化字符串也要同步改，否则 X_LEFT 按旧文本算、文本与区间错位
- 交互 P 文本过长（"P for interaction < 0.001"）会挤占右列 → 缩短为 "P-int < 0.001" / "P-int = %.3f"
- 验证：左侧文本右缘 < 绘图区左缘、右侧文本左缘 > 绘图区右缘、最右缘 < 画布宽；修 y 轴残留变量名 `labs(y=NULL)`

## ROC 曲线（AUC CI 完整性）
- **所有对比曲线都要给 95%CI**（用户明确问"为什么有的 AUC 不给置信区间"）：`ci.auc(roc_obj, method="delong")` 逐条算，图例 label 含 AUC (CI)
- AUC/DeLong 注释锚定右下空白角 (x=0.99, y=0.035, vjust=0)，不与曲线重叠；图例底部单行；多模型对比时 AUC 移入图例（nrow=2）

## 验证手段
- PNG 尺寸与 300dpi 物理尺寸吻合（如 3300×2100 = 11×7in @300dpi）
- SVG grep 字号文本 ≥12pt
- 数值复核：流程图计数、DCA NB、AUC 必须与稿件一致
- **关键：路径系数/统计数字要从与稿件一致的分析模型取**（见中介路径图），避免未调整/调整模型混用
- 修复后重新生成时，把 04_图表_矢量 与论文目录的 figures_vector 同步覆盖（用户论文 Word 引用的图路径两者都要更新）

## 两个隐藏库 bug（症状隐蔽、必查）
- **systemfonts 函数名**：`string_widths()`（复数）在 systemfonts ≥1.3 不存在，正确是 `string_width()`（单数，返回 pt）。用错函数时"精确测宽"静默走兜底估算（每字符 0.085in），森林图边距算不准 → 文字越界/重叠但脚本"看起来正常"。排查：`Rscript -e 'library(systemfonts); exists("string_widths")'` 返回 FALSE
- **ggrepel × scale_x_reverse**：ggrepel 0.9.8 在 `scale_x_reverse` + xlim 下把标签渲染到画布外，只留下灰色 segment 引线（用户看到"一堆无意义水平虚线"）。绕开：把 x 轴改成 `-log(λ)`（λ.min 自然落在右侧、用普通 scale），`segment.color=NA` 去掉引线，标签 `direction="y"` 展开

## 流程图（终极方案：不用 DiagrammeR 也不手摆散点）
- graphviz(DiagrammeR) 需要系统装 dot 可执行文件，Windows 默认没有 → 不要依赖
- 可靠方案：纯 ggplot + 逐框 `geom_rect(aes(xmin=cx-w/2,...))` + 两行 `geom_text`（标题行 cy+h*0.18 / 数据行 cy-h*0.22）+ **箭头从框边缘精确连出**（`get_edge(id, "bottom"/"top"/"right"/"left")` 函数返回框边中点，主框→队列用 bottom→top，主框→Excluded 用 right→left 虚线）
- 坐标经数学验证（12×8in 画布，框不重叠、文字不溢出），比散点坐标稳
- **theme 三连坑（本会话用户逐条抓）**：
  - ① `theme_void()` 后**不要再叠加 lancet_theme()/theme_classic()**——任何带 axis 的主题会把坐标刻度带回图里（用户："图一流程图为什么有坐标？"）。只加 `theme(plot.background=element_rect(fill="white", colour=NA), plot.margin=...)`
  - ② 箭头 y1→y2 只差 0.5 单位几乎不可见（"缺箭头"）——箭头必须跨满框间距（如 86→80.5、62→56.5），linewidth≥0.8，arrow length 0.22cm，颜色深灰
  - ③ 框内字号 3.3pt 太小（"字体偏小"）→ 列标题 5.5pt bold、框内 4.6pt、排除注释 3.8pt、底部定义注释 3.6pt

## RCS 剂量-反应图（OR 尺度是硬要求）
- **rms::Predict 的 yhat 是概率尺度，不是 OR 尺度**：`Predict(f, GLM7=gseq, ref.zero=TRUE)` 默认返回预测概率（0-1）。直接画在 OR y 轴上（ylim 0-6.4）曲线全压底部（本会话实测 yhat 0.06-0.44）。必须 `fun=exp`：`Predict(f, GLM7=gseq, ref.zero=TRUE, fun=exp)` → OR 范围 0.23-2.63 才正常
- 附带坑：`datadist` 全局赋值 `dd <<- datadist(d)` 且 d 只保留建模列（否则 lrm 报 "dataset dd not found"）；anova(f) 的非线性 P 从含 "Nonlinear" 的 rownames 取；改图后 P 值（overall/nonlinear）必须与正文/图注同步
- 主图 75% + 底部 DII 分布直方图 25%，**共享 x 轴**（scale 用 coord_cartesian 避免裁剪警告）
- 曲线 Lancet 红 #ED0000、CI 带 #FFB3B3 半透明、OR=1 灰虚线
- P 值注释（P-overall / P-nonlinear）放左上角空白区，加白底避免压曲线
- 注意 Predict() 默认只在 10–90% 分位数内预测，y 轴范围要容纳 CI 带完整显示

## 增量价值 AUC 对比图（数值多、对应关系必须可读）
- 6 个模型并排：每个点**上方标 AUC**（3 位小数）、**下方标 `ΔAUC ±.xxx\nP = ...`**（两行小字）；base 模型点用不同 shape（18 菱形）作参照；ΔAUC 为 NA 的 base 行不标
- **图底部 caption 定义 ΔAUC 含义**：`ΔAUC = AUC(model) − AUC(base). Base model: age, sex, race/ethnicity, education, PIR, smoking, alcohol, hypertension`
- facet_wrap 双周期并排（Earlier/Later period），AUC 值标签颜色与模型色一致，GLM7 红色突出
- **annotate 坐标超出 coord_cartesian 的 xlim 会被裁**（"图例/注释显示不完全"）：如注释 x=4.6 而 xlim 上限 4.55 → 文字裁半。修复：注释放进绘图区（x 缩到 4.15）或 xlim 上限扩过注释位置

## 双面板 ROC（空白多 / 标题图例不全）
- `coord_equal` 强制正方形 + expand 默认会留大片空白 → `coord_equal(expand=FALSE)` 或改普通坐标 + 缩小画布（6.8×8.8in）
- 标题用 `plot_annotation(title=...)`（完整显示），图例 legend.spacing.x 加大（0.8cm）防 GLM7/TyG AUC 标签挤在一起
