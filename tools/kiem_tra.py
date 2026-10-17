# -*- coding: utf-8 -*-
"""Kiểm website đã build trong dist/ (chạy sau tools/build.py, cả trên GitHub Actions).

    python3 tools/kiem_tra.py [dist]

Kiểm:
  1. Mọi trang (trừ trang noindex) có canonical, og:url trỏ đúng địa chỉ gốc SITE_URL (tiêu chí 7).
  2. sitemap.xml chỉ chứa URL thuộc SITE_URL và mỗi URL có trang tương ứng; robots.txt trỏ đúng sitemap.
  3. Mọi liên kết nội bộ, ảnh, CSS, JS trong HTML tới được tệp có thật; mã neo #… tồn tại trên trang đích.
  4. Cột trái trang quản trị (admin/config.yml, admin/cot-trai.json) xếp đúng thứ tự Menu chính trên website.
  5. SEO từng trang được lập chỉ mục: có <title>, mô tả, đúng 1 thẻ <h1>; tiêu đề, mô tả không trùng trang khác;
     JSON-LD đọc được; ảnh có alt, width, height (chống nhảy bố cục – CLS); 404.html là noindex.
  6. sitemap.xml, RSS (kien-thuc-phap-ly/feed.xml) đúng cú pháp XML; <lastmod> dạng YYYY-MM-DD, không ở tương lai.
Có lỗi → thoát mã 1 (GitHub Actions không đăng bản lỗi).
"""
import datetime
import json
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
        self.h1, self.title, self.imgs, self.ld, self._in = 0, "", [], [], None

    def handle_data(self, data):
        if self._in == "title":
            self.title += data
        elif self._in == "ld":
            self.ld[-1] += data

    def handle_endtag(self, tag):
        if tag in ("title", "script"):
            self._in = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        elif tag == "title":
            self._in = "title"
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._in = "ld"
            self.ld.append("")
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


FIXED = ("trang-chu", "gioi-thieu", "vi-sao-chon-chung-toi", "quy-trinh-lam-viec", "lien-he")
HUBS = {"dich-vu": "dich_vu", "kien-thuc-phap-ly": "bai_viet", "cau-hoi-thuong-gap": "hoi_dap"}


def _unit(path):
    """Đường dẫn trang → phần tương ứng trong cột trái trang quản trị."""
    first = path.strip("/").split("/")[0] or "trang-chu"
    if first in HUBS:
        return ("muc", HUBS[first])
    return ("trang", first) if first in FIXED else None


def check_admin_menu(dist, errors):
    """Thứ tự cột trái trang quản trị = thứ tự Menu chính trên website (đọc từ trang chủ đã build)."""
    cfg_path, home = os.path.join(dist, "admin", "config.yml"), os.path.join(dist, "index.html")
    if not os.path.isfile(cfg_path) or not os.path.isfile(home):
        return
    import yaml
    html = open(home, encoding="utf-8").read()
    m = re.search(r'<nav class="nav" id="nav"[^>]*>(.*?)</nav>', html, re.S)
    menu = []
    for href in re.findall(r'<a [^>]*href="([^"]*)"', m.group(1) if m else ""):
        u = _unit(href.split("#")[0].lstrip("./")) if not href.startswith(("tel:", "http")) else None
        if u and u not in menu:
            menu.append(u)
    cfg = yaml.safe_load(open(cfg_path, encoding="utf-8"))
    cms, labels, files = [], set(), set()
    for c in cfg.get("collections") or []:
        if c.get("divider"):
            if cms:
                break
            continue
        labels.add(c.get("label"))
        if c.get("name") in HUBS.values():
            cms.append(("muc", c["name"]))
        for f in c.get("files") or []:
            files.add(f'{c["name"]}/entries/{f["name"]}')
            mm = re.match(r"^content/trang/([a-z0-9-]+)\.yml$", f.get("file", ""))
            if mm:
                cms.append(("trang", mm.group(1)))
    in_menu = [u for u in cms if u in menu]
    if in_menu != menu:
        name = lambda us: " → ".join(n for _, n in us)  # noqa: E731
        errors.append(f"admin/config.yml: cột trái trang quản trị lệch Menu chính của website. Menu: {name(menu)}; cột trái: {name(in_menu)}")
    if cms[:len(menu)] != in_menu:
        errors.append("admin/config.yml: trang không có trên menu đang nằm xen giữa các trang của menu ở cột trái trang quản trị")
    deco = os.path.join(dist, "admin", "cot-trai.json")
    if os.path.isfile(deco):
        d = json.load(open(deco, encoding="utf-8"))
        for label, text, _ in d.get("tieu_de") or []:
            if label not in {c.get("label") for c in cfg.get("collections") or []}:
                errors.append(f"admin/cot-trai.json: tiêu đề “{text}” gắn vào mục “{label}” không có trong cột trái")
        for label, to in (d.get("mot_tep") or {}).items():
            if to not in files:
                errors.append(f"admin/cot-trai.json: mục “{label}” mở thẳng “{to}” không tồn tại")


