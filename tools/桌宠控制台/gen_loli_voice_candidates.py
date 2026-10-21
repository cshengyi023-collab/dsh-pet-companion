# -*- coding: utf-8 -*-
"""「二次元萝莉音」候选：偏尖、游戏配音感、非温柔系（参考蓝色鲸鱼娘形象）。"""
import json, os, time, urllib.request, ctypes

BASE = "http://127.0.0.1:19387/plugins/xiaomi-mimo-tts/synthesize"
OUT = r"D:\ai工作库\桌宠控制台\试音缓存"
os.makedirs(OUT, exist_ok=True)

LINES = [
    "哼！谁要跟你分大白饭啊，那是我一个人的！",
    "喂——你刚才是不是想偷偷摸鱼？被我逮到了吧～",
]

CANDIDATES = {
    "萝莉A-尖锐傲娇": "二次元动漫/游戏配音风格，8到12岁小女孩的萝莉音，音调偏高、声线尖细清脆，带夸张的二次元演技感，不是温柔系；语速偏快，句尾常上扬，生气时音量拔高、带赌气的哼哼，撒娇带点坏心眼。",
    "萝莉B-小恶魔": "二次元游戏配音风，9到13岁小恶魔系萝莉音，高音偏尖、亮而利，带调皮坏笑和黏糊的拖腔，语速快；挑衅时一点不客气，故意拖长尾音，笑声清脆。",
    "萝莉C-冷淡嫌弃": "二次元动漫配音风，10到14岁萝莉音，偏高偏尖但语气冷淡平淡，语速中等、句子短，带嫌弃和不耐烦；不撒娇、不温柔，偶尔冷哼，尾音往下压。",
    "萝莉D-游戏高音亮": "二次元抽卡游戏角色配音，10到13岁高音萝莉声线，清亮尖锐、共鸣靠前，演技夸张、情绪外放，语速快，笑声清脆，像游戏里的看板娘。",
}


def synth(text, prompt):
    body = {"text": text, "model": "mimo-v2.5-tts-voicedesign",
            "voiceDesignPrompt": prompt, "format": "mp3"}
    req = urllib.request.Request(BASE, data=json.dumps(body, ensure_ascii=False).encode(),
                                 method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def strip_id3(data):
    if data[:3] == b"ID3" and len(data) > 10:
        size = (data[6] & 0x7F) << 21 | (data[7] & 0x7F) << 14 | (data[8] & 0x7F) << 7 | (data[9] & 0x7F)
        footer = 10 if (data[5] & 0x10) else 0
        return data[10 + size + footer:]
    return data


mci = ctypes.windll.winmm.mciSendStringW


def play(path):
    mci("close t", None, 0, 0)
    if mci(f'open "{path}" type mpegvideo alias t', None, 0, 0) == 0:
        mci("play t", None, 0, 0)
        time.sleep(1)
        buf = ctypes.create_unicode_buffer(128)
        for _ in range(400):
            mci("status t mode", buf, 128, 0)
            if buf.value == "stopped":
                break
            time.sleep(0.3)
        mci("close t", None, 0, 0)


for name, prompt in CANDIDATES.items():
    parts = []
    for i, line in enumerate(LINES):
        try:
            audio = synth(line, prompt)
            parts.append(strip_id3(audio))
            print(f"{name} 第{i+1}句 OK {len(audio)}B")
        except Exception as e:
            print(f"{name} 第{i+1}句失败: {e}")
    if parts:
        path = os.path.join(OUT, f"{name}.mp3")
        with open(path, "wb") as f:
            f.write(b"".join(parts))
        print("saved:", path, os.path.getsize(path))

print("=== 依次播放（每段约 12 秒）===")
for name in CANDIDATES:
    path = os.path.join(OUT, f"{name}.mp3")
    if os.path.exists(path):
        print("playing:", name)
        play(path)
        time.sleep(0.4)
print("done")
