# -*- coding: utf-8 -*-
"""Kiểm website đã build trong dist/ (chạy sau tools/build.py, cả trên GitHub Actions).

    python3 tools/kiem_tra.py [dist]

Kiểm:
  1. Mọi trang (trừ trang noindex) có canonical, og:url trỏ đúng địa chỉ gốc SITE_URL (tiêu chí 7).
  2. sitemap.xml chỉ chứa URL thuộc SITE_URL và mỗi URL có trang tương ứng; robots.txt trỏ đúng sitemap.
  3. Mọi liên kết nội bộ, ảnh, CSS, JS trong HTML tới được tệp có thật; mã neo #… tồn tại trên trang đích.
Có lỗi → thoát mã 1 (GitHub Actions không đăng bản lỗi).
"""
import os
import re
import sys
import urllib.parse
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.meta, self.canonical = [], set(), {}, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        if tag == "meta":
            k = a.get("property") or a.get("name")
            if k:
                self.meta[k] = a.get("content", "")
        for attr in ("href", "src"):
            if a.get(attr) and not (tag == "link" and a.get("rel") == "canonical"):
                self.links.append((tag, a[attr]))
        if a.get("srcset"):
            for part in a["srcset"].split(","):
                self.links.append((tag, part.strip().split(" ")[0]))


def main():
    dist = os.path.join(ROOT, sys.argv[1] if len(sys.argv) > 1 else "dist")
    site_url = (os.environ.get("SITE_URL") or "https://willmichco.github.io/luatsunam").rstrip("/")
    errors = []
    warnings = []  # bản nháp riêng dưới /nhap/: không bao giờ chặn site chính thức
    pages = {}
    for d, _, files in os.walk(dist):
        for f in files:
            if f.endswith(".html") and "/admin" not in d.replace(dist, ""):
                rel = os.path.relpath(os.path.join(d, f), dist)
                p = Page()
                p.feed(open(os.path.join(d, f), encoding="utf-8").read())
                pages[rel] = p
    for rel, p in sorted(pages.items()):
        noindex = "noindex" in p.meta.get("robots", "")
        url_path = "" if rel == "index.html" else rel[:-len("index.html")] if rel.endswith("/index.html") else rel
        if not noindex and os.environ.get("NOINDEX", "0") != "1":
            want = f"{site_url}/{url_path}"
            if p.canonical != want:
                errors.append(f"{rel}: canonical “{p.canonical}” phải là “{want}”")
            if p.meta.get("og:url") != want:
                errors.append(f"{rel}: og:url “{p.meta.get('og:url')}” phải là “{want}”")
        for tag, link in p.links:
            if link.startswith(("http:", "https:", "mailto:", "tel:", "data:", "//", "javascript:")) or link == "":
                if link.startswith(site_url + "/") and tag != "meta":
                    errors.append(f"{rel}: liên kết tuyệt đối tới chính site “{link}” – nên dùng đường dẫn tương đối")
                continue
            if rel == "404.html":
                continue  # trang 404 tự đặt thẻ <base> khi chạy
            target, _, anchor = link.partition("#")
            target = urllib.parse.unquote(target.split("?")[0])
            base = os.path.dirname(os.path.join(dist, rel))
            full = os.path.normpath(os.path.join(base, target)) if target else os.path.join(dist, rel)
            if os.path.isdir(full):
                full = os.path.join(full, "index.html")
            if not os.path.isfile(full):
                (warnings if rel.startswith("nhap/") else errors).append(f"{rel}: liên kết hỏng “{link}”")
                continue
            if anchor and full.endswith(".html"):
                trel = os.path.relpath(full, dist)
                if trel in pages and anchor not in pages[trel].ids:
                    errors.append(f"{rel}: mã neo “#{anchor}” không có trên {trel}")
    sm = os.path.join(dist, "sitemap.xml")
    if os.path.isfile(sm):
        for loc in re.findall(r"<loc>(.*?)</loc>", open(sm, encoding="utf-8").read()):
            if not loc.startswith(site_url + "/"):
                errors.append(f"sitemap.xml: “{loc}” không thuộc {site_url}")
                continue
            path = loc[len(site_url) + 1:]
            if not os.path.isfile(os.path.join(dist, path, "index.html") if not path.endswith(".html") else os.path.join(dist, path)):
                errors.append(f"sitemap.xml: “{loc}” không có trang tương ứng")
        robots = open(os.path.join(dist, "robots.txt"), encoding="utf-8").read()
        if f"Sitemap: {site_url}/sitemap.xml" not in robots:
            errors.append("robots.txt không trỏ đúng sitemap")
    for w in warnings:
        print("  ! cảnh báo (bản nháp):", w)
    if errors:
        print(f"✗ {len(errors)} lỗi:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print(f"✓ Đã kiểm {len(pages)} trang HTML: canonical, og:url, sitemap, robots, liên kết nội bộ, mã neo – không có lỗi.")


if __name__ == "__main__":
    main()
