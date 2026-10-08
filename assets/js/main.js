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

  /* ---------- Hero slider (trang chủ) ---------- */
  var slides = $$('.hero__slide');
  var dots = $$('.hero__dots button');
  if (slides.length > 1) {
    var current = 0, timer = null;
    var go = function (i) {
      current = (i + slides.length) % slides.length;
      slides.forEach(function (s, k) { s.classList.toggle('is-active', k === current); s.setAttribute('aria-hidden', String(k !== current)); });
      dots.forEach(function (d, k) { d.classList.toggle('is-active', k === current); d.setAttribute('aria-selected', String(k === current)); });
    };
    var stop = function () { clearInterval(timer); };
    var play = function () { if (!reduceMotion) { stop(); timer = setInterval(function () { go(current + 1); }, 6500); } };
    dots.forEach(function (d, k) { d.addEventListener('click', function () { go(k); play(); }); });
    var hero = $('.hero');
    hero.addEventListener('mouseenter', stop);
    hero.addEventListener('mouseleave', play);
    go(0);
    play();
  }

  /* ---------- Hiện dần khi cuộn + đếm số ---------- */
  function countUp(el) {
    var target = parseInt(el.getAttribute('data-count'), 10);
    var pad = parseInt(el.getAttribute('data-pad') || '0', 10);
    var fmt = function (n) { var s = String(n); while (s.length < pad) s = '0' + s; return s; };
    if (reduceMotion) { el.textContent = fmt(target); return; }
    var start = null, dur = 1400;
    function step(t) {
      if (!start) start = t;
      var p = Math.min((t - start) / dur, 1);
      el.textContent = fmt(Math.round(target * (1 - Math.pow(1 - p, 3))));
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  var reveals = $$('.reveal');
  var counters = $$('[data-count]');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        if (el.classList.contains('reveal')) {
          var siblings = $$(':scope > .reveal', el.parentElement);
          el.style.transitionDelay = Math.min(Math.max(siblings.indexOf(el), 0), 5) * 70 + 'ms';
          el.classList.add('is-in');
        }
        if (el.hasAttribute('data-count')) countUp(el);
        obs.unobserve(el);
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });
    reveals.concat(counters).forEach(function (el) { io.observe(el); });
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
  $$('[data-open-search]').forEach(function (b) { b.addEventListener('click', function () { closeSubs(); if (nav && nav.classList.contains('is-open')) setNav(false); openOverlay(search); loadIndex(); }); });
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

  /* ---------- Mục lục bài viết: đánh dấu mục đang đọc ---------- */
  var tocLinks = $$('.toc a[href^="#"]');
  if (tocLinks.length && 'IntersectionObserver' in window) {
    var map = {};
    tocLinks.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        tocLinks.forEach(function (a) { a.classList.remove('is-active'); });
        if (map[e.target.id]) map[e.target.id].classList.add('is-active');
      });
    }, { rootMargin: '-20% 0px -70% 0px' });
    Object.keys(map).forEach(function (id) { var el = document.getElementById(id); if (el) spy.observe(el); });
  }

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
