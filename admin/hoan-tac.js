/* Hoàn tác trong trình soạn + nút mở Lịch sử chỉnh sửa (chỉ thêm nút, dùng đúng lệnh có sẵn của Sveltia – không tự ghi dữ liệu):
   - Ô vừa sửa mà chưa Lưu: hiện nút "↶ Hoàn tác" ở đầu ô → trả riêng ô đó về bản đã lưu
     (= lệnh "Hoàn tác thay đổi" trong menu ⋮ của ô; ô danh sách: trả cả danh sách, gồm mục vừa thêm / xóa / kéo).
   - Thanh trên cùng: "↶ Hoàn tác tất cả" khi còn thay đổi chưa lưu (= ⋮ → "Hoàn tác tất cả thay đổi"),
     "Lịch sử" mở trang Lịch sử chỉnh sửa (admin/lich-su.html) của đúng trang đang sửa, ở tab mới (không mất phần đang soạn).
   Ô nào "vừa sửa": có gõ / chọn / bấm nút bên trong ô (hoặc chọn trong menu của ô) kể từ lần Lưu gần nhất – Sveltia không cho đọc
   trạng thái này. Bấm Hoàn tác ở ô thật ra chưa đổi: báo "không có gì để hoàn tác" và ẩn nút. Lưu xong (nút Lưu tắt): mọi nút ẩn.
   Dựa vào giao diện Sveltia 0.221.8 (section.field > header > button.menu-button, menu trong dialog.popup [role=menu]):
   nâng cấp Sveltia phải thử lại. */
