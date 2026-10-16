# -*- coding: utf-8 -*-
"""Khối dựng trang (mục 5 kế hoạch). Mỗi khối = một section có sẵn trên site; chỉ có vài biến thể cố định.

Thêm khối mới: khai báo trường trong BLOCK_TYPES (tools/schema.py) + viết hàm render cùng tên ở đây.
CMS tự có lựa chọn mới trong nút "Thêm khối" ở lần build sau.
"""
import re

import markup as M
import tpl
from markup import esc
from schema import BLOCK_BY_NAME
from tpl import ARROW, F, ico


def paragraphs(text):
    return [re.sub(r"\s*\n\s*", " ", p).strip() for p in re.split(r"\n\s*\n", (text or "").strip()) if p.strip()]


def sec_open(b, hid=None, aria_label=None, default_bg="trang", extra_cls=""):
    bg = b.get("nen") or default_bg
    cls = "section" + {"kem": " section--cream", "toi": " section--dark"}.get(bg, "") + extra_cls
    idattr = f' id="{b["ma_neo"]}"' if b.get("ma_neo") else ""
    aria = f' aria-labelledby="{hid}"' if hid else (f' aria-label="{aria_label}"' if aria_label else "")
    return f'<section class="{cls}"{idattr}{aria}>'


def hid_of(b, i):
    return f'{b.get("ma_neo") or f"khoi-{i}"}-title'


def copy_head(ctx, b, hid, heading_cls="h2"):
    """Nhãn nhỏ + tiêu đề h2 (dùng trong bố cục hai cột)."""
    eb = f'<p class="eyebrow">{M.plain(b.get("nhan"), ctx)}</p>' if b.get("nhan") else ""
    return f'{eb}<h2 class="{heading_cls}" id="{hid}">{M.plain(b.get("tieu_de"), ctx)}</h2>'


# ---------------------------------------------------------------------------
# 1. Đầu trang lớn (Hero)
# ---------------------------------------------------------------------------
def dau_trang(ctx, b, i, page):
    f, r = F(), ctx.r
    crumbs = "" if page["path"] == "" else "\n        " + tpl.breadcrumb_html(page["crumbs"], r)
    eyebrow = f'\n        <p class="eyebrow">{M.plain(b.get("nhan"), ctx)}</p>' if b.get("nhan") else ""
    leads = "".join(f'<p class="hero__lead">{M.plain(p, ctx)}</p>' for p in paragraphs(b.get("doan_mo_dau")))
    actions = ""
    if b.get("nut_lien_he", True):
        actions = f"""
        <div class="hero__actions">
          <a class="btn btn--primary btn--lg" href="tel:{f["phone_tel"]}">{ico("i-phone")} Gọi {esc(f["phone"])}</a>
          <a class="btn btn--outline btn--lg" href="{esc(f["zalo"])}" target="_blank" rel="noopener">{ico("i-chat")} Nhắn Zalo</a>
        </div>"""
    info = ""
    if b.get("dai_thong_tin"):
        info = f"""
        <ul class="hero__info">
          <li>{ico("i-pin")} {esc(f["street"])}, {esc(f["ward"])}, {esc(f["city_short"])}</li>
          <li>{ico("i-clock")} {esc(f["hours"])}</li>
          <li>{tpl.open_now()}</li>
        </ul>"""
    copy = f"""<div class="hero__copy">{crumbs}{eyebrow}
        <h1 class="hero__title">{M.title(b.get("tieu_de"), ctx, tag="span")}</h1>
        {leads}{actions}{info}
      </div>"""
    fig = f"""<figure class="photo">
        {tpl.block_photo(ctx, b, lazy=False)}
        {tpl.figcaption(ctx, b)}
      </figure>"""
    inner = fig + "\n      " + copy if b.get("vi_tri_anh") == "trai" else copy + "\n      " + fig
    idattr = f' id="{b["ma_neo"]}"' if b.get("ma_neo") else ""
    facts = b.get("so_lieu") or []
    if facts:
        items = "".join(f'<li><b>{M.plain(x["so"], ctx)}</b><span>{M.plain(x["mo_ta"], ctx)}</span></li>' for x in facts)
        return f"""<section class="hero"{idattr}>
  <div class="container">
    <div class="hero__grid">
      {inner}
    </div>
    <ul class="facts">{items}</ul>
  </div>
</section>"""
    return f"""<section class="hero"{idattr}>
  <div class="container hero__grid">
      {inner}
  </div>
</section>"""


