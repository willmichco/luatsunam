# -*- coding: utf-8 -*-
"""Tổng hợp kết quả Lighthouse (workflow "Đo Lighthouse"): lấy trung vị nhiều lần đo cho từng trang × thiết bị.

Dùng: python3 tools/lighthouse_tom_tat.py <thư mục chứa trangN-mobile|desktop-K.report.json>
In bảng Markdown (dán thẳng vào docs/NGHIEM-THU.md để làm mốc so sánh khi chuyển tên miền – G5).
"""
import glob
import json
import os
import re
import statistics
import sys

CATS = [("performance", "Hiệu năng"), ("accessibility", "Truy cập"), ("best-practices", "Thực hành tốt"), ("seo", "SEO")]
METRICS = [("largest-contentful-paint", "LCP", "s"), ("cumulative-layout-shift", "CLS", ""),
           ("total-blocking-time", "TBT", "ms"), ("first-contentful-paint", "FCP", "s"),
           ("speed-index", "Speed Index", "s"), ("total-byte-weight", "Tổng tải", "KB")]


def fmt(v, unit):
    if v is None:
        return "–"
    if unit == "s":
        return f"{v / 1000:.1f} s"
    if unit == "ms":
        return f"{v:.0f} ms"
    if unit == "KB":
        return f"{v / 1024:.0f} KB"
    return f"{v:.3f}"


def main(folder):
    groups = {}
    version = None
    for path in sorted(glob.glob(os.path.join(folder, "*.report.json"))):
        m = re.match(r"trang(\d+)-(mobile|desktop)-\d+\.report\.json$", os.path.basename(path))
        if not m:
            continue
        try:
            r = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if r.get("runtimeError"):
            continue
        version = r.get("lighthouseVersion", version)
        key = (int(m.group(1)), m.group(2))
        g = groups.setdefault(key, {"url": r.get("finalDisplayedUrl") or r.get("requestedUrl"), "runs": []})
        row = {}
        for cid, _ in CATS:
            s = (r.get("categories", {}).get(cid) or {}).get("score")
            row[cid] = None if s is None else s * 100
        for aid, _, _ in METRICS:
            row[aid] = (r.get("audits", {}).get(aid) or {}).get("numericValue")
        g["runs"].append(row)
    if not groups:
        print("Không có kết quả Lighthouse hợp lệ.")
        return 1

    def med(runs, k):
        vals = [x[k] for x in runs if x.get(k) is not None]
        return statistics.median(vals) if vals else None

    n = max(len(g["runs"]) for g in groups.values())
    out = [f"### Lighthouse {version or ''} – trung vị {n} lần đo mỗi trang (máy GitHub Actions, mặc định của Lighthouse)", "",
           "| Trang | Thiết bị | " + " | ".join(l for _, l in CATS) + " | " + " | ".join(l for _, l, _ in METRICS) + " |",
           "|---|---|" + "---:|" * (len(CATS) + len(METRICS))]
    for (i, mode), g in sorted(groups.items()):
        runs = g["runs"]
        perf = [x["performance"] for x in runs if x["performance"] is not None]
        cats = []
        for cid, _ in CATS:
            v = med(runs, cid)
            cell = "–" if v is None else f"{v:.0f}"
            if cid == "performance" and len(perf) > 1:
                cell += f" ({min(perf):.0f}–{max(perf):.0f})"
            cats.append(cell)
        mets = [fmt(med(runs, aid), unit) for aid, _, unit in METRICS]
        page = g["url"].split("://", 1)[-1]
        out.append(f"| {page} | {'Điện thoại' if mode == 'mobile' else 'Máy tính'} | " + " | ".join(cats) + " | " + " | ".join(mets) + " |")
    out += ["", "Điện thoại: giả lập máy tầm trung + mạng 4G chậm (mặc định Lighthouse). Trong ngoặc: điểm hiệu năng thấp nhất – cao nhất giữa các lần đo."]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "ket-qua"))
