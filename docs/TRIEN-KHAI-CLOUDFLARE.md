# Triển khai bản thử Cloudflare + đăng nhập GitHub cho /admin (GĐ3 – phần việc của quản trị, khoảng 30 phút)

Code đã sẵn trong repo. Các bước dưới chỉ là bấm trên giao diện Cloudflare/GitHub, làm theo thứ tự A → E.
Toàn bộ dùng gói **Free**: 0 đ/tháng.

## 0. Cho GitHub Pages đọc nhánh `gh-pages` – đã làm (16/10/2026)

repo → **Settings** → **Pages** → *Build and deployment* → *Source*: **Deploy from a branch** → *Branch*: **gh-pages** / **(root)** → **Save**.

Workflow luôn đăng bản build mới nhất lên `gh-pages`, nên đổi nguồn lúc nào site cũng là bản mới nhất. Lần build đầu sau khi đổi
tự gỡ bản build cũ khỏi gốc `main` (commit “Gỡ bản build cũ… [skip ci]”), `main` chỉ còn mã nguồn.
**Không chọn** *Source: GitHub Actions*: website sẽ không nhận bản mới (workflow báo lỗi qua issue/email).

## A. Bản thử trên Cloudflare Pages (chứa bản nháp, chặn Google)

1. <https://dash.cloudflare.com> → **Workers & Pages** → **Create** → tab **Pages** → **Connect to Git** → chọn repo `willmichco/luatsunam`.
   (Nếu Cloudflare chỉ còn gợi ý “Workers”, chọn **Import a repository** – các ô cấu hình giống bên dưới.)
2. *Project name*: `luatsunam` → địa chỉ sẽ là `https://luatsunam.pages.dev`.
3. *Production branch*: `main` · *Framework preset*: **None**
   - *Build command*: `pip install -r requirements.txt && python3 tools/build.py`
   - *Build output directory*: `dist`
4. **Environment variables** → thêm `PYTHON_VERSION` = `3.13`. **Không** đặt `SITE_URL`: build tự nhận ra đang chạy trên Cloudflare và chuyển sang chế độ bản thử (xuất bản nháp tại `/nhap/…`, noindex toàn bộ bằng thẻ robots + header).
5. **Save and Deploy** (lần đầu khoảng 2 phút). Mở `https://luatsunam.pages.dev/nhap/` để xem danh sách bản nháp.

Kiểm: `https://luatsunam.pages.dev/robots.txt` phải ghi `Disallow: /`.

## B. Ứng dụng đăng nhập GitHub (OAuth App)

1. <https://github.com/settings/developers> → **OAuth Apps** → **New OAuth App**.
2. *Application name*: `CMS Luật Sư Nam` · *Homepage URL*: `https://willmichco.github.io/luatsunam/`
   *Authorization callback URL*: `https://luatsunam-cms-auth.<tên-tài-khoản>.workers.dev/callback` (tên chính xác lấy ở bước C.3; có thể sửa lại sau).
3. **Register application** → chép **Client ID** → **Generate a new client secret** → chép **Client Secret** (chỉ hiện 1 lần).

## C. Worker đăng nhập (giữ Client Secret, không lộ ra trình duyệt)

1. Cloudflare → **Workers & Pages** → **Create** → **Create Worker** → tên `luatsunam-cms-auth` → **Deploy**.
2. **Edit code** → xóa code mẫu → dán toàn bộ nội dung tệp [`cloudflare/oauth-worker/worker.js`](../cloudflare/oauth-worker/worker.js) → **Deploy**.
3. Chép địa chỉ Worker (dạng `https://luatsunam-cms-auth.<tên-tài-khoản>.workers.dev`), quay lại bước B.2 sửa *callback URL* cho khớp nếu cần.
4. Worker → **Settings** → **Variables and Secrets** → thêm:
   | Tên | Loại | Giá trị |
   |---|---|---|
   | `GITHUB_CLIENT_ID` | Text | Client ID (bước B.3) |
   | `GITHUB_CLIENT_SECRET` | **Secret** | Client Secret (bước B.3) |
   | `ALLOWED_DOMAINS` | Text | `willmichco.github.io, luatsunam.pages.dev, *.luatsunam.pages.dev` |
5. **Deploy**. Mở địa chỉ Worker: thấy dòng “Worker đăng nhập CMS – Luật Sư Nam” là đúng.

(Dùng dòng lệnh thay cho bấm tay: trong thư mục `cloudflare/oauth-worker` chạy `npx wrangler deploy` rồi `npx wrangler secret put GITHUB_CLIENT_ID` và `… GITHUB_CLIENT_SECRET`. Kiểm code: `node worker.test.mjs`.)

## D. Nối /admin với Worker

1. GitHub repo → **Settings** → **Secrets and variables** → **Actions** → tab **Variables** → **New repository variable**: `CMS_OAUTH_URL` = địa chỉ Worker (bước C.3, không có `/` cuối).
2. Cloudflare Pages project `luatsunam` → **Settings** → **Environment variables** → thêm `CMS_OAUTH_URL` cùng giá trị.
3. Lưu bất kỳ nội dung nào trong /admin (hoặc GitHub → Actions → **Build và đăng website** → **Run workflow** → *Use workflow from*: **main**) để build lại.
4. Mở /admin: có nút **Đăng nhập bằng GitHub**. Biên tập viên cần là cộng tác viên của repo (quyền **Write**).

Muốn /admin chỉ còn trên bản thử pages.dev (theo kế hoạch ban đầu): thêm repository variable `CMS_ADMIN` = `0`.

## E. Email khi build lỗi

- **GitHub Actions** đã tự mở issue “Build website lỗi” kèm danh sách lỗi tiếng Việt → GitHub gửi email cho người theo dõi repo. Kiểm: repo → **Watch** → **All Activity** (hoặc *Custom → Issues*); <https://github.com/settings/notifications> → *Actions* → bật **Only notify for failed workflows**.
- **Cloudflare**: **Notifications** → **Add** → **Pages** → *Deployment failure* → nhập email quản trị.

## F. (Tùy chọn) Khóa /admin và /nhap/ trên pages.dev bằng Cloudflare Access

**Zero Trust** → **Access** → **Applications** → **Add an application** → *Self-hosted* → domain `luatsunam.pages.dev`, path `admin` (thêm một ứng dụng nữa cho path `nhap`) → policy *Allow* → *Emails* = danh sách biên tập viên. Gói Free tối đa 50 người. Nếu pages.dev không cho chọn, dựa vào đăng nhập GitHub tới GĐ5 (tên miền riêng).