# ---------------------------------------------------------------------------
# 2. Dải cam kết
# ---------------------------------------------------------------------------
def dai_cam_ket(ctx, b, i, page):
    items = "".join(f'<li><span class="ichip ichip--sm">{ico(x["bieu_tuong"])}</span><div><strong>{M.plain(x["tieu_de"], ctx)}</strong>'
                    f'<span>{M.plain(x["mo_ta"], ctx)}</span></div></li>' for x in b.get("muc") or [])
    idattr = f' id="{b["ma_neo"]}"' if b.get("ma_neo") else ""
    return f"""<section class="promise"{idattr} aria-label="Cam kết khi làm việc">
  <div class="container">
    <ul class="promise__list">{items}</ul>
  </div>
</section>"""


# ---------------------------------------------------------------------------
# 3. Lưới thẻ
# ---------------------------------------------------------------------------
def luoi_the(ctx, b, i, page):
    hid = hid_of(b, i)
    dark = b.get("nen") == "toi"
    cols = b.get("so_cot") or "3"
    cards = []
    for x in b.get("the") or []:
        title, text = M.plain(x["tieu_de"], ctx), M.inline(x.get("mo_ta"), ctx)
        href = tpl.link_href(ctx, x.get("lien_ket")) if x.get("lien_ket") else None
        more = f'<span class="icard__more">Xem chi tiết {ARROW}</span>' if href else ""
        if dark:
            tag, attrs = ("a", f' href="{href}"') if href else ("article", "")
            cards.append(f'<{tag} class="ncard ncard--dark reveal"{attrs}><h3>{title}</h3><p>{text}</p>{more}</{tag}>')
            continue
        chip = f'<span class="ichip">{ico(x["bieu_tuong"])}</span>' if x.get("bieu_tuong") else ""
        tag, attrs = ("a", f' href="{href}"') if href else ("article", "")
        if cols == "2":
            cards.append(f'<{tag} class="icard icard--row icard--stack reveal"{attrs}>{chip}<div><h3 class="icard__title">{title}</h3>'
                         f'<p class="icard__text">{text}</p>{more}</div></{tag}>')
        else:
            cards.append(f'<{tag} class="icard reveal"{attrs}>{chip}<h3 class="icard__title">{title}</h3><p class="icard__text">{text}</p>{more}</{tag}>')
    return f"""{sec_open(b, hid)}
  <div class="container">
    {tpl.shead_from(ctx, b, hid, center=b.get("can_giua"))}
    <div class="grid grid--{cols}">
      {"".join(cards)}
    </div>
    {tpl.section_more(ctx, b.get("lien_ket_cuoi"), light=dark)}
  </div>
</section>"""


# ---------------------------------------------------------------------------
# 4. Ảnh + chữ
# ---------------------------------------------------------------------------
def anh_chu(ctx, b, i, page):
    hid = hid_of(b, i)
    checks = b.get("dau_tich") or []
    pcls = "shead__text" if checks else "profile__text"  # có danh sách: đoạn văn là lời dẫn ngắn
    text = "".join(f'<p class="{pcls}">{M.plain(p, ctx)}</p>' for p in paragraphs(b.get("noi_dung")))
    cl = tpl.check_list(checks, "check-list check-list--spaced", ctx) if checks else ""
    facts = ""
    if b.get("so_lieu"):
        facts = '<dl class="profile__facts">' + "".join(
            f'<div><dt>{M.plain(x["nhan"], ctx)}</dt><dd>{M.plain(x["gia_tri"], ctx)}</dd></div>' for x in b["so_lieu"]) + "</dl>"
    copy = f"""<div class="reveal">
      {copy_head(ctx, b, hid)}
      {text}{cl}
      {facts}
      {tpl.section_more(ctx, b.get("lien_ket"))}
    </div>"""
    fig = f"""<figure class="photo reveal">
      {tpl.block_photo(ctx, b, lazy=True)}
      {tpl.figcaption(ctx, b)}
    </figure>"""
    inner = fig + "\n    " + copy if (b.get("vi_tri_anh") or "trai") == "trai" else copy + "\n    " + fig
    return f"""{sec_open(b, hid)}
  <div class="container profile">
    {inner}
  </div>
</section>"""


