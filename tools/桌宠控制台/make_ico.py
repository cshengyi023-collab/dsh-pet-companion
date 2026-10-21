# -*- coding: utf-8 -*-
"""把插件图标 PNG 转成 .ico（给桌面快捷方式用）"""
from PIL import Image
import os
src = r"D:\ai工作库\dsh-pet-control\plugin-icon\plugin-icon.png"
dst = r"D:\ai工作库\桌宠控制台\桌宠.ico"
im = Image.open(src).convert("RGBA")
im.save(dst, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
print("ico:", dst, os.path.getsize(dst), "bytes")
