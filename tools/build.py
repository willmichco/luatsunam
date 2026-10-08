# -*- coding: utf-8 -*-
"""Sinh toàn bộ website tĩnh LSN Law Firm – Công Ty Luật TNHH Luật Sư Nam.

    python3 tools/build.py

Nguồn nội dung:
    tools/data.py            Thông tin pháp nhân, 8 lĩnh vực, bài viết, câu hỏi thường gặp
    src/pages/*.html         Nội dung các trang đơn lẻ (có khối <!--meta {...} --> ở đầu)
    src/bai-viet/*.html      Nội dung bài viết
    src/bo-luat-hinh-su.html Nội dung trang tra cứu Bộ luật Hình sự

Giao diện: mọi trang dùng chung assets/css/pages.css (thành phần tiền tố ls-, sinh bởi các hàm
page_hero_html, help_card, call_buttons, contact_band, problems_grid... dưới đây), trừ Từ điển
Bộ luật Hình sự giữ bộ giao diện riêng (reader-design.css, bo-luat-hinh-su/tu-dien.css).

Kết quả: <duong-dan>/index.html cho mọi trang, 404.html, sitemap.xml, robots.txt,
site.webmanifest, assets/search-index.json.
"""
import datetime
import hashlib
import html
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blhs  # noqa: E402
from data import (ARTICLE_BY_SLUG, ARTICLES, BASE_PATH, FAQ, FIRM, PROBLEM_ORDER,  # noqa: E402
                  SERVICE_BY_SLUG, SERVICES, SITE_URL, articles_for_service)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
TODAY = datetime.date.today().isoformat()
ORG_ID = SITE_URL + "/#organization"
SITE_ID = SITE_URL + "/#website"
ASSET_VERSION = "20260925a"


