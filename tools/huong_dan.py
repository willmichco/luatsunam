# -*- coding: utf-8 -*-
"""Trang hướng dẫn sử dụng /admin/huong-dan/ – dựng từ docs/huong-dan/README.md; kèm bài tập /admin/bai-tap/.

Một nguồn duy nhất: đọc được ngay trên GitHub (ảnh cùng thư mục), build dựng thành trang có mục lục,
ảnh bấm để phóng to, in được; nút "? Hướng dẫn" trong /admin mở trang này. Không lập chỉ mục Google.
"""
import os
import re
import shutil

from markdown_it import MarkdownIt

from markup import esc, slugify

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "huong-dan")

MD = MarkdownIt("commonmark", {"html": False})
MD.enable(["table"])

CSS = """
:root { --brand: #b5000b; --brand-700: #93000a; --ink: #2b1d21; --text: #4a4245; --muted: #6b6064; --line: #ebe1d3;
  --cream: #f8f2e8; --bg: #fffdf9; --note: #fff8e6; --note-line: #e8c46a; }
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; background: var(--bg); color: var(--text); font: 16px/1.7 system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif; }
a { color: var(--brand); overflow-wrap: anywhere; }
main { overflow-wrap: break-word; }
.top { position: sticky; top: 0; z-index: 5; display: flex; gap: 16px; align-items: center; padding: 10px 20px;
  background: var(--brand-700); color: #fff; font-size: 14px; }
.top strong { font-size: 15px; margin-right: auto; color: #fff; }
.top a { color: #fff; text-decoration: none; padding: 4px 10px; border: 1px solid rgba(255,255,255,.45); border-radius: 999px; white-space: nowrap; }
.top a:hover { background: rgba(255,255,255,.12); }
.wrap { display: grid; grid-template-columns: 250px minmax(0, 1fr); gap: 40px; max-width: 1180px; margin: 0 auto; padding: 28px 20px 80px; }
nav.toc { position: sticky; top: 64px; align-self: start; max-height: calc(100vh - 80px); overflow: auto; font-size: 14.5px; }
nav.toc p { margin: 0 0 8px; font-weight: 700; color: var(--ink); text-transform: uppercase; letter-spacing: .04em; font-size: 12.5px; }
nav.toc ol { list-style: none; margin: 0; padding: 0; counter-reset: toc; }
nav.toc li { counter-increment: toc; }
nav.toc a { display: block; padding: 6px 10px; border-left: 3px solid transparent; color: var(--text); text-decoration: none; }
nav.toc a::before { content: counter(toc) ". "; color: var(--muted); }
nav.toc a:hover, nav.toc a.on { border-left-color: var(--brand); color: var(--ink); background: var(--cream); }
main { min-width: 0; max-width: 860px; }
h1 { margin: 0 0 14px; color: var(--ink); font-size: clamp(26px, 3.2vw, 34px); line-height: 1.25; }
h2 { margin: 52px 0 10px; padding-top: 12px; border-top: 1px solid var(--line); color: var(--ink); font-size: 24px; line-height: 1.3; scroll-margin-top: 70px; }
h3 { margin: 28px 0 8px; color: var(--ink); font-size: 18px; }
ol, ul { padding-left: 1.4em; }
li + li { margin-top: .45em; }
li > p { margin: .3em 0; }
strong { color: var(--ink); }
code { padding: .1em .35em; background: var(--cream); border-radius: 4px; font: .92em/1.5 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; color: var(--ink); }
pre { overflow-x: auto; padding: 12px 14px; background: #2e1e22; color: #f3e9e6; border-radius: 8px; font-size: 13.5px; line-height: 1.6; }
pre code { padding: 0; background: none; color: inherit; }
blockquote { margin: 18px 0; padding: 12px 16px; background: var(--note); border: 1px solid var(--note-line); border-left-width: 4px; border-radius: 8px; color: var(--ink); }
blockquote p { margin: 0; }
figure { margin: 14px 0 20px; }
figure a { display: block; }
figure img { display: block; max-width: 100%; height: auto; border: 1px solid var(--line); border-radius: 10px; box-shadow: 0 6px 20px rgba(43,29,33,.10); background: #fff; }
figcaption { margin-top: 6px; color: var(--muted); font-size: 13.5px; }
.note-top { margin: 0 0 6px; color: var(--muted); font-size: 14px; }
@media (max-width: 900px) {
  .wrap { grid-template-columns: minmax(0, 1fr); gap: 8px; padding: 18px 16px 60px; }
  nav.toc { position: static; max-height: none; padding: 10px 12px; background: var(--cream); border-radius: 10px; }
  .top strong { display: none; }
}
@media print {
  .top, nav.toc { display: none; }
  .wrap { display: block; padding: 0; }
  h2 { break-after: avoid; }
  figure { break-inside: avoid; }
  figure img { max-height: 420px; width: auto; box-shadow: none; }
  a { color: inherit; text-decoration: none; }
}
"""

