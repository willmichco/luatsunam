# -*- coding: utf-8 -*-
"""Sinh toàn bộ hình ảnh lúc build (thay cho tools/make_images.py cũ).

Nguồn (sửa trong CMS → Cài đặt chung → Ảnh thương hiệu):
    content/anh-thuong-hieu/logo-lsn.webp   Logo, nền trong suốt
    content/anh-thuong-hieu/van-phong.webp  Luật sư tại văn phòng
    content/anh-thuong-hieu/phien-toa.webp  Luật sư tại phiên tòa (ảnh thẻ và ảnh tròn cắt theo "Vị trí khuôn mặt")

Kết quả trong dist/assets/img/:
    logo-lsn[-108].webp, favicon-32.png, icon-192.png, icon-512.png, apple-touch-icon.png
    luat-su-van-phong[-480|-640].avif/.webp, luat-su-phien-toa[-480|-640].avif/.webp
    luat-su-chan-dung.avif/.webp (thẻ "Luật sư phụ trách"), luat-su-avatar.webp (ảnh tròn)
    og-image.jpg, og/<loại>-<đường-dẫn>.jpg  Ảnh chia sẻ 1200×630 tự tạo từ tiêu đề
Ảnh tải lên (assets/uploads/) được chép kèm các bản thu nhỏ -480/-960/-1600.webp.

Mọi ảnh được lưu đệm trong .cache/ theo mã băm của nguồn: build sau chỉ sinh lại ảnh có thay đổi.
"""
import hashlib
import io
import json
import os
import shutil
import unicodedata

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache", "img")
VERSION = "2"  # tăng khi đổi thuật toán xử lý ảnh để bỏ ảnh lưu đệm cũ

# Bảng màu chung với assets/css/style.css
CREAM, PAPER, RED, INK, TEXT, GOLD = (248, 242, 232), (255, 253, 249), (181, 0, 11), (43, 29, 33), (84, 74, 77), (180, 135, 74)
PHOTO_WIDTHS = (480, 640, None)   # khớp srcset trong build
UPLOAD_WIDTHS = (480, 960, 1600)
# Lĩnh vực gắn với tố tụng dùng ảnh tại phiên tòa cho ảnh chia sẻ, còn lại dùng ảnh văn phòng
COURT = {"hinh-su", "tranh-tung-giai-quyet-tranh-chap", "dan-su", "hon-nhan-gia-dinh"}


def _hash(*parts):
    h = hashlib.sha1(VERSION.encode())
    with open(__file__, "rb") as fh:
        h.update(fh.read())
    for p in parts:
        if isinstance(p, str) and os.path.isfile(p):
            with open(p, "rb") as fh:
                h.update(fh.read())
        else:
            h.update(json.dumps(p, ensure_ascii=False, sort_keys=True).encode())
    return h.hexdigest()[:16]


def _src(path):
    return os.path.join(ROOT, path.lstrip("/"))


# ---------------------------------------------------------------------------
# Xử lý ảnh
# ---------------------------------------------------------------------------
def photo(path):
    """Ảnh điện thoại: cân sáng nhẹ, ấm hơn một chút, làm nét vừa phải. Giữ vẻ tự nhiên."""
    im = Image.open(path).convert("RGB")
    im = ImageOps.autocontrast(im, cutoff=0.4, preserve_tone=True)
    r, g, b = im.split()
    im = Image.merge("RGB", (r.point(lambda v: min(255, v * 1.012)), g, b.point(lambda v: v * 0.985)))
    im = ImageEnhance.Color(im).enhance(1.04)
    return im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=3))


def save_webp(im, path, width=None, quality=82):
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(path, "WEBP", quality=quality, method=6)


def save_avif(im, path, width=None, quality=48):  # 48: nhẹ hơn 56 khoảng 25%, nhìn không khác (ảnh LCP trang chủ 68 → 51 KB)
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(path, "AVIF", quality=quality, speed=4)


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


def _clamp(box, w, h):
    x0, y0, x1, y1 = box
    dx = -x0 if x0 < 0 else (w - x1 if x1 > w else 0)
    dy = -y0 if y0 < 0 else (h - y1 if y1 > h else 0)
    return tuple(round(v) for v in (x0 + dx, y0 + dy, x1 + dx, y1 + dy))


