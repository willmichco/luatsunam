# -*- coding: utf-8 -*-
"""Sinh website tĩnh Công Ty Luật TNHH Luật Sư Nam từ content/ → dist/.

    pip install -r requirements.txt
    python3 tools/build.py                       # bản chính thức (GitHub Pages)
    DRAFTS=1 NOINDEX=1 python3 tools/build.py    # bản thử: xuất cả bản nháp, chặn Google
    python3 -m http.server 8000 --directory dist

Một lệnh dùng chung cho máy, GitHub Actions và Cloudflare. Biến môi trường:
    SITE_URL       Địa chỉ gốc, không có / cuối (mặc định https://willmichco.github.io/luatsunam)
    BASE_PATH      Thư mục gốc trên máy chủ (mặc định: phần đường dẫn của SITE_URL – /luatsunam/ trên github.io, / trên tên miền riêng)
    DRAFTS=1       Xuất cả bản nháp. Kèm NOINDEX=1 (bản thử): nháp dựng ngay tại đường dẫn thật như đã đăng,
                   /nhap/<đường-dẫn>/ chuyển tới đó. Không kèm NOINDEX (bản chính thức trên tên miền riêng): nháp chỉ
                   dựng dưới /nhap/ (noindex, khóa bằng Cloudflare Access), không lộ ra menu, danh sách, sitemap.
    NOINDEX=1      Chặn Google lập chỉ mục toàn bộ (bản thử)
    CMS_OAUTH_URL  Địa chỉ Worker đăng nhập GitHub cho /admin (để trống: đăng nhập bằng mã truy cập)
    CMS_REPO, CMS_BRANCH  Repo nội dung (mặc định willmichco/luatsunam, main)
Trên Cloudflare Pages (biến CF_PAGES có sẵn) mà chưa đặt SITE_URL: tự chạy chế độ bản thử.

Build lỗi (nhập sai nội dung) → in lỗi tiếng Việt kèm tệp + trường, KHÔNG ghi dist/, site giữ bản cũ.
"""
import datetime
import json
import os
import re
import shutil
import sys
from urllib.parse import urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blocks  # noqa: E402
import content  # noqa: E402
import huong_dan  # noqa: E402
import markup as M  # noqa: E402
import schema  # noqa: E402
import tpl  # noqa: E402
from images import COURT, Images  # noqa: E402
from loi import LOI  # noqa: E402
from markup import Ctx, esc  # noqa: E402
from sprite import SPRITE  # noqa: E402
from tpl import ARROW, asset_ref, ico  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = datetime.date.today().isoformat()
LEGACY_URLS = ["https://willmichco.github.io/luatsunam", "https://luat-su-nam-phap-ly.willmich-co.chatgpt.site",
               "http://willmichco.github.io/luatsunam"]


def read_env():
    e = os.environ
    preview = bool(e.get("CF_PAGES")) and not e.get("SITE_URL")
    site_url = (e.get("SITE_URL") or (e.get("CF_PAGES_URL") if preview else "") or "https://willmichco.github.io/luatsunam").rstrip("/")
    # Suy từ SITE_URL để đổi sang tên miền chỉ cần 1 biến (quên BASE_PATH thì 404, robots, _redirects sẽ sai thư mục)
    base_path = e.get("BASE_PATH") or (urlsplit(site_url).path.rstrip("/") + "/")
    if not base_path.endswith("/"):
        base_path += "/"
    flag = (lambda k, d: (e.get(k) or ("1" if d else "0")).strip().lower() in ("1", "true", "yes"))
    return {
        "site_url": site_url, "base_path": base_path,
        # drafts: nháp hiện trong cấu trúc site như đã đăng (chỉ bản thử noindex toàn site);
        # nhap_rieng: bản chính thức vẫn xuất nháp nhưng chỉ dưới /nhap/ – DRAFTS=1 không bao giờ làm lộ nháp ra site thật
        "drafts": flag("DRAFTS", preview) and flag("NOINDEX", preview),
        "nhap_rieng": flag("DRAFTS", preview) and not flag("NOINDEX", preview),
        "noindex": flag("NOINDEX", preview),
        "oauth_url": e.get("CMS_OAUTH_URL", "").rstrip("/"),
        "repo": e.get("CMS_REPO") or "willmichco/luatsunam", "branch": e.get("CMS_BRANCH") or "main",
        "admin": flag("CMS_ADMIN", True),
        "out": os.path.join(ROOT, e.get("OUT") or "dist"),
        "internal_prefixes": sorted({site_url, *LEGACY_URLS}, key=len, reverse=True),
    }


ENV = None
S = None
IMG = None
ORG_ID = SITE_ID = ""


def abs_url(path):
    return ENV["site_url"] + "/" + path


def F():
    return S.firm


PREFIX = ""  # thư mục chứa trang đang dựng: "nhap/" khi dựng bản nháp riêng (bản chính thức trên tên miền riêng)


def root_of(path):
    return "../" * (PREFIX + path).count("/")


# ---------------------------------------------------------------------------
# Menu, đầu trang, chân trang
# ---------------------------------------------------------------------------
def p2path(value):
    """Giá trị ô "Trang" trong CMS ("/gioi-thieu/") → đường dẫn trang ("gioi-thieu/")."""
    return (value or "/").lstrip("/")


def menu_items():
    """Menu đã bỏ mục trỏ tới bản nháp (bản chính thức) và tự thêm lĩnh vực chưa xếp nhóm."""
    out = []
    for it in S.menu.get("menu") or []:
        it = dict(it)
        if p2path(it.get("trang")) in S.draft_paths and not S.drafts:
            continue
        if it.get("loai") == "menu_xo":
            it["muc_con"] = [x for x in it.get("muc_con") or [] if S.drafts or p2path(x.get("trang")) not in S.draft_paths]
        if it.get("loai") == "menu_linh_vuc":
            groups, placed = [], set()
            for g in it.get("nhom") or []:  # lĩnh vực nằm ở 2 nhóm: chỉ hiện ở nhóm đầu (kiểm nội dung có cảnh báo)
                keep = [x for x in dict.fromkeys(g.get("linh_vuc") or []) if x in S.service_by_slug and x not in placed]
                placed.update(keep)
                groups.append(dict(g, linh_vuc=keep))
            missing = [s["slug"] for s in S.services if s["slug"] not in placed]
            if missing and groups:
                groups[-1]["linh_vuc"] += missing
            it["nhom"] = groups
        out.append(it)
    return out


def menu_members(it):
    paths = {p2path(it.get("trang"))}
    if it.get("loai") == "menu_xo":
        paths |= {p2path(x.get("trang")) for x in it.get("muc_con") or []}
    if it.get("loai") == "menu_linh_vuc":
        paths |= {f"dich-vu/{s['slug']}/" for s in S.services}
    if "kien-thuc-phap-ly/" in paths:
        paths |= {f"kien-thuc-phap-ly/{a['slug']}/" for a in S.articles}
    return paths


def section_of(path):
    """Mục menu được tô sáng: mục chứa trang này; trang không có trên menu thì theo “Nằm trong mục” (trang cha)."""
    seen = set()
    while path is not None and path not in seen:
        seen.add(path)
        for i, it in enumerate(menu_items()):
            if path in menu_members(it):
                return i, it["nhan"]
        path = (getattr(S, "registry", None) or {}).get(path, {}).get("parent")
    return None, ""


def cur(page, href):
    return ' aria-current="page"' if page["path"] == href else ""


def nav_link(ctx, value):
    """Đường dẫn trong menu: giữ kiểu đường dẫn tương đối của site, đồng thời ghi lại để kiểm trang tồn tại."""
    path = p2path(value)
    S.link_refs.append(("content/cai-dat/menu.yml", "Menu chính", path, ""))
    return ctx.r + path


def nav_html(page, ctx):
    items = []
    active_idx, _ = section_of(page["path"])
    menu = menu_items()
    for idx, it in enumerate(menu):
        label = esc(it["nhan"])
        href = p2path(it.get("trang"))
        cls = "nav__link" + (" is-active" if idx == active_idx else "")
        if it.get("loai") == "lien_ket":
            items.append(f'<li class="nav__item"><a class="{cls}" href="{nav_link(ctx, it.get("trang"))}"{cur(page, href)}>{label}</a></li>')
            continue
        sid = "sub-" + (M.slugify(it["nhan"]) or str(idx))
        if it.get("loai") == "menu_linh_vuc":
            links = ""
            for g in it["nhom"]:
                group_links = "".join(
                    f'<li><a class="nav__sublink" href="{ctx.r}dich-vu/{s["slug"]}/"{cur(page, "dich-vu/" + s["slug"] + "/")}>'
                    f'{ico(s["bieu_tuong"], "nav__subicon")}<span>{esc(s["ten"])}</span></a></li>'
                    for slug in g["linh_vuc"] for s in [S.service_by_slug[slug]])
                links += f'<li class="nav__group"><p class="nav__group-title">{esc(g["ten_nhom"])}</p><ul>{group_links}</ul></li>'
            links += (f'<li class="nav__suball"><a href="{nav_link(ctx, it.get("trang"))}"{cur(page, href)}>'
                      f'{esc(it.get("nhan_tat_ca") or "Tất cả")} {ARROW}</a></li>')
            sub_cls = "nav__sub nav__sub--mega"
        else:
            links = "".join(
                f'<li><a class="nav__sublink" href="{nav_link(ctx, x.get("trang"))}"{cur(page, p2path(x.get("trang")))}>'
                f'<span>{esc(x["nhan"])}<small>{esc(x.get("mo_ta") or "")}</small></span></a></li>' for x in it.get("muc_con") or [])
            sub_cls = "nav__sub"
        if idx >= (len(menu) + 1) // 2:  # menu xổ ở nửa phải: căn theo mép phải để không tràn màn hình
            sub_cls += " nav__sub--right"
        items.append(
            f'<li class="nav__item has-sub"><button class="{cls} nav__toggle" type="button" '
            f'aria-expanded="false" aria-controls="{sid}"><span>{label}</span>{ico("i-chevron")}</button>'
            f'<ul class="{sub_cls}" id="{sid}">{links}</ul></li>')
    return "\n        ".join(items)


