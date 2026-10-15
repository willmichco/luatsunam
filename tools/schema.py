# -*- coding: utf-8 -*-
"""Schema dùng chung – NGUỒN DUY NHẤT mô tả nội dung của website.

Mỗi lần build, từ đây sinh cùng lúc:
  1. Cấu hình CMS (admin/config.yml): nhãn, gợi ý, giới hạn, danh sách chọn.
  2. Bộ kiểm dữ liệu lúc build: báo lỗi tiếng Việt kèm tên tệp + tên trường.
Nên CMS không bao giờ lệch cấu trúc site: thêm 1 trường ở đây → CMS tự hiện trường đó ở lần build sau.

Khóa bắt đầu bằng "_" chỉ dùng lúc build (không đưa vào CMS):
    _red      Ô tiêu đề có *chữ tô đỏ*
    _options  Danh sách chọn sinh từ nội dung hiện có: "pages" (mọi trang), "faq" (kho hỏi đáp)
    _rules    Quy tắc so sánh nhiều trường trong cùng một nhóm
"""
import datetime
import os
import re

from loi import LOI
from markup import HTML_TAG_RE, SLUG_RE, TOKEN_HINT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_IMAGE_BYTES = 5 * 1024 * 1024

# ---------------------------------------------------------------------------
# Kiểu trường
# ---------------------------------------------------------------------------


def _f(widget, name, label, hint=None, required=True, default=None, **kw):
    f = {"name": name, "label": label, "widget": widget}
    if hint:
        f["hint"] = hint
    if not required:
        f["required"] = False
    if default is not None:
        f["default"] = default
    f.update(kw)
    return f


def string(name, label, hint=None, minlength=None, maxlength=None, **kw):
    if minlength:
        kw["minlength"] = minlength
    if maxlength:
        kw["maxlength"] = maxlength
    return _f("string", name, label, hint, **kw)


def red_title(name, label, hint=None, example=None, maxlength=120, **kw):
    h = (hint + " " if hint else "") + "Phần cần **tô đỏ** đặt giữa hai dấu sao" + (f", ví dụ: `{example}`" if example else "") + "."
    return string(name, label, h, maxlength=maxlength, _red=True, **kw)


def text(name, label, hint=None, minlength=None, maxlength=None, **kw):
    if minlength:
        kw["minlength"] = minlength
    if maxlength:
        kw["maxlength"] = maxlength
    return _f("text", name, label, hint, **kw)


def rich(name, label, hint=None, **kw):
    """Ô chữ có nút Đậm / Nghiêng / Liên kết (lưu dạng Markdown, không nhận mã HTML)."""
    h = (hint + " " if hint else "") + "Liên kết trong site: dán đường dẫn bắt đầu bằng / (vd. /dich-vu/thua-ke/). " + TOKEN_HINT
    if "maxlength" in kw:  # ô định dạng của CMS không có bộ đếm: giới hạn chỉ kiểm lúc build
        kw["_maxlength"] = kw.pop("maxlength")
    return _f("richtext", name, label, h, buttons=["bold", "italic", "link"], editor_components=[],
              minimal=True, **kw)


def editor(name, label, hint=None, **kw):
    """Khung soạn thảo đầy đủ (bài viết, trang văn bản): đề mục, danh sách, trích dẫn, ảnh, bảng."""
    return _f("richtext", name, label, hint,
              buttons=["bold", "italic", "link", "heading-two", "heading-three", "bulleted-list", "numbered-list", "quote"],
              editor_components=["image", "bang"], linked_images=False, **kw)


def boolean(name, label, hint=None, default=False, **kw):
    return _f("boolean", name, label, hint, required=False, default=default, **kw)


def number(name, label, hint=None, min=None, max=None, **kw):
    if min is not None:
        kw["min"] = min
    if max is not None:
        kw["max"] = max
    return _f("number", name, label, hint, value_type="int", **kw)


def date(name, label, hint=None, **kw):
    return _f("datetime", name, label, hint, type="date", format="YYYY-MM-DD", **kw)


def select(name, label, options, hint=None, **kw):
    opts = [{"label": l, "value": v} for v, l in options] if options and isinstance(options[0], tuple) else options
    return _f("select", name, label, hint, options=opts, **kw)


def image(name, label, hint=None, **kw):
    return _f("image", name, label, hint, choose_url=False, **kw)


def relation_service(name, label, hint=None, multiple=False, **kw):
    if multiple:
        kw["multiple"] = True
    return _f("relation", name, label, hint, collection="dich_vu", value_field="{{slug}}",
              display_fields=["{{ten}}"], search_fields=["ten"], **kw)


def page_link(name, label, hint=None, **kw):
    h = (hint + " " if hint else "") + "Trang vừa tạo sẽ có trong danh sách sau khoảng 2–3 phút (tải lại trang quản trị)."
    return _f("select", name, label, h, options=[], _options="pages", **kw)


def lst(name, label, fields=None, field=None, types=None, hint=None, summary=None, min=None, max=None,
        label_singular=None, **kw):
    if fields is not None:
        kw["fields"] = fields
    if field is not None:
        kw["field"] = field
    if types is not None:
        kw["types"] = types
        kw.setdefault("typeKey", "loai")
    if summary:
        kw["summary"] = summary
    if min is not None:
        kw["min"] = min
    if max is not None:
        kw["max"] = max
    if label_singular:
        kw["label_singular"] = label_singular
    kw.setdefault("collapsed", "auto")
    return _f("list", name, label, hint, required=bool(min), **kw)


def strings(name, label, hint=None, min=None, max=None, maxlength=None, item_label="Dòng", multiline=False, **kw):
    sub = (text if multiline else string)("muc", item_label, maxlength=maxlength)
    return lst(name, label, field=sub, hint=hint, min=min, max=max, label_singular=item_label.lower(), **kw)


def obj(name, label, fields, hint=None, collapsed=False, summary=None, **kw):
    if collapsed:
        kw["collapsed"] = collapsed
    if summary:
        kw["summary"] = summary
    return _f("object", name, label, hint, fields=fields, **kw)


def link(name="lien_ket", label="Liên kết", hint=None, required=True, with_label=True):
    """Liên kết: chọn trang có sẵn (+ mã neo) hoặc nhập địa chỉ khác."""
    fields = []
    if with_label:
        fields.append(string("nhan", "Chữ hiển thị", "Ví dụ: Xem tất cả câu hỏi", maxlength=60))
    fields += [
        page_link("trang", "Trang trong site", required=False),
        string("ma_neo", "Mã neo (tùy chọn)", "Nhảy tới một mục trong trang, vd. ho-so-can-chuan-bi", required=False,
               pattern=["^[a-z0-9-]*$", "Chỉ a–z, 0–9 và gạch nối"]),
        string("ngoai", "Hoặc địa chỉ khác", "Chỉ điền khi không chọn trang ở trên: https://…, tel:…, mailto:…", required=False),
    ]
    return obj(name, label, fields, hint=hint, required=required, collapsed="auto",
               summary="{{fields.nhan}}" if with_label else "{{fields.trang}}", _rules=[_rule_link])


def _rule_link(v, add):
    if v and not v.get("trang") and not v.get("ngoai"):
        add("Chọn một trang trong site hoặc điền “Hoặc địa chỉ khác”.")
    if v and v.get("trang") and v.get("ngoai"):
        add("Chỉ chọn trang trong site HOẶC điền địa chỉ khác, không dùng cả hai.")


# ---------------------------------------------------------------------------
# Danh sách cố định
# ---------------------------------------------------------------------------
ICONS = [
    ("i-scale", "Cán cân công lý"), ("i-gavel", "Búa phán quyết"), ("i-inherit", "Ngôi nhà (thừa kế)"),
    ("i-house", "Tòa nhà (đất đai)"), ("i-heart", "Trái tim (gia đình)"), ("i-shield", "Khiên"),
    ("i-shield-check", "Khiên có dấu tích"), ("i-doc", "Tài liệu"), ("i-user", "Một người"),
    ("i-team", "Nhóm người"), ("i-network", "Mạng lưới"), ("i-diamond", "Kim cương"),
    ("i-steps", "Các bước"), ("i-book", "Sách"), ("i-question", "Dấu hỏi"), ("i-lock", "Ổ khóa"),
    ("i-coin", "Tiền / chi phí"), ("i-clock", "Đồng hồ"), ("i-calendar", "Lịch"), ("i-chat", "Tin nhắn"),
    ("i-phone", "Điện thoại"), ("i-mail", "Thư"), ("i-pin", "Ghim địa điểm"), ("i-check-circle", "Dấu tích tròn"),
    ("i-list", "Danh sách"), ("i-alert", "Cảnh báo"),
]
ICON_IDS = {k for k, _ in ICONS}


def icon(name="bieu_tuong", label="Biểu tượng", required=True, **kw):
    return select(name, label, ICONS, required=required, dropdown_threshold=0, **kw)


PHOTOS = [("van-phong", "Luật sư tại văn phòng"), ("phien-toa", "Luật sư tại phiên tòa")]
DAYS = [("Monday", "Thứ 2"), ("Tuesday", "Thứ 3"), ("Wednesday", "Thứ 4"), ("Thursday", "Thứ 5"),
        ("Friday", "Thứ 6"), ("Saturday", "Thứ 7"), ("Sunday", "Chủ nhật")]
