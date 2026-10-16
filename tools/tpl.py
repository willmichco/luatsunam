# -*- coding: utf-8 -*-
"""Thành phần giao diện dùng chung (thẻ, lưới, ảnh, khối liên hệ…). Markup giữ nguyên như site đang chạy.

Gọi tpl.init(site, images) một lần trước khi dựng trang.
"""
import html as _html
import re

import markup as M
from markup import esc

S = None          # Site (tools/content.py)
PHOTO_SIZE = {}   # kích thước thật của ảnh thương hiệu sau khi xử lý
UPLOADS = {}      # ảnh tải lên: đường dẫn → (rộng, cao, [bề ngang bản thu nhỏ])
ASSET_VERSION = "20261015b"


def init(site, photo_sizes, uploads):
    global S, PHOTO_SIZE, UPLOADS
    S, PHOTO_SIZE, UPLOADS = site, photo_sizes, uploads


def F():
    return S.firm


def asset_ref(path):
    return f"{path}?v={ASSET_VERSION}"


def ico(name, cls="ico"):
    return f'<svg class="{cls}" aria-hidden="true"><use href="#{name}"/></svg>'


ARROW = ico("i-arrow")


def cms(src, key, label=""):
    """Đánh dấu chỗ sửa cho khung mô phỏng trong /admin (tools/xem_truoc.py thay hàm này): thuộc tính data-cms để bấm vào
    thẻ/khối trên trang mô phỏng là mở đúng ô trong form (kể cả ô nằm ở tệp khác). Site thật: chuỗi rỗng, HTML không đổi."""
    return ""


# ---------------------------------------------------------------------------
# Ảnh
# ---------------------------------------------------------------------------
PHOTO_SETS = {
    "van-phong": {"alt": "{lawyer} làm việc tại văn phòng Luật Sư Nam, {street}",
                  "sizes": "(max-width: 700px) calc(100vw - 40px), (max-width: 900px) 640px, 560px"},
    "phien-toa": {"alt": "{lawyer} tại ghế người bào chữa trong phiên tòa",
                  "sizes": "(max-width: 600px) calc(100vw - 40px), 520px"},
}


def photo_alt(name):
    return PHOTO_SETS[name]["alt"].format(lawyer=F()["lawyer"], street=F()["street"])


def picture(r, name, lazy=False, alt=None):
    """Ảnh thật của luật sư: AVIF (nhẹ) + WebP (dự phòng), 3 bề ngang."""
    p = PHOTO_SETS[name]
    w, h = PHOTO_SIZE[name]
    base = f"assets/img/luat-su-{name}"

    def srcset(ext):
        return ", ".join(f"{r}{asset_ref(f'{base}{s}.{ext}')} {bw}w" for s, bw in (("-480", 480), ("-640", 640), ("", w)))
    load = 'loading="lazy" decoding="async"' if lazy else 'fetchpriority="high"'
    return (f'<picture><source type="image/avif" srcset="{srcset("avif")}" sizes="{p["sizes"]}">'
            f'<img src="{r}{asset_ref(base + ".webp")}" srcset="{srcset("webp")}" sizes="{p["sizes"]}" '
            f'alt="{esc(alt or photo_alt(name))}" width="{w}" height="{h}" {load}></picture>')


def upload_img(ctx, path, alt, sizes="(max-width: 700px) calc(100vw - 40px), 560px", lazy=True, cls=None):
    """Ảnh tải lên qua CMS: WebP kèm bản thu nhỏ cho điện thoại."""
    info = UPLOADS.get(path)
    src = M.href(path, ctx)
    attrs = f' class="{cls}"' if cls else ""
    load = 'loading="lazy" decoding="async"' if lazy else 'fetchpriority="high"'
    if not info:
        return f'<img{attrs} src="{src}" alt="{esc(alt)}" {load}>'
    w, h, widths = info
    stem = src.rsplit(".", 1)[0]
    srcset = ", ".join([f"{stem}-{bw}.webp {bw}w" for bw in widths] + [f"{src} {w}w"])
    return (f'<img{attrs} src="{src}" srcset="{srcset}" sizes="{sizes}" alt="{esc(alt)}" '
            f'width="{w}" height="{h}" {load}>')


