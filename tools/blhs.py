# -*- coding: utf-8 -*-
"""Từ điển Bộ luật Hình sự: sinh trang tổng quan, trang từng chương và trang từng điều.

Dữ liệu: bo-luat-hinh-su/data/*.json (do tools/build_blhs.py tạo từ tệp Word).
Nội dung bổ sung cho từng điều (không bắt buộc): src/blhs/<số điều>.html, gồm các khối

    <!-- tab: goc-nhin -->   Góc nhìn Luật sư Nam
    <!-- tab: ban-an -->     Bản án liên quan
    <!-- tab: tinh-huong --> Tình huống thực tiễn

Khối nào chưa có thì trang hiển thị hướng dẫn và nút liên hệ luật sư.
"""
import glob
import html
import json
import os
import re
from collections import Counter, OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "bo-luat-hinh-su", "data")
EXTRA = os.path.join(ROOT, "src", "blhs")
HUB = "bo-luat-hinh-su/"
AC = ' aria-current="page"'
TI = ' tabindex="-1"'

LAW_NAME = "Bộ luật Hình sự 2015 (sửa đổi, bổ sung 2017, 2025)"
AM_NOTE = ("Theo chú thích của tài liệu gốc: những điều, khoản, điểm có gắn dấu sao (*) là những điều, khoản, điểm "
           "đã được sửa đổi, bổ sung theo Luật sửa đổi, bổ sung một số điều của Bộ luật hình sự năm 2015.")

# Thuật ngữ thường tra cứu: chỉ hiển thị khi xuất hiện thật trong văn bản điều luật
GLOSSARY = [
    "đồng phạm", "phạm tội có tổ chức", "tái phạm nguy hiểm", "tái phạm", "có tính chất chuyên nghiệp",
    "tự thú", "đầu thú", "tình tiết giảm nhẹ", "tình tiết tăng nặng", "án treo", "xóa án tích", "án tích",
    "thời hiệu truy cứu trách nhiệm hình sự", "thời hiệu thi hành bản án", "miễn trách nhiệm hình sự",
    "miễn hình phạt", "người dưới 18 tuổi", "pháp nhân thương mại", "phòng vệ chính đáng", "tình thế cấp thiết",
    "chuẩn bị phạm tội", "phạm tội chưa đạt", "tự ý nửa chừng chấm dứt", "che giấu tội phạm", "không tố giác tội phạm",
    "cải tạo không giam giữ", "cảnh cáo", "phạt tiền", "tù có thời hạn", "tù chung thân", "tử hình", "trục xuất",
    "tịch thu tài sản", "cấm đảm nhiệm chức vụ", "quản chế", "cấm cư trú", "hình phạt bổ sung", "tổng hợp hình phạt",
    "chiếm đoạt tài sản", "lợi dụng chức vụ, quyền hạn", "thủ đoạn xảo quyệt", "bảo vật quốc gia", "người bị hại",
    "trẻ em", "phụ nữ mà biết là có thai", "người đủ 70 tuổi trở lên", "trốn thuế", "ma túy", "rửa tiền",
    "tham ô tài sản", "nhận hối lộ", "đưa hối lộ", "lừa đảo", "không gian mạng", "mạng máy tính",
]

DEF_RE = re.compile(r"^(?:\d+\.\s*)?([A-ZĐÂĂÊÔƠƯÁÀẢÃẠÉÈẺẼẸÍÌỈĨỊÓÒỎÕỌÚÙỦŨỤÝỲỶỸỴ][^.:;,()]{2,70}?) là ")
DEF_SKIP = ("Chỉ ", "Các ", "Những ", "Khi ", "Trong ", "Trường hợp ", "Người phạm tội", "Việc ")


def esc(s):
    return html.escape(s, quote=True)


def plain(h):
    h = re.sub(r'<sup class="fn"[^>]*>.*?</sup>', "", h)
    return html.unescape(re.sub(r"<[^>]+>", "", h)).strip()


def letter_id(ch):
    return "dd" if ch == "đ" else ch


