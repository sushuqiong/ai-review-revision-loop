#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OCR 版面质检：检查图件是否有文字越界/裁切，并对疑似裁切做"像素级复核"以排除假阳性。

为什么需要：本用户反复强调"画图表总是有问题"，且 vision 模型可能不可用；
OCR（tesseract 词级框坐标）是唯一可自动化的版面检查手段。但 OCR 会把
靠近边缘的文字框报为"裁切"，其中一部分是假阳性 → 必须二次确认。

用法：
    python figure_layout_ocr_qa.py <fig1.png> <fig2.png> ...
    python figure_layout_ocr_qa.py --dir 02_figures --max-cm 17.0

判读：
  * cm_w > 17.0  → 超版宽，必须重排（改 width=6.7 in @300dpi）
  * 某一 token 的 x+w >= W-2 或 y+h >= H-2 → 疑似越界
  * 对每个疑似框裁出 (x-60, y-20, W, y+h+20) 后放大 OCR：
      - 若该区域最暗像素 = 255（纯白）→ 假阳性（框边界贴画布但无墨迹）
      - 若非白比例明显 > 0 且放大能读出完整词 → 真裁切，缩短标题/轴标签后重渲染
常见真裁切根因：面板标题或整体标题过长（ggplot 不换行）、长轴标签、
                coord_flip 后仍用 scale_x_continuous 导致全部数据被丢弃。

依赖：tesseract 已安装；Windows 下必须设 TESSDATA_PREFIX，并把图片复制到 ASCII 路径。
"""
import csv, os, shutil, subprocess, sys, argparse

TESS_DEFAULT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSDATA_DEFAULT = r"C:\Program Files\Tesseract-OCR\tessdata"
TMP = os.path.join(os.path.expanduser("~"), "ocr_fig_qa_tmp")


def ocr_words(png, tess, tessdata):
    env = dict(os.environ, TESSDATA_PREFIX=tessdata)
    r = subprocess.run([tess, png, "stdout", "--psm", "11", "tsv"],
                       capture_output=True, env=env)
    out = []
    for row in csv.DictReader(r.stdout.decode("utf-8", "replace").splitlines(), delimiter="\t"):
        t = (row.get("text") or "").strip()
        if not t:
            continue
        try:
            out.append(dict(t=t, c=float(row.get("conf") or -1), x=int(row["left"]), y=int(row["top"]),
                            w=int(row["width"]), h=int(row["height"])))
        except Exception:
            pass
    return [w for w in out if w["c"] > 30]


def confirm_with_pixels(png, box, tess, tessdata):
    """返回 (真实裁切与否, 放大后识别文本)。纯白区域 → 假阳性。"""
    from PIL import Image
    import numpy as np
    im = Image.open(png).convert("RGB")
    W, H = im.size
    x, y, w, h = box["x"], box["y"], box["w"], box["h"]
    reg = im.crop((max(0, x - 60), max(0, y - 20), W, min(H, y + h + 20)))
    a = np.array(reg.convert("L"))
    dark = int(a.min()) < 250 and float((a < 200).mean()) > 0.002
    zoom = os.path.join(TMP, "zoom.png")
    reg.resize((reg.width * 3, reg.height * 3), Image.LANCZOS).save(zoom)
    env = dict(os.environ, TESSDATA_PREFIX=tessdata)
    txt = subprocess.run([tess, zoom, "stdout", "--psm", "7"], capture_output=True,
                         env=env).stdout.decode("utf-8", "replace").strip()[:90]
    return dark, txt


def check(png, tess, tessdata, max_cm=17.0):
    from PIL import Image
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(TMP, exist_ok=True)
    local = os.path.join(TMP, os.path.basename(png))          # ASCII 路径，避免中文路径失效
    shutil.copy(png, local)
    W, H = Image.open(local).size
    cm_w = W / 300 * 2.54
    words = ocr_words(local, tess, tessdata)
    suspects = [w for w in words if w["x"] <= 2 or w["y"] <= 2 or
                w["x"] + w["w"] >= W - 2 or w["y"] + w["h"] >= H - 2]
    print(f"{os.path.basename(png)}: {W}x{H}px  {cm_w:.2f}cm x {H/300*2.54:.2f}cm  "
          f"words={len(words)}  suspects={len(suspects)}")
    if cm_w > max_cm + 0.05:
        print(f"  [FAIL] 超版宽 {cm_w:.2f} > {max_cm}cm —— 必须改 width=6.7in @300dpi 重渲染")
    real = 0
    for s in suspects:
        dark, txt = confirm_with_pixels(local, s, tess, tessdata)
        if dark:
            real += 1
            print(f"  [REAL] 真裁切: token={s['t']!r} box=({s['x']},{s['y']},{s['w']}x{s['h']})  放大读数={txt!r}")
        else:
            print(f"  [ok]   假阳性（纯白区域）: token={s['t']!r} box=({s['x']},{s['y']})")
    print("  => " + ("版面通过（无真实裁切）" if real == 0 else f"需修复 {real} 处真实裁切：缩短标题/轴标签后重渲染"))
    return real == 0 and cm_w <= max_cm + 0.05


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--dir", default=None)
    ap.add_argument("--max-cm", type=float, default=17.0)
    ap.add_argument("--tess", default=TESS_DEFAULT)
    ap.add_argument("--tessdata", default=TESSDATA_DEFAULT)
    a = ap.parse_args()
    targets = list(a.files)
    if a.dir:
        targets += [os.path.join(a.dir, f) for f in sorted(os.listdir(a.dir)) if f.lower().endswith(".png")]
    if not targets:
        print("no figures given"); sys.exit(2)
    allok = all(check(p, a.tess, a.tessdata, a.max_cm) for p in targets)
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
