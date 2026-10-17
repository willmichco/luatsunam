/* Trang Lịch sử chỉnh sửa (admin/lich-su.html).
   - Danh sách: các commit đụng tới content/ trên nhánh của CMS (mỗi lần Lưu trong trang quản trị = 1 commit), mới nhất trước.
     Lọc theo trang: ?muc=<mục CMS>&tep=<tệp> (nút "Lịch sử" trong trình soạn mở đúng trang đang sửa) hoặc ô chọn trên đầu.
   - Bấm một lần lưu: đọc bản trước và bản sau của từng tệp, so từng ô, gọi theo nhãn trong config.yml (Tiêu đề, Khối 3 · Dải cam kết…).
   - Khôi phục: tạo MỘT commit mới đưa (các) tệp về đúng bản trước lần lưu đó. Không xóa, không viết lại lịch sử:
     bản khôi phục cũng hiện trong danh sách và hoàn tác lại được. Build kiểm như mọi lần Lưu; lỗi thì site giữ bản cũ.
   Đăng nhập: dùng token GitHub trang quản trị lưu trong trình duyệt (localStorage "sveltia-cms.user", cùng địa chỉ /admin/).
   Chỉ đọc / khôi phục tệp trong content/ – không đụng code, ảnh tải lên. */
(function () {
  'use strict';
  var API = 'https://api.github.com';
  var MOI_TRANG = 20;
  var st = { repo: '', branch: 'main', token: '', cfg: null, tep: {}, thu_muc: [], loc: 'content', trang: 1, dang_tai: false };
  var $ = function (s) { return document.querySelector(s); };

  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function bao(html, kieu) {
    var d = $('#thong-bao');
    d.innerHTML = html ? '<div class="bao ' + (kieu || '') + '">' + html + '</div>' : '';
    if (html && kieu) d.scrollIntoView({ block: 'nearest' });
  }
  function token() {
    try { var u = JSON.parse(localStorage.getItem('sveltia-cms.user') || 'null'); return (u && u.token) || ''; } catch (e) { return ''; }
  }

  /* ---------------- GitHub ---------------- */
  function gh(url, o) {
    o = o || {};
    var h = { Accept: o.raw ? 'application/vnd.github.raw+json' : 'application/vnd.github+json' };
    if (st.token) h.Authorization = 'Bearer ' + st.token;
    if (o.body) h['Content-Type'] = 'application/json';
    return fetch(API + url, { method: o.method || 'GET', headers: h, body: o.body ? JSON.stringify(o.body) : undefined, cache: 'no-store' })
      .catch(function () { throw new Error('Không kết nối được GitHub. Kiểm tra mạng rồi tải lại trang này.'); }) // thay "Failed to fetch" của trình duyệt
      .then(function (r) {
        if (r.status === 404 && o.cho404) return null;
        if (!r.ok) {
          return r.text().then(function (t) {
            var e = new Error(loiGh(r.status, t, r.headers.get('x-ratelimit-remaining')));
            e.status = r.status; throw e;
          });
        }
        return o.raw ? r.text() : r.json();
      });
  }
  function loiGh(status, text, conLai) {
    if (status === 401) return 'Phiên đăng nhập đã hết hạn. Mở <a href="./">trang quản trị</a>, đăng nhập lại rồi tải lại trang này.';
    if (status === 403 && conLai === '0') return 'GitHub tạm giới hạn số lần xem (chưa đăng nhập: 60 lần/giờ). Đăng nhập <a href="./">trang quản trị</a> rồi tải lại trang này.';
    if (status === 403 || status === 404) return 'Tài khoản GitHub này không có quyền ghi vào kho nội dung, hoặc kho không tồn tại.';
    if (status === 409 || status === 422) return 'Nội dung vừa được lưu ở nơi khác cùng lúc. Tải lại trang này rồi thử lại.';
    return 'GitHub báo lỗi ' + status + '. ' + esc(String(text || '').slice(0, 200));
  }
  function repoUrl(p) { return '/repos/' + st.repo + p; }
  function encPath(p) { return p.split('/').map(encodeURIComponent).join('/'); }
  function noiDung(path, ref) { return gh(repoUrl('/contents/' + encPath(path) + '?ref=' + encodeURIComponent(ref)), { raw: true, cho404: true }); }
  // Chạy tối đa n việc cùng lúc (giữ thứ tự kết quả)
  function lan_luot(ds, n, f) {
    var kq = new Array(ds.length), i = 0;
    function chay() { var j = i++; if (j >= ds.length) return Promise.resolve(); return f(ds[j], j).then(function (x) { kq[j] = x; return chay(); }); }
    var luong = []; for (var k = 0; k < Math.min(n, ds.length); k++) luong.push(chay());
    return Promise.all(luong).then(function () { return kq; });
  }

  /* ---------------- Tệp → tên trang, khai báo ô (từ config.yml) ---------------- */
  function napCauHinh(cfg) {
    st.cfg = cfg;
    st.repo = cfg.backend && cfg.backend.repo;
    st.branch = (cfg.backend && cfg.backend.branch) || 'main';
    (cfg.collections || []).forEach(function (c) {
      (c.files || []).forEach(function (f) {
        st.tep[f.file] = { ten: f.label || f.name, nhom: c.label, fields: f.fields || [], muc: c.name, ma: f.name };
      });
      if (c.folder) {
        var ext = c.extension || (c.format === 'yaml-frontmatter' ? 'md' : 'md');
        st.thu_muc.push({ folder: c.folder.replace(/\/$/, ''), ext: ext, nhom: c.label, mot: c.label_singular || c.label,
          fields: c.fields || [], ident: c.identifier_field || 'title', muc: c.name, index: c.index_file || null });
      }
    });
  }
  function moTa(path) {
    if (st.tep[path]) return st.tep[path];
    for (var i = 0; i < st.thu_muc.length; i++) {
      var m = st.thu_muc[i];
      if (path.indexOf(m.folder + '/') !== 0) continue;
      var ten = path.slice(m.folder.length + 1);
      if (ten.indexOf('/') >= 0) break;
      if (m.index && ten === m.index.name + '.' + (m.index.extension || m.ext)) {
        return { ten: m.index.label || m.nhom, nhom: m.nhom, fields: m.index.fields || [], muc: m.muc, ma: m.index.name };
      }
      var slug = ten.replace(/\.[^.]+$/, '');
      return { ten: viHoa(m.mot) + ': ' + slug, nhom: m.nhom, fields: m.fields, ident: m.ident, muc: m.muc, ma: slug };
    }
    return { ten: path.replace(/^content\//, ''), nhom: '', fields: [] };
  }
  function viHoa(s) { s = String(s || ''); return s.charAt(0).toUpperCase() + s.slice(1); }
  // ?muc=<mục>&tep=<tệp trong mục> → đường dẫn tệp trong kho
  function tuMuc(muc, ma) {
    var c = (st.cfg.collections || []).filter(function (x) { return x.name === muc; })[0];
    if (!c) return '';
    if (c.files) { var f = c.files.filter(function (x) { return x.name === ma; })[0]; return f ? f.file : ''; }
    if (c.folder) {
      var ext = c.extension || 'md';
      if (c.index_file && ma === c.index_file.name) ext = c.index_file.extension || ext;
      return c.folder.replace(/\/$/, '') + '/' + ma + '.' + ext;
    }
    return '';
  }

  /* ---------------- So từng ô ---------------- */
  function docTep(path, text) {
    if (text == null) return null;
    if (/\.md$/.test(path)) {
      var m = text.match(/^---\r?\n([\s\S]*?)\r?\n---[ \t]*\r?\n?([\s\S]*)$/);
      var d = m ? (jsyaml.load(m[1]) || {}) : {};
      d.body = (m ? m[2] : text).replace(/^\s+|\s+$/g, '');
      return d;
    }
    return jsyaml.load(text) || {};
  }
  function laDoiTuong(v) { return v && typeof v === 'object' && !Array.isArray(v) && !(v instanceof Date); }
  function hien(v, def) {
    if (v == null || v === '') return '';
    if (v instanceof Date) return v.toLocaleDateString('vi-VN');
    if (typeof v === 'boolean') return v ? 'Bật' : 'Tắt';
    if (def && def.options) {
      var o = def.options.filter(function (x) { return (x && x.value !== undefined ? x.value : x) === v; })[0];
      if (o && o.label) return o.label;
    }
    if (Array.isArray(v)) return v.map(function (x) { return hien(x, def); }).join(', ');
    return String(v);
  }
  // Tên dự phòng cho ô không có khai báo nhãn (ô ẩn trong CMS)
  var TEN = { tieu_de: 'Tiêu đề', nhan: 'Nhãn nhỏ', mo_dau: 'Đoạn mở đầu', mo_ta: 'Mô tả', ten: 'Tên', body: 'Nội dung', nhap: 'Bản nháp',
    anh: 'Ảnh', hien_thi: 'Hiển thị', thu_tu: 'Thứ tự', duong_dan: 'Đường dẫn', ngay_dang: 'Ngày đăng', ngay_cap_nhat: 'Ngày cập nhật' };
  function con(def, name) { return (def && def.fields || []).filter(function (f) { return f.name === name; })[0]; }
  function tenO(sd, name) { return (sd && sd.label) || TEN[name] || name; }
  function tomTat(x, boQua) {
    if (!laDoiTuong(x)) return hien(x);
    var uu = ['tieu_de', 'ten', 'nhan', 'hoi', 'chu', 'title'];
    for (var i = 0; i < uu.length; i++) if (typeof x[uu[i]] === 'string' && x[uu[i]]) return x[uu[i]];
    for (var k in x) if (typeof x[k] === 'string' && x[k] && k !== boQua) return x[k];
    return '';
  }
  // So hai bản của một tệp → danh sách thay đổi, gọi theo nhãn ô: "Các khối trên trang › Khối 3 · Dải cam kết › Tiêu đề"
  function soSanh(cu, moi, fields) {
    var out = [];
    soGiaTri(cu || {}, moi || {}, { fields: fields }, '', out, true);
    return out;
  }
  function noi(nhan, them) { return nhan ? nhan + ' › ' + them : them; }
  function soGiaTri(a, b, def, nhan, out, goc) {
    if (def && def.widget === 'lsn_nhom') return;
    var ds = function (v) { return Array.isArray(v) && v.some(laDoiTuong); };
    if (ds(a) || ds(b) || (def && def.widget === 'list' && (def.fields || def.types) && (Array.isArray(a) || Array.isArray(b)))) {
      return soDanhSach(Array.isArray(a) ? a : [], Array.isArray(b) ? b : [], def, nhan, out);
    }
    if (goc || laDoiTuong(a) || laDoiTuong(b)) {
      var A = laDoiTuong(a) ? a : {}, B = laDoiTuong(b) ? b : {}, names = (def && def.fields || []).map(function (f) { return f.name; });
      Object.keys(A).concat(Object.keys(B)).forEach(function (k) { if (names.indexOf(k) < 0) names.push(k); });
      names.forEach(function (k) {
        if (def && def.bo_qua === k) return;
        var sd = con(def, k);
        if (!(k in A) && !(k in B)) return;
        soGiaTri(A[k], B[k], sd, noi(nhan, tenO(sd, k)), out);
      });
      return;
    }
    var ha = hien(a, def), hb = hien(b, def);
    if (ha !== hb) out.push({ kieu: 'sua', nhan: nhan, cu: ha, moi: hb });
  }
  // Danh sách mục (khối, thẻ, câu hỏi…): khớp mục giống hệt (giữ nguyên / chỉ dời chỗ) trước, rồi ghép mục còn lại cùng loại theo thứ tự
  // (= mục được sửa); mục không ghép được là mục thêm / xóa. Nhờ vậy xóa 1 khối hay kéo đổi chỗ không làm mọi khối sau bị báo "đổi".
  function soDanhSach(A, B, def, nhan, out) {
    var ja = A.map(function (x) { return JSON.stringify(x); }), jb = B.map(function (x) { return JSON.stringify(x); });
    var n = A.length, m = B.length, L = [], i, j;
    for (i = 0; i <= n; i++) L.push(new Uint16Array(m + 1));
    for (i = n - 1; i >= 0; i--) for (j = m - 1; j >= 0; j--) L[i][j] = ja[i] === jb[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
    var cap = {}, capB = {}; // cap[i] = j: mục A[i] là mục B[j]
    i = 0; j = 0;
    while (i < n && j < m) {
      if (ja[i] === jb[j]) { cap[i] = j; capB[j] = { i: i, kieu: 'giu' }; i++; j++; }
      else if (L[i + 1][j] >= L[i][j + 1]) i++; else j++;
    }
    for (j = 0; j < m; j++) if (!capB[j]) for (i = 0; i < n; i++) if (!(i in cap) && ja[i] === jb[j]) { cap[i] = j; capB[j] = { i: i, kieu: 'doi-cho' }; break; }
    var tk = (def && def.typeKey) || 'type', loai = function (x) { return laDoiTuong(x) ? x[tk] : undefined; };
    for (j = 0; j < m; j++) if (!capB[j]) for (i = 0; i < n; i++) if (!(i in cap) && loai(A[i]) === loai(B[j])) { cap[i] = j; capB[j] = { i: i, kieu: 'sua' }; break; }
    var mot = def && def.label_singular ? viHoa(def.label_singular) : 'Mục';
    function tenMuc(x, k) {
      var t = def && def.types && laDoiTuong(x) ? def.types.filter(function (y) { return y.name === x[tk]; })[0] : null;
      return { nhan: noi(nhan, mot + ' ' + (k + 1) + (t ? ' · ' + (t.label || t.name) : '')), def: t ? Object.assign({ bo_qua: tk }, t) : def && (def.fields ? def : def.field ? { fields: [def.field] } : null) };
    }
    for (j = 0; j < m; j++) {
      var c = capB[j], t = tenMuc(B[j], j);
      if (!c) out.push({ kieu: 'them', nhan: t.nhan, moi: tomTat(B[j], tk) });
      else if (c.kieu === 'doi-cho') out.push({ kieu: 'thu-tu', nhan: t.nhan + ' (trước ở vị trí ' + (c.i + 1) + ')', moi: tomTat(B[j], tk) });
      else if (c.kieu === 'sua') {
        if (laDoiTuong(A[c.i]) || laDoiTuong(B[j])) soGiaTri(A[c.i], B[j], t.def, t.nhan, out);
        else { var ha = hien(A[c.i]), hb = hien(B[j]); if (ha !== hb) out.push({ kieu: 'sua', nhan: t.nhan, cu: ha, moi: hb }); }
      }
    }
    for (i = 0; i < n; i++) if (!(i in cap)) out.push({ kieu: 'bo', nhan: tenMuc(A[i], i).nhan + ' (vị trí cũ)', cu: tomTat(A[i], tk) });
  }
  // So từng chữ: đánh dấu phần bị bỏ / thêm; đoạn dài không đổi chỉ giữ ~100 ký tự quanh chỗ đổi
  function soChu(a, b) {
    var x = a.split(/(\s+)/), y = b.split(/(\s+)/), dau = 0, cuoi = 0;
    while (dau < x.length && dau < y.length && x[dau] === y[dau]) dau++;
    while (cuoi < x.length - dau && cuoi < y.length - dau && x[x.length - 1 - cuoi] === y[y.length - 1 - cuoi]) cuoi++;
    var X = x.slice(dau, x.length - cuoi), Y = y.slice(dau, y.length - cuoi), n = X.length, m = Y.length;
    var out = '', giu = x.slice(0, dau).join(''), bo = '', them = '', i, j;
    function raGiu(het) {
      if (giu.length > 260) giu = (out ? giu.slice(0, 100) : '') + '\u2002…\u2002' + (het ? '' : giu.slice(-100));
      out += esc(giu); giu = '';
    }
    function xa() {
      if (!bo && !them) return;
      raGiu(false);
      if (bo) out += '<del>' + esc(bo) + '</del>';
      if (them) out += '<ins>' + esc(them) + '</ins>';
      bo = them = '';
    }
    if (n * m > 400000) { bo = X.join(''); them = Y.join(''); }
    else {
      var L = []; for (i = 0; i <= n; i++) L.push(new Uint32Array(m + 1));
      for (i = n - 1; i >= 0; i--) for (j = m - 1; j >= 0; j--) L[i][j] = X[i] === Y[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1]);
      i = 0; j = 0;
      while (i < n && j < m) {
        if (X[i] === Y[j]) { xa(); giu += X[i]; i++; j++; }
        else if (L[i + 1][j] >= L[i][j + 1]) bo += X[i++];
        else them += Y[j++];
      }
      while (i < n) bo += X[i++];
      while (j < m) them += Y[j++];
    }
    xa();
    giu += x.slice(x.length - cuoi).join('');
    raGiu(true);
    return out;
  }
  function veDoi(d) {
    var trong = '<span class="phu">(trống)</span>';
    if (d.kieu === 'thu-tu') return '<li><span class="nhan-doi thu-tu">Dời chỗ</span><span class="o">' + esc(d.nhan) + '</span>' +
      (d.moi ? '<div class="gt">' + esc(d.moi) + '</div>' : '') + '</li>';
    if (d.kieu === 'them') return '<li><span class="nhan-doi them">Thêm</span><span class="o">' + esc(d.nhan) + '</span>' +
      (d.moi ? '<div class="gt"><ins>' + esc(d.moi) + '</ins></div>' : '') + '</li>';
    if (d.kieu === 'bo') return '<li><span class="nhan-doi bo">Xóa</span><span class="o">' + esc(d.nhan) + '</span>' +
      (d.cu ? '<div class="gt"><del>' + esc(d.cu) + '</del></div>' : '') + '</li>';
    var dai = (d.cu + d.moi).length > 160 || /\n/.test(d.cu + d.moi);
    var gt = dai && d.cu && d.moi ? soChu(d.cu, d.moi)
      : (d.cu ? '<del>' + esc(d.cu) + '</del>' : trong) + '<span class="mui-ten">→</span>' + (d.moi ? '<ins>' + esc(d.moi) + '</ins>' : trong);
    return '<li><div class="o">' + esc(d.nhan) + '</div><div class="gt' + (dai ? ' dai' : '') + '">' + gt + '</div></li>';
  }

  /* ---------------- Danh sách các lần lưu ---------------- */
  var NGAY = new Intl.DateTimeFormat('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  function luc(iso) {
    var t = new Date(iso), s = (Date.now() - t) / 1000, gan;
    if (s < 90) gan = 'vừa xong';
    else if (s < 3600) gan = Math.round(s / 60) + ' phút trước';
    else if (s < 86400) gan = Math.round(s / 3600) + ' giờ trước';
    else if (s < 86400 * 7) gan = Math.round(s / 86400) + ' ngày trước';
    return NGAY.format(t) + (gan ? ' · ' + gan : '');
  }
  function tepNoiDung(c) {
    return (c.files || []).filter(function (f) { return /^content\//.test(f.filename) && (st.loc === 'content' || f.filename === st.loc || f.filename.indexOf(st.loc + '/') === 0); });
  }
  var TT = { added: ['tao', 'Tạo mới'], removed: ['xoa', 'Đã xóa'], renamed: ['', 'Đổi tên'] };
  function veLan(c) {
    var tep = tepNoiDung(c), ai = (c.author && c.author.login) || (c.commit.author && c.commit.author.name) || '?';
    var anh = c.author && c.author.avatar_url ? '<img class="anh-dai-dien" alt="" src="' + esc(c.author.avatar_url) + '&s=68">' : '<span class="anh-dai-dien"></span>';
    var chips = tep.map(function (f) {
      var t = TT[f.status];
      return '<span class="chip ' + (t ? t[0] : '') + '">' + esc(moTa(f.filename).ten) + (t ? ' · ' + t[1] : '') + '</span>';
    }).join('');
    var anhTai = (c.files || []).filter(function (f) { return /^assets\/uploads\//.test(f.filename); }).length;
    var el = document.createElement('article');
    el.className = 'lan';
    el.innerHTML = '<button type="button" class="lan__dau" aria-expanded="false">' + anh +
      '<span class="lan__noi"><span class="lan__dong1"><span class="lan__ai">' + esc(ai) + '</span><span class="lan__luc">' + esc(luc(c.commit.author.date)) + '</span></span>' +
      '<span class="lan__tin" style="display:block">' + esc(c.commit.message.split('\n')[0]) + (anhTai ? ' · kèm ' + anhTai + ' ảnh tải lên' : '') + '</span>' +
      '<span style="display:block">' + chips + '</span></span><span class="mui" aria-hidden="true">›</span></button><div class="lan__than"></div>';
    var nut = el.querySelector('.lan__dau'), than = el.querySelector('.lan__than'), daTai = false;
    nut.addEventListener('click', function () {
      var mo = !el.classList.contains('mo');
      el.classList.toggle('mo', mo);
      nut.setAttribute('aria-expanded', String(mo));
      if (mo && !daTai) { daTai = true; chiTiet(c, tep, than); }
    });
    return el;
  }
  function chiTiet(c, tep, than) {
    than.innerHTML = '<div class="dang-tai">Đang đọc thay đổi…</div>';
    var truoc = c.parents[0] && c.parents[0].sha;
    lan_luot(tep, 4, function (f) {
      return Promise.all([
        f.status === 'added' || !truoc ? null : noiDung(f.previous_filename || f.filename, truoc),
        f.status === 'removed' ? null : noiDung(f.filename, c.sha)
      ]).then(function (x) { return { f: f, cu: x[0], moi: x[1] }; });
    }).then(function (ds) {
      than.innerHTML = '';
      ds.forEach(function (x) {
        var m = moTa(x.f.filename), doi, loiDoc = '';
        try {
          var a = docTep(x.f.filename, x.cu), b = docTep(x.f.filename, x.moi);
          var tieuDe = m.ident && ((b || a || {})[m.ident]);
          if (tieuDe) m = Object.assign({}, m, { ten: viHoa(String(tieuDe)) });
          doi = soSanh(a, b, m.fields);
        } catch (e) { doi = []; loiDoc = 'Không đọc được tệp để so từng ô (' + esc(e.message) + ').'; }
        var t = TT[x.f.status];
        var khoiPhuc = x.f.status === 'renamed' ? '' :
          '<button type="button" class="nut tep__nut" data-tep="' + esc(x.f.filename) + '">↶ ' +
          (x.f.status === 'added' ? 'Hoàn tác: xóa trang vừa tạo' : x.f.status === 'removed' ? 'Hoàn tác: lấy lại trang đã xóa' : 'Khôi phục trang này về trước lần lưu') + '</button>';
        var div = document.createElement('section');
        div.className = 'tep';
        div.innerHTML = '<div class="tep__dau"><h3>' + esc(m.ten) + '</h3>' + (m.nhom ? '<span class="tep__nhom">' + esc(m.nhom) + (t ? ' · ' + t[1] : '') + '</span>' : '') + khoiPhuc + '</div>' +
          (loiDoc ? '<div class="bao loi">' + loiDoc + '</div>' :
            doi.length ? '<ul class="doi">' + doi.map(veDoi).join('') + '</ul>' :
              '<p class="phu">' + (x.f.status === 'added' ? 'Trang mới tạo.' : x.f.status === 'removed' ? 'Trang đã bị xóa.' : 'Chỉ đổi cách ghi trong tệp, chữ trên trang không đổi.') + '</p>');
        than.appendChild(div);
        var b = div.querySelector('.tep__nut');
        if (b) b.addEventListener('click', function () { khoiPhuc_(c, [x.f], b); });
      });
      var cuoi = document.createElement('div');
      cuoi.className = 'lan__cuoi';
      var nhieu = tep.filter(function (f) { return f.status !== 'renamed'; });
      cuoi.innerHTML = (nhieu.length > 1 ? '<button type="button" class="nut chinh">↶ Hoàn tác cả lần lưu này (' + nhieu.length + ' trang)</button>' : '') +
        '<span class="phu">Mã lần lưu ' + esc(c.sha.slice(0, 7)) + '</span>' +
        '<a class="phu" href="' + esc(c.html_url) + '" target="_blank" rel="noopener">Xem trên GitHub ↗</a>';
      than.appendChild(cuoi);
      var bc = cuoi.querySelector('.nut');
      if (bc) bc.addEventListener('click', function () { khoiPhuc_(c, nhieu, bc); });
    }).catch(function (e) { than.innerHTML = '<div class="bao loi">' + e.message + '</div>'; });
  }

  /* ---------------- Khôi phục ---------------- */
  function khoiPhuc_(c, tep, nut) {
    if (!st.token) { bao('Cần đăng nhập để khôi phục: mở <a href="./">trang quản trị</a>, đăng nhập, rồi tải lại trang này.', 'loi'); return; }
    var truoc = c.parents[0] && c.parents[0].sha;
    if (!truoc) return;
    var ten = tep.map(function (f) { return '“' + moTa(f.filename).ten + '”'; }).join(', ');
    var ngay = NGAY.format(new Date(c.commit.author.date));
    nut.disabled = true;
    // Trang đã được sửa thêm sau lần lưu này? (bản hiện tại khác bản ngay sau lần lưu)
    lan_luot(tep, 4, function (f) {
      return gh(repoUrl('/contents/' + encPath(f.filename) + '?ref=' + encodeURIComponent(st.branch)), { cho404: true })
        .then(function (hienTai) { return (hienTai ? hienTai.sha : null) !== (f.status === 'removed' ? null : f.sha); });
    }).then(function (khac) {
      var xoa = tep.filter(function (f) { return f.status === 'added'; });
      var hoi = 'Khôi phục ' + ten + ' về như TRƯỚC lần lưu lúc ' + ngay + '?';
      if (xoa.length) hoi += '\n\n⚠ Lần lưu đó TẠO MỚI ' + xoa.map(function (f) { return '“' + moTa(f.filename).ten + '”'; }).join(', ') + ' → khôi phục sẽ XÓA trang này khỏi site.';
      if (khac.some(Boolean)) hoi += '\n\n⚠ Sau lần lưu này, trang đã được sửa thêm. Khôi phục sẽ bỏ luôn cả các lần sửa sau đó.';
      hoi += '\n\nSite cập nhật sau 1–3 phút. Thao tác này cũng ghi vào lịch sử, muốn quay lại vẫn hoàn tác được.';
      if (!window.confirm(hoi)) { nut.disabled = false; return; }
      bao('Đang khôi phục…');
      return ghiKhoiPhuc(c, tep, truoc, ten, ngay).then(function (ok) {
        if (ok === 'giong') { bao('Trang đang giống hệt bản trước lần lưu đó – không cần khôi phục.', 'tot'); nut.disabled = false; return; }
        bao('Đã khôi phục ' + esc(ten) + '. Site cập nhật sau 1–3 phút.<br><b>Nếu đang mở trang này ở cửa sổ quản trị: tải lại cửa sổ đó (F5) trước khi sửa tiếp</b>, kẻo bấm Lưu sẽ ghi đè bản vừa khôi phục.', 'tot');
        taiDanhSach(true);
      });
    }).catch(function (e) { bao(e.message, 'loi'); nut.disabled = false; });
  }
  // Một commit mới trên nhánh CMS: mỗi tệp trỏ về đúng bản (blob) trước lần lưu; tệp chưa có lúc đó → xóa
  function ghiKhoiPhuc(c, tep, truoc, ten, ngay) {
    var dau, goc;
    return gh(repoUrl('/git/ref/heads/' + encodeURIComponent(st.branch))).then(function (r) {
      dau = r.object.sha;
      return gh(repoUrl('/git/commits/' + dau));
    }).then(function (cm) {
      goc = cm.tree.sha;
      return lan_luot(tep, 4, function (f) {
        var cu = f.status === 'renamed' ? f.previous_filename : f.filename;
        return (f.status === 'added' ? Promise.resolve(null) : gh(repoUrl('/contents/' + encPath(cu) + '?ref=' + truoc), { cho404: true }))
          .then(function (x) {
            if (x && x.type !== 'file') throw new Error('Không khôi phục được ' + esc(cu) + '.');
            return { path: f.filename, mode: '100644', type: 'blob', sha: x ? x.sha : null };
          });
      });
    }).then(function (cay) {
      return gh(repoUrl('/git/trees'), { method: 'POST', body: { base_tree: goc, tree: cay } });
    }).then(function (t) {
      if (t.sha === goc) return 'giong';
      var tin = 'Khôi phục ' + ten + ' về trước lần lưu ' + ngay + ' (' + c.sha.slice(0, 7) + ')\n\n' +
        'Làm từ trang Lịch sử chỉnh sửa trong /admin. Lần lưu được hoàn tác: ' + c.commit.message.split('\n')[0];
      return gh(repoUrl('/git/commits'), { method: 'POST', body: { message: tin, tree: t.sha, parents: [dau] } })
        .then(function (moi) { return gh(repoUrl('/git/refs/heads/' + encodeURIComponent(st.branch)), { method: 'PATCH', body: { sha: moi.sha, force: false } }); })
        .then(function () { return true; });
    });
  }

  /* ---------------- Tải danh sách ---------------- */
  function taiDanhSach(tuDau) {
    if (st.dang_tai) return;
    st.dang_tai = true;
    if (tuDau) { st.trang = 1; $('#danh-sach').innerHTML = ''; }
    var them = $('#them-nua');
    them.hidden = true;
    var cho = document.createElement('div');
    cho.className = 'dang-tai'; cho.textContent = 'Đang tải lịch sử…';
    $('#danh-sach').appendChild(cho);
    gh(repoUrl('/commits?sha=' + encodeURIComponent(st.branch) + '&path=' + encodeURIComponent(st.loc) + '&per_page=' + MOI_TRANG + '&page=' + st.trang))
      .then(function (ds) {
        return lan_luot(ds, 6, function (c) { return gh(repoUrl('/commits/' + c.sha)); }).then(function (chiTiet) {
          cho.remove();
          chiTiet.forEach(function (c) { if (tepNoiDung(c).length) $('#danh-sach').appendChild(veLan(c)); });
          if (!$('#danh-sach').children.length) $('#danh-sach').innerHTML = '<p class="phu">Chưa có lần lưu nào cho trang này.</p>';
          them.hidden = ds.length < MOI_TRANG;
          st.trang++;
        });
      })
      .catch(function (e) { cho.remove(); bao(e.message, 'loi'); })
      .then(function () { st.dang_tai = false; });
  }
  function veOLoc(chon) {
    var s = $('#loc-trang'), nhom = {};
    (st.cfg.collections || []).forEach(function (c) {
      if (!c.label) return;
      var g = document.createElement('optgroup');
      g.label = c.label;
      if (c.folder) {
        var o = document.createElement('option');
        o.value = c.folder.replace(/\/$/, ''); o.textContent = 'Tất cả – ' + c.label;
        g.appendChild(o);
      }
      (c.files || []).forEach(function (f) {
        var o = document.createElement('option');
        o.value = f.file; o.textContent = f.label || f.name;
        g.appendChild(o);
      });
      if (g.children.length) { s.appendChild(g); nhom[c.name] = g; }
    });
    if (chon && !s.querySelector('option[value="' + CSS.escape(chon) + '"]')) {
      var m = moTa(chon), o = document.createElement('option');
      o.value = chon; o.textContent = m.ten;
      (nhom[m.muc] || s).appendChild(o);
    }
    s.value = chon || 'content';
    s.addEventListener('change', function () {
      st.loc = s.value;
      var u = new URL(location.href);
      u.search = st.loc === 'content' ? '' : '?tep=' + encodeURIComponent(st.loc);
      history.replaceState(null, '', u);
      bao('');
      taiDanhSach(true);
    });
  }

  function batDau() {
    st.token = token();
    if (!window.jsyaml) { bao('Không tải được thư viện đọc nội dung (mạng chặn unpkg.com). Tải lại trang.', 'loi'); return; }
    fetch('config.yml', { cache: 'no-cache' }).then(function (r) {
      if (!r.ok) throw new Error('Không đọc được cấu hình trang quản trị (config.yml).');
      return r.text();
    }).then(function (t) {
      napCauHinh(jsyaml.load(t));
      if (!st.repo) throw new Error('Cấu hình chưa có kho nội dung (backend.repo).');
      var q = new URLSearchParams(location.search), chon = '';
      if (q.get('tep') && /^content\//.test(q.get('tep'))) chon = q.get('tep');
      else if (q.get('muc')) chon = tuMuc(q.get('muc'), q.get('ma') || '') || '';
      st.loc = chon || 'content';
      veOLoc(chon);
      if (!st.token) bao('Chưa đăng nhập: vẫn xem được lịch sử (tối đa 60 lần tải/giờ), nhưng muốn <b>khôi phục</b> thì mở <a href="./">trang quản trị</a>, đăng nhập, rồi tải lại trang này.');
      $('#them-nua').addEventListener('click', function () { taiDanhSach(false); });
      taiDanhSach(true);
    }).catch(function (e) { bao(esc(e.message), 'loi'); });
  }
  batDau();
})();
