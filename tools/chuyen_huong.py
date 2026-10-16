# -*- coding: utf-8 -*-
"""Dựng bản chuyển hướng cho địa chỉ cũ willmichco.github.io/luatsunam sau khi chuyển sang tên miền riêng (GĐ5).

    python3 tools/chuyen_huong.py dist dist-chuyen-huong https://tenmien.vn

Đọc bản build vừa dựng (dist/) để lấy đủ mọi đường dẫn đang có trên github.io, ghi vào thư mục đích:
  - mỗi đường dẫn cũ 1 trang chuyển ngay tới đúng đường dẫn đó trên tên miền mới: <link rel="canonical"> +
    <meta http-equiv="refresh" content="0"> (Google coi chuyển hướng tức thì là chuyển hướng vĩnh viễn) + JavaScript
    giữ ?tham-số và #mã-neo; trang vốn là chuyển hướng (Cài đặt → Chuyển hướng) đi thẳng tới đích cuối, không qua 2 bước;
  - 404.html: đường dẫn lạ (bài đã gỡ, link gõ sai) cũng sang đúng đường dẫn đó trên tên miền mới;
  - sitemap.xml liệt kê URL CŨ để Google vào lại từng URL và thấy chuyển hướng sớm hơn
    (gửi trong Search Console của property github.io);
  - danh-sach-url.txt: cặp URL cũ → URL mới, dùng cho bộ kiểm G5 (tools/kiem_g5.py).
GitHub Pages không có chuyển hướng 301 thật. Workflow đăng thư mục này thay cho site khi đặt biến repo CHUYEN_HUONG_TOI.
"""
import html
import json
import os
import posixpath
import re
import shutil
import sys

OLD_SITE = "https://willmichco.github.io/luatsunam"
REFRESH_RE = re.compile(r'<meta http-equiv="refresh" content="0; url=([^"]+)"')
NEW_SITE_RE = re.compile(r"^https://[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}$")


def old_paths(dist):
    """Mọi trang HTML của bản build (trừ 404.html, bản nháp): [(đường dẫn, đích trong site nếu trang vốn là chuyển hướng)]."""
    out = []
    for d, dirs, files in os.walk(dist):
        dirs.sort()
        rel_dir = os.path.relpath(d, dist).replace(os.sep, "/")
        rel_dir = "" if rel_dir == "." else rel_dir
        if rel_dir.split("/")[0] == "nhap":
            continue
        for f in sorted(files):
            if not f.endswith(".html") or (f == "404.html" and not rel_dir):
                continue
            rel = posixpath.join(rel_dir, f)
            path = "" if rel == "index.html" else rel[:-len("index.html")] if rel.endswith("/index.html") else rel
            target = None
            with open(os.path.join(d, f), encoding="utf-8") as fh:
                m = REFRESH_RE.search(fh.read(3000))
            if m:  # trang chuyển tiếp nội bộ (vd. /doi-ngu-luat-su/ → /gioi-thieu/#doi-ngu-luat-su): đi thẳng tới đích
                p, sep, frag = html.unescape(m.group(1)).partition("#")
                joined = posixpath.normpath(posixpath.join(rel_dir, p))
                joined = "" if joined in (".", "") else joined + ("/" if p.endswith("/") else "")
                target = joined + ("#" + frag if sep else "")
            out.append((path, target))
    return out


def js_str(s):
    return json.dumps(s, ensure_ascii=False).replace("</", "<\\/")


def page(new_url):
    u = html.escape(new_url, quote=True)
    base, sep, frag = new_url.partition("#")
    canonical = html.escape(base, quote=True)  # canonical không mang #mã-neo
    # JavaScript chạy trước để giữ ?tham-số, #mã-neo; meta refresh cho Google và trình duyệt tắt JavaScript
    return (f'<!doctype html><html lang="vi"><head><meta charset="utf-8">'
            f'<script>location.replace({js_str(base)}+location.search+(location.hash||{js_str("#" + frag if sep else "")}));</script>'
            f'<meta http-equiv="refresh" content="0; url={u}"><link rel="canonical" href="{canonical}">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>Đã chuyển sang {u}</title></head>'
            f'<body><p>Website đã chuyển sang địa chỉ mới: <a href="{u}">{u}</a></p></body></html>\n')


def not_found(new_site, base_path):
    s = html.escape(new_site, quote=True)
    return (f'<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="robots" content="noindex">'
            f'<script>(function(){{var p=location.pathname,b={js_str(base_path)};'
            f'p=p.indexOf(b)===0?p.slice(b.length):p.replace(/^\\//,"");'
            f'location.replace({js_str(new_site + "/")}+p+location.search+location.hash);}})();</script>'
            f'<meta http-equiv="refresh" content="0; url={s}/">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>Website đã chuyển địa chỉ</title></head>'
            f'<body><p>Website đã chuyển sang <a href="{s}/">{s}</a>.</p></body></html>\n')


def build(dist, out, new_site, old_site=OLD_SITE):
    new_site, old_site = new_site.strip().rstrip("/"), old_site.rstrip("/")
    if not NEW_SITE_RE.match(new_site):
        sys.exit(f"Địa chỉ mới “{new_site}” chưa đúng dạng https://tenmien.vn (https, không có thư mục con).")
    paths = old_paths(dist)
    if not any(p == "" for p, _ in paths):
        sys.exit(f"Không thấy trang chủ trong {dist}/ – chạy tools/build.py trước.")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    base_path = re.sub(r"^https?://[^/]+", "", old_site) + "/"
    pairs = []
    for path, target in paths:
        new_url = f"{new_site}/{path if target is None else target}"
        full = os.path.join(out, path if path.endswith(".html") else path + "index.html")
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(page(new_url))
        pairs.append((f"{old_site}/{path}", new_url))
    with open(os.path.join(out, "404.html"), "w", encoding="utf-8") as fh:
        fh.write(not_found(new_site, base_path))
    with open(os.path.join(out, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        fh.writelines(f"  <url><loc>{html.escape(old)}</loc></url>\n" for old, _ in pairs if "/admin/" not in old + "/")
        fh.write("</urlset>\n")
    with open(os.path.join(out, "danh-sach-url.txt"), "w", encoding="utf-8") as fh:
        fh.write("# URL cũ → URL mới (tools/chuyen_huong.py); bộ kiểm G5 đọc tệp này\n")
        fh.writelines(f"{a} {b}\n" for a, b in pairs)
    open(os.path.join(out, ".nojekyll"), "w").close()
    return pairs


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    pairs = build(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f"Đã dựng {len(pairs)} trang chuyển hướng + 404 → {sys.argv[2]}/ (tới {sys.argv[3].strip().rstrip('/')})")


if __name__ == "__main__":
    main()