JS = """
(function () {
  var links = [].slice.call(document.querySelectorAll('nav.toc a'));
  var heads = links.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
  function on() {
    var y = window.scrollY + 90, cur = 0;
    heads.forEach(function (h, i) { if (h && h.offsetTop <= y) cur = i; });
    links.forEach(function (a, i) { a.classList.toggle('on', i === cur); });
  }
  window.addEventListener('scroll', on, {passive: true}); on();
})();
"""


def _image_size(name):
    try:
        from PIL import Image
        with Image.open(os.path.join(SRC, name)) as im:
            return im.size
    except Exception:
        return None


def render(text):
    tokens = MD.parse(text)
    toc, used, title = [], set(), "Hướng dẫn sử dụng"
    n_img = 0
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open":
            words = "".join(c.content for c in tokens[i + 1].children or [] if c.type in ("text", "code_inline"))
            if tok.tag == "h1":
                title = words
                continue
            base = slugify(re.sub(r"^\d+[.)]\s*", "", words), 50) or "muc"
            hid, k = base, 2
            while hid in used:
                hid, k = f"{base}-{k}", k + 1
            used.add(hid)
            tok.attrSet("id", hid)
            if tok.tag == "h2":
                toc.append((hid, re.sub(r"^\d+[.)]\s*", "", words)))
        elif tok.type == "inline":
            for c in tok.children or []:
                if c.type == "link_open" and re.match(r"https?://", c.attrGet("href") or ""):
                    c.attrSet("target", "_blank")
                    c.attrSet("rel", "noopener")
                elif c.type == "image":
                    n_img += 1
                    size = _image_size(c.attrGet("src") or "")
                    if size:
                        c.attrSet("width", str(size[0]))
                        c.attrSet("height", str(size[1]))
                    if n_img > 2:
                        c.attrSet("loading", "lazy")
                    c.attrSet("decoding", "async")
    body = MD.renderer.render(tokens, MD.options, {})

    def figure(m):
        img = m.group(1)
        src = re.search(r'src="([^"]*)"', img).group(1)
        cap = re.search(r' title="([^"]*)"', img)
        if cap:
            img = img.replace(cap.group(0), "")
        out = f'<figure><a href="{src}" target="_blank" rel="noopener" title="Bấm để xem ảnh cỡ lớn">{img}</a>'
        return out + (f"<figcaption>{cap.group(1)}</figcaption>" if cap else "") + "</figure>"
    body = re.sub(r"<p>(<img [^>]*>)</p>", figure, body)
    return title, toc, body


SOURCE_SITE = "https://willmichco.github.io/luatsunam"  # địa chỉ site ghi trong docs/huong-dan/README.md


def build(out, site_url=SOURCE_SITE):
    """Ghi out/admin/huong-dan/index.html và chép ảnh minh họa. Không có nguồn thì bỏ qua.
    Địa chỉ site trong nguồn được đổi theo địa chỉ đang build (tên miền riêng sau GĐ5)."""
    src_md = os.path.join(SRC, "README.md")
    if not os.path.isfile(src_md):
        return
    md = open(src_md, encoding="utf-8").read()
    if site_url != SOURCE_SITE:
        md = md.replace(SOURCE_SITE + "/", site_url + "/").replace(SOURCE_SITE.split("://", 1)[1] + "/", site_url.split("://", 1)[1] + "/")
    title, toc, body = render(md)
    dst = os.path.join(out, "admin", "huong-dan")
    os.makedirs(dst, exist_ok=True)
    for name in os.listdir(SRC):
        if name.lower().endswith((".webp", ".png", ".jpg", ".jpeg", ".gif", ".svg")):
            shutil.copy2(os.path.join(SRC, name), os.path.join(dst, name))
    items = "".join(f'<li><a href="#{hid}">{esc(t)}</a></li>' for hid, t in toc)
    html = f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{esc(title)}</title>
<style>{CSS}</style>
</head>
<body>
<header class="top"><strong>{esc(title)}</strong><a href="../">← Trang quản trị</a><a href="../../" target="_blank" rel="noopener">Xem website</a></header>
<div class="wrap">
<nav class="toc" aria-label="Mục lục"><p>Mục lục</p><ol>{items}</ol></nav>
<main>
{body}
</main>
</div>
<script>{JS}</script>
</body>
</html>
"""
    with open(os.path.join(dst, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    # Bài tập làm quen có bấm giờ (trang tĩnh, tự chứa): /admin/bai-tap/
    bai_tap = os.path.join(ROOT, "docs", "bai-tap", "index.html")
    if os.path.isfile(bai_tap):
        os.makedirs(os.path.join(out, "admin", "bai-tap"), exist_ok=True)
        shutil.copy2(bai_tap, os.path.join(out, "admin", "bai-tap", "index.html"))