def logo_html(r, tag=None):
    """Có tag: tên ngắn viết hoa + khẩu hiệu (chân trang). Không tag: "Công Ty Luật TNHH / Luật Sư Nam" (đầu trang)."""
    f = F()
    pre = f["legal_name"][: -len(f["short_name"])].strip() if f["legal_name"].endswith(f["short_name"]) else f["legal_name"]
    text = (f'<span class="logo__name">{esc(f["short_name"].upper())}</span> <span class="logo__tag">{esc(tag)}</span>' if tag else
            f'<span class="logo__pre">{esc(pre)}</span> <span class="logo__name logo__name--firm">{esc(f["short_name"])}</span>')
    return f"""<a class="logo" href="{r or './'}">
      <img class="logo__img" src="{r}{asset_ref("assets/img/logo-lsn-108.webp")}" srcset="{r}{asset_ref("assets/img/logo-lsn.webp")} 3x" width="54" height="54" alt="">
      <span class="logo__text">{text}<span class="sr-only"> – Trang chủ</span></span>
    </a>"""


def header_html(page, ctx):
    f, r = F(), ctx.r
    return f"""<header class="header site-header" id="site-header">
  <div class="container header__inner">
    {logo_html(r)}

    <nav class="nav" id="nav" aria-label="Điều hướng chính">
      <ul class="nav__list">
        {nav_html(page, ctx)}
      </ul>
      <div class="nav__mobile-extra">
        <a class="btn btn--primary btn--block" href="tel:{f["phone_tel"]}">{ico("i-phone")} Gọi {esc(f["phone"])}</a>
        <a class="btn btn--zalo btn--block" href="{esc(f["zalo"])}" target="_blank" rel="noopener">{ico("i-chat")} Nhắn Zalo cho luật sư</a>
        <p class="nav__note">{ico("i-clock")}{esc(f["hours"])}</p>
        <p class="nav__note">{tpl.open_now()}</p>
      </div>
    </nav>

    <div class="header__actions">
      <button class="header__search" type="button" aria-label="Tìm kiếm trên website" aria-haspopup="dialog" data-open-search>{ico("i-search")}<span>Tìm kiếm</span></button>
      <a class="header__call" href="tel:{f["phone_tel"]}" aria-label="Gọi tư vấn {esc(f["phone"])}">{ico("i-phone")}<span><small>Gọi tư vấn</small><strong>{esc(f["phone"])}</strong></span></a>
      <button class="icon-btn burger" type="button" aria-label="Mở menu" aria-expanded="false" aria-controls="nav" id="burger">{ico("i-menu", "")}</button>
    </div>
  </div>
</header>"""


def footer_html(ctx):
    f, r, m = F(), ctx.r, S.menu
    c = ctx.at(src="content/cai-dat/menu.yml", where="Cột liên kết ở chân trang")
    cols = m.get("tieu_de_cot") or {}
    # Thứ tự riêng cho chân trang (Cài đặt chung → Menu và chân trang); lĩnh vực chưa xếp nằm cuối theo ô "Thứ tự"
    pick = [x for x in dict.fromkeys(m.get("linh_vuc_chan_trang") or []) if x in S.service_by_slug]
    ordered = [S.service_by_slug[x] for x in pick] + [s for s in S.services if s["slug"] not in pick]
    services = "".join(f'<li><a href="{r}dich-vu/{s["slug"]}/">{esc(s["ten"])}</a></li>' for s in ordered)
    about_links = "".join(f'<li><a href="{tpl.link_href(c, x)}">{esc(x["nhan"])}</a></li>' for x in m.get("chan_trang") or [])
    legal = "".join(f'<a href="{tpl.link_href(c.at(where="Liên kết cuối chân trang"), x)}">{esc(x["nhan"])}</a>' for x in m.get("lien_ket_phap_ly") or [])
    about = M.inline(f["footer_about"], ctx.at(src="content/cai-dat/cong-ty.yml", where="Giới thiệu ngắn ở chân trang"))
    disclaimer = M.inline(S.text.get("mien_tru_chan_trang"), ctx.at(src="content/cai-dat/cau-chu.yml", where="Miễn trừ trách nhiệm ở chân trang"))
    return f"""<footer class="footer site-footer">
  <div class="container footer__grid">
    <div class="footer__brand">
      {logo_html(r, f["slogan"])}
      <p class="footer__about">{about}</p>
      <div class="social">
        <a href="{esc(f["zalo"])}" target="_blank" rel="noopener" aria-label="Nhắn Zalo {esc(f["phone"])}" class="social__zalo">Zalo</a>
        <a href="tel:{f["phone_tel"]}" aria-label="Gọi {esc(f["phone"])}">{ico("i-phone", "")}</a>
        <a href="mailto:{esc(f["email"])}" aria-label="Gửi email">{ico("i-mail", "")}</a>
        <a href="https://www.google.com/maps/search/?api=1&amp;query={f["maps_query"]}" target="_blank" rel="noopener" aria-label="Mở bản đồ văn phòng">{ico("i-pin", "")}</a>
      </div>
    </div>

    <div>
      <h2 class="footer__title">{esc(cols.get("ve_chung_toi") or "Về chúng tôi")}</h2>
      <ul class="footer__links">
        {about_links}
      </ul>
    </div>

    <div>
      <h2 class="footer__title">{esc(cols.get("linh_vuc") or "Lĩnh vực hoạt động")}</h2>
      <ul class="footer__links">{services}</ul>
    </div>

    <div>
      <h2 class="footer__title">{esc(cols.get("van_phong") or "Văn phòng")}</h2>
      <ul class="footer__contact">
        <li>{ico("i-pin")}<span>{esc(f["street"])},<br>{esc(f["ward"])},<br>{esc(f["city"])}</span></li>
        <li>{ico("i-phone")}<a href="tel:{f["phone_tel"]}">{esc(f["phone"])}</a></li>
        <li>{ico("i-mail")}<a href="mailto:{esc(f["email"])}">{esc(f["email"])}</a></li>
        <li>{ico("i-clock")}<span>{esc(f["hours"])}</span></li>
      </ul>
    </div>
  </div>
  <div class="footer__disclaimer">
    <div class="container">
      <p>{disclaimer}</p>
    </div>
  </div>
  <div class="footer__bottom">
    <div class="container footer__bottom-inner">
      <p>© <span data-year>{TODAY[:4]}</span> {esc(f["legal_name"])}.</p>
      <p class="footer__legal">{legal}</p>
    </div>
  </div>
</footer>"""


def overlays_html(ctx):
    f, r = F(), ctx.r
    c = ctx.at(src="content/cai-dat/menu.yml", where="Gợi ý trong ô tìm kiếm")
    hints = "\n      ".join(f'<a href="{tpl.link_href(c, x)}">{esc(x["nhan"])}</a>' for x in S.menu.get("goi_y_tim_kiem") or [])
    return f"""<div class="floating">
  <a class="floating__btn floating__btn--zalo" href="{esc(f["zalo"])}" target="_blank" rel="noopener" aria-label="Nhắn Zalo {esc(f["phone"])}">Zalo</a>
  <a class="floating__btn floating__btn--phone" href="tel:{f["phone_tel"]}" aria-label="Gọi hotline {esc(f["phone"])}">{ico("i-phone", "")}</a>
  <button class="floating__btn floating__btn--top" type="button" aria-label="Lên đầu trang" id="to-top">{ico("i-up", "")}</button>
</div>

<nav class="actionbar" aria-label="Liên hệ nhanh với luật sư">
  <a class="actionbar__call" href="tel:{f["phone_tel"]}">{ico("i-phone", "")}<span>Gọi luật sư</span></a>
  <a class="actionbar__zalo" href="{esc(f["zalo"])}" target="_blank" rel="noopener">{ico("i-chat", "")}<span>Nhắn Zalo</span></a>
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
      {hints}
    </p>
  </div>
</div>"""


# ---------------------------------------------------------------------------
# Đầu trang con, dữ liệu có cấu trúc, khung trang
# ---------------------------------------------------------------------------
def page_hero_html(page, ctx):
    """Đầu trang con dùng chung: đường dẫn, tiêu đề, mô tả; bên phải là thẻ luật sư phụ trách."""
    h = page.get("hero") or {}
    aside = tpl.lawyer_card(ctx.r) if page.get("lawyer_card", True) else ""
    lead = f'<p class="phead__lead">{page["lead"]}</p>' if page.get("lead") else ""
    eyebrow = f'<p class="eyebrow">{page["eyebrow"]}</p>' if page.get("eyebrow") else ""
    actions = f'<div class="phead__actions">{h["actions"]}</div>' if h.get("actions") else ""
    return f"""<section class="phead{' phead--aside' if aside else ''}">
  <div class="container phead__grid">
    <div class="phead__copy">
      {tpl.breadcrumb_html(page["crumbs"], ctx.r)}
      {eyebrow}
      <h1 class="phead__title">{page["h1"]}</h1>
      {lead}
      {h.get("extra", "")}
      {actions}
    </div>
    {aside}
  </div>
</section>"""


def org_node():
    f = F()
    days = f["open_days"]
    return {
        "@type": "LegalService", "@id": ORG_ID, "name": f["legal_name"],
        "alternateName": [f["short_name"], f["brand"]], "slogan": f["slogan"], "url": ENV["site_url"] + "/",
        "logo": {"@type": "ImageObject", "url": abs_url("assets/img/icon-512.png"), "width": 512, "height": 512},
        "image": abs_url(asset_ref("assets/img/og-image.jpg")),
        "description": S.seo.get("mo_ta_to_chuc") or "",
        "telephone": f["phone_intl"], "email": f["email"], "priceRange": "Theo thỏa thuận",
        "address": {"@type": "PostalAddress", "streetAddress": f["street"], "addressLocality": f["ward"],
                    "addressRegion": f["city"], "addressCountry": "VN"},
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification", "dayOfWeek": days,
                                       "opens": f["opens"], "closes": f["closes"]}],
        "areaServed": [{"@type": "City", "name": "Thành phố Hồ Chí Minh"}, {"@type": "Country", "name": "Việt Nam"}],
        "knowsLanguage": ["vi"], "sameAs": [f["zalo"]],
        "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Lĩnh vực hoạt động",
                            "itemListElement": [{"@type": "Offer", "itemOffered": {"@id": abs_url(f"dich-vu/{s['slug']}/") + "#service"}}
                                                for s in S.services]},
    }


