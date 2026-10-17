/* Trình bày form trong trình soạn (chỉ đổi cách hiện, KHÔNG đổi dữ liệu – tệp lưu ra y hệt):
   - Dòng tóm tắt của khối / thẻ đang thu gọn: Sveltia hiện nguyên chữ gõ ("Văn phòng luật do *{{luat_su}}* trực tiếp điều hành").
     Lớp này hiện như trên trang: phần *giữa hai dấu sao* tô đỏ, mã chèn {{…}} thay bằng chữ thật (build ghi admin/ma-chen.json từ
     Cài đặt chung › Thông tin công ty, lần Lưu gần nhất). Chữ gốc của Sveltia vẫn còn, chỉ giấu bằng CSS (admin/giao-dien.css).
   - Danh sách cấp 1 (Các khối trên trang…): số mục cạnh tên (data-lsn-dem), thay dòng "4 Các khối trên trang" đã giấu.
   Dựa vào giao diện Sveltia 0.221.8 (.summary > .truncated-text, section.field > .field-wrapper > .group > .inner > .item-list):
   nâng cấp Sveltia phải thử lại. */
(function () {
  'use strict';
  var MA = {};
  fetch(new URL('ma-chen.json', location.href).href, { cache: 'no-cache' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) { if (d) { MA = d; decorate(); } })
    .catch(function () { /* không có tệp: mã chèn hiện dạng ô nhỏ {{tên}} */ });

  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  // Cùng quy tắc với build (tools/markup.py: expand + title): mã chèn trước, rồi *…* thành chữ đỏ
  function pretty(text) {
    var s = esc(text).replace(/\{\{\s*([A-Za-z_]+)\s*\}\}/g, function (m, ten) {
      var v = MA[ten.toLowerCase()];
      return v ? esc(v) : '<span class="lsn-ma">' + m + '</span>';
    });
    return s.split('*').length % 2 ? s.replace(/\*(.+?)\*/g, '<em>$1</em>') : s;
  }

  function summaries() {
    [].forEach.call(document.querySelectorAll('section.field .summary > .truncated-text'), function (tt) {
      var raw = tt.textContent, sum = tt.parentElement, d = sum.querySelector(':scope > .lsn-tom-tat');
      if (!/\*|\{\{/.test(raw)) { if (d) d.remove(); return; } // chữ thường: để Sveltia hiện như cũ
      if (d && d.getAttribute('data-goc') === raw) return; // không đổi thì không chạm DOM (tránh vòng lặp observer)
      if (!d) {
        d = document.createElement('span');
        d.className = 'lsn-tom-tat';
        sum.appendChild(d); // cuối khung: sau mọi chỗ Sveltia tự chèn
      }
      d.setAttribute('data-goc', raw);
      d.title = raw;
      d.innerHTML = pretty(raw);
    });
  }

  function counts() {
    [].forEach.call(document.querySelectorAll('section.field[data-field-type="list"]:not([data-key-path*="."])'), function (f) {
      var h4 = f.querySelector(':scope > header > h4'), list = f.querySelector(':scope > .field-wrapper > .group > .inner > .item-list');
      if (!h4) return;
      var n = list ? [].filter.call(list.children, function (x) { return x.classList.contains('item-wrapper'); }).length : 0;
      var v = n ? String(n) : null;
      if (h4.getAttribute('data-lsn-dem') !== v) { if (v) h4.setAttribute('data-lsn-dem', v); else h4.removeAttribute('data-lsn-dem'); }
    });
  }

  function decorate() {
    summaries();
    counts();
  }
  new MutationObserver(function () {
    clearTimeout(decorate.t);
    decorate.t = setTimeout(decorate, 60);
  }).observe(document.documentElement, { childList: true, subtree: true, characterData: true });
})();
