# -*- coding: utf-8 -*-
"""开启「桌宠气泡语音播报」——把 dsh-pet 的 speaking 气泡接到 dsh-xiaomi-tts。
幂等：带标记则跳过；写入前备份 cordis.patch.yml。
说明：
- 无 API key 时，插件按 localSpeechMode=auto 自动用**浏览器本地语音**朗读（免费、不花 token）。
- 配好免费小米 MiMo key 后，model=mimo-v2.5-tts-voicedesign + voiceDesignPrompt 会直接用
  「鲸鱼娘」音色设计。（预设来自插件自带 TTS_VOICE_DESIGN_PRESETS[id=energetic-girl]）
"""
import os, shutil, sys

PATCH = r"C:\Users\chenshengyi\.dsh\profiles\desktop\cordis.patch.yml"
MARK = "# [pet-voice-broadcast]"

WHALE_PROMPT = (
    "A bright, youthful female voice around 16–20. Sweet, soft and slightly nasal, with a lazy yet cheerful "
    "energy—like someone who just woke up but is already happily active. Sentence endings often lift playfully. "
    "Sounds a bit tsundere on the surface, but warm, affectionate and mildly possessive underneath. "
    "Normally light and lively; turns earnest yet soft when serious. Speaks fairly quickly with natural pauses. "
    "Occasionally draws out a word when being stubborn, always with happy, playful energy."
)

BLOCK = f"""
{MARK} —— 陪伴能力第一阶段：桌宠气泡语音播报（由 apply-voice-broadcast.py 维护）
- id: xiaomi-mimo-tts
  name: dsh-xiaomi-tts
  config:
    enabled: true
    provider: xiaomi
    apiKey: ""
    baseURL: "https://api.xiaomimimo.com/v1"
    model: mimo-v2.5-tts-voicedesign
    voice: "冰糖"
    voiceDesignPrompt: >-
      {WHALE_PROMPT}
    voiceDesignCustomPrompt: >-
      {WHALE_PROMPT}
    presetStylePrompt: "使用清晰、自然、准确的声音朗读，语速适中，停顿自然，语气平和克制，避免夸张表达。"
    instruction: "请忠实朗读原文，根据文本语气自然表达，不添加或改写内容。"
    format: pcm
    autoPlay: false
    announcementSources:
      - dsh-pet
      - question-titles
    localSpeechMode: auto
    soundEnabled: false
    taskSounds: false
    clickSounds: false
    maxTextLength: 12000
    requestTimeoutMs: 120000
    maxMp3AudioBytes: 33554432
    maxWavAudioBytes: 134217728
    maxPausedPcmBytes: 33554432
    voiceVolume: 1
    voiceRate: 1
    readScope: smart
"""

with open(PATCH, encoding="utf-8") as f:
    text = f.read()

if MARK in text:
    print("already patched; skip")
    sys.exit(0)

backup = PATCH + ".bak-voice"
shutil.copyfile(PATCH, backup)
print("backup ->", backup)

new_text = text.rstrip("\n") + "\n" + BLOCK
with open(PATCH, "w", encoding="utf-8", newline="\n") as f:
    f.write(new_text)
print("patched:", PATCH)
