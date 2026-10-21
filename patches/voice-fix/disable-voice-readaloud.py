# -*- coding: utf-8 -*-
"""关闭语音朗读（保留 UI 音效）：enabled=false、announcementSources=[]、autoPlay=false。
幂等；写入 DSH profile 的插件配置。"""
import re

PATCH = r"C:\Users\chenshengyi\.dsh\profiles\desktop\cordis.patch.yml"

with open(PATCH, encoding="utf-8") as f:
    text = f.read()

lines = text.split("\n")
start = next((i for i, l in enumerate(lines) if l.strip() == "- id: xiaomi-mimo-tts"), None)
if start is None:
    raise SystemExit("找不到 xiaomi 配置条目")
end = len(lines)
for j in range(start + 1, len(lines)):
    if lines[j].startswith("- ") or lines[j].startswith("#"):
        end = j
        break
block = lines[start:end]

out = []
skip_ann = 0
for line in block:
    s = line.strip()
    if s.startswith("enabled:"):
        out.append("    enabled: false")
    elif s.startswith("announcementSources:"):
        out.append("    announcementSources: []")
        skip_ann = 1
    elif skip_ann and s.startswith("- "):
        continue  # 跳过原列表项
    else:
        skip_ann = 0
        out.append(line)

new_text = "\n".join(lines[:start] + out + lines[end:])
if new_text != text:
    with open(PATCH, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_text)
    print("voice read-aloud disabled")
else:
    print("no change")
