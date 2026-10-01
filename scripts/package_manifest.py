#!/usr/bin/env python3
"""数据包清单与校验：清单不含自身 + 清单摘要单列，避免「自引用」措辞被审稿人挑。

用法:
  python package_manifest.py 包目录              # 重建清单（每次增删包内文件后必须重跑）
  python package_manifest.py 包目录 --check      # 校验，必须 0 个 FAILED

产物（默认写入包内 08_qc/）:
  file_inventory_and_checksums.csv   file,bytes,rows,sha256（无自引用行）
  checksums_sha256.txt               每行一个数据文件，不含自身
  manifest_checksum.txt              上面两个清单文件自身的 sha256

实测教训：写完本工具回测真包时抓到「qc_adversarial_review.csv 未进清单」→ 先重建再打包。
"""
import argparse, csv, hashlib, os, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("package")
ap.add_argument("--qc-dir", default="08_qc")
ap.add_argument("--check", action="store_true")
a = ap.parse_args()

PK = os.path.abspath(a.package)
QC = os.path.join(PK, a.qc_dir)
os.makedirs(QC, exist_ok=True)
SELF = {"file_inventory_and_checksums.csv", "checksums_sha256.txt", "manifest_checksum.txt"}


def digest(fp):
    h = hashlib.sha256()
    with open(fp, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


if a.check:
    r = subprocess.run("sha256sum -c " + os.path.join(a.qc_dir, "checksums_sha256.txt"),
                       cwd=PK, shell=True, capture_output=True, text=True)
    ok = sum(1 for l in r.stdout.splitlines() if l.endswith(": OK"))
    bad = [l for l in r.stdout.splitlines() if not l.endswith(": OK")]
    print(f"verified {ok} | problems {bad or 'none'}")
    sys.exit(1 if bad else 0)

inv = []
for d0, _, fn in os.walk(PK):
    for f in sorted(fn):
        fp = os.path.join(d0, f)
        rel = os.path.relpath(fp, PK).replace(os.sep, "/")
        if os.path.dirname(rel) == a.qc_dir and os.path.basename(rel) in SELF:
            continue
        rows = ""
        if f.endswith(".csv"):
            try:
                rows = sum(1 for _ in open(fp, encoding="utf-8", errors="replace")) - 1
            except Exception:
                rows = ""
        inv.append(dict(file=rel, bytes=os.path.getsize(fp), rows=rows, sha256=digest(fp)))

inv_path = os.path.join(QC, "file_inventory_and_checksums.csv")
ck_path = os.path.join(QC, "checksums_sha256.txt")
with open(inv_path, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["file", "bytes", "rows", "sha256"], lineterminator="\n")
    w.writeheader(); w.writerows(inv)
with open(ck_path, "w", encoding="utf-8", newline="") as f:
    f.write("\n".join(f"{r['sha256']}  {r['file']}" for r in inv) + "\n")
with open(os.path.join(QC, "manifest_checksum.txt"), "w", encoding="utf-8", newline="") as f:
    f.write("# digest of the manifest files themselves (they are not covered by the list)\n")
    f.write(f"{digest(inv_path)}  file_inventory_and_checksums.csv\n")
    f.write(f"{digest(ck_path)}  checksums_sha256.txt\n")

print(f"package {PK}\nfiles {len(inv)} | wrote {os.path.relpath(inv_path, PK)}, "
      f"{os.path.relpath(ck_path, PK)}, {a.qc_dir}/manifest_checksum.txt")
