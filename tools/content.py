# -*- coding: utf-8 -*-
"""Nạp toàn bộ nội dung trong content/, kiểm theo schema và kiểm chéo giữa các tệp.

Kết quả là đối tượng Site: thông tin công ty, menu, câu chữ, lĩnh vực, bài viết, hỏi đáp, các trang.
Mọi lỗi được gom vào LOI (tools/loi.py) kèm tên tệp + tên trường theo đúng nhãn trong CMS.
"""
import glob
import json
import os
import re
import urllib.parse

import yaml

import schema
from loi import LOI
from markup import SLUG_RE, Ctx, company_tokens, expand, slugify

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


if getattr(yaml, "__with_libyaml__", False):
    class _Yaml12CLoader(yaml.CSafeLoader):
        """Cùng quy tắc YAML 1.2 nhưng phần phân tích chạy bằng libyaml (C): nhanh ~10 lần. Pyodide (khung mô phỏng)
        không có libyaml → dùng Yaml12Loader (Python thuần), kết quả như nhau."""
    _Yaml12CLoader.yaml_implicit_resolvers = Yaml12Loader.yaml_implicit_resolvers
    _Yaml12CLoader.yaml_constructors = Yaml12Loader.yaml_constructors
    _LOADER = _Yaml12CLoader
else:
    _LOADER = Yaml12Loader


def yaml_load(text):
    if text.lstrip().startswith("{"):  # bản đang sửa do khung mô phỏng ghi (JSON = YAML 1.2 hợp lệ): đọc thẳng, nhanh hơn nhiều
        try:
            return json.loads(text)
        except ValueError:
            pass
    return yaml.load(text, Loader=_LOADER)


def rel(path):
    return os.path.relpath(path, ROOT)