def jsonld(page):
    url = abs_url(page["path"])
    org = org_node()
    if page["path"] not in ("", "lien-he/", "gioi-thieu/"):
        org = {k: org[k] for k in ("@type", "@id", "name", "alternateName", "url", "logo", "image", "telephone", "email", "address")}
    graph = [org, {"@type": "WebSite", "@id": SITE_ID, "url": ENV["site_url"] + "/", "name": f'{F()["short_name"]} – {F()["brand"]}',
                   "inLanguage": "vi", "publisher": {"@id": ORG_ID}}]
    webpage = {
        "@type": page.get("schema_type", "WebPage"), "@id": url + "#webpage", "url": url,
        "name": page["title"], "description": page["description"], "inLanguage": "vi",
        "isPartOf": {"@id": SITE_ID}, "about": {"@id": ORG_ID},
        "primaryImageOfPage": {"@type": "ImageObject", "url": page["og_abs"]},
        "dateModified": page.get("modified", TODAY),
    }
    if page["path"]:
        webpage["breadcrumb"] = {"@id": url + "#breadcrumb"}
        graph.append({"@type": "BreadcrumbList", "@id": url + "#breadcrumb",
                      "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": abs_url(p)}
                                          for i, (n, p) in enumerate(page["crumbs"])]})
    webpage.update(page.get("webpage_extra", {}))
    graph.append(webpage)
    graph.extend(page.get("schema", []))
    data = {"@context": "https://schema.org", "@graph": graph}
    return json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")


def tracking_head(page):
    t = S.tracking
    out = ""
    if page["path"] == "" and t.get("search_console"):
        out += f'\n<meta name="google-site-verification" content="{esc(t["search_console"])}">'
    if not t.get("da_cap_nhat_chinh_sach") or ENV["noindex"]:
        return out
    if t.get("ga4"):
        g = t["ga4"]
        out += (f'\n<script async src="https://www.googletagmanager.com/gtag/js?id={g}"></script>'
                f"\n<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{g}');</script>")
    if t.get("meta_pixel"):
        px = t["meta_pixel"]
        out += ("\n<script>!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};"
                "if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;"
                "s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');"
                f"fbq('init','{px}');fbq('track','PageView');</script>")
    return out


def tracking_body():
    t = S.tracking
    if t.get("da_cap_nhat_chinh_sach") and t.get("zalo_oa") and not ENV["noindex"]:
        return (f'\n<div class="zalo-chat-widget" data-oaid="{t["zalo_oa"]}" data-welcome-message="Luật sư có thể giúp gì cho anh chị?" data-autopopup="0"></div>'
                '\n<script src="https://sp.zalo.me/plugins/sdk.js" defer></script>')
    return ""


def gio_attr():
    """Ngày + giờ làm việc cho main.js (trạng thái Đang trong giờ làm việc)."""
    f = F()
    days = ",".join(str(content.DAY_NUM[d]) for d in f["open_days"])

    def mins(t):
        h, m = (int(x) for x in t.split(":"))
        return h * 60 + m
    return f"{days}|{mins(f['opens'])}|{mins(f['closes'])}"


def layout(page):
    r = page.get("root_override", root_of(page["path"]))
    ctx = Ctx(S, r, page["path"], page.get("src", ""))
    css_v, js_v = file_hash("assets/css/style.css"), file_hash("assets/js/main.js")
    url = abs_url(page["path"])
    noindex = page.get("noindex") or ENV["noindex"]
    robots = "noindex, follow" if noindex else "index, follow, max-image-preview:large, max-snippet:-1"
    og_type = page.get("og_type", "website")
    art_meta = ""
    if og_type == "article":
        art_meta = (f'\n<meta property="article:published_time" content="{page["published"]}">'
                    f'\n<meta property="article:modified_time" content="{page["modified"]}">'
                    f'\n<meta property="article:section" content="{esc(page["article_section"])}">')
    hero = page_hero_html(page, ctx) if page.get("page_hero", True) else ""
    band = tpl.contact_band(ctx, page.get("cband_override"), page.get("cband")) if page.get("contact_band", True) else ""
    draft = ""
    if page.get("is_draft"):
        draft = ('\n<div class="draft-banner" role="note"><strong>BẢN NHÁP</strong> – chỉ để duyệt nội dung, chưa đăng lên website chính thức. '
                 'Bỏ dấu “Bản nháp” trong /admin khi đã duyệt.</div>')
    canonical = "" if page.get("noindex") else f'\n<link rel="canonical" href="{url}">'
    base_js = ""
    if page.get("dynamic_base"):
        # Trang 404 được phục vụ ở mọi độ sâu đường dẫn: xác định thư mục gốc khi chạy để tài nguyên tải đúng
        base_js = ('\n<script>(function(){var p="' + ENV["base_path"] + '",b=document.createElement("base");'
                   'b.href=location.pathname.indexOf(p)===0?p:"/";document.head.appendChild(b);})();</script>')
    og_title = page.get("og_title", page["title"])
    og_w, og_h = page.get("og_size", (1200, 630))
    return f"""<!doctype html>
<html lang="vi" data-root="{r}" data-gio="{gio_attr()}">
<head>
<meta charset="utf-8">{base_js}
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(page["title"])}</title>
<meta name="description" content="{esc(page["description"])}">
<meta name="robots" content="{robots}">{canonical}
<meta name="author" content="{esc(F()["legal_name"])}">
<meta name="theme-color" content="#fffdf9">
<meta name="format-detection" content="telephone=no">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(F()["legal_name"])}">
<meta property="og:locale" content="vi_VN">
<meta property="og:title" content="{esc(og_title)}">
<meta property="og:description" content="{esc(page["description"])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{page["og_abs"]}">
<meta property="og:image:width" content="{og_w}">
<meta property="og:image:height" content="{og_h}">
<meta property="og:image:alt" content="{esc(og_title)} – {esc(F()["lawyer"])}">{art_meta}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(og_title)}">
<meta name="twitter:description" content="{esc(page["description"])}">
<meta name="twitter:image" content="{page["og_abs"]}">
<link rel="icon" href="{r}assets/img/favicon-32.png" sizes="32x32" type="image/png">
<link rel="icon" href="{r}assets/img/icon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="{r}assets/img/apple-touch-icon.png">
<link rel="manifest" href="{r}site.webmanifest">
<link rel="preload" href="{r}assets/fonts/be-vietnam-pro-400-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{r}assets/fonts/be-vietnam-pro-400-normal-vietnamese.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{r}assets/css/style.css?v={css_v}">{tracking_head(page)}
<script type="application/ld+json">
{jsonld(page)}
</script>
</head>
<body{f' class="{page["body_class"]}"' if page.get("body_class") else ""}>
<a class="skip-link" href="#main">Bỏ qua đến nội dung chính</a>
{SPRITE}
{header_html(page, ctx)}
{draft}
<main id="main">
{hero}
{page["body"]}
{band}
</main>

{footer_html(ctx)}

{overlays_html(ctx)}

<script src="{r}assets/js/main.js?v={js_v}" defer></script>{tracking_body()}
</body>
</html>
"""


def file_hash(rel):
    import hashlib
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()[:8]


# ---------------------------------------------------------------------------
# Tiêu đề, ảnh chia sẻ
# ---------------------------------------------------------------------------
HOME = ("Trang chủ", "")


def full_title(seo_title, path):
    short = F()["short_name"]
    if path == "":
        return f'{F()["legal_name"]} | {seo_title}'
    return seo_title if seo_title.endswith(short) else f"{seo_title} | {short}"


def check_title(src, title):
    if len(title) < 30:
        LOI.them(src, "SEO › Tiêu đề trên Google", f"Tiêu đề đầy đủ “{title}” chỉ {len(title)} ký tự, cần ít nhất 30 để Google hiển thị rõ.")


def og_for(seo, default_rel, job=None):
    """Ảnh chia sẻ: ảnh tải riêng (nếu có) hoặc ảnh tự tạo từ tiêu đề; trả về (đường dẫn tuyệt đối, kích thước)."""
    if seo and seo.get("anh_chia_se"):
        p = seo["anh_chia_se"]
        size = S.image_size(p) or (1200, 630)
        return abs_url(p.lstrip("/")), size, p.lstrip("/")
    if job:
        IMG.og(*job)
    return abs_url(asset_ref(default_rel)), (1200, 630), default_rel


def lead_text(text, ctx):
    return M.plain(text, ctx) if text else ""


# ---------------------------------------------------------------------------
# Trang dựng từ khối
# ---------------------------------------------------------------------------
def crumbs_for_page(p, path):
    crumbs = [HOME]
    parent = p2path(p.get("trang_cha")) if p.get("trang_cha") else None
    seen = set()
    while parent and parent not in seen and parent in S.registry and parent != path:
        seen.add(parent)
        crumbs.insert(1, (S.registry[parent]["label"], parent))
        parent = S.registry[parent].get("parent")
    return crumbs + [(p["tieu_de"], path)]


def block_page(p):
    slug = p["slug"]
    path = "" if slug == content.HOME_SLUG else f"{slug}/"
    ctx = Ctx(S, root_of(path), path, p["_src"])
    visible = [b for b in p.get("cac_khoi") or [] if b.get("hien_thi", True)]
    has_hero = bool(visible) and visible[0]["loai"] == "dau_trang"
    head = p.get("dau_trang") or {}
    hc = ctx.at(where="Đầu trang tiêu chuẩn")
    page = {"path": path, "src": p["_src"], "crumbs": crumbs_for_page(p, path) if path else [HOME],
            "schema_type": p.get("loai_trang") or "WebPage", "ids": set(), "is_draft": p.get("nhap")}
    page.update({
        "page_hero": not has_hero and path != "",
        "eyebrow": M.plain(head.get("nhan"), hc), "h1": M.title(head.get("tieu_de"), hc), "lead": lead_text(head.get("mo_dau"), hc),
        "lawyer_card": head.get("the_luat_su", True),
    })
    page["body"] = blocks.render(ctx, page, p.get("cac_khoi") or [])
    seo = p.get("seo") or {}
    page["title"] = full_title(seo.get("tieu_de", ""), path)
    check_title(p["_src"], page["title"])
    page["description"] = seo.get("mo_ta", "")
    band = p.get("lien_he_cuoi_trang") or {}
    page["contact_band"] = band.get("hien", True)
    page["cband_override"] = dict(band, _src=p["_src"])
    if path == "":
        page["og_abs"], page["og_size"], page["og_rel"] = og_for(seo, "assets/img/og-image.jpg")
    else:
        title_txt = M.title_text(head.get("tieu_de") or (visible[0].get("tieu_de") if has_hero else p["tieu_de"]), hc)
        job = (f"og/trang-{slug}.jpg", M.expand(head.get("nhan") or F()["short_name"], hc), title_txt,
               M.expand(head.get("mo_dau") or seo.get("mo_ta", ""), hc), "van-phong")
        page["og_abs"], page["og_size"], page["og_rel"] = og_for(seo, f"assets/img/{job[0]}", job)
    return page


