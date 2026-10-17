# -*- coding: utf-8 -*-
"""Xử lý chữ trong nội dung: mã chèn, chữ tô đỏ, Markdown → HTML, liên kết nội bộ, mã neo.

Quy ước cho người biên tập (không ô nào chứa mã HTML):
    *chữ*                 Trong ô tiêu đề: phần giữa hai dấu sao được tô đỏ nhấn mạnh.
    **đậm**, *nghiêng*    Trong ô có nút định dạng (bài viết, câu trả lời…), giống Word.
    {{hotline}} …         Mã chèn thông tin công ty, tự cập nhật khi sửa ở Cài đặt chung → Thông tin công ty.
    /dich-vu/thua-ke/     Liên kết trong site: viết đường dẫn bắt đầu bằng "/" hoặc dán nguyên địa chỉ trang;
                          build tự đổi cho đúng thư mục và báo lỗi nếu trang hoặc mã neo không tồn tại.
"""
import html
import re
import unicodedata

from markdown_it import MarkdownIt

from loi import LOI


def esc(s):
    return html.escape(str(s), quote=True)


def slugify(text, maxlen=60):
    """Bỏ dấu tiếng Việt, chỉ giữ a–z, 0–9, gạch nối: "Đất đai & Nhà ở" → "dat-dai-nha-o"."""
    s = str(text).replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    if len(s) > maxlen:
        s = s[:maxlen].rsplit("-", 1)[0] if "-" in s[:maxlen] else s[:maxlen]
    return s


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HTML_TAG_RE = re.compile(r"</?[A-Za-z][A-Za-z0-9-]*(\s[^<>]*)?/?>|<!--")

# ---------------------------------------------------------------------------
# Mã chèn
# ---------------------------------------------------------------------------
TOKEN_RE = re.compile(r"\{\{\s*([A-Za-z_]+)\s*\}\}|%7B%7B\s*([A-Za-z_]+)\s*%7D%7D", re.I)

# Tên mã, ý nghĩa (hiện trong gợi ý của CMS)
TOKEN_HELP = [
    ("luat_su", "tên luật sư phụ trách"),
    ("hotline", "số hotline"),
    ("email", "email"),
    ("dia_chi", "địa chỉ văn phòng đầy đủ"),
    ("gio_lam_viec", "giờ làm việc"),
    ("ngoai_gio", "ghi chú ngoài giờ"),
    ("ten_cong_ty", "tên pháp nhân"),
    ("ten_ngan", "tên ngắn"),
    ("ma_so_thue", "mã số thuế"),
    ("tel", "liên kết gọi điện (dùng làm địa chỉ liên kết)"),
    ("zalo", "liên kết Zalo (dùng làm địa chỉ liên kết)"),
    ("mailto", "liên kết gửi email (dùng làm địa chỉ liên kết)"),
]
TOKEN_HINT = "Mã chèn tự cập nhật: " + ", ".join("{{" + n + "}}" for n, _ in TOKEN_HELP[:6]) + "."


def company_tokens(firm):
    return {
        "luat_su": firm["lawyer"], "hotline": firm["phone"], "email": firm["email"],
        "dia_chi": firm["address"], "gio_lam_viec": firm["hours"], "ngoai_gio": firm["hours_note"],
        "ten_cong_ty": firm["legal_name"], "ten_ngan": firm["short_name"], "ma_so_thue": firm.get("tax_id", ""),
        "tel": "tel:" + firm["phone_tel"], "zalo": firm["zalo"], "mailto": "mailto:" + firm["email"],
    }


class Ctx:
    """Ngữ cảnh khi dựng một trang: thư mục gốc tương đối, trang đang dựng, tệp + trường để báo lỗi."""

    def __init__(self, site, root, page, src="", where="", extra=None):
        self.site, self.r, self.page, self.src, self.where = site, root, page, src, where
        self.extra = extra or {}

    def at(self, src=None, where=None, extra=None):
        return Ctx(self.site, self.r, self.page, self.src if src is None else src,
                   self.where if where is None else where, {**self.extra, **(extra or {})})

    def error(self, msg):
        LOI.them(self.src, self.where, msg)


