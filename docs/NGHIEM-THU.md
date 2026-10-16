# Nghiệm thu CMS – GĐ4 (16/10/2026)

Kế hoạch yêu cầu GĐ4 đạt tiêu chí 1–6 và 9 (mục 2 kế hoạch). Bảng dưới ghi kết quả đo thật, cách kiểm và phần còn chờ.
Ký hiệu: **Đạt** = đã kiểm xong · **Đạt phần máy** = đã chạy đủ thao tác trên CMS thật, chờ người dùng thật bấm giờ · **Chờ** = phụ thuộc việc chưa làm.

| # | Tiêu chí | Kết quả | Cách kiểm |
|---|---|---|---|
| 1 | Người không biết code đăng 1 bài có ảnh ≤ 15 phút | **Đạt phần máy** – chờ bấm giờ người thật | Chạy trên Sveltia 0.221.8 thật: tạo bài, tải ảnh JPG 3000 px (tự thành WebP 2400 px), mô tả ảnh, bảng, SEO, lưu nháp → build: bản chính thức không xuất nháp, bản thử dựng đúng bố cục + `noindex`. Khoảng 26 thao tác. Bài tập 1 tại `/admin/bai-tap/` |
| 2 | Thêm, xóa, đổi thứ tự section trang chủ ≤ 5 phút | **Đạt phần máy** – chờ bấm giờ người thật | Kéo đổi thứ tự, thêm khối, ẩn khối, xóa khối trên Trang chủ → build: thứ tự HTML đúng, khối ẩn không ra trang. Khoảng 14 thao tác. Bài tập 2 |
| 3 | Trang mới từ khối, có trên menu ≤ 20 phút | **Đạt phần máy** – chờ bấm giờ người thật | Tạo trang “Phí dịch vụ” + đưa vào menu “Giới thiệu” → build: có trang, menu, sitemap, ảnh chia sẻ tự sinh. Trang mới có trong danh sách chọn của menu sau 1 lượt build (≈ 1 phút) + tải lại /admin. Bài tập 3 |
| 4 | CMS không bao giờ lệch site | **Đạt** | GĐ4 thêm ô “Đường dẫn bài viết” chỉ ở `tools/schema.py` → build sinh `admin/config.yml` mới → ô hiện trong CMS ngay lượt sau. Cấu hình kiểm theo schema Sveltia: 0 lỗi |
| 5 | Nhập sai không làm sập site; email ≤ 10 phút, lỗi tiếng Việt chỉ rõ tệp + trường | **Đạt** – báo lỗi sau 19 giây (issue #23), site giữ bản cũ; sửa xong thì issue tự đóng sau 20 giây | Cố ý xóa tiêu đề bài viết trên `main` (commit thử nghiệm) rồi hoàn tác |
| 6 | Luật sư duyệt nháp đúng bố cục thật tại `/nhap/<slug>/`, không bị Google index | **Đạt phần code** – chờ bản thử Cloudflare (bước A) để có link thật | Bản thử (`CF_PAGES`): nháp dựng tại đường dẫn thật, `/nhap/<slug>/` chuyển 302 tới đó, thẻ `noindex`, header `X-Robots-Tag: noindex`, `robots.txt` chặn toàn bộ. Bản chính thức: nháp không xuất, không vào sitemap, tìm kiếm, menu |
| 9 | Bấm Lưu → lên site ≤ 3 phút | **Đạt** – 51, 48 và 50 giây (đo đầu-cuối 3 lần); chậm nhất ước khoảng 2 phút | Thời điểm push → workflow build xong → GitHub Pages đăng xong (API GitHub Actions) |

## Tiêu chí 9 – thời gian từ lúc lưu tới lúc lên site

| Lần | Lần lưu (commit) | Push | Build + kiểm xong | GitHub Pages đăng xong | Tổng |
|---|---|---|---|---|---|
| 1 | `cb4ea96` sửa CMS + hướng dẫn | 01:07:00 | 01:07:23 | 01:07:51 | **51 giây** |
| 2 | `184713d` bài tập làm quen | 01:12:22 | 01:12:43 | 01:13:10 | **48 giây** |
| 3 | `5873796` kết quả nghiệm thu | 01:18:45 | 01:19:01 | 01:19:35 | **50 giây** |

Giờ UTC ngày 16/10/2026, lấy từ GitHub Actions. Hai phần của một lượt lưu, theo các lượt gần nhất:
- Build + kiểm trên GitHub Actions: 19–24 giây (7 lượt).
- GitHub Pages đăng: 22–92 giây, trung vị khoảng 31 giây (12 lượt).

Trường hợp chậm nhất ước khoảng 2 phút, vẫn dưới mức 3 phút.

Thêm mẫu đo: mỗi lần biên tập viên lưu trong lúc làm bài tập là một mẫu, xem ở GitHub → Actions.

Lưu ý: GitHub Pages cho trình duyệt giữ trang tới 10 phút. Ai vừa mở trang trước đó có thể thấy bản cũ: bấm Ctrl+F5 (điện thoại: mở tab ẩn danh) để xem bản mới.

## Tiêu chí 5 – nhập sai

Thử trên `main` thật: commit `3dfc867` cố ý để trống *Tiêu đề bài viết* của bài “Ly hôn đơn phương”.

| Mốc (UTC, 16/10) | Sự kiện |
|---|---|
| 01:13:20 | Push lần lưu sai |
| 01:13:39 | Build dừng, mở [issue #23](https://github.com/willmichco/luatsunam/issues/23) “Build website lỗi – site vẫn giữ bản cũ” → GitHub gửi email cho người theo dõi repo (**19 giây**) |
| – | Website không đổi: build lỗi thì không có bản build mới để đăng |
| 01:14:41 | Push bản hoàn tác (`aa58ba5`) |
| 01:15:01 | Build lại thành công, issue tự đóng kèm lời nhắn (**20 giây**) |

Nội dung issue (đúng như email):

```
Build dừng: 1 lỗi cần sửa
Website đang chạy KHÔNG bị ảnh hưởng (vẫn giữ bản cũ). Sửa đúng các trường dưới đây trong /admin rồi bấm Lưu.
content/bai-viet/ly-hon-don-phuong.md
- Tiêu đề bài viết: Không được để trống.
```

Cần anh/chị xác nhận đã nhận email lúc 01:13 (08:13 giờ VN). Không nhận được: GitHub → **Watch** → *All Activity*; [cài đặt thông báo](https://github.com/settings/notifications) → bật email.

## Lighthouse – mốc so sánh cho G5 (chuyển tên miền)

Lighthouse 13.5.0, trung vị 5 lần đo mỗi trang, chạy trên máy GitHub Actions ngày 16/10/2026 ([lượt đo](https://github.com/willmichco/luatsunam/actions/runs/38833850194), báo cáo chi tiết tải ở cuối trang, lưu 90 ngày).

| Trang | Thiết bị | Hiệu năng | Truy cập | Thực hành tốt | SEO | LCP | CLS | TBT | FCP | Speed Index | Tổng tải |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Trang chủ | Máy tính | 100 (100–100) | 100 | 100 | 100 | 0,4 s | 0,000 | 0 ms | 0,3 s | 0,3 s | 244 KB |
| Trang chủ | Điện thoại | 99 (96–100) | 100 | 100 | 100 | 1,8 s | 0,000 | 18 ms | 1,2 s | 1,2 s | 284 KB |
| Bài “Thời hiệu chia di sản” | Máy tính | 100 (100–100) | 100 | 100 | 100 | 0,3 s | 0,000 | 0 ms | 0,3 s | 0,3 s | 182 KB |
| Bài “Thời hiệu chia di sản” | Điện thoại | 100 (99–100) | 100 | 100 | 100 | 1,3 s | 0,000 | 45 ms | 1,1 s | 1,1 s | 176 KB |

Điện thoại: giả lập máy tầm trung, mạng 4G chậm (mặc định Lighthouse). Trong ngoặc: điểm thấp nhất – cao nhất giữa 5 lần. Mốc G5: sau khi chuyển tên miền, điểm không được thấp hơn bảng này.

Đo lại: GitHub → Actions → **Đo Lighthouse (site thật)** → **Run workflow** (chọn nhánh `main`; sau khi chuyển tên miền thì điền địa chỉ mới vào ô *urls*).

## Những gì chạy thử phát hiện và đã sửa trong GĐ4

| Phát hiện khi chạy trên CMS thật | Ảnh hưởng | Đã sửa |
|---|---|---|
| Ảnh chèn vào bài không bắt buộc mô tả; lỗi chỉ lộ ra lúc build | Bài có ảnh bị chặn khi đăng, mất một vòng sửa | Thành phần “Ảnh” riêng: ô *Mô tả ảnh* bắt buộc, CMS không cho lưu khi thiếu; thêm *Chú thích dưới ảnh* |
| Đường dẫn tự tạo từ tiêu đề dài bị cắt giữa chữ (`…tranh-mat-co`) | URL xấu, không sửa được sau khi lưu | Ô *Đường dẫn bài viết* riêng (2–8 từ); build bắt lỗi khi ô bị sửa lệch tên tệp |
| Ô chọn lĩnh vực có nút “+ Thêm lĩnh vực” mở form **tạo cả lĩnh vực mới**, ô chọn trông như bị khóa | Biên tập viên dễ tạo nhầm lĩnh vực rác | Danh sách tích sinh lúc build; ghi rõ thứ tự hiện = thứ tự tích |
| Đổi hotline: Zalo vẫn số cũ (ghi cứng), 4 mô tả SEO gõ thẳng số | Số cũ còn trên 10 trang | Zalo tự theo hotline; mô tả SEO dùng mã `{{hotline}}`; build chặn hotline/email gõ thẳng. Sau sửa: 0 trang còn số cũ |
| Esc, nút ← thoát form và **bỏ thay đổi chưa lưu không hỏi**; tải lại trang cũng mất | Mất bài đang soạn | Lớp hỏi lại trong /admin: Esc bị chặn kèm nhắc, ← hỏi xác nhận, đóng tab thì trình duyệt hỏi (thử 7 tình huống: đạt) |
| Bản nháp có lỗi chặn cả site chính thức | Một bài nháp dở dang chặn mọi thay đổi khác | Lỗi của bản nháp thành cảnh báo ở bản chính thức (bản thử vẫn chặn) |
| Kho ảnh stock (Picsum, Pexels…) và “Nhập URL” trong hộp chọn ảnh | Ảnh mẫu ngẫu nhiên, ảnh lấy từ site khác | Tắt |
| Khung “Xem trước” chung chung chiếm nửa màn hình ở form có cấu trúc | Form chật, dễ nhầm là bố cục thật | Tắt ở trang, lĩnh vực, cài đặt; giữ ở bài viết và trang văn bản |
| Tên khối có số thứ tự danh mục (“11 · Lưới lĩnh vực” ở vị trí 3) | Dễ nhầm là thứ tự trên trang | Bỏ số |
| Lần lưu đầu của mỗi tệp tạo diff lộn xộn (CMS sắp lại trường) | Khó xem lịch sử để hoàn tác | Chuẩn hóa toàn bộ `content/` theo đúng cách CMS ghi; HTML dựng ra giống hệt từng byte |

## Còn chờ

1. **Người dùng thật làm 4 bài tập** tại `/admin/bai-tap/` (bấm giờ tự động) → gửi kết quả để chốt tiêu chí 1–3.
2. **Bản thử Cloudflare + Worker đăng nhập** (docs/TRIEN-KHAI-CLOUDFLARE.md, mục A–D) → chốt tiêu chí 6 bằng link thật và để biên tập viên đăng nhập bằng GitHub.
3. **Đổi nhánh mặc định của repo sang `main`** (đang là nhánh cũ `claude/pensive-knuth-z2sfu9`).
