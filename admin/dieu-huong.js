/* Điều hướng trang quản trị (bổ sung cho Sveltia, không đổi dữ liệu):
   - Cột trái xếp theo đúng Menu chính của website (build sinh thứ tự mục trong config.yml và admin/cot-trai.json từ
     Cài đặt chung → Menu và chân trang): tiêu đề nhóm, mục thuộc một menu xổ thụt vào dưới tên menu xổ.
   - Mục chỉ có một trang (Trang chủ, Liên hệ…): bấm là mở thẳng trình soạn, không qua danh sách một dòng. Nút ← của trình soạn
     (và lần mở đầu tiên) vẫn về danh sách đó: dòng duy nhất hiện thành thẻ "Mở để sửa" (<html data-lsn-mot-tep>, CSS ở giao-dien.css).
   - Thanh trên cùng: Hướng dẫn, Lịch sử chỉnh sửa (mở tab mới, không mất phần đang soạn), Sáng / Tối (Sveltia giấu lựa chọn này
     trong Cài đặt của tài khoản). Khi đang soạn: Hướng dẫn + Sáng / Tối cạnh nút Lưu (Lịch sử của trang: admin/hoan-tac.js).
   - Tên trang trùng tên mục ("Trang chủ › Trang chủ"): đánh dấu để CSS chỉ hiện một lần.
   Dựa vào giao diện Sveltia 0.221.8 (data-label của mục, thanh công cụ trên cùng, h2 > bdi): nâng cấp Sveltia phải thử lại. */
