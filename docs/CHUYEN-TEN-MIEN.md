# Chuyển sang tên miền riêng (GĐ5) – làm khi đã mua tên miền

Phần code đã sẵn và đã chạy thử với tên miền giả (16/10/2026). Ngày chuyển chỉ còn các bước bấm dưới đây:
khoảng **60 phút**, cộng thời gian chờ đổi nameserver (thường dưới 1 giờ, tối đa 24 giờ).

Thứ tự đảm bảo site **không gián đoạn**: github.io vẫn chạy bản đầy đủ cho tới bước 7. Bước 7 chỉ làm khi tên miền
đã mở được site (bước 4). Trong bài, `tenmien.vn` là ví dụ – thay bằng tên miền thật.

## Cần có trước

- [ ] Tên miền đã mua, đứng tên công ty, **bật tự gia hạn**; đặt lịch nhắc trước hạn 30 ngày.
- [ ] Đã làm [TRIEN-KHAI-CLOUDFLARE.md](TRIEN-KHAI-CLOUDFLARE.md) mục A–E: project Cloudflare Pages `luatsunam`,
      Worker đăng nhập, email báo lỗi. Chưa làm thì làm trước (khoảng 30 phút).
- [ ] 2FA cho GitHub và Cloudflare (GĐ0).
- [ ] Chọn lúc ít khách (tối, cuối tuần), không trùng đợt chạy quảng cáo.

## 1. Trước 24 giờ (15 phút)

1. Tại nhà đăng ký tên miền: chụp màn hình **toàn bộ** bản ghi DNS (A, AAAA, CNAME, MX, TXT). MX và TXT là của email
   theo tên miền (Google Workspace, Zoho…) – mất là mất email.
2. Hạ TTL mọi bản ghi xuống thấp nhất (300 giây) để lúc đổi có hiệu lực nhanh.

## 2. Đưa tên miền vào Cloudflare (15 phút + chờ)

1. <https://dash.cloudflare.com> → **Add a domain** → nhập `tenmien.vn` → gói **Free**.
2. Cloudflare tự quét bản ghi DNS: đối chiếu với ảnh chụp bước 1.1, thiếu bản ghi nào (nhất là MX, TXT) thì **Add record** tay.
3. Tại nhà đăng ký: đổi nameserver sang 2 nameserver Cloudflare đưa ra. Chờ email “… is now active on Cloudflare”.
4. Gửi thử 1 email tới địa chỉ theo tên miền: phải nhận được.

## 3. Gắn tên miền vào site (10 phút)