def court_boxes(w, h, fx, fy):
    """Vùng cắt ảnh thẻ (4:3) và ảnh tròn (vuông) quanh khuôn mặt; mặc định (50, 30) khớp ảnh gốc."""
    cx, cy = (fx / 100 - 0.0025) * w, (fy / 100 + 0.0017241) * h
    half = 0.1625 * w
    avatar = _clamp((cx - half, cy - half, cx + half, cy + half), w, h)
    cw, ch = 0.35 * w, 0.2625 * w
    ccy = cy + 0.10222 * h
    card = _clamp((cx - cw, ccy - ch, cx + cw, ccy + ch), w, h)
    return card, avatar


def og_box(name, w, h):
    if name == "van-phong":
        return (round(40 / 784 * w), 0, round(600 / 784 * w), h)
    return (round(60 / 800 * w), round(20 / 812 * h), round(740 / 800 * w), h)


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


def og_card(logo, pic, box, eyebrow, title, text, firm, path):
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
    d.text((x0 + 80, 58), firm["short_name"].upper(), font=font(700, 27), fill=INK)
    d.text((x0 + 80, 94), firm["legal_name"].upper(), font=font(500, 13), fill=TEXT)

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

    label, pf = f'Gọi / Zalo {firm["phone"]}', font(600, 22)
    lw = d.textlength(label, font=pf)
    d.rounded_rectangle((x0, H - 108, x0 + lw + 44, H - 56), radius=8, fill=RED)
    d.text((x0 + 22, H - 96), label, font=pf, fill=(255, 255, 255))
    d.text((x0 + lw + 64, H - 96), f'{firm["street"]}, {firm["city_short"]}', font=font(500, 19), fill=TEXT)
    img.save(path, quality=86, optimize=True, progressive=True)


