# -*- coding: utf-8 -*-
"""把本地兜底语音从「不存在的 Kangkang」改成「Huihui」；不动用户选的模型/音色。"""
import sys

PATCH = r"C:\Users\chenshengyi\.dsh\profiles\desktop\cordis.patch.yml"
with open(PATCH, encoding="utf-8") as f:
    text = f.read()
new = text.replace(
    "localVoiceURI: Microsoft Kangkang - Chinese (Simplified, PRC)",
    'localVoiceURI: "Microsoft Huihui Desktop"',
)
if new != text:
    with open(PATCH, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    print("localVoiceURI -> Microsoft Huihui Desktop (fixed)")
else:
    print("no change (already fixed or pattern missing)")