def block_photo(ctx, b, lazy=True):
    """Ảnh của một khối: ảnh tải riêng nếu có, không thì ảnh có sẵn của luật sư."""
    alt = M.expand(b.get("mo_ta_anh") or "", ctx) or None
    if b.get("anh"):
        return upload_img(ctx, b["anh"], alt or "", lazy=lazy)
    name = b.get("anh_co_san") or "van-phong"
    return picture(ctx.r, name, lazy=lazy, alt=alt)


def figcaption(ctx, b):
    strong, small = M.plain(b.get("chu_thich"), ctx), M.plain(b.get("chu_thich_phu"), ctx)
    if not strong and not small:
        return ""
    return (f'<figcaption class="photo__cap">{f"<strong>{strong}</strong>" if strong else ""}'
            f'{f"<span>{small}</span>" if small else ""}</figcaption>')


def open_now(cls="open-now"):
    """Trạng thái "Đang trong giờ làm việc / Ngoài giờ" theo giờ Việt Nam, do main.js điền khi tải trang."""
    return f'<span class="{cls}" data-open-now>&nbsp;</span>'


# ---------------------------------------------------------------------------
# Liên kết
# ---------------------------------------------------------------------------
def link_href(ctx, ln):
    """Liên kết từ CMS: {trang, ma_neo} hoặc {ngoai}."""
    if not ln:
        return None
    if ln.get("ngoai"):
        return M.href(M.expand(ln["ngoai"], ctx), ctx)
    target = (ln.get("trang") or "/") + (f"#{ln['ma_neo']}" if ln.get("ma_neo") else "")
    return M.href(target, ctx)


def link_arrow(ctx, ln, light=False):
    if not ln:
        return ""
    cls = "link-arrow link-arrow--light" if light else "link-arrow"
    return f'<a class="{cls}" href="{link_href(ctx, ln)}">{M.plain(ln.get("nhan"), ctx)} {ARROW}</a>'


def section_more(ctx, links, light=False):
    links = [x for x in links or [] if x]
    if not links:
        return ""
    return '<p class="section-more">' + "".join(link_arrow(ctx, x, light) for x in links) + "</p>"


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
    f = F()
    cw, ch = PHOTO_SIZE.get("chan-dung", (560, 420))
    return f"""<aside class="lcard" aria-label="Luật sư phụ trách">
      <picture>
        <source media="(max-width: 900px)" srcset="{r}{asset_ref("assets/img/luat-su-avatar.webp")}">
        <source type="image/avif" srcset="{r}{asset_ref("assets/img/luat-su-chan-dung.avif")}">
        <img class="lcard__photo" src="{r}{asset_ref("assets/img/luat-su-chan-dung.webp")}" alt="{esc(f["lawyer"])} tại phiên tòa" width="{cw}" height="{ch}">
      </picture>
      <div class="lcard__body">
        <p class="lcard__name">{esc(f["lawyer"])}</p>
        <p class="lcard__role">{esc(f["lawyer_role"])}</p>
        <div class="lcard__actions">
          <a class="btn btn--primary btn--sm" href="tel:{f["phone_tel"]}">{ico("i-phone")} Gọi {esc(f["phone"])}</a>
          <a class="btn btn--outline btn--sm" href="{esc(f["zalo"])}" target="_blank" rel="noopener">{ico("i-chat")} Zalo</a>
        </div>
        <p class="lcard__note">{ico("i-clock")} {esc(f["hours"])}</p>
        {open_now("open-now lcard__status")}
      </div>
    </aside>"""


