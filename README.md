# Công Ty Luật TNHH Luật Sư Nam – website + CMS

Website tĩnh, nội dung sửa trong trang quản trị **/admin** (Sveltia CMS), build bằng Python, đăng lên GitHub Pages.

- Site chính thức: <https://willmichco.github.io/luatsunam/>
- Trang quản trị: <https://willmichco.github.io/luatsunam/admin/>
- Hướng dẫn có ảnh chụp: <https://willmichco.github.io/luatsunam/admin/huong-dan/> (nguồn: [docs/huong-dan/README.md](docs/huong-dan/README.md))
- Kết quả nghiệm thu GĐ4: [docs/NGHIEM-THU.md](docs/NGHIEM-THU.md)
- Triển khai bản thử Cloudflare + đăng nhập GitHub: [docs/TRIEN-KHAI-CLOUDFLARE.md](docs/TRIEN-KHAI-CLOUDFLARE.md)
- Chuyển sang tên miền riêng (GĐ5, code đã sẵn): [docs/CHUYEN-TEN-MIEN.md](docs/CHUYEN-TEN-MIEN.md)

## Cách hoạt động

```
/admin (Sveltia CMS) ──Lưu──▶ commit vào content/ (nhánh main)
                                   │
                    GitHub Actions: tools/build.py → tools/kiem_tra.py
                                   │                     │
                         đạt ──▶ đăng dist/ lên gh-pages   lỗi ──▶ KHÔNG đăng, site giữ bản cũ,
                                 (lên site sau 1–3 phút)          mở issue "Build lỗi" → email quản trị
```

**Schema là nguồn duy nhất** (`tools/schema.py`): mỗi lần build sinh cùng lúc HTML và `admin/config.yml`,
nên CMS không thể lệch cấu trúc site. Thêm 1 trường vào schema → CMS tự có trường đó ở lần build sau.

## Cấu trúc