BG = [("trang", "Trắng"), ("kem", "Kem")]
BG_DARK = BG + [("toi", "Tối (đỏ sẫm)")]
SLUG_PATTERN = ["^[a-z0-9]+(-[a-z0-9]+)*$", "Chỉ chữ a–z không dấu, số 0–9 và gạch nối, ví dụ: ly-hon-don-phuong"]
ANCHOR_PATTERN = ["^([a-z0-9]+(-[a-z0-9]+)*)?$", "Chỉ chữ a–z không dấu, số 0–9 và gạch nối"]
TIME_PATTERN = ["^([01][0-9]|2[0-3]):[0-5][0-9]$", "Giờ dạng 24 giờ, ví dụ 08:00 hoặc 17:30"]


def photo_fields(default_photo="van-phong",
                 hint_alt="Bắt buộc khi tải ảnh riêng. Tả ngắn nội dung ảnh, vd. Luật sư trao đổi hồ sơ với khách hàng"):
    return [
        image("anh", "Tải ảnh riêng (tùy chọn)", "Để trống = dùng ảnh có sẵn ở ô dưới. Ảnh ≤ 5 MB, tự đổi sang WebP.", required=False),
        select("anh_co_san", "Ảnh có sẵn", PHOTOS, default=default_photo, required=False,
               hint=None if default_photo else "Để trống = không có ảnh (hiện biểu tượng)."),
        string("mo_ta_anh", "Mô tả ảnh (alt)", hint_alt, required=False, maxlength=160),
        string("chu_thich", "Chú thích ảnh – dòng đậm", "Ví dụ: {{luat_su}}", required=False, maxlength=80),
        string("chu_thich_phu", "Chú thích ảnh – dòng nhỏ", "Ví dụ: Giám đốc · tại văn phòng 22c Vũ Ngọc Phan", required=False, maxlength=120),
    ]


def _rule_card_link(v, add):
    if v.get("lien_ket") and re.search(r"\]\(", v.get("mo_ta") or ""):
        add("Thẻ đã dẫn tới một trang thì nội dung thẻ không được chứa liên kết riêng (trình duyệt không cho liên kết lồng nhau).")


def _rule_photo(v, add):
    if v.get("anh") and not (v.get("mo_ta_anh") or "").strip():
        add("Ảnh tải riêng phải có “Mô tả ảnh (alt)”.")


def seo(title_example, desc_example):
    return obj("seo", "SEO – hiển thị trên Google và khi chia sẻ", [
        string("tieu_de", "Tiêu đề trên Google",
               f"Dòng chữ xanh trên Google. 15–60 ký tự; đuôi “ | Luật Sư Nam” tự thêm. Ví dụ: {title_example}",
               minlength=15, maxlength=60),
        text("mo_ta", "Mô tả trên Google",
             f"Đoạn chữ xám dưới tiêu đề. 70–160 ký tự, nêu rõ việc anh chị được giúp. Ví dụ: {desc_example}",
             minlength=70, maxlength=160),
        image("anh_chia_se", "Ảnh chia sẻ Facebook/Zalo (tùy chọn)",
              "Để trống = tự tạo ảnh từ tiêu đề. Ảnh riêng nên ngang 1200×630.", required=False),
    ], summary="{{fields.tieu_de}}")


def contact_band_fields():
    return obj("lien_he_cuoi_trang", "Khối liên hệ cuối trang", [
        boolean("hien", "Hiện khối liên hệ đỏ ở cuối trang", default=True),
        string("nhan", "Nhãn nhỏ", "Để trống = dùng câu chữ dùng chung", required=False, maxlength=60),
        string("tieu_de", "Tiêu đề", "Để trống = dùng câu chữ dùng chung", required=False, maxlength=110),
        text("doan_moi", "Đoạn mời liên hệ", "Để trống = dùng câu chữ dùng chung", required=False, maxlength=320),
    ], collapsed=True)


def page_head_fields(label="Đầu trang tiêu chuẩn", with_card=True, hint=None, required=True):
    f = [
        string("nhan", "Nhãn nhỏ trên tiêu đề", "Ví dụ: Quy trình làm việc", required=False, maxlength=60),
        red_title("tieu_de", "Tiêu đề lớn của trang (H1)", example="Làm việc với luật sư: *bốn bước, không phức tạp*"),
        text("mo_dau", "Đoạn mở đầu", "1–3 câu nói rõ trang này giúp gì cho người đọc.", required=False, maxlength=420),
    ]
    if with_card:
        f.append(boolean("the_luat_su", "Hiện thẻ “Luật sư phụ trách” bên phải", default=True))
    return obj("dau_trang", label, f, hint=hint, required=required)


def common(bg=BG, default_bg="trang"):
    f = [boolean("hien_thi", "Hiển thị khối này", "Tắt để tạm ẩn mà vẫn giữ nội dung", default=True),
         string("ma_neo", "Mã neo (tùy chọn)", "Để trang khác link thẳng tới khối này, vd. ho-so-can-chuan-bi → /trang/#ho-so-can-chuan-bi",
                required=False, pattern=ANCHOR_PATTERN)]
    if bg:
        f.append(select("nen", "Màu nền", bg, default=default_bg, required=False))
    return f


def section_head(eyebrow_ex="Hành trình", title_ex="Chặng đường hơn 25 năm", with_text=True, title_required=True):
    f = [string("nhan", "Nhãn nhỏ", f"Ví dụ: {eyebrow_ex}", required=False, maxlength=60),
         string("tieu_de", "Tiêu đề khối", f"Ví dụ: {title_ex}", required=title_required, maxlength=110)]
    if with_text:
        f.append(text("mo_ta", "Mô tả ngắn dưới tiêu đề", required=False, maxlength=360))
    return f


