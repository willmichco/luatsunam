# -*- coding: utf-8 -*-
"""Kiểm G5 sau khi chuyển sang tên miền riêng – tiêu chí 7 và 8 của kế hoạch (chạy trong GitHub Actions: "Kiểm chuyển tên miền (G5)").

    python3 tools/kiem_g5.py https://tenmien.vn            # kiểm site thật
    python3 tools/kiem_g5.py --ghi-moc dist                 # ghi lại mốc URL github.io (docs/g5/url-github-io.txt)

1. Mọi URL công khai trên github.io (mốc trong docs/g5/url-github-io.txt + danh sách mà bản chuyển hướng đang đăng):
   URL cũ trả trang chuyển hướng tức thì (meta refresh 0) + canonical tới tên miền, và URL đích trên tên miền
   trả 200 (qua tối đa 1 chuyển hướng 301 của đường dẫn cũ đã đổi) – tiêu chí 8: 100% đường dẫn giữ nguyên.
2. sitemap.xml trên tên miền: mọi URL thuộc tên miền, trả 200, canonical + og:url trỏ đúng chính nó; robots.txt trỏ
   sitemap mới – tiêu chí 7.
3. Thông tin thêm, không tính đạt/không đạt: www → tên miền gốc, http → https, /admin/ và /nhap/ đã khóa (Cloudflare Access).
Kết quả in dạng Markdown (hiện ngay trên trang kết quả của GitHub Actions); có lỗi thì thoát mã 1.
"""
import html
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD_SITE = "https://willmichco.github.io/luatsunam"
MOC = os.path.join(ROOT, "docs", "g5", "url-github-io.txt")
UA = "Mozilla/5.0 (kiem_g5; +https://github.com/willmichco/luatsunam)"
# Chỉ dùng khi thử trên máy: --doi-host https://tenmien.vn=http://127.0.0.1:8132 (gửi yêu cầu tới máy chủ giả lập)
HOST_MAP = []


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def _real(url):
    for a, b in HOST_MAP:
        if url.startswith(a):
            return b + url[len(a):]
    return url


def _virtual(url):
    for a, b in HOST_MAP:
        if url.startswith(b):
            return a + url[len(b):]
    return url


def get(url):
    """Một yêu cầu, không tự đi theo chuyển hướng: (mã, Location tuyệt đối, nội dung)."""
    req = urllib.request.Request(_real(url), headers={"User-Agent": UA})
    try:
        with OPENER.open(req, timeout=20) as r:
            return r.status, None, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        loc = e.headers.get("Location")
        body = e.read().decode("utf-8", "replace") if e.code >= 400 else ""
        return e.code, urllib.parse.urljoin(url, _virtual(loc)) if loc else None, body
    except Exception as e:  # tên miền chưa trỏ, chứng chỉ chưa cấp…
        return 0, None, f"{type(e).__name__}: {e}"


def follow(url, limit=5):
    """Đi theo chuyển hướng HTTP: (mã cuối, URL cuối, số lần chuyển, nội dung)."""
    hops = 0
    while True:
        code, loc, body = get(url)
        if code in (301, 302, 303, 307, 308) and loc and hops < limit:
            url, hops = loc, hops + 1
            continue
        return code, url, hops, body


def meta(body, name):
    if name == "canonical":
        m = re.search(r'<link rel="canonical" href="([^"]*)"', body)
    elif name == "refresh":
        m = re.search(r'<meta http-equiv="refresh" content="0; url=([^"]*)"', body)
    else:
        m = re.search(rf'<meta property="{re.escape(name)}" content="([^"]*)"', body)
    return html.unescape(m.group(1)) if m else None


def no_frag(u):
    return (u or "").split("#")[0]


def read_moc():
    if not os.path.isfile(MOC):
        return []
    return [l.strip() for l in open(MOC, encoding="utf-8") if l.startswith("http")]