# ---------------------------------------------------------------------------
# Bước build
# ---------------------------------------------------------------------------
class Images:
    def __init__(self, site, out):
        self.site, self.out = site, out
        self.img_dir = os.path.join(out, "assets", "img")
        os.makedirs(os.path.join(self.img_dir, "og"), exist_ok=True)
        b = site.brand
        self.src = {"logo": _src(b.get("logo") or ""), "van-phong": _src(b.get("van_phong") or ""),
                    "phien-toa": _src(b.get("phien_toa") or "")}
        face = b.get("khuon_mat") or {}
        self.face = (face.get("x") if face.get("x") is not None else 50, face.get("y") if face.get("y") is not None else 30)
        self.sizes = {}
        self._loaded = None
        self.og_jobs = []

    def _cached(self, key, build):
        """Sinh vào .cache/img/<key>/ (nếu chưa có) rồi chép sang dist."""
        d = os.path.join(CACHE, key)
        if not os.path.isdir(d):
            tmp = d + ".tmp"
            shutil.rmtree(tmp, ignore_errors=True)
            os.makedirs(tmp)
            build(tmp)
            os.replace(tmp, d)
        for name in os.listdir(d):
            src = os.path.join(d, name)
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(self.img_dir, name), dirs_exist_ok=True)
            else:
                shutil.copy2(src, os.path.join(self.img_dir, name))
        return d

    def _load(self):
        if self._loaded is None:
            logo = square(Image.open(self.src["logo"]).convert("RGBA"))
            self._loaded = {"logo": logo, "van-phong": photo(self.src["van-phong"]), "phien-toa": photo(self.src["phien-toa"])}
        return self._loaded

    def brand(self):
        key = "brand-v2-" + _hash(self.src["logo"], self.src["van-phong"], self.src["phien-toa"], list(self.face))

        def build(d):
            im = self._load()
            logo = im["logo"]
            fit(logo, 160).save(os.path.join(d, "logo-lsn.webp"), "WEBP", quality=90, method=6)
            fit(logo, 108).save(os.path.join(d, "logo-lsn-108.webp"), "WEBP", quality=90, method=6)
            # Biểu tượng trình duyệt tải ở mọi trang: bảng 256 màu (favicon 2,9 → 1,8 KB; apple-touch-icon 30 → 14 KB,
            # nhìn không khác). icon-192/512 (logo cho Google, cài lên màn hình) giữ đủ màu: giảm màu làm loang dải chuyển màu
            fit(logo, 32).quantize(256, method=Image.Quantize.FASTOCTREE).save(os.path.join(d, "favicon-32.png"), optimize=True)
            fit(logo, 192, .04).save(os.path.join(d, "icon-192.png"), optimize=True)
            fit(logo, 512, .04).save(os.path.join(d, "icon-512.png"), optimize=True)
            fit(logo, 180, .08, (255, 255, 255, 255)).convert("RGB").quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) \
                .save(os.path.join(d, "apple-touch-icon.png"), optimize=True)
            for name in ("van-phong", "phien-toa"):
                for w in PHOTO_WIDTHS:
                    suffix = f"-{w}" if w else ""
                    save_webp(im[name], os.path.join(d, f"luat-su-{name}{suffix}.webp"), w, quality=78)
                    save_avif(im[name], os.path.join(d, f"luat-su-{name}{suffix}.avif"), w)
            court = im["phien-toa"]
            card, avatar = court_boxes(court.width, court.height, *self.face)
            c = court.crop(card)
            save_webp(c, os.path.join(d, "luat-su-chan-dung.webp"), quality=80)
            save_avif(c, os.path.join(d, "luat-su-chan-dung.avif"))
            save_webp(court.crop(avatar), os.path.join(d, "luat-su-avatar.webp"), quality=84)
            json.dump({"van-phong": im["van-phong"].size, "phien-toa": court.size,
                       "chan-dung": c.size}, open(os.path.join(d, "sizes.json"), "w"))
        d = self._cached(key, build)
        os.remove(os.path.join(self.img_dir, "sizes.json"))
        self.sizes = {k: tuple(v) for k, v in json.load(open(os.path.join(d, "sizes.json"))).items()}
        return self.sizes

    def og(self, rel, eyebrow, title, text, photo_name="van-phong"):
        """Đăng ký một ảnh chia sẻ; trả về đường dẫn tương đối dùng trong thẻ og:image."""
        self.og_jobs.append((rel, eyebrow, title, text, photo_name))
        return f"assets/img/{rel}"

    def og_from_file(self, rel, src):
        """Ảnh chia sẻ mặc định tải riêng: cắt vừa 1200×630, lưu JPEG."""
        im = ImageOps.fit(Image.open(_src(src)).convert("RGB"), (1200, 630), Image.LANCZOS)
        im.save(os.path.join(self.img_dir, rel), quality=86, optimize=True, progressive=True)

    def run_og(self):
        firm = self.site.firm
        fonts = [os.path.join(ROOT, "assets", "fonts", f"be-vietnam-pro-{w}-normal-{s}.woff2")
                 for w in (400, 500, 600, 700) for s in ("latin", "vietnamese")]
        base = [self.src["logo"], self.src["van-phong"], self.src["phien-toa"], *fonts,
                {k: firm[k] for k in ("short_name", "legal_name", "phone", "street", "city_short")}]
        for rel, eyebrow, title, text, name in self.og_jobs:
            key = "og-" + _hash(*base, [rel, eyebrow, title, text, name])
            d = os.path.join(CACHE, key)
            target = os.path.join(self.img_dir, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            if not os.path.isfile(os.path.join(d, "og.jpg")):
                os.makedirs(d, exist_ok=True)
                im = self._load()
                pic = im[name]
                og_card(im["logo"], pic, og_box(name, pic.width, pic.height), eyebrow, title, text, firm, os.path.join(d, "og.jpg"))
            shutil.copy2(os.path.join(d, "og.jpg"), target)

    def uploads(self):
        """Chép ảnh tải lên + sinh bản thu nhỏ WebP cho srcset. Trả về {đường dẫn: (rộng, cao, [bề ngang bản thu nhỏ])}."""
        src_dir = os.path.join(ROOT, "assets", "uploads")
        dst_dir = os.path.join(self.out, "assets", "uploads")
        os.makedirs(dst_dir, exist_ok=True)
        info = {}
        for name in sorted(os.listdir(src_dir)) if os.path.isdir(src_dir) else []:
            src = os.path.join(src_dir, name)
            if name.startswith(".") or not os.path.isfile(src):
                continue
            shutil.copy2(src, os.path.join(dst_dir, name))
            stem, ext = os.path.splitext(name)
            if ext.lower() not in (".webp", ".jpg", ".jpeg", ".png", ".avif"):
                continue
            key = "up-" + _hash(src)
            d = os.path.join(CACHE, key)
            if not os.path.isfile(os.path.join(d, "meta.json")):
                os.makedirs(d, exist_ok=True)
                im = Image.open(src)
                im = ImageOps.exif_transpose(im)
                im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
                widths = [w for w in UPLOAD_WIDTHS if w < im.width]
                for w in widths:
                    save_webp(im, os.path.join(d, f"{w}.webp"), w, quality=80)
                json.dump({"size": im.size, "widths": widths}, open(os.path.join(d, "meta.json"), "w"))
            meta = json.load(open(os.path.join(d, "meta.json")))
            for w in meta["widths"]:
                shutil.copy2(os.path.join(d, f"{w}.webp"), os.path.join(dst_dir, f"{stem}-{w}.webp"))
            info["/assets/uploads/" + name] = (meta["size"][0], meta["size"][1], meta["widths"])
        return info
