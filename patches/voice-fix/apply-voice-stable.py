# -*- coding: utf-8 -*-
"""把已合并的 TTS 配置调整成「稳定可用」组合（幂等）：
- model: mimo-v2.5-tts（预设；实时流式/气泡播报/自动朗读都支持）
- voice: 冰糖（预设中文女声；无 key 时也能走浏览器本地语音）
- localVoiceURI: Microsoft Huihui Desktop（本机真实存在的本地中文语音；原来的 Kangkang 没装）
- 保留 announcementSources(dsh-pet) / 音效偏好 / instruction
「鲸鱼娘」音色设计参数保留在配置里，供「朗读台」按需用 body 覆盖方式调用（非流式）。
"""
import re, shutil, sys

PATCH = r"C:\Users\chenshengyi\.dsh\profiles\desktop\cordis.patch.yml"
MARK = "# [tts-voice-fix]"

with open(PATCH, encoding="utf-8") as f:
    text = f.read()

if MARK in text:
    print("already patched; skip")
    sys.exit(0)

bak = PATCH + ".bak-voicefix"
shutil.copyfile(PATCH, bak)
print("backup ->", bak)

lines = text.split("\n")
start = next((i for i, l in enumerate(lines) if l.strip() == "- id: xiaomi-mimo-tts"), None)
if start is None:
    raise SystemExit("xiaomi entry not found")
end = len(lines)
for j in range(start + 1, len(lines)):
    if lines[j].startswith("- ") or lines[j].startswith("#"):
        end = j
        break

block = lines[start:end]
out = []
for line in block:
    s = line.strip()
    if s.startswith("model:"):
        out.append("    model: mimo-v2.5-tts")
    elif s.startswith("voice:") and "voiceDesignPrompt" not in s:
        out.append('    voice: "冰糖"')
    elif s.startswith("localVoiceURI:"):
        out.append('    localVoiceURI: "Microsoft Huihui Desktop"')
    else:
        out.append(line)

new = "\n".join(lines[:start]) + f"\n{MARK} 稳定可用组合：预设模型（流式播报）+ 本机存在的本地语音\n" + "\n".join(out) + "\n" + "\n".join(lines[end:])
with open(PATCH, "w", encoding="utf-8", newline="\n") as f:
    f.write(new)
print("patched model/voice/localVoiceURI; apiKey preserved:", ("apiKey: \"" in "\n".join(out)))
