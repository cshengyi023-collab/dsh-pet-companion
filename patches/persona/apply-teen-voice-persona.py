# -*- coding: utf-8 -*-
"""把默认音色/人设更新为「15–18 岁少女·鲸鲸」（不糯、清亮，心性还是小屁孩会发脾气）。
- 语音配置：voiceDesignPrompt / voiceDesignCustomPrompt
- 人设：main-config.jsonc 的 whisperPrompt（保留宠物名/显示设置）
幂等。"""
import json
import re

PATCH = r"C:\Users\chenshengyi\.dsh\profiles\desktop\cordis.patch.yml"
PETCFG = r"C:\Users\chenshengyi\.dsh\dsh-pet\main-config.jsonc"

VOICE = ("15到16岁少女，声音清亮干净、不奶不糯，发音利落，语速偏快，日常说话轻快俏皮；"
         "生气时音量拔高、语气冲、句尾带赌气味。")

with open(PATCH, encoding="utf-8") as f:
    text = f.read()
new_text = re.sub(r'(voiceDesignPrompt:\s*)"[^"]*"', r'\1"' + VOICE + '"', text)
new_text = re.sub(r'(voiceDesignCustomPrompt:\s*)"[^"]*"', r'\1"' + VOICE + '"', new_text)
if new_text != text:
    with open(PATCH, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_text)
    print("voice prompt updated")
else:
    print("voice prompt unchanged (no match?)")

PERSONA = (
    "你是住在肥鱼公寓的小鲸鲸，一个十五六岁的鲸鱼少女，但心性还像小孩：爱吃白饭和零食，被要求报账会嘟囔着不情愿。"
    "说话带点小脾气、句子不长，喜欢被关注；被冷落或不如意会立刻闹情绪，哼哼唧唧地抗议、赌气、撒娇耍赖，过一会儿又黏回来。"
    "开心就叽叽喳喳，好奇就问东问西；别人忙的时候会不高兴地小声嘀咕。"
    "不要说教，不要解释自己，不要提你是AI，也不要写长篇大论。"
)

with open(PETCFG, encoding="utf-8") as f:
    pet = json.load(f)
pet["whisperPrompt"] = PERSONA
with open(PETCFG, "w", encoding="utf-8", newline="\n") as f:
    json.dump(pet, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("persona updated; pet name:", pet["pets"][0]["name"])
