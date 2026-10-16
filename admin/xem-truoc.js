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
    hoi_dap_hub: { ghi_chu_cuoi: ['.faq-aside', 'Ghi chú cuối'], tim_hieu_them: ['.faq-aside', 'Tìm hiểu thêm'] },
    hoi_dap: { cau_hoi: function (p) { return p.length > 1 ? ['.faq__item:nth-of-type(' + (+p[1] + 1) + ')', 'Câu hỏi ' + (+p[1] + 1)] : ['.faq', 'Câu hỏi thường gặp']; } },
    van_ban: { tieu_de: HERO, nhan: HERO, tieu_de_trang: HERO, mo_dau: HERO, ngay_cap_nhat: HERO, body: ['.legal-doc', 'Nội dung văn bản'],
      noi_dung: ['main', 'Nội dung trang 404'] },
    cong_ty: { hotline: HEAD, ten_viet_tat: HEAD, gioi_thieu_chan_trang: FOOT, '*': FOOT },
    menu: { menu: HEAD, goi_y_tim_kiem: 'Gợi ý hiện trong ô tìm kiếm (bấm kính lúp ở đầu trang).', '*': FOOT },
    cau_chu: { lien_he_cuoi_trang: BAND, mien_tru_chan_trang: FOOT, '*': 'Câu chữ này dùng ở trang lĩnh vực và cuối bài viết.' },
    theo_doi: { '*': 'Mã theo dõi không hiện trên trang.' },
    chuyen_huong: { '*': 'Chuyển hướng không hiện trên trang: địa chỉ cũ tự chuyển sang trang mới sau khi Lưu.' },
    anh_thuong_hieu: { logo: HEAD, '*': ['[data-cms="cac_khoi.0"]', 'Ảnh luật sư ở đầu trang chủ'] },
  };
  function mapName(entry) {
    var path = entry.get('path') || '';
    var m = path.match(/content\/(cai-dat|trang-tong-hop|trang-van-ban)\/([^/]+)\.(yml|md)$/);
    if (m && m[1] === 'cai-dat') return m[2].replace(/-/g, '_');
    if (m && m[1] === 'trang-tong-hop') return { 'dich-vu': 'dich_vu_hub', 'kien-thuc-phap-ly': 'kien_thuc', 'cau-hoi-thuong-gap': 'hoi_dap_hub' }[m[2]];
    if (m && m[1] === 'trang-van-ban') return 'van_ban';
    return entry.get('collection');
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
    '[data-cms]{cursor:pointer}a{cursor:pointer}';

  function prepareHtml(html, base) {
    return html
      .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '') // bỏ JS của site, mã theo dõi: mô phỏng chỉ để nhìn
      .replace(/<head>/i, '<head><base href="' + base + '"><style id="cms-style">' + PAGE_CSS + '</style>');
  }

  function morph(doc, html) {
    var nd = new DOMParser().parseFromString(html, 'text/html');
    doc.title = nd.title;
    var A = doc.querySelector('main'), B = nd.querySelector('main');
    var top = function (d) { return [].filter.call(d.body.children, function (e) { return e.id !== 'cms-khung' && e.id !== 'cms-tro'; }); };
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
    b.classList.toggle('trong', r.top + w.scrollY < 40); // sát mép trên: đặt nhãn bên trong khung
  }

  /* ---------------- Thành phần React ---------------- */
  var css = function (o) { return o; };
  var S = {
    wrap: css({ position: 'fixed', inset: 0, display: 'flex', flexDirection: 'column', background: '#efe9e0', font: '14px/1.4 "Be Vietnam Pro",system-ui,-apple-system,"Segoe UI",sans-serif', color: '#2b1d21' }),
    bar: css({ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 12px', background: '#fffdf9', borderBottom: '1px solid #e6ddd2', minHeight: '48px', boxSizing: 'border-box' }),
    dot: function (c) { return { width: '9px', height: '9px', borderRadius: '50%', background: c, flex: 'none' }; },
    chip: css({ display: 'block', flex: '0 1 auto', minWidth: 0, padding: '5px 10px', borderRadius: '999px', background: '#fbeaea', color: '#7a0007', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }),
    seg: css({ display: 'inline-flex', flex: 'none', border: '1px solid #d9cfc3', borderRadius: '8px', overflow: 'hidden', marginLeft: 'auto' }),
    segBtn: function (on) { return { border: 0, padding: '6px 11px', font: 'inherit', fontWeight: 600, cursor: 'pointer', background: on ? '#2b1d21' : '#fff', color: on ? '#fff' : '#2b1d21' }; },
    link: css({ color: RED, fontWeight: 600, textDecoration: 'none', whiteSpace: 'nowrap' }),
    stage: css({ position: 'relative', flex: 1, overflow: 'hidden' }),
    msg: css({ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', padding: '24px', textAlign: 'center', color: '#5f5557' }),
    panel: function (bg, fg, bd) { return { margin: '8px 12px 0', padding: '10px 12px', borderRadius: '8px', background: bg, color: fg, border: '1px solid ' + bd, maxHeight: '30vh', overflow: 'auto' }; },
  };

  var Preview = window.createClass({
    getInitialState: function () {
      var dev = 'may-tinh';
      try { dev = localStorage.getItem('lsn-xem-truoc-thiet-bi') || dev; } catch (e) { /* trình duyệt chặn lưu trữ */ }
      return { result: null, status: engine.ready ? 'dang-dung' : 'tai', key: focus.key, device: dev, size: [0, 0], hover: '', note: '', label: '' };
    },
    componentDidMount: function () {
      var self = this;
      this.onEngine = function () { self.forceUpdate(); };
      this.onKey = function (k) { self.setState({ key: k }, function () { self.highlight(true); }); };
      this.onHover = function (k) { self.hoverForm(k); };
      engine.subs.push(this.onEngine); focus.subs.push(this.onKey); hover.subs.push(this.onHover);
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
      var name = mapName(this.props.entry);
      doc.addEventListener('click', function (e) {
        var a = e.target.closest('a,button,summary,form');
        if (a) e.preventDefault(); // mô phỏng: không rời trang
        var t = e.target.closest('[data-cms]');
        if (t && !/^@/.test(t.getAttribute('data-cms'))) jumpToField(t.getAttribute('data-cms'));
        else if (t) self.setState({ note: 'Phần này sửa ở Cài đặt → ' + (t.getAttribute('data-cms') === '@chan-trang' ? 'Menu và chân trang / Thông tin công ty' : 'Menu và chân trang') + '.' });
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
      void name;
    },
    highlight: function (scroll) {
      var doc = this.frame && this.frame.contentDocument;
      if (!doc || !doc.body) return;
      doc.documentElement.style.setProperty('--cms-s', String(this.scale || 1));
      var r = resolve(doc, this.state.key, mapName(this.props.entry));
      var el = r && r.el, label = el ? r.label : '';
      this.activeKey = el ? el.getAttribute('data-cms') || '' : '';
      box(doc, 'cms-khung', el, label ? 'Đang sửa · ' + label : '');
      if (el && scroll) {
        var vh = doc.defaultView.innerHeight;
        el.scrollIntoView({ block: el.getBoundingClientRect().height > vh * 0.8 ? 'start' : 'center', behavior: 'smooth' });
      }
      var note = r && r.note ? r.note : '';
      if (note !== this.state.note || label !== this.state.label || !!(r && r.seo) !== !!this.state.seo) {
        this.setState({ note: note, label: label, seo: !!(r && r.seo) });
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
    setDevice: function (d) {
      try { localStorage.setItem('lsn-xem-truoc-thiet-bi', d); } catch (e) { /* bỏ qua */ }
      this.setState({ device: d }, this.highlight.bind(this, false));
    },
    seoCard: function () {
      var doc = this.frame && this.frame.contentDocument, res = this.state.result;
      if (!doc || !res) return null;
      var t = doc.title || '', meta = doc.querySelector('meta[name=description]'), d = meta ? meta.getAttribute('content') : '';
      var url = SITE.replace(/^https?:\/\//, '').replace(/\/$/, '') + '/' + (res.path || '');
      var count = function (s, max) { return h('span', { style: { color: s.length > max ? RED : '#2e7d32', fontWeight: 600 } }, s.length + '/' + max + ' ký tự'); };
      return h('div', { style: S.panel('#fff', '#2b1d21', '#d9cfc3') },
        h('div', { style: { fontSize: '12px', color: '#5f5557', marginBottom: '6px' } }, 'Mẫu kết quả trên Google (ước lượng) · tiêu đề ', count(t, 70), ' · mô tả ', count(d, 160)),
        h('div', { style: { fontSize: '13px', color: '#202124' } }, url.replace(/\//g, ' › ').replace(/ › $/, '')),
        h('div', { style: { fontSize: '19px', color: '#1a0dab', lineHeight: 1.3, margin: '2px 0' } }, t.length > 70 ? t.slice(0, 67) + '…' : t),
        h('div', { style: { fontSize: '14px', color: '#4d5156' } }, d.length > 160 ? d.slice(0, 157) + '…' : d));
    },
    render: function () {
      var self = this, st = this.state, res = st.result, e = this.props.entry;
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
      else if (!engine.ready) { status = 'Đang tải bộ dựng trang…'; color = '#c58a00'; }
      else if (st.status === 'xong') { status = 'Mô phỏng trực tiếp' + (res && res.ms ? ' · ' + (res.ms / 1000).toFixed(1).replace('.', ',') + ' giây' : ''); color = '#2e7d32'; }
      else { status = 'Đang dựng…'; color = '#c58a00'; }
      var path = res && res.path != null ? res.path : '';
      var draft = e.getIn && e.getIn(['data', 'nhap']);
      return h('div', { style: S.wrap },
        h('div', { style: S.bar },
          h('span', { style: S.dot(color), title: status }),
          h('span', { style: { fontWeight: 600, whiteSpace: 'nowrap', flex: 'none' } }, st.label ? status.split(' · ')[0] : status),
          st.label ? h('span', { style: S.chip, title: st.label }, '✎ ' + st.label) : null,
          h('div', { style: S.seg, role: 'group', 'aria-label': 'Xem trên' },
            h('button', { type: 'button', style: S.segBtn(!mobile), 'aria-pressed': !mobile, onClick: function () { self.setDevice('may-tinh'); } }, 'Máy tính'),
            h('button', { type: 'button', style: S.segBtn(mobile), 'aria-pressed': mobile, onClick: function () { self.setDevice('dien-thoai'); } }, 'Điện thoại')),
          res && !/\.html$/.test(path) && !draft && !e.get('newRecord') ? h('a', { href: SITE + path, target: '_blank', rel: 'noopener', style: S.link, title: 'Mở trang đang chạy trên website (chưa có thay đổi chưa lưu)' }, '↗') : null),
        errs.length ? h('div', { style: S.panel('#fdecec', '#7a0007', '#f3b9b9') },
          h('strong', null, 'Nếu Lưu bây giờ, website sẽ KHÔNG cập nhật (giữ bản cũ) vì ' + errs.length + ' lỗi:'),
          h('ul', { style: { margin: '6px 0 0', paddingLeft: '18px' } }, errs.map(function (x, i) {
            return h('li', { key: i }, x[0] ? h('strong', null, x[0] + ': ') : null, x[1]);
          }))) : null,
        warns.length ? h('div', { style: S.panel('#fff6e0', '#6b4a00', '#f0d48a') },
          h('strong', null, 'Lưu ý: '), warns.map(function (x) { return (x[0] ? x[0] + ': ' : '') + x[1]; }).join(' · ')) : null,
        st.seo ? this.seoCard() : null,
        st.note ? h('div', { style: S.panel('#f4f0ea', '#5f5557', '#e1d8cc') }, 'ⓘ ' + st.note) : null,
        h('div', { style: S.stage, ref: function (el) { self.stage = el; } },
          h('iframe', { ref: function (el) { self.frame = el; }, title: 'Mô phỏng trang', style: frameStyle }),
          !res || !res.html ? h('div', { style: S.msg },
            engine.error ? h('div', null, h('strong', null, 'Không tải được bộ dựng trang.'), h('br'), engine.error, h('br'),
              'Vẫn sửa và Lưu bình thường được; xem kết quả trên website sau khi Lưu khoảng 1 phút.')
              : res && !res.html ? h('div', null, 'Chưa dựng được trang – xem các lỗi ở trên.')
                : h('div', null, h('strong', null, 'Đang chuẩn bị bản mô phỏng…'), h('br'), 'Lần đầu khoảng 10 giây (tải bộ dựng trang), các lần sau gần như tức thì.')) : null));
    },
  });

  /* Dùng cho mọi loại nội dung: tên chuyên mục (bài viết, trang, lĩnh vực…) và tên từng tệp (cài đặt, trang tổng hợp…) */
  ['bai_viet', 'dich_vu', 'hoi_dap', 'trang', 'kien_thuc', 'chinh_sach_bao_mat', 'dieu_khoan_su_dung', 'mien_tru_trach_nhiem',
    'trang_404', 'cong_ty', 'menu', 'cau_chu', 'seo', 'theo_doi', 'chuyen_huong', 'anh_thuong_hieu'].forEach(function (n) {
    window.CMS.registerPreviewTemplate(n, Preview);
  });
  // Tải sẵn bộ dựng trang khi người dùng mở trang quản trị, để lúc mở bài đầu tiên đã sẵn sàng
  if ('requestIdleCallback' in window) window.requestIdleCallback(startEngine, { timeout: 4000 }); else setTimeout(startEngine, 3000);
})();
