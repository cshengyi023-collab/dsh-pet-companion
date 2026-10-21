# -*- coding: utf-8 -*-
"""把「小鲸鲸」音色预设直接加进 dsh-xiaomi-tts 插件的「音色设计」列表里，
这样在 DSH 设置 → 语音朗读 → 音色设计 里就能直接选、直接试听，不用外部脚本。
幂等；插件升级后重跑。"""
import os
import shutil

CLIENT = r"C:\Users\chenshengyi\.dsh\profiles\desktop\node_modules\dsh-xiaomi-tts\lib\client.js"
ASSETS = r"C:\Users\chenshengyi\.dsh\profiles\desktop\node_modules\dsh-xiaomi-tts\assets\voice-presets"
ICON = r"D:\ai工作库\dsh-pet-control\plugin-icon\plugin-icon.png"

PRESETS = [
    ("xiaojingjing-teen-a", "小鲸鲸·清亮16", "不糯清亮",
     "15到16岁少女，声音清亮干净、不奶不糯，发音利落，语速偏快，日常说话轻快俏皮；生气时音量拔高、语气冲、句尾带赌气味。"),
    ("xiaojingjing-teen-b", "小鲸鲸·元气17", "明亮直率",
     "16到18岁少女，明亮元气的少女音，不黏不糯，说话直来直去，笑声清爽；生气时语速加快、音量变大、带着不服气的反驳语气。"),
    ("xiaojingjing-teen-c", "小鲸鲸·傲娇17", "偏冷带傲",
     "17到18岁少女，偏冷偏亮的少女音，声线干净利落，平时说话简短、带点小傲娇；生气时压低声音赌气，撒娇时尾音拖长但不奶。"),
    ("xiaojingjing-child", "小鲸鲸·奶音4岁", "软糯小孩",
     "4到6岁小女孩，奶声奶气，声音软糯清亮，咬字略含糊，撒娇尾音上扬，语速偏快，情绪外露；生气时会拉长音、跺脚式地哼哼抗议。"),
]

with open(CLIENT, encoding="utf-8") as f:
    src = f.read()

if "xiaojingjing-teen-a" in src:
    print("already patched; skip insert")
else:
    bak = CLIENT + ".orig-presets"
    if not os.path.exists(bak):
        shutil.copyfile(CLIENT, bak)
        print("backup ->", bak)

    anchor = "const TTS_VOICE_DESIGN_PRESETS = [\n"
    if anchor not in src:
        raise SystemExit("找不到预设数组锚点")
    block = ""
    for pid, label, summary, prompt in PRESETS:
        block += (
            "\t{\n"
            f'\t\tid: "{pid}",\n'
            f'\t\tlabel: "{label}",\n'
            f'\t\tsummary: "{summary}",\n'
            f'\t\tprompt: "{prompt}"\n'
            "\t},\n"
        )
    src = src.replace(anchor, anchor + block, 1)
    with open(CLIENT, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    print("inserted presets:", len(PRESETS))

# 头像（192x192 webp）
from PIL import Image  # noqa: E402
os.makedirs(ASSETS, exist_ok=True)
im = Image.open(ICON).convert("RGBA").resize((192, 192), Image.LANCZOS)
for pid, *_ in PRESETS:
    path = os.path.join(ASSETS, f"{pid}.webp")
    im.save(path, "WEBP", quality=92)
    print("avatar:", pid, os.path.getsize(path), "B")

# 校验
with open(CLIENT, encoding="utf-8") as f:
    check = f.read()
print("presets present:", all(pid in check for pid, *_ in PRESETS))
