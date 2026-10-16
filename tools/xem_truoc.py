# -*- coding: utf-8 -*-
"""Khung mô phỏng trong /admin: dựng 1 trang từ BẢN ĐANG SỬA bằng đúng code build của site.

Chạy trong trình duyệt (Pyodide) – admin/xem-truoc.js nạp gói admin/xem-truoc/goi.zip do build sinh ra
(tools/*.py + content/ + thư viện Python thuần), rồi gọi render() mỗi lần người dùng gõ.
Chạy trên máy để thử:  python3 tools/xem_truoc.py content/trang/trang-chu.yml

Khác bản build thật (chỉ trong mô phỏng, không đụng tools/build.py):
  - mỗi khối, đầu trang, khối liên hệ, menu, chân trang được đánh dấu data-cms="<đường dẫn trường>"
    để khung mô phỏng tô sáng đúng chỗ đang sửa;
  - khối đang ẩn vẫn hiện (mờ, có nhãn) để thấy vị trí; khối chưa dựng được hiện thẻ báo lỗi thay vì làm hỏng cả trang;
  - không xử lý ảnh (kích thước ảnh lấy từ bản build gần nhất).
"""
import json
import os
import re
import sys
import time
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

if "PIL" not in sys.modules:  # Pyodide không có Pillow; mô phỏng không xử lý ảnh
    try:
        import PIL  # noqa: F401
    except ImportError:
        pil = types.ModuleType("PIL")
        for name in ("Image", "ImageDraw", "ImageEnhance", "ImageFilter", "ImageFont", "ImageOps"):
            setattr(pil, name, types.ModuleType("PIL." + name))
            sys.modules["PIL." + name] = getattr(pil, name)
        sys.modules["PIL"] = pil

import blocks  # noqa: E402
import build  # noqa: E402
import content  # noqa: E402
import markup as M  # noqa: E402
import schema  # noqa: E402
import tpl  # noqa: E402
from loi import LOI  # noqa: E402

ROOT = content.ROOT
SNAP = {"sizes": {}, "uploads": {}, "anh": {}, "hash": {}}
ORIGINAL = {}  # tệp đã bị thay bằng bản đang sửa → nội dung gốc (None: tệp mới)
_PATCHED = False


# ---------------------------------------------------------------------------
# Đánh dấu vị trí
# ---------------------------------------------------------------------------
TAG_RE = re.compile(r"^(\s*<[a-zA-Z][\w-]*)")


def mark(html, key, extra=""):
    return TAG_RE.sub(lambda m: f'{m.group(1)} data-cms="{key}"{extra}', html, count=1) if html else html


def render_blocks(ctx, page, items):
    """Như blocks.render nhưng giữ cả khối đang ẩn (mờ) và không để 1 khối dở dang làm hỏng cả trang."""
    out = []
    for i, b in enumerate(items, 1):
        t = blocks.BLOCK_BY_NAME.get(b.get("loai"))
        label = t["label"].split("·")[-1].strip() if t else (b.get("loai") or "Khối")
        key = f"cac_khoi.{i - 1}"
        try:
            c = ctx.at(where=f"Các khối trên trang › Khối {i} ({label})")
            html = blocks.RENDER[b["loai"]](c, b, i, page)
        except Exception as e:  # khối mới thêm, chưa điền đủ
            html = (f'<section class="cms-loi"><p><strong>Khối {i} · {M.esc(label)}</strong> chưa dựng được: '
                    f'{M.esc(type(e).__name__)} – điền đủ các ô bắt buộc.</p></section>')
        if not html:
            html = f'<section class="cms-trong"><p>Khối {i} · {M.esc(label)}: chưa có nội dung để hiện.</p></section>'
        hidden = not b.get("hien_thi", True)
        out.append(mark(html, key, f' data-cms-ten="Khối {i} · {M.esc(label)}"' + (' data-cms-an="1"' if hidden else "")))
    return "\n\n".join(out)


def _wrap(module, name, key, label):
    orig = getattr(module, name)

    def wrapped(*a, **k):
        return mark(orig(*a, **k), key, f' data-cms-ten="{label}"')
    setattr(module, name, wrapped)


def patch():
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True
    blocks.render = render_blocks
    _wrap(build, "page_hero_html", "dau_trang", "Đầu trang")
    _wrap(build, "header_html", "@dau-trang-site", "Menu và đầu trang")
    _wrap(build, "footer_html", "@chan-trang", "Chân trang")
    _wrap(tpl, "contact_band", "lien_he_cuoi_trang", "Khối liên hệ cuối trang")
    build.file_hash = lambda rel: SNAP["hash"].get(rel, "xem-truoc")


class NoImages:
    """Thay cho images.Images: mô phỏng không tạo ảnh (ảnh chia sẻ, thu nhỏ…)."""

    def og(self, rel, *a, **k):
        return f"assets/img/{rel}"

    def og_from_file(self, rel, src):
        return f"assets/img/{rel}"


