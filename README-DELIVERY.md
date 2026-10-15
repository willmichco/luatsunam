# Công Ty Luật TNHH Luật Sư Nam

Thiết kế đỏ, vàng kim, kem theo ảnh tham chiếu; logo do khách hàng cung cấp.
Nội dung nguồn: https://github.com/willmichco/law_newsite.

Chạy `python3 tools/package_site.py` để sinh website vào `dist/`.
Chạy `python3 -m http.server 8765 --directory dist` để xem ở http://localhost:8765.
Giao diện: `assets/css/style.css` (một tệp duy nhất); trang chủ: `src/pages/home.html`; dữ liệu: `tools/data.py`; ảnh: `tools/make_images.py` (chỉ dùng ảnh thật trong `src/brand/anh-that/`).

Biểu mẫu mở thư nháp trong ứng dụng email, chưa có dịch vụ nhận biểu mẫu trực tiếp.
480 → 23 trang HTML sau khi bỏ Từ điển Bộ luật Hình sự (10/2026).
Nội dung pháp luật giữ từ repository; chưa thẩm định toàn bộ hiệu lực pháp luật và bình luận.