# ---------------------------------------------------------------------------
# 16 khối dựng trang (mục 5 kế hoạch). Khối 16 "Liên hệ cuối trang" là nhóm cố định cuối mỗi trang.
# ---------------------------------------------------------------------------
BLOCK_TYPES = [
    {"name": "dau_trang", "label": "1 · Đầu trang lớn (Hero)", "summary": "Đầu trang: {{fields.tieu_de}}",
     "fields": common(bg=None) + [
         string("nhan", "Nhãn nhỏ", "Ví dụ: Luật sư tư vấn & tranh tụng tại TP.HCM", required=False, maxlength=70),
         red_title("tieu_de", "Tiêu đề lớn (H1)", example="Gặp chuyện pháp lý, *có luật sư bên cạnh*"),
         text("doan_mo_dau", "Đoạn mở đầu", "Mỗi đoạn cách nhau một dòng trống.", maxlength=900),
         boolean("nut_lien_he", "Hiện nút Gọi / Nhắn Zalo (số lấy từ Thông tin công ty)", default=True),
         boolean("dai_thong_tin", "Hiện dải địa chỉ + giờ làm việc", default=False),
         select("vi_tri_anh", "Vị trí ảnh", [("phai", "Bên phải"), ("trai", "Bên trái")], default="phai", required=False),
         *photo_fields(),
         lst("so_lieu", "Dải số liệu dưới đầu trang (tùy chọn)", fields=[
             string("so", "Con số / mốc", "Ví dụ: 01/2019", maxlength=20),
             string("mo_ta", "Ý nghĩa", "Ví dụ: Thành lập công ty luật", maxlength=70)],
             summary="{{fields.so}} – {{fields.mo_ta}}", max=4, label_singular="số liệu"),
     ], "_rules": [_rule_photo]},
    {"name": "dai_cam_ket", "label": "2 · Dải cam kết", "summary": "Dải cam kết",
     "fields": common(bg=None) + [
         lst("muc", "Các cam kết", fields=[icon(), string("tieu_de", "Dòng đậm", maxlength=50),
                                          string("mo_ta", "Dòng giải thích", maxlength=120)],
             summary="{{fields.tieu_de}}", min=3, max=5, label_singular="cam kết"),
     ]},
    {"name": "luoi_the", "label": "3 · Lưới thẻ", "summary": "Lưới thẻ: {{fields.tieu_de}}",
     "fields": common(bg=BG_DARK) + section_head("Nguyên tắc làm việc", "Bốn điều anh chị có thể yên tâm") + [
         boolean("can_giua", "Căn giữa tiêu đề", default=False),
         select("so_cot", "Số cột", [("2", "2 cột (biểu tượng bên trái)"), ("3", "3 cột"), ("4", "4 cột")], default="3", required=False),
         lst("the", "Các thẻ", fields=[
             icon(required=False, hint="Nền tối không hiện biểu tượng"),
             string("tieu_de", "Tiêu đề thẻ", maxlength=80),
             rich("mo_ta", "Nội dung thẻ", maxlength=420),
             link("lien_ket", "Cả thẻ dẫn tới (tùy chọn)", required=False, with_label=False)],
             summary="{{fields.tieu_de}}", min=1, max=12, label_singular="thẻ", _item_rules=[_rule_card_link]),
         lst("lien_ket_cuoi", "Liên kết dưới lưới (tùy chọn)", fields=link("lien_ket")["fields"], summary="{{fields.nhan}}",
             max=3, label_singular="liên kết", _item_rules=[_rule_link]),
     ]},
    {"name": "anh_chu", "label": "4 · Ảnh + chữ", "summary": "Ảnh + chữ: {{fields.tieu_de}}",
     "fields": common() + section_head("Về chúng tôi", "Văn phòng luật do {{luat_su}} trực tiếp điều hành", with_text=False) + [
         select("vi_tri_anh", "Vị trí ảnh", [("trai", "Bên trái"), ("phai", "Bên phải")], default="trai", required=False),
         text("noi_dung", "Đoạn văn", "Mỗi đoạn cách nhau một dòng trống. " + TOKEN_HINT, required=False, maxlength=1600),
         strings("dau_tich", "Danh sách dấu tích (tùy chọn)", max=8, maxlength=200),
         lst("so_lieu", "Ô thông tin (tùy chọn)", fields=[string("nhan", "Nhãn", "Ví dụ: Thành lập", maxlength=40),
                                                         string("gia_tri", "Giá trị", "Ví dụ: Tháng 01/2019", maxlength=60)],
             summary="{{fields.nhan}}: {{fields.gia_tri}}", max=6, label_singular="ô thông tin"),
         lst("lien_ket", "Liên kết dưới đoạn văn (tùy chọn)", fields=link()["fields"], summary="{{fields.nhan}}", max=2,
             label_singular="liên kết", _item_rules=[_rule_link]),
         *photo_fields(),
     ], "_rules": [_rule_photo]},
    {"name": "cac_buoc", "label": "5 · Các bước", "summary": "Các bước: {{fields.tieu_de}}",
     "fields": common(default_bg="kem") + section_head("Bốn bước", "Từ cuộc gọi đầu tiên đến khi xong việc") + [
         link("lien_ket", "Liên kết cạnh tiêu đề (tùy chọn)", required=False),
         boolean("can_giua", "Căn giữa tiêu đề", default=False),
         select("kieu", "Kiểu hiển thị", [("ngang", "Hàng ngang, số tròn"), ("the", "Thẻ có số + biểu tượng")], default="ngang", required=False),
         lst("buoc", "Các bước (tự đánh số)", fields=[
             string("tieu_de", "Tên bước", maxlength=70), text("mo_ta", "Mô tả", maxlength=420),
             string("ket_qua", "Kết quả của bước (tùy chọn)", "Hiện kèm dấu tích dưới mô tả", required=False, maxlength=90),
             icon(required=False, hint="Chỉ dùng với kiểu Thẻ")],
             summary="{{fields.tieu_de}}", min=2, max=6, label_singular="bước"),
         lst("ghi_chu", "Ghi chú dưới các bước (tùy chọn)", fields=[
             icon(), string("dam", "Phần in đậm", maxlength=60), string("noi_dung", "Nội dung", maxlength=220)],
             summary="{{fields.dam}}", max=3, label_singular="ghi chú"),
     ]},
    {"name": "dong_thoi_gian", "label": "6 · Dòng thời gian", "summary": "Dòng thời gian: {{fields.tieu_de}}",
     "fields": common() + section_head() + [
         lst("moc", "Các mốc (mốc cuối được tô nổi bật)", fields=[
             string("thoi_gian", "Thời gian", "Ví dụ: 09/1999", maxlength=20), string("tieu_de", "Tiêu đề", maxlength=90),
             text("mo_ta", "Mô tả", maxlength=500)], summary="{{fields.thoi_gian}} – {{fields.tieu_de}}", min=2, max=12,
             label_singular="mốc"),
     ]},
    {"name": "doi_ngu", "label": "7 · Đội ngũ", "summary": "Đội ngũ: {{fields.tieu_de}}",
     "fields": common(default_bg="kem") + section_head("Đội ngũ", "Đội ngũ Luật Sư Nam") + [
         select("kieu", "Cách trình bày", [("noi_bat", "Người đầu tiên nổi bật có ảnh, người khác là thẻ nhỏ"), ("luoi", "Lưới thẻ đều nhau")],
                default="noi_bat", required=False),
         lst("thanh_vien", "Thành viên", fields=[
             string("ten", "Họ tên", "Ví dụ: Luật sư Nguyễn Trọng Nam", maxlength=70),
             string("chuc_danh", "Chức danh", "Ví dụ: Giám đốc · Luật sư điều hành", maxlength=90),
             text("mo_ta", "Giới thiệu ngắn", maxlength=600),
             icon(required=False, hint="Hiện ở thẻ nhỏ khi không có ảnh"),
             lst("so_lieu", "Ô thông tin (tùy chọn)", fields=[string("nhan", "Nhãn", maxlength=40), string("gia_tri", "Giá trị", maxlength=60)],
                 summary="{{fields.nhan}}: {{fields.gia_tri}}", max=6, label_singular="ô thông tin"),
             *photo_fields(None)], summary="{{fields.ten}}", min=1, max=12, label_singular="thành viên", _item_rules=[_rule_photo]),
     ]},
    {"name": "dau_tich", "label": "8 · Danh sách dấu tích", "summary": "Danh sách: {{fields.tieu_de}}",
     "fields": common() + section_head("Chuẩn bị trước", "Giấy tờ nên mang theo buổi gặp đầu tiên") + [
         select("so_cot", "Số cột", [("1", "1 cột"), ("2", "2 cột")], default="1", required=False),
         strings("muc", "Các dòng", min=1, max=16, maxlength=220),
         string("ghi_chu_cuoi", "Ghi chú nhỏ dưới danh sách (tùy chọn)", required=False, maxlength=220),
         obj("hop_meo", "Hộp mẹo bên cạnh (tùy chọn)", [
             string("nhan", "Nhãn nhỏ", required=False, maxlength=60), string("tieu_de", "Tiêu đề", required=False, maxlength=90),
             text("mo_ta", "Mô tả", required=False, maxlength=300),
             lst("y", "Các ý (tự đánh số)", fields=[string("dam", "Phần in đậm", maxlength=70), string("noi_dung", "Nội dung", maxlength=200)],
                 summary="{{fields.dam}}", max=8, label_singular="ý")], collapsed="auto", required=False),
     ]},
    {"name": "doan_van", "label": "9 · Đoạn văn tự do", "summary": "Đoạn văn",
     "fields": common() + [
         select("do_rong", "Độ rộng", [("hep", "Hẹp – dễ đọc"), ("rong", "Rộng")], default="hep", required=False),
         editor("noi_dung", "Nội dung", "Đề mục, đậm, liên kết, danh sách, bảng, ảnh. " + TOKEN_HINT),
     ]},
    {"name": "hoi_dap", "label": "10 · Hỏi đáp", "summary": "Hỏi đáp: {{fields.tieu_de}}",
     "fields": common() + section_head("Hỏi đáp", "Những câu anh chị hay hỏi") + [
         link("lien_ket", "Liên kết dưới mô tả (tùy chọn)", required=False),
         _f("select", "cau_hoi", "Chọn câu hỏi từ kho Hỏi đáp chung",
            "Tích các câu muốn hiện, theo thứ tự tích. Sửa nội dung câu hỏi tại mục Hỏi đáp chung.",
            options=[], multiple=True, min=1, max=10, _options="faq", dropdown_threshold=20),
     ]},
    {"name": "luoi_linh_vuc", "label": "11 · Lưới lĩnh vực (tự động)", "summary": "Lưới lĩnh vực: {{fields.tieu_de}}",
     "fields": common(default_bg="kem") + section_head("Theo lĩnh vực", "Anh chị đang gặp chuyện gì?") + [
         link("lien_ket", "Liên kết cạnh tiêu đề (tùy chọn)", required=False),
         select("kieu", "Kiểu thẻ", [("tinh_huong", "Tình huống – “Anh chị đang gặp chuyện gì?”"), ("dich_vu", "Tên lĩnh vực + mô tả ngắn")],
                default="tinh_huong", required=False),
     ]},
    {"name": "bai_viet_moi", "label": "12 · Bài viết mới nhất (tự động)", "summary": "Bài viết mới: {{fields.tieu_de}}",
     "fields": common(default_bg="kem") + section_head("Bài viết", "Kiến thức pháp luật dễ hiểu") + [
         link("lien_ket", "Liên kết cạnh tiêu đề (tùy chọn)", required=False),
         number("so_bai", "Số bài hiện", min=1, max=12, default=3, required=False),
         select("so_cot", "Số cột", [("2", "2 cột"), ("3", "3 cột")], default="3", required=False),
         relation_service("linh_vuc", "Chỉ lấy bài thuộc lĩnh vực (tùy chọn)", required=False),
     ]},
    {"name": "giay_to_linh_vuc", "label": "13 · Giấy tờ theo lĩnh vực (tự động)", "summary": "Giấy tờ theo lĩnh vực",
     "fields": common(default_bg="kem") + section_head("Theo lĩnh vực", "Giấy tờ theo từng loại vụ việc") + [
         relation_service("linh_vuc", "Chỉ hiện các lĩnh vực (để trống = tất cả)", multiple=True, required=False),
     ]},
    {"name": "kenh_lien_he", "label": "14 · Kênh liên hệ", "summary": "Kênh liên hệ",
     "fields": common() + [
         select("kenh", "Kênh hiện", [("goi", "Gọi điện"), ("zalo", "Nhắn Zalo"), ("email", "Gửi email"), ("van_phong", "Đến văn phòng")],
                multiple=True, min=1, default=["goi", "zalo", "email"], hint="Số điện thoại, email, địa chỉ tự lấy từ Thông tin công ty"),
         string("ghi_chu_goi", "Ghi chú dưới Gọi điện", required=False, maxlength=120, default="{{gio_lam_viec}}. Việc gấp, hãy gọi trực tiếp."),
         string("ghi_chu_zalo", "Ghi chú dưới Nhắn Zalo", required=False, maxlength=120),
         string("ghi_chu_email", "Ghi chú dưới Gửi email", required=False, maxlength=120),
         boolean("viec_gap", "Hiện ô “Việc gấp?”", default=True),
         rich("noi_dung_viec_gap", "Nội dung ô Việc gấp", required=False, maxlength=420),
     ]},
    {"name": "ban_do", "label": "15 · Bản đồ văn phòng", "summary": "Bản đồ: {{fields.tieu_de}}",
     "fields": common() + section_head("Đường đến văn phòng", "Văn phòng Luật Sư Nam") + [
         string("ghi_chu_hotline", "Ghi chú dưới hotline", required=False, maxlength=100, default="Ưu tiên gọi trực tiếp với việc gấp"),
     ]},
]
BLOCK_BY_NAME = {b["name"]: b for b in BLOCK_TYPES}


