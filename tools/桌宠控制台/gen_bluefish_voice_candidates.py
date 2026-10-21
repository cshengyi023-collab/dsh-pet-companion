# -*- coding: utf-8 -*-
"""「蓝色大肥鱼」声线候选：我无法听视频，按常见角色声线做 4 个方向，播放供挑选。"""
import json, os, time, urllib.request, ctypes

BASE = "http://127.0.0.1:19387/plugins/xiaomi-mimo-tts/synthesize"
OUT = r"D:\ai工作库\桌宠控制台\试音缓存"
os.makedirs(OUT, exist_ok=True)

LINES = [
    "又吃饭？我这条鱼明明很强，只是……只是刚好有点饿而已。",
    "哼，别指望我帮你干活。除非……你给我加一碗大白饭。",
]

CANDIDATES = {
    "蓝鱼A-摆烂少年": "16到18岁少年音，偏低沉、略懒散，说话拖着尾音、漫不经心，语速中等偏慢，像不太情愿开口；不耐烦时压低声音嘟囔，但不会大喊。",
    "蓝鱼B-清亮冷淡少年": "15到17岁少年音，清亮干净偏冷，发音利落，语速偏快，平时话不多、语气平淡带点不耐烦；反驳时尾音上挑、音量略大。",
    "蓝鱼C-中性懒软": "15到18岁偏中性的声音，软但不糯，音色干净略沙，语速慢悠悠、带点鼻音，懒懒的没什么精神；被惹到会拖长音抗议。",
    "蓝鱼D-冷淡少女": "15到18岁少女音，偏冷偏亮、干净利落，说话简短平淡，语速中等，带点傲娇和嫌弃；生气时压低声音、语气很直。",
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
