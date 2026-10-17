/* Hai chế độ soạn, tách hẳn (chỉ đổi cách hiện form, KHÔNG đổi dữ liệu – tệp lưu ra y hệt):
   - "Sửa chữ" (mặc định): chỉ ô chữ, ảnh, liên kết. Không có trường bố cục, không thêm / xóa / kéo đổi thứ tự khối
     (mục bên trong khối – thẻ, bước… – vẫn thêm, xóa được: đó là nội dung).
   - "Sửa bố cục": chỉ thêm / xóa / kéo đổi thứ tự khối và trường bố cục (ẩn/hiện, mã neo, màu nền, số cột, kiểu, vị trí ảnh…).
   Ô đang báo lỗi luôn hiện ở cả hai chế độ (không bao giờ giấu lỗi). Form không có trường bố cục (bài viết, cài đặt…): không có
   nút chuyển, hiện đủ. Bấm trên trang mô phỏng vào chỗ thuộc chế độ kia: tự chuyển chế độ (xem-truoc.js gọi LSN_HIEN_O).
   Trường nào là bố cục: đánh dấu bo_cuc() trong tools/schema.py → build ghi admin/bo-cuc.json (đường dẫn dạng
   data-typed-key-path của Sveltia). Chưa tải được tệp đó thì không giấu gì.
   KHÓA (17/10/2026, theo yêu cầu chủ site): mọi mục chỉ có "Sửa chữ" – không có nút chuyển, không vào được "Sửa bố cục"
   (không thêm / xóa / kéo khối, không đổi ẩn-hiện, màu nền, số cột…). Mục nào còn được chuyển chế độ: GIU_BO_CUC bên dưới
   (Bài viết pháp lý – hiện chưa có trường bố cục nên không có nút; giữ nguyên như cũ). Mở lại cho mục khác: thêm tên mục vào GIU_BO_CUC.
   Dựa vào giao diện Sveltia 0.221.8 (section.field[data-typed-key-path], .item-wrapper, .drag-handle): nâng cấp Sveltia phải thử lại. */