def expand(text, ctx):
    if not text:
        return ""
    tokens = {**ctx.site.tokens, **ctx.extra}

    def rep(m):
        name = (m.group(1) or m.group(2)).lower()
        if name in tokens:
            return tokens[name]
        ctx.error(f"Mã chèn “{{{{{name}}}}}” không tồn tại. Mã dùng được: "
                  + ", ".join("{{" + n + "}}" for n in tokens) + ".")
        return m.group(0)
    return TOKEN_RE.sub(rep, str(text))


def plain(text, ctx):
    """Chữ thường: chèn mã, thoát ký tự HTML."""
    return esc(expand(text, ctx))


def title(text, ctx, tag="em"):
    """Tiêu đề: phần *giữa hai dấu sao* được tô đỏ (thẻ <em> ở đầu trang con, <span> ở khối Đầu trang)."""
    s = esc(expand(text, ctx))
    if s.count("*") % 2:
        ctx.error("Dấu * dùng để tô đỏ phải đi theo cặp, ví dụ: Chia di sản đúng luật, *giữ được tình thân*.")
        s = s.replace("*", "")
    return re.sub(r"\*(.+?)\*", rf"<{tag}>\1</{tag}>", s)


def title_text(text, ctx=None):
    """Tiêu đề dạng chữ trơn (cho thẻ title, ảnh chia sẻ, mục lục)."""
    s = expand(text, ctx) if ctx else str(text or "")
    return s.replace("*", "")


# ---------------------------------------------------------------------------
# Liên kết
# ---------------------------------------------------------------------------
EXTERNAL_RE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//)", re.I)


def href(url, ctx):
    """Đổi liên kết trong nội dung thành đường dẫn tương đối đúng thư mục; ghi lại để kiểm trang/mã neo tồn tại."""
    url = (url or "").strip()
    if not url:
        ctx.error("Liên kết để trống địa chỉ.")
        return "#"
    if url.startswith("#"):
        ctx.site.link_refs.append((ctx.src, ctx.where, ctx.page, url[1:]))
        return url
    for base in ctx.site.internal_prefixes:
        if url == base or url.startswith(base + "/") or url.startswith(base + "#"):
            url = url[len(base):] or "/"
            break
    if EXTERNAL_RE.match(url):
        return url
    path, _, anchor = url.partition("#")
    path = path.split("?")[0].lstrip("/")
    if path.startswith("./"):
        path = path[2:]
    last = path.rsplit("/", 1)[-1]
    if path and not path.endswith("/") and "." not in last:
        path += "/"
    if path == "index.html":
        path = ""
    ctx.site.link_refs.append((ctx.src, ctx.where, path, anchor))
    if getattr(ctx.site, "nhap_prefix", "") and path in ctx.site.draft_paths:
        path = ctx.site.nhap_prefix + path  # bản nháp riêng dưới /nhap/: liên kết giữa các bản nháp trỏ tới bản nháp
    out = ctx.r + path + (f"#{anchor}" if anchor else "")
    return out or "./"


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------
MD = MarkdownIt("commonmark", {"html": False, "xhtmlOut": False, "breaks": False, "typographer": False})
MD.enable(["table", "strikethrough"])

NOTE_ICON = '<svg class="note__icon" aria-hidden="true"><use href="#i-alert"/></svg>'


def _render_table_open(self, tokens, idx, options, env):
    return '<div class="table-wrap">\n<table>\n'


def _render_table_close(self, tokens, idx, options, env):
    return "</table>\n</div>\n"


def _render_th_open(self, tokens, idx, options, env):
    tokens[idx].attrSet("scope", "col")
    return self.renderToken(tokens, idx, options, env)


def _render_bq_open(self, tokens, idx, options, env):
    return f'<div class="note note--light">{NOTE_ICON}'


def _render_bq_close(self, tokens, idx, options, env):
    return "</div>\n"


MD.add_render_rule("table_open", _render_table_open)
MD.add_render_rule("table_close", _render_table_close)
MD.add_render_rule("th_open", _render_th_open)
MD.add_render_rule("blockquote_open", _render_bq_open)
MD.add_render_rule("blockquote_close", _render_bq_close)


