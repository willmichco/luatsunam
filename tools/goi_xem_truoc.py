# -*- coding: utf-8 -*-
"""Đóng gói cho khung mô phỏng trong /admin: dist/admin/xem-truoc/goi.zip.

Gồm đúng code build (tools/*.py, assets/css/style.css), nội dung đang có (content/*.yml, *.md), thư viện Python thuần cần để dựng trang
(PyYAML, markdown-it-py, mdurl – bỏ phần biên dịch C) và xem-truoc.json (kích thước ảnh, mã phiên bản CSS/JS lấy từ
lượt build này). admin/xem-truoc-worker.js giải nén gói trong Pyodide rồi gọi tools/xem_truoc.py.
"""
import io
import json
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBS = ("yaml", "markdown_it", "mdurl")
STAMP = (2026, 1, 1, 0, 0, 0)  # thời điểm cố định: cùng nội dung → cùng tệp zip


def _add(z, arc, data):
    info = zipfile.ZipInfo(arc, STAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    z.writestr(info, data)


def package(out, photo_sizes, uploads, file_hashes):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name in sorted(os.listdir(os.path.join(ROOT, "tools"))):
            if name.endswith(".py"):
                _add(z, f"repo/tools/{name}", open(os.path.join(ROOT, "tools", name), "rb").read())
        # CSS của site: build nhúng thẳng vào <head> mỗi trang (build.site_css), mô phỏng cũng vậy
        _add(z, "repo/assets/css/style.css", open(os.path.join(ROOT, "assets", "css", "style.css"), "rb").read())
        for d, dirs, files in sorted(os.walk(os.path.join(ROOT, "content"))):
            dirs.sort()
            for f in sorted(files):
                if f.endswith((".yml", ".md")):
                    full = os.path.join(d, f)
                    _add(z, "repo/" + os.path.relpath(full, ROOT).replace(os.sep, "/"), open(full, "rb").read())
        for lib in LIBS:
            base = os.path.dirname(__import__(lib).__file__)
            for d, dirs, files in sorted(os.walk(base)):
                dirs[:] = sorted(x for x in dirs if x != "__pycache__")
                for f in sorted(files):
                    if f.endswith((".py", ".yaml", ".typed")):
                        full = os.path.join(d, f)
                        _add(z, f"repo/lib/{lib}/" + os.path.relpath(full, base).replace(os.sep, "/"), open(full, "rb").read())
        snap = {"sizes": {k: list(v) for k, v in photo_sizes.items()},
                "uploads": {k: list(v) for k, v in uploads.items()},
                "anh": {k: [v[0], v[1]] for k, v in uploads.items()},
                "hash": file_hashes}
        _add(z, "repo/xem-truoc.json", json.dumps(snap, ensure_ascii=False))
    dst = os.path.join(out, "admin", "xem-truoc")
    os.makedirs(dst, exist_ok=True)
    with open(os.path.join(dst, "goi.zip"), "wb") as fh:
        fh.write(buf.getvalue())
    return len(buf.getvalue())


def missing_previews():
    """Tên mục / tệp trong cấu hình CMS chưa có trong PREVIEW_NAMES của admin/xem-truoc.js (Sveltia tìm khung theo tên)."""
    import re
    import schema
    js = open(os.path.join(ROOT, "admin", "xem-truoc.js"), encoding="utf-8").read()
    m = re.search(r"PREVIEW_NAMES = \[([^\]]*)\]", js)
    have = set(re.findall(r"'([^']+)'", m.group(1))) if m else set()
    need = []
    for c in schema.collections():
        if c.get("divider"):
            continue
        need += [f["name"] for f in c["files"]] if "files" in c else [c["name"]]
    return [n for n in need if n not in have]