def blocks_field():
    return lst("cac_khoi", "Các khối trên trang", types=BLOCK_TYPES, min=1, max=15, label_singular="khối",
               hint="Thêm, xóa, kéo để đổi thứ tự. Muốn tạm ẩn, tắt “Hiển thị khối này” thay vì xóa.")


# ---------------------------------------------------------------------------
# Câu chữ dùng chung, trang lĩnh vực
# ---------------------------------------------------------------------------
def _sec(name, label, *extra, text_=True):
    f = [string("nhan", "Nhãn nhỏ", maxlength=60), string("tieu_de", "Tiêu đề", maxlength=110)]
    if text_:
        f.append(text("mo_ta", "Mô tả", required=False, maxlength=300))
    return obj(name, label, f + list(extra), collapsed=True)


SERVICE_TEXT_HINT = "Dùng {{ten_linh_vuc}} để chèn tên lĩnh vực (chữ thường), vd. “thừa kế”."

# ---------------------------------------------------------------------------
# Các chuyên mục (collections)
# ---------------------------------------------------------------------------
SLUG_HINT = ("Đường dẫn tự tạo từ tiêu đề, bỏ dấu. Nên rút gọn còn 3–6 từ chính. "
             "**Sau khi lưu không đổi được** (đổi đường dẫn làm mất thứ hạng Google); cần đổi: xem Cài đặt → Chuyển hướng.")


def slug_opts(field):
    return {"template": "{{" + field + "}}", "editable": ["create"], "hint": SLUG_HINT, "pattern": SLUG_PATTERN}


