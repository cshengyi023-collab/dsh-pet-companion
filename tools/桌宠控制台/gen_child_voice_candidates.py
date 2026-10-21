# -*- coding: utf-8 -*-
"""生成「小孩鲸鱼娘」音色的 3 个候选试音，并依次播放供挑选。"""
import json, os, time, urllib.request, ctypes

BASE = "http://127.0.0.1:19387/plugins/xiaomi-mimo-tts/synthesize"
OUT = r"D:\ai工作库\桌宠控制台\试音缓存"
os.makedirs(OUT, exist_ok=True)

LINES = [
    "你回来啦！今天要陪我玩好久好久才行哦。",
    "哼！我生气了！你都不理我……我、我再也不跟你好了！",
]

CANDIDATES = {
    "小孩A-奶音4岁": "4到6岁小女孩，奶声奶气，声音软糯清亮，咬字略含糊，撒娇尾音上扬，语速偏快，情绪外露；生气时会拉长音、跺脚式地哼哼抗议。",
    "小孩B-傲娇7岁": "6到8岁小女孩，清脆明亮的童声，奶音不重，说话直接带小脾气；生气时音量变大、语速加快、尾音下压；撒娇时拖长音，情绪起伏明显。",
    "小孩C-元气6岁": "5到7岁小女孩，活泼俏皮的甜脆童声，说话跳脱，笑声多；生气时不服气地反驳、哼哼唧唧，语速快。",
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
        for _ in range(300):
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

print("=== 依次播放候选（每段约 10 秒）===")
for name in CANDIDATES:
    path = os.path.join(OUT, f"{name}.mp3")
    if os.path.exists(path):
        print("playing:", name)
        play(path)
        time.sleep(0.5)
print("done")
