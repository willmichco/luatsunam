# Hướng dẫn sử dụng trang quản trị (CMS) – Luật Sư Nam

Mọi việc sửa nội dung làm tại **<https://willmichco.github.io/luatsunam/admin/>**. Không cần biết code, không cần vào GitHub.
Bấm **Lưu** → website tự cập nhật sau **1–3 phút**. Nhập sai → website **giữ nguyên bản cũ**, quản trị nhận email báo lỗi.

## 0. Đăng nhập

**Hiện tại (trước khi có Worker đăng nhập):** đăng nhập bằng *mã truy cập GitHub* (làm 1 lần, khoảng 3 phút):

1. Đăng nhập github.com → ảnh đại diện → **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
2. *Token name*: `CMS Luật Sư Nam` · *Expiration*: 90 ngày · *Resource owner*: `willmichco` · *Repository access*: **Only select repositories** → `luatsunam`.
3. *Permissions* → *Repository permissions* → **Contents: Read and write** → **Generate token** → chép mã (bắt đầu bằng `github_pat_`).
4. Mở /admin → **Đăng nhập bằng mã truy cập** → dán mã → **Đăng nhập**.

> Mã này như chìa khóa: không gửi qua Zalo/email, không dùng trên máy công cộng (dùng xong bấm ảnh đại diện → Đăng xuất). Hết hạn thì tạo mã mới.

**Sau khi cài Worker (GĐ3):** bấm **Đăng nhập bằng GitHub** – không cần mã.

## 1. Đăng bài viết mới (khoảng 15 phút, chưa tính thời gian duyệt)

1. **Bài viết** → **Tạo mới**.
2. *Tiêu đề bài viết* → chọn *Lĩnh vực chính*. Đường dẫn tự tạo từ tiêu đề (bấm biểu tượng *Slug* ở cột phải để rút gọn còn 3–6 từ) – **sau khi lưu không đổi được**.
3. *Tóm tắt trên thẻ*, 3–4 ý *Tóm tắt nhanh*, *Đoạn dẫn đầu bài*.
4. *Nội dung bài viết*: dán thân bài. Dùng **Tiêu đề 2** cho mục chính (tự vào mục lục), **Tiêu đề 3** cho mục nhỏ, nút **Trích dẫn** để làm hộp lưu ý, **Chèn → Bảng** để thêm bảng (mỗi dòng một hàng, ô cách nhau dấu `|`), **Chèn → Ảnh** (bắt buộc điền mô tả ảnh).
5. *SEO*: tiêu đề Google (bộ đếm 15–60 ký tự), mô tả Google (70–160 ký tự).
6. **Để nguyên dấu “Bản nháp”** → **Lưu**.
7. Gửi luật sư phụ trách link xem trước `/nhap/<đường-dẫn>/` (có khi đã chạy bản thử Cloudflare).
8. Luật sư duyệt → bỏ dấu *Bản nháp* → **Lưu** → bài lên site sau 1–3 phút.
9. Mở bài trên site kiểm tra; Google Search Console → Kiểm tra URL → Yêu cầu lập chỉ mục.

## 2. Sửa hoặc thêm khối trên một trang

1. **Trang dựng từ khối** → chọn trang → mục **Các khối trên trang**.
2. **Thêm khối** → chọn loại (15 loại: Đầu trang lớn, Dải cam kết, Lưới thẻ, Ảnh + chữ, Các bước, Dòng thời gian, Đội ngũ, Danh sách dấu tích, Đoạn văn tự do, Hỏi đáp, Lưới lĩnh vực, Bài viết mới nhất, Giấy tờ theo lĩnh vực, Kênh liên hệ, Bản đồ) → điền nội dung.
3. Kéo biểu tượng ⋮⋮ để đổi thứ tự. Muốn tạm ẩn: tắt **Hiển thị khối này** (đừng xóa).
4. **Lưu** → kiểm tra trên site sau 1–3 phút, cả trên điện thoại.

## 3. Tạo trang mới (khoảng 20 phút)

1. **Trang dựng từ khối** → **Tạo mới** → *Tên trang*, *Nằm trong mục* (nếu là trang con), *Đầu trang tiêu chuẩn* (tiêu đề lớn + đoạn mở đầu), *SEO*.
2. Ghép khối (thường: Đoạn văn tự do / Lưới thẻ / Hỏi đáp…). Khối liên hệ đỏ cuối trang có sẵn.
3. Trang mới là **bản nháp** – bỏ dấu khi đã duyệt → **Lưu**.
4. Cần hiện trên menu: **Cài đặt → Menu và chân trang** → thêm mục → chọn trang vừa tạo (trang mới có trong danh sách sau 2–3 phút, tải lại /admin).

## 4. Đổi hotline, email, địa chỉ, giờ làm việc

**Cài đặt → Thông tin công ty** → sửa → **Lưu**. Tự cập nhật trên mọi trang: nút Gọi/Zalo, chân trang, bản đồ, thẻ luật sư, dữ liệu Google, trạng thái “Đang trong giờ làm việc”.
Trong các ô chữ, viết `{{hotline}}`, `{{luat_su}}`, `{{email}}`, `{{dia_chi}}`, `{{gio_lam_viec}}` thay vì gõ số/tên cứng để luôn tự cập nhật.

## 5. Đổi đường dẫn trang đã đăng (hiếm khi cần)

1. Tạo trang/bài mới với đường dẫn mới, chép nội dung sang.
2. **Cài đặt → Chuyển hướng 301** → thêm dòng: *Đường dẫn cũ* `/duong-dan-cu/` → *Chuyển tới* `/duong-dan-moi/`.
3. Xóa trang/bài cũ → **Lưu**. Build tự kiểm: đích phải có thật, không vòng lặp.

## 6. Khi website không cập nhật sau 5 phút (build lỗi)

- **Biên tập viên:** không cần lo – website vẫn chạy bản cũ. Báo quản trị kèm tên trang/bài vừa sửa.
- **Quản trị:** mở email “Build website lỗi” (issue trên GitHub) → đọc danh sách lỗi tiếng Việt, mỗi dòng ghi **tệp + tên trường** (ví dụ `content/hoi-dap.yml › Câu hỏi 1 › Câu trả lời: Không dùng mã HTML…`) → sửa đúng trường đó trong /admin → **Lưu**. Build lại thành công thì issue tự đóng.

## 7. Quy tắc nội dung pháp lý

- Bài hoặc câu trả lời có dẫn điều luật phải được luật sư duyệt trước khi bỏ dấu nháp.
- Không hứa hẹn kết quả (Quy tắc 9.1.6 Bộ Quy tắc Đạo đức và Ứng xử nghề nghiệp luật sư Việt Nam).
- Mỗi quý: rà ngày cập nhật và hiệu lực văn bản pháp luật trong bài cũ; cập nhật *Ngày cập nhật*.