def esc(s):
    return html.escape(s, quote=True)


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def file_hash(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()[:8]


# Google cắt title ở khoảng 580px (≈ 60 ký tự tiếng Việt), description ở khoảng 920px
# (≈ 155–160 ký tự). Tên website đã hiện riêng phía trên kết quả tìm kiếm, nên chỉ gắn
# đuôi "| Luật Sư Nam" khi còn đủ chỗ, ưu tiên giữ từ khóa chính.
TITLE_MAX, DESC_MAX = 60, 158


def seo_title(*candidates, brand=True):
    """Chọn phương án title đầu tiên vừa TITLE_MAX; thử kèm tên thương hiệu trước.
    Không phương án nào vừa thì dùng phương án cuối, không cắt chữ giữa chừng
    (cắt tên tội danh, tên chương sẽ làm sai nghĩa)."""
    opts = []
    for c in candidates:
        if brand and not c.endswith(FIRM["short_name"]):
            opts.append(f'{c} | {FIRM["short_name"]}')
        opts.append(c)
    return next((o for o in opts if len(o) <= TITLE_MAX), opts[-1])


def fit_desc(text, limit=DESC_MAX):
    """Cắt description ở ranh giới từ, không vượt limit ký tự."""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[:limit - 1].rsplit(" ", 1)[0].rstrip(",;:–-— ") + "…"


def abs_url(path):
    return SITE_URL + "/" + path


def asset_ref(path):
    return f"{path}?v={ASSET_VERSION}"


# ---------------------------------------------------------------------------
# Biểu tượng SVG (sprite)
# ---------------------------------------------------------------------------
SPRITE = """<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">
  <symbol id="i-arrow" viewBox="0 0 24 24"><path d="M4 12h15M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  <symbol id="i-chevron" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  <symbol id="i-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M20 20l-4-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></symbol>
  <symbol id="i-menu" viewBox="0 0 24 24"><path d="M3 6h18M3 12h18M3 18h18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></symbol>
  <symbol id="i-close" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></symbol>
  <symbol id="i-scale" viewBox="0 0 48 48"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M24 6v34M14 42h20M10 12h28"/><path d="M12 12L5 27h14L12 12zM36 12l-7 15h14l-7-15z"/><path d="M5 27a7 4 0 0 0 14 0M29 27a7 4 0 0 0 14 0"/></g></symbol>
  <symbol id="i-shield" viewBox="0 0 48 48"><path d="M24 4l16 6v12c0 10-7 18-16 22C15 40 8 32 8 22V10l16-6z" fill="currentColor"/><path d="M24 15l2.6 5.4 5.9.8-4.3 4.1 1 5.8L24 28.3l-5.2 2.8 1-5.8-4.3-4.1 5.9-.8L24 15z" fill="#fff"/></symbol>
  <symbol id="i-team" viewBox="0 0 48 48"><g fill="currentColor"><circle cx="24" cy="15" r="6"/><circle cx="11" cy="18" r="4.5"/><circle cx="37" cy="18" r="4.5"/><path d="M13 36c0-6.6 4.9-11 11-11s11 4.4 11 11v2H13v-2z"/><path d="M3 36c0-5 3.4-8.5 8-8.5 1.4 0 2.6.3 3.7.9A13.6 13.6 0 0 0 11 36v2H3v-2zM45 36c0-5-3.4-8.5-8-8.5-1.4 0-2.6.3-3.7.9A13.6 13.6 0 0 1 37 36v2h8v-2z"/></g></symbol>
  <symbol id="i-inherit" viewBox="0 0 48 48"><path d="M24 7 10 15v25h28V15L24 7Zm-7 33V23h14v17M18 16h12M21 29h6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  <symbol id="i-gavel" viewBox="0 0 48 48"><path d="M9 39h30M15 39V24h18v15M20 30h8M24 24V10m-8 7 8-7 8 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  <symbol id="i-house" viewBox="0 0 48 48"><path d="M12 41V9h24v32M8 41h32M18 16h4m4 0h4m-12 7h4m4 0h4m-12 7h4m4 0h4M21 41v-5h6v5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  <symbol id="i-heart" viewBox="0 0 48 48"><path d="M24 41S6 30 6 17.5A9.5 9.5 0 0 1 24 13a9.5 9.5 0 0 1 18 4.5C42 30 24 41 24 41z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></symbol>
  <symbol id="i-doc" viewBox="0 0 48 48"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"><path d="M12 6h18l8 8v28H12z"/><path d="M30 6v8h8M18 20h14M18 26h14M18 32h10"/></g></symbol>
  <symbol id="i-network" viewBox="0 0 48 48"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="24" cy="12" r="5"/><circle cx="10" cy="20" r="4"/><circle cx="38" cy="20" r="4"/><path d="M14 38c0-6 4.5-10 10-10s10 4 10 10M2 36c0-4.5 3-7.5 8-7.5M46 36c0-4.5-3-7.5-8-7.5"/></g></symbol>
  <symbol id="i-shield-check" viewBox="0 0 48 48"><path d="M24 7 10 13v10c0 9 5.8 15.3 14 18 8.2-2.7 14-9 14-18V13L24 7Zm-6 17 4 4 8-9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  <symbol id="i-diamond" viewBox="0 0 48 48"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 8h24l8 10-20 24L4 18z"/><path d="M4 18h40M18 8l-4 10 10 24 10-24-4-10"/></g></symbol>
  <symbol id="i-steps" viewBox="0 0 48 48"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="12" r="4"/><circle cx="38" cy="36" r="4"/><path d="M14 12h14a6 6 0 0 1 0 12H20a6 6 0 0 0 0 12h14"/></g></symbol>
  <symbol id="i-user" viewBox="0 0 48 48"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="24" cy="16" r="8"/><path d="M8 42c0-9 7-15 16-15s16 6 16 15"/></g></symbol>
  <symbol id="i-clock48" viewBox="0 0 48 48"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="24" cy="24" r="18"/><path d="M24 13v11l7 5"/></g></symbol>
  <symbol id="i-book" viewBox="0 0 48 48"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"><path d="M8 9h13a5 5 0 0 1 5 5v26a4 4 0 0 0-4-4H8z"/><path d="M40 9H29a5 5 0 0 0-3 1M40 9v27H30a4 4 0 0 0-4 4"/></g></symbol>
  <symbol id="i-question" viewBox="0 0 48 48"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="24" cy="24" r="18"/><path d="M18.5 19a5.5 5.5 0 1 1 7.7 5c-1.4.7-2.2 1.8-2.2 3.3V29M24 35v.5"/></g></symbol>
  <symbol id="i-pin" viewBox="0 0 24 24"><path d="M12 2a7 7 0 0 0-7 7c0 5.3 7 13 7 13s7-7.7 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z" fill="currentColor"/></symbol>
  <symbol id="i-phone" viewBox="0 0 24 24"><path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z" fill="currentColor"/></symbol>
  <symbol id="i-mail" viewBox="0 0 24 24"><path d="M3 5h18a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zm1 2.2V17h16V7.2l-8 5.3-8-5.3zM5.5 7l6.5 4.3L18.5 7h-13z" fill="currentColor"/></symbol>
  <symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 7v5l3 2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></symbol>
  <symbol id="i-chat" viewBox="0 0 24 24"><path d="M4 5h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H9l-5 4v-4H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></symbol>
  <symbol id="i-up" viewBox="0 0 24 24"><path d="M6 15l6-6 6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  <symbol id="i-check" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  <symbol id="i-calendar" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></g></symbol>
  <symbol id="i-arrow-l" viewBox="0 0 24 24"><path d="M20 12H5M11 6l-6 6 6 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  <symbol id="i-chevron-r" viewBox="0 0 24 24"><path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  <symbol id="i-bookmark" viewBox="0 0 24 24"><path d="M6 3h12v18l-6-4.5L6 21z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></symbol>
  <symbol id="i-print" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M7 8V3h10v5M7 17H4V9h16v8h-3"/><path d="M7 14h10v7H7z"/></g></symbol>
  <symbol id="i-share" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="18" cy="5" r="2.5"/><circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="19" r="2.5"/><path d="M8.2 10.8l7.6-4.4M8.2 13.2l7.6 4.4"/></g></symbol>
  <symbol id="i-copy" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><rect x="8" y="8" width="12" height="13" rx="1.5"/><path d="M16 8V4.5A1.5 1.5 0 0 0 14.5 3h-9A1.5 1.5 0 0 0 4 4.5V16a1.5 1.5 0 0 0 1.5 1.5H8"/></g></symbol>
  <symbol id="i-link" viewBox="0 0 24 24"><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></symbol>
  <symbol id="i-map" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><rect x="9" y="3" width="6" height="5" rx="1"/><rect x="2" y="16" width="6" height="5" rx="1"/><rect x="9" y="16" width="6" height="5" rx="1"/><rect x="16" y="16" width="6" height="5" rx="1"/><path d="M12 8v4M5 16v-4h14v4M12 12v4"/></g></symbol>
  <symbol id="i-alert" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 3 2 20h20L12 3z" stroke-linejoin="round"/><path d="M12 10v4M12 17v.5"/></g></symbol>
</svg>"""


# Biểu tượng bổ sung cho các trang dùng pages.css (không chèn vào trang Từ điển Bộ luật Hình sự)
EXTRA_SYMBOLS = """  <symbol id="i-lock" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3M12 15v2"/></g></symbol>
  <symbol id="i-coin" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="6" width="19" height="12" rx="2"/><circle cx="12" cy="12" r="2.6"/><path d="M6 9.5v.01M18 14.5v.01"/></g></symbol>
  <symbol id="i-check-circle" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8 12.4l2.8 2.8L16.2 9.8"/></g></symbol>
  <symbol id="i-list" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M9 6h11M9 12h11M9 18h11"/><path d="M4.5 6h.01M4.5 12h.01M4.5 18h.01" stroke-width="2.6"/></g></symbol>
"""


def ico(name, cls="ico"):
    return f'<svg class="{cls}" aria-hidden="true"><use href="#{name}"/></svg>'


ARROW = ico("i-arrow")

# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------
NAV = [
    ("home", "Trang chủ", "", None),
    ("about", "Giới thiệu", "gioi-thieu/", [
        ("Về Luật Sư Nam", "gioi-thieu/", "Triết lý hành nghề và cam kết nghề nghiệp"),
        ("Vì sao chọn chúng tôi", "vi-sao-chon-chung-toi/", "Bốn nguyên tắc trong mọi hồ sơ"),
        ("Quy trình làm việc", "quy-trinh-lam-viec/", "Bốn bước và hồ sơ cần chuẩn bị"),
    ]),
    ("services", "Dịch vụ", "dich-vu/", "services"),
    ("knowledge", "Thư viện pháp lý", "kien-thuc-phap-ly/", [
        ("Bài viết pháp lý", "kien-thuc-phap-ly/", "Phân tích, hướng dẫn theo từng lĩnh vực"),
        ("Tra cứu Bộ luật Hình sự", "bo-luat-hinh-su/", "Toàn văn kèm bình luận từng điều"),
        ("Câu hỏi thường gặp", "cau-hoi-thuong-gap/", "Chi phí, bảo mật, thời hạn"),
    ]),
    ("contact", "Liên hệ", "lien-he/", None),
]


def cur(page, href):
    return ' aria-current="page"' if page["path"] == href else ""


def nav_html(page, r):
    items = []
    for key, label, href, sub in NAV:
        active = page.get("section") == key
        current = page["path"] == href
        attrs = ' aria-current="page"' if current else ""
        cls = "nav__link" + (" is-active" if active else "")
        if not sub:
            items.append(f'<li class="nav__item"><a class="{cls}" href="{r}{href}"{attrs}>{label}</a></li>')
            continue
        sid = f"sub-{key}"
        if sub == "services":
            groups = [
                ("Cá nhân & gia đình", ["dan-su", "dat-dai-bat-dong-san", "hon-nhan-gia-dinh", "thua-ke"]),
                ("Tranh chấp & thủ tục", ["tranh-tung-giai-quyet-tranh-chap", "hinh-su", "lao-dong-viec-lam", "cong-chung"]),
            ]
            links = ""
            for group_title, slugs in groups:
                group_links = "".join(
                    f'<li><a class="nav__sublink" href="{r}dich-vu/{s["slug"]}/"{cur(page, "dich-vu/" + s["slug"] + "/")}>'
                    f'{ico(s["icon"], "nav__subicon")}<span>{esc(s["name"])}</span></a></li>'
                    for slug in slugs for s in [SERVICE_BY_SLUG[slug]])
                links += f'<li class="nav__group"><p class="nav__group-title">{esc(group_title)}</p><ul>{group_links}</ul></li>'
            links += f'<li class="nav__suball"><a href="{r}dich-vu/"{cur(page, "dich-vu/")}>Tổng quan dịch vụ pháp lý {ARROW}</a></li>'
            sub_cls = "nav__sub nav__sub--mega"
        else:
            links = "".join(
                f'<li><a class="nav__sublink" href="{r}{h}"{cur(page, h)}>'
                f'<span>{esc(t)}<small>{esc(d)}</small></span></a></li>' for t, h, d in sub)
            sub_cls = "nav__sub"
        items.append(
            f'<li class="nav__item has-sub"><button class="{cls} nav__toggle" type="button" '
            f'aria-expanded="false" aria-controls="{sid}"><span>{label}</span>{ico("i-chevron")}</button>'
            f'<ul class="{sub_cls}" id="{sid}">{links}</ul></li>')
    return "\n        ".join(items)


def logo_html(r, tag=None):
    """Logo kèm chữ. Thanh menu (tag=None): "Công Ty Luật TNHH" / "Luật Sư Nam";
    footer: "Luật Sư Nam" / khẩu hiệu (logo footer nằm cuối trang nên tải chậm)."""
    if tag is None:
        text = '<span class="logo__pre">Công Ty Luật TNHH</span><span class="logo__name">Luật Sư Nam</span>'
        lazy = ""
    else:
        text = f'<span class="logo__name">LUẬT SƯ NAM</span><span class="logo__tag">{tag}</span>'
        lazy = ' loading="lazy" decoding="async"'
    return f"""<a class="logo" href="{r or './'}" aria-label="{FIRM["legal_name"]} – Trang chủ">
      <img class="logo__img" src="{r}assets/img/logo-mark.webp?v=20261007a" width="88" height="88" alt=""{lazy}>
      <span class="logo__text">{text}</span>
    </a>"""


def header_html(page, r):
    return f"""<div class="topbar">
  <div class="container topbar__inner">
    <div class="topbar__info">
      <span>{ico("i-clock")}{FIRM["hours"]}</span>
      <a href="mailto:{FIRM["email"]}">{ico("i-mail")}{FIRM["email"]}</a>
    </div>
    <div class="topbar__right">
      <span class="topbar__addr">{ico("i-pin")}{FIRM["street"]}, {FIRM["ward"]}, TP.HCM</span>
      <a class="topbar__hotline" href="tel:{FIRM["phone_tel"]}">{ico("i-phone")}Hotline: {FIRM["phone"]}</a>
    </div>
  </div>
</div>

<header class="header site-header" id="site-header">
  <div class="container header__inner">
    {logo_html(r)}

    <nav class="nav" id="nav" aria-label="Điều hướng chính">
      <ul class="nav__list">
        {nav_html(page, r)}
      </ul>
      <div class="nav__mobile-extra">
        <a class="btn btn--primary btn--block" href="{r}lien-he/#lien-he-truc-tiep">Liên hệ tư vấn {ARROW}</a>
        <a class="nav__hotline" href="tel:{FIRM["phone_tel"]}">{ico("i-phone")} {FIRM["phone"]}</a>
      </div>
    </nav>

    <div class="header__actions">
      <button class="header__search" type="button" aria-label="Tìm kiếm trên website" aria-haspopup="dialog" data-open-search>{ico("i-search")}<span>Tìm kiếm</span></button>
      <a class="header__call" href="tel:{FIRM["phone_tel"]}" aria-label="Gọi tư vấn {FIRM["phone"]}">{ico("i-phone")}<span><small>Gọi tư vấn</small><strong>{FIRM["phone"]}</strong></span></a>
      <button class="icon-btn burger" type="button" aria-label="Mở menu" aria-expanded="false" aria-controls="nav" id="burger">{ico("i-menu", "")}</button>
    </div>
  </div>
</header>"""


def footer_html(r):
    services = "".join(f'<li><a href="{r}dich-vu/{s["slug"]}/">{esc(s["name"])}</a></li>' for s in SERVICES)
    return f"""<footer class="footer site-footer">
  <div class="container footer__grid">
    <div class="footer__brand">
      {logo_html(r, FIRM["slogan"])}
      <p class="footer__about"><strong>{FIRM["legal_name"]}</strong> tư vấn pháp luật, đại diện và tham gia tố tụng cho cá nhân, doanh nghiệp tại Thành phố Hồ Chí Minh và các tỉnh thành trên cả nước. Hoạt động theo Giấy đăng ký hoạt động do Sở Tư pháp cấp.</p>
      <div class="social">
        <a href="{FIRM["zalo"]}" target="_blank" rel="noopener" aria-label="Nhắn Zalo {FIRM["phone"]}" class="social__zalo">Zalo</a>
        <a href="tel:{FIRM["phone_tel"]}" aria-label="Gọi {FIRM["phone"]}">{ico("i-phone", "")}</a>
        <a href="mailto:{FIRM["email"]}" aria-label="Gửi email">{ico("i-mail", "")}</a>
        <a href="https://www.google.com/maps/search/?api=1&amp;query={FIRM["maps_query"]}" target="_blank" rel="noopener" aria-label="Mở bản đồ văn phòng">{ico("i-pin", "")}</a>
      </div>
    </div>

    <div>
      <h2 class="footer__title">Về chúng tôi</h2>
      <ul class="footer__links">
        <li><a href="{r}gioi-thieu/">Giới thiệu Luật Sư Nam</a></li>
        <li><a href="{r}vi-sao-chon-chung-toi/">Vì sao chọn chúng tôi</a></li>
        <li><a href="{r}quy-trinh-lam-viec/">Quy trình làm việc</a></li>
        <li><a href="{r}kien-thuc-phap-ly/">Kiến thức pháp lý</a></li>
        <li><a href="{r}bo-luat-hinh-su/">Tra cứu Bộ luật Hình sự</a></li>
        <li><a href="{r}cau-hoi-thuong-gap/">Câu hỏi thường gặp</a></li>
        <li><a href="{r}lien-he/">Liên hệ</a></li>
      </ul>
    </div>

    <div>
      <h2 class="footer__title">Lĩnh vực hoạt động</h2>
      <ul class="footer__links">{services}</ul>
    </div>

    <div>
      <h2 class="footer__title">Văn phòng</h2>
      <ul class="footer__contact">
        <li>{ico("i-pin")}<span>{FIRM["street"]},<br>{FIRM["ward"]},<br>{FIRM["city"]}</span></li>
        <li>{ico("i-phone")}<a href="tel:{FIRM["phone_tel"]}">{FIRM["phone"]}</a></li>
        <li>{ico("i-mail")}<a href="mailto:{FIRM["email"]}">{FIRM["email"]}</a></li>
        <li>{ico("i-clock")}<span>{FIRM["hours"]}</span></li>
      </ul>
    </div>
  </div>
  <div class="footer__disclaimer">
    <div class="container">
      <p><strong>Miễn trừ trách nhiệm:</strong> Nội dung trên website chỉ mang tính thông tin pháp lý chung, không phải ý kiến tư vấn cho một vụ việc cụ thể và không làm phát sinh quan hệ luật sư – khách hàng. Quy định pháp luật có thể thay đổi theo thời điểm. Xem đầy đủ tại <a href="{r}mien-tru-trach-nhiem/">Tuyên bố miễn trừ trách nhiệm</a>.</p>
    </div>
  </div>
  <div class="footer__bottom">
    <div class="container footer__bottom-inner">
      <p>© <span data-year>{TODAY[:4]}</span> {FIRM["legal_name"]}.</p>
      <p class="footer__legal"><a href="{r}chinh-sach-bao-mat/">Chính sách bảo mật</a><a href="{r}dieu-khoan-su-dung/">Điều khoản sử dụng</a><a href="{r}mien-tru-trach-nhiem/">Miễn trừ trách nhiệm</a></p>
    </div>
  </div>
</footer>"""


def overlays_html(r):
    return f"""<div class="floating">
  <a class="floating__btn floating__btn--zalo" href="{FIRM["zalo"]}" target="_blank" rel="noopener" aria-label="Nhắn Zalo {FIRM["phone"]}">Zalo</a>
  <a class="floating__btn floating__btn--phone" href="tel:{FIRM["phone_tel"]}" aria-label="Gọi hotline {FIRM["phone"]}">{ico("i-phone", "")}</a>
  <button class="floating__btn floating__btn--top" type="button" aria-label="Lên đầu trang" id="to-top">{ico("i-up", "")}</button>
</div>

<div class="overlay search" id="search" hidden>
  <div class="search__box" role="dialog" aria-modal="true" aria-label="Tìm kiếm trên website">
    <button class="icon-btn overlay__close" type="button" aria-label="Đóng" data-close>{ico("i-close", "")}</button>
    <form class="search__form" role="search" action="{r}kien-thuc-phap-ly/">
      {ico("i-search")}
      <input type="search" id="search-q" name="q" placeholder="Tìm lĩnh vực, bài viết, câu hỏi…" aria-label="Từ khóa tìm kiếm" autocomplete="off">
    </form>
    <ul class="search__results" id="search-results" aria-live="polite"></ul>
    <p class="search__hint">Gợi ý:
      <a href="{r}dich-vu/thua-ke/">Thừa kế</a>
      <a href="{r}dich-vu/hon-nhan-gia-dinh/">Ly hôn</a>
      <a href="{r}dich-vu/dat-dai-bat-dong-san/">Tranh chấp đất đai</a>
      <a href="{r}bo-luat-hinh-su/">Bộ luật Hình sự</a>
    </p>
  </div>
</div>"""


# ---------------------------------------------------------------------------
# Thành phần trang
# ---------------------------------------------------------------------------
def breadcrumb_html(crumbs, r):
    parts = []
    for i, (name, path) in enumerate(crumbs):
        if i == len(crumbs) - 1:
            parts.append(f'<li aria-current="page">{esc(name)}</li>')
        else:
            parts.append(f'<li><a href="{r}{path}">{esc(name)}</a></li>')
    return f'<nav class="breadcrumb" aria-label="Đường dẫn"><ol>{"".join(parts)}</ol></nav>'


# ---------------------------------------------------------------------------
# Thành phần giao diện dùng chung cho mọi trang (trừ Từ điển Bộ luật Hình sự).
# Kiểu hiển thị: assets/css/pages.css (tiền tố ls-).
# ---------------------------------------------------------------------------
PROMISES = [
    ("i-user", "Luật sư trực tiếp tiếp nhận", "Anh chị trao đổi thẳng với luật sư phụ trách, không qua trung gian."),
    ("i-scale", "Nói rõ được – mất", "Phân tích thẳng thắn điểm mạnh, điểm yếu; không hứa hẹn bảo đảm kết quả."),
    ("i-coin", "Chi phí thỏa thuận trước", "Phạm vi công việc và thù lao ghi rõ trong hợp đồng trước khi làm."),
    ("i-lock", "Giữ kín thông tin", "Bảo mật theo Luật Luật sư, ngay từ buổi trao đổi đầu tiên."),
]


def call_buttons(r, cls=""):
    """Hai nút liên hệ chính: gọi điện và nhắn Zalo."""
    return (f'<div class="ls-actions{(" " + cls) if cls else ""}">'
            f'<a class="btn btn--primary btn--lg" href="tel:{FIRM["phone_tel"]}">{ico("i-phone")} Gọi {FIRM["phone"]}</a>'
            f'<a class="btn btn--outline btn--lg" href="{FIRM["zalo"]}" target="_blank" rel="noopener">{ico("i-chat")} Nhắn Zalo</a></div>')


def help_card(r, title="Anh chị cần hỏi ngay?"):
    """Thẻ "hỏi luật sư" bên phải tiêu đề trang: ảnh luật sư, nút gọi, nút Zalo."""
    return f"""<aside class="ls-help" aria-label="Liên hệ luật sư">
      <div class="ls-help__who"><img src="{r}{asset_ref("assets/img/luat-su-nam-avatar.webp")}" alt="" width="64" height="64"><p><strong>{FIRM["lawyer"]}</strong><span>Trực tiếp nghe anh chị trình bày</span></p></div>
      <p class="ls-help__title">{title}</p>
      {call_buttons(r, "ls-actions--stack")}
      <ul class="ls-help__meta"><li>{ico("i-clock")}{FIRM["hours"]}</li><li>{ico("i-lock")}Thông tin được giữ kín theo Luật Luật sư</li></ul>
    </aside>"""


def page_hero_html(page, r):
    """Đầu trang thống nhất: đường dẫn, nhãn, tiêu đề, đoạn mở đầu và thẻ liên hệ."""
    h = page.get("hero") or {}
    kind = h.get("aside", "help")
    aside = help_card(r) if kind == "help" else ""
    lead = f'<p class="ls-hero__lead">{page["lead"]}</p>' if page.get("lead") else ""
    eyebrow = f'<p class="eyebrow">{esc(page["eyebrow"])}</p>' if page.get("eyebrow") else ""
    actions = call_buttons(r) if h.get("actions") else ""
    cls = "ls-hero" if aside else "ls-hero ls-hero--plain"
    return f"""<section class="{cls}">
  <div class="container ls-hero__grid">
    <div class="ls-hero__copy">
      {breadcrumb_html(page["crumbs"], r)}
      {eyebrow}
      <h1 class="ls-hero__title">{page["h1"]}</h1>
      {lead}
      {h.get("extra", "")}
      {actions}
    </div>
    {aside}
  </div>
</section>"""


def promise_html(cls=""):
    items = "".join(f'<li>{ico(i)}<div><strong>{esc(t)}</strong><span>{esc(d)}</span></div></li>' for i, t, d in PROMISES)
    return f'<section class="ls-promise{(" " + cls) if cls else ""}" aria-label="Cam kết khi làm việc"><div class="container"><ul class="ls-promise__list">{items}</ul></div></section>'


def contact_band(r, title="Cần hỏi luật sư? Liên hệ ngay",
                 text="Vụ việc càng sớm được xem xét, anh chị càng có nhiều lựa chọn. Với việc gấp như người thân bị tạm giữ hoặc sắp hết thời hạn kháng cáo, hãy gọi điện trực tiếp.",
                 hid="lien-he-ngay"):
    """Khối liên hệ cuối trang, giống nhau trên mọi trang: gọi điện, Zalo, đến văn phòng."""
    return f"""<section class="ls-contact" aria-labelledby="{hid}"><div class="container">
<div class="ls-head ls-head--light"><h2 class="h2" id="{hid}">{title}</h2><p>{text}</p></div>
<div class="ls-contact__grid">
<a class="ls-contact__card" href="tel:{FIRM["phone_tel"]}">{ico("i-phone")}<span>Gọi điện</span><strong>{FIRM["phone"]}</strong><small>{FIRM["hours"]}</small></a>
<a class="ls-contact__card" href="{FIRM["zalo"]}" target="_blank" rel="noopener">{ico("i-chat")}<span>Nhắn Zalo</span><strong>{FIRM["phone"]}</strong><small>Kể ngắn gọn sự việc của anh chị</small></a>
<a class="ls-contact__card" href="https://www.google.com/maps/dir/?api=1&amp;destination={FIRM["maps_query"]}" target="_blank" rel="noopener">{ico("i-pin")}<span>Đến văn phòng</span><strong>{FIRM["street"]}</strong><small>{FIRM["ward"]}, TP.HCM · Gọi trước để luật sư sắp xếp thời gian</small></a>
</div>
</div></section>"""


def problem_card(s, r):
    return (f'<a class="ls-problem" href="{r}dich-vu/{s["slug"]}/">'
            f'<span class="ls-problem__ico">{ico(s.get("problem_icon", s["icon"]))}</span>'
            f'<span class="ls-problem__tag">{esc(s["name"])}</span>'
            f'<h3>{esc(s["problem_title"])}</h3><p>{esc(s["problem_text"])}</p>'
            f'<span class="ls-problem__more">Xem cách giải quyết {ARROW}</span></a>')


def problems_grid(r):
    return '<div class="ls-problems">' + "".join(problem_card(SERVICE_BY_SLUG[x], r) for x in PROBLEM_ORDER) + "</div>"


def field_links(r, anchor=""):
    """Danh sách 8 lĩnh vực dạng thẻ nhỏ; anchor dẫn tới một mục trong trang lĩnh vực."""
    note = "Xem giấy tờ cần chuẩn bị" if anchor == "ho-so" else "Xem lĩnh vực"
    frag = f"#{anchor}" if anchor else ""
    items = "".join(f'<li><a href="{r}dich-vu/{x}/{frag}">{ico(SERVICE_BY_SLUG[x]["icon"])}<span><strong>{esc(SERVICE_BY_SLUG[x]["name"])}</strong><small>{note}</small></span>{ARROW}</a></li>'
                    for x in PROBLEM_ORDER)
    return f'<ul class="ls-fields">{items}</ul>'


def steps_html(steps):
    return '<ol class="ls-steps">' + "".join(f'<li><b>{i}</b><h3>{esc(h)}</h3><p>{esc(p)}</p></li>' for i, (h, p) in enumerate(steps, 1)) + "</ol>"


def vi_date(iso):
    y, m, d = iso.split("-")
    return f"{int(d):02d} Tháng {int(m)}, {y}"


def article_card(a, r, heading="h3"):
    return f"""<article class="post">
  <a class="post__img" href="{r}kien-thuc-phap-ly/{a["slug"]}/" tabindex="-1" aria-hidden="true"><img src="{r}assets/img/bai-viet/{a["slug"]}.webp?v={ASSET_VERSION}" alt="" loading="lazy" width="720" height="240"></a>
  <div class="post__body">
    <p class="post__meta"><a class="tag" href="{r}dich-vu/{a["service"]}/">{esc(a["category"])}</a><time datetime="{a["published"]}">{ico("i-clock")}{vi_date(a["published"])}</time></p>
    <{heading} class="post__title"><a href="{r}kien-thuc-phap-ly/{a["slug"]}/">{esc(a["card_title"])}</a></{heading}>
    <p>{esc(a["excerpt"])}</p>
    <a class="post__more" href="{r}kien-thuc-phap-ly/{a["slug"]}/" aria-hidden="true" tabindex="-1">Đọc bài {ARROW}</a>
  </div>
</article>"""


def articles_grid(r, items=None, cls="ls-posts"):
    items = items if items is not None else ARTICLES
    return f'<div class="{cls}">' + "".join(article_card(a, r) for a in items) + "</div>"


def faq_list(r, items=None):
    out = []
    for f in (items or FAQ):
        body = "".join(f"<p>{p}</p>" for p in f["a"]).replace("{{root}}", r)
        out.append(f"""<details class="faq__item" id="{f["id"]}">
  <summary><span>{esc(f["q"])}</span>{ico("i-chevron", "faq__chev")}</summary>
  <div class="faq__answer">{body}</div>
</details>""")
    return '<div class="faq">' + "".join(out) + "</div>"


def check_list(items, cls="ls-check"):
    return f'<ul class="{cls}">' + "".join(f"<li>{ico('i-check')}<span>{esc(i)}</span></li>" for i in items) + "</ul>"


TOKEN_RE = re.compile(r"\{\{(\w+)(?::([^}]*))?\}\}")


def render_tokens(body, page, r):
    def rep(m):
        name, arg = m.group(1), m.group(2)
        if name == "root":
            return r
        if name in ("phone", "phone_tel", "email", "zalo", "address", "hours", "hours_note", "maps_query",
                    "legal_name", "street", "ward", "city", "lawyer"):
            return FIRM[name]
        if name in ("cta", "contact"):
            return contact_band(r)
        if name == "breadcrumb":
            return breadcrumb_html(page["crumbs"], r)
        if name == "promise":
            return promise_html()
        if name == "call_buttons":
            return call_buttons(r)
        if name == "help_card":
            return help_card(r)
        if name in ("problems_grid", "services_grid"):
            return problems_grid(r)
        if name == "field_links":
            return field_links(r, arg or "")
        if name == "articles_grid":
            return articles_grid(r)
        if name == "faq_list":
            ids = arg.split(",") if arg else None
            return faq_list(r, [f for f in FAQ if f["id"] in ids] if ids else None)
        if name == "arrow":
            return ARROW
        if name == "ico":
            nm, _, cls = arg.partition("|")
            return ico(nm, cls or "ico")
        raise KeyError(f"Token không xác định: {name} ({page['path']})")
    return TOKEN_RE.sub(rep, body)

# ---------------------------------------------------------------------------
# Dữ liệu có cấu trúc (JSON-LD)
# ---------------------------------------------------------------------------
def org_node():
    return {
        "@type": "LegalService",
        "@id": ORG_ID,
        "name": FIRM["legal_name"],
        "alternateName": [FIRM["short_name"], FIRM["brand"]],
        "slogan": FIRM["slogan"],
        "url": SITE_URL + "/",
        "logo": {"@type": "ImageObject", "url": abs_url("assets/img/icon-512.png"), "width": 512, "height": 512},
        "image": abs_url(asset_ref("assets/img/og-image.jpg")),
        "description": "Công ty luật tại Thành phố Hồ Chí Minh, tư vấn và tham gia tố tụng trong các lĩnh vực thừa kế, "
                       "đất đai, hôn nhân gia đình, lao động, hình sự, dân sự, công chứng và tranh chấp thương mại.",
        "telephone": FIRM["phone_intl"],
        "email": FIRM["email"],
        "priceRange": "Theo thỏa thuận",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": FIRM["street"],
            "addressLocality": FIRM["ward"],
            "addressRegion": FIRM["city"],
            "addressCountry": "VN",
        },
        "openingHoursSpecification": [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "opens": "08:00", "closes": "17:30",
        }],
        "areaServed": [{"@type": "City", "name": "Thành phố Hồ Chí Minh"}, {"@type": "Country", "name": "Việt Nam"}],
        "knowsLanguage": ["vi"],
        "sameAs": [FIRM["zalo"]],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Lĩnh vực hoạt động",
            "itemListElement": [{"@type": "Offer", "itemOffered": {"@id": abs_url(f"dich-vu/{s['slug']}/") + "#service"}}
                                for s in SERVICES],
        },
    }


