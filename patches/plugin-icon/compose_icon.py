# -*- coding: utf-8 -*-
"""用桌宠官方立绘（assets/memes/可爱.png）合成插件图标。
- 白色背景做「从边缘泛洪」抠除（保留角色内部的白色围裙/帽子）
- 蓝渐变圆角底 + 少量气泡 + 脚底柔光
"""
from PIL import Image, ImageDraw
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"C:\Users\chenshengyi\.dsh\profiles\desktop\node_modules\dsh-pet\assets\memes\可爱.png"
OUT = os.path.join(HERE, "plugin-icon.png")
S = 256

# 1) 抠白底（只从四角泛洪，角色内部白色不受影响）
im = Image.open(SRC).convert("RGBA")
rgb = im.convert("RGB")
w, h = rgb.size
MARK = (255, 0, 255)
for xy in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
    ImageDraw.floodfill(rgb, xy, MARK, thresh=26)
px = rgb.load()
alpha = im.getchannel("A").point(lambda v: v)
a = alpha.load()
for y in range(h):
    for x in range(w):
        if px[x, y] == MARK:
            a[x, y] = 0
im.putalpha(alpha)
# 轻微收缩 alpha 去白边：连续两次 3x3 腐蚀（只用 alpha 通道）
from PIL import ImageFilter
alpha = im.getchannel("A").filter(ImageFilter.MinFilter(3))
im.putalpha(alpha)
bb = im.getchannel("A").getbbox()
if bb:
    im = im.crop(bb)

# 2) 背景：蓝渐变圆角方块 + 柔光气泡
icon = Image.new("RGBA", (S, S), (0, 0, 0, 0))
grad = Image.new("RGBA", (S, S), (0, 0, 0, 0))
gd = ImageDraw.Draw(grad)
top = (134, 210, 255)
bot = (40, 112, 236)
for y in range(S):
    t = y / (S - 1)
    c = tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)) + (255,)
    gd.line((0, y, S, y), fill=c)
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle((6, 6, S - 6, S - 6), radius=58, fill=255)
icon.paste(grad, (0, 0), mask)
d = ImageDraw.Draw(icon, "RGBA")
for (x, y, r, al) in [(44, 58, 10, 55), (66, 42, 6, 40), (208, 186, 13, 40), (36, 196, 8, 36)]:
    d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, al))

# 3) 角色：等比缩放进 208×208，脚底贴底
fw, fh = im.size
scale = min(206 / fw, 214 / fh)
im = im.resize((max(1, int(fw * scale)), max(1, int(fh * scale))), Image.LANCZOS)
cw, ch = im.size
cx = (S - cw) // 2
bottom = 238
cy = bottom - ch

shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
sd.ellipse((cx + cw * 0.10, bottom - 13, cx + cw * 0.90, bottom + 7), fill=(18, 55, 135, 95))
icon = Image.alpha_composite(icon, shadow)
icon.alpha_composite(im, (cx, max(6, cy)))

icon.save(OUT, "PNG", optimize=True)
print("icon written:", OUT, os.path.getsize(OUT), "bytes", icon.size)