# ---------------------------------------------------------------------------
# Thay tệp bằng bản đang sửa
# ---------------------------------------------------------------------------
def _collection(name):
    for c in schema.collections():
        if c.get("name") == name:
            return c
    raise KeyError(f"Không có chuyên mục “{name}”")


def target_path(collection, slug, file_name, data):
    c = _collection(collection)
    if "files" in c:
        f = next(x for x in c["files"] if x["name"] == file_name)
        return f["file"]
    if not slug:  # bài/trang mới chưa lưu: đường dẫn tạm từ ô đường dẫn hoặc tiêu đề
        slug = data.get("duong_dan") or M.slugify(data.get("tieu_de") or data.get("ten") or "", 60) or "ban-moi"
    return f'{c["folder"]}/{slug}.{c["extension"]}'


def serialize(path, data):
    """JSON là YAML hợp lệ: ghi bản đang sửa thành tệp để content.load đọc như tệp thật."""
    data = dict(data or {})
    if path.endswith(".md"):
        body = data.pop("body", "") or ""
        return "---\n" + json.dumps(data, ensure_ascii=False) + "\n---\n" + body + "\n"
    return json.dumps(data, ensure_ascii=False)


def restore():
    for rel, text in ORIGINAL.items():
        full = os.path.join(ROOT, rel)
        if text is None:
            if os.path.exists(full):
                os.remove(full)
        else:
            with open(full, "w", encoding="utf-8") as fh:
                fh.write(text)
    ORIGINAL.clear()


def apply(rel, data):
    full = os.path.join(ROOT, rel)
    if rel not in ORIGINAL:
        ORIGINAL[rel] = open(full, encoding="utf-8").read() if os.path.exists(full) else None
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(serialize(rel, data))


# ---------------------------------------------------------------------------
# Dựng
# ---------------------------------------------------------------------------
def page_for(rel):
    """Trang thể hiện tệp đang sửa (tệp cài đặt, kho hỏi đáp → trang chủ / trang câu hỏi)."""
    S = build.S
    hubs = {schema.HUB_FILES["dich_vu"]: build.services_hub, schema.HUB_FILES["kien_thuc"]: build.knowledge_hub,
            schema.HUB_FILES["hoi_dap"]: build.faq_page, "content/hoi-dap.yml": build.faq_page,
            "content/trang-van-ban/404.yml": build.not_found_page}
    if rel in hubs:
        return hubs[rel]()
    m = re.match(r"^content/(trang|dich-vu|bai-viet)/([^/_][^/]*)\.(yml|md)$", rel)
    if m:
        kind, slug = m.group(1), m.group(2)
        if kind == "trang":
            return build.block_page(S.pages[slug])
        if kind == "dich-vu":
            return build.service_page(next(s for s in S.services if s["slug"] == slug))
        return build.article_page(next(a for a in S.articles if a["slug"] == slug))
    m = re.match(r"^content/trang-van-ban/([^/]+)\.md$", rel)
    if m:
        return build.legal_page(m.group(1))
    return build.block_page(S.pages[content.HOME_SLUG])  # cài đặt chung: xem trên trang chủ


def check_page_links(rel):
    """Liên kết nội bộ của trang đang sửa trỏ tới trang có thật (như bước kiểm của build, rút gọn)."""
    S = build.S
    redirects = {build.p2path(x["tu"]) for x in S.redirects if x.get("tu")}
    for src, where, path, anchor in S.link_refs:
        if src != rel or not path or "." in path.rsplit("/", 1)[-1]:
            continue
        if path not in S.registry and path not in redirects:
            LOI.them(src, where, f"Liên kết tới “/{path}” không tồn tại trên site.")


def _fields_for(rel):
    return schema.fields_for_path(rel)


def fill_placeholders(fields, data):
    """Bài/trang đang soạn dở: ô bắt buộc còn trống được điền chữ giữ chỗ [Tên ô] để vẫn dựng được trang mô phỏng
    (lỗi thiếu ô vẫn báo đủ, lấy từ bản gốc). Trả về True nếu có điền."""
    changed = False
    for f in fields:
        name, w = f["name"], f.get("widget", "string")
        v = data.get(name)
        if w == "object" and isinstance(v, dict):
            changed |= fill_placeholders(f.get("fields") or [], v)
            continue
        if f.get("required", True) is False or v not in (None, "", []):
            continue
        label = f.get("label", name).split("(")[0].strip()
        if name == "duong_dan" or (f.get("pattern") and "a-z0-9" in f["pattern"][0]):
            val = M.slugify(data.get("tieu_de") or "", 40) or "ban-moi-dang-soan"
            val = val if "-" in val else val + "-moi"
        elif w in ("string", "text", "markdown", "richtext"):
            val = f"[{label}]"
        elif w == "select" and f.get("_options") == "services":
            folder = os.path.join(ROOT, "content", "dich-vu")
            first = sorted(x[:-4] for x in os.listdir(folder) if x.endswith(".yml") and not x.startswith("_"))
            val = ([first[0]] if f.get("multiple") else first[0]) if first else None
        elif w == "select" and f.get("options"):
            o = f["options"][0]
            val = o["value"] if isinstance(o, dict) else o
            val = [val] if f.get("multiple") else val
        elif w == "datetime":
            val = time.strftime("%Y-%m-%d")
        elif w == "object":
            val = {}
            fill_placeholders(f.get("fields") or [], val)
        elif w == "list" and f.get("field") and f["field"].get("widget") in ("string", "text"):
            val = [f"[{label}]"]
        else:
            continue
        if val is not None:
            data[name] = val
            changed = True
    return changed