def jsonld(page):
    url = abs_url(page["path"])
    org = org_node()
    if page["path"] not in ("", "lien-he/", "gioi-thieu/"):
        org = {k: org[k] for k in ("@type", "@id", "name", "alternateName", "url", "logo", "image", "telephone", "email", "address")}
    graph = [org, {
        "@type": "WebSite", "@id": SITE_ID, "url": SITE_URL + "/", "name": f'{FIRM["short_name"]} – {FIRM["brand"]}',
        "inLanguage": "vi", "publisher": {"@id": ORG_ID},
    }]
    webpage = {
        "@type": page.get("schema_type", "WebPage"), "@id": url + "#webpage", "url": url,
        "name": page["title"], "description": page["description"], "inLanguage": "vi",
        "isPartOf": {"@id": SITE_ID}, "about": {"@id": ORG_ID},
        "primaryImageOfPage": {"@type": "ImageObject", "url": abs_url(asset_ref(page.get("image", "assets/img/og-image.jpg")))},
        "dateModified": page.get("modified", TODAY),
    }
    if page["path"]:
        webpage["breadcrumb"] = {"@id": url + "#breadcrumb"}
        graph.append({
            "@type": "BreadcrumbList", "@id": url + "#breadcrumb",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": abs_url(p)}
                                for i, (n, p) in enumerate(page["crumbs"])],
        })
    webpage.update(page.get("webpage_extra", {}))
    graph.append(webpage)
    graph.extend(page.get("schema", []))
    data = {"@context": "https://schema.org", "@graph": graph}
    return json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")


