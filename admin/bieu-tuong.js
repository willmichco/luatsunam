/* Ô chọn "Biểu tượng" (lĩnh vực, thẻ, cam kết…): hiện hình biểu tượng cạnh tên, cả trong danh sách chọn lẫn ô đã chọn.
   Hình lấy từ đúng bộ biểu tượng của website (build ghi admin/bieu-tuong.json từ tools/sprite.py + schema.ICONS).
   Danh sách chọn: CSS theo data-value của từng dòng. Ô đã chọn: Sveltia chỉ hiện tên → gắn data-lsn-bt theo tên.
   Chỉ đổi cách hiện, không đổi dữ liệu. Dựa vào giao diện Sveltia 0.221.8 ([role=option][data-value], [role=combobox] .label). */
(function () {
  'use strict';
  var NHAN = null;
  fetch(new URL('bieu-tuong.json', location.href).href, { cache: 'no-cache' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d) return;
      var st = document.createElement('style');
      st.id = 'lsn-bieu-tuong-css';
      st.textContent = d.css;
      document.head.appendChild(st);
      NHAN = d.nhan || {};
      mark();
    }).catch(function () { /* không có hình: vẫn chọn theo tên như cũ */ });

  function mark() {
    if (!NHAN) return;
    [].forEach.call(document.querySelectorAll('[role=combobox]'), function (cb) {
      var l = cb.querySelector('.label'), key = l && NHAN[l.textContent.trim()];
      if ((key || null) !== cb.getAttribute('data-lsn-bt')) { // không đổi thì không chạm DOM (tránh vòng lặp observer)
        if (key) cb.setAttribute('data-lsn-bt', key); else cb.removeAttribute('data-lsn-bt');
      }
    });
  }
  new MutationObserver(function () {
    clearTimeout(mark.t);
    mark.t = setTimeout(mark, 60);
  }).observe(document.documentElement, { childList: true, subtree: true, characterData: true });
})();