def check_seo(dist, pages, errors):
    seen = {"title": {}, "description": {}}
    for rel, p in sorted(pages.items()):
        if rel.startswith("nhap/"):
            continue
        for a in p.imgs:
            name = a.get("src", "")[:60]
            if a.get("alt") is None:
                errors.append(f"{rel}: ảnh “{name}” thiếu thuộc tính alt (mô tả ảnh cho Google, người khiếm thị)")
            if not (a.get("width") and a.get("height")):
                errors.append(f"{rel}: ảnh “{name}” thiếu width/height – bố cục nhảy khi ảnh tải (CLS)")
        for raw in p.ld:
            try:
                json.loads(raw)
            except ValueError as e:
                errors.append(f"{rel}: JSON-LD (dữ liệu có cấu trúc) sai cú pháp: {e}")
        if rel == "404.html" and "noindex" not in p.meta.get("robots", ""):
            errors.append("404.html phải có robots noindex")
        if "noindex" in p.meta.get("robots", "") or "refresh" in p.meta.get("http-equiv", ""):
            continue  # trang chặn Google / trang chuyển tiếp
        for key, value in (("title", p.title.strip()), ("description", p.meta.get("description", "").strip())):
            if not value:
                errors.append(f"{rel}: thiếu {'<title>' if key == 'title' else 'mô tả (meta description)'}")
            elif value in seen[key]:
                errors.append(f"{rel}: {key} trùng với {seen[key][value]} – mỗi trang cần tiêu đề, mô tả riêng")
            else:
                seen[key][value] = rel
        if p.h1 != 1:
            errors.append(f"{rel}: có {p.h1} thẻ <h1>, cần đúng 1")
    import xml.etree.ElementTree as ET
    today = datetime.date.today().isoformat()
    for name in ("sitemap.xml", "kien-thuc-phap-ly/feed.xml"):
        path = os.path.join(dist, name)
        if not os.path.isfile(path):
            continue
        try:
            tree = ET.parse(path)
        except ET.ParseError as e:
            errors.append(f"{name}: sai cú pháp XML ({e})")
            continue
        for el in tree.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod"):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", el.text or "") or el.text > today:
                errors.append(f"{name}: <lastmod> “{el.text}” phải là ngày YYYY-MM-DD, không ở tương lai")


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
    check_seo(dist, pages, errors)
    check_admin_menu(dist, errors)
    for w in warnings:
        print("  ! cảnh báo (bản nháp):", w)
    if errors:
        print(f"✗ {len(errors)} lỗi:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print(f"✓ Đã kiểm {len(pages)} trang HTML: canonical, og:url, sitemap, robots, liên kết nội bộ, mã neo, "
          f"SEO (tiêu đề, mô tả, H1, JSON-LD, ảnh), RSS, cột trái trang quản trị theo menu – không có lỗi.")


if __name__ == "__main__":
    main()