def collections():
    return [
        {"name": "bai_viet", "label": "Bài viết", "label_singular": "bài viết", "icon": "article",
         "description": "Bài viết pháp lý tại /kien-thuc-phap-ly/. Bài mới luôn là bản nháp cho tới khi luật sư duyệt.",
         "folder": "content/bai-viet", "extension": "md", "format": "yaml-frontmatter",
         "identifier_field": "tieu_de", "slug": slug_opts("tieu_de"),
         "summary": "{{tieu_de}}{{fields.nhap | ternary(' · BẢN NHÁP', '')}}",
         "sortable_fields": {"fields": ["ngay_dang", "tieu_de", "ngay_cap_nhat"], "default": {"field": "ngay_dang", "direction": "descending"}},
         "view_filters": [{"name": "nhap", "label": "Bản nháp", "field": "nhap", "eq": True},
                          {"name": "da-dang", "label": "Đã đăng", "field": "nhap", "ne": True}],
         "preview_path": "kien-thuc-phap-ly/{{slug}}/",
         "fields": [
             string("tieu_de", "Tiêu đề bài viết",
                    "Hiện ở đầu bài. Ví dụ: Ly hôn đơn phương: căn cứ, hồ sơ và cách Tòa án xem xét quyền nuôi con",
                    minlength=20, maxlength=110),
             boolean("nhap", "Bản nháp – chưa đăng lên site",
                     "Bài mới luôn là nháp. Chỉ bỏ dấu khi luật sư phụ trách đã duyệt bản xem trước tại /nhap/<đường-dẫn>/.",
                     default=True),
             relation_service("linh_vuc", "Lĩnh vực chính", "Làm chuyên mục của bài và khung “Cần luật sư về…” cạnh bài."),
             date("ngay_dang", "Ngày đăng", default="{{now}}"),
             date("ngay_cap_nhat", "Ngày cập nhật", "Ngày rà soát nội dung gần nhất; không được trước ngày đăng. Để trống = ngày đăng.",
                  required=False),
             string("tieu_de_ngan", "Tiêu đề ngắn trên thẻ bài viết", "Để trống = dùng tiêu đề bài viết.", required=False, maxlength=80),
             text("tom_tat", "Tóm tắt trên thẻ bài viết", "1–2 câu, hiện ở danh sách bài viết.", minlength=60, maxlength=220),
             strings("tom_tat_nhanh", "Tóm tắt nhanh (3–4 ý)", "Khung “Tóm tắt nhanh” ở đầu bài. Mỗi ý ≤ 160 ký tự.",
                     min=3, max=4, maxlength=160, item_label="Ý"),
             text("doan_dan", "Đoạn dẫn đầu bài", "Đoạn mở đầu in to hơn, giới thiệu vấn đề.", minlength=80, maxlength=700),
             editor("body", "Nội dung bài viết",
                    "Dùng **Tiêu đề 2** cho mục chính (tự vào mục lục), **Tiêu đề 3** cho mục nhỏ; nút **Trích dẫn** = hộp lưu ý. "
                    "Bảng: nút + → Bảng. Liên kết trong site: /dich-vu/thua-ke/. Khẳng định pháp lý luôn kèm điều luật; "
                    "không hứa hẹn kết quả (Quy tắc 9.1.6)."),
             relation_service("linh_vuc_lien_quan", "Lĩnh vực liên quan (cột phải)", "Tối đa 3. Để trống = chỉ lĩnh vực chính.",
                              multiple=True, max=3, required=False),
             seo("Ly hôn đơn phương: căn cứ, hồ sơ, quyền nuôi con",
                 "Khi nào Tòa án giải quyết ly hôn theo yêu cầu của một bên, hồ sơ cần chuẩn bị và nguyên tắc giao con."),
         ], "_rules": [_rule_dates]},
        {"name": "dich_vu", "label": "Lĩnh vực dịch vụ", "label_singular": "lĩnh vực", "icon": "balance",
         "description": "Mỗi lĩnh vực có trang /dich-vu/<đường-dẫn>/, thẻ ở trang chủ, menu và chân trang. Bấm “Sắp xếp lại” để kéo đổi thứ tự.",
         "folder": "content/dich-vu", "extension": "yml", "format": "yml",
         "identifier_field": "ten", "slug": slug_opts("ten"),
         "summary": "{{ten}}{{fields.nhap | ternary(' · BẢN NHÁP', '')}}",
         "reorder": {"key": "thu_tu"},
         "sortable_fields": {"fields": ["thu_tu", "ten"], "default": {"field": "thu_tu", "direction": "ascending"}},
         "preview_path": "dich-vu/{{slug}}/",
         "fields": [
             string("ten", "Tên lĩnh vực", "Ví dụ: Thừa kế. Hiện trên menu, thẻ, chân trang.", minlength=3, maxlength=45),
             boolean("nhap", "Bản nháp – chưa đăng lên site", default=True),
             number("thu_tu", "Thứ tự hiển thị", "Số nhỏ đứng trước (hoặc kéo thả bằng nút Sắp xếp ở danh sách).", min=1, max=99, default=99),
             icon("bieu_tuong", "Biểu tượng lĩnh vực"),
             icon("bieu_tuong_tinh_huong", "Biểu tượng trên thẻ tình huống (tùy chọn)", required=False),
             text("mo_ta_ngan", "Mô tả ngắn", "Hiện ở thẻ lĩnh vực, khung cạnh bài viết, ảnh chia sẻ.", minlength=50, maxlength=180),
             obj("the_tinh_huong", "Thẻ “Anh chị đang gặp chuyện gì?”", [
                 string("tieu_de", "Tình huống", "Ví dụ: Chia đất, chia nhà sau khi cha mẹ mất", maxlength=70),
                 text("mo_ta", "Mô tả", maxlength=200)], collapsed=True),
             string("nhan_dau_trang", "Nhãn nhỏ trên tiêu đề trang", "Ví dụ: Luật sư thừa kế", maxlength=60),
             red_title("tieu_de_trang", "Tiêu đề trang (H1)", example="Chia di sản thừa kế đúng luật, *giữ được tình thân*"),
             text("mo_dau", "Đoạn mở đầu", minlength=80, maxlength=600),
             boolean("viec_gap", "Hiện ô “Việc gấp?” dưới tiêu đề", "Dùng cho lĩnh vực cần gọi ngay, vd. Hình sự.", default=False),
             strings("tinh_huong", "Tình huống thường gặp", min=3, max=8, maxlength=220, item_label="Tình huống"),
             obj("pham_vi", "Luật sư giúp được gì", [
                 text("gioi_thieu", "Đoạn giới thiệu", maxlength=500),
                 lst("cac_viec", "Các việc", fields=[string("tieu_de", "Tên việc", maxlength=70), text("mo_ta", "Mô tả", maxlength=300)],
                     summary="{{fields.tieu_de}}", min=2, max=9, label_singular="việc")], collapsed=True),
             strings("viec_nen_lam", "Việc nên làm ngay", min=2, max=6, maxlength=260, item_label="Việc"),
             obj("luu_y", "Hộp lưu ý", [string("tieu_de", "Tiêu đề", default="Lưu ý", maxlength=40),
                                        text("noi_dung", "Nội dung", maxlength=320)], collapsed=True),
             obj("nguyen_tac", "Hộp “Cách luật sư làm việc”", [string("tieu_de", "Tiêu đề", maxlength=80),
                                                               text("noi_dung", "Nội dung", maxlength=400)], collapsed=True),
             lst("cac_buoc", "Các bước làm việc", fields=[string("tieu_de", "Tên bước", maxlength=50), text("mo_ta", "Mô tả", maxlength=200)],
                 summary="{{fields.tieu_de}}", min=3, max=6, label_singular="bước"),
             obj("giay_to", "Giấy tờ", [string("tieu_de", "Tiêu đề", default="Giấy tờ nên mang theo", maxlength=60),
                                        strings("danh_sach", "Danh sách giấy tờ", min=2, max=10, maxlength=160, item_label="Giấy tờ")],
                 collapsed=True),
             strings("nhan_duoc", "Anh chị sẽ nhận được", min=2, max=8, maxlength=160),
             lst("hoi_dap", "Hỏi đáp riêng của lĩnh vực", fields=[
                 string("hoi", "Câu hỏi", maxlength=140),
                 rich("dap", "Câu trả lời", "Có dẫn điều luật cụ thể, in đậm tên điều luật.", maxlength=1400)],
                 summary="{{fields.hoi}}", min=1, max=8, label_singular="câu hỏi"),
             strings("can_cu_phap_ly", "Căn cứ pháp luật chủ yếu", min=1, max=8, maxlength=140, item_label="Văn bản"),
             obj("lien_he", "Lời mời liên hệ cuối trang", [string("tieu_de", "Tiêu đề", maxlength=110),
                                                           text("doan_moi", "Đoạn mời", maxlength=320)], collapsed=True),
             relation_service("linh_vuc_lien_quan", "Lĩnh vực liên quan", "Tối đa 3, hiện cuối trang theo thứ tự chọn.",
                              multiple=True, max=3, required=False),
             seo("Luật sư tư vấn Thừa kế tại TP.HCM",
                 "Luật sư tư vấn lập di chúc, khai nhận và phân chia di sản, giải quyết tranh chấp thừa kế."),
         ]},
        {"name": "hoi_dap", "label": "Hỏi đáp chung", "icon": "quiz",
         "description": "Kho câu hỏi dùng chung: trang Câu hỏi thường gặp hiện tất cả; các trang khác chọn câu từ đây.",
         "files": [{"name": "hoi_dap", "label": "Kho hỏi đáp", "file": "content/hoi-dap.yml", "format": "yml", "fields": [
             lst("cau_hoi", "Câu hỏi (kéo để đổi thứ tự trên trang Câu hỏi thường gặp)", fields=[
                 string("hoi", "Câu hỏi", maxlength=140),
                 string("ma", "Mã neo (tùy chọn)", "Để trống = tự tạo từ câu hỏi. Trang khác link tới: /cau-hoi-thuong-gap/#<mã>. "
                        "Đã có mã thì đừng đổi – liên kết cũ sẽ hỏng (build sẽ báo).", required=False, pattern=ANCHOR_PATTERN, maxlength=60),
                 rich("dap", "Câu trả lời", "Mỗi đoạn cách nhau một dòng trống. Dẫn điều luật cụ thể.", maxlength=2000)],
                 summary="{{fields.hoi}}", min=1, label_singular="câu hỏi", _rules=[_rule_unique("ma", "Mã neo")]),
         ]}]},
        {"divider": True, "name": "divider-trang"},
        {"name": "trang", "label": "Trang dựng từ khối", "label_singular": "trang", "icon": "dashboard_customize",
         "description": "Trang chủ, Giới thiệu, Liên hệ… và mọi trang mới: ghép từ các khối có sẵn. Trang mới mặc định là bản nháp.",
         "folder": "content/trang", "extension": "yml", "format": "yml",
         "identifier_field": "tieu_de", "slug": slug_opts("tieu_de"),
         "summary": "{{tieu_de}}{{fields.nhap | ternary(' · BẢN NHÁP', '')}}",
         "preview_path": "{{slug}}/",
         "fields": [
             string("tieu_de", "Tên trang", "Hiện ở đường dẫn điều hướng và kết quả tìm kiếm. Ví dụ: Phí dịch vụ", maxlength=60),
             boolean("nhap", "Bản nháp – chưa đăng lên site", default=True),
             page_link("trang_cha", "Nằm trong mục (tùy chọn)",
                       "Ví dụ: “Vì sao chọn chúng tôi” nằm trong Giới thiệu → Trang chủ › Giới thiệu › Vì sao chọn chúng tôi.", required=False),
             select("loai_trang", "Loại trang (cho Google)", [("WebPage", "Trang thông thường"), ("AboutPage", "Trang giới thiệu"),
                                                              ("ContactPage", "Trang liên hệ")], default="WebPage"),
             page_head_fields(hint="Tiêu đề, đoạn mở đầu ở đầu trang (và trên ảnh chia sẻ). Tự ẩn khi khối đầu tiên là “Đầu trang lớn (Hero)”; "
                              "Trang chủ không hiện phần này."),
             blocks_field(),
             contact_band_fields(),
             seo("Phí dịch vụ luật sư và cách tính thù lao", "Cách Luật Sư Nam tính thù lao theo Điều 55 Luật Luật sư, khoản nào báo trước."),
         ]},
        {"name": "trang_tong_hop", "label": "Trang tổng hợp", "icon": "view_list",
         "description": "Dịch vụ, Kiến thức pháp lý, Câu hỏi thường gặp: sửa chữ; danh sách bên dưới tự động.",
         "files": [
             {"name": "dich_vu", "label": "Trang Dịch vụ (/dich-vu/)", "file": "content/trang-tong-hop/dich-vu.yml", "format": "yml",
              "fields": [page_head_fields("Đầu trang", with_card=True),
                         _sec("luoi", "Khối lưới lĩnh vực"),
                         obj("hinh_thuc", "Khối “Hình thức hỗ trợ”", [
                             string("nhan", "Nhãn nhỏ", maxlength=60), string("tieu_de", "Tiêu đề", maxlength=110),
                             text("mo_ta", "Mô tả", required=False, maxlength=300),
                             lst("the", "Các thẻ", fields=[icon(), string("tieu_de", "Tiêu đề", maxlength=70), text("mo_ta", "Mô tả", maxlength=300)],
                                 summary="{{fields.tieu_de}}", min=1, max=6, label_singular="thẻ")], collapsed=True),
                         contact_band_fields(),
                         seo("Lĩnh vực hoạt động – Dịch vụ pháp lý", "Luật Sư Nam tư vấn, đại diện và tham gia tố tụng trong 7 lĩnh vực.")]},
             {"name": "kien_thuc", "label": "Trang Kiến thức pháp lý (/kien-thuc-phap-ly/)", "file": "content/trang-tong-hop/kien-thuc-phap-ly.yml",
              "format": "yml",
              "fields": [page_head_fields("Đầu trang", with_card=True),
                         _sec("bai_viet", "Khối danh sách bài viết"),
                         lst("the_cong_cu", "Hai thẻ lớn giữa trang", fields=[
                             icon(), string("nhan", "Nhãn nhỏ", maxlength=50), string("tieu_de", "Tiêu đề", maxlength=90),
                             text("mo_ta", "Mô tả", maxlength=260), link("lien_ket", "Dẫn tới")],
                             summary="{{fields.tieu_de}}", min=1, max=2, label_singular="thẻ",
                             hint="Thẻ thứ nhất nền tối, thẻ thứ hai nền sáng."),
                         _sec("theo_linh_vuc", "Khối “Theo lĩnh vực”", link("lien_ket", "Liên kết cạnh tiêu đề", required=False)),
                         contact_band_fields(),
                         seo("Kiến thức pháp lý – Bài viết, tra cứu luật", "Bài viết phân tích pháp luật về thừa kế, hôn nhân gia đình, đất đai.")]},
             {"name": "hoi_dap", "label": "Trang Câu hỏi thường gặp (/cau-hoi-thuong-gap/)", "file": "content/trang-tong-hop/cau-hoi-thuong-gap.yml",
              "format": "yml",
              "fields": [page_head_fields("Đầu trang", with_card=True),
                         rich("ghi_chu_cuoi", "Ghi chú dưới danh sách câu hỏi", required=False, maxlength=400),
                         lst("tim_hieu_them", "Cột “Tìm hiểu thêm”", fields=[icon(), *link("lien_ket")["fields"]],
                             summary="{{fields.nhan}}", max=6, label_singular="liên kết", _item_rules=[_rule_link]),
                         contact_band_fields(),
                         seo("Câu hỏi thường gặp khi thuê luật sư", "Giải đáp về chi phí thuê luật sư, bảo mật thông tin, thời hiệu.")]},
         ]},
        {"name": "trang_van_ban", "label": "Trang văn bản", "icon": "description",
         "description": "Chính sách bảo mật, Điều khoản sử dụng, Miễn trừ trách nhiệm, trang lỗi 404. Bố cục cố định, mục lục tự động.",
         "files": [
             *[{"name": n.replace("-", "_"), "label": l, "file": f"content/trang-van-ban/{n}.md", "format": "yaml-frontmatter",
                "fields": [string("tieu_de", "Tên trang", maxlength=60),
                           string("nhan", "Nhãn nhỏ trên tiêu đề", required=False, maxlength=60),
                           red_title("tieu_de_trang", "Tiêu đề lớn (H1)"),
                           text("mo_dau", "Đoạn mở đầu", "Dòng “Cập nhật lần cuối” tự thêm theo ngày cập nhật.", required=False, maxlength=400),
                           date("ngay_cap_nhat", "Ngày cập nhật"),
                           editor("body", "Nội dung", "Mỗi mục bắt đầu bằng **Tiêu đề 2** (tự vào mục lục bên phải). " + TOKEN_HINT),
                           seo(l, "Chính sách thu thập, sử dụng và bảo vệ dữ liệu cá nhân trên website Luật Sư Nam.")]}
               for n, l in [("chinh-sach-bao-mat", "Chính sách bảo mật"), ("dieu-khoan-su-dung", "Điều khoản sử dụng"),
                            ("mien-tru-trach-nhiem", "Miễn trừ trách nhiệm")]],
             {"name": "trang_404", "label": "Trang lỗi 404", "file": "content/trang-van-ban/404.yml", "format": "yml",
              "fields": [string("tieu_de", "Tiêu đề", maxlength=90), text("noi_dung", "Nội dung", maxlength=300),
                         obj("seo", "SEO", [string("tieu_de", "Tiêu đề tab trình duyệt", maxlength=60),
                                            text("mo_ta", "Mô tả", maxlength=160)], collapsed=True)]},
         ]},
        {"divider": True, "name": "divider-cai-dat"},
        {"name": "cai_dat", "label": "Cài đặt", "icon": "settings",
         "description": "Thông tin công ty, menu, câu chữ dùng chung, SEO, mã theo dõi, chuyển hướng, ảnh thương hiệu.",
         "files": settings_files()},
    ]


