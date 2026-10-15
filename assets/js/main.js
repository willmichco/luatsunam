/* =====================================================================
   LSN LAW FIRM – Công Ty Luật TNHH Luật Sư Nam
   ===================================================================== */
(function () {
  'use strict';

  var doc = document.documentElement;
  doc.classList.add('js');
  var ROOT = doc.getAttribute('data-root') || '';
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $$(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }

  /* Trang 404 dùng thẻ <base>: giữ các liên kết #neo trong trang hiện tại */
  if ($('base')) {
    $$('a[href^="#"]').forEach(function (a) { a.setAttribute('href', location.pathname + location.search + a.getAttribute('href')); });
  }

  /* ---------- Thông báo nhỏ ---------- */
  var toastEl = null, toastTimer = null;
  function toast(msg) {
    if (!toastEl) {
      toastEl = document.createElement('div');
      toastEl.className = 'toast';
      toastEl.setAttribute('role', 'status');
      document.body.appendChild(toastEl);
    }
    toastEl.innerHTML = '<svg class="ico" aria-hidden="true"><use href="#i-check"/></svg><span></span>';
    toastEl.lastChild.textContent = msg;
    requestAnimationFrame(function () { toastEl.classList.add('is-visible'); });
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('is-visible'); }, 3200);
  }
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (resolve, reject) {
      var ta = document.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy') ? resolve() : reject(); } catch (err) { reject(err); }
      ta.remove();
    });
  }

  /* ---------- Giờ làm việc theo giờ Việt Nam (UTC+7); ngày, giờ lấy từ CMS: <html data-gio="1,2,3,4,5|480|1050"> ---------- */
  (function () {
    var els = $$('[data-open-now]');
    if (!els.length) return;
    var cfg = (doc.getAttribute('data-gio') || '1,2,3,4,5|480|1050').split('|');
    var days = cfg[0].split(',').map(Number), opens = +cfg[1], closes = +cfg[2];
    var DAY = ['Chủ nhật', 'thứ Hai', 'thứ Ba', 'thứ Tư', 'thứ Năm', 'thứ Sáu', 'thứ Bảy'];
    var hhmm = ('0' + Math.floor(opens / 60)).slice(-2) + ':' + ('0' + opens % 60).slice(-2);
    function update() {
      var vn = new Date(Date.now() + 7 * 36e5); // đọc bằng getUTC* = giờ Việt Nam, không phụ thuộc múi giờ máy
      var day = vn.getUTCDay(), mins = vn.getUTCHours() * 60 + vn.getUTCMinutes();
      var workday = days.indexOf(day) >= 0;
      var open = workday && mins >= opens && mins < closes;
      var next = 'hôm nay';
      if (!(workday && mins < opens)) {
        for (var d = 1; d <= 7 && days.indexOf((day + d) % 7) < 0; d++) {}
        var nd = (day + d) % 7;
        next = nd === 1 ? 'thứ Hai' : (d === 1 ? 'sáng mai' : DAY[nd]);
      }
      var text = open ? 'Đang trong giờ làm việc' : 'Ngoài giờ · làm việc lại ' + hhmm + ' ' + next;
      els.forEach(function (el) {
        el.textContent = text;
        el.classList.toggle('is-closed', !open);
        el.classList.add('is-ready');
      });
    }
    update();
    setInterval(update, 60000);
  })();

  /* ---------- Máy tính: bấm số điện thoại thì chép số, vì nhiều máy không gọi được ---------- */
  if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    document.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('a[href^="tel:"]');
      if (!a) return;
      var num = a.getAttribute('href').slice(4).replace(/^(\d{4})(\d{3})(\d{3})$/, '$1 $2 $3');
      copyText(num).then(function () { toast('Đã chép số ' + num + ' – gọi bằng điện thoại hoặc nhắn Zalo'); }, function () {});
    });
  }

  /* ---------- Header, nút nổi ---------- */
  var header = $('#site-header');
  var toTop = $('#to-top');
  var floating = $('.floating');
  function onScroll() {
    var y = window.scrollY;
    if (header) header.classList.toggle('is-scrolled', y > 10);
    if (toTop) toTop.classList.toggle('is-visible', y > 600);
    if (floating) floating.classList.toggle('is-visible', y > 300);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  if (toTop) toTop.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' }); });

  /* ---------- Navigation: disclosure buttons, mouse and keyboard ---------- */
  var nav = $('#nav');
  var burger = $('#burger');
  var backdrop = null;
  var mobileQuery = window.matchMedia('(max-width: 1080px)');
  var toggles = $$('.nav__toggle');
  function closeSubs(except) {
    toggles.forEach(function (btn) {
      if (btn === except) return;
      btn.parentElement.classList.remove('is-open');
      btn.setAttribute('aria-expanded', 'false');
    });
  }
  function setSub(btn, open) {
    if (open) closeSubs(btn);
    btn.parentElement.classList.toggle('is-open', open);
    btn.setAttribute('aria-expanded', String(open));
  }
  function setNav(open) {
    if (!nav || !burger) return;
    nav.classList.toggle('is-open', open);
    burger.setAttribute('aria-expanded', String(open));
    burger.setAttribute('aria-label', open ? 'Đóng menu' : 'Mở menu');
    $('use', burger).setAttribute('href', open ? '#i-close' : '#i-menu');
    document.body.classList.toggle('no-scroll', open);
    if (open && !backdrop) {
      backdrop = document.createElement('div');
      backdrop.className = 'nav-backdrop';
      backdrop.addEventListener('click', function () { setNav(false); });
      document.body.appendChild(backdrop);
      var current = $('.nav__sublink[aria-current="page"]', nav);
      if (current) setSub($('.nav__toggle', current.closest('.has-sub')), true);
    } else if (!open) {
      if (backdrop) backdrop.remove();
      backdrop = null;
      closeSubs();
      burger.focus();
    }
  }
  if (burger) burger.addEventListener('click', function () { setNav(!nav.classList.contains('is-open')); });
  window.addEventListener('resize', function () {
    if (!mobileQuery.matches && nav && nav.classList.contains('is-open')) setNav(false);
  });
  toggles.forEach(function (btn) {
    var item = btn.parentElement;
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      setSub(btn, btn.getAttribute('aria-expanded') !== 'true');
    });
    btn.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') {
        e.preventDefault(); setSub(btn, true); requestAnimationFrame(function () { $('.nav__sublink', item).focus(); });
      }
    });
    item.addEventListener('focusout', function () {
      setTimeout(function () {
        if (!mobileQuery.matches && !item.contains(document.activeElement)) setSub(btn, false);
      }, 0);
    });
  });
  document.addEventListener('click', function (e) {
    if (!mobileQuery.matches && !e.target.closest('.nav__item')) closeSubs();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      var item = document.activeElement.closest('.nav__item.is-open');
      if (item) $('.nav__toggle', item).focus();
    }
    if (e.key !== 'Tab') return;
    var overlay = $('.overlay:not([hidden])');
    var scope = overlay || (mobileQuery.matches && nav && nav.classList.contains('is-open') ? nav : null);
    if (!scope) return;
    var controls = $$('a[href],button,input,select,textarea,[tabindex="0"]', scope).filter(function (el) {
      return !el.disabled && el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden';
    });
    if (scope === nav) controls.push(burger);
    var first = controls[0], last = controls[controls.length - 1];
    if (e.shiftKey && (document.activeElement === first || !controls.includes(document.activeElement))) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && (document.activeElement === last || !controls.includes(document.activeElement))) { e.preventDefault(); first.focus(); }
  });

  /* ---------- Hiện dần khi cuộn ---------- */
  var reveals = $$('.reveal');
  if ('IntersectionObserver' in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        var siblings = $$(':scope > .reveal', el.parentElement);
        el.style.transitionDelay = Math.min(Math.max(siblings.indexOf(el), 0), 4) * 60 + 'ms';
        el.classList.add('is-in');
        obs.unobserve(el);
      });
    }, { threshold: 0.06, rootMargin: '0px 0px -40px 0px' });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('is-in'); });
  }

  /* ---------- Cửa sổ tìm kiếm ---------- */
  var lastFocus = null;
  function openOverlay(el) {
    lastFocus = document.activeElement;
    el.hidden = false;
    document.body.classList.add('no-scroll');
    var first = $('input:not([type=hidden]):not([tabindex="-1"]), select, textarea', el);
    setTimeout(function () { if (first) first.focus(); }, 30);
  }
  function closeOverlay(el) {
    el.hidden = true;
    if (!nav || !nav.classList.contains('is-open')) document.body.classList.remove('no-scroll');
    if (lastFocus) lastFocus.focus();
  }
  var search = $('#search');
  function openSearch() {
    if (!search || !search.hidden) return;
    closeSubs();
    if (nav && nav.classList.contains('is-open')) setNav(false);
    openOverlay(search);
    loadIndex();
  }
  $$('[data-open-search]').forEach(function (b) { b.addEventListener('click', openSearch); });
  /* Phím tắt: "/" hoặc Ctrl/⌘ + K */
  document.addEventListener('keydown', function (e) {
    var t = e.target, typing = t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName));
    if ((e.key === '/' && !typing && !e.ctrlKey && !e.metaKey && !e.altKey) || ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K'))) {
      e.preventDefault();
      openSearch();
    }
  });
  $$('.overlay').forEach(function (ov) {
    ov.addEventListener('click', function (e) { if (e.target === ov || e.target.closest('[data-close]')) closeOverlay(ov); });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    $$('.overlay').forEach(function (ov) { if (!ov.hidden) closeOverlay(ov); });
    if (nav && nav.classList.contains('is-open')) setNav(false);
    closeSubs();
  });

  /* ---------- Tìm kiếm trong website ---------- */
  var index = null;
  var qInput = $('#search-q');
  var results = $('#search-results');
  function fold(s) {
    return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd');
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function loadIndex() {
    if (index) return Promise.resolve(index);
    return fetch(ROOT + 'assets/search-index.json').then(function (r) { return r.json(); }).then(function (data) {
      index = data.map(function (d) { d._t = fold(d.t); d._all = fold(d.t + ' ' + d.d + ' ' + d.k + ' ' + d.s); return d; });
      return index;
    }).catch(function () { index = []; return index; });
  }
  function runSearch() {
    var q = fold(qInput.value.trim());
    if (!q) { results.innerHTML = ''; return; }
    var words = q.split(/\s+/);
    loadIndex().then(function (idx) {
      var hits = idx.map(function (d) {
        var score = 0;
        words.forEach(function (w) {
          if (d._t.indexOf(w) > -1) score += 5;
          else if (d._all.indexOf(w) > -1) score += 1;
          else score -= 10;
        });
        if (d._t.indexOf(q) > -1) score += 8;
        return { d: d, s: score };
      }).filter(function (h) { return h.s > 0; }).sort(function (a, b) { return b.s - a.s; }).slice(0, 8);
      results.innerHTML = hits.length ? hits.map(function (h) {
        return '<li><a href="' + ROOT + h.d.u + '"><em>' + esc(h.d.s || 'Trang') + '</em><strong>' + esc(h.d.t) + '</strong><small>' + esc(h.d.d) + '</small></a></li>';
      }).join('') : '<li class="search__empty">Không tìm thấy nội dung phù hợp. Hãy thử từ khóa khác hoặc <a href="' + ROOT + 'lien-he/">hỏi trực tiếp luật sư</a>.</li>';
    });
  }
  if (qInput) {
    qInput.addEventListener('input', runSearch);
    $('.search__form').addEventListener('submit', function (e) {
      e.preventDefault();
      var first = $('a', results);
      if (first) window.location.href = first.getAttribute('href');
    });
    /* Mũi tên lên/xuống: di chuyển giữa ô tìm kiếm và các kết quả */
    search.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
      var links = $$('a', results);
      if (!links.length) return;
      var i = links.indexOf(document.activeElement);
      e.preventDefault();
      if (e.key === 'ArrowDown') (links[i + 1] || links[0]).focus();
      else if (i <= 0) qInput.focus();
      else links[i - 1].focus();
    });
  }

  /* ---------- Bản đồ: chỉ tải khi người dùng bấm ---------- */
  $$('.map[data-map]').forEach(function (box) {
    var btn = $('.map__load', box);
    btn.addEventListener('click', function () {
      var f = document.createElement('iframe');
      f.src = box.getAttribute('data-map');
      f.title = 'Bản đồ vị trí văn phòng Công Ty Luật TNHH Luật Sư Nam';
      f.loading = 'lazy';
      f.referrerPolicy = 'no-referrer-when-downgrade';
      f.allowFullscreen = true;
      box.appendChild(f);
      btn.remove();
    });
  });

  /* ---------- Mục lục bài viết, thanh mục trang dịch vụ: đánh dấu mục đang đọc ---------- */
  function spyOn(links) {
    if (!links.length || !('IntersectionObserver' in window)) return;
    var map = {}; // một mục có thể có nhiều liên kết (mục lục cột bên và mục lục đầu bài trên điện thoại)
    links.forEach(function (a) { var id = a.getAttribute('href').slice(1); (map[id] = map[id] || []).push(a); });
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting || !map[e.target.id]) return;
        links.forEach(function (a) { a.classList.remove('is-active'); });
        map[e.target.id].forEach(function (a) {
          a.classList.add('is-active');
          var bar = a.parentElement;
          if (bar.scrollWidth > bar.clientWidth) bar.scrollTo({ left: a.offsetLeft - 16, behavior: reduceMotion ? 'auto' : 'smooth' });
        });
      });
    }, { rootMargin: '-25% 0px -65% 0px' });
    Object.keys(map).forEach(function (id) { var el = document.getElementById(id); if (el) spy.observe(el); });
  }
  spyOn($$('.toc a[href^="#"]'));
  spyOn($$('.subnav a[href^="#"]'));

  /* Thanh mục trang dịch vụ: báo còn mục khuất bên phải */
  $$('.subnav .container').forEach(function (bar) {
    function edge() { bar.classList.toggle('has-more', bar.scrollLeft + bar.clientWidth < bar.scrollWidth - 4); }
    bar.addEventListener('scroll', edge, { passive: true });
    window.addEventListener('resize', edge);
    edge();
  });

  /* ---------- Bài viết: mục lục đầu bài, tiến độ đọc, chia sẻ ---------- */
  $$('.toc-mobile a').forEach(function (a) {
    a.addEventListener('click', function () { a.closest('details').open = false; });
  });
  var articleBody = $('#noi-dung-bai-viet');
  if (articleBody && header) {
    var bar = document.createElement('div');
    bar.className = 'read-progress';
    bar.setAttribute('aria-hidden', 'true');
    bar.innerHTML = '<span></span>';
    header.appendChild(bar);
    var fill = bar.firstChild, ticking = false;
    var progress = function () {
      ticking = false;
      var r = articleBody.getBoundingClientRect(), total = r.height - window.innerHeight * 0.6;
      fill.style.transform = 'scaleX(' + Math.min(1, Math.max(0, -r.top / Math.max(total, 1))) + ')';
    };
    window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(progress); } }, { passive: true });
    progress();
  }
  $$('[data-share]').forEach(function (btn) {
    btn.classList.add('is-ready');
    btn.addEventListener('click', function () {
      var data = { title: document.title, url: location.href.split('#')[0] };
      if (navigator.share) { navigator.share(data).catch(function () {}); return; }
      copyText(data.url).then(function () { toast('Đã chép liên kết bài viết – dán vào Zalo, Messenger để gửi'); }, function () {});
    });
  });

  /* ---------- Mở câu hỏi khi truy cập bằng liên kết #id ---------- */
  function openFromHash() {
    var id = decodeURIComponent(location.hash.slice(1));
    if (!id) return;
    var el = document.getElementById(id);
    if (el && el.tagName === 'DETAILS') el.open = true;
  }
  window.addEventListener('hashchange', openFromHash);
  openFromHash();

  /* ---------- Năm bản quyền ---------- */
  $$('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();