| Đường dẫn | Nội dung |
|---|---|
| `content/cai-dat/` | Thông tin công ty, menu + chân trang, câu chữ dùng chung, SEO, mã theo dõi, chuyển hướng 301, ảnh thương hiệu |
| `content/trang/*.yml` | Trang ghép từ khối: Trang chủ, Giới thiệu, Vì sao chọn chúng tôi, Quy trình, Liên hệ (mỗi trang một mục riêng trong CMS, luôn đăng), mọi trang tự tạo |
| `content/dich-vu/_index.yml`, `content/bai-viet/_index.yml`, `content/trang-tong-hop/cau-hoi-thuong-gap.yml` | Trang tổng quan Dịch vụ, Bài viết pháp lý, Câu hỏi thường gặp (danh sách bên dưới tự động). Hai tệp `_index` nằm trong thư mục của mục đó nên CMS hiện chúng ở dòng đầu danh sách. `content/dich-vu/_index.yml` › `luoi.the` = chữ + thứ tự các thẻ lưới lĩnh vực, dùng chung cho Trang chủ, trang Dịch vụ, trang Kiến thức pháp lý |
| `content/trang-van-ban/` | Chính sách bảo mật, Điều khoản, Miễn trừ trách nhiệm (Markdown), trang 404 |
| `content/dich-vu/*.yml` | 7 lĩnh vực dịch vụ |
| `content/bai-viet/*.md` | Bài viết (Markdown + thông tin đầu tệp). **Bố cục cố định** (`build.article_page`): tiêu đề → sapo → ảnh đại diện → tóm tắt nhanh → mục lục → nội dung H2/H3 → căn cứ pháp lý → hỏi đáp nhanh → luật sư tham vấn → lưu ý. Dữ liệu cho Google: `Article` (kèm `citation`), `WebPage.reviewedBy` = luật sư; build cảnh báo khi bài < 2 mục H2, H3 trước H2, < 500 từ |
| `content/hoi-dap.yml` | Kho hỏi đáp chung |
| `content/anh-thuong-hieu/` | Ảnh gốc: logo, luật sư tại văn phòng, tại phiên tòa (build tự cắt favicon, ảnh thẻ, ảnh chia sẻ) |
| `assets/uploads/` | Ảnh tải lên qua CMS (tự đổi WebP khi tải lên; build sinh thêm bản 480/960/1600) |
| `assets/css/style.css`, `assets/js/main.js`, `assets/fonts/` | Giao diện – chỉ sửa bằng code. Build rút gọn `style.css` và **nhúng thẳng vào `<head>` mỗi trang** (không chờ tải CSS riêng); mỗi trang có quy tắc tải trước trang khi rê chuột/chạm liên kết và hiệu ứng chuyển trang mờ dần |
| `admin/index.html` | Trang quản trị: Sveltia CMS khóa phiên bản 0.221.8, giao diện luôn tiếng Việt (kể cả trình duyệt để tiếng Anh), thành phần “Ảnh” (bắt buộc mô tả) và “Bảng”, ô `lsn_nhom` (tiêu đề phần, ghi chú “chữ này sửa ở đâu” có nút mở thẳng chỗ sửa – chỉ để nhìn, không ghi gì vào tệp), chống mất bài đang soạn, ô con thu gọn (khối, thẻ, nhóm) bấm bất kỳ đâu trên hàng tiêu đề hoặc dòng tóm tắt là mở |
| `admin/giao-dien.css` | Giao diện chung của `/admin` và trang Lịch sử chỉnh sửa – **một nguồn** cho màu (biến `--lsn-*` lấy theo bảng màu Sveltia, tông đỏ thương hiệu), phông Be Vietnam Pro, bo góc, kiểu nút trên thanh công cụ (cùng cỡ nút của Sveltia), cột trái, ghi chú vàng, thẻ “Mở để sửa” cho từng trang/bài trong danh sách của mọi mục (mục nhiều bài giữ ô chọn để xóa nhiều). **Trình soạn:** thanh “Chỉnh sửa” và thanh khung mô phỏng thẳng một hàng (bỏ thanh “Xem trước” của Sveltia); form là một cột thẻ trắng trên nền xám – ô đơn = thẻ gọn, phần (nhóm/danh sách cấp 1) = thanh tiêu đề có số khớp mô phỏng hoặc biểu tượng, gợi ý ngay dưới tên, bấm thanh để mở/thu (bỏ thanh mũi tên xám của Sveltia); khối = thẻ “LOẠI KHỐI + tiêu đề thật + Mở để sửa ›”; tiêu đề phần (`lsn_nhom`) = đề mục gạch chân đỏ; trạng thái đồng bộ `data-lsn-dang-sua` / `data-lsn-tro` / `data-lsn-ngoai`. Thêm nút/khung mới: dùng biến và lớp có sẵn ở đây thay vì ghi mã màu riêng |
| `admin/xem-truoc.js`, `admin/xem-truoc-worker.js` | Khung mô phỏng trong /admin: dựng trang bằng chính code build (Python chạy trong trình duyệt qua Pyodide 0.29.5 từ jsDelivr), đóng khung đỏ chỗ đang sửa, danh sách “Các phần” của trang (số khớp trên trang và trong form – đánh lại khi Sveltia dựng thêm khối; khung hẹp: danh sách chỉ nổi lên khi bấm), bấm trên mô phỏng → nhảy tới ô; đồng bộ hai chiều với form: khối đang có khung đỏ → thẻ trong form viền đỏ, rê chuột trên mô phỏng → thẻ trong form viền nét đứt, phần cấp 1 không có trên trang → nhãn “Không hiện trên trang này”; thẻ lấy chữ từ tệp khác (thẻ lĩnh vực, bài viết, câu hỏi) → mở đúng tệp, đúng ô; máy tính/điện thoại, mẫu kết quả Google, báo lỗi trước khi Lưu |
| `admin/dieu-huong.js` | Cột trái theo menu website: thứ tự mục do build sinh từ Menu chính (`schema.sidebar_plan`), tiêu đề nhóm / mục thụt vào / mục một trang đọc từ `/admin/cot-trai.json` (build sinh); thanh trên cùng có **Hướng dẫn**, **Lịch sử chỉnh sửa**, nút Tối/Sáng (khi đang soạn: cạnh nút Lưu); tiêu đề trùng “Trang chủ › Trang chủ” chỉ hiện một lần |
| `admin/bieu-mau.js` | Trình bày form: dòng tóm tắt của khối/thẻ thu gọn hiện như trên trang (`*…*` chữ đỏ, mã chèn `{{luat_su}}`… thay bằng chữ thật từ `/admin/ma-chen.json` – build ghi từ Thông tin công ty); số mục cạnh tên danh sách cấp 1. Chữ gốc của Sveltia chỉ giấu bằng CSS, không đổi dữ liệu |
| `admin/bieu-tuong.js` | Ô chọn **Biểu tượng** (lĩnh vực, thẻ, cam kết…): hiện hình biểu tượng cạnh tên, cả khi xổ danh sách lẫn ô đã chọn. Hình lấy từ bộ biểu tượng của site (`tools/sprite.py` + `schema.ICONS`), build ghi `/admin/bieu-tuong.json` |
| `admin/hoan-tac.js` | Hoàn tác trong trình soạn: ô vừa sửa (chưa Lưu) có nút **↶ Hoàn tác** (= lệnh *Hoàn tác thay đổi* trong menu ⋮ của ô, Sveltia tự làm), thanh trên cùng có **Hoàn tác tất cả** và **Lịch sử** (mở lịch sử đúng trang đang sửa). Chỉ thêm nút, không tự ghi dữ liệu |
| `admin/lich-su.html`, `admin/lich-su.js` | Trang **Lịch sử chỉnh sửa** (`/admin/lich-su.html`): mỗi commit vào `content/` = một lần Lưu; so từng ô theo nhãn trong `config.yml` (khối/thẻ khớp theo nội dung nên dời chỗ, xóa không làm lệch cả danh sách); **khôi phục** = một commit mới đưa tệp về bản trước lần lưu đó (Git Data API, không force-push). Dùng token GitHub của /admin trong cùng trình duyệt; js-yaml 4.1.0 từ unpkg |
| `admin/che-do.js` | Chế độ soạn. **Từ 17/10/2026 mọi mục khóa ở Sửa chữ** (chỉ ô chữ, ảnh, liên kết; không thêm/xóa/kéo khối, giấu trường bố cục, không có nút chuyển); chỉ mục trong `GIU_BO_CUC` (hiện: trống – kể cả Bài viết) còn hai chế độ Sửa chữ / Sửa bố cục. Hệ quả: Trang tự tạo (khối ≥ 1) không tạo mới được trong CMS → mục **Trang tự tạo ẩn khỏi cột trái** (`HIEN_TRANG_TU_TAO = False` trong `tools/schema.py`; build vẫn dựng và kiểm trang tự tạo có sẵn). Ô lỗi luôn hiện. Trường bố cục đánh dấu `bo_cuc()` trong `tools/schema.py`, build ghi `/admin/bo-cuc.json`. Chỉ đổi cách hiện form, không đổi dữ liệu |
| `tools/xem_truoc.py`, `tools/goi_xem_truoc.py` | Phần Python của khung mô phỏng; build đóng gói `tools/` + `content/` + thư viện vào `/admin/xem-truoc/goi.zip` (~280 KB) |
| `docs/huong-dan/` | Hướng dẫn sử dụng có ảnh chụp; build dựng thành `/admin/huong-dan/` (`tools/huong_dan.py`) |
| `tools/schema.py` | Khai báo mọi trường: nhãn, gợi ý, giới hạn, quy tắc kiểm; 15 khối dựng trang. `data_collections()` = dữ liệu build đọc và kiểm; `collections()` = cách xếp mục trong CMS, tự theo Menu chính trong `content/cai-dat/menu.yml` (cùng tệp, cùng trường). `nhom()` / `ghi_chu()` = tiêu đề phần, ghi chú trong form; `pick_list()` = chọn nhiều mục có thứ tự (kéo-thả) |
| `tools/build.py` | Build: đọc `content/`, kiểm, dựng trang, ảnh, sitemap, `_redirects`, `_headers`, `/admin/config.yml` |
| `tools/blocks.py`, `tools/tpl.py` | Template các khối và thành phần dùng chung |
| `tools/content.py`, `tools/markup.py`, `tools/loi.py` | Nạp + kiểm nội dung, Markdown/mã chèn/liên kết, báo lỗi tiếng Việt |
| `tools/images.py` | Ảnh thương hiệu, ảnh chia sẻ tự sinh, ảnh tải lên (lưu đệm `.cache/`) |
| `tools/kiem_tra.py` | Kiểm sau build: canonical, og:url, sitemap, robots, liên kết, mã neo, cột trái trang quản trị đúng thứ tự Menu chính |
| `tools/chuyen_huong.py` | GĐ5: dựng bản chuyển hướng github.io → tên miền (mỗi URL cũ 1 trang, 404 bắt đường dẫn lạ) |
| `tools/kiem_g5.py`, `docs/g5/` | GĐ5: kiểm tiêu chí 7, 8 trên site thật; mốc URL github.io trước khi chuyển |
| `cloudflare/oauth-worker/` | Worker đăng nhập GitHub cho /admin |

