# -*- coding: utf-8 -*-
"""Sinh toàn bộ hình ảnh của website từ logo và ảnh thật của luật sư.

    pip install pillow fonttools brotli
    python3 tools/make_images.py

Nguồn (thư mục src/, không xuất bản):
    src/brand/logo-lsn.webp           Logo gốc, nền trong suốt
    src/brand/anh-that/van-phong.webp Luật sư Nguyễn Trọng Nam tại bàn làm việc ở văn phòng
    src/brand/anh-that/phien-toa.webp Luật sư Nguyễn Trọng Nam tại ghế người bào chữa

Website chỉ dùng ảnh thật. Khi có ảnh mới (độ phân giải cao hơn, ảnh văn phòng, ảnh làm việc
với khách hàng đã được đồng ý), thay tệp trong src/brand/anh-that/ cùng tên rồi chạy lại script;
nếu bố cục ảnh khác, chỉnh toạ độ cắt trong PHOTOS.

Kết quả trong assets/img/:
    logo-lsn.webp, favicon-32.png, icon-192.png, icon-512.png, apple-touch-icon.png
    luat-su-van-phong[-480].webp      Ảnh văn phòng (trang chủ, giới thiệu)
    luat-su-phien-toa[-480].webp      Ảnh tại phiên tòa (trang chủ, giới thiệu)
    luat-su-chan-dung.webp            Ảnh cắt 4:3 cho thẻ "Luật sư phụ trách" ở đầu các trang
    luat-su-avatar.webp               Ảnh tròn nhỏ cho khối liên hệ
    og-image.jpg                      Ảnh chia sẻ mặc định 1200×630
    og/dich-vu-<slug>.jpg             Ảnh chia sẻ riêng cho 8 trang dịch vụ
    og/bai-viet-<slug>.jpg            Ảnh chia sẻ riêng cho từng bài viết
"""
import io
import os
import sys
import unicodedata

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import ARTICLES, FIRM, SERVICES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAND = os.path.join(ROOT, "src", "brand")
OUT = os.path.join(ROOT, "assets", "img")

# Bảng màu chung với assets/css/style.css
CREAM, PAPER, RED, INK, TEXT, GOLD = (248, 242, 232), (255, 253, 249), (181, 0, 11), (43, 29, 33), (84, 74, 77), (180, 135, 74)

# Toạ độ cắt (x0, y0, x1, y1) trên ảnh gốc
PHOTOS = {
    "van-phong": {"file": "van-phong.webp", "og": (40, 0, 600, 651)},
    "phien-toa": {"file": "phien-toa.webp", "og": (60, 20, 740, 812), "card": (118, 118, 678, 538), "avatar": (268, 115, 528, 375)},
}
# Dịch vụ gắn với tố tụng dùng ảnh tại phiên tòa, còn lại dùng ảnh văn phòng
COURT = {"hinh-su", "tranh-tung-giai-quyet-tranh-chap", "dan-su", "hon-nhan-gia-dinh", "lao-dong-viec-lam"}


def photo(name):
    """Ảnh điện thoại: cân sáng nhẹ, ấm hơn một chút, làm nét vừa phải. Giữ vẻ tự nhiên."""
    im = Image.open(os.path.join(BRAND, "anh-that", PHOTOS[name]["file"])).convert("RGB")
    im = ImageOps.autocontrast(im, cutoff=0.4, preserve_tone=True)
    r, g, b = im.split()
    im = Image.merge("RGB", (r.point(lambda v: min(255, v * 1.012)), g, b.point(lambda v: v * 0.985)))
    im = ImageEnhance.Color(im).enhance(1.04)
    return im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=3))


def save_webp(im, rel, width=None, quality=82):
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(os.path.join(OUT, rel), "WEBP", quality=quality, method=6)


