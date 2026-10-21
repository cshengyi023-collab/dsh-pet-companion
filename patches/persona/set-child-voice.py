# -*- coding: utf-8 -*-
"""把语音插件默认音色改成「小鲸鲸」小孩音（候选B：傲娇7岁），并保留 key/播报/音效设置。
幂等：重建 xiaomi-mimo-tts 配置条目。"""
import re

PATCH = r"C:\Users\chenshengyi\.dsh\profiles\desktop\cordis.patch.yml"
MARK = "# [xiaojingjing-voice]"

CHILD_B = ("6到8岁小女孩，清脆明亮的童声，奶音不重，说话直接带小脾气；生气时音量变大、语速加快、"
           "尾音下压；撒娇时拖长音，情绪起伏明显。日常说话轻快自然，像小屁孩在跟人撒娇、闹脾气一样。")

with open(PATCH, encoding="utf-8") as f:
    text = f.read()

keys = re.findall(r'^\s*apiKey:\s*"([^"]+)"\s*$', text, re.M)
api_key = keys[-1] if keys else ""

block = f'''{MARK} 小鲸鲸默认音色（小孩/会发脾气）；由 dsh-pet-control/persona 维护
- id: xiaomi-mimo-tts
  name: dsh-xiaomi-tts
  config:
    enabled: true
    provider: xiaomi
    apiKey: "{api_key}"
    baseURL: "https://api.xiaomimimo.com/v1"
    model: mimo-v2.5-tts-voicedesign
    voice: "冰糖"
    voiceDesignPrompt: "{CHILD_B}"
    voiceDesignCustomPrompt: "{CHILD_B}"
    presetStylePrompt: "使用清晰、自然、准确的声音朗读，语速适中，停顿自然，语气平和克制，避免夸张表达。"
    instruction: "用小女孩的语气自然地朗读，情绪跟着内容走，日常轻快、激动时更冲。"
    format: pcm
    announcementSources:
      - dsh-pet
      - question-titles
    localSpeechMode: auto
    localVoiceURI: "Microsoft Huihui Desktop"
    autoPlay: false
    readScope: smart
    voiceVolume: 1
    voiceRate: 1
    soundEnabled: true
    soundVolume: 0.36
    soundPack: soft
    taskSounds: true
    clickSounds: true
    maxTextLength: 12000
    requestTimeoutMs: 120000
    maxMp3AudioBytes: 33554432
    maxWavAudioBytes: 134217728
    maxPausedPcmBytes: 33554432
'''

lines = text.split("\n")
start = next((i for i, l in enumerate(lines) if l.strip() == "- id: xiaomi-mimo-tts"), None)
if start is None:
    raise SystemExit("找不到 xiaomi 配置条目")
# 向前吃掉标记注释行
head = lines[:start]
while head and (head[-1].strip().startswith("#") or head[-1].strip() == ""):
    head.pop()
end = len(lines)
for j in range(start + 1, len(lines)):
    if lines[j].startswith("- ") or lines[j].startswith("#"):
        end = j
        break
tail = lines[end:]
new_text = "\n".join(head + [""] + [block] + tail).rstrip("\n") + "\n"

with open(PATCH + ".bak-xiaojingjing", "w", encoding="utf-8", newline="\n") as f:
    f.write(text)
with open(PATCH, "w", encoding="utf-8", newline="\n") as f:
    f.write(new_text)
print("patched; apiKey preserved:", bool(api_key), "| child prompt set:", CHILD_B[:12] + "...")