# ---------------------------------------------------------------------------
# Nạp dữ liệu
# ---------------------------------------------------------------------------
class Code:
    def __init__(self):
        with open(os.path.join(DATA, "toc.json"), encoding="utf-8") as fh:
            self.toc = json.load(fh)
        self.v = self.toc["v"]
        self.parts = OrderedDict((p["id"], p) for p in self.toc["parts"])
        self.chapters = []
        self.arts = []
        for c in self.toc["chapters"]:
            c = dict(c)
            c["slug"] = f"chuong-{self.roman_to_int(c['num'])}" if c["num"] else "dieu-khoan-thi-hanh"
            c["label"] = f"Chương {c['num']}" if c["num"] else "Điều khoản thi hành"
            c["title"] = f"{c['label']}. {c['name']}" if c["num"] else c["name"]
            c["muc_names"] = {m["n"]: m["name"] for m in c["muc"]}
            self.chapters.append(c)
            for x in c["a"]:
                a = dict(x)
                a["ch"] = c
                a["i"] = len(self.arts)
                self.arts.append(a)
        self.by_id = {a["id"]: a for a in self.arts}
        body = {}
        for f in glob.glob(os.path.join(DATA, "*.json")):
            if f.endswith("toc.json"):
                continue
            with open(f, encoding="utf-8") as fh:
                for d in json.load(fh):
                    body[d["id"]] = d
        for a in self.arts:
            d = body[a["id"]]
            a["law"], a["cm"], a["fn"] = d["law"], d["cm"], d.get("fn", {})
            self._renumber_fn(a)
        KNOWN.update(a["id"] for a in self.arts)
        self._links()

    @staticmethod
    def _renumber_fn(a):
        """Chú thích đánh số lại từ 1 trong từng điều (tệp gốc đánh số liên tục cả Bộ luật)
        và ghi nhận chú thích nằm ở phần điều luật hay phần bình luận."""
        local, where = {}, {}
        def sub(m, part):
            g = m.group(1)
            if g not in local:
                local[g] = str(len(local) + 1)
                where[local[g]] = part
            return f'<sup class="fn" data-fn="{local[g]}">{local[g]}</sup>'
        for part in ("law", "cm"):
            a[part] = [[k, re.sub(r'<sup class="fn" data-fn="(\d+)">.*?</sup>', lambda m: sub(m, part), h)]
                       for k, h in a[part]]
        a["fn"] = {local[g]: t for g, t in a["fn"].items() if g in local}
        a["fn_where"] = where

    @staticmethod
    def roman_to_int(s):
        val = {"I": 1, "V": 5, "X": 10, "L": 50}
        total, prev = 0, 0
        for ch in reversed(s):
            n = val[ch]
            total = total - n if n < prev else total + n
            prev = max(prev, n)
        return total

    def _links(self):
        xr = re.compile(r'class="xr" href="#d(\w+)"')
        for a in self.arts:
            a["out_law"] = Counter(x for _, h in a["law"] for x in xr.findall(h) if x != a["id"] and x in self.by_id)
            a["out_cm"] = Counter(x for _, h in a["cm"] for x in xr.findall(h) if x != a["id"] and x in self.by_id)
            a["incoming"] = Counter()
        for a in self.arts:
            for x, n in a["out_law"].items():
                self.by_id[x]["incoming"][a["id"]] += n

    # ---- Phân tích nội dung ----
    def definitions(self, a):
        out = []
        for t, h in a["law"]:
            if t not in ("k", "x"):
                continue
            m = DEF_RE.match(plain(h))
            if not m:
                continue
            term = m.group(1).strip()
            if len(term.split()) > 7 or term.startswith(DEF_SKIP) or term in out:
                continue
            out.append(term)
        return out

    @staticmethod
    def khoan_nodes(a):
        nodes = []
        for t, h in a["law"]:
            if t != "k":
                continue
            s = plain(h).rstrip("*").strip()
            m = re.match(r"^(\d+)\.\s*(.*)$", s)
            if not m:
                continue
            num, body = m.group(1), m.group(2)
            if "còn có thể bị" in body:
                label, kind = "Hình phạt bổ sung", "pen"
            else:
                p = re.search(r"thì bị ((?:phạt|tù|cảnh cáo)[^:;]*?)(?::|;|\.\s*$|$)", body)
                if p:
                    label, kind = p.group(1).strip(), "pen"
                    label = label[0].upper() + label[1:]
                else:
                    words = body.split()
                    label, kind = " ".join(words[:10]) + ("…" if len(words) > 10 else ""), "txt"
            nodes.append((num, label, kind))
        return nodes

    def mindmap(self, a):
        defs = [d for d in self.definitions(a) if d.lower() != a["t"].lower()]
        if len(defs) >= 2:
            return "Các khái niệm được định nghĩa", [(None, d) for d in defs[:8]]
        nodes = self.khoan_nodes(a)
        if len(nodes) >= 2:
            if sum(1 for n in nodes if n[2] == "pen") >= 2:
                return "Khung hình phạt theo từng khoản", [(f"Khoản {n}", l) for n, l, _ in nodes[:8]]
            return "Cấu trúc điều luật", [(f"Khoản {n}", l) for n, l, _ in nodes[:8]]
        return None, []

    def glossary(self, a, limit=8):
        text = " ".join(plain(h) for _, h in a["law"]).lower()
        terms = [d for d in self.definitions(a)]
        for g in GLOSSARY:
            if g in text and not any(g in t.lower() for t in terms):
                terms.append(g)
        out = []
        for t in terms:
            if t.lower() not in [x.lower() for x in out]:
                out.append(t[0].upper() + t[1:])
        return out[:limit]

    def related(self, a, limit=5):
        order = []
        for src in (a["out_law"], a["out_cm"], a["incoming"]):
            for x, _ in src.most_common():
                if x not in order:
                    order.append(x)
        i = a["i"]
        for j in (i - 1, i + 1, i - 2, i + 2, i - 3, i + 3):
            if 0 <= j < len(self.arts) and self.arts[j]["id"] not in order and self.arts[j]["id"] != a["id"]:
                order.append(self.arts[j]["id"])
        return [self.by_id[x] for x in order[:limit]]

    def excerpt(self, a, n=170):
        text = " ".join(plain(h).rstrip("*") for _, h in a["law"])
        text = re.sub(r"\s+", " ", text)
        if len(text) <= n:
            return text
        cut = text[:n].rsplit(" ", 1)[0]
        return cut + "…"


PEN_RE = re.compile(r"thì bị ((?:phạt|tù|cảnh cáo)[^:;]*?)(?::|;|\.\s*$|$)")


def penalty_summary(a):
    """(số khung hình phạt, mức cao nhất) của điều luật quy định tội danh, hoặc None.

    Chỉ tính các khoản áp dụng cho cá nhân có câu "thì bị phạt/tù/cảnh cáo …". Bỏ qua khoản
    hình phạt bổ sung ("còn có thể bị") và khoản dành cho pháp nhân thương mại. Mức cao nhất
    xếp theo thứ tự: tử hình > tù chung thân > tù có thời hạn (năm, tháng) > cải tạo không
    giam giữ > phạt tiền, cảnh cáo. Dùng cho meta description nên trả về câu chữ ngắn."""
    frames, best = 0, None
    # Điều không chia khoản: toàn bộ quy định nằm trong một đoạn (loại "x")
    kinds = ("k",) if any(t == "k" for t, _ in a["law"]) else ("x",)
    for t, h in a["law"]:
        if t not in kinds:
            continue
        body = re.sub(r"^\d+\.\s*", "", plain(h).rstrip("*").strip())
        if "còn có thể bị" in body or body.startswith("Pháp nhân thương mại"):
            continue
        m = PEN_RE.search(body)
        if not m:
            continue
        found = False
        for opt in re.split(r",|\bhoặc\b", m.group(1)):
            opt = opt.strip().lower()
            if "tử hình" in opt:
                rank = (5, 0, "tử hình")
            elif "chung thân" in opt:
                rank = (4, 0, "tù chung thân")
            elif "tù" in opt and re.search(r"\d+\s*(năm|tháng)", opt):
                y = [int(n) for n in re.findall(r"(\d+)\s*năm", opt)]
                if y:
                    rank = (3, max(y), f"{max(y)} năm tù")
                else:
                    mo = max(int(n) for n in re.findall(r"(\d+)\s*tháng", opt))
                    rank = (2, mo, f"{mo} tháng tù")
            elif "cải tạo không giam giữ" in opt:
                y = [int(n) for n in re.findall(r"(\d+)\s*năm", opt)]
                rank = (1, max(y), f"{max(y)} năm cải tạo không giam giữ") if y else (1, 0, "cải tạo không giam giữ")
            elif "phạt tiền" in opt or "cảnh cáo" in opt:
                rank = (0, 0, "phạt tiền" if "tiền" in opt else "cảnh cáo")
            else:
                continue
            found = True
            if best is None or rank[:2] > best[:2]:
                best = rank
        frames += found
    if not frames or best[0] < 1:
        return None
    return frames, best[2]


# ---------------------------------------------------------------------------
# Dựng HTML
# ---------------------------------------------------------------------------
def art_url(a, base):
    return f"{base}dieu-{a['id']}/"


KNOWN = set()  # số hiệu các điều hiện có, do Code nạp
NUM = r"\d{1,3}[a-z]?(?![\d/])"
SEP = r"(?:,\s*|\s+và\s+|\s+hoặc\s+)"
# "điều 168, 169 và 290 của Bộ luật này" trong văn bản điều luật
LAW_REF = re.compile(r"\b([Đđ]iều)\s+(" + NUM + "(?:" + SEP + NUM + ")*)(?=\s*(?:,\s*)?(?:của\s+)?Bộ luật này)")