def _load(env):
    S = build.S = content.load(env)
    S._img.update({k: tuple(v) for k, v in SNAP["anh"].items()})
    S.registry = build.build_registry()
    S.draft_paths = build.draft_paths()
    tpl.init(S, {k: tuple(v) for k, v in SNAP["sizes"].items()}, {k: tuple(v) for k, v in SNAP["uploads"].items()})
    build.IMG = NoImages()
    return S


def render(collection, slug, file_name, data_json, is_new=False, path=None):
    """Trả JSON: {html, path, tep, loi: [[trường, thông báo]], canh: [...], ms}. path: tệp đang sửa (Sveltia biết sẵn)."""
    t0 = time.time()
    patch()
    restore()
    data = json.loads(data_json) if isinstance(data_json, str) else (data_json or {})
    rel = path if path and path.startswith("content/") and ".." not in path else target_path(collection, slug, file_name, data)
    env = build.read_env()
    env.update(drafts=True, noindex=False, nhap_rieng=False)  # bản nháp hiện như đã đăng
    build.ENV = env
    build.ORG_ID, build.SITE_ID = env["site_url"] + "/#organization", env["site_url"] + "/#website"
    filled = json.loads(json.dumps(data))
    first_errors = None
    if fill_placeholders(_fields_for(rel), filled):  # soạn dở: lấy lỗi từ bản gốc, dựng trang từ bản có chữ giữ chỗ
        apply(rel, data)
        LOI.loi, LOI.canh_bao = [], []
        try:
            content.load(env)
        except Exception:
            pass
        first_errors = [x for x in LOI.loi if x[0] == rel]
        data = filled
    apply(rel, data)
    LOI.loi, LOI.canh_bao = [], []
    html, page_path = "", ""
    try:
        _load(env)
        page = page_for(rel)
        page_path = page["path"]
        html = build.layout(page)
        check_page_links(rel)
    except Exception as e:  # dữ liệu dở dang làm hỏng cả trang: báo rõ thay vì trang trắng
        LOI.them(rel, "", f"Chưa dựng được trang ({type(e).__name__}: {e}).")
    own = lambda rows: [[w, msg] for f, w, msg in rows if f == rel]  # noqa: E731 – lỗi của chính tệp đang sửa
    if first_errors is not None:  # ô còn trống: báo lỗi của bản gốc, thêm lỗi khác (liên kết…) ở ô không bị điền giữ chỗ
        seen = {w for _, w, _ in first_errors}
        LOI.loi = first_errors + [x for x in LOI.loi if x[0] == rel and x[1] not in seen and "[" not in x[2]]
    return json.dumps({"html": html, "path": page_path, "tep": rel, "loi": own(LOI.loi),
                       "canh": own(LOI.canh_bao), "ms": round((time.time() - t0) * 1000)}, ensure_ascii=False)


def setup(snapshot_json):
    SNAP.update(json.loads(snapshot_json) if isinstance(snapshot_json, str) else snapshot_json)


def snapshot(out, sizes, uploads, img_sizes):
    """Build gọi: ghi dữ liệu cần cho mô phỏng (không có trong content/)."""
    return {"sizes": {k: list(v) for k, v in sizes.items()}, "uploads": {k: list(v) for k, v in uploads.items()},
            "anh": {k: list(v) for k, v in img_sizes.items() if v},
            "hash": {r: build.file_hash(r) for r in ("assets/css/style.css", "assets/js/main.js")}}


if __name__ == "__main__":
    rel = sys.argv[1] if len(sys.argv) > 1 else "content/trang/trang-chu.yml"
    data = content.read_file(os.path.join(ROOT, rel))
    m = re.match(r"^content/(trang|dich-vu|bai-viet)/([^/]+)\.", rel)
    col = {"trang": "trang", "dich-vu": "dich_vu", "bai-viet": "bai_viet"}[m.group(1)] if m else None
    r = json.loads(render(col, m.group(2) if m else None, None, json.dumps(data, ensure_ascii=False, default=str)))
    restore()
    print(f"{rel} → /{r['path']}: {len(r['html'])} ký tự, {r['ms']} ms, lỗi {r['loi']}, cảnh báo {r['canh']}")
    print(sorted(set(re.findall(r'data-cms="([^"]+)"', r["html"]))))