def _copy(v):
    """Bản sao sâu cho dữ liệu đọc từ YAML (dict/list lồng nhau; giá trị đơn – chữ, số, ngày – không đổi được nên dùng chung)."""
    if isinstance(v, dict):
        return {k: _copy(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_copy(x) for x in v]
    return v


# Tệp đã đọc: đường dẫn → (nội dung chữ, dữ liệu). Khung mô phỏng dựng lại trang theo từng chữ gõ: chỉ tệp đang sửa
# đổi nội dung, các tệp khác lấy lại từ đây thay vì phân tích YAML lại (phần tốn thời gian nhất trong Pyodide).
_PARSED = {}


def read_file(path):
    """Đọc YAML hoặc Markdown có front matter. Trả về dict (thân bài Markdown ở khóa "body")."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        LOI.them(rel(path), "", f"Không đọc được tệp: {e}")
        return None
    hit = _PARSED.get(path)
    if hit and hit[0] == text:
        return _copy(hit[1])  # bản sao: bước kiểm và dựng trang có thể sửa dữ liệu
    data = _parse(path, text)
    if data is not None:
        _PARSED[path] = (text, _copy(data))
    return data


def _parse(path, text):
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
    return {c["name"]: c for c in schema.data_collections() if not c.get("divider")}


def load_folder(col, site):
    entries = []
    for path in sorted(glob.glob(os.path.join(ROOT, col["folder"], "*." + col["extension"]))):
        slug = os.path.splitext(os.path.basename(path))[0]
        if slug.startswith("_"):  # _index: trang tổng quan của mục (Dịch vụ, Bài viết pháp lý), đọc riêng
            continue
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
        "footer_about": c.get("gioi_thieu_chan_trang") or "", "tax_id": str(c.get("ma_so_thue") or ""),
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


def literal_patterns(firm):
    """Mẫu tìm hotline/email gõ thẳng vào nội dung (thay vì mã chèn) – chúng sẽ không đổi theo Thông tin công ty."""
    out = []
    digits = firm["phone_tel"]
    if len(digits) == 10:
        sep = r"[\s.\-]?"
        body = sep.join(digits[1:])
        out.append((re.compile(rf"(?<!\d)(?:0|\+?84{sep}){body}(?!\d)"),
                    "Đang ghi thẳng số hotline “{}”. Thay bằng mã {{{{hotline}}}} (chữ) hoặc {{{{tel}}}} / {{{{zalo}}}} "
                    "(địa chỉ liên kết) để số tự đổi khi sửa ở Cài đặt chung → Thông tin công ty."))
    if firm["email"]:
        out.append((re.compile(re.escape(firm["email"]), re.I),
                    "Đang ghi thẳng email “{}”. Thay bằng mã {{{{email}}}} (chữ) hoặc {{{{mailto}}}} (địa chỉ liên kết) "
                    "để tự đổi khi sửa ở Cài đặt chung → Thông tin công ty."))
    return out


SEO_LABELS = (("tieu_de", "SEO – hiển thị trên Google và khi chia sẻ › Tiêu đề trên Google"),
              ("mo_ta", "SEO – hiển thị trên Google và khi chia sẻ › Mô tả trên Google"))


def expand_seo(site, item):
    """Cho phép mã chèn ({{hotline}}…) trong tiêu đề, mô tả SEO; kiểm độ dài sau khi thay."""
    seo = item.get("seo") if isinstance(item, dict) else None
    if not isinstance(seo, dict):
        return
    src = item.get("_src", "")
    for key, where in SEO_LABELS:
        v = seo.get(key)
        if isinstance(v, str) and "{{" in v:
            seo[key] = expand(v, Ctx(site, "", "", src, where))
            limit = 160 if key == "mo_ta" else 60
            if len(seo[key]) > limit:
                LOI.them(src, where, f"Sau khi thay mã chèn, dài {len(seo[key])} ký tự (tối đa {limit}). Rút ngắn câu chữ.")


def load(env):
    site = Site(env)
    cols = _collections()
    cd = cols["cai_dat"]
    site.company = load_file(cd, "cong_ty", site)
    site.firm = firm_from(site.company)
    site.tokens = company_tokens(site.firm)
    site.literals = literal_patterns(site.firm)
    site.menu = load_file(cd, "menu", site)
    site.text = load_file(cd, "cau_chu", site)
    site.seo = load_file(cd, "seo", site)
    site.tracking = load_file(cd, "theo_doi", site)
    site.redirects = load_file(cd, "chuyen_huong", site).get("chuyen_huong") or []
    site.brand = load_file(cd, "anh_thuong_hieu", site)

    all_services = load_folder(cols["dich_vu"], site)
    all_articles = load_folder(cols["bai_viet"], site)
    all_pages = load_folder(cols["trang"], site)
    for p in all_pages:  # trang cố định trên menu luôn được đăng (CMS không có ô Bản nháp cho chúng)
        if p["slug"] in schema.FIXED_SLUGS:
            p["nhap"] = False
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

    for a in all_articles:
        a["ngay_cap_nhat"] = a.get("ngay_cap_nhat") or a.get("ngay_dang")
        a["linh_vuc_lien_quan"] = a.get("linh_vuc_lien_quan") or ([a["linh_vuc"]] if a.get("linh_vuc") else [])
        _check_article_path(a)
    for x in all_services + all_articles + all_pages + list(site.hubs.values()) + list(site.legal.values()) + [site.not_found]:
        expand_seo(site, x)
    site.draft_items = [x for x in all_services + all_articles + all_pages if x.get("nhap")]
    site.services = sorted(visible(all_services), key=lambda s: (s.get("thu_tu") or 99, s.get("ten") or ""))
    site.service_by_slug = {s["slug"]: s for s in site.services}
    site.all_service_slugs = {s["slug"] for s in all_services}
    site.articles = sorted(visible(all_articles), key=lambda a: (a.get("ngay_dang") or "", a.get("tieu_de") or ""), reverse=True)
    site.pages = {p["slug"]: p for p in visible(all_pages)}

    _check(site, all_pages)
    return site


def _check_article_path(a):
    """Ô “Đường dẫn bài viết” phải khớp tên tệp (CMS đặt tên tệp từ ô này lúc tạo bài, sau đó khóa)."""
    want, slug = a.get("duong_dan"), a["slug"]
    if not want or want == slug:
        return
    where = "Đường dẫn bài viết (đặt 1 lần)"
    if re.fullmatch(re.escape(want) + r"-\d+", slug):
        LOI.them(a["_src"], where, f"Đường dẫn “{want}” đã có bài khác dùng nên CMS lưu bài này thành “{slug}”. "
                                   f"Xóa bài này rồi tạo lại với đường dẫn khác.")
    else:
        LOI.them(a["_src"], where, f"Ô này đã đổi thành “{want}” nhưng địa chỉ bài vẫn là “{slug}” – đường dẫn không đổi được "
                                   f"sau khi lưu. Trả ô về “{slug}”. Cần đổi địa chỉ: tạo bài mới và thêm chuyển hướng "
                                   f"(Cài đặt chung → Chuyển hướng).")


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
                    LOI.them(p["_src"], f"Các khối trên trang › Khối {i} (Hỏi đáp)", f"Câu hỏi “{fid}” không còn trong Kho câu hỏi dùng chung (mục Câu hỏi thường gặp).")
    # Lĩnh vực: không tự liên quan tới chính mình
    for s in site.services:
        if s["slug"] in (s.get("linh_vuc_lien_quan") or []):
            LOI.them(s["_src"], "Lĩnh vực liên quan", "Không chọn chính lĩnh vực này.")
    _check_menu(site, all_pages)
    _check_service_cards(site)


MENU_SRC = "content/cai-dat/menu.yml"


def _check_menu(site, all_pages):
    """Logic menu và thứ tự lĩnh vực. Chỉ cảnh báo (không chặn đăng): những chỗ làm menu hiện khác điều người sửa nghĩ.
    Chạy cả trong khung mô phỏng: sửa menu là thấy cảnh báo ngay, trước khi Lưu."""
    items = site.menu.get("menu") or []
    drafts = {"/" + p["slug"] + "/" for p in all_pages if p.get("nhap")}
    first_at = {}  # trang → mục menu đầu tiên chứa nó
    for i, it in enumerate(items, 1):
        where = f"Menu chính › Mục {i} ({it.get('nhan') or ''})"
        children = [x.get("trang") for x in it.get("muc_con") or [] if x.get("trang")]
        dup = {p for p in children if children.count(p) > 1}
        for p in sorted(dup):
            LOI.canh(MENU_SRC, where, f"Trang “{p}” có 2 dòng trong cùng menu xổ. Xóa bớt một dòng.")
        for p in dict.fromkeys(([it["trang"]] if it.get("trang") else []) + children):
            if p in first_at:
                LOI.canh(MENU_SRC, where, f"Trang “{p}” đã nằm ở mục “{first_at[p]}”. Khi người đọc ở trang này, menu chỉ tô sáng "
                                          f"mục “{first_at[p]}”; nên để mỗi trang ở một mục.")
            else:
                first_at[p] = it.get("nhan") or ""
            if p in drafts and not site.drafts:
                LOI.canh(MENU_SRC, where, f"Trang “{p}” đang là bản nháp nên chưa hiện trên menu của website. Bỏ dấu Bản nháp ở trang đó "
                                          f"để hiện.")
        if it.get("loai") != "menu_linh_vuc":
            continue
        groups = it.get("nhom") or []
        placed = {}
        for g in groups:
            for slug in g.get("linh_vuc") or []:
                if slug in placed:
                    LOI.canh(MENU_SRC, f"{where} › Nhóm “{g.get('ten_nhom') or ''}”",
                             f"Lĩnh vực “{slug}” đã nằm ở nhóm “{placed[slug]}”: menu chỉ hiện ở nhóm đầu. Xóa dòng trùng.")
                else:
                    placed[slug] = g.get("ten_nhom") or ""
        missing = [s["ten"] for s in site.services if s["slug"] not in placed]
        if missing and groups:
            LOI.canh(MENU_SRC, f"{where} › Nhóm lĩnh vực",
                     f"Chưa xếp vào nhóm nào: {', '.join(missing)} – đang tự nằm cuối nhóm “{groups[-1].get('ten_nhom') or ''}”. "
                     f"Thêm vào nhóm phù hợp để chọn đúng vị trí.")
    for slug in dict.fromkeys(site.menu.get("linh_vuc_chan_trang") or []):
        if slug not in site.all_service_slugs:
            LOI.canh(MENU_SRC, "Thứ tự lĩnh vực ở chân trang", f"Lĩnh vực “{slug}” không còn tồn tại – dòng này bị bỏ qua. Xóa dòng đó.")


def _check_service_cards(site):
    """Khối lưới lĩnh vực (Trang tổng quan Dịch vụ): mỗi lĩnh vực đã đăng nên có thẻ riêng."""
    src = schema.HUB_FILES["dich_vu"]
    where = "Khối lưới lĩnh vực › Các thẻ lĩnh vực"
    cards = ((site.hubs.get("dich_vu") or {}).get("luoi") or {}).get("the") or []
    have = set()
    for i, c in enumerate(cards, 1):
        slug = (c or {}).get("linh_vuc")
        if slug and slug not in site.all_service_slugs:
            LOI.canh(src, f"{where} › Thẻ {i}", f"Lĩnh vực “{slug}” không còn tồn tại – thẻ này bị bỏ qua. Xóa thẻ hoặc chọn lĩnh vực khác.")
        have.add(slug)
    missing = [s["ten"] for s in site.services if s["slug"] not in have]
    if missing:
        LOI.canh(src, where, f"Chưa có thẻ cho: {', '.join(missing)} – lưới đang tạm hiện tên + mô tả ngắn ở cuối. "
                             f"Thêm thẻ để viết tình huống và chọn vị trí.")
