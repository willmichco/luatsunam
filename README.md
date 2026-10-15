# LSN Law Firm – Công Ty Luật TNHH Luật Sư Nam

Website tĩnh nhiều trang (HTML, CSS, JavaScript thuần), dùng giao diện mới LSN Law Firm và nội dung chuyển từ website cũ [`willmichco/Website`](https://github.com/willmichco/Website).

- Xem trực tiếp: <https://willmichco.github.io/luatsunam/>
- Chỉ cần sửa nội dung trong `tools/data.py` và `src/`, sau đó chạy `python3 tools/build.py` để sinh lại toàn bộ trang.

## Sơ đồ website

| Đường dẫn | Trang | Dữ liệu có cấu trúc |
|---|---|---|
| `/` | Trang chủ | LegalService, WebSite |
| `/gioi-thieu/` | Giới thiệu, triết lý hành nghề, cam kết nghề nghiệp | AboutPage |
| `/doi-ngu-luat-su/` | Hồ sơ Luật sư Nam | ProfilePage, Person |
| `/vi-sao-chon-chung-toi/` | Bốn nguyên tắc làm việc | WebPage |
| `/quy-trinh-lam-viec/` | Quy trình 4 bước, hồ sơ cần chuẩn bị | WebPage |
| `/dich-vu/` | Tổng quan 7 lĩnh vực | CollectionPage, ItemList |
| `/dich-vu/<lĩnh-vực>/` | 7 trang dịch vụ: thừa kế, tranh tụng, hôn nhân gia đình, đất đai, hình sự, dân sự, công chứng. Mỗi trang: tình huống thường gặp, luật sư giúp gì, việc nên làm ngay, các bước, giấy tờ, hỏi đáp có dẫn điều luật | Service |
| `/kien-thuc-phap-ly/` | Danh mục bài viết và công cụ | CollectionPage, ItemList |
| `/kien-thuc-phap-ly/<bài-viết>/` | 3 bài viết pháp lý, mở đầu bằng khung “Tóm tắt nhanh” | Article |
| `/cau-hoi-thuong-gap/` | 7 câu hỏi thường gặp | FAQPage |
| `/lien-he/` | Gọi điện, Zalo, email, việc gấp, văn phòng và bản đồ | ContactPage |
| `/chinh-sach-bao-mat/`, `/dieu-khoan-su-dung/`, `/mien-tru-trach-nhiem/` | Văn bản pháp lý của website | WebPage |

Mọi trang có: `title` và `description` riêng, `canonical`, Open Graph, Twitter Card, breadcrumb hiển thị kèm `BreadcrumbList`. Đường dẫn giữ nguyên như website cũ để không mất thứ hạng khi chuyển tên miền.

## Giao diện thống nhất

Toàn website dùng một tệp giao diện duy nhất `assets/css/style.css` và chỉ dùng **ảnh thật** của Luật sư Nguyễn Trọng Nam:

- **Giọng văn:** gọi người đọc là “anh chị”, câu ngắn, tiêu đề như lời nói hằng ngày; khẳng định pháp lý luôn kèm điều luật.
- **Khung trang giống nhau:** đầu trang nền kem (đường dẫn, tiêu đề, đoạn mở đầu, thẻ “Luật sư phụ trách” có ảnh thật, nút Gọi/Zalo) → các mục xen kẽ nền trắng/kem → khối liên hệ đỏ cuối trang (ảnh luật sư, Gọi điện, Nhắn Zalo, Đến văn phòng). Trên điện thoại có thanh Gọi / Zalo cố định ở cuối màn hình.
- **Thành phần dùng chung**, sinh bởi `tools/build.py`, gọi được từ `src/pages/*.html` bằng token:

| Token | Hiển thị |
|---|---|
| `{{problems_grid}}` | 7 thẻ “Anh chị đang gặp chuyện gì?” (thứ tự: `PROBLEM_ORDER` trong `tools/data.py`) |
| `{{services_grid}}` | 7 thẻ lĩnh vực |
| `{{faq_list:id1,id2}}` | Câu hỏi thường gặp chọn lọc |
| `{{articles_grid}}` | Thẻ bài viết |
| `{{photo:van-phong}}`, `{{photo:phien-toa\|lazy}}` | Ảnh thật của luật sư dạng `<picture>` (AVIF + WebP, 3 kích thước); `lazy` cho ảnh dưới màn hình đầu |
| `{{open_now}}` | Trạng thái “Đang trong giờ làm việc / Ngoài giờ · làm việc lại 08:00…” theo giờ Việt Nam |
| `{{lawyer}}`, `{{phone}}`, `{{zalo}}`, `{{v}}`… | Thông tin trong `FIRM`, phiên bản tài nguyên |

Khối liên hệ cuối trang được thêm tự động (tắt bằng `"contact_band": false` trong khối meta); thẻ luật sư ở đầu trang tắt bằng `"lawyer_card": false`.

## Trải nghiệm và hiệu năng

- **Điện thoại:** thanh Gọi / Zalo cố định; 8 tình huống ở trang chủ hiển thị dạng danh sách gọn; các bước làm việc dạng dòng thời gian; thẻ đánh số gộp số và tiêu đề một hàng; footer hai cột; đường dẫn ẩn mục cuối (đã có ở tiêu đề).
- **Giờ làm việc:** `main.js` hiển thị “Đang trong giờ làm việc” hoặc “Ngoài giờ · làm việc lại 08:00 sáng mai/thứ Hai” theo giờ Việt Nam (Thứ 2 – Thứ 6, 08:00 – 17:30). Chưa tính ngày lễ; nếu đổi giờ làm việc, sửa cả `FIRM["hours"]` và hàm trong `main.js`.
- **Máy tính:** bấm số điện thoại sẽ chép số vào bộ nhớ tạm và báo “Đã chép số…”; tìm kiếm mở bằng phím `/` hoặc `Ctrl/⌘ + K`, chọn kết quả bằng phím mũi tên.
- **Bài viết:** mục lục thu gọn ở đầu bài trên điện thoại, thanh tiến độ đọc dưới header, nút “Chia sẻ bài viết” (mở bảng chia sẻ của điện thoại như Zalo, Messenger; máy tính thì chép liên kết).
- **Ảnh:** AVIF (nhẹ hơn WebP khoảng 40%) kèm WebP dự phòng, mỗi ảnh 3 bề ngang 480/640/gốc; thẻ luật sư trên điện thoại dùng ảnh avatar vuông nhỏ.
- **Phông chữ:** 3 độ đậm 400/600/700 (bỏ 500 để bớt 2 tệp tải). Phông dự phòng Arial/Roboto được chỉnh `size-adjust` khớp chiều rộng Be Vietnam Pro nên chữ không nhảy dòng khi phông chính tải xong (CLS ≈ 0). Tệp `be-vietnam-pro-500-*` vẫn giữ vì `tools/make_images.py` dùng cho ảnh chia sẻ.
- **Trang 404:** tự xác định thư mục gốc khi chạy, nên tải đúng giao diện cả trên GitHub Pages (`BASE_PATH`) lẫn tên miền riêng.

## Liên kết nội bộ

- Menu có menu xổ cho **Giới thiệu**, **Lĩnh vực hoạt động** (7 lĩnh vực) và **Kiến thức pháp lý**.
- Mỗi trang dịch vụ liên kết tới 3 lĩnh vực liên quan (khai báo ở trường `related` trong `tools/data.py`), bài viết liên quan, quy trình làm việc và câu hỏi thường gặp.
- Mỗi bài viết có mục lục, liên kết trong nội dung tới trang dịch vụ, khung “Cần luật sư về…”, danh sách lĩnh vực liên quan và bài viết khác.
- Footer liên kết tới toàn bộ trang chính và 7 lĩnh vực. Trang cũ `/dich-vu/lao-dong-viec-lam/` chuyển hướng về `/dich-vu/`.
- Tìm kiếm trong website (biểu tượng kính lúp) dùng chỉ mục `assets/search-index.json` do script sinh ra.

## Cấu trúc thư mục

```
tools/data.py              Thông tin pháp nhân, 7 lĩnh vực, bài viết, câu hỏi thường gặp
tools/build.py             Sinh toàn bộ trang, sitemap.xml, robots.txt, site.webmanifest, chỉ mục tìm kiếm
tools/make_images.py       Sinh logo, favicon, ảnh luật sư (cắt, tối ưu, AVIF + WebP nhiều kích thước) và ảnh chia sẻ OG
src/brand/logo-lsn.webp    Logo gốc (nền trong suốt)
src/brand/anh-that/        Ảnh thật gốc của luật sư: van-phong.webp (tại văn phòng), phien-toa.webp (tại phiên tòa)
src/pages/*.html           Nội dung các trang đơn lẻ (khối <!--meta {...} --> ở đầu là tiêu đề, mô tả)
src/bai-viet/*.html        Nội dung bài viết
assets/css/style.css       Toàn bộ giao diện (một tệp duy nhất): biến màu, chữ, khoảng cách ở :root, thành phần dùng chung
assets/js/main.js          Menu, tìm kiếm, hiện dần khi cuộn, mục đang đọc, bản đồ, giờ làm việc, chia sẻ, tiến độ đọc
assets/fonts/              Be Vietnam Pro, phông sans-serif duy nhất của website (tự lưu trữ, SIL OFL 1.1)
assets/img/                Ảnh
```

Các tệp `index.html`, `404.html`, `sitemap.xml`, `robots.txt`, `site.webmanifest`, `assets/search-index.json` do `tools/build.py` sinh ra. **Không sửa trực tiếp các tệp này**, sửa nguồn rồi chạy lại script.

## Sửa nội dung thường gặp

| Muốn sửa | Sửa tại |
|---|---|
| Số điện thoại, email, địa chỉ, giờ làm việc | `FIRM` trong `tools/data.py` |
| Nội dung một lĩnh vực | Mục tương ứng trong `SERVICES` (`tools/data.py`); ý nghĩa từng trường ghi ở đầu danh sách. Câu trả lời trong `faq` phải dẫn điều luật cụ thể. Sau khi sửa tên/mô tả ngắn, chạy lại `tools/make_images.py` để cập nhật ảnh chia sẻ |
| Thêm bài viết | Thêm mục vào `ARTICLES` (kèm 3–4 ý `key_points` cho khung “Tóm tắt nhanh”), tạo `src/bai-viet/<slug>.html`, chạy `python3 tools/make_images.py` để sinh ảnh chia sẻ `assets/img/og/bai-viet-<slug>.jpg` |
| Câu hỏi thường gặp | `FAQ` trong `tools/data.py` |
| Hồ sơ luật sư | `src/pages/gioi-thieu.html` |
| Tên miền | `SITE_URL`, `BASE_PATH` đầu tệp `tools/data.py` |
| Logo, ảnh luật sư, ảnh chia sẻ | Thay `src/brand/logo-lsn.webp` hoặc ảnh trong `src/brand/anh-that/` (giữ tên tệp), chạy `pip install pillow fonttools brotli && python3 tools/make_images.py`. Website **chỉ dùng ảnh thật**, không dùng ảnh AI/ảnh mẫu. Nếu bố cục ảnh mới khác, chỉnh toạ độ cắt ở `PHOTOS` trong `tools/make_images.py` |
| Tên, chức danh luật sư hiển thị ở thẻ "Luật sư phụ trách" | `lawyer`, `lawyer_role` trong `FIRM` (`tools/data.py`) |
| Phông chữ | `--font-sans` (chữ thường), `--font-heading` (tiêu đề) ở `:root` trong `assets/css/style.css` |

```bash
python3 tools/build.py                 # sinh lại website
python3 -m http.server 8000            # xem thử tại http://localhost:8000
```


## Việc cần làm trước khi chạy chính thức

- [ ] **Bật GitHub Pages**: Settings → Pages → *Deploy from a branch* → `gh-pages` / `(root)`.
- [ ] **Luật sư phụ trách rà soát 3 bài viết** trong `src/bai-viet/` trước khi công bố chính thức.
- [ ] Bổ sung số Thẻ luật sư, Đoàn Luật sư tại trang Đội ngũ (chỉ công bố thông tin đã được luật sư đồng ý).
- [x] Bỏ toàn bộ ảnh AI/mockup; website chỉ dùng 2 ảnh thật của Luật sư Nguyễn Trọng Nam.
- [ ] Bổ sung ảnh thật độ phân giải cao (≥ 1600px): mặt tiền văn phòng 22c Vũ Ngọc Phan, phòng tiếp khách, luật sư trao đổi hồ sơ (khách quay lưng hoặc đã đồng ý). Đặt vào `src/brand/anh-that/` rồi chạy lại `tools/make_images.py`.
- [ ] Khi có tên miền riêng: sửa `SITE_URL`/`BASE_PATH`, chạy lại build, khai báo tên miền trong Settings → Pages, nộp `sitemap.xml` lên Google Search Console.
- [ ] Chuyển hướng hoặc đặt `noindex` cho website cũ (`willmichco.github.io/Website/`) để tránh trùng lặp nội dung với website mới.

> ⚖️ Khi sửa nội dung, không thêm cụm cam kết kết quả (“cam kết thắng kiện”…) và không đăng số liệu chưa kiểm chứng. Bộ Quy tắc Đạo đức và Ứng xử nghề nghiệp luật sư Việt Nam nghiêm cấm luật sư hứa hẹn bảo đảm kết quả vụ việc (Quy tắc 9.1.6).

## Triển khai

Mỗi lần push vào `main`, GitHub Actions (`.github/workflows/pages.yml`) xuất bản website sang nhánh `gh-pages` (bỏ qua `src/`, `tools/`, README).
