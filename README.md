# LSN Law Firm – Công Ty Luật TNHH Luật Sư Nam

Website tĩnh nhiều trang (HTML, CSS, JavaScript thuần), dùng giao diện mới LSN Law Firm và nội dung chuyển từ website cũ [`willmichco/Website`](https://github.com/willmichco/Website).

- Xem trực tiếp: <https://willmichco.github.io/law_newsite/>
- Chỉ cần sửa nội dung trong `tools/data.py` và `src/`, sau đó chạy `python3 tools/build.py` để sinh lại toàn bộ trang.

## Sơ đồ website

| Đường dẫn | Trang | Dữ liệu có cấu trúc |
|---|---|---|
| `/` | Trang chủ | LegalService, WebSite |
| `/gioi-thieu/` | Giới thiệu, triết lý hành nghề, cam kết nghề nghiệp | AboutPage |
| `/doi-ngu-luat-su/` | Hồ sơ Luật sư Nam | ProfilePage, Person |
| `/vi-sao-chon-chung-toi/` | Bốn nguyên tắc làm việc | WebPage |
| `/quy-trinh-lam-viec/` | Quy trình 4 bước, hồ sơ cần chuẩn bị | WebPage |
| `/dich-vu/` | Tổng quan 8 lĩnh vực | CollectionPage, ItemList |
| `/dich-vu/<lĩnh-vực>/` | 8 trang dịch vụ: thừa kế, tranh tụng, hôn nhân gia đình, đất đai, lao động, hình sự, dân sự, công chứng. Mỗi trang: tình huống thường gặp, luật sư giúp gì, việc nên làm ngay, các bước, giấy tờ, hỏi đáp có dẫn điều luật | Service |
| `/kien-thuc-phap-ly/` | Danh mục bài viết và công cụ | CollectionPage, ItemList |
| `/kien-thuc-phap-ly/<bài-viết>/` | 3 bài viết pháp lý, mở đầu bằng khung “Tóm tắt nhanh” | Article |
| `/bo-luat-hinh-su/` | Từ điển Bộ luật Hình sự: cách tìm kiếm, các điều thường gặp theo chủ đề, cấu trúc Bộ luật | CollectionPage (about: Legislation) |
| `/bo-luat-hinh-su/chuong-<số>/` | 27 trang chương: danh sách điều kèm trích đoạn | CollectionPage |
| `/bo-luat-hinh-su/dieu-<số>/` | 428 trang điều luật: quy định, bình luận, điều liên quan, bản đồ tư duy | WebPage (about: Legislation) |
| `/cau-hoi-thuong-gap/` | 7 câu hỏi thường gặp | FAQPage |
| `/lien-he/` | Gọi điện, Zalo, email, việc gấp, văn phòng và bản đồ | ContactPage |
| `/chinh-sach-bao-mat/`, `/dieu-khoan-su-dung/`, `/mien-tru-trach-nhiem/` | Văn bản pháp lý của website | WebPage |

Mọi trang có: `title` và `description` riêng, `canonical`, Open Graph, Twitter Card, breadcrumb hiển thị kèm `BreadcrumbList`. Đường dẫn giữ nguyên như website cũ để không mất thứ hạng khi chuyển tên miền.

## Giao diện thống nhất

Toàn bộ website (trừ Từ điển Bộ luật Hình sự) dùng chung một hệ giao diện trong `assets/css/pages.css`, hướng tới người dân đang gặp chuyện cần luật sư:

- **Giọng văn:** gọi người đọc là “anh chị”, câu ngắn, tiêu đề viết như lời nói hằng ngày (“Anh chị đang gặp chuyện gì?”); khẳng định pháp lý luôn kèm điều luật.
- **Khung trang giống nhau:** đầu trang nền kem (đường dẫn, tiêu đề, đoạn mở đầu, thẻ “Anh chị cần hỏi ngay?” có ảnh luật sư) → các mục nội dung xen kẽ nền trắng/kem → khối liên hệ đỏ cuối trang (Gọi điện, Nhắn Zalo, Đến văn phòng).
- **Thành phần dùng chung** (tiền tố `ls-`), sinh bởi các hàm trong `tools/build.py` và gọi được từ `src/pages/*.html` bằng token:

| Token | Hiển thị |
|---|---|
| `{{call_buttons}}` | Nút Gọi điện + Nhắn Zalo |
| `{{help_card}}` | Thẻ “Anh chị cần hỏi ngay?” |
| `{{promise}}` | Dải 4 cam kết (luật sư trực tiếp, nói rõ được – mất, chi phí trước, giữ kín) |
| `{{problems_grid}}` | 8 thẻ “Anh chị đang gặp chuyện gì?” (thứ tự: `PROBLEM_ORDER` trong `tools/data.py`) |
| `{{field_links}}`, `{{field_links:ho-so}}` | 8 lĩnh vực dạng thẻ nhỏ (kèm neo tới mục giấy tờ) |
| `{{faq_list:id1,id2}}` | Câu hỏi thường gặp chọn lọc |
| `{{articles_grid}}` | Thẻ bài viết |
| `{{contact}}` | Khối liên hệ cuối trang |
| `{{breadcrumb}}` | Đường dẫn của trang |

**Khung bề ngang và màu dùng chung cho toàn site** (kể cả Từ điển Bộ luật Hình sự) nằm cuối `assets/css/navigation.css`: mọi khối nội dung, header, footer cùng khung 1280px; chữ cạnh logo trên menu là “Công Ty Luật TNHH / Luật Sư Nam”. Logo menu dùng `assets/img/logo-mark.webp` (10 KB), mục “Về chúng tôi” ở trang chủ dùng `assets/img/logo-emblem.webp` kèm tên công ty viết bằng chữ thật; cả hai được xuất từ `assets/img/logo-provided.png` (ảnh gốc 1254px, không nạp trực tiếp lên trang).

Trang Từ điển Bộ luật Hình sự giữ nguyên bộ giao diện riêng (`reader-design.css`, `bo-luat-hinh-su/tu-dien.css`); `pages.css` và các biểu tượng bổ sung không được nạp vào các trang này.

## Liên kết nội bộ

- Menu có menu xổ cho **Giới thiệu**, **Lĩnh vực hoạt động** (8 lĩnh vực) và **Kiến thức pháp lý**.
- Mỗi trang dịch vụ liên kết tới 3 lĩnh vực liên quan (khai báo ở trường `related` trong `tools/data.py`), bài viết liên quan, quy trình làm việc và câu hỏi thường gặp.
- Mỗi bài viết có mục lục, liên kết trong nội dung tới trang dịch vụ, khung “Cần luật sư về…”, danh sách lĩnh vực liên quan và bài viết khác.
- Footer liên kết tới toàn bộ trang chính và 8 lĩnh vực.
- Tìm kiếm trong website (biểu tượng kính lúp) dùng chỉ mục `assets/search-index.json` do script sinh ra.

## Cấu trúc thư mục

```
tools/data.py              Thông tin pháp nhân, 8 lĩnh vực, bài viết, câu hỏi thường gặp
tools/build.py             Sinh toàn bộ trang, sitemap.xml, robots.txt, site.webmanifest, chỉ mục tìm kiếm
tools/check_seo.py         Kiểm tra SEO sau khi build: tên miền canonical, liên kết hỏng, title, description, H1, alt ảnh, JSON-LD, sitemap
tools/lastmod.json         Ngày cập nhật thật của từng trang (do build.py ghi, phải commit cùng các trang)
tools/build_blhs.py        Chuyển tệp Word bình luận BLHS thành dữ liệu tra cứu
tools/make_images.py       Sinh logo, favicon, biểu tượng ứng dụng, banner trang chủ, ảnh 8 lĩnh vực, ảnh chia sẻ (og-image)
src/brand/logo-lsn.webp    Logo gốc (nền trong suốt)
src/brand/goc/             Ảnh gốc chưa xử lý của banner và 8 lĩnh vực
src/pages/*.html           Nội dung các trang đơn lẻ (khối <!--meta {...} --> ở đầu là tiêu đề, mô tả)
src/bai-viet/*.html        Nội dung bài viết
src/bo-luat-hinh-su.html   Nội dung trang tra cứu BLHS
assets/css/style.css       Giao diện nền (biến màu, phông chữ ở :root, header, footer)
assets/css/pages.css       Hệ giao diện chung của mọi trang trừ Từ điển Bộ luật Hình sự
assets/css/bundle-*.css    Tệp CSS gộp (build.py sinh từ các tệp CSS nguồn): mỗi trang chỉ tải một tệp CSS
assets/js/main.js          Menu, tìm kiếm, bản đồ, mục lục bài viết
assets/fonts/              Be Vietnam Pro, phông sans-serif duy nhất của website (tự lưu trữ, SIL OFL 1.1)
assets/img/                Ảnh
bo-luat-hinh-su/           Trình đọc và dữ liệu Bộ luật Hình sự
```

Các tệp `index.html`, `404.html`, `sitemap.xml`, `robots.txt`, `site.webmanifest`, `assets/search-index.json`, `assets/css/bundle-*.css`, `tools/lastmod.json` do `tools/build.py` sinh ra. **Không sửa trực tiếp các tệp này**, sửa nguồn rồi chạy lại script.

## Sửa nội dung thường gặp

| Muốn sửa | Sửa tại |
|---|---|
| Số điện thoại, email, địa chỉ, giờ làm việc | `FIRM` trong `tools/data.py` |
| Nội dung một lĩnh vực | Mục tương ứng trong `SERVICES` (`tools/data.py`); ý nghĩa từng trường ghi ở đầu danh sách. Câu trả lời trong `faq` phải dẫn điều luật cụ thể |
| Liên kết tới điều luật Bộ luật Hình sự | Trường `blhs` (danh sách số điều) trong `SERVICES`/`ARTICLES`. Trang dịch vụ, bài viết hiện danh sách điều; trang điều luật tự dẫn ngược về bài viết và lĩnh vực đó |
| Title, description hiển thị trên Google | `seo_title`, `description` trong `SERVICES`/`ARTICLES`; khối `<!--meta-->` của `src/pages/*.html`. Title tối đa 60 ký tự (đuôi "\| Luật Sư Nam" chỉ gắn khi còn chỗ, hàm `seo_title` trong `tools/build.py`), description tối đa 158 ký tự. Trang Bộ luật Hình sự sinh tự động: điều quy định tội danh nêu số khung và mức hình phạt cao nhất (`penalty_summary` trong `tools/blhs.py`) |
| Thêm bài viết | Thêm mục vào `ARTICLES` (kèm 3–4 ý `key_points` cho khung “Tóm tắt nhanh”), tạo `src/bai-viet/<slug>.html`, thêm ảnh `assets/img/bai-viet/<slug>.webp` (720×240) |
| Câu hỏi thường gặp | `FAQ` trong `tools/data.py` |
| Hồ sơ luật sư | `src/pages/doi-ngu-luat-su.html` (xem ghi chú cho người quản trị trong tệp) |
| Tên miền | `SITE_URL`, `BASE_PATH` đầu tệp `tools/data.py` |
| Logo, banner, ảnh lĩnh vực, ảnh chia sẻ | Thay `src/brand/logo-lsn.webp` hoặc ảnh gốc trong `src/brand/goc/`, chạy `pip install pillow numpy opencv-python-headless fonttools brotli && python3 tools/make_images.py`. Ảnh lĩnh vực được chỉnh chung một tông navy – vàng đồng; banner được gắn biển logo lên mảng tường đá (toạ độ trong hàm `clean_wall`, chỉ đúng với ảnh banner hiện tại) |
| Phông chữ | `--font-sans` (chữ thường), `--font-heading` (tiêu đề) ở `:root` trong `assets/css/style.css` |

```bash
python3 tools/build.py                 # sinh lại website
python3 tools/check_seo.py             # kiểm tra SEO (thêm -v để xem từng trang); phải không còn LỖI
python3 -m http.server 8000            # xem thử tại http://localhost:8000
```

**Ngày cập nhật (`lastmod` trong sitemap, `dateModified` trong schema):** build.py so dấu vân tay nội dung từng trang (tiêu đề, mô tả, thân trang) với `tools/lastmod.json`. Trang nào nội dung đổi thì lấy ngày build, trang không đổi giữ nguyên ngày cũ. Nhờ vậy Google tin tín hiệu `lastmod`. Bài viết dùng ngày `modified` khai báo trong `tools/data.py`.

Cập nhật dữ liệu Bộ luật Hình sự: `pip install python-docx && python3 tools/build_blhs.py "Binh-luan-BLHS.docx" && python3 tools/build.py`.

### Từ điển Bộ luật Hình sự

Dải tiêu đề và ô tìm kiếm nằm ngay dưới thanh menu, chia cột trùng bố cục 3 cột bên dưới: tên từ điển thẳng cột mục lục, ô tìm kiếm bắt đầu thẳng cột nội dung và kết thúc thẳng nút “Đặt lịch tư vấn”.

Trang tổng quan `/bo-luat-hinh-su/` đi theo 3 cách tra cứu: (1) tìm kiếm, kèm ví dụ bấm thử; (2) các điều thường gặp, xếp theo chủ đề và dẫn tới chương; (3) cấu trúc Bộ luật theo phần, chương. Danh sách điều thường gặp khai báo ở `topics` trong `Renderer.hub` (`tools/blhs.py`).

Mỗi điều luật có trang riêng `/bo-luat-hinh-su/dieu-<số>/`, bố cục 3 cột:

- **Trái:** mục lục Phần → Chương → Mục → Điều. Trên điện thoại, mục lục mở dạng ngăn kéo qua nút “Mục lục”.
- **Giữa:**
  - Thanh chuyển Điều trước/sau, chọn chương, chọn điều.
  - Hộp “Quy định của luật”.
  - Các nút Lưu, In, Chia sẻ, Trích dẫn.
  - Tab: Bình luận khoa học, Điều liên quan và các phần thực tiễn. Góc nhìn Luật sư Nam, Bản án liên quan, Tình huống thực tiễn chỉ thành tab riêng khi điều đó đã có nội dung; chưa có phần nào thì gộp thành một tab "Thực tiễn áp dụng" (tránh lặp nội dung trống trên hàng trăm trang).
- **Phải:**
  - Tìm kiếm liên quan: thuật ngữ có thật trong văn bản điều luật.
  - Điều liên quan: từ các liên kết dẫn chiếu giữa các điều.
  - Bản đồ tư duy, sinh tự động theo nội dung điều luật:
    - điều có định nghĩa: các khái niệm được định nghĩa;
    - điều về tội danh: khung hình phạt theo từng khoản;
    - trường hợp còn lại: cấu trúc các khoản.
  - Văn bản liên quan.

Liên kết sâu:

| Mục đích | Dạng liên kết |
|---|---|
| Tới một khoản | `…/dieu-51/#k1` |
| Tới một điểm | `…/dieu-51/#k1-s` |
| Tìm kiếm | `…/bo-luat-hinh-su/?q=án treo` |

Liên kết cũ dạng `#d173` và `#tim=…` tự chuyển sang địa chỉ mới.

**Bổ sung nội dung các tab** Góc nhìn Luật sư Nam, Bản án liên quan, Tình huống thực tiễn:

1. Sao chép `src/blhs/_mau.html` thành `src/blhs/<số điều>.html`.
2. Điền nội dung.
3. Chạy lại `python3 tools/build.py`.

## Việc cần làm trước khi chạy chính thức

- [ ] **Bật GitHub Pages**: Settings → Pages → *Deploy from a branch* → `gh-pages` / `(root)`.
- [ ] **Luật sư phụ trách rà soát 3 bài viết** trong `src/bai-viet/` trước khi công bố chính thức.
- [ ] Bổ sung số Thẻ luật sư, Đoàn Luật sư tại trang Đội ngũ (chỉ công bố thông tin đã được luật sư đồng ý).
- [ ] Thay ảnh minh họa lấy từ bản mockup (`assets/img/hero.webp`, `assets/img/dich-vu/*`, `assets/img/bai-viet/*`) bằng ảnh thật độ phân giải cao; ảnh gốc đặt trong `src/brand/goc/` rồi chạy lại `tools/make_images.py`.
- [ ] Chuyển sang tên miền lsn.vn: xem mục dưới.
- [ ] Chuyển hướng hoặc đặt `noindex` cho website cũ (`willmichco.github.io/Website/`) để tránh trùng lặp nội dung với website mới.
- [ ] **Google Search Console**: xác minh tên miền, nộp `sitemap.xml`, theo dõi mục *Trang* (lập chỉ mục) và *Trải nghiệm trên trang* (Core Web Vitals) sau 2–4 tuần.
- [ ] **Google Business Profile** (Google Maps): tạo hoặc nhận hồ sơ công ty, tên, địa chỉ, số điện thoại ghi đúng như trên website; quan trọng nhất cho tìm kiếm "luật sư gần đây", "luật sư TP.HCM".
- [ ] Kiểm tra dữ liệu có cấu trúc trên bản chạy thật bằng [Rich Results Test](https://search.google.com/test/rich-results) và [Schema Validator](https://validator.schema.org/) (trang chủ, một trang dịch vụ, một bài viết, một trang điều luật).
- [ ] Đo tốc độ bản chạy thật bằng [PageSpeed Insights](https://pagespeed.web.dev/).
- [ ] Luật sư soát lại mô tả "khung hình phạt, mức cao nhất" tự sinh trên trang điều luật (`penalty_summary` trong `tools/blhs.py`).
- [ ] Viết nội dung tab "Thực tiễn áp dụng" (góc nhìn luật sư, bản án, tình huống) cho các điều được tìm nhiều: 173, 174, 134, 260, 51, 65.

> ⚖️ Khi sửa nội dung, không thêm cụm cam kết kết quả (“cam kết thắng kiện”…) và không đăng số liệu chưa kiểm chứng. Bộ Quy tắc Đạo đức và Ứng xử nghề nghiệp luật sư Việt Nam nghiêm cấm luật sư hứa hẹn bảo đảm kết quả vụ việc (Quy tắc 9.1.6).

## Chuyển sang tên miền lsn.vn

Chỉ làm khi lsn.vn đã mua và truy cập được. Trước đó giữ nguyên `SITE_URL` hiện tại.

1. Trỏ DNS lsn.vn tới nơi lưu trữ đã chọn. Nếu dùng GitHub Pages: tạo tệp `CNAME` ở thư mục gốc chứa dòng `lsn.vn`, khai báo tên miền trong Settings → Pages, bật *Enforce HTTPS*.
2. Trong `tools/data.py`: `SITE_URL = "https://lsn.vn"`, `BASE_PATH = "/"`.
3. `python3 tools/build.py && python3 tools/check_seo.py`: phải không còn LỖI, canonical đã sang lsn.vn.
4. Google Search Console: thêm thuộc tính tên miền `lsn.vn` (xác minh DNS), nộp `https://lsn.vn/sitemap.xml`.
5. Bản cũ: nếu lsn.vn chạy trên GitHub Pages thì `willmichco.github.io/luatsunam/` tự chuyển hướng 301 sang lsn.vn. Bản chatgpt.site không chuyển hướng 301 được thì cứ để chạy: canonical trên đó đã trỏ về lsn.vn, Google sẽ dần gộp tín hiệu. Nơi lưu trữ nào cho phép chuyển hướng 301 thì bật lên và dùng công cụ *Change of Address* trong Search Console.
6. Cập nhật lsn.vn trên Google Business Profile, Zalo OA, danh thiếp và các trang mạng xã hội.

## Triển khai

Mỗi lần push vào `main`, GitHub Actions (`.github/workflows/pages.yml`) chạy `tools/check_seo.py` rồi xuất bản website sang nhánh `gh-pages` (bỏ qua `src/`, `tools/`, README). Còn LỖI SEO thì không xuất bản.

Mỗi pull request được `.github/workflows/seo-check.yml` kiểm tra: build lại phải ra đúng các tệp đã commit (tránh quên chạy build), và `check_seo.py` không có LỖI.
