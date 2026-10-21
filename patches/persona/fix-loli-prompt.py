# -*- coding: utf-8 -*-
"""把默认音色描述改成定稿的「小鲸鲸·萝莉」（A 尖锐傲娇 + B 小恶魔 融合）。
支持 YAML 折叠块（多行描述）。幂等。"""
PATCH = r"C:\Users\chenshengyi\.dsh\profiles\desktop\cordis.patch.yml"

PROMPT = (
    "二次元动漫/游戏配音风格，8到12岁小女孩的萝莉音，音调偏高、声线尖细清脆，带夸张的二次元演技感，"
    "不是温柔治愈系；语速偏快，句尾常上扬；带小恶魔式的坏笑和黏糊拖腔，"
    "生气时音量拔高、赌气哼哼，撒娇也带点坏心眼。"
)

with open(PATCH, encoding="utf-8") as f:
    lines = f.read().split("\n")

start = next((i for i, l in enumerate(lines) if l.strip() == "- id: xiaomi-mimo-tts"), None)
if start is None:
    raise SystemExit("找不到 xiaomi 条目")
end = len(lines)
for j in range(start + 1, len(lines)):
    if lines[j].startswith("- ") or lines[j].startswith("#"):
        end = j
        break

out = []
i = start
changed = 0
while i < end:
    line = lines[i]
    stripped = line.strip()
    key = None
    if stripped.startswith("voiceDesignPrompt:"):
        key = "voiceDesignPrompt"
    elif stripped.startswith("voiceDesignCustomPrompt:"):
        key = "voiceDesignCustomPrompt"
    if key:
        out.append(f'    {key}: "{PROMPT}"')
        # 跳过原值的续行（缩进 > 4 且不像新键）
        i += 1
        while i < end and lines[i].startswith("      ") and not lines[i].strip().startswith("- "):
            i += 1
        changed += 1
        continue
    out.append(line)
    i += 1

if changed == 0:
    raise SystemExit("没找到 voiceDesignPrompt 键")

new_lines = lines[:start] + out + lines[end:]
with open(PATCH, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(new_lines))
print("updated prompts:", changed)