def contact_band(ctx, override=None, defaults=None):
    """Khối liên hệ cuối trang: ảnh luật sư, gọi điện, Zalo, đường đến văn phòng.
    override: nhóm "Khối liên hệ cuối trang" của trang; ô để trống dùng câu chữ dùng chung."""
    f = F()
    base = S.text.get("lien_he_cuoi_trang") or {}
    o, d = override or {}, defaults or {}
    pick = (lambda k: o.get(k) or d.get(k) or base.get(k) or "")
    c = ctx.at(src=(o.get("_src") or ctx.src), where="Khối liên hệ cuối trang")
    return f"""<section class="cband" aria-labelledby="cband-title">
  <div class="container">
    <div class="cband__intro">
      <img class="cband__avatar" src="{ctx.r}{asset_ref("assets/img/luat-su-avatar.webp")}" alt="{esc(f["lawyer"])}" width="92" height="92" loading="lazy" decoding="async">
      <div>
        <p class="eyebrow">{M.plain(pick("nhan"), c)}</p>
        <h2 class="cband__title" id="cband-title">{M.plain(pick("tieu_de"), c)}</h2>
        <p class="cband__text">{M.plain(pick("doan_moi"), c)}</p>
      </div>
    </div>
    <div class="cband__cards">
      <a class="cband__card" href="tel:{f["phone_tel"]}">{ico("i-phone")}<span>Gọi điện</span><strong>{esc(f["phone"])}</strong><small>{esc(f["hours"])}</small>{open_now()}</a>
      <a class="cband__card cband__card--zalo" href="{esc(f["zalo"])}" target="_blank" rel="noopener">{ico("i-chat")}<span>Nhắn Zalo</span><strong>{esc(f["phone"])}</strong><small>{M.plain(base.get("ghi_chu_zalo"), c)}</small></a>
      <a class="cband__card" href="https://www.google.com/maps/dir/?api=1&amp;destination={f["maps_query"]}" target="_blank" rel="noopener">{ico("i-pin")}<span>Đến văn phòng</span><strong>{esc(f["street"])}</strong><small>{esc(f["ward"])}, {esc(f["city_short"])} · {M.plain(base.get("ghi_chu_van_phong"), c)}</small></a>
    </div>
  </div>
</section>"""


def shead(eyebrow, title, text="", link=None, center=False, hid=""):
    """Tiêu đề khu vực dùng chung (đối số là HTML đã xử lý): nhãn nhỏ, tiêu đề, mô tả, liên kết bên phải."""
    eb = f'<p class="eyebrow">{eyebrow}</p>' if eyebrow else ""
    p = f'<p class="shead__text">{text}</p>' if text else ""
    a = f'<a class="link-arrow" href="{link[0]}">{link[1]} {ARROW}</a>' if link else ""
    idattr = f' id="{hid}"' if hid else ""
    cls = "shead shead--center" if center else "shead"
    return f'<div class="{cls} reveal"><div class="shead__main">{eb}<h2 class="h2"{idattr}>{title}</h2>{p}</div>{a}</div>'


def shead_from(ctx, b, hid="", link=None, center=False):
    """shead từ các ô Nhãn nhỏ / Tiêu đề khối / Mô tả của một khối."""
    ln = (link_href(ctx, link), M.plain(link.get("nhan"), ctx)) if link else None
    return shead(M.plain(b.get("nhan"), ctx), M.plain(b.get("tieu_de"), ctx), M.plain(b.get("mo_ta"), ctx),
                 link=ln, center=center, hid=hid)


def icard(href, icon, title, text, more="Xem chi tiết", heading="h3", mark=""):
    return (f'<a class="icard reveal"{mark} href="{href}"><span class="ichip">{ico(icon, "")}</span>'
            f'<{heading} class="icard__title">{title}</{heading}><p class="icard__text">{text}</p>'
            f'<span class="icard__more">{more} {ARROW}</span></a>')


SERVICES_HUB_SRC = "content/dich-vu/_index.yml"


def grid_cards():
    """Lưới lĩnh vực (Trang chủ, trang Dịch vụ, trang Kiến thức pháp lý): đúng thứ tự thẻ ở Trang tổng quan Dịch vụ ›
    Khối lưới lĩnh vực. Lĩnh vực đã đăng chưa có thẻ nằm cuối, chữ tạm = tên + mô tả ngắn (build có cảnh báo).
    Trả về [(lĩnh vực, thẻ hoặc None, vị trí thẻ trong danh sách hoặc None)]."""
    cards = ((S.hubs.get("dich_vu") or {}).get("luoi") or {}).get("the") or []
    out, seen = [], set()
    for i, c in enumerate(cards):
        s = S.service_by_slug.get((c or {}).get("linh_vuc"))
        if s and s["slug"] not in seen:  # lĩnh vực nháp (bản chính thức) hoặc đã xóa: bỏ qua thẻ
            seen.add(s["slug"])
            out.append((s, c, i))
    return out + [(s, None, None) for s in S.services if s["slug"] not in seen]


