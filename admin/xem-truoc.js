/* Khung mô phỏng trong /admin (cột phải khi soạn).
   - Dựng trang bằng ĐÚNG code build của site (xem-truoc-worker.js chạy tools/xem_truoc.py trong Pyodide),
     cập nhật theo từng chữ gõ, giống hệt trang sẽ lên website (không tính phần tô sáng).
   - Bấm vào ô nào trong form: khối/mục tương ứng trên trang được viền đỏ, có nhãn và tự cuộn tới.
     Ngược lại, bấm vào một chỗ trên trang mô phỏng: form nhảy tới đúng ô đó.
   - Máy tính / Điện thoại; báo lỗi tiếng Việt TRƯỚC khi Lưu; ô SEO hiện mẫu kết quả Google.
   Dùng React do Sveltia cung cấp (window.createClass, window.createElement). */
(function () {
  'use strict';
  if (!window.CMS || !window.createClass || !window.createElement) return;
  var h = window.createElement;
  var SITE = new URL('../', location.href).href; // gốc website, vd. https://willmichco.github.io/luatsunam/
  var RED = '#b5000b';
  // Màu khung (thanh công cụ, bảng lỗi, danh sách các phần) theo giao diện Sáng / Tối của trang quản trị; trang mô phỏng giữ nguyên màu site
  var PALETTE = {
    light: { bg: '#efe9e0', bar: '#fffdf9', line: '#e6ddd2', ink: '#2b1d21', muted: '#5f5557', chipBg: '#fbeaea', chipInk: '#7a0007',
      segLine: '#d9cfc3', segOn: '#2b1d21', segOnInk: '#fff', segOff: '#fff', card: '#fff', soft: '#f4f0ea', softLine: '#e1d8cc',
      errBg: '#fdecec', errInk: '#7a0007', errLine: '#f3b9b9', warnBg: '#fff6e0', warnInk: '#6b4a00', warnLine: '#f0d48a',
      hover: '#f7efe6', active: '#fbeaea', ok: '#2e7d32', wait: '#c58a00', link: RED },
    dark: { bg: '#1d1718', bar: '#262021', line: '#3a3133', ink: '#f1e9ea', muted: '#b9adaf', chipBg: '#4a1d22', chipInk: '#ffd9dc',
      segLine: '#4a4042', segOn: '#f1e9ea', segOnInk: '#1d1718', segOff: '#262021', card: '#2b2425', soft: '#2b2425', softLine: '#3f3537',
      errBg: '#3d1519', errInk: '#ffd2d6', errLine: '#7a2a31', warnBg: '#3a2e12', warnInk: '#f5dfa6', warnLine: '#6d5622',
      hover: '#332a2c', active: '#4a1d22', ok: '#7bc47f', wait: '#e0a92e', link: '#ff8a93' },
  };
  var themeSubs = [];
  function pal() { return PALETTE[document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light']; }
  new MutationObserver(function () { themeSubs.forEach(function (f) { f(); }); })
    .observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  /* ---------------- Luồng dựng trang (1 cho cả trang quản trị) ---------------- */
  var engine = { worker: null, ready: false, error: '', ms: 0, seq: 0, cb: {}, subs: [] };
  function emit() { engine.subs.forEach(function (f) { f(); }); }
  function startEngine() {
    if (engine.worker) return;
    try {
      engine.worker = new Worker(new URL('xem-truoc-worker.js', location.href).href);
    } catch (e) {
      engine.error = 'Trình duyệt không chạy được bộ dựng trang (' + e.message + ')'; emit(); return;
    }
    engine.worker.onmessage = function (e) {
      var m = e.data;
      if (m.type === 'ready') { engine.ready = true; engine.ms = m.ms; emit(); }
      else if (m.type === 'error') { engine.error = m.message; emit(); }
      else if (m.type === 'html') {
        Object.keys(engine.cb).forEach(function (id) {
          if (+id <= m.id) { var f = engine.cb[id]; delete engine.cb[id]; if (+id === m.id) f(m.result); }
        });
      }
    };
    engine.worker.onerror = function (e) { engine.error = (e && e.message) || 'Bộ dựng trang gặp lỗi'; emit(); };
    engine.worker.postMessage({ type: 'init', goi: new URL('xem-truoc/goi.zip', location.href).href, pyodide: window.LSN_PYODIDE });
  }
  function renderPage(req, cb) {
    startEngine();
    var id = ++engine.seq;
    engine.cb[id] = cb;
    engine.worker.postMessage(Object.assign({ type: 'render', id: id }, req));
  }

  /* ---------------- Ô đang sửa trong form (data-key-path của Sveltia) ---------------- */
  var focus = { key: '', subs: [] };
  function setKey(k) {
    if (k == null || k === focus.key) return;
    focus.key = k;
    focus.subs.forEach(function (f) { f(k); });
  }
  function keyOf(el) {
    // Ô có data-key-path (vd. cac_khoi.2.tieu_de). Bấm vào đầu một mục danh sách đang thu gọn (chưa có ô con):
    // lấy thứ tự mục trong danh sách → cac_khoi.2
    var f = el && el.closest && el.closest('[data-key-path]');
    if (!f) return null;
    var key = f.getAttribute('data-key-path');
    var w = el.closest('.item-wrapper');
    if (w && f.contains(w) && w.parentElement) {
      key += '.' + [].filter.call(w.parentElement.children, function (x) { return x.classList.contains('item-wrapper'); }).indexOf(w);
    }
    return key;
  }
  ['focusin', 'pointerdown'].forEach(function (ev) {
    document.addEventListener(ev, function (e) { setKey(keyOf(e.target)); }, true);
  });
  // Rê chuột lên một mục trong form: viền nhẹ chỗ đó trên trang mô phỏng
  var hover = { key: '', subs: [], t: 0 };
  document.addEventListener('pointerover', function (e) {
    var k = e.target.closest && e.target.closest('.item-wrapper') ? keyOf(e.target) : '';
    clearTimeout(hover.t);
    hover.t = setTimeout(function () {
      if (k === hover.key) return;
      hover.key = k || '';
      hover.subs.forEach(function (f) { f(hover.key); });
    }, 120);
  }, true);

  /* Bấm trên trang mô phỏng → mở đúng ô trong form */
  function itemOf(key) {
    // mục thứ i của danh sách: .item-wrapper trong [data-key-path="<danh sách>"] (Sveltia không gắn key-path cho mục)
    var m = key.match(/^(.*)\.(\d+)$/);
    var list = m && document.querySelector('[data-key-path="' + CSS.escape(m[1]) + '"] .item-list');
    if (!list) return null;
    return [].filter.call(list.children, function (x) { return x.classList.contains('item-wrapper'); })[+m[2]] || null;
  }
  function jumpToField(key) {
    var parts = key.split('.');
    for (var n = parts.length; n > 0; n--) {
      var k = parts.slice(0, n).join('.');
      var el = document.querySelector('[data-key-path="' + CSS.escape(k) + '"]') || itemOf(k);
      if (!el) continue;
      var toggle = el.querySelector('.header button[aria-expanded="false"], button[aria-expanded="false"][aria-label="Mở rộng"]');
      if (toggle && n === parts.length) toggle.click();
      el.scrollIntoView({ block: 'center', behavior: 'smooth' });
      el.animate([{ boxShadow: '0 0 0 3px ' + RED }, { boxShadow: '0 0 0 3px transparent' }], { duration: 1600 });
      var input = el.querySelector('input:not([type=hidden]), textarea, [contenteditable=true], select, button');
      if (input && input.focus) input.focus({ preventScroll: true });
      setKey(key);
      return true;
    }
    return false;
  }

  function unsaved() {
    var b = document.querySelector('button[aria-keyshortcuts$="+S"]');
    return !!b && b.getAttribute('aria-disabled') === 'false';
  }
  function openEntry(hash) {
    if (unsaved() && !window.confirm('Còn thay đổi chưa lưu ở trang đang sửa. Rời đi thì các thay đổi đó sẽ mất. Vẫn mở?')) return;
    var col = hash.split('/')[0];
    // Sveltia 0.221.8 không dựng lại form khi nhảy thẳng giữa hai tệp cùng một mục: đi qua danh sách của mục trước
    if (location.hash.indexOf('#/collections/' + col + '/') === 0) {
      location.hash = '#/collections/' + col;
      setTimeout(function () { location.hash = '#/collections/' + hash; }, 300);
    } else {
      location.hash = '#/collections/' + hash;
    }
  }
  function formHas(key) {
    var root = key.split('.')[0];
    return !!document.querySelector('[data-key-path="' + CSS.escape(root) + '"]');
  }
  function formLabel(key) {
    var f = document.querySelector('[data-key-path="' + CSS.escape(key) + '"]');
    var l = f && f.querySelector('[id$="-label"]');
    return l ? l.textContent.replace(/\s*\*\s*$/, '').trim() : '';
  }

  /* ---------------- Ô không có data-cms riêng: tìm chỗ trên trang theo tên trường ---------------- */
  var HERO = ['[data-cms="dau_trang"]', 'Đầu trang'];
  var BAND = ['[data-cms="lien_he_cuoi_trang"]', 'Khối liên hệ cuối trang'];
  var HEAD = ['[data-cms="@dau-trang-site"]', 'Menu và đầu trang'];
  var FOOT = ['[data-cms="@chan-trang"]', 'Chân trang'];
  var ELSEWHERE_SVC = 'Ô này hiện ở thẻ lĩnh vực trên Trang chủ và trang Dịch vụ, không nằm trên trang này.';
  var TARGETS = {
    bai_viet: {
      tieu_de: HERO, tieu_de_ngan: HERO, linh_vuc: HERO, ngay_dang: HERO, ngay_cap_nhat: HERO,
      tom_tat: 'Tóm tắt hiện ở thẻ bài viết trong danh sách “Kiến thức pháp lý” và các khối bài viết mới.',
      tom_tat_nhanh: ['.keypoints', 'Tóm tắt nhanh'], doan_dan: ['.prose__lead', 'Đoạn dẫn'],
      body: ['#noi-dung-bai-viet', 'Nội dung bài viết'], linh_vuc_lien_quan: ['.article-aside', 'Khung bên phải bài'],
      duong_dan: 'Đường dẫn là địa chỉ trang, không hiện trong nội dung.',
    },
    dich_vu: {
      ten: HERO, nhan_dau_trang: HERO, tieu_de_trang: HERO, mo_dau: HERO, viec_gap: HERO,
      bieu_tuong: ELSEWHERE_SVC, mo_ta_ngan: ELSEWHERE_SVC, the_tinh_huong: ELSEWHERE_SVC, bieu_tuong_tinh_huong: ELSEWHERE_SVC,
      thu_tu: 'Thứ tự quyết định vị trí lĩnh vực trong menu, lưới lĩnh vực và chân trang.',
      tinh_huong: ['#tinh-huong', 'Tình huống thường gặp'], pham_vi: ['#pham-vi', 'Phạm vi hỗ trợ'],
      viec_nen_lam: ['#viec-nen-lam', 'Việc nên làm'], luu_y: ['#viec-nen-lam', 'Lưu ý'], nguyen_tac: ['#viec-nen-lam', 'Nguyên tắc'],
      cac_buoc: ['#quy-trinh', 'Quy trình'], giay_to: ['#ho-so', 'Hồ sơ cần chuẩn bị'], nhan_duoc: ['#ho-so', 'Anh chị nhận được'],
      hoi_dap: function (p) { return p.length > 1 ? ['#hoi-dap-' + (+p[1] + 1), 'Câu hỏi ' + (+p[1] + 1)] : ['#hoi-dap', 'Hỏi đáp']; },
      can_cu_phap_ly: ['#tham-khao', 'Căn cứ pháp lý'], linh_vuc_lien_quan: ['#lien-quan', 'Lĩnh vực liên quan'], lien_he: BAND,
    },
    trang: { tieu_de: HERO, trang_cha: HERO, loai_trang: 'Loại trang dùng cho Google (dữ liệu có cấu trúc), không hiện trên trang.' },
    kien_thuc: { bai_viet: ['main > section:nth-of-type(2)', 'Danh sách bài viết'], the_cong_cu: ['main > section:nth-of-type(3)', 'Thẻ công cụ'],
      theo_linh_vuc: ['main > section:nth-of-type(4)', 'Theo lĩnh vực'] },
    dich_vu_hub: { luoi: ['main > section:nth-of-type(2)', 'Lưới lĩnh vực'], hinh_thuc: ['main > section:nth-of-type(3)', 'Hình thức làm việc'] },
    hoi_dap_hub: { cau_hoi: ['.faq', 'Danh sách câu hỏi (kho câu hỏi dùng chung)'], ghi_chu_cuoi: ['.faq-aside', 'Ghi chú cuối'],
      tim_hieu_them: ['.faq-aside', 'Tìm hiểu thêm'] },
    hoi_dap: { cau_hoi: function (p) { return p.length > 1 ? ['.faq__item:nth-of-type(' + (+p[1] + 1) + ')', 'Câu hỏi ' + (+p[1] + 1)] : ['.faq', 'Câu hỏi thường gặp']; },
      tim_hieu_them: ['.faq-aside', 'Ghi chú, cột Tìm hiểu thêm'] },
    van_ban: { tieu_de: HERO, nhan: HERO, tieu_de_trang: HERO, mo_dau: HERO, ngay_cap_nhat: HERO, body: ['.legal-doc', 'Nội dung văn bản'] },
    trang_404: { tieu_de: ['main', 'Thông báo lỗi 404'], noi_dung: ['main', 'Thông báo lỗi 404'],
      seo: 'Tiêu đề tab trình duyệt của trang 404, không hiện trong nội dung.' },
    cong_ty: { hotline: HEAD, ten_viet_tat: HEAD, gioi_thieu_chan_trang: FOOT, '*': FOOT },
    menu: { menu: HEAD, goi_y_tim_kiem: 'Gợi ý hiện trong ô tìm kiếm (bấm kính lúp ở đầu trang).', '*': FOOT },
    cau_chu: { lien_he_cuoi_trang: BAND, mien_tru_chan_trang: FOOT, '*': 'Câu chữ này dùng ở trang lĩnh vực và cuối bài viết.' },
    theo_doi: { '*': 'Mã theo dõi không hiện trên trang.' },
    chuyen_huong: { '*': 'Chuyển hướng không hiện trên trang: địa chỉ cũ tự chuyển sang trang mới sau khi Lưu.' },
    anh_thuong_hieu: { logo: HEAD, '*': ['[data-cms="cac_khoi.0"]', 'Ảnh luật sư ở đầu trang chủ'] },
  };
  // Phần dùng chung mọi trang: sửa ở Cài đặt chung
  var SHARED = {
    '@dau-trang-site': [['Menu', 'cai_dat/entries/menu'], ['Hotline, giờ làm việc', 'cai_dat/entries/cong_ty'], ['Logo', 'cai_dat/entries/anh_thuong_hieu']],
    '@chan-trang': [['Liên kết, cột lĩnh vực', 'cai_dat/entries/menu'], ['Địa chỉ, giới thiệu ngắn', 'cai_dat/entries/cong_ty'],
      ['Dòng miễn trừ', 'cai_dat/entries/cau_chu']],
  };
  // Trang ghép từ 2 tệp (trang Câu hỏi thường gặp = phần chữ + kho câu hỏi): phần thuộc tệp kia mở tệp kia
  var OTHER_FILE = {
    hoi_dap: { '*': 'hoi_dap/entries/trang-hoi-dap' },
    hoi_dap_hub: { cau_hoi: 'hoi_dap/entries/kho-cau-hoi' },
  };

  // Loại nội dung theo tệp đang sửa (cùng một tệp có thể mở từ nhiều mục trong cột trái)
  var BY_PATH = {
    'content/dich-vu/_index.yml': 'dich_vu_hub', 'content/bai-viet/_index.yml': 'kien_thuc',
    'content/trang-tong-hop/cau-hoi-thuong-gap.yml': 'hoi_dap_hub', 'content/hoi-dap.yml': 'hoi_dap',
  };
  function mapName(entry) {
    var path = entry.get('path') || '';
    if (BY_PATH[path]) return BY_PATH[path];
    var m = path.match(/^content\/(cai-dat|trang-van-ban|trang|dich-vu|bai-viet)\/([^/]+)\.(yml|md)$/);
    if (m && m[1] === 'cai-dat') return m[2].replace(/-/g, '_');
    if (m && m[1] === 'trang-van-ban' && m[2] === '404') return 'trang_404';
    if (m) return { 'trang-van-ban': 'van_ban', trang: 'trang', 'dich-vu': 'dich_vu', 'bai-viet': 'bai_viet' }[m[1]];
    return entry.get('collection'); // bài / trang / lĩnh vực mới chưa lưu
  }
  function resolve(doc, key, name) {
    if (!doc || !key) return null;
    var parts = key.split('.');
    if (parts[0] === 'seo') return { seo: true };
    for (var n = parts.length; n > 0; n--) {
      var el = doc.querySelector('[data-cms="' + CSS.escape(parts.slice(0, n).join('.')) + '"]');
      if (el) return { el: el, label: el.getAttribute('data-cms-ten') || '' };
    }
    var map = TARGETS[name] || {};
    var t = map[parts[0]] || map['*'];
    if (typeof t === 'function') t = t(parts);
    if (typeof t === 'string') return { note: t };
    if (t) {
      var el2 = doc.querySelector(t[0]);
      if (el2) return { el: el2, label: t[1] };
    }
    return null;
  }

  /* ---------------- “Trang này gồm”: mọi phần sửa được, theo thứ tự từ trên xuống ---------------- */
  function outline(doc, name) {
    var items = [], seen = [];
    function add(el, key, label, extra) {
      if (!el || seen.indexOf(el) >= 0) return;
      seen.push(el);
      items.push(Object.assign({ el: el, key: key, label: label }, extra || {}));
    }
    [].forEach.call(doc.querySelectorAll('[data-cms]'), function (el) {
      if (el.parentElement && el.parentElement.closest('[data-cms]')) return; // phần con nằm trong phần khác
      var k = el.getAttribute('data-cms');
      add(el, k, el.getAttribute('data-cms-ten') || k, { an: el.hasAttribute('data-cms-an'), chung: k.charAt(0) === '@' });
    });
    var map = TARGETS[name] || {}, notes = [];
    Object.keys(map).forEach(function (f) {
      var t = map[f];
      if (f === '*') return;
      if (typeof t === 'function') t = t([f]);
      if (typeof t === 'string') { notes.push({ key: f, note: t }); return; }
      var el = t && doc.querySelector(t[0]);
      var owner = el && el.closest('[data-cms]');
      if (!el || (owner && owner.getAttribute('data-cms').charAt(0) !== '@')) return; // đã có trong phần chứa nó (vd. đầu trang)
      add(el, f, t[1]);
    });
    // Thứ tự từ trên xuống; phần nằm trong phần khác (vd. Tóm tắt nhanh trong Nội dung bài viết) đứng trước phần chứa nó
    items.sort(function (a, b) {
      if (a.el.contains(b.el)) return 1;
      if (b.el.contains(a.el)) return -1;
      return a.el.compareDocumentPosition(b.el) & 2 ? 1 : -1;
    });
    return { items: items, notes: notes };
  }
  function badges(doc, items) {
    [].slice.call(doc.querySelectorAll('.cms-so')).forEach(function (b) { b.remove(); });
    if (!items) return;
    var w = doc.defaultView;
    items.forEach(function (it, i) {
      var r = it.el.getBoundingClientRect();
      if (!r.width && !r.height) return;
      var b = doc.createElement('div');
      b.className = 'cms-so' + (it.chung ? ' chung' : '');
      b.textContent = i + 1;
      b.style.left = Math.max(4, r.left + w.scrollX + 6) + 'px';
      b.style.top = Math.max(4, r.top + w.scrollY + 6) + 'px';
      doc.body.appendChild(b);
    });
  }

  /* ---------------- Trang mô phỏng (iframe lồng) ---------------- */
  var PAGE_CSS =
    '.reveal{opacity:1!important;transform:none!important}' +
    'html{scroll-behavior:auto!important}' +
    '[data-cms-an]{opacity:.42;filter:grayscale(.6);outline:2px dashed #8a7f81;outline-offset:-2px;position:relative}' +
    '[data-cms-an]::before{content:"Đang ẩn – không hiện trên website";position:absolute;z-index:5;top:10px;right:10px;background:#5f5557;color:#fff;font:600 13px/1.3 system-ui,sans-serif;padding:5px 10px;border-radius:999px}' +
    '.cms-loi,.cms-trong{margin:16px auto;max-width:1100px;padding:18px 22px;border-radius:10px;font:500 15px/1.5 system-ui,sans-serif}' +
    '.cms-loi{background:#fdecec;color:#7a0007;border:2px dashed ' + RED + '}.cms-trong{background:#f4f0ea;color:#5f5557;border:2px dashed #c9bfb3}' +
    '#cms-khung,#cms-tro{position:absolute;pointer-events:none;z-index:2147483000;border-radius:6px;transition:all .18s ease}' +
    ':root{--cms-s:1}' +
    '#cms-khung{border:calc(3px / var(--cms-s)) solid ' + RED + ';background:rgba(181,0,11,.05);box-shadow:0 0 0 9999px rgba(30,20,22,.07)}' +
    '#cms-tro{border:calc(2px / var(--cms-s)) dashed rgba(181,0,11,.6)}' +
    '#cms-khung span,#cms-tro span{position:absolute;left:0;bottom:100%;white-space:nowrap;font:600 calc(13px / var(--cms-s))/1 system-ui,sans-serif;' +
    'padding:calc(7px / var(--cms-s)) calc(11px / var(--cms-s));border-radius:calc(6px / var(--cms-s)) calc(6px / var(--cms-s)) 0 0;color:#fff;background:' + RED + '}' +
    '#cms-tro span{background:rgba(181,0,11,.8)}' +
    '#cms-khung.trong span,#cms-tro.trong span{bottom:auto;top:0;border-radius:0 0 calc(6px / var(--cms-s)) 0}' +
    '[data-cms]{cursor:pointer}a{cursor:pointer}' +
    '.cms-so{position:absolute;z-index:2147482000;pointer-events:none;min-width:calc(26px / var(--cms-s));height:calc(26px / var(--cms-s));' +
    'padding:0 calc(6px / var(--cms-s));box-sizing:border-box;border-radius:999px;background:' + RED + ';color:#fff;' +
    'font:700 calc(14px / var(--cms-s))/calc(26px / var(--cms-s)) system-ui,sans-serif;text-align:center;' +
    'box-shadow:0 0 0 calc(2px / var(--cms-s)) #fff,0 2px 6px rgba(0,0,0,.25)}' +
    '.cms-so.chung{background:#5f5557}';

  function prepareHtml(html, base) {
    return html
      .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '') // bỏ JS của site, mã theo dõi: mô phỏng chỉ để nhìn
      .replace(/<head>/i, '<head><base href="' + base + '"><style id="cms-style">' + PAGE_CSS + '</style>');
  }

  function morph(doc, html) {
    var nd = new DOMParser().parseFromString(html, 'text/html');
    doc.title = nd.title;
    var A = doc.querySelector('main'), B = nd.querySelector('main');
    var top = function (d) { return [].filter.call(d.body.children, function (e) { return e.id !== 'cms-khung' && e.id !== 'cms-tro' && !e.classList.contains('cms-so'); }); };
    var ta = top(doc), tb = top(nd);
    if (!A || !B || ta.length !== tb.length) {
      doc.body.innerHTML = nd.body.innerHTML;
      return;
    }
    ta.forEach(function (x, i) {
      var y = tb[i];
      if (x.tagName === 'MAIN') return;
      if (x.outerHTML !== y.outerHTML) x.replaceWith(doc.importNode(y, true));
    });
    var ca = [].slice.call(A.children), cb = [].slice.call(B.children);
    if (ca.length !== cb.length) { A.innerHTML = B.innerHTML; return; }
    ca.forEach(function (x, i) { if (x.outerHTML !== cb[i].outerHTML) x.replaceWith(doc.importNode(cb[i], true)); });
  }

  function box(doc, id, el, label) {
    var b = doc.getElementById(id);
    if (!el) { if (b) b.style.display = 'none'; return; }
    if (!b) {
      b = doc.createElement('div'); b.id = id; b.appendChild(doc.createElement('span'));
      doc.body.appendChild(b);
    }
    var r = el.getBoundingClientRect(), w = doc.defaultView;
    b.style.display = 'block';
    b.style.left = r.left + w.scrollX + 'px'; b.style.top = r.top + w.scrollY + 'px';
    b.style.width = r.width + 'px'; b.style.height = r.height + 'px';
    b.firstChild.textContent = label;
    b.firstChild.style.display = label ? '' : 'none';
    b.classList.toggle('trong', r.top + w.scrollY < 40); // sát mép trên: đặt nhãn bên trong khung
  }

  /* ---------------- Thành phần React ---------------- */
  var SETTINGS_FILES = ['cong_ty', 'menu', 'cau_chu', 'seo', 'theo_doi', 'chuyen_huong', 'anh_thuong_hieu'];
  function styles(P) {
    return {
      wrap: { position: 'fixed', inset: 0, display: 'flex', flexDirection: 'column', background: P.bg, font: '14px/1.4 "Be Vietnam Pro",system-ui,-apple-system,"Segoe UI",sans-serif', color: P.ink },
      bar: { display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 12px', background: P.bar, borderBottom: '1px solid ' + P.line, minHeight: '48px', boxSizing: 'border-box' },
      dot: function (c) { return { width: '9px', height: '9px', borderRadius: '50%', background: c, flex: 'none' }; },
      chip: { display: 'block', flex: '0 1 auto', minWidth: 0, padding: '5px 10px', borderRadius: '999px', background: P.chipBg, color: P.chipInk, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
      btn: function (on) { return { flex: 'none', marginLeft: 'auto', display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '6px 11px', border: '1px solid ' + (on ? P.segOn : P.segLine), borderRadius: '8px', font: 'inherit', fontWeight: 600, cursor: 'pointer', background: on ? P.segOn : P.segOff, color: on ? P.segOnInk : P.ink }; },
      seg: { display: 'inline-flex', flex: 'none', border: '1px solid ' + P.segLine, borderRadius: '8px', overflow: 'hidden' },
      segBtn: function (on) { return { border: 0, padding: '6px 11px', font: 'inherit', fontWeight: 600, cursor: 'pointer', background: on ? P.segOn : P.segOff, color: on ? P.segOnInk : P.ink }; },
      link: { color: P.link, fontWeight: 600, textDecoration: 'none', whiteSpace: 'nowrap' },
      body: { position: 'relative', flex: 1, display: 'flex', minHeight: 0 },
      stage: { position: 'relative', flex: 1, overflow: 'hidden' },
      msg: { position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', padding: '24px', textAlign: 'center', color: P.muted },
      panel: function (bg, fg, bd) { return { margin: '8px 12px 0', padding: '10px 12px', borderRadius: '8px', background: bg, color: fg, border: '1px solid ' + bd, maxHeight: '30vh', overflow: 'auto' }; },
      side: function (overlay) { return { flex: 'none', width: '250px', overflow: 'auto', background: P.bar, borderRight: '1px solid ' + P.line, boxSizing: 'border-box', padding: '10px 0 16px', position: overlay ? 'absolute' : 'relative', zIndex: 3, top: 0, bottom: 0, left: 0, boxShadow: overlay ? '4px 0 18px rgba(0,0,0,.18)' : 'none' }; },
      sideHead: { display: 'flex', alignItems: 'baseline', gap: '6px', padding: '0 12px 6px', fontWeight: 700 },
      sideHint: { padding: '0 12px 8px', fontSize: '12px', color: P.muted },
      row: function (active, hover, muted) { return { display: 'flex', alignItems: 'flex-start', gap: '9px', width: '100%', padding: '7px 12px', border: 0, borderLeft: '3px solid ' + (active ? RED : 'transparent'), background: active ? P.active : hover ? P.hover : 'transparent', color: muted ? P.muted : P.ink, font: 'inherit', textAlign: 'left', cursor: 'pointer' }; },
      num: function (shared) { return { flex: 'none', minWidth: '22px', height: '22px', lineHeight: '22px', borderRadius: '999px', background: shared ? '#5f5557' : RED, color: '#fff', fontSize: '12px', fontWeight: 700, textAlign: 'center' }; },
      sub: { display: 'block', fontSize: '12px', color: P.muted, marginTop: '2px' },
      pill: { display: 'inline-block', padding: '2px 8px', border: '1px solid ' + P.segLine, borderRadius: '999px', color: P.link, fontWeight: 600, cursor: 'pointer', textDecoration: 'none' },
      group: { padding: '12px 12px 4px', fontSize: '11px', fontWeight: 700, letterSpacing: '.06em', textTransform: 'uppercase', color: P.muted },
    };
  }

  var Preview = window.createClass({
    getInitialState: function () {
      var dev = 'may-tinh', map = '1';
      try {
        dev = localStorage.getItem('lsn-xem-truoc-thiet-bi') || dev;
        map = localStorage.getItem('lsn-xem-truoc-ban-do') || map;
      } catch (e) { /* trình duyệt chặn lưu trữ */ }
      focus.key = ''; // mở bài/trang khác: bỏ ô đang sửa của lần trước (vd. ô SEO → thẻ Google)
      return { result: null, status: engine.ready ? 'dang-dung' : 'tai', key: '', device: dev, size: [0, 0], hover: '', note: '', label: '',
        map: map === '1', parts: null, hoverPart: -1 };
    },
    componentDidMount: function () {
      var self = this;
      this.onEngine = function () { self.forceUpdate(); };
      this.onKey = function (k) { self.setState({ key: k }, function () { self.highlight(true); }); };
      this.onHover = function (k) { self.hoverForm(k); };
      this.onTheme = function () { self.forceUpdate(); };
      engine.subs.push(this.onEngine); focus.subs.push(this.onKey); hover.subs.push(this.onHover); themeSubs.push(this.onTheme);
      var W = this.props.window || window;
      if (W.ResizeObserver && this.stage) {
        this.ro = new W.ResizeObserver(function () { self.measure(); });
        this.ro.observe(this.stage);
      }
      this.measure();
      this.request();
    },
    componentWillUnmount: function () {
      engine.subs = engine.subs.filter(function (f) { return f !== this.onEngine; }, this);
      focus.subs = focus.subs.filter(function (f) { return f !== this.onKey; }, this);
      hover.subs = hover.subs.filter(function (f) { return f !== this.onHover; }, this);
      themeSubs = themeSubs.filter(function (f) { return f !== this.onTheme; }, this);
      if (this.ro) this.ro.disconnect();
      clearTimeout(this.t);
    },
    componentDidUpdate: function (prev) {
      if (prev.entry !== this.props.entry) this.request();
    },
    measure: function () {
      if (!this.stage) return;
      var s = [this.stage.clientWidth, this.stage.clientHeight];
      if (s[0] !== this.state.size[0] || s[1] !== this.state.size[1]) this.setState({ size: s }, this.highlight.bind(this, false));
    },
    request: function () {
      var self = this;
      clearTimeout(this.t);
      this.t = setTimeout(function () {
        var e = self.props.entry;
        var data = e.get('data');
        renderPage({
          collection: e.get('collection'), slug: e.get('slug') || null, path: e.get('path') || null, isNew: !!e.get('newRecord'),
          data: JSON.stringify(data && data.toJS ? data.toJS() : {}),
        }, function (res) { self.apply(res); });
        if (!self.state.result) self.setState({ status: engine.ready ? 'dang-dung' : 'tai' });
      }, this.state.result ? 280 : 0);
    },
    apply: function (res) {
      var frame = this.frame;
      if (!frame) return;
      var self = this, base = SITE + (res.path && !/\.html$/.test(res.path) ? res.path : '');
      var prev = this.state.result;
      this.setState({ result: res, status: 'xong' });
      if (!res.html) return;
      var doc = frame.contentDocument;
      if (!prev || !prev.html || prev.path !== res.path || !doc || !doc.body || !doc.getElementById('cms-style')) {
        frame.onload = function () { self.wire(); self.highlight(true); };
        frame.srcdoc = prepareHtml(res.html, base);
      } else {
        morph(doc, prepareHtml(res.html, base));
        this.media();
        this.highlight(false);
      }
    },
    media: function () {
      // ảnh vừa tải lên trong lúc soạn (chưa Lưu) chưa có trên website: dùng bản trong trình duyệt
      var doc = this.frame && this.frame.contentDocument, files = this.props.entry.get('mediaFiles');
      if (!doc || !files || !files.size) return;
      files.forEach(function (f) {
        var name = String(f.get('name') || f.get('path') || '').split('/').pop(), url = f.get('url');
        if (!name || !url) return;
        [].forEach.call(doc.querySelectorAll('img'), function (img) {
          if ((img.getAttribute('src') || '').split('?')[0].split('/').pop() === name) { img.removeAttribute('srcset'); img.src = url; }
        });
      });
    },
    wire: function () {
      var self = this, doc = this.frame.contentDocument;
      if (!doc) return;
      this.media();
      doc.addEventListener('click', function (e) {
        var a = e.target.closest('a,button,summary,form');
        if (a) e.preventDefault(); // mô phỏng: không rời trang
        var t = e.target.closest('[data-cms]');
        if (t && !/^@/.test(t.getAttribute('data-cms'))) self.goPart({ key: t.getAttribute('data-cms') });
        else if (t) self.setState({ note: 'Phần này dùng chung cho mọi trang – sửa ở Cài đặt chung: ' + SHARED[t.getAttribute('data-cms')].map(function (x) { return x[0]; }).join(' · ') + ' (xem danh sách “Các phần” bên trái).' });
      }, true);
      doc.addEventListener('submit', function (e) { e.preventDefault(); }, true);
      doc.addEventListener('mousemove', function (e) {
        var t = e.target.closest('[data-cms]');
        var k = t ? t.getAttribute('data-cms') : '';
        if (k === self.hoverKey) return;
        self.hoverKey = k;
        box(doc, 'cms-tro', t && k !== self.activeKey ? t : null, t ? 'Bấm để sửa · ' + (t.getAttribute('data-cms-ten') || '') : '');
      });
      doc.addEventListener('mouseleave', function () { self.hoverKey = ''; box(doc, 'cms-tro', null); });
      doc.defaultView.addEventListener('resize', function () { self.highlight(false); });
    },
    highlight: function (scroll) {
      var doc = this.frame && this.frame.contentDocument;
      if (!doc || !doc.body) return;
      doc.documentElement.style.setProperty('--cms-s', String(this.scale || 1));
      var name = mapName(this.props.entry);
      var r = resolve(doc, this.state.key, name);
      var el = r && r.el, label = el ? r.label : '';
      this.activeKey = el ? el.getAttribute('data-cms') || '' : '';
      this.activeEl = el || null;
      box(doc, 'cms-khung', el, label ? 'Đang sửa · ' + label : '');
      if (el && scroll) {
        var vh = doc.defaultView.innerHeight;
        el.scrollIntoView({ block: el.getBoundingClientRect().height > vh * 0.8 ? 'start' : 'center', behavior: 'smooth' });
      }
      // Danh sách các phần của trang + số thứ tự trên trang mô phỏng
      var parts = this.parts = SETTINGS_FILES.indexOf(name) < 0 ? outline(doc, name) : null;
      badges(doc, this.state.map && parts ? parts.items : null);
      var sig = parts ? parts.items.map(function (x) { return x.key + (x.an ? '~' : '') + x.label; }).join('|') : '';
      var note = r && r.note ? r.note : '';
      if (sig !== this.partsSig || note !== this.state.note || label !== this.state.label || !!(r && r.seo) !== !!this.state.seo) {
        this.partsSig = sig;
        this.setState({ note: note, label: label, seo: !!(r && r.seo), parts: parts });
      }
    },
    hoverForm: function (k) {
      var doc = this.frame && this.frame.contentDocument;
      if (!doc || !doc.body) return;
      doc.documentElement.style.setProperty('--cms-s', String(this.scale || 1));
      var r = k ? resolve(doc, k, mapName(this.props.entry)) : null;
      var el = r && r.el && r.el.getAttribute('data-cms') !== this.activeKey ? r.el : null;
      box(doc, 'cms-tro', el, el ? r.label : '');
    },
    hoverPart: function (i) {
      var doc = this.frame && this.frame.contentDocument, parts = this.parts; // phần tử mới nhất (trang vừa dựng lại)
      if (!doc || !doc.body) return;
      var it = parts && i >= 0 ? parts.items[i] : null;
      box(doc, 'cms-tro', it && it.el !== this.activeEl ? it.el : null, it ? (i + 1) + ' · ' + it.label : '');
      if (i !== this.state.hoverPart) this.setState({ hoverPart: i });
    },
    goPart: function (it) {
      var name = mapName(this.props.entry);
      if (it.chung) return; // phần dùng chung: dùng các liên kết “sửa ở …”
      if (!formHas(it.key)) {
        var other = OTHER_FILE[name] && (OTHER_FILE[name][it.key.split('.')[0]] || OTHER_FILE[name]['*']);
        if (other) openEntry(other);
        return;
      }
      if (!jumpToField(it.key)) setKey(it.key);
    },
    toggleMap: function () {
      var on = !this.state.map;
      try { localStorage.setItem('lsn-xem-truoc-ban-do', on ? '1' : '0'); } catch (e) { /* bỏ qua */ }
      this.setState({ map: on }, this.highlight.bind(this, false));
    },
    setDevice: function (d) {
      try { localStorage.setItem('lsn-xem-truoc-thiet-bi', d); } catch (e) { /* bỏ qua */ }
      this.setState({ device: d }, this.highlight.bind(this, false));
    },
    seoCard: function (S, P) {
      var doc = this.frame && this.frame.contentDocument, res = this.state.result;
      if (!doc || !res) return null;
      var t = doc.title || '', meta = doc.querySelector('meta[name=description]'), d = meta ? meta.getAttribute('content') : '';
      var url = SITE.replace(/^https?:\/\//, '').replace(/\/$/, '') + '/' + (res.path || '');
      var count = function (s, max) { return h('span', { style: { color: s.length > max ? RED : P.ok, fontWeight: 600 } }, s.length + '/' + max + ' ký tự'); };
      // Mẫu Google luôn nền trắng như trang kết quả thật
      return h('div', { style: S.panel('#fff', '#2b1d21', P.segLine) },
        h('div', { style: { fontSize: '12px', color: '#5f5557', marginBottom: '6px' } }, 'Mẫu kết quả trên Google (ước lượng) · tiêu đề ', count(t, 70), ' · mô tả ', count(d, 160)),
        h('div', { style: { fontSize: '13px', color: '#202124' } }, url.replace(/\//g, ' › ').replace(/ › $/, '')),
        h('div', { style: { fontSize: '19px', color: '#1a0dab', lineHeight: 1.3, margin: '2px 0' } }, t.length > 70 ? t.slice(0, 67) + '…' : t),
        h('div', { style: { fontSize: '14px', color: '#4d5156' } }, d.length > 160 ? d.slice(0, 157) + '…' : d));
    },
    sidePanel: function (S, P, overlay) {
      var self = this, parts = this.state.parts, name = mapName(this.props.entry);
      var activeRoot = (this.state.key || '').split('.').slice(0, this.state.key && /^cac_khoi\./.test(this.state.key) ? 2 : 1).join('.');
      var rows = parts.items.map(function (it, i) {
        var inForm = it.chung || formHas(it.key);
        var other = !inForm && OTHER_FILE[name] && (OTHER_FILE[name][it.key.split('.')[0]] || OTHER_FILE[name]['*']);
        var live = self.parts && self.parts.items[i];
        var active = !it.chung && (it.key === activeRoot || (!!live && live.el === self.activeEl));
        var sub = null;
        if (it.chung) {
          sub = h('span', { style: S.sub }, 'Dùng chung mọi trang – sửa ở Cài đặt chung:',
            h('span', { style: { display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' } }, SHARED[it.key].map(function (x, j) {
              return h('a', { key: j, role: 'link', tabIndex: 0, style: S.pill, title: 'Mở Cài đặt chung → ' + x[0],
                onClick: function (e) { e.stopPropagation(); openEntry(x[1]); } }, x[0] + ' ›');
            })));
        } else if (it.an) {
          sub = h('span', { style: S.sub }, 'Đang ẩn – không hiện trên website');
        } else if (other) {
          sub = h('span', { style: S.sub }, 'Sửa ở tệp khác của trang này – bấm để mở');
        }
        return h('button', {
          key: i, type: 'button', style: S.row(active, self.state.hoverPart === i, it.an), title: it.chung ? '' : 'Bấm để mở đúng ô sửa phần này',
          onMouseEnter: function () { self.hoverPart(i); }, onMouseLeave: function () { self.hoverPart(-1); },
          onFocus: function () { self.hoverPart(i); }, onBlur: function () { self.hoverPart(-1); },
          onClick: function () { self.goPart(it); if (overlay) self.setState({ map: false }, self.highlight.bind(self, false)); },
        }, h('span', { style: S.num(it.chung) }, String(i + 1)), h('span', null, it.label, sub));
      });
      var extra = [];
      if (formHas('seo')) extra.push({ key: 'seo', label: 'SEO: tiêu đề, mô tả trên Google, ảnh chia sẻ' });
      parts.notes.forEach(function (n) { if (formHas(n.key)) extra.push({ key: n.key, label: formLabel(n.key) || n.key, note: n.note }); });
      return h('div', { style: S.side(overlay), role: 'navigation', 'aria-label': 'Các phần của trang' },
        h('div', { style: S.sideHead }, 'Trang này gồm ' + parts.items.length + ' phần',
          h('button', { type: 'button', onClick: this.toggleMap, title: 'Ẩn danh sách', 'aria-label': 'Ẩn danh sách các phần',
            style: { marginLeft: 'auto', border: 0, background: 'none', color: P.muted, font: 'inherit', fontSize: '18px', cursor: 'pointer', lineHeight: 1 } }, '×')),
        h('div', { style: S.sideHint }, 'Theo thứ tự từ trên xuống, số khớp với số đỏ trên trang. Bấm một phần để mở đúng ô sửa.'),
        rows,
        extra.length ? h('div', { style: S.group }, 'Không hiện trên trang này') : null,
        extra.map(function (x, i) {
          return h('button', { key: 'x' + i, type: 'button', style: S.row(false, false, true), title: x.note || '',
            onClick: function () { jumpToField(x.key); } },
            h('span', { style: { flex: 'none', width: '22px', textAlign: 'center' } }, '•'), h('span', null, x.label, x.note ? h('span', { style: S.sub }, x.note) : null));
        }));
    },
    render: function () {
      var self = this, st = this.state, res = st.result, e = this.props.entry;
      var P = pal(), S = styles(P);
      var errs = (res && res.loi) || [], warns = (res && res.canh) || [];
      var W = st.size[0] || 800, H = st.size[1] || 600;
      var mobile = st.device === 'dien-thoai';
      var pw = mobile ? 390 : 1280, scale = Math.min(1, (W - (mobile ? 24 : 0)) / pw);
      this.scale = scale;
      var frameStyle = {
        position: 'absolute', top: mobile ? '12px' : 0, left: mobile ? Math.max(12, (W - pw * scale) / 2) + 'px' : 0,
        width: pw + 'px', height: ((H - (mobile ? 24 : 0)) / scale) + 'px', border: 0, background: '#fff',
        transform: 'scale(' + scale + ')', transformOrigin: '0 0',
        borderRadius: mobile ? '18px' : 0, boxShadow: mobile ? '0 10px 30px rgba(0,0,0,.18)' : 'none',
      };
      var status, color;
      if (engine.error) { status = 'Không tải được bộ dựng trang'; color = RED; }
      else if (!engine.ready) { status = 'Đang tải bộ dựng trang…'; color = P.wait; }
      else if (st.status === 'xong') { status = 'Mô phỏng trực tiếp' + (res && res.ms ? ' · ' + (res.ms / 1000).toFixed(1).replace('.', ',') + ' giây' : ''); color = P.ok; }
      else { status = 'Đang dựng…'; color = P.wait; }
      var path = res && res.path != null ? res.path : '';
      var draft = e.getIn && e.getIn(['data', 'nhap']);
      var hasParts = !!(st.parts && st.parts.items.length);
      var showSide = st.map && hasParts && res && res.html;
      var overlay = (this.paneW || 0) < 900; // khung hẹp: danh sách nổi trên trang, tự thu lại sau khi chọn một phần
      return h('div', { style: S.wrap, ref: function (el) { if (el) self.paneW = el.clientWidth; } },
        h('div', { style: S.bar },
          h('span', { style: S.dot(color), title: status }),
          h('span', { style: { fontWeight: 600, whiteSpace: 'nowrap', flex: 'none' } }, st.label ? status.split(' · ')[0] : status),
          st.label ? h('span', { style: S.chip, title: st.label }, '✎ ' + st.label) : null,
          hasParts ? h('button', { type: 'button', style: S.btn(st.map), 'aria-pressed': !!st.map, onClick: this.toggleMap,
            title: 'Danh sách mọi phần sửa được của trang này, theo thứ tự từ trên xuống' }, '☰ Các phần (' + st.parts.items.length + ')') : null,
          h('div', { style: Object.assign({}, S.seg, hasParts ? {} : { marginLeft: 'auto' }), role: 'group', 'aria-label': 'Xem trên' },
            h('button', { type: 'button', style: S.segBtn(!mobile), 'aria-pressed': !mobile, onClick: function () { self.setDevice('may-tinh'); } }, 'Máy tính'),
            h('button', { type: 'button', style: S.segBtn(mobile), 'aria-pressed': mobile, onClick: function () { self.setDevice('dien-thoai'); } }, 'Điện thoại')),
          res && !/\.html$/.test(path) && !draft && !e.get('newRecord') ? h('a', { href: SITE + path, target: '_blank', rel: 'noopener', style: S.link, title: 'Mở trang đang chạy trên website (chưa có thay đổi chưa lưu)' }, '↗') : null),
        errs.length ? h('div', { style: S.panel(P.errBg, P.errInk, P.errLine) },
          h('strong', null, 'Nếu Lưu bây giờ, website sẽ KHÔNG cập nhật (giữ bản cũ) vì ' + errs.length + ' lỗi:'),
          h('ul', { style: { margin: '6px 0 0', paddingLeft: '18px' } }, errs.map(function (x, i) {
            return h('li', { key: i }, x[0] ? h('strong', null, x[0] + ': ') : null, x[1]);
          }))) : null,
        warns.length ? h('div', { style: S.panel(P.warnBg, P.warnInk, P.warnLine) },
          h('strong', null, 'Lưu ý: '), warns.map(function (x) { return (x[0] ? x[0] + ': ' : '') + x[1]; }).join(' · ')) : null,
        st.seo ? this.seoCard(S, P) : null,
        st.note ? h('div', { style: S.panel(P.soft, P.muted, P.softLine) }, 'ⓘ ' + st.note) : null,
        h('div', { style: S.body },
          showSide ? this.sidePanel(S, P, overlay) : null,
          h('div', { style: S.stage, ref: function (el) { self.stage = el; } },
            h('iframe', { ref: function (el) { self.frame = el; }, title: 'Mô phỏng trang', style: frameStyle }),
            !res || !res.html ? h('div', { style: S.msg },
              engine.error ? h('div', null, h('strong', null, 'Không tải được bộ dựng trang.'), h('br'), engine.error, h('br'),
                'Vẫn sửa và Lưu bình thường được; xem kết quả trên website sau khi Lưu khoảng 1 phút.')
                : res && !res.html ? h('div', null, 'Chưa dựng được trang – xem các lỗi ở trên.')
                  : h('div', null, h('strong', null, 'Đang chuẩn bị bản mô phỏng…'), h('br'), 'Lần đầu khoảng 10 giây (tải bộ dựng trang), các lần sau gần như tức thì.')) : null)));
    },
  });

  /* Dùng cho mọi loại nội dung: Sveltia tìm khung xem trước theo tên tệp (mục nhiều tệp) hoặc tên mục (bài viết, lĩnh vực…).
     Build kiểm danh sách này đủ mọi tên trong admin/config.yml. */
  var PREVIEW_NAMES = ['dich_vu', 'bai_viet', 'trang', 'trang-chu', 'gioi-thieu', 'vi-sao-chon-chung-toi', 'quy-trinh-lam-viec', 'lien-he',
    'trang-hoi-dap', 'kho-cau-hoi', 'chinh_sach_bao_mat', 'dieu_khoan_su_dung', 'mien_tru_trach_nhiem', 'trang_404',
    'cong_ty', 'menu', 'anh_thuong_hieu', 'cau_chu', 'seo', 'theo_doi', 'chuyen_huong'];
  PREVIEW_NAMES.forEach(function (n) { window.CMS.registerPreviewTemplate(n, Preview); });
  // Tải sẵn bộ dựng trang khi người dùng mở trang quản trị, để lúc mở bài đầu tiên đã sẵn sàng
  if ('requestIdleCallback' in window) window.requestIdleCallback(startEngine, { timeout: 4000 }); else setTimeout(startEngine, 3000);
})();