def link_lists(h, a, base):
    """Gắn liên kết cho mọi số điều trong danh sách: số đầu đã có liên kết thì nối tiếp các số sau;
    văn bản điều luật ghi "các điều …, … của Bộ luật này" thì gắn cho cả danh sách."""
    def one(n):
        if n not in KNOWN:
            return n
        href = f"{base}dieu-{n}/" if n != a["id"] else "#quy-dinh"
        return f'<a class="xr" href="{href}">{n}</a>'

    def nums(txt):
        return re.sub(NUM, lambda m: one(m.group(0)), txt)

    parts = re.split(r"(<[^>]+>)", h)
    depth, after_xr = 0, False
    for i, t in enumerate(parts):
        if i % 2:
            if t.startswith("<a"):
                depth += 1
                after_xr = False
            elif t == "</a>":
                depth -= 1
                after_xr = parts[i - 2].startswith('<a class="xr"') if i >= 2 else False
            else:
                after_xr = False
            continue
        if depth:
            continue
        if after_xr:
            m = re.match("(?:" + SEP + NUM + ")+", t)
            if m:
                t = nums(m.group(0)) + t[m.end():]
        t = LAW_REF.sub(lambda m: f"{m.group(1)} {nums(m.group(2))}", t)
        parts[i] = t
        after_xr = False
    return "".join(parts)


def fix_para(h, a, base, is_law):
    h = re.sub(r'class="xr" href="#d(\w+)"',
               lambda m: f'class="xr" href="{base}dieu-{m.group(1)}/"' if m.group(1) != a["id"] else 'class="xr" href="#quy-dinh"', h)
    h = re.sub(r'<sup class="fn" data-fn="(\d+)">(.*?)</sup>',
               lambda m: f'<sup class="fn"><a href="#fn-{m.group(1)}" title="{esc(a["fn"].get(m.group(1), ""))}">{m.group(2)}</a></sup>', h)
    h = link_lists(h, a, base)
    if is_law:
        h = re.sub(r"\*((?:</[a-z]+>)*)$", r'<span class="tdl-star" title="Được sửa đổi, bổ sung">*</span>\1', h)
    return h


def law_html(a, base):
    out, k, opened = [], None, False
    seen = set()
    for i, (t, h) in enumerate(a["law"]):
        txt = plain(h)
        if t == "k" and re.match(r"^(\d+)\.", txt):
            k = re.match(r"^(\d+)\.", txt).group(1)
            if opened: out.append('</div></div>')
            opened = True
            out.append(f'<div class="tdl-clause" id="k{k}"><span class="tdl-clause__number">{int(k):02d}</span><button class="tdl-clause__copy" type="button" data-copy-clause="k{k}" aria-label="Sao chép khoản {k}">⧉</button><div class="tdl-clause__text">')
            h = re.sub(r"^\d+\.\s*", "", h)
            out.append(f'<p class="tdl-k" data-l="{i}">{fix_para(h, a, base, True)}</p>')
        else:
            pid = ""
            m = re.match(r"^([a-zđ])\)", txt) if t == "p" else None
            if m: pid = (f"k{k}-" if k else "d-") + letter_id(m.group(1))
            if pid in seen: pid = ""
            seen.add(pid)
            attr = f' id="{pid}"' if pid else ""
            cls = {"p": "tdl-p", "x": "tdl-x", "h": "tdl-h"}.get(t, "tdl-x")
            out.append(f'<p class="{cls}"{attr} data-l="{i}">{fix_para(h, a, base, True)}</p>')
    if opened: out.append('</div></div>')
    return "\n".join(out)


def cm_html(a, base):
    """Trả về (html, danh sách mục) của phần bình luận."""
    out, heads = [], []
    for i, (t, h) in enumerate(a["cm"]):
        body = fix_para(h, a, base, False)
        di = f' data-c="{i}"'
        if t == "h":
            hid = f"bl-{len(heads) + 1}"
            m = re.match(r"^(\d+)\.\s*(.*?):?\s*$", plain(h))
            if m:
                heads.append((hid, m.group(2)))
                out.append(f'<h3 class="tdl-cm__h" id="{hid}"{di}><span class="tdl-cm__num">{m.group(1)}</span>{esc(m.group(2))}</h3>')
            else:
                heads.append((hid, plain(h).rstrip(":")))
                out.append(f'<h3 class="tdl-cm__h" id="{hid}"{di}>{body}</h3>')
        elif t == "s":
            out.append(f'<h4 class="tdl-cm__s"{di}>{body}</h4>')
        else:
            cls = {"b": "tdl-cm__b", "q": "tdl-cm__q", "n": "tdl-cm__n"}.get(t, "")
            out.append(f'<p{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}{di}>{body}</p>')
    return "\n".join(out), heads


def footnotes_html(a, part):
    notes = {n: t for n, t in a["fn"].items() if a.get("fn_where", {}).get(n, "law") == part}
    if not notes:
        return ""
    items = "".join(f'<li id="fn-{n}" value="{n}">{esc(t)}</li>' for n, t in sorted(notes.items(), key=lambda x: int(x[0])))
    return f'<ol class="tdl-fns" aria-label="Chú thích">{items}</ol>'


def badges_html(a):
    b = []
    if a.get("am"):
        b.append(f'<span class="tdl-badge tdl-badge--am" title="{esc(AM_NOTE)}">Có sửa đổi, bổ sung (*)</span>')
    if a.get("n25"):
        b.append('<span class="tdl-badge tdl-badge--new">Điểm mới năm 2025</span>')
    if a.get("rep"):
        b.append('<span class="tdl-badge tdl-badge--rep">Đã bãi bỏ</span>')
    return f'<div class="tdl-badges">{"".join(b)}</div>' if b else ""


def load_extra(aid):
    path = os.path.join(EXTRA, f"{aid}.html")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    parts = re.split(r"<!--\s*tab:\s*([\w-]+)\s*-->", text)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2) if parts[i + 1].strip()}