# ---------------------------------------------------------------------------
# 5. Các bước
# ---------------------------------------------------------------------------
def cac_buoc(ctx, b, i, page):
    hid = hid_of(b, i)
    steps = b.get("buoc") or []
    if b.get("kieu") == "the":
        items = "".join(f'<li class="reveal"><span class="callprep__num">{n}</span><span class="ichip">{ico(x.get("bieu_tuong") or "i-check-circle")}</span>'
                        f'<h3>{M.plain(x["tieu_de"], ctx)}</h3><p>{M.plain(x["mo_ta"], ctx)}</p></li>' for n, x in enumerate(steps, 1))
        lst = f'<ol class="callprep">{items}</ol>'
    else:
        def result(x):
            return f'<p class="steps__result">{ico("i-check-circle")} {M.plain(x["ket_qua"], ctx)}</p>' if x.get("ket_qua") else ""
        items = "".join(f'<li class="reveal"><span class="steps__num">{n}</span><h3>{M.plain(x["tieu_de"], ctx)}</h3>'
                        f'<p>{M.plain(x["mo_ta"], ctx)}</p>{result(x)}</li>' for n, x in enumerate(steps, 1))
        lst = f'<ol class="steps{" steps--5" if len(steps) == 5 else ""}">{items}</ol>'
    notes = ""
    if b.get("ghi_chu"):
        notes = '\n    <div class="assure reveal">' + "".join(
            f'<p>{ico(x["bieu_tuong"])}<span><strong>{M.plain(x["dam"], ctx)}</strong> {M.plain(x["noi_dung"], ctx)}</span></p>'
            for x in b["ghi_chu"]) + "</div>"
    return f"""{sec_open(b, hid, default_bg="kem")}
  <div class="container">
    {tpl.shead_from(ctx, b, hid, link=b.get("lien_ket"), center=b.get("can_giua"))}
    {lst}{notes}
  </div>
</section>"""


# ---------------------------------------------------------------------------
# 6. Dòng thời gian
# ---------------------------------------------------------------------------
def dong_thoi_gian(ctx, b, i, page):
    hid = hid_of(b, i)
    moc = b.get("moc") or []
    items = "".join(f'<li class="{"is-now reveal" if n == len(moc) else "reveal"}"><time>{M.plain(x["thoi_gian"], ctx)}</time>'
                    f'<div><h3>{M.plain(x["tieu_de"], ctx)}</h3><p>{M.plain(x["mo_ta"], ctx)}</p></div></li>' for n, x in enumerate(moc, 1))
    return f"""{sec_open(b, hid)}
  <div class="container">
    {tpl.shead_from(ctx, b, hid)}
    <ol class="timeline">{items}</ol>
  </div>
</section>"""


# ---------------------------------------------------------------------------
# 7. Đội ngũ
# ---------------------------------------------------------------------------
def _has_photo(m):
    return bool(m.get("anh") or m.get("anh_co_san"))


def _facts(ctx, items):
    if not items:
        return ""
    return '<dl class="profile__facts">' + "".join(
        f'<div><dt>{M.plain(x["nhan"], ctx)}</dt><dd>{M.plain(x["gia_tri"], ctx)}</dd></div>' for x in items) + "</dl>"


def _member_card(ctx, m, featured_row=True):
    name = M.plain(m["ten"], ctx)
    mid = M.slugify(M.expand(m["ten"], ctx))
    chip = f'<span class="ichip">{ico(m.get("bieu_tuong") or "i-user")}</span>'
    if featured_row:
        return (f'<div class="icard icard--row icard--stack profile__colleague" id="{mid}">{chip}<div><h3 class="icard__title">{name}</h3>'
                f'<p class="profile__role">{M.plain(m.get("chuc_danh"), ctx)}</p><p class="icard__text">{M.plain(m.get("mo_ta"), ctx)}</p></div></div>')
    top = f'<figure class="team-card__photo">{tpl.block_photo(ctx, m, lazy=True)}</figure>' if _has_photo(m) else chip
    return (f'<article class="icard team-card reveal" id="{mid}">{top}<h3 class="icard__title">{name}</h3>'
            f'<p class="profile__role">{M.plain(m.get("chuc_danh"), ctx)}</p><p class="icard__text">{M.plain(m.get("mo_ta"), ctx)}</p>'
            f'{_facts(ctx, m.get("so_lieu"))}</article>')