# ---------------------------------------------------------------------------
# Khung trang
# ---------------------------------------------------------------------------
def layout(page):
    r = page.get("root_override", "../" * page["path"].count("/"))
    css_v, js_v = file_hash("assets/css/style.css"), file_hash("assets/js/main.js")
    url = abs_url(page["path"])
    # Ảnh chia sẻ luôn dùng JPG 1200×630 để tương thích Facebook, Zalo, LinkedIn
    image = abs_url(asset_ref("assets/img/og-image.jpg"))
    robots = "noindex, follow" if page.get("noindex") else "index, follow, max-image-preview:large, max-snippet:-1"
    og_type = page.get("og_type", "website")
    art_meta = ""
    if og_type == "article":
        art_meta = (f'\n<meta property="article:published_time" content="{page["published"]}">'
                    f'\n<meta property="article:modified_time" content="{page["modified"]}">'
                    f'\n<meta property="article:section" content="{esc(page["article_section"])}">')
    # Ảnh nạp trước phải trùng hệt địa chỉ (kể cả ?v=) với chỗ dùng ảnh, nếu không trình duyệt tải hai lần
    preload = "".join(f'\n<link rel="preload" as="image" href="{r}{p if "?" in p else asset_ref(p)}" fetchpriority="high">'
                      for p in page.get("preload_images", []))
    extra_head = page.get("extra_head", "").replace("{{root}}", r)
    hero = render_tokens(page_hero_html(page, r), page, r) if page.get("page_hero", True) else ""
    body = render_tokens(page["body"], page, r)
    body = re.sub(r"\s*<!--\s*(GHI CHÚ CHO NGƯỜI QUẢN TRỊ|Nội dung trang tra cứu).*?-->", "", body, flags=re.S)
    scripts = "".join(f'\n<script src="{r}{s}" defer></script>' for s in page.get("scripts", []))
    canonical = "" if page.get("noindex") else f'\n<link rel="canonical" href="{url}">'
    # Từ điển Bộ luật Hình sự giữ nguyên bộ giao diện riêng (reader-design.css, tu-dien.css).
    # Mọi trang còn lại dùng chung một hệ giao diện: pages.css.
    reader = page.get("body_class") == "tdl-page"
    sheets = ("nam-theme", "mobile", "navigation", "reader-design") if reader else ("nam-theme", "mobile", "navigation", "pages")
    styles = f'<link rel="stylesheet" href="{r}assets/css/style.css?v={css_v}">{extra_head}\n' + "\n".join(
        f'<link rel="stylesheet" href="{r}assets/css/{n}.css?v={file_hash(f"assets/css/{n}.css")}">' for n in sheets)
    if reader:
        styles += "\n\n"
        body_cls = f' class="{page["body_class"]}"'
        sprite = SPRITE
    else:
        body_cls = f' class="{" ".join(c for c in ("site-page", page.get("body_class")) if c)}"'
        sprite = SPRITE.replace("</svg>", EXTRA_SYMBOLS + "</svg>")
    return f"""<!doctype html>
<html lang="vi" data-root="{r}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(page["title"])}</title>
<meta name="description" content="{esc(page["description"])}">
<meta name="robots" content="{robots}">{canonical}
<meta name="author" content="{FIRM["legal_name"]}">
<meta name="theme-color" content="#fffefa">
<meta name="format-detection" content="telephone=no">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{FIRM["legal_name"]}">
<meta property="og:locale" content="vi_VN">
<meta property="og:title" content="{esc(page.get("og_title", page["title"]))}">
<meta property="og:description" content="{esc(page["description"])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{FIRM["legal_name"]} – LSN Law Firm">{art_meta}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(page.get("og_title", page["title"]))}">
<meta name="twitter:description" content="{esc(page["description"])}">
<meta name="twitter:image" content="{image}">
<link rel="icon" href="{r}assets/img/favicon-32.png" sizes="32x32" type="image/png">
<link rel="icon" href="{r}assets/img/icon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="{r}assets/img/apple-touch-icon.png">
<link rel="manifest" href="{r}site.webmanifest">
<link rel="preload" href="{r}assets/fonts/be-vietnam-pro-400-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{r}assets/fonts/be-vietnam-pro-400-normal-vietnamese.woff2" as="font" type="font/woff2" crossorigin>{preload}
{styles}
<script type="application/ld+json">
{jsonld(page)}
</script>
</head>
<body{body_cls}>
<a class="skip-link" href="#main">Bỏ qua đến nội dung chính</a>
{sprite}
{header_html(page, r)}

<main id="main">
{hero}
{body}
</main>

{footer_html(r)}

{overlays_html(r)}

<script src="{r}assets/js/main.js?v={js_v}" defer></script>{scripts}
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Đọc trang nguồn
# ---------------------------------------------------------------------------
META_RE = re.compile(r"^\s*<!--meta\s*(\{.*?\})\s*-->\s*", re.S)


def load_src(rel):
    with open(os.path.join(SRC, rel), encoding="utf-8") as fh:
        text = fh.read()
    m = META_RE.match(text)
    meta = json.loads(m.group(1)) if m else {}
    return meta, text[m.end():] if m else text


HOME = ("Trang chủ", "")


def crumbs_for(*items):
    return [HOME] + list(items)


# ---------------------------------------------------------------------------
# Trang dịch vụ
# ---------------------------------------------------------------------------
def service_page(s):
    path = f"dich-vu/{s['slug']}/"
    name_lc = s["name"].lower()
    arts = articles_for_service(s["slug"])
    image = s.get("image", f'assets/img/dich-vu/{s["slug"]}.webp')
    iw, ih = s.get("image_size", (1200, 600))
    situations = "".join(f'<li>{ico("i-check-circle")}<span>{esc(x)}</span></li>' for x in s["situations"])
    scope = "".join(f'<article class="ls-card"><span class="ls-card__num">{i:02d}</span><h3>{esc(h)}</h3><p>{esc(p)}</p></article>'
                    for i, (h, p) in enumerate(s["scope"], 1))
    tips = "".join(f"<li>{esc(t)}</li>" for t in s["tips"])
    faq = "".join(f"""<details class="faq__item" id="hoi-dap-{i}">
  <summary><span>{esc(q)}</span>{ico("i-chevron", "faq__chev")}</summary>
  <div class="faq__answer"><p>{a}</p></div>