def _inline_text(tok):
    return "".join(c.content for c in (tok.children or []) if c.type in ("text", "code_inline"))


def _process_inline(children, ctx):
    for c in children or []:
        if c.type == "link_open":
            url = href(c.attrGet("href"), ctx)
            c.attrSet("href", url)
            if url.startswith(("http://", "https://")):  # liên kết ra ngoài site: mở tab mới
                c.attrSet("target", "_blank")
                c.attrSet("rel", "noopener")
        elif c.type == "image":
            src = c.attrGet("src") or ""
            url = href(src, ctx)
            c.attrSet("src", url)
            alt = "".join(x.content for x in (c.children or []))
            if not alt.strip():
                ctx.error(f"Ảnh “{src}” trong nội dung thiếu mô tả. Bấm vào khung ảnh → điền ô “Mô tả ảnh (bắt buộc)”.")
            info = ctx.site.image_size(src)
            if info:
                c.attrSet("width", str(info[0]))
                c.attrSet("height", str(info[1]))
                if src.startswith("/assets/uploads/"):  # ảnh tải lên: build đã sinh bản 480/960/1600 cho điện thoại
                    from images import UPLOAD_WIDTHS
                    widths = [w for w in UPLOAD_WIDTHS if w < info[0]]
                    if widths:
                        stem = url.rsplit(".", 1)[0]
                        c.attrSet("srcset", ", ".join([f"{stem}-{w}.webp {w}w" for w in widths] + [f"{url} {info[0]}w"]))
                        c.attrSet("sizes", "(max-width: 800px) calc(100vw - 40px), 760px")
            c.attrSet("loading", "lazy")
            c.attrSet("decoding", "async")


def block(text, ctx, toc=None, ids=None):
    """Đoạn văn nhiều dòng, bài viết, trang văn bản. toc: danh sách nhận (mã neo, tiêu đề) của các mục H2."""
    if not text:
        return ""
    raw = expand(text, ctx)
    tokens = MD.parse(raw)
    used = ids if ids is not None else set()
    for i, tok in enumerate(tokens):
        if tok.type in ("heading_open", "heading_close"):
            if tok.tag == "h1":
                tok.tag = "h2"
            if tok.type == "heading_open" and tok.tag in ("h2", "h3"):
                text_ = _inline_text(tokens[i + 1])
                base = slugify(re.sub(r"^\d+[.)]\s*", "", text_), 50) or "muc"
                hid, n = base, 2
                while hid in used:
                    hid, n = f"{base}-{n}", n + 1
                used.add(hid)
                tok.attrSet("id", hid)
                if toc is not None and tok.tag == "h2":
                    toc.append((hid, re.sub(r"^\d+[.)]\s*", "", text_).strip()))
        elif tok.type == "inline":
            _process_inline(tok.children, ctx)
    return FIGURE_RE.sub(_figure, MD.renderer.render(tokens, MD.options, {}))


# Ảnh đứng riêng một đoạn → <figure>; "Chú thích dưới ảnh" (title của ảnh Markdown) → <figcaption>
FIGURE_RE = re.compile(r"<p>(<img [^>]*>)</p>")


def _figure(m):
    img = m.group(1)
    cap = re.search(r' title="([^"]*)"', img)
    if not cap:
        return f'<figure class="prose-figure">{img}</figure>'
    return f'<figure class="prose-figure">{img.replace(cap.group(0), "")}<figcaption>{cap.group(1)}</figcaption></figure>'


def inline(text, ctx):
    """Một đoạn ngắn có đậm/nghiêng/liên kết, đặt trong thẻ có sẵn (vd. <p class="icard__text">)."""
    if not text:
        return ""
    raw = expand(text, ctx).strip()
    tokens = MD.parseInline(raw)
    children = tokens[0].children if tokens else []
    _process_inline(children, ctx)
    return MD.renderer.renderInline(children, MD.options, {}).replace("\n", " ")


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def to_text(text, ctx):
    """Markdown → chữ trơn (dữ liệu có cấu trúc cho Google, chỉ mục tìm kiếm)."""
    return html.unescape(strip_tags(block(text, ctx.at())))
