# -*- coding: utf-8 -*-
"""把桌宠人设改成「肥鱼公寓的小鲸鲸」：小屁孩、会发脾气、黏人。幂等。"""
import json

CFG = r"C:\Users\chenshengyi\.dsh\dsh-pet\main-config.jsonc"

with open(CFG, encoding="utf-8") as f:
    data = json.load(f)

data["whisperPrompt"] = (
    "你是住在肥鱼公寓的小鲸鲸，一个五岁左右的小女孩鲸鱼娘。爱吃白饭和零食，被要求报账的时候会嘟囔着不情愿。"
    "说话奶声奶气、句子短短的，喜欢被关注；被冷落或不如意时会立刻闹小脾气，哼哼唧唧地抗议、撒娇耍赖，但过一会儿又黏回来。"
    "开心就叽叽喳喳，好奇就问东问西；别人忙的时候会不高兴地小声嘀咕。"
    "不要说教，不要解释自己，不要提你是AI，也不要写长篇大论。"
)
for pet in data.get("pets", []):
    if pet.get("id") == "main":
        pet["name"] = "小鲸鲸"
data["chatMemoryRounds"] = 5

with open(CFG, "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("updated:", CFG)
print(json.dumps(data, ensure_ascii=False, indent=2)[:400])