(function () {
  'use strict';
  var KEY = 'lsn-che-do';
  var GIU_BO_CUC = ['bai_viet']; // mục (collection) còn nút Sửa chữ / Sửa bố cục; mục khác luôn Sửa chữ
  var root = document.documentElement;
  var LAYOUT = [];
  var style = document.createElement('style');
  style.id = 'lsn-che-do-css';
  document.head.appendChild(style);

  function saved() {
    try { return localStorage.getItem(KEY) === 'bo-cuc' ? 'bo-cuc' : 'chu'; } catch (e) { return 'chu'; }
  }
  var mode = saved();
  function editing() { return /^#\/collections\/[^/]+\/(entries\/|new)/.test(location.hash); }
  function collection() { var m = location.hash.match(/^#\/collections\/([^/?#]+)/); return m ? decodeURIComponent(m[1]) : ''; }
  function locked() { return GIU_BO_CUC.indexOf(collection()) < 0; }
  function current() { return locked() ? 'chu' : mode; } // chế độ đang dùng cho form này
  function hasLayout() {
    return !!LAYOUT.length && !!document.querySelector('section.field[data-key-path="cac_khoi"], ' + LAYOUT.map(sel).join(','));
  }
  // Thuộc tính trên <html>: "chu" | "bo-cuc" khi form này có trường bố cục; bỏ đi (hiện đủ) với form khác
  function paintRoot() {
    var v = editing() && hasLayout() ? current() : null;
    if (root.getAttribute('data-lsn-che-do') !== v) {
      if (v) root.setAttribute('data-lsn-che-do', v); else root.removeAttribute('data-lsn-che-do');
    }
  }
  function setMode(m) {
    mode = m;
    try { localStorage.setItem(KEY, m); } catch (e) { /* trình duyệt chặn lưu trữ: chỉ đổi cho lần này */ }
    decorate();
  }

  function sel(p) { return 'section.field[data-typed-key-path="' + p.replace(/"/g, '\\"') + '"]'; }
  function under(p) { return 'section.field[data-typed-key-path^="' + p.replace(/"/g, '\\"') + '."]'; }
  function isLayout(typed) {
    return LAYOUT.some(function (p) { return typed === p || typed.indexOf(p + '.') === 0; });
  }
  function buildCss(paths) {
    LAYOUT = paths;
    if (!paths.length) { style.textContent = ''; return; }
    // Bố cục = trường bố cục + mọi ô bên trong nó; "khung" = nhóm chứa trường bố cục (cac_khoi, dau_trang…): hiện ở cả hai chế độ
    var layout = paths.map(sel).concat(paths.map(under)).join(',');
    var frames = {};
    paths.forEach(function (p) {
      var parts = p.replace(/\.\*(<[^>]*>)?/g, '').split('.');
      for (var i = 1; i < parts.length; i++) frames[parts.slice(0, i).join('.')] = 1;
    });
    var frame = Object.keys(frames).map(function (k) { return 'section.field[data-key-path="' + k + '"]'; }).join(',');
    var ok = ':not(:has(.validation))'; // ô (hoặc nhóm chứa ô) đang báo lỗi: luôn hiện
    var blocks = 'section.field[data-key-path="cac_khoi"]';
    var top = ':not(section.field[data-key-path^="cac_khoi."] *)'; // khối cấp 1, không phải mục danh sách bên trong khối
    var chu = ':root[data-lsn-che-do="chu"] ', bc = ':root[data-lsn-che-do="bo-cuc"] ';
    style.textContent =
      // Sửa chữ: giấu trường bố cục; giấu nút thêm / xóa / kéo khối
      chu + ':is(' + layout + ')' + ok + ' { display: none !important; }' +
      chu + blocks + ' .item-wrapper' + top + ' > .item > .header :is(.center, .end) { display: none !important; }' +
      chu + blocks + ' button.menu-button.tertiary' + top + ' { display: none !important; }' +
      // Sửa bố cục: giấu mọi ô không phải bố cục (trừ nhóm khung chứa trường bố cục)
      bc + 'section.field:not(:is(' + layout + (frame ? ',' + frame : '') + '))' + ok + ' { display: none !important; }';
  }
  fetch(new URL('bo-cuc.json', location.href).href, { cache: 'no-cache' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) { buildCss((d && d.o) || []); decorate(); })
    .catch(function () { /* không giấu gì */ });

  // Khung mô phỏng nhảy tới một ô đang bị giấu vì thuộc chế độ kia: chuyển chế độ (trả về true nếu đã chuyển)
  window.LSN_HIEN_O = function (el) {
    var f = el && el.closest && el.closest('section.field[data-typed-key-path]');
    if (!f || !root.hasAttribute('data-lsn-che-do') || locked()) return false; // đã khóa Sửa chữ: không tự chuyển
    var want = isLayout(f.getAttribute('data-typed-key-path')) ? 'bo-cuc' : 'chu';
    if (want === current()) return false;
    setMode(want);
    return true;
  };

  /* ---------- Nút chuyển chế độ trên thanh của trình soạn (cạnh nút Sáng / Tối, trước nút Lưu) ---------- */
  function placeSwitch() {
    var sw = document.getElementById('lsn-che-do');
    var save = document.querySelector('button[aria-keyshortcuts$="+S"]');
    if (!editing() || !save || !hasLayout() || locked()) { if (sw) sw.remove(); return; }
    var saveEl = save.parentElement && /wrapper/.test(save.parentElement.className) ? save.parentElement : save;
    var theme = document.getElementById('lsn-sang-toi');
    var anchor = theme && theme.parentNode === saveEl.parentNode ? theme : saveEl; // thứ tự: [chế độ][Sáng/Tối][Lưu]
    if (!sw) {
      sw = document.createElement('div');
      sw.id = 'lsn-che-do';
      sw.setAttribute('role', 'group');
      sw.setAttribute('aria-label', 'Chế độ soạn');
      [['chu', 'edit_note', 'Sửa chữ', 'Chỉ sửa chữ, ảnh, liên kết'],
        ['bo-cuc', 'dashboard', 'Sửa bố cục', 'Chỉ thêm, xóa, kéo đổi thứ tự khối; ẩn/hiện, màu nền, số cột, cách trình bày']].forEach(function (x) {
        var b = document.createElement('button');
        b.type = 'button';
        b.setAttribute('data-che-do', x[0]);
        b.title = x[3];
        b.innerHTML = '<span class="icon" aria-hidden="true">' + x[1] + '</span><span class="chu">' + x[2] + '</span>';
        b.addEventListener('click', function () { setMode(x[0]); });
        sw.appendChild(b);
      });
    }
    if (sw.nextElementSibling !== anchor) anchor.parentNode.insertBefore(sw, anchor);
    [].forEach.call(sw.children, function (b) {
      var on = String(b.getAttribute('data-che-do') === current());
      if (b.getAttribute('aria-pressed') !== on) b.setAttribute('aria-pressed', on); // không đổi thì không chạm DOM (tránh vòng lặp observer)
    });
  }

  function decorate() {
    paintRoot();
    placeSwitch();
  }
  function schedule() {
    clearTimeout(schedule.t);
    schedule.t = setTimeout(decorate, 60);
  }
  window.addEventListener('hashchange', schedule);
  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  decorate();
})();