</details>""" for i, (q, a) in enumerate(s["faq"], 1))
    laws = "".join(f"<li>{esc(x)}</li>" for x in s["laws"])
    resources = [(f'kien-thuc-phap-ly/{a["slug"]}/', "Bài viết", a["card_title"], a["excerpt"]) for a in arts[:3]]
    extras = [("cau-hoi-thuong-gap/", "Hỏi đáp", "Câu hỏi thường gặp khi thuê luật sư", "Chi phí, bảo mật và cách bắt đầu làm việc với luật sư."),
              ("quy-trinh-lam-viec/#ho-so-can-chuan-bi", "Chuẩn bị", "Trước buổi gặp luật sư đầu tiên", "Giấy tờ nên mang theo và cách ghi lại diễn biến sự việc.")]
    if s["slug"] == "hinh-su":
        extras.insert(0, ("bo-luat-hinh-su/", "Tra cứu", "Bộ luật Hình sự và bình luận", "Tra cứu nội dung theo điều, khoản, điểm và từ khóa."))
    resources += extras[:max(0, 3 - len(resources))]
    cards = "".join(f'<a class="ls-resource" href="{{{{root}}}}{href}"><span class="ls-resource__label">{label}</span><h3>{esc(title)}</h3><p>{esc(text)}</p><span class="ls-resource__more">Xem chi tiết {ARROW}</span></a>'
                    for href, label, title, text in resources)
    related = "".join(f'<li><a href="{{{{root}}}}dich-vu/{x}/">{ico(SERVICE_BY_SLUG[x]["icon"])}{esc(SERVICE_BY_SLUG[x]["name"])}</a></li>' for x in s["related"])
    urgent = ""
    if s.get("urgent"):
        urgent = (f'<p class="ls-urgent">{ico("i-alert")}<span><strong>Việc gấp?</strong> Người thân vừa bị bắt, tạm giữ hoặc sắp phải làm việc với cơ quan điều tra: '
                  f'hãy gọi ngay <a href="tel:{FIRM["phone_tel"]}">{FIRM["phone"]}</a>. {FIRM["hours_note"]}.</span></p>')
    body = f"""
<section class="ls-hero ls-hero--service">
  <div class="container ls-hero__grid">
    <div class="ls-hero__copy">
      {{{{breadcrumb}}}}
      <p class="eyebrow">Luật sư {esc(name_lc if s["slug"] != "cong-chung" else "hỗ trợ công chứng")}</p>
      <h1 class="ls-hero__title">{s["hero_title"]}</h1>
      <p class="ls-hero__lead">{esc(s["lead"])}</p>
      {call_buttons("{{root}}")}
      {urgent}
    </div>
    <figure class="ls-hero__media{" ls-hero__media--portrait" if s.get("image") else ""}"><img src="{{{{root}}}}{asset_ref(image)}" alt="{esc(s["image_alt"])}" width="{iw}" height="{ih}" fetchpriority="high"></figure>
  </div>
</section>
{promise_html("ls-promise--line")}

<section class="ls-section" id="tinh-huong" aria-labelledby="tinh-huong-title"><div class="container">
  <div class="ls-head"><h2 class="h2" id="tinh-huong-title">Anh chị có đang gặp chuyện này?</h2><p>Đây là những trường hợp về {esc(name_lc)} mà người dân thường tìm đến luật sư.</p></div>
  <ul class="ls-situations">{situations}</ul>
  <p class="ls-situations__foot">Trường hợp của anh chị khác? Cứ <a href="tel:{FIRM["phone_tel"]}">gọi {FIRM["phone"]}</a> hoặc <a href="{FIRM["zalo"]}" target="_blank" rel="noopener">nhắn Zalo</a> kể ngắn gọn – luật sư sẽ cho biết có giúp được hay không.</p>
</div></section>

<section class="ls-section ls-section--cream" id="pham-vi" aria-labelledby="pham-vi-title"><div class="container">
  <div class="ls-head"><h2 class="h2" id="pham-vi-title">Luật sư giúp được anh chị những gì</h2><p>{esc(s["scope_intro"])}</p></div>
  <div class="ls-grid ls-grid--3">{scope}</div>
</div></section>

<section class="ls-section" id="viec-nen-lam" aria-labelledby="viec-nen-lam-title"><div class="container ls-split">
  <div>
    <div class="ls-head"><h2 class="h2" id="viec-nen-lam-title">Việc nên làm ngay</h2><p>Trong lúc chờ gặp luật sư, những việc nhỏ dưới đây giúp anh chị giữ được quyền lợi.</p></div>
    <ol class="ls-tips">{tips}</ol>
  </div>
  <div class="ls-stack">
    <div class="ls-note">{ico("i-alert")}<p><strong>{esc(s["note_title"])}:</strong> {esc(s["note_text"])}</p></div>
    <article class="ls-card ls-card--accent"><p class="eyebrow">Cách luật sư làm việc</p><h3>{esc(s["principle_title"])}</h3><p>{esc(s["principle_text"])}</p></article>
  </div>
</div></section>

<section class="ls-section ls-section--cream" id="quy-trinh" aria-labelledby="quy-trinh-title"><div class="container">
  <div class="ls-head ls-head--row"><div><h2 class="h2" id="quy-trinh-title">Làm việc với luật sư diễn ra thế nào?</h2><p>Năm bước rõ ràng. Ở mỗi bước, anh chị đều biết việc gì đang được làm.</p></div><a class="link-arrow" href="{{{{root}}}}quy-trinh-lam-viec/">Quy trình làm việc chung {ARROW}</a></div>
  {steps_html(s["steps"])}
</div></section>

<section class="ls-section" id="ho-so" aria-labelledby="ho-so-title"><div class="container">
  <div class="ls-head"><h2 class="h2" id="ho-so-title">Cần chuẩn bị gì và anh chị nhận được gì</h2><p>Chưa đủ giấy tờ cũng không sao: cứ mang những gì đang có, luật sư sẽ hướng dẫn bổ sung.</p></div>
  <div class="ls-grid ls-grid--2">
    <article class="ls-card ls-card--list"><h3>{ico("i-doc", "ls-card__ico")}{esc(s.get("docs_title", "Giấy tờ nên mang theo"))}</h3>{check_list(s["docs"])}<a class="link-arrow" href="{{{{root}}}}quy-trinh-lam-viec/#ho-so-can-chuan-bi">Hướng dẫn chuẩn bị hồ sơ {ARROW}</a></article>
    <article class="ls-card ls-card--list"><h3>{ico("i-check-circle", "ls-card__ico")}Anh chị sẽ nhận được</h3>{check_list(s["deliverables"])}<a class="link-arrow" href="{{{{root}}}}cau-hoi-thuong-gap/#chi-phi-thue-luat-su">Chi phí được tính thế nào {ARROW}</a></article>
  </div>
</div></section>

<section class="ls-section ls-section--cream" id="hoi-dap" aria-labelledby="hoi-dap-title"><div class="container ls-split ls-split--faq">
  <div class="ls-head"><h2 class="h2" id="hoi-dap-title">Câu hỏi hay gặp về {esc(name_lc)}</h2><p>Giải đáp ngắn gọn, có dẫn điều luật. Mỗi vụ việc có tình tiết riêng, anh chị nên hỏi luật sư trước khi quyết định.</p><a class="link-arrow" href="{{{{root}}}}cau-hoi-thuong-gap/">Câu hỏi chung khi thuê luật sư {ARROW}</a></div>
  <div class="faq">{faq}</div>
</div></section>

<section class="ls-section" id="tham-khao" aria-labelledby="tham-khao-title"><div class="container">
  <div class="ls-head ls-head--row"><div><h2 class="h2" id="tham-khao-title">Đọc thêm trước khi gặp luật sư</h2></div><a class="link-arrow" href="{{{{root}}}}kien-thuc-phap-ly/">Thư viện pháp lý {ARROW}</a></div>
  <div class="ls-grid ls-grid--3">{cards}</div>
  <div class="ls-split ls-split--even ls-more">
    <div><h3 class="ls-more__title">Căn cứ pháp luật chủ yếu</h3><ul class="ls-laws">{laws}</ul><p class="ls-small">Danh mục tham khảo; văn bản áp dụng cụ thể được luật sư xác định theo từng vụ việc.</p></div>
    <div><h3 class="ls-more__title">Lĩnh vực liên quan</h3><ul class="ls-chips">{related}</ul></div>
  </div>
</div></section>