(function () {
  'use strict';
  // Mặc định (khi chưa tải được cot-trai.json): đúng menu lúc dựng web. Tiêu đề chèn TRƯỚC mục có nhãn tương ứng.
  var HEADINGS = {
    'Trang chủ': ['Trang theo menu website', ''],
    'Bài viết pháp lý': ['Thư viện pháp lý', 'con'],
    'Trang tự tạo': ['Trang khác', ''],
    'Cài đặt chung': ['Dùng chung mọi trang', ''],
  };
  var INDENT = ['Bài viết pháp lý', 'Câu hỏi thường gặp'];
  // Mục một tệp → mở thẳng tệp đó
  var SINGLE = { 'Trang chủ': 'trang_chu/entries/trang-chu', 'Liên hệ': 'lien_he/entries/lien-he' };
  fetch(new URL('cot-trai.json', location.href).href, { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d) return;
      HEADINGS = {};
      (d.tieu_de || []).forEach(function (x) { HEADINGS[x[0]] = [x[1], x[2]]; });
      INDENT = d.thut || [];
      SINGLE = d.mot_tep || {};
      var nav = document.querySelector('nav.primary-sidebar');
      if (nav) [].forEach.call(nav.querySelectorAll('.lsn-nhom'), function (h) { h.remove(); });
      if (nav) [].forEach.call(nav.querySelectorAll('.lsn-con, .lsn-mot-tep'), function (x) { x.classList.remove('lsn-con', 'lsn-mot-tep'); });
      decorate();
    }).catch(function () { /* giữ mặc định */ });

  function decorate() {
    addButtons();
    markSingleList();
    markSameTitle();
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
  }

  document.addEventListener('click', function (e) {
    var item = e.target.closest && e.target.closest('nav.primary-sidebar [role=treeitem]');
    var to = item && SINGLE[item.getAttribute('data-label')];
    if (!to || e.ctrlKey || e.metaKey || e.shiftKey) return;
    e.preventDefault(); e.stopImmediatePropagation();
    location.hash = '#/collections/' + to;
  }, true);

  // Danh sách của mục một trang (#/collections/trang_chu): đánh dấu <html> để CSS vẽ dòng duy nhất thành thẻ "Mở để sửa"
  function markSingleList() {
    var m = location.hash.match(/^#\/collections\/([^/?#]+)\/?(?:[?#]|$)/), name = m && decodeURIComponent(m[1]);
    var on = !!name && Object.keys(SINGLE).some(function (k) { return SINGLE[k].split('/')[0] === name; });
    var root = document.documentElement;
    if (on !== root.hasAttribute('data-lsn-mot-tep')) { if (on) root.setAttribute('data-lsn-mot-tep', ''); else root.removeAttribute('data-lsn-mot-tep'); }
  }
  // Tiêu đề trình soạn "Trang chủ › Trang chủ" (tên mục = tên trang): CSS chỉ hiện một lần
  function markSameTitle() {
    [].forEach.call(document.querySelectorAll('[role=toolbar] h2'), function (h2) {
      var b = h2.querySelectorAll(':scope > .truncated-text > bdi');
      var same = b.length === 2 && b[0].textContent.trim() === b[1].textContent.trim();
      if (same !== h2.hasAttribute('data-lsn-trung')) { if (same) h2.setAttribute('data-lsn-trung', ''); else h2.removeAttribute('data-lsn-trung'); }
    });
  }

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
    var b = document.getElementById('lsn-sang-toi'), dark = theme() === 'dark', icon = dark ? 'light_mode' : 'dark_mode';
    if (!b || b.firstChild.textContent === icon) return; // không đổi thì không chạm DOM (tránh vòng lặp observer)
    b.firstChild.textContent = icon;
    b.title = dark ? 'Đang ở giao diện tối – bấm để chuyển sang sáng' : 'Đang ở giao diện sáng – bấm để chuyển sang tối';
    b.setAttribute('aria-label', dark ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối');
  }
  function visible(el) { return !!el && el.getClientRects().length > 0; }
  // Nút tài khoản ở thanh trên cùng: nhãn tiếng Việt / tiếng Anh, hoặc biểu tượng mặc định (khi chưa có ảnh đại diện)
  function accountButton() {
    return document.querySelector('[role=toolbar] button[aria-label="Hiển thị trình đơn tài khoản"], [role=toolbar] button[aria-label="Show Account Menu"]') ||
      [].filter.call(document.querySelectorAll('[role=toolbar] button[aria-haspopup=menu]'), function (x) {
        return /account_circle/.test(x.textContent);
      })[0] || null;
  }

  /* ---------- Nút chung trên thanh trên cùng: Hướng dẫn, Lịch sử chỉnh sửa, Sáng / Tối ---------- */
  function button(tag, id, icon, chu, title, cls) {
    var b = document.createElement(tag);
    b.id = id; b.className = 'lsn-nut' + (cls ? ' ' + cls : ''); b.title = title;
    if (tag === 'a') { b.target = '_blank'; b.rel = 'noopener'; } else b.type = 'button';
    b.innerHTML = '<span class="icon" aria-hidden="true">' + icon + '</span>' + (chu ? '<span class="chu">' + chu + '</span>' : '');
    if (!chu) b.setAttribute('aria-label', title);
    return b;
  }
  function addButtons() {
    // Đang soạn: thanh của trình soạn phủ lên màn danh sách (thanh trên cùng vẫn còn bên dưới) → đặt cạnh nút Lưu
    var save = document.querySelector('button[aria-keyshortcuts$="+S"]');
    var soan = !!save && /\/(entries|new)/.test(location.hash) && visible(save);
    var anchor = soan ? save : accountButton(), cuoi = null;
    if (soan && anchor.parentElement && /wrapper/.test(anchor.parentElement.className)) anchor = anchor.parentElement;
    if (!visible(anchor)) {
      // Màn hình điện thoại: Sveltia bỏ thanh trên cùng (không có nút tài khoản) → đặt cuối thanh tên mục, nếu có
      var bar = soan ? null : [].filter.call(document.querySelectorAll('[role=toolbar][aria-label="Chuyên mục"], [role=toolbar][aria-label="Collection"]'), visible)[0];
      if (!bar) return;
      cuoi = bar.querySelector(':scope > .inner') || bar;
    }
    var g = document.getElementById('lsn-nut-chung');
    if (!g) {
      g = document.createElement('div');
      g.id = 'lsn-nut-chung'; g.className = 'lsn-nhom-nut';
      g.appendChild(button('a', 'lsn-huong-dan', 'help', 'Hướng dẫn', 'Hướng dẫn sử dụng trang quản trị (mở tab mới)'));
      g.lastChild.href = 'huong-dan/';
      g.appendChild(button('a', 'lsn-lich-su-chung', 'history', 'Lịch sử chỉnh sửa', 'Lịch sử chỉnh sửa: xem các lần lưu, khôi phục bản cũ (mở tab mới)'));
      g.lastChild.href = 'lich-su.html';
      var t = button('button', 'lsn-sang-toi', '', '', 'Giao diện tối', 'lsn-nut--icon');
      t.addEventListener('click', function () { setTheme(theme() === 'dark' ? 'light' : 'dark'); });
      g.appendChild(t);
    }
    // Đang soạn: Hướng dẫn chỉ còn biểu tượng; Lịch sử chỉnh sửa nhường chỗ nút "Lịch sử" của đúng trang đang sửa (admin/hoan-tac.js)
    var hd = g.querySelector('#lsn-huong-dan'), ls = g.querySelector('#lsn-lich-su-chung');
    if (hd.classList.contains('lsn-nut--icon') !== soan) {
      hd.classList.toggle('lsn-nut--icon', soan);
      hd.setAttribute('aria-label', 'Hướng dẫn');
    }
    if (ls.hidden !== soan) ls.hidden = soan; // không đổi thì không chạm DOM (tránh vòng lặp observer)
    if (cuoi) { if (g.parentNode !== cuoi || g.nextElementSibling) cuoi.appendChild(g); }
    else if (g.nextElementSibling !== anchor) anchor.parentNode.insertBefore(g, anchor);
    paintThemeButton();
  }

  function schedule() {
    clearTimeout(decorate.t);
    decorate.t = setTimeout(decorate, 50);
  }
  window.addEventListener('hashchange', schedule);
  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  new MutationObserver(paintThemeButton).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
})();