(function () {
  'use strict';
  var DA_SUA = 'data-lsn-da-sua';
  var cho = null; // ô vừa mở menu / danh sách chọn: mục chọn trong menu (nằm ngoài ô) tính cho ô này

  function editing() { return /^#\/collections\/[^/]+\/(entries\/|new)/.test(location.hash); }
  function saveButton() { return document.querySelector('button[aria-keyshortcuts$="+S"]'); }
  function unsaved() { var b = saveButton(); return !!b && b.getAttribute('aria-disabled') === 'false'; }
  function fieldOf(el) {
    var f = el && el.closest && el.closest('section.field[data-key-path]');
    return f && f.getAttribute('data-field-type') !== 'lsn_nhom' ? f : null;
  }
  function label(f) {
    var l = f.querySelector(':scope > header h4');
    return l ? l.textContent.replace(/\s*\*\s*$/, '').trim() : 'ô này';
  }
  function mark(f) {
    if (!f || !editing() || f.hasAttribute(DA_SUA)) return;
    f.setAttribute(DA_SUA, '');
    schedule();
  }
  function unmark(f) {
    [f].concat([].slice.call(f.querySelectorAll('[' + DA_SUA + ']'))).forEach(function (x) { x.removeAttribute(DA_SUA); });
    schedule();
  }

  /* ---------- Nhận biết ô vừa sửa ---------- */
  ['input', 'change', 'drop'].forEach(function (ev) {
    document.addEventListener(ev, function (e) { if (!e.target.closest('.lsn-hoan-tac')) mark(fieldOf(e.target)); }, true);
  });
  document.addEventListener('keydown', function (e) {
    // Dời mục bằng phím mũi tên trên nút kéo ═
    if (/^(ArrowUp|ArrowDown|Home|End)$/.test(e.key) && e.target.closest && e.target.closest('.drag-handle')) mark(fieldOf(e.target));
  }, true);
  document.addEventListener('click', function (e) {
    var t = e.target, b = t.closest && t.closest('button, [role=button], [role=menuitem], [role=menuitemradio], [role=option]');
    if (!b || b.closest('.lsn-hoan-tac, #lsn-lich-su-nhom')) return;
    // Chọn một mục trong menu / danh sách xổ (vẽ ngoài form): tính cho ô vừa mở menu đó
    if (!b.closest('section.field')) {
      if (cho && b.closest('[role=menu], [role=listbox], dialog') && /^(menuitem|menuitemradio|option)$/.test(b.getAttribute('role') || '')) {
        if (!/hoàn tác|revert/i.test(b.textContent)) mark(cho);
      }
      return;
    }
    var f = fieldOf(b);
    if (!f) return;
    if (b.hasAttribute('aria-haspopup')) { cho = f; return; } // mở menu ⋮ / ô chọn: chưa đổi gì
    if (b.matches('[aria-expanded][aria-controls]') || b.classList.contains('drag-handle')) return; // mở / thu ô, cầm nút kéo
    if (b.closest('.toolbar') && !b.querySelector('.icon, .material-symbols-outlined')) return; // "Mở hết" / "Thu hết"
    mark(f);
  }, true);

  /* ---------- Bấm trong menu của Sveltia (ẩn đi trong lúc làm) ---------- */
  var anMenu = document.createElement('style');
  anMenu.textContent = 'dialog.popup { opacity: 0 !important; }';
  function waitMenu(t0) {
    return new Promise(function (ok) {
      (function look() {
        var m = [].filter.call(document.querySelectorAll('dialog[open] [role=menu]'), function (x) { return x.getClientRects().length; }).pop();
        if (m) return ok(m);
        if (Date.now() - t0 > 1500) return ok(null);
        setTimeout(look, 30);
      })();
    });
  }
  function closeMenu(menu) {
    var d = menu && menu.closest('dialog');
    if (!d) return;
    // Sveltia đóng menu khi Esc (sự kiện cancel của dialog) hoặc bấm ra ngoài
    var ev = new Event('cancel', { cancelable: true });
    d.dispatchEvent(ev);
    if (d.open) d.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    if (d.open) d.close();
  }
  function pick(menuButton, match) {
    document.head.appendChild(anMenu);
    menuButton.click();
    return waitMenu(Date.now()).then(function (menu) {
      var items = menu ? [].slice.call(menu.querySelectorAll('[role=menuitem]')) : [];
      var it = items.filter(function (x) { return match.test(x.textContent); })[0];
      var r = !it ? 'khong-thay' : it.getAttribute('aria-disabled') === 'true' || it.disabled ? 'khong-doi' : 'xong';
      if (r === 'xong') it.click(); else closeMenu(menu);
      setTimeout(function () { anMenu.remove(); }, 50);
      return r;
    });
  }
  function toast(chu) {
    var d = document.getElementById('lsn-hoan-tac-bao') || document.createElement('div');
    d.id = 'lsn-hoan-tac-bao'; d.setAttribute('role', 'status'); d.textContent = chu;
    document.body.appendChild(d);
    clearTimeout(toast.t); toast.t = setTimeout(function () { d.remove(); }, 4000);
  }

  function revertField(f) {
    var mb = f.querySelector(':scope > header > button.menu-button');
    if (!mb) { toast('Ô này không hoàn tác được.'); return; }
    var ten = label(f);
    pick(mb, /^\s*(hoàn tác thay đổi|revert changes)\s*$/i).then(function (r) {
      unmark(f);
      toast(r === 'xong' ? '↶ Đã trả “' + ten + '” về bản đã lưu.' : r === 'khong-doi' ? '“' + ten + '” đang giống bản đã lưu – không có gì để hoàn tác.' : 'Không tìm thấy lệnh hoàn tác cho ô này.');
    });
  }
  function revertAll() {
    var save = saveButton(), bar = save && save.closest('[role=toolbar]');
    // Nút ⋮ "tùy chọn trình soạn" ngay sau nút Lưu
    var mb = bar && [].filter.call(bar.querySelectorAll('button.menu-button'), function (b) {
      return save.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING;
    })[0];
    if (!mb) { toast('Không tìm thấy lệnh hoàn tác.'); return; }
    if (!window.confirm('Bỏ MỌI thay đổi chưa lưu ở trang này, trả về đúng bản đã lưu?')) return;
    pick(mb, /^\s*(hoàn tác tất cả thay đổi|revert all changes)\s*$/i).then(function (r) {
      [].forEach.call(document.querySelectorAll('[' + DA_SUA + ']'), function (x) { x.removeAttribute(DA_SUA); });
      toast(r === 'xong' ? '↶ Đã trả cả trang về bản đã lưu.' : 'Không có thay đổi nào để hoàn tác.');
      schedule();
    });
  }

  /* ---------- Vẽ nút ---------- */
  function fieldButton(f) {
    var h = f.querySelector(':scope > header'), b = h && h.querySelector(':scope > .lsn-hoan-tac');
    var want = f.hasAttribute(DA_SUA) && unsaved() && h && h.querySelector(':scope > button.menu-button');
    if (!want) { if (b) b.remove(); return; }
    if (b) return;
    b = document.createElement('button');
    b.type = 'button'; b.className = 'lsn-hoan-tac';
    b.title = 'Trả ô này về như lần Lưu gần nhất';
    b.innerHTML = '<span class="icon" aria-hidden="true">undo</span>Hoàn tác';
    b.addEventListener('click', function (e) { e.preventDefault(); e.stopPropagation(); revertField(f); });
    h.appendChild(b); // cuối header: sau mọi chỗ Sveltia tự chèn, không xen vào khối nó quản lý
  }
  function toolbar() {
    var g = document.getElementById('lsn-lich-su-nhom'), save = saveButton();
    if (!editing() || !save) { if (g) g.remove(); return; }
    var saveEl = save.parentElement && /wrapper/.test(save.parentElement.className) ? save.parentElement : save;
    // Thứ tự: [Hoàn tác tất cả][Lịch sử][chế độ][Hướng dẫn, Sáng/Tối][Lưu] (admin/che-do.js, admin/dieu-huong.js đặt các nút giữa)
    var anchor = [document.getElementById('lsn-che-do'), document.getElementById('lsn-nut-chung'), saveEl].filter(function (x) {
      return x && x.parentNode === saveEl.parentNode;
    })[0];
    if (!g) {
      g = document.createElement('div');
      g.id = 'lsn-lich-su-nhom'; g.className = 'lsn-nhom-nut'; // kiểu nút: admin/giao-dien.css
      g.innerHTML = '<button type="button" class="lsn-nut lsn-nut--do" data-viec="het" title="Bỏ mọi thay đổi chưa lưu, trả trang về bản đã lưu">' +
        '<span class="icon" aria-hidden="true">undo</span><span class="chu">Hoàn tác tất cả</span></button>' +
        '<button type="button" class="lsn-nut" data-viec="lich-su" title="Xem các lần lưu trước của trang này, khôi phục bản cũ (mở tab mới)">' +
        '<span class="icon" aria-hidden="true">history</span><span class="chu">Lịch sử</span></button>';
      g.querySelector('[data-viec=het]').addEventListener('click', revertAll);
      g.querySelector('[data-viec=lich-su]').addEventListener('click', function () {
        var m = location.hash.match(/^#\/collections\/([^/]+)\/entries\/([^/?#]+)/);
        window.open('lich-su.html' + (m ? '?muc=' + encodeURIComponent(m[1]) + '&ma=' + encodeURIComponent(decodeURIComponent(m[2])) : ''), '_blank', 'noopener');
      });
    }
    if (g.nextElementSibling !== anchor) anchor.parentNode.insertBefore(g, anchor);
    var het = g.querySelector('[data-viec=het]'), ls = g.querySelector('[data-viec=lich-su]');
    var hetHien = unsaved(), lsHien = /\/entries\//.test(location.hash); // trang mới tạo chưa có lịch sử
    if (het.hidden === hetHien) het.hidden = !hetHien; // không đổi thì không chạm DOM (tránh vòng lặp observer)
    if (ls.hidden === lsHien) ls.hidden = !lsHien;
  }

  function decorate() {
    if (!editing() || !unsaved()) {
      [].forEach.call(document.querySelectorAll('[' + DA_SUA + ']'), function (x) { x.removeAttribute(DA_SUA); });
    }
    [].forEach.call(document.querySelectorAll('section.field[' + DA_SUA + '], .lsn-hoan-tac'), function (x) {
      var f = x.matches('section.field') ? x : x.closest('section.field');
      if (f) fieldButton(f); else x.remove();
    });
    toolbar();
  }
  function schedule() {
    clearTimeout(schedule.t);
    schedule.t = setTimeout(decorate, 80);
  }
  window.addEventListener('hashchange', schedule);
  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['aria-disabled'] });
  decorate();
})();