def _rule_dates(v, add):
    a, b = v.get("ngay_dang"), v.get("ngay_cap_nhat")
    if a and b and b < a:
        add(f"Ngày cập nhật ({b}) không được trước ngày đăng ({a}).")


def _rule_unique(key, label):
    def rule(items, add):
        seen = set()
        for i, it in enumerate(items or [], 1):
            k = (it or {}).get(key)
            if k and k in seen:
                add(f"{label} “{k}” bị trùng (mục {i}). Mỗi mục cần {label.lower()} riêng.")
            seen.add(k)
    return rule


def settings_files():
    return [
        {"name": "cong_ty", "label": "Thông tin công ty", "file": "content/cai-dat/cong-ty.yml", "format": "yml", "fields": [
            string("ten_phap_nhan", "Tên pháp nhân", maxlength=80),
            string("ten_ngan", "Tên ngắn", "Dùng làm đuôi tiêu đề trang và trong câu chữ.", maxlength=40),
            string("thuong_hieu", "Tên thương hiệu", maxlength=40),
            string("khau_hieu", "Khẩu hiệu", maxlength=60),
            string("luat_su", "Luật sư phụ trách", "Ví dụ: Luật sư Nguyễn Trọng Nam", maxlength=60),
            string("chuc_danh_luat_su", "Chức danh trên thẻ “Luật sư phụ trách”", maxlength=90),
            string("hotline", "Hotline", "Số di động 10 số, có thể có dấu cách: 0983 498 499. Nút Gọi, Zalo, dữ liệu Google tự cập nhật.",
                   pattern=["^0[0-9 .]{9,13}$", "Số điện thoại Việt Nam bắt đầu bằng 0, ví dụ 0983 498 499"]),
            string("zalo", "Liên kết Zalo", "Để trống = https://zalo.me/<hotline>.", required=False,
                   pattern=["^(https://zalo\\.me/.+)?$", "Bắt đầu bằng https://zalo.me/"]),
            string("email", "Email", pattern=["^[^@\\s]+@[^@\\s]+\\.[a-z]{2,}$", "Email chưa đúng định dạng"]),
            obj("dia_chi", "Địa chỉ văn phòng", [
                string("so_nha_duong", "Số nhà, đường", maxlength=80), string("phuong", "Phường/xã", maxlength=80),
                string("thanh_pho", "Tỉnh/thành phố", maxlength=80),
                string("thanh_pho_viet_tat", "Tỉnh/thành phố viết tắt", "Dùng ở dải địa chỉ ngắn, vd. TP.HCM", maxlength=20)]),
            obj("gio_lam_viec", "Giờ làm việc", [
                select("ngay", "Ngày làm việc", DAYS, multiple=True, min=1, dropdown_threshold=7),
                string("mo_cua", "Giờ mở cửa", pattern=TIME_PATTERN), string("dong_cua", "Giờ đóng cửa", pattern=TIME_PATTERN),
                string("hien_thi", "Cách viết giờ làm việc (tùy chọn)", "Để trống = tự viết, vd. “Thứ 2 – Thứ 6: 08:00 – 17:30”.",
                       required=False, maxlength=80),
                string("ngoai_gio", "Ghi chú ngoài giờ", maxlength=140)]),
            rich("gioi_thieu_chan_trang", "Giới thiệu ngắn ở chân trang", maxlength=400),
        ]},
        {"name": "menu", "label": "Menu và chân trang", "file": "content/cai-dat/menu.yml", "format": "yml", "fields": [
            lst("menu", "Menu chính", types=[
                {"name": "lien_ket", "label": "Mục đơn", "summary": "{{fields.nhan}}",
                 "fields": [string("nhan", "Chữ trên menu", maxlength=30), page_link("trang", "Trang")]},
                {"name": "menu_xo", "label": "Mục có menu xổ", "summary": "{{fields.nhan}} ▾",
                 "fields": [string("nhan", "Chữ trên menu", maxlength=30),
                            page_link("trang", "Trang chính của mục", "Dùng để tô sáng mục khi đang ở trang này."),
                            lst("muc_con", "Mục con", fields=[string("nhan", "Chữ", maxlength=50),
                                                               string("mo_ta", "Dòng mô tả nhỏ", required=False, maxlength=70),
                                                               page_link("trang", "Trang")],
                                summary="{{fields.nhan}}", min=1, max=8, label_singular="mục con")]},
                {"name": "menu_linh_vuc", "label": "Mục lĩnh vực (menu xổ lớn)", "summary": "{{fields.nhan}} ▾ (lĩnh vực)",
                 "fields": [string("nhan", "Chữ trên menu", maxlength=30), page_link("trang", "Trang tổng quan"),
                            lst("nhom", "Nhóm lĩnh vực", fields=[string("ten_nhom", "Tên nhóm", maxlength=40),
                                                                 relation_service("linh_vuc", "Lĩnh vực trong nhóm", multiple=True, min=1)],
                                summary="{{fields.ten_nhom}}", min=1, max=4, label_singular="nhóm",
                                hint="Lĩnh vực mới chưa xếp vào nhóm nào sẽ tự nằm cuối nhóm cuối cùng."),
                            string("nhan_tat_ca", "Chữ liên kết “xem tất cả”", maxlength=50)]},
            ], min=1, max=7, label_singular="mục menu", hint="Kéo để đổi thứ tự. Tối đa 7 mục để menu không xuống dòng."),
            obj("tieu_de_cot", "Tiêu đề các cột chân trang", [
                string("ve_chung_toi", "Cột liên kết", maxlength=40), string("linh_vuc", "Cột lĩnh vực (tự động)", maxlength=40),
                string("van_phong", "Cột văn phòng", maxlength=40)], collapsed=True),
            lst("chan_trang", "Cột liên kết ở chân trang", fields=link("lien_ket")["fields"], summary="{{fields.nhan}}",
                min=1, max=10, label_singular="liên kết", _item_rules=[_rule_link]),
            lst("lien_ket_phap_ly", "Liên kết cuối chân trang", fields=link("lien_ket")["fields"], summary="{{fields.nhan}}",
                max=5, label_singular="liên kết", _item_rules=[_rule_link]),
            lst("goi_y_tim_kiem", "Gợi ý trong ô tìm kiếm", fields=link("lien_ket")["fields"], summary="{{fields.nhan}}",
                max=6, label_singular="gợi ý", _item_rules=[_rule_link]),
        ]},
        {"name": "cau_chu", "label": "Câu chữ dùng chung", "file": "content/cai-dat/cau-chu.yml", "format": "yml", "fields": [
            obj("lien_he_cuoi_trang", "Khối liên hệ cuối trang (mặc định)", [
                string("nhan", "Nhãn nhỏ", maxlength=60), string("tieu_de", "Tiêu đề", maxlength=110),
                text("doan_moi", "Đoạn mời", maxlength=320),
                string("ghi_chu_zalo", "Ghi chú thẻ Nhắn Zalo", maxlength=120),
                string("ghi_chu_van_phong", "Ghi chú thẻ Đến văn phòng", maxlength=80)], collapsed=True),
            obj("viec_gap", "Ô “Việc gấp?”", [string("nhan", "Chữ đậm", maxlength=30),
                                              rich("noi_dung", "Nội dung trên trang lĩnh vực", maxlength=400)], collapsed=True),
            rich("mien_tru_chan_trang", "Miễn trừ trách nhiệm ở chân trang", maxlength=600),
            rich("mien_tru_cuoi_bai", "Lưu ý cuối mỗi bài viết", maxlength=500),
            obj("bai_viet", "Trang bài viết", [
                string("tac_gia", "Dòng tác giả", "Ví dụ: Ban biên tập {{ten_ngan}}", maxlength=60),
                string("doc_tiep_nhan", "Nhãn khối đọc tiếp", maxlength=40),
                string("doc_tiep_tieu_de", "Tiêu đề khối đọc tiếp", maxlength=60)], collapsed=True),
            obj("trang_linh_vuc", "Trang lĩnh vực – tiêu đề các mục cố định", [
                strings("muc_luc", "Thanh mục lục dưới đầu trang (6 mục, đúng thứ tự)", min=6, max=6, maxlength=30, item_label="Mục"),
                _sec("tinh_huong", "Mục Tình huống", rich("cuoi", "Dòng dưới danh sách tình huống", maxlength=300)),
                _sec("pham_vi", "Mục Luật sư giúp gì", text_=False),
                _sec("viec_nen_lam", "Mục Việc nên làm ngay", string("nhan_nguyen_tac", "Nhãn hộp Cách luật sư làm việc", maxlength=50)),
                _sec("quy_trinh", "Mục Các bước", string("lien_ket", "Chữ liên kết tới Quy trình làm việc", maxlength=50)),
                _sec("ho_so", "Mục Giấy tờ", string("tieu_de_nhan_duoc", "Tiêu đề cột Anh chị sẽ nhận được", maxlength=60),
                     string("lien_ket_ho_so", "Chữ liên kết hướng dẫn hồ sơ", maxlength=60),
                     string("lien_ket_chi_phi", "Chữ liên kết chi phí", maxlength=60)),
                _sec("hoi_dap", "Mục Hỏi đáp", string("tieu_de_can_cu", "Tiêu đề hộp căn cứ pháp luật", maxlength=60),
                     string("ghi_chu_can_cu", "Ghi chú dưới căn cứ", maxlength=200)),
                _sec("tham_khao", "Mục Đọc thêm", string("lien_ket", "Chữ liên kết", maxlength=40), text_=False),
                _sec("lien_quan", "Mục Lĩnh vực liên quan", string("lien_ket", "Chữ liên kết", maxlength=40), text_=False),
                string("nhan_lien_he", "Nhãn khối liên hệ cuối trang", "Ví dụ: Tư vấn {{ten_linh_vuc}}", maxlength=60),
                lst("the_bo_sung", "Thẻ bổ sung khi lĩnh vực có ít hơn 3 bài viết", fields=[
                    string("nhan", "Nhãn", maxlength=30), string("tieu_de", "Tiêu đề", maxlength=80),
                    text("mo_ta", "Mô tả", maxlength=200), link("lien_ket", "Dẫn tới", with_label=False)],
                    summary="{{fields.tieu_de}}", min=3, max=3, label_singular="thẻ"),
            ], collapsed=True, hint=SERVICE_TEXT_HINT),
        ]},
        {"name": "seo", "label": "SEO mặc định", "file": "content/cai-dat/seo.yml", "format": "yml", "fields": [
            text("mo_ta_to_chuc", "Mô tả công ty cho Google (dữ liệu có cấu trúc)", maxlength=300),
            obj("anh_chia_se", "Ảnh chia sẻ mặc định (tự tạo)", [
                string("nhan", "Dòng nhãn", maxlength=50), string("tieu_de", "Tiêu đề", maxlength=60),
                text("mo_ta", "Mô tả", maxlength=160),
                image("anh_rieng", "Hoặc tải ảnh riêng 1200×630", required=False)], collapsed=True),
        ]},
        {"name": "theo_doi", "label": "Mã theo dõi", "file": "content/cai-dat/theo-doi.yml", "format": "yml", "fields": [
            string("search_console", "Mã xác minh Google Search Console", "Chỉ dán phần content của thẻ meta, vd. AbC123…",
                   required=False, pattern=["^[A-Za-z0-9_-]{20,90}$", "Chỉ dán chuỗi mã (chữ, số, - và _), không dán cả thẻ <meta>"]),
            boolean("da_cap_nhat_chinh_sach", "Đã cập nhật Chính sách bảo mật và thông báo cookie",
                    "Bắt buộc theo Nghị định 13/2023/NĐ-CP trước khi bật GA4, Meta Pixel, Zalo OA. Chưa tích: các mã dưới KHÔNG được xuất ra site.",
                    default=False),
            string("ga4", "Google Analytics 4 – Measurement ID", "Dạng G-XXXXXXXXXX", required=False,
                   pattern=["^(G-[A-Z0-9]{6,12})?$", "Mã GA4 có dạng G-XXXXXXXXXX"]),
            string("meta_pixel", "Meta Pixel ID", "Dãy 15–16 chữ số", required=False, pattern=["^([0-9]{15,16})?$", "Pixel ID là 15–16 chữ số"]),
            string("zalo_oa", "Zalo OA ID (khung chat)", "Dãy số OA ID", required=False, pattern=["^([0-9]{6,25})?$", "Zalo OA ID là dãy số"]),
        ]},
        {"name": "chuyen_huong", "label": "Chuyển hướng 301", "file": "content/cai-dat/chuyen-huong.yml", "format": "yml", "fields": [
            lst("chuyen_huong", "Đường dẫn cũ → mới", fields=[
                string("tu", "Đường dẫn cũ", "Bắt đầu và kết thúc bằng /, vd. /doi-ngu-luat-su/",
                       pattern=["^/([a-z0-9-]+/)+$", "Dạng /duong-dan/ (chữ thường không dấu, gạch nối)"]),
                string("den", "Chuyển tới", "Trang đang có, vd. /gioi-thieu/#doi-ngu-luat-su",
                       pattern=["^/([a-z0-9-]+/)*(#[a-z0-9-]+)?$", "Dạng /duong-dan/ hoặc /duong-dan/#ma-neo"]),
                string("ghi_chu", "Ghi chú", required=False, maxlength=120)],
                summary="{{fields.tu}} → {{fields.den}}", label_singular="chuyển hướng",
                hint="Build kiểm: đích phải là trang có thật, không vòng lặp, đường dẫn cũ không trùng trang đang có.",
                _rules=[_rule_unique("tu", "Đường dẫn cũ")]),
        ]},
        {"name": "anh_thuong_hieu", "label": "Ảnh thương hiệu", "file": "content/cai-dat/anh-thuong-hieu.yml", "format": "yml", "fields": [
            image("logo", "Logo (nền trong suốt, vuông)", "Build tự cắt ra favicon, biểu tượng ứng dụng.",
                  media_folder="/content/anh-thuong-hieu", public_folder="/content/anh-thuong-hieu"),
            image("van_phong", "Ảnh luật sư tại văn phòng", "Ảnh ngang. Dùng ở Trang chủ, Giới thiệu, ảnh chia sẻ.",
                  media_folder="/content/anh-thuong-hieu", public_folder="/content/anh-thuong-hieu"),
            image("phien_toa", "Ảnh luật sư tại phiên tòa", "Ảnh gần vuông, thấy rõ khuôn mặt. Build cắt ra ảnh thẻ và ảnh tròn.",
                  media_folder="/content/anh-thuong-hieu", public_folder="/content/anh-thuong-hieu"),
            obj("khuon_mat", "Vị trí khuôn mặt trong ảnh phiên tòa", [
                number("x", "Ngang (%)", "0 = mép trái, 100 = mép phải", min=0, max=100),
                number("y", "Dọc (%)", "0 = mép trên, 100 = mép dưới", min=0, max=100)],
                collapsed=True, hint="Dùng để cắt ảnh tròn và ảnh thẻ cho đúng khuôn mặt khi thay ảnh mới."),
        ]},
    ]


