# -*- coding: utf-8 -*-
"""Sinh toàn bộ website tĩnh LSN Law Firm – Công Ty Luật TNHH Luật Sư Nam.

    python3 tools/build.py

Nguồn nội dung:
    tools/data.py            Thông tin pháp nhân, 7 lĩnh vực, bài viết, câu hỏi thường gặp
    src/pages/*.html         Nội dung các trang đơn lẻ (có khối <!--meta {...} --> ở đầu)
    src/bai-viet/*.html      Nội dung bài viết

Kết quả: <duong-dan>/index.html cho mọi trang, 404.html, sitemap.xml, robots.txt,
site.webmanifest, assets/search-index.json.
"""
import datetime
import hashlib
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import (ARTICLE_BY_SLUG, ARTICLES, BASE_PATH, FAQ, FIRM, PROBLEM_ORDER,  # noqa: E402
                  SERVICE_BY_SLUG, SERVICES, SITE_URL, articles_for_service)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
TODAY = datetime.date.today().isoformat()
ORG_ID = SITE_URL + "/#organization"
SITE_ID = SITE_URL + "/#website"
ASSET_VERSION = "20261015b"


def esc(s):
    return html.escape(s, quote=True)


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def file_hash(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()[:8]


def abs_url(path):
    return SITE_URL + "/" + path


def asset_ref(path):
    return f"{path}?v={ASSET_VERSION}"


# ---------------------------------------------------------------------------
# Ảnh thật của luật sư: AVIF (nhẹ) + WebP (dự phòng), 3 bề ngang do tools/make_images.py sinh ra
# ---------------------------------------------------------------------------
PHOTO_SETS = {
    "van-phong": {"w": 784, "h": 651, "alt": f'{FIRM["lawyer"]} làm việc tại văn phòng Luật Sư Nam, {FIRM["street"]}',
                  "sizes": "(max-width: 700px) calc(100vw - 40px), (max-width: 900px) 640px, 560px"},
    "phien-toa": {"w": 800, "h": 812, "alt": f'{FIRM["lawyer"]} tại ghế người bào chữa trong phiên tòa',
                  "sizes": "(max-width: 600px) calc(100vw - 40px), 520px"},
}


def picture(r, name, lazy=False):
    p = PHOTO_SETS[name]
    base = f"assets/img/luat-su-{name}"

    def srcset(ext):
        return ", ".join(f"{r}{asset_ref(f'{base}{s}.{ext}')} {w}w" for s, w in (("-480", 480), ("-640", 640), ("", p["w"])))
    load = 'loading="lazy" decoding="async"' if lazy else 'fetchpriority="high"'
    return (f'<picture><source type="image/avif" srcset="{srcset("avif")}" sizes="{p["sizes"]}">'
            f'<img src="{r}{asset_ref(base + ".webp")}" srcset="{srcset("webp")}" sizes="{p["sizes"]}" '
            f'alt="{esc(p["alt"])}" width="{p["w"]}" height="{p["h"]}" {load}></picture>')


def open_now(cls="open-now"):
    """Trạng thái "Đang trong giờ làm việc / Ngoài giờ" theo giờ Việt Nam, do main.js điền khi tải trang."""
    # Giữ sẵn chỗ (ẩn bằng visibility) để khi điền chữ, bố cục không bị xô lệch
    return f'<span class="{cls}" data-open-now>&nbsp;</span>'


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
  <symbol id="i-lock" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3M12 15v2"/></g></symbol>
  <symbol id="i-coin" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="6" width="19" height="12" rx="2"/><circle cx="12" cy="12" r="2.6"/><path d="M6 9.5v.01M18 14.5v.01"/></g></symbol>
  <symbol id="i-check-circle" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8 12.4l2.8 2.8L16.2 9.8"/></g></symbol>
  <symbol id="i-list" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M9 6h11M9 12h11M9 18h11"/><path d="M4.5 6h.01M4.5 12h.01M4.5 18h.01" stroke-width="2.6"/></g></symbol>
  <symbol id="i-alert" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M12 3 2 20h20L12 3z" stroke-linejoin="round"/><path d="M12 10v4M12 17v.5"/></g></symbol>
</svg>"""


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
                ("Tranh chấp & thủ tục", ["tranh-tung-giai-quyet-tranh-chap", "hinh-su", "cong-chung"]),
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
    """Có tag: "LUẬT SƯ NAM" + khẩu hiệu (footer). Không tag: "Công Ty Luật TNHH / Luật Sư Nam" (header)."""
    # Tên đọc bởi trình đọc màn hình lấy từ chữ hiển thị (khớp nhãn nhìn thấy), thêm "Trang chủ" ẩn
    text = (f'<span class="logo__name">LUẬT SƯ NAM</span> <span class="logo__tag">{tag}</span>' if tag else
            '<span class="logo__pre">Công Ty Luật TNHH</span> <span class="logo__name logo__name--firm">Luật Sư Nam</span>')
    return f"""<a class="logo" href="{r or './'}">
      <img class="logo__img" src="{r}{asset_ref("assets/img/logo-lsn-108.webp")}" srcset="{r}{asset_ref("assets/img/logo-lsn.webp")} 3x" width="54" height="54" alt="">
      <span class="logo__text">{text}<span class="sr-only"> – Trang chủ</span></span>
    </a>"""


def header_html(page, r):
    return f"""<header class="header site-header" id="site-header">
  <div class="container header__inner">
    {logo_html(r)}

    <nav class="nav" id="nav" aria-label="Điều hướng chính">
      <ul class="nav__list">
        {nav_html(page, r)}
      </ul>
      <div class="nav__mobile-extra">
        <a class="btn btn--primary btn--block" href="tel:{FIRM["phone_tel"]}">{ico("i-phone")} Gọi {FIRM["phone"]}</a>
        <a class="btn btn--zalo btn--block" href="{FIRM["zalo"]}" target="_blank" rel="noopener">{ico("i-chat")} Nhắn Zalo cho luật sư</a>
        <p class="nav__note">{ico("i-clock")}{FIRM["hours"]}</p>
        <p class="nav__note">{open_now()}</p>
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

<nav class="actionbar" aria-label="Liên hệ nhanh với luật sư">
  <a class="actionbar__call" href="tel:{FIRM["phone_tel"]}">{ico("i-phone", "")}<span>Gọi luật sư</span></a>
  <a class="actionbar__zalo" href="{FIRM["zalo"]}" target="_blank" rel="noopener">{ico("i-chat", "")}<span>Nhắn Zalo</span></a>
</nav>

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
      <a href="{r}dich-vu/hinh-su/">Luật sư hình sự</a>
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


def lawyer_card(r):
    """Thẻ luật sư phụ trách ở đầu trang: ảnh thật, tên, gọi / Zalo."""
    # Điện thoại, máy tính bảng: ảnh hiển thị tròn 72–96px nên dùng ảnh avatar vuông (nhẹ, đúng khung mặt)
    return f"""<aside class="lcard" aria-label="Luật sư phụ trách">
      <picture>
        <source media="(max-width: 900px)" srcset="{r}{asset_ref("assets/img/luat-su-avatar.webp")}">
        <source type="image/avif" srcset="{r}{asset_ref("assets/img/luat-su-chan-dung.avif")}">
        <img class="lcard__photo" src="{r}{asset_ref("assets/img/luat-su-chan-dung.webp")}" alt="{FIRM["lawyer"]} tại phiên tòa" width="560" height="420">
      </picture>
      <div class="lcard__body">
        <p class="lcard__name">{FIRM["lawyer"]}</p>
        <p class="lcard__role">{FIRM["lawyer_role"]}</p>
        <div class="lcard__actions">
          <a class="btn btn--primary btn--sm" href="tel:{FIRM["phone_tel"]}">{ico("i-phone")} Gọi {FIRM["phone"]}</a>
          <a class="btn btn--outline btn--sm" href="{FIRM["zalo"]}" target="_blank" rel="noopener">{ico("i-chat")} Zalo</a>
        </div>
        <p class="lcard__note">{ico("i-clock")} {FIRM["hours"]}</p>
        {open_now("open-now lcard__status")}
      </div>
    </aside>"""


def page_hero_html(page, r):
    """Đầu trang con dùng chung: đường dẫn, tiêu đề, mô tả; bên phải là thẻ luật sư phụ trách."""
    h = page.get("hero") or {}
    aside = lawyer_card(r) if page.get("lawyer_card", True) else ""
    lead = f'<p class="phead__lead">{page["lead"]}</p>' if page.get("lead") else ""
    eyebrow = f'<p class="eyebrow">{esc(page["eyebrow"])}</p>' if page.get("eyebrow") else ""
    actions = f'<div class="phead__actions">{h["actions"]}</div>' if h.get("actions") else ""
    return f"""<section class="phead{' phead--aside' if aside else ''}">
  <div class="container phead__grid">
    <div class="phead__copy">
      {breadcrumb_html(page["crumbs"], r)}
      {eyebrow}
      <h1 class="phead__title">{page["h1"]}</h1>
      {lead}
      {h.get("extra", "")}
      {actions}
    </div>
    {aside}
  </div>
</section>"""


CBAND_TEXT = ("Vụ việc càng sớm được xem xét, anh chị càng có nhiều lựa chọn. Với việc gấp như người nhà bị tạm giữ "
              "hoặc sắp hết thời hạn kháng cáo, hãy gọi điện trực tiếp.")


def contact_band(r, eyebrow="Tư vấn trực tiếp với luật sư", title="Cần hỏi luật sư? Liên hệ ngay", text=CBAND_TEXT):
    """Khối liên hệ cuối mọi trang: ảnh luật sư, gọi điện, Zalo, đường đến văn phòng."""
    return f"""<section class="cband" aria-labelledby="cband-title">
  <div class="container">
    <div class="cband__intro">
      <img class="cband__avatar" src="{r}{asset_ref("assets/img/luat-su-avatar.webp")}" alt="{FIRM["lawyer"]}" width="92" height="92" loading="lazy" decoding="async">
      <div>
        <p class="eyebrow">{esc(eyebrow)}</p>
        <h2 class="cband__title" id="cband-title">{title}</h2>
        <p class="cband__text">{text}</p>
      </div>
    </div>
    <div class="cband__cards">
      <a class="cband__card" href="tel:{FIRM["phone_tel"]}">{ico("i-phone")}<span>Gọi điện</span><strong>{FIRM["phone"]}</strong><small>{FIRM["hours"]}</small>{open_now()}</a>
      <a class="cband__card cband__card--zalo" href="{FIRM["zalo"]}" target="_blank" rel="noopener">{ico("i-chat")}<span>Nhắn Zalo</span><strong>{FIRM["phone"]}</strong><small>Kể ngắn gọn sự việc, luật sư phản hồi trong giờ làm việc</small></a>
      <a class="cband__card" href="https://www.google.com/maps/dir/?api=1&amp;destination={FIRM["maps_query"]}" target="_blank" rel="noopener">{ico("i-pin")}<span>Đến văn phòng</span><strong>{FIRM["street"]}</strong><small>{FIRM["ward"]}, TP.HCM · gọi trước khi đến</small></a>
    </div>
  </div>
</section>"""


def shead(eyebrow, title, text="", link=None, center=False, hid=""):
    """Tiêu đề khu vực dùng chung: nhãn nhỏ, tiêu đề, mô tả, liên kết bên phải."""
    eb = f'<p class="eyebrow">{eyebrow}</p>' if eyebrow else ""
    p = f'<p class="shead__text">{text}</p>' if text else ""
    a = f'<a class="link-arrow" href="{link[0]}">{link[1]} {ARROW}</a>' if link else ""
    idattr = f' id="{hid}"' if hid else ""
    cls = "shead shead--center" if center else "shead"
    return f'<div class="{cls} reveal"><div class="shead__main">{eb}<h2 class="h2"{idattr}>{title}</h2>{p}</div>{a}</div>'


def icard(href, icon, title, text, more="Xem chi tiết", heading="h3"):
    return (f'<a class="icard reveal" href="{href}"><span class="ichip">{ico(icon, "")}</span>'
            f'<{heading} class="icard__title">{title}</{heading}><p class="icard__text">{text}</p>'
            f'<span class="icard__more">{more} {ARROW}</span></a>')


def problem_card(s, r):
    """Thẻ "anh chị đang gặp chuyện gì": tình huống đời thường dẫn tới trang lĩnh vực."""
    return (f'<a class="icard reveal" href="{r}dich-vu/{s["slug"]}/"><span class="ichip">{ico(s.get("problem_icon", s["icon"]), "")}</span>'
            f'<span class="icard__tag">{esc(s["name"])}</span>'
            f'<h3 class="icard__title">{esc(s["problem_title"])}</h3><p class="icard__text">{esc(s["problem_text"])}</p>'
            f'<span class="icard__more">Xem cách giải quyết {ARROW}</span></a>')


def problems_grid(r):
    return '<div class="grid grid--4 grid--problems">' + "".join(problem_card(SERVICE_BY_SLUG[x], r) for x in PROBLEM_ORDER) + "</div>"


def service_card(s, r, heading="h3"):
    return icard(f'{r}dich-vu/{s["slug"]}/', s["icon"], esc(s["name"]), esc(s["short"]), heading=heading)


def services_grid(r, exclude=None, only=None, cls="grid grid--4"):
    items = [SERVICE_BY_SLUG[x] for x in only] if only else [s for s in SERVICES if s["slug"] != exclude]
    return f'<div class="{cls}">' + "".join(service_card(s, r) for s in items) + "</div>"


def vi_date(iso):
    y, m, d = iso.split("-")
    return f"{int(d):02d} Tháng {int(m)}, {y}"


def article_card(a, r, heading="h3"):
    return f"""<article class="post reveal">
  <p class="post__meta"><a class="tag" href="{r}dich-vu/{a["service"]}/">{esc(a["category"])}</a><time datetime="{a["published"]}">{ico("i-calendar")}{vi_date(a["published"])}</time></p>
  <{heading} class="post__title"><a href="{r}kien-thuc-phap-ly/{a["slug"]}/">{esc(a["card_title"])}</a></{heading}>
  <p class="post__excerpt">{esc(a["excerpt"])}</p>
  <span class="post__more" aria-hidden="true">Đọc bài viết {ARROW}</span>
</article>"""


def articles_grid(r, items=None, cls="grid grid--3"):
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


def check_list(items):
    return '<ul class="check-list">' + "".join(f"<li>{ico('i-check')}<span>{esc(i)}</span></li>" for i in items) + "</ul>"


TOKEN_RE = re.compile(r"\{\{(\w+)(?::([^}]*))?\}\}")


def render_tokens(body, page, r):
    def rep(m):
        name, arg = m.group(1), m.group(2)
        if name == "root":
            return r
        if name in ("phone", "phone_tel", "email", "zalo", "address", "hours", "hours_note", "maps_query",
                    "legal_name", "street", "ward", "city", "lawyer", "lawyer_role"):
            return FIRM[name]
        if name == "v":
            return ASSET_VERSION
        if name == "cta":
            return ""
        if name == "services_grid":
            return services_grid(r)
        if name == "problems_grid":
            return problems_grid(r)
        if name == "articles_grid":
            return articles_grid(r)
        if name == "faq_list":
            ids = arg.split(",") if arg else None
            return faq_list(r, [f for f in FAQ if f["id"] in ids] if ids else None)
        if name == "arrow":
            return ARROW
        if name == "photo":
            nm, _, opt = arg.partition("|")
            return picture(r, nm, lazy=opt == "lazy")
        if name == "open_now":
            return open_now()
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
                       "đất đai, hôn nhân gia đình, hình sự, dân sự, công chứng và tranh chấp thương mại.",
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
    # Ảnh chia sẻ JPG 1200×630 (Facebook, Zalo, LinkedIn): riêng cho dịch vụ, bài viết; còn lại dùng ảnh chung
    image = abs_url(asset_ref(page.get("og_image", "assets/img/og-image.jpg")))
    robots = "noindex, follow" if page.get("noindex") else "index, follow, max-image-preview:large, max-snippet:-1"
    og_type = page.get("og_type", "website")
    art_meta = ""
    if og_type == "article":
        art_meta = (f'\n<meta property="article:published_time" content="{page["published"]}">'
                    f'\n<meta property="article:modified_time" content="{page["modified"]}">'
                    f'\n<meta property="article:section" content="{esc(page["article_section"])}">')
    extra_head = page.get("extra_head", "").replace("{{root}}", r)
    hero = render_tokens(page_hero_html(page, r), page, r) if page.get("page_hero", True) else ""
    body = render_tokens(page["body"], page, r)
    body = re.sub(r"\s*<!--\s*(GHI CHÚ CHO NGƯỜI QUẢN TRỊ|Nội dung trang tra cứu).*?-->", "", body, flags=re.S)
    band = contact_band(r, **page.get("cband", {})) if page.get("contact_band", True) else ""
    scripts = "".join(f'\n<script src="{r}{s}" defer></script>' for s in page.get("scripts", []))
    body_cls = f' class="{page["body_class"]}"' if page.get("body_class") else ""
    canonical = "" if page.get("noindex") else f'\n<link rel="canonical" href="{url}">'
    # Trang 404 được phục vụ ở mọi độ sâu đường dẫn: xác định thư mục gốc khi chạy để tài nguyên tải đúng
    # cả trên GitHub Pages (BASE_PATH) lẫn tên miền riêng (/)
    base_js = ""
    if page.get("dynamic_base"):
        base_js = ('\n<script>(function(){var p="' + BASE_PATH + '",b=document.createElement("base");'
                   'b.href=location.pathname.indexOf(p)===0?p:"/";document.head.appendChild(b);})();</script>')
    return f"""<!doctype html>
<html lang="vi" data-root="{r}">
<head>
<meta charset="utf-8">{base_js}
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(page["title"])}</title>
<meta name="description" content="{esc(page["description"])}">
<meta name="robots" content="{robots}">{canonical}
<meta name="author" content="{FIRM["legal_name"]}">
<meta name="theme-color" content="#fffdf9">
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
<meta property="og:image:alt" content="{esc(page.get("og_title", page["title"]))} – {FIRM["lawyer"]}">{art_meta}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(page.get("og_title", page["title"]))}">
<meta name="twitter:description" content="{esc(page["description"])}">
<meta name="twitter:image" content="{image}">
<link rel="icon" href="{r}assets/img/favicon-32.png" sizes="32x32" type="image/png">
<link rel="icon" href="{r}assets/img/icon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="{r}assets/img/apple-touch-icon.png">
<link rel="manifest" href="{r}site.webmanifest">
<link rel="preload" href="{r}assets/fonts/be-vietnam-pro-400-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{r}assets/fonts/be-vietnam-pro-400-normal-vietnamese.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{r}assets/css/style.css?v={css_v}">{extra_head}
<script type="application/ld+json">
{jsonld(page)}
</script>
</head>
<body{body_cls}>
<a class="skip-link" href="#main">Bỏ qua đến nội dung chính</a>
{SPRITE}
{header_html(page, r)}

<main id="main">
{hero}
{body}
{band}
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
    situations = "".join(f'<li>{ico("i-check-circle")}<span>{esc(x)}</span></li>' for x in s["situations"])
    scope = "".join(f'<article class="ncard ncard--num reveal"><div class="ncard__top"><span class="ncard__num">{i:02d}</span></div>'
                    f'<h3>{esc(h)}</h3><p>{esc(p)}</p></article>' for i, (h, p) in enumerate(s["scope"], 1))
    tips = "".join(f"<li>{esc(x)}</li>" for x in s["tips"])
    steps = "".join(f'<li class="reveal"><span class="steps__num">{i}</span><h3>{esc(h)}</h3><p>{esc(p)}</p></li>'
                    for i, (h, p) in enumerate(s["steps"], 1))
    faq = "".join(f"""<details class="faq__item" id="hoi-dap-{i}">
  <summary><span>{esc(q)}</span>{ico("i-chevron", "faq__chev")}</summary>
  <div class="faq__answer"><p>{a}</p></div>
</details>""" for i, (q, a) in enumerate(s["faq"], 1))
    laws = "".join(f'<li>{esc(x)}</li>' for x in s["laws"])
    resources = [(f'kien-thuc-phap-ly/{a["slug"]}/', "Bài viết", a["card_title"], a["excerpt"]) for a in arts[:3]]
    extras = [("cau-hoi-thuong-gap/", "Hỏi đáp", "Câu hỏi thường gặp khi thuê luật sư", "Chi phí, bảo mật và cách bắt đầu làm việc với luật sư."),
              ("quy-trinh-lam-viec/#ho-so-can-chuan-bi", "Chuẩn bị", "Trước buổi gặp luật sư đầu tiên", "Giấy tờ nên mang theo và cách ghi lại diễn biến sự việc."),
              ("vi-sao-chon-chung-toi/", "Cách làm việc", "Những điều luật sư cam kết và không làm", "Nói rõ được – mất, chi phí thỏa thuận trước, không hứa hẹn kết quả.")]
    resources += extras[:max(0, 3 - len(resources))]
    cards = "".join(f'<a class="rcard reveal" href="{{{{root}}}}{href}"><span class="tag">{label}</span><h3>{esc(title)}</h3>'
                    f'<p>{esc(text)}</p><span class="icard__more">Xem chi tiết {ARROW}</span></a>' for href, label, title, text in resources)
    related = "".join(icard(f'{{{{root}}}}dich-vu/{x["slug"]}/', x["icon"], esc(x["name"]), esc(x["short"]))
                      for x in SERVICES if x["slug"] in s["related"])
    urgent = ""
    if s.get("urgent"):
        urgent = (f'<p class="urgent">{ico("i-alert")}<span><strong>Việc gấp?</strong> Người thân vừa bị bắt, tạm giữ hoặc sắp phải làm việc với cơ quan điều tra: '
                  f'hãy gọi ngay <a href="tel:{FIRM["phone_tel"]}">{FIRM["phone"]}</a>. {FIRM["hours_note"]}.</span></p>')
    body = f"""
<nav class="subnav" aria-label="Nội dung trang"><div class="container"><a href="#tinh-huong">Tình huống thường gặp</a><a href="#pham-vi">Luật sư giúp gì</a><a href="#viec-nen-lam">Việc nên làm ngay</a><a href="#quy-trinh">Các bước</a><a href="#ho-so">Giấy tờ</a><a href="#hoi-dap">Hỏi đáp</a></div></nav>

<section class="section svc-section" id="tinh-huong">
  <div class="container">
    {shead("Tình huống thường gặp", "Anh chị có đang gặp chuyện này?", f"Đây là những trường hợp về {esc(name_lc)} mà người dân thường tìm đến luật sư.")}
    <ul class="situations">{situations}</ul>
    <p class="situations__foot">Trường hợp của anh chị khác? Cứ <a href="tel:{FIRM["phone_tel"]}">gọi {FIRM["phone"]}</a> hoặc <a href="{FIRM["zalo"]}" target="_blank" rel="noopener">nhắn Zalo</a> kể ngắn gọn – luật sư sẽ cho biết có giúp được hay không.</p>
  </div>
</section>

<section class="section section--cream svc-section" id="pham-vi">
  <div class="container">
    {shead("Phạm vi hỗ trợ", "Luật sư giúp được anh chị những gì", esc(s["scope_intro"]))}
    <div class="grid grid--3">{scope}</div>
  </div>
</section>

<section class="section svc-section" id="viec-nen-lam">
  <div class="container split">
    <div class="reveal">
      <p class="eyebrow">Trong lúc chờ gặp luật sư</p>
      <h2 class="h2">Việc nên làm ngay</h2>
      <p class="shead__text">Những việc nhỏ dưới đây giúp anh chị giữ được quyền lợi.</p>
      <ol class="tips">{tips}</ol>
    </div>
    <div class="stack">
      <div class="note reveal">{ico("i-alert")}<p><strong>{esc(s["note_title"])}:</strong> {esc(s["note_text"])}</p></div>
      <article class="context__dark reveal"><p class="eyebrow">Cách luật sư làm việc</p><h3>{esc(s["principle_title"])}</h3><p>{esc(s["principle_text"])}</p></article>
    </div>
  </div>
</section>

<section class="section section--cream svc-section" id="quy-trinh">
  <div class="container">
    {shead("Quy trình thực hiện", "Làm việc với luật sư diễn ra thế nào?", "Năm bước rõ ràng. Ở mỗi bước, anh chị đều biết việc gì đang được làm.", link=("{{root}}quy-trinh-lam-viec/", "Quy trình làm việc chung"))}
    <ol class="steps steps--5">{steps}</ol>
  </div>
</section>

<section class="section svc-section" id="ho-so">
  <div class="container">
    {shead("Hồ sơ &amp; kết quả", "Cần chuẩn bị gì và anh chị nhận được gì", "Chưa đủ giấy tờ cũng không sao: cứ mang những gì đang có, luật sư sẽ hướng dẫn bổ sung.")}
    <div class="docs">
      <article class="reveal"><h3><span class="ichip ichip--sm">{ico("i-doc", "")}</span>{esc(s.get("docs_title", "Giấy tờ nên mang theo"))}</h3>{check_list(s["docs"])}<a class="link-arrow" href="{{{{root}}}}quy-trinh-lam-viec/#ho-so-can-chuan-bi">Hướng dẫn chuẩn bị hồ sơ {ARROW}</a></article>
      <article class="reveal"><h3><span class="ichip ichip--sm">{ico("i-check-circle", "")}</span>Anh chị sẽ nhận được</h3>{check_list(s["deliverables"])}<a class="link-arrow" href="{{{{root}}}}cau-hoi-thuong-gap/#chi-phi-thue-luat-su">Chi phí được tính thế nào {ARROW}</a></article>
    </div>
  </div>
</section>

<section class="section section--cream svc-section" id="hoi-dap">
  <div class="container split">
    <div class="reveal">
      <p class="eyebrow">Hỏi đáp</p>
      <h2 class="h2">Câu hỏi hay gặp về {esc(name_lc)}</h2>
      <p class="shead__text">Giải đáp ngắn gọn, có dẫn điều luật. Mỗi vụ việc có tình tiết riêng, anh chị nên hỏi luật sư trước khi quyết định.</p>
      <div class="context__laws laws-box"><h3>Căn cứ pháp luật chủ yếu</h3><ul>{laws}</ul><small>Danh mục tham khảo; văn bản áp dụng cụ thể được luật sư xác định theo từng vụ việc.</small></div>
    </div>
    <div class="faq reveal">{faq}</div>
  </div>
</section>

<section class="section svc-section" id="tham-khao">
  <div class="container">
    {shead("Đọc thêm", "Thông tin hữu ích trước khi gặp luật sư", link=("{{root}}kien-thuc-phap-ly/", "Thư viện kiến thức"))}
    <div class="grid grid--3">{cards}</div>
  </div>
</section>

<section class="section section--cream svc-section" id="lien-quan">
  <div class="container">
    {shead("Lĩnh vực liên quan", "Hỗ trợ các vấn đề có liên quan", link=("{{root}}dich-vu/", "Tất cả dịch vụ"))}
    <div class="grid grid--3">{related}</div>
  </div>
</section>
"""
    url = abs_url(path)
    og = f'assets/img/og/dich-vu-{s["slug"]}.jpg'
    eyebrow = "Luật sư hỗ trợ công chứng" if s["slug"] == "cong-chung" else f"Luật sư {name_lc}"
    return {
        "path": path, "section": "services",
        "title": f'{s["title"]} | {FIRM["short_name"]}', "description": s["description"],
        "eyebrow": eyebrow, "h1": s["hero_title"], "lead": esc(s["lead"]), "hero": {"extra": urgent},
        "crumbs": crumbs_for(("Dịch vụ", "dich-vu/"), (s["name"], path)),
        "image": og, "og_image": og, "body": body,
        "cband": {"eyebrow": f"Tư vấn {name_lc}", "title": esc(s["cta_title"]), "text": esc(s["cta_text"])},
        "schema": [{
            "@type": "Service", "@id": url + "#service", "name": s["name"], "serviceType": s["title"],
            "description": s["description"], "url": url, "provider": {"@id": ORG_ID},
            "areaServed": [{"@type": "City", "name": "Thành phố Hồ Chí Minh"}, {"@type": "Country", "name": "Việt Nam"}],
            "image": abs_url(asset_ref(og)),
        }],
        "webpage_extra": {"mainEntity": {"@id": url + "#service"}},
    }


def services_hub():
    path = "dich-vu/"
    modes = [
        ("i-chat", "Tư vấn, giải đáp", "Luật sư nghe anh chị trình bày, giải thích quy định và hướng xử lý; soạn hoặc kiểm tra hợp đồng, đơn từ, giấy tờ trước khi anh chị ký, nộp."),
        ("i-user", "Thay mặt anh chị làm việc", "Trong phạm vi được ủy quyền, luật sư thay anh chị làm việc, thương lượng, hòa giải với bên kia và làm thủ tục tại cơ quan nhà nước."),
        ("i-gavel", "Cùng anh chị ra Tòa", "Luật sư bào chữa, bảo vệ quyền lợi hoặc đại diện cho anh chị trong vụ án hình sự, dân sự, hôn nhân gia đình, kinh doanh thương mại và tại Trọng tài."),
    ]
    mode_html = "".join(f'<article class="icard reveal"><span class="ichip">{ico(i, "")}</span><h3 class="icard__title">{h}</h3><p class="icard__text">{p}</p></article>'
                        for i, h, p in modes)
    body = f"""
<section class="section section--cream">
  <div class="container">
    {shead("Bảy lĩnh vực", "Chọn tình huống gần giống với anh chị", "Mỗi lĩnh vực có trang riêng: những trường hợp thường gặp, luật sư giúp được gì, giấy tờ cần chuẩn bị và các bước làm việc.")}
    {{{{problems_grid}}}}
  </div>
</section>

<section class="section">
  <div class="container">
    {shead("Hình thức hỗ trợ", "Luật sư có thể giúp anh chị theo ba cách", "Tùy vụ việc, anh chị chọn một hoặc kết hợp nhiều cách, theo phạm vi hành nghề quy định tại Luật Luật sư.", center=True)}
    <div class="grid grid--3">{mode_html}</div>
  </div>
</section>
"""
    url = abs_url(path)
    return {
        "path": path, "section": "services", "schema_type": "CollectionPage",
        "title": f'Lĩnh vực hoạt động – Dịch vụ pháp lý | {FIRM["short_name"]}',
        "description": "Luật Sư Nam tư vấn, đại diện và tham gia tố tụng trong 7 lĩnh vực: thừa kế, tranh tụng, hôn nhân gia đình, đất đai, hình sự, dân sự, công chứng.",
        "eyebrow": "Lĩnh vực hoạt động",
        "h1": "Anh chị cần luật sư <em>giúp việc gì?</em>",
        "lead": "Từ chia di sản, ly hôn, mua bán nhà đất đến người thân gặp chuyện hình sự – Luật Sư Nam tư vấn, đại diện và tham gia tố tụng trong bảy lĩnh vực gắn với đời sống hằng ngày của người dân.",
        "crumbs": crumbs_for(("Lĩnh vực hoạt động", path)),
        "body": body,
        "cband": {"eyebrow": "Chưa rõ lĩnh vực", "title": "Chưa rõ vụ việc thuộc lĩnh vực nào?",
                  "text": "Không sao cả. Anh chị cứ gọi điện hoặc nhắn Zalo kể ngắn gọn sự việc – luật sư sẽ xác định vấn đề pháp lý chính và hướng xử lý phù hợp."},
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
    heads = H2_RE.findall(content)
    toc = "".join(f'<li><a href="#{i}">{strip_tags(t)}</a></li>' for i, t in heads)
    words = len(strip_tags(content).split())
    minutes = max(1, round(words / 220))
    svc = SERVICE_BY_SLUG[a["service"]]
    others = [x for x in ARTICLES if x["slug"] != a["slug"]]
    related_svcs = "".join(
        f'<li><a href="{{{{root}}}}dich-vu/{x}/">{ico(SERVICE_BY_SLUG[x]["icon"], "rel-list__icon")}<span>{esc(SERVICE_BY_SLUG[x]["name"])}</span>{ARROW}</a></li>'
        for x in a["related_services"])
    points = "".join(f"<li>{esc(p)}</li>" for p in a.get("key_points", []))
    keypoints = f'<div class="keypoints"><p class="keypoints__title">{ico("i-list")}Tóm tắt nhanh</p><ul>{points}</ul></div>' if points else ""
    extra = f"""<p class="article-meta">
        <span>{ico("i-user")}Ban biên tập {FIRM["short_name"]}</span>
        <span>{ico("i-calendar")}Đăng <time datetime="{a["published"]}">{vi_date(a["published"])}</time></span>
        <span>{ico("i-clock")}Cập nhật <time datetime="{a["modified"]}">{vi_date(a["modified"])}</time> · {minutes} phút đọc</span>
        <button class="share-btn" type="button" data-share>{ico("i-share")}Chia sẻ bài viết</button>
      </p>"""
    body = f"""
<section class="section">
  <div class="container article-layout">
    <article class="prose" id="noi-dung-bai-viet">
      <details class="toc-mobile">
        <summary>{ico("i-list")}<span>Mục lục bài viết</span><small>{len(heads)} mục</small>{ico("i-chevron", "toc-mobile__chev")}</summary>
        <ol class="toc">{toc}</ol>
      </details>
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
      <div class="aside-card aside-card--cta">
        <div class="aside-card__who"><img src="{{{{root}}}}{asset_ref("assets/img/luat-su-avatar.webp")}" alt="" width="52" height="52" loading="lazy" decoding="async"><div><strong>{FIRM["lawyer"]}</strong><small>Trực tiếp tiếp nhận hồ sơ</small></div></div>
        <p class="aside-card__title">Cần luật sư về {esc(svc["name"].lower())}?</p>
        <p>{esc(svc["short"])}</p>
        <a class="btn btn--primary btn--block btn--sm" href="tel:{FIRM["phone_tel"]}">{ico("i-phone")} Gọi {FIRM["phone"]}</a>
        <a class="btn btn--light btn--block btn--sm" href="{{{{root}}}}dich-vu/{svc["slug"]}/">Xem dịch vụ {esc(svc["name"])}</a>
      </div>
      <div class="aside-card">
        <p class="aside-card__title">Lĩnh vực liên quan</p>
        <ul class="rel-list">{related_svcs}</ul>
      </div>
    </aside>
  </div>
</section>

<section class="section section--cream">
  <div class="container">
    {shead("Đọc tiếp", "Bài viết khác", link=("{{root}}kien-thuc-phap-ly/", "Tất cả bài viết"))}
    {articles_grid("{{root}}", others, cls="grid grid--2")}
  </div>
</section>
"""
    url = abs_url(path)
    og = f'assets/img/og/bai-viet-{a["slug"]}.jpg'
    return {
        "path": path, "section": "knowledge", "og_type": "article", "lawyer_card": False,
        "published": a["published"], "modified": a["modified"], "article_section": a["category"],
        "title": f'{a["seo_title"]} | {FIRM["short_name"]}',
        "og_title": a["title"],
        "description": a["description"],
        "eyebrow": a["category"],
        "h1": esc(a["title"]),
        "crumbs": crumbs_for(("Kiến thức pháp lý", "kien-thuc-phap-ly/"), (a["card_title"], path)),
        "image": og, "og_image": og,
        "hero": {"extra": extra},
        "body": body, "modified": a["modified"],
        "cband": {"eyebrow": f"Tư vấn {svc['name'].lower()}", "title": esc(svc["cta_title"]), "text": esc(svc["cta_text"])},
        "schema": [{
            "@type": "Article", "@id": url + "#article", "headline": a["title"], "description": a["description"],
            "image": abs_url(asset_ref(og)), "datePublished": a["published"],
            "dateModified": a["modified"], "inLanguage": "vi", "articleSection": a["category"], "wordCount": words,
            "author": {"@id": ORG_ID}, "publisher": {"@id": ORG_ID},
            "mainEntityOfPage": {"@id": url + "#webpage"},
            "about": {"@id": abs_url(f'dich-vu/{a["service"]}/') + "#service"},
        }],
    }


def knowledge_hub():
    path = "kien-thuc-phap-ly/"
    body = f"""
<section class="section section--cream">
  <div class="container">
    {shead("Bài viết mới", "Giải thích tình huống người dân hay gặp", "Mỗi bài có trích điều luật cụ thể và ghi rõ ngày cập nhật.")}
    {{{{articles_grid}}}}
  </div>
</section>

<section class="section">
  <div class="container grid grid--2">
    <a class="tool-card tool-card--dark reveal" href="{{{{root}}}}quy-trinh-lam-viec/">
      <span class="ichip">{ico("i-steps", "")}</span>
      <span class="eyebrow">Làm việc với luật sư</span>
      <h2 class="tool-card__title">Quy trình 4 bước và giấy tờ cần chuẩn bị</h2>
      <p>Từ buổi trao đổi đầu tiên đến khi hoàn tất: mỗi bước có đầu việc, kết quả và người phụ trách rõ ràng.</p>
      <span class="link-arrow link-arrow--light">Xem quy trình làm việc {ARROW}</span>
    </a>
    <a class="tool-card reveal" href="{{{{root}}}}cau-hoi-thuong-gap/">
      <span class="ichip">{ico("i-question", "")}</span>
      <span class="eyebrow">Hỏi đáp</span>
      <h2 class="tool-card__title">Câu hỏi thường gặp khi làm việc với luật sư</h2>
      <p>Chi phí thuê luật sư, bảo mật thông tin, thời hiệu, thời gian phản hồi và phạm vi hoạt động.</p>
      <span class="link-arrow">Xem câu hỏi thường gặp {ARROW}</span>
    </a>
  </div>
</section>

<section class="section section--cream">
  <div class="container">
    {shead("Theo lĩnh vực", "Tìm theo vấn đề của anh chị", "Mỗi lĩnh vực có giải đáp ngắn, việc nên làm ngay và giấy tờ cần chuẩn bị.", link=("{{root}}dich-vu/", "Tất cả lĩnh vực"))}
    {{{{problems_grid}}}}
  </div>
</section>
"""
    return {
        "path": path, "section": "knowledge", "schema_type": "CollectionPage",
        "title": f'Kiến thức pháp lý – Bài viết, tra cứu luật | {FIRM["short_name"]}',
        "description": "Bài viết phân tích pháp luật về thừa kế, hôn nhân gia đình, đất đai và giải đáp thắc mắc khi làm việc với luật sư.",
        "eyebrow": "Kiến thức pháp lý",
        "h1": "Hiểu đúng quyền lợi của mình <em>trước khi quyết định</em>",
        "lead": "Bài viết và giải đáp do Luật Sư Nam biên soạn bằng lời lẽ dễ hiểu, có dẫn điều luật cụ thể. Đọc để nắm vấn đề – còn vụ việc của anh chị, hãy hỏi trực tiếp luật sư.",
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
<section class="section">
  <div class="container faq-layout">
    <div>{{{{faq_list}}}}
      <p class="faq__foot">Các giải đáp trên mang tính thông tin chung, không thay thế ý kiến tư vấn cho vụ việc cụ thể. Xem thêm <a href="{{{{root}}}}mien-tru-trach-nhiem/">Tuyên bố miễn trừ trách nhiệm</a>.</p>
    </div>
    <aside class="faq-aside">
      <div class="aside-card">
        <p class="aside-card__title">Tìm hiểu thêm</p>
        <ul class="rel-list">
          <li><a href="{{{{root}}}}quy-trinh-lam-viec/">{ico("i-steps", "rel-list__icon")}<span>Quy trình làm việc</span>{ARROW}</a></li>
          <li><a href="{{{{root}}}}vi-sao-chon-chung-toi/">{ico("i-diamond", "rel-list__icon")}<span>Vì sao chọn chúng tôi</span>{ARROW}</a></li>
          <li><a href="{{{{root}}}}kien-thuc-phap-ly/">{ico("i-book", "rel-list__icon")}<span>Kiến thức pháp lý</span>{ARROW}</a></li>
          <li><a href="{{{{root}}}}lien-he/">{ico("i-pin", "rel-list__icon")}<span>Liên hệ, đường đến văn phòng</span>{ARROW}</a></li>
        </ul>
      </div>
    </aside>
  </div>
</section>
"""
    return {
        "path": path, "section": "knowledge", "schema_type": "FAQPage",
        "title": f'Câu hỏi thường gặp khi thuê luật sư | {FIRM["short_name"]}',
        "description": "Giải đáp về chi phí thuê luật sư theo Điều 55 Luật Luật sư, bảo mật thông tin, cam kết kết quả, thời hiệu, thời gian phản hồi và vụ việc ngoài TP.HCM.",
        "eyebrow": "Câu hỏi thường gặp",
        "h1": "Những điều anh chị <em>hay băn khoăn nhất</em>",
        "lead": "Thuê luật sư tốn bao nhiêu, thông tin có được giữ kín không, có cần gấp không – giải đáp ngắn gọn, có dẫn quy định cụ thể.",
        "crumbs": crumbs_for(("Kiến thức pháp lý", "kien-thuc-phap-ly/"), ("Câu hỏi thường gặp", path)),
        "body": body,
        "cband": {"title": "Chưa thấy câu trả lời? Hỏi trực tiếp luật sư"},
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
    if "title" in page and not page["title"].endswith(FIRM["short_name"]) and path:
        page["title"] = f'{page["title"]} | {FIRM["short_name"]}'
    return page


def all_pages():
    pages = []
    meta, body = load_src("pages/home.html")
    home = {"path": "", "section": "home", "crumbs": [HOME], "body": body, "page_hero": False}
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

    pages.append(simple_page("lien-he", "lien-he/", "contact", crumbs_for(("Liên hệ", "lien-he/")), schema_type="ContactPage",
                             contact_band=False))
    for name, label in [("chinh-sach-bao-mat", "Chính sách bảo mật"), ("dieu-khoan-su-dung", "Điều khoản sử dụng"),
                        ("mien-tru-trach-nhiem", "Miễn trừ trách nhiệm")]:
        pages.append(simple_page(name, f"{name}/", "", crumbs_for((label, f"{name}/")), lawyer_card=False))

    nf = simple_page("404", "404.html", "", [HOME], noindex=True, root_override="", dynamic_base=True,
                     page_hero=False, contact_band=False)
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


def main():
    pages = all_pages()
    for p in pages:
        out = p["path"] if p["path"].endswith(".html") else p["path"] + "index.html"
        write(out, layout(p))

    write("doi-ngu-luat-su/index.html", '<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url=../gioi-thieu/#doi-ngu-luat-su"><title>Giới thiệu Luật Sư Nam</title><link rel="canonical" href="' + SITE_URL + '/gioi-thieu/"></head><body><p>Nội dung đội ngũ đã được chuyển vào <a href="../gioi-thieu/#doi-ngu-luat-su">Giới thiệu Luật Sư Nam</a>.</p></body></html>')

    # Lĩnh vực Lao động & Việc làm đã ngừng: giữ đường dẫn cũ, chuyển về trang Dịch vụ để không ra trang lỗi
    write("dich-vu/lao-dong-viec-lam/index.html", '<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url=../"><title>Lĩnh vực hoạt động – Luật Sư Nam</title><link rel="canonical" href="' + SITE_URL + '/dich-vu/"></head><body><p>Xem các <a href="../">lĩnh vực hoạt động</a> của Luật Sư Nam.</p></body></html>')

    indexable = [p for p in pages if not p.get("noindex")]
    urls = "".join(
        f"  <url>\n    <loc>{abs_url(p['path'])}</loc>\n    <lastmod>{p.get('modified', TODAY)}</lastmod>\n  </url>\n"
        for p in indexable)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    write("robots.txt", f"# {FIRM['legal_name']}\nUser-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    write("site.webmanifest", json.dumps({
        "name": FIRM["legal_name"], "short_name": "LSN Law Firm", "description": "Tư vấn pháp lý và tham gia tố tụng tại Thành phố Hồ Chí Minh.",
        "lang": "vi", "start_url": "./", "scope": "./", "display": "standalone",
        "background_color": "#fffdf9", "theme_color": "#fffdf9",
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
        section = next((lbl for key, lbl, _, _ in NAV if key == p.get("section")), "")
        index.append({"t": p.get("search_title") or (p["crumbs"][-1][0] if p["path"] else FIRM["legal_name"]), "u": p["path"],
                      "d": p.get("search_desc") or p["description"], "s": section, "k": keys})
    for f in FAQ:
        index.append({"t": f["q"], "u": f"cau-hoi-thuong-gap/#{f['id']}", "d": strip_tags(f["a"][0].replace("{{root}}", ""))[:180],
                      "s": "Câu hỏi thường gặp", "k": ""})
    write("assets/search-index.json", json.dumps(index, ensure_ascii=False, separators=(",", ":")))

    print(f"Đã tạo {len(pages)} trang, sitemap {len(indexable)} URL.")


if __name__ == "__main__":
    main()