def write_moc(dist):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import chuyen_huong
    urls = [f"{OLD_SITE}/{p}" for p, _ in chuyen_huong.old_paths(dist) if not p.startswith("admin/")]
    os.makedirs(os.path.dirname(MOC), exist_ok=True)
    with open(MOC, "w", encoding="utf-8") as fh:
        fh.write("# Mốc G5: mọi URL công khai trên github.io trước khi chuyển tên miền (sinh bằng tools/kiem_g5.py --ghi-moc dist).\n"
                 "# Sau khi chuyển, từng URL này phải chuyển hướng tới đúng trang trên tên miền mới.\n")
        fh.writelines(u + "\n" for u in urls)
    print(f"Đã ghi {len(urls)} URL vào {os.path.relpath(MOC, ROOT)}")


def check(new_site, old_site=OLD_SITE):
    new_site, old_site = new_site.strip().rstrip("/"), old_site.rstrip("/")
    loi, ghi_chu, rows, moved = [], [], [], set()

    # --- 1. URL cũ → tên miền (tiêu chí 8)
    old_urls = list(dict.fromkeys(read_moc()))
    code, _, body = get(old_site + "/danh-sach-url.txt")
    live = [l.split()[0] for l in body.splitlines() if l.startswith("http")] if code == 200 else []
    if not live:
        loi.append(f"Chưa thấy bản chuyển hướng trên {old_site}/ (danh-sach-url.txt trả mã {code}). "
                   "Kiểm biến repo CHUYEN_HUONG_TOI và lượt chạy “Build và đăng website”; GitHub Pages có thể giữ bản cũ tới 10 phút.")
    old_urls += [u for u in live if u not in old_urls and "/admin/" not in u + "/"]
    ok8 = 0
    for old in old_urls:
        code, _, body = get(old)
        target = meta(body, "refresh") if code == 200 else None
        canon = meta(body, "canonical") if code == 200 else None
        path = old[len(old_site):] if old.startswith(old_site) else None
        if not target or not target.startswith(new_site + "/"):
            loi.append(f"{old}: chưa chuyển hướng tới {new_site} (mã {code}, đích “{target}”)")
            continue
        if no_frag(canon) != no_frag(target):
            loi.append(f"{old}: canonical “{canon}” khác đích chuyển hướng “{target}”")
            continue
        fcode, final, hops, fbody = follow(no_frag(target))
        if fcode != 200:
            loi.append(f"{old} → {target}: tên miền trả mã {fcode} ({fbody[:80] if fcode == 0 else final})")
            continue
        same = target[len(new_site):] == path
        if not same:  # đường dẫn cũ đã đổi (Cài đặt chung → Chuyển hướng): đích phải là trang thật, đi thẳng 1 bước
            moved.add(path)
            ghi_chu.append(f"{path} → {target[len(new_site):]} (đường dẫn cũ đã đổi trong Cài đặt chung → Chuyển hướng)")
        ok8 += 1
    rows.append(("8", "URL github.io cũ → đúng trang trên tên miền", f"{ok8}/{len(old_urls)}", ok8 == len(old_urls) and bool(old_urls)))

    # --- 2. sitemap, canonical, og:url trên tên miền (tiêu chí 7)
    code, _, sm = get(new_site + "/sitemap.xml")
    locs = re.findall(r"<loc>(.*?)</loc>", sm) if code == 200 else []
    if not locs:
        loi.append(f"{new_site}/sitemap.xml trả mã {code} hoặc rỗng ({sm[:80] if code == 0 else ''})")
    ok7 = 0
    for loc in locs:
        loc = html.unescape(loc)
        if not loc.startswith(new_site + "/"):
            loi.append(f"sitemap.xml: “{loc}” không thuộc {new_site}")
            continue
        code, _, body = get(loc)
        if code != 200:
            loi.append(f"{loc}: mã {code}")
            continue
        c, o = meta(body, "canonical"), meta(body, "og:url")
        if c != loc or o != loc:
            loi.append(f"{loc}: canonical “{c}”, og:url “{o}” phải đúng là URL của trang")
            continue
        ok7 += 1
    rows.append(("7", "Trang trong sitemap trả 200, canonical + og:url đúng tên miền", f"{ok7}/{len(locs)}", ok7 == len(locs) and bool(locs)))
    code, _, robots = get(new_site + "/robots.txt")
    robots_ok = code == 200 and f"Sitemap: {new_site}/sitemap.xml" in robots and "Disallow: /\n" not in robots + "\n"
    if not robots_ok:
        loi.append(f"{new_site}/robots.txt phải trỏ “Sitemap: {new_site}/sitemap.xml” và không chặn toàn site (mã {code})")
    rows.append(("7", "robots.txt trỏ sitemap mới, không chặn site", "đạt" if robots_ok else "chưa", robots_ok))
    old_paths = {u[len(old_site):] for u in old_urls if u.startswith(old_site)}
    new_paths = {html.unescape(l)[len(new_site):] for l in locs if html.unescape(l).startswith(new_site)}
    # đường dẫn cũ đã đổi (Cài đặt chung → Chuyển hướng) không nằm trong sitemap mới là đúng – đã kiểm ở mục 1
    missing = sorted(old_paths - new_paths - moved)
    if missing:
        loi.append("Trang có trên github.io nhưng không có trong sitemap tên miền: " + ", ".join(missing[:10]))
    rows.append(("8", "Đường dẫn giữ nguyên (sitemap cũ ⊂ sitemap mới)", f"thiếu {len(missing)}", not missing))

    # --- 3. Thông tin thêm
    host = urllib.parse.urlsplit(new_site).netloc
    extra = []
    code, loc, body = get(f"https://www.{host}/")
    extra.append(("www → tên miền gốc", code in (301, 308) and (loc or "").rstrip("/") == new_site,
                  f"mã {code} → {loc}" if code else f"chưa truy cập được ({body[:60]})"))
    code, loc, body = get(f"http://{host}/")
    extra.append(("http → https", code in (301, 308) and (loc or "").startswith("https://"),
                  f"mã {code} → {loc}" if code else f"chưa truy cập được ({body[:60]})"))
    for p in ("/admin/", "/nhap/"):
        code, loc, body = get(new_site + p)
        locked = code in (401, 403) or (code in (302, 303) and "cloudflareaccess.com" in (loc or ""))
        why = ("đã khóa" if locked else "CHƯA khóa – ai cũng mở được" if code == 200 else
               "chưa khóa (hiện chưa có trang)" if code == 404 else f"chưa rõ, mã {code}" + (f" → {loc}" if loc else ""))
        extra.append((f"{p} khóa bằng Cloudflare Access", locked, why))

    # --- In kết quả
    dat = not loi
    print(f"## Kiểm chuyển tên miền (G5): {'ĐẠT' if dat else 'CHƯA ĐẠT'}\n")
    print(f"Địa chỉ cũ: {old_site}/ → tên miền: {new_site}/\n")
    print("| Tiêu chí | Kiểm | Kết quả | |\n|---|---|---|---|")
    for tc, ten, kq, ok in rows:
        print(f"| {tc} | {ten} | {kq} | {'✓' if ok else '✗'} |")
    print("\n**Thông tin thêm** (không tính đạt/không đạt):\n")
    for ten, ok, chi_tiet in extra:
        print(f"- {'✓' if ok else '!'} {ten}: {chi_tiet}")
    if ghi_chu:
        print("\nĐường dẫn cũ đã đổi (đi thẳng tới trang mới):\n" + "".join(f"- {n}\n" for n in ghi_chu))
    if loi:
        print(f"\n### {len(loi)} lỗi\n")
        for e in loi[:40]:
            print(f"- {e}")
        if len(loi) > 40:
            print(f"- … và {len(loi) - 40} lỗi khác")
        print("\nVừa đổi xong thì chờ 10 phút (GitHub Pages, Cloudflare còn giữ bản cũ) rồi chạy lại.")
    return dat


def main():
    args = sys.argv[1:]
    while "--doi-host" in args:
        i = args.index("--doi-host")
        a, b = args[i + 1].split("=", 1)
        HOST_MAP.append((a.rstrip("/"), b.rstrip("/")))
        del args[i:i + 2]
    if args[:1] == ["--ghi-moc"]:
        return write_moc(os.path.join(ROOT, args[1] if len(args) > 1 else "dist"))
    old = OLD_SITE
    if "--cu" in args:
        i = args.index("--cu")
        old = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1 or not re.match(r"^https://[a-z0-9.-]+\.[a-z]{2,}/?$", args[0].strip()):
        sys.exit("Cách dùng: python3 tools/kiem_g5.py https://tenmien.vn")
    sys.exit(0 if check(args[0], old) else 1)


if __name__ == "__main__":
    main()
