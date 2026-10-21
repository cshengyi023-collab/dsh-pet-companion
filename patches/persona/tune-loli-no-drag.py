# -*- coding: utf-8 -*-
"""微调定稿音色：去掉拖腔、去掉嗲味；保留偏尖、二次元、小恶魔坏笑。"""
import os

OLD = ("二次元动漫/游戏配音风格，8到12岁小女孩的萝莉音，音调偏高、声线尖细清脆，带夸张的二次元演技感，"
       "不是温柔治愈系；语速偏快，句尾常上扬；带小恶魔式的坏笑和黏糊拖腔，"
       "生气时音量拔高、赌气哼哼，撒娇也带点坏心眼。")
NEW = ("二次元动漫/游戏配音风格，8到12岁小女孩的萝莉音，音调偏高、声线尖细清脆，带夸张的二次元演技感；"
       "语速偏快、吐字干脆，尾音利落不拖长，不撒娇、不黏糊；带小恶魔式的坏笑，"
       "生气时音量拔高、语气冲。")

PATCH = r"C:\Users\chenshengyi\.dsh\profiles\desktop\cordis.patch.yml"
TTS_DIR = r"C:\Users\chenshengyi\.dsh\profiles\desktop\node_modules\dsh-xiaomi-tts\lib"
FILES = [PATCH, os.path.join(TTS_DIR, "client.js"), os.path.join(TTS_DIR, "utils-Cv8enEiT.js")]

for path in FILES:
    with open(path, encoding="utf-8") as f:
        src = f.read()
    if OLD in src:
        src = src.replace(OLD, NEW)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(src)
        print("updated:", os.path.basename(path))
    else:
        print("pattern not found in", os.path.basename(path))