# ---------------------------------------------------------------------------
# Kiểm dữ liệu
# ---------------------------------------------------------------------------
MISSING = object()


def _empty(v):
    return v is None or v == "" or v == [] or v == {}


def _len_msg(n, lo, hi):
    if lo and n < lo:
        return f"Quá ngắn: {n} ký tự, cần tối thiểu {lo}."
    if hi and n > hi:
        return f"Quá dài: {n} ký tự, tối đa {hi}."
    return None


def validate(value, field, src, path, ctx):
    """Kiểm một giá trị theo định nghĩa trường; trả về giá trị đã chuẩn hóa (điền mặc định)."""
    w = field["widget"]
    label = " › ".join(path)

    def add(msg):
        LOI.them(src, label, msg)

    required = field.get("required", True)
    if value is MISSING or _empty(value):
        if w == "boolean":
            return field.get("default", False) if value is MISSING or value is None else bool(value)
        if w == "list":
            if field.get("min"):
                add(f"Cần ít nhất {field['min']} mục.")
            return []
        if w == "object":
            if required is False:
                return None
            value = {}
        elif required:
            d = field.get("default")
            if value is MISSING and d is not None and not (isinstance(d, str) and "{{" in d):
                return d  # trường có giá trị mặc định: tệp cũ chưa ghi thì dùng mặc định (CMS cũng hiện như vậy)
            add("Không được để trống.")
            return None
        else:
            d = field.get("default")
            if isinstance(d, str) and d.startswith("{{now"):
                d = None
            return d if d is not None else ([] if field.get("multiple") else None)

    if w in ("string", "text"):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            value = str(value)
        if not isinstance(value, str):
            add("Phải là chữ.")
            return ""
        value = value.strip() if w == "string" else value.strip("\n")
        if HTML_TAG_RE.search(value):
            add("Không dùng mã HTML (thẻ <…>). Ô tiêu đề: dùng *dấu sao* để tô đỏ; ô có nút định dạng: dùng nút Đậm / Nghiêng / Liên kết.")
        msg = _len_msg(len(value), field.get("minlength"), field.get("maxlength"))
        if msg:
            add(msg)
        if field.get("pattern") and value and not re.search(field["pattern"][0], value):
            add(field["pattern"][1] + f" (đang là “{value}”).")
        if field.get("_red") and value.count("*") % 2:
            add("Dấu * dùng để tô đỏ phải đi theo cặp, ví dụ: Chia di sản đúng luật, *giữ được tình thân*.")
        return value
    if w == "richtext":
        if not isinstance(value, str):
            add("Phải là chữ.")
            return ""
        value = value.strip()
        stripped = re.sub(r"`[^`]*`", "", value)
        if HTML_TAG_RE.search(stripped):
            add("Không dùng mã HTML (thẻ <…>). Dùng nút Đậm / Nghiêng / Liên kết trên thanh công cụ.")
        msg = _len_msg(len(value), None, field.get("_maxlength"))
        if msg:
            add(msg)
        return value
    if w == "boolean":
        if isinstance(value, str):
            value = value.strip().lower() in ("true", "1", "yes", "có")
        return bool(value)
    if w == "number":
        try:
            n = int(value)
        except (TypeError, ValueError):
            add(f"Phải là số nguyên (đang là “{value}”).")
            return field.get("default")
        if field.get("min") is not None and n < field["min"]:
            add(f"Nhỏ nhất là {field['min']}.")
        if field.get("max") is not None and n > field["max"]:
            add(f"Lớn nhất là {field['max']}.")
        return n
    if w == "datetime":
        if isinstance(value, datetime.datetime):
            value = value.date()
        if isinstance(value, datetime.date):
            return value.isoformat()
        s = str(value).strip()[:10]
        try:
            datetime.date.fromisoformat(s)
        except ValueError:
            add(f"Ngày không hợp lệ “{value}”. Chọn ngày trên lịch.")
            return None
        return s
    if w == "select":
        opts = field.get("options") or []
        values = [o["value"] if isinstance(o, dict) else o for o in opts]
        dynamic = field.get("_options")
        items = value if field.get("multiple") else [value]
        if field.get("multiple") and not isinstance(value, list):
            items = [value]
            value = items
        for it in items:
            if dynamic == "pages":
                if not isinstance(it, str) or not re.match(r"^/([a-z0-9-]+/)*$", it):
                    add(f"Trang “{it}” không hợp lệ. Chọn trang từ danh sách.")
            elif dynamic == "faq":
                if not isinstance(it, str) or not SLUG_RE.match(it):
                    add(f"Câu hỏi “{it}” không hợp lệ. Chọn từ danh sách.")
            elif str(it) not in [str(x) for x in values]:
                add(f"Giá trị “{it}” không có trong danh sách chọn.")
        if field.get("multiple"):
            if field.get("min") and len(items) < field["min"]:
                add(f"Chọn ít nhất {field['min']} mục.")
            if field.get("max") and len(items) > field["max"]:
                add(f"Chọn tối đa {field['max']} mục.")
            if len(set(map(str, items))) != len(items):
                add("Có mục được chọn trùng nhau.")
        return value
    if w == "relation":
        items = value if isinstance(value, list) else [value]
        for it in items:
            ctx.relations.append((src, label, field["collection"], it))
        if field.get("multiple"):
            if not isinstance(value, list):
                value = [value]
            if field.get("min") and len(value) < field["min"]:
                add(f"Chọn ít nhất {field['min']} mục.")
            if field.get("max") and len(value) > field["max"]:
                add(f"Chọn tối đa {field['max']} mục.")
        return value
    if w in ("image", "file"):
        if not isinstance(value, str):
            add("Đường dẫn ảnh không hợp lệ.")
            return None
        full = os.path.join(ROOT, value.lstrip("/"))
        if not os.path.isfile(full):
            add(f"Không tìm thấy tệp ảnh “{value}”. Tải lại ảnh trong CMS.")
        elif os.path.getsize(full) > MAX_IMAGE_BYTES:
            add(f"Ảnh “{value}” nặng {os.path.getsize(full) / 1048576:.1f} MB, tối đa 5 MB. Nén ảnh rồi tải lại.")
        return value
    if w == "list":
        if not isinstance(value, list):
            add("Phải là danh sách.")
            return []
        if field.get("min") and len(value) < field["min"]:
            add(f"Cần ít nhất {field['min']} mục (đang có {len(value)}).")
        if field.get("max") and len(value) > field["max"]:
            add(f"Tối đa {field['max']} mục (đang có {len(value)}).")
        out = []
        singular = field.get("label_singular") or "mục"
        for i, item in enumerate(value, 1):
            if "types" in field:
                tkey = field.get("typeKey", "type")
                tname = (item or {}).get(tkey)
                t = next((t for t in field["types"] if t["name"] == tname), None)
                if not t:
                    LOI.them(src, " › ".join(path + [f"{singular.capitalize()} {i}"]), f"Loại “{tname}” không tồn tại.")
                    continue
                sub = {"widget": "object", "fields": t.get("fields", []), "_rules": t.get("_rules", [])}
                norm = validate(item, sub, src, path + [f"{singular.capitalize()} {i} ({t['label'].split('·')[-1].strip()})"], ctx)
                norm[tkey] = tname
                out.append(norm)
            elif "fields" in field:
                sub = {"widget": "object", "fields": field["fields"], "_rules": field.get("_item_rules", [])}
                out.append(validate(item, sub, src, path + [f"{singular.capitalize()} {i}"], ctx))
            else:
                out.append(validate(item, field["field"], src, path + [f"{singular.capitalize()} {i}"], ctx))
        for rule in field.get("_rules", []):
            rule(out, add)
        return out
    if w == "object":
        if not isinstance(value, dict):
            add("Dữ liệu không đúng dạng nhóm trường.")
            value = {}
        out = {}
        for sub in field.get("fields", []):
            out[sub["name"]] = validate(value.get(sub["name"], MISSING), sub, src, path + [sub["label"]], ctx)
        for k, v in value.items():
            if k not in out:
                out[k] = v
        for rule in field.get("_rules", []):
            rule(out, add)
        return out
    return value