1. **Workers & Pages** → `luatsunam` → **Custom domains** → **Set up a custom domain** → `tenmien.vn` → **Activate domain**.
2. **DNS** → **Add record**: *Type* `CNAME`, *Name* `www`, *Target* `tenmien.vn`, *Proxy* bật (đám mây cam).
3. **Rules** → **Create rule** → **Redirect Rule** → mẫu **Redirect from WWW to root** (301, giữ đường dẫn và tham số)
   ([hướng dẫn của Cloudflare](https://developers.cloudflare.com/rules/url-forwarding/examples/redirect-www-to-root/)).
4. **SSL/TLS** → **Edge Certificates** → **Always Use HTTPS**: bật.

## 4. Biến môi trường bản chính thức (5 phút)

Project `luatsunam` → **Settings** → **Variables and Secrets** (môi trường *Production*):

| Biến | Giá trị | Ghi chú |
|---|---|---|
| `SITE_URL` | `https://tenmien.vn` | không có `/` cuối. Đặt biến này là site chuyển từ bản thử sang bản chính thức (bỏ noindex) |
| `DRAFTS` | `1` | bản nháp chỉ xuất tại `/nhap/…` (chặn Google), không lộ ra menu, danh sách, sitemap |

Giữ nguyên `PYTHON_VERSION`, `CMS_OAUTH_URL`. **Không** đặt `BASE_PATH`, `NOINDEX` (build tự suy từ `SITE_URL`).
Sau đó **Deployments** → lượt mới nhất → **⋯** → **Retry deployment** (khoảng 2 phút).

Kiểm (tab ẩn danh):
- `https://tenmien.vn/` mở được site, có ổ khóa HTTPS; `https://www.tenmien.vn/` tự chuyển về `https://tenmien.vn/`.
- `https://tenmien.vn/robots.txt` có dòng `Sitemap: https://tenmien.vn/sitemap.xml`, **không** có dòng `Disallow: /` đứng riêng.

Chưa đạt thì dừng ở đây (github.io vẫn chạy bình thường), sửa xong mới sang bước 5.

## 5. Khóa /admin và /nhap/ (10 phút)

1. **Zero Trust** → **Access** → **Applications** → **Add an application** → **Self-hosted**.
2. *Application domain*: `tenmien.vn`, path `admin`; **Add domain** thêm `tenmien.vn`, path `nhap`.
3. Policy: *Action* **Allow**, *Include* → **Emails** = email quản trị + từng biên tập viên, người duyệt (gói Free tối đa 50 người).
4. Kiểm: mở `https://tenmien.vn/admin/` ở tab ẩn danh → phải hiện trang Cloudflare hỏi email, nhập email trong danh sách
   → nhận mã → vào được /admin.
5. (Nên làm) Đưa địa chỉ cũ của bản thử về tên miền để không còn cửa vào /admin, /nhap/ không khóa:
   **Bulk Redirects** → tạo danh sách: nguồn `luatsunam.pages.dev`, đích `https://tenmien.vn`, 301, bật *Preserve query string*,
   *Include subdomains*, *Subpath matching*, *Preserve path suffix* → tạo **Bulk Redirect Rule** dùng danh sách đó.

## 6. Đăng nhập CMS trên tên miền (3 phút)

1. Worker `luatsunam-cms-auth` → **Settings** → **Variables and Secrets** → `ALLOWED_DOMAINS`: thêm `, tenmien.vn` → **Deploy**.
2. GitHub OAuth App (<https://github.com/settings/developers>) → *Homepage URL* đổi thành `https://tenmien.vn/` (callback giữ nguyên).
3. Kiểm: `https://tenmien.vn/admin/` → **Đăng nhập bằng GitHub** → vào được, sửa thử 1 câu → Lưu → 1–3 phút sau thấy trên site.

## 7. Bật chuyển hướng từ github.io (2 phút)

1. GitHub repo → **Settings** → **Secrets and variables** → **Actions** → tab **Variables** → **New repository variable**:
   `CHUYEN_HUONG_TOI` = `https://tenmien.vn`.
2. **Actions** → **Build và đăng website (GitHub Pages)** → **Run workflow** (nhánh `main`).
3. 1–2 phút sau, mọi địa chỉ `willmichco.github.io/luatsunam/…` chuyển ngay tới đúng trang tương ứng trên tên miền
   (giữ cả `?utm_…` và `#mục`); đường dẫn đã đổi trong *Cài đặt → Chuyển hướng* đi thẳng tới trang mới. Mỗi lần lưu,
   workflow vẫn build để kiểm lỗi và gửi email khi lỗi như trước.

## 8. Google Search Console (10 phút)

1. **Add property** → loại **Domain** → `tenmien.vn` → xác minh bằng bản ghi TXT (Cloudflare → DNS → Add record → TXT).
2. Property mới → **Sitemaps** → gửi `https://tenmien.vn/sitemap.xml`.
3. Property cũ `https://willmichco.github.io/luatsunam/` → **Sitemaps** → gửi lại `https://willmichco.github.io/luatsunam/sitemap.xml`
   (giờ là danh sách URL cũ, giúp Google vào lại từng URL và thấy chuyển hướng sớm hơn). **Giữ property cũ ít nhất 12 tháng.**
4. Không dùng được công cụ *Thay đổi địa chỉ* (Change of Address): Google chỉ cho dùng với property cấp tên miền,
   còn `github.io/luatsunam` là property có thư mục con. Chuyển hướng từng URL + sitemap là đủ.
5. Property mới → **Kiểm tra URL** trang chủ và 3–5 trang quan trọng → **Yêu cầu lập chỉ mục**.

## 9. Kiểm G5 (5 phút)

1. GitHub → **Actions** → **Kiểm chuyển tên miền (G5)** → **Run workflow** (để trống ô tên miền) → mở lượt chạy:
   bảng **ĐẠT / CHƯA ĐẠT** cho tiêu chí 7, 8 (mọi URL github.io cũ chuyển đúng trang; mọi trang trên tên miền trả 200,
   canonical, og:url, sitemap đúng tên miền) kèm phần thông tin thêm: www, https, /admin và /nhap/ đã khóa.
   Chưa đạt: làm theo dòng lỗi, chờ 10 phút (GitHub Pages, Cloudflare còn giữ bản cũ) rồi chạy lại.
2. **Actions** → **Đo Lighthouse (site thật)** → **Run workflow** (để trống: tự đo trên tên miền) → so với mốc trong
   [NGHIEM-THU.md](NGHIEM-THU.md#lighthouse--mốc-so-sánh-cho-g5-chuyển-tên-miền): điểm không được thấp hơn.

## 10. Đổi địa chỉ ở nơi khác (tùy, 15 phút)

Google Business Profile, Facebook, Zalo OA, chữ ký email, danh thiếp, hồ sơ trên các danh bạ luật sư: đổi website sang `https://tenmien.vn`.
Liên kết trong nội dung site không cần sửa: build tự dùng địa chỉ mới.

## Quay lui khi có sự cố

| Sự cố | Cách xử lý |
|---|---|
| Lưu nội dung làm site trên tên miền lỗi | Cloudflare → `luatsunam` → **Deployments** → bản trước → **Rollback** (có hiệu lực ngay) |
| Tên miền chưa chạy ổn, cần trả khách về github.io | GitHub → Variables → xóa `CHUYEN_HUONG_TOI` → **Run workflow**: 1–2 phút sau github.io có lại site đầy đủ |
| Mất email theo tên miền sau khi đổi nameserver | Cloudflare → DNS: thêm lại bản ghi MX/TXT theo ảnh chụp bước 1 |

## Sau khi chuyển

- 2–4 tuần đầu: mỗi tuần xem Search Console – property cũ giảm dần số trang được lập chỉ mục, property mới tăng.
- Giữ trang chuyển hướng github.io **ít nhất 12 tháng**.
- GĐ6 (đưa mã nguồn sang private) chỉ làm sau khi bước 9 đạt.