def doi_ngu(ctx, b, i, page):
    hid = hid_of(b, i)
    members = b.get("thanh_vien") or []
    head = tpl.shead_from(ctx, b, hid)
    if b.get("kieu", "noi_bat") == "noi_bat" and members and _has_photo(members[0]):
        lead, others = members[0], members[1:]
        body = f"""<div class="profile">
      <figure class="photo reveal">
        {tpl.block_photo(ctx, lead, lazy=True)}
        {tpl.figcaption(ctx, lead)}
      </figure>
      <div class="reveal">
        <h3 class="h2">{M.plain(lead["ten"], ctx)}</h3>
        <p class="profile__role">{M.plain(lead.get("chuc_danh"), ctx)}</p>
        <p class="profile__text">{M.plain(lead.get("mo_ta"), ctx)}</p>
        {_facts(ctx, lead.get("so_lieu"))}
        {"".join(_member_card(ctx, m) for m in others)}
      </div>
    </div>"""
    else:
        body = '<div class="grid grid--3">' + "".join(_member_card(ctx, m, featured_row=False) for m in members) + "</div>"
    return f"""{sec_open(b, hid, default_bg="kem")}
  <div class="container">
    {head}
    {body}
  </div>
</section>"""


# ---------------------------------------------------------------------------
# 8. Danh sách dấu tích
# ---------------------------------------------------------------------------
def dau_tich(ctx, b, i, page):
    hid = hid_of(b, i)
    cls = "check-list check-list--2col" if b.get("so_cot") == "2" else "check-list"
    foot = f'\n        <p class="card__foot">{M.plain(b["ghi_chu_cuoi"], ctx)}</p>' if b.get("ghi_chu_cuoi") else ""
    card = f"""<div class="card card--spaced">
        {tpl.check_list(b.get("muc") or [], cls, ctx)}{foot}
      </div>"""
    text = f'<p class="shead__text">{M.plain(b.get("mo_ta"), ctx)}</p>' if b.get("mo_ta") else ""
    tip = b.get("hop_meo")
    if tip and (tip.get("tieu_de") or tip.get("y")):
        ys = "".join(f'<li><strong>{M.plain(y["dam"], ctx)}</strong> {M.plain(y["noi_dung"], ctx)}</li>' for y in tip.get("y") or [])
        aside = f"""<aside class="context__dark tipbox reveal">
      {f'<p class="eyebrow">{M.plain(tip.get("nhan"), ctx)}</p>' if tip.get("nhan") else ""}
      {f'<h3>{M.plain(tip.get("tieu_de"), ctx)}</h3>' if tip.get("tieu_de") else ""}
      {f'<p>{M.plain(tip.get("mo_ta"), ctx)}</p>' if tip.get("mo_ta") else ""}
      {f'<ol class="tips">{ys}</ol>' if ys else ""}
    </aside>"""
        return f"""{sec_open(b, hid)}
  <div class="container split">
    <div class="reveal">
      {copy_head(ctx, b, hid)}
      {text}
      {card}
    </div>
    {aside}
  </div>
</section>"""
    return f"""{sec_open(b, hid)}
  <div class="container">
    {tpl.shead_from(ctx, b, hid)}
    <div class="reveal">{card}</div>
  </div>
</section>"""


# ---------------------------------------------------------------------------
# 9. Đoạn văn tự do
# ---------------------------------------------------------------------------
def doan_van(ctx, b, i, page):
    narrow = (b.get("do_rong") or "hep") == "hep"
    return f"""{sec_open(b)}
  <div class="container">
    <div class="prose{" prose--narrow" if narrow else ""} reveal">{M.block(b.get("noi_dung"), ctx, ids=page["ids"])}</div>
  </div>
</section>"""


