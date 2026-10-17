/* Khung mô phỏng /admin – luồng riêng chạy ĐÚNG code build của site (Python) trong trình duyệt bằng Pyodide,
   để gõ chữ không bị giật trong lúc dựng trang. Nhận {type:"init"} một lần rồi {type:"render"} mỗi lần nội dung đổi;
   chỉ dựng yêu cầu mới nhất (bỏ qua các yêu cầu cũ còn chờ). */
const PYODIDE = 'https://cdn.jsdelivr.net/npm/pyodide@0.29.5/'; // khóa phiên bản: Python 3.13 như GitHub Actions

let xt = null;
let pending = null;
let busy = false;

async function init(msg) {
  const base = msg.pyodide || PYODIDE;
  importScripts(base + 'pyodide.js');
  const t0 = Date.now();
  const [py, goi] = await Promise.all([
    loadPyodide({ indexURL: base }),
    fetch(msg.goi, { cache: 'no-cache' }).then((r) => {
      if (!r.ok) throw new Error('Không tải được gói mô phỏng (' + r.status + ')');
      return r.arrayBuffer();
    }),
  ]);
  py.unpackArchive(goi, 'zip', { extractDir: '/home/pyodide' });
  py.runPython(
    "import sys\nsys.path[:0] = ['/home/pyodide/repo/tools', '/home/pyodide/repo/lib']\n" +
      "import xem_truoc\nxem_truoc.setup(open('/home/pyodide/repo/xem-truoc.json', encoding='utf-8').read())",
  );
  xt = py.globals.get('xem_truoc');
  postMessage({ type: 'ready', ms: Date.now() - t0 });
  next(); // yêu cầu dựng gửi tới trong lúc đang tải (mở thẳng một trang / tải lại trang): dựng ngay, không đợi lần gõ sau
}

function next() {
  if (busy || !pending || !xt) return;
  const m = pending;
  pending = null;
  busy = true;
  try {
    const out = JSON.parse(xt.render(m.collection, m.slug || null, m.file || null, m.data, !!m.isNew, m.path || null));
    postMessage({ type: 'html', id: m.id, result: out });
  } catch (e) {
    postMessage({ type: 'html', id: m.id, result: { html: '', loi: [['', 'Mô phỏng gặp lỗi: ' + e]], canh: [] } });
  }
  busy = false;
  setTimeout(next, 0);
}

self.onmessage = (e) => {
  const m = e.data;
  if (m.type === 'init') {
    init(m).catch((err) => postMessage({ type: 'error', message: String(err && err.message ? err.message : err) }));
  } else if (m.type === 'render') {
    pending = m;
    next();
  }
};
