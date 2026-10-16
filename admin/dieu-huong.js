/* Điều hướng trang quản trị (bổ sung cho Sveltia, không đổi dữ liệu):
   - Cột trái chia nhóm có tiêu đề, đúng thứ tự menu website; "Bài viết pháp lý" và "Câu hỏi thường gặp" thụt vào
     dưới nhãn "Thư viện pháp lý" như menu xổ trên site.
   - Mục chỉ có một trang (Trang chủ, Liên hệ): bấm là mở thẳng trình soạn, không qua danh sách một dòng.
   - Nút Sáng / Tối luôn thấy ở thanh trên cùng (Sveltia giấu lựa chọn này trong Cài đặt của tài khoản).
   Dựa vào giao diện Sveltia 0.221.8 (data-label của mục, thanh công cụ "Dùng chung"): nâng cấp Sveltia phải thử lại. */
(function () {
  'use strict';
  // Tiêu đề chèn TRƯỚC mục có nhãn tương ứng (nhãn = label trong admin/config.yml)
  var HEADINGS = {
    'Trang chủ': ['Trang theo menu website', ''],
    'Bài viết pháp lý': ['Thư viện pháp lý', 'con'],
    'Trang tự tạo': ['Trang ngoài menu', ''],
    'Cài đặt chung': ['Dùng chung mọi trang', ''],
  };
  var INDENT = ['Bài viết pháp lý', 'Câu hỏi thường gặp'];
  // Mục một tệp → mở thẳng tệp đó
  var SINGLE = { 'Trang chủ': 'trang_chu/entries/trang-chu', 'Liên hệ': 'lien_he/entries/lien-he' };

  function decorate() {
    var nav = document.querySelector('nav.primary-sidebar');
    if (!nav) return;
    Object.keys(HEADINGS).forEach(function (label) {
      var item = nav.querySelector('[role=treeitem][data-label="' + label + '"]');
      if (!item || (item.previousElementSibling && item.previousElementSibling.classList.contains('lsn-nhom'))) return;
      var h = document.createElement('div');
      h.className = 'lsn-nhom' + (HEADINGS[label][1] ? ' lsn-nhom-con' : '');
      h.setAttribute('aria-hidden', 'true');
      h.textContent = HEADINGS[label][0];
      item.parentNode.insertBefore(h, item);
    });
    INDENT.forEach(function (label) {
      var item = nav.querySelector('[role=treeitem][data-label="' + label + '"]');
      if (item) item.classList.add('lsn-con');
    });
    Object.keys(SINGLE).forEach(function (label) {
      var item = nav.querySelector('[role=treeitem][data-label="' + label + '"]');
      if (item) item.classList.add('lsn-mot-tep');
    });
    addThemeButton();
  }

  document.addEventListener('click', function (e) {
    var item = e.target.closest && e.target.closest('nav.primary-sidebar [role=treeitem]');
    var to = item && SINGLE[item.getAttribute('data-label')];
    if (!to || e.ctrlKey || e.metaKey || e.shiftKey) return;
    e.preventDefault(); e.stopImmediatePropagation();
    location.hash = '#/collections/' + to;
  }, true);

  /* ---------- Sáng / Tối ----------
     Sveltia đặt <html data-theme> theo lựa chọn lưu ở localStorage "sveltia-cms.prefs" (theme: auto | light | dark).
     Nút này đổi ngay giao diện và ghi lựa chọn vào đó, nên lần sau mở vẫn giữ. */
  var PREFS = 'sveltia-cms.prefs';
  function theme() { return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light'; }
  function setTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    document.documentElement.setAttribute('data-auto-theming', 'false');
    try {
      var p = JSON.parse(localStorage.getItem(PREFS) || '{}') || {};
      p.theme = t;
      localStorage.setItem(PREFS, JSON.stringify(p));
    } catch (e) { /* trình duyệt chặn lưu trữ: chỉ đổi cho lần này */ }
    paintThemeButton();
  }
  function paintThemeButton() {
    var b = document.getElementById('lsn-sang-toi');
    if (!b) return;
    var dark = theme() === 'dark';
    b.querySelector('.icon').textContent = dark ? 'light_mode' : 'dark_mode';
    b.querySelector('.chu').textContent = dark ? 'Sáng' : 'Tối';
    b.title = dark ? 'Đang ở giao diện tối – bấm để chuyển sang sáng' : 'Đang ở giao diện sáng – bấm để chuyển sang tối';
    b.setAttribute('aria-pressed', dark ? 'true' : 'false');
  }
  function visible(el) { return !!el && el.getClientRects().length > 0; }
  // Nút tài khoản ở thanh trên cùng: nhận theo tên biểu tượng (không đổi theo ngôn ngữ giao diện)
  function accountButton() {
    return document.querySelector('[role=toolbar] button[aria-label="Hiển thị trình đơn tài khoản"]') ||
      [].filter.call(document.querySelectorAll('[role=toolbar] button[aria-haspopup=menu]'), function (x) {
        return /account_circle/.test(x.textContent);
      })[0] || null;
  }
  function addThemeButton() {
    // Thanh trên cùng ở màn danh sách (trước nút tài khoản), hoặc thanh của trình soạn (trước nút Lưu)
    var save = document.querySelector('button[aria-keyshortcuts$="+S"]');
    // Đang soạn: thanh của trình soạn phủ lên màn danh sách (thanh trên cùng vẫn còn bên dưới) → ưu tiên cạnh nút Lưu
    var anchor = [save && /\/(entries|new)/.test(location.hash) ? save : null, accountButton()].filter(visible)[0];
    var b = document.getElementById('lsn-sang-toi');
    if (anchor === save && anchor.parentElement && /wrapper/.test(anchor.parentElement.className)) anchor = anchor.parentElement;
    if (!anchor || (b && b.nextElementSibling === anchor)) return;
    if (!b) {
      b = document.createElement('button');
      b.type = 'button'; b.id = 'lsn-sang-toi';
      b.setAttribute('aria-label', 'Giao diện tối');
      b.innerHTML = '<span class="icon material-symbols-outlined" aria-hidden="true"></span><span class="chu"></span>';
      b.addEventListener('click', function () { setTheme(theme() === 'dark' ? 'light' : 'dark'); });
    }
    anchor.parentNode.insertBefore(b, anchor);
    paintThemeButton();
  }

  new MutationObserver(function () {
    clearTimeout(decorate.t);
    decorate.t = setTimeout(decorate, 50);
  }).observe(document.documentElement, { childList: true, subtree: true });
  new MutationObserver(paintThemeButton).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
})();