# ---------------------------------------------------------------------------
# Trang lĩnh vực
# ---------------------------------------------------------------------------
def service_page(s):
    path = f"dich-vu/{s['slug']}/"
    r = root_of(path)
    name_lc = s["ten"].lower()
    ctx = Ctx(S, r, path, s["_src"], extra={"ten_linh_vuc": name_lc})
    T = S.text.get("trang_linh_vuc") or {}
    tc = ctx.at(src="content/cai-dat/cau-chu.yml", where="Trang lĩnh vực")

    def sec(key):
        return T.get(key) or {}

    def P(text, c=tc):
        return M.plain(text, c)
    arts = [a for a in S.articles if s["slug"] in a["linh_vuc_lien_quan"]]
    situations = "".join(f'<li>{ico("i-check-circle")}<span>{P(x, ctx)}</span></li>' for x in s.get("tinh_huong") or [])
    pv = s.get("pham_vi") or {}
    scope = "".join(f'<article class="ncard ncard--num reveal"><div class="ncard__top"><span class="ncard__num">{i:02d}</span></div>'
                    f'<h3>{P(x["tieu_de"], ctx)}</h3><p>{P(x["mo_ta"], ctx)}</p></article>' for i, x in enumerate(pv.get("cac_viec") or [], 1))
    tips = "".join(f"<li>{P(x, ctx)}</li>" for x in s.get("viec_nen_lam") or [])
    steps_ = s.get("cac_buoc") or []
    steps = "".join(f'<li class="reveal"><span class="steps__num">{i}</span><h3>{P(x["tieu_de"], ctx)}</h3><p>{P(x["mo_ta"], ctx)}</p></li>'
                    for i, x in enumerate(steps_, 1))
    faq = "".join(f"""<details class="faq__item" id="hoi-dap-{i}"{tpl.cms(s["_src"], f"hoi_dap.{i - 1}", f"Câu hỏi {i}")}>
  <summary><span>{P(x["hoi"], ctx)}</span>{ico("i-chevron", "faq__chev")}</summary>
  <div class="faq__answer">{re.sub(r">\n<", "><", M.block(x["dap"], ctx.at(where=f"Hỏi đáp riêng › Câu hỏi {i}")).strip())}</div>
</details>""" for i, x in enumerate(s.get("hoi_dap") or [], 1))
    laws = "".join(f"<li>{P(x, ctx)}</li>" for x in s.get("can_cu_phap_ly") or [])
    resources = [(f"{r}kien-thuc-phap-ly/{a['slug']}/", "Bài viết", a.get("tieu_de_ngan") or a["tieu_de"], a["tom_tat"]) for a in arts[:3]]
    for x in (T.get("the_bo_sung") or [])[: max(0, 3 - len(resources))]:
        resources.append((tpl.link_href(tc.at(where="Trang lĩnh vực › Thẻ bổ sung"), x.get("lien_ket")), x["nhan"], x["tieu_de"], x["mo_ta"]))
    cards = "".join(f'<a class="rcard reveal" href="{href}"><span class="tag">{esc(label)}</span><h3>{esc(title)}</h3>'
                    f'<p>{esc(text)}</p><span class="icard__more">Xem chi tiết {ARROW}</span></a>' for href, label, title, text in resources)
    related = "".join(tpl.icard(f'{r}dich-vu/{x}/', S.service_by_slug[x]["bieu_tuong"], esc(S.service_by_slug[x]["ten"]),
                                esc(S.service_by_slug[x]["mo_ta_ngan"]),
                                mark=tpl.cms(S.service_by_slug[x]["_src"], "mo_ta_ngan", f'Thẻ {S.service_by_slug[x]["ten"]} (mô tả ngắn)'))
                      for x in s.get("linh_vuc_lien_quan") or [] if x in S.service_by_slug)
    urgent = ""
    if s.get("viec_gap"):
        vg = S.text.get("viec_gap") or {}
        urgent = (f'<p class="urgent">{ico("i-alert")}<span><strong>{P(vg.get("nhan"))}</strong> '
                  f'{M.inline(vg.get("noi_dung"), tc.at(where="Ô Việc gấp"))}</span></p>')
    nav = "".join(f'<a href="#{a}">{P(lbl)}</a>' for a, lbl in zip(["tinh-huong", "pham-vi", "viec-nen-lam", "quy-trinh", "ho-so", "hoi-dap"],
                                                                    T.get("muc_luc") or []))
    th, pvh, vn, qt, hs, hd, tk, lq = (sec(k) for k in ("tinh_huong", "pham_vi", "viec_nen_lam", "quy_trinh", "ho_so", "hoi_dap", "tham_khao", "lien_quan"))
    gt = s.get("giay_to") or {}
    lu, ng = s.get("luu_y") or {}, s.get("nguyen_tac") or {}
    link_qt = tpl.link_href(tc, {"trang": "/quy-trinh-lam-viec/"})
    link_hs = tpl.link_href(tc, {"trang": "/quy-trinh-lam-viec/", "ma_neo": "ho-so-can-chuan-bi"})
    link_cp = tpl.link_href(tc, {"trang": "/cau-hoi-thuong-gap/", "ma_neo": "chi-phi-thue-luat-su"})
    own = lambda key, label: tpl.cms(s["_src"], key, label)  # noqa: E731 – chỉ khung mô phỏng
    shared = lambda key, label: tpl.cms("content/cai-dat/cau-chu.yml", "trang_linh_vuc." + key, label)  # noqa: E731
    body = f"""
<nav class="subnav"{shared("muc_luc", "Thanh mục lục (dùng chung mọi lĩnh vực)")} aria-label="Nội dung trang"><div class="container">{nav}</div></nav>

<section class="section svc-section" id="tinh-huong"{own("tinh_huong", "Tình huống thường gặp")}>
  <div class="container">
    {tpl.shead(P(th.get("nhan")), P(th.get("tieu_de")), P(th.get("mo_ta")))}
    <ul class="situations">{situations}</ul>
    <p class="situations__foot">{M.inline(th.get("cuoi"), tc.at(where="Trang lĩnh vực › Mục Tình huống"))}</p>
  </div>
</section>

<section class="section section--cream svc-section" id="pham-vi"{own("pham_vi", "Luật sư giúp được gì")}>
  <div class="container">
    {tpl.shead(P(pvh.get("nhan")), P(pvh.get("tieu_de")), P(pv.get("gioi_thieu"), ctx))}
    <div class="grid grid--3">{scope}</div>
  </div>
</section>

<section class="section svc-section" id="viec-nen-lam"{own("viec_nen_lam", "Việc nên làm ngay")}>
  <div class="container split">
    <div class="reveal">
      <p class="eyebrow">{P(vn.get("nhan"))}</p>
      <h2 class="h2">{P(vn.get("tieu_de"))}</h2>
      <p class="shead__text">{P(vn.get("mo_ta"))}</p>
      <ol class="tips">{tips}</ol>
    </div>
    <div class="stack">
      <div class="note reveal">{ico("i-alert")}<p><strong>{P(lu.get("tieu_de"), ctx)}:</strong> {P(lu.get("noi_dung"), ctx)}</p></div>
      <article class="context__dark reveal"><p class="eyebrow">{P(vn.get("nhan_nguyen_tac"))}</p><h3>{P(ng.get("tieu_de"), ctx)}</h3><p>{P(ng.get("noi_dung"), ctx)}</p></article>
    </div>
  </div>
</section>

<section class="section section--cream svc-section" id="quy-trinh"{own("cac_buoc", "Các bước làm việc")}>
  <div class="container">
    {tpl.shead(P(qt.get("nhan")), P(qt.get("tieu_de")), P(qt.get("mo_ta")), link=(link_qt, P(qt.get("lien_ket"))))}
    <ol class="steps{" steps--5" if len(steps_) == 5 else ""}">{steps}</ol>
  </div>
</section>

<section class="section svc-section" id="ho-so"{own("giay_to", "Giấy tờ và kết quả nhận được")}>
  <div class="container">
    {tpl.shead(P(hs.get("nhan")), P(hs.get("tieu_de")), P(hs.get("mo_ta")))}
    <div class="docs">
      <article class="reveal"><h3><span class="ichip ichip--sm">{ico("i-doc", "")}</span>{P(gt.get("tieu_de") or "Giấy tờ nên mang theo", ctx)}</h3>{tpl.check_list(gt.get("danh_sach") or [], ctx=ctx)}<a class="link-arrow" href="{link_hs}">{P(hs.get("lien_ket_ho_so"))} {ARROW}</a></article>
      <article class="reveal"><h3><span class="ichip ichip--sm">{ico("i-check-circle", "")}</span>{P(hs.get("tieu_de_nhan_duoc"))}</h3>{tpl.check_list(s.get("nhan_duoc") or [], ctx=ctx)}<a class="link-arrow" href="{link_cp}">{P(hs.get("lien_ket_chi_phi"))} {ARROW}</a></article>
    </div>
  </div>
</section>

<section class="section section--cream svc-section" id="hoi-dap"{own("hoi_dap", "Hỏi đáp")}>
  <div class="container split">
    <div class="reveal">
      <p class="eyebrow">{P(hd.get("nhan"))}</p>
      <h2 class="h2">{P(hd.get("tieu_de"))}</h2>
      <p class="shead__text">{P(hd.get("mo_ta"))}</p>
      <div class="context__laws laws-box"><h3>{P(hd.get("tieu_de_can_cu"))}</h3><ul>{laws}</ul><small>{P(hd.get("ghi_chu_can_cu"))}</small></div>
    </div>
    <div class="faq reveal">{faq}</div>
  </div>
</section>

<section class="section svc-section" id="tham-khao"{shared("tham_khao", "Mục Đọc thêm (tự lấy bài viết của lĩnh vực)")}>
  <div class="container">
    {tpl.shead(P(tk.get("nhan")), P(tk.get("tieu_de")), link=(tpl.link_href(tc, {"trang": "/kien-thuc-phap-ly/"}), P(tk.get("lien_ket"))))}
    <div class="grid grid--3">{cards}</div>
  </div>
</section>
"""
    if related:
        body += f"""
<section class="section section--cream svc-section" id="lien-quan"{own("linh_vuc_lien_quan", "Lĩnh vực liên quan")}>
  <div class="container">
    {tpl.shead(P(lq.get("nhan")), P(lq.get("tieu_de")), link=(tpl.link_href(tc, {"trang": "/dich-vu/"}), P(lq.get("lien_ket"))))}
    <div class="grid grid--3">{related}</div>
  </div>
</section>
"""
    url = abs_url(path)
    seo = s.get("seo") or {}
    og_abs, og_size, og_rel = og_for(seo, f'assets/img/og/dich-vu-{s["slug"]}.jpg',
                                     (f'og/dich-vu-{s["slug"]}.jpg', "Dịch vụ pháp lý", s["ten"], s["mo_ta_ngan"],
                                      "phien-toa" if s["slug"] in COURT else "van-phong"))
    lh = s.get("lien_he") or {}
    title = full_title(seo.get("tieu_de", ""), path)
    check_title(s["_src"], title)
    return {
        "path": path, "src": s["_src"], "is_draft": s.get("nhap"),
        "title": title, "description": seo.get("mo_ta", ""),
        "eyebrow": P(s.get("nhan_dau_trang"), ctx), "h1": M.title(s.get("tieu_de_trang"), ctx), "lead": P(s.get("mo_dau"), ctx),
        "hero": {"extra": urgent},
        "crumbs": [HOME, ("Dịch vụ", "dich-vu/"), (s["ten"], path)],
        "og_abs": og_abs, "og_size": og_size, "og_rel": og_rel, "body": body,
        "cband": {"nhan": M.expand(T.get("nhan_lien_he") or "", ctx), "tieu_de": lh.get("tieu_de"), "doan_moi": lh.get("doan_moi")},
        "schema": [{
            "@type": "Service", "@id": url + "#service", "name": s["ten"], "serviceType": seo.get("tieu_de", ""),
            "description": seo.get("mo_ta", ""), "url": url, "provider": {"@id": ORG_ID},
            "areaServed": [{"@type": "City", "name": "Thành phố Hồ Chí Minh"}, {"@type": "Country", "name": "Việt Nam"}],
            "image": og_abs,
        }],
        "webpage_extra": {"mainEntity": {"@id": url + "#service"}},
    }