def square(im):
    im = im.crop(im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox())
    side = max(im.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
    return sq


def fit(logo, size, pad=0.0, bg=(0, 0, 0, 0)):
    inner = round(size * (1 - 2 * pad))
    canvas = Image.new("RGBA", (size, size), bg)
    mark = logo.resize((inner, inner), Image.LANCZOS)
    off = (size - inner) // 2
    canvas.paste(mark, (off, off), mark)
    return canvas


_FONTS = {}


def font(weight, size):
    """Be Vietnam Pro tự lưu trữ (woff2, tách latin/vietnamese) gộp lại thành một phông cho Pillow."""
    if weight not in _FONTS:
        from fontTools.merge import Merger
        from fontTools.ttLib import TTFont
        bufs = []
        for sub in ("latin", "vietnamese"):
            f = TTFont(os.path.join(ROOT, "assets", "fonts", f"be-vietnam-pro-{weight}-normal-{sub}.woff2"))
            f.flavor = None
            b = io.BytesIO()
            f.save(b)
            b.seek(0)
            bufs.append(b)
        out = io.BytesIO()
        Merger().merge(bufs).save(out)
        _FONTS[weight] = out.getvalue()
    return ImageFont.truetype(io.BytesIO(_FONTS[weight]), size)


def wrap(d, s, f, width, max_lines):
    words, lines, cur = unicodedata.normalize("NFC", s).split(), [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if d.textlength(test, font=f) <= width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while d.textlength(lines[-1] + "…", font=f) > width:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        lines[-1] += "…"
    return lines


def og_card(logo, pic, box, eyebrow, title, text, rel):
    """Ảnh chia sẻ 1200×630: nội dung bên trái trên nền kem, ảnh thật của luật sư bên phải."""
    W, H, PW = 1200, 630, 470
    img = Image.new("RGB", (W, H), CREAM)
    side = pic.crop(box)
    side = ImageOps.fit(side, (PW, H), Image.LANCZOS, centering=(0.5, 0.35))
    img.paste(side, (W - PW, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((W - PW - 6, 0, W - PW - 1, H), fill=GOLD)
    x0, maxw = 64, W - PW - 64 - 56

    mark = logo.resize((64, 64), Image.LANCZOS)
    img.paste(mark, (x0, 52), mark)
    d.text((x0 + 80, 58), "LUẬT SƯ NAM", font=font(700, 27), fill=INK)
    d.text((x0 + 80, 94), FIRM["legal_name"].upper(), font=font(500, 13), fill=TEXT)

    y = 176
    d.text((x0, y), unicodedata.normalize("NFC", eyebrow.upper()), font=font(600, 17), fill=GOLD)
    y += 38
    tf = font(700, 46 if len(title) < 44 else 40)
    for line in wrap(d, title, tf, maxw, 3):
        d.text((x0, y), line, font=tf, fill=RED)
        y += tf.size + 12
    y += 6
    bf = font(400, 21)
    for line in wrap(d, text, bf, maxw, 3 if y < 380 else 2):
        d.text((x0, y), line, font=bf, fill=TEXT)
        y += 32

    label, pf = f'Gọi / Zalo {FIRM["phone"]}', font(600, 22)
    lw = d.textlength(label, font=pf)
    d.rounded_rectangle((x0, H - 108, x0 + lw + 44, H - 56), radius=8, fill=RED)
    d.text((x0 + 22, H - 96), label, font=pf, fill=(255, 255, 255))
    d.text((x0 + lw + 64, H - 96), f'{FIRM["street"]}, TP.HCM', font=font(500, 19), fill=TEXT)
    os.makedirs(os.path.dirname(os.path.join(OUT, rel)), exist_ok=True)
    img.save(os.path.join(OUT, rel), quality=86, optimize=True, progressive=True)


def main():
    logo = square(Image.open(os.path.join(BRAND, "logo-lsn.webp")).convert("RGBA"))
    fit(logo, 160).save(os.path.join(OUT, "logo-lsn.webp"), "WEBP", quality=90, method=6)
    fit(logo, 32).save(os.path.join(OUT, "favicon-32.png"), optimize=True)
    fit(logo, 192, .04).save(os.path.join(OUT, "icon-192.png"), optimize=True)
    fit(logo, 512, .04).save(os.path.join(OUT, "icon-512.png"), optimize=True)
    fit(logo, 180, .08, (255, 255, 255, 255)).convert("RGB").save(os.path.join(OUT, "apple-touch-icon.png"), optimize=True)

    office, court = photo("van-phong"), photo("phien-toa")
    save_webp(office, "luat-su-van-phong.webp")
    save_webp(office, "luat-su-van-phong-480.webp", 480)
    save_webp(court, "luat-su-phien-toa.webp")
    save_webp(court, "luat-su-phien-toa-480.webp", 480)
    save_webp(court.crop(PHOTOS["phien-toa"]["card"]), "luat-su-chan-dung.webp")
    save_webp(court.crop(PHOTOS["phien-toa"]["avatar"]).resize((200, 200), Image.LANCZOS), "luat-su-avatar.webp", quality=86)

    og_card(logo, court, PHOTOS["phien-toa"]["og"], "Luật sư tư vấn & tranh tụng tại TP.HCM",
            "Gặp chuyện pháp lý, có luật sư bên cạnh",
            "Luật sư Nguyễn Trọng Nam trực tiếp lắng nghe, nói rõ quyền lợi, rủi ro và cùng anh chị chọn cách giải quyết.",
            "og-image.jpg")
    for s in SERVICES:
        pic, key = (court, "phien-toa") if s["slug"] in COURT else (office, "van-phong")
        og_card(logo, pic, PHOTOS[key]["og"], "Dịch vụ pháp lý", s["name"], s["short"], f'og/dich-vu-{s["slug"]}.jpg')
    for a in ARTICLES:
        og_card(logo, office, PHOTOS["van-phong"]["og"], a["category"], a["card_title"], a["excerpt"], f'og/bai-viet-{a["slug"]}.jpg')
    print("Đã sinh logo, biểu tượng, ảnh luật sư và ảnh chia sẻ trong assets/img/.")


if __name__ == "__main__":
    main()
