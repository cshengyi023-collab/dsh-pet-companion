# -*- coding: utf-8 -*-
"""给 dsh-pet 画一个插件图标：蓝色大肥鱼（256×256 RGBA，透明圆角底）。
纯 Pillow 绘制，不依赖外部素材/网络。"""
from PIL import Image, ImageDraw
import os

S = 256
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugin-icon.png")

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

# ---------- 1) 蓝渐变圆角底 ----------
grad = Image.new("RGBA", (S, S), (0, 0, 0, 0))
gd = ImageDraw.Draw(grad)
top = (122, 204, 255)
bot = (44, 118, 238)
for y in range(S):
    t = y / (S - 1)
    c = tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)) + (255,)
    gd.line((0, y, S, y), fill=c)
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle((7, 7, S - 7, S - 7), radius=60, fill=255)
img.paste(grad, (0, 0), mask)

d = ImageDraw.Draw(img, "RGBA")

# ---------- 2) 背景气泡 ----------
for (x, y, r, a) in [(46, 62, 11, 70), (68, 40, 6, 55), (208, 188, 15, 55),
                     (228, 158, 8, 45), (36, 192, 9, 50), (198, 52, 6, 45)]:
    d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, a))

# ---------- 3) 大肥鱼本体 ----------
BODY = (56, 92, 190, 188)          # 蓝色身体（椭圆）
EDGE = (24, 82, 176, 255)
FIN = (74, 156, 255, 255)

# 尾巴（三角鳍，接在身体左侧）
d.polygon([(64, 140), (20, 102), (28, 140), (20, 178)], fill=FIN, outline=EDGE)
# 背鳍
d.polygon([(108, 94), (132, 58), (158, 94)], fill=FIN, outline=EDGE)
# 身体
d.ellipse(BODY, fill=(124, 199, 255, 255), outline=EDGE, width=6)
# 肚皮
d.ellipse((80, 146, 172, 190), fill=(233, 247, 255, 255), outline=(150, 200, 240, 255), width=2)
# 侧鳍（身体左下角伸出的小鳍）
d.polygon([(92, 144), (124, 162), (88, 172)], fill=FIN, outline=EDGE)
# 眼睛（白 + 黑 + 高光）
d.ellipse((146, 108, 184, 146), fill=(255, 255, 255, 255), outline=EDGE, width=3)
d.ellipse((160, 121, 178, 139), fill=(30, 48, 78, 255))
d.ellipse((164, 123, 171, 130), fill=(255, 255, 255, 255))
# 微笑
d.arc((150, 150, 184, 174), start=15, end=165, fill=EDGE, width=4)
# 头顶小水花
for (x, y, r) in [(206, 96, 7), (222, 78, 5), (192, 78, 4)]:
    d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 210))

# ---------- 4) 一小颗心（点缀） ----------
hx, hy, hs = 60, 74, 7
d.polygon([(hx, hy + hs), (hx - hs, hy - 2), (hx - hs // 3, hy - hs),
           (hx, hy - hs // 3), (hx + hs // 3, hy - hs), (hx + hs, hy - 2)],
          fill=(255, 138, 178, 235))

img.save(OUT, "PNG", optimize=True)
print("icon written:", OUT, os.path.getsize(OUT), "bytes", img.size, img.mode)