Các tệp HTML, `sitemap.xml`, ảnh trong `assets/img/` do build sinh vào `dist/`, **không sửa tay**.
Workflow đăng `dist/` lên nhánh `gh-pages`, nơi GitHub Pages đọc (Settings → Pages → *Deploy from a branch* → `gh-pages`, từ 16/10/2026);
`main` chỉ chứa mã nguồn. Nếu Pages bị đổi về đọc gốc `main`, workflow chép thêm bản build vào gốc `main` (danh sách tệp: `.ban-build.txt`)
và tự gỡ khi Pages đọc lại `gh-pages`. Chọn nhầm *Source: GitHub Actions* thì workflow báo lỗi qua issue/email.

## Chạy trên máy

```bash
pip install -r requirements.txt
python3 tools/build.py                 # bản chính thức → dist/
python3 tools/kiem_tra.py              # kiểm sau build
python3 -m http.server 8000 --directory dist   # xem tại http://localhost:8000
```

Biến môi trường của build:

| Biến | Mặc định | Dùng khi |
|---|---|---|
| `SITE_URL` | `https://willmichco.github.io/luatsunam` | Đổi sang tên miền riêng (GĐ5) |
| `BASE_PATH` | phần đường dẫn của `SITE_URL` | Gần như không cần đặt: github.io → `/luatsunam/`, tên miền riêng → `/` |
| `DRAFTS=1` | tắt | Xuất cả bản nháp. Bản thử (kèm `NOINDEX=1`): nháp dựng như đã đăng, `/nhap/<đường-dẫn>/` chuyển tới. Bản chính thức trên tên miền: nháp **chỉ** dựng dưới `/nhap/` (noindex), không lộ ra menu, danh sách, sitemap |
| `NOINDEX=1` | tắt | Bản thử: chặn Google toàn bộ |
| `CMS_OAUTH_URL` | trống | Địa chỉ Worker đăng nhập; trống = /admin chỉ đăng nhập bằng mã truy cập |