{contact_band("{{root}}", esc(s["cta_title"]), esc(s["cta_text"]))}
"""
    url = abs_url(path)
    return {
        "path": path, "section": "services", "body_class": "service-page", "page_hero": False,
        "title": seo_title(s.get("seo_title", s["title"])), "description": s["description"],
        "crumbs": crumbs_for(("Dịch vụ", "dich-vu/"), (s["name"], path)),
        "h1": strip_tags(s["hero_title"]),
        "image": image, "image_alt": s["image_alt"],
        "preload_images": [image], "body": body,
        "schema": [{
            "@type": "Service", "@id": url + "#service", "name": s["name"], "serviceType": s["title"],
            "description": s["description"], "url": url, "provider": {"@id": ORG_ID},
            "areaServed": [{"@type": "City", "name": "Thành phố Hồ Chí Minh"}, {"@type": "Country", "name": "Việt Nam"}],
            "image": abs_url(asset_ref(f'assets/img/dich-vu/{s["slug"]}.webp')),
        }],
        "webpage_extra": {"mainEntity": {"@id": url + "#service"}},
    }


def services_hub():
    path = "dich-vu/"
    modes = [
        ("i-chat", "Tư vấn, giải đáp", "Luật sư nghe anh chị trình bày, giải thích quy định và hướng xử lý; soạn hoặc kiểm tra hợp đồng, đơn từ, giấy tờ trước khi anh chị ký, nộp."),
        ("i-user", "Thay mặt anh chị làm việc", "Trong phạm vi được ủy quyền, luật sư thay anh chị làm việc, thương lượng, hòa giải với bên kia và làm thủ tục tại cơ quan nhà nước."),
        ("i-gavel", "Cùng anh chị ra Tòa", "Luật sư bào chữa, bảo vệ quyền lợi hoặc đại diện cho anh chị trong vụ án hình sự, dân sự, hôn nhân gia đình, lao động, kinh doanh thương mại và tại Trọng tài."),
    ]
    mode_html = "".join(f'<article class="ls-card ls-card--icon">{ico(i, "ls-card__ico")}<h3>{h}</h3><p>{p}</p></article>' for i, h, p in modes)
    body = f"""
{{{{promise}}}}

<section class="ls-section ls-section--cream" aria-labelledby="tinh-huong-title"><div class="container">
  <div class="ls-head"><h2 class="h2" id="tinh-huong-title">Chọn tình huống gần giống với anh chị</h2><p>Mỗi lĩnh vực có trang riêng: những trường hợp thường gặp, luật sư giúp được gì, giấy tờ cần chuẩn bị và các bước làm việc.</p></div>
  {{{{problems_grid}}}}
</div></section>

<section class="ls-section" aria-labelledby="hinh-thuc-title"><div class="container">
  <div class="ls-head"><h2 class="h2" id="hinh-thuc-title">Luật sư có thể giúp anh chị theo ba cách</h2><p>Tùy vụ việc, anh chị chọn một hoặc kết hợp nhiều cách, theo phạm vi hành nghề quy định tại Luật Luật sư.</p></div>
  <div class="ls-grid ls-grid--3">{mode_html}</div>
</div></section>

{contact_band("{{root}}", "Chưa biết vụ việc thuộc lĩnh vực nào?", "Không sao cả. Anh chị cứ gọi điện hoặc nhắn Zalo kể ngắn gọn sự việc – luật sư sẽ xác định vấn đề pháp lý chính và hướng xử lý phù hợp.")}
"""
    return {
        "path": path, "section": "services", "schema_type": "CollectionPage",
        "title": seo_title("Lĩnh vực hoạt động – Dịch vụ pháp lý"),
        "description": "Luật Sư Nam tư vấn, đại diện và tham gia tố tụng trong 8 lĩnh vực: thừa kế, tranh tụng, hôn nhân gia đình, đất đai, lao động, hình sự, dân sự, công chứng.",
        "eyebrow": "Lĩnh vực hoạt động",
        "h1": "Anh chị cần luật sư <em>giúp việc gì?</em>",
        "lead": "Từ chia di sản, ly hôn, mua bán nhà đất đến người thân gặp chuyện hình sự – Luật Sư Nam tư vấn, đại diện và tham gia tố tụng trong tám lĩnh vực gắn với đời sống hằng ngày của người dân.",
        "crumbs": crumbs_for(("Lĩnh vực hoạt động", path)),
        "body": body,
        "webpage_extra": {"mainEntity": {
            "@type": "ItemList", "numberOfItems": len(SERVICES),
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": abs_url(f"dich-vu/{s['slug']}/"), "name": s["name"]}
                                for i, s in enumerate(SERVICES)]}},
    }


# ---------------------------------------------------------------------------
# Bài viết
# ---------------------------------------------------------------------------
H2_RE = re.compile(r'<h2 id="([^"]+)">(.*?)</h2>', re.S)


def article_page(a):
    path = f"kien-thuc-phap-ly/{a['slug']}/"
    meta, content = load_src(f"bai-viet/{a['slug']}.html")
    toc = "".join(f'<li><a href="#{i}">{strip_tags(t)}</a></li>' for i, t in H2_RE.findall(content))
    words = len(strip_tags(content).split())
    minutes = max(1, round(words / 220))
    svc = SERVICE_BY_SLUG[a["service"]]
    others = [x for x in ARTICLES if x["slug"] != a["slug"]]
    related_svcs = "".join(
        f'<li><a href="{{{{root}}}}dich-vu/{x}/">{ico(SERVICE_BY_SLUG[x]["icon"], "rel-list__icon")}<span>{esc(SERVICE_BY_SLUG[x]["name"])}</span>{ARROW}</a></li>'
        for x in a["related_services"])
    points = "".join(f"<li>{esc(p)}</li>" for p in a.get("key_points", []))
    keypoints = f'<div class="ls-keypoints"><p class="ls-keypoints__title">{ico("i-list")}Tóm tắt nhanh</p><ul>{points}</ul></div>' if points else ""
    extra = f"""<p class="article-meta">
        <span>{ico("i-user")}Ban biên tập {FIRM["short_name"]}</span>
        <span>{ico("i-calendar")}Đăng <time datetime="{a["published"]}">{vi_date(a["published"])}</time></span>
        <span>{ico("i-clock")}Cập nhật <time datetime="{a["modified"]}">{vi_date(a["modified"])}</time> · {minutes} phút đọc</span>
      </p>"""
    body = f"""
<section class="ls-section ls-section--article">
  <div class="container article-layout">
    <article class="prose" id="noi-dung-bai-viet">
      <img class="prose__cover" src="{{{{root}}}}assets/img/bai-viet/{a["slug"]}.webp?v={ASSET_VERSION}" alt="{esc(a["image_alt"])}" width="720" height="240" fetchpriority="high">
      {keypoints}
      {content}
      <div class="article-disclaimer">
        {ico("i-alert", "note__icon")}
        <p>Bài viết mang tính thông tin pháp lý chung tại thời điểm cập nhật, không thay thế ý kiến tư vấn cho vụ việc cụ thể. Văn bản pháp luật có thể được sửa đổi, bổ sung sau ngày đăng; vui lòng kiểm tra hiệu lực hoặc <a href="{{{{root}}}}lien-he/">hỏi luật sư</a> trước khi quyết định.</p>
      </div>
    </article>
    <aside class="article-aside">
      <div class="aside-card aside-card--toc">
        <p class="aside-card__title">Nội dung bài viết</p>
        <ol class="toc">{toc}</ol>
      </div>
      <div class="aside-card ls-ask">
        <div class="ls-help__who"><img src="{{{{root}}}}{asset_ref("assets/img/luat-su-nam-avatar.webp")}" alt="" width="56" height="56" loading="lazy"><p><strong>Cần hỏi về {esc(svc["name"].lower())}?</strong><span>{FIRM["lawyer"]} trực tiếp nghe anh chị trình bày</span></p></div>
        {call_buttons("{{root}}", "ls-actions--stack ls-actions--sm")}
        <a class="link-arrow" href="{{{{root}}}}dich-vu/{svc["slug"]}/">Xem dịch vụ {esc(svc["name"])} {ARROW}</a>
      </div>
      <div class="aside-card">
        <p class="aside-card__title">Lĩnh vực liên quan</p>
        <ul class="rel-list">{related_svcs}</ul>
      </div>
    </aside>
  </div>
</section>

<section class="ls-section ls-section--cream" aria-labelledby="doc-tiep-title"><div class="container">
  <div class="ls-head ls-head--row"><div><h2 class="h2" id="doc-tiep-title">Bài viết khác</h2></div><a class="link-arrow" href="{{{{root}}}}kien-thuc-phap-ly/">Tất cả bài viết {ARROW}</a></div>
  {articles_grid("{{root}}", others, cls="ls-posts ls-posts--2")}
</div></section>

{contact_band("{{root}}", esc(svc["cta_title"]), esc(svc["cta_text"]))}
"""
    url = abs_url(path)
    return {
        "path": path, "section": "knowledge", "og_type": "article", "body_class": "article-page",
        "published": a["published"], "modified": a["modified"], "article_section": a["category"],
        "title": seo_title(a["seo_title"]),
        "og_title": a["title"],
        "description": a["description"],
        "eyebrow": a["category"],
        "h1": esc(a["title"]),
        "crumbs": crumbs_for(("Kiến thức pháp lý", "kien-thuc-phap-ly/"), (a["card_title"], path)),
        "image": f'assets/img/bai-viet/{a["slug"]}.webp', "image_alt": a["image_alt"],
        "hero": {"aside": "none", "extra": extra},
        "body": body, "modified": a["modified"],
        "schema": [{
            "@type": "Article", "@id": url + "#article", "headline": a["title"], "description": a["description"],
            "image": abs_url(asset_ref(f'assets/img/bai-viet/{a["slug"]}.webp')), "datePublished": a["published"],
            "dateModified": a["modified"], "inLanguage": "vi", "articleSection": a["category"], "wordCount": words,
            "author": {"@id": ORG_ID}, "publisher": {"@id": ORG_ID},
            "mainEntityOfPage": {"@id": url + "#webpage"},
            "about": {"@id": abs_url(f'dich-vu/{a["service"]}/') + "#service"},
        }],
    }


def knowledge_hub():
    path = "kien-thuc-phap-ly/"
    body = f"""
<section class="ls-section ls-section--cream" aria-labelledby="bai-viet-title"><div class="container">
  <div class="ls-head"><h2 class="h2" id="bai-viet-title">Bài viết mới</h2><p>Mỗi bài giải thích một tình huống người dân hay gặp, có trích điều luật cụ thể và ghi rõ ngày cập nhật.</p></div>
  {{{{articles_grid}}}}
</div></section>