# ---------------------------------------------------------------------------
# Trang tổng hợp
# ---------------------------------------------------------------------------
def hub_head(page, d, ctx):
    head = d.get("dau_trang") or {}
    c = ctx.at(where="Đầu trang")
    page.update({"eyebrow": M.plain(head.get("nhan"), c), "h1": M.title(head.get("tieu_de"), c),
                 "lead": lead_text(head.get("mo_dau"), c), "lawyer_card": head.get("the_luat_su", True)})
    band = d.get("lien_he_cuoi_trang") or {}
    page["contact_band"] = band.get("hien", True)
    page["cband_override"] = dict(band, _src=d["_src"])
    seo = d.get("seo") or {}
    page["title"] = full_title(seo.get("tieu_de", ""), page["path"])
    check_title(d["_src"], page["title"])
    page["description"] = seo.get("mo_ta", "")
    page["og_abs"], page["og_size"], page["og_rel"] = og_for(seo, "assets/img/og-image.jpg")
    return page


def services_hub():
    d = S.hubs["dich_vu"]
    path = "dich-vu/"
    ctx = Ctx(S, root_of(path), path, d["_src"])
    lw, ht = d.get("luoi") or {}, d.get("hinh_thuc") or {}
    mode_html = "".join(f'<article class="icard reveal"><span class="ichip">{ico(x["bieu_tuong"], "")}</span><h3 class="icard__title">{M.plain(x["tieu_de"], ctx)}</h3>'
                        f'<p class="icard__text">{M.plain(x["mo_ta"], ctx)}</p></article>' for x in ht.get("the") or [])
    body = f"""
<section class="section section--cream"{tpl.cms(d["_src"], "luoi", "Khối lưới lĩnh vực")}>
  <div class="container">
    {tpl.shead(M.plain(lw.get("nhan"), ctx), M.plain(lw.get("tieu_de"), ctx), M.plain(lw.get("mo_ta"), ctx))}
    {tpl.problems_grid(ctx.r)}
  </div>
</section>

<section class="section"{tpl.cms(d["_src"], "hinh_thuc", "Khối “Hình thức hỗ trợ”")}>
  <div class="container">
    {tpl.shead(M.plain(ht.get("nhan"), ctx), M.plain(ht.get("tieu_de"), ctx), M.plain(ht.get("mo_ta"), ctx), center=True)}
    <div class="grid grid--3">{mode_html}</div>
  </div>
</section>
"""
    page = {"path": path, "src": d["_src"], "schema_type": "CollectionPage", "crumbs": [HOME, ("Lĩnh vực hoạt động", path)], "body": body,
            "webpage_extra": {"mainEntity": {
                "@type": "ItemList", "numberOfItems": len(S.services),
                "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": abs_url(f"dich-vu/{s['slug']}/"), "name": s["ten"]}
                                    for i, (s, _, _) in enumerate(tpl.grid_cards())]}}}
    return hub_head(page, d, ctx)


def knowledge_hub():
    d = S.hubs["kien_thuc"]
    path = "kien-thuc-phap-ly/"
    ctx = Ctx(S, root_of(path), path, d["_src"])
    bv, tl = d.get("bai_viet") or {}, d.get("theo_linh_vuc") or {}
    tools_html = []
    for n, x in enumerate(d.get("the_cong_cu") or []):
        dark = n == 0
        tools_html.append(f"""<a class="tool-card{" tool-card--dark" if dark else ""} reveal" href="{tpl.link_href(ctx.at(where="Hai thẻ lớn giữa trang"), x.get("lien_ket"))}">
      <span class="ichip">{ico(x["bieu_tuong"], "")}</span>
      <span class="eyebrow">{M.plain(x.get("nhan"), ctx)}</span>
      <h2 class="tool-card__title">{M.plain(x["tieu_de"], ctx)}</h2>
      <p>{M.plain(x.get("mo_ta"), ctx)}</p>
      <span class="link-arrow{" link-arrow--light" if dark else ""}">{M.plain((x.get("lien_ket") or {}).get("nhan"), ctx)} {ARROW}</span>
    </a>""")
    tl_link = tl.get("lien_ket")
    body = f"""
<section class="section section--cream"{tpl.cms(d["_src"], "bai_viet", "Khối danh sách bài viết")}>
  <div class="container">
    {tpl.shead(M.plain(bv.get("nhan"), ctx), M.plain(bv.get("tieu_de"), ctx), M.plain(bv.get("mo_ta"), ctx))}
    {tpl.articles_grid(ctx.r)}
  </div>
</section>

<section class="section"{tpl.cms(d["_src"], "the_cong_cu", "Hai thẻ lớn giữa trang")}>
  <div class="container grid grid--2">
    {(chr(10) + "    ").join(tools_html)}
  </div>
</section>

<section class="section section--cream"{tpl.cms(d["_src"], "theo_linh_vuc", "Khối “Theo lĩnh vực”")}>
  <div class="container">
    {tpl.shead(M.plain(tl.get("nhan"), ctx), M.plain(tl.get("tieu_de"), ctx), M.plain(tl.get("mo_ta"), ctx),
               link=(tpl.link_href(ctx, tl_link), M.plain(tl_link.get("nhan"), ctx)) if tl_link else None)}
    {tpl.problems_grid(ctx.r)}
  </div>
</section>
"""
    page = {"path": path, "src": d["_src"], "schema_type": "CollectionPage", "crumbs": [HOME, ("Kiến thức pháp lý", path)], "body": body,
            "webpage_extra": {"mainEntity": {
                "@type": "ItemList", "numberOfItems": len(S.articles),
                "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": abs_url(f"kien-thuc-phap-ly/{a['slug']}/"), "name": a["tieu_de"]}
                                    for i, a in enumerate(S.articles)]}}}
    return hub_head(page, d, ctx)


def faq_page():
    d = S.hubs["hoi_dap"]
    path = "cau-hoi-thuong-gap/"
    ctx = Ctx(S, root_of(path), path, d["_src"])
    aside = "\n          ".join(f'<li><a href="{tpl.link_href(ctx.at(where="Cột Tìm hiểu thêm"), x)}">{ico(x["bieu_tuong"], "rel-list__icon")}'
                               f'<span>{M.plain(x["nhan"], ctx)}</span>{ARROW}</a></li>' for x in d.get("tim_hieu_them") or [])
    foot = M.inline(d.get("ghi_chu_cuoi"), ctx.at(where="Ghi chú dưới danh sách câu hỏi"))
    body = f"""
<section class="section">
  <div class="container faq-layout">
    <div>{tpl.faq_list(ctx, mark=tpl.cms("content/hoi-dap.yml", "cau_hoi", "Danh sách câu hỏi (Kho câu hỏi dùng chung)"))}
      {f'<p class="faq__foot"{tpl.cms(d["_src"], "ghi_chu_cuoi", "Ghi chú dưới danh sách câu hỏi")}>{foot}</p>' if foot else ""}
    </div>
    <aside class="faq-aside"{tpl.cms(d["_src"], "tim_hieu_them", "Cột “Tìm hiểu thêm”")}>
      <div class="aside-card">
        <p class="aside-card__title">Tìm hiểu thêm</p>
        <ul class="rel-list">
          {aside}
        </ul>
      </div>
    </aside>
  </div>
</section>
"""
    qa = []
    for f in S.faq:
        qa.append({"@type": "Question", "name": f["hoi"],
                   "acceptedAnswer": {"@type": "Answer", "text": M.to_text(f["dap"], ctx.at(src="content/hoi-dap.yml"))}})
    page = {"path": path, "src": d["_src"], "schema_type": "FAQPage",
            "crumbs": [HOME, ("Kiến thức pháp lý", "kien-thuc-phap-ly/"), ("Câu hỏi thường gặp", path)], "body": body,
            "webpage_extra": {"mainEntity": qa}}
    return hub_head(page, d, ctx)