# ---------------------------------------------------------------------------
# 10. Hỏi đáp
# ---------------------------------------------------------------------------
def hoi_dap(ctx, b, i, page):
    hid = hid_of(b, i)
    items = [tpl.S.faq_by_id[x] for x in b.get("cau_hoi") or [] if x in tpl.S.faq_by_id]
    text = f'\n      <p class="shead__text">{M.plain(b.get("mo_ta"), ctx)}</p>' if b.get("mo_ta") else ""
    more = f'\n      {tpl.section_more(ctx, [b.get("lien_ket")])}' if b.get("lien_ket") else ""
    return f"""{sec_open(b, hid)}
  <div class="container split">
    <div class="reveal">
      {copy_head(ctx, b, hid)}{text}{more}
    </div>
    <div class="reveal">{tpl.faq_list(ctx, items)}</div>
  </div>
</section>"""


# ---------------------------------------------------------------------------
# 11. Lưới lĩnh vực (tự động)
# ---------------------------------------------------------------------------
def luoi_linh_vuc(ctx, b, i, page):
    hid = hid_of(b, i)
    grid = tpl.services_grid(ctx.r) if b.get("kieu") == "dich_vu" else tpl.problems_grid(ctx.r)
    return f"""{sec_open(b, hid, default_bg="kem")}
  <div class="container">
    {tpl.shead_from(ctx, b, hid, link=b.get("lien_ket"))}
    {grid}
  </div>
</section>"""


# ---------------------------------------------------------------------------
# 12. Bài viết mới nhất (tự động)
# ---------------------------------------------------------------------------
def bai_viet_moi(ctx, b, i, page):
    hid = hid_of(b, i)
    items = tpl.S.articles
    if b.get("linh_vuc"):
        items = [a for a in items if a["linh_vuc"] == b["linh_vuc"] or b["linh_vuc"] in a["linh_vuc_lien_quan"]]
    items = items[: b.get("so_bai") or 3]
    if not items:
        return ""
    cols = b.get("so_cot") or "3"
    return f"""{sec_open(b, hid, default_bg="kem")}
  <div class="container">
    {tpl.shead_from(ctx, b, hid, link=b.get("lien_ket"))}
    {tpl.articles_grid(ctx.r, items, cls=f"grid grid--{cols}")}
  </div>
</section>"""


# ---------------------------------------------------------------------------
# 13. Giấy tờ theo lĩnh vực (tự động)
# ---------------------------------------------------------------------------
def giay_to_linh_vuc(ctx, b, i, page):
    hid = hid_of(b, i)
    only = b.get("linh_vuc") or []
    items = [tpl.S.service_by_slug[x] for x in only if x in tpl.S.service_by_slug] if only else tpl.S.services
    cards = "".join(
        f'<article class="reveal"{tpl.cms(s["_src"], "giay_to", "Giấy tờ – " + s["ten"])}><h3><span class="ichip ichip--sm">{ico(s["bieu_tuong"], "")}</span>{esc(s["ten"])}</h3>'
        f'{tpl.check_list((s.get("giay_to") or {}).get("danh_sach") or [])}'
        f'<a class="link-arrow" href="{ctx.r}dich-vu/{s["slug"]}/#ho-so">Xem chi tiết {ARROW}</a></article>' for s in items)
    return f"""{sec_open(b, hid, default_bg="kem")}
  <div class="container">
    {tpl.shead_from(ctx, b, hid)}
    <div class="docs">{cards}</div>
  </div>
</section>"""