Trên Cloudflare Pages (có biến `CF_PAGES`) mà chưa đặt `SITE_URL`, build tự chạy chế độ bản thử (nháp + noindex).

## Rào chắn nhập liệu (đã cài)

- Mỗi trường có nhãn, gợi ý, ví dụ tiếng Việt; tiêu đề SEO 15–60 ký tự (tiêu đề đầy đủ ≥ 30), mô tả SEO 70–160, có bộ đếm.
- Đường dẫn tự tạo từ tiêu đề, bỏ dấu, khóa sau khi lưu; build chặn đường dẫn sai dạng hoặc trùng trang cố định.
- Ô chữ không nhận HTML; tô đỏ tiêu đề bằng `*dấu sao*`; mã chèn `{{hotline}}`, `{{luat_su}}`… tự cập nhật khi đổi thông tin công ty.
- Liên kết nội bộ, mã neo, chuyển hướng (đích có thật, không vòng lặp) đều được build kiểm.
- Bài viết, trang, lĩnh vực mới mặc định là **bản nháp**. Lỗi trong bản nháp **không chặn** site chính thức (chỉ cảnh báo); bản thử vẫn chặn để luật sư xem nháp đúng như khi đăng.
- Bài viết có ô **Đường dẫn** riêng (2–8 từ, khóa sau khi lưu; build bắt lỗi nếu ô bị sửa lệch tên tệp).
- Ảnh trong bài: **bắt buộc mô tả ảnh** (CMS không cho lưu khi thiếu), có chú thích dưới ảnh; build sinh bản 480/960/1600 cho điện thoại. Tắt kho ảnh stock.
- Chọn lĩnh vực bằng danh sách chọn (không còn nút “Thêm lĩnh vực” dễ bấm nhầm tạo lĩnh vực mới). Chọn nhiều mục có thứ tự (nhóm lĩnh vực trên menu, lĩnh vực liên quan, câu hỏi trong khối Hỏi đáp, giấy tờ theo lĩnh vực, thứ tự chân trang) là **danh sách kéo-thả**: thấy được thứ tự, không còn kiểu “thứ tự = thứ tự tích”. Chọn trùng → báo lỗi.
- Chữ dùng ở nhiều trang chỉ sửa **một chỗ**, form ghi rõ chỗ đó: thẻ lưới lĩnh vực (Trang tổng quan Dịch vụ › Khối lưới lĩnh vực), câu hỏi (Kho câu hỏi), tiêu đề mục trang lĩnh vực (Câu chữ dùng chung), thông tin công ty. Lĩnh vực chưa có thẻ → thẻ tạm + cảnh báo.
- Kiểm logic menu mỗi lần build và ngay trong khung mô phỏng (cảnh báo, không chặn): trang nằm ở 2 mục menu, lĩnh vực ở 2 nhóm hoặc chưa xếp nhóm, menu trỏ tới bản nháp, thẻ/thứ tự trỏ tới lĩnh vực đã xóa. Trang tự tạo không có trên menu nhưng có “Nằm trong mục” → menu tô sáng mục cha.
- Hotline/email gõ thẳng vào nội dung → build báo lỗi, yêu cầu dùng `{{hotline}}`/`{{email}}`; mô tả SEO dùng được mã chèn.
- Chống mất bài đang soạn: Esc, nút ←, đóng tab khi còn thay đổi chưa lưu đều được hỏi lại.
- Mã theo dõi (GA4, Meta Pixel, Zalo OA) chỉ xuất ra site khi đã tích “Đã cập nhật Chính sách bảo mật và thông báo cookie” (Nghị định 13/2023).
- Build lỗi: liệt kê **mọi** lỗi một lần, kèm tệp + tên trường như trong CMS; không ghi `dist/`.
- Khung mô phỏng hiện cùng danh sách lỗi đó **trước khi Lưu** (chỉ cảnh báo, không chặn Lưu). Mô phỏng thêm thuộc tính `data-cms` chỉ trong trình duyệt; HTML xuất ra site không đổi.

> ⚖️ Không thêm cụm cam kết kết quả (“cam kết thắng kiện”…) và không đăng số liệu chưa kiểm chứng (Quy tắc 9.1.6 Bộ Quy tắc Đạo đức và Ứng xử nghề nghiệp luật sư Việt Nam). Bài có dẫn điều luật phải được luật sư duyệt trước khi bỏ dấu nháp.