# ---------------------------------------------------------------------------
# Bài viết
# ---------------------------------------------------------------------------
def article_page(a):
    path = f"kien-thuc-phap-ly/{a['slug']}/"
    r = root_of(path)
    ctx = Ctx(S, r, path, a["_src"], where="Nội dung bài viết")
    svc = S.service_by_slug.get(a["linh_vuc"]) or {"slug": a["linh_vuc"], "ten": "", "mo_ta_ngan": "", "bieu_tuong": "i-doc",
                                                    "lien_he": {}}
    tb = S.text.get("bai_viet") or {}
    tc = ctx.at(src="content/cai-dat/cau-chu.yml", where="Trang bài viết")
    toc_items = []
    lead = f'<p class="prose__lead">{M.plain(a.get("doan_dan"), ctx.at(where="Đoạn dẫn đầu bài"))}</p>'
    content_html = lead + "\n\n" + M.block(a.get("body"), ctx, toc=toc_items)
    toc = "".join(f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in toc_items)
    words = len(M.strip_tags(content_html).split())
    minutes = max(1, round(words / 220))
    others = [x for x in S.articles if x["slug"] != a["slug"]][:4]
    related_svcs = "".join(
        f'<li><a href="{r}dich-vu/{x}/">{ico(S.service_by_slug[x]["bieu_tuong"], "rel-list__icon")}<span>{esc(S.service_by_slug[x]["ten"])}</span>{ARROW}</a></li>'
        for x in a["linh_vuc_lien_quan"] if x in S.service_by_slug)
    points = "".join(f"<li>{M.plain(p, ctx)}</li>" for p in a.get("tom_tat_nhanh") or [])
    keypoints = f'<div class="keypoints"><p class="keypoints__title">{ico("i-list")}Tóm tắt nhanh</p><ul>{points}</ul></div>' if points else ""
    pub, mod = a["ngay_dang"], a["ngay_cap_nhat"]
    extra = f"""<p class="article-meta">
        <span>{ico("i-user")}{M.plain(tb.get("tac_gia"), tc)}</span>
        <span>{ico("i-calendar")}Đăng <time datetime="{pub}">{tpl.vi_date(pub)}</time></span>
        <span>{ico("i-clock")}Cập nhật <time datetime="{mod}">{tpl.vi_date(mod)}</time> · {minutes} phút đọc</span>
        <button class="share-btn" type="button" data-share>{ico("i-share")}Chia sẻ bài viết</button>
      </p>"""
    body = f"""
<section class="section">
  <div class="container article-layout">
    <article class="prose" id="noi-dung-bai-viet">
      <details class="toc-mobile">
        <summary>{ico("i-list")}<span>Mục lục bài viết</span><small>{len(toc_items)} mục</small>{ico("i-chevron", "toc-mobile__chev")}</summary>
        <ol class="toc">{toc}</ol>
      </details>
      {keypoints}
      {content_html}
      <div class="article-disclaimer">
        {ico("i-alert", "note__icon")}
        <p>{M.inline(S.text.get("mien_tru_cuoi_bai"), tc.at(where="Lưu ý cuối mỗi bài viết"))}</p>
      </div>
    </article>
    <aside class="article-aside">
      <div class="aside-card aside-card--toc">
        <p class="aside-card__title">Nội dung bài viết</p>
        <ol class="toc">{toc}</ol>
      </div>
      <div class="aside-card aside-card--cta">
        <div class="aside-card__who"><img src="{r}{asset_ref("assets/img/luat-su-avatar.webp")}" alt="" width="52" height="52" loading="lazy" decoding="async"><div><strong>{esc(F()["lawyer"])}</strong><small>Trực tiếp tiếp nhận hồ sơ</small></div></div>
        <p class="aside-card__title">Cần luật sư về {esc(svc["ten"].lower())}?</p>
        <p>{esc(svc["mo_ta_ngan"])}</p>
        <a class="btn btn--primary btn--block btn--sm" href="tel:{F()["phone_tel"]}">{ico("i-phone")} Gọi {esc(F()["phone"])}</a>
        <a class="btn btn--light btn--block btn--sm" href="{r}dich-vu/{svc["slug"]}/">Xem dịch vụ {esc(svc["ten"])}</a>
      </div>
      <div class="aside-card">
        <p class="aside-card__title">Lĩnh vực liên quan</p>
        <ul class="rel-list">{related_svcs}</ul>
      </div>
    </aside>
  </div>
</section>
"""
    if others:
        body += f"""
<section class="section section--cream">
  <div class="container">
    {tpl.shead(M.plain(tb.get("doc_tiep_nhan"), tc), M.plain(tb.get("doc_tiep_tieu_de"), tc), link=(f"{r}kien-thuc-phap-ly/", "Tất cả bài viết"))}
    {tpl.articles_grid(r, others, cls="grid grid--2")}
  </div>
</section>
"""
    url = abs_url(path)
    seo = a.get("seo") or {}
    card_title = a.get("tieu_de_ngan") or a["tieu_de"]
    og_abs, og_size, og_rel = og_for(seo, f'assets/img/og/bai-viet-{a["slug"]}.jpg',
                                     (f'og/bai-viet-{a["slug"]}.jpg', svc["ten"], card_title, a["tom_tat"], "van-phong"))
    lh = svc.get("lien_he") or {}
    title = full_title(seo.get("tieu_de", ""), path)
    check_title(a["_src"], title)
    return {
        "path": path, "src": a["_src"], "is_draft": a.get("nhap"), "og_type": "article", "lawyer_card": False,
        "published": pub, "modified": mod, "article_section": svc["ten"],
        "title": title, "og_title": a["tieu_de"], "description": seo.get("mo_ta", ""),
        "eyebrow": esc(svc["ten"]), "h1": esc(a["tieu_de"]),
        "crumbs": [HOME, ("Kiến thức pháp lý", "kien-thuc-phap-ly/"), (card_title, path)],
        "og_abs": og_abs, "og_size": og_size, "og_rel": og_rel, "hero": {"extra": extra}, "body": body,
        "cband": {"nhan": f"Tư vấn {svc['ten'].lower()}", "tieu_de": lh.get("tieu_de"), "doan_moi": lh.get("doan_moi")},
        "schema": [{
            "@type": "Article", "@id": url + "#article", "headline": a["tieu_de"], "description": seo.get("mo_ta", ""),
            "image": og_abs, "datePublished": pub, "dateModified": mod, "inLanguage": "vi", "articleSection": svc["ten"],
            "wordCount": words, "author": {"@id": ORG_ID}, "publisher": {"@id": ORG_ID},
            "mainEntityOfPage": {"@id": url + "#webpage"},
            "about": {"@id": abs_url(f'dich-vu/{a["linh_vuc"]}/') + "#service"},
        }],
    }


# ---------------------------------------------------------------------------
# Trang văn bản, trang 404
# ---------------------------------------------------------------------------
LEGAL = [("chinh-sach-bao-mat", "i-shield-check"), ("dieu-khoan-su-dung", "i-doc"), ("mien-tru-trach-nhiem", "i-alert")]


def legal_page(name):
    d = S.legal[name]
    path = f"{name}/"
    r = root_of(path)
    ctx = Ctx(S, r, path, d["_src"], where="Nội dung")
    toc_items = []
    content_html = M.block(d.get("body"), ctx, toc=toc_items)
    toc = "\n          ".join(f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in toc_items)
    rel = "\n          ".join(f'<li><a href="{r}{n}/">{ico(icon, "rel-list__icon")}<span>{esc(S.legal[n].get("tieu_de", ""))}</span>{ARROW}</a></li>'
                              for n, icon in LEGAL if n != name)
    body = f"""
<section class="section section--cream">
  <div class="container legal-layout">
    <article class="prose card legal-doc">
      {content_html}
    </article>
    <aside class="legal-aside">
      <div class="aside-card aside-card--toc">
        <p class="aside-card__title">Nội dung chính</p>
        <ol class="toc">
          {toc}
        </ol>
      </div>
      <div class="aside-card">
        <p class="aside-card__title">Văn bản liên quan</p>
        <ul class="rel-list">
          {rel}
        </ul>
      </div>
    </aside>
  </div>
</section>
"""
    mod = d.get("ngay_cap_nhat") or TODAY
    y, m, dd = mod.split("-")
    lead = M.plain(d.get("mo_dau"), ctx.at(where="Đoạn mở đầu"))
    lead = (lead + " " if lead else "") + f"Cập nhật lần cuối: {dd}/{m}/{y}."
    seo = d.get("seo") or {}
    page = {"path": path, "src": d["_src"], "lawyer_card": False, "modified": mod, "body": body,
            "crumbs": [HOME, (d.get("tieu_de", ""), path)], "eyebrow": M.plain(d.get("nhan"), ctx),
            "h1": M.title(d.get("tieu_de_trang"), ctx), "lead": lead,
            "title": full_title(seo.get("tieu_de", ""), path), "description": seo.get("mo_ta", "")}
    check_title(d["_src"], page["title"])
    page["og_abs"], page["og_size"], page["og_rel"] = og_for(seo, "assets/img/og-image.jpg")
    return page


def not_found_page():
    d = S.not_found
    ctx = Ctx(S, "", "404.html", d["_src"])
    f = F()
    body = f"""<section class="notfound">
  <div class="container notfound__inner">
    <p class="notfound__code">404</p>
    <h1 class="notfound__title">{M.plain(d.get("tieu_de"), ctx)}</h1>
    <p class="notfound__text">{M.plain(d.get("noi_dung"), ctx)}</p>
    <div class="notfound__actions">
      <a class="btn btn--primary" href="">Về trang chủ {ARROW}</a>
      <a class="btn btn--outline" href="dich-vu/">Xem lĩnh vực hoạt động</a>
      <a class="btn btn--outline" href="lien-he/">Liên hệ luật sư</a>
    </div>
    <ul class="notfound__links">
      <li><a href="kien-thuc-phap-ly/">Kiến thức pháp lý</a></li>
      <li><a href="cau-hoi-thuong-gap/">Câu hỏi thường gặp</a></li>
      <li><a href="tel:{f["phone_tel"]}">Gọi {esc(f["phone"])}</a></li>
    </ul>
  </div>
</section>"""
    seo = d.get("seo") or {}
    page = {"path": "404.html", "src": d["_src"], "noindex": True, "root_override": "", "dynamic_base": True,
            "page_hero": False, "contact_band": False, "crumbs": [HOME], "body": body,
            "title": full_title(seo.get("tieu_de", ""), "404.html"), "description": seo.get("mo_ta", "")}
    page["og_abs"], page["og_size"], page["og_rel"] = og_for({}, "assets/img/og-image.jpg")
    return page