# ---------------------------------------------------------------------------
# 14. Kênh liên hệ
# ---------------------------------------------------------------------------
def kenh_lien_he(ctx, b, i, page):
    f = F()
    base = tpl.S.text.get("lien_he_cuoi_trang") or {}
    note = (lambda k, d="": M.plain(b.get(k) or d, ctx))
    cards = {
        "goi": f'<a class="cband__card" href="tel:{f["phone_tel"]}">{ico("i-phone")}<span>Gọi điện</span><strong>{esc(f["phone"])}</strong>'
               f'<small>{note("ghi_chu_goi", "{{gio_lam_viec}}")}</small></a>',
        "zalo": f'<a class="cband__card cband__card--zalo" href="{esc(f["zalo"])}" target="_blank" rel="noopener">{ico("i-chat")}<span>Nhắn Zalo</span>'
                f'<strong>{esc(f["phone"])}</strong><small>{note("ghi_chu_zalo", base.get("ghi_chu_zalo") or "")}</small></a>',
        "email": f'<a class="cband__card" href="mailto:{esc(f["email"])}">{ico("i-mail")}<span>Gửi email</span>'
                 f'<strong class="cband__email">{esc(f["email"])}</strong><small>{note("ghi_chu_email")}</small></a>',
        "van_phong": f'<a class="cband__card" href="https://www.google.com/maps/dir/?api=1&amp;destination={f["maps_query"]}" target="_blank" rel="noopener">'
                     f'{ico("i-pin")}<span>Đến văn phòng</span><strong>{esc(f["street"])}</strong><small>{esc(f["ward"])}, {esc(f["city_short"])} · '
                     f'{M.plain(base.get("ghi_chu_van_phong"), ctx)}</small></a>',
    }
    picked = "\n      ".join(cards[k] for k in b.get("kenh") or ["goi", "zalo", "email"] if k in cards)
    urgent = ""
    if b.get("viec_gap", True):
        label = M.plain((tpl.S.text.get("viec_gap") or {}).get("nhan") or "Việc gấp?", ctx)
        body = M.inline(b.get("noi_dung_viec_gap") or (tpl.S.text.get("viec_gap") or {}).get("noi_dung"), ctx)
        urgent = f'\n    <p class="urgent">{ico("i-alert")}<span><strong>{label}</strong> {body}</span></p>'
    return f"""{sec_open(b, aria_label="Cách liên hệ luật sư")}
  <div class="container">
    <div class="cband__cards">
      {picked}
    </div>{urgent}
  </div>
</section>"""


# ---------------------------------------------------------------------------
# 15. Bản đồ văn phòng
# ---------------------------------------------------------------------------
def ban_do(ctx, b, i, page):
    f = F()
    hid = hid_of(b, i)
    q = f["maps_query"]
    text = f'\n      <p class="shead__text">{M.plain(b.get("mo_ta"), ctx)}</p>' if b.get("mo_ta") else ""
    hot = f'<small>{M.plain(b.get("ghi_chu_hotline"), ctx)}</small>' if b.get("ghi_chu_hotline") else ""
    return f"""{sec_open(b, hid)}
  <div class="container split split--media">
    <div class="reveal">
      {copy_head(ctx, b, hid)}{text}
      <ul class="contact__list">
        <li><span class="ichip ichip--sm">{ico("i-pin")}</span><div><strong>Địa chỉ</strong>{esc(f["address"])}</div></li>
        <li><span class="ichip ichip--sm">{ico("i-phone")}</span><div><strong>Hotline, Zalo</strong><a href="tel:{f["phone_tel"]}">{esc(f["phone"])}</a>{hot}</div></li>
        <li><span class="ichip ichip--sm">{ico("i-mail")}</span><div><strong>Email</strong><a href="mailto:{esc(f["email"])}">{esc(f["email"])}</a></div></li>
        <li><span class="ichip ichip--sm">{ico("i-clock")}</span><div><strong>Giờ làm việc</strong>{esc(f["hours"])} {tpl.open_now()}<small>{esc(f["hours_note"])}</small></div></li>
      </ul>
      <div class="map-links">
        <a class="btn btn--primary btn--sm" href="https://www.google.com/maps/dir/?api=1&amp;destination={q}" target="_blank" rel="noopener">{ico("i-pin")} Chỉ đường</a>
        <a class="btn btn--outline btn--sm" href="https://www.google.com/maps/search/?api=1&amp;query={q}" target="_blank" rel="noopener">Mở Google Maps</a>
      </div>
    </div>
    <div class="map reveal" data-map="https://www.google.com/maps?q={q}&amp;hl=vi&amp;z=17&amp;output=embed">
      <button class="map__load" type="button">
        {ico("i-pin", "map__pin")}
        <strong>Bấm để xem bản đồ</strong>
        <small>{esc(f["address"])}</small>
        <span class="map__note">Bản đồ chỉ tải khi anh chị bấm, để hạn chế chia sẻ dữ liệu với bên thứ ba.</span>
      </button>
    </div>
  </div>
</section>"""


RENDER = {name: globals()[name] for name in BLOCK_BY_NAME}


def render(ctx, page, blocks):
    out = []
    for i, b in enumerate(blocks, 1):
        if not b.get("hien_thi", True):
            continue
        t = BLOCK_BY_NAME[b["loai"]]
        c = ctx.at(where=f"Các khối trên trang › Khối {i} ({t['label'].split('·')[-1].strip()})")
        out.append(RENDER[b["loai"]](c, b, i, page))
    return "\n\n".join(x for x in out if x)
