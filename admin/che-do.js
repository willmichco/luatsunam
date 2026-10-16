/* Hai chế độ soạn (chỉ đổi cách hiện form, KHÔNG đổi dữ liệu – tệp lưu ra y hệt):
   - "Sửa chữ" (mặc định): mỗi khối chỉ hiện ô chữ, ảnh, liên kết. Trường bố cục (ẩn/hiện, mã neo, màu nền, số cột, kiểu,
     vị trí ảnh…) gom vào dòng "⚙ Cài đặt khối" thu gọn của từng khối; không có nút thêm / xóa / kéo đổi thứ tự khối.
   - "Sửa bố cục": hiện đủ như trước. Trường bố cục có vạch vàng bên trái để dễ nhận ra.
   Trường nào là bố cục: đánh dấu bo_cuc() trong tools/schema.py → build ghi admin/bo-cuc.json (đường dẫn dạng
   data-typed-key-path của Sveltia). Chưa tải được tệp đó thì không giấu gì. Ô bố cục đang báo lỗi luôn hiện.
   Dựa vào giao diện Sveltia 0.221.8 (section.field[data-typed-key-path], .item-wrapper, .drag-handle): nâng cấp Sveltia phải thử lại. */
(function () {
  'use strict';
  var KEY = 'lsn-che-do';
  var root = document.documentElement;
  var SET = {};
  var opened = typeof WeakSet === 'function' ? new WeakSet() : null; // khối đang mở "Cài đặt khối"
  var style = document.createElement('style');
  style.id = 'lsn-che-do-css';
  document.head.appendChild(style);

  function saved() {
    try { return localStorage.getItem(KEY) === 'bo-cuc' ? 'bo-cuc' : 'chu'; } catch (e) { return 'chu'; }
  }
  var mode = saved();
  function isNew(h) { return /^#\/collections\/[^/]+\/new(\?|$)/.test(h); }
  function editing() { return /^#\/collections\/[^/]+\/(entries\/|new)/.test(location.hash); }
  // Tạo trang / khối mới cần thêm khối: mở ở Sửa bố cục (không ghi nhớ); rời trang mới thì về lựa chọn đã lưu
  var lastHash = '';
  function onRoute() {
    var h = location.hash;
    if (isNew(h) && !isNew(lastHash)) mode = 'bo-cuc';
    else if (!isNew(h) && isNew(lastHash)) mode = saved();
    lastHash = h;
    root.setAttribute('data-lsn-che-do', mode);
    schedule();
  }
  function setMode(m) {
    mode = m;
    try { localStorage.setItem(KEY, m); } catch (e) { /* trình duyệt chặn lưu trữ: chỉ đổi cho lần này */ }
    root.setAttribute('data-lsn-che-do', m);
    decorate();
  }

  function buildCss(paths) {
    SET = {};
    paths.forEach(function (p) { SET[p] = 1; });
    if (!paths.length) { style.textContent = ''; return; }
    var sel = paths.map(function (p) { return 'section.field[data-typed-key-path="' + p.replace(/"/g, '\\"') + '"]'; }).join(',');
    var chu = ':root[data-lsn-che-do="chu"] ';
    var blocks = 'section.field[data-key-path="cac_khoi"]';
    var top = ':not(section.field[data-key-path^="cac_khoi."] *)'; // khối cấp 1, không phải mục danh sách bên trong khối
    style.textContent =
      // Sửa chữ: giấu trường bố cục, trừ khi khối đó đang mở "Cài đặt khối" hoặc ô đang báo lỗi
      chu + ':is(' + sel + '):not(:has(> .validation)):not(.lsn-mo-cai-dat *) { display: none !important; }' +
      // Sửa chữ: không thêm / xóa / kéo đổi thứ tự khối (mục bên trong khối – thẻ, bước… – vẫn thêm, xóa được)
      chu + blocks + ' .item-wrapper' + top + ' > .item > .header :is(.center, .end) { display: none !important; }' +
      chu + blocks + ' button.menu-button.tertiary' + top + ' { display: none !important; }' +
      // Trường bố cục đang hiện: vạch vàng bên trái
      ':is(' + sel + ') { box-shadow: inset 3px 0 0 var(--lsn-bo-cuc, #c58a00); }';
  }
  fetch(new URL('bo-cuc.json', location.href).href, { cache: 'no-cache' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) { buildCss((d && d.o) || []); decorate(); })
    .catch(function () { /* không giấu gì */ });

  /* ---------- Dòng "⚙ Cài đặt khối" trong từng khối (chế độ Sửa chữ) ---------- */
  function setText(el, t) { if (el.textContent !== t) el.textContent = t; } // không đổi thì không chạm DOM (tránh vòng lặp observer)
  function makeToggle() {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'lsn-cai-dat';
    b.innerHTML = '<span class="lsn-cai-dat__icon" aria-hidden="true">settings</span><span class="lsn-cai-dat__chu"></span>' +
      '<span class="lsn-cai-dat__phu"></span><span class="lsn-cai-dat__mui" aria-hidden="true"></span>';
    b.addEventListener('click', function () {
      var w = b.closest('.item-wrapper');
      if (!w) return;
      var on = !w.classList.contains('lsn-mo-cai-dat');
      w.classList.toggle('lsn-mo-cai-dat', on);
      if (opened) { if (on) opened.add(w); else opened.delete(w); }
      paintToggle(b, w);
    });
    return b;
  }
  function blockHidden(i) {
    var sw = document.querySelector('section.field[data-key-path="cac_khoi.' + i + '.hien_thi"] [role=switch]');
    return !!sw && sw.getAttribute('aria-checked') === 'false';
  }
  function paintToggle(b, w) {
    var on = w.classList.contains('lsn-mo-cai-dat'), i = b.getAttribute('data-khoi');
    setText(b.querySelector('.lsn-cai-dat__chu'), 'Cài đặt khối');
    setText(b.querySelector('.lsn-cai-dat__phu'), (blockHidden(i) ? 'ĐANG ẨN · ' : '') + 'hiện/ẩn, mã neo, màu nền, cách trình bày');
    setText(b.querySelector('.lsn-cai-dat__mui'), on ? 'expand_less' : 'expand_more');
    if (b.getAttribute('aria-expanded') !== String(on)) b.setAttribute('aria-expanded', String(on));
    b.classList.toggle('lsn-cai-dat--an', blockHidden(i));
  }
  function decorateBlocks() {
    var list = document.querySelector('section.field[data-key-path="cac_khoi"]');
    if (!list) return;
    var first = {};
    [].forEach.call(list.querySelectorAll('section.field[data-typed-key-path]'), function (sec) {
      if (!SET[sec.getAttribute('data-typed-key-path')]) return;
      var m = /^cac_khoi\.(\d+)\.[^.]+$/.exec(sec.getAttribute('data-key-path') || '');
      if (m && !first[m[1]]) first[m[1]] = sec;
    });
    var keep = [];
    Object.keys(first).forEach(function (i) {
      var sec = first[i], w = sec.closest('.item-wrapper');
      if (!w) return;
      if (opened && opened.has(w) && !w.classList.contains('lsn-mo-cai-dat')) w.classList.add('lsn-mo-cai-dat');
      var b = sec.previousElementSibling;
      if (!b || !b.classList.contains('lsn-cai-dat')) { b = makeToggle(); sec.parentNode.insertBefore(b, sec); }
      if (b.getAttribute('data-khoi') !== i) b.setAttribute('data-khoi', i);
      paintToggle(b, w);
      keep.push(b);
    });
    // Nút cũ (khối vừa xóa / đổi chỗ) không còn đứng ngay trước trường bố cục đầu tiên: bỏ
    [].forEach.call(list.querySelectorAll('.lsn-cai-dat'), function (b) { if (keep.indexOf(b) < 0) b.remove(); });
  }

  /* ---------- Nút chuyển chế độ trên thanh của trình soạn (cạnh nút Sáng / Tối, trước nút Lưu) ---------- */
  function placeSwitch() {
    var sw = document.getElementById('lsn-che-do');
    var save = document.querySelector('button[aria-keyshortcuts$="+S"]');
    if (!editing() || !save) { if (sw) sw.remove(); return; }
    var saveEl = save.parentElement && /wrapper/.test(save.parentElement.className) ? save.parentElement : save;
    var theme = document.getElementById('lsn-sang-toi');
    var anchor = theme && theme.parentNode === saveEl.parentNode ? theme : saveEl; // thứ tự: [chế độ][Sáng/Tối][Lưu]
    if (!sw) {
      sw = document.createElement('div');
      sw.id = 'lsn-che-do';
      sw.setAttribute('role', 'group');
      sw.setAttribute('aria-label', 'Chế độ soạn');
      [['chu', 'edit_note', 'Sửa chữ', 'Chỉ hiện ô chữ, ảnh, liên kết – gọn, khó bấm nhầm'],
        ['bo-cuc', 'dashboard', 'Sửa bố cục', 'Hiện đủ: thêm, xóa, kéo đổi thứ tự khối, ẩn/hiện, màu nền, số cột…']].forEach(function (x) {
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
      var on = String(b.getAttribute('data-che-do') === mode);
      if (b.getAttribute('aria-pressed') !== on) b.setAttribute('aria-pressed', on);
    });
  }

  function decorate() {
    placeSwitch();
    if (editing()) decorateBlocks();
  }
  function schedule() {
    clearTimeout(schedule.t);
    schedule.t = setTimeout(decorate, 60);
  }
  window.addEventListener('hashchange', onRoute);
  onRoute();
  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  // Bật / tắt "Hiển thị khối này" không thêm bớt nút: theo dõi riêng để dòng Cài đặt khối báo "ĐANG ẨN" kịp thời
  new MutationObserver(schedule).observe(document.documentElement, { attributes: true, subtree: true, attributeFilter: ['aria-checked'] });
})();
