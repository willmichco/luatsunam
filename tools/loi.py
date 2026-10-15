# -*- coding: utf-8 -*-
"""Gom lỗi và cảnh báo khi build, in ra bằng tiếng Việt kèm tên tệp và tên trường.

Build không dừng ở lỗi đầu tiên: mọi lỗi được gom lại để người quản trị sửa một lần.
Có lỗi → build dừng, không xuất website; site đang chạy giữ nguyên bản cũ.
"""
import os


class Loi:
    def __init__(self):
        self.loi = []
        self.canh_bao = []

    def them(self, tep, truong, thong_bao):
        """tep: đường dẫn tệp nội dung; truong: nhãn trường theo CMS, vd. "Hỏi đáp › Mục 2 › Câu trả lời"."""
        item = (tep or "", truong or "", thong_bao)
        if item in self.loi:
            return
        # Cùng lỗi đã ghi kèm tên trường: bỏ bản thiếu tên trường; ngược lại thay bản thiếu bằng bản đủ
        same = [x for x in self.loi if x[0] == item[0] and x[2] == thong_bao]
        if not truong and any(x[1] for x in same):
            return
        if truong:
            self.loi = [x for x in self.loi if not (x[0] == item[0] and x[2] == thong_bao and not x[1])]
        self.loi.append(item)

    def canh(self, tep, truong, thong_bao):
        item = (tep or "", truong or "", thong_bao)
        if item not in self.canh_bao:
            self.canh_bao.append(item)

    def __bool__(self):
        return bool(self.loi)

    @staticmethod
    def _nhom(items):
        groups = {}
        for tep, truong, tb in items:
            groups.setdefault(tep, []).append((truong, tb))
        return groups

    def bao_cao(self, markdown=False):
        """Báo cáo dạng chữ (terminal) hoặc Markdown (email, GitHub)."""
        out = []
        if self.loi:
            out.append(("## " if markdown else "") + f"Build dừng: {len(self.loi)} lỗi cần sửa")
            out.append("")
            out.append("Website đang chạy KHÔNG bị ảnh hưởng (vẫn giữ bản cũ). Sửa đúng các trường dưới đây trong /admin rồi bấm Lưu.")
            out.append("")
            for tep, rows in self._nhom(self.loi).items():
                out.append((f"**{tep}**" if markdown else f"▸ {tep}") if tep else ("**Chung**" if markdown else "▸ Chung"))
                for truong, tb in rows:
                    label = f"{truong}: " if truong else ""
                    out.append(f"- {label}{tb}" if markdown else f"    ✗ {label}{tb}")
                out.append("")
        if self.canh_bao:
            out.append(("### " if markdown else "") + f"{len(self.canh_bao)} cảnh báo (không chặn build)")
            out.append("")
            for tep, rows in self._nhom(self.canh_bao).items():
                out.append((f"**{tep}**" if markdown else f"▸ {tep}") if tep else ("**Chung**" if markdown else "▸ Chung"))
                for truong, tb in rows:
                    label = f"{truong}: " if truong else ""
                    out.append(f"- {label}{tb}" if markdown else f"    ! {label}{tb}")
                out.append("")
        return "\n".join(out).rstrip() + "\n"

    def ghi_tom_tat_github(self):
        """Hiện báo cáo ngay trên trang kết quả GitHub Actions (Summary)."""
        path = os.environ.get("GITHUB_STEP_SUMMARY")
        if path and (self.loi or self.canh_bao):
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(self.bao_cao(markdown=True))


LOI = Loi()