# ---------------------------------------------------------------------------
# Danh mục trang (cho menu, kiểm liên kết, danh sách chọn trong CMS)
# ---------------------------------------------------------------------------
def build_registry():
    """Mọi trang sẽ có trên site, theo thứ tự hiển thị ở sitemap và tìm kiếm."""
    reg = {}

    def add(path, label, kind, parent=None, title=None):
        reg[path] = {"label": label, "kind": kind, "parent": parent, "title": title or label}

    add("", "Trang chủ", "trang")
    for slug, p in S.pages.items():
        if slug != content.HOME_SLUG:
            add(f"{slug}/", p["tieu_de"], "trang", p2path(p.get("trang_cha")) if p.get("trang_cha") else None)
    add("dich-vu/", "Lĩnh vực hoạt động", "hub")
    for s in S.services:
        add(f"dich-vu/{s['slug']}/", s["ten"], "dich_vu", "dich-vu/", f"Dịch vụ › {s['ten']}")
    add("kien-thuc-phap-ly/", "Kiến thức pháp lý", "hub")
    for a in S.articles:
        add(f"kien-thuc-phap-ly/{a['slug']}/", a.get("tieu_de_ngan") or a["tieu_de"], "bai_viet", "kien-thuc-phap-ly/",
            f"Bài viết › {a.get('tieu_de_ngan') or a['tieu_de']}")
    add("cau-hoi-thuong-gap/", "Câu hỏi thường gặp", "hub", "kien-thuc-phap-ly/")
    for name, _ in LEGAL:
        add(f"{name}/", S.legal[name].get("tieu_de", name), "van_ban")
    return reg


def draft_paths():
    out = {}
    for x in S.draft_items:
        src = x["_src"]
        if src.startswith("content/dich-vu/"):
            out[f"dich-vu/{x['slug']}/"] = x.get("ten")
        elif src.startswith("content/bai-viet/"):
            out[f"kien-thuc-phap-ly/{x['slug']}/"] = x.get("tieu_de")
        elif src.startswith("content/trang/"):
            out[f"{x['slug']}/"] = x.get("tieu_de")
    return out


def menu_walk():
    order = []
    for it in S.menu.get("menu") or []:
        order.append(p2path(it.get("trang")))
        for x in it.get("muc_con") or []:
            order.append(p2path(x.get("trang")))
    return order


def ordered_pages(pages):
    walk = menu_walk()
    pos = {p: i for i, p in reversed(list(enumerate(walk)))}
    svc_at = pos.get("dich-vu/", 10 ** 6)

    def key(p):
        path = p["path"]
        if path == "":
            return (0, 0, "")
        kind = S.registry.get(path, {}).get("kind")
        if kind == "trang":
            i = pos.get(path, 10 ** 7)
            return (1 if i < svc_at else 3, i, path)
        if kind == "van_ban":
            return (4, [n for n, _ in LEGAL].index(path.rstrip("/")), path)
        return (2, 0, "")  # trang tổng hợp, lĩnh vực, bài viết: giữ thứ tự dựng
    return sorted(pages, key=key)


def cms_options():
    entries = [(path, info) for path, info in S.registry.items()]
    for path, title in S.draft_paths.items():
        if path not in S.registry:
            entries.append((path, {"title": f"{title} (bản nháp)"}))
    pages = [{"label": f'{info["title"]} — /{path}', "value": "/" + path} for path, info in entries]
    faq = [{"label": f["hoi"], "value": f["ma"]} for f in S.faq]
    drafts = [x for x in S.draft_items if x["_src"].startswith("content/dich-vu/") and x["slug"] not in S.service_by_slug]
    services = [{"label": s["ten"] + (" (bản nháp)" if s.get("nhap") else ""), "value": s["slug"]}
                for s in S.services + sorted(drafts, key=lambda s: (s.get("thu_tu") or 99, s.get("ten") or ""))]
    return {"pages": pages, "faq": faq, "services": services}


# ---------------------------------------------------------------------------
# Kiểm liên kết nội bộ, mã neo, chuyển hướng
# ---------------------------------------------------------------------------
ID_RE = re.compile(r'\sid="([^"]+)"')


def check_links(rendered, out):
    ids = {path: set(ID_RE.findall(h)) for path, h in rendered.items()}
    redirect_from = {p2path(x["tu"]): x["den"] for x in S.redirects if x.get("tu")}
    for src, where, path, anchor in S.link_refs:
        if path and "." in path.rsplit("/", 1)[-1]:  # tệp tĩnh (ảnh, pdf…)
            if not os.path.isfile(os.path.join(out, path)):
                LOI.them(src, where, f"Liên kết tới tệp “/{path}” không tồn tại.")
            continue
        if path not in rendered:
            if path in redirect_from:
                LOI.them(src, where, f"Liên kết tới “/{path}” là đường dẫn cũ đã chuyển hướng; đổi thành “{redirect_from[path]}”.")
            elif path in S.draft_paths and not S.drafts:
                LOI.them(src, where, f"Liên kết tới “/{path}” – trang này đang là bản nháp nên chưa có trên site. Đăng trang đó trước hoặc bỏ liên kết.")
            else:
                LOI.them(src, where, f"Liên kết tới “/{path}” không tồn tại trên site.")
            continue
        if anchor and anchor not in ids[path]:
            LOI.them(src, where, f"Mã neo “#{anchor}” không có trên trang “/{path}”.")
    # Chuyển hướng: đích có thật, không vòng lặp, đường dẫn cũ không trùng trang đang có
    for i, x in enumerate(S.redirects, 1):
        where = f"Đường dẫn cũ → mới › Chuyển hướng {i}"
        src_p, (dst_p, _, anchor) = p2path(x["tu"]), p2path(x["den"]).partition("#")
        if src_p in rendered:
            LOI.them("content/cai-dat/chuyen-huong.yml", where, f"“{x['tu']}” đang là một trang có thật; không thể vừa là trang vừa chuyển hướng.")
        if dst_p in redirect_from:
            LOI.them("content/cai-dat/chuyen-huong.yml", where, f"Đích “{x['den']}” lại là đường dẫn chuyển hướng khác (vòng lặp/chuỗi chuyển hướng).")
        elif dst_p not in rendered:
            LOI.them("content/cai-dat/chuyen-huong.yml", where, f"Đích “{x['den']}” không phải trang có thật.")
        elif anchor and anchor not in ids[dst_p]:
            LOI.them("content/cai-dat/chuyen-huong.yml", where, f"Mã neo “#{anchor}” không có trên trang “{x['den']}”.")