class Renderer:
    """Sinh HTML cho các trang từ điển. `ico`, `arrow` lấy từ tools/build.py."""

    def __init__(self, code, ico, arrow, firm):
        self.c = code
        self.ico = ico
        self.arrow = arrow
        self.firm = firm
        # refs[id điều] = {"articles": [(đường dẫn, tiêu đề)], "services": [...]}: do build.py điền
        self.refs = {}

    # ---- Khung chung ----
    def band(self, r):
        return f"""<section class="tdl-band" aria-label="Tra cứu Bộ luật Hình sự">
  <div class="tdl-wrap tdl-band__inner">
    <a class="tdl-band__brand" href="{r}{HUB}">
      
      <span><span class="tdl-band__title">Từ điển Bộ luật Hình sự</span><span class="tdl-band__firm">LUẬT SƯ NAM</span><span class="tdl-band__sub">Tra cứu nhanh · Hiểu đúng · Áp dụng chuẩn</span></span>
    </a>
    <form class="tdl-search" action="{r}{HUB}" method="get" role="search" autocomplete="off">
      <label class="sr-only" for="tdl-q">Tìm trong Bộ luật Hình sự</label>
      {self.ico("i-search", "tdl-search__icon")}
      <input id="tdl-q" name="q" type="search" placeholder="Tìm điều luật, tội danh, từ khóa…" role="combobox" aria-expanded="false" aria-controls="tdl-sug" aria-autocomplete="list" enterkeyhint="search">
      <kbd class="tdl-search__key" aria-hidden="true">/</kbd>
      <button class="btn btn--primary tdl-search__btn" type="submit" aria-label="Tìm kiếm">{self.ico("i-search")} <span>Tìm kiếm</span></button>
      <div class="tdl-sug" id="tdl-sug" role="listbox" aria-label="Gợi ý" hidden></div>
    </form>
    <div class="tdl-band__examples"><span>Ví dụ:</span><a href="{r}{HUB}dieu-17/">Điều 17</a><a href="{r}{HUB}?q=đồng%20phạm">đồng phạm</a><a href="{r}{HUB}?q=người%20giúp%20sức">người giúp sức</a><a href="{r}{HUB}?q=phạm%20tội%20có%20tổ%20chức">phạm tội có tổ chức</a><a href="{r}{HUB}?q=lừa%20đảo">lừa đảo</a><a href="{r}{HUB}?q=tham%20ô">tham ô</a></div>
  </div>
</section>"""

    def toc(self, r, cur_art=None, cur_ch=None):
        base = r + HUB
        cur_ch = cur_ch or (cur_art["ch"] if cur_art else None)
        out = []
        for pid, p in self.c.parts.items():
            chs = [c for c in self.c.chapters if c["part"] == pid]
            open_p = " open" if (cur_ch is None or cur_ch["part"] == pid) else ""
            items = []
            for c in chs:
                is_cur = cur_ch is not None and c["id"] == cur_ch["id"]
                arts = ""
                if is_cur:
                    rows, last_m = [], None
                    rows.append(f'<li class="tdl-toc__overview"><a href="{base}{c["slug"]}/"'
                                f'{AC if not cur_art else ""}>Tổng quan {esc(c["label"] if c["num"] else self.c.parts[c["part"]]["label"])} {self.arrow}</a></li>')
                    for a in c["a"]:
                        if a.get("m") and a["m"] != last_m:
                            last_m = a["m"]
                            rows.append(f'<li class="tdl-toc__muc">{esc(c["muc_names"].get(a["m"], ""))}</li>')
                        cur = cur_art is not None and a["id"] == cur_art["id"]
                        rows.append(f'<li><a href="{base}dieu-{a["id"]}/"{AC if cur else ""}>'
                                    f'<span class="n">Điều {a["id"]}</span><span class="t">{esc(a["t"])}</span></a></li>')
                    arts = "".join(rows)
                rng = f'{c["a"][0]["id"]}–{c["a"][-1]["id"]}' if len(c["a"]) > 1 else c["a"][0]["id"]
                items.append(
                    f'<details class="tdl-toc__ch" data-ch="{c["id"]}"{" open" if is_cur else ""}>' +
                    (f'<summary><span class="tdl-toc__chl">{esc(c["label"])}.</span> {esc(c["name"])}<small>Điều {rng}</small></summary>'
                     if c["num"] else f'<summary>{esc(c["name"])}<small>Điều {rng}</small></summary>') +
                    f'<ol class="tdl-toc__arts"{"" if is_cur else " data-lazy"}>{arts}</ol></details>')
            out.append(
                f'<details class="tdl-toc__part" id="{pid}"{open_p}><summary>{self.ico("i-bookmark", "tdl-toc__picon")}'
                f'<span><b>{esc(p["label"])}</b>{esc(p["name"])}</span></summary>{"".join(items)}</details>')
        return f"""<aside class="tdl-toc" id="tdl-toc" aria-label="Mục lục Bộ luật Hình sự">
  <div class="tdl-toc__head">{self.ico("i-book", "tdl-toc__hicon")}<span>NỘI DUNG BLHS</span>
    <button class="tdl-toc__close" type="button" aria-label="Đóng mục lục" data-toc-close>{self.ico("i-close", "")}</button></div>
  <nav class="tdl-toc__body">{"".join(out)}</nav>
</aside>"""

    def side_docs(self, r):
        return f"""<section class="tdl-card tdl-card--green">
  <h2 class="tdl-card__title">{self.ico("i-doc", "tdl-card__icon")}Văn bản liên quan</h2>
  <ul class="tdl-list">
    <li>Bộ luật Hình sự số 100/2015/QH13</li>
    <li>Luật số 12/2017/QH14 sửa đổi, bổ sung Bộ luật Hình sự</li>
    <li>Luật số 86/2025/QH15 sửa đổi, bổ sung Bộ luật Hình sự</li>
    <li>Bộ luật Tố tụng hình sự 2015 (sửa đổi, bổ sung)</li>
  </ul>
  <a class="link-arrow" href="{r}dich-vu/hinh-su/">Dịch vụ luật sư hình sự {self.arrow}</a>
</section>"""

    def side_cta(self, r, aid=None):
        what = f"về Điều {aid}" if aid else "về vụ án hình sự"
        # Lĩnh vực khác (ngoài hình sự) có dẫn chiếu điều này, ví dụ Điều 186 với Hôn nhân & Gia đình
        others = [(u, t) for u, t in self.refs.get(aid, {}).get("services", []) if u != "dich-vu/hinh-su/"]
        more = "".join(f'<a class="link-arrow link-arrow--light" href="{r}{u}">{esc(t)} {self.arrow}</a>' for u, t in others)
        return f"""<section class="tdl-card tdl-card--navy">
  {self.ico("i-shield-check", "tdl-card__big")}
  <h2 class="tdl-card__title tdl-card__title--light">Cần luật sư {what}?</h2>
  <p>Bào chữa, bảo vệ bị hại và tư vấn khẩn cấp qua các giai đoạn điều tra, truy tố, xét xử.</p>{more}
  <a class="btn btn--primary btn--block btn--sm" href="{r}lien-he/#lien-he-truc-tiep">Liên hệ tư vấn {self.arrow}</a>
  <a class="tdl-card__phone" href="tel:{self.firm["phone_tel"]}">{self.ico("i-phone")} {self.firm["phone"]}</a>
</section>"""

    def chips(self, r, terms, aid=None):
        if not terms:
            return ""
        items = "".join(f'<li><a href="{r}{HUB}?q=%22{esc(t.lower())}%22">{self.ico("i-chevron-r")}{esc(t)}</a></li>' for t in terms)
        return f"""<section class="tdl-card tdl-card--cream">
  <h2 class="tdl-card__title">{self.ico("i-search", "tdl-card__icon")}{f"Từ khóa trong Điều {aid}" if aid else "Từ khóa tra cứu"}</h2>
  <ul class="tdl-chips">{items}</ul>
</section>"""

    def ch_select(self, r, cur_ch):
        base = r + HUB
        opts = "".join(f'<option value="{base}{c["slug"]}/"{" selected" if c["id"] == cur_ch["id"] else ""}>'
                       f'{esc(c["label"])} – {esc(c["name"])}</option>' for c in self.c.chapters)
        return f'<select class="tdl-nav__sel" aria-label="Chọn chương" data-go>{opts}</select>'

    def layout(self, r, toc, main, side, extra_cls=""):
        return f"""{self.band(r)}
<div class="tdl{extra_cls}" data-base="{r}{HUB}" data-v="{self.c.v}">
  <div class="tdl-wrap tdl__grid">
    {toc}
    <div class="tdl-main" id="tdl-main">
      <button class="tdl-toc-btn" type="button" data-toc-open aria-controls="tdl-toc" aria-expanded="false">{self.ico("i-book")} Nội dung BLHS</button>
      {main}
    </div>
    <aside class="tdl-side" aria-label="Trợ lý nghiên cứu"><h2 class="tdl-side__head">{self.ico("i-book")} TRỢ LÝ NGHIÊN CỨU</h2>{side}</aside>
  </div>
</div>
<div class="tdl-toast" role="status" aria-live="polite" hidden></div>"""

    # ---- Trang một điều ----
    def article(self, a, r):
        c = self.c
        base = r + HUB
        ch = a["ch"]
        part = c.parts[ch["part"]]
        prev_a = c.arts[a["i"] - 1] if a["i"] > 0 else None
        next_a = c.arts[a["i"] + 1] if a["i"] + 1 < len(c.arts) else None
        art_opts = "".join(f'<option value="{base}dieu-{x["id"]}/"{" selected" if x["id"] == a["id"] else ""}>'
                           f'Điều {x["id"]}. {esc(x["t"])}</option>' for x in ch["a"])
        muc = ch["muc_names"].get(a.get("m")) if a.get("m") else ""
        ch_line = f'{esc(ch["label"])} – {esc(ch["name"])}' + (f' · {esc(muc)}' if muc else "")
        prev_btn = (f'<a class="tdl-nav__btn" href="{base}dieu-{prev_a["id"]}/" rel="prev">{self.ico("i-arrow-l")}<span><b>Điều {prev_a["id"]}</b><small>{esc(prev_a["t"])}</small></span></a>'
                    if prev_a else '<span class="tdl-nav__btn is-disabled"></span>')
        next_btn = (f'<a class="tdl-nav__btn tdl-nav__btn--next" href="{base}dieu-{next_a["id"]}/" rel="next"><span><b>Điều {next_a["id"]}</b><small>{esc(next_a["t"])}</small></span>{self.ico("i-arrow")}</a>'
                    if next_a else '<span class="tdl-nav__btn is-disabled"></span>')
        extra = load_extra(a["id"])
        rel = c.related(a)
        mm_title, mm_nodes = c.mindmap(a)

        # Tabs
        cm, cm_heads = cm_html(a, base)
        cm_toc = ""
        if len(cm_heads) >= 2:
            cm_toc = ('<nav class="tdl-cmtoc" aria-label="Các mục của phần bình luận"><b>Nội dung bình luận</b><ol>' +
                      "".join(f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in cm_heads) + '</ol></nav>')
        if cm_heads:
            pieces = re.split(r'(?=<h3 class="tdl-cm__h")', cm)
            grouped = [pieces[0]]
            for i, chunk in enumerate(pieces[1:]):
                match = re.match(r'<h3[^>]*id="([^"]+)"([^>]*)>(.*?)</h3>(.*)', chunk, re.S)
                if match:
                    hid, attrs, title, text = match.groups()
                    grouped.append(f'<details class="tdl-comment-section"{" open" if i == 0 else ""} id="{hid}"><summary{attrs}>{title}</summary><div>{text}</div></details>')
                else: grouped.append(chunk)
            cm = "".join(grouped)
        tab_cm = (f'<h2 class="tdl-panel__title">Bình luận khoa học</h2><p class="tdl-panel__by">Tác giả phần bình luận: Đinh Văn Quế. '
                  f'Phần bình luận thể hiện quan điểm khoa học của tác giả, có giá trị tham khảo.</p>{cm_toc}<div class="tdl-cm">{cm}</div>{footnotes_html(a, "cm")}'
                  if cm else '<h2 class="tdl-panel__title">Bình luận khoa học</h2><p class="tdl-empty">Điều này chưa có phần bình luận.</p>')

        def empty(title, text, extra_html=""):
            return (f'<h2 class="tdl-panel__title">{title}</h2><div class="tdl-empty">{self.ico("i-doc", "tdl-empty__icon")}'
                    f'<p>{text}</p>{extra_html}<div class="tdl-empty__actions">'
                    f'<a class="btn btn--primary btn--sm" href="{r}lien-he/#lien-he-truc-tiep">Liên hệ tư vấn {self.arrow}</a>'
                    f'<a class="btn btn--outline btn--sm" href="{r}dich-vu/hinh-su/">Dịch vụ luật sư hình sự</a></div></div>')

        tab_lawyer = (f'<h2 class="tdl-panel__title">Góc nhìn Luật sư Nam</h2><div class="tdl-cm">{extra["goc-nhin"]}</div>'
                      if "goc-nhin" in extra else
                      empty("Góc nhìn Luật sư Nam", f"Phần phân tích thực tiễn của Luật sư Nam về Điều {a['id']} đang được biên soạn. "
                            "Nếu bạn đang gặp vụ việc liên quan, luật sư có thể trao đổi trực tiếp để đánh giá hồ sơ cụ thể."))
        tab_cases = (f'<h2 class="tdl-panel__title">Bản án liên quan</h2><div class="tdl-cm">{extra["ban-an"]}</div>'
                     if "ban-an" in extra else
                     empty("Bản án liên quan", f"Chưa có bản án được tuyển chọn cho Điều {a['id']}.",
                           '<p>Bạn có thể tra cứu bản án, quyết định đã công bố tại <a href="https://congbobanan.toaan.gov.vn/" target="_blank" rel="noopener">'
                           'Cổng công bố bản án của Tòa án nhân dân</a> và án lệ tại <a href="https://anle.toaan.gov.vn/" target="_blank" rel="noopener">'
                           'Trang thông tin án lệ</a>.</p>'))
        tab_sit = (f'<h2 class="tdl-panel__title">Tình huống thực tiễn</h2><div class="tdl-cm">{extra["tinh-huong"]}</div>'
                   if "tinh-huong" in extra else
                   empty("Tình huống thực tiễn", f"Tình huống thực tiễn áp dụng Điều {a['id']} đang được biên soạn."))

        def rel_list(counter, empty_text):
            if not counter:
                return f'<p class="tdl-muted">{empty_text}</p>'
            items = "".join(f'<li><a href="{base}dieu-{x}/"><b>Điều {x}</b><span>{esc(c.by_id[x]["t"])}</span>'
                            f'{f"<small>{n} lần</small>" if n > 1 else ""}</a></li>' for x, n in counter.most_common())
            return f'<ul class="tdl-rel">{items}</ul>'
        same_ch = Counter({x["id"]: 1 for x in ch["a"] if x["id"] != a["id"]})
        tab_rel = f"""<h2 class="tdl-panel__title">Điều liên quan</h2>
<div class="tdl-relgrid">
  <section><h3>Điều này dẫn chiếu tới</h3>{rel_list(a["out_law"], "Văn bản điều luật không dẫn chiếu điều khác.")}</section>
  <section><h3>Được dẫn chiếu tại</h3>{rel_list(a["incoming"], "Chưa có điều luật nào dẫn chiếu trực tiếp tới điều này.")}</section>
  <section><h3>Được nhắc tới trong phần bình luận</h3>{rel_list(a["out_cm"], "Phần bình luận không dẫn chiếu điều khác.")}</section>
  <section><h3>Cùng {esc(ch["label"].lower())}</h3>{rel_list(same_ch, "")}</section>
</div>"""
        # Ba phần thực tiễn chỉ thành tab riêng khi đã có nội dung (src/blhs/<số điều>.html).
        # Chưa có phần nào thì gộp thành một tab ngắn, tránh lặp ba khối trống trên hàng trăm trang.
        practice = [(tid, label, icn, body) for tid, label, icn, body in (
            ("goc-nhin", "Góc nhìn Luật sư Nam", "i-user", tab_lawyer), ("ban-an", "Bản án liên quan", "i-doc", tab_cases),
            ("tinh-huong", "Tình huống thực tiễn", "i-question", tab_sit)) if tid in extra]
        if not practice:
            practice = [("thuc-tien", "Thực tiễn áp dụng", "i-question", empty(
                "Thực tiễn áp dụng",
                f"Góc nhìn của Luật sư Nam, bản án và tình huống thực tiễn về Điều {a['id']} đang được biên soạn. "
                "Nếu anh chị đang gặp vụ việc liên quan, luật sư có thể trao đổi trực tiếp để đánh giá hồ sơ cụ thể.",
                '<p>Tra cứu bản án, quyết định đã công bố tại <a href="https://congbobanan.toaan.gov.vn/" target="_blank" rel="noopener">'
                'Cổng công bố bản án của Tòa án nhân dân</a> và án lệ tại <a href="https://anle.toaan.gov.vn/" target="_blank" rel="noopener">'
                'Trang thông tin án lệ</a>.</p>'))]
        tabs = [("binh-luan", "Bình luận khoa học", "i-scale", tab_cm)] + practice + [("dieu-lien-quan", "Điều liên quan", "i-link", tab_rel)]
        tab_btns = "".join(
            f'<button class="tdl-tab" type="button" role="tab" id="tab-{tid}" aria-controls="panel-{tid}" aria-selected="{"true" if k == 0 else "false"}"'
            f'{"" if k == 0 else TI}>{self.ico(icn)}<span>{label}</span></button>' for k, (tid, label, icn, _) in enumerate(tabs))
        tab_panels = "".join(
            f'<section class="tdl-panel" role="tabpanel" id="panel-{tid}" aria-labelledby="tab-{tid}"{"" if k == 0 else " hidden"}>{body}</section>'
            for k, (tid, label, icn, body) in enumerate(tabs))

        pager = f"""<nav class="tdl-pager" aria-label="Điều trước, điều sau">
  {f'<a class="tdl-pager__item" href="{base}dieu-{prev_a["id"]}/" rel="prev"><small>{self.ico("i-arrow-l")} Điều trước</small><b>Điều {prev_a["id"]}. {esc(prev_a["t"])}</b></a>' if prev_a else '<span></span>'}
  {f'<a class="tdl-pager__item tdl-pager__item--next" href="{base}dieu-{next_a["id"]}/" rel="next"><small>Điều sau {self.ico("i-arrow")}</small><b>Điều {next_a["id"]}. {esc(next_a["t"])}</b></a>' if next_a else '<span></span>'}
</nav>"""

        main = f"""<nav class="tdl-bc" aria-label="Đường dẫn"><ol>
  <li><a href="{r}">Trang chủ</a></li><li><a href="{base}">Bộ luật Hình sự</a></li>
  <li><a href="{base}#{ch["part"]}">{esc(part["label"])}</a></li><li><a href="{base}{ch["slug"]}/">{esc(ch["label"])}{"" if not ch["num"] else ". " + esc(ch["name"])}</a></li>
  <li aria-current="page">Điều {a["id"]}</li></ol></nav>
<div class="tdl-nav">
  {prev_btn}
  {self.ch_select(r, ch)}
  <select class="tdl-nav__sel tdl-nav__sel--art" aria-label="Chọn điều trong chương" data-go>{art_opts}</select>
  {next_btn}
</div>
<article class="tdl-article" data-id="{a["id"]}" data-title="{esc(a["t"])}">
  <header class="tdl-head">
    <div>
      <p class="tdl-head__ch">{ch_line}</p>
      <h1 class="tdl-head__title">Điều {a["id"]}. {esc(a["t"])}</h1>
      {badges_html(a)}
    </div>
    <div class="tdl-actions">
      <button type="button" data-act="save" aria-pressed="false">{self.ico("i-bookmark")}<span>Lưu</span></button>
      <button type="button" data-act="print">{self.ico("i-print")}<span>In</span></button>
      <button type="button" data-act="share">{self.ico("i-share")}<span>Chia sẻ</span></button>
      <button type="button" data-act="cite">{self.ico("i-copy")}<span>Trích dẫn</span></button>
    </div>
  </header>
  <section class="tdl-law" aria-labelledby="quy-dinh">
    <div class="tdl-law__head"><h2 id="quy-dinh">{self.ico("i-scale", "tdl-law__icon")}Quy định của luật</h2><span>({LAW_NAME}) · Trang cập nhật {{{{modified}}}}</span></div>
    <div class="tdl-law__body">
{law_html(a, base)}
    </div>
    {footnotes_html(a, "law")}
  </section>
  <div class="tdl-tabs">
    <div class="tdl-tabs__list" role="tablist" aria-label="Nội dung phân tích Điều {a["id"]}">{tab_btns}</div>
    {tab_panels}
  </div>
</article>
{pager}"""

        rel_html = "".join(f'<li><a href="{base}dieu-{x["id"]}/"><b>Điều {x["id"]}</b><span>{esc(x["t"])}</span></a></li>' for x in rel)
        if mm_nodes:
            nodes = "".join(f'<li>{f"<b>{esc(k)}</b>" if k else ""}<span>{esc(v)}</span></li>' for k, v in mm_nodes)
            mm = f"""<section class="tdl-card tdl-card--blue">
  <h2 class="tdl-card__title">{self.ico("i-map", "tdl-card__icon")}Bản đồ tư duy</h2>
  <div class="tdl-mm">
    <div class="tdl-mm__root"><b>{esc(a["t"])}</b><small>Điều {a["id"]}</small></div>
    <p class="tdl-mm__cap">{esc(mm_title)}</p>
    <ul class="tdl-mm__nodes{" tdl-mm__nodes--wide" if any(len(v) > 28 for _, v in mm_nodes) else ""}">{nodes}</ul>
  </div>
  <a class="link-arrow" href="#quy-dinh">Đối chiếu văn bản điều luật {self.arrow}</a>
</section>"""
        else:
            mm = f"""<section class="tdl-card tdl-card--blue">
  <h2 class="tdl-card__title">{self.ico("i-map", "tdl-card__icon")}Vị trí trong Bộ luật</h2>
  <ol class="tdl-path">
    <li>{esc(part["label"])}<small>{esc(part["name"])}</small></li>
    <li>{esc(ch["label"])}<small>{esc(ch["name"])}</small></li>
    {f"<li>{esc(muc)}</li>" if muc else ""}
    <li class="is-cur">Điều {a["id"]}<small>{esc(a["t"])}</small></li>
  </ol>
</section>"""
        side = (self.chips(r, c.glossary(a), a["id"]) +
                f"""<section class="tdl-card tdl-card--rose">
  <h2 class="tdl-card__title">{self.ico("i-link", "tdl-card__icon")}Điều liên quan</h2>
  <ul class="tdl-rel tdl-rel--compact">{rel_html}</ul>
</section>""" + self.side_articles(r, a["id"]) + mm + self.side_docs(r) + self.side_cta(r, a["id"]))
        return self.layout(r, self.toc(r, cur_art=a), main, side)

    def side_articles(self, r, aid):
        arts = self.refs.get(aid, {}).get("articles", [])
        if not arts:
            return ""
        items = "".join(f'<li><a href="{r}{u}"><b>Bài viết</b><span>{esc(t)}</span></a></li>' for u, t in arts)
        return f"""<section class="tdl-card tdl-card--rose">
  <h2 class="tdl-card__title">{self.ico("i-doc", "tdl-card__icon")}Bài viết liên quan</h2>
  <ul class="tdl-rel tdl-rel--compact">{items}</ul>
</section>"""

    # ---- Trang một chương ----
    def chapter(self, ch, r):
        c = self.c
        base = r + HUB
        part = c.parts[ch["part"]]
        idx = c.chapters.index(ch)
        prev_c = c.chapters[idx - 1] if idx > 0 else None
        next_c = c.chapters[idx + 1] if idx + 1 < len(c.chapters) else None
        rows, last_m = [], None
        for x in ch["a"]:
            a = c.by_id[x["id"]]
            if a.get("m") and a["m"] != last_m:
                last_m = a["m"]
                rows.append(f'<h2 class="tdl-chlist__muc">{esc(ch["muc_names"].get(a["m"], ""))}</h2>')
            rows.append(f"""<a class="tdl-item" href="{base}dieu-{a["id"]}/">
  <span class="tdl-item__n">Điều {a["id"]}</span>
  <span class="tdl-item__body"><b>{esc(a["t"])}</b><span>{esc(c.excerpt(a))}</span>{badges_html(a)}</span>
  {self.ico("i-arrow", "tdl-item__go")}
</a>""")
        terms = Counter()
        for x in ch["a"]:
            for t in c.glossary(c.by_id[x["id"]], 20):
                terms[t] += 1
        rng = f'Điều {ch["a"][0]["id"]} – {ch["a"][-1]["id"]}' if len(ch["a"]) > 1 else f'Điều {ch["a"][0]["id"]}'
        main = f"""<nav class="tdl-bc" aria-label="Đường dẫn"><ol>
  <li><a href="{r}">Trang chủ</a></li><li><a href="{base}">Bộ luật Hình sự</a></li>
  <li><a href="{base}#{ch["part"]}">{esc(part["label"])}</a></li><li aria-current="page">{esc(ch["label"])}</li></ol></nav>
<div class="tdl-nav">
  {f'<a class="tdl-nav__btn" href="{base}{prev_c["slug"]}/" rel="prev">{self.ico("i-arrow-l")} {esc(prev_c["label"])}</a>' if prev_c else '<span class="tdl-nav__btn is-disabled"></span>'}
  {self.ch_select(r, ch)}
  {f'<a class="tdl-nav__btn tdl-nav__btn--next" href="{base}{next_c["slug"]}/" rel="next">{esc(next_c["label"])} {self.ico("i-arrow")}</a>' if next_c else '<span class="tdl-nav__btn is-disabled"></span>'}
</div>
<header class="tdl-head tdl-head--ch">
  <div>
    <p class="tdl-head__ch">{esc(part["label"])} – {esc(part["name"])}</p>
    <h1 class="tdl-head__title">{esc(ch["title"])}</h1>
    <p class="tdl-head__meta">{rng} · {len(ch["a"])} điều{f' · {len(ch["muc"])} mục' if ch["muc"] else ""}</p>
  </div>
</header>
<div class="tdl-chlist">{"".join(rows)}</div>"""
        side = self.chips(r, [t for t, _ in terms.most_common(8)]) + self.side_docs(r) + self.side_cta(r)
        return self.layout(r, self.toc(r, cur_ch=ch), main, side)

    # ---- Trang tổng quan ----
    def hub(self, r):
        c = self.c
        base = r + HUB
        st = c.toc["stats"]

        def rng(arts):
            return f'Điều {arts[0]["id"]}' + (f'–{arts[-1]["id"]}' if len(arts) > 1 else "")

        # Cấu trúc: mỗi phần một bảng chương
        parts = []
        for pid, p in c.parts.items():
            chs = [ch for ch in c.chapters if ch["part"] == pid]
            arts = [a for ch in chs for a in ch["a"]]
            nums = [ch["num"] for ch in chs if ch["num"]]
            meta = [f'Chương {nums[0]}–{nums[-1]}' if len(nums) > 1 else ""] if nums else []
            meta.append(rng(arts))
            rows = "".join(
                f'<li><a href="{base}{ch["slug"]}/"><span class="tdl-chs__n">{esc(ch["num"])}</span>'
                f'<span class="tdl-chs__t"><b>{esc(ch["name"])}</b><small>{rng(ch["a"])} · {len(ch["a"])} điều</small></span></a></li>'
                if ch["num"] else
                # Phần không chia chương (Điều khoản thi hành): dẫn thẳng tới từng điều
                "".join(f'<li><a href="{base}dieu-{a["id"]}/"><span class="tdl-chs__n">§</span>'
                        f'<span class="tdl-chs__t"><b>{esc(a["t"])}</b><small>Điều {a["id"]}</small></span></a></li>' for a in ch["a"])
                for ch in chs)
            parts.append(
                f'<section class="tdl-part" id="{pid}"><header class="tdl-part__head"><span class="tdl-part__label">{esc(p["label"])}</span>'
                f'<h3>{esc(p["name"])}</h3><span class="tdl-part__meta">{" · ".join(m for m in meta if m)}</span></header>'
                f'<ol class="tdl-chs">{rows}</ol></section>')

        # Các điều thường gặp, xếp theo chủ đề (nhãn ngắn, bám theo tên chương)
        topics = [
            ("Tội phạm, trách nhiệm hình sự", ["8", "12", "17"]),
            ("Quyết định hình phạt, án treo", ["51", "52", "54", "65"]),
            ("Tính mạng, sức khỏe", ["123", "134"]),
            ("Sở hữu", ["168", "173", "174", "175"]),
            ("Ma túy", ["248", "249", "251"]),
            ("An toàn, trật tự công cộng", ["260", "321"]),
            ("Chức vụ", ["353", "354"]),
        ]
        topic_rows = []
        for label, ids in topics:
            arts = [c.by_id[x] for x in ids if x in c.by_id]
            chs = list(OrderedDict((a["ch"]["id"], a["ch"]) for a in arts).values())
            ch_links = ", ".join(f'<a href="{base}{ch["slug"]}/">{esc(ch["label"])}</a>' for ch in chs)
            items = "".join(f'<li><a href="{base}dieu-{a["id"]}/"><b>Điều {a["id"]}</b><span>{esc(a["t"])}</span></a></li>' for a in arts)
            topic_rows.append(f'<div class="tdl-row"><div class="tdl-row__k"><h3>{esc(label)}</h3><small>{ch_links}</small></div>'
                              f'<ul class="tdl-arts">{items}</ul></div>')

        def tries(*qs):
            return "".join(f'<button class="tdl-try" type="button" data-try="{esc(q)}">{self.ico("i-search")}{esc(q)}</button>' for q in qs)
        ways = [
            ("Số điều", "Gõ số rồi nhấn Enter", tries("173", "điều 217a")),
            ("Khoản, điểm", "Mở thẳng tới đoạn cần đọc", tries("điểm s khoản 1 điều 51")),
            ("Từ khóa", "Có dấu hay không dấu đều được", tries("án treo", "trom cap tai san")),
            ("Cụm từ chính xác", "Đặt trong ngoặc kép", tries("“tái phạm nguy hiểm”")),
        ]
        way_rows = "".join(f'<div class="tdl-row"><div class="tdl-row__k"><h3>{k}</h3><small>{hint}</small></div>'
                           f'<div class="tdl-row__v">{v}</div></div>' for k, hint, v in ways)

        main = f"""<nav class="tdl-bc" aria-label="Đường dẫn"><ol><li><a href="{r}">Trang chủ</a></li><li><a href="{r}kien-thuc-phap-ly/">Kiến thức pháp lý</a></li><li aria-current="page">Bộ luật Hình sự</li></ol></nav>
<section class="tdl-results" id="tdl-results" aria-live="polite" hidden></section>
<div class="tdl-overview" id="tdl-overview">
  <header class="tdl-hub">
    <p class="tdl-hub__eyebrow">Tra cứu toàn văn kèm bình luận khoa học</p>
    <h1 class="tdl-hub__title">Bộ luật Hình sự 2015 <em>sửa đổi, bổ sung năm 2017 và 2025</em></h1>
    <p class="tdl-hub__lead">Mỗi điều luật có trang riêng: văn bản điều luật, bình luận khoa học, điều liên quan và bản đồ tư duy.</p>
    <ul class="tdl-kpis">
      <li><b>{st["arts"]}</b><span>điều luật</span></li>
      <li><b>{st["chapters"]}</b><span>chương</span></li>
      <li><b>{st["am"]}</b><span>điều có sửa đổi, bổ sung (*)</span></li>
      <li><b>{st["n25"]}</b><span>điều có điểm mới năm 2025</span></li>
    </ul>
  </header>

  <section class="tdl-sec" id="huong-dan" aria-labelledby="h-tim">
    <div class="tdl-sec__head"><span class="tdl-sec__num">1</span><div><h2 id="h-tim">Tìm kiếm</h2><p>Gõ vào ô tìm kiếm ở đầu trang, hoặc bấm một ví dụ để thử.</p></div></div>
    <div class="tdl-rows">{way_rows}</div>
    <p class="tdl-keys"><span><kbd>/</kbd> mở ô tìm kiếm</span><span><kbd>[</kbd> <kbd>]</kbd> sang điều trước, điều sau</span></p>
  </section>

  <section class="tdl-sec" aria-labelledby="h-nhanh">
    <div class="tdl-sec__head"><span class="tdl-sec__num">2</span><div><h2 id="h-nhanh">Các điều thường gặp</h2><p>Lối tắt tới những điều hay được tra cứu, xếp theo chủ đề.</p></div></div>
    <div class="tdl-rows">{"".join(topic_rows)}</div>
  </section>

  <section class="tdl-sec" aria-labelledby="h-cautruc">
    <div class="tdl-sec__head"><span class="tdl-sec__num">3</span><div><h2 id="h-cautruc">Cấu trúc Bộ luật</h2><p>{len(c.parts)} phần · {st["chapters"]} chương · {st["arts"]} điều. Chọn một chương để xem danh sách điều kèm trích đoạn.</p></div></div>
    {"".join(parts)}
  </section>

  <p class="tdl-notice">Văn bản điều luật được trình bày theo tài liệu gốc; khi trích dẫn chính thức, vui lòng đối chiếu văn bản hợp nhất và văn bản hướng dẫn hiện hành. Phần bình luận của tác giả Đinh Văn Quế thể hiện quan điểm khoa học, có giá trị tham khảo, không phải văn bản hướng dẫn áp dụng pháp luật. Xem <a href="{r}mien-tru-trach-nhiem/">Tuyên bố miễn trừ trách nhiệm</a>.</p>
</div>"""
        side = f"""<section class="tdl-card tdl-card--cream" id="tdl-saved" hidden>
  <h2 class="tdl-card__title">{self.ico("i-bookmark", "tdl-card__icon")}Điều đã lưu</h2>
  <ul class="tdl-rel tdl-rel--compact"></ul>
</section>""" + self.side_docs(r) + self.side_cta(r)
        return self.layout(r, self.toc(r), main, side, " tdl--hub")
