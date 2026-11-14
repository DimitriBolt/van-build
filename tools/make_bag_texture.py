# -*- coding: utf-8 -*-
"""Текстура крышки баула SUP (Genreen) для модели: assets/sup_bag_crop.png (вырезка из картинки Dimitri, 294×607 px,
верх = молния) → assets/sup_bag_top.png в пропорции 300×1100 мм. Логотип и надпись сверху и оранжевый логотип снизу
остаются в натуральном масштабе, растягивается только ровная синяя полоса между ними (так картинка не искажается).
Запуск: python3 tools/make_bag_texture.py"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "..", "assets")
W_MM, L_MM = 300.0, 1100.0
TRIM = (0, 8, 286, 607)                 # убрать белый фон по краям вырезки: x0, y0, x1, y1
SPLIT = (192, 352)                      # ровная синяя полоса между «WAVE IT EASY» и оранжевым логотипом (px после обрезки)

src = Image.open(os.path.join(A, "sup_bag_crop.png")).convert("RGB").crop(TRIM)
w, h = src.size
need_h = round(w * L_MM / W_MM)         # высота текстуры при ширине w px
top, mid, bot = src.crop((0, 0, w, SPLIT[0])), src.crop((0, SPLIT[0], w, SPLIT[1])), src.crop((0, SPLIT[1], w, h))
mid2 = mid.resize((w, need_h - top.size[1] - bot.size[1]), Image.LANCZOS)
out = Image.new("RGB", (w, need_h))
out.paste(top, (0, 0)); out.paste(mid2, (0, top.size[1])); out.paste(bot, (0, top.size[1] + mid2.size[1]))
out = out.resize((w * 2, need_h * 2), Image.LANCZOS)
out.save(os.path.join(A, "sup_bag_top.png"))
print("sup_bag_top.png", out.size)