def problem_card(s, card, i, r):
    """Thẻ "anh chị đang gặp chuyện gì": tình huống đời thường dẫn tới trang lĩnh vực."""
    t = card or {}
    mark = cms(SERVICES_HUB_SRC, f"luoi.the.{i}" if i is not None else "luoi.the", f"Thẻ {s['ten']}")
    return (f'<a class="icard reveal"{mark} href="{r}dich-vu/{s["slug"]}/"><span class="ichip">{ico(t.get("bieu_tuong") or s["bieu_tuong"], "")}</span>'
            f'<span class="icard__tag">{esc(s["ten"])}</span>'
            f'<h3 class="icard__title">{esc(t.get("tieu_de") or s["ten"])}</h3><p class="icard__text">{esc(t.get("mo_ta") or s["mo_ta_ngan"])}</p>'
            f'<span class="icard__more">Xem cách giải quyết {ARROW}</span></a>')


def problems_grid(r):
    return '<div class="grid grid--4 grid--problems">' + "".join(problem_card(s, c, i, r) for s, c, i in grid_cards()) + "</div>"


def service_card(s, r, heading="h3"):
    return icard(f'{r}dich-vu/{s["slug"]}/', s["bieu_tuong"], esc(s["ten"]), esc(s["mo_ta_ngan"]), heading=heading,
                 mark=cms(s["_src"], "mo_ta_ngan", f"Thẻ {s['ten']} (tên + mô tả ngắn)"))


def services_grid(r, cls="grid grid--4"):
    return f'<div class="{cls}">' + "".join(service_card(s, r) for s, _, _ in grid_cards()) + "</div>"


def vi_date(iso):
    y, m, d = iso.split("-")
    return f"{int(d):02d} Tháng {int(m)}, {y}"


def article_card(a, r, heading="h3"):
    svc = S.service_by_slug.get(a["linh_vuc"], {"ten": ""})
    return f"""<article class="post reveal"{cms(a["_src"], "tom_tat", "Thẻ bài: " + (a.get("tieu_de_ngan") or a["tieu_de"]))}>
  <p class="post__meta"><a class="tag" href="{r}dich-vu/{a["linh_vuc"]}/">{esc(svc["ten"])}</a><time datetime="{a["ngay_dang"]}">{ico("i-calendar")}{vi_date(a["ngay_dang"])}</time></p>
  <{heading} class="post__title"><a href="{r}kien-thuc-phap-ly/{a["slug"]}/">{esc(a.get("tieu_de_ngan") or a["tieu_de"])}</a></{heading}>
  <p class="post__excerpt">{esc(a["tom_tat"])}</p>
  <span class="post__more" aria-hidden="true">Đọc bài viết {ARROW}</span>
</article>"""


def articles_grid(r, items=None, cls="grid grid--3"):
    items = S.articles if items is None else items
    return f'<div class="{cls}">' + "".join(article_card(a, r) for a in items) + "</div>"


def faq_list(ctx, items=None, mark=""):
    out = []
    for f in (S.faq if items is None else items):
        c = ctx.at(src="content/hoi-dap.yml", where=f"Câu hỏi “{f['hoi']}” › Câu trả lời")
        body = re.sub(r">\n<", "><", M.block(f["dap"], c).strip())
        mark = cms("content/hoi-dap.yml", f"cau_hoi.{S.faq.index(f)}", f"Câu hỏi: {f['hoi']}") if f in S.faq else ""
        out.append(f"""<details class="faq__item" id="{f["ma"]}"{mark}>
  <summary><span>{esc(f["hoi"])}</span>{ico("i-chevron", "faq__chev")}</summary>
  <div class="faq__answer">{body}</div>
</details>""")
    return f'<div class="faq"{mark}>' + "".join(out) + "</div>"


def check_list(items, cls="check-list", ctx=None):
    txt = (lambda i: M.plain(i, ctx)) if ctx else esc
    return f'<ul class="{cls}">' + "".join(f"<li>{ico('i-check')}<span>{txt(i)}</span></li>" for i in items) + "</ul>"


def unescape(s):
    return _html.unescape(s)