<section class="ls-section" aria-labelledby="cong-cu-title"><div class="container">
  <div class="ls-head"><h2 class="h2" id="cong-cu-title">Tự tra cứu</h2><p>Công cụ và giải đáp giúp anh chị hiểu vấn đề trước khi gặp luật sư.</p></div>
  <div class="ls-grid ls-grid--2">
    <a class="ls-tool" href="{{{{root}}}}bo-luat-hinh-su/">{ico("i-book", "ls-tool__ico")}<span class="ls-resource__label">Công cụ tra cứu</span><h3>Bộ luật Hình sự 2015 (sửa đổi 2017, 2025)</h3><p>Toàn văn 428 điều kèm bình luận từng điều; tìm theo số điều hoặc từ khóa, gõ có dấu hay không dấu đều được.</p><span class="ls-resource__more">Mở công cụ tra cứu {ARROW}</span></a>
    <a class="ls-tool" href="{{{{root}}}}cau-hoi-thuong-gap/">{ico("i-question", "ls-tool__ico")}<span class="ls-resource__label">Hỏi đáp</span><h3>Câu hỏi thường gặp khi làm việc với luật sư</h3><p>Chi phí thuê luật sư, giữ bí mật thông tin, thời hạn cần lưu ý, thời gian phản hồi và vụ việc ở tỉnh khác.</p><span class="ls-resource__more">Xem câu hỏi thường gặp {ARROW}</span></a>
  </div>
</div></section>

<section class="ls-section ls-section--cream" aria-labelledby="linh-vuc-title"><div class="container">
  <div class="ls-head ls-head--row"><div><h2 class="h2" id="linh-vuc-title">Tìm theo vấn đề của anh chị</h2><p>Mỗi lĩnh vực có giải đáp ngắn, việc nên làm ngay và giấy tờ cần chuẩn bị.</p></div><a class="link-arrow" href="{{{{root}}}}dich-vu/">Tất cả lĩnh vực {ARROW}</a></div>
  {{{{field_links}}}}
</div></section>

{{{{contact}}}}
"""
    return {
        "path": path, "section": "knowledge", "schema_type": "CollectionPage",
        "title": seo_title("Kiến thức pháp lý – Bài viết, tra cứu luật"),
        "description": "Bài viết phân tích pháp luật về thừa kế, hôn nhân gia đình, đất đai; tra cứu Bộ luật Hình sự kèm bình luận và giải đáp thắc mắc khi làm việc với luật sư.",
        "eyebrow": "Kiến thức pháp lý",
        "h1": "Hiểu đúng quyền lợi của mình <em>trước khi quyết định</em>",
        "lead": "Bài viết, công cụ tra cứu và giải đáp do Luật Sư Nam biên soạn bằng lời lẽ dễ hiểu, có dẫn điều luật cụ thể. Đọc để nắm vấn đề – còn vụ việc của anh chị, hãy hỏi trực tiếp luật sư.",
        "crumbs": crumbs_for(("Kiến thức pháp lý", path)),
        "body": body,
        "webpage_extra": {"mainEntity": {
            "@type": "ItemList", "numberOfItems": len(ARTICLES),
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": abs_url(f"kien-thuc-phap-ly/{a['slug']}/"), "name": a["title"]}
                                for i, a in enumerate(ARTICLES)]}},
    }


def faq_page():
    path = "cau-hoi-thuong-gap/"
    body = f"""
<section class="ls-section ls-section--cream"><div class="container faq-layout">
  <div>{{{{faq_list}}}}
    <p class="faq__foot">Các giải đáp trên mang tính thông tin chung, không thay thế ý kiến tư vấn cho vụ việc cụ thể. Xem thêm <a href="{{{{root}}}}mien-tru-trach-nhiem/">Tuyên bố miễn trừ trách nhiệm</a>.</p>
  </div>
  <aside class="faq-aside">
    <div class="aside-card ls-ask">
      <div class="ls-help__who"><img src="{{{{root}}}}{asset_ref("assets/img/luat-su-nam-avatar.webp")}" alt="" width="56" height="56" loading="lazy"><p><strong>Chưa thấy câu trả lời?</strong><span>Gọi điện hoặc nhắn Zalo để hỏi trực tiếp luật sư</span></p></div>
      {call_buttons("{{root}}", "ls-actions--stack ls-actions--sm")}
    </div>
    <div class="aside-card">
      <p class="aside-card__title">Tìm hiểu thêm</p>
      <ul class="rel-list">
        <li><a href="{{{{root}}}}quy-trinh-lam-viec/">{ico("i-steps", "rel-list__icon")}<span>Quy trình làm việc</span>{ARROW}</a></li>
        <li><a href="{{{{root}}}}vi-sao-chon-chung-toi/">{ico("i-diamond", "rel-list__icon")}<span>Vì sao chọn chúng tôi</span>{ARROW}</a></li>
        <li><a href="{{{{root}}}}dich-vu/">{ico("i-scale", "rel-list__icon")}<span>Lĩnh vực hoạt động</span>{ARROW}</a></li>
        <li><a href="{{{{root}}}}kien-thuc-phap-ly/">{ico("i-book", "rel-list__icon")}<span>Kiến thức pháp lý</span>{ARROW}</a></li>
      </ul>
    </div>
  </aside>
</div></section>

