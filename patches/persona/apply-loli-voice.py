# -*- coding: utf-8 -*-
"""定稿音色：A（尖锐傲娇）+ B（小恶魔）融合的「小鲸鲸·萝莉」。
1) 写入语音插件默认音色描述（voiceDesignPrompt / Custom）
2) 在插件音色设计列表（前端 + 宿主静态资源清单）加入「小鲸鲸·萝莉」预设
3) 生成对应头像
幂等；插件升级后重跑。"""
import os
import re
import shutil

PATCH = r"C:\Users\chenshengyi\.dsh\profiles\desktop\cordis.patch.yml"
PKG = r"C:\Users\chenshengyi\.dsh\profiles\desktop\node_modules\dsh-xiaomi-tts"
CLIENT = os.path.join(PKG, "lib", "client.js")
UTILS = os.path.join(PKG, "lib", "utils-Cv8enEiT.js")
ASSETS = os.path.join(PKG, "assets", "voice-presets")

PID = "xiaojingjing-loli"
LABEL = "小鲸鲸·萝莉"
SUMMARY = "二次元偏尖"
PROMPT = (
    "二次元动漫/游戏配音风格，8到12岁小女孩的萝莉音，音调偏高、声线尖细清脆，带夸张的二次元演技感，"
    "不是温柔治愈系；语速偏快，句尾常上扬；带小恶魔式的坏笑和黏糊拖腔，"
    "生气时音量拔高、赌气哼哼，撒娇也带点坏心眼。"
)


def php_block():
    return (
        "\t{\n"
        f'\t\tid: "{PID}",\n'
        f'\t\tlabel: "{LABEL}",\n'
        f'\t\tsummary: "{SUMMARY}",\n'
        f'\t\tprompt: "{PROMPT}"\n'
        "\t},\n"
    )


# ---- 1) 插件默认音色描述 ----
with open(PATCH, encoding="utf-8") as f:
    text = f.read()
new_text = re.sub(r'(voiceDesignPrompt:\s*)"[^"]*"', r'\1"' + PROMPT + '"', text)
new_text = re.sub(r'(voiceDesignCustomPrompt:\s*)"[^"]*"', r'\1"' + PROMPT + '"', new_text)
if new_text != text:
    with open(PATCH, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_text)
    print("default voice prompt -> loli (merged A+B)")

# ---- 2) 前后端预设列表 ----
for path in (CLIENT, UTILS):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    if PID in src:
        print("preset already in", os.path.basename(path))
        continue
    anchor = "const TTS_VOICE_DESIGN_PRESETS = [\n"
    if anchor not in src:
        raise SystemExit("找不到锚点: " + path)
    src = src.replace(anchor, anchor + php_block(), 1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    print("preset added to", os.path.basename(path))

# ---- 3) 头像 ----
src_avatar = os.path.join(ASSETS, "xiaojingjing-teen-a.webp")
dst_avatar = os.path.join(ASSETS, f"{PID}.webp")
if os.path.exists(src_avatar):
    if not os.path.exists(dst_avatar):
        shutil.copyfile(src_avatar, dst_avatar)
    print("avatar:", dst_avatar, os.path.getsize(dst_avatar), "B")
else:
    raise SystemExit("缺少头像源文件")

print("done")
