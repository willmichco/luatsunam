# -*- coding: utf-8 -*-
"""Tạo lại phông web assets/fonts/be-vietnam-pro-{400,600,700}-vi.woff2 (chạy tay, chỉ khi đổi phông hoặc bộ ký tự).

    # bản gốc: https://github.com/google/fonts/tree/main/ofl/bevietnampro (SIL Open Font License 1.1, assets/fonts/OFL.txt)
    python3 tools/phong_web.py <thư mục chứa BeVietnamPro-Regular.ttf, -SemiBold.ttf, -Bold.ttf>

Mỗi độ đậm MỘT tệp gồm chữ Latin cơ bản + đủ bộ chữ tiếng Việt (mọi nguyên âm × 5 dấu thanh, đ, dấu tổ hợp cho văn bản
dạng NFD) + dấu câu thường gặp. Trước đây mỗi độ đậm tách 2 tệp latin + vietnamese, văn bản tiếng Việt luôn cần cả hai:
6 tệp ~102 KB → 3 tệp ~36 KB. Ký tự ngoài bộ (hiếm) hiện bằng phông dự phòng đã chỉnh cỡ khớp (BVP Fallback).
Tệp latin/vietnamese cũ vẫn giữ cho ảnh chia sẻ (tools/images.py) và trang quản trị (admin/giao-dien.css).
"""
import os
import sys
import unicodedata

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEIGHTS = ((400, "Regular"), (600, "SemiBold"), (700, "Bold"))


def charset():
    chars = {chr(c) for c in range(0x20, 0x7F)}
    chars |= set("ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯư")
    for base in "aăâeêioôơuưyAĂÂEÊIOÔƠUƯY":
        for mark in ("", "̀", "́", "̉", "̃", "̣"):
            chars.add(unicodedata.normalize("NFC", base + mark))
    chars |= set("̣̀́̃̉")
    chars |= set("–—‘’‚“”„…•·‹›«»€₫№×÷±°©®™†‰′″←→↑↓−§¶  ​ ")
    return chars


def main():
    src = sys.argv[1]
    unicodes = sorted(ord(c) for c in charset())
    for weight, name in WEIGHTS:
        opt = subset.Options()
        opt.flavor = "woff2"
        opt.layout_features = ["kern", "liga", "ccmp", "mark", "mkmk", "locl", "calt"]
        opt.name_IDs = [0, 1, 2, 3, 4, 5, 6]  # giữ bản quyền, tên phông (OFL)
        opt.hinting = False
        opt.desubroutinize = True
        font = TTFont(os.path.join(src, f"BeVietnamPro-{name}.ttf"))
        sub = subset.Subsetter(opt)
        sub.populate(unicodes=unicodes)
        sub.subset(font)
        font.flavor = "woff2"
        out = os.path.join(ROOT, "assets", "fonts", f"be-vietnam-pro-{weight}-vi.woff2")
        font.save(out)
        print(f"{os.path.relpath(out, ROOT)}: {os.path.getsize(out) // 1024} KB")


if __name__ == "__main__":
    main()