# ---------------------------------------------------------------------------
# Tệp phụ trợ
# ---------------------------------------------------------------------------
def write(out, rel, text):
    full = os.path.join(out, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(text)


def redirect_stub(path, target, label):
    depth = path.count("/")
    rel_target = "../" * depth + target.lstrip("/")
    canonical = abs_url(target.lstrip("/").split("#")[0])
    return (f'<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="robots" content="noindex">'
            f'<meta http-equiv="refresh" content="0; url={esc(rel_target)}"><title>{esc(label)}</title>'
            f'<link rel="canonical" href="{canonical}"></head><body><p>Trang đã chuyển sang <a href="{esc(rel_target)}">{esc(label)}</a>.</p></body></html>')


def write_extras(out, pages, rendered):
    bp = ENV["base_path"]
    # Chuyển hướng: trang chuyển tiếp (GitHub Pages) + _redirects 301 thật (Cloudflare)
    lines = []
    for x in S.redirects:
        src_p = p2path(x["tu"])
        dst_p = p2path(x["den"]).split("#")[0]
        label = S.registry.get(dst_p, {}).get("label", "trang mới")
        write(out, src_p + "index.html", redirect_stub(src_p, x["den"], f"{label} – {F()['short_name']}"))
        lines.append(f"{bp}{src_p} {bp}{x['den'].lstrip('/')} 301")
        lines.append(f"{bp}{src_p.rstrip('/')} {bp}{x['den'].lstrip('/')} 301")
    if S.drafts:
        for path in S.draft_paths:
            slug = path.rstrip("/").rsplit("/", 1)[-1]
            lines.append(f"{bp}nhap/{slug}/ {bp}{path} 302")
    nhap = getattr(S, "nhap_rieng", None) or {}
    for path in nhap:  # link ngắn /nhap/<đường-dẫn>/ → bản nháp riêng (bài viết, lĩnh vực nằm sâu hơn 1 cấp)
        slug = path.rstrip("/").rsplit("/", 1)[-1]
        if slug + "/" != path and slug + "/" not in nhap:
            lines.append(f"{bp}nhap/{slug}/ {bp}nhap/{path} 302")
    write(out, "_redirects", "\n".join(lines) + "\n")
    headers = [f"{bp}assets/fonts/*", "  Cache-Control: public, max-age=31536000, immutable",
               f"{bp}assets/*", "  Cache-Control: public, max-age=604800",
               f"{bp}admin/*", "  X-Robots-Tag: noindex, nofollow", "  Cache-Control: no-cache",
               f"{bp}nhap/*", "  X-Robots-Tag: noindex, nofollow"]
    if ENV["noindex"]:
        headers += [f"{bp}*", "  X-Robots-Tag: noindex, nofollow"]
    write(out, "_headers", "\n".join(headers) + "\n")
    write(out, ".nojekyll", "")

    indexable = [p for p in pages if not p.get("noindex") and not p.get("is_draft")]
    if ENV["noindex"]:
        write(out, "robots.txt", f"# {F()['legal_name']} – bản thử, không lập chỉ mục\nUser-agent: *\nDisallow: /\n")
    else:
        urls = "".join(f"  <url>\n    <loc>{abs_url(p['path'])}</loc>\n    <lastmod>{p.get('modified', TODAY)}</lastmod>\n  </url>\n"
                       for p in indexable)
        write(out, "sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
        write(out, "robots.txt", f"# {F()['legal_name']}\nUser-agent: *\nAllow: /\nDisallow: {bp}admin/\nDisallow: {bp}nhap/\n\n"
                                 f"Sitemap: {ENV['site_url']}/sitemap.xml\n")
    write(out, "site.webmanifest", json.dumps({
        "name": F()["legal_name"], "short_name": F()["brand"], "description": "Tư vấn pháp lý và tham gia tố tụng tại Thành phố Hồ Chí Minh.",
        "lang": "vi", "start_url": "./", "scope": "./", "display": "standalone",
        "background_color": "#fffdf9", "theme_color": "#fffdf9",
        "icons": [{"src": "assets/img/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "assets/img/icon-512.png", "sizes": "512x512", "type": "image/png"},
                  {"src": "assets/img/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"}],
    }, ensure_ascii=False, indent=2) + "\n")

    # Chỉ mục tìm kiếm trong site
    index = []
    for p in indexable:
        heads = re.findall(r"<h[23][^>]*>(.*?)</h[23]>", p["body"], re.S)
        keys = " · ".join(tpl.unescape(M.strip_tags(h)) for h in heads)[:600]
        _, section = section_of(p["path"])
        index.append({"t": p["crumbs"][-1][0] if p["path"] else F()["legal_name"], "u": p["path"],
                      "d": p["description"], "s": section, "k": keys})
    ctx = Ctx(S, "", "cau-hoi-thuong-gap/", "content/hoi-dap.yml")
    for f in S.faq:
        first = M.to_text(f["dap"].split("\n\n")[0], ctx)
        index.append({"t": f["hoi"], "u": f"cau-hoi-thuong-gap/#{f['ma']}", "d": first[:180], "s": "Câu hỏi thường gặp", "k": ""})
    write(out, "assets/search-index.json", json.dumps(index, ensure_ascii=False, separators=(",", ":")))

    # Trang danh sách bản nháp: bản thử (nháp ở đường dẫn thật) hoặc bản chính thức có nháp riêng dưới /nhap/
    if (S.drafts and S.draft_paths) or nhap:
        listed, pre = (S.draft_paths, "../") if S.drafts else (nhap, "")
        rows = "".join(f'<li><a href="{pre}{p}">{esc(t or p)}</a> <small>/{p}</small></li>' for p, t in listed.items())
        write(out, "nhap/index.html", '<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="robots" content="noindex, nofollow">'
                                      '<meta name="viewport" content="width=device-width, initial-scale=1"><title>Bản nháp chờ duyệt</title>'
                                      '<style>body{font:16px/1.6 system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 16px;color:#2b1d21}'
                                      'a{color:#b5000b}small{color:#7a6e70}</style></head><body><h1>Bản nháp chờ duyệt</h1>'
                                      f'<p>Bấm để xem đúng bố cục thật. Chưa đăng lên site chính thức.</p><ul>{rows}</ul></body></html>')

    # Trang quản trị /admin: Sveltia CMS + cấu hình sinh từ schema
    if ENV["admin"]:
        import yaml
        os.makedirs(os.path.join(out, "admin"), exist_ok=True)
        for name in sorted(os.listdir(os.path.join(ROOT, "admin"))):  # index.html + khung mô phỏng (xem-truoc*.js)
            if name.endswith((".html", ".js", ".css")):
                shutil.copy2(os.path.join(ROOT, "admin", name), os.path.join(out, "admin", name))
        cfg = schema.cms_config(cms_options(), ENV)
        header = ("# TỆP TỰ SINH từ tools/schema.py mỗi lần build – không sửa tay.\n"
                  "# Thêm/sửa trường: sửa tools/schema.py rồi build lại.\n")
        # Danh sách chọn dùng lại nhiều chỗ: ghi đầy đủ, không dùng &id/*id. Bản C (libyaml) nhanh ~15 lần, cùng kết quả.
        class NoAlias(getattr(yaml, "CSafeDumper", yaml.SafeDumper)):
            def ignore_aliases(self, data):
                return True
        write(out, "admin/config.yml", header + yaml.dump(cfg, Dumper=NoAlias, allow_unicode=True, sort_keys=False, width=10 ** 6))
        # Cột trái xếp theo Menu chính: tiêu đề nhóm, mục thụt vào, mục một trang (admin/dieu-huong.js đọc tệp này)
        write(out, "admin/cot-trai.json", json.dumps(schema.sidebar_decor(schema.collections()), ensure_ascii=False))
        huong_dan.build(out, ENV["site_url"])  # /admin/huong-dan/: hướng dẫn có ảnh chụp, dựng từ docs/huong-dan/README.md
        # /admin/xem-truoc/goi.zip: code build + nội dung cho khung mô phỏng (chạy trong trình duyệt)
        import goi_xem_truoc
        goi_xem_truoc.package(out, tpl.PHOTO_SIZE, tpl.UPLOADS, {r: file_hash(r) for r in ("assets/css/style.css", "assets/js/main.js")})
        thieu = goi_xem_truoc.missing_previews()
        if thieu:
            LOI.canh("admin/xem-truoc.js", "PREVIEW_NAMES", "Chưa đăng ký khung mô phỏng cho: " + ", ".join(thieu))


# ---------------------------------------------------------------------------
# Chạy
# ---------------------------------------------------------------------------
def copy_static(out):
    for d in ("css", "js", "fonts"):
        shutil.copytree(os.path.join(ROOT, "assets", d), os.path.join(out, "assets", d))


def try_drafts(out=None):
    """Bản chính thức không đưa bản nháp vào site, nhưng vẫn dựng thử để báo sớm lỗi chỉ lộ ra khi dựng trang
    (ảnh thiếu mô tả, mã chèn sai…). Có `out` (DRAFTS=1 trên bản chính thức – tên miền riêng): ghi từng bản nháp
    riêng tại /nhap/<đường-dẫn>/ (noindex), menu, danh sách, sitemap vẫn như bản chính thức.
    Trả về {đường dẫn thật: tiêu đề} của các bản nháp đã ghi."""
    global PREFIX
    n = len(S.link_refs)
    written = {}
    PREFIX = S.nhap_prefix = "nhap/" if out else ""
    try:
        for x in S.draft_items:
            src = x["_src"]
            try:
                if src.startswith("content/bai-viet/"):
                    page = article_page(x)
                elif src.startswith("content/dich-vu/"):
                    page = service_page(x)
                elif src.startswith("content/trang/"):
                    page = block_page(x)
                else:
                    continue
                if out:
                    page.update(noindex=True, is_draft=True)
                html = layout(page)
            except Exception as e:  # dữ liệu nháp dở dang: chỉ cảnh báo
                LOI.canh(src, "", f"Chưa dựng thử được bản nháp ({type(e).__name__}: {e}).")
                continue
            if out:
                write(out, "nhap/" + page["path"] + "index.html", html)
                written[page["path"]] = S.draft_paths.get(page["path"]) or page["title"]
    finally:
        PREFIX = S.nhap_prefix = ""
        del S.link_refs[n:]
    return written


def drafts_never_block():
    """Bản nháp không bao giờ chặn site chính thức: lỗi của tệp đang là nháp chuyển thành cảnh báo
    (bản thử trên Cloudflare vẫn coi là lỗi để luật sư xem nháp đúng như sẽ đăng)."""
    if S.drafts:
        return
    srcs = {x["_src"] for x in S.draft_items}
    keep = []
    for tep, truong, tb in LOI.loi:
        if tep in srcs:
            LOI.canh(tep, truong, "Bản nháp – cần sửa trước khi bỏ dấu nháp: " + tb)
        else:
            keep.append((tep, truong, tb))
    LOI.loi = keep


def fail():
    print(LOI.bao_cao(), file=sys.stderr)
    LOI.ghi_tom_tat_github()
    path = os.environ.get("BUILD_ERRORS_FILE")
    if path:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(LOI.bao_cao(markdown=True))
    sys.exit(1)


def main():
    global ENV, S, IMG, ORG_ID, SITE_ID
    ENV = read_env()
    ORG_ID, SITE_ID = ENV["site_url"] + "/#organization", ENV["site_url"] + "/#website"
    S = content.load(ENV)
    invalid = bool(LOI)  # có lỗi dữ liệu: vẫn dựng thử để gom thêm lỗi (liên kết, mã chèn…) rồi mới dừng
    S.registry = build_registry()
    S.draft_paths = draft_paths()

    out = ENV["out"]
    tmp = out + ".tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    try:
        copy_static(tmp)
        IMG = Images(S, tmp)
        sizes = IMG.brand()
        uploads = IMG.uploads()
        tpl.init(S, sizes, uploads)
        default_og = S.seo.get("anh_chia_se") or {}
        if default_og.get("anh_rieng"):
            IMG.og_from_file("og-image.jpg", default_og["anh_rieng"])
        else:
            IMG.og("og-image.jpg", default_og.get("nhan", ""), default_og.get("tieu_de", ""), default_og.get("mo_ta", ""), "phien-toa")

        pages = [block_page(S.pages[content.HOME_SLUG])]
        pages += [block_page(p) for slug, p in S.pages.items() if slug != content.HOME_SLUG]
        pages.append(services_hub())
        pages += [service_page(s) for s in S.services]
        pages.append(knowledge_hub())
        pages += [article_page(a) for a in S.articles]
        pages.append(faq_page())
        pages += [legal_page(n) for n, _ in LEGAL]
        pages = ordered_pages(pages)
        nf = not_found_page()

        rendered = {}
        for p in pages + [nf]:
            html = layout(p)
            rendered[p["path"]] = html
            write(tmp, p["path"] if p["path"].endswith(".html") else p["path"] + "index.html", html)
        check_links(rendered, tmp)
        if not S.drafts:
            S.nhap_rieng = try_drafts(tmp if ENV["nhap_rieng"] else None)
        drafts_never_block()
        if LOI:
            fail()
    except SystemExit:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        if invalid:
            drafts_never_block()
            if LOI:
                fail()  # dữ liệu sai làm bước dựng trang không chạy tiếp được: báo các lỗi đã gom
        raise
    try:
        IMG.run_og()
        write_extras(tmp, pages, rendered)
    except SystemExit:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    shutil.rmtree(out, ignore_errors=True)
    os.replace(tmp, out)
    drafts = f", {len(S.draft_paths)} bản nháp" + (" (đã xuất để xem trước)" if S.drafts else
                                                 f" (xuất riêng {len(S.nhap_rieng)} bản tại /nhap/)" if ENV["nhap_rieng"] else " (không xuất)")
    print(f"Đã tạo {len(pages) + 1} trang, sitemap {0 if ENV['noindex'] else len([p for p in pages if not p.get('is_draft')])} URL{drafts} → {os.path.relpath(out, ROOT)}/")
    print(f"Địa chỉ gốc: {ENV['site_url']}/  ·  noindex: {'có' if ENV['noindex'] else 'không'}")
    if LOI.canh_bao:
        print(LOI.bao_cao())
        LOI.ghi_tom_tat_github()


if __name__ == "__main__":
    main()
