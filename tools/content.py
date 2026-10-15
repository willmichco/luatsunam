# -*- coding: utf-8 -*-
"""Nạp toàn bộ nội dung trong content/, kiểm theo schema và kiểm chéo giữa các tệp.

Kết quả là đối tượng Site: thông tin công ty, menu, câu chữ, lĩnh vực, bài viết, hỏi đáp, các trang.
Mọi lỗi được gom vào LOI (tools/loi.py) kèm tên tệp + tên trường theo đúng nhãn trong CMS.
"""
import glob
import os
import re
import urllib.parse

import yaml

import schema
from loi import LOI
from markup import SLUG_RE, company_tokens, slugify

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Đường dẫn cấp 1 đã dùng cho trang cố định: trang dựng từ khối không được trùng
RESERVED = {"dich-vu", "kien-thuc-phap-ly", "cau-hoi-thuong-gap", "chinh-sach-bao-mat", "dieu-khoan-su-dung",
            "mien-tru-trach-nhiem", "admin", "nhap", "assets", "content", "404"}
HOME_SLUG = "trang-chu"
DAY_NUM = {"Sunday": 0, "Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5, "Saturday": 6}
DAY_VI = {"Monday": "Thứ 2", "Tuesday": "Thứ 3", "Wednesday": "Thứ 4", "Thursday": "Thứ 5", "Friday": "Thứ 6",
          "Saturday": "Thứ 7", "Sunday": "Chủ nhật"}
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class Yaml12Loader(yaml.SafeLoader):
    """Đọc YAML theo chuẩn 1.2 như Sveltia CMS ghi: "17:30" là chữ (không phải số cơ số 60),
    "yes/no/on/off" là chữ (chỉ true/false là đúng/sai)."""


Yaml12Loader.yaml_implicit_resolvers = {
    k: [(tag, rx) for tag, rx in v if tag not in ("tag:yaml.org,2002:bool", "tag:yaml.org,2002:int", "tag:yaml.org,2002:float")]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()}
Yaml12Loader.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"), list("tTfF"))
Yaml12Loader.add_implicit_resolver("tag:yaml.org,2002:int", re.compile(r"^(?:[-+]?[0-9]+|0o[0-7]+|0x[0-9a-fA-F]+)$"), list("-+0123456789"))
Yaml12Loader.add_implicit_resolver("tag:yaml.org,2002:float", re.compile(
    r"^(?:[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$"), list("-+0123456789."))


def _int12(loader, node):
    v = loader.construct_scalar(node)
    if v.startswith(("0x", "0o")):
        return int(v[2:], 16 if v[1] == "x" else 8)
    return int(v)


Yaml12Loader.add_constructor("tag:yaml.org,2002:int", _int12)


def yaml_load(text):
    return yaml.load(text, Loader=Yaml12Loader)


def rel(path):
    return os.path.relpath(path, ROOT)


def read_file(path):
    """Đọc YAML hoặc Markdown có front matter. Trả về dict (thân bài Markdown ở khóa "body")."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        LOI.them(rel(path), "", f"Không đọc được tệp: {e}")
        return None
    try:
        if path.endswith(".md"):
            m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
            if not m:
                LOI.them(rel(path), "", "Thiếu phần thông tin đầu tệp (front matter giữa hai dòng ---).")
                return None
            data = yaml_load(m.group(1)) or {}
            data["body"] = m.group(2).strip()
            return data
        return yaml_load(text) or {}
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        where = f" (dòng {mark.line + 1})" if mark else ""
        LOI.them(rel(path), "", f"Tệp sai cú pháp{where}: {getattr(e, 'problem', e)}. Mở lại trong CMS và lưu lại để sửa.")
        return None


class Site:
    def __init__(self, env):
        self.env = env
        self.drafts = env["drafts"]
        self.site_url = env["site_url"]
        self.internal_prefixes = env["internal_prefixes"]
        self.link_refs = []
        self.relations = []
        self._img = {}

    # -- tiện ích cho markup.py -------------------------------------------------
    def image_size(self, url):
        path = url.split("?")[0]
        if not path.startswith("/") or not re.search(r"\.(webp|jpe?g|png|avif|gif)$", path, re.I):
            return None
        if path not in self._img:
            full = os.path.join(ROOT, path.lstrip("/"))
            try:
                from PIL import Image
                with Image.open(full) as im:
                    self._img[path] = im.size
            except Exception:  # ảnh không mở được: kiểm ở bước kiểm liên kết
                self._img[path] = None
        return self._img[path]


def _collections():
    return {c["name"]: c for c in schema.collections() if not c.get("divider")}


def load_folder(col, site):
    entries = []
    for path in sorted(glob.glob(os.path.join(ROOT, col["folder"], "*." + col["extension"]))):
        slug = os.path.splitext(os.path.basename(path))[0]
        src = rel(path)
        if not SLUG_RE.match(slug) or len(slug) > 60:
            LOI.them(src, "Đường dẫn", f"Tên tệp/đường dẫn “{slug}” không hợp lệ: chỉ a–z, 0–9, gạch nối, tối đa 60 ký tự.")
        data = read_file(path)
        if data is None:
            continue
        norm = schema.validate_entry(data, col["fields"], src, site, col.get("_rules", ()))
        norm["slug"], norm["_src"] = slug, src
        entries.append(norm)
    return entries


def load_file(col, name, site):
    f = next(x for x in col["files"] if x["name"] == name)
    path = os.path.join(ROOT, f["file"])
    src = rel(path)
    data = read_file(path)
    if data is None:
        return {"_src": src}
    norm = schema.validate_entry(data, f["fields"], src, site, f.get("_rules", ()))
    norm["_src"] = src
    return norm


def firm_from(c):
    """Thông tin công ty → dạng dùng trong template (giữ tên khóa cũ của data.py)."""
    digits = re.sub(r"\D", "", c.get("hotline") or "")
    addr = c.get("dia_chi") or {}
    gio = c.get("gio_lam_viec") or {}
    days = sorted(gio.get("ngay") or [], key=DAY_ORDER.index)
    hours = gio.get("hien_thi") or _hours_text(days, gio.get("mo_cua"), gio.get("dong_cua"))
    firm = {
        "legal_name": c.get("ten_phap_nhan") or "", "short_name": c.get("ten_ngan") or "", "brand": c.get("thuong_hieu") or "",
        "slogan": c.get("khau_hieu") or "", "lawyer": c.get("luat_su") or "", "lawyer_role": c.get("chuc_danh_luat_su") or "",
        "phone": c.get("hotline") or "", "phone_tel": digits, "phone_intl": "+84" + digits[1:] if digits.startswith("0") else digits,
        "email": c.get("email") or "", "zalo": c.get("zalo") or f"https://zalo.me/{digits}",
        "street": addr.get("so_nha_duong") or "", "ward": addr.get("phuong") or "", "city": addr.get("thanh_pho") or "",
        "city_short": addr.get("thanh_pho_viet_tat") or addr.get("thanh_pho") or "",
        "hours": hours, "hours_note": gio.get("ngoai_gio") or "",
        "open_days": days, "opens": gio.get("mo_cua") or "08:00", "closes": gio.get("dong_cua") or "17:30",
        "footer_about": c.get("gioi_thieu_chan_trang") or "",
    }
    firm["address"] = f'{firm["street"]}, {firm["ward"]}, {firm["city"]}'
    firm["maps_query"] = urllib.parse.quote(firm["address"], safe="")
    if digits and len(digits) != 10:
        LOI.them("content/cai-dat/cong-ty.yml", "Hotline", f"Số điện thoại cần đủ 10 chữ số (đang có {len(digits)}).")
    if firm["opens"] >= firm["closes"]:
        LOI.them("content/cai-dat/cong-ty.yml", "Giờ làm việc", "Giờ đóng cửa phải sau giờ mở cửa.")
    return firm


def _hours_text(days, opens, closes):
    """["Monday"…"Friday"], 08:00, 17:30 → "Thứ 2 – Thứ 6: 08:00 – 17:30"."""
    if not days:
        return ""
    idx = [DAY_ORDER.index(d) for d in days]
    runs, start = [], idx[0]
    for a, b in zip(idx, idx[1:] + [None]):
        if b != a + 1:
            runs.append((start, a))
            start = b
    parts = [DAY_VI[DAY_ORDER[s]] if s == e else f"{DAY_VI[DAY_ORDER[s]]} – {DAY_VI[DAY_ORDER[e]]}" for s, e in runs]
    return f'{", ".join(parts)}: {opens} – {closes}'


def load(env):
    site = Site(env)
    cols = _collections()
    cd = cols["cai_dat"]
    site.company = load_file(cd, "cong_ty", site)
    site.firm = firm_from(site.company)
    site.tokens = company_tokens(site.firm)
    site.menu = load_file(cd, "menu", site)
    site.text = load_file(cd, "cau_chu", site)
    site.seo = load_file(cd, "seo", site)
    site.tracking = load_file(cd, "theo_doi", site)
    site.redirects = load_file(cd, "chuyen_huong", site).get("chuyen_huong") or []
    site.brand = load_file(cd, "anh_thuong_hieu", site)

    all_services = load_folder(cols["dich_vu"], site)
    all_articles = load_folder(cols["bai_viet"], site)
    all_pages = load_folder(cols["trang"], site)
    site.faq = load_file(cols["hoi_dap"], "hoi_dap", site).get("cau_hoi") or []
    for i, f in enumerate(site.faq, 1):
        if not f.get("ma"):  # câu hỏi mới chưa đặt mã neo: tự tạo từ câu hỏi
            f["ma"] = slugify(f.get("hoi") or f"cau-hoi-{i}", 60)
    ids = [f["ma"] for f in site.faq]
    for m in {x for x in ids if ids.count(x) > 1}:
        LOI.them("content/hoi-dap.yml", "Câu hỏi", f"Mã neo “{m}” bị trùng giữa các câu hỏi; đặt mã khác cho một câu.")
    site.faq_by_id = {f["ma"]: f for f in site.faq if f.get("ma")}
    th = cols["trang_tong_hop"]
    site.hubs = {n: load_file(th, n, site) for n in ("dich_vu", "kien_thuc", "hoi_dap")}
    tv = cols["trang_van_ban"]
    site.legal = {n: load_file(tv, n.replace("-", "_"), site) for n in ("chinh-sach-bao-mat", "dieu-khoan-su-dung", "mien-tru-trach-nhiem")}
    site.not_found = load_file(tv, "trang_404", site)

    def visible(items):
        return [x for x in items if site.drafts or not x.get("nhap")]

    site.draft_items = [x for x in all_services + all_articles + all_pages if x.get("nhap")]
    site.services = sorted(visible(all_services), key=lambda s: (s.get("thu_tu") or 99, s.get("ten") or ""))
    site.service_by_slug = {s["slug"]: s for s in site.services}
    site.all_service_slugs = {s["slug"] for s in all_services}
    site.articles = sorted(visible(all_articles), key=lambda a: (a.get("ngay_dang") or "", a.get("tieu_de") or ""), reverse=True)
    for a in site.articles:
        a["ngay_cap_nhat"] = a.get("ngay_cap_nhat") or a.get("ngay_dang")
        a["linh_vuc_lien_quan"] = a.get("linh_vuc_lien_quan") or ([a["linh_vuc"]] if a.get("linh_vuc") else [])
    site.pages = {p["slug"]: p for p in visible(all_pages)}

    _check(site, all_pages)
    return site


def _check(site, all_pages):
    # Lĩnh vực được chọn phải tồn tại (và đã đăng, với bản chính thức)
    for src, where, col, value in site.relations:
        if col != "dich_vu" or not value:
            continue
        if value not in site.all_service_slugs:
            LOI.them(src, where, f"Lĩnh vực “{value}” không tồn tại. Chọn lại từ danh sách.")
        elif value not in site.service_by_slug:
            LOI.them(src, where, f"Lĩnh vực “{value}” đang là bản nháp nên chưa có trên site. Đăng lĩnh vực đó trước, hoặc chọn lĩnh vực khác.")
    # Trang chủ bắt buộc; đường dẫn không trùng trang cố định
    if HOME_SLUG not in {p["slug"] for p in all_pages}:
        LOI.them("content/trang/", "", "Thiếu Trang chủ (content/trang/trang-chu.yml). Không được xóa Trang chủ.")
    elif HOME_SLUG not in site.pages:
        LOI.them(f"content/trang/{HOME_SLUG}.yml", "Bản nháp", "Trang chủ không được để ở trạng thái bản nháp.")
    for p in all_pages:
        if p["slug"] in RESERVED:
            LOI.them(p["_src"], "Đường dẫn", f"Đường dẫn “/{p['slug']}/” trùng với trang cố định của website. Tạo lại trang với đường dẫn khác.")
        blocks = [b for b in p.get("cac_khoi") or [] if b.get("hien_thi", True)]
        has_hero = bool(blocks) and blocks[0].get("loai") == "dau_trang"
        if p["slug"] != HOME_SLUG and not has_hero and not (p.get("dau_trang") or {}).get("tieu_de"):
            LOI.them(p["_src"], "Đầu trang tiêu chuẩn › Tiêu đề lớn của trang (H1)",
                     "Trang cần tiêu đề: điền ô này, hoặc đặt khối “Đầu trang lớn (Hero)” lên đầu.")
        if not blocks:
            LOI.them(p["_src"], "Các khối trên trang", "Trang cần ít nhất 1 khối đang hiển thị.")
        anchors = [b.get("ma_neo") for b in p.get("cac_khoi") or [] if b.get("ma_neo")]
        for a in set(anchors):
            if anchors.count(a) > 1:
                LOI.them(p["_src"], "Các khối trên trang", f"Mã neo “{a}” dùng cho nhiều khối; mỗi khối cần mã neo riêng.")
        for i, b in enumerate(p.get("cac_khoi") or [], 1):
            for fid in b.get("cau_hoi") or []:
                if fid not in site.faq_by_id:
                    LOI.them(p["_src"], f"Các khối trên trang › Khối {i} (Hỏi đáp)", f"Câu hỏi “{fid}” không còn trong kho Hỏi đáp chung.")
    # Lĩnh vực: không tự liên quan tới chính mình
    for s in site.services:
        if s["slug"] in (s.get("linh_vuc_lien_quan") or []):
            LOI.them(s["_src"], "Lĩnh vực liên quan", "Không chọn chính lĩnh vực này.")