{{{{contact}}}}
"""
    return {
        "path": path, "section": "knowledge", "schema_type": "FAQPage",
        "title": seo_title("Câu hỏi thường gặp khi thuê luật sư"),
        "description": "Giải đáp về chi phí thuê luật sư theo Điều 55 Luật Luật sư, bảo mật thông tin, cam kết kết quả, thời hiệu, thời gian phản hồi và vụ việc ngoài TP.HCM.",
        "eyebrow": "Câu hỏi thường gặp",
        "h1": "Những điều anh chị <em>hay băn khoăn nhất</em>",
        "lead": "Thuê luật sư tốn bao nhiêu, thông tin có được giữ kín không, có cần gấp không – giải đáp ngắn gọn, có dẫn quy định cụ thể.",
        "crumbs": crumbs_for(("Kiến thức pháp lý", "kien-thuc-phap-ly/"), ("Câu hỏi thường gặp", path)),
        "body": body,
        "webpage_extra": {"mainEntity": [{
            "@type": "Question", "name": f["q"],
            "acceptedAnswer": {"@type": "Answer", "text": " ".join(strip_tags(p.replace("{{root}}", "")) for p in f["a"])},
        } for f in FAQ]},
    }

# ---------------------------------------------------------------------------
# Trang đơn lẻ từ src/pages
# ---------------------------------------------------------------------------
def simple_page(name, path, section, crumbs, **extra):
    meta, body = load_src(f"pages/{name}.html")
    page = {"path": path, "section": section, "crumbs": crumbs, "body": body}
    page.update(meta)
    page.update(extra)
    if "title" in page and path:
        page["title"] = seo_title(page["title"])
    return page


# ---------------------------------------------------------------------------
# Từ điển Bộ luật Hình sự
# ---------------------------------------------------------------------------
CODE_LEGISLATION = {"@type": "Legislation", "name": "Bộ luật Hình sự", "legislationIdentifier": "100/2015/QH13",
                    "legislationJurisdiction": "VN", "inLanguage": "vi"}


def chapter_desc(ch):
    """Mô tả trang chương: tên chương, phạm vi điều, rồi thêm lần lượt tên các điều đầu
    chương khi còn chỗ (không cắt dở tên điều). Tên chương quá dài thì rút gọn tên chương
    nhưng giữ phạm vi điều và lời mời đọc."""
    arts = ch["a"]
    rng = f'Điều {arts[0]["id"]}–{arts[-1]["id"]}' if len(arts) > 1 else f'Điều {arts[0]["id"]}'
    code_name = "" if "bộ luật hình sự" in ch["name"].lower() else " Bộ luật Hình sự"  # tránh lặp chữ ở Chương II
    head = f'{ch["title"]}{code_name} 2015 ({rng}, {len(arts)} điều)'
    tail = " Toàn văn kèm bình luận."
    if len(head) + 1 + len(tail) > DESC_MAX:
        prefix = f'{ch["label"]} BLHS 2015 ({rng}, {len(arts)} điều): '
        name = fit_desc(ch["name"], DESC_MAX - len(prefix) - len(tail) - 1)
        return prefix + name + ("" if name.endswith("…") else ".") + tail
    best = head + "." + tail
    for k in range(1, 5):
        names = ", ".join(a["t"].lower() for a in arts[:k])
        cand = f"{head}: {names}{'…' if k < len(arts) else '.'}{tail}"
        if len(cand) > DESC_MAX:
            break
        best = cand
    return best


def article_desc(code, a):
    """Mô tả trang điều luật. Điều quy định tội danh: số khung và mức hình phạt cao nhất
    (trích tự động từ văn bản điều luật, xem blhs.penalty_summary). Điều khác: trích đoạn đầu."""
    head = f'Điều {a["id"]} BLHS 2015 – {a["t"]}'
    if a.get("repealed"):
        return fit_desc(f"{head}: " + code.excerpt(a, 300))
    pen = blhs.penalty_summary(a)
    if pen:
        n, top = pen
        body = f"{n} khung hình phạt, cao nhất {top}" if n > 1 else f"khung hình phạt cao nhất {top}"
        for tail in (". Toàn văn, bình luận và các điều liên quan.", ". Toàn văn kèm bình luận.", "."):
            if len(f"{head}: {body}{tail}") <= DESC_MAX:
                return f"{head}: {body}{tail}"
        return fit_desc(f'Điều {a["id"]} BLHS 2015 quy định {body}: {a["t"].lower()}.')
    head += ": "
    return fit_desc(head + code.excerpt(a, max(60, DESC_MAX - len(head) + 20)))


def blhs_pages():
    code = blhs.Code()
    rd = blhs.Renderer(code, ico, ARROW, FIRM)
    common = {
        "section": "knowledge", "page_hero": False, "body_class": "tdl-page", "index_k": False,
        "extra_head": '\n<link rel="stylesheet" href="{{root}}bo-luat-hinh-su/tu-dien.css?v=' + file_hash("bo-luat-hinh-su/tu-dien.css") + '">',
        "scripts": ["bo-luat-hinh-su/lx-core.js?v=" + file_hash("bo-luat-hinh-su/lx-core.js"),
                    "bo-luat-hinh-su/tu-dien.js?v=" + file_hash("bo-luat-hinh-su/tu-dien.js")],
    }
    hub_crumb = ("Bộ luật Hình sự", "bo-luat-hinh-su/")
    pages = []
    st = code.toc["stats"]
    hub = dict(common)
    hub.update({
        "path": "bo-luat-hinh-su/", "h1": "Bộ luật Hình sự",
        "title": seo_title("Tra cứu Bộ luật Hình sự 2015 kèm bình luận"),
        "description": f'Tra cứu toàn văn {st["arts"]} điều Bộ luật Hình sự 2015 (sửa đổi 2017, 2025) kèm bình luận từng điều; tìm theo số điều, khoản, điểm, tội danh, có dấu hoặc không dấu.',
        "crumbs": crumbs_for(("Kiến thức pháp lý", "kien-thuc-phap-ly/"), hub_crumb),
        "body": rd.hub("../"),
        "schema_type": "CollectionPage",
        "webpage_extra": {"about": CODE_LEGISLATION},
    })
    pages.append(hub)
    for ch in code.chapters:
        path = f"bo-luat-hinh-su/{ch['slug']}/"
        pg = dict(common)
        pg.update({
            "path": path, "h1": ch["title"],
            "title": seo_title(f'{ch["title"]} 2015' if "bộ luật hình sự" in ch["name"].lower() else f'{ch["title"]} – Bộ luật Hình sự',
                               f'{ch["label"]} BLHS: {ch["name"]}' if ch["num"] else ch["title"]),
            "description": chapter_desc(ch),
            "crumbs": crumbs_for(hub_crumb, (ch["label"], path)),
            "body": rd.chapter(ch, "../../"),
            "schema_type": "CollectionPage",
            "webpage_extra": {"about": CODE_LEGISLATION},
        })
        pages.append(pg)
    for a in code.arts:
        path = f"bo-luat-hinh-su/dieu-{a['id']}/"
        a["repealed"] = code.excerpt(a, 60).startswith("Tội này đã được bãi bỏ")
        name = a["t"] + (" (đã bãi bỏ)" if a["repealed"] else "")
        pg = dict(common)
        pg.update({
            "path": path, "h1": f'Điều {a["id"]}. {a["t"]}',
            "title": seo_title(f'Điều {a["id"]} Bộ luật Hình sự: {name}', f'Điều {a["id"]} BLHS 2015: {name}',
                               f'Điều {a["id"]} BLHS: {name}'),
            "og_title": f'Điều {a["id"]} Bộ luật Hình sự: {name} | {FIRM["short_name"]}',
            "description": article_desc(code, a),
            "crumbs": crumbs_for(hub_crumb, (a["ch"]["label"], f'bo-luat-hinh-su/{a["ch"]["slug"]}/'), (f'Điều {a["id"]}', path)),
            "body": rd.article(a, "../../"),
            "search_title": f'Điều {a["id"]}. {a["t"]}',
            "search_desc": code.excerpt(a, 150),
            "webpage_extra": {"about": {
                "@type": "Legislation", "name": f'Điều {a["id"]}. {a["t"]}', "legislationJurisdiction": "VN", "inLanguage": "vi",
                "legislationIdentifier": f'Điều {a["id"]} Bộ luật Hình sự số 100/2015/QH13', "isPartOf": CODE_LEGISLATION}},
        })
        pages.append(pg)
    return pages


def all_pages():
    pages = []
    meta, body = load_src("pages/home.html")
    home = {"path": "", "section": "home", "crumbs": [HOME], "body": body, "page_hero": False,
            # Ảnh nền banner khai báo trong nam-theme.css, mobile.css: giữ cùng ?v= với hai tệp đó
            "preload_images": ["assets/img/nam-hero-luat-su.webp?v=20261006b"]}
    home.update(meta)
    pages.append(home)

    pages.append(simple_page("gioi-thieu", "gioi-thieu/", "about",
                             crumbs_for(("Giới thiệu", "gioi-thieu/")), schema_type="AboutPage"))
    pages.append(simple_page("vi-sao-chon-chung-toi", "vi-sao-chon-chung-toi/", "about",
                             crumbs_for(("Giới thiệu", "gioi-thieu/"), ("Vì sao chọn chúng tôi", "vi-sao-chon-chung-toi/"))))
    pages.append(simple_page("quy-trinh-lam-viec", "quy-trinh-lam-viec/", "about",
                             crumbs_for(("Giới thiệu", "gioi-thieu/"), ("Quy trình làm việc", "quy-trinh-lam-viec/"))))
    pages.append(services_hub())
    pages.extend(service_page(s) for s in SERVICES)
    pages.append(knowledge_hub())
    pages.extend(article_page(a) for a in ARTICLES)
    pages.append(faq_page())

    pages.extend(blhs_pages())

    pages.append(simple_page("lien-he", "lien-he/", "contact", crumbs_for(("Liên hệ", "lien-he/")), schema_type="ContactPage"))
    for name, label in [("chinh-sach-bao-mat", "Chính sách bảo mật"), ("dieu-khoan-su-dung", "Điều khoản sử dụng"),
                        ("mien-tru-trach-nhiem", "Miễn trừ trách nhiệm")]:
        pages.append(simple_page(name, f"{name}/", "", crumbs_for((label, f"{name}/")),
                                 hero={"aside": "none"}, body_class="legal-page"))

    nf = simple_page("404", "404.html", "", [HOME], noindex=True, root_override=BASE_PATH, page_hero=False)
    pages.append(nf)
    return pages


# ---------------------------------------------------------------------------
# Tệp phụ trợ
# ---------------------------------------------------------------------------
def write(rel, text):
    full = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(text)


# ---------------------------------------------------------------------------
# Ngày cập nhật thật của từng trang (sitemap lastmod, dateModified)
# ---------------------------------------------------------------------------
# Google chỉ tin lastmod khi nó phản ánh lần sửa nội dung thật. tools/lastmod.json lưu
# dấu vân tay nội dung (tiêu đề, mô tả, thân trang) và ngày đổi gần nhất của mỗi trang:
# build lại mà nội dung không đổi thì ngày giữ nguyên. Nhớ commit tệp này cùng các trang.
LASTMOD_FILE = os.path.join(ROOT, "tools", "lastmod.json")


def fingerprint(page):
    parts = [page.get("title", ""), page.get("description", ""), page.get("h1", ""), page["body"]]
    return hashlib.md5("\x00".join(parts).encode("utf-8")).hexdigest()[:12]


def git_date(rel):
    """Ngày commit gần nhất của trang đã sinh (chỉ dùng khi trang chưa có trong sổ)."""
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
        return out or TODAY
    except (OSError, subprocess.CalledProcessError):
        return TODAY


def apply_lastmod(pages):
    try:
        with open(LASTMOD_FILE, encoding="utf-8") as fh:
            ledger = json.load(fh)
    except FileNotFoundError:
        ledger = {}
    fresh = {}
    for p in pages:
        fp = fingerprint(p)
        old = ledger.get(p["path"])
        if old and old["hash"] == fp:
            date = old["date"]
        elif old:
            date = TODAY
        else:
            date = git_date(out_file(p))
        fresh[p["path"]] = {"hash": fp, "date": date}
        # Bài viết tự khai báo ngày cập nhật (hiển thị trên trang) thì giữ ngày đó
        p.setdefault("modified", date)
    with open(LASTMOD_FILE, "w", encoding="utf-8") as fh:
        json.dump(fresh, fh, ensure_ascii=False, indent=0, sort_keys=True)
        fh.write("\n")


def out_file(page):
    return page["path"] if page["path"].endswith(".html") else page["path"] + "index.html"


IMG_RE = re.compile(r'<img\b[^>]*?\bsrc="([^"]+)"[^>]*?\balt="([^"]+)"')


def content_images(page, rendered):
    """Ảnh nội dung (có alt) trong <main>, đổi sang địa chỉ tuyệt đối cho image sitemap."""
    main = rendered.split('<main id="main">', 1)[-1].split("</main>", 1)[0]
    base = "/" + os.path.dirname(out_file(page))
    seen = []
    for src, _alt in IMG_RE.findall(main):
        if src.startswith(("http:", "https:", "data:")):
            continue
        u = abs_url(os.path.normpath(os.path.join(base, src)).lstrip("/"))
        if u not in seen:
            seen.append(u)
    return seen


def main():
    pages = all_pages()
    apply_lastmod(pages)
    images = {}
    for p in pages:
        rendered = layout(p)
        write(out_file(p), rendered)
        images[p["path"]] = content_images(p, rendered)

    # Trang cũ đã gộp vào Giới thiệu: chuyển hướng ngay (Google coi như chuyển hướng 301).
    # Không đặt noindex để tín hiệu chuyển hướng và canonical không mâu thuẫn nhau.
    write("doi-ngu-luat-su/index.html", '<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=../gioi-thieu/#doi-ngu-luat-su"><title>Giới thiệu Luật Sư Nam</title><link rel="canonical" href="' + SITE_URL + '/gioi-thieu/"></head><body><p>Nội dung đội ngũ đã được chuyển vào <a href="../gioi-thieu/#doi-ngu-luat-su">Giới thiệu Luật Sư Nam</a>.</p></body></html>')

    indexable = [p for p in pages if not p.get("noindex")]
    urls = "".join(
        f"  <url>\n    <loc>{abs_url(p['path'])}</loc>\n    <lastmod>{p['modified']}</lastmod>\n"
        + "".join(f"    <image:image><image:loc>{esc(u)}</image:loc></image:image>\n" for u in images[p["path"]])
        + "  </url>\n"
        for p in indexable)
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
          f' xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n{urls}</urlset>\n')
    write("robots.txt", f"# {FIRM['legal_name']}\nUser-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    write("site.webmanifest", json.dumps({
        "name": FIRM["legal_name"], "short_name": "LSN Law Firm", "description": "Tư vấn pháp lý và tham gia tố tụng tại Thành phố Hồ Chí Minh.",
        "lang": "vi", "start_url": "./", "scope": "./", "display": "standalone",
        "background_color": "#fffefa", "theme_color": "#c50008",
        "icons": [{"src": "assets/img/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "assets/img/icon-512.png", "sizes": "512x512", "type": "image/png"},
                  {"src": "assets/img/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"}],
    }, ensure_ascii=False, indent=2) + "\n")

    # Chỉ mục tìm kiếm trong site
    index = []
    for p in indexable:
        if p.get("index_k", True):
            heads = re.findall(r"<h[23][^>]*>(.*?)</h[23]>", render_tokens(p["body"], p, ""), re.S)
            keys = " · ".join(strip_tags(h) for h in heads)[:600]
        else:
            keys = ""
        section = "Bộ luật Hình sự" if p["path"].startswith("bo-luat-hinh-su/") else \
            next((lbl for key, lbl, _, _ in NAV if key == p.get("section")), "")
        index.append({"t": p.get("search_title") or (p["crumbs"][-1][0] if p["path"] else FIRM["legal_name"]), "u": p["path"],
                      "d": p.get("search_desc") or p["description"], "s": section, "k": keys})
    for f in FAQ:
        index.append({"t": f["q"], "u": f"cau-hoi-thuong-gap/#{f['id']}", "d": strip_tags(f["a"][0].replace("{{root}}", ""))[:180],
                      "s": "Câu hỏi thường gặp", "k": ""})
    write("assets/search-index.json", json.dumps(index, ensure_ascii=False, separators=(",", ":")))

    print(f"Đã tạo {len(pages)} trang, sitemap {len(indexable)} URL.")


if __name__ == "__main__":
    main()
