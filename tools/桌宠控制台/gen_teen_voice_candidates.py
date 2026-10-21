# -*- coding: utf-8 -*-
"""生成「15–18 岁少女」鲸鲸音色候选（不糯、清亮），依次播放供挑选。"""
import json, os, time, urllib.request, ctypes

BASE = "http://127.0.0.1:19387/plugins/xiaomi-mimo-tts/synthesize"
OUT = r"D:\ai工作库\桌宠控制台\试音缓存"
os.makedirs(OUT, exist_ok=True)

LINES = [
    "你回来啦！今天要陪我玩好久才行哦。",
    "哼！我生气了！你都不理我……我再也不跟你好了！",
]

CANDIDATES = {
    "少女A-清亮16岁": "15到16岁少女，声音清亮干净、不奶不糯，发音利落，语速偏快，日常说话轻快俏皮；生气时音量拔高、语气冲、句尾带赌气味。",
    "少女B-元气17岁": "16到18岁少女，明亮元气的少女音，不黏不糯，说话直来直去，笑声清爽；生气时语速加快、音量变大、带着不服气的反驳语气。",
    "少女C-傲娇17岁": "17到18岁少女，偏冷偏亮的少女音，声线干净利落，平时说话简短、带点小傲娇；生气时压低声音赌气，撒娇时尾音拖长但不奶。",
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

print("=== 依次播放（每段约 10 秒）===")
for name in CANDIDATES:
    path = os.path.join(OUT, f"{name}.mp3")
    if os.path.exists(path):
        print("playing:", name)
        play(path)
        time.sleep(0.4)
print("done")
