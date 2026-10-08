# -*- coding: utf-8 -*-
"""Kiểm tra SEO toàn bộ website đã sinh. Chạy sau tools/build.py:

    python3 tools/check_seo.py            # tóm tắt
    python3 tools/check_seo.py -v         # liệt kê từng trang có vấn đề

LỖI (thoát mã 1): sai tên miền canonical, liên kết nội bộ hỏng, JSON-LD hỏng, thiếu
title/description/canonical/H1, trang index được nhưng thiếu trong sitemap (hoặc ngược lại),
ảnh thiếu thuộc tính alt.
CẢNH BÁO: độ dài title/description, trùng lặp, ảnh thiếu kích thước hoặc alt rỗng.
"""
import collections
import html
import json
import os
import re
import sys
from urllib.parse import unquote, urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import SITE_URL  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "src", "tools", "dist", "node_modules", ".github", ".openai", ".sites-runtime"}
# Google cắt title ở khoảng 580px (≈ 60 ký tự tiếng Việt), description ở khoảng 920px (≈ 155–160 ký tự)
TITLE_MAX, DESC_MIN, DESC_MAX = 60, 70, 160


def pages():
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        for f in sorted(files):
            if f.endswith(".html"):
                full = os.path.join(d, f)
                with open(full, encoding="utf-8") as fh:
                    yield os.path.relpath(full, ROOT).replace(os.sep, "/"), fh.read()


def meta(h, attr, name):
    m = re.search(rf'<meta {attr}="{name}" content="([^"]*)"', h)
    return html.unescape(m.group(1)) if m else None


def page_url(rel):
    path = rel[:-len("index.html")] if rel.endswith("index.html") else rel
    return SITE_URL + "/" + path


def main():
    verbose = "-v" in sys.argv
    errors, warns = collections.defaultdict(list), collections.defaultdict(list)
    titles, descs = collections.defaultdict(list), collections.defaultdict(list)
    indexable = set()
    n_img = 0

    for rel, h in pages():
        redirect = 'http-equiv="refresh"' in h
        noindex = re.search(r'<meta name="robots" content="[^"]*noindex', h) is not None
        canon = re.search(r'<link rel="canonical" href="([^"]+)"', h)

        if canon and not canon.group(1).startswith(SITE_URL + "/"):
            errors["canonical khác tên miền SITE_URL"].append(rel)
        og_url = meta(h, "property", "og:url")
        if og_url and not og_url.startswith(SITE_URL + "/"):
            errors["og:url khác tên miền SITE_URL"].append(rel)

        # Liên kết nội bộ và tài nguyên
        for attr, link in re.findall(r'\b(href|src)="([^"]+)"', h):
            if link.startswith(("http:", "https:", "mailto:", "tel:", "#", "data:", "javascript:", "//", "{")):
                continue
            path = unquote(urlsplit(link).path)
            if not path or (rel == "404.html" and path.startswith("/")):
                continue  # 404 dùng đường dẫn gốc của máy chủ (BASE_PATH)
            target = os.path.normpath(os.path.join(ROOT, os.path.dirname(rel), path))
            if path.endswith("/") or os.path.isdir(target):
                target = os.path.join(target, "index.html")
            if not os.path.exists(target):
                errors["liên kết nội bộ hỏng"].append(f"{rel} → {link}")

        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
            try:
                json.loads(block)
            except ValueError as e:
                errors["JSON-LD không hợp lệ"].append(f"{rel}: {e}")

        if redirect:
            continue
        if noindex:
            if canon:
                errors["noindex nhưng có canonical (tín hiệu mâu thuẫn)"].append(rel)
            continue

        indexable.add(page_url(rel))
        m = re.search(r"<title>(.*?)</title>", h, re.S)
        title = html.unescape(m.group(1)).strip() if m else ""
        desc = meta(h, "name", "description") or ""
        if not title:
            errors["thiếu title"].append(rel)
        elif len(title) > TITLE_MAX:
            warns[f"title dài hơn {TITLE_MAX} ký tự"].append(f"{rel} ({len(title)})")
        if not desc:
            errors["thiếu meta description"].append(rel)
        elif len(desc) > DESC_MAX:
            warns[f"description dài hơn {DESC_MAX} ký tự"].append(f"{rel} ({len(desc)})")
        elif len(desc) < DESC_MIN:
            warns[f"description ngắn hơn {DESC_MIN} ký tự"].append(f"{rel} ({len(desc)})")
        titles[title].append(rel)
        descs[desc].append(rel)
        if not canon:
            errors["thiếu canonical"].append(rel)
        elif canon.group(1) != page_url(rel):
            warns["canonical trỏ sang trang khác"].append(f"{rel} → {canon.group(1)}")
        n_h1 = len(re.findall(r"<h1[\s>]", h))
        if n_h1 != 1:
            errors[f"số thẻ H1 khác 1"].append(f"{rel} ({n_h1})")

        for tag in re.findall(r"<img\b[^>]*>", h):
            n_img += 1
            if " alt=" not in tag:
                errors["ảnh thiếu thuộc tính alt"].append(rel)
            elif 'alt=""' in tag:
                warns["ảnh alt rỗng (ảnh trang trí)"].append(rel)
            if "width=" not in tag or "height=" not in tag:
                warns["ảnh thiếu width/height (gây xô lệch bố cục)"].append(rel)

    for t, rels in titles.items():
        if t and len(rels) > 1:
            warns["title trùng nhau"].append(", ".join(rels))
    for d, rels in descs.items():
        if d and len(rels) > 1:
            warns["description trùng nhau"].append(", ".join(rels))

    # Sitemap, robots.txt
    with open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8") as fh:
        sm = fh.read()
    locs = set(re.findall(r"<loc>([^<]+)</loc>", sm))
    for u in sorted(locs - indexable):
        errors["sitemap có URL không phải trang index được"].append(u)
    for u in sorted(indexable - locs):
        errors["trang index được nhưng thiếu trong sitemap"].append(u)
    for d in re.findall(r"<lastmod>([^<]+)</lastmod>", sm):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            errors["lastmod sai định dạng"].append(d)
    with open(os.path.join(ROOT, "robots.txt"), encoding="utf-8") as fh:
        if f"Sitemap: {SITE_URL}/sitemap.xml" not in fh.read():
            errors["robots.txt không trỏ sitemap của SITE_URL"].append("robots.txt")

    print(f"Tên miền: {SITE_URL}")
    print(f"Trang index được: {len(indexable)} · sitemap: {len(locs)} URL, "
          f"{sm.count('<image:loc>')} ảnh · thẻ <img> đã kiểm: {n_img}")
    for label, group in (("LỖI", errors), ("CẢNH BÁO", warns)):
        print(f"\n{label}: {sum(len(v) for v in group.values()) or 'không có'}")
        for k, v in sorted(group.items(), key=lambda kv: -len(kv[1])):
            uniq = list(dict.fromkeys(v))
            print(f"  {len(v):5}  {k}" + ("" if verbose else f"   ví dụ: {uniq[0]}"))
            if verbose:
                for x in uniq:
                    print(f"         - {x}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