def validate_entry(data, fields, src, ctx, rules=()):
    return validate(data, {"widget": "object", "fields": fields, "_rules": list(rules)}, src, [], ctx)


# ---------------------------------------------------------------------------
# Sinh cấu hình CMS
# ---------------------------------------------------------------------------
def _clean(o, dynamic):
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if k.startswith("_"):
                continue
            out[k] = _clean(v, dynamic)
        if o.get("_options"):
            out["options"] = dynamic.get(o["_options"]) or [{"label": "(chưa có)", "value": ""}]
        return out
    if isinstance(o, list):
        return [_clean(x, dynamic) for x in o]
    return o


def cms_config(dynamic, env):
    """dynamic: {"pages": [...], "faq": [...]} – danh sách chọn sinh từ nội dung hiện có."""
    backend = {"name": "github", "repo": env["repo"], "branch": env["branch"],
               "commit_messages": {
                   "create": "Tạo {{collection}} “{{slug}}”",
                   "update": "Cập nhật {{collection}} “{{slug}}”",
                   "delete": "Xóa {{collection}} “{{slug}}”",
                   "uploadMedia": "Tải lên “{{path}}”",
                   "deleteMedia": "Xóa tệp “{{path}}”"}}
    if env.get("oauth_url"):
        backend["base_url"] = env["oauth_url"]
    else:
        backend["auth_methods"] = ["token"]
    if env.get("test_backend"):
        backend = {"name": "test-repo"}
    cfg = {
        "app_title": "Quản trị website Luật Sư Nam",
        "backend": backend,
        "site_url": env["site_url"] + "/",
        "logo": {"src": env["base_path"] + "assets/img/logo-lsn.webp"},
        "media_folder": "assets/uploads",
        "public_folder": "/assets/uploads",
        "media_libraries": {"default": {"config": {
            "max_file_size": MAX_IMAGE_BYTES, "slugify_filename": True,
            "transformations": {"raster_image": {"format": "webp", "quality": 82, "width": 2400, "height": 2400}}}}},
        "slug": {"encoding": "ascii", "clean_accents": True, "sanitize_replacement": "-", "maxlength": 60},
        "output": {"omit_empty_optional_fields": True, "yaml": {"indent_size": 2, "indent_sequences": True}},
        "collections": _clean(collections(), dynamic),
    }
    return cfg
